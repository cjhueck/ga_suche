const fs = require('fs');
const path = require('path');

// Suche in allen JSON-Dateien nach Bildern
const lecturesDir = './steiner-full-lectures';
const imagesDir = './steiner-images';

// Sammle alle Bilder aus der Bilder-Datenbank
const imagesDb = {};
const imageFiles = fs.readdirSync(imagesDir).filter(f => f.endsWith('.json'));
for (const file of imageFiles) {
  const content = JSON.parse(fs.readFileSync(path.join(imagesDir, file), 'utf8'));
  for (const img of content) {
    if (!imagesDb[img.lectureId]) {
      imagesDb[img.lectureId] = [];
    }
    imagesDb[img.lectureId].push(img.path);
  }
}

// Finde Bilder in Vorträgen die nicht in der Datenbank sind
const lectureFiles = fs.readdirSync(lecturesDir).filter(f => f.endsWith('.json'));
const missingImages = new Map(); // GA -> Set of lecture IDs

for (const file of lectureFiles) {
  const content = JSON.parse(fs.readFileSync(path.join(lecturesDir, file), 'utf8'));
  const lectures = content.lectures || [];
  
  for (const lecture of lectures) {
    const lectureId = lecture.ID;
    const gaNumber = lecture.gaNumber;
    
    // Suche nach Bildern im Content
    for (const para of (lecture.paragraphs || [])) {
      const paraContent = para.content || '';
      // Suche nach img-Tags
      const imgMatches = paraContent.match(/<img[^>]+src=["']([^"']+)["'][^>]*>/gi);
      if (imgMatches) {
        for (const match of imgMatches) {
          const srcMatch = match.match(/src=["']([^"']+)["']/i);
          if (srcMatch) {
            let src = srcMatch[1].replace(/^<|>$/g, '');
            // Prüfe ob dieses Bild in der DB ist
            const dbImages = imagesDb[lectureId] || [];
            const srcFilename = src.split('/').pop().toLowerCase();
            const found = dbImages.some(dbPath => {
              const dbFilename = dbPath.split('/').pop().toLowerCase();
              return dbFilename === srcFilename || 
                     dbPath.toLowerCase() === src.toLowerCase();
            });
            
            if (!found && (src.startsWith('assets/') || src.includes('img-') || src.includes('page_'))) {
              if (!missingImages.has(gaNumber)) {
                missingImages.set(gaNumber, new Set());
              }
              missingImages.get(gaNumber).add(lectureId + ': ' + src);
            }
          }
        }
      }
    }
  }
}

// Ausgabe
console.log('GA-Bände mit fehlenden Bildern in der Datenbank:');
console.log('================================================');
const sorted = [...missingImages.entries()].sort((a, b) => a[0].localeCompare(b[0]));
for (const [ga, lectures] of sorted) {
  console.log('\n' + ga + ': ' + lectures.size + ' fehlende Bilder');
  // Zeige erste 5 Beispiele
  const examples = [...lectures].slice(0, 5);
  for (const ex of examples) {
    console.log('  - ' + ex);
  }
  if (lectures.size > 5) {
    console.log('  ... und ' + (lectures.size - 5) + ' weitere');
  }
}
console.log('\n================================================');
console.log('Befehl zum Neu-Export:');
console.log('python export_master.py ' + sorted.map(([ga]) => ga).join(' '));

