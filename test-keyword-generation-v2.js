/**
 * Test-Skript für Keyword-Generierung V2
 * 
 * Usage:
 *   node test-keyword-generation-v2.js
 */

const fetch = require('node-fetch');

const BASE_URL = 'http://localhost:3003';

// Farben für Console-Output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function testTemplateInfo() {
  log('\n=== TEST 1: Template-Info abrufen ===', 'cyan');
  
  try {
    const response = await fetch(`${BASE_URL}/api/keywords-template-info`);
    const data = await response.json();
    
    if (data.stats) {
      log('✓ Template erfolgreich geladen', 'green');
      log(`  Themen: ${data.stats.totalThemes}`, 'bright');
      log(`  Keywords: ${data.stats.totalKeywords}`, 'bright');
      log(`  Synonym-Gruppen: ${data.stats.synonymGroups}`, 'bright');
      log(`  Confidence: ${data.stats.confidenceThreshold}`, 'bright');
      return true;
    } else {
      log('✗ Template konnte nicht geladen werden', 'red');
      console.log(data);
      return false;
    }
  } catch (error) {
    log(`✗ Fehler: ${error.message}`, 'red');
    return false;
  }
}

async function testSingleLecture() {
  log('\n=== TEST 2: Einzelnen Vortrag verarbeiten ===', 'cyan');
  
  const testLectureId = 'GA068a/11'; // Beispiel-Vortrag
  
  try {
    const response = await fetch(`${BASE_URL}/api/generate-keywords-v2`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lectureIds: [testLectureId],
        useExistingVocab: true,
        consolidateSynonyms: true
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      log('✓ Keyword-Generierung erfolgreich', 'green');
      log(`  Verarbeitet: ${data.stats.processed}`, 'bright');
      log(`  Übersprungen: ${data.stats.skipped}`, 'bright');
      log(`  Fehler: ${data.stats.errors}`, 'bright');
      log(`  Vokabular-Größe: ${data.stats.newVocabularySize}`, 'bright');
      log(`  Synonyme konsolidiert: ${data.stats.synonymsConsolidated}`, 'bright');
      
      if (data.results && data.results.length > 0) {
        const result = data.results[0];
        log(`\n  Lecture: ${result.lectureId}`, 'bright');
        log(`  Keywords: ${result.keywordsCount}`, 'bright');
        log(`  Neue Keywords: ${result.newKeywordsCount}`, 'bright');
      }
      
      return true;
    } else {
      log('✗ Keyword-Generierung fehlgeschlagen', 'red');
      console.log(data);
      return false;
    }
  } catch (error) {
    log(`✗ Fehler: ${error.message}`, 'red');
    return false;
  }
}

async function testGAVolume() {
  log('\n=== TEST 3: GA-Band verarbeiten (Simulation - nur Info) ===', 'cyan');
  
  log('⚠ Dieser Test würde einen kompletten GA-Band verarbeiten', 'yellow');
  log('  Für echten Test, kommentiere testGAVolume() aus und verwende:', 'yellow');
  log('  POST /api/generate-keywords-v2', 'bright');
  log('  { "gaVolumes": ["GA068"], "useExistingVocab": true }', 'bright');
  
  return true;
}

async function testKeywordsStats() {
  log('\n=== TEST 4: Keywords-Statistiken ===', 'cyan');
  
  try {
    const response = await fetch(`${BASE_URL}/api/keywords-stats`);
    const data = await response.json();
    
    log('✓ Statistiken abgerufen', 'green');
    log(`  Total Lectures: ${data.totalLectures}`, 'bright');
    log(`  Keywords Generated: ${data.keywordsGenerated}`, 'bright');
    log(`  Percentage: ${data.percentage}%`, 'bright');
    log(`  Mit Thema: ${data.withTheme}`, 'bright');
    log(`  Ohne Thema: ${data.withoutTheme}`, 'bright');
    
    return true;
  } catch (error) {
    log(`✗ Fehler: ${error.message}`, 'red');
    return false;
  }
}

async function runTests() {
  log('╔════════════════════════════════════════════════╗', 'bright');
  log('║  Keyword-Generierung V2 - Test Suite          ║', 'bright');
  log('╚════════════════════════════════════════════════╝', 'bright');
  
  const results = [];
  
  // Test 1: Template-Info
  results.push(await testTemplateInfo());
  
  // Test 2: Einzelner Vortrag
  results.push(await testSingleLecture());
  
  // Test 3: GA-Band (Simulation)
  results.push(await testGAVolume());
  
  // Test 4: Statistiken
  results.push(await testKeywordsStats());
  
  // Zusammenfassung
  log('\n╔════════════════════════════════════════════════╗', 'bright');
  log('║  Test-Zusammenfassung                          ║', 'bright');
  log('╚════════════════════════════════════════════════╝', 'bright');
  
  const passed = results.filter(r => r).length;
  const failed = results.filter(r => !r).length;
  
  log(`\n✓ Bestanden: ${passed}`, 'green');
  log(`✗ Fehlgeschlagen: ${failed}`, failed > 0 ? 'red' : 'reset');
  
  if (failed === 0) {
    log('\n🎉 Alle Tests bestanden!', 'green');
  } else {
    log('\n⚠ Einige Tests fehlgeschlagen', 'yellow');
  }
}

// Hauptausführung
if (require.main === module) {
  runTests().catch(error => {
    log(`\n✗ Kritischer Fehler: ${error.message}`, 'red');
    console.error(error);
    process.exit(1);
  });
}

module.exports = { runTests };

