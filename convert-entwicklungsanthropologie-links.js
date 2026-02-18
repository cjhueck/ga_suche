const fs = require('fs');
const path = require('path');

// Pfad zum Entwicklungsanthropologie Vault
const vaultPath = 'C:\\Users\\chuec\\OneDrive\\Obsidian\\Obsidian Entwicklungsanthropologie';

// Regex für die alten Links aus dem Entwicklungsanthropologie Vault
// Format: [GA 307, S. 85, 09.08.1923](https://akanthosakademie...)
// oder: [GA 304a, S. 110, 14.11.1923](https://akanthosakademie...)
const oldLinkPattern = /\[GA\s*(\d+[a-z]?),\s*S\.\s*(\d+)(?:[-–]\d+)?,\s*(\d{2})\.(\d{2})\.(\d{4})\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]*\)/g;

let totalFiles = 0;
let totalConverted = 0;
let filesChanged = 0;

function extractFirstWords(textBefore, count = 5) {
    // Finde den Anfang des aktuellen Absatzes (nach dem letzten \n\n oder Anfang der Datei)
    const paragraphStart = Math.max(
        textBefore.lastIndexOf('\n\n'),
        textBefore.lastIndexOf('\n#'),  // Überschrift
        0
    );
    
    // Nimm nur den aktuellen Absatz
    const currentParagraph = textBefore.substring(paragraphStart).trim();
    
    // Bereinige den Text: entferne HTML-Tags, Markdown-Links und Formatierung
    let cleanText = currentParagraph
        .replace(/<\/?[^>]+(>|$)/g, '') // HTML-Tags
        .replace(/##+\s*/g, '')         // Markdown-Überschriften
        .replace(/\[\[([^\]]*?\|)?([^\]]*?)\]\]/g, '$2') // [[wikilinks]]
        .replace(/\*\*([^\*]+)\*\*/g, '$1') // **bold**
        .replace(/\*([^\*]+)\*/g, '$1') // *italic*
        .replace(/`([^`]+)`/g, '$1') // `code`
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // existierende Links
        .trim();
    
    // Extrahiere Worte
    const words = cleanText
        .split(/\s+/)
        .map(w => w.replace(/^[,;.:!?()"""''„"‚'»«›‹—–-]+|[,;.:!?()"""''„"‚'»«›‹—–-]+$/g, ''))
        .filter(w => w.length >= 2);
    
    const firstWords = words.slice(0, count);
    return firstWords.length >= count ? firstWords.join(' ') : '';
}

function convertLinks(content, filePath) {
    let converted = content;
    let matches = [];
    let match;
    
    // Sammle alle Matches
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
    
    if (matches.length === 0) return null;
    
    // Ersetze von hinten nach vorne
    for (let i = matches.length - 1; i >= 0; i--) {
        const m = matches[i];
        
        // Formatiere Datum: YYYY-MM-DD
        const formattedDate = `${m.year}-${m.month}-${m.day}`;
        
        // Extrahiere die ersten 5 Worte vor dem Link
        const textBefore = content.substring(0, m.index);
        const firstFiveWords = extractFirstWords(textBefore, 5);
        
        // Erstelle die neue URL
        let newUrl = `http://localhost:3003/goto.html#ga=${m.ga}&date=${formattedDate}&page=${m.page}`;
        if (firstFiveWords) {
            newUrl += `&text=${encodeURIComponent(firstFiveWords)}`;
        }
        
        // Füge Vault-Info hinzu
        newUrl += `&vault=${encodeURIComponent('Obsidian Entwicklungsanthropologie')}`;
        
        // Relativer Pfad zur Datei
        const relativePath = path.relative(vaultPath, filePath).replace(/\\/g, '/');
        newUrl += `&file=${encodeURIComponent(relativePath)}`;
        
        // Erstelle den neuen Link mit Semikolon statt Komma vor dem Datum
        const newLink = `[GA ${m.ga}, S. ${m.page}; ${m.day}.${m.month}.${m.year}](${newUrl})`;
        
        // Ersetze
        converted = converted.substring(0, m.index) + newLink + converted.substring(m.index + m.fullMatch.length);
        totalConverted++;
    }
    
    return converted;
}

function processFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        const converted = convertLinks(content, filePath);
        
        if (converted && converted !== content) {
            // Erstelle Backup
            fs.writeFileSync(filePath + '.backup', content, 'utf8');
            
            // Schreibe konvertierte Datei
            fs.writeFileSync(filePath, converted, 'utf8');
            
            filesChanged++;
            console.log(`✓ Konvertiert: ${path.relative(vaultPath, filePath)}`);
            return true;
        }
        return false;
    } catch (err) {
        console.error(`✗ Fehler bei ${filePath}: ${err.message}`);
        return false;
    }
}

function walkDirectory(dir) {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
            // Überspringe .obsidian und andere versteckte Ordner
            if (!file.startsWith('.')) {
                walkDirectory(fullPath);
            }
        } else if (file.endsWith('.md')) {
            totalFiles++;
            processFile(fullPath);
        }
    }
}

console.log('Starte Konvertierung der Links im Vault Entwicklungsanthropologie...\n');
console.log(`Vault-Pfad: ${vaultPath}\n`);

if (!fs.existsSync(vaultPath)) {
    console.error(`Fehler: Vault-Pfad existiert nicht: ${vaultPath}`);
    process.exit(1);
}

walkDirectory(vaultPath);

console.log('\n=== Zusammenfassung ===');
console.log(`Durchsuchte Dateien: ${totalFiles}`);
console.log(`Geänderte Dateien: ${filesChanged}`);
console.log(`Konvertierte Links: ${totalConverted}`);
console.log('\nHinweis: Backup-Dateien wurden mit .backup-Endung erstellt.');
