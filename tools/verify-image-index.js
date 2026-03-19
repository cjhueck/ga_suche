/**
 * Vergleicht Index-basierte Suche mit vollständiger Suche
 * um sicherzustellen, dass keine Bilder verloren gehen.
 */
const fs = require('fs');
const path = require('path');

const imagesDir = path.join(__dirname, '..', 'steiner-images');
const indexPath = path.join(imagesDir, 'image-index.json');

async function verify() {
  const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  const partFiles = fs.readdirSync(imagesDir)
    .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
    .sort();

  // Vollständige Suche: baue Referenz-Map
  console.log('Baue Referenz-Map durch Vollsuche...');
  const fullMap = {};
  for (const file of partFiles) {
    const data = JSON.parse(fs.readFileSync(path.join(imagesDir, file), 'utf8'));
    if (Array.isArray(data)) {
      for (const img of data) {
        if (!img.lectureId) continue;
        if (!fullMap[img.lectureId]) fullMap[img.lectureId] = 0;
        fullMap[img.lectureId]++;
      }
    } else {
      for (const [lid, imgs] of Object.entries(data)) {
        const arr = Array.isArray(imgs) ? imgs : [imgs];
        if (!fullMap[lid]) fullMap[lid] = 0;
        fullMap[lid] += arr.length;
      }
    }
  }

  // Vergleiche
  const fullIds = Object.keys(fullMap).sort();
  const indexIds = Object.keys(index).sort();

  console.log(`Vollsuche: ${fullIds.length} Vorträge`);
  console.log(`Index:     ${indexIds.length} Vorträge`);

  let errors = 0;

  // Prüfe ob alle Vollsuche-IDs im Index sind
  for (const lid of fullIds) {
    if (!index[lid]) {
      console.error(`FEHLT im Index: ${lid} (${fullMap[lid]} Bilder)`);
      errors++;
    } else if (index[lid].count !== fullMap[lid]) {
      console.error(`FALSCHE ANZAHL: ${lid} - Index: ${index[lid].count}, Voll: ${fullMap[lid]}`);
      errors++;
    }
  }

  // Prüfe ob Index keine überflüssigen IDs hat
  for (const lid of indexIds) {
    if (!fullMap[lid]) {
      console.error(`IM INDEX ABER NICHT IN DATEN: ${lid}`);
      errors++;
    }
  }

  // Stichprobe: Lade 5 zufällige Vorträge über Index und vergleiche Bildanzahl
  const sampleIds = fullIds.sort(() => Math.random() - 0.5).slice(0, 5);
  console.log('\nStichprobe:');
  for (const lid of sampleIds) {
    const entry = index[lid];
    let indexCount = 0;
    for (const partFile of entry.parts) {
      const data = JSON.parse(fs.readFileSync(path.join(imagesDir, partFile), 'utf8'));
      if (Array.isArray(data)) {
        indexCount += data.filter(img => img.lectureId === lid).length;
      } else if (data[lid]) {
        indexCount += Array.isArray(data[lid]) ? data[lid].length : 1;
      }
    }
    const ok = indexCount === fullMap[lid] ? '✓' : '✗';
    console.log(`  ${ok} ${lid}: Index-Suche=${indexCount}, Vollsuche=${fullMap[lid]}`);
    if (indexCount !== fullMap[lid]) errors++;
  }

  console.log(`\n${errors === 0 ? '✓ VERIFIZIERUNG ERFOLGREICH' : `✗ ${errors} FEHLER GEFUNDEN`}`);
  process.exit(errors > 0 ? 1 : 0);
}

verify().catch(err => { console.error(err); process.exit(1); });
