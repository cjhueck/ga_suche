// repair-corrupt-json-v2.js
// Robustere Reparatur: Finde und entferne komplett korrupte Keyword-Einträge

const fs = require('fs');

console.log('=== REPARATUR DER KORRUPTEN DATEI (v2) ===\n');

console.log('1. Lade korrupte Datei...');
let content = fs.readFileSync('keywords-database-CORRUPT-backup.json', 'utf8');
console.log(`   ✓ Geladen (${content.length} Zeichen)\n`);

console.log('2. Versuche direkte Reparatur der bekannten Fehler...');

// Ersetze die bekannte korrupte Stelle
// "Menschheitsentwicklung"[korrupt]"index":
// wird zu:
// "Menschheitsentwicklung",
// [entferne das korrupte keyword-objekt]

let fixed = content;

// Pattern: Finde Keywords ohne "term"-Feld (nur "," vor "index")
// Das sind korrupte Einträge, die wir entfernen
fixed = fixed.replace(/\{\s*,\s*"index":[^}]+\}/g, '');

// Entferne doppelte Kommas die durch Entfernung entstanden sind
fixed = fixed.replace(/,\s*,/g, ',');

// Entferne Kommas vor schließenden Klammern
fixed = fixed.replace(/,(\s*)\]/g, '$1]');

console.log('   ✓ Bekannte Fehler bereinigt\n');

console.log('3. Validiere repariertes JSON...');
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
  
  console.log('4. Statistik der reparierten Datei:');
  console.log(`   Vorträge gesamt: ${count}`);
  console.log(`   Vorträge mit Keywords: ${lecturesWithKeywords}`);
  console.log(`   Individuelle Keywords: ${uniqueKeywords.size} ✓✓✓`);
  console.log(`   Keyword-Vorkommen gesamt: ${totalKeywords}`);
  console.log(`   Durchschnitt pro Vortrag: ${(totalKeywords / lecturesWithKeywords).toFixed(1)}\n`);
  
  if (uniqueKeywords.size < 3000) {
    console.log('   ✓ Keyword-Anzahl ist im erwarteten Bereich!\n');
  } else {
    console.log('   ⚠ WARNUNG: Zu viele individuelle Keywords!\n');
  }
  
  console.log('5. Speichere reparierte Datei...');
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
      console.log(fixed.substring(pos - 150, pos + 150));
    }
  }
  
  process.exit(1);
}

