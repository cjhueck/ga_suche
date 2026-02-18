const fs = require('fs');
const path = require('path');

// Test-Datei
const testFile = 'C:\\Users\\chuec\\OneDrive\\Obsidian\\Obsidian Entwicklungsanthropologie\\I. Themen\\Denken - Fühlen - Wollen\\Seelische Entwicklung.md';
const vaultPath = 'C:\\Users\\chuec\\OneDrive\\Obsidian\\Obsidian Entwicklungsanthropologie';

// Regex für die alten Links
// Format: [GA 307, S. 85, 09.08.1923](https://akanthosakademie...)
// oder: [GA 304a, S. 110, 14.11.1923](https://akanthosakademie...)
const oldLinkPattern = /\[GA\s*(\d+[a-z]?),\s*S\.\s*(\d+)(?:[-–]\d+)?,\s*(\d{2})\.(\d{2})\.(\d{4})\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]*\)/g;

function extractFirstWords(textBefore, count = 5) {
    // Finde den Anfang des aktuellen Absatzes (nach dem letzten \n\n oder Anfang der Datei)
    const paragraphStart = Math.max(
        textBefore.lastIndexOf('\n\n'),
        textBefore.lastIndexOf('\n#'),  // Überschrift
        0
    );
    
    // Nimm nur den aktuellen Absatz
    const currentParagraph = textBefore.substring(paragraphStart).trim();
    
    let cleanText = currentParagraph
        .replace(/<\/?[^>]+(>|$)/g, '') // Entferne HTML-Tags
        .replace(/##+\s*/g, '')         // Entferne Markdown-Überschriften
        .replace(/\[\[([^\]]*?\|)?([^\]]*?)\]\]/g, '$2')
        .replace(/\*\*([^\*]+)\*\*/g, '$1')
        .replace(/\*([^\*]+)\*/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
        .trim();
    
    const words = cleanText
        .split(/\s+/)
        .map(w => w.replace(/^[,;.:!?()"""''„"‚'»«›‹—–-]+|[,;.:!?()"""''„"‚'»«›‹—–-]+$/g, ''))
        .filter(w => w.length >= 2);
    
    const firstWords = words.slice(0, count);
    return firstWords.length >= count ? firstWords.join(' ') : '';
}

console.log('=== Probe-Konvertierung ===\n');
console.log(`Test-Datei: ${path.basename(testFile)}\n`);

if (!fs.existsSync(testFile)) {
    console.error(`Fehler: Datei existiert nicht: ${testFile}`);
    process.exit(1);
}

const content = fs.readFileSync(testFile, 'utf8');
let matches = [];
let match;

// Sammle alle Matches
oldLinkPattern.lastIndex = 0;
while ((match = oldLinkPattern.exec(content)) !== null) {
    matches.push({
        fullMatch: match[0],
        ga: match[1],
        page: match[2],
        day: match[3],
        month: match[4],
        year: match[5],
        index: match.index
    });
}

console.log(`Gefundene Links: ${matches.length}\n`);

if (matches.length === 0) {
    console.log('Keine Links zum Konvertieren gefunden.');
    process.exit(0);
}

// Zeige die ersten 3 Beispiele
console.log('=== Beispiel-Konvertierungen (erste 3) ===\n');
for (let i = 0; i < Math.min(3, matches.length); i++) {
    const m = matches[i];
    const formattedDate = `${m.year}-${m.month}-${m.day}`;
    const textBefore = content.substring(0, m.index);
    const firstFiveWords = extractFirstWords(textBefore, 5);
    
    let newUrl = `http://localhost:3003/goto.html#ga=${m.ga}&date=${formattedDate}&page=${m.page}`;
    if (firstFiveWords) {
        newUrl += `&text=${encodeURIComponent(firstFiveWords)}`;
    }
    newUrl += `&vault=${encodeURIComponent('Obsidian Entwicklungsanthropologie')}`;
    const relativePath = path.relative(vaultPath, testFile).replace(/\\/g, '/');
    newUrl += `&file=${encodeURIComponent(relativePath)}`;
    
    const newLink = `[GA ${m.ga}, S. ${m.page}; ${m.day}.${m.month}.${m.year}](${newUrl})`;
    
    console.log(`${i + 1}. ALT:`);
    console.log(`   ${m.fullMatch.substring(0, 80)}...`);
    console.log(`\n   NEU:`);
    console.log(`   ${newLink.substring(0, 120)}...`);
    console.log('');
}

console.log('\n=== Soll die Konvertierung durchgeführt werden? ===');
console.log('Wenn ja, führen Sie aus:');
console.log('  node convert-links-test.js --convert\n');

if (process.argv.includes('--convert')) {
    let converted = content;
    
    // Ersetze von hinten nach vorne
    for (let i = matches.length - 1; i >= 0; i--) {
        const m = matches[i];
        const formattedDate = `${m.year}-${m.month}-${m.day}`;
        const textBefore = content.substring(0, m.index);
        const firstFiveWords = extractFirstWords(textBefore, 5);
        
        let newUrl = `http://localhost:3003/goto.html#ga=${m.ga}&date=${formattedDate}&page=${m.page}`;
        if (firstFiveWords) {
            newUrl += `&text=${encodeURIComponent(firstFiveWords)}`;
        }
        newUrl += `&vault=${encodeURIComponent('Obsidian Entwicklungsanthropologie')}`;
        const relativePath = path.relative(vaultPath, testFile).replace(/\\/g, '/');
        newUrl += `&file=${encodeURIComponent(relativePath)}`;
        
        const newLink = `[GA ${m.ga}, S. ${m.page}; ${m.day}.${m.month}.${m.year}](${newUrl})`;
        converted = converted.substring(0, m.index) + newLink + converted.substring(m.index + m.fullMatch.length);
    }
    
    // Erstelle Backup
    fs.writeFileSync(testFile + '.backup', content, 'utf8');
    
    // Schreibe konvertierte Datei
    fs.writeFileSync(testFile, converted, 'utf8');
    
    console.log('\n✓ Konvertierung durchgeführt!');
    console.log(`✓ Backup erstellt: ${path.basename(testFile)}.backup`);
    console.log(`✓ ${matches.length} Links konvertiert`);
}
