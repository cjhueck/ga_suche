/*
 * Bereinigt fehlerhaft in BILD-DATEINAMEN eingefuegte Seitenmarker (|NNN|).
 *
 * Hintergrund: Bei einem process_pagebreaks-Lauf sind Seitenmarker der Form |NNN|
 * teils MITTEN in die src/alt-Attribute von <img>-Tags geraten, z.B.
 *   <img src="assets/GA350-...Wi|139|e kommt...img-14.png" ...>
 * Dadurch zeigt die Datei weder lokal noch online (R2) an, weil der Dateiname
 * nicht mehr existiert.
 *
 * Dieses Skript entfernt |NNN| AUSSCHLIESSLICH INNERHALB von <img ...>-Tags.
 * Die legitimen Seitenmarker im Fliesstext (z.B. |25|) bleiben unberuehrt.
 *
 * Arbeitet byte-schonend direkt auf dem Rohtext (kein JSON-Reserialize),
 * damit Formatierung/Encoding erhalten bleiben.
 *
 * Verwendung:
 *   node tools/fix-image-src-pagemarkers.js            # nur BERICHT (Dry-Run)
 *   node tools/fix-image-src-pagemarkers.js --write     # aendert Dateien (mit Backup)
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const CONTENT_DIRS = [
  path.join(ROOT, 'steiner-full-lectures'),
  path.join(ROOT, 'steiner-books')
];

const DO_WRITE = process.argv.includes('--write');

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const BACKUP_DIR = path.join(ROOT, 'backups', `image-src-fix-${ts}`);

const IMG_TAG_RE = /<img\b[^>]*>/g;
const MARKER_RE = /\|\d+\|/g;

function processText(raw) {
  let removed = 0;
  const examples = [];
  const out = raw.replace(IMG_TAG_RE, (tag) => {
    if (tag.indexOf('|') === -1) return tag;
    const cleaned = tag.replace(MARKER_RE, (m) => { removed++; return ''; });
    if (cleaned !== tag && examples.length < 3) {
      examples.push(tag.slice(0, 160));
    }
    return cleaned;
  });
  return { out, removed, examples };
}

function main() {
  console.log(`Modus: ${DO_WRITE ? 'SCHREIBEN (mit Backup)' : 'BERICHT (Dry-Run)'}\n`);

  let totalFiles = 0, changedFiles = 0, totalRemoved = 0;
  const allExamples = [];

  for (const dir of CONTENT_DIRS) {
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
    for (const fname of files) {
      const full = path.join(dir, fname);
      let raw;
      try { raw = fs.readFileSync(full, 'utf8'); }
      catch (e) { console.warn(`  [WARN] ${fname} nicht lesbar: ${e.message}`); continue; }
      totalFiles++;
      if (raw.indexOf('<img') === -1) continue;

      const { out, removed, examples } = processText(raw);
      if (removed === 0) continue;

      changedFiles++;
      totalRemoved += removed;
      console.log(`  ${fname}: ${removed} Marker in <img>-Tags entfernt`);
      examples.forEach(ex => { if (allExamples.length < 12) allExamples.push(ex); });

      if (DO_WRITE) {
        // Backup
        const rel = path.relative(ROOT, full).replace(/[\\/]/g, '__');
        if (!fs.existsSync(BACKUP_DIR)) fs.mkdirSync(BACKUP_DIR, { recursive: true });
        fs.writeFileSync(path.join(BACKUP_DIR, rel), raw, 'utf8');
        // WICHTIG: mtime bewahren. Das Backend dedupliziert Vortrags-Duplikate ueber
        // die mtime (neueste gewinnt). Wuerde das Schreiben die mtime aktualisieren,
        // koennte diese Sammel-Datei ploetzlich andere/aeltere Vortragsversionen
        // ueberschreiben. Daher Original-Zeitstempel nach dem Schreiben wiederherstellen.
        let origStat = null;
        try { origStat = fs.statSync(full); } catch { /* ignore */ }
        // Schreiben (utf8, ohne BOM-Manipulation – Rohtext bleibt sonst unveraendert)
        fs.writeFileSync(full, out, 'utf8');
        if (origStat) {
          try { fs.utimesSync(full, origStat.atime, origStat.mtime); } catch { /* ignore */ }
        }
      }
    }
  }

  console.log(`\n=== ${changedFiles} Datei(en) betroffen, ${totalRemoved} Marker gesamt (von ${totalFiles} JSON-Dateien) ===`);
  if (allExamples.length) {
    console.log('\nBeispiele (vor Bereinigung):');
    allExamples.forEach(ex => console.log('   ' + ex + ' …'));
  }
  if (!DO_WRITE && totalRemoved > 0) {
    console.log('\n(Nur Bericht. Zum Anwenden: node tools/fix-image-src-pagemarkers.js --write)');
  } else if (DO_WRITE && changedFiles > 0) {
    console.log(`\nBackups gespeichert in: ${path.relative(ROOT, BACKUP_DIR)}`);
  }
}

main();
