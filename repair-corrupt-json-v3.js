// repair-corrupt-json-v3.js
const fs = require('fs');

console.log('=== REPARATUR DER KORRUPTEN DATEI (v3) ===\n');

console.log('1. Lade korrupte Datei...');
let content = fs.readFileSync('keywords-database-CORRUPT-backup.json', 'utf8');
console.log(`   ✓ Geladen (${content.length} Zeichen)\n`);

console.log('2. Entferne korrupte Zeichen...');

// Finde alle non-ASCII Zeichen zwischen Anführungszeichen und "index"
// und ersetze sie durch Komma + Newline
let fixed = content;

// Pattern: "WORT"[non-printable chars]"index":
// Ersetze alles zwischen dem zweiten " und "index" mit ,\n
fixed = fixed.replace(/"([^"]+)"[^\n",{]+?"index":/g, '"$1",\n        "index":');

console.log('   ✓ Korrupte Zeichen entfernt\n');

console.log('3. Bereinige Syntax...');
// Entferne doppelte Kommas
fixed = fixed.replace(/,\s*,/g, ',');
// Entferne Kommas vor schließenden Klammern
fixed = fixed.replace(/,(\s*)\]/g, '$1]');
fixed = fixed.replace(/,(\s*)\}/g, '$1}');

console.log('   ✓ Syntax bereinigt\n');

console.log('4. Validiere repariertes JSON...');
try {
  const data = JSON.parse(fixed);
  const count = Object.keys(data).length;
  console.log(`   ✓ JSON ist gültig!`);
  console.log(`   ✓ Enthält ${count} Vorträge\n`);
  
  // Zähle individuelle Keywords
  const uniqueKeywords = new Set();
  let totalKeywords = 0;
  let lecturesWithKeywords = 0;
  
  Object.values(data).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecturesWithKeywords++;
      lecture.keywords.forEach(kw => {
        if (kw.term) {
          uniqueKeywords.add(kw.term);
          totalKeywords++;
        }
      });
    }
  });
  
  console.log('5. Statistik der reparierten Datei:');
  console.log(`   Vorträge gesamt: ${count}`);
  console.log(`   Vorträge mit Keywords: ${lecturesWithKeywords}`);
  console.log(`   Individuelle Keywords: ${uniqueKeywords.size}`);
  console.log(`   Keyword-Vorkommen gesamt: ${totalKeywords}`);
  console.log(`   Durchschnitt pro Vortrag: ${(totalKeywords / lecturesWithKeywords).toFixed(1)}\n`);
  
  if (uniqueKeywords.size < 3000) {
    console.log('   ✓✓✓ Keyword-Anzahl ist im erwarteten Bereich! ✓✓✓\n');
  } else {
    console.log('   ⚠ WARNUNG: ${uniqueKeywords.size} ist zu viel!\n');
  }
  
  console.log('6. Speichere reparierte Datei...');
  fs.writeFileSync('keywords-database.json', JSON.stringify(data, null, 2), 'utf8');
  console.log('   ✓ Gespeichert als keywords-database.json\n');
  
  console.log('=== REPARATUR ERFOLGREICH ===');
  
} catch (error) {
  console.error('\n✗ FEHLER beim Validieren:', error.message);
  
  if (error.message.includes('position')) {
    const match = error.message.match(/position (\d+)/);
    if (match) {
      const pos = parseInt(match[1]);
      console.log('\nKontext um Fehlerposition:');
      console.log(fixed.substring(Math.max(0, pos - 150), Math.min(fixed.length, pos + 150)));
    }
  }
  
  process.exit(1);
}


