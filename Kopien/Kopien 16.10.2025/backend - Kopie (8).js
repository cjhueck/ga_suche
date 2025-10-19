// hybrid-search-server-unified.js - Vereinheitlichtes System mit GA/Vortrag IDs
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = 3003;

// Middleware - WICHTIG: Reihenfolge beachten!
app.use(cors());
app.use(express.json());

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
    
    const rankedResults = applySemanticRanking(keywordResults, query);
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
    const { word1, word2, proximity = null } = req.body;
    
    if (!word1) {
      return res.status(400).json({ error: 'Mindestens ein Suchwort erforderlich' });
    }
    
    console.log(`Volltext-Suche: "${word1}"${word2 ? ` + "${word2}"` : ''}${proximity ? ` (Proximity: ${proximity})` : ''}`);
    
    const results = [];
    const addedParagraphs = new Set();
    
    Object.values(fullLectures).forEach(lecture => {
      const paragraphs = lecture.paragraphs || [];
      
      paragraphs.forEach((para, paraIndex) => {
        const content = (para.content || para.text || '').toLowerCase();
        const hasWord1 = word1 && content.includes(word1.toLowerCase());
        const hasWord2 = word2 && content.includes(word2.toLowerCase());
        
        const paragraphsToAdd = [];
        
        if (!word2) {
          if (hasWord1) {
            paragraphsToAdd.push(paraIndex);
          }
        } else if (!proximity) {
          if (hasWord1 || hasWord2) {
            paragraphsToAdd.push(paraIndex);
          }
        } else {
          const maxDist = parseInt(proximity);
          
          if (hasWord1 && hasWord2) {
            paragraphsToAdd.push(paraIndex);
          } else if (hasWord1) {
            for (let i = Math.max(0, paraIndex - maxDist); i <= Math.min(paragraphs.length - 1, paraIndex + maxDist); i++) {
              if (i !== paraIndex) {
                const neighborContent = (paragraphs[i].content || paragraphs[i].text || '').toLowerCase();
                if (neighborContent.includes(word2.toLowerCase())) {
                  paragraphsToAdd.push(paraIndex);
                  paragraphsToAdd.push(i);
                  break;
                }
              }
            }
          } else if (hasWord2) {
            for (let i = Math.max(0, paraIndex - maxDist); i <= Math.min(paragraphs.length - 1, paraIndex + maxDist); i++) {
              if (i !== paraIndex) {
                const neighborContent = (paragraphs[i].content || paragraphs[i].text || '').toLowerCase();
                if (neighborContent.includes(word1.toLowerCase())) {
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
            const pContent = (p.content || p.text || '').toLowerCase();
            
            results.push({
              ID: lecture.ID,
              title: lecture.title,
              fileName: lecture.fileName,
              location: lecture.location,
              date: lecture.date,
              paragraphIndex: idx,
              index: p.index,
              content: p.content || p.text,
              hasWord1: pContent.includes(word1.toLowerCase()),
              hasWord2: word2 && pContent.includes(word2.toLowerCase())
            });
          }
        });
      });
    });
    
    console.log(`Volltext-Suche: ${results.length} Absätze gefunden`);
    
    // Query-Tracking
    if (word1) trackQueryTerms(word1, results.length);
    if (word2) trackQueryTerms(word2, results.length);
    
    res.json({
      query: { word1, word2, proximity },
      results: results,
      resultCount: results.length
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
    
    // Speichere nur in zentrale Summary-Datenbank (kein Memory-Cache mehr)
    try {
      console.log(`[SPEICHERUNG] Lade aktuelle Summary-DB...`);
      const summaryDB = await loadSummaryDatabase();
      console.log(`[SPEICHERUNG] Aktuelle DB hat ${Object.keys(summaryDB).length} Einträge`);
      
      summaryDB[lectureId] = {
        summary: summaryData.summary,
        headings: summaryData.headings || [],
        timestamp: new Date().toISOString()
      };
      console.log(`[SPEICHERUNG] Füge Summary für ${lectureId} hinzu...`);
      
      const success = await saveSummaryDatabase(summaryDB);
      if (success) {
        console.log(`[SPEICHERUNG] ✓ Summary für ${lectureId} erfolgreich in zentrale DB gespeichert`);
      } else {
        console.error(`[SPEICHERUNG] ✗ Speicherung fehlgeschlagen für ${lectureId}`);
      }
    } catch (dbError) {
      console.error(`[SPEICHERUNG] ✗ Zentrale DB-Speicherung fehlgeschlagen für ${lectureId}:`, dbError.message);
      console.error(`[SPEICHERUNG] Stack:`, dbError.stack);
    }
    
    // Legacy saveSummaryCache() entfernt - verwenden nur noch zentrale DB
    
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

// ============================================================================
// KEYWORD TIMELINE ANALYSIS (KI-basierte Timeline für Schlagwörter)
// ============================================================================

// Konfigurierbare Parameter für Timeline-Optimierung
const TIMELINE_CONFIG = {
  MAX_LECTURES_PER_REQUEST: 50,        // Maximale Vorträge pro API-Call
  MAX_PARAGRAPHS_PER_LECTURE: 15,       // Maximale Absätze pro Vortrag
  MAX_PARAGRAPH_LENGTH: 2000,           // Maximale Länge pro Absatz
  CHUNK_SIZE: 30,                       // Vorträge pro Chunk bei Chunking
  MIN_RELEVANCE_SCORE: 0.1,             // Mindest-Relevanz-Score
  MAX_TOTAL_TOKENS: 150000              // Geschätzte Token-Limits (Input)
};

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

// Hilfsfunktion: Absatz kürzen mit Kontext um das Schlagwort
function truncateParagraph(paragraph, keyword, maxLength = TIMELINE_CONFIG.MAX_PARAGRAPH_LENGTH) {
  if (paragraph.content.length <= maxLength) {
    return paragraph.content;
  }
  
  const keywordLower = keyword.toLowerCase();
  const contentLower = paragraph.content.toLowerCase();
  const keywordIndex = contentLower.indexOf(keywordLower);
  
  if (keywordIndex === -1) {
    // Fallback: Erste Zeichen nehmen
    return paragraph.content.substring(0, maxLength) + '...';
  }
  
  // Kontext um das Schlagwort herum
  const contextStart = Math.max(0, keywordIndex - maxLength / 2);
  const contextEnd = Math.min(paragraph.content.length, contextStart + maxLength);
  
  let truncated = paragraph.content.substring(contextStart, contextEnd);
  
  // Füge Ellipsen hinzu wenn gekürzt wurde
  if (contextStart > 0) truncated = '...' + truncated;
  if (contextEnd < paragraph.content.length) truncated = truncated + '...';
  
  return truncated;
}

// Hilfsfunktion: Vorträge nach Relevanz sortieren und limitieren
function selectTopRelevantLectures(relevantLectures, keyword, maxLectures = TIMELINE_CONFIG.MAX_LECTURES_PER_REQUEST) {
  console.log(`[KEYWORD-TIMELINE] Berechne Relevanz-Scores für ${relevantLectures.length} Vorträge...`);
  
  // Berechne Relevanz-Scores
  const scoredLectures = relevantLectures.map(lecture => {
    const score = calculateRelevanceScore(lecture, keyword);
    return { ...lecture, relevanceScore: score };
  });
  
  // Sortiere nach Relevanz (absteigend)
  scoredLectures.sort((a, b) => b.relevanceScore - a.relevanceScore);
  
  // Filtere nach Mindest-Score
  const filteredLectures = scoredLectures.filter(lecture => 
    lecture.relevanceScore >= TIMELINE_CONFIG.MIN_RELEVANCE_SCORE
  );
  
  console.log(`[KEYWORD-TIMELINE] ${filteredLectures.length} Vorträge über Mindest-Score (${TIMELINE_CONFIG.MIN_RELEVANCE_SCORE})`);
  
  // Nimm nur die Top-Vorträge
  const topLectures = filteredLectures.slice(0, maxLectures);
  
  console.log(`[KEYWORD-TIMELINE] Verwende Top ${topLectures.length} Vorträge für Analyse`);
  
  return topLectures;
}

// Chunking-Funktion für sehr häufige Schlagwörter
async function generateKeywordTimelineAnalysisChunked(keyword, relevantLectures, allLectures) {
  console.log(`[KEYWORD-TIMELINE-CHUNKED] Starte Chunking-Analyse für "${keyword}" mit ${relevantLectures.length} Vorträgen`);
  
  // Sortiere alle Vorträge nach Relevanz
  const scoredLectures = relevantLectures.map(lecture => {
    const score = calculateRelevanceScore(lecture, keyword);
    return { ...lecture, relevanceScore: score };
  }).sort((a, b) => b.relevanceScore - a.relevanceScore);
  
  // Teile in Chunks auf
  const chunks = [];
  for (let i = 0; i < scoredLectures.length; i += TIMELINE_CONFIG.CHUNK_SIZE) {
    chunks.push(scoredLectures.slice(i, i + TIMELINE_CONFIG.CHUNK_SIZE));
  }
  
  console.log(`[KEYWORD-TIMELINE-CHUNKED] Aufgeteilt in ${chunks.length} Chunks`);
  
  const allTimelineEntries = [];
  const chunkResults = [];
  
  // Verarbeite jeden Chunk
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    console.log(`[KEYWORD-TIMELINE-CHUNKED] Verarbeite Chunk ${i + 1}/${chunks.length} (${chunk.length} Vorträge)`);
    
    try {
      const chunkResult = await processTimelineChunk(keyword, chunk, allLectures, i + 1, chunks.length);
      chunkResults.push(chunkResult);
      allTimelineEntries.push(...chunkResult.timelineEntries);
      
      // Kurze Pause zwischen Chunks um API-Limits zu schonen
      if (i < chunks.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    } catch (error) {
      console.error(`[KEYWORD-TIMELINE-CHUNKED] Fehler bei Chunk ${i + 1}:`, error);
      // Fallback für diesen Chunk
      const fallbackResult = generateFallbackKeywordTimeline(keyword, chunk);
      chunkResults.push(fallbackResult);
      allTimelineEntries.push(...fallbackResult.timelineEntries);
    }
  }
  
  // Zusammenführung und Deduplizierung
  const mergedResult = mergeTimelineResults(allTimelineEntries, keyword, allLectures, relevantLectures.length);
  
  console.log(`[KEYWORD-TIMELINE-CHUNKED] Chunking-Analyse abgeschlossen: ${mergedResult.timelineEntries.length} Timeline-Einträge`);
  
  return mergedResult;
}

// Verarbeite einen einzelnen Chunk
async function processTimelineChunk(keyword, chunkLectures, allLectures, chunkNumber, totalChunks) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  // Erstelle Kontext-Text für diesen Chunk
  const contextText = chunkLectures
    .map(lecture => {
      const relevantParagraphs = lecture.paragraphs
        .filter(paragraph => 
          paragraph.content && paragraph.content.toLowerCase().includes(keyword.toLowerCase())
        )
        .slice(0, TIMELINE_CONFIG.MAX_PARAGRAPHS_PER_LECTURE);
      
      const paragraphsText = relevantParagraphs
        .map(p => {
          const truncatedContent = truncateParagraph(p, keyword);
          return `[${lecture.ID}:${p.index}] ${truncatedContent}`;
        })
        .join('\n\n');
      
      return `=== ${lecture.ID} - ${lecture.title} (${lecture.date || 'Datum unbekannt'}) [Score: ${lecture.relevanceScore.toFixed(3)}] ===\n${paragraphsText}`;
    })
    .join('\n\n---\n\n');

  const prompt = `Analysiere das Vorkommen des Schlagworts "${keyword}" in Rudolf Steiners Gesamtausgabe (GA) und erstelle eine chronologische Timeline mit thematischer Relevanz-Bewertung.

HINWEIS: Dies ist Chunk ${chunkNumber} von ${totalChunks} - analysiere nur die hier bereitgestellten Vorträge und wähle NUR die mit höchster thematischer Relevanz aus.

AUFGABE:
1. Identifiziere alle Vorträge, in denen "${keyword}" das zentrale Thema ist
2. Erstelle eine chronologische Timeline NUR der Vorträge mit höchster thematischer Relevanz
3. Analysiere die Entwicklung des Begriffs über die Zeit

BEWERTUNGSKRITERIEN für "hoch"-Relevanz:
- Das Schlagwort ist zentrales Thema des Vortrags/Abschnitts
- Das Schlagwort wird ausführlich und tiefgreifend behandelt
- Der Vortrag/Abschnitt dreht sich hauptsächlich um dieses Konzept

ZITATE-ANWEISUNGEN:
- Extrahiere NUR direkte Zitate aus dem Text, die das Schlagwort enthalten
- Füge den Absatz-Index in eckigen Klammern vor jedem Zitat hinzu (z.B. [GA087/18:5])
- KEINE zusammenfassenden Sätze oder Interpretationen
- KEINE Überschriften oder Beschreibungen über den Zitaten
- Zitate müssen wörtlich aus dem Text stammen
- Beispiel: "[GA087/18:5] Die anschauende Urteilskraft ist..." statt "Goethes Auseinandersetzung mit Kant..."

AUSGABEFORMAT:
Erstelle eine JSON-Struktur mit folgendem Format:

{
  "keyword": "${keyword}",
  "timelineEntries": [
    {
      "lectureId": "GA066/1",
      "title": "Vortragstitel",
      "date": "15.03.1912",
      "year": 1912,
      "keyQuotes": ["wichtiges Zitat 1", "wichtiges Zitat 2"],
      "thematicFocus": "Beschreibung des thematischen Schwerpunkts"
    }
  ],
  "analysis": "Kurze Analyse der Entwicklung des Begriffs über die Zeit (nur für Vorträge mit höchster Relevanz)",
  "chunkInfo": {
    "chunkNumber": ${chunkNumber},
    "totalChunks": ${totalChunks},
    "processedLectures": ${chunkLectures.length}
  }
}

WICHTIGE HINWEISE:
- Sortiere die timelineEntries chronologisch nach Jahr und Datum
- Verwende NUR Vorträge mit höchster thematischer Relevanz ("hoch")
- Ignoriere Vorträge, in denen das Schlagwort nur beiläufig erwähnt wird
- Zitate müssen wörtlich aus dem Text stammen und das Schlagwort enthalten
- KEINE zusammenfassenden Sätze, Interpretationen oder Überschriften über den Zitaten
- KEINE eigenen Formulierungen wie "Goethes Auseinandersetzung mit Kant..."
- Nur direkte Textzitate in Anführungszeichen
- Die Analyse sollte die Entwicklung und Bedeutung des Begriffs über die Zeit beschreiben

VERFÜGBARE VORTRÄGE (Chunk ${chunkNumber}/${totalChunks}):
${contextText}

ANALYSE:`;

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
        max_tokens: 8000,
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
    
    // Versuche JSON aus der Antwort zu extrahieren
    try {
      const jsonMatch = analysisText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const chunkData = JSON.parse(jsonMatch[0]);
        return chunkData;
      }
    } catch (parseError) {
      console.warn(`[KEYWORD-TIMELINE-CHUNKED] JSON-Parse Fehler bei Chunk ${chunkNumber}:`, parseError.message);
    }
    
    // Fallback für diesen Chunk
    return generateFallbackKeywordTimeline(keyword, chunkLectures);
    
  } catch (error) {
    console.error(`[KEYWORD-TIMELINE-CHUNKED] API-Fehler bei Chunk ${chunkNumber}:`, error);
    return generateFallbackKeywordTimeline(keyword, chunkLectures);
  }
}

// Zusammenführung der Chunk-Ergebnisse
function mergeTimelineResults(allTimelineEntries, keyword, allLectures, relevantLecturesCount) {
  console.log(`[KEYWORD-TIMELINE-MERGE] Zusammenführung von ${allTimelineEntries.length} Timeline-Einträgen`);
  
  // Deduplizierung nach lectureId
  const uniqueEntries = new Map();
  
  allTimelineEntries.forEach(entry => {
    if (!uniqueEntries.has(entry.lectureId)) {
      uniqueEntries.set(entry.lectureId, entry);
    } else {
      // Bei Duplikaten: Behalte den mit höherer Relevanz
      const existing = uniqueEntries.get(entry.lectureId);
      const relevanceOrder = { 'hoch': 3, 'mittel': 2, 'niedrig': 1 };
      
      if (relevanceOrder[entry.relevance] > relevanceOrder[existing.relevance]) {
        uniqueEntries.set(entry.lectureId, entry);
      }
    }
  });
  
  // Sortiere chronologisch
  const sortedEntries = Array.from(uniqueEntries.values()).sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.date.localeCompare(b.date);
  });
  
  // Erstelle finale Analyse
  const analysis = `Das Schlagwort "${keyword}" wurde in ${relevantLecturesCount} Vorträgen gefunden. 
Die Timeline zeigt die chronologische Entwicklung der Erwähnungen über ${sortedEntries.length} thematisch relevante Vorträge.
Die Analyse wurde durch Chunking optimiert, um alle relevanten Inhalte zu erfassen.`;
  
  return {
    keyword: keyword,
    timelineEntries: sortedEntries,
    analysis: analysis,
    totalLectures: allLectures.length,
    relevantLectures: relevantLecturesCount,
    processingMethod: 'chunked-analysis'
  };
}

