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

// Prüfe spezifische Vorträge
const checkLectures = ['GA152/6', 'GA177/2', 'GA195/15', 'GA266c/12'];

for (const lectureId of checkLectures) {
  console.log('\n=== ' + lectureId + ' ===');
  
  // Bilder in DB
  const dbImages = imagesDb[lectureId] || [];
  console.log('Bilder in DB: ' + dbImages.length);
  dbImages.forEach(img => console.log('  DB: ' + img.path));
  
  // Suche im Content
  const lectureFiles = fs.readdirSync(lecturesDir).filter(f => f.endsWith('.json'));
  
  for (const file of lectureFiles) {
    const content = JSON.parse(fs.readFileSync(path.join(lecturesDir, file), 'utf8'));
    const lectures = content.lectures || [];
    
    const lecture = lectures.find(l => l.ID === lectureId);
    if (lecture) {
      console.log('Gefunden in: ' + file);
      
      // Suche nach Bildern im Content
      let foundImages = 0;
      for (const para of (lecture.paragraphs || [])) {
        const paraContent = para.content || '';
        const imgRegex = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi;
        let match;
        while ((match = imgRegex.exec(paraContent)) !== null) {
          const src = match[1];
          console.log('  Content: ' + src);
          foundImages++;
        }
      }
      if (foundImages === 0) {
        console.log('  [KEINE BILDER IM CONTENT GEFUNDEN]');
      }
      break;
    }
  }
}

