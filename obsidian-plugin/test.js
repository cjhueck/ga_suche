// Test-Skript für die extractFirstThreeWords Funktion

class TestPlugin {
    extractFirstThreeWords(text) {
        const lines = text.split('\n');
        let lastH1Index = -1;
        
        for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.startsWith('# ') && !line.startsWith('## ')) {
                lastH1Index = i;
                break;
            }
        }
        
        if (lastH1Index === -1) {
            return this.extractWordsFromText(text);
        }
        
        const afterH1 = lines.slice(lastH1Index + 1).join('\n');
        
        return this.extractWordsFromText(afterH1);
    }
    
    extractWordsFromText(text) {
        let cleanText = text
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
        
        const firstThree = words.slice(0, 3);
        
        return firstThree.length >= 3 ? firstThree.join(' ') : '';
    }
}

const plugin = new TestPlugin();

// Test 1: "Nun habe ich" Zitat
const text1 = `# Erst die geistige Beobachtung, dann die Systematik. GA 110 18.04.1909

Nun habe ich schon gestern betont - das bitte ich immer zu berücksichtigen -, daß hier nicht aus irgendeiner Spekulation, aus einem Schema heraus charakterisiert wird, sondern aus den wirklichen Tatsachen heraus, die man die Tatsachen der Akasha-Chronik nennt; und daher können sich diese Tatsachen erst nachträglich zu einer Art von Systematik zusammenschließen. (GA 110, S. 140; 18.04.1909)`;
const beforeGA1 = text1.substring(0, text1.lastIndexOf('(GA'));
const result1 = plugin.extractFirstThreeWords(beforeGA1);
console.log('Test 1:');
console.log('  Ergebnis:', result1);
console.log('  Erwartet: "Nun habe ich"');
console.log('');

// Test 2: "Alles was materiell"
const text2 = `# Materielles ist Hülle geistiger Wesenheiten. GA 110 12.04.1909

Alles, was materiell geschieht, ist ja nur der Ausdruck von geistigen Tatsachen, und alle Dinge, die uns materiell entgegentreten, sind nur die äußere Hülle von geistigen Wesenheiten. (GA 110, S. 30; 12.04.1909)`;
const beforeGA2 = text2.substring(0, text2.lastIndexOf('(GA'));
const result2 = plugin.extractFirstThreeWords(beforeGA2);
console.log('Test 2:');
console.log('  Ergebnis:', result2);
console.log('  Erwartet: "Alles was materiell"');
console.log('');

// Test 3: Mit [[Wikilinks]]
const text3 = `# Test mit Links

So also sehen Sie, daß hohe geistige Wesenheiten, hohe Hierarchien, die [[Throne]] zunächst, aus ihrer eigenen Substanz die Feuermaterie heraussondern. (GA 110, S. 75; 13.04.1909)`;
const beforeGA3 = text3.substring(0, text3.lastIndexOf('(GA'));
const result3 = plugin.extractFirstThreeWords(beforeGA3);
console.log('Test 3:');
console.log('  Ergebnis:', result3);
console.log('  Erwartet: "So also sehen"');
