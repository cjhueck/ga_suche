// Migriert lokale paragraph-embeddings/<GAxxx>.json nach Cloudflare Vectorize.
//
// Nutzung:
//   node _migrate_paragraph_embeddings.js GA001
//   node _migrate_paragraph_embeddings.js GA001 GA002 GA003
//   node _migrate_paragraph_embeddings.js --all
//
// Idempotent: Vectorize-Upsert überschreibt vorhandene Vektoren mit derselben ID.
// IDs sind "<gaBand>:<blockId>" (z.B. "GA001:^4Z6QqW"), passend zum bisherigen Cache-Key.

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const v = require('./vectorize-client');

const PARA_DIR = path.join(__dirname, 'paragraph-embeddings');
const BOOK_TYP_BANDS = new Set([
  // Hier könnten wir Bände kennzeichnen, die als "book" zu taggen sind.
  // Für GA001 wird vereinfacht "lecture" verwendet (paßt zur internen
  // Datenstruktur paragraphsFromLectures).
]);

function readEmbeddingsFile(gaBand) {
  const fp = path.join(PARA_DIR, `${gaBand}.json`);
  if (!fs.existsSync(fp)) return null;
  let raw = fs.readFileSync(fp, 'utf8');
  if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
  return { obj: JSON.parse(raw), size: fs.statSync(fp).size };
}

function buildVectorsForGA(gaBand) {
  const data = readEmbeddingsFile(gaBand);
  if (!data) {
    console.warn(`  ! ${gaBand}: keine Datei in paragraph-embeddings/ gefunden`);
    return [];
  }
  const { obj, size } = data;
  const keys = Object.keys(obj);
  const typ = BOOK_TYP_BANDS.has(gaBand) ? 'book' : 'lecture';

  const vectors = [];
  for (const key of keys) {
    const entry = obj[key];
    if (!entry || !Array.isArray(entry.embedding) || entry.embedding.length !== 768) continue;
    // key Form: "GA001:^abc123"  (manchmal "GA001:abc123" ohne ^)
    const blockId = key.split(':').slice(1).join(':');
    vectors.push({
      id: key,
      values: entry.embedding,
      metadata: {
        gaBand,
        typ,
        blockId
      }
    });
  }
  console.log(`  ${gaBand}: ${vectors.length} Vektoren aus ${keys.length} Einträgen (Datei ${(size / 1024 / 1024).toFixed(2)} MB)`);
  return vectors;
}

async function migrateBand(gaBand) {
  console.log(`\n[${gaBand}]  Lade Embeddings…`);
  const vectors = buildVectorsForGA(gaBand);
  if (vectors.length === 0) return { gaBand, upserted: 0 };

  const t0 = Date.now();
  const result = await v.upsertVectors(vectors, { batchSize: 500 });
  const dt = Date.now() - t0;
  console.log(`  ✓ Upsert ${result.upserted} Vektoren in ${dt} ms (${(result.upserted / (dt/1000)).toFixed(0)}/s)`);
  console.log(`    mutationIds: ${result.mutationIds.length} Batch(es)`);
  return { gaBand, upserted: result.upserted, mutationIds: result.mutationIds };
}

(async () => {
  if (!v.isConfigured()) {
    console.error('FEHLER: Vectorize nicht konfiguriert.');
    process.exit(1);
  }

  let bands = process.argv.slice(2);
  if (bands.includes('--all')) {
    bands = fs.readdirSync(PARA_DIR)
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace(/\.json$/, ''));
  }
  if (bands.length === 0) {
    console.error('Nutzung: node _migrate_paragraph_embeddings.js GA001 [GA002 …]  oder  --all');
    process.exit(1);
  }

  console.log(`[MIGRATE] ${bands.length} Band(s): ${bands.join(', ')}`);
  console.log(`[MIGRATE] Index: ${v.getIndexName()}`);

  let totalUpserted = 0;
  for (const band of bands) {
    try {
      const r = await migrateBand(band);
      totalUpserted += r.upserted;
    } catch (e) {
      console.error(`  ✗ ${band} fehlgeschlagen:`, e.message);
      if (e.body) console.error('    Body:', JSON.stringify(e.body).substring(0, 300));
    }
  }

  console.log(`\n=== MIGRATION FERTIG ===  ${totalUpserted} Vektoren insgesamt hochgespielt.`);
  console.log('Vectorize indexiert asynchron — neue Vektoren werden nach ~10–60 s suchbar.');
})().catch(e => {
  console.error('[MIGRATE] FATAL:', e.message);
  process.exit(1);
});