async function generateKeywordTimelineAnalysis(keyword, allLectures) {
  console.log(`[KEYWORD-TIMELINE] Generiere Timeline-Analyse für: "${keyword}"`);
  
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('[KEYWORD-TIMELINE] Kein Claude API Key - verwende Fallback');
    return generateFallbackKeywordTimeline(keyword, allLectures);
  }

  // Filtere alle Vorträge, die das Schlagwort enthalten
  const relevantLectures = allLectures.filter(lecture => {
    if (!lecture.paragraphs) return false;
    
    return lecture.paragraphs.some(paragraph => {
      const content = paragraph.content || '';
      return content.toLowerCase().includes(keyword.toLowerCase());
    });
  });

  console.log(`[KEYWORD-TIMELINE] ${relevantLectures.length} Vorträge mit "${keyword}" gefunden`);

  if (relevantLectures.length === 0) {
    return {
      keyword: keyword,
      timelineEntries: [],
      analysis: `Keine Vorträge mit dem Schlagwort "${keyword}" gefunden.`,
      totalLectures: allLectures.length,
      relevantLectures: 0
    };
  }

  // Prüfe ob Chunking notwendig ist
  if (relevantLectures.length > TIMELINE_CONFIG.MAX_LECTURES_PER_REQUEST) {
    console.log(`[KEYWORD-TIMELINE] Zu viele Vorträge (${relevantLectures.length}) - verwende Chunking-Strategie`);
    return await generateKeywordTimelineAnalysisChunked(keyword, relevantLectures, allLectures);
  }

  // Verwende optimierte Vortragsauswahl
  const topLectures = selectTopRelevantLectures(relevantLectures, keyword);

  // Erstelle optimierten Kontext-Text für KI-Analyse
  const contextText = topLectures
    .map(lecture => {
      const relevantParagraphs = lecture.paragraphs
        .filter(paragraph => 
          paragraph.content && paragraph.content.toLowerCase().includes(keyword.toLowerCase())
        )
        .slice(0, TIMELINE_CONFIG.MAX_PARAGRAPHS_PER_LECTURE); // Limit pro Vortrag
      
      const paragraphsText = relevantParagraphs
        .map(p => {
          const truncatedContent = truncateParagraph(p, keyword);
          return `[${lecture.ID}:${p.index}] ${truncatedContent}`;
        })
        .join('\n\n');
      
      return `=== ${lecture.ID} - ${lecture.title} (${lecture.date || 'Datum unbekannt'}) [Score: ${lecture.relevanceScore.toFixed(3)}] ===\n${paragraphsText}`;
    })
    .join('\n\n---\n\n');

  // Logge Kontext-Größe für Debugging
  const contextLength = contextText.length;
  console.log(`[KEYWORD-TIMELINE] Kontext-Länge: ${contextLength} Zeichen (geschätzte Tokens: ${Math.round(contextLength / 4)})`);

  const prompt = `Analysiere das Vorkommen des Schlagworts "${keyword}" in Rudolf Steiners Gesamtausgabe (GA) und erstelle eine chronologische Timeline mit thematischer Relevanz-Bewertung.

OPTIMIERUNG: Diese Analyse verwendet intelligente Relevanz-Bewertung - nur die wichtigsten Vorträge wurden ausgewählt.

AUFGABE:
1. Identifiziere alle Vorträge, in denen "${keyword}" das zentrale Thema ist
2. Erstelle eine chronologische Timeline NUR der Vorträge mit höchster thematischer Relevanz
3. Analysiere die Entwicklung des Begriffs über die Zeit

BEWERTUNGSKRITERIEN für "hoch"-Relevanz:
- Das Schlagwort ist zentrales Thema des Vortrags/Abschnitts
- Das Schlagwort wird ausführlich und tiefgreifend behandelt
- Der Vortrag/Abschnitt dreht sich hauptsächlich um dieses Konzept

ZITATE-ANWEISUNGEN:
- Extrahiere NUR direkte Zitate aus dem Text, die das Schlagwort enthalten
- Füge den Absatz-Index in eckigen Klammern vor jedem Zitat hinzu (z.B. [GA087/18:5])
- KEINE zusammenfassenden Sätze oder Interpretationen
- KEINE Überschriften oder Beschreibungen über den Zitaten
- Zitate müssen wörtlich aus dem Text stammen
- Beispiel: "[GA087/18:5] Die anschauende Urteilskraft ist..." statt "Goethes Auseinandersetzung mit Kant..."

AUSGABEFORMAT:
Erstelle eine JSON-Struktur mit folgendem Format:

{
  "keyword": "${keyword}",
  "timelineEntries": [
    {
      "lectureId": "GA066/1",
      "title": "Vortragstitel",
      "date": "15.03.1912",
      "year": 1912,
      "keyQuotes": ["wichtiges Zitat 1", "wichtiges Zitat 2"],
      "thematicFocus": "Beschreibung des thematischen Schwerpunkts"
    }
  ],
  "analysis": "Kurze Analyse der Entwicklung des Begriffs über die Zeit (nur für Vorträge mit höchster Relevanz)",
  "totalLectures": ${allLectures.length},
  "relevantLectures": ${topLectures.length},
  "processingMethod": "optimized-analysis"
}

WICHTIGE HINWEISE:
- Sortiere die timelineEntries chronologisch nach Jahr und Datum
- Verwende NUR Vorträge mit höchster thematischer Relevanz ("hoch")
- Ignoriere Vorträge, in denen das Schlagwort nur beiläufig erwähnt wird
- Zitate müssen wörtlich aus dem Text stammen und das Schlagwort enthalten
- KEINE zusammenfassenden Sätze, Interpretationen oder Überschriften über den Zitaten
- KEINE eigenen Formulierungen wie "Goethes Auseinandersetzung mit Kant..."
- Nur direkte Textzitate in Anführungszeichen
- Die Analyse sollte die Entwicklung und Bedeutung des Begriffs über die Zeit beschreiben

VERFÜGBARE VORTRÄGE (Top ${topLectures.length} nach Relevanz):
${contextText}

ANALYSE:`;

  try {
    console.log('[KEYWORD-TIMELINE] Rufe Claude API auf...');
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': claudeApiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 8000,
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
    
    console.log('[KEYWORD-TIMELINE] Claude Antwort erhalten, Länge:', analysisText.length);
    
    // Versuche JSON aus der Antwort zu extrahieren
    try {
      const jsonMatch = analysisText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const timelineData = JSON.parse(jsonMatch[0]);
        console.log('[KEYWORD-TIMELINE] JSON erfolgreich geparst');
        return timelineData;
      }
    } catch (parseError) {
      console.warn('[KEYWORD-TIMELINE] JSON-Parse Fehler:', parseError.message);
    }
    
    // Fallback: Erstelle Timeline aus verfügbaren Daten
    return generateFallbackKeywordTimeline(keyword, topLectures);

  } catch (error) {
    console.error('[KEYWORD-TIMELINE] LLM-Analyse Fehler:', error);
    return generateFallbackKeywordTimeline(keyword, topLectures);
  }
}

