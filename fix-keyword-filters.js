// fix-keyword-filters.js
// Erweitert alle isNewGeneration Filter um 'synced-from-summary-db'

const fs = require('fs');

console.log('Aktualisiere Keyword-Filter in app.html...\n');

let content = fs.readFileSync('app.html', 'utf8');

// Alter Filter-Pattern (ohne synced-from-summary-db)
const oldPattern = /const isNewGeneration = lecture\.generationMethod && \n\s+\(lecture\.generationMethod\.includes\('unified-batch'\) \|\| \n\s+lecture\.generationMethod\.includes\('unified'\) \|\|\n\s+lecture\.generationMethod\.includes\('manual-add'\) \|\|\n\s+lecture\.generationMethod\.includes\('manual'\)\);/g;

// Neuer Filter (mit synced-from-summary-db)
const newPattern = `const isNewGeneration = lecture.generationMethod && 
          (lecture.generationMethod.includes('unified-batch') || 
           lecture.generationMethod.includes('unified') ||
           lecture.generationMethod.includes('manual-add') ||
           lecture.generationMethod.includes('manual') ||
           lecture.generationMethod.includes('synced-from-summary-db'));`;

// Zähle Vorkommen
const matches = content.match(/const isNewGeneration = lecture\.generationMethod/g);
console.log(`Gefunden: ${matches ? matches.length : 0} Filter-Stellen\n`);

// Ersetze mit verschiedenen Whitespace-Toleranz
let count = 0;

// Pattern 1: 2 Spaces Indent
content = content.replace(
  /const isNewGeneration = lecture\.generationMethod && \n        \(lecture\.generationMethod\.includes\('unified-batch'\) \|\| \n         lecture\.generationMethod\.includes\('unified'\) \|\|\n         lecture\.generationMethod\.includes\('manual-add'\) \|\|\n         lecture\.generationMethod\.includes\('manual'\)\);/g,
  () => { count++; return `const isNewGeneration = lecture.generationMethod && 
        (lecture.generationMethod.includes('unified-batch') || 
         lecture.generationMethod.includes('unified') ||
         lecture.generationMethod.includes('manual-add') ||
         lecture.generationMethod.includes('manual') ||
         lecture.generationMethod.includes('synced-from-summary-db'));`; }
);

// Pattern 2: 4 Spaces Indent (für eingerückte Blöcke)
content = content.replace(
  /const isNewGeneration = lecture\.generationMethod && \n            \(lecture\.generationMethod\.includes\('unified-batch'\) \|\| \n             lecture\.generationMethod\.includes\('unified'\) \|\|\n             lecture\.generationMethod\.includes\('manual-add'\) \|\|\n             lecture\.generationMethod\.includes\('manual'\)\);/g,
  () => { count++; return `const isNewGeneration = lecture.generationMethod && 
            (lecture.generationMethod.includes('unified-batch') || 
             lecture.generationMethod.includes('unified') ||
             lecture.generationMethod.includes('manual-add') ||
             lecture.generationMethod.includes('manual') ||
             lecture.generationMethod.includes('synced-from-summary-db'));`; }
);

console.log(`Ersetzt: ${count} Filter-Stellen\n`);

// Speichere
fs.writeFileSync('app.html', content, 'utf8');
console.log('✓ app.html aktualisiert');

