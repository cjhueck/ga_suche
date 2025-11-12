// fix-json-error.js
const fs = require('fs');

console.log('Repariere keywords-database.json...\n');

// Lese Datei
const content = fs.readFileSync('keywords-database.json', 'utf8');

// Erstelle Backup
const backupName = `keywords-database-backup-before-fix-${Date.now()}.json`;
fs.writeFileSync(backupName, content, 'utf8');
console.log(`✓ Backup erstellt: ${backupName}\n`);

// Fehlerposition ist 3379424
const errorPos = 3379424;

// Zeige was um die Position herum ist
console.log('Vor dem Fehler:');
console.log(content.substring(errorPos - 100, errorPos));
console.log('\nNach dem Fehler:');
console.log(content.substring(errorPos, errorPos + 100));

// Suche nach dem fehlerhaften Pattern
const beforeError = content.substring(0, errorPos);
const afterError = content.substring(errorPos);

// Finde das Ende von "Menschheitsentwicklung" und ersetze bis zum nächsten "
const lastQuote = beforeError.lastIndexOf('"Menschheitsentwicklung"');
if (lastQuote !== -1) {
  console.log('\n✓ Gefunden bei Position:', lastQuote);
  
  // Schneide alles bis zum korrekten Punkt
  const before = content.substring(0, lastQuote + '"Menschheitsentwicklung"'.length);
  
  // Finde die nächste Stelle wo "index" vorkommt nach dem Fehler
  const nextIndex = content.indexOf('"index":', lastQuote + '"Menschheitsentwicklung"'.length);
  if (nextIndex !== -1) {
    const after = content.substring(nextIndex);
    
    // Setze zusammen mit korrektem Komma
    const fixed = before + ',\n        ' + after;
    
    // Teste ob das reparierte JSON gültig ist
    try {
      JSON.parse(fixed);
      console.log('\n✓ Repariertes JSON ist gültig!\n');
      
      // Speichere reparierte Datei
      fs.writeFileSync('keywords-database.json', fixed, 'utf8');
      console.log('✓ keywords-database.json wurde repariert!');
      
    } catch (error) {
      console.error('\n✗ Fehler nach Reparatur:', error.message);
      console.error('Backup wurde NICHT überschrieben.');
    }
  }
}
