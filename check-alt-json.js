// check-alt-json.js
const fs = require('fs');

try {
  console.log('Prüfe keywords-database (alt).json...\n');
  const content = fs.readFileSync('keywords-database (alt).json', 'utf8');
  
  const data = JSON.parse(content);
  console.log(`✓ JSON ist gültig!`);
  console.log(`✓ Enthält ${Object.keys(data).length} Vorträge`);
  
  // Zeige ersten Eintrag
  const firstKey = Object.keys(data)[0];
  console.log(`\nBeispiel-Eintrag (${firstKey}):`);
  console.log(JSON.stringify(data[firstKey], null, 2).substring(0, 500) + '...');
  
} catch (error) {
  console.error('✗ Fehler:', error.message);
}


