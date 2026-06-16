// Sanity-Check: lade GA001-Embeddings, sende eine Probe-Query
// an Gemini-Embedding, berechne Cosine-Similarity und zeige Top-Hits.

const fs = require('fs');
require('dotenv').config();

const PROBE_QUERY = "Goethes Metamorphosenlehre überwindet Kants Verbot der Organismus-Erkenntnis durch den intuitiven Verstand";

(async () => {
  // 1. Embeddings laden
  let raw = fs.readFileSync('paragraph-embeddings/GA001.json', 'utf8');
  if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
  const embeddings = JSON.parse(raw);
  const keys = Object.keys(embeddings);
  console.log(`Geladen: ${keys.length} Absatz-Embeddings (${(fs.statSync('paragraph-embeddings/GA001.json').size / 1024 / 1024).toFixed(2)} MB)`);

  // 2. Lectures laden für Content-Lookup
  // GA001 hat eine 568 KB md-Datei, die in Absätze gesplittet wird;
  // den fertigen Absatz-Text holen wir uns über die laufende API.
  const probeBody = JSON.stringify({
    query: PROBE_QUERY,
    limit: 30,
    thematicMode: 'broad',
    gaFilter: 'GA001',
    skipCache: true
  });

  // 3. Query-Embedding über das laufende Backend holen, indem wir den
  //    existierenden createEmbedding-Pfad nutzen — wir rufen direkt
  //    Gemini-API auf, gleiche Pfad wie der Server.
  const geminiKey = process.env.GEMINI_API_KEY;
  if (!geminiKey) { console.error('GEMINI_API_KEY fehlt'); process.exit(1); }

  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=${geminiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'models/gemini-embedding-001',
      content: { parts: [{ text: PROBE_QUERY }] },
      outputDimensionality: 768
    })
  });
  if (!r.ok) { console.error('Query-Embedding fehlgeschlagen:', await r.text()); process.exit(1); }
  const data = await r.json();
  const queryEmb = data.embedding.values;
  console.log(`Query-Embedding: dim=${queryEmb.length}`);

  // 4. Cosine-Similarity berechnen
  function cosine(a, b) {
    let dot = 0, na = 0, nb = 0;
    for (let i = 0; i < a.length; i++) { dot += a[i]*b[i]; na += a[i]*a[i]; nb += b[i]*b[i]; }
    return dot / (Math.sqrt(na) * Math.sqrt(nb));
  }

  const t0 = Date.now();
  const sims = keys.map(k => [k, cosine(queryEmb, embeddings[k].embedding)]);
  sims.sort((a, b) => b[1] - a[1]);
  const dt = Date.now() - t0;
  console.log(`Similarity über ${keys.length} Vektoren in ${dt} ms`);

  // 5. Inhalte aus der GA001-Markdown-Datei laden, dort sind die Absätze
  //    durch Obsidian-Block-IDs (^xyz) markiert
  const lectureFile = 'Steiner_GA/GA001-Goethes Naturwissenschaftliche Schriften/GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897).md';
  let lectureContent = '';
  try {
    lectureContent = fs.readFileSync(lectureFile, 'utf8');
  } catch (e) { console.warn('Konnte Vortragsdatei nicht laden:', e.message); }

  function findParagraphByBlockId(blockId) {
    // Block-ID am Ende eines Absatzes: ' ^xyz'
    const blockIdMarker = ` ^${blockId.replace(/^\^/, '')}`;
    const pos = lectureContent.indexOf(blockIdMarker);
    if (pos < 0) return null;
    // Suche Absatzanfang (vorherige Doppel-Newline) und Absatzende (Position des Markers)
    let start = lectureContent.lastIndexOf('\n\n', pos);
    if (start < 0) start = 0; else start += 2;
    return lectureContent.substring(start, pos).trim();
  }

  // 6. Top 8 ausgeben
  console.log(`\nTop 8 für: "${PROBE_QUERY}"\n`);
  for (let i = 0; i < 8 && i < sims.length; i++) {
    const [key, sim] = sims[i];
    const idx = key.split(':')[1];
    const content = (findParagraphByBlockId(idx) || '(Absatz nicht im md-File gefunden)')
      .substring(0, 280)
      .replace(/\n+/g, ' ');
    console.log(`${i+1}. sim=${sim.toFixed(3)}  ${key}`);
    console.log(`   ${content}${content.length === 280 ? '…' : ''}`);
    console.log('');
  }
})().catch(e => { console.error(e); process.exit(1); });
