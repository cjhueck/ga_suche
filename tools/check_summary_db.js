const fs = require('fs');
const path = require('path');
const fileArg = process.argv[2];
const p = fileArg ? path.resolve(process.cwd(), fileArg) : path.join(__dirname, '..', 'summary-database (2).json');
const s = fs.statSync(p);
const txt = fs.readFileSync(p, 'utf8');
let parsed;
try {
  parsed = JSON.parse(txt);
} catch (e) {
  console.error('PARSE_ERR', e.message);
  process.exit(1);
}
const keys = Object.keys(parsed);
const dupes = [];
const seen = new Set();
const topKeys = [];
const lines = txt.split(/\r?\n/);
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  const m = line.match(/^\s*\"([A-Za-z0-9_\/-]+)\"\s*:\s*\{/);
  if (m) {
    topKeys.push({ key: m[1], line: i + 1 });
    if (seen.has(m[1])) dupes.push({ key: m[1], line: i + 1 });
    else seen.add(m[1]);
  }
}
console.log('PARSE_OK');
console.log('fileSizeBytes', s.size);
console.log('mtime', s.mtime.toISOString());
console.log('topLevelKeys_count', keys.length);
console.log('sampleKeysFirst10', keys.slice(0, 10));
console.log('duplicateTopKeysCount', dupes.length);
if (dupes.length) console.log('duplicatesSample', dupes.slice(0, 20));
// Print last top-level key and first one for quick spot-check
if (topKeys.length) {
  console.log('firstTopKey', topKeys[0]);
  console.log('lastTopKey', topKeys[topKeys.length - 1]);
}
