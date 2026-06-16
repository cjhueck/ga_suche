let s = require('fs').readFileSync('.essay-test-response.json', 'utf8');
if (s.charCodeAt(0) === 0xFEFF) s = s.slice(1);
const r = JSON.parse(s);
require('fs').writeFileSync('.essay-test-content.md', r.content, 'utf8');
console.log('Content gespeichert. Sources (' + r.sources.length + '):');
r.sources.forEach((src, i) => {
  console.log('  [' + (i + 1) + '] ' + src.ID + ':' + src.index + '  score=' + src.score + '  --  ' + (src.fileName || src.title).substring(0, 80));
});
