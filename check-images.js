/**
 * Script zum Prüfen, welche GA-Bände Bilder in der Datenbank haben
 * 
 * Verwendung:
 *   node check-images.js
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

async function checkImages() {
  console.log('\n=== Bilder-Datenbank-Prüfung ===\n');
  
  try {
    // Lade Part-Dateien
    const imagesDir = path.join(__dirname, 'steiner-images');
    const files = await fs.readdir(imagesDir);
    const partFiles = files
      .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
      .sort();
    
    console.log(`Gefunden: ${partFiles.length} Part-Dateien\n`);
    
    // Sammle alle lectureIds
    const lectureIdsWithImages = new Set();
    const gaBandsWithImages = new Set();
    let totalImages = 0;
    
    for (const partFile of partFiles) {
      const partPath = path.join(imagesDir, partFile);
      const data = await fs.readFile(partPath, 'utf8');
      const partData = JSON.parse(data);
      
      if (Array.isArray(partData)) {
        partData.forEach(img => {
          if (img.lectureId) {
            lectureIdsWithImages.add(img.lectureId);
            
            // Extrahiere GA-Band (z.B. "GA110" aus "GA110/6")
            const gaMatch = img.lectureId.match(/^(GA\d+[a-z]?)/i);
            if (gaMatch) {
              gaBandsWithImages.add(gaMatch[1].toUpperCase());
            }
            
            totalImages++;
          }
        });
      }
    }
    
    console.log(`Statistik:`);
    console.log(`  - Gesamt Bilder: ${totalImages}`);
    console.log(`  - Vorträge mit Bildern: ${lectureIdsWithImages.size}`);
    console.log(`  - GA-Bände mit Bildern: ${gaBandsWithImages.size}\n`);
    
    // Sortiere GA-Bände
    const sortedGABands = Array.from(gaBandsWithImages).sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)[0]);
      const numB = parseInt(b.match(/\d+/)[0]);
      return numA - numB;
    });
    
    console.log('GA-Bände mit Bildern:');
    sortedGABands.forEach(ga => {
      const lecturesInBand = Array.from(lectureIdsWithImages)
        .filter(id => id.startsWith(ga + '/'))
        .sort((a, b) => {
          const numA = parseInt(a.split('/')[1] || '0');
          const numB = parseInt(b.split('/')[1] || '0');
          return numA - numB;
        });
      
      const imageCount = Array.from(lectureIdsWithImages)
        .filter(id => id.startsWith(ga + '/'))
        .length;
      
      console.log(`  ${ga}: ${lecturesInBand.length} Vorträge`);
      console.log(`    ${lecturesInBand.join(', ')}`);
    });
    
    // Prüfe auch, welche GA110 Vorträge Bilder haben
    console.log('\n=== Spezifisch GA110 ===');
    const ga110Lectures = Array.from(lectureIdsWithImages).filter(id => id.startsWith('GA110/'));
    console.log(`GA110 Vorträge mit Bildern: ${ga110Lectures.length}`);
    console.log(ga110Lectures.join(', '));
    
  } catch (error) {
    console.error('Fehler:', error);
  }
}

checkImages();
