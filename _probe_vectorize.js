// Probe-Query gegen den Vectorize-Index, identisch zur lokalen Probe in
// .essay-emb-probe.js. Ergebnis sollte mit dem lokalen Probe-Lauf vergleichbar sein.
//
// Nutzung:
//   node _probe_vectorize.js
//   node _probe_vectorize.js "andere Anfrage hier"
//   node _probe_vectorize.js --no-filter      # ohne gaBand-Filter
//   node _probe_vectorize.js --topk 5

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const v = require('./vectorize-client');

const DEFAULT_QUERY = "Goethes Metamorphosenlehre überwindet Kants Verbot der Organismus-Erkenntnis durch den intuitiven Verstand";

const args = process.argv.slice(2);
let queryText = null;
let topK = 8;
let useFilter = true;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--no-filter') useFilter = false;
  else if (a === '--topk') { topK = parseInt(args[++i]) || 8; }
  else if (!queryText) queryText = a;
}
if (!queryText) queryText = DEFAULT_QUERY;

async function createGeminiEmbedding(text) {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error('GEMINI_API_KEY fehlt');
  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'models/gemini-embedding-001',
      content: { parts: [{ text }] },
      outputDimensionality: 768
    })
  });
  if (!r.ok) throw new Error(`Gemini embedding fehlgeschlagen: ${await r.text()}`);
  return (await r.json()).embedding.values;
}

function findParagraphByBlockId(lectureContent, blockId) {
  const id = blockId.replace(/^\^/, '');
  const marker = ` ^${id}`;
  const pos = lectureContent.indexOf(marker);
  if (pos < 0) return null;
  let start = lectureContent.lastIndexOf('\n\n', pos);
  if (start < 0) start = 0; else start += 2;
  return lectureContent.substring(start, pos).trim();
}

(async () => {
  if (!v.isConfigured()) { console.error('Vectorize nicht konfiguriert.'); process.exit(1); }

  console.log(`Query: "${queryText}"`);
  console.log(`Index: ${v.getIndexName()}, topK=${topK}, filter=${useFilter ? '{gaBand:"GA001"}' : 'none'}`);

  // 1) Index-Stand
  try {
    const info = await v.getIndexInfo();
    console.log('Index-Stand:', JSON.stringify(info.result || info, null, 2));
  } catch (e) {
    console.warn('  (Index-Info nicht abrufbar):', e.message);
  }

  // 2) Query-Embedding
  const t0 = Date.now();
  const queryEmb = await createGeminiEmbedding(queryText);
  console.log(`Query-Embedding: dim=${queryEmb.length}, in ${Date.now() - t0} ms`);

  // 3) Vectorize-Query
  const t1 = Date.now();
  const result = await v.queryNearest(queryEmb, {
    topK,
    filter: useFilter ? { gaBand: 'GA001' } : null,
    returnMetadata: 'indexed'
  });
  const dt = Date.now() - t1;
  console.log(`Vectorize-Query: ${result.count ?? (result.matches || []).length} Treffer in ${dt} ms`);

  // 4) Inhalte aus md-Datei (wie im lokalen Probe-Skript) holen
  const lectureFile = 'Steiner_GA/GA001-Goethes Naturwissenschaftliche Schriften/GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897).md';
  let lectureContent = '';
  try { lectureContent = fs.readFileSync(lectureFile, 'utf8'); } catch (e) { console.warn('md-Datei nicht ladbar:', e.message); }

  console.log('');
  (result.matches || []).forEach((m, i) => {
    const blockId = m.id.split(':').slice(1).join(':');
    const text = (findParagraphByBlockId(lectureContent, blockId) || '(Absatz nicht im md-File gefunden)')
      .substring(0, 280)
      .replace(/\n+/g, ' ');
    console.log(`${i + 1}. score=${(m.score || 0).toFixed(4)}  id=${m.id}`);
    console.log(`   ${text}${text.length === 280 ? '…' : ''}`);
    console.log('');
  });

  if (!result.matches || result.matches.length === 0) {
    console.warn('!! Keine Treffer. Mögliche Ursachen:');
    console.warn('   - Indexierung noch nicht durch (warte 30–60 s und nochmal probieren)');
    console.warn('   - filter zu eng (probiere --no-filter)');
    console.warn('   - Vektoren wurden nicht hochgespielt (überprüfe vectorCount in info)');
  }
})().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
