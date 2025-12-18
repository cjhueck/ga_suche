/**
 * Splittet steiner-images.json in kleinere Part-Dateien
 * Jede Part-Datei sollte unter 10 MB sein für Git
 */

const fs = require('fs');
const path = require('path');

const SOURCE_FILE = path.join(__dirname, 'steiner-images.json');
const MAX_SIZE_MB = 10; // Max 10 MB pro Part-Datei

async function splitImagesDatabase() {
  console.log('Lade steiner-images.json...');
  
  if (!fs.existsSync(SOURCE_FILE)) {
    console.error('steiner-images.json nicht gefunden!');
    return;
  }
  
  const content = fs.readFileSync(SOURCE_FILE, 'utf-8');
  const data = JSON.parse(content);
  
  const lectureIds = Object.keys(data);
  console.log(`Gefunden: ${lectureIds.length} Vorträge/Bücher mit Bildern`);
  
  // Sortiere nach GA-Nummer
  lectureIds.sort((a, b) => {
    const gaA = a.match(/GA(\d+)/)?.[1] || '0';
    const gaB = b.match(/GA(\d+)/)?.[1] || '0';
    return parseInt(gaA) - parseInt(gaB) || a.localeCompare(b);
  });
  
  let partNumber = 1;
  let currentPart = {};
  let currentSize = 0;
  const maxSizeBytes = MAX_SIZE_MB * 1024 * 1024;
  
  // Lösche alte Part-Dateien
  const existingParts = fs.readdirSync(__dirname)
    .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'));
  
  console.log(`Lösche ${existingParts.length} alte Part-Dateien...`);
  for (const partFile of existingParts) {
    fs.unlinkSync(path.join(__dirname, partFile));
  }
  
  for (const lectureId of lectureIds) {
    const lectureData = data[lectureId];
    const entryJson = JSON.stringify({ [lectureId]: lectureData });
    const entrySize = Buffer.byteLength(entryJson, 'utf-8');
    
    // Wenn diese Entry die Part-Datei zu groß machen würde, speichere und starte neue Part
    if (currentSize + entrySize > maxSizeBytes && Object.keys(currentPart).length > 0) {
      const partFileName = `steiner-images-part${String(partNumber).padStart(2, '0')}.json`;
      fs.writeFileSync(
        path.join(__dirname, partFileName),
        JSON.stringify(currentPart, null, 2)
      );
      console.log(`  Gespeichert: ${partFileName} (${(currentSize / 1024 / 1024).toFixed(2)} MB, ${Object.keys(currentPart).length} Einträge)`);
      
      partNumber++;
      currentPart = {};
      currentSize = 0;
    }
    
    currentPart[lectureId] = lectureData;
    currentSize += entrySize + 2; // +2 für Komma und Newline
  }
  
  // Speichere letzte Part-Datei
  if (Object.keys(currentPart).length > 0) {
    const partFileName = `steiner-images-part${String(partNumber).padStart(2, '0')}.json`;
    fs.writeFileSync(
      path.join(__dirname, partFileName),
      JSON.stringify(currentPart, null, 2)
    );
    console.log(`  Gespeichert: ${partFileName} (${(currentSize / 1024 / 1024).toFixed(2)} MB, ${Object.keys(currentPart).length} Einträge)`);
  }
  
  console.log(`\n✓ Fertig! ${partNumber} Part-Dateien erstellt.`);
  console.log('\nDie steiner-images.json kann jetzt gelöscht oder in .gitignore aufgenommen werden.');
}

splitImagesDatabase().catch(console.error);








