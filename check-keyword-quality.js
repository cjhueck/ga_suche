/**
 * Prüft die Qualität der generierten Keywords
 * 
 * Usage: node check-keyword-quality.js
 */

const fs = require('fs').promises;
const path = require('path');

async function checkKeywordQuality() {
  console.log('=== KEYWORD QUALITY CHECK ===\n');
  
  // Lade keywords-database.json
  const keywordsDB = JSON.parse(
    await fs.readFile(path.join(__dirname, 'keywords-database.json'), 'utf8')
  );
  
  // Sammle Statistiken
  const stats = {
    totalLectures: Object.keys(keywordsDB).length,
    totalKeywords: 0,
    keywordsByWordCount: {},
    tooLongKeywords: [],
    newKeywords: [],
    matchTypes: {}
  };
  
  // Analysiere Keywords
  Object.entries(keywordsDB).forEach(([lectureId, data]) => {
    if (!data.keywords || !Array.isArray(data.keywords)) return;
    
    data.keywords.forEach(kw => {
      stats.totalKeywords++;
      
      // Zähle Worte
      const wordCount = kw.term.trim().split(/\s+/).length;
      stats.keywordsByWordCount[wordCount] = (stats.keywordsByWordCount[wordCount] || 0) + 1;
      
      // Sammle zu lange Keywords (>5 Worte)
      if (wordCount > 5) {
        stats.tooLongKeywords.push({
          lectureId,
          term: kw.term,
          wordCount,
          heading: kw.heading
        });
      }
      
      // Match-Type Statistik
      const matchType = kw.matchType || 'unknown';
      stats.matchTypes[matchType] = (stats.matchTypes[matchType] || 0) + 1;
      
      // Sammle neue Keywords
      if (matchType === 'new') {
        stats.newKeywords.push({
          lectureId,
          term: kw.term,
          confidence: kw.confidence,
          heading: kw.heading
        });
      }
    });
  });
  
  // Ausgabe
  console.log(`📊 STATISTIKEN:`);
  console.log(`   Vorträge: ${stats.totalLectures}`);
  console.log(`   Keywords gesamt: ${stats.totalKeywords}`);
  console.log(`   Durchschnitt: ${(stats.totalKeywords / stats.totalLectures).toFixed(1)} KW/Vortrag\n`);
  
  console.log(`📏 KEYWORD-LÄNGE (Wort-Anzahl):`);
  Object.entries(stats.keywordsByWordCount)
    .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
    .forEach(([wordCount, count]) => {
      const percentage = ((count / stats.totalKeywords) * 100).toFixed(1);
      const bar = '█'.repeat(Math.floor(percentage / 2));
      console.log(`   ${wordCount} Wort${wordCount > 1 ? 'e' : ' '}: ${count.toString().padStart(5)} (${percentage.toString().padStart(5)}%) ${bar}`);
    });
  
  console.log(`\n🎯 MATCH-TYPES:`);
  Object.entries(stats.matchTypes)
    .sort((a, b) => b[1] - a[1])
    .forEach(([type, count]) => {
      const percentage = ((count / stats.totalKeywords) * 100).toFixed(1);
      console.log(`   ${type.padEnd(15)}: ${count.toString().padStart(5)} (${percentage.toString().padStart(5)}%)`);
    });
  
  console.log(`\n⚠️ ZU LANGE KEYWORDS (>5 Worte): ${stats.tooLongKeywords.length}`);
  if (stats.tooLongKeywords.length > 0) {
    console.log('\n   Erste 10 Beispiele:');
    stats.tooLongKeywords.slice(0, 10).forEach(kw => {
      console.log(`   • "${kw.term}" (${kw.wordCount} Worte)`);
      console.log(`     ${kw.lectureId}: ${kw.heading}`);
    });
  }
  
  console.log(`\n🆕 NEUE KEYWORDS: ${stats.newKeywords.length}`);
  if (stats.newKeywords.length > 0) {
    console.log('\n   Erste 20:');
    stats.newKeywords.slice(0, 20).forEach(kw => {
      console.log(`   • "${kw.term}" (confidence: ${kw.confidence})`);
      console.log(`     ${kw.lectureId}: ${kw.heading}`);
    });
  }
  
  // Qualitäts-Score
  console.log(`\n✅ QUALITÄTS-SCORE:`);
  
  const goodLength = (stats.keywordsByWordCount[1] || 0) + 
                     (stats.keywordsByWordCount[2] || 0) + 
                     (stats.keywordsByWordCount[3] || 0);
  const lengthScore = (goodLength / stats.totalKeywords * 100).toFixed(1);
  
  const vocabUsage = ((stats.matchTypes['exact'] || 0) + 
                      (stats.matchTypes['wordstem'] || 0) + 
                      (stats.matchTypes['synonym'] || 0) + 
                      (stats.matchTypes['thematic'] || 0)) / stats.totalKeywords * 100;
  
  const newPercentage = ((stats.newKeywords.length / stats.totalKeywords) * 100).toFixed(1);
  
  console.log(`   Länge (1-3 Worte): ${lengthScore}% ${lengthScore > 90 ? '✓' : lengthScore > 75 ? '⚠' : '✗'}`);
  console.log(`   Vokabular-Nutzung: ${vocabUsage.toFixed(1)}% ${vocabUsage > 90 ? '✓' : vocabUsage > 75 ? '⚠' : '✗'}`);
  console.log(`   Neue Keywords: ${newPercentage}% ${newPercentage < 10 ? '✓' : newPercentage < 20 ? '⚠' : '✗'}`);
  
  const overallScore = (parseFloat(lengthScore) + parseFloat(vocabUsage) + (100 - parseFloat(newPercentage))) / 3;
  console.log(`\n   GESAMT: ${overallScore.toFixed(1)}% ${overallScore > 85 ? '🎉 EXZELLENT' : overallScore > 70 ? '👍 GUT' : overallScore > 50 ? '⚠ AKZEPTABEL' : '❌ SCHLECHT'}`);
}

// Hauptausführung
checkKeywordQuality().catch(error => {
  console.error('Fehler:', error);
  process.exit(1);
});

