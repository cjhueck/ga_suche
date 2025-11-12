// repair-corrupt-json.js
// Repariert die korrupte keywords-database mit 3476 Vorträgen

const fs = require('fs');

console.log('=== REPARATUR DER KORRUPTEN DATEI ===\n');

console.log('1. Lade korrupte Datei...');
let content = fs.readFileSync('keywords-database-CORRUPT-backup.json', 'utf8');
console.log(`   ✓ Geladen (${content.length} Zeichen)\n`);

console.log('2. Suche nach korrupten Stellen...');

// Finde alle Vorkommen von fehlerhaften Mustern
let fixCount = 0;

// Pattern 1: "term"corrupted_chars"index"
const pattern1 = /"([^"]+)"[^\n,{]*?"index":/g;
let match;
let positions = [];

while ((match = pattern1.exec(content)) !== null) {
  // Prüfe ob nach dem Anführungszeichen direkt ein Komma oder newline kommt
  const afterQuote = content.substring(match.index + match[0].length - 8, match.index + match[0].length);
  if (!afterQuote.includes(',')) {
    positions.push({
      index: match.index,
      matched: match[0],
      term: match[1]
    });
  }
}

console.log(`   Gefunden: ${positions.length} potentiell korrupte Stellen\n`);

console.log('3. Repariere korrupte Stellen...');

// Ersetze von hinten nach vorne, damit Positionen stimmen bleiben
for (let i = positions.length - 1; i >= 0; i--) {
  const pos = positions[i];
  const termEnd = content.indexOf(`"${pos.term}"`, pos.index) + pos.term.length + 1;
  const indexStart = content.indexOf('"index":', termEnd);
  
  if (indexStart > termEnd && indexStart - termEnd < 50) {
    // Schneide den korrupten Teil heraus und ersetze mit Komma + Newline
    const before = content.substring(0, termEnd);
    const after = content.substring(indexStart);
    content = before + ',\n        ' + after;
    fixCount++;
    
    if (fixCount % 10 === 0) {
      console.log(`   ${fixCount} Stellen repariert...`);
    }
  }
}

console.log(`   ✓ ${fixCount} Stellen repariert\n`);

console.log('4. Validiere repariertes JSON...');
try {
  const data = JSON.parse(content);
  const count = Object.keys(data).length;
  console.log(`   ✓ JSON ist gültig!`);
  console.log(`   ✓ Enthält ${count} Vorträge\n`);
  
  // Zähle individuelle Keywords
  const uniqueKeywords = new Set();
  let totalKeywords = 0;
  
  Object.values(data).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => {
        if (kw.term) {
          uniqueKeywords.add(kw.term);
          totalKeywords++;
        }
      });
    }
  });
  
  console.log('5. Statistik der reparierten Datei:');
  console.log(`   Vorträge: ${count}`);
  console.log(`   Individuelle Keywords: ${uniqueKeywords.size}`);
  console.log(`   Keyword-Vorkommen gesamt: ${totalKeywords}`);
  console.log(`   Durchschnitt pro Vortrag: ${(totalKeywords / count).toFixed(1)}\n`);
  
  console.log('6. Speichere reparierte Datei...');
  fs.writeFileSync('keywords-database.json', JSON.stringify(data, null, 2), 'utf8');
  console.log('   ✓ Gespeichert als keywords-database.json\n');
  
  console.log('=== REPARATUR ERFOLGREICH ===');
  
} catch (error) {
  console.error('\n✗ FEHLER beim Validieren:', error.message);
  
  // Zeige wo der Fehler ist
  if (error.message.includes('position')) {
    const match = error.message.match(/position (\d+)/);
    if (match) {
      const pos = parseInt(match[1]);
      console.log('\nKontext um Fehlerposition:');
      console.log(content.substring(pos - 100, pos + 100));
    }
  }
  
  process.exit(1);
}

