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
        coOccurrences: {},
        lastUsed: new Date().toISOString()
      };
    }
    queryLog[term].count++;
    queryLog[term].lastUsed = new Date().toISOString();
    
    terms.forEach(otherTerm => {
      if (term !== otherTerm) {
        if (!queryLog[term].coOccurrences[otherTerm]) {
          queryLog[term].coOccurrences[otherTerm] = 0;
        }
        queryLog[term].coOccurrences[otherTerm]++;
      }
    });
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

function performThematicKeywordSearch(query, paragraphsFromLectures) {
  const terms = extractKeyTerms(query);
  
  if (terms.length === 0) {
    console.log('Keine Schlüsselbegriffe gefunden, verwende gesamte Query');
    return performKeywordSearch(query, paragraphsFromLectures);
  }
  
  // NEUE STRATEGIE: Suche zuerst nach Phrasen in Anführungszeichen
  const quotedPhrases = query.match(/"([^"]+)"|'([^']+)'/g);
  if (quotedPhrases && quotedPhrases.length > 0) {
    console.log('[DIREKTE PHRASENSUCHE] Verwende nur Phrasen in Anführungszeichen');
    
    const phraseResults = [];
    quotedPhrases.forEach(phrase => {
      const cleaned = phrase.replace(/['"]/g, '').trim().toLowerCase();
      console.log(`Suche direkt nach: "${cleaned}"`);
      const results = performKeywordSearch(cleaned, paragraphsFromLectures);
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
      const veryCommonWords = ['anthroposophie', 'bedeutung', 'geisteswissenschaft', 'welche', 'haben'];
      if (veryCommonWords.includes(term)) {
        console.log(`Überspringe zu generischen Begriff: "${term}"`);
        return;
      }
    }
    
    console.log(`Suche nach Begriff: "${term}"`);
    const termResults = performKeywordSearch(term, paragraphsFromLectures);
    
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
  
  const topResults = results.slice(0, 15);

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
    'allgemein': 2000,
    'genau': 3500,
    'ausführlich': 6000
  };
  
  const prompt = `Analysiere die folgenden Textstellen aus Rudolf Steiners Werk zur Frage: "${query}"

ANALYSE-TIEFE: ${depth}

QUELLENANGABEN:
- Verwende das Format (GAXXX/Y:index) nach jeder spezifischen Aussage
- Verfügbare Referenzen: ${availableRefs}
- Format: (GA###/lectureNum:index) - z.B. (GA052/7:n5x6ru) oder (GA068a/7:p5fg67)
- WICHTIG: Verwende immer das vollständige Format mit /Y:index
- Beispiel: "Steiner kritisiert Kants Erkenntnisgrenze (GA052/7:n5x6ru)."

VORGEHEN:
1. Identifiziere alle Textstellen mit relevanten Suchwörtern zur Themenanfrage
2. Vergleiche diese Textstellen auf Ähnlichkeit
3. Wähle möglichst viele nicht-redundante Textstellen aus
4. Entwickle eine eigene thematische Gliederung mit aussagekräftigen Zwischenüberschriften

INHALTLICHE PERSPEKTIVEN (als Orientierung, nicht als Überschriften verwenden):
Berücksichtige bei deiner Analyse verschiedene Perspektiven - wähle die relevanten aus:
- Sachliche und leibliche Aspekte (Was ist gemeint? Konkrete Phänomene, Substanzen, leibliche Prozesse)
- Funktionelle und physiologische Aspekte (Wie verhält es sich? Funktionen, Wirkungsweisen, Prozesse)
- Erlebnismäßige und seelisch-psychologische Aspekte (Welche Erfahrungen oder seelischen Prozesse?)
- Begriffliche und geistige Aspekte (Welche Ideen, Begriffe oder geistigen Prinzipien?)
- Methodische und erkenntnistheoretische Aspekte (Wie kann man das erkennen? Methoden, Erkenntnisstufen)
- Vergleich mit anderen Inhalten (Verhältnis zu anderen Wesen, Naturreichen, Konzepten)
- Entwicklung und Evolution (Entwicklungsprozesse, evolutionäre Aspekte)
- Besonderheiten und Sonstiges
- keine eigenen Bewertungen oder Interpretationen!

STRUKTURIERUNG:
- Erstelle eigene, thematisch passende Zwischenüberschriften (## Überschrift)
- Die Überschriften sollen den Inhalt des folgenden Abschnitts ankündigen
- NICHT die obigen Kategorienamen als Überschriften verwenden
- Beispiele für gute Überschriften: "Die Verwandlung der Sinneswahrnehmung", "Drei Stufen der Ich-Entwicklung", "Der Zusammenhang von Denken und Willen"

FORMATIERUNG:
- Verwende Markdown-Formatierung
- **Fette wichtige Schlagwörter** und **zentrale Aussagen**
- Gib nach jeder spezifischen Aussage die Quelle an: (GA###/Y:index) oder (GA###a/Y:index)
- Zitiere prägnante Stellen wörtlich in "Anführungszeichen" mit Quellenangabe
- Vermeide Redundanzen - jede Information nur einmal

WICHTIG:
- Wenn du relevante inhaltliche Bezüge findest, präsentiere diese direkt ohne einschränkende Vorbemerkungen
- Konzentriere dich auf das, was die Texte AUSSAGEN, nicht darauf, was sie nicht aussagen

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
        max_tokens: maxTokens[depth] || 8192,
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
  
  const refToDataMapping = {};
  
  results.forEach(result => {
    if (result.ID && result.index) {
      const cleanIndex = result.index.replace(/^\^/, '');
      
      const key1 = `${result.ID}:${result.index}`;
      const key2 = `${result.ID}:${cleanIndex}`;
      
      const mapping = {
        id: result.ID,
        index: cleanIndex,
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
  
  const gaPattern = /\(?(GA\d{3}[a-z]?\/\d+:\^?[a-z0-9]+)\)?/gi;
  
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
      const replacement = `<a href="#" class="ga-reference" data-id="${chunkData.id}" data-index="${chunkData.index}" data-file-name="${chunkData.fileName || ''}">${idPart}</a>`;
      
      linkedText = linkedText.substring(0, matchInfo.position) + 
                   replacement + 
                   linkedText.substring(matchInfo.position + matchInfo.fullMatch.length);
      
      linksCreated++;
    } else {
      console.warn(`Keine Daten für ${matchInfo.fullRef}`);
      console.warn(`Gesuchte Keys: ${matchInfo.fullRef} und ${refClean}`);
    }
  });
  
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
    const { query, depth = 'allgemein', limit = 30 } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Query erforderlich' });
    }
    
    const keywordResults = performThematicKeywordSearch(query, paragraphsFromLectures);
    
    if (keywordResults.length === 0) {
      return res.json({
        query: query,
        content: 'Keine relevanten Textstellen gefunden.',
        sources: []
      });
    }
    
    const rankedResults = applySemanticRanking(keywordResults, query);
    const topResults = rankedResults.slice(0, limit);
    
    // Query-Tracking
    trackQueryTerms(query, topResults.length);
    
    const analysis = await generateAnalysis(query, topResults, depth);
    
    res.json({
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
    });
    
  } catch (error) {
    console.error('Thematische Suche Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/full-lecture/:lectureId', (req, res) => {
  try {
    const lectureId = req.params.lectureId;
    
    console.log(`Vortrag-Anfrage: ${lectureId}`);
    
    const lectureIdLower = lectureId.toLowerCase();
    let lecture = fullLectures[lectureId] || fullLectures[lectureIdLower];
    
    if (!lecture) {
      const foundKey = Object.keys(fullLectures).find(key => 
        key.toLowerCase() === lectureIdLower
      );
      if (foundKey) {
        lecture = fullLectures[foundKey];
      }
    }
    
    if (!lecture) {
      console.error(`   Nicht gefunden: ${lectureId}`);
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}`,
        available: Object.keys(fullLectures).slice(0, 10)
      });
    }
    
    console.log(`   Gefunden: ${lectureId}`);
    
    res.json({
      lecture: lecture,
      paragraphCount: lecture.paragraphs?.length || 0,
      hasIndices: lecture.paragraphs?.some(p => p.index) || false
    });
    
  } catch (error) {
    console.error('Vortrag-Abruf Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/full-lecture/:gaNumber/:lectureNum', (req, res) => {
  try {
    const lectureId = `${req.params.gaNumber}/${req.params.lectureNum}`;
    
    console.log(`Vortrag-Anfrage: ${lectureId}`);
    
    const lectureIdLower = lectureId.toLowerCase();
    let lecture = fullLectures[lectureId] || fullLectures[lectureIdLower];
    
    if (!lecture) {
      const foundKey = Object.keys(fullLectures).find(key => 
        key.toLowerCase() === lectureIdLower
      );
      if (foundKey) {
        lecture = fullLectures[foundKey];
      }
    }
    
    if (!lecture) {
      console.error(`   Nicht gefunden: ${lectureId}`);
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}`,
        available: Object.keys(fullLectures).filter(k => k.startsWith(req.params.gaNumber)).slice(0, 10)
      });
    }
    
    console.log(`   Gefunden: ${lectureId}`);
    
    res.json({
      lecture: lecture,
      paragraphCount: lecture.paragraphs?.length || 0,
      hasIndices: lecture.paragraphs?.some(p => p.index) || false
    });
    
  } catch (error) {
    console.error('Vortrag-Abruf Fehler:', error);
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
    
    try {
      // Lese alle .json Dateien im keywords/ Ordner
      const files = await fs.readdir(keywordsPath);
      const jsonFiles = files.filter(file => file.endsWith('.json'));
      
      for (const fileName of jsonFiles) {
        try {
          const filePath = path.join(keywordsPath, fileName);
          const fileContent = await fs.readFile(filePath, 'utf8');
          const data = JSON.parse(fileContent);
          
          // Konvertiere in einheitliches Format
          if (data.keywords && data.text) {
            const keywordEntry = {
              keyword: data.keywords.Keyword || 'Unbekannt',
              alphabetical: data.keywords.Alphabetical || data.keywords.Keyword?.charAt(0).toUpperCase() || 'U',
              text: data.text,
              gaReferences: extractGAReferencesFromText(data.text)
            };
            
            allKeywords.push(keywordEntry);
          }
        } catch (error) {
          console.warn(`[KEYWORDS-API] Fehler beim Verarbeiten von ${fileName}:`, error.message);
        }
      }
      
      console.log(`[KEYWORDS-API] ${allKeywords.length} Schlagwörter erfolgreich geladen`);
      
    } catch (error) {
      console.log('[KEYWORDS-API] keywords/ Ordner nicht gefunden, verwende Fallback');
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
});

// ============================================================================
// ZENTRALE SUMMARY-DATENBANK
// ============================================================================

const SUMMARY_DB_FILE = path.join(__dirname, 'summary-database.json');

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
// SERVER START
// ============================================================================

async function startServer() {
  try {
    console.log('\n========================================');
    console.log('Initialisiere Server...');
    console.log('========================================');
    
await loadSynonyms();
await loadFullLectures();

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
    
    console.log('\n========================================');
    console.log('DATEN GELADEN:');
    console.log(`  ${paragraphsFromLectures.length} Absätze`);
    console.log(`  ${Object.keys(fullLectures).length} Vorträge`);
    console.log(`  ${Object.keys(synonyms).length} Synonym-Gruppen`);
    console.log(`  ${Object.keys(queryLog).length} Query-Log Einträge`);
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
      console.log(`   GET  /summary-database.json`);
      console.log(`\n✓ System bereit!\n`);
    });
    
  } catch (error) {
    console.error('\n✗ Fehler beim Server-Start:', error);
    process.exit(1);
  }
}

startServer();