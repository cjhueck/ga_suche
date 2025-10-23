// hybrid-search-server-unified.js - Vereinheitlichtes System mit GA/Vortrag IDs
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const fsSync = require('fs'); // Für synchrone Operationen (Seed-Keywords laden)
const path = require('path');

const app = express();
const PORT = 3003;

// Middleware - WICHTIG: Reihenfolge beachten!
app.use(cors());
app.use(express.json());

// Statische Dateien aus dem system Ordner bereitstellen
app.use('/system', express.static(path.join(__dirname, 'system')));

// Statische HTML-Dateien aus dem Hauptverzeichnis bereitstellen
app.use(express.static(__dirname));

// Logging Middleware für alle Requests
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Global variables
let chunks = []; // WIRD NICHT MEHR VERWENDET
let paragraphsFromLectures = []; // NEU
let fullLectures = {};
let synonyms = {};
let summaryCache = {};
let gaOverviewCache = {};
let queryLog = {}; // NEU: Für Query-Tracking
let lastSynonymUpdate = null; // NEU: Timestamp der letzten Synonym-Generierung

// Hilfsfunktion: Synonym-Expansion
function expandSynonyms(query) {
  const words = query.toLowerCase().split(/\W+/);
  let expanded = new Set(words);
  for (const word of words) {
    if (synonyms[word]) {
      synonyms[word].forEach(syn => expanded.add(syn));
    }
  }
  return Array.from(expanded);
}

// Hilfsfunktion: Levenshtein-Distanz
function levenshtein(a, b) {
  if (a === b) return 0;
  const matrix = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  return matrix[a.length][b.length];
}

// Hilfsfunktion: Keyword-Overlap
function keywordOverlap(a, b) {
  const wa = new Set(a.toLowerCase().split(/\W+/));
  const wb = new Set(b.toLowerCase().split(/\W+/));
  let overlap = 0;
  wa.forEach(w => { if (wb.has(w)) overlap++; });
  return overlap / Math.max(wa.size, wb.size);
}

// Hybrid-Cache-Suche
function findHybridCacheHit(query, depth, limit, gaFilter, thematicDB) {
  const expanded = expandSynonyms(query);
  let bestKey = null;
  let bestScore = 0;
  for (const key of Object.keys(thematicDB)) {
    const [cachedQuery, cachedDepth, cachedLimit, cachedGaFilter] = key.split('|');
    if (cachedDepth !== depth || Number(cachedLimit) !== Number(limit) || cachedGaFilter !== gaFilter) continue;
    // 1. Exact Match
    if (cachedQuery === query.toLowerCase().trim()) return { key, score: 1.0 };
    // 2. Synonym/Stemming
    if (expanded.includes(cachedQuery)) return { key, score: 0.95 };
    // 3. String-Similarity
    const levDist = levenshtein(query.toLowerCase().trim(), cachedQuery);
    const levScore = 1 - levDist / Math.max(query.length, cachedQuery.length);
    // 4. Keyword-Overlap
    const overlapScore = keywordOverlap(query, cachedQuery);
    // Kombiniere Scores
    const score = Math.max(levScore, overlapScore);
    if (score > bestScore) {
      bestScore = score;
      bestKey = key;
    }
  }
  if (bestScore > 0.8) return { key: bestKey, score: bestScore };
  return null;
}

// Hilfsfunktion für case-insensitive Zugriff auf GA-Overview-Cache
function findGAOverviewKey(requestedKey) {
  const keys = Object.keys(gaOverviewCache);
  const match = keys.find(k => k.toLowerCase() === requestedKey.toLowerCase());
  return match || requestedKey;
}

// Standard-Synonyme
const defaultSynonyms = {
  "kant": ["kant", "kants", "kantisch", "kantische", "kantischen", "immanuel kant", "kategorischer imperativ", "ding an sich"],
  "erkenntnistheorie": ["erkenntnistheorie", "epistemologie", "erkenntnis", "erkenntnislehre"],
  "bewusstsein": ["bewusstsein", "bewußtsein", "seelenleben", "geistesleben", "seele"],
  "philosophie": ["philosophie", "weltanschauung", "denken", "gedanke", "philosophisch"],
  "anthroposophie": ["anthroposophie", "geisteswissenschaft", "übersinnlich", "geistige welt"],
  "ätherleib": ["ätherleib", "lebensleib", "bildekräfteleib", "ätherischer leib", "aetherleib"],
  "astralleib": ["astralleib", "empfindungsleib", "seelenleib", "astraler leib"],
  "ich": ["ich", "ich-organisation", "geist-selbst", "ich-wesenheit"]
};

// ============================================================================
// DATEI-SUCHE FUNKTIONEN
// ============================================================================

async function findDataFiles() {
  const files = await fs.readdir(__dirname);
  
  // Suche nach steiner-search-XXX-YYY*.json
  const searchPattern = /^steiner-search-(\d{3}[a-z]?)-(\d{3}[a-z]?).*\.json$/i;
  const searchFiles = files.filter(f => searchPattern.test(f));
  
  // Suche nach steiner-full-lectures-XXX-YYY*.json
  const lecturePattern = /^steiner-full-lectures-(\d{3}[a-z]?)-(\d{3}[a-z]?).*\.json$/i;
  const lectureFiles = files.filter(f => lecturePattern.test(f));
  
  console.log('\nGefundene Dateien:');
  console.log('  Search-Dateien:', searchFiles);
  console.log('  Lecture-Dateien:', lectureFiles);
  
  return {
    searchFiles,
    lectureFiles
  };
}

// ============================================================================
// DATEN LADEN UND SPEICHERN
// ============================================================================

async function loadChunks() {
  try {
    const { searchFiles } = await findDataFiles();
    
    if (searchFiles.length === 0) {
      throw new Error('Keine steiner-search-XXX-YYY*.json Dateien gefunden');
    }
    
    console.log(`\nLade Chunks aus ${searchFiles.length} Datei(en)...`);
    
    for (const fileName of searchFiles) {
      const jsonPath = path.join(__dirname, fileName);
      console.log(`  Lade: ${fileName}`);
      
      const data = await fs.readFile(jsonPath, 'utf8');
      const parsed = JSON.parse(data);
      
      const fileChunks = parsed.chunks || [];
      chunks = chunks.concat(fileChunks);
      
      console.log(`    -> ${fileChunks.length} Chunks geladen`);
    }
    
    const sample = chunks[0];
    console.log('\nChunk-Struktur:', {
      ID: sample?.ID,
      index: sample?.index,
      fileName: sample?.fileName,
      content: sample?.content ? `${sample.content.substring(0, 50)}...` : 'fehlt'
    });
    
    console.log(`\nGesamt: ${chunks.length} Chunks geladen`);
    return chunks;
    
  } catch (error) {
    console.error('Fehler beim Laden der Chunks:', error.message);
    throw error;
  }
}

async function loadFullLectures() {
  try {
    const { lectureFiles } = await findDataFiles();
    
    if (lectureFiles.length === 0) {
      console.warn('Keine steiner-full-lectures-XXX-YYY*.json Dateien gefunden');
      return {};
    }
    
    console.log(`\nLade Vorträge aus ${lectureFiles.length} Datei(en)...`);
    
    for (const fileName of lectureFiles) {
      const jsonPath = path.join(__dirname, fileName);
      console.log(`  Lade: ${fileName}`);
      
      const data = await fs.readFile(jsonPath, 'utf8');
      const parsed = JSON.parse(data);
      
      const lectures = parsed.lectures || [];
      
      lectures.forEach(lecture => {
        if (lecture.ID) {
          fullLectures[lecture.ID] = lecture;
        }
      });
      
      console.log(`    -> ${lectures.length} Vorträge geladen`);
    }
    
    const sample = Object.values(fullLectures)[0];
    console.log('\nVortrags-Struktur:', {
      ID: sample?.ID,
      fileName: sample?.fileName,
      title: sample?.title,
      gaNumber: sample?.gaNumber,
      gaTitle: sample?.gaTitle,
      paragraphs: sample?.paragraphs?.length,
      hasIndices: sample?.paragraphs?.some(p => p.index)
    });
    
    console.log(`\nGesamt: ${Object.keys(fullLectures).length} Vorträge geladen`);
    return fullLectures;
    
  } catch (error) {
    console.error('Fehler beim Laden der Vorträge:', error.message);
    console.warn('System läuft ohne vollständige Vorträge');
    return {};
  }
}

async function loadSynonyms() {
  try {
    const synonymPath = path.join(__dirname, 'synonyms.json');
    
    try {
      const data = await fs.readFile(synonymPath, 'utf8');
      synonyms = JSON.parse(data);
      console.log(`Synonyme geladen: ${Object.keys(synonyms).length} Begriffe`);
    } catch {
      synonyms = defaultSynonyms;
      await fs.writeFile(synonymPath, JSON.stringify(synonyms, null, 2), 'utf8');
      console.log(`Standard-Synonyme erstellt`);
    }
    
    return synonyms;
    
  } catch (error) {
    console.error('Fehler beim Laden der Synonyme:', error.message);
    synonyms = defaultSynonyms;
    return synonyms;
  }
}

async function saveSynonyms() {
  try {
    const synonymPath = path.join(__dirname, 'synonyms.json');
    await fs.writeFile(synonymPath, JSON.stringify(synonyms, null, 2), 'utf8');
    console.log('✓ Synonyme gespeichert');
    return true;
  } catch (error) {
    console.error('✗ Fehler beim Speichern der Synonyme:', error.message);
    return false;
  }
}

async function loadQueryLog() {
  try {
    const logPath = path.join(__dirname, 'query-log.json');
    const data = await fs.readFile(logPath, 'utf8');
    queryLog = JSON.parse(data);
    console.log(`Query-Log geladen: ${Object.keys(queryLog).length} Begriffe`);
  } catch {
    queryLog = {};
    console.log('Kein Query-Log gefunden - neuer Log erstellt');
  }
  return queryLog;
}

async function saveQueryLog() {
  try {
    const logPath = path.join(__dirname, 'query-log.json');
    await fs.writeFile(logPath, JSON.stringify(queryLog, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern des Query-Logs:', error.message);
    return false;
  }
}

// Legacy loadSummaryCache() und saveSummaryCache() Funktionen entfernt 
// Verwenden nur noch zentrale Summary-Datenbank (summary-database.json)

async function invalidateGAOverviewCache(lectureId) {
  try {
    const rawGA = lectureId.split('/')[0];
    const actualKey = findGAOverviewKey(rawGA);

    if (gaOverviewCache[actualKey]) {
      console.log(`[CACHE] Invalidiere GA-Overview-Cache für ${actualKey}`);
      delete gaOverviewCache[actualKey];
      await saveGAOverviewCache();
      console.log(`[CACHE] ✓ GA-Overview-Cache für ${actualKey} gelöscht`);
    } else {
      console.log(`[CACHE] Kein Cache-Eintrag für ${rawGA} gefunden (Key-Scan ergab: ${actualKey})`);
    }

    return true;
  } catch (error) {
    console.error('[CACHE] Fehler beim Invalidieren des GA-Overview-Cache:', error.message);
    return false;
  }
}

// ============================================================================
// GA-ÜBERSICHTS-FUNKTIONEN
// ============================================================================

async function loadGAOverviewCache() {
  try {
    const cachePath = path.join(__dirname, 'ga-overview-cache.json');
    
    try {
      const data = await fs.readFile(cachePath, 'utf8');
      gaOverviewCache = JSON.parse(data);
      console.log(`GA-Übersichten geladen: ${Object.keys(gaOverviewCache).length} GA-Bände`);
    } catch {
      gaOverviewCache = {};
      console.log('Keine gespeicherten GA-Übersichten gefunden - leerer Cache erstellt');
    }
    
    return gaOverviewCache;
    
  } catch (error) {
    console.error('Fehler beim Laden des GA-Overview-Cache:', error.message);
    gaOverviewCache = {};
    return gaOverviewCache;
  }
}

async function saveGAOverviewCache() {
  try {
    const cachePath = path.join(__dirname, 'ga-overview-cache.json');
    const jsonString = JSON.stringify(gaOverviewCache, null, 2);
    await fs.writeFile(cachePath, jsonString, 'utf8');
    console.log('✓ GA-Overview-Cache gespeichert');
    return true;
  } catch (error) {
    console.error('✗ Fehler beim Speichern des GA-Overview-Cache:', error.message);
    return false;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  
  const months = {
    '01': 'Januar', '02': 'Februar', '03': 'März', '04': 'April',
    '05': 'Mai', '06': 'Juni', '07': 'Juli', '08': 'August',
    '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Dezember'
  };
  
  const match = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const [, year, month, day] = match;
    return `${parseInt(day)}. ${months[month]} ${year}`;
  }
  
  return dateStr;
}

async function generateGAOverview(gaNumber) {
  const lectures = Object.values(fullLectures)
    .filter(lec => lec.gaNumber === gaNumber)
    .sort((a, b) => {
      const numA = parseInt(a.lectureNumber) || 0;
      const numB = parseInt(b.lectureNumber) || 0;
      return numA - numB;
    });
  
  if (lectures.length === 0) {
    return null;
  }
  
  const gaTitle = lectures[0].gaTitle || gaNumber;
  
  // Lade zentrale Summary-Datenbank (kein Cache mehr)
  const summaryDB = await loadSummaryDatabase();
  
  const overview = {
    gaNumber: gaNumber,
    gaTitle: gaTitle,
    lectureCount: lectures.length,
    lectures: lectures.map(lec => {
      const lectureId = lec.ID;
      const summaryData = summaryDB[lectureId];
      
      let summaryText = null;
      if (summaryData && summaryData.summary) {
        summaryText = summaryData.summary;
      }
      
      return {
        lectureNumber: lec.lectureNumber,
        ID: lectureId,
        title: lec.title,
        fileName: lec.fileName,
        location: lec.location,
        date: formatDate(lec.date),
        summary: summaryText
      };
    })
  };
  
  return overview;
}

// ============================================================================
// QUERY-TRACKING UND SYNONYM-GENERIERUNG
// ============================================================================

function trackQueryTerms(query, resultCount) {
  if (resultCount === 0) return;

  const terms = extractKeyTerms(query);

  terms.forEach(term => {
    if (!queryLog[term]) {
      queryLog[term] = {
        count: 0,
        last: new Date().toISOString()
      };
    }
    queryLog[term].count++;
    queryLog[term].last = new Date().toISOString();
  });

  const totalQueries = Object.values(queryLog).reduce((sum, entry) => sum + entry.count, 0);
  if (totalQueries % 10 === 0) {
    saveQueryLog();
  }
}

function generateSynonymsFromQueries(minCoOccurrence = 3) {
  const newSynonyms = {};
  
  Object.keys(queryLog).forEach(term => {
    const entry = queryLog[term];
    
    if (entry.count < 2) return;
    
    const coOccurs = entry.coOccurrences;
    const relatedTerms = Object.keys(coOccurs)
      .filter(t => coOccurs[t] >= minCoOccurrence)
      .sort((a, b) => coOccurs[b] - coOccurs[a])
      .slice(0, 10);
    
    if (relatedTerms.length > 0) {
      newSynonyms[term] = [term, ...relatedTerms];
    }
  });
  
  console.log(`\n[SYNONYME] Aus Query-Log generiert: ${Object.keys(newSynonyms).length} Begriffe`);
  
  return newSynonyms;
}

async function generateSynonymsWithClaude(term) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  if (!claudeApiKey) {
    console.log(`[CLAUDE] Kein API-Key für "${term}"`);
    return [term];
  }
  
  const prompt = `Erstelle eine Liste von Synonymen und verwandten Begriffen für: "${term}"

Kontext: Rudolf Steiner / Anthroposophie / Geisteswissenschaft / Deutsche Philosophie

Berücksichtige:
- Historische Schreibweisen (z.B. "Bewußtsein" vs "Bewusstsein", "Urtheil" vs "Urteil")
- Verwandte Konzepte aus der Anthroposophie
- Unterschiedliche Formulierungen
- Genitivformen und Adjektive (z.B. "Kants", "kantisch", "kantische")
- Zusammengesetzte Begriffe

Gib nur die Begriffe zurück, kommasepariert, maximal 15 Begriffe, keine Erklärungen.

Beispiel für "ich":
ich, ich-organisation, ich-wesenheit, geist-selbst, menschliches ich, höheres ich

Begriffe für "${term}":`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 400,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    const synonymText = result.content[0].text.trim();
    const synonymList = synonymText
      .split(',')
      .map(s => s.trim().toLowerCase())
      .filter(s => s.length > 0);
    
    console.log(`[CLAUDE] Synonyme für "${term}": ${synonymList.length} Begriffe`);
    
    return synonymList;
  } catch (error) {
    console.error(`[CLAUDE] Fehler für "${term}":`, error.message);
    return [term];
  }
}

