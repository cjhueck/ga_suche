// Frische Paragraph-Embeddings für einen GA-Band erzeugen.
// Nötig nach strukturellen Änderungen (neue Block-IDs, Splits/Merges usw.),
// damit alte Vectorize-Vektoren mit nicht mehr existenten IDs verschwinden.
//
// Aufruf:
//   node _refresh_paragraph_embeddings.js --ga GA032
//   node _refresh_paragraph_embeddings.js --ga GA032 --concurrency 8
//   node _refresh_paragraph_embeddings.js --ga GA032 --skip-delete  (wenn nur Lokales weg & neu)
//
// Schritte:
//   1) Liest IDs aus paragraph-embeddings/<GA>.json
//   2) Löscht diese IDs aus Cloudflare Vectorize (Batches à 1000)
//   3) Verschiebt die alte Cache-Datei nach <GA>.json.bak-<timestamp>
//   4) Triggert /api/reload-lectures, damit der Backend-Cache die neuen
//      Block-IDs sieht (paragraphsFromLectures wird neu aufgebaut)
//   5) Triggert /api/generate-paragraph-embeddings (frische Generierung)
//   6) Pollt /api/paragraph-embeddings-status bis fertig (oder Stagnation)

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const vectorize = require('./vectorize-client');

const BASE = process.env.GA_BACKEND || 'http://localhost:3003';
const POLL_INTERVAL_MS = 5000;
const STAGNATION_TIMEOUT_MS = 180 * 1000;
const DELETE_BATCH_SIZE = 1000;

const args = process.argv.slice(2);
let gaBand = null;
let concurrency = 10;
let skipDelete = false;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--ga') gaBand = args[++i];
  else if (args[i] === '--concurrency') concurrency = parseInt(args[++i]);
  else if (args[i] === '--skip-delete') skipDelete = true;
}
if (!gaBand) {
  console.error('Fehlend: --ga GAxxx');
  process.exit(1);
}
gaBand = gaBand.toUpperCase();

const cachePath = path.join(__dirname, 'paragraph-embeddings', `${gaBand}.json`);

async function step1ReadOldIds() {
  if (!fs.existsSync(cachePath)) {
    console.log(`(1) Keine lokale Cache-Datei: ${cachePath} — überspringe Lösch-Schritte.`);
    return [];
  }
  const json = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
  const ids = Object.keys(json);
  console.log(`(1) ${ids.length} alte IDs aus ${path.basename(cachePath)} gelesen`);
  return ids;
}

async function step2DeleteFromVectorize(ids) {
  if (skipDelete) {
    console.log('(2) --skip-delete: Vectorize bleibt unangetastet');
    return;
  }
  if (!vectorize.isConfigured()) {
    console.warn('(2) Vectorize nicht konfiguriert → keine Vector-Löschung möglich');
    return;
  }
  if (ids.length === 0) {
    console.log('(2) Keine alten IDs → nichts zu löschen');
    return;
  }
  console.log(`(2) Lösche ${ids.length} Vectoren aus Vectorize "${vectorize.getIndexName()}"…`);
  let deleted = 0;
  for (let i = 0; i < ids.length; i += DELETE_BATCH_SIZE) {
    const batch = ids.slice(i, i + DELETE_BATCH_SIZE);
    await vectorize.deleteByIds(batch);
    deleted += batch.length;
    process.stdout.write(`    ${deleted}/${ids.length}\r`);
  }
  console.log(`    ${deleted}/${ids.length} ✓`);
}

async function step3MoveCache() {
  if (!fs.existsSync(cachePath)) return;
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const backupPath = `${cachePath}.bak-${ts}`;
  fs.renameSync(cachePath, backupPath);
  console.log(`(3) Alte Cache-Datei umbenannt → ${path.basename(backupPath)}`);
}

async function step4ReloadLectures() {
  console.log(`(4) Triggere /api/reload-lectures, damit der Backend-Cache die neuen Block-IDs sieht…`);
  const r = await fetch(`${BASE}/api/reload-lectures`, { method: 'POST' });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`reload-lectures HTTP ${r.status}: ${t.substring(0, 300)}`);
  }
  const body = await r.json();
  console.log(`    Geladen: ${body.lecturesLoaded} Vorträge, Absätze neu: ${JSON.stringify(body.paragraphsRebuilt || {})}`);
}

async function step5Generate() {
  console.log(`(5) Triggere neue Embedding-Generierung für ${gaBand}…`);
  const r = await fetch(`${BASE}/api/generate-paragraph-embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gaBand, concurrency, skipExisting: true })
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`HTTP ${r.status}: ${t.substring(0, 300)}`);
  }
  const startResp = await r.json();
  console.log(`    toProcess=${startResp.toProcess}, totalCandidates=${startResp.totalCandidates}`);
  return startResp;
}

async function step6Poll(startResp) {
  const expectedTotal = (startResp.existing || 0) + (startResp.toProcess || 0);
  if (expectedTotal === 0) {
    console.log('(6) Nichts zu tun.');
    return;
  }
  let lastEmbedded = -1;
  let stagnationStart = null;
  const t0 = Date.now();
  console.log(`(6) Poll bis ${expectedTotal} Embeddings vorhanden…`);
  while (true) {
    const r = await fetch(`${BASE}/api/paragraph-embeddings-status?gaBand=${gaBand}`);
    if (!r.ok) {
      await new Promise(res => setTimeout(res, POLL_INTERVAL_MS));
      continue;
    }
    const s = await r.json();
    const elapsed = Math.round((Date.now() - t0) / 1000);
    process.stdout.write(`    ${s.embedded}/${expectedTotal} (${elapsed}s)\r`);
    if (s.embedded >= expectedTotal) {
      console.log(`\n    ✓ fertig nach ${elapsed}s`);
      return;
    }
    if (s.embedded === lastEmbedded) {
      if (!stagnationStart) stagnationStart = Date.now();
      else if (Date.now() - stagnationStart > STAGNATION_TIMEOUT_MS) {
        console.log(`\n    ⚠ Stagnation: ${s.embedded}/${expectedTotal} — Backend läuft im Hintergrund weiter.`);
        return;
      }
    } else {
      stagnationStart = null;
    }
    lastEmbedded = s.embedded;
    await new Promise(res => setTimeout(res, POLL_INTERVAL_MS));
  }
}

(async () => {
  console.log(`==================================================`);
  console.log(` Refresh paragraph embeddings — ${gaBand}`);
  console.log(` Backend: ${BASE}`);
  console.log(` skipDelete: ${skipDelete}`);
  console.log(`==================================================`);
  const oldIds = await step1ReadOldIds();
  await step2DeleteFromVectorize(oldIds);
  await step3MoveCache();
  await step4ReloadLectures();
  const startResp = await step5Generate();
  await step6Poll(startResp);
  console.log(`\nFertig. Backup der alten Cache-Datei liegt im paragraph-embeddings/-Ordner.`);
})().catch(e => { console.error('FEHLER:', e.message); process.exit(1); });
