// Diagnose: Sucht den Wolf-Passus in GA293/13 und prüft, ob die zugehörigen
// Block-IDs in den Embeddings vorhanden sind. Misst dann die Cosine-Similarity
// zwischen einer Beispiel-Anfrage ("menschliche Kopf wird tierisch") und den
// Embeddings dieser Absätze, um zu sehen, ob die Stelle prinzipiell findbar
// wäre — und falls ja, warum die Quote-Suche sie verfehlt.

require('dotenv').config();
const fs = require('fs');
const path = require('path');

const BASE = process.env.GA_BACKEND || 'http://localhost:3003';
const LECTURE_ID = 'GA293/13';
const QUERY = 'Wo sagt Steiner, dass der menschliche Kopf die Tendenz hat, tierisch zu werden?';

(async () => {
  // 1) Hole die Lecture vom Backend (mit aktuellen Block-IDs)
  console.log(`[1] Lade ${LECTURE_ID} vom Backend…`);
  const r = await fetch(`${BASE}/api/lecture-with-summary/GA293/13`);
  if (!r.ok) {
    console.error('Lecture nicht ladbar:', r.status, await r.text());
    process.exit(1);
  }
  const j = await r.json();
  const paragraphs = j.lecture.paragraphs || [];
  console.log(`    ${paragraphs.length} Absätze in der Lecture.`);

  // 2) Finde Absätze mit dem Wolfsgestalt-/Tier-Vokabular
  const needle = /Wolfsgestalt|aussehen wie ein Wolf|aussehen wie ein Lamm|metamorphosieren|tierische Umwelt|über diese tierische/i;
  const hits = [];
  paragraphs.forEach((p, i) => {
    const c = p.content || '';
    if (needle.test(c)) {
      hits.push({ idx: i, index: p.index, content: c });
    }
  });
  console.log(`[2] ${hits.length} Treffer im Volltext der Lecture:`);
  hits.forEach(h => {
    const preview = h.content.replace(/\n+/g, ' ').slice(0, 180);
    console.log(`    [${h.idx}] index="${h.index}"  "${preview}…"`);
  });

  if (hits.length === 0) {
    console.error('Keine Treffer im Volltext — ggf. wurde GA293/13 strukturell anders ausgeliefert.');
    process.exit(2);
  }

  // 3) Lade die GA293-Embeddings, prüfe, ob die Block-IDs darin vorkommen
  const embeddingsFile = path.join(__dirname, 'paragraph-embeddings', 'GA293.json');
  if (!fs.existsSync(embeddingsFile)) {
    console.error('paragraph-embeddings/GA293.json nicht gefunden.');
    process.exit(3);
  }
  const embeddings = JSON.parse(fs.readFileSync(embeddingsFile, 'utf8'));
  console.log(`[3] ${Object.keys(embeddings).length} Embeddings in GA293.json.`);
  const expectedKeys = hits.map(h => `GA293/13:${h.index}`);
  console.log('    Erwartete Embedding-IDs für die Treffer:');
  expectedKeys.forEach(k => {
    console.log(`      ${k}  →  ${embeddings[k] ? 'embedded' : '!!! FEHLT !!!'}`);
  });

  // 4) Erzeuge Query-Embedding direkt über Gemini (gleiches Modell wie der Backend benutzt)
  console.log(`[4] Erzeuge Query-Embedding für: "${QUERY}"`);
  async function createEmbedding(text) {
    const key = process.env.GEMINI_API_KEY;
    if (!key) throw new Error('GEMINI_API_KEY fehlt in .env');
    const r = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=${key}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'models/gemini-embedding-001',
          content: { parts: [{ text: text.substring(0, 10000) }] },
          outputDimensionality: 768
        })
      }
    );
    if (!r.ok) throw new Error(`Gemini API Fehler ${r.status}: ${await r.text()}`);
    const j = await r.json();
    return j.embedding.values;
  }
  const qVec = await createEmbedding(QUERY);

  function cosine(a, b) {
    let dot = 0, na = 0, nb = 0;
    for (let i = 0; i < a.length; i++) { dot += a[i]*b[i]; na += a[i]*a[i]; nb += b[i]*b[i]; }
    return dot / (Math.sqrt(na) * Math.sqrt(nb));
  }

  console.log(`[5] Cosine-Similarities zwischen Query und Treffer-Embeddings:`);
  for (const k of expectedKeys) {
    const e = embeddings[k];
    if (!e || !e.embedding) { console.log(`      ${k}  →  fehlt`); continue; }
    const sim = cosine(qVec, e.embedding);
    console.log(`      ${k}  →  ${sim.toFixed(4)}`);
  }

  // 6) Zum Vergleich: Top-5 ähnlichste Absätze aus GANZ GA293
  console.log(`[6] Top-10 ähnlichste GA293-Absätze zur Query (rein semantisch):`);
  const sims = [];
  for (const [id, rec] of Object.entries(embeddings)) {
    if (!rec || !rec.embedding) continue;
    sims.push({ id, sim: cosine(qVec, rec.embedding) });
  }
  sims.sort((a, b) => b.sim - a.sim);
  for (const s of sims.slice(0, 10)) {
    console.log(`      ${s.id}  →  ${s.sim.toFixed(4)}`);
  }

  // 7) Vergleiche mit /api/thematic-hybrid-search im quote-Modus
  console.log(`[7] Was schickt /api/thematic-hybrid-search im quote-Modus zurück?`);
  const hr = await fetch(`${BASE}/api/thematic-hybrid-search`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: QUERY, limit: 250, thematicMode: 'quote', skipCache: true })
  });
  const hj = await hr.json();
  const sources = hj.sources || [];
  console.log(`    ${sources.length} Quellen zurückgegeben. Top 10 IDs:`);
  sources.slice(0, 10).forEach(s => {
    console.log(`      ${s.ID}:${s.index}  (score=${s.combinedScore?.toFixed?.(4) || s.score?.toFixed?.(4) || '?'})`);
  });
  console.log(`    Enthält die GA293/13-Treffer-IDs?`);
  for (const k of expectedKeys) {
    const [lecId, blockId] = k.split(':');
    const found = sources.find(s => s.ID === lecId && s.index === blockId);
    console.log(`      ${k}  →  ${found ? 'JA, Position ' + (sources.indexOf(found)+1) : 'NEIN'}`);
  }
})().catch(e => { console.error('FEHLER:', e); process.exit(99); });
