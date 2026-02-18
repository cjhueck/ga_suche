const fs = require('fs');
const path = require('path');

const filePath = String.raw`C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA302a-Erziehung und Unterricht aus Menschenerkenntnis\GA302a - Erziehung und Unterricht aus Menschenerkenntnis (1920-1923).md`;

function processContent(content) {
  let count = 0;
  let matches = [];
  
  const pattern = /([^\n]+?)( \^[a-z0-9]+)\s*\n\s*\n\s*---\s*\n\s*\n\s*([^\n]+)/g;
  
  const fixed = content.replace(pattern, (match, textBefore, absatzId, textAfter, offset) => {
    const endsWithPeriod = /[.!?]\s*$/.test(textBefore);
    const startsWithCapital = /^[A-ZÄÖÜ]/.test(textAfter);
    
    const matchInfo = {
      position: offset,
      before: textBefore.substring(Math.max(0, textBefore.length - 40)),
      id: absatzId,
      after: textAfter.substring(0, 40),
      endsWithPeriod,
      startsWithCapital,
      action: 'none'
    };
    
    if (!endsWithPeriod && !startsWithCapital) {
      count++;
      matchInfo.action = 'merge';
      
      const hasDash = /-\s*$/.test(textBefore);
      const cleanedBefore = textBefore.replace(/-\s*$/, '');
      const separator = hasDash ? '' : ' ';
      const result = `${cleanedBefore}${separator}${textAfter}${absatzId}`;
      
      matchInfo.result = result;
      matches.push(matchInfo);
      return result;
    }
    
    if (endsWithPeriod && startsWithCapital) {
      count++;
      matchInfo.action = 'remove-separator';
      
      const result = `${textBefore}${absatzId}\n\n${textAfter}`;
      matchInfo.result = result;
      matches.push(matchInfo);
      return result;
    }
    
    matches.push(matchInfo);
    return match;
  });
  
  return { fixed, count, matches };
}

console.log('=== TESTE GA302a DATEI ===\n');
console.log('Lese Datei:', filePath);

try {
  const content = fs.readFileSync(filePath, 'utf8');
  console.log('Datei gelesen, Länge:', content.length, 'Zeichen\n');
  
  const { fixed, count, matches } = processContent(content);
  
  console.log(`\n=== ERGEBNIS ===`);
  console.log(`Gefundene Matches: ${matches.length}`);
  console.log(`Durchgeführte Korrekturen: ${count}\n`);
  
  console.log('=== DETAILS ===');
  matches.forEach((m, i) => {
    console.log(`\n--- Match ${i + 1} ---`);
    console.log(`Position: ${m.position}`);
    console.log(`Before: ...${m.before}`);
    console.log(`ID: ${m.id}`);
    console.log(`After: ${m.after}...`);
    console.log(`Endet mit Punkt: ${m.endsWithPeriod}`);
    console.log(`Beginnt groß: ${m.startsWithCapital}`);
    console.log(`Aktion: ${m.action}`);
    if (m.result) {
      console.log(`Ergebnis: ${m.result.substring(0, 100)}...`);
    }
  });
  
  // Speichere die korrigierte Version in eine Test-Datei
  if (count > 0) {
    const testOutputPath = filePath.replace('.md', '-KORRIGIERT-TEST.md');
    fs.writeFileSync(testOutputPath, fixed, 'utf8');
    console.log(`\n✓ Korrigierte Version gespeichert in:`);
    console.log(`  ${testOutputPath}`);
  }
  
} catch (error) {
  console.error('Fehler:', error);
}
