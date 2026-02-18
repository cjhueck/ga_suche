const fs = require('fs');
const path = require('path');

const testFile = 'c:\\Users\\chuec\\OneDrive\\Obsidian\\Obsidian Entwicklungsanthropologie\\I. Themen\\Denken - Fühlen - Wollen\\Seelische Entwicklung.md';
const backupFile = testFile + '.backup';
const vaultPath = 'C:\\Users\\chuec\\OneDrive\\Obsidian\\Obsidian Entwicklungsanthropologie';

// Regex
const oldLinkPattern = /\[GA\s*(\d+[a-z]?),\s*S\.\s*(\d+)(?:[-–]\d+)?,\s*(\d{2})\.(\d{2})\.(\d{4})\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]*\)/g;

function extractFirstWords(textBefore, count = 5) {
    const paragraphStart = Math.max(
        textBefore.lastIndexOf('\n\n'),
        textBefore.lastIndexOf('\n#'),
        0
    );
    
    const currentParagraph = textBefore.substring(paragraphStart).trim();
    
    let cleanText = currentParagraph
        .replace(/<\/?[^>]+(>|$)/g, '')
        .replace(/##+\s*/g, '')
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

console.log('=== Rekonvertierung mit korrigierter Logik ===\n');

// 1. Backup wiederherstellen
if (fs.existsSync(backupFile)) {
    console.log('✓ Backup gefunden, stelle wieder her...');
    const backupContent = fs.readFileSync(backupFile, 'utf8');
    fs.writeFileSync(testFile, backupContent, 'utf8');
    console.log('✓ Backup wiederhergestellt\n');
} else {
    console.log('⚠ Kein Backup gefunden, verwende aktuelle Datei\n');
}

// 2. Konvertiere
const content = fs.readFileSync(testFile, 'utf8');
let matches = [];
let match;

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

// Zeige erste 3 Beispiele MIT den extrahierten Worten
console.log('=== Beispiel-Konvertierungen (mit extrahierten Worten) ===\n');
for (let i = 0; i < Math.min(3, matches.length); i++) {
    const m = matches[i];
    const formattedDate = `${m.year}-${m.month}-${m.day}`;
    const textBefore = content.substring(0, m.index);
    const firstFiveWords = extractFirstWords(textBefore, 5);
    
    console.log(`${i + 1}. GA ${m.ga}, Seite ${m.page}, Datum ${m.day}.${m.month}.${m.year}`);
    console.log(`   Extrahierte Worte: "${firstFiveWords}"`);
    console.log(`   Text-Kontext (letzte 80 Zeichen vor Link):`);
    console.log(`   ...${content.substring(Math.max(0, m.index - 80), m.index)}`);
    console.log('');
}

// 3. Führe Konvertierung durch
let converted = content;
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

// Erstelle neues Backup
fs.writeFileSync(testFile + '.backup', content, 'utf8');

// Schreibe konvertierte Datei
fs.writeFileSync(testFile, converted, 'utf8');

console.log('\n✓ Konvertierung durchgeführt!');
console.log(`✓ Neues Backup erstellt: ${path.basename(testFile)}.backup`);
console.log(`✓ ${matches.length} Links konvertiert`);
