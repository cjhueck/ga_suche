/**
 * Fügt Wandtafelzeichnungen-Paragraphen zu Pagebreak-Override-Dateien hinzu
 * ohne die bestehenden Seitenmarker zu beschädigen.
 */

const fs = require('fs');
const path = require('path');

const projectDir = path.join(__dirname, '..');
const exportDir = path.join(projectDir, 'steiner-full-lectures');
const pagebreakDir = path.join(projectDir, 'pagebreak-books');

// GA-Bände die aktualisiert werden sollen
const gaNumbers = process.argv.slice(2);

if (gaNumbers.length === 0) {
    console.log('Usage: node update_pagebreak_with_wz.js GA191 GA194 ...');
    process.exit(1);
}

console.log(`Aktualisiere Pagebreak-Dateien für: ${gaNumbers.join(', ')}`);

// Lade alle Export-Dateien
const exportFiles = fs.readdirSync(exportDir).filter(f => f.startsWith('steiner-full-lectures-') && f.endsWith('.json'));
const allExportLectures = [];

exportFiles.forEach(file => {
    try {
        const data = JSON.parse(fs.readFileSync(path.join(exportDir, file), 'utf8'));
        if (data.lectures) {
            allExportLectures.push(...data.lectures);
        }
    } catch (e) {
        console.warn(`Fehler beim Laden von ${file}: ${e.message}`);
    }
});

console.log(`${allExportLectures.length} Vorträge aus Export-Dateien geladen`);

// Verarbeite jeden GA-Band
gaNumbers.forEach(ga => {
    const overridePath = path.join(pagebreakDir, `${ga}.json`);
    
    if (!fs.existsSync(overridePath)) {
        console.log(`${ga}: Keine Override-Datei gefunden`);
        return;
    }
    
    const overrideData = JSON.parse(fs.readFileSync(overridePath, 'utf8'));
    let updatedCount = 0;
    
    overrideData.lectures.forEach(overrideLecture => {
        // Finde entsprechenden Export-Vortrag
        const exportLecture = allExportLectures.find(l => l.ID === overrideLecture.ID);
        if (!exportLecture) return;
        
        // Finde WZ-Paragraphen im Export (Index enthält z.B. "ga191t" oder "ga194t")
        const gaLower = ga.toLowerCase();
        const wzParagraphs = exportLecture.paragraphs.filter(p => 
            p.index && p.index.toLowerCase().includes(gaLower + 't')
        );
        
        if (wzParagraphs.length > 0) {
            // Prüfe ob WZ bereits vorhanden
            const hasWZ = overrideLecture.paragraphs.some(p => 
                p.index && p.index.toLowerCase().includes(gaLower + 't')
            );
            
            if (!hasWZ) {
                // Füge WZ am Ende hinzu
                overrideLecture.paragraphs.push(...wzParagraphs);
                updatedCount++;
                console.log(`  + ${overrideLecture.ID}: ${wzParagraphs.length} WZ hinzugefügt`);
            }
        }
    });
    
    if (updatedCount > 0) {
        // Speichere mit gleicher Formatierung (2 Spaces Indent)
        fs.writeFileSync(overridePath, JSON.stringify(overrideData, null, 2), 'utf8');
        console.log(`${ga}: ${updatedCount} Vorträge aktualisiert`);
    } else {
        console.log(`${ga}: Keine Änderungen nötig`);
    }
});

console.log('Fertig!');