async function enrichSynonymsWithClaude(topN = 30) {
  console.log(`\n[CLAUDE] Starte Anreicherung für Top ${topN} Begriffe...`);
  
  const topTerms = Object.keys(queryLog)
    .filter(term => term.length > 3)
    .sort((a, b) => queryLog[b].count - queryLog[a].count)
    .slice(0, topN);
  
  let enrichedCount = 0;
  
  for (const term of topTerms) {
    if (synonyms[term] && synonyms[term].length > 2) {
      console.log(`[CLAUDE] Überspringe "${term}" (bereits ${synonyms[term].length} Synonyme)`);
      continue;
    }
    
    console.log(`[CLAUDE] Generiere Synonyme für: "${term}" (${queryLog[term].count}x gesucht)`);
    const generatedSynonyms = await generateSynonymsWithClaude(term);
    
    if (generatedSynonyms.length > 1) {
      synonyms[term] = generatedSynonyms;
      enrichedCount++;
      await saveSynonyms();
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.log(`[CLAUDE] ✓ ${enrichedCount} Begriffe angereichert\n`);
  return enrichedCount;
}

// ============================================================================
// SUCHE
// ============================================================================

function expandQueryWithSynonyms(query) {
  const queryLower = query.toLowerCase();
  const expandedTerms = new Set([queryLower]);
  
  for (const [concept, synonymList] of Object.entries(synonyms)) {
    const matchingSynonyms = synonymList.filter(syn => 
      queryLower.includes(syn.toLowerCase()) || syn.toLowerCase().includes(queryLower)
    );
    
    if (matchingSynonyms.length > 0) {
      synonymList.forEach(syn => expandedTerms.add(syn.toLowerCase()));
    }
  }
  
  return Array.from(expandedTerms);
}

function performKeywordSearch(query, paragraphsFromLectures) {
  const expandedTerms = expandQueryWithSynonyms(query);
  const results = [];
  
  console.log(`Suche nach: ${expandedTerms.slice(0, 5).join(' | ')}${expandedTerms.length > 5 ? '...' : ''}`);
  
  paragraphsFromLectures.forEach(paragraph => {
    const content = (paragraph.content || '').toLowerCase();
    const title = (paragraph.title || '').toLowerCase();
    const paragraphId = (paragraph.ID || '').toLowerCase();
    
    let score = 0;
    let matchedTerms = [];
    
    expandedTerms.forEach(term => {
      const termLower = term.toLowerCase();
      
      let contentMatches = 0;
      let pos = 0;
      while ((pos = content.indexOf(termLower, pos)) !== -1) {
        contentMatches++;
        pos += 1;
      }
      
      let titleMatches = 0;
      pos = 0;
      while ((pos = title.indexOf(termLower, pos)) !== -1) {
        titleMatches++;
        pos += 1;
      }
      
      let idMatches = 0;
      pos = 0;
      while ((pos = paragraphId.indexOf(termLower, pos)) !== -1) {
        idMatches++;
        pos += 1;
      }
      
      if (contentMatches > 0 || titleMatches > 0 || idMatches > 0) {
        score += contentMatches + (titleMatches * 3) + (idMatches * 5);
        matchedTerms.push(term);
      }
    });
    
    if (score > 0) {
      results.push({
        ...paragraph,
        keywordScore: score,
        matchedTerms: matchedTerms,
        similarity: score / 10
      });
    }
  });
  
  results.sort((a, b) => b.keywordScore - a.keywordScore);
  
  console.log(`Keyword-Suche: ${results.length} Treffer`);
  
  return results;
}

function extractKeyTerms(query) {
  const stopWords = [
    'wie', 'ist', 'das', 'verhältnis', 'von', 'und', 'der', 'die', 'des', 
    'den', 'dem', 'ein', 'eine', 'einem', 'einen', 'was', 'welche', 'welcher',
    'zwischen', 'bei', 'nach', 'für', 'mit', 'aus', 'über', 'sich', 'zur',
    'hat', 'haben', 'wird', 'werden', 'sein', 'ihre', 'seiner', 'ihren'
  ];
  
  const terms = [];
  
  // 1. Extrahiere Phrasen in Anführungszeichen (höchste Priorität)
  const quotedPhrases = query.match(/"([^"]+)"|'([^']+)'/g);
  if (quotedPhrases) {
    quotedPhrases.forEach(phrase => {
      const cleaned = phrase.replace(/['"]/g, '').trim().toLowerCase();
      if (cleaned.length > 3) {
        terms.push(cleaned);
        console.log(`  [Quote] "${cleaned}"`);
      }
    });
  }
  
  // Entferne Anführungszeichen aus dem Query für weitere Verarbeitung
  const queryWithoutQuotes = query.replace(/"[^"]+"|'[^']+'/g, '').trim();
  const queryLower = queryWithoutQuotes.toLowerCase();
  
  // 2. Tokenisierung
  const words = queryLower
    .replace(/[.,;:!?"']/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 0);
  
  // 3. Extrahiere 3-Wort-Phrasen (z.B. "anschauende urteilskraft für")
  for (let i = 0; i < words.length - 2; i++) {
    const w1 = words[i];
    const w2 = words[i + 1];
    const w3 = words[i + 2];
    
    // Alle drei Wörter müssen mindestens 3 Zeichen haben
    if (w1.length > 2 && w2.length > 2 && w3.length > 2) {
      // Mindestens zwei der drei Wörter dürfen nicht Stopwörter sein
      const stopWordCount = [w1, w2, w3].filter(w => stopWords.includes(w)).length;
      if (stopWordCount <= 1) {
        const phrase = `${w1} ${w2} ${w3}`;
        terms.push(phrase);
        console.log(`  [3-Word] "${phrase}"`);
      }
    }
  }
  
  // 4. Extrahiere 2-Wort-Phrasen (z.B. "anschauende urteilskraft")
  for (let i = 0; i < words.length - 1; i++) {
    const w1 = words[i];
    const w2 = words[i + 1];
    
    // Beide Wörter müssen mindestens 3 Zeichen haben
    if (w1.length > 2 && w2.length > 2) {
      // Mindestens ein Wort darf kein Stopwort sein
      if (!stopWords.includes(w1) || !stopWords.includes(w2)) {
        const phrase = `${w1} ${w2}`;
        terms.push(phrase);
        console.log(`  [2-Word] "${phrase}"`);
      }
    }
  }
  
  // 5. Extrahiere bedeutungsvolle Einzelwörter
  words.forEach(word => {
    if (word.length > 3 && !stopWords.includes(word)) {
      terms.push(word);
      console.log(`  [Single] "${word}"`);
    }
  });
  
  // 6. Entferne exakte Duplikate
  const uniqueTerms = [...new Set(terms)];
  
  console.log(`\nExtrahierte ${uniqueTerms.length} Suchbegriffe aus "${query}":`);
  console.log(uniqueTerms.slice(0, 10).join(', ') + (uniqueTerms.length > 10 ? '...' : ''));
  
  return uniqueTerms;
}

function performThematicKeywordSearch(query, paragraphsFromLectures, gaFilter = '') {
  const terms = extractKeyTerms(query);
  
  // GA-Filter anwenden, wenn angegeben
  let filteredParagraphs = paragraphsFromLectures;
  if (gaFilter) {
    filteredParagraphs = paragraphsFromLectures.filter(paragraph => 
      paragraph.ID && paragraph.ID.startsWith(gaFilter)
    );
    console.log(`[GA-FILTER] Suche auf GA-Band ${gaFilter} beschränkt: ${filteredParagraphs.length} von ${paragraphsFromLectures.length} Paragraphen`);
  }
  
  if (terms.length === 0) {
    console.log('Keine Schlüsselbegriffe gefunden, verwende gesamte Query');
    return performKeywordSearch(query, filteredParagraphs);
  }
  
  // NEUE STRATEGIE: Suche zuerst nach Phrasen in Anführungszeichen
  const quotedPhrases = query.match(/"([^"]+)"|'([^']+)'/g);
  if (quotedPhrases && quotedPhrases.length > 0) {
    console.log('[DIREKTE PHRASENSUCHE] Verwende nur Phrasen in Anführungszeichen');
    
    const phraseResults = [];
    quotedPhrases.forEach(phrase => {
      const cleaned = phrase.replace(/['"]/g, '').trim().toLowerCase();
      console.log(`Suche direkt nach: "${cleaned}"`);
      const results = performKeywordSearch(cleaned, filteredParagraphs);
      phraseResults.push(...results);
    });
    
    // Wenn Phrasen-Treffer vorhanden: NUR diese verwenden
    if (phraseResults.length > 0) {
      // Dedupliziere nach ID-index
      const uniqueResults = new Map();
      phraseResults.forEach(result => {
        const key = `${result.ID}-${result.index}`;
        if (!uniqueResults.has(key) || uniqueResults.get(key).keywordScore < result.keywordScore) {
          uniqueResults.set(key, result);
        }
      });
      
      const finalResults = Array.from(uniqueResults.values())
        .sort((a, b) => b.keywordScore - a.keywordScore);
      
      console.log(`Phrasensuche: ${finalResults.length} direkte Treffer gefunden`);
      return finalResults;
    }
  }
  
  // Fallback: Normale thematische Suche mit allen Begriffen
  console.log('[NORMALE THEMATISCHE SUCHE] Keine Phrasen in Anführungszeichen oder keine Treffer');
  
  const allResults = new Map();
  
  terms.forEach(term => {
    const wordCount = term.split(' ').length;
    
    // Überspringe zu generische Einzelwörter
    if (wordCount === 1) {
      const veryCommonWords = ['bedeutung', 'welche', 'haben'];
      if (veryCommonWords.includes(term)) {
        console.log(`Überspringe zu generischen Begriff: "${term}"`);
        return;
      }
    }
    
    console.log(`Suche nach Begriff: "${term}"`);
    const termResults = performKeywordSearch(term, filteredParagraphs);
    
    const phraseBoost = wordCount >= 2 ? 10 : 1;
    
    termResults.forEach(result => {
      const key = `${result.ID}-${result.index}`;
      const boostedScore = result.keywordScore * phraseBoost;
      
      if (!allResults.has(key)) {
        allResults.set(key, {
          ...result,
          matchedTerms: result.matchedTerms,
          keywordScore: boostedScore
        });
      } else {
        const existing = allResults.get(key);
        existing.keywordScore += boostedScore * 0.1;
        existing.matchedTerms = [...new Set([...existing.matchedTerms, ...result.matchedTerms])];
      }
    });
  });
  
  const results = Array.from(allResults.values())
    .sort((a, b) => b.keywordScore - a.keywordScore);
  
  console.log(`Thematische Suche: ${results.length} Treffer für ${terms.length} Begriffe`);
  
  return results;
}

function applySemanticRanking(keywordResults, query) {
  const queryLower = query.toLowerCase();
  const queryWords = queryLower.split(/\s+/).filter(w => w.length > 2);
  
  return keywordResults.map(result => {
    let semanticScore = result.keywordScore;
    const content = (result.content || '').toLowerCase();
    
    queryWords.forEach(word => {
      const wordIndex = content.indexOf(word);
      if (wordIndex !== -1) {
        queryWords.forEach(otherWord => {
          if (word !== otherWord) {
            const otherIndex = content.indexOf(otherWord);
            if (otherIndex !== -1) {
              const distance = Math.abs(wordIndex - otherIndex);
              if (distance < 100) {
                semanticScore += Math.max(0, 10 - distance / 10);
              }
            }
          }
        });
      }
    });
    
    const philosophicalTerms = [
      'erkenntnis', 'wahrheit', 'wirklichkeit', 'geist', 'seele', 
      'bewusstsein', 'denken', 'anschauung', 'begriff'
    ];
    
    philosophicalTerms.forEach(term => {
      if (content.includes(term)) {
        semanticScore += 2;
      }
    });
    
    const idealLength = 500;
    const lengthPenalty = Math.abs(content.length - idealLength) / idealLength;
    semanticScore *= (1 - Math.min(lengthPenalty, 0.5));
    
    return {
      ...result,
      semanticScore: semanticScore,
      finalScore: semanticScore
    };
  }).sort((a, b) => b.finalScore - a.finalScore);
}

// Hilfsfunktion: Relevanz-Scoring für Stichwortsuche-Ergebnisse hinzufügen
function addRelevanceScoringToResults(results, query) {
  console.log(`[RELEVANCE-SCORING] Füge Relevanz-Scores für ${results.length} Ergebnisse hinzu`);
  
  // Zerlege Query in einzelne Wörter (für Zwei-Wort-Suchen)
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 0);
  const isTwoWordQuery = queryWords.length === 2;
  
  if (isTwoWordQuery) {
    console.log(`[RELEVANCE-SCORING] Zwei-Wort-Suche erkannt: "${queryWords[0]}" + "${queryWords[1]}"`);
  }
  
  // Gruppiere Ergebnisse nach Vortrag
  const lectureGroups = {};
  results.forEach(result => {
    const lectureId = result.ID;
    if (!lectureGroups[lectureId]) {
      lectureGroups[lectureId] = [];
    }
    lectureGroups[lectureId].push(result);
  });
  
  // Berechne Relevanz-Score für jeden Vortrag
  const resultsWithRelevance = results.map(result => {
    const lectureId = result.ID;
    const lectureResults = lectureGroups[lectureId];
    
    let relevanceScore;
    
    if (isTwoWordQuery) {
      // Spezielle Behandlung für Zwei-Wort-Suchen
      relevanceScore = calculateTwoWordRelevanceScore(lectureResults, queryWords[0], queryWords[1]);
    } else {
      // Einzelwort-Suche
      relevanceScore = calculateRelevanceScoreForLecture(lectureResults, query);
    }
    
    // Debug-Ausgabe für die ersten 5 Vorträge
    if (Object.keys(lectureGroups).indexOf(lectureId) < 5) {
      console.log(`[RELEVANCE-DEBUG] ${lectureId}: Score=${relevanceScore.toFixed(3)}, Chunks=${lectureResults.length}`);
    }
    
    // Bestimme Relevanz-Kategorie (stark erhöhte Schwellwerte für bessere Differenzierung)
    let relevanceCategory = 'niedrig';
    if (relevanceScore >= 0.50) {
      relevanceCategory = 'hoch';      // Score ≥ 0.50 (verdoppelt)
    } else if (relevanceScore >= 0.20) {
      relevanceCategory = 'mittel';    // Score ≥ 0.20 und < 0.50 (verdoppelt)
    }
    // else bleibt 'niedrig' (Score < 0.20)
    
    return {
      ...result,
      relevanceScore: relevanceScore,
      relevanceCategory: relevanceCategory
    };
  });
  
  console.log(`[RELEVANCE-SCORING] Relevanz-Kategorien: ${Object.values(resultsWithRelevance).reduce((acc, r) => {
    acc[r.relevanceCategory] = (acc[r.relevanceCategory] || 0) + 1;
    return acc;
  }, {})}`);
  
  return resultsWithRelevance;
}

// ============================================================================
// ZWEI-WORT-RELEVANZ-BERECHNUNG
// ============================================================================

function calculateTwoWordRelevanceScore(lectureResults, word1, word2) {
  if (!lectureResults || lectureResults.length === 0) return 0;
  
  const word1Lower = word1.toLowerCase();
  const word2Lower = word2.toLowerCase();
  const phraseQuery = `${word1Lower} ${word2Lower}`;
  
  // Sortiere Ergebnisse nach paragraphIndex
  const sortedResults = [...lectureResults].sort((a, b) => 
    (a.paragraphIndex || 0) - (b.paragraphIndex || 0)
  );
  
  // Erstelle zusammenhängenden Text mit Wort-Positionen
  let fullText = '';
  let wordPositions = []; // [{ word, wordIndex, startPos, endPos }]
  let currentWordIndex = 0;
  
  sortedResults.forEach((result) => {
    const content = result.content || '';
    const words = content.split(/\s+/);
    
    words.forEach(word => {
      const startPos = fullText.length;
      fullText += word + ' ';
      const endPos = fullText.length;
      
      wordPositions.push({
        word: word,
        wordIndex: currentWordIndex,
        startPos: startPos,
        endPos: endPos
      });
      
      currentWordIndex++;
    });
  });
  
  const totalWords = currentWordIndex;
  const fullTextLower = fullText.toLowerCase();
  
  // 1. Zähle Einzelwort-Vorkommen
  let word1Count = 0;
  let word2Count = 0;
  let phraseCount = 0;
  
  let word1Positions = [];
  let word2Positions = [];
  
  // Zähle word1
    let pos = 0;
  while ((pos = fullTextLower.indexOf(word1Lower, pos)) !== -1) {
    word1Count++;
    word1Positions.push(pos);
    pos += word1Lower.length;
  }
  
  // Zähle word2
  pos = 0;
  while ((pos = fullTextLower.indexOf(word2Lower, pos)) !== -1) {
    word2Count++;
    word2Positions.push(pos);
    pos += word2Lower.length;
  }
  
  // Zähle exakte Phrase
  pos = 0;
  while ((pos = fullTextLower.indexOf(phraseQuery, pos)) !== -1) {
    phraseCount++;
    pos += phraseQuery.length;
  }
  
  if (word1Count === 0 || word2Count === 0) return 0;
  
  console.log(`[2-WORD] "${word1}" (${word1Count}×) + "${word2}" (${word2Count}×), Phrase: ${phraseCount}×`);
  
  // 2. Berechne Nähe-Bonus: Wie oft stehen die Wörter nah beieinander?
  let proximityPairs = 0;
  const MAX_DISTANCE = 50; // Zeichen
  
  word1Positions.forEach(pos1 => {
    word2Positions.forEach(pos2 => {
      const distance = Math.abs(pos1 - pos2);
      if (distance > 0 && distance <= MAX_DISTANCE) {
        proximityPairs++;
      }
    });
  });
  
  console.log(`[2-WORD] Nähe-Paare (≤50 Zeichen): ${proximityPairs}`);
  
  // 3. Sliding Window über 1000 Wörter
  const WINDOW_SIZE = 1000;
  let bestWindowScore = 0;
  
  for (let startWordIdx = 0; startWordIdx < totalWords; startWordIdx += 250) {
    const endWordIdx = Math.min(startWordIdx + WINDOW_SIZE, totalWords);
    if (startWordIdx >= totalWords) break;
    
    const windowStartPos = wordPositions[startWordIdx]?.startPos || 0;
    const windowEndPos = wordPositions[endWordIdx - 1]?.endPos || fullText.length;
    const windowText = fullTextLower.substring(windowStartPos, windowEndPos);
    
    // Zähle beide Wörter im Fenster
    let window_word1 = 0;
    let window_word2 = 0;
    let window_phrase = 0;
    
    let wPos = 0;
    while ((wPos = windowText.indexOf(word1Lower, wPos)) !== -1) {
      window_word1++;
      wPos += word1Lower.length;
    }
    
    wPos = 0;
    while ((wPos = windowText.indexOf(word2Lower, wPos)) !== -1) {
      window_word2++;
      wPos += word2Lower.length;
    }
    
    wPos = 0;
    while ((wPos = windowText.indexOf(phraseQuery, wPos)) !== -1) {
      window_phrase++;
      wPos += phraseQuery.length;
    }
    
    if (window_word1 > 0 && window_word2 > 0) {
      const actualWindowWords = endWordIdx - startWordIdx;
      const windowLength = windowEndPos - windowStartPos;
      
      // Normalisiere auf 1000 Wörter
      const normalized_word1 = actualWindowWords < WINDOW_SIZE ? 
        (window_word1 / actualWindowWords) * WINDOW_SIZE : window_word1;
      const normalized_word2 = actualWindowWords < WINDOW_SIZE ? 
        (window_word2 / actualWindowWords) * WINDOW_SIZE : window_word2;
      
      // Kombinierter Score:
      // - Beide Wörter müssen vorkommen (Minimum-basiert)
      // - Phrase-Bonus (extra hoch bewertet)
      const minOccurrences = Math.min(normalized_word1, normalized_word2);
      const avgOccurrences = (normalized_word1 + normalized_word2) / 2;
      
      const proximityScore = Math.pow(minOccurrences, 0.8) * Math.sqrt(avgOccurrences);
      const phraseBonus = window_phrase > 0 ? Math.pow(window_phrase, 1.5) * 2.0 : 1.0;
      const density = (window_word1 + window_word2) / Math.max(windowLength, 1);
      
      const windowScore = proximityScore * phraseBonus * density * 
                          (1 + Math.log(window_word1 + window_word2 + 1));
      
      if (windowScore > bestWindowScore) {
        bestWindowScore = windowScore;
      }
    }
  }
  
  // 4. Lade BEIDE Kontext-Indices
  const contextIndex1 = loadContextIndex(word1Lower);
  const contextIndex2 = loadContextIndex(word2Lower);
  
  // 5. Berechne Kontext-Relevanz für beide Wörter (Durchschnitt)
  const contextRelevance1 = calculateContextRelevance(fullText, word1Lower, contextIndex1);
  const contextRelevance2 = calculateContextRelevance(fullText, word2Lower, contextIndex2);
  const avgContextRelevance = (contextRelevance1 + contextRelevance2) / 2;
  
  console.log(`[2-WORD-CONTEXT] "${word1}": ${contextRelevance1.toFixed(2)}, "${word2}": ${contextRelevance2.toFixed(2)}, Avg: ${avgContextRelevance.toFixed(2)}`);
  
  // 6. Finaler Score
  const totalOccurrenceFactor = Math.sqrt(word1Count + word2Count);
  const proximityFactor = proximityPairs > 0 ? 1.0 + Math.log(proximityPairs + 1) * 0.3 : 1.0;
  const phraseFactor = phraseCount > 0 ? 1.0 + Math.log(phraseCount + 1) * 0.5 : 1.0;
  
  const finalScore = bestWindowScore * 
                     totalOccurrenceFactor * 
                     avgContextRelevance * 
                     proximityFactor * 
                     phraseFactor * 
                     5; // Skalierung
  
  console.log(`[2-WORD-FINAL] BestWindow=${bestWindowScore.toFixed(4)}, TotalOcc=${totalOccurrenceFactor.toFixed(2)}, Proximity=${proximityFactor.toFixed(2)}, Phrase=${phraseFactor.toFixed(2)}, Context=${avgContextRelevance.toFixed(2)}, Score=${Math.min(finalScore, 1).toFixed(3)}`);
  
  return Math.min(finalScore, 1);
}

// Kontext-Index Cache (wird beim Start geladen)
let contextIndexCache = {};

// Hilfsfunktion: Ist ein Wort ein Substantiv? (Heuristik)
function isSubstantive(word) {
  const cleaned = word.replace(/[^\w]/g, '');
  
  if (cleaned.length < 3) return false;
  if (!cleaned[0] || cleaned[0] !== cleaned[0].toUpperCase()) return false;
  
  const stopwords = new Set(['Der', 'Die', 'Das', 'Dem', 'Den', 'Des', 'Ein', 'Eine', 'Einer', 
                             'Eines', 'Einem', 'Einen', 'Und', 'Oder', 'Aber', 'Wenn', 'Dann',
                             'Wie', 'Was', 'Wer', 'Wo', 'Warum', 'Wann', 'Auch', 'Nur', 'Noch',
                             'Schon', 'Sehr', 'Mehr', 'Alle', 'Jede', 'Jeder', 'Jedes', 'Manche',
                             'Einige', 'Viele', 'Wenige', 'Andere', 'Solche', 'Welche']);
  
  return !stopwords.has(cleaned);
}

// Generiere Kontext-Index on-the-fly
function generateContextIndex(query, contextWords = 100, minOccurrences = 3) {
  console.log(`[CONTEXT] Generiere Kontext-Index für "${query}" (±${contextWords} Wörter)...`);
  
  const queryLower = query.toLowerCase();
  const allContextWords = [];
  let totalOccurrences = 0;
  let lecturesWithTerm = 0;
  
  // Durchsuche alle Vorträge
  Object.values(fullLectures).forEach(lecture => {
    const paragraphs = lecture.paragraphs || [];
    const fullText = paragraphs.map(p => p.content || p.text || '').join(' ');
    const words = fullText.split(/\s+/);
    
    // Zähle Vorkommen
    const occurrences = fullText.toLowerCase().split(queryLower).length - 1;
    
    if (occurrences > 0) {
      totalOccurrences += occurrences;
      lecturesWithTerm++;
      
      // Extrahiere Kontextwörter um jeden Treffer
      for (let i = 0; i < words.length; i++) {
        if (words[i].toLowerCase().includes(queryLower)) {
          const start = Math.max(0, i - contextWords);
          const end = Math.min(words.length, i + contextWords + 1);
          const context = words.slice(start, i).concat(words.slice(i + 1, end));
          allContextWords.push(...context);
        }
      }
    }
  });
  
  if (totalOccurrences === 0) {
    console.log(`[CONTEXT] Keine Vorkommen gefunden für "${query}"`);
    return null;
  }
  
  console.log(`[CONTEXT] ${totalOccurrences} Vorkommen in ${lecturesWithTerm} Vorträgen`);
  
  // Filtere Substantive
  const substantives = allContextWords.filter(isSubstantive);
  
  // Zähle Häufigkeiten
  const wordCounts = {};
  substantives.forEach(word => {
    wordCounts[word] = (wordCounts[word] || 0) + 1;
  });
  
  // Filtere nach Mindesthäufigkeit und sortiere
  const filtered = {};
  Object.entries(wordCounts)
    .filter(([word, count]) => count >= minOccurrences)
    .sort((a, b) => b[1] - a[1])
    .forEach(([word, count]) => {
      filtered[word] = count;
    });
  
  const result = {
    query: query,
    context_words: contextWords,
    total_occurrences: totalOccurrences,
    lectures_with_term: lecturesWithTerm,
    lectures_count: Object.keys(fullLectures).length, // Gesamtanzahl aller Vorträge
    context_terms: filtered,
    generated_at: new Date().toISOString()
  };
  
  // Speichere in zentrale Indizes-Datei mit automatischer Bereinigung
  try {
    const fs = require('fs');
    const path = require('path');
    const indicesFile = path.join(__dirname, 'context-indices.json');
    
    // Lade bestehende Indizes
    let allIndices = {};
    if (fs.existsSync(indicesFile)) {
      try {
        allIndices = JSON.parse(fs.readFileSync(indicesFile, 'utf-8'));
      } catch (e) {
        console.log(`[CONTEXT] Fehler beim Laden bestehender Indizes: ${e.message}`);
      }
    }
    
    // Füge neuen Index hinzu (überschreibt alten Index für gleichen Query)
    allIndices[queryLower] = result;
    
    // BEREINIGUNG: Alte und ungenutzte Indices entfernen
    const MAX_INDICES = 100; // Maximal 100 verschiedene Keywords speichern
    const MAX_AGE_DAYS = 90; // Indices älter als 90 Tage löschen
    const currentDate = new Date();
    
    // Filtere veraltete Indices
    const validIndices = {};
    let removedCount = 0;
    
    Object.entries(allIndices).forEach(([key, indexData]) => {
      const generatedAt = new Date(indexData.generated_at || 0);
      const ageInDays = (currentDate - generatedAt) / (1000 * 60 * 60 * 24);
      
      if (ageInDays <= MAX_AGE_DAYS) {
        validIndices[key] = indexData;
      } else {
        removedCount++;
        console.log(`[CONTEXT-CLEANUP] Entferne veralteten Index: "${key}" (${ageInDays.toFixed(0)} Tage alt)`);
      }
    });
    
    // Wenn immer noch zu viele: Behalte nur die neuesten MAX_INDICES
    if (Object.keys(validIndices).length > MAX_INDICES) {
      const sortedByDate = Object.entries(validIndices)
        .sort((a, b) => {
          const dateA = new Date(a[1].generated_at || 0);
          const dateB = new Date(b[1].generated_at || 0);
          return dateB - dateA; // Neueste zuerst
        })
        .slice(0, MAX_INDICES); // Behalte nur die neuesten MAX_INDICES
      
      const limitRemovedCount = Object.keys(validIndices).length - MAX_INDICES;
      allIndices = Object.fromEntries(sortedByDate);
      console.log(`[CONTEXT-CLEANUP] ${limitRemovedCount} älteste Indices entfernt (Limit: ${MAX_INDICES})`);
    } else {
      allIndices = validIndices;
    }
    
    if (removedCount > 0) {
      console.log(`[CONTEXT-CLEANUP] Gesamt ${removedCount} veraltete Indices entfernt`);
    }
    
    // Speichere zurück
    fs.writeFileSync(indicesFile, JSON.stringify(allIndices, null, 2), 'utf-8');
    console.log(`[CONTEXT] Index gespeichert in context-indices.json: ${Object.keys(filtered).length} Begriffe (${Object.keys(allIndices).length} Indices gesamt)`);
  } catch (error) {
    console.log(`[CONTEXT] Fehler beim Speichern: ${error.message}`);
  }
  
  return result;
}

// Lade oder generiere Kontext-Index für einen Suchbegriff
function loadContextIndex(query) {
  const queryLower = query.toLowerCase();
  
  // Prüfe Cache
  if (contextIndexCache[queryLower]) {
    return contextIndexCache[queryLower];
  }
  
  // Versuche aus zentraler Indizes-Datei zu laden
  try {
    const fs = require('fs');
    const path = require('path');
    const indicesFile = path.join(__dirname, 'context-indices.json');
    
    if (fs.existsSync(indicesFile)) {
      const allIndices = JSON.parse(fs.readFileSync(indicesFile, 'utf-8'));
      
      if (allIndices[queryLower]) {
        const data = allIndices[queryLower];
        
        // Prüfe ob Index veraltet ist (Datenbank gewachsen?)
        const currentLectureCount = Object.keys(fullLectures).length;
        const indexedLectureCount = data.lectures_count || 0;
        const growthPercent = ((currentLectureCount - indexedLectureCount) / indexedLectureCount) * 100;
        
        // Wenn Datenbank um >5% gewachsen ist, regeneriere Index
        if (growthPercent > 5) {
          console.log(`[CONTEXT] Index veraltet (${indexedLectureCount} -> ${currentLectureCount} Vorträge, +${growthPercent.toFixed(1)}%), regeneriere...`);
          // Springe zur Regenerierung (weiter unten im Code)
        } else {
          contextIndexCache[queryLower] = data;
          console.log(`[CONTEXT] Kontext-Index geladen: ${Object.keys(data.context_terms).length} Begriffe (${indexedLectureCount} Vorträge)`);
          return data;
        }
      }
    }
  } catch (error) {
    console.log(`[CONTEXT] Fehler beim Laden: ${error.message}`);
  }
  
  // Falls nicht vorhanden: Prüfe ob genug Vorkommen für Index-Generierung
  // Schnelle Vorkommen-Prüfung
  let totalOccurrences = 0;
  Object.values(fullLectures).forEach(lecture => {
    const paragraphs = lecture.paragraphs || [];
    const fullText = paragraphs.map(p => p.content || p.text || '').join(' ');
    totalOccurrences += (fullText.toLowerCase().match(new RegExp(queryLower, 'g')) || []).length;
  });
  
  console.log(`[CONTEXT] "${query}" hat ${totalOccurrences} Vorkommen gesamt`);
  
  // Nur für häufigere Begriffe (≥5 Vorkommen) Index generieren
  if (totalOccurrences >= 5) {
    console.log(`[CONTEXT] Generiere Index (≥5 Vorkommen)...`);
    const newIndex = generateContextIndex(query);
    
    if (newIndex) {
      contextIndexCache[queryLower] = newIndex;
    }
    
    return newIndex;
  } else {
    console.log(`[CONTEXT] Zu wenige Vorkommen (<5), kein Index generiert`);
    return null;
  }
}

// Berechne Kontext-Relevanz: Wie viele typische Kontextwörter kommen im Vortrag vor?
function calculateContextRelevance(fullText, query, contextIndex) {
  if (!contextIndex || !contextIndex.context_terms) {
    return 1.0; // Neutral, wenn kein Kontext-Index vorhanden
  }
  
  const fullTextLower = fullText.toLowerCase();
  const contextTerms = contextIndex.context_terms;
  const topTerms = Object.entries(contextTerms)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 50); // Nutze Top 50 Kontextwörter
  
  let matchedTerms = 0;
  let weightedMatches = 0;
  
  for (const [term, frequency] of topTerms) {
    const termLower = term.toLowerCase();
    
    // Zähle Vorkommen des Kontextworts im Vortrag
    let count = 0;
    let pos = 0;
    while ((pos = fullTextLower.indexOf(termLower, pos)) !== -1) {
      count++;
      pos += termLower.length;
    }
    
    if (count > 0) {
      matchedTerms++;
      // Gewichte nach Häufigkeit im Kontext-Index
      weightedMatches += Math.min(count, 5) * Math.log(frequency + 1);
    }
  }
  
  // Normalisiere: Je mehr typische Kontextwörter vorkommen, desto höher die Relevanz
  const matchRatio = matchedTerms / Math.min(topTerms.length, 20); // Normiere auf Top 20
  const contextRelevance = 1.0 + (matchRatio * 2.0); // Faktor 1.0 - 3.0
  
  return Math.min(contextRelevance, 3.0);
}

// Hilfsfunktion: Relevanz-Score für einen Vortrag berechnen (1000-Wörter-Fenster + Kontext Version)
function calculateRelevanceScoreForLecture(lectureResults, query) {
  if (!lectureResults || lectureResults.length === 0) return 0;
  
  const queryLower = query.toLowerCase();
  
  // Sortiere Ergebnisse nach paragraphIndex
  const sortedResults = [...lectureResults].sort((a, b) => 
    (a.paragraphIndex || 0) - (b.paragraphIndex || 0)
  );
  
  // Erstelle einen zusammenhängenden Text mit Wort-Positionen
  let fullText = '';
  let wordPositions = []; // [{ wordIndex, paragraphIndex, startPos, endPos }]
  let currentWordIndex = 0;
  
  sortedResults.forEach((result, paraIdx) => {
    const content = result.content || '';
    const words = content.split(/\s+/);
    
    words.forEach(word => {
      const startPos = fullText.length;
      fullText += word + ' ';
      const endPos = fullText.length;
      
      wordPositions.push({
        wordIndex: currentWordIndex,
        paragraphIndex: paraIdx,
        startPos: startPos,
        endPos: endPos
      });
      
      currentWordIndex++;
    });
  });
  
  const totalWords = currentWordIndex;
  const fullTextLower = fullText.toLowerCase();
  
  // 1. Parameter: Gesamtvorkommen im ganzen Text zählen
  let totalOccurrences = 0;
  let occurrencePositions = [];
  let pos = 0;
  while ((pos = fullTextLower.indexOf(queryLower, pos)) !== -1) {
    totalOccurrences++;
    occurrencePositions.push(pos);
    pos += queryLower.length;
  }
  
  if (totalOccurrences === 0) return 0;
  
  // 2. Sliding Window über 1000 Wörter
  const WINDOW_SIZE = 1000; // Wörter
  let bestWindowScore = 0;
  
  // Verschiebe das Fenster über den Text (Schrittweite: 250 Wörter für Performance)
  for (let startWordIdx = 0; startWordIdx < totalWords; startWordIdx += 250) {
    const endWordIdx = Math.min(startWordIdx + WINDOW_SIZE, totalWords);
    
    if (startWordIdx >= totalWords) break;
    
    // Bestimme Textbereich für dieses Fenster
    const windowStartPos = wordPositions[startWordIdx]?.startPos || 0;
    const windowEndPos = wordPositions[endWordIdx - 1]?.endPos || fullText.length;
    const windowText = fullTextLower.substring(windowStartPos, windowEndPos);
    
    // Zähle Vorkommen in diesem Fenster
    let windowOccurrences = 0;
    let windowPos = 0;
    while ((windowPos = windowText.indexOf(queryLower, windowPos)) !== -1) {
      windowOccurrences++;
      windowPos += queryLower.length;
    }
    
    if (windowOccurrences > 0) {
      const actualWindowWords = endWordIdx - startWordIdx;
      
      // SCHRITT 1: Proximity-Score (Häufigkeit pro 1000 Wörter)
      // Normalisiere auf 1000 Wörter, falls Fenster kleiner
      const normalizedOccurrences = actualWindowWords < WINDOW_SIZE ? 
        (windowOccurrences / actualWindowWords) * WINDOW_SIZE : windowOccurrences;
      
      // Proximity-Score: Je mehr Vorkommen im 1000-Wörter-Fenster, desto höher
      // Reduzierter Exponent für mehr Differenzierung
      const proximityScore = Math.pow(normalizedOccurrences, 1.0); // Von 1.3 auf 1.0 reduziert (linear)
      
      // SCHRITT 2: Dichte-Bewertung (Vorkommen pro Zeichen im Fenster)
      const windowLength = windowEndPos - windowStartPos;
      const densityInWindow = windowOccurrences / Math.max(windowLength, 1);
      
      // Kombinierter Window-Score
      const windowScore = 
        proximityScore *                        // Proximity (Häufigkeit im Fenster)
        densityInWindow *                       // Dichte (Zeichen-basiert)
        (1 + Math.log(windowOccurrences + 1)); // Log-Bonus
      
      // Behalte besten Window-Score
      if (windowScore > bestWindowScore) {
        bestWindowScore = windowScore;
      }
    }
  }
  
  // 3. Kontext-Relevanz berechnen
  const contextIndex = loadContextIndex(query);
  const contextRelevance = calculateContextRelevance(fullText, query, contextIndex);
  
  // 4. Normalisierung mit Gesamtvorkommen
  const totalOccurrenceFactor = Math.sqrt(totalOccurrences);
  
  // Finaler Score = Window-Score × Gesamtvorkommen × Kontext-Relevanz × Skalierung
  const finalScore = bestWindowScore * totalOccurrenceFactor * contextRelevance * 5;
  
  // Debug-Ausgabe
  if (totalOccurrences > 0) {
    console.log(`[RELEVANCE-CONTEXT] Query="${query}", TotalOcc=${totalOccurrences}, BestWindow=${bestWindowScore.toFixed(6)}, Context=${contextRelevance.toFixed(2)}, FinalScore=${Math.min(finalScore, 1).toFixed(3)}`);
  }
  
  return Math.min(finalScore, 1);
}

async function performHybridSearch(query, limit = 20) {
  try {
    const keywordResults = performKeywordSearch(query, paragraphsFromLectures);
    
    if (keywordResults.length === 0) {
      return {
        results: [],
        method: 'hybrid-keyword',
        message: 'Keine Treffer gefunden'
      };
    }
    
    // NEU: Relevanz-Scoring für jeden Vortrag hinzufügen
    const resultsWithRelevance = addRelevanceScoringToResults(keywordResults, query);
    
    const rankedResults = applySemanticRanking(resultsWithRelevance, query);
    const topResults = rankedResults.slice(0, limit);
    
    console.log(`Hybrid: ${keywordResults.length} Keywords -> ${topResults.length} Final`);
    
    return {
      results: topResults,
      method: 'hybrid-keyword-semantic',
      totalKeywordMatches: keywordResults.length,
      finalResults: topResults.length
    };
    
  } catch (error) {
    console.error('Hybrid-Suche Fehler:', error);
    throw error;
  }
}

// ============================================================================
// VOLLTEXT-SUCHE
// ============================================================================

app.post('/api/fulltext-search', async (req, res) => {
  try {
    const { word1, word2, word1IsPhrase = false, word2IsPhrase = false, proximity = null, relevanceFilter = 'alle', yearFilter = '' } = req.body;
    
    if (!word1) {
      return res.status(400).json({ error: 'Mindestens ein Suchwort erforderlich' });
    }
    
    // Bei Zwei-Wort-Suche ohne explizite Proximity: Setze automatisch auf max. 3 Absätze
    let effectiveProximity = proximity;
    if (word2 && !proximity) {
      effectiveProximity = 3;
      console.log(`[2-WORD-PROXIMITY] Automatische Proximity für Zwei-Wort-Suche: max. 3 Absätze`);
    }
    
    console.log(`Volltext-Suche: ${word1IsPhrase ? '"' : ''}${word1}${word1IsPhrase ? '"' : ''}${word2 ? ` + ${word2IsPhrase ? '"' : ''}${word2}${word2IsPhrase ? '"' : ''}` : ''}${effectiveProximity ? ` (Proximity: ${effectiveProximity})` : ''} [Relevanz-Filter: ${relevanceFilter}]${yearFilter ? ` [Jahr-Filter: ${yearFilter}]` : ''}`);
    
    // Hilfsfunktion für exakte Phrasensuche oder flexible Wortsuche
    const searchInText = (text, searchTerm, isPhrase) => {
      if (!searchTerm) return false;
      const textLower = text.toLowerCase();
      const termLower = searchTerm.toLowerCase();
      
      if (isPhrase) {
        // Exakte Phrasensuche: Wortgrenzen beachten
        // \b funktioniert nicht gut mit Umlauten, daher verwende manuelle Wortgrenze
        const escapedTerm = termLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(^|[\\s,.;:!?()\\-—])${escapedTerm}($|[\\s,.;:!?()\\-—])`, 'i');
        return regex.test(text);
      } else {
        // Flexible Suche: auch Teilwörter erlaubt
        return textLower.includes(termLower);
      }
    };
    
    const results = [];
    const addedParagraphs = new Set();
    
    Object.values(fullLectures).forEach(lecture => {
      // Jahr-Filter: Überspringe Vorträge, die nicht dem ausgewählten Jahr entsprechen
      if (yearFilter) {
        const lectureYear = lecture.date ? lecture.date.substring(0, 4) : '';
        
        // Prüfe ob es ein Jahresbereich ist (z.B. "1910-1915")
        if (yearFilter.includes('-')) {
          const [startYear, endYear] = yearFilter.split('-').map(y => y.trim());
          if (lectureYear < startYear || lectureYear > endYear) {
            return; // Überspringe diesen Vortrag (außerhalb des Bereichs)
          }
        } else {
          // Einzelnes Jahr
          if (lectureYear !== yearFilter) {
            return; // Überspringe diesen Vortrag
          }
        }
      }
      
      const paragraphs = lecture.paragraphs || [];
      
      paragraphs.forEach((para, paraIndex) => {
        const content = (para.content || para.text || '');
        const hasWord1 = word1 && searchInText(content, word1, word1IsPhrase);
        const hasWord2 = word2 && searchInText(content, word2, word2IsPhrase);
        
        const paragraphsToAdd = [];
        
        if (!word2) {
          // Einzelwort-Suche
          if (hasWord1) {
            paragraphsToAdd.push(paraIndex);
          }
        } else if (!effectiveProximity) {
          // Zwei-Wort-Suche OHNE Proximity (sollte nicht mehr vorkommen, da effectiveProximity automatisch gesetzt wird)
          if (hasWord1 || hasWord2) {
            paragraphsToAdd.push(paraIndex);
          }
        } else {
          // Zwei-Wort-Suche MIT Proximity (Standard: max. 2 Absätze)
          const maxDist = parseInt(effectiveProximity);
          
          if (hasWord1 && hasWord2) {
            // Beide Wörter im gleichen Absatz → immer hinzufügen
            paragraphsToAdd.push(paraIndex);
          } else if (hasWord1) {
            // Nur word1 im aktuellen Absatz → suche word2 in benachbarten Absätzen
            for (let i = Math.max(0, paraIndex - maxDist); i <= Math.min(paragraphs.length - 1, paraIndex + maxDist); i++) {
              if (i !== paraIndex) {
                const neighborContent = (paragraphs[i].content || paragraphs[i].text || '');
                if (searchInText(neighborContent, word2, word2IsPhrase)) {
                  paragraphsToAdd.push(paraIndex);
                  paragraphsToAdd.push(i);
                  break;
                }
              }
            }
          } else if (hasWord2) {
            // Nur word2 im aktuellen Absatz → suche word1 in benachbarten Absätzen
            for (let i = Math.max(0, paraIndex - maxDist); i <= Math.min(paragraphs.length - 1, paraIndex + maxDist); i++) {
              if (i !== paraIndex) {
                const neighborContent = (paragraphs[i].content || paragraphs[i].text || '');
                if (searchInText(neighborContent, word1, word1IsPhrase)) {
                  paragraphsToAdd.push(paraIndex);
                  paragraphsToAdd.push(i);
                  break;
                }
              }
            }
          }
        }
        
        paragraphsToAdd.forEach(idx => {
          const key = `${lecture.ID}-${idx}`;
          if (!addedParagraphs.has(key)) {
            addedParagraphs.add(key);
            const p = paragraphs[idx];
            const pContent = (p.content || p.text || '');
            
            results.push({
              ID: lecture.ID,
              title: lecture.title,
              fileName: lecture.fileName,
              location: lecture.location,
              date: lecture.date,
              paragraphIndex: idx,
              index: p.index,
              content: p.content || p.text,
              hasWord1: searchInText(pContent, word1, word1IsPhrase),
              hasWord2: word2 && searchInText(pContent, word2, word2IsPhrase)
            });
          }
        });
      });
    });
    
    console.log(`Volltext-Suche: ${results.length} Absätze gefunden`);
    
    // NEU: Relevanz-Scoring für Volltext-Suche hinzufügen (außer bei "ohne")
    let resultsWithRelevance;
    if (relevanceFilter === 'ohne') {
      // Schnelle Suche ohne Relevanzberechnung
      console.log('[RELEVANZ] Überspringe Relevanzberechnung (Filter: ohne)');
      resultsWithRelevance = results;
    } else {
    const searchQuery = word2 ? `${word1} ${word2}` : word1;
      resultsWithRelevance = addRelevanceScoringToResults(results, searchQuery);
    }
    
    // Backend-Filterung nach Relevanz
    let filteredResults = resultsWithRelevance;
    if (relevanceFilter && relevanceFilter !== 'alle' && relevanceFilter !== 'ohne') {
      filteredResults = resultsWithRelevance.filter(r => r.relevanceCategory === relevanceFilter);
      console.log(`[BACKEND-FILTER] ${resultsWithRelevance.length} -> ${filteredResults.length} Ergebnisse nach Filter "${relevanceFilter}"`);
    }
    
    // Query-Tracking
    if (word1) trackQueryTerms(word1, filteredResults.length);
    if (word2) trackQueryTerms(word2, filteredResults.length);
    
    res.json({
      query: { 
        word1, 
        word2, 
        word1IsPhrase, 
        word2IsPhrase, 
        proximity: effectiveProximity, // Verwende effectiveProximity statt proximity
        originalProximity: proximity,   // Optional: ursprünglicher Wert
        relevanceFilter 
      },
      results: filteredResults,
      resultCount: filteredResults.length,
      unfilteredCount: resultsWithRelevance.length
    });
    
  } catch (error) {
    console.error('Volltext-Suche Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// LLM ANALYSE
// ============================================================================

async function generateAnalysis(query, results, depth = 'allgemein') {
  console.log('generateAnalysis aufgerufen für:', query, '| Depth:', depth, '| Results:', results.length);
  
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('Kein Claude API Key - verwende Fallback');
    return generateFallbackAnalysis(query, results);
  }
  
  const topResults = results;  // Verwende alle übergebenen Ergebnisse gemäß aktuellem Limit

  console.log('=== DEBUG topResults ===');
  console.log('Erste 3 topResults:', JSON.stringify(topResults.slice(0, 3).map(r => ({ 
    ID: r.ID, 
    index: r.index,
    fileName: r.fileName 
  })), null, 2));
  
  const contextText = topResults
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      return `[${refId}] ${result.fileName || result.title}\n${result.content}`;
    })
    .join('\n\n---\n\n');
    
  const availableRefs = topResults.map(r => `${r.ID}:${r.index}`).join(', ');
  
  console.log(`Claude bekommt Referenzen im Format GA###/##:index`);
  
  const maxTokens = {
    'allgemein': 4000,    // Erhöht von 2000 auf 4000
    'ausführlich': 8000   // Erhöht von 6000 auf 8000
  };
  
  // Erzwinge immer den ausführlichen Prompt unabhängig vom übergebenen depth
  const effectiveDepth = 'ausführlich';
  const prompt = `Analysiere die folgenden Textstellen aus Rudolf Steiners Werk zur Frage: "${query}"

ANALYSE-TIEFE: ${effectiveDepth}

Prompt für thematische Textanalyse:
Du bist ein Assistent zur Analyse und Darstellung von Textmaterial aus Rudolf Steiners Gesamtausgabe (GA).
Deine Aufgabe
Erstelle eine thematisch gegliederte Darstellung zu einer Themenanfrage basierend auf vorliegenden Textauszügen.
Arbeitsschritte

Identifiziere die relevanten Suchwörter der Themenanfrage
Lokalisiere alle Textstellen (Absätze), in denen die Suchwörter vorkommen (inklusive Kontext)
Vergleiche die Textstellen auf inhaltliche Ähnlichkeit
Wähle aus: Nur inhaltlich verschiedene Textstellen (keine Redundanzen)
Gliedere das Material mit eigenen, aussagekräftigen Zwischenüberschriften
Beziehe alle Aussagen inhaltlich auf die Suchwörter der Themenanfrage
Schreibe am Ende ein kurzes inhaltliches Fazit
Liste unter dem Fazit die verwendeten Quellenangaben auf

KRITISCH WICHTIG: Stelle nur Aspekte dar, die sich inhaltlich unmittelbar auf die Themenanfrage beziehen. Lasse alles weg, was nur am Rande oder indirekt mit dem Thema zu tun hat.
Inhaltliche Perspektiven (als Orientierung)
Wähle aus folgenden Perspektiven die relevanten aus:

Sachliche Aspekte (konkrete Phänomene, Substanzen, leibliche Prozesse)
Funktionelle Aspekte (Wirkungsweisen, Prozesse, physiologische Aspekte)
Erlebnismäßige und seelisch-psychologische Aspekte
Begriffliche und geistige Aspekte (Ideen, Prinzipien)
Methodische und erkenntnistheoretische Aspekte
Vergleich mit anderen Inhalten
Entwicklung und Evolution
Besonderheiten und Sonstiges

Wichtig: Keine eigenen Bewertungen oder Interpretationen.
Strukturierung

Eigene Zwischenüberschriften (## Format) die den Inhalt ankündigen
NICHT die obigen Kategorienamen als Überschriften verwenden
Beispiele für gute Überschriften:

"Die Verwandlung der Sinneswahrnehmung"
"Drei Stufen der Ich-Entwicklung"
"Der Zusammenhang von Denken und Willen"


Stilistische Anforderungen
Beginne direkt mit konkreten Inhalten:

KEINE einleitenden Sätze wie "Die vorliegenden Textstellen bieten..." oder "Rudolf Steiners Verständnis offenbart sich als..."
Starte unmittelbar mit substanziellen Aussagen oder Zitaten

Formulierungsstil:

Verwende hauptsächlich direkte Zitate in "Anführungszeichen" mit Quellenangaben
Minimaler erläuternder Text - nur zur Verbindung der Zitate
VERMEIDE Formulierungen wie "Steiner sagt/versteht/beschreibt/entwickelt/unterscheidet/behandelt"
Formuliere direkt: "Das Konzept der anschauenden Urteilskraft..." statt "Steiner entwickelt das Konzept..."
Verwende aktive Formulierungen: "Die anschauende Urteilskraft unterscheidet sich..." statt "Steiner unterscheidet..."

Vermeidungen:

Keine redundanten Formulierungen
Keine Dopplungen (jede Information nur einmal)
Keine zusammenfassenden Einleitungen
Keine Paraphrasen von bereits zitierten Stellen

Formatierung

Markdown-Formatierung
Fette wichtige Schlagwörter und zentrale Aussagen
FETT sehr sparsam einsetzen: Innerhalb von Zitaten nur relevante Begriffe/Kernaussagen fett markieren, niemals ganze Zitate; Begriffe/Kernaussagen nur einmal fett markieren (keine Redundanzen) ! wichtig
Zitiere kurz und prägnant - nur das Wesentliche
Halte die Darstellung insgesamt prägnant

Quellenangaben

Nach jeder spezifischen Aussage die Quelle angeben
Format: (GA###/lectureNum:index)
Beispiel: (GA052/7:n5x6ru) oder (GA068a/7:p5fg67)
EIN Leerzeichen VOR der öffnenden Klammer: "Text (GA052/7:n5x6ru)"
KEINE Leerzeichen INNERHALB der Klammern
Vollständiges Format verwenden: Immer GA###/Y:index


Schreibe am Ende der Darstellung ein kurzes inhaltliches Fazit unter der ## Überschrift "Fazit" in einem neuen Absatz
OHNE Quellenangaben im Fazit
Fasse die wesentlichen Erkenntnisse zusammen

Weitere relevante Quellen

Liste unter dem Text unter der ## Überschrift "Weitere relevante Quellen" in einem neuen AbsatzWEITERE relevante Quellen, die im obigen Text NICHT genannt wurden.
Format: GA###/lectureNum:index (wie im Text), ohne Klammern !, komma-getrennt
Jede Quelle nur einmal; verwende keine Quellen, die bereits im Text zitiert wurden
Beispiel: "GA070b/13:abc123, GA080b/4:def456"

Verfügbare Referenzen: ${availableRefs}
Umfang: Du hast ${topResults.length} relevante Textstellen zur Verfügung - nutze sie ausführlich.


TEXTPASSAGEN:
${contextText}

ANALYSE:`;

  try {
    console.log('Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: maxTokens[effectiveDepth] || 8192,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    let analysisText = result.content[0].text;
    
    console.log('Claude Antwort erhalten, Länge:', analysisText.length);
    
    analysisText = addClickableReferences(analysisText, topResults);
    
    console.log('Gesendeter Text enthält <a> Tags:', analysisText.includes('<a'));
    console.log('Beispiel (erste 300 Zeichen):', analysisText.substring(0, 300));
    
    return analysisText;

  } catch (error) {
    console.error('LLM-Analyse Fehler:', error);
    console.error('Error Details:', error.message);
    console.error('Stack:', error.stack);
    return generateFallbackAnalysis(query, results);
  }
}

function addClickableReferences(text, results) {
  console.log('addClickableReferences gestartet');
  console.log('Erste 3 Results:', results.slice(0, 3).map(r => ({ ID: r.ID, index: r.index })));
  
  // Bereich der "Weitere relevante Quellen"-Sektion ermitteln, um dort Klammern zu vermeiden
  const sourcesHeading = '## Weitere relevante Quellen';
  const sourcesStart = text.indexOf(sourcesHeading);
  let sourcesEnd = -1;
  if (sourcesStart !== -1) {
    const after = text.slice(sourcesStart + sourcesHeading.length);
    const nextH2Rel = after.indexOf('\n## ');
    sourcesEnd = nextH2Rel === -1 ? text.length : sourcesStart + sourcesHeading.length + nextH2Rel;
  }

  const refToDataMapping = {};
  
  results.forEach(result => {
    if (result.ID && result.index) {
      const cleanIndex = result.index.replace(/^\^/, '');

      const key1 = `${result.ID}:${result.index}`;
      const key2 = `${result.ID}:${cleanIndex}`;

      const mapping = {
        id: result.ID,
        index: result.index, // Original mit Caret bleibt im Mapping
        title: result.title,
        fileName: result.fileName,
        content: result.content
      };

      refToDataMapping[key1] = mapping;
      refToDataMapping[key2] = mapping;
    }
  });
  
  console.log(`Mapping erstellt für ${Object.keys(refToDataMapping).length} Referenzen`);
  console.log(`Beispiel-Keys:`, Object.keys(refToDataMapping).slice(0, 6));
  
  const gaPattern = /\s*\(?(GA\d{3}[a-z]?\/\d+:\^?[a-z0-9]+)\)?\s*/gi;
  
  let linkedText = text;
  const matches = [];
  let match;
  
  gaPattern.lastIndex = 0;
  
  while ((match = gaPattern.exec(text)) !== null) {
    matches.push({
      fullMatch: match[0],
      fullRef: match[1],
      position: match.index
    });
  }
  
  console.log(`${matches.length} GA-Referenzen gefunden`);
  if (matches.length > 0) {
    console.log(`Erste 3 gefundene Refs:`, matches.slice(0, 3).map(m => m.fullRef));
  }
  
  matches.sort((a, b) => b.position - a.position);
  
  let linksCreated = 0;
  
  matches.forEach(matchInfo => {
    const refClean = matchInfo.fullRef.replace(/:\^/, ':');
    
    const refLower = matchInfo.fullRef.toLowerCase();
    const refCleanLower = refClean.toLowerCase();
    
    const chunkData = refToDataMapping[matchInfo.fullRef] || 
                      refToDataMapping[refClean] ||
                      refToDataMapping[refLower] ||
                      refToDataMapping[refCleanLower];
    
    if (chunkData) {
      const [idPart] = matchInfo.fullRef.split(':');
      // Nur für das data-index Attribut das Caret entfernen
      const cleanIndex = chunkData.index.replace(/^\^/, '');
      // Entferne Klammern aus dem ursprünglichen Text
      const cleanIdPart = idPart.replace(/^\(|\)$/g, '');
      const anchor = `<a href="#" class="ga-reference" data-id="${chunkData.id}" data-index="${cleanIndex}" data-file-name="${chunkData.fileName || ''}">${cleanIdPart}</a>`;
      // In der "Weitere relevante Quellen"-Sektion keine Klammern um die Links
      const inSourcesSection = sourcesStart !== -1 && matchInfo.position >= sourcesStart && (sourcesEnd === -1 || matchInfo.position < sourcesEnd);
      const replacement = inSourcesSection ? ` ${anchor}` : ` (${anchor})`;

      // Das Pattern erfasst bereits Leerzeichen, daher einfache Ersetzung
      linkedText = linkedText.substring(0, matchInfo.position) + 
                   replacement + 
                   linkedText.substring(matchInfo.position + matchInfo.fullMatch.length);

      linksCreated++;
    } else {
      console.warn(`Keine Daten für ${matchInfo.fullRef}`);
      console.warn(`Gesuchte Keys: ${matchInfo.fullRef} und ${refClean}`);
    }
  });
  
  // Anweisung zurückgenommen: keine nachträgliche Verlinkung von GA###/Y ohne Index
  
  console.log(`${linksCreated} von ${matches.length} Links erfolgreich erstellt`);
  console.log('Gesendeter Text enthält <a> Tags:', linkedText.includes('<a'));
  
  return linkedText;
}

function generateFallbackAnalysis(query, results) {
  const topResults = results.slice(0, 10);
  
  let analysis = `# Analyse zu: "${query}"\n\nBasierend auf ${results.length} Textstellen:\n\n`;
  
  topResults.forEach((result, i) => {
    const preview = result.content.substring(0, 250);
    const displayTitle = result.fileName || result.ID;
    analysis += `## ${i + 1}. ${displayTitle}\n\n"${preview}..."\n\n`;
  });
  
  analysis += `**Quellen**: ${topResults.map(r => r.fileName || r.ID).join(', ')}`;
  
  return analysis;
}

// ============================================================================
// VORTRAGS-ZUSAMMENFASSUNG
// ============================================================================

app.post('/api/summarize-lecture', async (req, res) => {
  try {
    const { lectureId, forceRegenerate = false } = req.body;
    
    if (!lectureId) {
      return res.status(400).json({ error: 'Lecture ID erforderlich' });
    }
    
    console.log(`\n→ Zusammenfassung für ${lectureId} angefordert (forceRegenerate: ${forceRegenerate})...`);
    
    // Prüfe zuerst zentrale Summary-Datenbank
    if (!forceRegenerate) {
      const summaryDB = await loadSummaryDatabase();
      if (summaryDB[lectureId]) {
        console.log(`  ✓ Summary aus zentraler DB für ${lectureId}`);
        const dbData = summaryDB[lectureId];
        
        return res.json({
          lectureId: lectureId,
          summary: dbData.summary,
          headings: dbData.headings || [],
          fromCache: true,
          paragraphCount: fullLectures[lectureId]?.paragraphs?.length || 0
        });
      }
    }
    
    const lecture = fullLectures[lectureId];
    
    if (!lecture) {
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}`,
        available: Object.keys(fullLectures).slice(0, 10)
      });
    }
    
    console.log(`  → Generiere neue Zusammenfassung...`);
    const summaryData = await generateLectureSummary(lecture);
    
    // Speichere in zentrale Summary-Datenbank mit robustem Locking
    try {
      await saveSummaryToDatabase(lectureId, {
        summary: summaryData.summary,
        headings: summaryData.headings || []
      });
      console.log(`  ✓ Summary für ${lectureId} sicher in DB gespeichert`);
    } catch (dbError) {
      console.error(`[SPEICHERUNG] ✗ Fehler beim Speichern von ${lectureId}:`, dbError.message);
      // Werfe Fehler nicht weiter, Response sollte trotzdem gesendet werden
    }
    
    console.log(`  ✓ Zusammenfassung erstellt und in zentrale DB gespeichert`);
    
    res.json({
      lectureId: lectureId,
      summary: summaryData.summary,
      headings: summaryData.headings || [],
      fromCache: false,
      paragraphCount: lecture.paragraphs?.length || 0
    });
    
  } catch (error) {
    console.error('✗ Zusammenfassungs-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/check-summary/:gaNumber/:lectureNum', async (req, res) => {
  try {
    const lectureId = `${req.params.gaNumber}/${req.params.lectureNum}`;
    
    console.log(`[CHECK-SUMMARY] Prüfe zentrale DB für ${lectureId}`);
    
    const summaryDB = await loadSummaryDatabase();
    if (summaryDB[lectureId]) {
      const dbData = summaryDB[lectureId];
      
      console.log(`[CHECK-SUMMARY] ✓ Zusammenfassung existiert für ${lectureId}`);
      
      return res.json({
        exists: true,
        lectureId: lectureId,
        summary: dbData.summary,
        headings: dbData.headings || []
      });
    }
    
    console.log(`[CHECK-SUMMARY] ✗ Keine Zusammenfassung für ${lectureId}`);
    
    res.json({
      exists: false,
      lectureId: lectureId,
      summary: null,
      headings: []
    });
    
  } catch (error) {
    console.error('[CHECK-SUMMARY] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

async function generateLectureSummary(lecture) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('Kein Claude API Key - verwende Fallback-Zusammenfassung');
    return generateFallbackSummary(lecture);
  }
  
  const fullText = lecture.paragraphs
    .map((p, idx) => {
      const content = p.content || p.text || '';
      const paraIndex = p.index || `para_${idx}`;
      return `[Index: ${paraIndex}]\n${content}`;
    })
    .filter(text => text.trim().length > 0)
    .join('\n\n');
  
  const estimatedTokens = fullText.length / 4;
  console.log(`Vortrag: ${lecture.ID}, Paragraphen: ${lecture.paragraphs.length}, Geschätzte Tokens: ${Math.round(estimatedTokens)}`);
  
  let textToSummarize = fullText;
  let headingsDisabled = false;
  
  if (estimatedTokens > 180000) {
    console.log('Vortrag zu lang (>180k tokens) - Überschriften deaktiviert, nur Zusammenfassung');
    headingsDisabled = true;
    const halfChunkSize = 360000;
    textToSummarize = fullText.substring(0, halfChunkSize) + 
                     '\n\n[... Mittlerer Teil des Vortrags ausgelassen ...]\n\n' +
                     fullText.substring(fullText.length - halfChunkSize);
  }
  
  const prompt = `Erstelle eine Zusammenfassung${headingsDisabled ? '' : ' und Zwischenüberschriften'} für diesen Vortrag von Rudolf Steiner.

VORTRAG: ${lecture.fileName || lecture.title || lecture.ID}
${lecture.location ? `ORT: ${lecture.location}` : ''}
${lecture.date ? `DATUM: ${lecture.date}` : ''}

Der Vortrag hat ${lecture.paragraphs.length} Absätze.

AUFGABE:
1. Schreibe eine prägnante ZUSAMMENFASSUNG (100-150 Wörter) der Kernaussagen
${headingsDisabled ? '' : `2. Erstelle eine hierarchische Gliederung mit:
   - 3-6 HAUPTÜBERSCHRIFTEN (H3) für die großen thematischen Abschnitte
   - Jeweils 2-4 UNTERÜBERSCHRIFTEN (H4) pro Hauptabschnitt für Unterabschnitte
3. Ordne jede Überschrift einem Absatz-Index zu

WICHTIG ZUR INDEX-ZUORDNUNG:
- Jeder Absatz im Text ist markiert mit [Index: XXXXX] (z.B. [Index: ^1e6ps7])
- Verwende EXAKT diesen Index in deiner Antwort
- Der Index gibt an, VOR welchem Absatz die Überschrift eingefügt wird
- Die Überschrift leitet den FOLGENDEN Abschnitt ein
- Beispiel: Wenn bei [Index: ^1e6ps7] das Thema "Die Sophistik" beginnt:
  * H3: {"index": "^1e6ps7", "text": "Die griechische Philosophie", "level": "h3"}
  * H4: {"index": "^1e6ps7", "text": "Die Sophistik und die Wendung zum Menschen", "level": "h4"}
- Die Überschrift wird VOR diesem Absatz eingefügt
- Überschriften sollten gleichmäßig über den Vortrag verteilt sein
- H4-Überschriften folgen logisch unter ihren H3-Hauptüberschriften
- Lies genau die [Index: ...] Markierungen im Text`}

AUSGABEFORMAT (als JSON):
{
  "summary": "Deine Zusammenfassung in 100-150 Wörtern"${headingsDisabled ? '' : `,
  "headings": [
    {"index": "^1e6ps7", "text": "Die griechische Philosophie", "level": "h3"},
    {"index": "^1e6ps7", "text": "Die Sophistik und die Wendung zum Menschen", "level": "h4"},
    {"index": "^3k8mw2", "text": "Sokrates und die Selbsterkenntnis", "level": "h4"},
    {"index": "^8k2mw9", "text": "Platon und Aristoteles", "level": "h3"},
    {"index": "^8k2mw9", "text": "Platon und die ewige Lehre", "level": "h4"},
    {"index": "^5n7rx4", "text": "Aristoteles und die Formen in der Natur", "level": "h4"}
  ]`}
}

WICHTIG:
- Gib NUR das JSON zurück, keinen anderen Text
- Setze für Hauptüberschriften "level": "h3" und für Unterüberschriften "level": "h4"
${headingsDisabled ? '- Gib ein leeres headings-Array zurück: "headings": []' : '- Verwende die EXAKTEN Index-Strings aus dem Text (mit ^ am Anfang)'}
- Die Zusammenfassung sollte die Kernthesen erfassen
${headingsDisabled ? '' : `- Überschriften sollen das kommende Thema ankündigen
- Achte darauf, dass jede Überschrift zum Inhalt des folgenden Abschnitts passt
- H3 für Hauptthemen, H4 für Unterthemen innerhalb eines Hauptthemas`}

${headingsDisabled ? '\nHINWEIS: Aufgrund der Länge des Vortrags werden KEINE Zwischenüberschriften generiert. Konzentriere dich auf eine gute Zusammenfassung.\n' : ''}

VORTRAG-TEXT:
${textToSummarize}

AUSGABE (JSON):`;

  try {
    console.log('Rufe Claude API für Zusammenfassung auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Claude API Fehler: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    let summaryText = result.content[0].text;
    
    console.log('\n=== CLAUDE RESPONSE DEBUG ===');
    console.log('Rohe Antwort (erste 500 Zeichen):', summaryText.substring(0, 500));
    console.log('Antwort Länge:', summaryText.length);
    
    try {
      summaryText = summaryText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const summaryData = JSON.parse(summaryText);
      
      if (!summaryData.summary || !Array.isArray(summaryData.headings)) {
        throw new Error('Ungültiges JSON-Format von Claude');
      }
      
      console.log('✓ JSON erfolgreich geparst');
      console.log('Summary Länge:', summaryData.summary?.length);
      console.log('Anzahl Headings TOTAL:', summaryData.headings?.length);
      
      const h3Count = summaryData.headings?.filter(h => h.level === 'h3').length || 0;
      const h4Count = summaryData.headings?.filter(h => h.level === 'h4').length || 0;
      const otherCount = summaryData.headings?.filter(h => h.level !== 'h3' && h.level !== 'h4').length || 0;
      
      console.log('Headings nach Level:');
      console.log(`  H3: ${h3Count}`);
      console.log(`  H4: ${h4Count}`);
      console.log(`  Andere: ${otherCount}`);
      console.log('Erste 5 Headings:', JSON.stringify(summaryData.headings?.slice(0, 5), null, 2));
      console.log('============================\n');
      
      return summaryData;
      
    } catch (parseError) {
      console.error('JSON Parse Fehler:', parseError);
      console.log('Rohe Antwort:', summaryText.substring(0, 500));
      
      return {
        summary: summaryText,
        headings: []
      };
    }

  } catch (error) {
    console.error('Claude API Fehler:', error.message);
    return generateFallbackSummary(lecture);
  }
}

function generateFallbackSummary(lecture) {
  const displayTitle = lecture.fileName || lecture.title || lecture.ID;
  
  return {
    summary: `Automatische Zusammenfassung nicht verfügbar (kein Claude API-Schlüssel konfiguriert). Der Vortrag "${displayTitle}" enthält ${lecture.paragraphs?.length || 0} Absätze. Für eine detaillierte KI-Zusammenfassung benötigt das System einen Claude API-Schlüssel in der .env Datei.`,
    headings: []
  };
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

app.get('/debug/status', async (req, res) => {
  const summaryDB = await loadSummaryDatabase();
  res.json({
    server: 'hybrid-search-unified',
    status: 'running',
    chunksLoaded: chunks.length,
    lecturesLoaded: Object.keys(fullLectures).length,
    synonymGroups: Object.keys(synonyms).length,
    summariesInDB: Object.keys(summaryDB).length,
    queryLogSize: Object.keys(queryLog).length,
    claudeConfigured: !!process.env.CLAUDE_API_KEY
  });
});

// API-Endpunkt: GA-Liste für Dropdowns
app.get('/api/ga-list', async (req, res) => {
  try {
    const gaMap = {};
    
    // Sammle GA-Nummern und Titel
    Object.values(fullLectures).forEach(lecture => {
      const gaNumber = lecture.ID?.split('/')[0];
      if (gaNumber && !gaMap[gaNumber]) {
        // Verwende den Band-Titel falls vorhanden, sonst GA-Nummer
        gaMap[gaNumber] = {
          number: gaNumber,
          title: lecture.bandTitle || lecture.gaTitle || gaNumber
        };
      }
    });
    
    // Konvertiere zu Array und sortiere
    const gaList = Object.values(gaMap).sort((a, b) => {
      const numA = parseInt(a.number.replace('GA', ''));
      const numB = parseInt(b.number.replace('GA', ''));
      return numA - numB;
    });
    
    res.json(gaList);
  } catch (error) {
    console.error('Fehler beim Laden der GA-Liste:', error);
    res.status(500).json({ error: 'Fehler beim Laden der GA-Liste' });
  }
});

app.post('/api/hybrid-search', async (req, res) => {
  try {
    const { query, limit = 20 } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Query erforderlich' });
    }
    
    const searchResult = await performHybridSearch(query, limit);
    
    res.json({
      query: query,
      results: searchResult.results,
      resultCount: searchResult.results.length,
      totalMatches: searchResult.totalKeywordMatches,
      searchMethod: searchResult.method
    });
    
  } catch (error) {
    console.error('Hybrid-Suche Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/thematic-hybrid-search', async (req, res) => {
  try {
    const { query, limit = 100, gaFilter = '' } = req.body;
    const effectiveDepth = 'ausführlich';
    
    // Konsolidierte Hybrid-Cache-Logik
    const cacheKey = generateThematicCacheKey(query, effectiveDepth, limit, gaFilter);
    const thematicDB = await loadThematicSearchDatabase();
    // Hybrid-Cache-Logik zuerst prüfen
    const hybridHit = findHybridCacheHit(query, effectiveDepth, limit, gaFilter, thematicDB);
    if (hybridHit && hybridHit.key && thematicDB[hybridHit.key]) {
      console.log(`[THEMATIC-CACHE] Hybrid-Cache-Hit für: "${query}" (ausführlich, ${limit}) | Score: ${hybridHit.score}`);
      const cachedResult = thematicDB[hybridHit.key];
      return res.json({
        ...cachedResult,
        fromCache: true,
        cacheScore: hybridHit.score,
        cacheKey: hybridHit.key,
        cacheTimestamp: cachedResult.timestamp
      });
    }

    // Kein Cache-Hit: Neue Suche
    console.log(`[THEMATIC-SEARCH] Neue Suche für: "${query}" (ausführlich, ${limit})`);
    let keywordResults = performThematicKeywordSearch(query, paragraphsFromLectures, gaFilter);

    if (keywordResults.length === 0) {
      const emptyResult = {
        query: query,
        content: 'Keine relevanten Textstellen gefunden.',
        sources: [],
        searchMethod: 'hybrid-thematic-unified',
        totalMatches: 0,
        llmUsed: false
      };
      // Auch leere Ergebnisse cachen (um wiederholte Suchen zu vermeiden)
      thematicDB[cacheKey] = {
        ...emptyResult,
        timestamp: new Date().toISOString()
      };
      await saveThematicSearchDatabase(thematicDB);
      return res.json(emptyResult);
    }

    let rankedResults = applySemanticRanking(keywordResults, query);
    let topResults = rankedResults.slice(0, limit);

    // Query-Tracking
    trackQueryTerms(query, topResults.length);

    let analysis = await generateAnalysis(query, topResults, effectiveDepth);

    let searchResult = {
      query: query,
      content: analysis,
      sources: topResults.slice(0, 10).map(result => ({
        ID: result.ID,
        index: result.index,
        title: result.title,
        fileName: result.fileName,
        score: Math.round(result.finalScore),
        matchedTerms: result.matchedTerms
      })),
      searchMethod: 'hybrid-thematic-unified',
      totalMatches: keywordResults.length,
      llmUsed: !!process.env.CLAUDE_API_KEY
    };

    // Speichere Ergebnis im Cache
    thematicDB[cacheKey] = {
      ...searchResult,
      timestamp: new Date().toISOString()
    };

    // Speichere Cache-DB (non-blocking)
    saveThematicSearchDatabase(thematicDB).then(() => {
      console.log(`[THEMATIC-CACHE] Ergebnis gecacht für: "${query}" (ausführlich, ${limit})`);
    }).catch(err => {
      console.warn('[THEMATIC-CACHE] Fehler beim Cachen:', err.message);
    });

    return res.json(searchResult);
  } catch (error) {
    console.error('Hybrid-thematic-Search Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/lectures/list', (req, res) => {
  res.json({
    count: Object.keys(fullLectures).length,
    lectures: Object.keys(fullLectures),
    sample: Object.values(fullLectures)[0] || null
  });
});

app.get('/api/available-ga', async (req, res) => {
  try {
    const gaSet = new Set();

    Object.values(fullLectures).forEach(lecture => {
      if (lecture.gaNumber && typeof lecture.gaNumber === 'string') {
        gaSet.add(lecture.gaNumber);
      }
    });

    const result = Array.from(gaSet).sort();
    console.log("[INFO] Verfügbare GA-Bände:", result);
    res.json({ availableGA: result });
  } catch (error) {
    console.error("[ERROR] Fehler bei /api/available-ga:", error);
    res.status(500).json({ error: "Interner Serverfehler" });
  }
});

app.get('/api/ga-overview/:gaNumber', async (req, res) => {
  try {
    const gaNumberOriginal = req.params.gaNumber;

    console.log(`[GA-OVERVIEW] Anfrage für ${gaNumberOriginal}`);

    // Generiere Übersicht direkt aus zentraler Datenbank (kein Cache)
    const overview = await generateGAOverview(gaNumberOriginal);

    if (!overview) {
      return res.status(404).json({ error: `Keine Vorträge gefunden für ${gaNumberOriginal}` });
    }

    console.log(`[GA-OVERVIEW] Übersicht generiert für ${gaNumberOriginal}: ${overview.lectureCount} Vorträge`);
    res.json(overview);

  } catch (error) {
    console.error('[GA-OVERVIEW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/ga-overview-map.json', async (req, res) => {
  try {
    const mapPath = path.join(__dirname, 'ga-overview-map.json');
    
    console.log('[GA-OVERVIEW-MAP] Anfrage erhalten');
    
    try {
      await fs.access(mapPath);
      const data = await fs.readFile(mapPath, 'utf8');
      res.setHeader('Content-Type', 'application/json');
      res.send(data);
      console.log('[GA-OVERVIEW-MAP] Datei erfolgreich gesendet');
    } catch (fileErr) {
      console.log('[GA-OVERVIEW-MAP] Datei nicht gefunden, generiere Fallback');
      
      const gaSet = new Set();
      Object.values(fullLectures).forEach(lecture => {
        if (lecture.gaNumber) {
          gaSet.add(lecture.gaNumber);
        }
      });
      
      const map = {};
      Array.from(gaSet).forEach(ga => {
        map[ga] = `/api/ga-overview/${ga}`;
      });
      
      res.json(map);
    }
  } catch (err) {
    console.error('[GA-OVERVIEW-MAP] Fehler:', err);
    res.status(500).json({ error: 'cannot read ga-overview-map.json' });
  }
});

// ============================================================================
// ADMIN ENDPOINTS FÜR SYNONYM-GENERIERUNG
// ============================================================================

app.post('/api/admin/generate-synonyms', async (req, res) => {
  try {
    const { minCoOccurrence = 3, enrichWithClaude = true, topN = 30 } = req.body;
    
    console.log('\n========================================');
    console.log('SYNONYM-GENERIERUNG GESTARTET');
    console.log('========================================');
    
    const startCount = Object.keys(synonyms).length;
    
    console.log('\n[SCHRITT 1] Generiere aus Query-Log...');
    const querySynonyms = generateSynonymsFromQueries(minCoOccurrence);
    
    Object.keys(querySynonyms).forEach(term => {
      if (!synonyms[term]) {
        synonyms[term] = querySynonyms[term];
      } else {
        const existing = new Set(synonyms[term]);
        querySynonyms[term].forEach(syn => existing.add(syn));
        synonyms[term] = Array.from(existing);
      }
    });
    
    await saveSynonyms();
    
    let enrichedCount = 0;
    if (enrichWithClaude && process.env.CLAUDE_API_KEY) {
      console.log('\n[SCHRITT 2] Anreicherung mit Claude API...');
      enrichedCount = await enrichSynonymsWithClaude(topN);
    } else {
      console.log('\n[SCHRITT 2] Claude-Anreicherung übersprungen');
    }
    
    const endCount = Object.keys(synonyms).length;
    
    console.log('\n========================================');
    console.log('SYNONYM-GENERIERUNG ABGESCHLOSSEN');
    console.log(`Vorher: ${startCount} Begriffe`);
    console.log(`Nachher: ${endCount} Begriffe`);
    console.log(`Neu: ${endCount - startCount} Begriffe`);
    console.log(`Claude-Anreicherung: ${enrichedCount} Begriffe`);
    console.log('========================================\n');
    
    lastSynonymUpdate = new Date().toISOString();
    
    res.json({
      success: true,
      synonymCountBefore: startCount,
      synonymCountAfter: endCount,
      newSynonyms: endCount - startCount,
      querySynonymsGenerated: Object.keys(querySynonyms).length,
      claudeEnriched: enrichedCount,
      lastUpdate: lastSynonymUpdate
    });
    
  } catch (error) {
    console.error('Fehler bei Synonym-Generierung:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SCHLAGWORT-SYSTEM API
// ============================================================================

// API-Endpunkt: Liste aller verfügbaren Schlagwort-Dateien
app.get('/api/keywords-files', async (req, res) => {
  try {
    console.log('[KEYWORDS-API] Lade verfügbare Schlagwort-Dateien...');
    
    const keywordsPath = path.join(__dirname, 'keywords');
    
    // Prüfe ob keywords/ Ordner existiert
    try {
      await fs.access(keywordsPath);
    } catch (error) {
      console.log('[KEYWORDS-API] keywords/ Ordner nicht gefunden');
      return res.json({ files: [] });
    }
    
    // Lese alle .json Dateien im keywords/ Ordner
    const files = await fs.readdir(keywordsPath);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    console.log(`[KEYWORDS-API] ${jsonFiles.length} JSON-Dateien gefunden:`, jsonFiles);
    
    res.json({ 
      files: jsonFiles,
      count: jsonFiles.length 
    });
    
  } catch (error) {
    console.error('[KEYWORDS-API] Fehler beim Lesen des keywords/ Ordners:', error);
    res.status(500).json({ 
      error: 'Fehler beim Laden der Schlagwort-Dateien',
      files: [] 
    });
  }
});

// API-Endpunkt: Vollständige Schlagwort-Liste laden
app.get('/api/keywords-list', async (req, res) => {
  try {
    console.log('[KEYWORDS-API] Lade alle Schlagwörter...');
    
    const keywordsPath = path.join(__dirname, 'keywords');
    let allKeywords = [];
    
    // Versuche zuerst zentrale keywords.json im Hauptordner zu laden
    try {
      const filePath = path.join(__dirname, 'keywords.json');
      const fileContent = await fs.readFile(filePath, 'utf8');
      const data = JSON.parse(fileContent);
      if (Array.isArray(data)) {
        allKeywords = allKeywords.concat(data);
        console.log(`[KEYWORDS-API] ${allKeywords.length} Schlagwörter aus keywords.json geladen`);
      }
    } catch (error) {
      console.warn('[KEYWORDS-API] Keine zentrale keywords.json gefunden:', error.message);
      // Fallback: Lese alle .json Dateien im keywords/ Ordner
      try {
        const files = await fs.readdir(keywordsPath);
        const jsonFiles = files.filter(file => file.endsWith('.json'));
        for (const fileName of jsonFiles) {
          try {
            const filePath = path.join(keywordsPath, fileName);
            const fileContent = await fs.readFile(filePath, 'utf8');
            const data = JSON.parse(fileContent);
            if (Array.isArray(data)) {
              allKeywords = allKeywords.concat(data);
            }
          } catch (error) {
            console.warn(`[KEYWORDS-API] Fehler beim Verarbeiten von ${fileName}:`, error.message);
          }
        }
        console.log(`[KEYWORDS-API] ${allKeywords.length} Schlagwörter aus keywords/-Ordner geladen`);
      } catch (error) {
        console.warn('[KEYWORDS-API] keywords/ Ordner nicht gefunden:', error.message);
      }
    }
    res.json({ 
      keywords: allKeywords,
      count: allKeywords.length 
    });
  } catch (error) {
    console.error('[KEYWORDS-API] Fehler beim Laden der Schlagwörter:', error);
    res.status(500).json({ 
      error: 'Fehler beim Laden der Schlagwörter',
      keywords: [] 
    });
  }
});

// API-Endpunkt: Keywords mit KI aus GA-Text generieren
app.post('/api/keywords-generate', async (req, res) => {
  try {
    const { lectureId, maxKeywords = 5 } = req.body;
    
    if (!lectureId) {
      return res.status(400).json({ 
        error: 'lectureId ist erforderlich',
        received: { lectureId, maxKeywords }
      });
    }
    
    console.log('[KEYWORDS-GENERATE] Generiere Keywords für:', lectureId);
    
    // Lade Vortrag
    const lecture = fullLectures[lectureId];
    if (!lecture) {
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}` 
      });
    }
    
    // Bereite Text für KI vor
    const lectureText = lecture.paragraphs
      ?.map(p => p.content || p.text || '')
      .join('\n\n')
      .substring(0, 8000) || ''; // Begrenze auf 8000 Zeichen
    
    if (!lectureText.trim()) {
      return res.status(400).json({ 
        error: 'Kein Text im Vortrag gefunden' 
      });
    }
    
    // KI-Prompt für Keyword-Generierung
    const claudeApiKey = process.env.CLAUDE_API_KEY;
    if (!claudeApiKey) {
      return res.status(500).json({ 
        error: 'Claude API Key nicht konfiguriert' 
      });
    }
    
    const prompt = `Analysiere den folgenden Text aus Rudolf Steiners Werk und extrahiere die wichtigsten Schlagwörter/Begriffe.

KONTEXT: Rudolf Steiner / Anthroposophie / Geisteswissenschaft

AUFGABE:
1. Identifiziere ${maxKeywords} der wichtigsten Schlagwörter/Begriffe
2. Für jedes Schlagwort erstelle eine kurze Definition (2-3 Sätze)
3. Extrahiere relevante GA-Referenzen aus dem Text

FORMAT (JSON):
{
  "keywords": [
    {
      "keyword": "Begriff",
      "alphabetical": "B",
      "text": "**Begriff** ist eine kurze Definition mit wichtigen Aspekten aus dem Text.",
      "gaReferences": ["GA013/1", "GA066/2"]
    }
  ]
}

KRITERIEN für Schlagwörter:
- Zentrale anthroposophische Begriffe (z.B. Astralleib, Ätherleib, Ich, Bewusstsein)
- Philosophische Konzepte (z.B. Erkenntnis, Meditation, Karma)
- Spezifische Steiner-Begriffe (z.B. Abbauprozesse, Bildekräfte)
- Wichtige Personen (z.B. Kant, Goethe, Christus)
- Vermeide zu allgemeine Begriffe wie "Mensch", "Welt", "Leben"

TEXT:
${lectureText}

SCHLAGWÖRTER:`;

    console.log('[KEYWORDS-GENERATE] Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 2000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    const generatedText = result.content[0].text.trim();
    
    console.log('[KEYWORDS-GENERATE] Claude Antwort erhalten, Länge:', generatedText.length);
    
    // Parse JSON-Antwort
    let generatedKeywords;
    try {
      // Entferne mögliche Markdown-Code-Blöcke
      const cleanText = generatedText.replace(/```json\n?/g, '').replace(/```\n?/g, '');
      generatedKeywords = JSON.parse(cleanText);
    } catch (parseError) {
      console.error('[KEYWORDS-GENERATE] JSON Parse Fehler:', parseError);
      console.log('[KEYWORDS-GENERATE] Rohe Antwort:', generatedText.substring(0, 500));
      
      // Fallback: Versuche Keywords aus Text zu extrahieren
      generatedKeywords = {
        keywords: [{
          keyword: "Generiertes Keyword",
          alphabetical: "G",
          text: "**Generiertes Keyword** wurde automatisch aus dem Vortrag extrahiert.",
          gaReferences: []
        }]
      };
    }
    
    // Validiere und bereinige Keywords
    const validKeywords = generatedKeywords.keywords
      ?.filter(k => k.keyword && k.text)
      ?.map(k => ({
        keyword: k.keyword.trim(),
        alphabetical: k.alphabetical || k.keyword.charAt(0).toUpperCase(),
        text: k.text.trim(),
        gaReferences: k.gaReferences || [],
        generatedAt: new Date().toISOString(),
        sourceLecture: lectureId
      })) || [];
    
    console.log(`[KEYWORDS-GENERATE] ${validKeywords.length} Keywords generiert für ${lectureId}`);
    
    res.json({ 
      success: true,
      lectureId: lectureId,
      generatedKeywords: validKeywords,
      count: validKeywords.length,
      sourceText: lectureText.substring(0, 200) + '...'
    });
    
  } catch (error) {
    console.error('[KEYWORDS-GENERATE] Fehler:', error);
    res.status(500).json({ 
      error: 'Fehler bei der Keyword-Generierung',
      details: error.message 
    });
  }
});

// ============================================================================
// FULL LECTURES API (für Timeline)
// ============================================================================

app.get('/api/full-lectures', async (req, res) => {
  try {
    console.log('[FULL-LECTURES] API-Aufruf');
    
    if (Object.keys(fullLectures).length === 0) {
      console.log('[FULL-LECTURES] Lade Vorträge...');
      await loadFullLectures();
    }
    
    // Erstelle vereinfachte Struktur für Frontend
    const simplifiedLectures = {};
    Object.values(fullLectures).forEach(lecture => {
      if (lecture.ID) {
        simplifiedLectures[lecture.ID] = {
          ID: lecture.ID,
          title: lecture.title,
          fileName: lecture.fileName,
          location: lecture.location,
          date: lecture.date,
          gaNumber: lecture.gaNumber,
          gaTitle: lecture.gaTitle,
          lectureNumber: lecture.lectureNumber
        };
      }
    });
    
    console.log(`[FULL-LECTURES] Sende ${Object.keys(simplifiedLectures).length} Vorträge`);
    res.json(simplifiedLectures);
    
  } catch (error) {
    console.error('[FULL-LECTURES] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Hilfsfunktion: Relevanz-Score berechnen
function calculateRelevanceScore(lecture, keyword) {
  const paragraphs = lecture.paragraphs.filter(p => 
    p.content && p.content.toLowerCase().includes(keyword.toLowerCase())
  );
  
  if (paragraphs.length === 0) return 0;
  
  let totalScore = 0;
  let keywordOccurrences = 0;
  
  paragraphs.forEach(paragraph => {
    const content = paragraph.content.toLowerCase();
    const keywordLower = keyword.toLowerCase();
    
    // Anzahl der Vorkommen
    const occurrences = (content.split(keywordLower).length - 1);
    keywordOccurrences += occurrences;
    
    // Dichte-Score (Vorkommen pro Zeichen)
    const density = occurrences / paragraph.content.length;
    
    // Kontext-Länge-Score (längere Abschnitte = höhere Relevanz)
    const contextScore = Math.log(paragraph.content.length + 1);
    
    // Kombinierter Score für diesen Absatz
    const paragraphScore = density * contextScore * Math.sqrt(occurrences);
    totalScore += paragraphScore;
  });
  
  // Normalisierung: Score pro Absatz und pro Vorkommen
  const normalizedScore = totalScore / Math.max(paragraphs.length, 1);
  const occurrenceBonus = Math.log(keywordOccurrences + 1) * 0.1;
  
  return normalizedScore + occurrenceBonus;
}

// ============================================================================
// SINGLE LECTURE API
// ============================================================================

app.get('/api/lecture/:lectureId', async (req, res) => {
  try {
    const { lectureId } = req.params;
    
    console.log(`[LECTURE] Lade Vortrag: ${lectureId}`);
    
    if (Object.keys(fullLectures).length === 0) {
      await loadFullLectures();
    }
    
    const lecture = fullLectures[lectureId];
    if (!lecture) {
      return res.status(404).json({ error: 'Vortrag nicht gefunden' });
    }
    
    // Generiere HTML-Inhalt für den Vortrag
    let content = '';
    
    if (lecture.paragraphs && lecture.paragraphs.length > 0) {
      lecture.paragraphs.forEach(paragraph => {
        if (paragraph.content) {
          content += `<p>${paragraph.content}</p>`;
        }
      });
    } else {
      content = '<p>Kein Inhalt verfügbar.</p>';
    }
    
    res.json({
      ID: lecture.ID,
      title: lecture.title,
      fileName: lecture.fileName,
      content: content
    });
    
  } catch (error) {
    console.error('[LECTURE] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// KEYWORD THEMATIC SEARCH (basierend auf Themensuche)
// ============================================================================

app.post('/api/keyword-thematic-search', async (req, res) => {
  try {
    const { query, limit = 30, useCache = true } = req.body;
    const effectiveDepth = 'ausführlich';
    
    if (!query) {
      return res.status(400).json({ error: 'Query erforderlich' });
    }
    
    console.log(`[KEYWORD-THEMATIC] Suche für: "${query}" (ausführlich, ${limit})`);
    
    // Cache-System für Keyword-Thematische Suche
    const cacheKey = `keyword_${query.toLowerCase().trim()}_${effectiveDepth}_${limit}`;
    const keywordThematicDB = await loadKeywordThematicDatabase();
    
    // Prüfe Cache (nur wenn useCache true ist)
    if (useCache && keywordThematicDB[cacheKey]) {
      console.log(`[KEYWORD-THEMATIC-CACHE] Cache-Hit für: "${query}"`);
      return res.json({
        ...keywordThematicDB[cacheKey],
        fromCache: true,
        cacheTimestamp: keywordThematicDB[cacheKey].timestamp
      });
    }
    
    // Führe Keyword-Suche durch
    let keywordResults = performThematicKeywordSearch(query, paragraphsFromLectures);
    
    if (keywordResults.length === 0) {
      const emptyResult = {
        query: query,
        content: 'Keine relevanten Textstellen für dieses Schlagwort gefunden.',
        sources: [],
        searchMethod: 'keyword-thematic-search',
        totalMatches: 0,
        llmUsed: false
      };
      
      // Cache leeres Ergebnis
      keywordThematicDB[cacheKey] = {
        ...emptyResult,
        timestamp: new Date().toISOString()
      };
      await saveKeywordThematicDatabase(keywordThematicDB);
      return res.json(emptyResult);
    }
    
    // Semantisches Ranking
    let rankedResults = applySemanticRanking(keywordResults, query);
    let topResults = rankedResults.slice(0, limit);
    
    // Generiere Keyword-spezifische Analyse
    let analysis = await generateKeywordAnalysis(query, topResults, effectiveDepth);
    
    let searchResult = {
      query: query,
      content: analysis,
      sources: topResults.slice(0, 10).map(result => ({
        ID: result.ID,
        index: result.index,
        title: result.title,
        fileName: result.fileName,
        score: Math.round(result.finalScore),
        matchedTerms: result.matchedTerms
      })),
      searchMethod: 'keyword-thematic-search',
      totalMatches: keywordResults.length,
      llmUsed: !!process.env.CLAUDE_API_KEY
    };
    
    // Speichere im Cache
    keywordThematicDB[cacheKey] = {
      ...searchResult,
      timestamp: new Date().toISOString()
    };
    
    // Speichere Cache-DB (non-blocking)
    saveKeywordThematicDatabase(keywordThematicDB).then(() => {
      console.log(`[KEYWORD-THEMATIC-CACHE] Ergebnis gecacht für: "${query}"`);
    }).catch(err => {
      console.warn('[KEYWORD-THEMATIC-CACHE] Fehler beim Cachen:', err.message);
    });
    
    return res.json({
      ...searchResult,
      fromCache: false,
      cacheTimestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Keyword-Thematic-Search Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API-Endpunkt: Keyword speichern
app.post('/api/keywords-save', async (req, res) => {
  try {
    const { keyword, alphabetical, text, gaReferences } = req.body;
    
    if (!keyword || !text) {
      return res.status(400).json({ 
        error: 'keyword und text sind erforderlich',
        received: { keyword, alphabetical, text, gaReferences }
      });
    }
    
    console.log('[KEYWORDS-SAVE] Speichere Keyword:', keyword);
    
    // Lade aktuelle Keywords
    const keywordsPath = path.join(__dirname, 'keywords');
    const keywordsFile = path.join(__dirname, 'keywords.json');
    
    let allKeywords = [];
    
    // Versuche zuerst zentrale keywords.json zu laden
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      const data = JSON.parse(fileContent);
      if (Array.isArray(data)) {
        allKeywords = data;
        console.log(`[KEYWORDS-SAVE] ${allKeywords.length} Keywords aus keywords.json geladen`);
      }
    } catch (error) {
      console.log('[KEYWORDS-SAVE] Keine keywords.json gefunden, erstelle neue');
    }
    
    // Prüfe ob Keyword bereits existiert
    const existingIndex = allKeywords.findIndex(k => k.keyword.toLowerCase() === keyword.toLowerCase());
    
    const newKeyword = {
      keyword: keyword,
      alphabetical: alphabetical || keyword.charAt(0).toUpperCase(),
      text: text,
      gaReferences: gaReferences || extractGAReferencesFromText(text),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    if (existingIndex >= 0) {
      // Update existing keyword
      allKeywords[existingIndex] = { ...allKeywords[existingIndex], ...newKeyword };
      console.log(`[KEYWORDS-SAVE] Keyword "${keyword}" aktualisiert`);
    } else {
      // Add new keyword
      allKeywords.push(newKeyword);
      console.log(`[KEYWORDS-SAVE] Neues Keyword "${keyword}" hinzugefügt`);
    }
    
    // Speichere zurück in keywords.json
    await fs.writeFile(keywordsFile, JSON.stringify(allKeywords, null, 2), 'utf8');
    
    res.json({ 
      success: true, 
      message: existingIndex >= 0 ? 'Keyword aktualisiert' : 'Keyword hinzugefügt',
      keyword: newKeyword,
      totalKeywords: allKeywords.length
    });
    
  } catch (error) {
    console.error('[KEYWORDS-SAVE] Fehler beim Speichern:', error);
    res.status(500).json({ 
      error: 'Fehler beim Speichern des Keywords',
      details: error.message 
    });
  }
});

// ============================================================================
// KEYWORD THEMATIC SEARCH HILFSFUNKTIONEN (vor /api/keywords-add)
// ============================================================================

// Keyword-Thematische-Suche-Cache-Datenbank
const KEYWORD_THEMATIC_DB_FILE = path.join(__dirname, 'keyword-thematic-search.json');

// Lade Keyword-Thematische-Suche-Cache-Datenbank
async function loadKeywordThematicDatabase() {
  try {
    const data = await fs.readFile(KEYWORD_THEMATIC_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('Keyword-Thematische-Suche-Cache-DB nicht gefunden, erstelle neue');
    return {};
  }
}

// Speichere Keyword-Thematische-Suche-Cache-Datenbank
async function saveKeywordThematicDatabase(keywordThematicDB) {
  try {
    await fs.writeFile(KEYWORD_THEMATIC_DB_FILE, JSON.stringify(keywordThematicDB, null, 2), 'utf8');
    console.log('Keyword-Thematische-Suche-Cache-DB gespeichert');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Keyword-Thematische-Suche-Cache-DB:', error);
    return false;
  }
}

// API-Endpunkt: Batch-Schlagwort-Generierung
app.post('/api/keywords-batch-add', async (req, res) => {
  try {
    const { keywords, overwrite = false, batchId = null } = req.body;
    
    if (!keywords || !Array.isArray(keywords) || keywords.length === 0) {
      return res.status(400).json({ 
        error: 'keywords Array erforderlich (mindestens 1 Schlagwort)',
        received: { keywords, overwrite, batchId }
      });
    }
    
    console.log(`[KEYWORDS-BATCH-ADD] Starte parallele Batch-Verarbeitung für ${keywords.length} Schlagwörter (Concurrency: 5)`);
    
    const results = {
      batchId: batchId || `batch_${Date.now()}`,
      totalKeywords: keywords.length,
      processed: 0,
      successful: [],
      failed: [],
      skipped: [],
      startTime: new Date().toISOString()
    };
    
    // Lade keywords.json einmalig vor der Verarbeitung
    const keywordsFile = path.join(__dirname, 'keywords.json');
    let allKeywords = [];
    
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
      console.log('[KEYWORDS-BATCH-ADD] keywords.json nicht gefunden, erstelle neue');
    }
    
    // Definiere Verarbeitungsfunktion für ein Schlagwort
    const processKeyword = async (keyword, i) => {
      const trimmedKeyword = keyword.trim();
      
      if (!trimmedKeyword) {
        return {
          status: 'skipped',
          keyword: keyword,
          reason: 'Leeres Schlagwort',
          index: i
        };
      }
      
      console.log(`[KEYWORDS-BATCH-ADD] Verarbeite ${i + 1}/${keywords.length}: "${trimmedKeyword}"`);
      
      // Prüfe auf Duplikate
      const existingKeywordIndex = allKeywords.findIndex(k => 
        k.keyword.toLowerCase() === trimmedKeyword.toLowerCase()
      );
      
      if (existingKeywordIndex !== -1 && !overwrite) {
        return {
          status: 'skipped',
          keyword: trimmedKeyword,
          reason: 'Schlagwort bereits vorhanden',
          index: i,
          existingKeyword: allKeywords[existingKeywordIndex].keyword
        };
      }
      
      // Führe Keyword-Thematische Suche durch
      let keywordResults = performThematicKeywordSearch(trimmedKeyword, paragraphsFromLectures);
      
      if (keywordResults.length === 0) {
        return {
          status: 'failed',
          keyword: trimmedKeyword,
          reason: 'Keine relevanten Textstellen gefunden',
          index: i
        };
      }
      
      // Generiere KI-Analyse
      const analysis = await generateKeywordAnalysis(trimmedKeyword, keywordResults, 'ausführlich');
      
      // Erstelle neues Schlagwort-Objekt
      const newKeyword = {
        keyword: trimmedKeyword,
        alphabetical: trimmedKeyword.charAt(0).toUpperCase(),
        text: `**${trimmedKeyword}**`,
        gaReferences: keywordResults.slice(0, 20).map(r => r.ID),
        generatedAt: new Date().toISOString(),
        sourceAnalysis: 'ki-generated-batch',
        analysisLength: analysis.length,
        resultCount: keywordResults.length,
        hasDetailedAnalysis: true,
        batchId: results.batchId,
        batchIndex: i
      };
      
      // Speichere detaillierte Analyse im Cache
      const keywordThematicDB = await loadKeywordThematicDatabase();
      const cacheKey = `keyword_${trimmedKeyword.toLowerCase().trim()}_ausführlich_30`;
      
      keywordThematicDB[cacheKey] = {
        query: trimmedKeyword,
        content: analysis,
        sources: keywordResults.slice(0, 20).map(result => ({
          ID: result.ID,
          index: result.index,
          title: result.title,
          fileName: result.fileName,
          score: Math.round(result.finalScore || 100),
          matchedTerms: result.matchedTerms || [trimmedKeyword]
        })),
        searchMethod: 'keyword-thematic-search',
        totalMatches: keywordResults.length,
        llmUsed: !!process.env.CLAUDE_API_KEY,
        timestamp: new Date().toISOString(),
        batchId: results.batchId
      };
      
      await saveKeywordThematicDatabase(keywordThematicDB);
      
      console.log(`[KEYWORDS-BATCH-ADD] ✓ "${trimmedKeyword}" erfolgreich verarbeitet`);
      
      return {
        status: 'successful',
        keyword: trimmedKeyword,
        index: i,
        resultCount: keywordResults.length,
        analysisLength: analysis.length,
        newKeyword: newKeyword,
        existingKeywordIndex: existingKeywordIndex
      };
    };
    
    // Verarbeite alle Schlagwörter parallel (max 5 gleichzeitig, 200ms Verzögerung zwischen Starts)
    const batchResults = await processBatchWithConcurrency(
      keywords,
      processKeyword,
      5,  // Concurrency Limit
      200 // Delay zwischen Starts in ms
    );
    
    // Sammle Ergebnisse und aktualisiere keywords.json
    for (const result of batchResults) {
      if (result.success) {
        const data = result.result;
        
        if (data.status === 'successful') {
          // Aktualisiere allKeywords Array
          if (data.existingKeywordIndex !== -1 && overwrite) {
            allKeywords[data.existingKeywordIndex] = data.newKeyword;
          } else if (data.existingKeywordIndex === -1) {
            allKeywords.push(data.newKeyword);
          }
          
          results.successful.push({
            keyword: data.keyword,
            index: data.index,
            resultCount: data.resultCount,
            analysisLength: data.analysisLength
          });
        } else if (data.status === 'skipped') {
          results.skipped.push(data);
        } else if (data.status === 'failed') {
          results.failed.push(data);
        }
      } else {
        results.failed.push({
          keyword: result.item,
          reason: result.error || 'Unbekannter Fehler',
          index: result.index
        });
      }
      
      results.processed++;
    }
    
    // Speichere aktualisierte keywords.json
    await fs.writeFile(keywordsFile, JSON.stringify(allKeywords, null, 2), 'utf8');
    console.log('[KEYWORDS-BATCH-ADD] keywords.json aktualisiert');
    
    results.endTime = new Date().toISOString();
    results.duration = new Date(results.endTime) - new Date(results.startTime);
    
    console.log(`[KEYWORDS-BATCH-ADD] Batch abgeschlossen: ${results.successful.length} erfolgreich, ${results.failed.length} fehlgeschlagen, ${results.skipped.length} übersprungen`);
    
    res.json({
      success: true,
      message: `Batch-Verarbeitung abgeschlossen: ${results.successful.length}/${results.totalKeywords} Schlagwörter erfolgreich`,
      results: results
    });
    
  } catch (error) {
    console.error('[KEYWORDS-BATCH-ADD] Kritischer Fehler:', error);
    res.status(500).json({
      error: 'Fehler bei der Batch-Verarbeitung',
      message: error.message,
      stack: error.stack
    });
  }
});

// API-Endpunkt: Neues Schlagwort hinzufügen und durch KI-Analyse befüllen
app.post('/api/keywords-add', async (req, res) => {
  try {
    const { keyword, overwrite = false } = req.body;
    
    if (!keyword || !keyword.trim()) {
      return res.status(400).json({ error: 'Schlagwort erforderlich' });
    }
    
    const cleanKeyword = keyword.trim();
    console.log(`[KEYWORDS-ADD] ${overwrite ? 'Überschreibe' : 'Füge neues'} Schlagwort hinzu: "${cleanKeyword}"`);
    
    // Prüfe ob Schlagwort bereits existiert
    const keywordsFile = path.join(__dirname, 'keywords.json');
    let allKeywords = [];
    
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
      console.log('[KEYWORDS-ADD] keywords.json nicht gefunden, erstelle neue');
    }
    
    // Prüfe auf Duplikate
    const existingKeywordIndex = allKeywords.findIndex(k => 
      k.keyword.toLowerCase() === cleanKeyword.toLowerCase()
    );
    
    if (existingKeywordIndex !== -1 && !overwrite) {
      return res.status(409).json({ 
        error: 'Schlagwort bereits vorhanden',
        existingKeyword: allKeywords[existingKeywordIndex].keyword
      });
    }
    
    // Führe Keyword-Thematische Suche durch, um das Schlagwort zu analysieren
    console.log(`[KEYWORDS-ADD] Führe KI-Analyse für "${cleanKeyword}" durch...`);
    
    let keywordResults = performThematicKeywordSearch(cleanKeyword, paragraphsFromLectures);
    
    if (keywordResults.length === 0) {
      return res.status(404).json({ 
        error: 'Keine relevanten Textstellen für dieses Schlagwort gefunden',
        keyword: cleanKeyword
      });
    }
    
    // Generiere KI-Analyse
    const analysis = await generateKeywordAnalysis(cleanKeyword, keywordResults, 'ausführlich');
    
    // Erstelle neues Schlagwort-Objekt für Index (keywords.json)
    const newKeyword = {
      keyword: cleanKeyword,
      alphabetical: cleanKeyword.charAt(0).toUpperCase(),
      text: `**${cleanKeyword}**`,
      gaReferences: keywordResults.slice(0, 20).map(r => r.ID), // Top 20 GA-Referenzen (erhöht von 10)
      generatedAt: new Date().toISOString(),
      sourceAnalysis: 'ki-generated',
      analysisLength: analysis.length,
      resultCount: keywordResults.length,
      hasDetailedAnalysis: true // Flag für Frontend
    };
    
    if (existingKeywordIndex !== -1 && overwrite) {
      // Überschreibe bestehendes Schlagwort
      allKeywords[existingKeywordIndex] = newKeyword;
      console.log(`[KEYWORDS-ADD] Schlagwort "${cleanKeyword}" überschrieben`);
    } else {
      // Füge zur Liste hinzu
      allKeywords.push(newKeyword);
      console.log(`[KEYWORDS-ADD] Schlagwort "${cleanKeyword}" neu hinzugefügt`);
    }
    
    // Speichere zurück in keywords.json
    await fs.writeFile(keywordsFile, JSON.stringify(allKeywords, null, 2), 'utf8');
    
    // Speichere auch die detaillierte Analyse im Cache
    const keywordThematicDB = await loadKeywordThematicDatabase();
    const cacheKey = `keyword_${cleanKeyword.toLowerCase().trim()}_ausführlich_30`;
    
    keywordThematicDB[cacheKey] = {
      query: cleanKeyword,
      content: analysis,
      sources: keywordResults.slice(0, 20).map(result => ({
        ID: result.ID,
        index: result.index,
        title: result.title,
        fileName: result.fileName,
        score: Math.round(result.finalScore || 100),
        matchedTerms: result.matchedTerms || [cleanKeyword]
      })),
      searchMethod: 'keyword-thematic-search',
      totalMatches: keywordResults.length,
      llmUsed: !!process.env.CLAUDE_API_KEY,
      timestamp: new Date().toISOString()
    };
    
    await saveKeywordThematicDatabase(keywordThematicDB);
    
    console.log(`[KEYWORDS-ADD] Schlagwort "${cleanKeyword}" erfolgreich hinzugefügt`);
    console.log(`[KEYWORDS-ADD] Analyse-Länge: ${analysis.length} Zeichen`);
    console.log(`[KEYWORDS-ADD] Gefundene Ergebnisse: ${keywordResults.length}`);
    console.log(`[KEYWORDS-ADD] Detaillierte Analyse im Cache gespeichert`);
    
    res.json({ 
      success: true, 
      message: 'Schlagwort erfolgreich hinzugefügt und analysiert',
      keyword: newKeyword,
      totalKeywords: allKeywords.length,
      analysisLength: analysis.length,
      resultCount: keywordResults.length,
      // Neue Felder für direkte Anzeige
      content: analysis,
      sources: keywordResults.slice(0, 20).map(result => ({
        ID: result.ID,
        index: result.index,
        title: result.title,
        fileName: result.fileName,
        score: Math.round(result.finalScore || 100),
        matchedTerms: result.matchedTerms || [cleanKeyword]
      }))
    });
    
  } catch (error) {
    console.error('[KEYWORDS-ADD] Fehler beim Hinzufügen:', error);
    res.status(500).json({ 
      error: 'Fehler beim Hinzufügen des Schlagworts',
      details: error.message 
    });
  }
});

// Hilfsfunktion: GA-Referenzen aus Text extrahieren
function extractGAReferencesFromText(text) {
  if (!text) return [];
  
  const gaMatches = text.match(/\[\[([^\]]*\|)?([^|\]]+)\]\]/g);
  if (!gaMatches) return [];
  
  return gaMatches.map(match => {
    const gaMatch = match.match(/\[\[([^\]]*\|)?([^|\]]+)\]\]/);
    if (gaMatch && gaMatch[2]) {
      const gaId = gaMatch[2].trim();
      return gaId;
    }
    return null;
  }).filter(id => id && /^GA\d{3}[a-z]?\/\d+$/i.test(id));
}

// ============================================================================

app.get('/api/admin/synonym-stats', (req, res) => {
  const topQueries = Object.entries(queryLog)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 20)
    .map(([term, data]) => ({ term, count: data.count }));

  res.json({
    synonymCount: Object.keys(synonyms).length,
    queryLogSize: Object.keys(queryLog).length,
    totalSearches: Object.values(queryLog).reduce((sum, e) => sum + e.count, 0),
    lastUpdate: lastSynonymUpdate,
    topQueries: topQueries
  });
});

// Route aus Verschachtelung herausgelöst
app.post('/api/admin/clear-incomplete-summaries', async (req, res) => {
  try {
    console.log('\n========================================');
    console.log('LÖSCHE UNVOLLSTÄNDIGE ZUSAMMENFASSUNGEN');
    console.log('========================================');

    let deletedCount = 0;
    const toDelete = [];

    // Prüfe zentrale DB auf unvollständige Summaries
    const summaryDB = await loadSummaryDatabase();
    Object.entries(summaryDB).forEach(([lectureId, summary]) => {
      const headings = summary.headings || [];
      const h3Count = headings.filter(h => h.level === 'h3').length;

      // Lösche wenn keine Headings oder keine H3
      if (headings.length === 0 || h3Count === 0) {
        toDelete.push(lectureId);
        console.log(`  Markiere ${lectureId} (${headings.length} headings, ${h3Count} H3)`);
      }
    });

    // Lösche aus zentraler DB mit robustem Locking
    deletedCount = await deleteSummariesFromDatabase(toDelete);

    console.log(`✓ ${deletedCount} unvollständige Summaries aus zentraler DB gelöscht`);

    console.log(`✓ ${deletedCount} unvollständige Zusammenfassungen gelöscht`);
    console.log('========================================\n');

    res.json({
      success: true,
      deletedCount: deletedCount,
      deletedIds: toDelete
    });

  } catch (error) {
    console.error('Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// KEYWORD LÖSCHEN
// ============================================================================

app.post('/api/keywords-delete', async (req, res) => {
  try {
    const { keyword } = req.body;
    if (!keyword || !keyword.trim()) {
      return res.status(400).json({ error: 'Schlagwort erforderlich' });
    }

    const cleanKeyword = keyword.trim();
    console.log(`[KEYWORDS-DELETE] Lösche Schlagwort: "${cleanKeyword}"`);

    // 1) Entferne aus keywords.json
    const keywordsFile = path.join(__dirname, 'keywords.json');
    let allKeywords = [];
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
      console.log('[KEYWORDS-DELETE] keywords.json nicht gefunden, nichts zu entfernen');
    }

    const beforeCount = allKeywords.length;
    allKeywords = allKeywords.filter(k => k.keyword.toLowerCase() !== cleanKeyword.toLowerCase());
    const removedFromIndex = beforeCount - allKeywords.length;

    if (beforeCount !== allKeywords.length) {
      await fs.writeFile(keywordsFile, JSON.stringify(allKeywords, null, 2), 'utf8');
      console.log(`[KEYWORDS-DELETE] Aus keywords.json entfernt: ${removedFromIndex}`);
    } else {
      console.log('[KEYWORDS-DELETE] Kein Eintrag in keywords.json gefunden');
    }

    // 2) Entferne aus allen Dateien im keywords/ Ordner
    const keywordsDir = path.join(__dirname, 'keywords');
    let removedFromFolderFiles = 0;
    try {
      const files = await fs.readdir(keywordsDir);
      const jsonFiles = files.filter(f => f.endsWith('.json'));
      for (const fileName of jsonFiles) {
        try {
          const filePath = path.join(keywordsDir, fileName);
          const content = await fs.readFile(filePath, 'utf8');
          const data = JSON.parse(content);
          if (Array.isArray(data) && data.length > 0) {
            const before = data.length;
            const filtered = data.filter(k => String(k.keyword || '').toLowerCase() !== cleanKeyword.toLowerCase());
            if (filtered.length !== before) {
              await fs.writeFile(filePath, JSON.stringify(filtered, null, 2), 'utf8');
              removedFromFolderFiles += (before - filtered.length);
              console.log(`[KEYWORDS-DELETE] Aus ${fileName} entfernt: ${before - filtered.length}`);
            }
          }
        } catch (innerErr) {
          console.warn(`[KEYWORDS-DELETE] Datei konnte nicht verarbeitet werden: ${fileName}:`, innerErr.message);
        }
      }
    } catch (dirErr) {
      console.log('[KEYWORDS-DELETE] keywords/ Ordner nicht vorhanden oder nicht lesbar');
    }

    // 3) Entferne aus keyword-thematic-search.json Cache
    const keywordThematicDB = await loadKeywordThematicDatabase();
    const cacheKey = `keyword_${cleanKeyword.toLowerCase().trim()}_allgemein_30`;
    let removedFromCache = false;
    if (keywordThematicDB[cacheKey]) {
      delete keywordThematicDB[cacheKey];
      removedFromCache = true;
      await saveKeywordThematicDatabase(keywordThematicDB);
      console.log(`[KEYWORDS-DELETE] Cache-Eintrag entfernt: ${cacheKey}`);
    } else {
      console.log('[KEYWORDS-DELETE] Kein Cache-Eintrag gefunden');
    }

    return res.json({
      success: true,
      message: 'Schlagwort gelöscht',
      removedFromIndex: removedFromIndex > 0,
      removedFromFolderFiles,
      removedFromCache
    });
  } catch (error) {
    console.error('[KEYWORDS-DELETE] Fehler beim Löschen:', error);
    res.status(500).json({
      error: 'Fehler beim Löschen des Schlagworts',
      details: error.message
    });
  }
});

// ============================================================================
// ZENTRALE SUMMARY-DATENBANK
// ============================================================================

const SUMMARY_DB_FILE = path.join(__dirname, 'summary-database.json');
const THEMATIC_SEARCH_DB_FILE = path.join(__dirname, 'thematic-search-database.json');
const KEYWORDS_DB_FILE = path.join(__dirname, 'keywords-database.json');
const THEMES_DB_FILE = path.join(__dirname, 'themes-database.json');
const CLUSTERS_FILE = path.join(__dirname, 'thematic-clusters.json');

// Backup-Verzeichnisse
const BACKUP_BASE_DIR = path.join(__dirname, 'backups');
const KEYWORDS_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'keywords');
const SUMMARY_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'summary');
const THEMES_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'themes');
const CLUSTERS_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'clusters');
const CODE_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'code');
const HTML_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'html');

// ============================================================================
// AUTOMATISCHES BACKUP-SYSTEM - UMFASSEND
// ============================================================================

// Erstelle alle Backup-Ordner falls nicht vorhanden
async function ensureBackupDirectories() {
  const dirs = [
    KEYWORDS_BACKUP_DIR,
    SUMMARY_BACKUP_DIR,
    THEMES_BACKUP_DIR,
    CLUSTERS_BACKUP_DIR,
    CODE_BACKUP_DIR,
    HTML_BACKUP_DIR
  ];
  
  for (const dir of dirs) {
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (error) {
      console.error(`[BACKUP] Fehler beim Erstellen von ${dir}:`, error);
    }
  }
}

// Legacy-Funktion für Abwärtskompatibilität
async function ensureBackupDirectory() {
  await ensureBackupDirectories();
}

// Generische Backup-Funktion für jede Datei
async function createBackup(sourceFile, backupDir, prefix, maxBackups = 10) {
  try {
    await ensureBackupDirectories();
    
    // Prüfe ob Datei existiert und nicht leer ist
    try {
      const stats = await fs.stat(sourceFile);
      if (stats.size === 0) {
        console.warn(`[BACKUP] WARNUNG: ${path.basename(sourceFile)} ist leer - kein Backup erstellt`);
        return null;
      }
    } catch (error) {
      console.log(`[BACKUP] ${path.basename(sourceFile)} nicht gefunden - kein Backup erstellt`);
      return null;
    }
    
    // Erstelle Backup mit Timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(backupDir, `${prefix}-${timestamp}.json`);
    
    const data = await fs.readFile(sourceFile, 'utf8');
    await fs.writeFile(backupFile, data, 'utf8');
    
    console.log(`[BACKUP] ✓ ${prefix}: ${path.basename(backupFile)}`);
    
    // Bereinige alte Backups
    await cleanOldBackupsGeneric(backupDir, prefix, maxBackups);
    
    return backupFile;
  } catch (error) {
    console.error(`[BACKUP] Fehler beim Backup von ${prefix}:`, error);
    return null;
  }
}

// Generische Bereinigungsfunktion
async function cleanOldBackupsGeneric(backupDir, prefix, maxBackups) {
  try {
    const files = await fs.readdir(backupDir);
    const backupFiles = files
      .filter(f => f.startsWith(prefix) && f.endsWith('.json'))
      .map(f => ({
        name: f,
        fullPath: path.join(backupDir, f)
      }));
    
    // Sortiere nach Dateinamen (Timestamp im Namen)
    backupFiles.sort((a, b) => b.name.localeCompare(a.name));
    
    // Lösche alle außer den letzten N
    const toDelete = backupFiles.slice(maxBackups);
    for (const file of toDelete) {
      await fs.unlink(file.fullPath);
    }
    
    if (toDelete.length > 0) {
      console.log(`[BACKUP] ${toDelete.length} alte ${prefix}-Backups gelöscht`);
    }
  } catch (error) {
    console.error(`[BACKUP] Fehler beim Bereinigen von ${prefix}:`, error);
  }
}

// Spezifische Backup-Funktionen für jede Datei
async function createKeywordsBackup() {
  return await createBackup(KEYWORDS_DB_FILE, KEYWORDS_BACKUP_DIR, 'keywords-database', 10);
}

async function createSummaryBackup() {
  return await createBackup(SUMMARY_DB_FILE, SUMMARY_BACKUP_DIR, 'summary-database', 10);
}

async function createThemesBackup() {
  return await createBackup(THEMES_DB_FILE, THEMES_BACKUP_DIR, 'themes-database', 10);
}

async function createClustersBackup() {
  return await createBackup(CLUSTERS_FILE, CLUSTERS_BACKUP_DIR, 'thematic-clusters', 10);
}

async function createCodeBackup() {
  const backendFile = path.join(__dirname, 'backend.js');
  return await createBackup(backendFile, CODE_BACKUP_DIR, 'backend', 20);
}

async function createHtmlBackup(htmlFile = 'index.html') {
  const sourceFile = path.join(__dirname, htmlFile);
  const prefix = htmlFile.replace('.html', '');
  return await createBackup(sourceFile, HTML_BACKUP_DIR, prefix, 10);
}

// Umfassendes Backup aller wichtigen Dateien
async function createFullBackup() {
  console.log('[BACKUP] Erstelle umfassendes Backup...');
  const results = await Promise.all([
    createKeywordsBackup(),
    createSummaryBackup(),
    createThemesBackup(),
    createClustersBackup(),
    createCodeBackup(),
    createHtmlBackup('index.html'),
    createHtmlBackup('keyword-manager-advanced.html')
  ]);
  
  const successful = results.filter(r => r !== null).length;
  console.log(`[BACKUP] ✓ ${successful} von ${results.length} Backups erstellt`);
  
  return successful;
}

// Legacy-Funktion für Abwärtskompatibilität
async function cleanOldBackups() {
  await cleanOldBackupsGeneric(KEYWORDS_BACKUP_DIR, 'keywords-database', 10);
}

// ============================================================================
// ROBUSTE SUMMARY-DATENBANK MIT LOCKING-MECHANISMUS
// ============================================================================

// Lock-Queue für sequenzielles Schreiben in die Summary-DB
let summaryDbWriteQueue = Promise.resolve();
let summaryDbLock = false;

// Lade zentrale Summary-Datenbank
async function loadSummaryDatabase() {
  try {
    const data = await fs.readFile(SUMMARY_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('Zentrale Summary-DB nicht gefunden, erstelle neue...');
    return {};
  }
}

// Speichere zentrale Summary-Datenbank (veraltet - verwende saveSummaryToDatabase)
async function saveSummaryDatabase(summaryDB) {
  try {
    await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
    console.log('Zentrale Summary-DB gespeichert');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Summary-DB:', error);
    return false;
  }
}

// ROBUSTE FUNKTION: Speichere einzelne Summary in Datenbank (mit Locking)
// Diese Funktion verhindert Race Conditions bei parallelen Schreibzugriffen
async function saveSummaryToDatabase(lectureId, summaryData) {
  // Reihe diese Operation in die Queue ein
  return new Promise((resolve, reject) => {
    summaryDbWriteQueue = summaryDbWriteQueue.then(async () => {
      try {
        console.log(`[LOCK] Sperre DB für ${lectureId}...`);
        
        // Lade immer die aktuellste Version der Datenbank
        const summaryDB = await loadSummaryDatabase();
        
        // Füge neue Summary hinzu oder aktualisiere bestehende
        summaryDB[lectureId] = {
          summary: summaryData.summary,
          headings: summaryData.headings || [],
          timestamp: new Date().toISOString()
        };
        
        // Speichere Datenbank
        await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
        
        console.log(`[LOCK] ✓ Summary für ${lectureId} gespeichert (${Object.keys(summaryDB).length} Einträge total)`);
        
        resolve(true);
        
      } catch (error) {
        console.error(`[LOCK] ✗ Fehler beim Speichern von ${lectureId}:`, error);
        reject(error);
      }
    }).catch(error => {
      console.error('[LOCK] Queue-Fehler:', error);
      reject(error);
    });
  });
}

// ROBUSTE FUNKTION: Lösche mehrere Summaries aus Datenbank (mit Locking)
async function deleteSummariesFromDatabase(lectureIds) {
  return new Promise((resolve, reject) => {
    summaryDbWriteQueue = summaryDbWriteQueue.then(async () => {
      try {
        console.log(`[LOCK] Sperre DB für Bulk-Delete (${lectureIds.length} Einträge)...`);
        
        // Lade immer die aktuellste Version der Datenbank
        const summaryDB = await loadSummaryDatabase();
        
        // Lösche Einträge
        let deletedCount = 0;
        lectureIds.forEach(id => {
          if (summaryDB[id]) {
            delete summaryDB[id];
            deletedCount++;
          }
        });
        
        // Speichere Datenbank
        await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
        
        console.log(`[LOCK] ✓ ${deletedCount} Summaries gelöscht (${Object.keys(summaryDB).length} Einträge verbleiben)`);
        
        resolve(deletedCount);
        
      } catch (error) {
        console.error(`[LOCK] ✗ Fehler beim Löschen:`, error);
        reject(error);
      }
    }).catch(error => {
      console.error('[LOCK] Queue-Fehler:', error);
      reject(error);
    });
  });
}

// API: Summary speichern
app.post('/api/save-summary', async (req, res) => {
  try {
    const { lectureId, summary } = req.body;
    
    if (!lectureId || !summary) {
      return res.status(400).json({ error: 'lectureId und summary sind erforderlich' });
    }
    
    // Verwende robuste Speicherfunktion mit Locking
    const success = await saveSummaryToDatabase(lectureId, {
      summary: summary.summary,
      headings: summary.headings || []
    });
    
    if (success) {
      res.json({ success: true, message: `Summary für ${lectureId} gespeichert` });
    } else {
      res.status(500).json({ error: 'Fehler beim Speichern' });
    }
    
  } catch (error) {
    console.error('Fehler beim Speichern der Summary:', error);
    res.status(500).json({ error: error.message });
  }
});

// Statische Datei: summary-database.json bereitstellen
app.get('/summary-database.json', async (req, res) => {
  try {
    const summaryDB = await loadSummaryDatabase();
    res.json(summaryDB);
  } catch (error) {
    console.error('Fehler beim Laden der Summary-DB:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// KEYWORDS-DATENBANK MIT LOCKING-MECHANISMUS
// ============================================================================

// Lock-Queue für sequenzielles Schreiben in die Keywords-DB
let keywordsDbWriteQueue = Promise.resolve();

// Lade zentrale Keywords-Datenbank
async function loadKeywordsDatabase() {
  try {
    const data = await fs.readFile(KEYWORDS_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('[KEYWORDS-DB] Datenbank nicht gefunden, erstelle neue...');
    return {};
  }
}

// ROBUSTE FUNKTION: Speichere gesamte Keywords-Datenbank (mit Locking & Backup)
async function saveCompleteKeywordsDatabase(keywordsDB) {
  return new Promise((resolve, reject) => {
    keywordsDbWriteQueue = keywordsDbWriteQueue.then(async () => {
      try {
        console.log(`[KEYWORDS-LOCK] Sperre DB für komplettes Speichern...`);
        
        // WICHTIG: Erstelle Backup BEVOR wir speichern
        await createKeywordsBackup();
        
        // Validiere dass wir nicht versuchen, leere Daten zu speichern
        if (!keywordsDB || Object.keys(keywordsDB).length === 0) {
          console.error('[KEYWORDS-LOCK] ✗ WARNUNG: Versuch, leere Datenbank zu speichern - ABGEBROCHEN!');
          reject(new Error('Datenbank ist leer - Speichern abgebrochen'));
          return;
        }
        
        // Speichere Datenbank
        await fs.writeFile(KEYWORDS_DB_FILE, JSON.stringify(keywordsDB, null, 2), 'utf8');
        
        console.log(`[KEYWORDS-LOCK] ✓ Komplette Keywords-DB gespeichert (${Object.keys(keywordsDB).length} Einträge)`);
        
        resolve(true);
        
      } catch (error) {
        console.error('[KEYWORDS-LOCK] ✗ Fehler beim Speichern:', error);
        reject(error);
      }
    });
  });
}

// ROBUSTE FUNKTION: Speichere Keywords in Datenbank (mit Locking)
async function saveKeywordsToDatabase(lectureId, keywordsData) {
  return new Promise((resolve, reject) => {
    keywordsDbWriteQueue = keywordsDbWriteQueue.then(async () => {
      try {
        console.log(`[KEYWORDS-LOCK] Sperre DB für ${lectureId}...`);
        
        // WICHTIG: Erstelle Backup BEVOR wir speichern
        await createKeywordsBackup();
        
        // Lade immer die aktuellste Version der Datenbank
        const keywordsDB = await loadKeywordsDatabase();
        
        // Füge neue Keywords hinzu oder aktualisiere bestehende
        keywordsDB[lectureId] = {
          ...keywordsData,
          timestamp: new Date().toISOString()
        };
        
        // Validiere dass Datenbank nicht leer ist
        if (Object.keys(keywordsDB).length === 0) {
          console.error('[KEYWORDS-LOCK] ✗ WARNUNG: Datenbank wäre leer - ABGEBROCHEN!');
          reject(new Error('Datenbank ist leer - Speichern abgebrochen'));
          return;
        }
        
        // Speichere Datenbank
        await fs.writeFile(KEYWORDS_DB_FILE, JSON.stringify(keywordsDB, null, 2), 'utf8');
        
        console.log(`[KEYWORDS-LOCK] ✓ Keywords für ${lectureId} gespeichert (${Object.keys(keywordsDB).length} Einträge total)`);
        
        resolve(true);
        
      } catch (error) {
        console.error(`[KEYWORDS-LOCK] ✗ Fehler beim Speichern von ${lectureId}:`, error);
        reject(error);
      }
    }).catch(error => {
      console.error('[KEYWORDS-LOCK] Queue-Fehler:', error);
      reject(error);
    });
  });
}

// Funktion: Keywords aus Überschriften generieren (HAUPTEINSTIEG)
// Verwendet IMMER Claude KI für beste Qualität
async function generateKeywordsFromHeadings(lecture, headings) {
  console.log('[KEYWORDS-GEN] Verwende KI-basierte Extraktion mit Claude');
  return await generateKeywordsWithAI(lecture, headings);
}

// OPTIONAL: Keywords mit Claude KI extrahieren (nur wenn USE_AI_FOR_KEYWORDS=true)
// Hilfsfunktion: Parallele Verarbeitung mit Concurrency-Limit
async function processBatchWithConcurrency(items, processFn, concurrencyLimit = 5, delayMs = 200) {
  const results = [];
  const executing = [];
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    
    // Erstelle Promise für dieses Item
    const promise = (async () => {
      try {
        const result = await processFn(item, i);
        return { success: true, item, index: i, result };
      } catch (error) {
        return { success: false, item, index: i, error: error.message };
      }
    })();
    
    results.push(promise);
    executing.push(promise);
    
    // Entferne abgeschlossene Promises aus executing
    promise.then(() => {
      executing.splice(executing.indexOf(promise), 1);
    });
    
    // Warte, wenn Concurrency-Limit erreicht
    if (executing.length >= concurrencyLimit) {
      await Promise.race(executing);
    }
    
    // Kleine Verzögerung zwischen Starts (für Rate Limiting)
    if (i < items.length - 1 && delayMs > 0) {
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  
  // Warte auf alle verbleibenden Promises
  return await Promise.all(results);
}

// Normalisiere und dedupliziere Schlagwörter
function normalizeKeywords(keywords) {
  if (!keywords || !Array.isArray(keywords)) return [];
  
  const normalized = new Map();
  
  keywords.forEach(kw => {
    let term = kw.term || kw;
    if (typeof term !== 'string') return;
    
    // Bereinige und kapitalisiere
    term = term.trim();
    
    // Kapitalisiere erste Buchstaben von Substantiven
    term = term.split(/\s+/).map(word => {
      // Kleine Wörter (und, oder, etc.) kleinschreiben
      if (['und', 'oder', 'der', 'die', 'das', 'des', 'dem', 'den'].includes(word.toLowerCase())) {
        return word.toLowerCase();
      }
      // Sonst: Erster Buchstabe groß
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    }).join(' ');
    
    // Normalisiere ähnliche Begriffe
    const lower = term.toLowerCase();
    const baseForm = lower
      .replace(/\s+/g, ' ')
      .replace(/ä/g, 'a').replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ß/g, 'ss');
    
    // Erkenne Duplikate/Varianten
    let isDuplicate = false;
    for (const [existingBase, existingTerm] of normalized.entries()) {
      // Exakte Übereinstimmung (case-insensitive)
      if (existingTerm.toLowerCase() === lower) {
        isDuplicate = true;
        break;
      }
      
      // Singular/Plural Erkennung
      if (lower.endsWith('en') && lower.slice(0, -2) === existingTerm.toLowerCase()) {
        isDuplicate = true;
        break;
      }
      if (existingTerm.toLowerCase().endsWith('en') && existingTerm.toLowerCase().slice(0, -2) === lower) {
        isDuplicate = true;
        break;
      }
      
      // Ähnliche zusammengesetzte Begriffe
      const existingWords = existingTerm.toLowerCase().split(' ');
      const currentWords = lower.split(' ');
      
      // "karma" vs "kosmisches karma" -> behalte längeren
      if (existingWords.length === 1 && currentWords.length > 1 && currentWords.includes(existingWords[0])) {
        // Ersetze kürzeren durch längeren
        normalized.delete(existingBase);
        break;
      }
      if (currentWords.length === 1 && existingWords.length > 1 && existingWords.includes(currentWords[0])) {
        isDuplicate = true;
        break;
      }
    }
    
    if (!isDuplicate && term.length > 0) {
      normalized.set(baseForm, term);
    }
  });
  
  const result = Array.from(normalized.values());
  console.log(`[NORMALIZE] ${keywords.length} Keywords → ${result.length} normalisiert`);
  
  return result.map(term => {
    // Bewahre ursprüngliche Struktur falls vorhanden
    const original = keywords.find(k => (k.term || k).toLowerCase() === term.toLowerCase());
    if (original && typeof original === 'object') {
      return { ...original, term };
    }
    return { term };
  });
}

async function generateKeywordsWithAI(lecture, headings) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('[KEYWORDS-GEN] Kein Claude API Key - verwende Regel-basiert');
    return extractKeywordsFromHeadings(headings);
  }
  
  // Formatiere alle Überschriften für den Prompt
  const headingsText = headings
    .map((h, idx) => `${idx + 1}. "${h.text}" [${h.level}, Index: ${h.index}]`)
    .join('\n');
  
  const prompt = `Analysiere die folgenden Zwischenüberschriften (H3 und H4) aus einem Vortrag von Rudolf Steiner.
Erstelle für JEDE Überschrift EIN prägnantes Schlagwort.

ANFORDERUNGEN:
- JEDE Überschrift wird zu EINEM Schlagwort
- Schlagwörter können 1-3 Worte lang sein
- Reduziere die Überschrift auf das Wesentliche
- Mischung aus abstrakten (z.B. "Karma", "Erkenntnistheorie") und konkreten Begriffen (z.B. "Deutsches Reich", "Rosenkreuzer")
- WICHTIG: Korrekte deutsche Großschreibung - Substantive IMMER groß ("Karma", "Reinkarnation", "Tod"), Adjektive und Verbformen klein ("vorgeburtlich", "kosmisch")
- Kleine Wörter wie "und", "der", "die" immer klein
- Behalte den Index der Original-Überschrift bei

BEISPIELE:
"Die Entstehung des deutschen Reiches" → "Deutsches Reich"
"Karma und Reinkarnation im indischen Denken" → "Karma und Reinkarnation"
"Die heiligen Rishis als Bewahrer der Urweisheit" → "Heilige Rishis"
"Der Verfall des Rittertums" → "Rittertum"
"Vorgeburtliche Erziehung" → "Vorgeburtliche Erziehung"
"Das kosmische Karma" → "Kosmisches Karma"

ÜBERSCHRIFTEN:
${headingsText}

ANTWORT-FORMAT (JSON):
[
  {
    "term": "Schlagwort (1-3 Worte)",
    "index": "^abc123",
    "heading": "Original-Überschrift"
  },
  ...
]

Wichtig: Ein Eintrag pro Überschrift! Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text.`;

  try {
    console.log('[KEYWORDS-GEN] Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    let responseText = result.content[0].text.trim();
    
    // Entferne Markdown Code-Blöcke falls vorhanden
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    let keywords = JSON.parse(responseText);
    
    console.log('[KEYWORDS-GEN] ✓ Keywords mit KI extrahiert:', keywords.length, 'aus', headings.length, 'Überschriften');
    
    // Füge level-Feld hinzu basierend auf Original-Überschriften
    keywords = keywords.map(kw => {
      const originalHeading = headings.find(h => h.index === kw.index || h.text === kw.heading);
      return {
        ...kw,
        level: originalHeading?.level || 'h3' // Übernehme level von Original-Überschrift
      };
    });
    
    // Normalisiere Keywords (Großschreibung, Deduplizierung)
    keywords = normalizeKeywords(keywords);
    
    return keywords;

  } catch (error) {
    console.error('[KEYWORDS-GEN] Fehler bei Claude API:', error);
    return extractKeywordsFromHeadings(headings);
  }
}

// ============================================================================
// ITERATIVE KEYWORD-GENERIERUNG MIT SEED-VOKABULAR
// ============================================================================

// Lade Seed-Keywords aus Keywords - merged.md
function loadSeedKeywords() {
  try {
    const content = fsSync.readFileSync(path.join(__dirname, 'Keywords', 'Keywords - merged.md'), 'utf8');
    const regex = /^## \[\[([^\]]+)\]\]/gm;
    const matches = [...content.matchAll(regex)];
    const seedKeywords = matches.map(m => m[1].trim());
    
    console.log(`[SEED] Geladen: ${seedKeywords.length} Seed-Keywords aus Keywords - merged.md`);
    return seedKeywords;
  } catch (error) {
    console.error('[SEED] Fehler beim Laden der Seed-Keywords:', error.message);
    return [];
  }
}

// Extrahiere Hauptbegriffe aus Summary
async function extractKeyTermsFromSummary(summary, existingVocabulary) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('[SUMMARY-TERMS] Kein Claude API Key - Fallback auf Regel-basiert');
    // Einfache Regel: Häufigste Substantive mit Großbuchstaben
    const words = summary.split(/\s+/);
    const capitalWords = words.filter(w => w.length > 3 && /^[A-ZÄÖÜ]/.test(w));
    return [...new Set(capitalWords)].slice(0, 8);
  }
  
  const vocabSample = existingVocabulary.slice(0, 500).join(', ');
  
  const prompt = `Analysiere diese Vortrag-Summary und extrahiere die 5-8 wichtigsten HAUPTTHEMEN.

BEVORZUGE Begriffe aus diesem bestehenden Vokabular:
${vocabSample}

SUMMARY:
"${summary}"

REGELN:
1. Nur zentrale Themen/Konzepte (keine Details)
2. Substantive oder feste Begriffe
3. BEVORZUGT bestehende Vokabular-Begriffe verwenden
4. 1-3 Worte pro Begriff
5. Korrekte deutsche Großschreibung

BEISPIELE:
"Steiner analysiert das Hochmittelalter... Kreuzzüge... Rittertum..."
→ ["Mittelalter", "Kreuzzüge", "Rittertum", "Deutsche Geschichte"]

"Die Entwicklung der Karma-Lehre in verschiedenen Kulturen..."
→ ["Karma", "Reinkarnation", "Östliche Weisheit", "Kulturentwicklung"]

Ausgabe als JSON-Array: ["Begriff1", "Begriff2", ...]
Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text.`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1024,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    let responseText = result.content[0].text.trim();
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    const terms = JSON.parse(responseText);
    console.log(`[SUMMARY-TERMS] Extrahiert: ${terms.join(', ')}`);
    return terms;
    
  } catch (error) {
    console.error('[SUMMARY-TERMS] Fehler bei Claude API:', error.message);
    return [];
  }
}

// Generiere Keywords iterativ mit Summary-Kontext und bestehendem Vokabular
async function generateKeywordsIterativeWithSummary(lectureId, summary, headings, vocabulary, frequencyMap = {}) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('[KEYWORDS-ITER] Kein Claude API Key - verwende Regel-basiert');
    return extractKeywordsFromHeadings(headings);
  }
  
  // 1. Extrahiere Hauptbegriffe aus Summary
  const summaryKeyTerms = await extractKeyTermsFromSummary(summary, vocabulary);
  
  // 2. Finde thematisch passende Keywords (die in Summary-Begriffen vorkommen)
  const relatedKeywords = vocabulary.filter(kw => 
    summaryKeyTerms.some(term => 
      kw.toLowerCase().includes(term.toLowerCase()) || 
      term.toLowerCase().includes(kw.toLowerCase())
    )
  ).slice(0, 50);
  
  // 3. Häufigste Keywords (Top 100)
  const sortedByFreq = Object.entries(frequencyMap)
    .sort((a, b) => b[1] - a[1])
    .map(([term]) => term)
    .slice(0, 100);
  
  // 4. Formatiere Überschriften
  const headingsText = headings
    .map((h, idx) => `${idx + 1}. "${h.text}" [${h.level}, Index: ${h.index}]`)
    .join('\n');
  
  const prompt = `VORTRAG: ${lectureId}

VORTRAG-SUMMARY (Übergeordnetes Thema):
"${summary}"

HAUPTBEGRIFFE AUS SUMMARY:
${summaryKeyTerms.join(', ')}

BESTEHENDES VOKABULAR:
Gesamt: ${vocabulary.length} Begriffe
Thematisch passend: ${relatedKeywords.join(', ') || 'keine'}
Häufigste: ${sortedByFreq.slice(0, 80).join(', ')}

NEUE ÜBERSCHRIFTEN (zu verschlagworten):
${headingsText}

AUFGABE:
Erstelle für JEDE Überschrift EIN prägnantes Schlagwort (1-3 Worte).

PRIORITÄTEN:
1. HÖCHSTE: Begriffe die in der Summary vorkommen
2. HOHE: Thematisch passende bestehende Keywords
3. MITTLERE: Häufige bestehende Keywords
4. NIEDRIGE: Neue Keywords (NUR wenn kein bestehendes passt)

REGELN:
- BEVORZUGT bestehende Begriffe wiederverwenden
- Bei Synonymen: Wähle die häufigere/in-Summary-erwähnte Form
- Korrekte deutsche Großschreibung (Substantive groß)
- "und", "oder", "der", "die" etc. kleinschreiben
- Bei hierarchischen Begriffen: Passende Granularität wählen

SEMANTIC MATCHING:
- "Astralleib" ≈ "Astralischer Leib" → VERWENDE das häufigere
- "Karma und Reinkarnation" vs "Karma" → WÄHLE passende Granularität

AUSGABE (JSON):
[
  {
    "term": "Gewähltes Schlagwort",
    "index": "^abc123",
    "heading": "Original-Überschrift",
    "matchType": "summary-derived|existing-exact|existing-similar|new",
    "matchedExisting": "Name des gematchten Keywords (oder null)",
    "summaryMentioned": true/false,
    "confidence": 0.0-1.0
  }
]

Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text.`;

  try {
    console.log(`[KEYWORDS-ITER] ${lectureId}: Rufe Claude API auf...`);
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    let responseText = result.content[0].text.trim();
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    let keywords = JSON.parse(responseText);
    
    // Füge level-Feld hinzu
    keywords = keywords.map(kw => {
      const originalHeading = headings.find(h => h.index === kw.index || h.text === kw.heading);
      return {
        ...kw,
        level: originalHeading?.level || 'h3'
      };
    });
    
    console.log(`[KEYWORDS-ITER] ${lectureId}: ✓ ${keywords.length} Keywords generiert`);
    console.log(`[KEYWORDS-ITER]   Existing: ${keywords.filter(k => k.matchType !== 'new').length}, New: ${keywords.filter(k => k.matchType === 'new').length}`);
    
    return keywords;

  } catch (error) {
    console.error(`[KEYWORDS-ITER] ${lectureId}: Fehler bei Claude API:`, error.message);
    return extractKeywordsFromHeadings(headings);
  }
}

// Berechne Keyword-Häufigkeit
function calculateKeywordFrequency(keywordsDB) {
  const frequencyMap = {};
  
  for (const [lectureId, data] of Object.entries(keywordsDB)) {
    if (!data.keywords) continue;
    data.keywords.forEach(kw => {
      const term = kw.term.trim();
      frequencyMap[term] = (frequencyMap[term] || 0) + 1;
    });
  }
  
  return frequencyMap;
}

// ============================================================================
// BATCH-REGENERIERUNG GA-BAND-WEISE
// ============================================================================

// Hilfsfunktion: Gruppiere Vorträge nach GA-Band
function groupLecturesByGA(summaryDB) {
  const gaGroups = {};
  
  for (const lectureId of Object.keys(summaryDB)) {
    // Match GA-Nummern mit optionalem Suffix (z.B. GA304a, GA051)
    const gaMatch = lectureId.match(/^GA(\d+[a-z]?)/i);
    const gaNum = gaMatch ? gaMatch[1] : 'unknown';
    const gaKey = `GA${gaNum}`;
    
    if (!gaGroups[gaKey]) {
      gaGroups[gaKey] = [];
    }
    gaGroups[gaKey].push(lectureId);
  }
  
  // Sortiere GA-Bände numerisch (mit Suffix-Unterstützung)
  const sortedGAs = Object.keys(gaGroups).sort((a, b) => {
    const matchA = a.match(/GA(\d+)([a-z]?)/i);
    const matchB = b.match(/GA(\d+)([a-z]?)/i);
    
    const numA = matchA ? parseInt(matchA[1]) : 0;
    const numB = matchB ? parseInt(matchB[1]) : 0;
    
    if (numA !== numB) {
      return numA - numB;
    }
    
    // Bei gleicher Nummer: Sortiere nach Suffix (a < b < c)
    const suffixA = matchA && matchA[2] ? matchA[2].toLowerCase() : '';
    const suffixB = matchB && matchB[2] ? matchB[2].toLowerCase() : '';
    return suffixA.localeCompare(suffixB);
  });
  
  return { gaGroups, sortedGAs };
}

// Funktion: Erweitere bestehende Cluster mit neuen Keywords
async function expandClustersWithNewKeywords(newKeywords, existingClusters) {
  console.log(`[CLUSTERS] Erweitere Cluster mit ${newKeywords.length} neuen Keywords...`);
  
  const prompt = `Du bist ein Experte für thematische Klassifikation von philosophischen und anthroposophischen Begriffen.

BESTEHENDE THEMATISCHE CLUSTER:
${JSON.stringify(existingClusters, null, 2)}

NEUE KEYWORDS ZUM ZUORDNEN:
${newKeywords.join(', ')}

AUFGABE:
1. Ordne jedes neue Keyword einem passenden bestehenden Cluster zu
2. Wenn ein Keyword zu KEINEM bestehenden Cluster passt, schlage einen NEUEN Cluster vor
3. Vermeide redundante Cluster - nur neue Cluster wenn wirklich nötig
4. Sei konservativ: Bevorzuge Zuordnung zu bestehenden Clustern

ANTWORTE im folgenden JSON-Format:
{
  "assignments": {
    "ClusterName": ["keyword1", "keyword2", ...],
    ...
  },
  "newClusters": {
    "NewClusterName": {
      "description": "Beschreibung des neuen Themenbereichs",
      "keywords": ["keyword1", ...]
    },
    ...
  },
  "reasoning": "Kurze Erklärung der Entscheidungen"
}`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8000,
        temperature: 0.3,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Claude API Error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const responseText = data.content[0].text;
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    
    if (!jsonMatch) {
      throw new Error('No valid JSON in Claude response');
    }

    const result = JSON.parse(jsonMatch[0]);
    console.log(`[CLUSTERS] Expansion: ${Object.keys(result.assignments || {}).length} bestehende erweitert, ${Object.keys(result.newClusters || {}).length} neue erstellt`);
    
    return result;
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler bei Expansion:', error);
    throw error;
  }
}

// Endpoint: Liste verfügbare GA-Bände
app.get('/api/keywords/available-ga-volumes', async (req, res) => {
  try {
    const summaryDB = JSON.parse(fsSync.readFileSync(SUMMARY_DB_FILE, 'utf8'));
    const { gaGroups, sortedGAs } = groupLecturesByGA(summaryDB);
    
    // Lade Keywords-Database um zu prüfen welche Bände bereits verarbeitet wurden
    let keywordsDB = {};
    try {
      keywordsDB = JSON.parse(fsSync.readFileSync(KEYWORDS_DB_FILE, 'utf8'));
    } catch (error) {
      console.log('[GA-VOLUMES] Keine Keywords-Database gefunden');
    }
    
    const volumes = sortedGAs.map(ga => {
      // Prüfe ob mindestens ein Vortrag dieses Bandes in keywordsDB vorhanden ist
      const hasKeywords = gaGroups[ga].some(lectureId => keywordsDB[lectureId]);
      
      return {
        volume: ga,
        lectureCount: gaGroups[ga].length,
        lectures: gaGroups[ga].sort(),
        hasKeywords: hasKeywords
      };
    });
    
    res.json({ volumes });
  } catch (error) {
    console.error('[GA-VOLUMES] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Regeneriere einen GA-Band
app.post('/api/keywords/regenerate-ga-volume', async (req, res) => {
  const { gaVolume, useExistingVocab, updateClusters, parallelBatchSize, forceReprocess } = req.body;
  const PARALLEL_BATCH_SIZE = parallelBatchSize || 5; // Default: 5 parallel
  
  console.log(`\n[GA-BATCH] Starte Regenerierung für ${gaVolume}...`);
  console.log(`[GA-BATCH] Verwende bestehendes Vokabular: ${useExistingVocab ? 'Ja' : 'Nein (nur Seeds)'}`);
  console.log(`[GA-BATCH] Cluster iterativ erweitern: ${updateClusters ? 'Ja' : 'Nein'}`);
  console.log(`[GA-BATCH] Parallele Verarbeitung: ${PARALLEL_BATCH_SIZE} Vorträge pro Batch`);
  console.log(`[GA-BATCH] Bereits verarbeitete neu verarbeiten: ${forceReprocess ? 'Ja' : 'Nein'}`);
  
  try {
    // 1. Lade Seed-Keywords
    const seedKeywords = loadSeedKeywords();
    if (seedKeywords.length === 0) {
      throw new Error('Keine Seed-Keywords gefunden');
    }
    
    // 2. Lade Full Lectures für Datum/Jahr
    if (Object.keys(fullLectures).length === 0) {
      console.log('[GA-BATCH] Lade Full Lectures für Metadaten...');
      await loadFullLectures();
    }
    
    // 3. Lade Summary-Database
    const summaryDB = JSON.parse(fsSync.readFileSync(SUMMARY_DB_FILE, 'utf8'));
    
    // 3. Lade existierende Keywords-Database (falls useExistingVocab)
    let existingKeywordsDB = {};
    let masterVocabulary = new Set(seedKeywords);
    let frequencyMap = {};
    
    if (useExistingVocab) {
      try {
        existingKeywordsDB = JSON.parse(fsSync.readFileSync(KEYWORDS_DB_FILE, 'utf8'));
        
        // Extrahiere alle bereits verwendeten Keywords
        for (const [lectureId, data] of Object.entries(existingKeywordsDB)) {
          if (!data.keywords) continue;
          data.keywords.forEach(kw => {
            masterVocabulary.add(kw.term);
            frequencyMap[kw.term] = (frequencyMap[kw.term] || 0) + 1;
          });
        }
        
        console.log(`[GA-BATCH] Geladen: ${masterVocabulary.size} Keywords aus bestehender Datenbank`);
      } catch (error) {
        console.log(`[GA-BATCH] Keine bestehende Datenbank gefunden, starte mit Seeds`);
      }
    }
    
    // 4. Filtere Vorträge für diesen GA-Band
    const { gaGroups } = groupLecturesByGA(summaryDB);
    const lectures = gaGroups[gaVolume];
    
    if (!lectures || lectures.length === 0) {
      throw new Error(`Keine Vorträge für ${gaVolume} gefunden`);
    }
    
    console.log(`[GA-BATCH] ${gaVolume}: ${lectures.length} Vorträge`);
    console.log(`[GA-BATCH] Start-Vokabular: ${masterVocabulary.size} Keywords`);
    
    // 5. Sortiere Vorträge innerhalb des GA-Bands
    const sortedLectures = lectures.sort();
    
    const newKeywordsDB = {};
    const stats = {
      gaVolume: gaVolume,
      processed: 0,
      skipped: 0,
      totalKeywords: 0,
      newKeywords: 0,
      reusedKeywords: 0,
      errors: 0,
      vocabularyGrowth: []
    };
    
    // 6. Iteriere durch Vorträge dieses GA-Bands (PARALLEL mit Batching)
    // PARALLEL_BATCH_SIZE aus Request-Parameter übernommen
    // Empfohlene Werte:
    //   - 3-5: Sicher für Claude Tier 1 (50 req/min, 50k tokens/min)
    //   - 10-20: Optimal für Claude Tier 2 (1000 req/min, 2M tokens/min)
    //   - 5: Default - funktioniert zuverlässig für beide Tiers
    
    for (let batchStart = 0; batchStart < sortedLectures.length; batchStart += PARALLEL_BATCH_SIZE) {
      const batchEnd = Math.min(batchStart + PARALLEL_BATCH_SIZE, sortedLectures.length);
      const batch = sortedLectures.slice(batchStart, batchEnd);
      
      console.log(`\n[GA-BATCH] Batch ${Math.floor(batchStart/PARALLEL_BATCH_SIZE)+1}: Verarbeite ${batch.length} Vorträge parallel...`);
      
      // Erstelle Array von Promises für parallele Verarbeitung
      const batchPromises = batch.map(async (lectureId, batchIndex) => {
        const globalIndex = batchStart + batchIndex;
        const data = summaryDB[lectureId];
        
        if (!data.headings || data.headings.length === 0) {
          console.log(`[GA-BATCH] ${globalIndex+1}/${sortedLectures.length} ${lectureId}: Überspringe (keine Überschriften)`);
          return { lectureId, skipped: true };
        }
        
        // Überspringe bereits verarbeitete Vorträge (nur wenn useExistingVocab aktiv)
        if (useExistingVocab && existingKeywordsDB[lectureId]) {
          console.log(`[GA-BATCH] ${globalIndex+1}/${sortedLectures.length} ${lectureId}: Überspringe (bereits verarbeitet)`);
          return { lectureId, skipped: true, reason: 'already_processed' };
        }
        
        try {
          console.log(`[GA-BATCH] ${globalIndex+1}/${sortedLectures.length} ${lectureId}: Starte...`);
          
          // Snapshot des aktuellen Vokabulars für diese Verarbeitung
          const vocabSnapshot = Array.from(masterVocabulary);
          const freqSnapshot = { ...frequencyMap };
          
          // Generiere Keywords mit aktuellem Vokabular
          const keywords = await generateKeywordsIterativeWithSummary(
            lectureId,
            data.summary || '',
            data.headings,
            vocabSnapshot,
            freqSnapshot
          );
          
          // Analysiere Results
          const newKws = keywords.filter(k => k.matchType === 'new');
          const reusedKws = keywords.filter(k => k.matchType !== 'new');
          
          // Extrahiere Datum und Jahr aus fullLectures
          const lecture = fullLectures[lectureId];
          const date = lecture?.date || lecture?.dateString || '';
          const year = date ? parseInt(date.substring(0, 4)) : null;
          const gaMatch = lectureId.match(/^GA(\d+)/);
          const gaVol = gaMatch ? `GA${gaMatch[1]}` : null;
          
          console.log(`[GA-BATCH] ${globalIndex+1}/${sortedLectures.length} ${lectureId}: ✓ ${keywords.length} KWs (${newKws.length} neu, ${reusedKws.length} wiederverwendet)`);
          
          return {
            lectureId,
            date,
            year,
            gaVolume: gaVol,
            summary: data.summary,
            keywords,
            newKws,
            reusedKws,
            skipped: false
          };
          
        } catch (error) {
          console.error(`[GA-BATCH] ${globalIndex+1}/${sortedLectures.length} ${lectureId}: FEHLER:`, error.message);
          return { lectureId, error: error.message, skipped: false };
        }
      });
      
      // Warte auf alle Promises in diesem Batch
      const batchResults = await Promise.all(batchPromises);
      
      // Verarbeite Batch-Ergebnisse sequenziell (wichtig für Vokabular-Updates!)
      for (const result of batchResults) {
        if (result.skipped) {
          stats.skipped++;
          continue;
        }
        
        if (result.error) {
          stats.errors++;
          continue;
        }
        
        // Update Master-Vokabular (NACH der Verarbeitung, sequenziell!)
        result.newKws.forEach(kw => masterVocabulary.add(kw.term));
        
        // Update Frequency Map
        result.keywords.forEach(kw => {
          frequencyMap[kw.term] = (frequencyMap[kw.term] || 0) + 1;
        });
        
        // Speichere mit aktualisierter Vokabular-Größe
        newKeywordsDB[result.lectureId] = {
          lectureId: result.lectureId,
          date: result.date,
          year: result.year,
          gaVolume: result.gaVolume,
          summary: result.summary,
          keywords: result.keywords,
          vocabSizeAtGeneration: masterVocabulary.size,
          generated: new Date().toISOString()
        };
        
        // Update Stats
        stats.processed++;
        stats.totalKeywords += result.keywords.length;
        stats.newKeywords += result.newKws.length;
        stats.reusedKeywords += result.reusedKws.length;
        stats.vocabularyGrowth.push({
          lecture: result.lectureId,
          vocabSize: masterVocabulary.size,
          newInThisLecture: result.newKws.length
        });
      }
      
      console.log(`[GA-BATCH] Batch abgeschlossen. Vokabular: ${masterVocabulary.size} Keywords\n`);
      
      // Kleine Pause zwischen Batches (Rate Limit Protection)
      if (batchEnd < sortedLectures.length) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    // 7. Finale Statistiken
    const startVocabSize = useExistingVocab ? Object.keys(existingKeywordsDB).length * 10 : seedKeywords.length; // Schätzung
    console.log(`\n[GA-BATCH] === ${gaVolume} FERTIG ===`);
    console.log(`[GA-BATCH] Verarbeitet: ${stats.processed}/${sortedLectures.length}`);
    if (stats.skipped > 0) {
      console.log(`[GA-BATCH] Übersprungen: ${stats.skipped} (bereits verarbeitet)`);
    }
    console.log(`[GA-BATCH] Fehler: ${stats.errors}`);
    console.log(`[GA-BATCH] Total Keywords generiert: ${stats.totalKeywords}`);
    console.log(`[GA-BATCH] Neue Keywords: ${stats.newKeywords}`);
    console.log(`[GA-BATCH] Wiederverwendet: ${stats.reusedKeywords}`);
    console.log(`[GA-BATCH] Wiederverwendungsrate: ${(stats.reusedKeywords / stats.totalKeywords * 100).toFixed(1)}%`);
    console.log(`[GA-BATCH] End-Vokabular: ${masterVocabulary.size} Keywords`);
    
    // 8. Merge mit bestehender Datenbank (falls useExistingVocab)
    let finalDB = newKeywordsDB;
    if (useExistingVocab) {
      finalDB = { ...existingKeywordsDB, ...newKeywordsDB };
      console.log(`[GA-BATCH] Gemerged mit bestehender Datenbank: ${Object.keys(finalDB).length} total Vorträge`);
    }
    
    // 9. Speichere Ergebnis
    const resultPath = path.join(__dirname, `keywords-database-${gaVolume}.json`);
    fsSync.writeFileSync(resultPath, JSON.stringify(finalDB, null, 2));
    console.log(`[GA-BATCH] Gespeichert: ${resultPath}`);
    
    // 10. Optional: Aktualisiere Haupt-Datenbank
    if (useExistingVocab) {
      // BACKUP erstellen vor dem Speichern
      await createKeywordsBackup();
      
      // Validiere dass Datenbank nicht leer ist
      if (Object.keys(finalDB).length === 0) {
        console.error('[GA-BATCH] ✗ WARNUNG: finalDB ist leer - Haupt-Datenbank wird NICHT überschrieben!');
      } else {
        fsSync.writeFileSync(KEYWORDS_DB_FILE, JSON.stringify(finalDB, null, 2));
        console.log(`[GA-BATCH] Haupt-Datenbank aktualisiert: keywords-database.json`);
      }
    }
    
    // 11. Optional: Erweitere Cluster mit neuen Keywords
    let clusterUpdateInfo = null;
    if (updateClusters && stats.newKeywords > 0) {
      console.log(`\n[GA-BATCH] Erweitere Cluster mit ${stats.newKeywords} neuen Keywords...`);
      
      try {
        // Sammle alle neuen Keywords
        const newKeywords = [];
        for (const [lectureId, data] of Object.entries(newKeywordsDB)) {
          if (data.keywords) {
            data.keywords.forEach(kw => {
              // Nur Keywords die nicht im Seed-Vokabular waren
              if (!seedKeywords.includes(kw.term) && !newKeywords.includes(kw.term)) {
                newKeywords.push(kw.term);
              }
            });
          }
        }
        
        if (newKeywords.length > 0) {
          // Lade existierende Cluster
          let existingClusters = null;
          const clustersPath = path.join(__dirname, 'thematic-clusters.json');
          
          if (fsSync.existsSync(clustersPath)) {
            existingClusters = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
            
            // Erweitere Cluster iterativ
            const expansion = await expandClustersWithNewKeywords(newKeywords, existingClusters);
            
            // Merge assignments in bestehende Cluster
            if (expansion.assignments) {
              Object.entries(expansion.assignments).forEach(([clusterName, keywords]) => {
                if (existingClusters[clusterName]) {
                  existingClusters[clusterName].keywords = [
                    ...new Set([...existingClusters[clusterName].keywords, ...keywords])
                  ];
                }
              });
            }
            
            // Füge neue Cluster hinzu
            if (expansion.newClusters) {
              Object.entries(expansion.newClusters).forEach(([clusterName, data]) => {
                existingClusters[clusterName] = data;
              });
            }
            
            // Speichere erweiterte Cluster
            fsSync.writeFileSync(clustersPath, JSON.stringify(existingClusters, null, 2));
            
            clusterUpdateInfo = {
              newKeywordsProcessed: newKeywords.length,
              clustersExtended: Object.keys(expansion.assignments || {}).length,
              newClustersCreated: Object.keys(expansion.newClusters || {}).length,
              totalClusters: Object.keys(existingClusters).length
            };
            
            console.log(`[GA-BATCH] ✓ Cluster erweitert: ${clusterUpdateInfo.clustersExtended} bestehende, ${clusterUpdateInfo.newClustersCreated} neue`);
          } else {
            console.log(`[GA-BATCH] Keine Cluster gefunden - bitte erst initial generieren`);
            clusterUpdateInfo = { error: 'Keine Cluster gefunden' };
          }
        }
      } catch (error) {
        console.error('[GA-BATCH] Fehler bei Cluster-Erweiterung:', error);
        clusterUpdateInfo = { error: error.message };
      }
    }
    
    res.json({
      success: true,
      gaVolume: gaVolume,
      stats: {
        ...stats,
        startVocabulary: startVocabSize,
        finalVocabulary: masterVocabulary.size,
        vocabularyGrowth: masterVocabulary.size - startVocabSize,
        reuseRate: stats.totalKeywords > 0 
          ? (stats.reusedKeywords / stats.totalKeywords * 100).toFixed(1) + '%'
          : '0%'
      },
      resultFile: `keywords-database-${gaVolume}.json`,
      mainDatabaseUpdated: useExistingVocab,
      clusterUpdate: clusterUpdateInfo
    });
    
  } catch (error) {
    console.error(`[GA-BATCH] Fehler:`, error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// THEMATISCHE CLUSTER-GENERIERUNG
// ============================================================================

// Generiere übergeordnete Themenbereiche aus Seed-Keywords
app.post('/api/themes/generate-clusters-from-seeds', async (req, res) => {
  console.log('\n[THEMES] Generiere thematische Cluster aus Seed-Keywords...');
  
  try {
    const claudeApiKey = process.env.CLAUDE_API_KEY;
    if (!claudeApiKey) {
      throw new Error('CLAUDE_API_KEY nicht gefunden');
    }
    
    // 1. Lade Seed-Keywords
    const seedKeywords = loadSeedKeywords();
    if (seedKeywords.length === 0) {
      throw new Error('Keine Seed-Keywords gefunden');
    }
    
    console.log(`[THEMES] Analysiere ${seedKeywords.length} Seed-Keywords...`);
    
    // 2. Erstelle Prompt für Claude
    const prompt = `Analysiere diese Liste von Schlüsselbegriffen aus Rudolf Steiners Gesamtausgabe und erstelle daraus übergeordnete THEMENBEREICHE.

ALLE SEED-KEYWORDS (${seedKeywords.length} Begriffe):
${seedKeywords.join(', ')}

AUFGABE:
Identifiziere die natürlichen thematischen Gruppierungen in dieser Liste.
Erstelle ÜBERGEORDNETE THEMENBEREICHE, die diese Keywords sinnvoll strukturieren.

ANFORDERUNGEN:
1. Anzahl: Finde die natürliche Anzahl von Themenbereichen (vermutlich 8-15)
2. Keine vorab festgelegte Anzahl - lass die Struktur organisch entstehen
3. Jeder Themenbereich sollte:
   - Einen klaren, prägnanten deutschen Namen haben
   - Eine kurze Beschreibung (1-2 Sätze) haben
   - Mindestens 20-30 Keywords umfassen
   - Thematisch kohärent sein
4.Deckung: Zusammen sollten die Bereiche >90% der Keywords abdecken
5. Restliche Keywords: Sammle in "Verschiedenes" oder ähnlich

BEISPIEL-STRUKTUR (nur als Orientierung):
{
  "Themenbereich-Name": {
    "description": "Kurze Beschreibung des Themenbereichs",
    "keywords": ["Keyword1", "Keyword2", ...],
    "keywordCount": 45,
    "coverage": "12%"
  },
  ...
}

WICHTIG:
- Verwende die EXAKTEN Keyword-Schreibweisen aus der Liste
- Sei inklusiv: Ein Keyword kann zu mehreren Bereichen gehören
- Priorisiere thematische Kohärenz über gleichmäßige Verteilung
- Deutsche Begriffe für Themenbereiche

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.`;

    console.log('[THEMES] Rufe Claude API auf...');
    
    // 3. Claude API Call
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8192,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    let responseText = result.content[0].text.trim();
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    const clusters = JSON.parse(responseText);
    
    // 4. Validierung und Statistiken
    const clusterNames = Object.keys(clusters);
    let totalKeywordsInClusters = 0;
    let uniqueKeywords = new Set();
    
    for (const [name, data] of Object.entries(clusters)) {
      totalKeywordsInClusters += data.keywords.length;
      data.keywords.forEach(kw => uniqueKeywords.add(kw));
    }
    
    const coverage = (uniqueKeywords.size / seedKeywords.length * 100).toFixed(1);
    
    console.log(`[THEMES] ✓ ${clusterNames.length} Themenbereiche generiert`);
    console.log(`[THEMES] Abdeckung: ${uniqueKeywords.size}/${seedKeywords.length} (${coverage}%)`);
    clusterNames.forEach(name => {
      console.log(`[THEMES]   - ${name}: ${clusters[name].keywords.length} Keywords`);
    });
    
    // 5. Speichere Ergebnis
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    fsSync.writeFileSync(clustersPath, JSON.stringify({
      generated: new Date().toISOString(),
      seedKeywordsCount: seedKeywords.length,
      clustersCount: clusterNames.length,
      coverage: coverage + '%',
      clusters: clusters
    }, null, 2));
    
    console.log(`[THEMES] Gespeichert: ${clustersPath}`);
    
    res.json({
      success: true,
      clustersCount: clusterNames.length,
      coverage: coverage + '%',
      uniqueKeywordsCovered: uniqueKeywords.size,
      totalSeedKeywords: seedKeywords.length,
      clusters: clusters,
      clusterNames: clusterNames
    });
    
  } catch (error) {
    console.error('[THEMES] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Lade bestehende Cluster
app.get('/api/themes/clusters', async (req, res) => {
  try {
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    const data = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
    res.json(data);
  } catch (error) {
    res.status(404).json({ error: 'Keine Cluster gefunden. Bitte erst generieren.' });
  }
});

// Manuell Cluster hinzufügen
app.post('/api/themes/add-cluster', async (req, res) => {
  const { name, description, keywords } = req.body;
  
  console.log(`[CLUSTERS] Füge manuellen Cluster hinzu: ${name}`);
  
  try {
    // Validierung
    if (!name || !name.trim()) {
      throw new Error('Cluster-Name ist erforderlich');
    }
    
    // Keywords sind optional - leere Cluster sind erlaubt
    const validKeywords = (keywords && Array.isArray(keywords)) ? keywords.filter(kw => kw && kw.trim()) : [];
    
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    
    // Lade bestehende Cluster oder erstelle neue Datei
    let clustersData = {};
    let clusters = {};
    
    if (fsSync.existsSync(clustersPath)) {
      clustersData = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
      // Extrahiere Cluster aus verschachtelter Struktur
      clusters = clustersData.clusters || clustersData;
    }
    
    // Prüfe ob Cluster bereits existiert
    if (clusters[name]) {
      throw new Error(`Cluster "${name}" existiert bereits`);
    }
    
    // Füge neuen Cluster hinzu
    clusters[name] = {
      description: description || `Manuell hinzugefügter Themenbereich: ${name}`,
      keywords: validKeywords,
      manual: true, // Markierung für manuell hinzugefügte Cluster
      created: new Date().toISOString()
    };
    
    // Aktualisiere Metadaten falls vorhanden
    if (clustersData.clusters) {
      clustersData.clusters = clusters;
      clustersData.clustersCount = Object.keys(clusters).length;
    } else {
      // Falls alte Struktur, speichere nur Cluster
      clustersData = clusters;
    }
    
    // Speichere mit erhaltener Struktur
    fsSync.writeFileSync(clustersPath, JSON.stringify(clustersData, null, 2));
    
    console.log(`[CLUSTERS] ✓ Cluster "${name}" hinzugefügt mit ${validKeywords.length} Keywords`);
    
    res.json({
      success: true,
      clusterName: name,
      keywordCount: validKeywords.length,
      totalClusters: Object.keys(clusters).length
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler beim Hinzufügen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Cluster reorganisieren (Keywords neu zuordnen)
app.post('/api/themes/reorganize-clusters', async (req, res) => {
  console.log('[CLUSTERS] Starte Reorganisation...');
  
  try {
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    
    if (!fsSync.existsSync(clustersPath)) {
      throw new Error('Keine Cluster gefunden. Bitte erst generieren.');
    }
    
    const clustersData = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
    const clusters = clustersData.clusters || clustersData;
    
    // Sammle alle Keywords aus keywords-database.json (nicht nur aus Clustern!)
    const allKeywords = new Set();
    
    try {
      const keywordsDB = JSON.parse(fsSync.readFileSync(KEYWORDS_DB_FILE, 'utf8'));
      
      // Durchlaufe alle Vorträge und sammle alle Keywords
      Object.values(keywordsDB).forEach(lecture => {
        if (lecture.keywords && Array.isArray(lecture.keywords)) {
          lecture.keywords.forEach(kw => {
            if (kw.term) {
              allKeywords.add(kw.term);
            }
          });
        }
      });
      
      console.log(`[CLUSTERS] Gefunden: ${allKeywords.size} einzigartige Keywords aus keywords-database.json`);
    } catch (error) {
      console.log('[CLUSTERS] Keine keywords-database.json gefunden, verwende nur Cluster-Keywords');
      // Fallback: Sammle Keywords aus Clustern
      Object.values(clusters).forEach(cluster => {
        if (cluster.keywords && Array.isArray(cluster.keywords)) {
          cluster.keywords.forEach(kw => allKeywords.add(kw));
        }
      });
    }
    
    const keywordsList = Array.from(allKeywords);
    console.log(`[CLUSTERS] Reorganisiere ${keywordsList.length} Keywords über ${Object.keys(clusters).length} Cluster...`);
    
    // Erstelle Prompt für Claude
    const prompt = `Du bist ein Experte für thematische Klassifikation von philosophischen und anthroposophischen Begriffen.

BESTEHENDE THEMATISCHE CLUSTER:
${JSON.stringify(clusters, null, 2)}

AUFGABE:
Analysiere ALLE Keywords aus ALLEN Clustern und ordne sie neu zu:
1. Jedes Keyword dem am besten passenden Cluster zuordnen
2. Falls ein Keyword zu keinem bestehenden Cluster passt, einen NEUEN Cluster vorschlagen
3. Cluster können leer werden (Keywords wandern woanders hin)
4. Ziel: Optimale thematische Kohärenz

ANTWORTE im folgenden JSON-Format:
{
  "reorganized": {
    "ClusterName": ["keyword1", "keyword2", ...],
    ...
  },
  "newClusters": {
    "NewClusterName": {
      "description": "Beschreibung",
      "keywords": ["keyword1", ...]
    },
    ...
  },
  "moved": 123,
  "reasoning": "Kurze Erklärung der Hauptänderungen"
}`;

    // Call Claude API
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 16000,
        temperature: 0.3,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Claude API Error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const responseText = data.content[0].text;
    
    // Parse JSON response
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('Keine JSON-Antwort von Claude erhalten');
    }
    
    const result = JSON.parse(jsonMatch[0]);
    
    // Merge reorganisierte Cluster mit neuen Clustern
    const finalClusters = {};
    
    // Bestehende Cluster mit neu zugeordneten Keywords
    Object.entries(result.reorganized).forEach(([name, keywords]) => {
      if (keywords.length > 0) { // Nur nicht-leere Cluster behalten
        const originalCluster = clusters[name];
        finalClusters[name] = {
          description: originalCluster?.description || name,
          keywords: keywords,
          manual: originalCluster?.manual || false
        };
      }
    });
    
    // Neue Cluster hinzufügen
    if (result.newClusters) {
      Object.entries(result.newClusters).forEach(([name, data]) => {
        finalClusters[name] = {
          description: data.description,
          keywords: data.keywords,
          manual: false,
          newFromReorg: true
        };
      });
    }
    
    // Behalte Metadaten
    const finalData = {
      generated: new Date().toISOString(),
      reorganized: true,
      seedKeywordsCount: clustersData.seedKeywordsCount || 0,
      clustersCount: Object.keys(finalClusters).length,
      clusters: finalClusters
    };
    
    // Speichere
    fsSync.writeFileSync(clustersPath, JSON.stringify(finalData, null, 2));
    
    console.log(`[CLUSTERS] ✓ Reorganisation abgeschlossen`);
    console.log(`[CLUSTERS] Keywords verschoben: ${result.moved || 0}`);
    console.log(`[CLUSTERS] Neue Cluster: ${Object.keys(result.newClusters || {}).length}`);
    console.log(`[CLUSTERS] Total Cluster: ${Object.keys(finalClusters).length}`);
    
    res.json({
      success: true,
      keywordsMoved: result.moved || 0,
      newClustersCreated: Object.keys(result.newClusters || {}).length,
      totalClusters: Object.keys(finalClusters).length,
      reasoning: result.reasoning
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler bei Reorganisation:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Keyword umbenennen/zusammenführen
app.post('/api/keywords/move-to-cluster', async (req, res) => {
  const { keyword, targetCluster } = req.body;
  
  console.log(`[KEYWORDS] Move: "${keyword}" -> Cluster "${targetCluster}"`);
  
  try {
    if (!keyword || !keyword.trim()) {
      throw new Error('Keyword erforderlich');
    }
    
    if (!targetCluster || !targetCluster.trim()) {
      throw new Error('Ziel-Cluster erforderlich');
    }
    
    // Lade Thematic Clusters
    const clustersFilePath = path.join(__dirname, 'thematic-clusters.json');
    const clustersData = JSON.parse(fsSync.readFileSync(clustersFilePath, 'utf8'));
    const clusters = clustersData.clusters || clustersData;
    
    if (!clusters[targetCluster]) {
      throw new Error(`Cluster "${targetCluster}" existiert nicht`);
    }
    
    const normalizedKeyword = keyword.trim().toLowerCase();
    let foundInCluster = null;
    let removed = false;
    
    // Suche Keyword in allen Clustern und entferne es
    for (const [clusterName, clusterInfo] of Object.entries(clusters)) {
      const keywords = clusterInfo.keywords || clusterInfo;
      if (!Array.isArray(keywords)) continue;
      
      const index = keywords.findIndex(kw => kw.toLowerCase() === normalizedKeyword);
      if (index !== -1) {
        foundInCluster = clusterName;
        keywords.splice(index, 1);
        removed = true;
        console.log(`[KEYWORDS] Keyword aus Cluster "${clusterName}" entfernt`);
      }
    }
    
    if (!removed) {
      console.log(`[KEYWORDS] Keyword nicht gefunden, füge als neu hinzu`);
    }
    
    // Füge Keyword zum Ziel-Cluster hinzu (wenn nicht schon vorhanden)
    // Stelle sicher, dass das keywords-Array existiert
    if (!clusters[targetCluster].keywords) {
      clusters[targetCluster].keywords = [];
    }
    
    const keywordsArray = clusters[targetCluster].keywords;
    if (!keywordsArray.some(kw => kw.toLowerCase() === normalizedKeyword)) {
      keywordsArray.push(keyword.trim());
      console.log(`[KEYWORDS] Keyword zu Cluster "${targetCluster}" hinzugefügt`);
    } else {
      console.log(`[KEYWORDS] Keyword bereits in Ziel-Cluster vorhanden`);
    }
    
    // Speichere aktualisierte Clusters (mit Original-Struktur)
    if (clustersData.clusters) {
      clustersData.clusters = clusters;
      fsSync.writeFileSync(clustersFilePath, JSON.stringify(clustersData, null, 2));
    } else {
      fsSync.writeFileSync(clustersFilePath, JSON.stringify(clusters, null, 2));
    }
    
    res.json({
      success: true,
      keyword: keyword.trim(),
      fromCluster: foundInCluster || 'neu',
      toCluster: targetCluster,
      message: foundInCluster 
        ? `Keyword von "${foundInCluster}" nach "${targetCluster}" verschoben`
        : `Keyword zu "${targetCluster}" hinzugefügt`
    });
    
  } catch (error) {
    console.error('[KEYWORDS] Fehler beim Verschieben:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/keywords/rename', async (req, res) => {
  const { oldKeyword, newKeyword } = req.body;
  
  console.log(`[KEYWORDS] Rename/Merge: "${oldKeyword}" -> "${newKeyword || 'DELETE'}"`);
  
  try {
    if (!oldKeyword || !oldKeyword.trim()) {
      throw new Error('Altes Keyword erforderlich');
    }
    
    // Lade Keywords-Database
    const keywordsDB = await loadKeywordsDatabase();
    
    let affectedLectures = 0;
    let totalReplacements = 0;
    let duplicatesRemoved = 0;
    
    const oldKwLower = oldKeyword.toLowerCase().trim();
    const newKwLower = newKeyword ? newKeyword.toLowerCase().trim() : null;
    
    // Iteriere durch alle Vorträge
    for (const [lectureId, data] of Object.entries(keywordsDB)) {
      if (!data.keywords || !Array.isArray(data.keywords)) continue;
      
      let lectureModified = false;
      const updatedKeywords = [];
      
      // Prüfe ob Vortrag bereits das neue Keyword hat (für Duplikat-Erkennung)
      const hasNewKeyword = newKwLower && data.keywords.some(kw => 
        kw.term.toLowerCase() === newKwLower
      );
      
      data.keywords.forEach(kw => {
        const kwLower = kw.term.toLowerCase();
        
        if (kwLower === oldKwLower) {
          // Altes Keyword gefunden
          totalReplacements++;
          lectureModified = true;
          
          if (newKeyword && newKeyword.trim()) {
            // Zusammenführen/Umbenennen
            if (hasNewKeyword) {
              // Duplikat: Vortrag hat bereits das neue Keyword
              // -> altes Keyword einfach entfernen (nicht umbenennen)
              duplicatesRemoved++;
              console.log(`[KEYWORDS] Duplikat entfernt in ${lectureId}: "${oldKeyword}" (existiert bereits als "${newKeyword}")`);
            } else {
              // Kein Duplikat: Umbenennen
              updatedKeywords.push({
                ...kw,
                term: newKeyword.trim()
              });
            }
          }
          // Wenn newKeyword leer: löschen (nicht hinzufügen)
        } else {
          // Anderes Keyword: unverändert beibehalten
          updatedKeywords.push(kw);
        }
      });
      
      if (lectureModified) {
        keywordsDB[lectureId].keywords = updatedKeywords;
        affectedLectures++;
      }
    }
    
    // Speichere aktualisierte Database mit Locking-Mechanismus
    await saveCompleteKeywordsDatabase(keywordsDB);
    
    console.log(`[KEYWORDS] ✓ ${affectedLectures} Vorträge aktualisiert, ${totalReplacements} Ersetzungen, ${duplicatesRemoved} Duplikate entfernt`);
    
    res.json({
      success: true,
      affectedLectures: affectedLectures,
      totalReplacements: totalReplacements,
      duplicatesRemoved: duplicatesRemoved,
      action: newKeyword ? (duplicatesRemoved > 0 ? 'merged' : 'renamed') : 'deleted'
    });
    
  } catch (error) {
    console.error('[KEYWORDS] Fehler beim Umbenennen/Zusammenführen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Cluster umbenennen
app.post('/api/themes/rename-cluster', async (req, res) => {
  const { oldName, newName } = req.body;
  
  console.log(`[CLUSTERS] Rename: "${oldName}" -> "${newName}"`);
  
  try {
    if (!oldName || !newName) {
      throw new Error('Alter und neuer Name erforderlich');
    }
    
    if (oldName === newName) {
      throw new Error('Namen sind identisch');
    }
    
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    
    if (!fsSync.existsSync(clustersPath)) {
      throw new Error('Keine Cluster gefunden');
    }
    
    const clustersData = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
    const clusters = clustersData.clusters || clustersData;
    
    if (!clusters[oldName]) {
      throw new Error(`Cluster "${oldName}" nicht gefunden`);
    }
    
    if (clusters[newName]) {
      throw new Error(`Cluster "${newName}" existiert bereits. Verwenden Sie Zusammenführen.`);
    }
    
    // Umbenennen
    clusters[newName] = { ...clusters[oldName] };
    delete clusters[oldName];
    
    // Speichern
    if (clustersData.clusters) {
      clustersData.clusters = clusters;
    } else {
      Object.assign(clustersData, clusters);
    }
    
    fsSync.writeFileSync(clustersPath, JSON.stringify(clustersData, null, 2));
    
    console.log(`[CLUSTERS] ✓ Cluster umbenannt`);
    
    res.json({
      success: true,
      totalClusters: Object.keys(clusters).length
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler beim Umbenennen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Cluster zusammenführen
app.post('/api/themes/merge-clusters', async (req, res) => {
  const { sourceCluster, targetCluster } = req.body;
  
  console.log(`[CLUSTERS] Merge: "${sourceCluster}" -> "${targetCluster}"`);
  
  try {
    if (!sourceCluster || !targetCluster) {
      throw new Error('Quell- und Ziel-Cluster erforderlich');
    }
    
    if (sourceCluster === targetCluster) {
      throw new Error('Cluster müssen unterschiedlich sein');
    }
    
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    
    if (!fsSync.existsSync(clustersPath)) {
      throw new Error('Keine Cluster gefunden');
    }
    
    const clustersData = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
    const clusters = clustersData.clusters || clustersData;
    
    if (!clusters[sourceCluster]) {
      throw new Error(`Quell-Cluster "${sourceCluster}" nicht gefunden`);
    }
    
    if (!clusters[targetCluster]) {
      throw new Error(`Ziel-Cluster "${targetCluster}" nicht gefunden`);
    }
    
    // Merge Keywords
    const sourceKeywords = clusters[sourceCluster].keywords || [];
    const targetKeywords = clusters[targetCluster].keywords || [];
    
    // Kombiniere und dedupliziere
    const mergedKeywords = [...new Set([...targetKeywords, ...sourceKeywords])];
    
    clusters[targetCluster].keywords = mergedKeywords;
    
    // Lösche Quell-Cluster
    delete clusters[sourceCluster];
    
    // Speichern
    if (clustersData.clusters) {
      clustersData.clusters = clusters;
      clustersData.clustersCount = Object.keys(clusters).length;
    } else {
      Object.assign(clustersData, clusters);
    }
    
    fsSync.writeFileSync(clustersPath, JSON.stringify(clustersData, null, 2));
    
    console.log(`[CLUSTERS] ✓ ${sourceKeywords.length} Keywords von "${sourceCluster}" nach "${targetCluster}" verschoben`);
    
    res.json({
      success: true,
      keywordsMerged: sourceKeywords.length,
      totalClusters: Object.keys(clusters).length
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler beim Zusammenführen:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================

// HAUPTFUNKTION: Extrahiere Keywords aus Überschriften (regel-basiert, ohne KI)
function extractKeywordsFromHeadings(headings) {
  console.log('[KEYWORDS-GEN] Verwende regel-basierte Extraktion');
  
  return headings.map(h => ({
    term: extractKeywordFromHeading(h.text),
    index: h.index,
    heading: h.text,
    level: h.level || 'h3' // Übernehme Level (h3 oder h4)
  }));
}

// HILFSFUNKTION: Extrahiere prägnantes Keyword aus einer Überschrift
function extractKeywordFromHeading(text) {
  // Liste der deutschen Füllwörter
  const stopWords = [
    'der', 'die', 'das', 'den', 'dem', 'des',
    'ein', 'eine', 'eines', 'einem', 'einen', 'einer',
    'von', 'zu', 'mit', 'für', 'über', 'aus', 'in', 'an', 'bei', 'auf', 'durch', 'als',
    'im', 'am', 'vom', 'zum', 'zur', 'ins', 'ans',
    'ihre', 'ihr', 'sein', 'seine', 'ihren', 'seiner', 'seinen',
    'werden', 'wurde', 'wurden', 'wird',
    'haben', 'hat', 'hatte', 'hatten',
    'sein', 'ist', 'war', 'sind', 'waren'
  ];
  
  // Tokenize
  let words = text.split(/\s+/);
  
  // Filtere Füllwörter am Anfang und Ende
  while (words.length > 0 && stopWords.includes(words[0].toLowerCase())) {
    words.shift();
  }
  while (words.length > 0 && stopWords.includes(words[words.length - 1].toLowerCase())) {
    words.pop();
  }
  
  // Baue Keyword auf: Erkenne Adjektiv + Substantiv Muster
  let result = [];
  
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    const next = words[i + 1];
    
    // Überspringe Füllwörter
    if (stopWords.includes(word.toLowerCase())) {
      continue;
    }
    
    // Substantiv gefunden (großgeschrieben)
    if (word[0] === word[0].toUpperCase()) {
      // Prüfe ob nächstes Wort auch Substantiv ist und durch "und" verbunden
      if (next && next.toLowerCase() === 'und' && words[i + 2] && words[i + 2][0] === words[i + 2][0].toUpperCase()) {
        // "Karma und Reinkarnation"
        result.push(word);
        result.push('und');
        result.push(words[i + 2]);
        i += 2; // Überspringe die nächsten beiden
      } else {
        result.push(word);
      }
    }
    // Kleingeschrieben = potentielles Adjektiv
    else if (word[0] === word[0].toLowerCase() && next && next[0] === next[0].toUpperCase()) {
      // Adjektiv vor Substantiv: "deutsches Reich"
      result.push(word);
      result.push(next);
      i++; // Überspringe das nächste Wort
    }
  }
  
  // Fallback: wenn nichts gefunden, nimm ersten 3 Wörter
  if (result.length === 0) {
    result = words.slice(0, 3);
  }
  
  // Begrenze auf maximal 5 Wörter (für Fälle mit "und")
  const keyword = result.slice(0, 5).join(' ').trim();
  
  return keyword || text.split(' ').slice(0, 3).join(' '); // Ultimate Fallback
}

// API: Keywords für einzelnen oder mehrere Vorträge generieren
app.post('/api/generate-keywords', async (req, res) => {
  try {
    const { lectureId, batch, batchByVolumes, volumes = [], startIndex = 0, batchSize = 50, gaFilter = [] } = req.body;
    
    console.log(`[KEYWORDS-API] Generierungsanfrage: ${batchByVolumes ? `GA-Bände: ${volumes.join(', ')}` : batch ? `Batch (Start: ${startIndex}, Size: ${batchSize})` : lectureId}`);
    
    // Lade Summary-Database für Zugriff auf Überschriften
    const summaryDB = await loadSummaryDatabase();
    const keywordsDB = await loadKeywordsDatabase();
    
    const results = [];
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    if (batchByVolumes) {
      // GA-BAND-BASIERTE BATCH-VERARBEITUNG (Option A: Sequenziell pro Band, parallel pro Vortrag)
      
      if (!volumes || volumes.length === 0) {
        return res.status(400).json({ error: 'volumes Array erforderlich (z.B. ["GA110", "GA066"])' });
      }
      
      console.log(`[GA-BATCH] Starte GA-Band-basierte Verarbeitung: ${volumes.length} Bände`);
      
      const volumeResults = [];
      let totalProcessed = 0;
      let totalSkipped = 0;
      let totalErrors = 0;
      
      // Verarbeite jeden GA-Band sequenziell
      for (const volume of volumes) {
        console.log(`\n[GA-BATCH] ========================================`);
        console.log(`[GA-BATCH] Starte Verarbeitung: ${volume}`);
        console.log(`[GA-BATCH] ========================================\n`);
        
        // Filtere Vorträge für diesen GA-Band
        const volumeLectures = Object.keys(summaryDB).filter(lid => 
          lid.startsWith(volume + '/')
        );
        
        if (volumeLectures.length === 0) {
          console.log(`[GA-BATCH] ⚠ Keine Vorträge gefunden für ${volume}`);
          volumeResults.push({
            volume: volume,
            processed: 0,
            skipped: 0,
            errors: 0,
            total: 0,
            status: 'no_lectures'
          });
          continue;
        }
        
        console.log(`[GA-BATCH] ${volume}: ${volumeLectures.length} Vorträge gefunden`);
        
        let volumeProcessed = 0;
        let volumeSkipped = 0;
        let volumeErrors = 0;
        
        // Definiere Verarbeitungsfunktion für einen Vortrag
        const processLecture = async (lid, index) => {
          // Überspringe, wenn bereits Keywords existieren
          if (keywordsDB[lid]) {
            console.log(`[GA-BATCH] ${volume}: Überspringe ${lid} (bereits vorhanden)`);
            return { status: 'skipped', lectureId: lid, reason: 'bereits vorhanden' };
          }
          
          const summaryData = summaryDB[lid];
          if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
            console.log(`[GA-BATCH] ${volume}: Überspringe ${lid} (keine Überschriften)`);
            return { status: 'skipped', lectureId: lid, reason: 'keine Überschriften' };
          }
          
          // Extrahiere Datum und Jahr aus fullLectures
          const lecture = fullLectures[lid];
          const date = lecture?.date || lecture?.dateString || '';
          const year = date ? parseInt(date.substring(0, 4)) : null;
          
          // Generiere Keywords
          const keywords = await generateKeywordsFromHeadings(lecture, summaryData.headings);
          
          // Speichere in Keywords-DB
          await saveKeywordsToDatabase(lid, {
            lectureId: lid,
            date: date,
            year: year,
            keywords: keywords,
            theme: null,
            generated: new Date().toISOString(),
            model: 'claude-sonnet-4',
            source: 'headings',
            gaVolume: volume
          });
          
          console.log(`[GA-BATCH] ${volume}: ✓ ${lid}: ${keywords.length} Keywords generiert`);
          
          return { 
            status: 'processed', 
            lectureId: lid, 
            keywords: keywords.length, 
            success: true 
          };
        };
        
        // Verarbeite alle Vorträge dieses Bandes parallel (max 5 gleichzeitig)
        console.log(`[GA-BATCH] ${volume}: Starte parallele Verarbeitung (Concurrency: 5)`);
        const startTime = Date.now();
        
        const batchResults = await processBatchWithConcurrency(
          volumeLectures,
          processLecture,
          5,  // Concurrency Limit
          200 // Delay zwischen Starts in ms
        );
        
        // Sammle Ergebnisse für diesen Band
        for (const result of batchResults) {
          if (result.success) {
            const data = result.result;
            
            if (data.status === 'processed') {
              results.push({ lectureId: data.lectureId, keywords: data.keywords, success: true, volume: volume });
              volumeProcessed++;
            } else if (data.status === 'skipped') {
              volumeSkipped++;
            }
          } else {
            console.error(`[GA-BATCH] ${volume}: Fehler bei ${result.item}:`, result.error);
            results.push({ lectureId: result.item, error: result.error, success: false, volume: volume });
            volumeErrors++;
          }
        }
        
        const duration = Math.round((Date.now() - startTime) / 1000);
        
        console.log(`\n[GA-BATCH] ${volume}: ABGESCHLOSSEN`);
        console.log(`[GA-BATCH] ${volume}: ✓ ${volumeProcessed} verarbeitet, ⊘ ${volumeSkipped} übersprungen, ✗ ${volumeErrors} Fehler`);
        console.log(`[GA-BATCH] ${volume}: Dauer: ${duration}s\n`);
        
        volumeResults.push({
          volume: volume,
          processed: volumeProcessed,
          skipped: volumeSkipped,
          errors: volumeErrors,
          total: volumeLectures.length,
          duration: duration,
          status: 'completed'
        });
        
        totalProcessed += volumeProcessed;
        totalSkipped += volumeSkipped;
        totalErrors += volumeErrors;
      }
      
      console.log(`\n[GA-BATCH] ========================================`);
      console.log(`[GA-BATCH] ALLE BÄNDE ABGESCHLOSSEN`);
      console.log(`[GA-BATCH] Total: ${totalProcessed} verarbeitet, ${totalSkipped} übersprungen, ${totalErrors} Fehler`);
      console.log(`[GA-BATCH] ========================================\n`);
      
      return res.json({
        success: true,
        batchByVolumes: true,
        volumes: volumeResults,
        processed: totalProcessed,
        skipped: totalSkipped,
        errors: totalErrors,
        results: results
      });
      
    } else if (batch) {
      // ALTE BATCH-VERARBEITUNG (mit startIndex/batchSize)
      let allLectureIds = Object.keys(summaryDB);
      
      // Filter nach GA-Bänden wenn angegeben
      if (gaFilter && gaFilter.length > 0) {
        console.log(`[KEYWORDS-BATCH] Filter nach GAs: ${gaFilter.join(', ')}`);
        allLectureIds = allLectureIds.filter(lid => {
          const gaNumber = lid.split('/')[0]; // z.B. "GA110"
          return gaFilter.includes(gaNumber);
        });
        console.log(`[KEYWORDS-BATCH] Nach GA-Filter: ${allLectureIds.length} Vorträge`);
      }
      
      const total = allLectureIds.length;
      const toProcess = allLectureIds.slice(startIndex, startIndex + batchSize);
      
      console.log(`[KEYWORDS-BATCH] Parallele Verarbeitung von ${toProcess.length}/${total} Vorträgen (${startIndex}-${startIndex + toProcess.length}, Concurrency: 5)`);
      
      // Definiere Verarbeitungsfunktion für einen Vortrag
      const processLecture = async (lid, index) => {
        // Überspringe, wenn bereits Keywords existieren
        if (keywordsDB[lid]) {
          console.log(`[KEYWORDS-BATCH] Überspringe ${lid} (bereits vorhanden)`);
          return { status: 'skipped', lectureId: lid, reason: 'bereits vorhanden' };
        }
        
        const summaryData = summaryDB[lid];
        if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
          console.log(`[KEYWORDS-BATCH] Überspringe ${lid} (keine Überschriften)`);
          return { status: 'skipped', lectureId: lid, reason: 'keine Überschriften' };
        }
        
        // Extrahiere Datum und Jahr aus fullLectures
        const lecture = fullLectures[lid];
        const date = lecture?.date || lecture?.dateString || '';
        const year = date ? parseInt(date.substring(0, 4)) : null;
        
        // Generiere Keywords
        const keywords = await generateKeywordsFromHeadings(lecture, summaryData.headings);
        
        // Speichere in Keywords-DB
        await saveKeywordsToDatabase(lid, {
          lectureId: lid,
          date: date,
          year: year,
          keywords: keywords,
          theme: null,
          generated: new Date().toISOString(),
          model: 'claude-sonnet-4',
          source: 'headings'
        });
        
        console.log(`[KEYWORDS-BATCH] ✓ ${lid}: ${keywords.length} Keywords generiert`);
        
        return { 
          status: 'processed', 
          lectureId: lid, 
          keywords: keywords.length, 
          success: true 
        };
      };
      
      // Verarbeite alle Vorträge parallel (max 5 gleichzeitig)
      const batchResults = await processBatchWithConcurrency(
        toProcess,
        processLecture,
        5,  // Concurrency Limit
        200 // Delay zwischen Starts in ms
      );
      
      // Sammle Ergebnisse
      for (const result of batchResults) {
        if (result.success) {
          const data = result.result;
          
          if (data.status === 'processed') {
            results.push({ lectureId: data.lectureId, keywords: data.keywords, success: true });
            processed++;
          } else if (data.status === 'skipped') {
            skipped++;
          }
        } else {
          console.error(`[KEYWORDS-BATCH] Fehler bei ${result.item}:`, result.error);
          results.push({ lectureId: result.item, error: result.error, success: false });
          errors++;
        }
      }
      
      res.json({
        success: true,
        batch: true,
        processed: processed,
        skipped: skipped,
        errors: errors,
        total: total,
        progress: {
          current: startIndex + toProcess.length,
          total: total,
          percentage: Math.round(((startIndex + toProcess.length) / total) * 100)
        },
        results: results
      });
      
    } else {
      // Einzelverarbeitung
      if (!lectureId) {
        return res.status(400).json({ error: 'lectureId ist erforderlich' });
      }
      
      const summaryData = summaryDB[lectureId];
      if (!summaryData) {
        return res.status(404).json({ error: `Keine Summary für ${lectureId} gefunden` });
      }
      
      if (!summaryData.headings || summaryData.headings.length === 0) {
        return res.status(400).json({ error: `Keine Überschriften für ${lectureId} vorhanden` });
      }
      
      // Extrahiere Datum und Jahr
      const lecture = fullLectures[lectureId];
      const date = lecture?.date || lecture?.dateString || '';
      const year = date ? parseInt(date.substring(0, 4)) : null;
      
      // Generiere Keywords
      const keywords = await generateKeywordsFromHeadings(lecture, summaryData.headings);
      
      // Speichere in Keywords-DB
      await saveKeywordsToDatabase(lectureId, {
        lectureId: lectureId,
        date: date,
        year: year,
        keywords: keywords,
        theme: null,
        generated: new Date().toISOString(),
        model: 'claude-sonnet-4',
        source: 'headings'
      });
      
      res.json({
        success: true,
        lectureId: lectureId,
        keywords: keywords,
        keywordCount: keywords.length
      });
    }
    
  } catch (error) {
    console.error('[KEYWORDS-API] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Keywords-Datenbank abrufen
app.get('/api/keywords-database', async (req, res) => {
  try {
    const keywordsDB = await loadKeywordsDatabase();
    res.json(keywordsDB);
  } catch (error) {
    console.error('[KEYWORDS-API] Fehler beim Laden:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Keywords-Statistiken
app.get('/api/keywords-stats', async (req, res) => {
  try {
    const keywordsDB = await loadKeywordsDatabase();
    const summaryDB = await loadSummaryDatabase();
    
    const stats = {
      totalLectures: Object.keys(summaryDB).length,
      keywordsGenerated: Object.keys(keywordsDB).length,
      percentage: Math.round((Object.keys(keywordsDB).length / Object.keys(summaryDB).length) * 100),
      withTheme: Object.values(keywordsDB).filter(k => k.theme).length,
      withoutTheme: Object.values(keywordsDB).filter(k => !k.theme).length
    };
    
    res.json(stats);
  } catch (error) {
    console.error('[KEYWORDS-API] Fehler bei Statistiken:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// THEMES-DATENBANK
// ============================================================================

// Lade Themes-Datenbank
async function loadThemesDatabase() {
  try {
    const data = await fs.readFile(THEMES_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('[THEMES-DB] Datenbank nicht gefunden, erstelle neue...');
    return {};
  }
}

// Speichere Themes-Datenbank
async function saveThemesDatabase(themesDB) {
  try {
    await fs.writeFile(THEMES_DB_FILE, JSON.stringify(themesDB, null, 2), 'utf8');
    console.log('[THEMES-DB] Datenbank gespeichert');
    return true;
  } catch (error) {
    console.error('[THEMES-DB] Fehler beim Speichern:', error);
    return false;
  }
}

// Funktion: Themen aus allen Keywords mit Claude generieren
async function generateThemesFromKeywords(targetThemeCount = 30) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('[THEMES-GEN] Kein Claude API Key - verwende Fallback');
    return generateFallbackThemes();
  }
  
  // Lade alle Keywords
  const keywordsDB = await loadKeywordsDatabase();
  const allKeywords = [];
  const keywordFrequency = {};
  
  // Sammle alle Keywords mit Häufigkeit
  Object.values(keywordsDB).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => {
        const term = kw.term.toLowerCase().trim();
        allKeywords.push(term);
        keywordFrequency[term] = (keywordFrequency[term] || 0) + 1;
      });
    }
  });
  
  // Sortiere nach Häufigkeit und nimm die Top 300 (reduziert wegen Token-Limits)
  const topKeywords = Object.entries(keywordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 300)
    .map(([term, freq]) => `${term} (${freq}x)`)
    .join(', ');
  
  console.log(`[THEMES-GEN] Analysiere ${Object.keys(keywordFrequency).length} unique Keywords aus ${Object.keys(keywordsDB).length} Vorträgen (Top 300 für Themen-Generierung)`);
  
  const prompt = `Analysiere die folgenden Schlagwörter aus Rudolf Steiners Vortragswerk und gruppiere sie in genau ${targetThemeCount} übergeordnete Themenbereiche.

HÄUFIGSTE SCHLAGWÖRTER (Top 300):
${topKeywords}

ANFORDERUNGEN:
- Genau ${targetThemeCount} Themenbereiche
- Themen sollten die Hauptgebiete der Anthroposophie abdecken
- Jedes Thema mit deutschen Namen (z.B. "Erkenntnistheorie", "Christologie", "Soziale Dreigliederung")
- Für jedes Thema: Liste der zugehörigen Hauptkeywords (10-20 wichtigste)
- Themen sollten ausgewogen sein (nicht zu breit, nicht zu eng)
- WICHTIG: Keywords mit korrekter deutscher Großschreibung (Substantive groß, z.B. "Karma", "Reinkarnation", "Wiederverkörperung")
- Entferne Redundanzen: statt "karma", "kosmisches karma" nur "Karma" (kürzere Form wird automatisch konsolidiert)
- Entferne Redundanzen: statt "reinkarnation", "reinkarnationslehre" nur "Reinkarnation", "Reinkarnationslehre" (beides behalten wenn unterschiedliche Bedeutung)
- Entferne Redundanzen: statt "tod", "tod und sterben" nur "Tod und Sterben"

BEISPIELE FÜR THEMEN:
- Erkenntnistheorie
- Christologie und Evangelien
- Karma und Reinkarnation
- Soziale Dreigliederung
- Pädagogik und Erziehung
- Anthroposophische Medizin
- Kosmologie und Planetensphären
- Mysterien und Einweihung
- Deutsche Mystik
- Goetheanismus
[... weitere]

ANTWORT-FORMAT (JSON):
{
  "Erkenntnistheorie": {
    "keywords": ["Goetheanismus", "Phänomenologie", "Wissenschaft", "Naturerkenntnis", ...],
    "description": "Kurze Beschreibung des Themenbereichs"
  },
  ...
}

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.`;

  try {
    console.log('[THEMES-GEN] Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8192,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[THEMES-GEN] Claude API Error:', response.status, errorText);
      throw new Error(`Claude API Fehler: ${response.status} - ${errorText.substring(0, 200)}`);
    }

    const result = await response.json();
    let responseText = result.content[0].text.trim();
    
    // Entferne Markdown Code-Blöcke falls vorhanden
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    let themes = JSON.parse(responseText);
    
    console.log('[THEMES-GEN] ✓ Themen erfolgreich generiert:', Object.keys(themes).length);
    
    // Normalisiere alle Keywords in jedem Thema
    for (const [themeName, themeData] of Object.entries(themes)) {
      if (themeData.keywords && Array.isArray(themeData.keywords)) {
        // Konvertiere String-Array zu Objekt-Array für Normalisierung
        const keywordObjects = themeData.keywords.map(kw => 
          typeof kw === 'string' ? { term: kw } : kw
        );
        const normalized = normalizeKeywords(keywordObjects);
        themes[themeName].keywords = normalized.map(kw => kw.term);
        console.log(`[THEMES-GEN] ${themeName}: ${themeData.keywords.length} → ${themes[themeName].keywords.length} Keywords`);
      }
    }
    
    return themes;

  } catch (error) {
    console.error('[THEMES-GEN] Fehler bei Claude API:', error);
    return generateFallbackThemes();
  }
}

// Fallback: Einfache Themengruppierung (ohne KI)
function generateFallbackThemes() {
  console.log('[THEMES-GEN] Verwende Fallback-Methode');
  
  return {
    "Erkenntnistheorie": {
      keywords: ["Goetheanismus", "Wissenschaft", "Naturerkenntnis"],
      description: "Erkenntnistheoretische Grundlagen"
    },
    "Christologie": {
      keywords: ["Christus", "Evangelien", "Mysterium von Golgatha"],
      description: "Christologische Themen"
    },
    "Karma und Reinkarnation": {
      keywords: ["Karma", "Reinkarnation", "Schicksal"],
      description: "Wiederverkörperung und Schicksalsgesetze"
    }
  };
}

// API: Themen generieren
app.post('/api/generate-themes', async (req, res) => {
  try {
    const { targetThemeCount = 30 } = req.body;
    
    console.log(`[THEMES-API] Generiere ${targetThemeCount} Themen...`);
    
    // Generiere Themen
    const themes = await generateThemesFromKeywords(targetThemeCount);
    
    // Speichere in Themes-DB
    await saveThemesDatabase(themes);
    
    // Ordne jetzt allen Keywords ihre Themen zu
    const keywordsDB = await loadKeywordsDatabase();
    let assignedCount = 0;
    
    for (const [lectureId, lectureData] of Object.entries(keywordsDB)) {
      if (lectureData.keywords && Array.isArray(lectureData.keywords)) {
        // Finde passendes Thema für die Keywords dieses Vortrags
        let bestTheme = null;
        let bestScore = 0;
        
        for (const [themeName, themeData] of Object.entries(themes)) {
          const themeKeywords = themeData.keywords.map(k => k.toLowerCase());
          let score = 0;
          
          lectureData.keywords.forEach(kw => {
            const term = kw.term.toLowerCase();
            if (themeKeywords.some(tk => tk.includes(term) || term.includes(tk))) {
              score++;
            }
          });
          
          if (score > bestScore) {
            bestScore = score;
            bestTheme = themeName;
          }
        }
        
        // Aktualisiere Lecture mit Thema
        if (bestTheme) {
          await saveKeywordsToDatabase(lectureId, {
            ...lectureData,
            theme: bestTheme
          });
          assignedCount++;
        }
      }
    }
    
    console.log(`[THEMES-API] ✓ ${Object.keys(themes).length} Themen generiert, ${assignedCount} Vorträgen zugeordnet`);
    
    res.json({
      success: true,
      themes: themes,
      themeCount: Object.keys(themes).length,
      assignedLectures: assignedCount
    });
    
  } catch (error) {
    console.error('[THEMES-API] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Themes-Datenbank abrufen (nutzt neue thematic-clusters.json)
app.get('/api/themes-database', async (req, res) => {
  try {
    // Versuche zuerst neue thematic-clusters.json zu laden
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    if (fsSync.existsSync(clustersPath)) {
      const data = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
      // Extrahiere nur die Cluster selbst (nicht die Metadaten)
      const clusters = data.clusters || data;
      console.log('[THEMES-API] Liefere thematic-clusters.json');
      res.json(clusters);
      return;
    }
    
    // Fallback: alte themes-database.json
    const themesDB = await loadThemesDatabase();
    console.log('[THEMES-API] Liefere themes-database.json (Fallback)');
    res.json(themesDB);
  } catch (error) {
    console.error('[THEMES-API] Fehler beim Laden:', error);
    res.status(500).json({ error: error.message });
  }
});

// === KEYWORD CONSOLIDATION ===

async function generateConsolidationPreview(factor) {
  const keywordsDB = await loadKeywordsDatabase();
  
  // Sammle alle Keywords mit Häufigkeit
  const keywordFrequency = {};
  Object.values(keywordsDB).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => {
        const term = kw.term.trim();
        keywordFrequency[term] = (keywordFrequency[term] || 0) + 1;
      });
    }
  });
  
  const uniqueBefore = Object.keys(keywordFrequency).length;
  console.log(`[CONSOLIDATION] ${uniqueBefore} unique Keywords vor Konsolidierung`);
  
  // Erstelle Konsolidierungs-Mapping
  const consolidationMap = await buildConsolidationMap(Object.keys(keywordFrequency), factor);
  
  // Zähle konsolidierte Keywords
  const uniqueAfter = new Set(Object.values(consolidationMap)).size;
  const reduction = ((uniqueBefore - uniqueAfter) / uniqueBefore * 100);
  
  // Erstelle Beispiele
  const examples = [];
  const groupedBy = {};
  
  Object.entries(consolidationMap).forEach(([source, target]) => {
    if (source !== target) {
      if (!groupedBy[target]) groupedBy[target] = [];
      groupedBy[target].push(source);
    }
  });
  
  Object.entries(groupedBy).forEach(([target, sources]) => {
    examples.push({ target, sources });
  });
  
  // Sortiere nach Anzahl der konsolidierten Keywords
  examples.sort((a, b) => b.sources.length - a.sources.length);
  
  return {
    uniqueBefore,
    uniqueAfter,
    reduction,
    consolidationCount: examples.length,
    examples: examples.slice(0, 50) // Top 50 für Vorschau
  };
}

async function buildConsolidationMap(keywords, factor) {
  const consolidationMap = {};
  
  // Sortiere Keywords nach Länge (kürzere zuerst = Ziel-Keywords)
  const sortedKeywords = [...keywords].sort((a, b) => a.length - b.length);
  
  console.log(`[CONSOLIDATION] Verarbeite ${sortedKeywords.length} Keywords mit Faktor ${factor}...`);
  const startTime = Date.now();
  
  // OPTIMIERT: Verwende nur Substring-Matching für Geschwindigkeit
  // Bei factor < 0.6: Nur exakte Substrings
  // Bei factor >= 0.6: Auch Levenshtein für kurze Keywords
  
  const targetMap = {}; // lowercase -> original keyword
  
  for (let i = 0; i < sortedKeywords.length; i++) {
    const keyword = sortedKeywords[i];
    const keywordLower = keyword.toLowerCase();
    let targetKeyword = keyword;
    let foundMatch = false;
    
    // Schnelle Substring-Suche in bereits verarbeiteten Keywords
    for (const [existingLower, existingOriginal] of Object.entries(targetMap)) {
      // Substring-Check (schnell!)
      if (keywordLower.includes(existingLower) || existingLower.includes(keywordLower)) {
        const longer = Math.max(keywordLower.length, existingLower.length);
        const shorter = Math.min(keywordLower.length, existingLower.length);
        const similarity = shorter / longer;
        
        if (similarity >= factor) {
          targetKeyword = existingOriginal;
          foundMatch = true;
          break;
        }
      }
      
      // Bei höherem Factor: Auch Levenshtein für kurze Keywords (< 15 Zeichen)
      if (factor >= 0.6 && !foundMatch && keywordLower.length < 15 && existingLower.length < 15) {
        const similarity = calculateSimilarity(keywordLower, existingLower, factor);
        if (similarity >= factor) {
          targetKeyword = existingOriginal;
          foundMatch = true;
          break;
        }
      }
    }
    
    // Speichere als neues Ziel-Keyword wenn kein Match
    if (!foundMatch) {
      targetMap[keywordLower] = keyword;
    }
    
    consolidationMap[keyword] = targetKeyword;
    
    // Progress-Logging alle 2000 Keywords
    if ((i + 1) % 2000 === 0) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const percent = ((i + 1) / sortedKeywords.length * 100).toFixed(1);
      console.log(`[CONSOLIDATION] ${i + 1}/${sortedKeywords.length} (${percent}%) - ${elapsed}s`);
    }
  }
  
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`[CONSOLIDATION] Fertig in ${totalTime}s. ${Object.keys(targetMap).length} Ziel-Keywords`);
  
  return consolidationMap;
}

function calculateSimilarity(str1, str2, factor) {
  // Exakte Übereinstimmung
  if (str1 === str2) return 1.0;
  
  // Kapitalisierung ignorieren
  const s1 = str1.toLowerCase();
  const s2 = str2.toLowerCase();
  
  if (s1 === s2) return 1.0;
  
  // 1. Substring-Matching (wichtigste Regel)
  if (s1.includes(s2) || s2.includes(s1)) {
    const longer = Math.max(s1.length, s2.length);
    const shorter = Math.min(s1.length, s2.length);
    return shorter / longer; // z.B. "karma" in "karmagesetz" = 5/11 = 0.45
  }
  
  // 2. Levenshtein-Distanz für ähnliche Schreibweisen
  const maxLen = Math.max(s1.length, s2.length);
  const distance = levenshtein(s1, s2);
  const levSimilarity = 1 - (distance / maxLen);
  
  // 3. Wortstamm-basiert (einfach: gemeinsame Anfangs-Zeichen)
  let commonPrefix = 0;
  const minLen = Math.min(s1.length, s2.length);
  for (let i = 0; i < minLen; i++) {
    if (s1[i] === s2[i]) commonPrefix++;
    else break;
  }
  const prefixSimilarity = commonPrefix / maxLen;
  
  // Kombiniere die Metriken
  return Math.max(levSimilarity, prefixSimilarity);
}

async function executeConsolidation(factor) {
  const keywordsDB = await loadKeywordsDatabase();
  
  // Erstelle Backup
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupFile = `keywords-database-backup-${timestamp}.json`;
  await fs.writeFile(backupFile, JSON.stringify(keywordsDB, null, 2));
  console.log(`[CONSOLIDATION] Backup erstellt: ${backupFile}`);
  
  // Sammle alle Keywords
  const allKeywords = new Set();
  Object.values(keywordsDB).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => allKeywords.add(kw.term.trim()));
    }
  });
  
  // Erstelle Konsolidierungs-Mapping
  const consolidationMap = await buildConsolidationMap(Array.from(allKeywords), factor);
  
  // Wende Konsolidierung an
  let consolidatedCount = 0;
  Object.values(keywordsDB).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => {
        const original = kw.term.trim();
        const consolidated = consolidationMap[original];
        
        if (consolidated && consolidated !== original) {
          kw.term = consolidated;
          consolidatedCount++;
        }
      });
    }
  });
  
  // Speichere konsolidierte Datenbank als SEPARATE Datei
  const consolidatedFile = `keywords-database-consolidated-${timestamp}.json`;
  await fs.writeFile(consolidatedFile, JSON.stringify(keywordsDB, null, 2));
  console.log(`[CONSOLIDATION] ${consolidatedCount} Keywords konsolidiert → ${consolidatedFile}`);
  
  return {
    backupFile,
    consolidatedFile,
    consolidatedCount,
    timestamp
  };
}

async function activateConsolidatedDatabase(consolidatedFile) {
  // BACKUP erstellen vor dem Aktivieren
  await createKeywordsBackup();
  
  // Sichere aktuelle Datenbank
  const currentDB = await fs.readFile(KEYWORDS_DB_FILE, 'utf-8');
  const preConsolidationFile = 'keywords-database-pre-consolidation.json';
  await fs.writeFile(preConsolidationFile, currentDB);
  console.log(`[CONSOLIDATION] Aktuelle DB gesichert: ${preConsolidationFile}`);
  
  // Aktiviere konsolidierte Datenbank
  const consolidatedDB = await fs.readFile(consolidatedFile, 'utf-8');
  
  // Validiere dass konsolidierte DB nicht leer ist
  const parsedDB = JSON.parse(consolidatedDB);
  if (Object.keys(parsedDB).length === 0) {
    throw new Error('Konsolidierte Datenbank ist leer - Aktivierung abgebrochen');
  }
  
  await fs.writeFile(KEYWORDS_DB_FILE, consolidatedDB);
  console.log(`[CONSOLIDATION] Konsolidierte DB aktiviert: ${consolidatedFile} → ${KEYWORDS_DB_FILE}`);
  
  return {
    preConsolidationFile,
    activeFile: KEYWORDS_DB_FILE
  };
}

app.post('/api/consolidate-keywords-preview', async (req, res) => {
  try {
    const { factor } = req.body;
    console.log(`[CONSOLIDATION] Preview mit Faktor ${factor}`);
    
    const preview = await generateConsolidationPreview(factor);
    res.json(preview);
  } catch (error) {
    console.error('[CONSOLIDATION] Preview-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/consolidate-keywords-execute', async (req, res) => {
  try {
    const { factor } = req.body;
    console.log(`[CONSOLIDATION] Execute mit Faktor ${factor}`);
    
    const result = await executeConsolidation(factor);
    res.json(result);
  } catch (error) {
    console.error('[CONSOLIDATION] Execute-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/consolidate-keywords-activate', async (req, res) => {
  try {
    const { consolidatedFile } = req.body;
    console.log(`[CONSOLIDATION] Aktiviere ${consolidatedFile}`);
    
    const result = await activateConsolidatedDatabase(consolidatedFile);
    res.json(result);
  } catch (error) {
    console.error('[CONSOLIDATION] Aktivierungs-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Timeline-Daten für Visualisierung
app.get('/api/timeline-data', async (req, res) => {
  try {
    const { theme, keyword, yearFrom, yearTo } = req.query;
    
    console.log(`[TIMELINE-DATA] Filter: theme=${theme}, keyword=${keyword}, years=${yearFrom}-${yearTo}`);
    
    const keywordsDB = await loadKeywordsDatabase();
    let filteredLectures = Object.values(keywordsDB);
    
    // Filter nach Thema
    if (theme && theme !== '') {
      filteredLectures = filteredLectures.filter(l => l.theme === theme);
    }
    
    // Filter nach Schlagwort
    if (keyword && keyword !== '') {
      filteredLectures = filteredLectures.filter(l => {
        return l.keywords && l.keywords.some(kw => 
          kw.term.toLowerCase().includes(keyword.toLowerCase())
        );
      });
    }
    
    // Filter nach Jahr
    if (yearFrom) {
      filteredLectures = filteredLectures.filter(l => l.year >= parseInt(yearFrom));
    }
    if (yearTo) {
      filteredLectures = filteredLectures.filter(l => l.year <= parseInt(yearTo));
    }
    
    // Gruppiere nach Jahr
    const byYear = {};
    filteredLectures.forEach(lecture => {
      const year = lecture.year || 'Unbekannt';
      if (!byYear[year]) {
        byYear[year] = [];
      }
      byYear[year].push({
        lectureId: lecture.lectureId,
        date: lecture.date,
        keywords: lecture.keywords,
        theme: lecture.theme
      });
    });
    
    // Sortiere Jahre
    const sortedYears = Object.keys(byYear)
      .filter(y => y !== 'Unbekannt')
      .map(y => parseInt(y))
      .sort((a, b) => a - b);
    
    console.log(`[TIMELINE-DATA] Gefunden: ${filteredLectures.length} Vorträge über ${sortedYears.length} Jahre`);
    
    res.json({
      lectures: filteredLectures,
      byYear: byYear,
      years: sortedYears,
      totalCount: filteredLectures.length
    });
    
  } catch (error) {
    console.error('[TIMELINE-DATA] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// THEMENSUCHEN-CACHE-DATENBANK
// ============================================================================

// Lade Themensuchen-Cache-Datenbank
async function loadThematicSearchDatabase() {
  try {
    const data = await fs.readFile(THEMATIC_SEARCH_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('Themensuchen-Cache-DB nicht gefunden, erstelle neue...');
    return {};
  }
}

// Speichere Themensuchen-Cache-Datenbank
async function saveThematicSearchDatabase(thematicDB) {
  try {
    await fs.writeFile(THEMATIC_SEARCH_DB_FILE, JSON.stringify(thematicDB, null, 2), 'utf8');
    console.log('Themensuchen-Cache-DB gespeichert');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Themensuchen-Cache-DB:', error);
    return false;
  }
}

// Generiere Cache-Schlüssel für Themensuche
function generateThematicCacheKey(query, depth, limit, gaFilter = '') {
  const normalizedQuery = query.toLowerCase().trim();
  return `${normalizedQuery}|${depth}|${limit}|${gaFilter}`;
}

// ============================================================================
// KEYWORD THEMATIC SEARCH HILFSFUNKTIONEN (Funktionen bereits oben definiert)
// ============================================================================

// Synchronisiere keywords.json mit keyword-thematic-search.json
async function synchronizeKeywordSystems() {
  try {
    console.log('[SYNC] Starte Synchronisation der Keyword-Systeme...');
    
    const keywordsFile = path.join(__dirname, 'keywords.json');
    const keywordThematicDB = await loadKeywordThematicDatabase();
    
    let allKeywords = [];
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
      console.log('[SYNC] keywords.json nicht gefunden, erstelle neue');
      return;
    }
    
    let syncCount = 0;
    
    // Prüfe jedes Keyword in keywords.json
    for (const keyword of allKeywords) {
      const cacheKey = `keyword_${keyword.keyword.toLowerCase().trim()}_allgemein_30`;
      
      // Wenn Keyword in keywords.json existiert, aber nicht im Cache
      if (!keywordThematicDB[cacheKey] && keyword.hasDetailedAnalysis) {
        console.log(`[SYNC] Keyword "${keyword.keyword}" fehlt im Cache - generiere Analyse...`);
        
        try {
          // Generiere Analyse für fehlendes Keyword
          let keywordResults = performThematicKeywordSearch(keyword.keyword, paragraphsFromLectures);
          
          if (keywordResults.length > 0) {
            const analysis = await generateKeywordAnalysis(keyword.keyword, keywordResults, 'allgemein');
            
            keywordThematicDB[cacheKey] = {
              query: keyword.keyword,
              content: analysis,
              sources: keywordResults.slice(0, 20).map(result => ({
                ID: result.ID,
                index: result.index,
                title: result.title,
                fileName: result.fileName,
                score: Math.round(result.finalScore || 100),
                matchedTerms: result.matchedTerms || [keyword.keyword]
              })),
              searchMethod: 'keyword-thematic-search',
              totalMatches: keywordResults.length,
              llmUsed: !!process.env.CLAUDE_API_KEY,
              timestamp: new Date().toISOString()
            };
            
            syncCount++;
          }
        } catch (error) {
          console.warn(`[SYNC] Fehler bei Keyword "${keyword.keyword}":`, error.message);
        }
      }
    }
    
    if (syncCount > 0) {
      await saveKeywordThematicDatabase(keywordThematicDB);
      console.log(`[SYNC] ${syncCount} Keywords synchronisiert`);
    } else {
      console.log('[SYNC] Alle Keywords bereits synchronisiert');
    }
    
  } catch (error) {
    console.error('[SYNC] Fehler bei Synchronisation:', error);
  }
}

// Generiere Keyword-spezifische Analyse
async function generateKeywordAnalysis(query, results, depth = 'allgemein') {
  console.log('generateKeywordAnalysis aufgerufen für:', query, '| Depth:', depth, '| Results:', results.length);
  
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('Kein Claude API Key - verwende Fallback');
    return generateFallbackKeywordAnalysis(query, results);
  }
  
  const topResults = results;  // Verwende alle übergebenen Ergebnisse gemäß aktuellem Limit

  console.log('=== DEBUG topResults ===');
  console.log('Erste 3 topResults:', JSON.stringify(topResults.slice(0, 3).map(r => ({ 
    ID: r.ID, 
    index: r.index,
    fileName: r.fileName 
  })), null, 2));
  
  const contextText = topResults
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      return `[${refId}] ${result.fileName || result.title}\n${result.content}`;
    })
    .join('\n\n---\n\n');
    
  const availableRefs = topResults.map(r => `${r.ID}:${r.index}`).join(', ');
  
  console.log(`Claude bekommt Referenzen im Format GA###/##:index`);
  
  const maxTokens = {
    'allgemein': 4000,    // Erhöht von 2000 auf 4000
    'genau': 6000,        // Erhöht von 3500 auf 6000  
    'ausführlich': 8000   // Erhöht von 6000 auf 8000
  };

  // Erzwinge immer die ausführliche Tiefe unabhängig vom übergebenen depth
  const effectiveDepth = 'ausführlich';

  const prompt = `Analysiere die folgenden Textstellen zum Schlagwort: "${query}"

ANALYSE-TIEFE: ${effectiveDepth}

QUELLENANGABEN:
- Format: (GA###/Y:index) - z.B. (GA052/7:n5x6ru) oder (GA068a/7:p5fg67)
- Verfügbare Referenzen: ${availableRefs}
- KEINE Leerzeichen um Klammern!

VORGEHEN:
1. Identifiziere alle Textstellen mit "${query}"
2. Entwickle thematische Gliederung mit Zwischenüberschriften (## Überschrift)
3. Verwende hauptsächlich direkte Zitate in "Anführungszeichen" mit Quellenangaben
4. Minimaler erläuternder Text - nur zur Verbindung der Zitate

PERSPEKTIVEN für "${query}":
- Definition (Was bedeutet "${query}"?)
- Funktion (Wie wirkt "${query}"?)
- Erscheinungsformen (Wo zeigt sich "${query}"?)
- Entwicklung (Wie entwickelt sich "${query}"?)
- Zusammenhänge (Mit was steht "${query}" in Verbindung?)

FORMATIERUNG:
- Markdown: **Fette wichtige Begriffe**
- Zitate: "Text" (GA###/Y:index) oder (GA###a/Y: index)
- Überschriften: ## Überschrift
- Nutze alle ${topResults.length} verfügbaren Textstellen ausführlich

TEXTPASSAGEN:
${contextText}

ANALYSE:`;

  try {
    console.log('Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: maxTokens[effectiveDepth] || 8000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      throw new Error(`Claude API Fehler: ${response.status}`);
    }

    const result = await response.json();
    const analysisText = result.content[0].text.trim();
    
    console.log('Claude Antwort erhalten, Länge:', analysisText.length);
    
    return analysisText;
    
  } catch (error) {
    console.error('Claude API Fehler:', error.message);
    return generateFallbackKeywordAnalysis(query, results);
  }
}

// Fallback-Analyse für Keywords
function generateFallbackKeywordAnalysis(query, results) {
  const displayTitle = `Schlagwort: ${query}`;
  
  return `**${displayTitle}**

Automatische Analyse nicht verfügbar (kein Claude API-Schlüssel konfiguriert). 

Gefundene Textstellen: ${results.length}

Für eine detaillierte KI-Analyse des Schlagworts "${query}" benötigt das System einen Claude API-Schlüssel in der .env Datei.

Verfügbare Quellen:
${results.slice(0, 10).map(r => `- ${r.fileName || r.title} (${r.ID}:${r.index})`).join('\n')}`;
}

// API: Themensuchen-Cache bereitstellen
app.get('/thematic-search-database.json', async (req, res) => {
  try {
    const thematicDB = await loadThematicSearchDatabase();
    res.json(thematicDB);
  } catch (error) {
    console.error('Fehler beim Laden der Themensuchen-Cache-DB:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SERVER START
// ============================================================================

// API: Vollständigen Vortrag nach GA-Nummer und Vortragsnummer bereitstellen
app.get('/api/full-lecture/:gaNumber/:lectureNum', async (req, res) => {
  try {
    const { gaNumber, lectureNum } = req.params;
    // Compose lecture ID as used in fullLectures
    const lectureId = `${gaNumber}/${lectureNum}`;
    const lecture = fullLectures[lectureId];
    if (!lecture) {
      return res.status(404).json({ error: `Vortrag nicht gefunden: ${lectureId}` });
    }
  res.json({ lecture });
  } catch (error) {
    console.error('Fehler beim Laden des Vortrags:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Vollständigen Vortrag nach lectureId bereitstellen (Kompatibilität)
app.get('/api/full-lecture/:lectureId', async (req, res) => {
  try {
    const { lectureId } = req.params;
    const lecture = fullLectures[lectureId];
    if (!lecture) {
      return res.status(404).json({ error: `Vortrag nicht gefunden: ${lectureId}` });
    }
  res.json({ lecture });
  } catch (error) {
    console.error('Fehler beim Laden des Vortrags:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// API: MARKIERTE WÖRTER SPEICHERN
// ============================================================================

app.post('/api/save-marked-word', async (req, res) => {
  try {
    const { word, gaTitle, timestamp } = req.body;
    
    if (!word || !gaTitle) {
      return res.status(400).json({ error: 'Wort und GA-Titel erforderlich' });
    }
    
    console.log(`[MARKED-WORD] Speichere: "${word}" aus "${gaTitle}"`);
    
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    // Lade existierende Einträge
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      // Datei existiert noch nicht
      console.log('[MARKED-WORD] Erstelle neue Datei');
    }
    
    // Füge neuen Eintrag hinzu
    markedWords.push({
      word: word,
      gaTitle: gaTitle,
      timestamp: timestamp || new Date().toISOString()
    });
    
    // Speichere aktualisierte Datei
    await fs.writeFile(markedWordsFile, JSON.stringify(markedWords, null, 2), 'utf8');
    
    console.log(`[MARKED-WORD] Erfolgreich gespeichert. Insgesamt: ${markedWords.length} Einträge`);
    
    res.json({ 
      success: true, 
      totalEntries: markedWords.length,
      message: `Wort "${word}" gespeichert`
    });
    
  } catch (error) {
    console.error('[MARKED-WORD] Fehler beim Speichern:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// API: FILE MANAGEMENT
// ============================================================================

// Liste alle JSON-Dateien im Root-Verzeichnis
app.get('/api/list-files', async (req, res) => {
  try {
    const files = await fs.readdir(__dirname);
    const jsonFiles = files.filter(f => f.endsWith('.json'));
    res.json(jsonFiles);
  } catch (error) {
    console.error('Fehler beim Listen der Dateien:', error);
    res.status(500).json({ error: 'Fehler beim Listen der Dateien' });
  }
});

// Lade eine spezifische JSON-Datei
app.get('/api/file/:filename', async (req, res) => {
  try {
    const filename = req.params.filename;
    
    // Sicherheitsprüfung: Nur JSON-Dateien im Root-Verzeichnis
    if (!filename.endsWith('.json') || filename.includes('/') || filename.includes('\\')) {
      return res.status(400).json({ error: 'Ungültiger Dateiname' });
    }
    
    const filePath = path.join(__dirname, filename);
    const data = await fs.readFile(filePath, 'utf-8');
    res.json(JSON.parse(data));
  } catch (error) {
    console.error(`Fehler beim Laden von ${req.params.filename}:`, error);
    res.status(500).json({ error: 'Fehler beim Laden der Datei' });
  }
});

// ============================================================================
// BACKUP-VERWALTUNGS-ENDPUNKTE
// ============================================================================

// Liste alle verfügbaren Backups auf (Legacy - zeigt Keywords-Backups)
app.get('/api/backups/list', async (req, res) => {
  try {
    await ensureBackupDirectories();
    
    const files = await fs.readdir(KEYWORDS_BACKUP_DIR);
    const backupFiles = files
      .filter(f => f.startsWith('keywords-database-') && f.endsWith('.json'))
      .map(f => {
        const filePath = path.join(KEYWORDS_BACKUP_DIR, f);
        const stats = fsSync.statSync(filePath);
        return {
          name: f,
          path: filePath,
          size: stats.size,
          created: stats.birthtime,
          modified: stats.mtime,
          type: 'keywords'
        };
      });
    
    // Sortiere nach Änderungsdatum (neueste zuerst)
    backupFiles.sort((a, b) => b.modified - a.modified);
    
    res.json({
      backups: backupFiles,
      count: backupFiles.length
    });
  } catch (error) {
    console.error('[BACKUP-API] Fehler beim Auflisten:', error);
    res.status(500).json({ error: error.message });
  }
});

// Stelle ein Backup wieder her
app.post('/api/backups/restore', async (req, res) => {
  try {
    const { backupName } = req.body;
    
    if (!backupName) {
      return res.status(400).json({ error: 'Backup-Name erforderlich' });
    }
    
    const backupPath = path.join(KEYWORDS_BACKUP_DIR, backupName);
    
    // Prüfe ob Backup existiert
    try {
      await fs.access(backupPath);
    } catch (error) {
      return res.status(404).json({ error: 'Backup nicht gefunden' });
    }
    
    // Erstelle Backup der aktuellen Datei vor der Wiederherstellung
    console.log('[BACKUP-API] Erstelle Sicherung der aktuellen Datenbank...');
    await createKeywordsBackup();
    
    // Lade und validiere Backup
    const backupData = await fs.readFile(backupPath, 'utf8');
    const parsedBackup = JSON.parse(backupData);
    
    if (Object.keys(parsedBackup).length === 0) {
      return res.status(400).json({ error: 'Backup ist leer' });
    }
    
    // Stelle Backup wieder her
    await fs.writeFile(KEYWORDS_DB_FILE, backupData, 'utf8');
    
    console.log(`[BACKUP-API] ✓ Backup wiederhergestellt: ${backupName}`);
    console.log(`[BACKUP-API] ${Object.keys(parsedBackup).length} Einträge wiederhergestellt`);
    
    res.json({
      success: true,
      restored: backupName,
      entries: Object.keys(parsedBackup).length
    });
  } catch (error) {
    console.error('[BACKUP-API] Fehler bei Wiederherstellung:', error);
    res.status(500).json({ error: error.message });
  }
});

// Manuelles Backup erstellen
app.post('/api/backups/create', async (req, res) => {
  try {
    const { type = 'keywords' } = req.body;
    let backupFile;
    
    switch (type) {
      case 'keywords':
        backupFile = await createKeywordsBackup();
        break;
      case 'summary':
        backupFile = await createSummaryBackup();
        break;
      case 'themes':
        backupFile = await createThemesBackup();
        break;
      case 'clusters':
        backupFile = await createClustersBackup();
        break;
      case 'code':
        backupFile = await createCodeBackup();
        break;
      case 'full':
        const count = await createFullBackup();
        return res.json({
          success: true,
          backupsCreated: count,
          type: 'full'
        });
      default:
        return res.status(400).json({ error: 'Ungültiger Backup-Typ' });
    }
    
    if (backupFile) {
      res.json({
        success: true,
        backup: path.basename(backupFile),
        type: type
      });
    } else {
      res.status(500).json({ error: 'Backup konnte nicht erstellt werden' });
    }
  } catch (error) {
    console.error('[BACKUP-API] Fehler beim Erstellen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Liste Backups nach Typ
app.get('/api/backups/list/:type', async (req, res) => {
  try {
    const { type } = req.params;
    let backupDir, prefix;
    
    switch (type) {
      case 'keywords':
        backupDir = KEYWORDS_BACKUP_DIR;
        prefix = 'keywords-database';
        break;
      case 'summary':
        backupDir = SUMMARY_BACKUP_DIR;
        prefix = 'summary-database';
        break;
      case 'themes':
        backupDir = THEMES_BACKUP_DIR;
        prefix = 'themes-database';
        break;
      case 'clusters':
        backupDir = CLUSTERS_BACKUP_DIR;
        prefix = 'thematic-clusters';
        break;
      case 'code':
        backupDir = CODE_BACKUP_DIR;
        prefix = 'backend';
        break;
      case 'html':
        backupDir = HTML_BACKUP_DIR;
        prefix = null; // Alle HTML-Dateien
        break;
      default:
        return res.status(400).json({ error: 'Ungültiger Backup-Typ' });
    }
    
    await ensureBackupDirectories();
    
    const files = await fs.readdir(backupDir);
    const backupFiles = files
      .filter(f => {
        if (prefix) {
          return f.startsWith(prefix) && (f.endsWith('.json') || f.endsWith('.js') || f.endsWith('.html'));
        }
        return f.endsWith('.json') || f.endsWith('.js') || f.endsWith('.html');
      })
      .map(f => {
        const filePath = path.join(backupDir, f);
        const stats = fsSync.statSync(filePath);
        return {
          name: f,
          path: filePath,
          size: stats.size,
          created: stats.birthtime,
          modified: stats.mtime,
          type: type
        };
      });
    
    // Sortiere nach Änderungsdatum (neueste zuerst)
    backupFiles.sort((a, b) => b.modified - a.modified);
    
    res.json({
      backups: backupFiles,
      count: backupFiles.length,
      type: type
    });
  } catch (error) {
    console.error('[BACKUP-API] Fehler beim Auflisten:', error);
    res.status(500).json({ error: error.message });
  }
});

async function startServer() {
  try {
    console.log('\n========================================');
    console.log('Initialisiere Server...');
    console.log('========================================');
    
await loadSynonyms();
await loadFullLectures();

// Synchronisiere Keyword-Systeme beim Start
await synchronizeKeywordSystems();

// Konvertiere Lectures zu Absatz-Format
console.log('\nKonvertiere Lectures zu Absatz-Format...');
Object.values(fullLectures).forEach(lecture => {
  lecture.paragraphs?.forEach((para, idx) => {
    paragraphsFromLectures.push({
      ID: lecture.ID,
      index: para.index || `para_${idx}`,
      title: lecture.title,
      fileName: lecture.fileName,
      content: para.content || para.text || '',
      location: lecture.location,
      date: lecture.date
    });
  });
});
console.log(`  ✓ ${paragraphsFromLectures.length} Absätze konvertiert`);
    await loadQueryLog();
    
    // Lade Themensuchen-Cache-DB
    const thematicDB = await loadThematicSearchDatabase();
    console.log(`Themensuchen-Cache geladen: ${Object.keys(thematicDB).length} Einträge`);
    
    console.log('\n========================================');
    console.log('DATEN GELADEN:');
    console.log(`  ${paragraphsFromLectures.length} Absätze`);
    console.log(`  ${Object.keys(fullLectures).length} Vorträge`);
    console.log(`  ${Object.keys(synonyms).length} Synonym-Gruppen`);
    console.log(`  ${Object.keys(queryLog).length} Query-Log Einträge`);
    console.log(`  ${Object.keys(thematicDB).length} Themensuchen im Cache`);
    console.log('========================================');
    
    app.listen(PORT, () => {
      console.log(`\n✓ Server läuft auf http://localhost:${PORT}`);
      console.log(`\nVerfügbare Endpoints:`);
      console.log(`   GET  /debug/status`);
      console.log(`   POST /api/hybrid-search`);
      console.log(`   POST /api/fulltext-search`);
      console.log(`   POST /api/thematic-hybrid-search`);
      console.log(`   POST /api/summarize-lecture`);
      console.log(`   GET  /api/check-summary/:gaNumber/:lectureNum`);
      console.log(`   GET  /api/full-lecture/:lectureId`);
      console.log(`   GET  /api/full-lecture/:gaNumber/:lectureNum`);
      console.log(`   GET  /api/lectures/list`);
      console.log(`   GET  /api/available-ga`);
      console.log(`   GET  /api/ga-overview/:gaNumber`);
      console.log(`   GET  /ga-overview-map.json`);
      console.log(`   POST /api/admin/generate-synonyms`);
      console.log(`   GET  /api/admin/synonym-stats`);
      console.log(`   POST /api/save-summary`);
      console.log(`   POST /api/keywords-generate`);
      console.log(`   POST /api/keyword-thematic-search`);
      console.log(`   POST /api/keywords-save`);
      console.log(`   POST /api/keywords-add`);
      console.log(`   POST /api/keywords-delete`);
      console.log(`   GET  /api/keywords-files`);
      console.log(`   GET  /api/keywords-list`);
      console.log(`   POST /api/save-marked-word`);
      console.log(`   GET  /summary-database.json`);
      console.log(`   GET  /thematic-search-database.json`);
      console.log(`   POST /api/generate-keywords`);
      console.log(`   GET  /api/keywords-database`);
      console.log(`   GET  /api/keywords-stats`);
      console.log(`   POST /api/generate-themes`);
      console.log(`   GET  /api/themes-database`);
      console.log(`   GET  /api/timeline-data`);
      console.log(`\n✓ System bereit!\n`);
    });
    
  } catch (error) {
    console.error('\n✗ Fehler beim Server-Start:', error);
    process.exit(1);
  }
}

startServer();