function generateFallbackKeywordTimeline(keyword, lectures) {
  console.log('[KEYWORD-TIMELINE] Verwende Fallback-Timeline');
  
  const timelineEntries = lectures.map(lecture => {
    // Extrahiere Jahr aus Datum oder GA-Nummer
    let year = null;
    if (lecture.date) {
      const yearMatch = lecture.date.match(/^(\d{4})/);
      if (yearMatch) year = parseInt(yearMatch[1]);
    }
    
    if (!year) {
      const gaNum = parseInt(lecture.ID.replace('GA', '').split('/')[0]);
      if (gaNum >= 51 && gaNum <= 100) year = 1900 + Math.floor((gaNum - 51) * 0.5);
      else if (gaNum >= 101 && gaNum <= 200) year = 1910 + Math.floor((gaNum - 101) * 0.3);
      else if (gaNum >= 201 && gaNum <= 300) year = 1920 + Math.floor((gaNum - 201) * 0.2);
      else year = 1925;
    }
    
    return {
      lectureId: lecture.ID,
      title: lecture.title || 'Titel unbekannt',
      date: lecture.date || 'Datum unbekannt',
      year: year,
      relevance: 'mittel', // Fallback-Wert
      context: `Erwähnung von "${keyword}" in ${lecture.ID}`,
      keyQuotes: [],
      thematicFocus: 'Automatisch erkannt'
    };
  });
  
  // Sortiere chronologisch
  timelineEntries.sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.date.localeCompare(b.date);
  });
  
  return {
    keyword: keyword,
    timelineEntries: timelineEntries,
    analysis: `Das Schlagwort "${keyword}" wurde in ${lectures.length} Vorträgen gefunden. Die Timeline zeigt die chronologische Entwicklung der Erwähnungen.`,
    totalLectures: lectures.length,
    relevantLectures: lectures.length,
    processingMethod: 'fallback-analysis'
  };
}

