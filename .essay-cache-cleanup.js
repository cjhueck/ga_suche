const fs = require('fs');
const path = 'thematic-search-database.json';
let raw = fs.readFileSync(path, 'utf8');
if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
const db = JSON.parse(raw);

const before = Object.keys(db).length;
let removed = 0;
let keptDeepBroadQuote = 0;

for (const key of Object.keys(db)) {
  const entry = db[key];
  const c = entry && typeof entry.content === 'string' ? entry.content : '';
  // Essay-Einträge erkennen wir am Markup (essay-beleg / essay-deutung).
  const isEssay = c.includes('class="essay-beleg"') || c.includes('class="essay-deutung"');
  if (isEssay) {
    delete db[key];
    removed++;
  } else {
    keptDeepBroadQuote++;
  }
}

const backupPath = `thematic-search-database.backup-${Date.now()}.json`;
fs.copyFileSync(path, backupPath);
fs.writeFileSync(path, JSON.stringify(db, null, 2), 'utf8');

console.log(`Vorher: ${before} Einträge`);
console.log(`Entfernt (essay-mode): ${removed}`);
console.log(`Erhalten (deep/quote/broad): ${keptDeepBroadQuote}`);
console.log(`Backup: ${backupPath}`);
