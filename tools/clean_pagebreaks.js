/**
 * Bereinigt Seitenzahlen in pagebreaks-Dateien
 * Entfernt Duplikate, nicht-sequenzielle und fremde Seitenzahlen
 */

const fs = require('fs');
const path = require('path');

const pagebreaksDir = path.join(__dirname, '..', 'pagebreaks');

function cleanPageNumbers(paragraphs) {
  // Sammle alle Seitenzahlen mit Position
  const allPages = [];
  let globalPos = 0;
  
  for (let paraIdx = 0; paraIdx < paragraphs.length; paraIdx++) {
    const paragraph = paragraphs[paraIdx];
    const content = paragraph.content || paragraph.text || '';
    if (!content) {
      globalPos += 1;
      continue;
    }
    
    const regex = /\|<?(\d+)>?\|/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
      allPages.push({
        page: parseInt(match[1]),
        paraIdx: paraIdx,
        matchIndex: match.index,
        matchLength: match[0].length,
        globalPos: globalPos + match.index
      });
    }
    globalPos += content.length + 1;
  }
  
  if (allPages.length === 0) return { removed: 0, log: [] };
  
  // Finde den Hauptbereich (größte streng aufeinanderfolgende Gruppe)
  const sortedPages = [...allPages].sort((a, b) => a.page - b.page);
  
  let bestStart = 0, bestEnd = 0, bestCount = 0;
  let currentStart = 0, currentCount = 1;
  
  for (let i = 1; i < sortedPages.length; i++) {
    const diff = sortedPages[i].page - sortedPages[i - 1].page;
    if (diff <= 2) { // Erlaubt 1 fehlende Seite
      currentCount++;
    } else {
      if (currentCount > bestCount) {
        bestCount = currentCount;
        bestStart = currentStart;
        bestEnd = i - 1;
      }
      currentStart = i;
      currentCount = 1;
    }
  }
  if (currentCount > bestCount) {
    bestStart = currentStart;
    bestEnd = sortedPages.length - 1;
  }
  
  let expectedMin = sortedPages[bestStart].page;
  let expectedMax = sortedPages[bestEnd].page;
  
  // SICHERHEITSCHECK: Wenn der Hauptbereich weniger als 50% der Seiten umfasst,
  // ist die Bestimmung möglicherweise falsch - sei konservativer
  if (bestCount < allPages.length * 0.5) {
    // Verwende einen weiteren Bereich basierend auf der ersten Seitenzahl
    const firstPage = allPages[0].page;
    expectedMin = Math.min(expectedMin, firstPage);
    expectedMax = Math.max(expectedMax, firstPage + 30); // Typischer Vortrag hat max 30 Seiten
  }
  
  const log = [`Bereich: ${expectedMin}–${expectedMax}`];
  
  // Identifiziere zu entfernende Seitenzahlen
  const toRemove = new Set();
  const seenPages = new Set();
  let lastValidPage = 0;
  
  for (let i = 0; i < allPages.length; i++) {
    const current = allPages[i];
    
    // Bereichs-Check
    if (current.page < expectedMin - 1 || current.page > expectedMax + 1) {
      toRemove.add(i);
      log.push(`Außerhalb: |${current.page}|`);
      continue;
    }
    
    // Duplikat-Check
    if (seenPages.has(current.page)) {
      toRemove.add(i);
      log.push(`Duplikat: |${current.page}|`);
      continue;
    }
    
    // Sequenz-Check
    if (lastValidPage > 0) {
      const diff = current.page - lastValidPage;
      if (diff < -2 || diff > 5) {
        toRemove.add(i);
        log.push(`Sprung: |${current.page}| (nach |${lastValidPage}|)`);
        continue;
      }
    }
    
    seenPages.add(current.page);
    lastValidPage = current.page;
  }
  
  // Entferne markierte Seitenzahlen
  const removeByPara = new Map();
  for (const idx of toRemove) {
    const pageInfo = allPages[idx];
    if (!removeByPara.has(pageInfo.paraIdx)) {
      removeByPara.set(pageInfo.paraIdx, []);
    }
    removeByPara.get(pageInfo.paraIdx).push(pageInfo);
  }
  
  let removedCount = 0;
  for (const [paraIdx, pageInfos] of removeByPara) {
    pageInfos.sort((a, b) => b.matchIndex - a.matchIndex);
    
    let content = paragraphs[paraIdx].content || paragraphs[paraIdx].text || '';
    for (const pageInfo of pageInfos) {
      content = content.substring(0, pageInfo.matchIndex) + 
                content.substring(pageInfo.matchIndex + pageInfo.matchLength);
      removedCount++;
    }
    paragraphs[paraIdx].content = content;
    if (paragraphs[paraIdx].text) {
      paragraphs[paraIdx].text = content;
    }
  }
  
  return { removed: removedCount, log };
}

async function main() {
  const files = fs.readdirSync(pagebreaksDir)
    .filter(f => /^GA\d{3}[a-z]?\.json$/i.test(f));
  
  console.log(`Gefunden: ${files.length} Pagebreak-Dateien`);
  
  let totalFixed = 0;
  
  for (const file of files) {
    const filePath = path.join(pagebreaksDir, file);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    let fileFixed = 0;
    
    if (data.lectures && Array.isArray(data.lectures)) {
      for (const lecture of data.lectures) {
        if (!lecture.paragraphs) continue;
        
        const result = cleanPageNumbers(lecture.paragraphs);
        if (result.removed > 0) {
          console.log(`${lecture.ID || lecture.fileName}: ${result.removed} entfernt`);
          result.log.forEach(l => console.log(`  - ${l}`));
          fileFixed += result.removed;
        }
      }
    }
    
    if (fileFixed > 0) {
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
      console.log(`✓ ${file} gespeichert (${fileFixed} Korrekturen)`);
      totalFixed += fileFixed;
    }
  }
  
  console.log(`\nGesamt: ${totalFixed} Seitenzahlen korrigiert`);
}

main().catch(console.error);

