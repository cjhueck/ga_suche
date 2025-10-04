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
let chunks = [];
let fullLectures = {};
let synonyms = {};
let summaryCache = {};
let gaOverviewCache = {}; // NEU: Cache für GA-Übersichten

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
// DATEN LADEN
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

async function loadSummaryCache() {
  try {
    const summaryPath = path.join(__dirname, 'lecture-summaries.json');
    
    try {
      const data = await fs.readFile(summaryPath, 'utf8');
      summaryCache = JSON.parse(data);
      console.log(`Zusammenfassungen geladen: ${Object.keys(summaryCache).length} Vorträge`);
    } catch {
      summaryCache = {};
      console.log('Keine gespeicherten Zusammenfassungen gefunden - leerer Cache erstellt');
    }
    
    return summaryCache;
    
  } catch (error) {
    console.error('Fehler beim Laden des Summary-Cache:', error.message);
    summaryCache = {};
    return summaryCache;
  }
}

async function saveSummaryCache() {
  try {
    const summaryPath = path.join(__dirname, 'lecture-summaries.json');
    console.log('\n=== SPEICHERE CACHE ===');
    console.log('Pfad:', summaryPath);
    console.log('Anzahl Einträge im Cache:', Object.keys(summaryCache).length);
    console.log('Erste 5 Keys:', Object.keys(summaryCache).slice(0, 5));
    
    // Prüfe ob Verzeichnis beschreibbar ist
    const testFile = path.join(__dirname, '.write-test');
    try {
      await fs.writeFile(testFile, 'test', 'utf8');
      await fs.unlink(testFile);
      console.log('✓ Verzeichnis ist beschreibbar');
    } catch (writeError) {
      console.error('✗ Verzeichnis nicht beschreibbar:', writeError.message);
      throw writeError;
    }
    
    const jsonString = JSON.stringify(summaryCache, null, 2);
    console.log('JSON Größe:', (jsonString.length / 1024).toFixed(2), 'KB');
    
    await fs.writeFile(summaryPath, jsonString, 'utf8');
    
    console.log('✓ Datei erfolgreich geschrieben!');
    
    // Verifiziere das Schreiben
    const fileStats = await fs.stat(summaryPath);
    console.log('✓ Datei existiert, Größe:', (fileStats.size / 1024).toFixed(2), 'KB');
    console.log('======================\n');
    
    return true;
  } catch (error) {
    console.error('\n✗ FEHLER beim Speichern des Cache:');
    console.error('Error Type:', error.constructor.name);
    console.error('Error Message:', error.message);
    console.error('Stack:', error.stack);
    console.error('======================\n');
    return false;
  }
}
async function invalidateGAOverviewCache(lectureId) {
  try {
    const rawGA = lectureId.split('/')[0];  // z. B. "GA051"
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
// NEU: GA-ÜBERSICHTS-FUNKTIONEN
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

function generateGAOverview(gaNumber) {
  // Filtere alle Vorträge dieses GA-Bandes
  const lectures = Object.values(fullLectures)
    .filter(lec => lec.gaNumber === gaNumber)
    .sort((a, b) => {
      // Sortiere nach Vortragsnummer
      const numA = parseInt(a.lectureNumber) || 0;
      const numB = parseInt(b.lectureNumber) || 0;
      return numA - numB;
    });
  
  if (lectures.length === 0) {
    return null;
  }
  
  // Hole Titel des GA-Bandes vom ersten Vortrag
  const gaTitle = lectures[0].gaTitle || gaNumber;
  
  // Erstelle Übersicht mit Vorträgen und (falls vorhanden) Zusammenfassungen
  const overview = {
    gaNumber: gaNumber,
    gaTitle: gaTitle,
    lectureCount: lectures.length,
    lectures: lectures.map(lec => {
      const lectureId = lec.ID;
      const cached = summaryCache[lectureId];
      
      // Extrahiere summary-Text aus dem Cache
      let summaryText = null;
      if (cached) {
        if (typeof cached === 'string') {
          // Altes Format: direkt ein String
          summaryText = cached;
        } else if (typeof cached === 'object' && cached.summary) {
          // Neues Format: Objekt mit .summary Property
          summaryText = cached.summary;
        }
      }
      
      return {
        lectureNumber: lec.lectureNumber,
        ID: lectureId,
        title: lec.title,
        fileName: lec.fileName,
        location: lec.location,
        date: formatDate(lec.date),
        summary: summaryText  // Nur der Text, nicht das Objekt
      };
    })
  };
  
  return overview;
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

function performKeywordSearch(query, chunks) {
  const expandedTerms = expandQueryWithSynonyms(query);
  const results = [];
  
  console.log(`Suche nach: ${expandedTerms.slice(0, 5).join(' | ')}${expandedTerms.length > 5 ? '...' : ''}`);
  
  chunks.forEach(chunk => {
    const content = (chunk.content || '').toLowerCase();
    const title = (chunk.title || '').toLowerCase();
    const chunkId = (chunk.ID || '').toLowerCase();
    
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
      while ((pos = chunkId.indexOf(termLower, pos)) !== -1) {
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
        ...chunk,
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
    'zwischen', 'bei', 'nach', 'für', 'mit', 'aus', 'über', 'sich', 'zur'
  ];
  
  const words = query.toLowerCase()
    .replace(/[.,;:!?]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 3 && !stopWords.includes(word));
  
  console.log(`Extrahierte Schlüsselbegriffe aus "${query}":`, words);
  
  return words;
}

function performThematicKeywordSearch(query, chunks) {
  const terms = extractKeyTerms(query);
  
  if (terms.length === 0) {
    console.log('Keine Schlüsselbegriffe gefunden, verwende gesamte Query');
    return performKeywordSearch(query, chunks);
  }
  
  const allResults = new Map();
  
  terms.forEach(term => {
    console.log(`Suche nach Begriff: "${term}"`);
    const termResults = performKeywordSearch(term, chunks);
    
    termResults.forEach(result => {
      const key = `${result.ID}-${result.index}`;
      
      if (!allResults.has(key)) {
        allResults.set(key, {
          ...result,
          matchedTerms: result.matchedTerms,
          keywordScore: result.keywordScore
        });
      } else {
        const existing = allResults.get(key);
        existing.keywordScore += result.keywordScore * 0.5;
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
    const keywordResults = performKeywordSearch(query, chunks);
    
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
  
  const prompt = `Analysieren Sie die folgenden Textstellen aus Rudolf Steiners Werk zur Frage: "${query}"

ANALYSE-TIEFE: ${depth}

QUELLENANGABEN:
- Verwenden Sie das Format GA###/##:index nach jeder spezifischen Aussage
- Verfügbare Referenzen: ${availableRefs}
- Format: GA###/##:index (z.B. GA052/7:n5x6ru)
- WICHTIG: Verwenden Sie immer das vollständige Format mit :index
- Beispiel: "Steiner kritisiert Kants Erkenntnisgrenze (GA052/7:n5x6ru)."

ANWEISUNGEN:
- Arbeiten Sie nur mit den gegebenen Textpassagen
- Fassen Sie thematische Verbindungen zusammen
- Strukturieren Sie nach wichtigsten Aspekten
- Verwenden Sie die vollständigen Referenzen GA###/##:index für jede spezifische Aussage

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
      
      // Erstelle mehrere mögliche Keys
      const key1 = `${result.ID}:${result.index}`;        // z.B. GA052/7:^abc123
      const key2 = `${result.ID}:${cleanIndex}`;          // z.B. GA052/7:abc123
      
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
  
  // Probiere auch lowercase Version
  const refLower = matchInfo.fullRef.toLowerCase();
  const refCleanLower = refClean.toLowerCase();
  
  const chunkData = refToDataMapping[matchInfo.fullRef] || 
                    refToDataMapping[refClean] ||
                    refToDataMapping[refLower] ||
                    refToDataMapping[refCleanLower];
    
    if (chunkData) {
      const [idPart] = matchInfo.fullRef.split(':');
      const replacement = `<a href="#" class="ga-reference" data-id="${chunkData.id}" data-index="${chunkData.index}">${idPart}</a>`;
      
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
    
    // Prüfe ob bereits im Cache (außer wenn Regenerierung erzwungen wird)
    if (!forceRegenerate && summaryCache[lectureId]) {
      console.log(`  ✓ Cache-Hit für ${lectureId}`);
      const cachedData = summaryCache[lectureId];
      
      // NEU: Detailliertes Logging für Cache-Hit
      console.log('  → Typ der cachedData:', typeof cachedData);
      console.log('  → cachedData ist Array?', Array.isArray(cachedData));
      if (typeof cachedData === 'object' && cachedData !== null) {
        console.log('  → cachedData Keys:', Object.keys(cachedData));
        console.log('  → cachedData.summary vorhanden?', !!cachedData.summary);
        console.log('  → cachedData.headings vorhanden?', !!cachedData.headings);
        console.log('  → cachedData.headings ist Array?', Array.isArray(cachedData.headings));
        console.log('  → cachedData.headings Länge:', cachedData.headings?.length);
        console.log('  → Erste 3 headings:', JSON.stringify(cachedData.headings?.slice(0, 3), null, 2));
      }
      
      // Unterstütze beide Formate: altes (string) und neues (object)
      const responseData = typeof cachedData === 'string' 
        ? { summary: cachedData, headings: [] }
        : cachedData;
      
      console.log(`  → Response Headings Länge: ${responseData.headings?.length || 0}`);
      
      return res.json({
        lectureId: lectureId,
        summary: responseData.summary,
        headings: responseData.headings || [],
        fromCache: true,
        paragraphCount: fullLectures[lectureId]?.paragraphs?.length || 0
      });
    }
    
    // Hole Vortrag aus bereits geladenen Daten
    const lecture = fullLectures[lectureId];
    
    if (!lecture) {
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}`,
        available: Object.keys(fullLectures).slice(0, 10)
      });
    }
    
    console.log(`  → Generiere neue Zusammenfassung...`);
    const summaryData = await generateLectureSummary(lecture);
    
    // Speichere im Cache
    console.log(`  → Speichere in Cache (Vor): ${Object.keys(summaryCache).length} Einträge`);
    summaryCache[lectureId] = summaryData;
    console.log(`  → Speichere in Cache (Nach): ${Object.keys(summaryCache).length} Einträge`);
    console.log(`  → Headings im neuen Eintrag: ${summaryData.headings?.length || 0}`);
    
    const saved = await saveSummaryCache();
    console.log(`  → saveSummaryCache() Rückgabe: ${saved}`);
    
    if (saved) {
      await invalidateGAOverviewCache(lectureId);
      console.log(`  ✓ Zusammenfassung erstellt und gespeichert`);
    } else {
      console.log(`  ✗ Zusammenfassung erstellt aber NICHT gespeichert!`);
    }
    
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

async function generateLectureSummary(lecture) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  
  if (!claudeApiKey) {
    console.log('Kein Claude API Key - verwende Fallback-Zusammenfassung');
    return generateFallbackSummary(lecture);
  }
  
  // Kombiniere alle Paragraphen MIT ihren Original-Indizes
  const fullText = lecture.paragraphs
    .map((p, idx) => {
      const content = p.content || p.text || '';
      const paraIndex = p.index || `para_${idx}`;
      return `[Index: ${paraIndex}]\n${content}`;
    })
    .filter(text => text.trim().length > 0)
    .join('\n\n');
  
  // Token-Schätzung: ~4 Zeichen = 1 Token
  const estimatedTokens = fullText.length / 4;
  console.log(`Vortrag: ${lecture.ID}, Paragraphen: ${lecture.paragraphs.length}, Geschätzte Tokens: ${Math.round(estimatedTokens)}`);
  
  // Wenn zu lang (>180k tokens), nur Zusammenfassung ohne Überschriften
  let textToSummarize = fullText;
  let headingsDisabled = false;
  
  if (estimatedTokens > 180000) {
    console.log('Vortrag zu lang (>180k tokens) - Überschriften deaktiviert, nur Zusammenfassung');
    headingsDisabled = true;
    // Nimm erste und letzte 90k tokens (ca. 360k Zeichen) für Zusammenfassung
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
    
    // Parse JSON response
    try {
      // Entferne mögliche Markdown-Code-Blocks
      summaryText = summaryText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const summaryData = JSON.parse(summaryText);
      
      // Validiere Struktur
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
      
      // Fallback: Gib Rohantwort als einfache Zusammenfassung zurück
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

app.get('/debug/status', (req, res) => {
  res.json({
    server: 'hybrid-search-unified',
    status: 'running',
    chunksLoaded: chunks.length,
    lecturesLoaded: Object.keys(fullLectures).length,
    synonymGroups: Object.keys(synonyms).length,
    summariesCached: Object.keys(summaryCache).length,
    gaOverviewsCached: Object.keys(gaOverviewCache).length,
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
    
    const keywordResults = performThematicKeywordSearch(query, chunks);
    
    if (keywordResults.length === 0) {
      return res.json({
        query: query,
        content: 'Keine relevanten Textstellen gefunden.',
        sources: []
      });
    }
    
    const rankedResults = applySemanticRanking(keywordResults, query);
    const topResults = rankedResults.slice(0, limit);
    
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
    
    // Suche case-insensitive
    const lectureIdLower = lectureId.toLowerCase();
    let lecture = fullLectures[lectureId] || fullLectures[lectureIdLower];
    
    // Falls nicht gefunden, suche in allen Keys (case-insensitive)
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
    
    // Suche case-insensitive
    const lectureIdLower = lectureId.toLowerCase();
    let lecture = fullLectures[lectureId] || fullLectures[lectureIdLower];
    
    // Falls nicht gefunden, suche in allen Keys (case-insensitive)
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

// Liste aller verfügbaren GA-Bände basierend auf JSON-Inhalten
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

// NEU: GA-Übersichtsseite abrufen
app.get('/api/ga-overview/:gaNumber', async (req, res) => {
  try {
    const gaNumberOriginal = req.params.gaNumber;     // z.B. "GA068a"
    const gaKey = gaNumberOriginal.toLowerCase();     // Cache-Key
    const forceRefresh = req.query.refresh === 'true';

    console.log(`[GA-OVERVIEW] Anfrage für ${gaNumberOriginal} (refresh: ${forceRefresh})`);

    if (!forceRefresh && gaOverviewCache[gaKey]) {
      console.log(`[GA-OVERVIEW] Cache-Hit für ${gaKey}`);
      return res.json(gaOverviewCache[gaKey]);
    }

    // WICHTIG: Hier die Original-Schreibweise benutzen,
    // weil generateGAOverview streng vergleicht (===)
    const overview = generateGAOverview(gaNumberOriginal);

    if (!overview) {
      return res.status(404).json({ error: `Keine Vorträge gefunden für ${gaNumberOriginal}` });
    }

    gaOverviewCache[gaKey] = overview;
    await saveGAOverviewCache();

    console.log(`[GA-OVERVIEW] Übersicht ${forceRefresh ? 'aktualisiert' : 'generiert'} für ${gaKey}: ${overview.lectureCount} Vorträge`);
    res.json(overview);

  } catch (error) {
    console.error('[GA-OVERVIEW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// GA-Overview-Map ausliefern
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
// SERVER START
// ============================================================================

async function startServer() {
  try {
    console.log('\n========================================');
    console.log('Initialisiere Server...');
    console.log('========================================');
    
    await loadChunks();
    await loadSynonyms();
    await loadFullLectures();
    await loadSummaryCache();
    await loadGAOverviewCache();
    
    console.log('\n========================================');
    console.log('DATEN GELADEN:');
    console.log(`  ${chunks.length} Chunks`);
    console.log(`  ${Object.keys(fullLectures).length} Vorträge`);
    console.log(`  ${Object.keys(synonyms).length} Synonym-Gruppen`);
    console.log(`  ${Object.keys(summaryCache).length} Zusammenfassungen im Cache`);
    console.log(`  ${Object.keys(gaOverviewCache).length} GA-Übersichten im Cache`);
    console.log('========================================');
    
    app.listen(PORT, () => {
      console.log(`\n✓ Server läuft auf http://localhost:${PORT}`);
      console.log(`\nVerfügbare Endpoints:`);
      console.log(`   GET  /debug/status`);
      console.log(`   POST /api/hybrid-search`);
      console.log(`   POST /api/fulltext-search`);
      console.log(`   POST /api/thematic-hybrid-search`);
      console.log(`   POST /api/summarize-lecture`);
      console.log(`   GET  /api/full-lecture/:lectureId`);
      console.log(`   GET  /api/full-lecture/:gaNumber/:lectureNum`);
      console.log(`   GET  /api/lectures/list`);
      console.log(`   GET  /api/available-ga`);
      console.log(`   GET  /api/ga-overview/:gaNumber`);
      console.log(`   GET  /ga-overview-map.json`);
      console.log(`\n✓ System bereit!\n`);
    });
    
  } catch (error) {
    console.error('\n✗ Fehler beim Server-Start:', error);
    process.exit(1);
  }
}

startServer();