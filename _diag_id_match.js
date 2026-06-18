// Prüft, ob die in GA293.json (Embeddings) verwendeten Block-IDs auch in
// paragraphsFromLectures (in-memory im Backend) zu finden sind. Wenn nicht,
// wird die Quote-Suche jeden semantischen Treffer aus Vectorize stillschweigend
// verwerfen (siehe backend.js, Zeile ~11491: "if (!para) continue").

const fs = require('fs');
const path = require('path');

(async () => {
  // 1) IDs aus dem Embedding-Cache lesen
  const cache = JSON.parse(
    fs.readFileSync(path.join(__dirname, 'paragraph-embeddings', 'GA293.json'), 'utf8')
  );
  const embeddingKeys = Object.keys(cache);
  console.log(`Embeddings in GA293.json: ${embeddingKeys.length}`);

  // 2) Backend nach allen GA293-Vorträgen fragen, alle Block-IDs einsammeln
  //    (über mehrere Lectures: GA293/1 .. GA293/14)
  const allLectureIds = new Set();
  for (const k of embeddingKeys) {
    const colon = k.lastIndexOf(':');
    allLectureIds.add(k.substring(0, colon));
  }
  console.log(`Distinct Lecture-IDs in den Embedding-Keys: ${allLectureIds.size}`);
  console.log(`  Beispiele:`, [...allLectureIds].slice(0, 5));

  // 3) Für jede Lecture die aktuellen Block-IDs vom Backend holen
  const allBackendKeys = new Set();
  for (const lectureId of allLectureIds) {
    const [ga, num] = lectureId.split('/');
    const r = await fetch(`http://localhost:3003/api/lecture-with-summary/${ga}/${num}`);
    if (!r.ok) { console.warn(`  ${lectureId}: HTTP ${r.status}`); continue; }
    const j = await r.json();
    (j.lecture.paragraphs || []).forEach(p => {
      if (p.index) allBackendKeys.add(`${lectureId}:${p.index}`);
    });
  }
  console.log(`Distinct Block-IDs vom Backend (alle GA293-Vorträge): ${allBackendKeys.size}`);

  // 4) Diff
  const onlyInEmbeddings = embeddingKeys.filter(k => !allBackendKeys.has(k));
  const onlyInBackend = [...allBackendKeys].filter(k => !cache[k]);
  console.log(`\nNur in Embedding-Cache (nicht in aktuellen Vorträgen): ${onlyInEmbeddings.length}`);
  console.log(`  Beispiele:`, onlyInEmbeddings.slice(0, 5));
  console.log(`Nur im Backend (kein Embedding): ${onlyInBackend.length}`);
  console.log(`  Beispiele:`, onlyInBackend.slice(0, 5));

  // 5) Speziell für unsere Zielstelle prüfen
  const TARGET = 'GA293/13:^a1tz1x';
  console.log(`\nZielstelle ${TARGET}:`);
  console.log(`  in Embedding-Cache:        ${cache[TARGET] ? 'JA' : 'NEIN'}`);
  console.log(`  in paragraphsFromLectures: ${allBackendKeys.has(TARGET) ? 'JA' : 'NEIN'}`);
})().catch(e => { console.error(e); process.exit(1); });
