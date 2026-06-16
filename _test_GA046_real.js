const fs = require('fs');
const html = fs.readFileSync('_essay_test_response.html', 'utf8');

// Extrahiere alle data-quote-text
const re = /data-id="(GA046\/11)" data-index="(\^?[a-z0-9]+)"[^>]*data-quote-text="([^"]+)"/g;
let m;
let found = 0;
while ((m = re.exec(html)) !== null) {
  found++;
  const decoded = m[3].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'");
  const fragments = decoded.split('|||');
  console.log(`──── ${m[1]}:${m[2]} ──── (${fragments.length} Fragmente)`);
  fragments.forEach((f, i) => {
    let hex = '';
    for (let j = 0; j < Math.min(f.length, 40); j++) {
      const c = f.charCodeAt(j);
      hex += c >= 32 && c <= 126 ? f[j] : `<${c.toString(16)}>`;
    }
    console.log(`  ${i+1}. [${f.length}ch] hex-prefix="${hex}…"`);
    console.log(`     text="${f}"`);
  });
}

// Suche auch GA046/11 mit allgemeineren Pattern
if (found === 0) {
  console.log('Kein data-quote-text gefunden für GA046/11. Zeige relevante Anker:');
  const re2 = /data-id="(GA046\/11)"[^>]+>([^<]+)</g;
  let mm;
  while ((mm = re2.exec(html)) !== null) {
    console.log(`  Anker: ${mm[0].substring(0, 200)}`);
  }
}
