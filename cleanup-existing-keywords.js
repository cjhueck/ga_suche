/**
 * Bereinigt bereits generierte Keywords (entfernt Füllwörter, kürzt zu lange)
 * 
 * Usage: node cleanup-existing-keywords.js
 */

const fs = require('fs').promises;
const path = require('path');

// Lade Template für Vokabular
async function loadTemplate() {
  const data = await fs.readFile(path.join(__dirname, 'themes-keywords-template.json'), 'utf8');
  return JSON.parse(data);
}

// Extrahiere Vokabular
function getVocabulary(template) {
  const vocab = new Set();
  Object.values(template.themes).forEach(theme => {
    theme.keywords.forEach(kw => vocab.add(kw.toLowerCase()));
  });
  return Array.from(vocab);
}

// Bereinige ein Keyword
function cleanKeyword(term, vocabulary) {
  let cleaned = term.trim();
  const original = cleaned;
  
  // 1. Füllwörter am Anfang entfernen
  const fillWords = [
    'Wesen', 'Problem', 'Lehre', 'Stellung', 'Wendung', 'Bedeutung',
    'Aufgabe', 'Prozess', 'Natur', 'Macht', 'Bedürfnis', 'Wesenheit', 'Frage'
  ];
  
  fillWords.forEach(fw => {
    cleaned = cleaned.replace(new RegExp(`^${fw}\\s+`, 'i'), '');
  });
  
  // 2. Adjektive am Anfang entfernen
  const adjectives = [
    'griechischen', 'individuellen', 'historische', 'hellenistischen',
    'suggestive', 'erwachende', 'ewige', 'materialistische',
    'geisteswissenschaftliche', 'viergliederige', 'menschlichen', 'seelische',
    'neuzeitlichen'
  ];
  
  adjectives.forEach(adj => {
    cleaned = cleaned.replace(new RegExp(`^${adj}\\s+`, 'i'), '');
  });
  
  // 3. Unvollständige Phrasen (endet mit Konjunktion)
  cleaned = cleaned.replace(/\s+(und|oder|zwischen|nach|zu|von)\s*$/i, '');
  
  // 4. Grammatik-Fixes
  cleaned = cleaned.replace(/geisteswissenschaftlichen Forschung/i, 'Geisteswissenschaftliche Forschung');
  cleaned = cleaned.replace(/biologischen Grundsatz/i, 'biologischer Grundsatz');
  cleaned = cleaned.replace(/menschlichen Wesenkern/i, 'Wesenskern');
  cleaned = cleaned.replace(/menschlichen Seele/i, 'der Seele');
  cleaned = cleaned.replace(/individuellen Seele/i, 'der Seele');
  cleaned = cleaned.replace(/Viergliederige Wesenheit Menschen/i, 'Viergliederigkeit Mensch');
  
  // 5. Wenn immer noch >3 Worte: Versuche zu kürzen
  const words = cleaned.split(/\s+/);
  
  if (words.length > 3) {
    // Strategie A: Letztes Wort im Vokabular?
    const lastWord = words[words.length - 1];
    if (vocabulary.includes(lastWord.toLowerCase())) {
      return { cleaned: lastWord, changed: true, method: 'lastWord' };
    }
    
    // Strategie B: Letzte 2 Worte im Vokabular?
    if (words.length >= 2) {
      const lastTwo = words.slice(-2).join(' ');
      if (vocabulary.includes(lastTwo.toLowerCase())) {
        return { cleaned: lastTwo, changed: true, method: 'lastTwo' };
      }
    }
    
    // Strategie C: Hauptsubstantive (Großbuchstaben)
    const capitals = words.filter(w => /^[A-ZÄÖÜ]/.test(w));
    if (capitals.length >= 1 && capitals.length <= 2) {
      const result = capitals.slice(0, 2).join(' ');
      return { cleaned: result, changed: true, method: 'capitals' };
    }
    
    // Strategie D: Erste 2 Worte
    const firstTwo = words.slice(0, 2).join(' ');
    return { cleaned: firstTwo, changed: true, method: 'firstTwo' };
  }
  
  return {
    cleaned: cleaned,
    changed: cleaned !== original,
    method: cleaned !== original ? 'fillwords' : 'unchanged'
  };
}

async function cleanupKeywords() {
  console.log('=== KEYWORD CLEANUP ===\n');
  
  // Lade Daten
  const template = await loadTemplate();
  const vocabulary = getVocabulary(template);
  const keywordsDB = JSON.parse(
    await fs.readFile(path.join(__dirname, 'keywords-database.json'), 'utf8')
  );
  
  console.log(`Vokabular: ${vocabulary.length} Begriffe`);
  console.log(`Vorträge: ${Object.keys(keywordsDB).length}\n`);
  
  // Backup erstellen
  const backupFile = `keywords-database-backup-before-cleanup-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
  await fs.writeFile(backupFile, JSON.stringify(keywordsDB, null, 2));
  console.log(`✓ Backup erstellt: ${backupFile}\n`);
  
  // Bereinige Keywords
  let totalCleaned = 0;
  let totalRejected = 0;
  const changes = [];
  
  Object.entries(keywordsDB).forEach(([lectureId, data]) => {
    if (!data.keywords || !Array.isArray(data.keywords)) return;
    
    data.keywords = data.keywords.filter(kw => {
      const result = cleanKeyword(kw.term, vocabulary);
      
      if (result.changed) {
        console.log(`${lectureId}: "${kw.term}" → "${result.cleaned}" (${result.method})`);
        kw.term = result.cleaned;
        totalCleaned++;
        changes.push({ lectureId, old: kw.term, new: result.cleaned });
      }
      
      // Verwerfe wenn immer noch zu lang (>5 Worte)
      const finalWordCount = result.cleaned.split(/\s+/).length;
      if (finalWordCount > 5) {
        console.log(`${lectureId}: VERWORFEN (zu lang): "${result.cleaned}"`);
        totalRejected++;
        return false;
      }
      
      return true;
    });
  });
  
  // Speichere bereinigte Datenbank
  const cleanedFile = 'keywords-database-cleaned.json';
  await fs.writeFile(cleanedFile, JSON.stringify(keywordsDB, null, 2));
  
  console.log(`\n✅ CLEANUP ABGESCHLOSSEN`);
  console.log(`   Bereinigt: ${totalCleaned} Keywords`);
  console.log(`   Verworfen: ${totalRejected} Keywords`);
  console.log(`   Gespeichert: ${cleanedFile}`);
  console.log(`\n📝 Nächste Schritte:`);
  console.log(`   1. Prüfe: ${cleanedFile}`);
  console.log(`   2. Wenn OK: cp ${cleanedFile} keywords-database.json`);
  console.log(`   3. Backend neu starten`);
}

cleanupKeywords().catch(error => {
  console.error('Fehler:', error);
  process.exit(1);
});