// ============================================================================
// TIMELINE CACHE FUNCTIONS
// ============================================================================

async function loadTimelineCacheDatabase() {
  try {
    const timelineCachePath = path.join(__dirname, 'timeline-cache-database.json');
    const data = await fs.readFile(timelineCachePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('[TIMELINE-CACHE] Neue Timeline-Cache-DB erstellt');
    return {};
  }
}

async function saveTimelineCacheDatabase(timelineCacheDB) {
  try {
    const timelineCachePath = path.join(__dirname, 'timeline-cache-database.json');
    await fs.writeFile(timelineCachePath, JSON.stringify(timelineCacheDB, null, 2));
    console.log('[TIMELINE-CACHE] Timeline-Cache-DB gespeichert');
  } catch (error) {
    console.error('[TIMELINE-CACHE] Fehler beim Speichern:', error);
    throw error;
  }
}

// ============================================================================
// KEYWORD TIMELINE API ENDPOINT
// ============================================================================

app.post('/api/keyword-timeline-analysis', async (req, res) => {
  try {
    const { keyword, useCache = true } = req.body;
    
    if (!keyword) {
      return res.status(400).json({ error: 'Keyword erforderlich' });
    }
    
    console.log(`[KEYWORD-TIMELINE-API] Timeline-Analyse für: "${keyword}"`);
    
    // Cache-System für Keyword-Timeline-Analyse
    const cacheKey = `timeline_${keyword.toLowerCase().trim()}`;
    const timelineCacheDB = await loadTimelineCacheDatabase();
    
    // Prüfe Cache (nur wenn useCache true ist)
    if (useCache && timelineCacheDB[cacheKey]) {
      console.log(`[KEYWORD-TIMELINE-CACHE] Cache-Hit für: "${keyword}"`);
      return res.json({
        ...timelineCacheDB[cacheKey],
        fromCache: true,
        cacheTimestamp: timelineCacheDB[cacheKey].timestamp
      });
    }
    
    // Lade alle Vorträge
    if (Object.keys(fullLectures).length === 0) {
      await loadFullLectures();
    }
    
    const allLectures = Object.values(fullLectures);
    
    // Generiere Timeline-Analyse
    const timelineData = await generateKeywordTimelineAnalysis(keyword, allLectures);
    
    // Erweitere Timeline-Daten um zusätzliche Metadaten
    const enhancedTimelineData = {
      ...timelineData,
      searchMethod: 'keyword-timeline-analysis',
      llmUsed: !!process.env.CLAUDE_API_KEY,
      generatedAt: new Date().toISOString()
    };
    
    // Speichere im Cache
    timelineCacheDB[cacheKey] = {
      ...enhancedTimelineData,
      timestamp: new Date().toISOString()
    };
    
    // Speichere Cache-DB (non-blocking)
    saveTimelineCacheDatabase(timelineCacheDB).then(() => {
      console.log(`[KEYWORD-TIMELINE-CACHE] Timeline gecacht für: "${keyword}"`);
    }).catch(err => {
      console.warn('[KEYWORD-TIMELINE-CACHE] Fehler beim Cachen:', err.message);
    });
    
    return res.json({
      ...enhancedTimelineData,
      fromCache: false,
      cacheTimestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[KEYWORD-TIMELINE-API] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SINGLE LECTURE API (für Timeline)
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
    
    console.log(`[KEYWORDS-BATCH-ADD] Starte Batch-Verarbeitung für ${keywords.length} Schlagwörter`);
    
    const results = {
      batchId: batchId || `batch_${Date.now()}`,
      totalKeywords: keywords.length,
      processed: 0,
      successful: [],
      failed: [],
      skipped: [],
      startTime: new Date().toISOString()
    };
    
    // Verarbeite Schlagwörter sequenziell (um API-Limits zu respektieren)
    for (let i = 0; i < keywords.length; i++) {
      const keyword = keywords[i].trim();
      
      if (!keyword) {
        results.skipped.push({
          keyword: keywords[i],
          reason: 'Leeres Schlagwort',
          index: i
        });
        continue;
      }
      
      console.log(`[KEYWORDS-BATCH-ADD] Verarbeite ${i + 1}/${keywords.length}: "${keyword}"`);
      
      try {
        // Prüfe ob Schlagwort bereits existiert
        const keywordsFile = path.join(__dirname, 'keywords.json');
        let allKeywords = [];
        
        try {
          const fileContent = await fs.readFile(keywordsFile, 'utf8');
          allKeywords = JSON.parse(fileContent);
        } catch (error) {
          console.log('[KEYWORDS-BATCH-ADD] keywords.json nicht gefunden, erstelle neue');
        }
        
        // Prüfe auf Duplikate
        const existingKeywordIndex = allKeywords.findIndex(k => 
          k.keyword.toLowerCase() === keyword.toLowerCase()
        );
        
        if (existingKeywordIndex !== -1 && !overwrite) {
          results.skipped.push({
            keyword: keyword,
            reason: 'Schlagwort bereits vorhanden',
            index: i,
            existingKeyword: allKeywords[existingKeywordIndex].keyword
          });
          continue;
        }
        
        // Führe Keyword-Thematische Suche durch
        let keywordResults = performThematicKeywordSearch(keyword, paragraphsFromLectures);
        
        if (keywordResults.length === 0) {
          results.failed.push({
            keyword: keyword,
            reason: 'Keine relevanten Textstellen gefunden',
            index: i
          });
          continue;
        }
        
        // Generiere KI-Analyse
        const analysis = await generateKeywordAnalysis(keyword, keywordResults, 'ausführlich');
        
        // Erstelle neues Schlagwort-Objekt
        const newKeyword = {
          keyword: keyword,
          alphabetical: keyword.charAt(0).toUpperCase(),
          text: `**${keyword}**`,
          gaReferences: keywordResults.slice(0, 20).map(r => r.ID),
          generatedAt: new Date().toISOString(),
          sourceAnalysis: 'ki-generated-batch',
          analysisLength: analysis.length,
          resultCount: keywordResults.length,
          hasDetailedAnalysis: true,
          batchId: results.batchId,
          batchIndex: i
        };
        
        if (existingKeywordIndex !== -1 && overwrite) {
          allKeywords[existingKeywordIndex] = newKeyword;
        } else {
          allKeywords.push(newKeyword);
        }
        
        // Speichere zurück in keywords.json
        await fs.writeFile(keywordsFile, JSON.stringify(allKeywords, null, 2), 'utf8');
        
        // Speichere detaillierte Analyse im Cache
        const keywordThematicDB = await loadKeywordThematicDatabase();
        const cacheKey = `keyword_${keyword.toLowerCase().trim()}_ausführlich_30`;
        
        keywordThematicDB[cacheKey] = {
          query: keyword,
          content: analysis,
          sources: keywordResults.slice(0, 20).map(result => ({
            ID: result.ID,
            index: result.index,
            title: result.title,
            fileName: result.fileName,
            score: Math.round(result.finalScore || 100),
            matchedTerms: result.matchedTerms || [keyword]
          })),
          searchMethod: 'keyword-thematic-search',
          totalMatches: keywordResults.length,
          llmUsed: !!process.env.CLAUDE_API_KEY,
          timestamp: new Date().toISOString(),
          batchId: results.batchId
        };
        
        await saveKeywordThematicDatabase(keywordThematicDB);
        
        results.successful.push({
          keyword: keyword,
          index: i,
          resultCount: keywordResults.length,
          analysisLength: analysis.length
        });
        
        console.log(`[KEYWORDS-BATCH-ADD] ✓ "${keyword}" erfolgreich verarbeitet`);
        
        // Kurze Pause zwischen API-Calls (um Rate Limits zu respektieren)
        if (i < keywords.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
      } catch (error) {
        console.error(`[KEYWORDS-BATCH-ADD] ✗ Fehler bei "${keyword}":`, error);
        results.failed.push({
          keyword: keyword,
          reason: error.message || 'Unbekannter Fehler',
          index: i,
          error: error.toString()
        });
      }
      
      results.processed++;
    }
    
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

    // Lösche aus zentraler DB
    toDelete.forEach(id => {
      delete summaryDB[id];
      deletedCount++;
    });
    await saveSummaryDatabase(summaryDB);

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

// Speichere zentrale Summary-Datenbank
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

// API: Summary speichern
app.post('/api/save-summary', async (req, res) => {
  try {
    const { lectureId, summary } = req.body;
    
    if (!lectureId || !summary) {
      return res.status(400).json({ error: 'lectureId und summary sind erforderlich' });
    }
    
    // Lade aktuelle DB
    const summaryDB = await loadSummaryDatabase();
    
    // Füge Summary hinzu
    summaryDB[lectureId] = {
      summary: summary.summary,
      headings: summary.headings || [],
      timestamp: new Date().toISOString()
    };
    
    // Speichere DB
    const success = await saveSummaryDatabase(summaryDB);
    
    if (success) {
      console.log(`Summary für ${lectureId} in zentrale DB gespeichert`);
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
      console.log(`   GET  /summary-database.json`);
      console.log(`   GET  /thematic-search-database.json`);
      console.log(`\n✓ System bereit!\n`);
    });
    
  } catch (error) {
    console.error('\n✗ Fehler beim Server-Start:', error);
    process.exit(1);
  }
}

startServer();
