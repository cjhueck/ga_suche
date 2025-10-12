const fs = require('fs');
const path = require('path');
const infile = process.argv[2] || path.join(process.cwd(), 'summary-database - Kopie (2).json');
const backup = infile + '.bak.' + Date.now();
console.log('infile', infile);
console.log('backup ->', backup);
fs.copyFileSync(infile, backup);
const txt = fs.readFileSync(infile, 'utf8');
let parsed;
try {
  parsed = JSON.parse(txt);
} catch (e) {
  console.error('PARSE_ERR original file not valid JSON:', e.message);
  process.exit(1);
}
// JSON.parse already keeps the last occurrence for duplicate keys; write cleaned JSON
const out = JSON.stringify(parsed, null, 2);
fs.writeFileSync(infile, out, 'utf8');
console.log('Wrote cleaned file. Keys:', Object.keys(parsed).length);
console.log('Backup saved as', backup);
