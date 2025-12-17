// Debug Export-Test
const fs = require('fs');
const path = require('path');

const sourceDir = path.join(__dirname, 'Steiner_GA');

// Finde alle Markdown-Dateien rekursiv
function findMarkdownFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      findMarkdownFiles(filePath, fileList);
    } else if (file.endsWith('.md')) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

const allFiles = findMarkdownFiles(sourceDir);
console.log('Gefundene .md Dateien:', allFiles.length);

// Filtere nach GA051-GA054 Vorträgen
const selectedGAs = ['GA051', 'GA052', 'GA053', 'GA054'];
let matchedFiles = 0;
let skippedByFilter = 0;
let noMeta = 0;

for (const filePath of allFiles) {
  const filename = path.basename(filePath);
  
  // Check if it's a lecture file
  const gaMatch = filename.match(/^GA\s*\d{2,3}[a-z]?\s*\(\d+\.\)/);
  if (!gaMatch) continue;
  
  const gaNumber = filename.match(/^GA\s*(\d{2,3}[a-z]?)/i)?.[1]?.toUpperCase();
  
  // GA filter
  if (selectedGAs.length > 0 && (!gaNumber || !selectedGAs.includes(`GA${gaNumber.toLowerCase()}`))) {
    skippedByFilter++;
    continue;
  }
  
  console.log('MATCH:', filename);
  console.log('  gaNumber:', gaNumber);
  console.log('  GA format:', `GA${gaNumber.toLowerCase()}`);
  console.log('  In selectedGAs?', selectedGAs.includes(`GA${gaNumber.toLowerCase()}`));
  matchedFiles++;
}

console.log('');
console.log('Ergebnis:');
console.log('  Passende Dateien:', matchedFiles);
console.log('  Gefiltert (andere GA):', skippedByFilter);






