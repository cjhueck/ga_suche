// Hintergrund-Runner für Phase 4: arbeitet alle GA-Bände nacheinander durch.
//
// Aufruf:
//   node _run_all_paragraph_embeddings.js                   # alle Bände, sortiert
//   node _run_all_paragraph_embeddings.js --start GA050     # ab GA050
//   node _run_all_paragraph_embeddings.js --only GA125a,GA170 # nur diese
//   node _run_all_paragraph_embeddings.js --concurrency 8   # andere Concurrency
//
// Idempotent: überspringt Bände, deren Embeddings bereits vollständig sind.
// Schreibt einen Lauf-Log nach _phase4_log.jsonl (eine Zeile pro Band).

const fs = require('fs');
const path = require('path');

const BASE = process.env.GA_BACKEND || 'http://localhost:3003';
const STEINER_DIR = path.join(__dirname, 'Steiner_GA');
const LOG_FILE = path.join(__dirname, '_phase4_log.jsonl');
const POLL_INTERVAL_MS = 8000;
const STAGNATION_TIMEOUT_MS = 120 * 1000; // 2 min ohne Fortschritt → nächster Band
const SLEEP_BETWEEN_BANDS_MS = 3000;

const args = process.argv.slice(2);
let startFrom = null;
let onlyList = null;
let concurrency = 10;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--start') startFrom = args[++i];
  else if (args[i] === '--only') onlyList = args[++i].split(',').map(s => s.trim());
  else if (args[i] === '--concurrency') concurrency = parseInt(args[++i]);
}

function logLine(obj) {
  const line = JSON.stringify({ ts: new Date().toISOString(), ...obj });
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

function listGABands() {
  const entries = fs.readdirSync(STEINER_DIR, { withFileTypes: true });
  const bands = new Set();
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const m = e.name.match(/^(GA\d+[a-zA-Z]?)/);
    if (m) bands.add(m[1]);
  }
  return [...bands].sort((a, b) => {
    // Sortierung: nach Zahl, dann Suffix
    const ma = a.match(/^GA(\d+)([a-zA-Z]?)$/);
    const mb = b.match(/^GA(\d+)([a-zA-Z]?)$/);
    if (ma && mb) {
      const na = parseInt(ma[1]); const nb = parseInt(mb[1]);
      if (na !== nb) return na - nb;
      return (ma[2] || '').localeCompare(mb[2] || '');
    }
    return a.localeCompare(b);
  });
}

async function getStatus(band) {
  const r = await fetch(`${BASE}/api/paragraph-embeddings-status?gaBand=${band}`);
  if (!r.ok) throw new Error(`status ${band}: HTTP ${r.status}`);
  return r.json();
}

async function startBand(band) {
  const r = await fetch(`${BASE}/api/generate-paragraph-embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gaBand: band, concurrency, skipExisting: true })
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`start ${band}: HTTP ${r.status} ${t.substring(0, 200)}`);
  }
  return r.json();
}

async function waitForCompletion(band, expectedTotal) {
  // expectedTotal = existing + toProcess (Ziel-embedded-Wert nach diesem Lauf)
  let lastEmbedded = -1;
  let stagnationStart = null;
  let lastReportAt = Date.now();
  const t0 = Date.now();

  while (true) {
    let s;
    try { s = await getStatus(band); } catch (e) {
      // Server kurzzeitig nicht erreichbar (Hot-Reload o.ä.) — nicht hart abbrechen
      console.warn(`[${band}] Status-Abruf fehlgeschlagen: ${e.message}`);
      await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
      continue;
    }
    const now = Date.now();

    // Live-Bericht alle ~30 s
    if (now - lastReportAt > 30000) {
      const pct = expectedTotal > 0 ? (s.embedded / expectedTotal * 100).toFixed(1) : '?';
      console.log(`  [${band}]   ${s.embedded}/${expectedTotal} (${pct}%), seit Start ${Math.round((now-t0)/1000)} s`);
      lastReportAt = now;
    }

    if (s.embedded >= expectedTotal) {
      return { ...s, durationMs: now - t0 };
    }

    if (s.embedded === lastEmbedded) {
      if (!stagnationStart) stagnationStart = now;
      else if (now - stagnationStart > STAGNATION_TIMEOUT_MS) {
        console.warn(`  [${band}] Stagnation seit ${Math.round((now-stagnationStart)/1000)} s — gehe zum nächsten Band (Rest läuft im Backend weiter)`);
        return { ...s, durationMs: now - t0, stagnated: true };
      }
    } else {
      stagnationStart = null;
    }
    lastEmbedded = s.embedded;
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
  }
}

(async () => {
  let bands = onlyList || listGABands();
  if (startFrom) {
    const idx = bands.indexOf(startFrom);
    if (idx < 0) { console.error(`--start ${startFrom} nicht gefunden`); process.exit(1); }
    bands = bands.slice(idx);
  }

  console.log('==================================================');
  console.log(` Phase 4 Runner — ${bands.length} Bände`);
  console.log(` Backend: ${BASE}`);
  console.log(` Concurrency: ${concurrency}`);
  console.log(` Log: ${LOG_FILE}`);
  console.log('==================================================\n');

  let totalNew = 0;
  let totalSkipped = 0;
  let totalErrored = 0;
  const runStart = Date.now();

  for (let i = 0; i < bands.length; i++) {
    const band = bands[i];
    const prefix = `[${i+1}/${bands.length}] ${band}`;
    try {
      const before = await getStatus(band);
      if (before.candidates === 0) {
        console.log(`${prefix}  →  keine Kandidaten, übersprungen`);
        logLine({ band, action: 'skip-no-candidates' });
        totalSkipped++;
        continue;
      }

      const startResp = await startBand(band);
      if (startResp.toProcess === 0) {
        console.log(`${prefix}  →  bereits vollständig (${startResp.existing}/${before.candidates})`);
        logLine({ band, action: 'skip-complete', existing: startResp.existing });
        totalSkipped++;
        continue;
      }

      console.log(`${prefix}  →  Generierung gestartet: ${startResp.toProcess} neu (von ${startResp.totalCandidates})`);
      const target = startResp.existing + startResp.toProcess;
      const finalStatus = await waitForCompletion(band, target);
      const newCount = finalStatus.embedded - startResp.existing;
      totalNew += newCount;
      console.log(`${prefix}  ✓  ${newCount} neu in ${(finalStatus.durationMs/1000).toFixed(0)} s${finalStatus.stagnated ? ' (Stagnation)' : ''}`);
      logLine({ band, action: 'done', toProcess: startResp.toProcess, embedded: finalStatus.embedded, durationMs: finalStatus.durationMs, stagnated: !!finalStatus.stagnated });

      await new Promise(r => setTimeout(r, SLEEP_BETWEEN_BANDS_MS));
    } catch (e) {
      console.error(`${prefix}  ✗  ${e.message}`);
      logLine({ band, action: 'error', error: e.message });
      totalErrored++;
      // Bei Fehler trotzdem weitermachen, nach kurzem Cool-Down
      await new Promise(r => setTimeout(r, 10000));
    }
  }

  const totalSec = (Date.now() - runStart) / 1000;
  console.log('\n==================================================');
  console.log(` Phase 4 fertig — ${totalNew} neue Vektoren`);
  console.log(` Übersprungen: ${totalSkipped}, Fehler: ${totalErrored}`);
  console.log(` Gesamtdauer: ${(totalSec/60).toFixed(1)} min`);
  console.log('==================================================');
  logLine({ summary: true, totalNew, totalSkipped, totalErrored, totalSec });
})().catch(e => { console.error('FATAL:', e); process.exit(1); });
