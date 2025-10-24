const fs = require('fs');

const themes = JSON.parse(fs.readFileSync('themes-database.json', 'utf8'));
let total = 0;
Object.values(themes).forEach(t => total += (t.keywords || []).length);

console.log('\n========================================');
console.log('THEMES-DATABASE STATUS');
console.log('========================================');
console.log('Total Keywords:', total);

if (total > 0) {
  console.log('\n✓ BATCH-ZUORDNUNG ERFOLGREICH!\n');
  Object.entries(themes).forEach(([name, data]) => {
    console.log(`${name}: ${data.keywords.length} Keywords`);
  });
} else {
  console.log('\n⏳ Batch läuft noch oder noch nicht gestartet...\n');
}

