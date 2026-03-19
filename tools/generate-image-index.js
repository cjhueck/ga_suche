/**
 * Generiert einen Index: lectureId → Part-Datei(en) + Bildanzahl
 * Wird einmalig ausgeführt und bei Änderungen an den Part-Dateien erneut.
 * Output: steiner-images/image-index.json (~50-100 KB statt 700 MB durchsuchen)
 */
const fs = require('fs');
const path = require('path');

const imagesDir = path.join(__dirname, '..', 'steiner-images');
const outputPath = path.join(imagesDir, 'image-index.json');

async function generateIndex() {
  const files = fs.readdirSync(imagesDir)
    .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
    .sort();

  console.log(`Durchsuche ${files.length} Part-Dateien...`);

  // Format: { "GA074/1": { parts: ["steiner-images-part05.json"], count: 3 }, ... }
  const index = {};
  let totalImages = 0;

  for (const file of files) {
    const filePath = path.join(imagesDir, file);
    const raw = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(raw);

    if (Array.isArray(data)) {
      for (const img of data) {
        const lid = img.lectureId;
        if (!lid) continue;
        if (!index[lid]) {
          index[lid] = { parts: [], count: 0 };
        }
        if (!index[lid].parts.includes(file)) {
          index[lid].parts.push(file);
        }
        index[lid].count++;
        totalImages++;
      }
    } else {
      for (const [lid, imgs] of Object.entries(data)) {
        const arr = Array.isArray(imgs) ? imgs : [imgs];
        if (!index[lid]) {
          index[lid] = { parts: [], count: 0 };
        }
        if (!index[lid].parts.includes(file)) {
          index[lid].parts.push(file);
        }
        index[lid].count += arr.length;
        totalImages += arr.length;
      }
    }

    process.stdout.write(`  ${file} verarbeitet\n`);
  }

  const lectureCount = Object.keys(index).length;
  fs.writeFileSync(outputPath, JSON.stringify(index, null, 2), 'utf8');

  const indexSize = fs.statSync(outputPath).size;
  console.log(`\nIndex erstellt: ${outputPath}`);
  console.log(`  ${lectureCount} Vorträge, ${totalImages} Bilder`);
  console.log(`  Index-Größe: ${(indexSize / 1024).toFixed(1)} KB`);
}

generateIndex().catch(err => {
  console.error('Fehler:', err);
  process.exit(1);
});
