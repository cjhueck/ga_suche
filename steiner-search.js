#!/usr/bin/env node
// Semantische Suche über den bestehenden Cloudflare-Vectorize-Index
// "ga-paragraph-embeddings". Query-Embedding via Gemini (embedding-001, 768d),
// nearest-neighbor via Vectorize, Text-Auflösung aus Steiner_GA/<GA###-…>/*.md.
//
// Nutzung:
//   node steiner-search.js "die Grenzen des Erkennens"
//   node steiner-search.js "Freiheit als geistige Tat" --limit 15
//   node steiner-search.js "denken und wahrnehmen" --ga GA004
//   node steiner-search.js "Ich-Erlebnis" --ga-in GA004,GA009,GA010 --typ lecture
//   node steiner-search.js "Wärmeorganismus" --json
//
// Voraussetzungen in .env (bereits vorhanden):
//   GEMINI_API_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, VECTORIZE_INDEX_NAME

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const v = require('./vectorize-client');

const STEINER_DIR = path.join(__dirname, 'Steiner_GA');
const GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent';
const DEFAULT_LIMIT = 10;
const SNIPPET_LEN = 260;

function parseArgs(argv) {
  const opts = { limit: DEFAULT_LIMIT, ga: null, gaIn: null, typ: null, json: false, queryParts: [] };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--limit') opts.limit = parseInt(argv[++i], 10);
    else if (a === '--ga') opts.ga = argv[++i];
    else if (a === '--ga-in') opts.gaIn = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
    else if (a === '--typ') opts.typ = argv[++i];
    else if (a === '--json') opts.json = true;
    else if (a === '--help' || a === '-h') opts.help = true;
    else opts.queryParts.push(a);
  }
  opts.query = opts.queryParts.join(' ').trim();
  return opts;
}

function usage() {
  console.error(`Nutzung: node steiner-search.js "query" [--limit N] [--ga GA004] [--ga-in GA002,GA004] [--typ lecture|book] [--json]`);
}

