// Tiefere Diagnose: Welche Stufen der Quote-Pipeline filtert die Stelle weg?
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const vectorize = require('./vectorize-client');

const QUERY = 'Wo sagt Steiner, dass der menschliche Kopf die Tendenz hat, tierisch zu werden?';
const TARGET = 'GA293/13:^a1tz1x';

async function createEmbedding(text) {
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=${process.env.GEMINI_API_KEY}`,
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
  if (!r.ok) throw new Error(`Embedding HTTP ${r.status}: ${await r.text()}`);
  const j = await r.json();
  return j.embedding.values;
}

(async () => {
  // 1) Query-Embedding
  const qVec = await createEmbedding(QUERY);

  // 2) Vectorize-Query: Top 100 GLOBAL
  console.log('[1] Vectorize: Top 100 global');
  const vRes = await vectorize.queryNearest(qVec, { topK: 100, returnMetadata: 'none' });
  const matches = vRes.matches || [];
  console.log(`    ${matches.length} Treffer.`);
  console.log(`    Top 10:`);
  matches.slice(0, 10).forEach((m, i) => {
    console.log(`      ${String(i+1).padStart(3)}. ${m.id}  →  ${m.score.toFixed(4)}`);
  });
  const targetRank = matches.findIndex(m => m.id === TARGET);
  console.log(`    Position von ${TARGET}: ${targetRank >= 0 ? `Rang ${targetRank+1}, score=${matches[targetRank].score.toFixed(4)}` : 'NICHT in Top 100'}`);

  // 3) Was sieht das Backend? Trigger einen quote-Hybrid-Search und logge mit
  console.log('\n[2] Backend hybrid-search im quote-Modus, was kommt zurück?');
  const r = await fetch('http://localhost:3003/api/thematic-hybrid-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: QUERY, limit: 250, thematicMode: 'quote', skipCache: true })
  });
  const j = await r.json();
  const sources = j.sources || [];
  console.log(`    ${sources.length} Quellen zurückgegeben.`);
  console.log(`    sourcesPipelineMeta:`, j.pipelineMeta || j.debug || '(keine Meta-Info)');

  const found = sources.find(s => `${s.ID}:${s.index}` === TARGET);
  console.log(`    GA293/13:^a1tz1x in den Quellen? ${found ? `JA, Rang ${sources.indexOf(found)+1}` : 'NEIN'}`);

  // 4) Schaue das LLM-Antwort-Feld an
  console.log('\n[3] LLM-Antwort (gekürzt auf 800 Zeichen):');
  const content = (j.content || j.answer || '').substring(0, 800);
  console.log('    ' + content.replace(/\n/g, '\n    '));
})().catch(e => { console.error('FEHLER:', e); process.exit(1); });
