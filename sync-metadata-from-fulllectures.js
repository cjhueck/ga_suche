/**
 * Synchronisiert Metadaten (date, year, location) aus fullLectures
 * in summary-database.json und keywords-database.json
 * 
 * Usage: node sync-metadata-from-fulllectures.js
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

async function syncMetadata() {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║  Synchronisiere Metadaten aus fullLectures                    ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');
  
  // 1. Lade fullLectures
  console.log('[SYNC] Lade fullLectures...');
  const fullLectures = {};
  const files = [
    'steiner-full-lectures-051-311-part01.json',
    'steiner-full-lectures-051-311-part02.json',
    'steiner-full-lectures-051-311-part03.json',
    'steiner-full-lectures-051-311-part04.json',
    'steiner-full-lectures-051-311-part05.json',
    'steiner-full-lectures-051-311-part06.json',
    'steiner-full-lectures-051-311-part07.json'
  ];
  
  for (const file of files) {
    try {
      const filePath = path.join(__dirname, file);
      const content = await fs.readFile(filePath, 'utf8');
      const data = JSON.parse(content);
      
      // Die Dateien haben "lectures" Array
      if (data.lectures && Array.isArray(data.lectures)) {
        data.lectures.forEach(lecture => {
          if (lecture.ID) {
            fullLectures[lecture.ID] = lecture;
          }
        });
        console.log(`  ✓ ${file}: ${data.lectures.length} Vorträge`);
      }
    } catch (error) {
      console.warn(`  ⚠ ${file}: ${error.message}`);
    }
  }
  
  console.log(`[SYNC] Total fullLectures geladen: ${Object.keys(fullLectures).length}\n`);
  
  // 2. Lade Datenbanken
  console.log('[SYNC] Lade Datenbanken...');
  const keywordsDBPath = path.join(__dirname, 'keywords-database.json');
  const summaryDBPath = path.join(__dirname, 'summary-database.json');
  
  const keywordsDB = JSON.parse(await fs.readFile(keywordsDBPath, 'utf8'));
  const summaryDB = JSON.parse(await fs.readFile(summaryDBPath, 'utf8'));
  
  console.log(`  ✓ keywords-database.json: ${Object.keys(keywordsDB).length} Einträge`);
  console.log(`  ✓ summary-database.json: ${Object.keys(summaryDB).length} Einträge\n`);
  
  // 3. Hilfsfunktion: Extrahiere Datum aus location/fileName
  function extractDateFromString(str) {
    if (!str) return null;
    
    const months = {
      'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
      'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
      'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
    };
    
    const match = str.match(/(\d{1,2})\.\s*([a-zäöüß]+)\s*(\d{4})/i);
    if (!match) return null;
    
    const day = match[1].padStart(2, '0');
    const monthName = match[2].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const month = months[monthName];
    const year = match[3];
    
    if (month) return `${year}-${month}-${day}`;
    return null;
  }
  
  // 4. Synchronisiere keywords-database.json
  console.log('[SYNC] Synchronisiere keywords-database.json...\n');
  let kwUpdated = 0;
  let kwNoFullLecture = 0;
  
  for (const [lectureId, lectureData] of Object.entries(keywordsDB)) {
    const fullLecture = fullLectures[lectureId];
    
    if (!fullLecture) {
      kwNoFullLecture++;
      continue;
    }
    
    // Hole Datum aus fullLecture (mit Fallback auf location/fileName)
    let date = fullLecture.date || fullLecture.dateString || '';
    
    if (!date && (fullLecture.location || fullLecture.fileName)) {
      date = extractDateFromString(fullLecture.location || fullLecture.fileName);
      if (date) {
        console.log(`  [KW] ${lectureId}: Datum aus location/fileName extrahiert: ${date}`);
      }
    }
    
    const year = date ? parseInt(date.substring(0, 4)) : null;
    const location = fullLecture.location || null;
    
    let updated = false;
    
    // Aktualisiere nur wenn unterschiedlich oder leer
    if (lectureData.date !== date) {
      lectureData.date = date;
      updated = true;
    }
    
    if (lectureData.year !== year) {
      lectureData.year = year;
      updated = true;
    }
    
    // Location wird in keywords-database nicht gespeichert, aber wir könnten es hinzufügen
    if (location && !lectureData.location) {
      lectureData.location = location;
      updated = true;
    }
    
    if (updated) {
      console.log(`  ✓ ${lectureId}: date=${date}, year=${year}, location=${location || '(null)'}`);
      kwUpdated++;
    }
  }
  
  console.log(`\n[SYNC] keywords-database.json: ${kwUpdated} Einträge aktualisiert, ${kwNoFullLecture} nicht in fullLectures gefunden\n`);
  
  // 5. Synchronisiere summary-database.json (hat keine date/year Felder, daher nur zur Info)
  console.log('[SYNC] Prüfe summary-database.json...');
  let summaryNoFullLecture = 0;
  
  for (const [lectureId] of Object.entries(summaryDB)) {
    if (!fullLectures[lectureId]) {
      summaryNoFullLecture++;
    }
  }
  
  console.log(`[SYNC] summary-database.json: ${summaryNoFullLecture} Einträge nicht in fullLectures gefunden`);
  console.log('[SYNC] (summary-database.json speichert date/year nicht, daher keine Änderungen)\n');
  
  // 6. Speichere aktualisierte Datenbanken
  if (kwUpdated > 0) {
    console.log('[SYNC] Speichere keywords-database.json...');
    await fs.writeFile(keywordsDBPath, JSON.stringify(keywordsDB, null, 2), 'utf8');
    console.log('[SYNC] ✓ Gespeichert!\n');
  }
  
  // 7. Zusammenfassung
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║  Zusammenfassung                                               ║');
  console.log('╚════════════════════════════════════════════════════════════════╝');
  console.log(`  fullLectures: ${Object.keys(fullLectures).length} Vorträge`);
  console.log(`  keywords-database: ${kwUpdated} aktualisiert`);
  console.log(`  Nicht gefunden: ${kwNoFullLecture} in keywords-DB, ${summaryNoFullLecture} in summary-DB`);
  console.log('\n✅ Synchronisation abgeschlossen!');
}

// Hauptausführung
if (require.main === module) {
  syncMetadata().catch(error => {
    console.error('\n❌ Fehler:', error);
    process.exit(1);
  });
}

module.exports = { syncMetadata };