async function embedQuery(text, apiKey) {
  const body = {
    model: 'models/gemini-embedding-001',
    content: { parts: [{ text: text.substring(0, 8000) }] },
    outputDimensionality: 768
  };
  let lastErr;
  for (let attempt = 0; attempt <= 3; attempt++) {
    const r = await fetch(`${GEMINI_URL}?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (r.ok) {
      const data = await r.json();
      return data.embedding.values;
    }
    const errText = await r.text();
    lastErr = new Error(`Gemini HTTP ${r.status}: ${errText.substring(0, 200)}`);
    if (![429, 500, 502, 503, 504].includes(r.status)) break;
    await new Promise(res => setTimeout(res, 1000 * (2 ** attempt)));
  }
  throw lastErr;
}

function buildFilter(opts) {
  const f = {};
  if (opts.ga) f.gaBand = opts.ga;
  else if (opts.gaIn && opts.gaIn.length) f.gaBand = { $in: opts.gaIn };
  if (opts.typ) f.typ = opts.typ;
  return f;
}

// GA-Band → Liste aller md-Dateipfade im Bandordner (cache).
const bandFilesCache = new Map();
function listMdsForBand(gaBand) {
  if (bandFilesCache.has(gaBand)) return bandFilesCache.get(gaBand);
  const result = [];
  if (!fs.existsSync(STEINER_DIR)) { bandFilesCache.set(gaBand, result); return result; }
  for (const entry of fs.readdirSync(STEINER_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const m = entry.name.match(/^(GA\d+[a-zA-Z]?)/);
    if (!m || m[1] !== gaBand) continue;
    const folderPath = path.join(STEINER_DIR, entry.name);
    const mds = fs.readdirSync(folderPath)
      .filter(f => f.endsWith('.md'))
      .sort((a, b) => {
        // Konventionsdatei "GA### - ..." zuerst probieren, dann Aufsätze.
        const ka = /^GA\d+\s-\s/.test(a) ? 0 : 1;
        const kb = /^GA\d+\s-\s/.test(b) ? 0 : 1;
        return ka - kb || a.localeCompare(b);
      });
    for (const md of mds) result.push(path.join(folderPath, md));
    break;
  }
  bandFilesCache.set(gaBand, result);
  return result;
}

// md-Inhalt (cache).
const mdContentCache = new Map();
function readMd(mdPath) {
  if (mdContentCache.has(mdPath)) return mdContentCache.get(mdPath);
  let content = null;
  try { content = fs.readFileSync(mdPath, 'utf8'); }
  catch { content = null; }
  mdContentCache.set(mdPath, content);
  return content;
}

// Snippet aus md holen: Absatz, dessen letzte Zeile mit "^<blockId>" endet.
// blockId kann mit oder ohne führendes ^ kommen. Sucht in allen md-Dateien
// des Bandordners (viele GA-Bände sind pro Aufsatz gesplittet).
function findSnippet(gaBand, blockId) {
  const files = listMdsForBand(gaBand);
  for (const mdPath of files) {
    const content = readMd(mdPath);
    const snippet = extractSnippetFromContent(content, blockId);
    if (snippet) return { snippet, mdPath };
  }
  return { snippet: null, mdPath: files[0] || null };
}

function extractSnippetFromContent(content, blockId) {
  if (!content) return null;
  const idClean = blockId.replace(/^\^/, '');
  const marker = `^${idClean}`;
  const idxA = content.indexOf(` ${marker}`);
  const idxB = content.indexOf(`\n${marker}`);
  let idx = -1;
  if (idxA >= 0 && idxB >= 0) idx = Math.min(idxA, idxB);
  else if (idxA >= 0) idx = idxA;
  else if (idxB >= 0) idx = idxB;
  else return null;
  // Absatz-Start = letzter Doppel-Newline vor idx.
  let start = content.lastIndexOf('\n\n', idx);
  if (start < 0) start = Math.max(0, idx - SNIPPET_LEN * 3);
  else start += 2;
  const raw = content.substring(start, idx);
  return cleanSnippet(raw);
}

function cleanSnippet(raw) {
  let s = raw
    .replace(/\|\d+\|\s*/g, '')          // |7| Seitennummern raus
    .replace(/^#+\s.*$/gm, '')           // Überschriften-Zeilen raus
    .replace(/\s\^[a-z0-9]{6,10}(?=\s|$)/g, '') // vorherige Block-Marker im Snippet entfernen
    .replace(/\r/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (s.length > SNIPPET_LEN) s = '…' + s.substring(s.length - SNIPPET_LEN);
  return s;
}

function fmtScore(x) {
  if (typeof x !== 'number') return '   -';
  return x.toFixed(4);
}

async function main() {
  const opts = parseArgs(process.argv);
  if (opts.help || !opts.query) { usage(); process.exit(opts.help ? 0 : 1); }

  if (!process.env.GEMINI_API_KEY) {
    console.error('FEHLER: GEMINI_API_KEY fehlt in .env');
    process.exit(1);
  }
  if (!v.isConfigured()) {
    console.error('FEHLER: Vectorize nicht konfiguriert (CLOUDFLARE_ACCOUNT_ID/API_TOKEN in .env prüfen).');
    process.exit(1);
  }

  const filter = buildFilter(opts);
  const t0 = Date.now();
  const vec = await embedQuery(opts.query, process.env.GEMINI_API_KEY);
  const tEmbed = Date.now() - t0;

  const t1 = Date.now();
  const res = await v.queryNearest(vec, {
    topK: Math.min(opts.limit, 100),
    filter: Object.keys(filter).length ? filter : null,
    returnMetadata: 'indexed'
  });
  const tQuery = Date.now() - t1;

  const matches = res.matches || [];
  const results = matches.map((m, i) => {
    const id = m.id || '';
    const gaBand = m.metadata?.gaBand || id.split(':')[0] || '';
    const blockId = m.metadata?.blockId || id.split(':').slice(1).join(':') || '';
    const typ = m.metadata?.typ || '';
    const { snippet, mdPath } = gaBand ? findSnippet(gaBand, blockId) : { snippet: null, mdPath: null };
    return {
      rank: i + 1,
      score: m.score,
      id, gaBand, blockId, typ,
      mdPath,
      snippet: snippet || '(kein Text gefunden — evtl. anderer GA-Suffix oder Datei fehlt)'
    };
  });

  if (opts.json) {
    console.log(JSON.stringify({
      query: opts.query, filter, count: results.length,
      timings: { embedMs: tEmbed, queryMs: tQuery },
      results
    }, null, 2));
    return;
  }

  const filterStr = Object.keys(filter).length ? `  filter=${JSON.stringify(filter)}` : '';
  console.log(`Query: "${opts.query}"${filterStr}`);
  console.log(`Embedding ${tEmbed} ms  •  Vectorize ${tQuery} ms  •  ${results.length} Treffer\n`);
  for (const r of results) {
    console.log(`#${r.rank}  score=${fmtScore(r.score)}  ${r.gaBand}  ^${r.blockId.replace(/^\^/, '')}${r.typ ? `  [${r.typ}]` : ''}`);
    if (r.mdPath) console.log(`    ${path.relative(__dirname, r.mdPath)}`);
    console.log(`    ${r.snippet}\n`);
  }
}

main().catch(e => {
  console.error('FEHLER:', e.message);
  if (e.body) console.error('  Body:', JSON.stringify(e.body).substring(0, 500));
  process.exit(1);
});
