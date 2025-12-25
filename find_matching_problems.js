const fs = require('fs');
const path = require('path');

// Suche nach Bildern mit Matching-Problemen
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
    imagesDb[img.lectureId].push({
      path: img.path,
      markdownRef: img.markdownRef,
      index: img.index
    });
  }
}

// Normalisiere Pfad für Vergleich
function normalizePath(p) {
  if (!p) return '';
  return p
    .replace(/^<|>$/g, '')
    .replace(/^['"]|['"]$/g, '')
    .trim()
    .toLowerCase()
    .replace(/\\/g, '/');
}

// Extrahiere Dateinamen
function extractFilename(p) {
  if (!p) return '';
  const normalized = normalizePath(p);
  const parts = normalized.split('/');
  return parts[parts.length - 1] || '';
}

// Extrahiere img-X Pattern
function extractImgPattern(p) {
  const match = p.match(/img-(\d+)\.(png|jpg|jpeg|webp)/i);
  return match ? match[0].toLowerCase() : null;
}

// Finde Matching-Probleme
const lectureFiles = fs.readdirSync(lecturesDir).filter(f => f.endsWith('.json'));
const matchingProblems = new Map(); // GA -> Array of problems

for (const file of lectureFiles) {
  const content = JSON.parse(fs.readFileSync(path.join(lecturesDir, file), 'utf8'));
  const lectures = content.lectures || [];
  
  for (const lecture of lectures) {
    const lectureId = lecture.ID;
    const gaNumber = lecture.gaNumber;
    
    // Bilder in der DB für diesen Vortrag
    const dbImages = imagesDb[lectureId] || [];
    
    // Suche nach Bildern im Content
    for (const para of (lecture.paragraphs || [])) {
      const paraContent = para.content || '';
      
      // Suche nach img-Tags
      const imgRegex = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi;
      let match;
      while ((match = imgRegex.exec(paraContent)) !== null) {
        let src = match[1].replace(/^<|>$/g, '').trim();
        
        // Überspringe bereits base64 oder externe URLs
        if (src.startsWith('data:') || src.startsWith('http')) continue;
        
        // Prüfe ob dieses Bild in der DB ist und ob es matchen würde
        const srcNormalized = normalizePath(src);
        const srcFilename = extractFilename(src);
        const srcImgPattern = extractImgPattern(src);
        
        // Versuche verschiedene Matching-Strategien
        let foundMatch = null;
        let matchType = null;
        
        for (const dbImg of dbImages) {
          const dbNormalized = normalizePath(dbImg.path);
          const dbFilename = extractFilename(dbImg.path);
          const dbImgPattern = extractImgPattern(dbImg.path);
          
          // Exaktes Match
          if (srcNormalized === dbNormalized) {
            foundMatch = dbImg;
            matchType = 'exact';
            break;
          }
          
          // Dateiname Match
          if (srcFilename === dbFilename) {
            foundMatch = dbImg;
            matchType = 'filename';
            break;
          }
          
          // img-X Pattern Match
          if (srcImgPattern && dbImgPattern && srcImgPattern === dbImgPattern) {
            foundMatch = dbImg;
            matchType = 'img-pattern';
            break;
          }
        }
        
        // Problem: Bild im Content aber kein Match in DB
        if (!foundMatch && dbImages.length > 0) {
          // Es gibt Bilder in der DB, aber keines matcht
          if (!matchingProblems.has(gaNumber)) {
            matchingProblems.set(gaNumber, []);
          }
          matchingProblems.get(gaNumber).push({
            lectureId,
            srcInContent: src,
            dbPaths: dbImages.map(i => i.path).slice(0, 3) // Erste 3 DB-Pfade
          });
        }
        
        // Problem: Bild im Content, keine Bilder in DB für diesen Vortrag
        if (dbImages.length === 0 && (src.startsWith('assets/') || src.includes('img-') || src.includes('page_'))) {
          if (!matchingProblems.has(gaNumber)) {
            matchingProblems.set(gaNumber, []);
          }
          matchingProblems.get(gaNumber).push({
            lectureId,
            srcInContent: src,
            dbPaths: ['[KEINE BILDER IN DB FÜR DIESEN VORTRAG]']
          });
        }
      }
    }
  }
}

// Ausgabe
console.log('GA-Bände mit Bild-Anzeigeproblemen (Matching-Probleme):');
console.log('========================================================');
const sorted = [...matchingProblems.entries()].sort((a, b) => a[0].localeCompare(b[0]));

for (const [ga, problems] of sorted) {
  // Gruppiere nach Lecture
  const byLecture = new Map();
  for (const p of problems) {
    if (!byLecture.has(p.lectureId)) {
      byLecture.set(p.lectureId, []);
    }
    byLecture.get(p.lectureId).push(p);
  }
  
  console.log(`\n${ga}: ${problems.length} Probleme in ${byLecture.size} Vorträgen`);
  
  // Zeige erste 3 Vorträge
  let count = 0;
  for (const [lectureId, lectureProblems] of byLecture) {
    if (count >= 3) {
      console.log(`  ... und ${byLecture.size - 3} weitere Vorträge`);
      break;
    }
    console.log(`  ${lectureId}:`);
    for (const p of lectureProblems.slice(0, 2)) {
      console.log(`    Content: ${p.srcInContent}`);
      console.log(`    DB:      ${p.dbPaths[0] || 'N/A'}`);
    }
    if (lectureProblems.length > 2) {
      console.log(`    ... und ${lectureProblems.length - 2} weitere Bilder`);
    }
    count++;
  }
}

console.log('\n========================================================');
console.log('Befehl zum Neu-Export:');
const gaList = sorted.map(([ga]) => ga).join(' ');
console.log(`python export_master.py ${gaList}`);

