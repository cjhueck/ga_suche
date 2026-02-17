const { Plugin, Notice } = require('obsidian');

module.exports = class GALinkConverterPlugin extends Plugin {
    async onload() {
        console.log('GA Link Converter Plugin geladen');

        // Command: Konvertiere GA-Zitate im aktuellen Dokument
        this.addCommand({
            id: 'convert-ga-citations',
            name: 'Konvertiere GA-Zitate zu Links',
            editorCallback: (editor) => {
                this.convertGACitations(editor);
            }
        });

        // Command: Konvertiere nur die aktuelle Auswahl
        this.addCommand({
            id: 'convert-ga-citations-selection',
            name: 'Konvertiere GA-Zitate in Auswahl zu Links',
            editorCallback: (editor) => {
                this.convertGACitationsInSelection(editor);
            }
        });
    }

    convertGACitations(editor) {
        const content = editor.getValue();
        const file = this.app.workspace.getActiveFile();
        const vault = this.app.vault.getName();
        const converted = this.processText(content, vault, file ? file.path : '');
        
        if (converted !== content) {
            editor.setValue(converted);
            new Notice('GA-Zitate erfolgreich konvertiert!');
        } else {
            new Notice('Keine GA-Zitate gefunden.');
        }
    }

    convertGACitationsInSelection(editor) {
        const selection = editor.getSelection();
        
        if (!selection) {
            new Notice('Bitte Text auswählen.');
            return;
        }

        const file = this.app.workspace.getActiveFile();
        const vault = this.app.vault.getName();
        const converted = this.processText(selection, vault, file ? file.path : '');
        
        if (converted !== selection) {
            editor.replaceSelection(converted);
            new Notice('GA-Zitate in Auswahl konvertiert!');
        } else {
            new Notice('Keine GA-Zitate in Auswahl gefunden.');
        }
    }

    processText(text, vault = '', filePath = '') {
        // Regex-Pattern für GA-Zitate: (GA 110, S. 30; 12.04.1909) oder (GA 110, S. 105–106; 15.04.1909)
        const gaPattern = /\(GA\s*(\d+),\s*S\.\s*(\d+)(?:[-–]\d+)?\s*;\s*(\d{2})\.(\d{2})\.(\d{4})\)/g;
        
        let result = text;
        let match;
        const replacements = [];
        
        // Sammle alle Matches mit ihren Positionen
        while ((match = gaPattern.exec(text)) !== null) {
            const [fullMatch, ga, page, day, month, year] = match;
            const offset = match.index;
            
            // Formatiere das Datum für die URL: YYYY-MM-DD
            const formattedDate = `${year}-${month}-${day}`;
            
            // Extrahiere die ersten 5 Worte vor der GA-Angabe
            const textBefore = text.substring(0, offset);
            const firstFiveWords = this.extractFirstWords(textBefore, 5);
            
            // Erstelle die URL mit den ersten 5 Worten als Suchtext
            let url = `http://localhost:3003/goto.html#ga=${ga}&date=${formattedDate}&page=${page}`;
            if (firstFiveWords) {
                url += `&text=${encodeURIComponent(firstFiveWords)}`;
            }
            // Füge Vault und Datei hinzu für Rücklink
            if (vault) {
                url += `&vault=${encodeURIComponent(vault)}`;
            }
            if (filePath) {
                url += `&file=${encodeURIComponent(filePath)}`;
            }
            
            // Erstelle den Markdown-Link
            const linkText = fullMatch.slice(1, -1); // Entferne ( und )
            const replacement = `([${linkText}](${url}))`;
            
            replacements.push({
                start: offset,
                end: offset + fullMatch.length,
                replacement: replacement
            });
        }
        
        // Ersetze von hinten nach vorne, um Indizes nicht zu verschieben
        for (let i = replacements.length - 1; i >= 0; i--) {
            const r = replacements[i];
            result = result.substring(0, r.start) + r.replacement + result.substring(r.end);
        }
        
        return result;
    }

    extractFirstWords(text, count = 5) {
        // Finde den Text nach der letzten H1-Überschrift (# ...)
        // Die Struktur ist: # Überschrift\n\nErster Satz... (GA ...)
        
        const lines = text.split('\n');
        let lastH1Index = -1;
        
        // Finde die letzte H1-Überschrift
        for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.startsWith('# ') && !line.startsWith('## ')) {
                lastH1Index = i;
                break;
            }
        }
        
        if (lastH1Index === -1) {
            // Keine H1 gefunden, nutze den ganzen Text
            return this.extractWordsFromText(text, count);
        }
        
        // Nimm alle Zeilen nach der H1
        const afterH1 = lines.slice(lastH1Index + 1).join('\n');
        
        return this.extractWordsFromText(afterH1, count);
    }
    
    extractWordsFromText(text, count = 5) {
        // Bereinige den Text: entferne Markdown-Links [[...]] und Formatierung
        let cleanText = text
            .replace(/\[\[([^\]]*?\|)?([^\]]*?)\]\]/g, '$2') // Entferne [[wikilinks]]
            .replace(/\*\*([^\*]+)\*\*/g, '$1') // Entferne **bold**
            .replace(/\*([^\*]+)\*/g, '$1') // Entferne *italic*
            .replace(/`([^`]+)`/g, '$1') // Entferne `code`
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Entferne bereits existierende Links
            .trim();
        
        // Extrahiere alle Worte
        const words = cleanText
            .split(/\s+/)
            .map(w => w.replace(/^[,;.:!?()"""''„"‚'»«›‹—–-]+|[,;.:!?()"""''„"‚'»«›‹—–-]+$/g, '')) // Entferne Satzzeichen am Anfang/Ende
            .filter(w => w.length >= 2); // Nur Worte mit mind. 2 Zeichen
        
        // Nimm die ersten N Worte
        const firstWords = words.slice(0, count);
        
        return firstWords.length >= count ? firstWords.join(' ') : '';
    }

    onunload() {
        console.log('GA Link Converter Plugin entladen');
    }
};
