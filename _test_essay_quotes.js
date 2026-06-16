// Diagnose: prüft, wie der Backend Essay-Snippets generiert.
// Macht eine Essay-Anfrage, parst die data-quote-text-Attribute aus dem
// HTML-Response und zeigt für jeden Beleg an: wieviele Fragmente, mit
// welchem Text. Erlaubt schnellen Iterationszyklus ohne Browser.

const fs = require('fs');

(async () => {
  const args = process.argv.slice(2);
  const query = args[0] || "Goethes Typus-Begriff: der Typus als flüssige Form des Organischen";
  const gaFilter = args[1] || "GA002";

  console.log(`Query: "${query}"\nFilter: ${gaFilter}\n`);

  const r = await fetch('http://localhost:3003/api/thematic-hybrid-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, gaFilter, thematicMode: 'essay', skipCache: true, limit: 8 })
  });
  const json = await r.json();

  if (!json.content) { console.log('Keine Essay-Antwort'); console.log(json); return; }

  // Parse alle data-quote-text Vorkommen
  const re = /data-quote-text="([^"]+)"/g;
  let m, idx = 0;
  const allFragments = [];
  while ((m = re.exec(json.content)) !== null) {
    idx++;
    const decoded = m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<');
    const fragments = decoded.split('|||');
    allFragments.push({ idx, fragments });
  }

  console.log(`Insgesamt ${allFragments.length} Belege mit data-quote-text:\n`);

  allFragments.forEach(({ idx, fragments }) => {
    console.log(`──── Beleg #${idx} ──── (${fragments.length} Fragmente)`);
    fragments.forEach((f, i) => {
      const trim = f.length > 140 ? f.substring(0, 140) + '…' : f;
      console.log(`  ${i + 1}. [${f.length}ch] "${trim}"`);
    });
    console.log();
  });

  // Statistik: wieviele Belege haben 1, 2, 3+ Fragmente
  const dist = {};
  allFragments.forEach(({ fragments }) => {
    const k = fragments.length >= 4 ? '4+' : String(fragments.length);
    dist[k] = (dist[k] || 0) + 1;
  });
  console.log('Verteilung Fragmente/Beleg:', JSON.stringify(dist));

  // Auch: wieviele Belege enthalten Klammern in einem Fragment (sollte = 0 nach Splitting)
  let withBrackets = 0;
  allFragments.forEach(({ fragments }) => {
    if (fragments.some(f => /\[(?:\.\.\.|…|[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß. ]{0,28})\]/.test(f))) {
      withBrackets++;
    }
  });
  console.log(`Belege mit Klammer-Resten in Fragmenten: ${withBrackets} (sollte 0 sein)`);

  fs.writeFileSync('_essay_test_response.html', json.content, 'utf8');
  console.log('\nVoll-HTML in _essay_test_response.html gespeichert.');
})().catch(e => { console.error(e); process.exit(1); });
