const fs = require('fs');
const path = require('path');

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
    imagesDb[img.lectureId].push(img);
  }
}

// Finde ALLE Bild-Probleme (sowohl Markdown als auch HTML)
const lectureFiles = fs.readdirSync(lecturesDir).filter(f => f.endsWith('.json'));
const problems = new Map(); // GA -> Array of problems

for (const file of lectureFiles) {
  const content = JSON.parse(fs.readFileSync(path.join(lecturesDir, file), 'utf8'));
  const lectures = content.lectures || [];
  
  for (const lecture of lectures) {
    const lectureId = lecture.ID;
    const gaNumber = lecture.gaNumber;
    const dbImages = imagesDb[lectureId] || [];
    
    for (const para of (lecture.paragraphs || [])) {
      const paraContent = para.content || '';
      
      // Pattern 1: Markdown-Bilder ![alt](path) - NICHT konvertiert!
      const mdRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
      let match;
      while ((match = mdRegex.exec(paraContent)) !== null) {
        const src = match[2];
        if (!problems.has(gaNumber)) {
          problems.set(gaNumber, []);
        }
        problems.get(gaNumber).push({
          lectureId,
          type: 'MARKDOWN_NOT_CONVERTED',
          src: src,
          dbCount: dbImages.length
        });
      }
      
      // Pattern 2: HTML img mit assets/ aber keine Base64
      const htmlRegex = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi;
      while ((match = htmlRegex.exec(paraContent)) !== null) {
        const src = match[1];
        // Überspringe bereits base64 oder externe URLs
        if (src.startsWith('data:') || src.startsWith('http')) continue;
        
        // Hat assets/ oder img- Pattern
        if (src.includes('assets/') || src.includes('img-') || src.includes('page_')) {
          if (!problems.has(gaNumber)) {
            problems.set(gaNumber, []);
          }
          problems.get(gaNumber).push({
            lectureId,
            type: 'HTML_NO_BASE64',
            src: src,
            dbCount: dbImages.length
          });
        }
      }
    }
  }
}

// Ausgabe
console.log('GA-Bände mit Bild-Anzeigeproblemen:');
console.log('===================================');

const sorted = [...problems.entries()].sort((a, b) => {
  const numA = parseInt(a[0].replace(/\D/g, ''));
  const numB = parseInt(b[0].replace(/\D/g, ''));
  return numA - numB;
});

for (const [ga, probs] of sorted) {
  // Gruppiere nach Typ
  const byType = {};
  for (const p of probs) {
    if (!byType[p.type]) byType[p.type] = [];
    byType[p.type].push(p);
  }
  
  const mdCount = (byType['MARKDOWN_NOT_CONVERTED'] || []).length;
  const htmlCount = (byType['HTML_NO_BASE64'] || []).length;
  
  // Unique lectures
  const uniqueLectures = new Set(probs.map(p => p.lectureId));
  
  console.log(`\n${ga}: ${probs.length} Probleme in ${uniqueLectures.size} Vorträgen`);
  if (mdCount > 0) console.log(`  - ${mdCount}x Markdown nicht konvertiert`);
  if (htmlCount > 0) console.log(`  - ${htmlCount}x HTML ohne Base64`);
  
  // Zeige Beispiele
  const examples = probs.slice(0, 3);
  for (const ex of examples) {
    console.log(`  ${ex.lectureId}: ${ex.type}`);
    console.log(`    src: ${ex.src.substring(0, 80)}${ex.src.length > 80 ? '...' : ''}`);
  }
}

console.log('\n===================================');
console.log('Befehl zum Neu-Export:');
console.log('python export_master.py ' + sorted.map(([ga]) => ga).join(' '));

