// hybrid-search-server-unified.js - Vereinheitlichtes System mit GA/Vortrag IDs
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const fsSync = require('fs'); // Für synchrone Operationen (Seed-Keywords laden)
const path = require('path');
const { getProviderForTask, getSpecificProvider, generateCompletionWithFallback, showRateLimitStatus, isProviderRateLimited } = require('./llm-providers'); // LLM Provider Abstraction

const app = express();
const PORT = process.env.PORT || 3003; // Render setzt PORT-Umgebungsvariable

// Middleware - WICHTIG: Reihenfolge beachten!
app.use(cors());
app.use(express.json({ limit: '10mb' })); // Limit für JSON-Body

// Trust Proxy für Render (wichtig für korrekte IP-Erkennung)
app.set('trust proxy', 1);

// SICHERHEIT: Einfaches Rate Limiting (TEMPORÄR DEAKTIVIERT ZUM TESTEN)
// TODO: Wieder aktivieren nach erfolgreichem Test
/*
const rateLimitMap = new Map();
const RATE_LIMIT_WINDOW = 15 * 60 * 1000; // 15 Minuten
const RATE_LIMIT_MAX = 500; // Max 500 Requests pro IP pro 15 Minuten (sehr großzügig)

app.use((req, res, next) => {
  // IP-Erkennung: Unterstützt Proxy-Header (wichtig für Render)
  const ip = req.headers['x-forwarded-for']?.split(',')[0]?.trim() 
    || req.headers['x-real-ip'] 
    || req.ip 
    || req.connection.remoteAddress 
    || 'unknown';
  const now = Date.now();
  
  if (!rateLimitMap.has(ip)) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
    return next();
  }
  
  const limit = rateLimitMap.get(ip);
  
  // Reset wenn Zeitfenster abgelaufen
  if (now > limit.resetTime) {
    limit.count = 1;
    limit.resetTime = now + RATE_LIMIT_WINDOW;
    return next();
  }
  
  // Prüfe Limit
  if (limit.count >= RATE_LIMIT_MAX) {
    console.warn(`[RATE-LIMIT] Limit erreicht für IP: ${ip}`);
    return res.status(429).json({ error: 'Too many requests, please try again later' });
  }
  
  limit.count++;
  next();
  
  // Cleanup alte Einträge (alle 5 Minuten)
  if (Math.random() < 0.01) { // 1% Chance bei jedem Request
    for (const [key, value] of rateLimitMap.entries()) {
      if (now > value.resetTime) {
        rateLimitMap.delete(key);
      }
    }
  }
});
*/

// ============================================================================
// SICHERHEIT: Input-Validierung Helper-Funktionen
// ============================================================================
// DEAKTIVIERT - verursachte Probleme mit Timeline-Suche und anderen Features
// TODO: Später wieder aktivieren mit weniger strikten Validierungen

/*
function validateLectureId(lectureId) {
  if (!lectureId || typeof lectureId !== 'string') return false;
  return /^GA\d{3}(\/\d{1,3})?$/.test(lectureId);
}

function validateGANumber(gaNumber) {
  if (!gaNumber || typeof gaNumber !== 'string') return false;
  const normalized = gaNumber.toUpperCase().replace(/^GA/, '');
  return /^\d{3}$/.test(normalized);
}

function sanitizeString(input, maxLength = 1000) {
  if (typeof input !== 'string') return '';
  return input
    .replace(/[<>]/g, '')
    .substring(0, maxLength)
    .trim();
}
*/

// API: Bilder aus GA-Ordnern servieren (für Bücher) - MUSS VOR express.static kommen!
app.get('/assets/*', async (req, res) => {
  try {
    // Extrahiere den Pfad nach /assets/
    const imagePath = req.path.replace('/assets/', ''); // z.B. "GA046-Nachgelassene Abhandlungen...img-0.png"
    
    // Decode URL-encoded Zeichen
    const decodedPath = decodeURIComponent(imagePath);
    
    // Finde den GA-Ordner basierend auf dem Bildpfad
    const gaMatch = decodedPath.match(/^(GA\d{3}[a-z]?)/i);
    if (!gaMatch) {
      return res.status(404).json({ error: 'GA-Nummer nicht gefunden' });
    }
    
    const gaNumber = gaMatch[1];
    
    const steinerGADir = path.join(__dirname, 'Steiner_GA');
    
    // Suche nach dem GA-Ordner
    const files = await fs.readdir(steinerGADir);
    const gaFolder = files.find(f => {
      const stat = fsSync.statSync(path.join(steinerGADir, f));
      return stat.isDirectory() && f.startsWith(gaNumber);
    });
    
    if (!gaFolder) {
      return res.status(404).json({ error: `GA-Ordner nicht gefunden: ${gaNumber}` });
    }
    
    
    // Konstruiere den vollständigen Pfad zum Bild
    let fullImagePath = path.join(steinerGADir, gaFolder, 'assets', decodedPath);
    
    // Prüfe ob Datei existiert
    if (!fsSync.existsSync(fullImagePath)) {
      
      // Falls .png nicht gefunden, versuche .jpeg oder .jpg
      if (decodedPath.endsWith('.png')) {
        const jpegPath = decodedPath.replace(/\.png$/i, '.jpeg');
        const jpgPath = decodedPath.replace(/\.png$/i, '.jpg');
        
        const jpegFullPath = path.join(steinerGADir, gaFolder, 'assets', jpegPath);
        const jpgFullPath = path.join(steinerGADir, gaFolder, 'assets', jpgPath);
        
        if (fsSync.existsSync(jpegFullPath)) {
          fullImagePath = jpegFullPath;
        } else if (fsSync.existsSync(jpgFullPath)) {
          fullImagePath = jpgFullPath;
        } else {
          const assetsDir = path.join(steinerGADir, gaFolder, 'assets');
          if (fsSync.existsSync(assetsDir)) {
            const assetsFiles = fsSync.readdirSync(assetsDir);
          }
          return res.status(404).json({ error: 'Bild nicht gefunden' });
        }
      } else {
        const assetsDir = path.join(steinerGADir, gaFolder, 'assets');
        if (fsSync.existsSync(assetsDir)) {
          const assetsFiles = fsSync.readdirSync(assetsDir);
        }
        return res.status(404).json({ error: 'Bild nicht gefunden' });
      }
    }
    
    // Serviere das Bild
    res.sendFile(fullImagePath);
  } catch (error) {
    console.error('[IMAGES-ASSETS] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Statische Dateien aus dem system Ordner bereitstellen
app.use('/system', express.static(path.join(__dirname, 'system')));

// Statische HTML-Dateien aus dem Hauptverzeichnis bereitstellen
app.use(express.static(__dirname));

// Logging Middleware für alle Requests
app.use((req, res, next) => {
  next();
});

// Global variables
let chunks = []; // WIRD NICHT MEHR VERWENDET
let paragraphsFromLectures = []; // NEU
let fullLectures = {};
let fullBooks = {}; // GA-Schriften (GA001-GA046)

// Hilfsfunktion: Konvertiert Bücher in Paragraphs-Format (für Suche)
function convertBookToParagraphs(book) {
  if (!book || !book.content) return [];
  
  const paragraphs = [];
  const content = book.content || '';
  
  // Teile Content in Zeilen auf
  const lines = content.split('\n');
  let currentParagraph = '';
  let currentIndex = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Suche nach Index am Ende der Zeile (Format: ^abc123)
    const indexMatch = line.match(/\s+(\^[a-z0-9]+)\s*$/);
    
    if (indexMatch) {
      // Index gefunden - speichere aktuellen Paragraph
      const index = indexMatch[1];
      const lineWithoutIndex = line.replace(/\s+\^[a-z0-9]+\s*$/, '').trim();
      
      if (currentParagraph || lineWithoutIndex) {
        paragraphs.push({
          index: index,
          content: (currentParagraph + (currentParagraph ? ' ' : '') + lineWithoutIndex).trim(),
          text: (currentParagraph + (currentParagraph ? ' ' : '') + lineWithoutIndex).trim()
        });
      }
      
      currentParagraph = '';
      currentIndex = index;
    } else {
      // Kein Index - füge zur aktuellen Paragraph hinzu
      if (line.trim()) {
        currentParagraph += (currentParagraph ? ' ' : '') + line.trim();
      }
    }
  }
  
  // Füge letzten Paragraph hinzu, falls vorhanden
  if (currentParagraph.trim()) {
    paragraphs.push({
      index: currentIndex || null,
      content: currentParagraph.trim(),
      text: currentParagraph.trim()
    });
  }
  
  // Wenn keine Indizes gefunden wurden, teile nach Absätzen (doppelte Zeilenumbrüche)
  if (paragraphs.length === 0) {
    const sections = content.split(/\n\n+/);
    sections.forEach((section, idx) => {
      if (section.trim()) {
        paragraphs.push({
          index: null,
          content: section.trim(),
          text: section.trim()
        });
      }
    });
  }
  
  return paragraphs;
}

// Hilfsfunktion: Erstellt Paragraph-Objekte aus Büchern für Suche
function getBookParagraphsForSearch(book) {
  const paragraphs = convertBookToParagraphs(book);
  
  return paragraphs.map((para, idx) => ({
    ID: book.ID || book.gaNumber,
    title: book.title || book.fileName || book.ID,
    fileName: book.fileName || book.title || book.ID,
    gaNumber: book.gaNumber || book.ID,
    paragraphIndex: idx,
    index: para.index,
    content: para.content,
    text: para.text || para.content,
    isBook: true
  }));
}
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
  const allLectureFiles = files.filter(f => lecturePattern.test(f));
  
  // Filtere alte, spezifische Dateien heraus, die bereits in großen part-Dateien enthalten sind
  // Beispiel: steiner-full-lectures-130-159*.json und steiner-full-lectures-261-261.json
  // sind bereits in steiner-full-lectures-051-354-part*.json enthalten
  const hasLargeRange = allLectureFiles.some(f => f.includes('051-354'));
  
  const lectureFiles = allLectureFiles.filter(file => {
    if (!hasLargeRange) return true; // Wenn keine große Range existiert, lade alle
    
    // Überspringe spezifische Dateien, die in der großen Range enthalten sind
    const match = file.match(/steiner-full-lectures-(\d{3}[a-z]?)-(\d{3}[a-z]?)/i);
    if (!match) return true;
    
    const start = parseInt(match[1]);
    const end = parseInt(match[2]);
    
    // Wenn die große Range (051-354) existiert, überspringe kleinere Überschneidungen
    if (start >= 51 && end <= 354 && file.includes('051-354')) {
      return true; // Das ist die große Datei selbst
    }
    
    if (start >= 51 && end <= 354 && !file.includes('051-354')) {
      // Kleine Datei innerhalb der großen Range - überspringen
      return false;
    }
    
    return true; // Alle anderen Dateien behalten
  });
  
  // Suche nach steiner-books-XXX-YYY*.json oder steiner_books_XXX-YYY*.json
  // Pattern: steiner[-_]books[-_](\d{3}[a-z]?)[-_](\d{3}[a-z]?).*\.json
  // WICHTIG: Muss auch steiner-books-001-003.json matchen (ohne part-Nummer)
  // UND auch steiner-books-040a-040a.json (mit Suffix)
  const bookPattern = /^steiner[-_]books[-_](\d{3}[a-z]?)[-_](\d{3}[a-z]?).*\.json$/i;
  const bookFiles = files.filter(f => {
    const matches = bookPattern.test(f);
    if (!matches && f.includes('steiner') && f.includes('books') && f.endsWith('.json')) {
    }
    return matches;
  });
  
  // DEBUG: Zeige alle gefundenen Books-Dateien
  if (bookFiles.length > 0) {
  } else {
    console.warn('[DEBUG] KEINE Books-Dateien gefunden! Verfügbare Dateien mit "books":', 
      files.filter(f => f.includes('books') && f.endsWith('.json')));
  }
  
  
  return {
    searchFiles,
    lectureFiles,
    bookFiles
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
    
    
    for (const fileName of searchFiles) {
      const jsonPath = path.join(__dirname, fileName);
      
      const data = await fs.readFile(jsonPath, 'utf8');
      const parsed = JSON.parse(data);
      
      const fileChunks = parsed.chunks || [];
      chunks = chunks.concat(fileChunks);
      
    }
    
    return chunks;
    
  } catch (error) {
    console.error('Fehler beim Laden der Chunks:', error.message);
    throw error;
  }
}

// Bilder-Datenbank
let steinerImages = {};

async function loadSteinerImages() {
  try {
    const singleFilePath = path.join(__dirname, 'steiner-images.json');
    
    // Versuche zuerst Einzeldatei zu laden
    if (fsSync.existsSync(singleFilePath)) {
      const data = await fs.readFile(singleFilePath, 'utf8');
      steinerImages = JSON.parse(data);
      
      const totalImages = Object.values(steinerImages).reduce((sum, imgs) => sum + imgs.length, 0);
      
      return steinerImages;
    }
    
    // Falls keine Einzeldatei: Suche nach Part-Dateien
    const files = await fs.readdir(__dirname);
    const partFiles = files
      .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
      .sort();
    
    if (partFiles.length === 0) {
      return {};
    }
    
    // Lade alle Part-Dateien
    
    steinerImages = {};
    let totalImages = 0;
    
    for (const partFile of partFiles) {
      const partPath = path.join(__dirname, partFile);
      const data = await fs.readFile(partPath, 'utf8');
      const partData = JSON.parse(data);
      
      // Prüfe ob Array oder Objekt
      if (Array.isArray(partData)) {
        // Konvertiere Array zu Objekt gruppiert nach lectureId
        partData.forEach(img => {
          if (!steinerImages[img.lectureId]) {
            steinerImages[img.lectureId] = [];
          }
          steinerImages[img.lectureId].push(img);
          totalImages++;
        });
      } else {
        // Objekt-Format (legacy)
        Object.assign(steinerImages, partData);
        const partImages = Object.values(partData).reduce((sum, imgs) => sum + imgs.length, 0);
        totalImages += partImages;
      }
    }
    
    
    return steinerImages;
  } catch (error) {
    console.error('Fehler beim Laden von steiner-images:', error.message);
    return {};
  }
}

async function loadFullLectures() {
  try {
    const { lectureFiles } = await findDataFiles();
    
    if (lectureFiles.length === 0) {
      console.error('❌ FEHLER: Keine steiner-full-lectures-XXX-YYY*.json Dateien gefunden!');
      console.error('   Verfügbare Dateien:', (await fs.readdir(__dirname)).filter(f => f.includes('lectures') && f.endsWith('.json')));
      return {};
    }
    
    
    let totalLectures = 0;
    for (const fileName of lectureFiles) {
      const jsonPath = path.join(__dirname, fileName);
      
      try {
        const data = await fs.readFile(jsonPath, 'utf8');
        const parsed = JSON.parse(data);
        
        const lectures = parsed.lectures || [];
        
        if (lectures.length === 0) {
          console.warn(`    ⚠️  Warnung: ${fileName} enthält keine Vorträge!`);
        }
        
        lectures.forEach(lecture => {
          if (lecture.ID) {
            // Prüfe auf Duplikate - nur warnen wenn wirklich unterschiedlich
            if (fullLectures[lecture.ID]) {
              const existing = fullLectures[lecture.ID];
              const existingFileName = existing.fileName || 'unbekannt';
              const newFileName = lecture.fileName || 'unbekannt';
              
              // Nur warnen wenn Dateinamen unterschiedlich sind (echtes Duplikat)
              if (existingFileName !== newFileName) {
                console.warn(`    ⚠️  Duplikat gefunden: ${lecture.ID} wird überschrieben`);
                console.warn(`        Alte Datei: ${existingFileName}`);
                console.warn(`        Neue Datei: ${newFileName}`);
              }
              // Ansonsten ist es derselbe Vortrag aus einer anderen Part-Datei (normal bei Chunks)
            }
            fullLectures[lecture.ID] = lecture;
            totalLectures++;
          } else {
            console.warn(`    ⚠️  Vortrag ohne ID übersprungen:`, Object.keys(lecture));
          }
        });
        
      } catch (fileError) {
        console.error(`    ❌ Fehler beim Laden von ${fileName}:`, fileError.message);
      }
    }
    
    const uniqueLecturesCount = Object.keys(fullLectures).length;
    const duplicateCount = totalLectures - uniqueLecturesCount;
    
    if (duplicateCount > 0) {
      console.warn(`  ⚠️  ${duplicateCount} Duplikate gefunden (überschrieben)`);
    }
    
    return fullLectures;
    
  } catch (error) {
    console.error('Fehler beim Laden der Vorträge:', error.message);
    console.warn('System läuft ohne vollständige Vorträge');
    return {};
  }
}

async function loadBooks() {
  try {
    const { bookFiles } = await findDataFiles();
    
    if (bookFiles.length === 0) {
      console.error('❌ FEHLER: Keine steiner-books-XXX-YYY*.json Dateien gefunden!');
      const allFiles = await fs.readdir(__dirname);
      const bookLikeFiles = allFiles.filter(f => f.includes('books') && f.endsWith('.json'));
      console.error('   Verfügbare Dateien mit "books":', bookLikeFiles);
      return {};
    }
    
    
    let totalBooks = 0;
    for (const fileName of bookFiles) {
      const jsonPath = path.join(__dirname, fileName);
      
      try {
        const data = await fs.readFile(jsonPath, 'utf8');
        const parsed = JSON.parse(data);
        
        const books = parsed.books || [];
        
        if (books.length === 0) {
          console.warn(`    ⚠️  Warnung: ${fileName} enthält keine Schriften!`);
        }
        
        
        books.forEach(book => {
          if (book.ID || book.gaNumber) {
            const bookId = book.ID || book.gaNumber;
            fullBooks[bookId] = book;
            totalBooks++;
          } else {
            console.warn(`      ⚠️  Übersprungen: Keine ID oder gaNumber gefunden`, Object.keys(book));
          }
        });
        
      } catch (fileError) {
        console.error(`    ❌ Fehler beim Laden von ${fileName}:`, fileError.message);
      }
    }
    
    
    return fullBooks;
    
  } catch (error) {
    console.error('Fehler beim Laden der Schriften:', error.message);
    console.warn('System läuft ohne Schriften');
    return {};
  }
}

async function loadSynonyms() {
  try {
    const synonymPath = path.join(__dirname, 'synonyms.json');
    
    try {
      const data = await fs.readFile(synonymPath, 'utf8');
      synonyms = JSON.parse(data);
    } catch {
      synonyms = defaultSynonyms;
      await fs.writeFile(synonymPath, JSON.stringify(synonyms, null, 2), 'utf8');
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
  } catch {
    queryLog = {};
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
      delete gaOverviewCache[actualKey];
      await saveGAOverviewCache();
    } else {
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
    } catch {
      gaOverviewCache = {};
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
  // Case-insensitive Vergleich
  const gaNumberNormalized = gaNumber.toLowerCase();
  
  // Suche nach Vorträgen (Books haben eigenen Endpoint /api/book/:gaNumber)
  const lectures = Object.values(fullLectures)
    .filter(lec => lec.gaNumber && lec.gaNumber.toLowerCase() === gaNumberNormalized)
    .sort((a, b) => {
      const numA = parseInt(a.lectureNumber) || 0;
      const numB = parseInt(b.lectureNumber) || 0;
      return numA - numB;
    });
  
  if (lectures.length === 0) {
    console.warn(`[GA-OVERVIEW] Keine Vorträge für ${gaNumber} gefunden (fullLectures hat ${Object.keys(fullLectures).length} Einträge)`);
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
        summary: summaryText,
        shortSummary: summaryData?.shortSummary || null,
        headings: summaryData?.headings || [],
        tableOfContents: summaryData?.tableOfContents || [],
        lectureKeywords: summaryData?.lectureKeywords || [],
        version: summaryData?.version || 'v1'
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
  
  
  return newSynonyms;
}

async function generateSynonymsWithClaude(term) {
  const claudeApiKey = process.env.CLAUDE_API_KEY;
  if (!claudeApiKey) {
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
    
    
    return synonymList;
  } catch (error) {
    console.error(`[CLAUDE] Fehler für "${term}":`, error.message);
    return [term];
  }
}

async function enrichSynonymsWithClaude(topN = 30) {
  
  const topTerms = Object.keys(queryLog)
    .filter(term => term.length > 3)
    .sort((a, b) => queryLog[b].count - queryLog[a].count)
    .slice(0, topN);
  
  let enrichedCount = 0;
  
  for (const term of topTerms) {
    if (synonyms[term] && synonyms[term].length > 2) {
      continue;
    }
    
    const generatedSynonyms = await generateSynonymsWithClaude(term);
    
    if (generatedSynonyms.length > 1) {
      synonyms[term] = generatedSynonyms;
      enrichedCount++;
      await saveSynonyms();
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
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
      }
    }
  }
  
  // 5. Extrahiere bedeutungsvolle Einzelwörter
  words.forEach(word => {
    if (word.length > 3 && !stopWords.includes(word)) {
      terms.push(word);
    }
  });
  
  // 6. Entferne exakte Duplikate
  const uniqueTerms = [...new Set(terms)];
  
  
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
  }
  
  if (terms.length === 0) {
    return performKeywordSearch(query, filteredParagraphs);
  }
  
  // NEUE STRATEGIE: Suche zuerst nach Phrasen in Anführungszeichen
  const quotedPhrases = query.match(/"([^"]+)"|'([^']+)'/g);
  if (quotedPhrases && quotedPhrases.length > 0) {
    
    const phraseResults = [];
    quotedPhrases.forEach(phrase => {
      const cleaned = phrase.replace(/['"]/g, '').trim().toLowerCase();
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
      
      return finalResults;
    }
  }
  
  // Fallback: Normale thematische Suche mit allen Begriffen
  
  const allResults = new Map();
  
  terms.forEach(term => {
    const wordCount = term.split(' ').length;
    
    // Überspringe zu generische Einzelwörter
    if (wordCount === 1) {
      const veryCommonWords = ['bedeutung', 'welche', 'haben'];
      if (veryCommonWords.includes(term)) {
        return;
      }
    }
    
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

// ============================================================================
// RELEVANZ-SCORING: Basierend auf Häufigkeit in 2 Absätzen vor/nach Treffer
// ============================================================================

// Hilfsfunktion: Relevanz-Scoring für Stichwortsuche-Ergebnisse hinzufügen
function addRelevanceScoringToResults(results, query) {
  const totalResults = results.length;
  const CONTEXT_PARAGRAPHS = 2; // Anzahl Absätze vor und nach jedem Treffer
  
  if (totalResults === 0) {
    return results;
  }
  
  // Zerlege Query in einzelne Wörter (für Zwei-Wort-Suchen)
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 0);
  const isTwoWordQuery = queryWords.length === 2;
  
  // Hilfsfunktion: Hole Kontext-Absätze für einen einzelnen Treffer (2 vor + Treffer + 2 nach)
  function getContextForSingleHit(lectureId, hitParagraphIndex, isBookFlag) {
    let paragraphs;
    
    if (isBookFlag) {
      const book = fullBooks[lectureId];
      if (!book) return null;
      paragraphs = convertBookToParagraphs(book);
    } else {
      const lecture = fullLectures[lectureId];
      if (!lecture || !lecture.paragraphs) return null;
      paragraphs = lecture.paragraphs;
    }
    
    if (!paragraphs || paragraphs.length === 0) return null;
    
    // Stelle sicher, dass hitParagraphIndex innerhalb des gültigen Bereichs liegt
    if (hitParagraphIndex < 0 || hitParagraphIndex >= paragraphs.length) {
      return null;
    }
    
    const startIndex = Math.max(0, hitParagraphIndex - CONTEXT_PARAGRAPHS);
    const endIndex = Math.min(paragraphs.length - 1, hitParagraphIndex + CONTEXT_PARAGRAPHS);
    
    const contextParagraphs = [];
    for (let i = startIndex; i <= endIndex; i++) {
      if (paragraphs[i]) {
        const content = paragraphs[i].content || paragraphs[i].text || '';
        if (content.trim().length > 0) {
          contextParagraphs.push({
            paragraphIndex: i,
            content: content
          });
        }
      }
    }
    
    return contextParagraphs.length > 0 ? contextParagraphs : null;
  }
  
  // Hilfsfunktion: Zähle Vorkommen eines Wortes im Text (ganze Wörter)
  // WICHTIG: Normalisiere Text und Wort zu lowercase für korrekten Vergleich mit Umlauten
  function countWholeWordOccurrences(text, word) {
    // Normalisiere Text und Wort zu lowercase für korrekten Vergleich
    const textLower = text.toLowerCase();
    const wordLower = word.toLowerCase();
    
    // Escaped Word für Regex (nach Normalisierung)
    const escapedWord = wordLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    
    // Verwende eine robuste Word-Boundary-Erkennung, die auch mit Umlauten funktioniert
    // Suche nach dem Wort, umgeben von Nicht-Wort-Zeichen (inkl. Umlaute) oder String-Grenzen
    // Erweitere Zeichenklasse um deutsche Umlaute und andere Unicode-Zeichen
    const wordBoundaryBefore = '(^|[^a-zäöüßA-ZÄÖÜ0-9_])';
    const wordBoundaryAfter = '([^a-zäöüßA-ZÄÖÜ0-9_]|$)';
    const regex = new RegExp(`${wordBoundaryBefore}${escapedWord}${wordBoundaryAfter}`, 'gi');
    
    const matches = textLower.match(regex);
    return matches ? matches.length : 0;
  }
  
  // Berechne Relevanz-Score für einen Treffer basierend auf Häufigkeit im Kontext
  function calculateRelevanceScoreForHit(contextParagraphs, query, isTwoWord) {
    if (!contextParagraphs || contextParagraphs.length === 0) return 0;
    
    // Kombiniere alle Kontext-Absätze zu einem Text
    const contextText = contextParagraphs.map(p => p.content || '').join(' ');
    const queryLower = query.toLowerCase();
    
    if (isTwoWord) {
      const word1 = queryWords[0];
      const word2 = queryWords[1];
      
      // Zähle Vorkommen jedes Wortes (ganze Wörter)
      const word1Matches = countWholeWordOccurrences(contextText, word1);
      const word2Matches = countWholeWordOccurrences(contextText, word2);
      const phrasePattern = `${word1} ${word2}`;
      const phraseMatches = countWholeWordOccurrences(contextText, phrasePattern);
      
      // Score basierend auf Häufigkeit im Kontext (5 Absätze)
      // Für Zwei-Wort-Suchen: Ähnlich differenziert wie Einzelwort-Suchen
      // Berücksichtige Gesamtzahl der Vorkommen beider Wörter und Phrasen
      const totalMatches = word1Matches + word2Matches;
      
      // Basis-Score basierend auf Gesamtzahl der Vorkommen (ähnlich wie Einzelwort)
      let baseScore;
      if (totalMatches === 0) {
        baseScore = 0;
      } else if (totalMatches === 1) {
        // Nur 1 Vorkommen insgesamt (eines der beiden Wörter)
        baseScore = 0.2;
      } else if (totalMatches === 2) {
        // 2 Vorkommen insgesamt
        baseScore = 0.35;
      } else if (totalMatches === 3) {
        // 3 Vorkommen insgesamt
        baseScore = 0.5;
      } else if (totalMatches === 4) {
        // 4 Vorkommen insgesamt
        baseScore = 0.6;
      } else if (totalMatches === 5) {
        // 5 Vorkommen insgesamt
        baseScore = 0.65;
      } else {
        // 6+ Vorkommen: Linear skalieren bis 0.8
        const normalizedMatches = Math.min(totalMatches / 10, 1); // Normalisiere auf max 10 Treffer
        baseScore = 0.65 + (normalizedMatches * 0.15); // Zwischen 0.65 und 0.8
      }
      
      // Phrase-Bonus: Wenn beide Wörter als Phrase vorkommen, erhöhe den Score
      let phraseBonus = 0;
      if (phraseMatches > 0) {
        // Bonus für Phrasen: Je mehr Phrasen, desto höher der Bonus
        if (phraseMatches === 1) {
          phraseBonus = 0.1; // +0.1 für 1 Phrase
        } else if (phraseMatches === 2) {
          phraseBonus = 0.15; // +0.15 für 2 Phrasen
        } else {
          phraseBonus = 0.15 + (Math.min(phraseMatches / 5, 1) * 0.05); // +0.15 bis +0.2 für 3+ Phrasen
        }
      }
      
      // Bonus wenn beide Wörter vorkommen (auch wenn nicht als Phrase)
      let bothWordsBonus = 0;
      if (word1Matches > 0 && word2Matches > 0) {
        bothWordsBonus = 0.05; // +0.05 wenn beide Wörter vorkommen
      }
      
      const score = Math.min(baseScore + phraseBonus + bothWordsBonus, 0.8); // Max 0.8 (wie Einzelwort)
      return score;
    } else {
      // Für Einzelwort-Suchen: Zähle Vorkommen im Kontext (ganze Wörter)
      const matches = countWholeWordOccurrences(contextText, queryLower);
      
      // Score basierend auf Häufigkeit im Kontext (5 Absätze)
      // Verbesserte Differenzierung für bessere Verteilung:
      // - 1 Vorkommen: Basis-Score (0.3)
      // - 2 Vorkommen: Erhöhter Score (0.5)
      // - 3 Vorkommen: Hoher Score (0.6)
      // - 4+ Vorkommen: Sehr hoher Score (0.7-0.8)
      let score;
      if (matches === 0) {
        score = 0;
      } else if (matches === 1) {
        score = 0.3; // Erhöht von 0.2 auf 0.3
      } else if (matches === 2) {
        score = 0.5; // Erhöht von 0.35 auf 0.5
      } else if (matches === 3) {
        score = 0.6; // Erhöht von 0.45 auf 0.6
      } else {
        // Für 4+ Vorkommen: Linear skalieren bis 0.8
        const normalizedMatches = Math.min(matches / 10, 1); // Normalisiere auf max 10 Treffer
        score = 0.6 + (normalizedMatches * 0.2); // Zwischen 0.6 und 0.8
      }
      
      return Math.min(score, 0.8); // Max 0.8 (erhöht von 0.6)
    }
  }
  
  // Berechne Relevanz-Score für jeden Treffer
  const resultScores = results.map((result, index) => {
    const lectureId = result.ID;
    const hitParagraphIndex = result.paragraphIndex || 0;
    const isBookFlag = result.isBook || false;
    
    // Prüfe, ob der Treffer-Absatz selbst das Wort enthält
    const hitContent = result.content || '';
    const hitContainsQuery = hitContent.toLowerCase().includes(query.toLowerCase());
    
    // Hole Kontext für diesen Treffer (2 Absätze vor + Treffer + 2 Absätze nach)
    const contextParagraphs = getContextForSingleHit(lectureId, hitParagraphIndex, isBookFlag);
    
    // Berechne Score basierend auf Kontext
    const score = contextParagraphs 
      ? calculateRelevanceScoreForHit(contextParagraphs, query, isTwoWordQuery)
      : 0.05; // Niedriger Fallback-Score wenn Kontext nicht verfügbar
    
    // Debug für erste 10 Treffer
    if (index < 10) {
      const contextText = contextParagraphs ? contextParagraphs.map(p => p.content || '').join(' ') : '';
      const matches = !isTwoWordQuery ? countWholeWordOccurrences(contextText, query.toLowerCase()) : 0;
      const contextPreview = contextText.substring(0, 200).replace(/\s+/g, ' ');
      const queryLower = query.toLowerCase();
      const contextLower = contextText.toLowerCase();
      const containsQuery = contextLower.includes(queryLower);
      const hitPreview = hitContent.substring(0, 100).replace(/\s+/g, ' ');
    }
    
    return {
      result: result,
      score: score
    };
  });
  
  // KONTINUIERLICHE ANPASSUNG: Schwellwerte relativ zur Gesamthäufigkeit des Suchworts
  // WICHTIG: Bei seltenen Wörtern sind niedrigere Schwellwerte angemessen
  //          Bei häufigen Wörtern müssen höhere Schwellwerte verwendet werden
  //          Keine prozentuale Verteilung - alle Treffer mit entsprechender Häufigkeit werden kategorisiert
  //          KONTINUIERLICHE Funktion (nicht stufenweise)
  
  // Basis-Schwellwerte basierend auf Score-Werten (die Häufigkeit widerspiegeln):
  // - Score 0.3 = 1 Vorkommen
  // - Score 0.5 = 2 Vorkommen
  // - Score 0.6 = 3 Vorkommen
  // - Score 0.7+ = 4+ Vorkommen
  
  // Kontinuierliche Funktion für Schwellwerte basierend auf Gesamtzahl der Treffer
  // Verwendet logarithmische Skalierung für natürliche Anpassung über den gesamten Bereich
  
  // Parameter für kontinuierliche Funktion:
  // - Bei 1 Treffer: thresholdHigh = 0.3 (1 Vorkommen = hoch)
  // - Bei 10000 Treffern: thresholdHigh = 0.65 (3-4+ Vorkommen = hoch, nicht zu streng)
  // - Logarithmische Skalierung für natürliche Kurve
  
  const logResults = Math.log10(Math.max(totalResults, 1)); // log10(1) = 0, log10(10000) ≈ 4
  const maxLogResults = Math.log10(10000); // Referenzpunkt für maximale Häufigkeit
  
  // Normalisiere auf 0-1 Skala basierend auf logarithmischer Häufigkeit
  // Bei sehr wenigen Treffern (log10(1-100) = 0-2): niedrige Schwellwerte
  // Bei vielen Treffern (log10(5000-10000) = 3.7-4): moderate Schwellwerte (nicht zu streng)
  const normalizedFrequency = Math.min(logResults / maxLogResults, 1); // 0 bis 1
  
  // Kontinuierliche Berechnung der Schwellwerte
  // thresholdHigh: von 0.3 (selten) bis 0.6 (häufig) - reduziert, damit 3 Vorkommen (Score 0.6) noch "hoch" sind
  // Bei sehr vielen Treffern: 3+ Vorkommen (Score 0.6) sollten noch als "hoch" gelten
  let thresholdHigh = 0.3 + (normalizedFrequency * 0.3); // 0.3 bis 0.6
  
  // thresholdMedium: von 0.2 (selten) bis 0.4 (häufig) - reduziert
  let thresholdMedium = 0.2 + (normalizedFrequency * 0.2); // 0.2 bis 0.4
  
  // Stelle sicher, dass Schwellwerte in sinnvollem Bereich bleiben
  thresholdHigh = Math.max(0.3, Math.min(0.6, thresholdHigh));
  thresholdMedium = Math.max(0.2, Math.min(0.4, thresholdMedium));
  
  // Stelle sicher, dass Medium unter High liegt (mindestens 0.1 Abstand)
  if (thresholdMedium >= thresholdHigh) {
    thresholdMedium = Math.max(0.2, thresholdHigh - 0.1);
  }
  
  // Kategorisiere ALLE Ergebnisse basierend auf Häufigkeit (Score)
  // KEINE prozentuale Verteilung - jeder Treffer wird nach seiner tatsächlichen Häufigkeit bewertet
  const resultsWithRelevance = resultScores.map(({ result, score }) => {
    let relevanceCategory = 'niedrig';
    if (score >= thresholdHigh) {
      relevanceCategory = 'hoch';
    } else if (score >= thresholdMedium) {
      relevanceCategory = 'mittel';
    }
    
    return {
      ...result,
      relevanceScore: score,
      relevanceCategory: relevanceCategory
    };
  });
  
  // Debug-Ausgabe
  const categoryCounts = resultsWithRelevance.reduce((acc, r) => {
    acc[r.relevanceCategory] = (acc[r.relevanceCategory] || 0) + 1;
    return acc;
  }, {});
  
  
  return resultsWithRelevance;
}

// ============================================================================
// ZWEI-WORT-RELEVANZ-BERECHNUNG (ENTFERNT - wird später neu implementiert)
// ============================================================================

function calculateTwoWordRelevanceScore(lectureResults, word1, word2, useSimplifiedContext = false) {
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
  
  // 5. Berechne Kontext-Relevanz für beide Wörter (Durchschnitt) (OPTIMIERUNG #4: vereinfacht)
  const contextRelevance1 = calculateContextRelevance(fullText, word1Lower, contextIndex1, useSimplifiedContext);
  const contextRelevance2 = calculateContextRelevance(fullText, word2Lower, contextIndex2, useSimplifiedContext);
  const avgContextRelevance = (contextRelevance1 + contextRelevance2) / 2;
  
  
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
  
  // Durchsuche auch Bücher
  Object.values(fullBooks).forEach(book => {
    const bookParagraphs = getBookParagraphsForSearch(book);
    const fullText = bookParagraphs.map(p => p.content || p.text || '').join(' ');
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
    return null;
  }
  
  
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
    } else {
      allIndices = validIndices;
    }
    
    if (removedCount > 0) {
    }
    
    // Speichere zurück
    fs.writeFileSync(indicesFile, JSON.stringify(allIndices, null, 2), 'utf-8');
  } catch (error) {
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
          // Springe zur Regenerierung (weiter unten im Code)
        } else {
          contextIndexCache[queryLower] = data;
          return data;
        }
      }
    }
  } catch (error) {
  }
  
  // Falls nicht vorhanden: Prüfe ob genug Vorkommen für Index-Generierung
  // Schnelle Vorkommen-Prüfung
  let totalOccurrences = 0;
  Object.values(fullLectures).forEach(lecture => {
    const paragraphs = lecture.paragraphs || [];
    const fullText = paragraphs.map(p => p.content || p.text || '').join(' ');
    totalOccurrences += (fullText.toLowerCase().match(new RegExp(queryLower, 'g')) || []).length;
  });
  
  
  // Nur für häufigere Begriffe (≥5 Vorkommen) Index generieren
  if (totalOccurrences >= 5) {
    const newIndex = generateContextIndex(query);
    
    if (newIndex) {
      contextIndexCache[queryLower] = newIndex;
    }
    
    return newIndex;
  } else {
    return null;
  }
}

// Berechne Kontext-Relevanz: Wie viele typische Kontextwörter kommen im Vortrag vor?
// OPTIMIERUNG #4: Vereinfachte Kontext-Relevanz mit weniger Kontextwörtern
function calculateContextRelevance(fullText, query, contextIndex, useSimplified = false) {
  if (!contextIndex || !contextIndex.context_terms) {
    return 1.0; // Neutral, wenn kein Kontext-Index vorhanden
  }
  
  const fullTextLower = fullText.toLowerCase();
  const contextTerms = contextIndex.context_terms;
  
  // OPTIMIERUNG #4: Reduziere Anzahl der Kontextwörter (von 50 auf 10-15)
  const maxTerms = useSimplified ? 10 : 20; // Bei vereinfachter Berechnung nur Top 10
  const topTerms = Object.entries(contextTerms)
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxTerms);
  
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
      // Gewichte nach Häufigkeit im Kontext-Index (vereinfacht bei vielen Treffern)
      if (useSimplified) {
        weightedMatches += Math.min(count, 3); // Max 3 statt 5
      } else {
        weightedMatches += Math.min(count, 5) * Math.log(frequency + 1);
      }
    }
  }
  
  // Normalisiere: Je mehr typische Kontextwörter vorkommen, desto höher die Relevanz
  const matchRatio = matchedTerms / Math.min(topTerms.length, maxTerms);
  // OPTIMIERUNG #4: Reduzierter Faktor bei vereinfachter Berechnung
  const contextRelevance = useSimplified 
    ? 1.0 + (matchRatio * 1.0)  // Faktor 1.0 - 2.0 (reduziert)
    : 1.0 + (matchRatio * 2.0); // Faktor 1.0 - 3.0 (normal)
  
  return Math.min(contextRelevance, useSimplified ? 2.0 : 3.0);
}

// Hilfsfunktion: Relevanz-Score für einen Vortrag berechnen (1000-Wörter-Fenster + Kontext Version)
function calculateRelevanceScoreForLecture(lectureResults, query, useSimplifiedContext = false) {
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
  
  // 3. Kontext-Relevanz berechnen (OPTIMIERUNG #4: vereinfacht bei vielen Treffern)
  const contextIndex = loadContextIndex(query);
  const contextRelevance = calculateContextRelevance(fullText, query, contextIndex, useSimplifiedContext);
  
  // 4. Normalisierung mit Gesamtvorkommen
  const totalOccurrenceFactor = Math.sqrt(totalOccurrences);
  
  // Finaler Score = Window-Score × Gesamtvorkommen × Kontext-Relevanz × Skalierung
  const finalScore = bestWindowScore * totalOccurrenceFactor * contextRelevance * 5;
  
  // Debug-Ausgabe
  if (totalOccurrences > 0) {
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
    
    // Relevanz-Scoring für jeden Vortrag hinzufügen
    const resultsWithRelevance = addRelevanceScoringToResults(keywordResults, query);
    
    const rankedResults = applySemanticRanking(resultsWithRelevance, query);
    const topResults = rankedResults.slice(0, limit);
    
    
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
    const { word1, word2, word1IsPhrase = false, word2IsPhrase = false, wordOperator = 'and', proximity = null, relevanceFilter = 'alle', yearFilter = '', gaFilter = '' } = req.body;
    
    if (!word1) {
      return res.status(400).json({ error: 'Mindestens ein Suchwort erforderlich' });
    }
    
    // Proximity-Filter:
    // null/"" = kein Limit (beliebiger Abstand im gesamten Vortrag)
    // 1, 2 oder 3 = max. X Absätze Abstand zwischen den Wörtern
    const effectiveProximity = proximity || null;
    
    const operatorText = word2 ? ` ${wordOperator.toUpperCase()} ` : '';
    const proximityInfo = effectiveProximity ? ` (Proximity: max. ${effectiveProximity} Absätze)` : word2 ? ' (beliebiger Abstand)' : '';
    
    // Hilfsfunktion für exakte Phrasensuche oder flexible Wortsuche
    const searchInText = (text, searchTerm, isPhrase) => {
      if (!searchTerm) return false;
      
      if (isPhrase) {
        // Exakte Phrasensuche: Wortgrenzen UND case-sensitive
        // \b funktioniert nicht gut mit Umlauten, daher verwende manuelle Wortgrenze
        const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(^|[\\s,.;:!?()\\-—])${escapedTerm}($|[\\s,.;:!?()\\-—])`);
        return regex.test(text);
      } else {
        // Flexible Suche: auch Teilwörter erlaubt, case-insensitive
        const textLower = text.toLowerCase();
        const termLower = searchTerm.toLowerCase();
        return textLower.includes(termLower);
      }
    };
    
    const results = [];
    const addedParagraphs = new Set();
    
    Object.values(fullLectures).forEach(lecture => {
      // GA-Filter: Überspringe Vorträge, die nicht zu den ausgewählten GA-Bänden gehören
      if (gaFilter) {
        const lectureGA = lecture.ID ? lecture.ID.split('/')[0] : ''; // z.B. "GA110"
        const gaFilters = gaFilter.split(',').map(f => f.trim()).filter(f => f);
        
        // Prüfe ob der Vortrag zu einem der ausgewählten GA-Bände gehört
        const matchesFilter = gaFilters.some(filter => 
          lectureGA === filter || 
          lectureGA === `GA${filter}` || 
          lectureGA.replace('GA', '').replace('ga', '') === filter
        );
        
        if (!matchesFilter) {
          return; // Überspringe diesen Vortrag
        }
      }
      
      // Jahr-Filter: Überspringe Vorträge, die nicht zu den ausgewählten Jahren gehören
      if (yearFilter) {
        const lectureYear = lecture.date ? lecture.date.substring(0, 4) : '';
        const yearFilters = yearFilter.split(',').map(f => f.trim()).filter(f => f);
        
        // Prüfe ob der Vortrag zu einem der ausgewählten Jahre gehört
        const matchesYearFilter = yearFilters.some(filter => lectureYear === filter);
        
        if (!matchesYearFilter) {
          return; // Überspringe diesen Vortrag
        }
      }
      
      const paragraphs = lecture.paragraphs || [];
      
      // Bei UND ohne Proximity: Prüfe erst ob beide Wörter irgendwo im Vortrag vorkommen
      let lectureHasWord1 = false;
      let lectureHasWord2 = false;
      if (word2 && wordOperator === 'and' && !effectiveProximity) {
        for (const para of paragraphs) {
          const content = (para.content || para.text || '');
          if (!lectureHasWord1) lectureHasWord1 = searchInText(content, word1, word1IsPhrase);
          if (!lectureHasWord2) lectureHasWord2 = searchInText(content, word2, word2IsPhrase);
          if (lectureHasWord1 && lectureHasWord2) break;
        }
      }
      
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
        } else if (wordOperator === 'or') {
          // ODER-Suche: Mindestens ein Wort muss vorkommen (Proximity irrelevant)
          if (hasWord1 || hasWord2) {
            paragraphsToAdd.push(paraIndex);
          }
        } else if (!effectiveProximity) {
          // UND-Suche OHNE Proximity-Limit (beide Wörter müssen irgendwo im Vortrag vorkommen)
          if (lectureHasWord1 && lectureHasWord2 && (hasWord1 || hasWord2)) {
            paragraphsToAdd.push(paraIndex);
          }
        } else {
          // UND-Suche MIT Proximity-Limit (max. 1, 2 oder 3 Absätze)
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
    
    // Durchsuche auch Bücher
    Object.values(fullBooks).forEach(book => {
      // GA-Filter: Überspringe Bücher, die nicht zu den ausgewählten GA-Bänden gehören
      if (gaFilter) {
        const bookGA = book.ID || book.gaNumber || '';
        const gaFilters = gaFilter.split(',').map(f => f.trim()).filter(f => f);
        
        const matchesFilter = gaFilters.some(filter => 
          bookGA === filter || 
          bookGA === `GA${filter}` || 
          bookGA.replace('GA', '').replace('ga', '') === filter
        );
        
        if (!matchesFilter) {
          return; // Überspringe dieses Buch
        }
      }
      
      // Konvertiere Buch in Paragraphs
      const bookParagraphs = getBookParagraphsForSearch(book);
      
      bookParagraphs.forEach((para, paraIndex) => {
        const content = (para.content || para.text || '');
        
        // Prüfe ob Paragraph die Suchwörter enthält
        const hasWord1 = searchInText(content, word1, word1IsPhrase);
        const hasWord2 = word2 && searchInText(content, word2, word2IsPhrase);
        
        const paragraphsToAdd = [];
        
        if (!word2) {
          if (hasWord1) {
            paragraphsToAdd.push(paraIndex);
          }
        } else {
          // Zwei Wörter: Prüfe Operatoren und Proximity
          if (wordOperator === 'and') {
            if (hasWord1 && hasWord2) {
              if (effectiveProximity === null) {
                // Beliebiger Abstand im gesamten Buch
                paragraphsToAdd.push(paraIndex);
              } else {
                // Proximity: Suche in benachbarten Absätzen
                // Da Bücher keine klaren Absatz-Grenzen haben wie Vorträge,
                // verwenden wir einen größeren Proximity-Bereich
                paragraphsToAdd.push(paraIndex);
              }
            }
          } else if (wordOperator === 'or') {
            if (hasWord1 || hasWord2) {
              paragraphsToAdd.push(paraIndex);
            }
          }
        }
        
        paragraphsToAdd.forEach(idx => {
          const key = `${book.ID || book.gaNumber}-${idx}`;
          if (!addedParagraphs.has(key)) {
            addedParagraphs.add(key);
            const p = bookParagraphs[idx];
            const pContent = (p.content || p.text || '');
            
            results.push({
              ID: book.ID || book.gaNumber,
              title: book.title,
              fileName: book.fileName,
              location: null, // Bücher haben keinen Ort
              date: book.yearRange || null, // Bücher haben Jahr-Range statt Datum
              paragraphIndex: idx,
              index: p.index,
              content: p.content || p.text,
              hasWord1: searchInText(pContent, word1, word1IsPhrase),
              hasWord2: word2 && searchInText(pContent, word2, word2IsPhrase),
              isBook: true
            });
          }
        });
      });
    });
    
    
    // Relevanz-Scoring für Volltext-Suche hinzufügen
    const searchQuery = word2 ? `${word1} ${word2}` : word1;
    const resultsWithRelevance = addRelevanceScoringToResults(results, searchQuery);
    
    // Backend-Filterung nach Relevanz
    let filteredResults = resultsWithRelevance;
    if (relevanceFilter && relevanceFilter !== 'alle' && relevanceFilter !== 'ohne') {
      filteredResults = resultsWithRelevance.filter(r => r.relevanceCategory === relevanceFilter);
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
      unfilteredCount: results.length
    });
    
  } catch (error) {
    console.error('Volltext-Suche Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// ERWEITERTE SUCHE (bis zu 7 Worte)
// ============================================================================

app.post('/api/advanced-search', async (req, res) => {
  try {
    const { words, operators, proximity = null, gaFilter = '' } = req.body;
    
    if (!words || words.length === 0) {
      return res.status(400).json({ error: 'Mindestens ein Suchwort erforderlich' });
    }
    
    
    const results = [];
    
    // Hilfsfunktion für flexible oder exakte Wortsuche
    const searchInText = (text, searchTerm) => {
      if (!searchTerm) return false;
      
      // Prüfe ob searchTerm in Anführungszeichen steht (exakte Suche)
      const isExactMatch = searchTerm.startsWith('"') && searchTerm.endsWith('"');
      
      if (isExactMatch) {
        // Exakte Suche: Entferne Anführungszeichen und suche mit Wortgrenzen
        const exactTerm = searchTerm.slice(1, -1); // Entferne " am Anfang und Ende
        
        // Suche mit Wortgrenzen (word boundaries)
        // OHNE 'i' Flag für case-sensitive Suche bei exaktem Matching
        const regex = new RegExp(`\\b${exactTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
        return regex.test(text);
      } else {
        // Flexible Suche wie bisher (case-insensitive)
        const textLower = text.toLowerCase();
        const termLower = searchTerm.toLowerCase();
        return textLower.includes(termLower);
      }
    };
    
    // Hilfsfunktion: Erstelle Snippet mit dem Suchwort im Kontext
    const createContextSnippet = (content, searchWord, maxLength = 200) => {
      // Prüfe ob exakte Suche (mit Anführungszeichen)
      const isExactMatch = searchWord.startsWith('"') && searchWord.endsWith('"');
      
      // Entferne Anführungszeichen falls vorhanden
      const cleanWord = isExactMatch 
        ? searchWord.slice(1, -1) 
        : searchWord;
      
      // Finde das Wort im Inhalt
      let wordIndex;
      if (isExactMatch) {
        // Case-sensitive Suche bei exaktem Matching
        wordIndex = content.indexOf(cleanWord);
      } else {
        // Case-insensitive Suche bei flexibler Suche
        const contentLower = content.toLowerCase();
        const wordLower = cleanWord.toLowerCase();
        wordIndex = contentLower.indexOf(wordLower);
      }
      
      if (wordIndex === -1) {
        // Fallback: Anfang des Textes wenn Wort nicht gefunden
        return content.substring(0, maxLength) + (content.length > maxLength ? '...' : '');
      }
      
      // Berechne Start und Ende des Snippets so, dass das Wort zentral ist
      const contextBefore = Math.floor((maxLength - cleanWord.length) / 2);
      const contextAfter = maxLength - cleanWord.length - contextBefore;
      
      let start = Math.max(0, wordIndex - contextBefore);
      let end = Math.min(content.length, wordIndex + cleanWord.length + contextAfter);
      
      // Versuche an Wortgrenzen zu schneiden
      if (start > 0) {
        // Finde Wortgrenze (Leerzeichen) vor dem Start
        const spaceBeforeStart = content.lastIndexOf(' ', start);
        if (spaceBeforeStart > start - 20 && spaceBeforeStart !== -1) {
          start = spaceBeforeStart + 1;
        }
      }
      
      if (end < content.length) {
        // Finde Wortgrenze (Leerzeichen) nach dem Ende
        const spaceAfterEnd = content.indexOf(' ', end);
        if (spaceAfterEnd < end + 20 && spaceAfterEnd !== -1) {
          end = spaceAfterEnd;
        }
      }
      
      let snippet = content.substring(start, end);
      
      // Füge Ellipsen hinzu
      if (start > 0) snippet = '...' + snippet;
      if (end < content.length) snippet = snippet + '...';
      
      return snippet;
    };
    
    // Durchsuche alle Vorträge
    Object.values(fullLectures).forEach(lecture => {
      // GA-Filter: Überspringe Vorträge, die nicht zu den ausgewählten GA-Bänden gehören
      if (gaFilter) {
        const lectureGA = lecture.ID ? lecture.ID.split('/')[0] : ''; // z.B. "GA110"
        const gaFilters = gaFilter.split(',').map(f => f.trim()).filter(f => f);
        
        // Prüfe ob der Vortrag zu einem der ausgewählten GA-Bände gehört
        const matchesFilter = gaFilters.some(filter => 
          lectureGA === filter || 
          lectureGA === `GA${filter}` || 
          lectureGA.replace('GA', '').replace('ga', '') === filter
        );
        
        if (!matchesFilter) {
          return; // Überspringe diesen Vortrag
        }
      }
      const paragraphs = lecture.paragraphs || [];
      
      // Für jedes Wort: Finde alle Absätze, die es enthalten
      const wordMatches = {};
      words.forEach(word => {
        wordMatches[word] = [];
      });
      
      paragraphs.forEach((para, paraIndex) => {
        const content = (para.content || para.text || '');
        
        words.forEach(word => {
          if (searchInText(content, word)) {
            wordMatches[word].push({
              paraIndex: paraIndex,
              content: content
            });
          }
        });
      });
      
      // Jetzt wenden wir die Operatoren und Proximity an
      // Wir gehen davon aus, dass die Operatoren die Worte miteinander verbinden:
      // Wort1 OP1 Wort2 OP2 Wort3 OP3 Wort4 ...
      
      if (proximity) {
        // Mit Proximity: Prüfe ob die Wörter innerhalb des Abstands vorkommen
        const proximityValue = parseInt(proximity);
        
        // Für jedes Wort: Prüfe ob es innerhalb des Abstands zu den anderen Wörtern vorkommt
        // Dies ist eine vereinfachte Logik - für eine vollständige Implementierung
        // müsste man alle Kombinationen prüfen
        
        words.forEach(word => {
          wordMatches[word].forEach(match => {
            const paraIndex = match.paraIndex;
            let matchesProximity = true;
            
            // Prüfe ob andere Wörter (je nach Operator) in der Nähe sind
            for (let i = 0; i < words.length; i++) {
              const otherWord = words[i];
              if (otherWord === word) continue;
              
              const operator = i > 0 ? operators[i - 1] : (operators[0] || 'and');
              
              // Finde ob das andere Wort im Proximity-Bereich vorkommt
              const otherWordInRange = wordMatches[otherWord].some(otherMatch => {
                return Math.abs(otherMatch.paraIndex - paraIndex) <= proximityValue;
              });
              
              if (operator === 'and' && !otherWordInRange) {
                matchesProximity = false;
                break;
              }
            }
            
            if (matchesProximity || operators.includes('or')) {
              // Erstelle ein Snippet mit dem Suchwort im Kontext
              const snippet = createContextSnippet(match.content, word, 200);
              
              results.push({
                lectureId: lecture.ID,
                lectureTitle: lecture.title || lecture.ID,
              lectureDate: lecture.date || '',
                snippet: snippet,
                matchedWord: word,
                paragraphIndex: paraIndex
              });
            }
          });
        });
        
      } else {
        // Ohne Proximity: Jedes Wort das vorkommt ist ein Treffer
        // (Operatoren bestimmen nur ob wir Treffer aus verschiedenen Wörtern kombinieren)
        
        // Vereinfachte Logik: Zeige alle Treffer für jedes Wort
        words.forEach(word => {
          wordMatches[word].forEach(match => {
            // Erstelle ein Snippet mit dem Suchwort im Kontext
            const snippet = createContextSnippet(match.content, word, 200);
            
            results.push({
              lectureId: lecture.ID,
              lectureTitle: lecture.title || lecture.ID,
            lectureDate: lecture.date || '',
              snippet: snippet,
              matchedWord: word,
              paragraphIndex: match.paraIndex
            });
          });
        });
      }
    });
    
    // Durchsuche auch Bücher
    Object.values(fullBooks).forEach(book => {
      // GA-Filter: Überspringe Bücher, die nicht zu den ausgewählten GA-Bänden gehören
      if (gaFilter) {
        const bookGA = book.ID || book.gaNumber || '';
        const gaFilters = gaFilter.split(',').map(f => f.trim()).filter(f => f);
        
        const matchesFilter = gaFilters.some(filter => 
          bookGA === filter || 
          bookGA === `GA${filter}` || 
          bookGA.replace('GA', '').replace('ga', '') === filter
        );
        
        if (!matchesFilter) {
          return; // Überspringe dieses Buch
        }
      }
      
      // Konvertiere Buch in Paragraphs
      const bookParagraphs = getBookParagraphsForSearch(book);
      
      // Für jedes Wort: Finde alle Absätze, die es enthalten
      const wordMatches = {};
      words.forEach(word => {
        wordMatches[word] = [];
      });
      
      bookParagraphs.forEach((para, paraIndex) => {
        const content = (para.content || para.text || '');
        
        words.forEach(word => {
          if (searchInText(content, word)) {
            wordMatches[word].push({
              paraIndex: paraIndex,
              content: content
            });
          }
        });
      });
      
      // Wende Operatoren und Proximity an (gleiche Logik wie bei Vorträgen)
      if (proximity) {
        const proximityValue = parseInt(proximity);
        
        words.forEach(word => {
          wordMatches[word].forEach(match => {
            const paraIndex = match.paraIndex;
            let matchesProximity = true;
            
            for (let i = 0; i < words.length; i++) {
              const otherWord = words[i];
              if (otherWord === word) continue;
              
              const operator = i > 0 ? operators[i - 1] : (operators[0] || 'and');
              
              const otherWordInRange = wordMatches[otherWord].some(otherMatch => {
                return Math.abs(otherMatch.paraIndex - paraIndex) <= proximityValue;
              });
              
              if (operator === 'and' && !otherWordInRange) {
                matchesProximity = false;
                break;
              }
            }
            
            if (matchesProximity || operators.includes('or')) {
              const snippet = createContextSnippet(match.content, word, 200);
              
              results.push({
                lectureId: book.ID || book.gaNumber,
                lectureTitle: book.title || book.fileName || book.ID,
                lectureDate: book.yearRange || null,
                snippet: snippet,
                matchedWord: word,
                paragraphIndex: paraIndex,
                index: bookParagraphs[paraIndex].index,
                isBook: true
              });
            }
          });
        });
      } else {
        words.forEach(word => {
          wordMatches[word].forEach(match => {
            const snippet = createContextSnippet(match.content, word, 200);
            
            results.push({
              lectureId: book.ID || book.gaNumber,
              lectureTitle: book.title || book.fileName || book.ID,
              lectureDate: book.yearRange || null,
              snippet: snippet,
              matchedWord: word,
              paragraphIndex: match.paraIndex,
              index: bookParagraphs[match.paraIndex].index,
              isBook: true
            });
          });
        });
      }
    });
    
    
    res.json({
      results: results,
      totalResults: results.length
    });
    
  } catch (error) {
    console.error('Erweiterte Suche Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// LLM ANALYSE
// ============================================================================

async function generateAnalysis(query, results, depth = 'allgemein') {
  
  // Hole passenden LLM-Provider (kein Fallback mehr)
  let provider;
  try {
    provider = getProviderForTask('analysis');
  } catch (error) {
    throw new Error('KI-Suche nicht verfügbar');
  }
  
  const topResults = results;  // Verwende alle übergebenen Ergebnisse gemäß aktuellem Limit

  const contextText = topResults
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      return `[${refId}] ${result.fileName || result.title}\n${result.content}`;
    })
    .join('\n\n---\n\n');
    
  const availableRefs = topResults.map(r => `${r.ID}:${r.index}`).join(', ');
  
  
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
Gliedere das Material mit wenigen, aussagekräftigen Zwischenüberschriften
Beziehe alle Aussagen inhaltlich auf die Suchwörter der Themenanfrage
Schreibe am Ende ein kurzes inhaltliches Fazit
Liste unter dem Fazit weitere relevante Quellenangaben als GA-Links auf

KRITISCH WICHTIG: Stelle nur Aspekte dar, die sich inhaltlich unmittelbar auf die Themenanfrage beziehen. Lasse alles weg, was nur am Rande oder indirekt mit dem Thema zu tun hat.
Inhaltliche Perspektiven (als Orientierung)
Wähle aus folgenden Perspektiven die jeweils relevanten Aspekte aus:

Sachliche Aspekte (konkrete Phänomene, Substanzen, leibliche Prozesse)
Funktionelle Aspekte (Wirkungsweisen, Prozesse, physiologische Aspekte)
Erlebnismäßige und seelisch-psychologische Aspekte
Begriffliche und geistige Aspekte (Ideen, Prinzipien)
Methodische und erkenntnistheoretische Aspekte
Vergleich mit anderen Inhalten
Entwicklung und/oder Evolution
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
Minimaler erläuternder Text - nur zur Verbindung der Zitate; keine Wiederholung des Inhalts der Zitate im verbindenden Text
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
Wenige ette wichtige Schlagwörter und zentrale Aussagen
FETT sehr sparsam einsetzen: Innerhalb von Zitaten nur relevante Begriffe/Kernaussagen fett markieren, niemals ganze Zitate; Begriffe/Kernaussagen nur einmal fett markieren (keine Redundanzen) ! wichtig
Keine GANZEN ZITATE fett markieren!
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
    
    // Verwende Provider-Abstraction
    let analysisText = await provider.generateCompletion(prompt, {
      maxTokens: maxTokens[effectiveDepth] || 8192,
      temperature: 0.7
    });
    
    
    analysisText = addClickableReferences(analysisText, topResults);
    
    
    return analysisText;

  } catch (error) {
    console.error('LLM-Analyse Fehler:', error);
    console.error('Error Details:', error.message);
    console.error('Stack:', error.stack);
    throw error;
  }
}

function addClickableReferences(text, results) {
  
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
  
  
  // Pattern erkennt sowohl Vorträge (GA###/Y:index) als auch Bücher (GA###:^index)
  const gaPattern = /\s*\(?(GA\d{3}[a-z]?(\/\d+)?:\^?[a-z0-9]+)\)?\s*/gi;
  
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
  
  if (matches.length > 0) {
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
    const { lectureId, forceRegenerate = false, preferredProvider = null } = req.body;
    
    if (!lectureId) {
      return res.status(400).json({ error: 'Lecture ID erforderlich' });
    }
    
    
    const lecture = fullLectures[lectureId];
    
    if (!lecture) {
      return res.status(404).json({ 
        error: `Vortrag nicht gefunden: ${lectureId}`,
        available: Object.keys(fullLectures).slice(0, 10)
      });
    }
    
    // Prüfe zuerst zentrale Summary-Datenbank
    const summaryDB = await loadSummaryDatabase();
    const existingSummary = summaryDB[lectureId] || null;
        
    if (!forceRegenerate && existingSummary) {
      // Prüfe ob V2 (vollständig mit TOC und Keywords)
      if (existingSummary.version === 'v2' && 
          existingSummary.tableOfContents && existingSummary.tableOfContents.length > 0 &&
          existingSummary.lectureKeywords && existingSummary.lectureKeywords.length > 0) {
        return res.json({
          lectureId: lectureId,
          summary: existingSummary.summary,
          headings: existingSummary.headings || [],
          tableOfContents: existingSummary.tableOfContents || [],
          lectureKeywords: existingSummary.lectureKeywords || [],
          fromCache: true,
          version: 'v2',
          paragraphCount: lecture.paragraphs?.length || 0
        });
      } else {
        // V1 vorhanden oder V2 unvollständig → Ergänze zu V2
      }
    } else if (!forceRegenerate && !existingSummary) {
    } else if (forceRegenerate && existingSummary && existingSummary.summary) {
      // WICHTIG: Bei forceRegenerate mit existierender Summary
      // → Nur TOC und Keywords neu generieren, Summary behalten!
    } else {
    }
    
    // Entscheide ob Summary neu generiert werden muss
    let summaryData;
    
    if (forceRegenerate && existingSummary && existingSummary.summary && existingSummary.headings) {
      // FALL: Summary + Headings existieren bereits
      // → Behalte beide, generiere nur neue Keywords
      
      summaryData = {
        summary: existingSummary.summary,
        headings: existingSummary.headings,
        tableOfContents: existingSummary.tableOfContents || [],
        lectureKeywords: existingSummary.lectureKeywords || [],
        version: 'v2'
      };
    } else {
      // FALL: Keine Summary oder forceRegenerate ohne existierende Daten
      // → Generiere alles neu
      summaryData = await generateLectureSummary(lecture, existingSummary, 'auto', preferredProvider);
    }
    
    // Speichere in zentrale Summary-Datenbank mit robustem Locking
    try {
      await saveSummaryToDatabase(lectureId, {
        summary: summaryData.summary,
        headings: summaryData.headings || [],
        tableOfContents: tableOfContents,  // Neu generiertes TOC
        lectureKeywords: summaryData.lectureKeywords || [],
        version: summaryData.version || 'v2'
      });
    } catch (dbError) {
      console.error(`[SPEICHERUNG] ✗ Fehler beim Speichern von ${lectureId}:`, dbError.message);
      // Werfe Fehler nicht weiter, Response sollte trotzdem gesendet werden
    }
    
    // NEU: Generiere TOC + Keywords mit V3 (flexible + Budget) wenn forceRegenerate
    let generatedKeywords = summaryData.lectureKeywords || [];
    let tableOfContents = summaryData.tableOfContents || [];
    
    if (forceRegenerate && summaryData.headings && summaryData.headings.length > 0) {
      // Bei forceRegenerate: TOC IMMER neu generieren (auch wenn vorhanden)
      if (forceRegenerate || !tableOfContents || tableOfContents.length === 0) {
        try {
          
          // Hole Provider
          let tocProvider;
          try {
            if (preferredProvider) {
              const { createProvider } = require('./llm-providers');
              tocProvider = createProvider(preferredProvider);
              if (!tocProvider.isAvailable()) {
                throw new Error(`${preferredProvider} nicht verfügbar`);
              }
            } else {
              tocProvider = getProviderForTask('summary');
            }
          } catch (providerError) {
            console.warn(`[TOC] Provider-Fehler: ${providerError.message}, überspringe TOC-Generierung`);
            tocProvider = null;
          }
          
          if (tocProvider) {
            // Filtere H3-Überschriften für TOC
            const h3Headings = summaryData.headings.filter(h => h.level === 'h3');
            
            if (h3Headings.length > 0) {
              const headingsText = h3Headings.map((h, idx) => 
                `${idx + 1}. ${h.text} [Index: ${h.index}]`
              ).join('\n');
              
              const tocPrompt = `Erstelle für jede H3-Überschrift eine prägnante Beschreibung (10-15 Wörter) was in diesem Abschnitt behandelt wird.

⚠️ ABSOLUT VERBOTEN - KEINE META-SPRACHE:
❌ NIEMALS: "Rudolf Steiner beschreibt...", "Steiner erklärt...", "Es wird untersucht..."
❌ NIEMALS: "Diskussion über...", "Analyse der...", "Betrachtung von..."
❌ NIEMALS: "Der Vortrag behandelt...", "Hier wird gezeigt..."
❌ NIEMALS: "Im Folgenden...", "Zunächst wird..."

✅ STATTDESSEN: Direkte, sachliche Formulierung!
✅ Schreibe als wäre es eine Lexikon-Definition
✅ Beginne direkt mit dem Inhalt

BEISPIELE:
❌ FALSCH: "Rudolf Steiner beschreibt die Transformation Roms zur Kirchenmacht"
✅ RICHTIG: "Transformation Roms zur Kirchenmacht nach dem Untergang des römischen Reiches"

❌ FALSCH: "Es wird die Entwicklung des Ich-Bewusstseins untersucht"
✅ RICHTIG: "Entwicklung des Ich-Bewusstseins vom antiken Griechenland bis zur Gegenwart"

❌ FALSCH: "Steiner erläutert die Bedeutung der Mysterien"
✅ RICHTIG: "Bedeutung der Mysterien für die geistige Entwicklung der Menschheit"

H3-ÜBERSCHRIFTEN:
${headingsText}

AUSGABE als JSON-Array:
[
  {
    "heading": "Überschrift-Text",
    "description": "Kurzbeschreibung in 20-30 Wörtern OHNE Meta-Sprache",
    "index": "^abc123"
  }
]

Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text.`;

              const tocResponse = await tocProvider.generateCompletion(tocPrompt, {
                maxTokens: 2000,
                temperature: 0.5
              });
              
              const cleanedResponse = tocResponse.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
              tableOfContents = JSON.parse(cleanedResponse);
              
            }
          }
        } catch (tocError) {
          console.error(`[TOC] Fehler bei TOC-Generierung:`, tocError.message);
          // Fahre fort ohne TOC
        }
      }
      
      // Generiere Keywords V3 (bei forceRegenerate: IMMER neu, auch wenn vorhanden)
      try {
        
        // Lade Template
        const template = await loadThemesKeywordsTemplate();
        
        // Lade existierendes Vokabular
        const existingKeywordsDB = await loadKeywordsDatabase();
        const existingVocabulary = [];
        const frequencyMap = {};
        
        Object.values(existingKeywordsDB).forEach(lectureData => {
          if (lectureData.keywords && Array.isArray(lectureData.keywords)) {
            lectureData.keywords.forEach(kw => {
              const term = kw.term.trim();
              if (!existingVocabulary.includes(term)) {
                existingVocabulary.push(term);
              }
              frequencyMap[term] = (frequencyMap[term] || 0) + 1;
            });
          }
        });
        
        // Hole Provider
        let provider;
        try {
          if (preferredProvider) {
            const { createProvider } = require('./llm-providers');
            provider = createProvider(preferredProvider);
            if (!provider.isAvailable()) {
              throw new Error(`${preferredProvider} nicht verfügbar`);
            }
          } else {
            provider = getProviderForTask('keywords');
          }
        } catch (providerError) {
          console.warn(`[KEYWORDS-V3] Provider-Fehler: ${providerError.message}, überspringe Keyword-Generierung`);
          provider = null;
        }
        
        if (template && provider) {
          // Generiere Keywords mit V3
          generatedKeywords = await generateKeywordsFlexibleWithBudget(
            lectureId,
            summaryData.headings,
            template,
            existingVocabulary,
            frequencyMap,
            provider,
            4  // Budget: 4 neue Keywords
          );
          
          // Extrahiere Metadaten
          const date = lecture?.date || lecture?.dateString || '';
          const year = date ? parseInt(date.substring(0, 4)) : null;
          const gaMatch = lectureId.match(/^GA(\d+)/);
          const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
          
          // Speichere Keywords in Keywords-DB
          await saveKeywordsToDatabase(lectureId, {
            lectureId: lectureId,
            date: date,
            year: year,
            gaVolume: gaVolume,
            summary: summaryData.summary || '',
            keywords: generatedKeywords,
            generated: new Date().toISOString(),
            generationMethod: 'flexible-v3-auto',
            maxNewKeywordsBudget: 4
          });
          
          const newKws = generatedKeywords.filter(k => k.matchType === 'new');
          
          // WICHTIG: Aktualisiere auch Summary-DB mit neuen Keywords (für Side Panel)
          try {
            await saveSummaryToDatabase(lectureId, {
              summary: summaryData.summary,
              headings: summaryData.headings || [],
              tableOfContents: tableOfContents,
              lectureKeywords: generatedKeywords,  // ← Neue Keywords auch hier!
              version: summaryData.version || 'v2'
            });
          } catch (updateError) {
            console.warn(`[KEYWORDS-V3] Warnung: Summary-DB konnte nicht aktualisiert werden:`, updateError.message);
          }
        }
      } catch (keywordError) {
        console.error(`[KEYWORDS-V3] Fehler bei Keyword-Generierung:`, keywordError.message);
        // Fahre fort mit den Keywords aus der Summary
      }
    }
    
    
    res.json({
      lectureId: lectureId,
      summary: summaryData.summary,
      headings: summaryData.headings || [],
      tableOfContents: tableOfContents,  // Neu generiertes TOC
      lectureKeywords: generatedKeywords,  // V3 Keywords wenn regeneriert
      keywords: generatedKeywords,  // Zusätzlich für Kompatibilität
      fromCache: false,
      version: summaryData.version || 'v2',
      paragraphCount: lecture.paragraphs?.length || 0,
      keywordsGenerated: forceRegenerate && generatedKeywords.length > 0,
      summaryReused: forceRegenerate && existingSummary && existingSummary.summary ? true : false
    });
    
  } catch (error) {
    console.error('✗ Zusammenfassungs-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// NEUE 3-BUTTON ARCHITEKTUR - UNIFIED BATCH APIs
// ============================================================================

/**
 * BUTTON 1: Batch-Generierung - Grundstruktur (S+H+TOC)
 * Überspringt Vorträge die bereits S+H+TOC haben
 */
app.post('/api/batch-generate-structure', async (req, res) => {
  try {
    const { 
      lectureIds = [], 
      preferredProvider = null,
      skipExisting = true,  // Standard: überspringen
      parallelChunkSize = 10  // NEU: Anzahl paralleler Verarbeitungen
    } = req.body;
    
    if (!Array.isArray(lectureIds) || lectureIds.length === 0) {
      return res.status(400).json({ error: 'Lecture IDs erforderlich (Array)' });
    }
    
    
    // Lade Vokabular
    const vocabularyTerms = await loadSeedVocabulary();
    
    // Lade existierende Summary-DB
    const summaryDB = await loadSummaryDatabase();
    
    const results = {
      processed: 0,
      skipped: 0,
      failed: 0,
      errors: []
    };
    
    // Hilfsfunktion: Verarbeite einen einzelnen Vortrag
    const processLecture = async (lectureId, index, total) => {
      try {
        // Prüfe ob bereits vorhanden
        const existingData = summaryDB[lectureId];
        const hasStructure = existingData && existingData.summary && 
                           existingData.headings && existingData.headings.length > 0 &&
                           existingData.tableOfContents && existingData.tableOfContents.length > 0;
        
        if (skipExisting && hasStructure) {
          return { success: true, skipped: true, lectureId };
        }
        
        
        // Generiere S+H+TOC
        const generatedData = await generateUnifiedLectureData(lectureId, 'structure', {
          provider: preferredProvider,
          vocabularyTerms: vocabularyTerms
        });
        
        // Speichere in Summary-DB
        await saveSummaryToDatabase(lectureId, {
          summary: generatedData.summary,
          headings: generatedData.headings,
          tableOfContents: generatedData.tableOfContents,
          lectureKeywords: [],  // Noch keine Keywords
          version: generatedData.version,
          generated: generatedData.generated
        });
        
        return { success: true, skipped: false, lectureId };
        
      } catch (error) {
        console.error(`[BATCH-STRUCTURE] ✗ ${lectureId} fehlgeschlagen:`, error.message);
        return { success: false, skipped: false, lectureId, error: error.message };
      }
    };
    
    // Verarbeite in parallelen Chunks
    for (let i = 0; i < lectureIds.length; i += parallelChunkSize) {
      const chunk = lectureIds.slice(i, i + parallelChunkSize);
      const chunkNumber = Math.floor(i / parallelChunkSize) + 1;
      const totalChunks = Math.ceil(lectureIds.length / parallelChunkSize);
      
      
      // Verarbeite Chunk parallel
      const chunkResults = await Promise.allSettled(
        chunk.map((lectureId, idx) => processLecture(lectureId, i + idx, lectureIds.length))
      );
      
      // Sammle Ergebnisse
      chunkResults.forEach(result => {
        if (result.status === 'fulfilled') {
          if (result.value.success && result.value.skipped) {
            results.skipped++;
          } else if (result.value.success) {
            results.processed++;
          } else {
            results.failed++;
            results.errors.push({ 
              lectureId: result.value.lectureId, 
              error: result.value.error 
            });
          }
        } else {
          results.failed++;
          results.errors.push({ 
            lectureId: 'unknown', 
            error: result.reason?.message || 'Unbekannter Fehler' 
          });
        }
      });
      
    }
    
    
    res.json({
      success: true,
      ...results
    });
    
  } catch (error) {
    console.error('[BATCH-STRUCTURE] Kritischer Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * BUTTON 2: Batch-Generierung - Keywords ergänzen
 * Überspringt Vorträge die bereits Keywords haben
 * Benötigt existierende S+H+TOC
 */
app.post('/api/batch-generate-keywords', async (req, res) => {
  try {
    const { 
      lectureIds = [], 
      preferredProvider = null,
      skipExisting = true,
      parallelChunkSize = 10  // NEU: Anzahl paralleler Verarbeitungen
    } = req.body;
    
    if (!Array.isArray(lectureIds) || lectureIds.length === 0) {
      return res.status(400).json({ error: 'Lecture IDs erforderlich (Array)' });
    }
    
    
    // Lade Vokabular und Template
    const vocabularyTerms = await loadSeedVocabulary();
    const template = await loadThemesKeywordsTemplate();
    
    // Lade existierende Datenbanken
    const summaryDB = await loadSummaryDatabase();
    const keywordsDB = await loadKeywordsDatabase();
    
    // Baue Frequency Map aus existierenden Keywords
    const frequencyMap = calculateKeywordFrequency(keywordsDB);
    
    const results = {
      processed: 0,
      skipped: 0,
      failed: 0,
      errors: []
    };
    
    // Hilfsfunktion: Verarbeite einen einzelnen Vortrag
    const processLecture = async (lectureId, index, total) => {
      try {
        // Prüfe ob MINDESTENS Summary + Headings vorhanden (TOC wird neu generiert wenn nötig)
        const existingData = summaryDB[lectureId];
        if (!existingData || !existingData.summary || !existingData.headings || existingData.headings.length === 0) {
          return { success: true, skipped: true, reason: 'no-structure', lectureId };
        }
        
        // Prüfe ob bereits Keywords in SUMMARY-DB vorhanden (das ist was im Browser angezeigt wird)
        // keywords-database.json wird ignoriert, da diese synchronisiert wird
        const hasKeywordsInSummaryDB = existingData.lectureKeywords && existingData.lectureKeywords.length > 0;
        
        if (skipExisting && hasKeywordsInSummaryDB) {
          return { success: true, skipped: true, reason: 'already-exists', lectureId };
        }
        
        
        // Generiere TOC + Keywords
        const generatedData = await generateUnifiedLectureData(lectureId, 'keywords', {
          provider: preferredProvider,
          vocabularyTerms: vocabularyTerms,
          frequencyMap: frequencyMap
        });
        
        const keywords = generatedData.keywords;
        const tableOfContents = generatedData.tableOfContents;
        
        // Speichere in Summary-DB (aktualisiere TOC + Keywords)
        await saveSummaryToDatabase(lectureId, {
          summary: existingData.summary,
          headings: existingData.headings,
          tableOfContents: tableOfContents,  // NEU: TOC überschreiben
          lectureKeywords: keywords,  // NEU: Keywords hinzufügen
          version: existingData.version || 'v2-unified',
          generated: existingData.generated
        });
        
        // Extrahiere Metadaten für Keywords-DB
        const lecture = fullLectures[lectureId];
        const date = lecture?.date || lecture?.dateString || '';
        const year = date ? parseInt(date.substring(0, 4)) : null;
        const gaMatch = lectureId.match(/^GA(\d+)/);
        const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
        
        // Speichere parallel in Keywords-DB
        await saveKeywordsToDatabase(lectureId, {
          lectureId: lectureId,
          date: date,
          year: year,
          gaVolume: gaVolume,
          summary: existingData.summary || '',
          keywords: keywords,
          generated: new Date().toISOString(),
          generationMethod: 'unified-batch-keywords'
        });
        
        return { success: true, skipped: false, lectureId, keywordsCount: keywords.length };
        
      } catch (error) {
        console.error(`[BATCH-KEYWORDS] ✗ ${lectureId} fehlgeschlagen:`, error.message);
        return { success: false, skipped: false, lectureId, error: error.message };
      }
    };
    
    // Verarbeite in parallelen Chunks
    for (let i = 0; i < lectureIds.length; i += parallelChunkSize) {
      const chunk = lectureIds.slice(i, i + parallelChunkSize);
      const chunkNumber = Math.floor(i / parallelChunkSize) + 1;
      const totalChunks = Math.ceil(lectureIds.length / parallelChunkSize);
      
      
      // Verarbeite Chunk parallel
      const chunkResults = await Promise.allSettled(
        chunk.map((lectureId, idx) => processLecture(lectureId, i + idx, lectureIds.length))
      );
      
      // Sammle Ergebnisse
      chunkResults.forEach(result => {
        if (result.status === 'fulfilled') {
          if (result.value.success && result.value.skipped) {
            results.skipped++;
          } else if (result.value.success) {
            results.processed++;
          } else {
            results.failed++;
            results.errors.push({ 
              lectureId: result.value.lectureId, 
              error: result.value.error 
            });
          }
        } else {
          results.failed++;
          results.errors.push({ 
            lectureId: 'unknown', 
            error: result.reason?.message || 'Unbekannter Fehler' 
          });
        }
      });
      
    }
    
    
    res.json({
      success: true,
      ...results
    });
    
  } catch (error) {
    console.error('[BATCH-KEYWORDS] Kritischer Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * BUTTON 3: Batch-Generierung - Alles neu (S+H+TOC+KW)
 * Überschreibt IMMER existierende Daten
 */
app.post('/api/batch-regenerate-all', async (req, res) => {
  try {
    const { 
      lectureIds = [], 
      preferredProvider = null,
      parallelChunkSize = 10  // NEU: Anzahl paralleler Verarbeitungen
    } = req.body;
    
    if (!Array.isArray(lectureIds) || lectureIds.length === 0) {
      return res.status(400).json({ error: 'Lecture IDs erforderlich (Array)' });
    }
    
    
    // Lade Vokabular und Template
    const vocabularyTerms = await loadSeedVocabulary();
    const template = await loadThemesKeywordsTemplate();
    
    // Lade existierende Keywords-DB für Frequency Map
    const keywordsDB = await loadKeywordsDatabase();
    const frequencyMap = calculateKeywordFrequency(keywordsDB);
    
    const results = {
      processed: 0,
      failed: 0,
      errors: []
    };
    
    // Hilfsfunktion: Verarbeite einen einzelnen Vortrag
    const processLecture = async (lectureId, index, total) => {
      try {
        
        // Generiere ALLES in einem Call
        const generatedData = await generateUnifiedLectureData(lectureId, 'full', {
          provider: preferredProvider,
          vocabularyTerms: vocabularyTerms,
          frequencyMap: frequencyMap,
          forceRegenerate: true
        });
        
        // Speichere in Summary-DB
        await saveSummaryToDatabase(lectureId, {
          summary: generatedData.summary,
          headings: generatedData.headings,
          tableOfContents: generatedData.tableOfContents,
          lectureKeywords: generatedData.keywords,
          version: generatedData.version,
          generated: generatedData.generated
        });
        
        // Extrahiere Metadaten für Keywords-DB
        const lecture = fullLectures[lectureId];
        const date = lecture?.date || lecture?.dateString || '';
        const year = date ? parseInt(date.substring(0, 4)) : null;
        const gaMatch = lectureId.match(/^GA(\d+)/);
        const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
        
        // Speichere parallel in Keywords-DB
        await saveKeywordsToDatabase(lectureId, {
          lectureId: lectureId,
          date: date,
          year: year,
          gaVolume: gaVolume,
          summary: generatedData.summary || '',
          keywords: generatedData.keywords,
          generated: new Date().toISOString(),
          generationMethod: 'unified-batch-full'
        });
        
        return { success: true, lectureId };
        
      } catch (error) {
        console.error(`[BATCH-REGENERATE] ✗ ${lectureId} fehlgeschlagen:`, error.message);
        return { success: false, lectureId, error: error.message };
      }
    };
    
    // Verarbeite in parallelen Chunks
    for (let i = 0; i < lectureIds.length; i += parallelChunkSize) {
      const chunk = lectureIds.slice(i, i + parallelChunkSize);
      const chunkNumber = Math.floor(i / parallelChunkSize) + 1;
      const totalChunks = Math.ceil(lectureIds.length / parallelChunkSize);
      
      
      // Verarbeite Chunk parallel
      const chunkResults = await Promise.allSettled(
        chunk.map((lectureId, idx) => processLecture(lectureId, i + idx, lectureIds.length))
      );
      
      // Sammle Ergebnisse
      chunkResults.forEach(result => {
        if (result.status === 'fulfilled' && result.value.success) {
          results.processed++;
        } else {
          results.failed++;
          const error = result.status === 'rejected' 
            ? result.reason?.message || 'Unbekannter Fehler'
            : result.value.error;
          results.errors.push({ 
            lectureId: result.value?.lectureId || 'unknown', 
            error 
          });
        }
      });
      
    }
    
    
    res.json({
      success: true,
      ...results
    });
    
  } catch (error) {
    console.error('[BATCH-REGENERATE] Kritischer Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/check-summary/:gaNumber/:lectureNum', async (req, res) => {
  try {
    // VALIDIERUNG ENTFERNT - verursachte Probleme
    const lectureId = `${req.params.gaNumber}/${req.params.lectureNum}`;
    
    console.log(`[CHECK-SUMMARY] Prüfe zentrale DB für ${lectureId}`);
    
    const summaryDB = await loadSummaryDatabase();
    
    // Prüfe exakte Übereinstimmung
    if (summaryDB[lectureId]) {
      const dbData = summaryDB[lectureId];
      
      console.log(`[CHECK-SUMMARY] ✓ Zusammenfassung existiert für ${lectureId} (Version: ${dbData.version || 'v1'})`);
      
      return res.json({
        exists: true,
        lectureId: lectureId,
        summary: dbData.summary,
        headings: dbData.headings || [],
        tableOfContents: dbData.tableOfContents || [],
        lectureKeywords: dbData.lectureKeywords || [],
        version: dbData.version || 'v1'
      });
    }
    
    // DEBUG: Zeige verfügbare IDs für dieses GA
    const availableIds = Object.keys(summaryDB).filter(id => id.startsWith(req.params.gaNumber));
    if (availableIds.length > 0) {
      console.log(`[CHECK-SUMMARY] Verfügbare IDs für ${req.params.gaNumber}:`, availableIds.slice(0, 10));
      console.log(`[CHECK-SUMMARY] Gesuchte ID: ${lectureId}`);
      console.log(`[CHECK-SUMMARY] Exakte Übereinstimmung: ${availableIds.includes(lectureId)}`);
      
      // Versuche alternative Formatierungen (z.B. GA052/1 vs GA052/01)
      const lectureNum = parseInt(req.params.lectureNum);
      const alternativeId1 = `${req.params.gaNumber}/${lectureNum}`; // ohne führende Null
      const alternativeId2 = `${req.params.gaNumber}/${lectureNum.toString().padStart(2, '0')}`; // mit führender Null
      
      let foundData = null;
      let foundId = null;
      
      if (summaryDB[alternativeId1] && alternativeId1 !== lectureId) {
        foundData = summaryDB[alternativeId1];
        foundId = alternativeId1;
      } else if (summaryDB[alternativeId2] && alternativeId2 !== lectureId) {
        foundData = summaryDB[alternativeId2];
        foundId = alternativeId2;
      }
      
      if (foundData) {
        console.log(`[CHECK-SUMMARY] ✓ Alternative ID gefunden: ${foundId} statt ${lectureId}`);
        return res.json({
          exists: true,
          lectureId: foundId,
          summary: foundData.summary,
          headings: foundData.headings || [],
          tableOfContents: foundData.tableOfContents || [],
          lectureKeywords: foundData.lectureKeywords || [],
          version: foundData.version || 'v1'
        });
      }
    } else {
      console.log(`[CHECK-SUMMARY] Keine IDs für ${req.params.gaNumber} gefunden`);
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

// ============================================================================
// HILFSFUNKTIONEN FÜR SUMMARY V2
// ============================================================================

// Lade Seed-Vokabular aus themes-keywords-template.json
async function loadSeedVocabulary() {
  try {
    const templatePath = path.join(__dirname, 'themes-keywords-template.json');
    const fileContent = fsSync.readFileSync(templatePath, 'utf8');
    const data = JSON.parse(fileContent);
    
    const vocabulary = [];
    Object.values(data.themes || {}).forEach(theme => {
      if (theme.keywords && Array.isArray(theme.keywords)) {
        vocabulary.push(...theme.keywords);
      }
    });
    
    return vocabulary;
  } catch (error) {
    console.warn('[VOCAB] Fehler beim Laden des Seed-Vokabulars:', error.message);
    return [];
  }
}

// Intelligentes Sampling für lange Vorträge
// Nimmt repräsentative Absätze pro H3-Abschnitt statt kompletten Text
function sampleParagraphsForLongLectures(paragraphs, maxParagraphs = 60) {
  if (paragraphs.length <= maxParagraphs) {
    return paragraphs; // Kurzer Vortrag: alle nehmen
  }
  
  
  // Strategie: Gleichmäßig verteilt über den Text
  const sampledIndices = [];
  const step = Math.floor(paragraphs.length / maxParagraphs);
  
  for (let i = 0; i < paragraphs.length; i += step) {
    sampledIndices.push(i);
    if (sampledIndices.length >= maxParagraphs) break;
  }
  
  // Stelle sicher, dass letzter Absatz dabei ist
  if (!sampledIndices.includes(paragraphs.length - 1)) {
    sampledIndices[sampledIndices.length - 1] = paragraphs.length - 1;
  }
  
  const sampled = sampledIndices.map(i => paragraphs[i]);
  
  return sampled;
}

// ============================================================================
// NEUE V2 SUMMARY-GENERIERUNG
// ============================================================================

// Hilfsfunktion: Entfernt Meta-Sprache aus Summary und TOC
function removeMetaLanguage(text) {
  if (!text) return text;
  
  let cleaned = text;
  
  // 1. Entferne Sätze die mit "Der Vortrag GA..." beginnen
  cleaned = cleaned.replace(/^Der Vortrag\s+GA\d{3}[a-z]?\/\d+\s+(bietet|gibt|zeigt|behandelt|beleuchtet|erörtert)\s+/gi, '');
  cleaned = cleaned.replace(/^Der Vortrag\s+(bietet|gibt|zeigt|behandelt|beleuchtet|erörtert|liefert)\s+(einen|eine|ein)?\s*/gi, '');
  
  // 2. Entferne "Rudolf Steiner" / "Steiner" am Satzanfang
  cleaned = cleaned.replace(/^Rudolf Steiner\s+(beschreibt|erklärt|erläutert|zeigt|stellt dar|erörtert|behandelt|untersucht|beleuchtet|schildert|bietet)\s+/gi, '');
  cleaned = cleaned.replace(/^Steiner\s+(beschreibt|erklärt|erläutert|zeigt|stellt dar|erörtert|behandelt|untersucht|beleuchtet|schildert|bietet)\s+/gi, '');
  
  // 3. Entferne "Es wird..." Konstruktionen
  cleaned = cleaned.replace(/Es wird\s+(betont|erwähnt|gezeigt|erklärt|hervorgehoben|deutlich|dargelegt),?\s+(dass|wie)?\s*/gi, '');
  cleaned = cleaned.replace(/\.\s*Es wird\s+(betont|erwähnt|gezeigt|erklärt|hervorgehoben|deutlich|dargelegt),?\s+(dass|wie)?\s*/gi, '. ');
  
  // 4. Entferne "Die X soll/sollte helfen/unterstützen..." → "Die X hilft/unterstützt..."
  cleaned = cleaned.replace(/\b(soll|sollte|sollen)\s+(helfen|unterstützen|ermöglichen|klären|begleiten|fördern)/gi, (match, modal, verb) => {
    const verbMap = {
      'helfen': 'hilft',
      'unterstützen': 'unterstützt',
      'ermöglichen': 'ermöglicht',
      'klären': 'klärt',
      'begleiten': 'begleitet',
      'fördern': 'fördert'
    };
    return verbMap[verb.toLowerCase()] || verb;
  });
  
  // 5. Entferne andere Meta-Konstruktionen
  cleaned = cleaned.replace(/^(Im|In diesem|Dieser)\s+Vortrag\s+/gi, '');
  cleaned = cleaned.replace(/^(Der|Die|Das)\s+(Text|Redner|Vortragende)\s+(beschreibt|erklärt|zeigt)\s+/gi, '');
  
  // 6. Entferne Meta-Phrasen mitten im Text
  cleaned = cleaned.replace(/,\s+wie\s+Rudolf Steiner\s+(beschreibt|erklärt|erläutert|zeigt)/gi, '');
  cleaned = cleaned.replace(/,\s+wie\s+Steiner\s+(beschreibt|erklärt|erläutert|zeigt)/gi, '');
  cleaned = cleaned.replace(/,\s+wie\s+(im Vortrag|hier|der Text)\s+(beschrieben|erklärt|erläutert|gezeigt)/gi, '');
  
  // 7. Bereinige Doppelpunkte und Kommata nach Entfernungen
  cleaned = cleaned.replace(/^[,\s]+/, '');  // Führende Kommata entfernen
  cleaned = cleaned.replace(/\s{2,}/g, ' '); // Doppelte Leerzeichen entfernen
  
  // 8. Kapitalisiere ersten Buchstaben
  cleaned = cleaned.trim();
  if (cleaned.length > 0) {
    cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  }
  
  return cleaned;
}

// Vollständige Generierung (neue Vorträge): Summary + H3/H4 + TOC + Keywords
async function generateFullSummaryV2(lecture, vocabulary, preferredProvider = null) {
  const provider = preferredProvider 
    ? getSpecificProvider(preferredProvider)
    : getProviderForTask('summary');
  
  // Bereite Text vor
  let paragraphsToAnalyze = lecture.paragraphs;
  const estimatedTokens = JSON.stringify(paragraphsToAnalyze).length / 4;
  
  // Bei langen Vorträgen: Intelligentes Sampling
  if (estimatedTokens > 180000) {
    paragraphsToAnalyze = sampleParagraphsForLongLectures(paragraphsToAnalyze, 80);
  }
  
  const fullText = paragraphsToAnalyze
    .map((p, idx) => {
      const content = p.content || p.text || '';
      const paraIndex = p.index || `para_${idx}`;
      return `[Index: ${paraIndex}]\n${content}`;
    })
    .filter(text => text.trim().length > 0)
    .join('\n\n');
  
  // Top 50 häufigste Vokabular-Keywords
  const topVocab = vocabulary.slice(0, 50);
  
  const prompt = `🚨 KRITISCHE REGEL - SOFORT LESEN 🚨
SCHREIBE NIEMALS ÜBER DEN VORTRAG ODER DEN REDNER!
SCHREIBE NUR ÜBER DIE INHALTE SELBST!

STRIKT VERBOTEN IN SUMMARY UND TABLE OF CONTENTS:
❌ "Rudolf Steiner..." / "Steiner..."
❌ "Im Vortrag..." / "Der Vortrag..." / "Dieser Vortrag..."
❌ "Es wird..." / "Hier wird..." / "Der Text..."
❌ "beschreibt", "erklärt", "zeigt", "erörtert", "behandelt"
❌ Jede Erwähnung des Redners oder des Vortrags selbst

✅ RICHTIG: Schreibe wie eine sachliche Enzyklopädie
✅ NUR die Inhalte, Konzepte, Ideen selbst beschreiben
✅ Als würdest du ein Lexikon über die Themen schreiben

BEISPIEL FALSCH: "Rudolf Steiner erläutert die Entwicklung des Bewusstseins..."
BEISPIEL RICHTIG: "Die Entwicklung des Bewusstseins vollzieht sich von der Antike..."

BEISPIEL FALSCH: "Der Vortrag behandelt die Mysterien der Antike..."
BEISPIEL RICHTIG: "Die antiken Mysterien bilden die Brücke zwischen..."

NOCH EINMAL ZUR KLARSTELLUNG:
- Du bist kein Redakteur, der einen Vortrag beschreibt
- Du bist ein Enzyklopädie-Autor, der Fakten beschreibt
- Schreibe DIREKT über die Themen, nicht über den Vortrag

---

VORTRAG: ${lecture.fileName || lecture.title || lecture.ID}
${lecture.location ? `ORT: ${lecture.location}` : ''}
${lecture.date ? `DATUM: ${lecture.date}` : ''}
Absätze: ${lecture.paragraphs.length}

SEED-VOKABULAR (${vocabulary.length} Begriffe, häufigste):
${topVocab.join(', ')}

AUFGABE:
1. ZUSAMMENFASSUNG (100-150 Wörter) - DIREKT die Inhalte beschreiben, NICHT den Vortrag
   🚨 ERINNERE DICH: Kein "Steiner", kein "Vortrag", keine Meta-Sprache!

2. HIERARCHISCHE GLIEDERUNG - 🔴 KRITISCH WICHTIG:
   
   H3 = HAUPTTHEMA (große thematische Abschnitte)
   - Markiert einen neuen Hauptgedanken oder großes Themengebiet
   - Beispiele: "Die Entwicklung des Bewusstseins", "Die Mysterien der Antike"
   
   H4 = UNTERTHEMA (Aspekte innerhalb eines H3-Hauptthemas)
   - Gehört IMMER zu einem H3-Thema und vertieft/untergliedert dieses
   - Beispiele unter H3 "Die Entwicklung des Bewusstseins":
     * H4: "Das alte Bewusstsein in Atlantis"
     * H4: "Der Übergang zur nachatlantischen Zeit"
     * H4: "Das moderne Ich-Bewusstsein"
   
   🚨 KRITISCH: KEINE ÜBERSCHRIFTEN IN GEDICHTE!
   - Ein Gedicht besteht aus mindestens zwei aufeinanderfolgenden Zeilen, die durch Absatzmarken getrennt sind und weniger als 90 Zeichen pro Zeile haben
   - In solchen Bereichen DARFST DU ABSOLUT KEINE Überschriften (H3 oder H4) einfügen!
   - Prüfe VOR jeder Überschrift, ob der Bereich ein Gedicht ist!
   
   🎯 STRUKTUR-REGEL:
   - Erstelle 5-8 H3-Hauptthemen gleichmäßig über den Vortrag verteilt
   - JEDES H3 MUSS 2-4 H4-Unterthemen haben
   - H4 folgen direkt nach dem zugehörigen H3 (nicht isoliert)

3. INHALTSVERZEICHNIS - Für jede H3: Prägnante Kurzbeschreibung (10-15 Wörter) was in diesem Abschnitt behandelt wird
   ⚠️ ABSOLUT VERBOTEN - KEINE META-SPRACHE in Beschreibungen!
   ❌ NIEMALS: "Rudolf Steiner beschreibt...", "Steiner erklärt...", "Untersucht wird...", "Diskussion über...", "Analyse der...", "Der Vortrag behandelt..."
   ✅ STATTDESSEN: Direkte, sachliche Formulierung wie in einem Lexikon
   ✅ BEISPIELE: "Transformation Roms zur Kirchenmacht", "Die fortbestehende Würde des Menschen", "Entwicklung des Ich-Bewusstseins"
5. SCHLAGWORTE (maximal 12 Keywords):
   
   🚨 SCHRITT 1: TITEL ANALYSIEREN (ABSOLUTE PRIORITÄT - PFLICHT-KEYWORDS!)
   
   EXTRAHIERE die HAUPTBEGRIFFE (Substantive) aus dem Vortragstitel
   
   ✅ BEISPIELE FÜR PFLICHT-KEYWORDS AUS TITELN:
   → "DIE SEELE DER TIERE..." → Keyword: "Tiere" (MUSS erscheinen!)
   → "DIE SOGENANNTEN GEFAHREN..." → Keyword: "Gefahren" (MUSS erscheinen!)
   → "BIBEL UND WEISHEIT" → Keyword: "Bibel" (MUSS erscheinen!)
   → "DER LEBENSLAUF DES MENSCHEN" → Keyword: "Lebenslauf" (MUSS erscheinen!)
   → "WEISHEIT UND GESUNDHEIT" → Keyword: "Gesundheit" (MUSS erscheinen!)
   → "BLUT IST EIN GANZ BESONDERER SAFT" → Keyword: "Blut" (MUSS erscheinen!)
   
   ❌ NUR IGNORIEREN wenn Titel NICHT inhaltlich:
   → "Erster Vortrag", "Zweiter Vortrag", "Öffentlicher Vortrag"
   
   ⚠️ KRITISCH: Diese Titel-Keywords erscheinen oft AUCH in Summary und H3!
      → Das ist KEIN Problem! Verwende sie trotzdem als Keyword!
   
   🔴 SCHRITT 2: SUMMARY ERGÄNZEN (falls noch kein Hauptthema/Person aus Titel)
   - Falls Titel keine klare Person/Hauptthema hatte:
     * Extrahiere aus der ZUSAMMENFASSUNG (Punkt 1) die wichtigste Person ODER das Hauptthema
     * ⚠️ NIEMALS: "Rudolf Steiner" (er ist der Vortragende, kein Inhalt!)
     * ✅ Personen: "Platon", "Kant", "Buddha", "Christus", "Paracelsus" etc.
   
   🔴 SCHRITT 3: H3-ABSCHNITTE (10-11 weitere Keywords)
   - Wähle die wichtigsten Begriffe aus dem Vortragstextinhalt basierend auf den H3-Abschnitten
   - Bevorzuge das Seed-Vokabular (iteratives Wachstum)

WICHTIG ZU INDIZES:
- Jeder Absatz ist markiert: [Index: ^abc123]
- H3/H4: Index gibt an, VOR welchem Absatz die Überschrift eingefügt wird
- Keywords: Index des H3-Abschnitts, wo das Thema hauptsächlich behandelt wird
- tableOfContents: Gleicher Index wie die entsprechende H3

SCHLAGWORT-REGELN (WICHTIG):
- MAXIMAL 12 Keywords total!
- 1-3 Worte, 1-2 Substantive
- Nominativ (z.B. "Mittelalterliche Philosophie" NICHT "mittelalterlichen Philosophie")
- BEVORZUGE STARK Seed-Vokabular (iterativ wachsend)
- NUR neue Keywords wenn kein passendes im Vokabular existiert
- Analysiere Summary UND TEXTINHALT der H3-Abschnitte
- Jedes Keyword mit Index des H3-Abschnitts wo es hauptsächlich behandelt wird
- Verteile Keywords über verschiedene H3-Abschnitte (nicht alle aus einem Thema)
- ⚠️ KRITISCH: KEINE doppelten Keywords! Jeder Begriff nur EINMAL pro Vortrag

AUSGABEFORMAT (JSON):
{
  "summary": "Zusammenfassung in 100-150 Wörtern",
  "headings": [
    {"index": "^8ju77n", "text": "Die griechische Philosophie", "level": "h3"},
    {"index": "^8ju77n", "text": "Thales und die Wasserlehre", "level": "h4"},
    {"index": "^9kv88p", "text": "Heraklit und der Fluss des Werdens", "level": "h4"},
    {"index": "^a2w99q", "text": "Pythagoras und die Zahl", "level": "h4"},
    {"index": "^r38v26", "text": "Parmenides und die Kritik", "level": "h3"},
    {"index": "^r38v26", "text": "Die Lehre vom unveränderlichen Sein", "level": "h4"},
    {"index": "^s49w37", "text": "Kritik der Sinneswahrnehmung", "level": "h4"}
  ],
  "tableOfContents": [
    {
      "heading": "Die griechische Philosophie",
      "description": "Die ersten Denker suchten den Urgrund in natürlichen Elementen wie Wasser und Luft",
      "index": "^8ju77n"
    },
    {
      "heading": "Parmenides und die Kritik",
      "description": "Kritik der Sinnenwelt und die Suche nach ewiger Wahrheit durch reines Denken",
      "index": "^r38v26"
    }
  ],
  "lectureKeywords": [
    {"term": "Antike Philosophie", "index": "^8ju77n", "confidence": 0.95},
    {"term": "Vorsokratiker", "index": "^8ju77n", "confidence": 0.9},
    {"term": "Erkenntnistheorie", "index": "^r38v26", "confidence": 0.85}
  ]
}

VORTRAG-TEXT:
${fullText}

AUSGABE (nur JSON, keine Erklärungen):`;

  try {
    
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 6000,
      temperature: 0.3  // Niedrig für deterministischeres, regelkonformeres Verhalten
    });
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const data = JSON.parse(responseText);
    
    // POST-PROCESSING: Entferne Meta-Sprache automatisch
    data.summary = removeMetaLanguage(data.summary);
    if (data.tableOfContents) {
      data.tableOfContents.forEach(toc => {
        toc.description = removeMetaLanguage(toc.description);
      });
    }
    
    
    return {
      summary: data.summary,
      headings: data.headings || [],
      tableOfContents: data.tableOfContents || [],
      lectureKeywords: data.lectureKeywords || [],
      version: 'v2'
    };
    
  } catch (error) {
    console.error('[SUMMARY-V2] Fehler:', error.message);
    throw error;
  }
}

// Ergänzung für alte Summaries: Nur TOC + Keywords hinzufügen
async function enhanceSummaryV2(lecture, existingSummary, vocabulary, preferredProvider = null) {
  const provider = preferredProvider 
    ? getSpecificProvider(preferredProvider)
    : getProviderForTask('summary');
  
  const h3Headings = (existingSummary.headings || []).filter(h => h.level === 'h3');
  
  if (h3Headings.length === 0) {
    return existingSummary;
  }
  
  // Bereite Text vor (mit Sampling bei langen Vorträgen)
  let paragraphsToAnalyze = lecture.paragraphs;
  const estimatedTokens = JSON.stringify(paragraphsToAnalyze).length / 4;
  
  if (estimatedTokens > 180000) {
    paragraphsToAnalyze = sampleParagraphsForLongLectures(paragraphsToAnalyze, 80);
  }
  
  const fullText = paragraphsToAnalyze
    .map((p, idx) => {
      const content = p.content || p.text || '';
      const paraIndex = p.index || `para_${idx}`;
      return `[Index: ${paraIndex}]\n${content}`;
    })
    .filter(text => text.trim().length > 0)
    .join('\n\n');
  
  const h3List = h3Headings.map((h, i) => `${i+1}. ${h.text} (Index: ${h.index})`).join('\n');
  const topVocab = vocabulary.slice(0, 50);
  
  const prompt = `🚨 KRITISCHE REGEL - TABLE OF CONTENTS 🚨
NIEMALS ÜBER DEN VORTRAG ODER REDNER SCHREIBEN!
NUR DIE INHALTE SELBST BESCHREIBEN!

STRIKT VERBOTEN:
❌ "Rudolf Steiner..." / "Steiner..."
❌ "Der Vortrag..." / "Im Vortrag..."
❌ "beschreibt", "erklärt", "zeigt", "behandelt"

✅ RICHTIG: Schreibe wie in einer Enzyklopädie - NUR über die Themen selbst

---

Ergänze eine bestehende Vortragszusammenfassung um Inhaltsverzeichnis und Schlagworte.

VORTRAG: ${lecture.fileName || lecture.title || lecture.ID}

BESTEHENDE SUMMARY:
"${existingSummary.summary}"

BESTEHENDE H3-ÜBERSCHRIFTEN (${h3Headings.length}):
${h3List}

SEED-VOKABULAR (${vocabulary.length} Begriffe, häufigste):
${topVocab.join(', ')}

AUFGABE:
1. INHALTSVERZEICHNIS - Für jede H3: 10-15 Wörter DIREKT über die Inhalte
   🚨 ERINNERE DICH: Keine Meta-Sprache! Schreibe über die Themen, nicht über den Vortrag!
2. SCHLAGWORTE (maximal 12 Keywords):
   
   🚨 SCHRITT 1: TITEL ANALYSIEREN (ABSOLUTE PRIORITÄT - PFLICHT-KEYWORDS!)
   
   EXTRAHIERE die HAUPTBEGRIFFE (Substantive) aus dem Vortragstitel
   
   ✅ BEISPIELE FÜR PFLICHT-KEYWORDS AUS TITELN:
   → "DIE SEELE DER TIERE..." → Keyword: "Tiere" (MUSS erscheinen!)
   → "DIE SOGENANNTEN GEFAHREN..." → Keyword: "Gefahren" (MUSS erscheinen!)
   → "BIBEL UND WEISHEIT" → Keyword: "Bibel" (MUSS erscheinen!)
   → "DER LEBENSLAUF DES MENSCHEN" → Keyword: "Lebenslauf" (MUSS erscheinen!)
   → "WEISHEIT UND GESUNDHEIT" → Keyword: "Gesundheit" (MUSS erscheinen!)
   → "BLUT IST EIN GANZ BESONDERER SAFT" → Keyword: "Blut" (MUSS erscheinen!)
   
   ❌ NUR IGNORIEREN wenn Titel NICHT inhaltlich:
   → "Erster Vortrag", "Zweiter Vortrag", "Öffentlicher Vortrag"
   
   ⚠️ KRITISCH: Diese Titel-Keywords erscheinen oft AUCH in Summary und H3!
      → Das ist KEIN Problem! Verwende sie trotzdem als Keyword!
   
   🔴 SCHRITT 2: SUMMARY ERGÄNZEN (falls noch kein Hauptthema/Person aus Titel)
   - Falls Titel keine klare Person/Hauptthema hatte:
     * Identifiziere aus der BESTEHENDEN SUMMARY die Hauptperson ODER das Hauptthema
     * ⚠️ NIEMALS: "Rudolf Steiner" (er ist der Vortragende, kein Inhalt!)
     * ✅ Personen: "Platon", "Kant", "Shakespeare", "Buddha", "Christus" etc.
   
   🔴 SCHRITT 3: H3-ABSCHNITTE (10-11 weitere Keywords)
   - Wähle die wichtigsten Begriffe aus Summary + Vortragstextinhalt

SCHLAGWORT-REGELN:
- MAXIMAL 12 Keywords total!
- 1-3 Worte, 1-2 Substantive, Nominativ
- BEVORZUGE STARK Seed-Vokabular (iterativ)
- Analysiere Summary UND Textinhalt der H3-Abschnitte
- Jedes Keyword mit Index des passendsten H3-Abschnitts
- Verteile über verschiedene Abschnitte
- ⚠️ KRITISCH: KEINE doppelten Keywords! Jeder Begriff nur EINMAL pro Vortrag

AUSGABEFORMAT (JSON):
{
  "tableOfContents": [
    {
      "heading": "Die ersten griechischen Naturphilosophen",
      "description": "Prägnante Beschreibung 10-15 Wörter",
      "index": "^8ju77n"
    }
  ],
  "lectureKeywords": [
    {"term": "Antike Philosophie", "index": "^8ju77n", "confidence": 0.95}
  ]
}

VORTRAG-TEXT:
${fullText}

AUSGABE (nur JSON):`;

  try {
    
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 4000,
      temperature: 0.3  // Niedrig für regelkonformeres Verhalten
    });
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const data = JSON.parse(responseText);
    
    // POST-PROCESSING: Entferne Meta-Sprache aus TOC
    if (data.tableOfContents) {
      data.tableOfContents.forEach(toc => {
        toc.description = removeMetaLanguage(toc.description);
      });
    }
    
    
    // Kombiniere mit bestehender Summary
    return {
      ...existingSummary,
      tableOfContents: data.tableOfContents || [],
      lectureKeywords: data.lectureKeywords || [],
      version: 'v2'
    };
    
  } catch (error) {
    console.error('[ENHANCE-V2] Fehler:', error.message);
    // Bei Fehler: Behalte alte Summary unverändert
    return existingSummary;
  }
}

// ============================================================================
// HAUPT-ROUTER: Entscheidet zwischen V1 und V2
// ============================================================================

async function generateLectureSummary(lecture, existingSummary = null, mode = 'auto', preferredProvider = null) {
  // Lade Seed-Vokabular
  const vocabulary = await loadSeedVocabulary();
  
  // Entscheide Modus
  if (mode === 'auto') {
    if (existingSummary && existingSummary.summary) {
      // Hat bereits Summary → Prüfe Version
      if (existingSummary.version === 'v2') {
        return existingSummary;
      } else {
        mode = 'enhance';
      }
    } else {
      mode = 'full';
    }
  }
  
  // Führe entsprechenden Modus aus
  if (mode === 'enhance' && existingSummary) {
    return await enhanceSummaryV2(lecture, existingSummary, vocabulary, preferredProvider);
  } else if (mode === 'full') {
    return await generateFullSummaryV2(lecture, vocabulary, preferredProvider);
  } else if (mode === 'v1') {
    // Fallback auf alte Methode
    return await generateLectureSummaryV1(lecture);
  } else {
    throw new Error(`Unbekannter Modus: ${mode}`);
  }
}

// ============================================================================
// ALTE V1 FUNKTION (als Fallback)
// ============================================================================

async function generateLectureSummaryV1(lecture) {
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  let provider;
  try {
    provider = getProviderForTask('summary');
  } catch (error) {
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
  
  let textToSummarize = fullText;
  let headingsDisabled = false;
  
  if (estimatedTokens > 180000) {
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
   ⚠️ WICHTIG: KEINE META-SPRACHE! Sachliche, direkte Formulierung!
   ❌ NIEMALS: "Rudolf Steiner stellt dar...", "Im Vortrag wird erklärt...", "Steiner beschreibt...", "Der Redner zeigt..."
   ✅ STATTDESSEN: Direkt die Inhalte beschreiben, als wäre es ein Lexikon-Eintrag
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
    
    // Verwende Provider-Abstraction
    let summaryText = await provider.generateCompletion(prompt, {
      maxTokens: 4000,
      temperature: 0.7
    });
    
    
    try {
      summaryText = summaryText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const summaryData = JSON.parse(summaryText);
      
      if (!summaryData.summary || !Array.isArray(summaryData.headings)) {
        throw new Error('Ungültiges JSON-Format von Claude');
      }
      
      
      const h3Count = summaryData.headings?.filter(h => h.level === 'h3').length || 0;
      const h4Count = summaryData.headings?.filter(h => h.level === 'h4').length || 0;
      const otherCount = summaryData.headings?.filter(h => h.level !== 'h3' && h.level !== 'h4').length || 0;
      
      
      return summaryData;
      
    } catch (parseError) {
      console.error('JSON Parse Fehler:', parseError);
      
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
// ZENTRALE UNIFIED GENERATION SYSTEM - 3 BUTTON ARCHITEKTUR
// ============================================================================

/**
 * Formatiert Vortragtext für Prompts (mit Sampling für lange Vorträge)
 */
function formatLectureTextForPrompt(lecture, maxParagraphs = 80) {
  let paragraphs = lecture.paragraphs || [];
  
  // Sampling für sehr lange Vorträge
  const estimatedTokens = JSON.stringify(paragraphs).length / 4;
  if (estimatedTokens > 180000 && paragraphs.length > maxParagraphs) {
    paragraphs = sampleParagraphsForLongLectures(paragraphs, maxParagraphs);
  }
  
  return paragraphs
    .map((p, idx) => {
      const content = p.content || p.text || '';
      const paraIndex = p.index || `para_${idx}`;
      return `[Index: ${paraIndex}]\n${content}`;
    })
    .filter(text => text.trim().length > 0)
    .join('\n\n');
}

/**
 * Formatiert Headings für Prompts
 */
function formatHeadingsForPrompt(headings) {
  if (!headings || headings.length === 0) return 'Keine Überschriften vorhanden';
  
  return headings
    .map((h, idx) => `${idx + 1}. [${h.level.toUpperCase()}] ${h.text} [Index: ${h.index}]`)
    .join('\n');
}

/**
 * ZENTRALE PROMPT-TEMPLATES (an EINER Stelle definiert)
 */
const UNIFIED_PROMPTS = {
  
  // ========== STRUCTURE MODE: Summary + Headings + TOC ==========
  STRUCTURE: (lectureId, lectureText, vocabularyTop50 = []) => `
Erstelle eine vollständige Analyse für diesen Vortrag von Rudolf Steiner.

VORTRAG: ${lectureId}

AUFGABEN:
1. SUMMARY: Prägnante Zusammenfassung in 100-150 Wörtern
2. HEADINGS: Gliedere den Text in inhaltliche Abschnitte (H3) und Unterabschnitte (H4)
3. TABLE OF CONTENTS: Erstelle für jede H3-Überschrift eine prägnante Kurzbeschreibung (10-15 Wörter)

WICHTIGE VOKABULAR-BEGRIFFE (zur Orientierung):
${vocabularyTop50.slice(0, 50).join(', ') || 'keine'}

REGELN FÜR SUMMARY:
- 100-150 Wörter
- Erfasse die Kernthesen des Vortrags
- Sachlich und präzise
⚠️ WICHTIG: KEINE META-SPRACHE!
❌ NIEMALS: "Rudolf Steiner stellt dar...", "Im Vortrag wird erklärt...", "Steiner beschreibt...", "Der Redner zeigt..."
❌ NIEMALS: "In diesem Vortrag...", "Hier wird untersucht...", "Der Text behandelt..."
✅ STATTDESSEN: Direkt die Inhalte beschreiben wie in einem Lexikon-Artikel

REGELN FÜR HEADINGS - 🔴 HIERARCHIE BEACHTEN:

H3 = HAUPTTHEMA (große thematische Abschnitte)
- Markiert einen neuen Hauptgedanken oder großes Themengebiet
- Beispiele: "Die Entwicklung des Bewusstseins", "Die Mysterien der Antike", "Das Verhältnis von Geist und Materie"

H4 = UNTERTHEMA (Aspekte innerhalb eines H3-Hauptthemas)
- Gehört IMMER zu einem H3-Thema und vertieft/untergliedert dieses
- Beispiele unter H3 "Die Entwicklung des Bewusstseins":
  * H4: "Das alte Bewusstsein in Atlantis"
  * H4: "Der Übergang zur nachatlantischen Zeit"
  * H4: "Das moderne Ich-Bewusstsein"

🎯 STRUKTUR-REGEL:
- Erstelle 5-8 H3-Hauptthemen gleichmäßig über den Vortrag verteilt
- JEDES H3 MUSS 2-4 H4-Unterthemen haben
- H4 folgen direkt nach dem zugehörigen H3 (nicht isoliert)
- Verwende die Index-Markierungen [Index: ^abc123] aus dem Text
- Überschriften sollen das kommende Thema ankündigen

🚨 KRITISCH: KEINE ÜBERSCHRIFTEN IN GEDICHTE!
- Ein Gedicht besteht aus mindestens zwei aufeinanderfolgenden Zeilen, die durch Absatzmarken getrennt sind und weniger als 90 Zeichen pro Zeile haben
- In solchen Bereichen DARFST DU ABSOLUT KEINE Überschriften (H3 oder H4) einfügen!
- Prüfe VOR jeder Überschrift, ob der Bereich ein Gedicht ist!

REGELN FÜR TABLE OF CONTENTS:
⚠️ ABSOLUT VERBOTEN - KEINE META-SPRACHE:
❌ NIEMALS: "Rudolf Steiner beschreibt...", "Steiner erklärt...", "Es wird untersucht..."
❌ NIEMALS: "Diskussion über...", "Analyse der...", "Betrachtung von..."
❌ NIEMALS: "Der Vortrag behandelt...", "Hier wird gezeigt..."

✅ STATTDESSEN: Direkte, sachliche Formulierung wie in einem Lexikon
✅ Beginne direkt mit dem Inhalt

BEISPIELE:
❌ FALSCH: "Rudolf Steiner beschreibt die Transformation Roms"
✅ RICHTIG: "Transformation Roms zur Kirchenmacht nach dem Untergang des römischen Reiches"

VORTRAG-TEXT:
${lectureText}

JSON-AUSGABE (NUR JSON, kein zusätzlicher Text):
{
  "summary": "Deine Zusammenfassung in 100-150 Wörtern",
  "headings": [
    {"index": "^abc123", "text": "Die Entwicklung des Bewusstseins", "level": "h3"},
    {"index": "^abc123", "text": "Das alte Bewusstsein in Atlantis", "level": "h4"},
    {"index": "^def456", "text": "Der Übergang zur nachatlantischen Zeit", "level": "h4"},
    {"index": "^ghi789", "text": "Das moderne Ich-Bewusstsein", "level": "h4"},
    {"index": "^jkl012", "text": "Die Mysterien der Antike", "level": "h3"},
    {"index": "^jkl012", "text": "Ägyptische Mysterien", "level": "h4"},
    {"index": "^mno345", "text": "Griechische Mysterien", "level": "h4"}
  ],
  "tableOfContents": [
    {
      "heading": "Die Entwicklung des Bewusstseins",
      "description": "Vom alten traumhaften Bewusstsein zum modernen Ich-Bewusstsein",
      "index": "^abc123"
    },
    {
      "heading": "Die Mysterien der Antike",
      "description": "Einweihungswege in Ägypten und Griechenland",
      "index": "^jkl012"
    }
  ]
}
`,

  // ========== KEYWORDS MODE: TOC + Keywords (mit existierenden S+H) ==========
  KEYWORDS: (lectureId, lectureText, existingSummary, existingHeadings, vocabularyTerms = [], frequencyMap = {}) => {
    const headingsText = formatHeadingsForPrompt(existingHeadings);
    const h3Headings = existingHeadings.filter(h => h.level === 'h3');
    const topVocab = vocabularyTerms.slice(0, 80);
    const topFrequent = Object.entries(frequencyMap)
      .sort((a, b) => b[1] - a[1])
      .map(([term]) => term)
      .slice(0, 100);
    
    return `
TOC + KEYWORD-GENERIERUNG aus vollem Kontext

VORTRAG: ${lectureId}

BEREITS VORHANDEN (nutze diese Information):

SUMMARY:
${existingSummary}

GLIEDERUNG:
${headingsText}

VERFÜGBARES VOKABULAR (bevorzuge diese Begriffe!):
Thematisch passend: ${topVocab.join(', ') || 'keine'}
Häufigste global: ${topFrequent.slice(0, 80).join(', ') || 'keine'}

AUFGABEN:
1. TABLE OF CONTENTS: Erstelle für jede H3-Überschrift eine prägnante Kurzbeschreibung (10-15 Wörter, KEINE Meta-Sprache)
2. KEYWORDS: Generiere 8-15 Keywords aus dem VOLLEN KONTEXT (Titel + Summary + Headings + Originaltext)

🔴 KRITISCHE KEYWORD-REGELN:

🚨 SCHRITT 1: TITEL ANALYSIEREN (ABSOLUTE PRIORITÄT - PFLICHT-KEYWORDS!)

EXTRAHIERE die HAUPTBEGRIFFE (Substantive) aus dem Titel: ${lectureId}

✅ BEISPIELE FÜR PFLICHT-KEYWORDS AUS TITELN:
→ "DIE SEELE DER TIERE..." → Keyword: "Tiere" (MUSS erscheinen!)
→ "DIE SOGENANNTEN GEFAHREN..." → Keyword: "Gefahren" (MUSS erscheinen!)
→ "BIBEL UND WEISHEIT" → Keyword: "Bibel" (MUSS erscheinen!)
→ "DER LEBENSLAUF DES MENSCHEN" → Keyword: "Lebenslauf" (MUSS erscheinen!)
→ "WEISHEIT UND GESUNDHEIT" → Keyword: "Gesundheit" (MUSS erscheinen!)
→ "BLUT IST EIN GANZ BESONDERER SAFT" → Keyword: "Blut" (MUSS erscheinen!)

❌ NUR IGNORIEREN wenn Titel NICHT inhaltlich:
→ "Erster Vortrag", "Zweiter Vortrag", "Öffentlicher Vortrag" → KEINE Keywords

⚠️ KRITISCH: Diese Titel-Keywords erscheinen oft AUCH in Summary und H3!
   → Das ist KEIN Problem! Verwende sie trotzdem als Keyword!
   → Markiere mit "source": "title-summary"

SCHRITT 2: SUMMARY ERGÄNZEN (falls noch kein Hauptthema/Person aus Titel)
- Falls Titel keine klare Person/Hauptthema hatte:
  * Extrahiere aus der vorhandenen SUMMARY die wichtigste Person ODER das Hauptthema
  * ⚠️ NIEMALS: "Rudolf Steiner" (er ist der Vortragende, kein Inhalt!)
  * ✅ Personen: "Platon", "Kant", "Buddha", "Christus", "Paracelsus" etc.
- Markiere diese mit "source": "title-summary"

SCHRITT 3: H3-ABSCHNITTE (${h3Headings.length} H3-Abschnitte vorhanden)
- Für jeden H3-Abschnitt: 1-2 zentrale Begriffe
- Bevorzuge STARK Vokabular-Begriffe (iteratives Wachstum!)
- Markiere diese mit "source": "h3"

BUDGET-REGEL:
- Maximal 4 NEUE Keywords (matchType: "new")
- Alle anderen MÜSSEN aus dem Vokabular stammen ("existing-exact" oder "existing-similar")
- Gesamt: 8-15 Keywords total
- ⚠️ KRITISCH: KEINE doppelten Keywords! Jeder Begriff nur EINMAL pro Vortrag
  (Wenn ein Begriff in mehreren H3-Abschnitten relevant ist, nutze ihn nur für den wichtigsten Abschnitt)

MATCHING-HIERARCHIE:
1. Exakt im Vokabular → "matchType": "existing-exact", "confidence": 0.9-1.0
2. Ähnlich im Vokabular → "matchType": "existing-similar", "confidence": 0.75-0.85
3. Wenn Budget erlaubt UND nichts passt → "matchType": "new", "confidence": 0.6-0.7

REGELN FÜR TABLE OF CONTENTS:
⚠️ ABSOLUT VERBOTEN - KEINE META-SPRACHE:
❌ NIEMALS: "Rudolf Steiner beschreibt...", "Steiner erklärt...", "Es wird untersucht..."
❌ NIEMALS: "Diskussion über...", "Analyse der...", "Betrachtung von..."

✅ STATTDESSEN: Direkte, sachliche Formulierung wie in einem Lexikon

WICHTIG FÜR KEYWORDS:
- Verwende die Index-Positionen aus den Headings
- Für Summary-Keywords verwende den ersten Absatz-Index (z.B. der erste ^index im Text)

ORIGINALTEXT (zur Orientierung, nutze die Indizes):
${lectureText}

JSON-AUSGABE (NUR JSON-Objekt, kein zusätzlicher Text):
{
  "tableOfContents": [
    {
      "heading": "H3-Überschrift (exakter Text)",
      "description": "Prägnante Beschreibung in 10-15 Wörtern OHNE Meta-Sprache",
      "index": "^abc123"
    }
  ],
  "keywords": [
    {
      "term": "Goethe",
      "index": "^abc123",
      "heading": "Summary",
      "source": "title-summary",
      "matchType": "existing-exact",
      "matchedExisting": "Goethe",
      "summaryMentioned": true,
      "confidence": 1.0,
      "level": "h3"
    },
    {
      "term": "Erkenntnis",
      "index": "^def456",
      "heading": "Die Erkenntnislehre",
      "source": "h3",
      "matchType": "existing-similar",
      "matchedExisting": "Erkenntnistheorie",
      "summaryMentioned": false,
      "confidence": 0.85,
      "level": "h3"
    }
  ]
}
`;
  },

  // ========== FULL MODE: Alles in einem Call (S+H+TOC+KW) ==========
  FULL: (lectureId, lectureText, vocabularyTerms = [], frequencyMap = {}) => {
    const topVocab = vocabularyTerms.slice(0, 50);
    const topFrequent = Object.entries(frequencyMap)
      .sort((a, b) => b[1] - a[1])
      .map(([term]) => term)
      .slice(0, 100);
    
    return `
VOLLSTÄNDIGE VORTRAG-ANALYSE in einem Durchgang

VORTRAG: ${lectureId}

VERFÜGBARES VOKABULAR (nutze für Keywords):
Wichtigste: ${topVocab.join(', ') || 'keine'}
Häufigste: ${topFrequent.slice(0, 80).join(', ') || 'keine'}

AUFGABEN:
1. SUMMARY: 100-150 Wörter Zusammenfassung
   ⚠️ WICHTIG: KEINE META-SPRACHE! Sachlich wie ein Lexikon-Artikel!
   ❌ NIEMALS: "Rudolf Steiner stellt dar...", "Im Vortrag wird erklärt...", "Steiner beschreibt..."
   ✅ STATTDESSEN: Direkt die Inhalte beschreiben

2. HEADINGS: Hierarchische Gliederung mit H3 (Hauptthemen) und H4 (Unterthemen)
   
   🔴 KRITISCH WICHTIG - HIERARCHIE BEACHTEN:
   
   H3 = HAUPTTHEMA (große thematische Abschnitte)
   - Markiert einen neuen Hauptgedanken oder großes Themengebiet
   - Beispiele: "Die Entwicklung des Bewusstseins", "Die Mysterien der Antike", "Das Verhältnis von Geist und Materie"
   
   H4 = UNTERTHEMA (Aspekte innerhalb eines H3-Hauptthemas)
   - Gehört IMMER zu einem H3-Thema und vertieft/untergliedert dieses
   - Beispiele unter H3 "Die Entwicklung des Bewusstseins":
     * H4: "Das alte Bewusstsein in Atlantis"
     * H4: "Der Übergang zur nachatlantischen Zeit"
     * H4: "Das moderne Ich-Bewusstsein"
   
   🎯 STRUKTUR-REGEL:
   - Erstelle 5-8 H3-Hauptthemen gleichmäßig über den Vortrag verteilt
   - JEDES H3 MUSS 2-4 H4-Unterthemen haben
   - H4 folgen direkt nach dem zugehörigen H3 (nicht isoliert)
   - Nutze die Index-Markierungen [Index: ^abc123] aus dem Text

3. TABLE OF CONTENTS: Für jede H3 eine Kurzbeschreibung (10-15 Wörter, KEINE Meta-Sprache)
4. KEYWORDS: 8-15 Keywords

🔴 KRITISCHE KEYWORD-REGELN:

🚨 SCHRITT 1: TITEL ANALYSIEREN (ABSOLUTE PRIORITÄT - PFLICHT-KEYWORDS!)

EXTRAHIERE die HAUPTBEGRIFFE (Substantive) aus dem Titel: ${lectureId}

✅ BEISPIELE FÜR PFLICHT-KEYWORDS AUS TITELN:
→ "DIE SEELE DER TIERE..." → Keyword: "Tiere" (MUSS erscheinen!)
→ "DIE SOGENANNTEN GEFAHREN..." → Keyword: "Gefahren" (MUSS erscheinen!)
→ "BIBEL UND WEISHEIT" → Keyword: "Bibel" (MUSS erscheinen!)
→ "DER LEBENSLAUF DES MENSCHEN" → Keyword: "Lebenslauf" (MUSS erscheinen!)
→ "WEISHEIT UND GESUNDHEIT" → Keyword: "Gesundheit" (MUSS erscheinen!)
→ "BLUT IST EIN GANZ BESONDERER SAFT" → Keyword: "Blut" (MUSS erscheinen!)
→ "Goethe und die Naturwissenschaft" → Keyword: "Goethe" (MUSS erscheinen!)

❌ NUR IGNORIEREN wenn Titel NICHT inhaltlich:
→ "Erster Vortrag", "Zweiter Vortrag", "Öffentlicher Vortrag" → KEINE Keywords

⚠️ KRITISCH: Diese Titel-Keywords erscheinen oft AUCH in Summary und H3!
   → Das ist KEIN Problem! Verwende sie trotzdem als Keyword!
   → Markiere mit "source": "title-summary"

SCHRITT 2: SUMMARY ERGÄNZEN (falls noch kein Hauptthema/Person aus Titel)
- Falls Titel keine klare Person/Hauptthema hatte:
  * Extrahiere aus der SUMMARY die wichtigste Person ODER das Hauptthema
  * ⚠️ NIEMALS: "Rudolf Steiner" (er ist der Vortragende, kein Inhalt!)
  * ✅ Personen: "Platon", "Kant", "Buddha", "Christus", "Paracelsus" etc.
- Markiere diese mit "source": "title-summary"

SCHRITT 3: H3-ABSCHNITTE (1-2 Keywords pro H3)
- Für jeden H3-Abschnitt: 1-2 zentrale Begriffe
- Bevorzuge STARK Vokabular-Begriffe (iteratives Wachstum!)
- Markiere diese mit "source": "h3"

BUDGET-REGEL:
- Maximal 4 NEUE Keywords (matchType: "new")
- Alle anderen MÜSSEN aus dem Vokabular stammen ("existing-exact" oder "existing-similar")
- Gesamt: 8-15 Keywords total
- ⚠️ KRITISCH: KEINE doppelten Keywords! Jeder Begriff nur EINMAL pro Vortrag
  (Wenn ein Begriff in mehreren H3-Abschnitten relevant ist, nutze ihn nur für den wichtigsten Abschnitt)

MATCHING:
- "existing-exact": Exakt im Vokabular (confidence: 0.9-1.0)
- "existing-similar": Ähnlich im Vokabular (confidence: 0.75-0.85)
- "new": Neu, nur wenn Budget erlaubt (confidence: 0.6-0.7)

⚠️ TABLE OF CONTENTS: KEINE Meta-Sprache wie "Steiner beschreibt..."
✅ Direkte sachliche Formulierungen wie in einem Lexikon

VORTRAG-TEXT:
${lectureText}

JSON-AUSGABE (NUR JSON, kein zusätzlicher Text):
{
  "summary": "Zusammenfassung in 100-150 Wörtern",
  "headings": [
    {"index": "^abc123", "text": "Die Entwicklung des Bewusstseins", "level": "h3"},
    {"index": "^abc123", "text": "Das alte Bewusstsein in Atlantis", "level": "h4"},
    {"index": "^def456", "text": "Der Übergang zur nachatlantischen Zeit", "level": "h4"},
    {"index": "^ghi789", "text": "Das moderne Ich-Bewusstsein", "level": "h4"},
    {"index": "^jkl012", "text": "Die Mysterien der Antike", "level": "h3"},
    {"index": "^jkl012", "text": "Ägyptische Mysterien", "level": "h4"},
    {"index": "^mno345", "text": "Griechische Mysterien", "level": "h4"}
  ],
  "tableOfContents": [
    {
      "heading": "Die Entwicklung des Bewusstseins",
      "description": "Vom alten traumhaften Bewusstsein zum modernen Ich-Bewusstsein",
      "index": "^abc123"
    },
    {
      "heading": "Die Mysterien der Antike",
      "description": "Einweihungswege in Ägypten und Griechenland",
      "index": "^jkl012"
    }
  ],
  "keywords": [
    {
      "term": "Goethe",
      "index": "^abc123",
      "heading": "Summary",
      "source": "title-summary",
      "matchType": "existing-exact",
      "matchedExisting": "Goethe",
      "summaryMentioned": true,
      "confidence": 1.0,
      "level": "h3"
    },
    {
      "term": "Bewusstseinsentwicklung",
      "index": "^abc123",
      "heading": "Die Entwicklung des Bewusstseins",
      "source": "h3",
      "matchType": "existing-similar",
      "matchedExisting": "Bewusstsein",
      "summaryMentioned": false,
      "confidence": 0.85,
      "level": "h3"
    },
    {
      "term": "Mysterien",
      "index": "^jkl012",
      "heading": "Die Mysterien der Antike",
      "source": "h3",
      "matchType": "existing-exact",
      "matchedExisting": "Mysterien",
      "summaryMentioned": false,
      "confidence": 0.95,
      "level": "h3"
    }
  ]
}
`;
  }
};

/**
 * ZENTRALE UNIFIED GENERATION FUNKTION
 * Führt die Generierung basierend auf dem Modus aus
 * 
 * @param {string} lectureId - ID des Vortrags
 * @param {string} mode - 'structure' | 'keywords' | 'full'
 * @param {Object} options - Zusätzliche Optionen
 * @returns {Object} Generierte Daten
 */
async function generateUnifiedLectureData(lectureId, mode, options = {}) {
  const {
    provider = null,
    forceRegenerate = false,
    vocabularyTerms = [],
    frequencyMap = {}
  } = options;
  
  
  // 1. Lade Vortrag
  const lecture = fullLectures[lectureId];
  if (!lecture) {
    throw new Error(`Vortrag nicht gefunden: ${lectureId}`);
  }
  
  // 2. Hole LLM-Provider
  let llmProvider;
  try {
    if (provider) {
      const { createProvider } = require('./llm-providers');
      llmProvider = createProvider(provider);
      if (!llmProvider.isAvailable()) {
        throw new Error(`${provider} nicht verfügbar`);
      }
    } else {
      llmProvider = getProviderForTask('summary');
    }
  } catch (providerError) {
    console.error(`[UNIFIED] Provider-Fehler: ${providerError.message}`);
    throw new Error(`Kein LLM-Provider verfügbar: ${providerError.message}`);
  }
  
  // 3. Formatiere Vortragtext
  const lectureText = formatLectureTextForPrompt(lecture);
  
  // 4. Generiere basierend auf Modus
  let prompt, result;
  
  if (mode === 'structure') {
    // ========== MODE: Nur S+H+TOC ==========
    prompt = UNIFIED_PROMPTS.STRUCTURE(lectureId, lectureText, vocabularyTerms);
    
    const responseText = await llmProvider.generateCompletion(prompt, {
      maxTokens: 4000,
      temperature: 0.7
    });
    
    const cleaned = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    result = JSON.parse(cleaned);
    
    // Validierung
    if (!result.summary || !Array.isArray(result.headings) || !Array.isArray(result.tableOfContents)) {
      throw new Error('Ungültiges JSON-Format von LLM (Structure Mode)');
    }
    
    
    return {
      summary: result.summary,
      headings: result.headings,
      tableOfContents: result.tableOfContents,
      version: 'v2-unified',
      generated: new Date().toISOString()
    };
    
  } else if (mode === 'keywords') {
    // ========== MODE: TOC + Keywords (benötigt existierende S+H) ==========
    
    // Lade existierende Daten
    const summaryDB = await loadSummaryDatabase();
    const existingData = summaryDB[lectureId];
    
    if (!existingData || !existingData.summary || !existingData.headings) {
      throw new Error('Keine existierenden Summary/Headings gefunden für Keywords-Only Modus');
    }
    
    prompt = UNIFIED_PROMPTS.KEYWORDS(
      lectureId, 
      lectureText,
      existingData.summary,
      existingData.headings,
      vocabularyTerms,
      frequencyMap
    );
    
    const responseText = await llmProvider.generateCompletion(prompt, {
      maxTokens: 4000,
      temperature: 0.4
    });
    
    const cleaned = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    result = JSON.parse(cleaned);
    
    if (!result.tableOfContents || !Array.isArray(result.tableOfContents) || 
        !result.keywords || !Array.isArray(result.keywords)) {
      throw new Error('Ungültiges JSON-Format von LLM (Keywords Mode - erwartet tableOfContents + keywords)');
    }
    
    
    return {
      tableOfContents: result.tableOfContents,
      keywords: result.keywords,
      generated: new Date().toISOString()
    };
    
  } else if (mode === 'full') {
    // ========== MODE: Alles (S+H+TOC+KW in einem Call) ==========
    
    prompt = UNIFIED_PROMPTS.FULL(lectureId, lectureText, vocabularyTerms, frequencyMap);
    
    const responseText = await llmProvider.generateCompletion(prompt, {
      maxTokens: 6000,
      temperature: 0.7
    });
    
    const cleaned = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    result = JSON.parse(cleaned);
    
    // Validierung
    if (!result.summary || !Array.isArray(result.headings) || 
        !Array.isArray(result.tableOfContents) || !Array.isArray(result.keywords)) {
      throw new Error('Ungültiges JSON-Format von LLM (Full Mode)');
    }
    
    
    return {
      summary: result.summary,
      headings: result.headings,
      tableOfContents: result.tableOfContents,
      keywords: result.keywords,
      version: 'v2-unified',
      generated: new Date().toISOString()
    };
    
  } else {
    throw new Error(`Unbekannter Modus: ${mode}`);
  }
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

app.get('/debug/status', async (req, res) => {
  // Debug: Zeige auch Books-Status
  const { bookFiles } = await findDataFiles();
  
  const summaryDB = await loadSummaryDatabase();
  
  res.json({
    server: 'hybrid-search-unified',
    status: 'running',
    chunksLoaded: chunks.length,
    lecturesLoaded: Object.keys(fullLectures).length,
    booksLoaded: Object.keys(fullBooks).length,
    bookFilesFound: bookFiles.length,
    bookFiles: bookFiles,
    books: Object.keys(fullBooks),
    synonymGroups: Object.keys(synonyms).length,
    summariesInDB: Object.keys(summaryDB).length,
    queryLogSize: Object.keys(queryLog).length,
    llmProviders: {
      claude: !!process.env.CLAUDE_API_KEY,
      openai: !!process.env.OPENAI_API_KEY,
      gemini: !!process.env.GEMINI_API_KEY,
      default: process.env.LLM_PROVIDER_DEFAULT || 'claude'
    }
  });
});

// API-Endpunkt: GA-Liste für Dropdowns
app.get('/api/ga-list', async (req, res) => {
  try {
    
    const gaMap = {};
    
    // Sammle GA-Nummern und Titel aus Vorträgen
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
    
    // Sammle GA-Nummern und Titel aus Schriften (Books)
    Object.values(fullBooks).forEach(book => {
      const gaNumber = book.ID || book.gaNumber;
      if (gaNumber && !gaMap[gaNumber]) {
        gaMap[gaNumber] = {
          number: gaNumber,
          title: book.title || gaNumber
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
    console.error('[API/GA-LIST] Fehler beim Laden der GA-Liste:', error);
    console.error('[API/GA-LIST] Stack:', error.stack);
    res.status(500).json({ error: 'Fehler beim Laden der GA-Liste', details: error.message });
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
    const { query, limit = 100, gaFilter = '', skipCache = false } = req.body;
    const effectiveDepth = 'ausführlich';
    
    // Prüfe ob Request von localhost kommt
    const isLocalRequest = req.hostname === 'localhost' || 
                           req.hostname === '127.0.0.1' || 
                           req.ip === '::1' ||
                           req.ip === '127.0.0.1';
    
    // Themensuchen werden nur bei lokalem Server gespeichert
    const shouldCache = isLocalRequest && !skipCache;
    
    
    // Konsolidierte Hybrid-Cache-Logik
    const cacheKey = generateThematicCacheKey(query, effectiveDepth, limit, gaFilter);
    const thematicDB = await loadThematicSearchDatabase();
    // Hybrid-Cache-Logik zuerst prüfen
    const hybridHit = findHybridCacheHit(query, effectiveDepth, limit, gaFilter, thematicDB);
    if (hybridHit && hybridHit.key && thematicDB[hybridHit.key]) {
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
      // Leere Ergebnisse nur bei localhost cachen
      if (shouldCache) {
        thematicDB[cacheKey] = {
          ...emptyResult,
          timestamp: new Date().toISOString()
        };
        await saveThematicSearchDatabase(thematicDB);
      } else {
      }
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

    // Speichere Ergebnis nur bei localhost
    if (shouldCache) {
      thematicDB[cacheKey] = {
        ...searchResult,
        timestamp: new Date().toISOString()
      };

      // Speichere Cache-DB (non-blocking)
      saveThematicSearchDatabase(thematicDB).then(() => {
      }).catch(err => {
        console.warn('[THEMATIC-CACHE] Fehler beim Cachen:', err.message);
      });
    } else {
    }

    return res.json(searchResult);
  } catch (error) {
    console.error('Hybrid-thematic-Search Fehler:', error);
    // Spezielle Fehlermeldung für KI-Suche
    res.status(500).json({ 
      error: 'Suche fehlgeschlagen - bitte Anfrage anders formulieren, relevante Suchworte in Anführungszeichen setzen und in Kürze noch einmal versuchen',
      originalError: error.message 
    });
  }
});

// ============================================================================
// KONZEPT-ÜBERSICHT API (KI-BASIERT)
// ============================================================================

/**
 * Wiederverwendbare Funktion: Generiert Themen_Übersicht für ein Konzept
 * @param {string} concept - Das Konzept/Schlagwort
 * @param {string} gaFilter - Optionaler GA-Filter
 * @returns {Promise<Object>} Übersicht mit definitionText, functionText, interactionText, specialText, alternativeTerms
 */
async function generateConceptOverviewData(concept, gaFilter = '') {
  
  // Prüfe ob paragraphsFromLectures verfügbar ist
  if (!paragraphsFromLectures || paragraphsFromLectures.length === 0) {
    console.error('[CONCEPT-OVERVIEW] Keine Paragraphen geladen');
    throw new Error('Vortrags-Daten noch nicht geladen. Bitte warten Sie einen Moment.');
  }
  
  // 1. Verwende die gleiche Suchmethode wie bei thematischer Suche
  let keywordResults = performThematicKeywordSearch(concept, paragraphsFromLectures, gaFilter);
  
  if (keywordResults.length === 0) {
    return {
      overview: {
        alternativeTerms: [],
        definitionText: 'Keine Informationen gefunden.',
        functionText: 'Keine Informationen gefunden.',
        interactionText: 'Keine Informationen gefunden.',
        specialText: 'Keine Informationen gefunden.'
      }
    };
  }
  
  // 2. Ranking und Begrenzung
  let rankedResults = applySemanticRanking(keywordResults, concept);
  
  // Verwende mehr Ergebnisse für umfassendere Analyse (bis zu 200 für alternative Begriffe)
  let topResults = rankedResults.slice(0, 200); // Top 200 für alternative Begriffe
  
  
  // 3. Finde alternative Begriffe (ohne ähnliche Wortstämme)
  const alternativeTerms = [];
  const conceptLower = concept.toLowerCase();
  
  // Funktion zum Normalisieren eines Wortes (entfernt Pluralformen)
  const normalizeWord = (word) => {
    const lower = word.toLowerCase();
    // Entferne häufige Pluralendungen: -e, -er, -en, -n, -s
    return lower.replace(/(e|er|en|n|s)$/, '');
  };
  
  // Funktion zum Prüfen, ob zwei Wörter ähnliche Wortstämme haben
  const hasSimilarStem = (word1, word2) => {
    const norm1 = normalizeWord(word1);
    const norm2 = normalizeWord(word2);
    
    // Wenn normalisierte Formen gleich sind, haben sie den gleichen Stamm
    if (norm1 === norm2) return true;
    
    // Prüfe, ob ein Wort eine Variante des anderen ist
    const shorter = norm1.length < norm2.length ? norm1 : norm2;
    const longer = norm1.length >= norm2.length ? norm1 : norm2;
    
    // Wenn das längere Wort mit dem kürzeren beginnt und nur 1-2 Zeichen Unterschied hat
    if (longer.startsWith(shorter) && longer.length - shorter.length <= 2) {
      return true;
    }
    
    return false;
  };
  
  // Sammle alle potentiellen alternativen Begriffe
  const allWords = new Set();
  const conceptPattern = new RegExp(`\\b([A-ZÄÖÜ][a-zäöüß]+(?:leib|körper|wesen|prinzip|kraft|glied))\\b`, 'gi');
  
  // Verwende mehr Ergebnisse für Suche nach alternativen Begriffen
  for (const result of topResults.slice(0, 100)) {
    const matches = result.content.match(conceptPattern);
    if (matches) {
      matches.forEach(match => {
        const word = match.trim();
        const wordLower = word.toLowerCase();
        
        // Überspringe das ursprüngliche Konzept selbst
        if (wordLower === conceptLower) return;
        
        // Überspringe zu kurze oder zu lange Wörter
        if (word.length <= 3 || word.length > 25) return;
        
        allWords.add(word);
      });
    }
  }
  
  // Filtere ähnliche Wortstämme heraus
  const uniqueTerms = [];
  for (const word of allWords) {
    let isDuplicate = false;
    
    // Prüfe gegen alle bereits hinzugefügten Begriffe
    for (const existing of uniqueTerms) {
      if (hasSimilarStem(word, existing)) {
        // Behalte den kürzeren Begriff (wahrscheinlich die Grundform)
        if (word.length < existing.length) {
          const index = uniqueTerms.indexOf(existing);
          uniqueTerms[index] = word;
        }
        isDuplicate = true;
        break;
      }
    }
    
    // Prüfe auch gegen das ursprüngliche Konzept
    if (!isDuplicate && hasSimilarStem(word, concept)) {
      isDuplicate = true;
    }
    
    // Füge hinzu, wenn nicht dupliziert
    if (!isDuplicate && uniqueTerms.length < 10) {
      uniqueTerms.push(word);
    }
  }
  
  // Sortiere und begrenze auf 5 beste Ergebnisse
  const sortedAlternatives = uniqueTerms
    .sort((a, b) => a.length - b.length) // Kürzere zuerst (wahrscheinlich Grundformen)
    .slice(0, 5);
  
  alternativeTerms.push(...sortedAlternatives);
  
  // 4. Bereite Kontext für KI vor (mit Ranking-Scores)
  // Verwende mehr Ergebnisse für umfassendere KI-Analyse (bis zu 100)
  // Mit optimierter Kürzung sollte das Token-Limit eingehalten werden
  const MAX_RESULTS_FOR_AI = 100; // Wiederhergestellt auf 100
  const resultsForAI = topResults.slice(0, MAX_RESULTS_FOR_AI);
  
  // Hilfsfunktion: Kürze Textpassage auf maximal 400 Zeichen (optimiert für mehr Passagen)
  const truncateContent = (content, maxLength = 400) => {
    if (!content || content.length <= maxLength) {
      return content;
    }
    // Versuche bei Satzende zu kürzen
    const truncated = content.substring(0, maxLength);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastExclamation = truncated.lastIndexOf('!');
    const lastQuestion = truncated.lastIndexOf('?');
    const lastSentenceEnd = Math.max(lastPeriod, lastExclamation, lastQuestion);
    
    if (lastSentenceEnd > maxLength * 0.7) {
      // Wenn Satzende gefunden wurde (nicht zu weit am Anfang), kürze dort
      return truncated.substring(0, lastSentenceEnd + 1) + '...';
    }
    // Sonst kürze einfach und füge ... hinzu
    return truncated + '...';
  };
  
  const contextText = resultsForAI
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      // Kürze jede Textpassage auf maximal 500 Zeichen
      const truncatedContent = truncateContent(result.content, 500);
      return `[${refId}] ${result.fileName || result.title}\n${truncatedContent}`;
    })
    .join('\n\n---\n\n');
  
  // 5. KI-Prompt für strukturierte Analyse (mit Stichworten statt Zitaten)
  const prompt = `Analysiere die folgenden Textstellen aus Rudolf Steiners Werk zum Konzept: "${concept}"

AUFGABE:
Erstelle eine strukturierte Übersicht zum Konzept "${concept}" basierend auf den vorliegenden Textauszügen.
Gliedere deine Analyse in GENAU diese 4 Kategorien:

1. DEFINITION
Was ist "${concept}"? Wie wird es definiert und beschrieben?
- Verwende KURZE, PRÄGNANTE STICHWORTE und Begriffe
- Gib IMMER Quellenangaben im korrekten Format an:
  * Für VORTRÄGE: (GA###/##:index) - z.B. (GA013/01:42), (GA009/03:23), (GA027/05:67)
  * Für BÜCHER: (GA###:^index) - z.B. (GA013:^xba9rk), (GA007:^iyj24c), (GA035:^l7py6i)
  * WICHTIG: Bücher haben KEINEN Slash nach der GA-Nummer, nur einen Doppelpunkt!
- Beispiel: "zweites Wesensglied (GA013/01:42), Lebenskräfte (GA009/03:23), Erlebnis der Seele (GA013:^xba9rk)"
- KEINE vollständigen Zitate, nur relevante Schlüsselbegriffe

2. FUNKTION
Welche Funktion oder Aufgabe hat "${concept}"?
- STICHWORTE zu Wirkungen und Aufgaben
- Quellenangaben im korrekten Format:
  * Vorträge: (GA###/##:index) - z.B. (GA027/05:88), (GA053/10:45)
  * Bücher: (GA###:^index) - z.B. (GA013:^xba9rk), (GA007:^iyj24c)
- Beispiel für Singular (z.B. "Ätherleib"): "durchdringt physischen Leib (GA027/05:88), trägt Lebenskräfte (GA053/10:45), schafft Ätherleib (GA184/3)"
- Beispiel für Plural (z.B. "Wesensglieder"): "durchdringen physischen Leib (GA027/05:88), tragen Lebenskräfte (GA053/10:45), schaffen Ätherleib (GA184/3)"
- WICHTIG: Verb vor Objekt UND grammatikalische Kongruenz mit "${concept}"

3. INTERAKTIONEN
Wie steht "${concept}" in Beziehung zu anderen Konzepten?
- STICHWORTE zu Wechselwirkungen
- Quellenangaben im korrekten Format:
  * Vorträge: (GA###/##:index) - z.B. (GA088/12:34), (GA013/01:56)
  * Bücher: (GA###:^index) - z.B. (GA013:^xba9rk), (GA035:^l7py6i)
- Beispiel für Singular (z.B. "Ätherleib"): "wechselwirkt mit Astralleib (GA088/12:34), verbindet mit Ich (GA013/01:56)"
- Beispiel für Plural (z.B. "Wesensglieder"): "wechselwirken mit Astralleib (GA088/12:34), verbinden mit Ich (GA013/01:56)"
- WICHTIG: Verb vor Objekt UND grammatikalische Kongruenz mit "${concept}"

4. BESONDERHEITEN
Welche besonderen Eigenschaften oder Merkmale hat "${concept}"?
- STICHWORTE zu besonderen Merkmalen
- Quellenangaben im korrekten Format:
  * Vorträge: (GA###/##:index) - z.B. (GA053/10:78), (GA013/01:90)
  * Bücher: (GA###:^index) - z.B. (GA013:^xba9rk), (GA007:^iyj24c)
- Beispiel: "Gedächtnisträger (GA053/10:78), Erinnerungskräfte (GA013/01:90), Loslösung von physischer Bindung (GA013:^xba9rk)"

STILISTISCHE ANFORDERUNGEN:
- NUR relevante STICHWORTE und Begriffe (KEINE vollständigen Sätze oder Zitate)
- Jedes Stichwort mit Quellenangabe im korrekten Format:
  * Vorträge: (GA###/##:index)
  * Bücher: (GA###:^index)
- Kompakt und übersichtlich
- Durch Kommas getrennt
- KEINE einleitenden Sätze
- KEINE Formulierungen wie "Steiner beschreibt..."

GRAMMATIKALISCHE KORREKTHEIT:
- Stichworte MÜSSEN grammatikalisch korrekt formuliert sein
- Bei Verben: Verb VOR dem Objekt, nicht danach
- RICHTIG: "bauen Nervensystem auf", "durchströmen rhythmische Organisation", "ermöglichen Fühlen"
- FALSCH: "Nervensystem aufbauen", "rhythmische Organisation durchströmen", "Fühlen ermöglichen"
- Bei Substantiven/Nomen: normale Wortstellung beibehalten

GRAMMATIKALISCHE KONGRUENZ MIT DEM SUCHWORT:
- Die Verben MÜSSEN im Numerus und in der Person mit dem Suchwort "${concept}" übereinstimmen
- Wenn das Suchwort im Singular steht (z.B. "Alter Saturn", "Ätherleib", "Astralleib"): Verben in 3. Person Singular
  - RICHTIG: "bildet erste Anlage (GA110/9)", "schafft Wärmekörper (GA110/3)", "durchdringt physischen Leib (GA027/05)"
  - FALSCH: "bilden erste Anlage", "schaffen Wärmekörper", "durchdringen physischen Leib"
- Wenn das Suchwort im Plural steht (z.B. "Wesensglieder", "Lebenskräfte"): Verben in 3. Person Plural
  - RICHTIG: "bilden erste Anlage", "schaffen Wärmekörper", "durchdringen physischen Leib"
  - FALSCH: "bildet erste Anlage", "schafft Wärmekörper", "durchdringt physischen Leib"
- Analysiere das Suchwort "${concept}" und passe die Verbformen entsprechend an
- Beispiel für Singular: "Alter Saturn" → "bildet (GA110/9), schafft (GA110/3), ermöglicht (GA353/16)"
- Beispiel für Plural: "Wesensglieder" → "bilden (GA110/9), schaffen (GA110/3), ermöglichen (GA353/16)"

FORMATIERUNG:
Verwende folgendes Format:

## DEFINITION
Stichwort1 (GA###/##:index oder GA###:^index), Stichwort2 (GA###/##:index oder GA###:^index), Stichwort3 (GA###/##:index oder GA###:^index)

## FUNKTION
Stichwort1 (GA###/##:index oder GA###:^index), Stichwort2 (GA###/##:index oder GA###:^index)

## INTERAKTIONEN
Stichwort1 (GA###/##:index oder GA###:^index), Stichwort2 (GA###/##:index oder GA###:^index)

## BESONDERHEITEN
Stichwort1 (GA###/##:index oder GA###:^index), Stichwort2 (GA###/##:index oder GA###:^index)

WICHTIG:
- Nur STICHWORTE, keine vollständigen Zitate
- Quellenangaben MÜSSEN im korrekten Format sein:
  * Vorträge: (GA###/##:index) - z.B. (GA013/01:42)
  * Bücher: (GA###:^index) - z.B. (GA013:^xba9rk)
- Maximum 8-10 Stichworte pro Kategorie
- Nur verschiedene, nicht-redundante Aspekte
- GRAMMATIKALISCHE KORREKTHEIT: Verb vor Objekt bei verbalen Formulierungen
- GRAMMATIKALISCHE KONGRUENZ: Verben müssen im Numerus und in der Person mit "${concept}" übereinstimmen
  - Singular (z.B. "Alter Saturn", "Ätherleib") → 3. Person Singular: "bildet", "schafft", "durchdringt"
  - Plural (z.B. "Wesensglieder", "Lebenskräfte") → 3. Person Plural: "bilden", "schaffen", "durchdringen"

TEXTSTELLEN:

${contextText}

Erstelle jetzt die strukturierte Übersicht mit Stichworten:`;

  
  let fullText;
  try {
    const response = await generateCompletionWithFallback(prompt, {
      temperature: 0.3,
      maxTokens: 16000  // Erhöht von 4000 auf 16000 für längere Antworten
    }, 'analysis');
    
    fullText = response.text || response.content;
  } catch (error) {
    console.error('[CONCEPT-OVERVIEW] KI-Anfrage fehlgeschlagen:', error.message);
    
    // Prüfe welche Provider verfügbar sind
    const { getAllAvailableProviders } = require('./llm-providers');
    const availableProviders = getAllAvailableProviders('analysis');
    const providerStatus = [];
    
    // Prüfe Claude explizit
    const { createProvider } = require('./llm-providers');
    try {
      const claudeProvider = createProvider('claude');
      if (claudeProvider.isAvailable()) {
        providerStatus.push('Claude: ✅ API-Key vorhanden');
      } else {
        providerStatus.push('Claude: ❌ Kein API-Key (CLAUDE_API_KEY fehlt)');
      }
    } catch (e) {
      providerStatus.push(`Claude: ❌ ${e.message}`);
    }
    
    // Prüfe OpenAI
    try {
      const openaiProvider = createProvider('openai');
      if (openaiProvider.isAvailable()) {
        providerStatus.push('OpenAI: ✅ API-Key vorhanden');
      } else {
        providerStatus.push('OpenAI: ❌ Kein API-Key (OPENAI_API_KEY fehlt)');
      }
    } catch (e) {
      providerStatus.push(`OpenAI: ❌ ${e.message}`);
    }
    
    // Prüfe Gemini
    try {
      const geminiProvider = createProvider('gemini');
      if (geminiProvider.isAvailable()) {
        providerStatus.push('Gemini: ✅ API-Key vorhanden');
      } else {
        providerStatus.push('Gemini: ❌ Kein API-Key (GEMINI_API_KEY fehlt)');
      }
    } catch (e) {
      providerStatus.push(`Gemini: ❌ ${e.message}`);
    }
    
    // Prüfe Rate-Limits
    const { isProviderRateLimited } = require('./llm-providers');
    const rateLimitedInfo = [];
    if (isProviderRateLimited('claude')) {
      rateLimitedInfo.push('Claude ist aktuell Rate-Limited');
    }
    if (isProviderRateLimited('openai')) {
      rateLimitedInfo.push('OpenAI ist aktuell Rate-Limited');
    }
    if (isProviderRateLimited('gemini')) {
      rateLimitedInfo.push('Gemini ist aktuell Rate-Limited');
    }
    
    // Erstelle detaillierte Fehlermeldung
    let errorDetails = `Zu "${concept}" wurden ${topResults.length} Textpassagen gefunden.\n\n`;
    errorDetails += `Provider-Status:\n${providerStatus.join('\n')}\n\n`;
    
    if (rateLimitedInfo.length > 0) {
      errorDetails += `Rate-Limits:\n${rateLimitedInfo.join('\n')}\n\n`;
    }
    
    errorDetails += `Fehler beim letzten Versuch:\n${error.message}`;
    
    // Fallback: Einfache Textextraktion
    return {
      overview: {
        alternativeTerms: alternativeTerms,
        definitionText: errorDetails,
        functionText: 'LLM-Provider erforderlich.',
        interactionText: 'LLM-Provider erforderlich.',
        specialText: 'LLM-Provider erforderlich.'
      }
    };
  }
  
  // 6. Parse die KI-Antwort in Kategorien
  const categories = {
    definitionText: '',
    functionText: '',
    interactionText: '',
    specialText: ''
  };
  
  // Extrahiere Kategorien
  const definitionMatch = fullText.match(/##\s*DEFINITION\s*([\s\S]*?)(?=##\s*FUNKTION|$)/i);
  const functionMatch = fullText.match(/##\s*FUNKTION\s*([\s\S]*?)(?=##\s*INTERAKTIONEN|$)/i);
  const interactionMatch = fullText.match(/##\s*INTERAKTIONEN\s*([\s\S]*?)(?=##\s*BESONDERHEITEN|$)/i);
  const specialMatch = fullText.match(/##\s*BESONDERHEITEN\s*([\s\S]*?)$/i);
  
  // Hilfsfunktion: Formatiere Text - Großbuchstabe am Anfang, Punkt am Ende
  const formatCategoryText = (text) => {
    if (!text || text.trim() === '') return text;
    
    let formatted = text.trim();
    
    // Erster Buchstabe groß
    if (formatted.length > 0) {
      formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1);
    }
    
    // Punkt am Ende hinzufügen (falls noch keiner vorhanden)
    if (formatted.length > 0 && !formatted.endsWith('.') && !formatted.endsWith('!') && !formatted.endsWith('?')) {
      formatted = formatted + '.';
    }
    
    return formatted;
  };
  
  if (definitionMatch) categories.definitionText = formatCategoryText(definitionMatch[1].trim());
  if (functionMatch) categories.functionText = formatCategoryText(functionMatch[1].trim());
  if (interactionMatch) categories.interactionText = formatCategoryText(interactionMatch[1].trim());
  if (specialMatch) categories.specialText = formatCategoryText(specialMatch[1].trim());
  
  const result = {
    overview: {
      alternativeTerms: alternativeTerms,
      ...categories
    }
  };
  
  
  return result;
}

app.post('/api/concept-overview', async (req, res) => {
  try {
    const { concept, gaFilter = '' } = req.body;
    
    if (!concept || !concept.trim()) {
      return res.status(400).json({ error: 'Konzept ist erforderlich' });
    }
    
    // Verwende die wiederverwendbare Funktion
    const result = await generateConceptOverviewData(concept, gaFilter);
    res.json(result);
    
  } catch (error) {
    console.error('[CONCEPT-OVERVIEW] Fehler:', error);
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

    // Sammle GA-Nummern aus Vorträgen
    Object.values(fullLectures).forEach(lecture => {
      if (lecture.gaNumber && typeof lecture.gaNumber === 'string') {
        gaSet.add(lecture.gaNumber);
      }
    });

    // Sammle GA-Nummern aus Schriften (Books)
    Object.values(fullBooks).forEach(book => {
      const gaNumber = book.ID || book.gaNumber;
      if (gaNumber && typeof gaNumber === 'string') {
        gaSet.add(gaNumber);
      }
    });

    const result = Array.from(gaSet).sort();
    res.json({ availableGA: result });
  } catch (error) {
    console.error("[ERROR] Fehler bei /api/available-ga:", error);
    res.status(500).json({ error: "Interner Serverfehler" });
  }
});

app.get('/api/available-years', async (req, res) => {
  try {
    const yearSet = new Set();

    Object.values(fullLectures).forEach(lecture => {
      if (lecture.date && typeof lecture.date === 'string') {
        const year = lecture.date.substring(0, 4);
        if (year && /^\d{4}$/.test(year)) {
          yearSet.add(year);
        }
      }
    });

    const result = Array.from(yearSet).sort();
    res.json({ years: result });
  } catch (error) {
    console.error("[ERROR] Fehler bei /api/available-years:", error);
    res.status(500).json({ error: "Interner Serverfehler" });
  }
});

// API-Endpunkt: Buch (Schrift) abrufen
// Reload-Endpoint für Books (zum Neuladen ohne Server-Neustart)
app.post('/api/reload-books', async (req, res) => {
  try {
    fullBooks = {}; // Leere den Cache
    const reloaded = await loadBooks();
    res.json({ 
      success: true, 
      booksLoaded: Object.keys(reloaded).length,
      books: Object.keys(reloaded)
    });
  } catch (error) {
    console.error('[RELOAD] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/book/:gaNumber', async (req, res) => {
  try {
    const gaNumberOriginal = req.params.gaNumber;
    
    // VALIDIERUNG ENTFERNT - verursachte Probleme
    const gaNumberNormalized = gaNumberOriginal.toLowerCase();


    // Suche nach Book
    const book = Object.values(fullBooks).find(b => {
      const bookGA = (b.ID || b.gaNumber || '').toLowerCase();
      return bookGA === gaNumberNormalized;
    });

    if (!book) {
      return res.status(404).json({ error: `Keine Schrift gefunden für ${gaNumberOriginal}` });
    }


    // Speichere Überschriften in summary-database.json für TOC-Anzeige
    // WICHTIG: Nur für Books (GA001-GA046), niemals Vortrags-Einträge überschreiben!
    const bookId = book.ID || book.gaNumber;
    
    // Prüfe ob es wirklich ein Book ist (GA001-GA046)
    const gaMatch = bookId.match(/^GA0?([0-4][0-6]|[0-4][0-9])$/);
    if (!gaMatch) {
      const gaNum = parseInt(bookId.replace('GA', ''));
      if (gaNum < 1 || gaNum > 46) {
        console.warn(`[BOOK] ⚠️  ${bookId} ist kein Book (GA001-GA046) - Überschriften werden NICHT gespeichert`);
        // Gebe Book trotzdem zurück, aber ohne Überschriften zu speichern
      }
    }
    
    if (book.headings && book.headings.length > 0) {
      try {
        // Lade bestehende Datenbank - WICHTIG: Bei Fehler NICHT überschreiben!
        let summaryDB = null;
        let dbLoadError = null;
        try {
          const dbContent = await fs.readFile(SUMMARY_DB_FILE, 'utf8');
          summaryDB = JSON.parse(dbContent);
          
          // Prüfe ob Datenbank gültig ist (nicht leer nach Parse)
          if (!summaryDB || typeof summaryDB !== 'object') {
            throw new Error('Datenbank ist kein gültiges Objekt');
          }
          
          // Prüfe ob Vortrags-Einträge vorhanden sind (GA051+)
          const hasLectures = Object.keys(summaryDB).some(id => {
            const match = id.match(/^GA(\d+)/);
            if (match) {
              const num = parseInt(match[1]);
              return num >= 51; // Vorträge beginnen ab GA051
            }
            return false;
          });
          
          if (hasLectures) {
          }
        } catch (e) {
          dbLoadError = e;
          console.error(`[BOOK] ❌ FEHLER beim Laden der summary-database.json: ${e.message}`);
          console.error(`[BOOK] ⚠️  Überschriften werden NICHT gespeichert, um Vortrags-Einträge zu schützen!`);
          // NICHT überschreiben - Book wird trotzdem zurückgegeben
        }

        // Nur speichern wenn Datenbank erfolgreich geladen wurde
        // WICHTIG: Überschreibe NICHT, wenn bereits Überschriften vorhanden sind (wurden vom Export-Skript gesetzt)
        if (summaryDB && !dbLoadError) {
          const existingEntry = summaryDB[bookId];
          const hasExistingHeadings = existingEntry && existingEntry.headings && existingEntry.headings.length > 0;
          
          // Prüfe ob bestehende Überschriften Absatz-Indizes haben (beginnen mit ^)
          const hasParagraphIndices = hasExistingHeadings && 
            existingEntry.headings.some(h => h.index && h.index.startsWith('^'));
          
          if (!hasExistingHeadings || !hasParagraphIndices) {
            // Nur speichern wenn keine Überschriften vorhanden oder keine Absatz-Indizes
            // Konvertiere Book-Headings zu summary-database Format
            const headingsForDB = book.headings.map(h => ({
              index: h.id || `heading-${h.line || 0}`,
              text: h.text,
              level: `h${h.level || 3}`
            }));

            // Erstelle oder aktualisiere NUR den Eintrag für dieses Book
            // WICHTIG: Bestehende Vortrags-Einträge bleiben unverändert!
            if (!summaryDB[bookId]) {
              summaryDB[bookId] = {};
            }
            summaryDB[bookId].headings = headingsForDB;
            summaryDB[bookId].tableOfContents = book.headings.map(h => ({
              heading: h.text,
              description: '', // Books haben keine Beschreibungen
              index: h.id || `heading-${h.line || 0}`
            }));
            summaryDB[bookId].version = 'v2';

            // Speichere zurück - Vortrags-Einträge bleiben erhalten
            await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
          } else {
            console.log(`[BOOK] ${bookId}: Überschreibe NICHT - bereits Absatz-Indizes vorhanden`);
          }
          const totalEntries = Object.keys(summaryDB).length;
          const lectureEntries = Object.keys(summaryDB).filter(id => {
            const match = id.match(/^GA(\d+)/);
            return match && parseInt(match[1]) >= 51;
          }).length;
        } else {
          console.warn(`[BOOK] ⚠️  Überschriften für ${bookId} wurden NICHT gespeichert (Datenbank konnte nicht geladen werden)`);
        }
      } catch (dbError) {
        console.error('[BOOK] ❌ Fehler beim Speichern der Überschriften:', dbError);
        // Nicht kritisch - Book wird trotzdem zurückgegeben
      }
    }

    // Gebe vollständige Book-Daten zurück
    res.json({
      ID: book.ID || book.gaNumber,
      gaNumber: book.gaNumber || book.ID,
      title: book.title,
      fileName: book.fileName,
      yearRange: book.yearRange,
      content: book.content,
      headings: book.headings || [],
      wordCount: book.wordCount,
      charCount: book.charCount
    });

  } catch (error) {
    console.error('[BOOK] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/ga-overview/:gaNumber', async (req, res) => {
  try {
    const gaNumberOriginal = req.params.gaNumber;


    // Generiere Übersicht direkt aus zentraler Datenbank (kein Cache)
    const overview = await generateGAOverview(gaNumberOriginal);

    if (!overview) {
      return res.status(404).json({ error: `Keine Vorträge gefunden für ${gaNumberOriginal}` });
    }

    res.json(overview);

  } catch (error) {
    console.error('[GA-OVERVIEW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Alle Vorträge chronologisch sortiert
app.get('/api/lectures/chronological', async (req, res) => {
  try {
    
    // Sammle alle Vorträge mit Datum
    const lecturesWithDate = [];
    
    Object.values(fullLectures).forEach(lecture => {
      if (lecture.date) {
        lecturesWithDate.push({
          ID: lecture.ID,
          title: lecture.title,
          fileName: lecture.fileName,
          date: lecture.date,
          location: lecture.location,
          gaNumber: lecture.gaNumber
        });
      }
    });
    
    // Sortiere chronologisch aufsteigend
    lecturesWithDate.sort((a, b) => {
      return new Date(a.date) - new Date(b.date);
    });
    
    
    res.json({
      success: true,
      count: lecturesWithDate.length,
      lectures: lecturesWithDate
    });
    
  } catch (error) {
    console.error('[CHRONOLOGICAL] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/ga-overview-map.json', async (req, res) => {
  try {
    const mapPath = path.join(__dirname, 'ga-overview-map.json');
    
    
    try {
      await fs.access(mapPath);
      const data = await fs.readFile(mapPath, 'utf8');
      res.setHeader('Content-Type', 'application/json');
      res.send(data);
    } catch (fileErr) {
      
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
    
    
    const startCount = Object.keys(synonyms).length;
    
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
      enrichedCount = await enrichSynonymsWithClaude(topN);
    } else {
    }
    
    const endCount = Object.keys(synonyms).length;
    
    
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
// SYNONYM-VERWALTUNG (Manuell)
// ============================================================================

// Endpoint: Manuelles Hinzufügen von Synonymen
app.post('/api/synonyms/add', async (req, res) => {
  try {
    const { baseKeyword, synonym } = req.body;
    
    if (!baseKeyword || !synonym) {
      return res.status(400).json({ error: 'baseKeyword und synonym erforderlich' });
    }
    
    const baseNormalized = baseKeyword.toLowerCase().trim();
    const synonymNormalized = synonym.toLowerCase().trim();
    
    
    // Initialisiere Array falls noch nicht vorhanden
    if (!synonyms[baseNormalized]) {
      synonyms[baseNormalized] = [baseNormalized];
    }
    
    // Prüfe ob Synonym bereits existiert
    if (synonyms[baseNormalized].includes(synonymNormalized)) {
      return res.json({
        success: true,
        message: 'Synonym existiert bereits',
        alreadyExists: true
      });
    }
    
    // Füge Synonym hinzu
    synonyms[baseNormalized].push(synonymNormalized);
    
    // Speichere
    await saveSynonyms();
    
    
    res.json({
      success: true,
      baseKeyword: baseNormalized,
      synonym: synonymNormalized,
      totalSynonyms: synonyms[baseNormalized].length,
      allSynonyms: synonyms[baseNormalized]
    });
    
  } catch (error) {
    console.error('[SYNONYM-ADD] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Hole alle Synonyme für ein Keyword
app.get('/api/synonyms/:keyword', (req, res) => {
  try {
    const keyword = req.params.keyword.toLowerCase().trim();
    
    const synonymList = synonyms[keyword] || [];
    
    res.json({
      keyword: keyword,
      synonyms: synonymList,
      count: synonymList.length
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SCHLAGWORT-SYSTEM API
// ============================================================================

// API-Endpunkt: Liste aller verfügbaren Schlagwort-Dateien
app.get('/api/concepts-files', async (req, res) => {
  try {
    
    const keywordsPath = path.join(__dirname, 'keywords');
    
    // Prüfe ob keywords/ Ordner existiert
    try {
      await fs.access(keywordsPath);
    } catch (error) {
      return res.json({ files: [] });
    }
    
    // Lese alle .json Dateien im keywords/ Ordner
    const files = await fs.readdir(keywordsPath);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    
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
app.get('/api/concepts-list', async (req, res) => {
  try {
    
    const keywordsPath = path.join(__dirname, 'keywords');
    let allKeywords = [];
    
    // Versuche zuerst zentrale concepts-database.json im Hauptordner zu laden
    try {
      const filePath = path.join(__dirname, 'concepts-database.json');
      const fileContent = await fs.readFile(filePath, 'utf8');
      const data = JSON.parse(fileContent);
      if (Array.isArray(data)) {
        allKeywords = allKeywords.concat(data);
      }
    } catch (error) {
      console.warn('[KEYWORDS-API] Keine zentrale concepts-database.json gefunden:', error.message);
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

// API-Endpunkt: Einzelnes Konzept laden (für Netzwerk-Modal)
app.get('/api/concepts/:concept', async (req, res) => {
  try {
    const searchConcept = decodeURIComponent(req.params.concept).toLowerCase();
    
    // Lade concepts-database.json
    const filePath = path.join(__dirname, 'concepts-database.json');
    let allConcepts = [];
    
    try {
      const fileContent = await fs.readFile(filePath, 'utf8');
      allConcepts = JSON.parse(fileContent);
    } catch (error) {
      return res.status(404).json({ error: 'Konzept-Datenbank nicht gefunden' });
    }
    
    // Suche nach dem Konzept (case-insensitive)
    const concept = allConcepts.find(c => 
      c.keyword && c.keyword.toLowerCase() === searchConcept
    );
    
    if (!concept) {
      return res.status(404).json({ error: `Konzept "${req.params.concept}" nicht gefunden` });
    }
    
    res.json(concept);
  } catch (error) {
    console.error('[CONCEPTS-API] Fehler beim Laden des Konzepts:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// BEZIEHUNGS-SUCHE (Relationship Search)
// ============================================================================

const RELATIONSHIPS_DB_FILE = path.join(__dirname, 'relationships-database.json');
let relationshipsCache = {};

// Lade Beziehungs-Datenbank beim Start
async function loadRelationshipsDatabase() {
  try {
    const content = await fs.readFile(RELATIONSHIPS_DB_FILE, 'utf8');
    relationshipsCache = JSON.parse(content);
    console.log(`[RELATIONSHIPS] ${Object.keys(relationshipsCache).length} Beziehungen geladen`);
  } catch (error) {
    console.log('[RELATIONSHIPS] Keine bestehende Datenbank gefunden, starte mit leerem Cache');
    relationshipsCache = {};
  }
}

// Speichere Beziehungs-Datenbank
async function saveRelationshipsDatabase() {
  try {
    await fs.writeFile(RELATIONSHIPS_DB_FILE, JSON.stringify(relationshipsCache, null, 2), 'utf8');
  } catch (error) {
    console.error('[RELATIONSHIPS] Fehler beim Speichern:', error);
  }
}

// Erzeuge einen eindeutigen Schlüssel für ein Begriffspaar (alphabetisch sortiert)
function getRelationshipKey(term1, term2) {
  const sorted = [term1.toLowerCase(), term2.toLowerCase()].sort();
  return `${sorted[0]}|${sorted[1]}`;
}

// Finde Co-Occurrences in Paragraphen (inkl. benachbarter Paragraphen)
function findCoOccurrences(term1, term2, limit = 100) {
  const results = [];
  const term1Lower = term1.toLowerCase();
  const term2Lower = term2.toLowerCase();
  
  // Gruppiere Paragraphen nach Vortrag
  const lectureGroups = {};
  paragraphsFromLectures.forEach((p, idx) => {
    const lectureId = p.ID || 'unknown';
    if (!lectureGroups[lectureId]) {
      lectureGroups[lectureId] = [];
    }
    lectureGroups[lectureId].push({ ...p, globalIndex: idx });
  });
  
  // Durchsuche jeden Vortrag
  Object.entries(lectureGroups).forEach(([lectureId, paragraphs]) => {
    paragraphs.forEach((p, localIdx) => {
      const content = (p.content || '').toLowerCase();
      const hasTerm1 = content.includes(term1Lower);
      const hasTerm2 = content.includes(term2Lower);
      
      // Fall 1: Beide Begriffe im selben Paragraph
      if (hasTerm1 && hasTerm2) {
        results.push({
          type: 'same',
          lectureId: lectureId,
          index: p.index || p.globalIndex,
          content: p.content,
          title: p.title || lectureId,
          score: 1.0
        });
        return;
      }
      
      // Fall 2: Begriff 1 hier, Begriff 2 in benachbartem Paragraph
      if (hasTerm1) {
        // Prüfe vorherigen Paragraph
        if (localIdx > 0) {
          const prevContent = (paragraphs[localIdx - 1].content || '').toLowerCase();
          if (prevContent.includes(term2Lower)) {
            results.push({
              type: 'adjacent',
              lectureId: lectureId,
              index: p.index || p.globalIndex,
              content: paragraphs[localIdx - 1].content + ' [...] ' + p.content,
              title: p.title || lectureId,
              score: 0.8
            });
          }
        }
        // Prüfe nächsten Paragraph
        if (localIdx < paragraphs.length - 1) {
          const nextContent = (paragraphs[localIdx + 1].content || '').toLowerCase();
          if (nextContent.includes(term2Lower)) {
            results.push({
              type: 'adjacent',
              lectureId: lectureId,
              index: p.index || p.globalIndex,
              content: p.content + ' [...] ' + paragraphs[localIdx + 1].content,
              title: p.title || lectureId,
              score: 0.8
            });
          }
        }
      }
    });
  });
  
  // Sortiere nach Score und entferne Duplikate
  const seen = new Set();
  const unique = results.filter(r => {
    const key = `${r.lectureId}:${r.index}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  
  return unique.sort((a, b) => b.score - a.score).slice(0, limit);
}

// Extrahiere Kurzaspekte mit KI
async function extractRelationshipAspects(term1, term2, coOccurrences) {
  if (coOccurrences.length === 0) {
    return [];
  }
  
  // Hole passenden LLM-Provider (keywords-Provider, default: Claude)
  let provider;
  try {
    provider = getProviderForTask('keywords');
    if (!provider || !provider.isAvailable()) {
      throw new Error('Kein LLM-Provider verfügbar');
    }
  } catch (error) {
    console.error('[RELATIONSHIPS] Kein LLM-Provider verfügbar:', error);
    // Fallback: Einfache Extraktion ohne KI
    return coOccurrences.slice(0, 20).map(co => {
      const sentence = extractSentenceWithTerms(co.content, term1, term2);
      return {
        text: sentence.length > 80 ? sentence.substring(0, 77) + '...' : sentence,
        gaRef: co.lectureId + ':' + co.index,
        score: co.score
      };
    });
  }
  
  // Bereite Kontext für KI vor - wähle aus VERSCHIEDENEN Vorträgen, aber erlaube mehrere pro Vortrag
  // Gruppiere nach Vortrag (lectureId) und wähle max 2 pro Vortrag
  const byLecture = {};
  coOccurrences.forEach(co => {
    const lectureId = co.lectureId;
    if (!byLecture[lectureId]) byLecture[lectureId] = [];
    byLecture[lectureId].push(co);
  });
  
  // Wähle max 2 Fundstellen pro Vortrag, bis zu 30 insgesamt
  const diverseOccurrences = [];
  const lectures = Object.keys(byLecture).sort(() => Math.random() - 0.5); // Mische die Vorträge
  let round = 0;
  while (diverseOccurrences.length < 30 && round < 2) {
    for (const lecture of lectures) {
      if (diverseOccurrences.length >= 30) break;
      if (byLecture[lecture][round]) {
        diverseOccurrences.push(byLecture[lecture][round]);
      }
    }
    round++;
  }
  
  const contextParagraphs = diverseOccurrences.map((co, i) => 
    `[${i + 1}] ${co.lectureId}:${co.index}\n${co.content.substring(0, 500)}`
  ).join('\n\n---\n\n');
  
  const prompt = `Extrahiere KURZE Stichpunkte zur Beziehung zwischen "${term1}" und "${term2}".

WICHTIG - KONTEXT BEACHTEN:
- Lies jeden Textabschnitt SORGFÄLTIG und verstehe den KONTEXT
- Extrahiere NUR Aspekte, die TATSÄCHLICH im Text beschrieben werden
- Der Aspekt muss den SINN des Textes korrekt wiedergeben
- KEINE Interpretation oder Vermutung - nur was explizit dasteht

FORMAT: Kurze Aussagen (5-10 Worte), KEINE Zitate!
- OHNE "${term1}" am Anfang! Beginne direkt mit dem Verb (3. Person Singular)
- Verb + kurze Beschreibung
- KEINE Anführungszeichen, KEINE langen Sätze

STRENGE REGELN:

1. NUR BEZIEHUNGSASPEKTE: Jeder Aspekt MUSS die Beziehung zwischen ${term1} und ${term2} beschreiben!
   - "${term2}" MUSS im Aspekt vorkommen oder direkt gemeint sein
   - KEINE Aussagen nur über ${term1} allein!

2. KONTEXTTREUE: Der Aspekt muss mit dem Kontext des Textabschnitts übereinstimmen!
   - Was ist die Hauptaussage des Absatzes?
   - In welchem Zusammenhang werden ${term1} und ${term2} erwähnt?

3. KEINE REDUNDANZEN:
   - Sagt dieser Aspekt INHALTLICH dasselbe wie ein anderer? → WEGLASSEN
   - Mehrere VERSCHIEDENE Aspekte aus demselben Vortrag sind OK!

BEISPIELE für RICHTIGE Kurzaspekte (Beziehung zu ${term2}!):
- "schließt Bund mit ${term2}"
- "kämpft mit ${term2} in der Menschenseele"  
- "unterscheidet sich klar von ${term2}"
- "wirkt gemeinsam mit ${term2}"

BEISPIELE für FALSCHE Aspekte (zu vermeiden):
❌ "wirkte auf Ätherleib" (kein Bezug zu ${term2}!)
❌ "${term1} schließt Bund..." (NICHT mit "${term1}" beginnen!)
❌ Aspekte, die nicht im Kontext des Textes stehen

TEXTSTELLEN:
${contextParagraphs}

Antworte NUR im JSON-Format:
{
  "aspects": [
    {"text": "beginnt mit Verb", "source": 1},
    {"text": "weiterer Stichpunkt aus anderer Quelle", "source": 5}
  ]
}

Bis zu 24 Aspekte, aber NUR bei Einhaltung aller Kriterien (keine Redundanz, verschiedene Vorträge). KEIN Aspekt darf mit "${term1}" beginnen!`;

  try {
    const response = await provider.generateCompletion(prompt, { maxTokens: 3000 });
    
    // Parse JSON aus Antwort
    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      
      // Mappe die Aspekte auf die Quellenangaben
      return (parsed.aspects || []).map(a => {
        const sourceIdx = (a.source || 1) - 1;
        const co = diverseOccurrences[sourceIdx] || diverseOccurrences[0];
        return {
          text: a.text,
          gaRef: co ? (co.lectureId + ':' + co.index) : null,
          score: co ? co.score : 0.5
        };
      });
    }
  } catch (error) {
    console.error('[RELATIONSHIPS] KI-Extraktion fehlgeschlagen:', error);
  }
  
  // Fallback
  return coOccurrences.slice(0, 10).map(co => ({
    text: extractSentenceWithTerms(co.content, term1, term2).substring(0, 80),
    gaRef: co.lectureId + ':' + co.index,
    score: co.score
  }));
}

// Hilfsfunktion: Extrahiere Satz mit beiden Begriffen
function extractSentenceWithTerms(text, term1, term2) {
  const sentences = text.split(/[.!?]+/);
  const t1 = term1.toLowerCase();
  const t2 = term2.toLowerCase();
  
  // Suche Satz mit beiden Begriffen
  for (const s of sentences) {
    const sLower = s.toLowerCase();
    if (sLower.includes(t1) && sLower.includes(t2)) {
      return s.trim();
    }
  }
  
  // Suche Satz mit mindestens einem Begriff
  for (const s of sentences) {
    const sLower = s.toLowerCase();
    if (sLower.includes(t1) || sLower.includes(t2)) {
      return s.trim();
    }
  }
  
  return text.substring(0, 150);
}

// API-Endpunkt: Beziehungs-Suche
app.post('/api/relationship-search', async (req, res) => {
  try {
    const { term1, term2, forceRefresh = false } = req.body;
    
    if (!term1 || !term2) {
      return res.status(400).json({ error: 'term1 und term2 sind erforderlich' });
    }
    
    const key = getRelationshipKey(term1, term2);
    
    // Prüfe Cache (max 7 Tage alt)
    if (!forceRefresh && relationshipsCache[key]) {
      const cached = relationshipsCache[key];
      const age = Date.now() - new Date(cached.generatedAt).getTime();
      const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 Tage
      
      if (age < maxAge) {
        console.log(`[RELATIONSHIPS] Cache-Hit für ${key}`);
        return res.json({
          ...cached,
          fromCache: true
        });
      }
    }
    
    console.log(`[RELATIONSHIPS] Suche Beziehung: ${term1} <-> ${term2}`);
    
    // 1. Finde Co-Occurrences
    const coOccurrences = findCoOccurrences(term1, term2, 50);
    console.log(`[RELATIONSHIPS] ${coOccurrences.length} Co-Occurrences gefunden`);
    
    if (coOccurrences.length === 0) {
      return res.json({
        term1,
        term2,
        aspects: [],
        totalOccurrences: 0,
        message: 'Keine gemeinsamen Fundstellen'
      });
    }
    
    // 2. Extrahiere Kurzaspekte mit KI
    const aspects = await extractRelationshipAspects(term1, term2, coOccurrences);
    console.log(`[RELATIONSHIPS] ${aspects.length} Aspekte extrahiert`);
    
    // 3. Erstelle Ergebnis
    const result = {
      term1,
      term2,
      aspects,
      totalOccurrences: coOccurrences.length,
      generatedAt: new Date().toISOString()
    };
    
    // 4. Speichere im Cache
    relationshipsCache[key] = result;
    await saveRelationshipsDatabase();
    
    res.json({
      ...result,
      fromCache: false
    });
    
  } catch (error) {
    console.error('[RELATIONSHIPS] API-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Lade Beziehungs-DB beim Start
loadRelationshipsDatabase();

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
    
    
    // Parse JSON-Antwort
    let generatedKeywords;
    try {
      // Entferne mögliche Markdown-Code-Blöcke
      const cleanText = generatedText.replace(/```json\n?/g, '').replace(/```\n?/g, '');
      generatedKeywords = JSON.parse(cleanText);
    } catch (parseError) {
      console.error('[KEYWORDS-GENERATE] JSON Parse Fehler:', parseError);
      
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
    
    if (Object.keys(fullLectures).length === 0) {
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
          lectureNumber: lecture.lectureNumber,
          paragraphs: lecture.paragraphs || []  // NEU: Absätze mit Indices für Timeline-Überschriften
        };
      }
    });
    
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
    
    // Prüfe ob Request von localhost kommt
    const isLocalRequest = req.hostname === 'localhost' || 
                           req.hostname === '127.0.0.1' || 
                           req.ip === '::1' ||
                           req.ip === '127.0.0.1';
    
    
    // Cache-System für Keyword-Thematische Suche
    const cacheKey = `keyword_${query.toLowerCase().trim()}_${effectiveDepth}_${limit}`;
    const keywordThematicDB = await loadKeywordThematicDatabase();
    
    // Prüfe Cache (nur wenn useCache true ist)
    if (useCache && keywordThematicDB[cacheKey]) {
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
      
      // Cache leeres Ergebnis nur bei localhost
      if (isLocalRequest) {
        keywordThematicDB[cacheKey] = {
          ...emptyResult,
          timestamp: new Date().toISOString()
        };
        await saveKeywordThematicDatabase(keywordThematicDB);
      } else {
      }
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
    
    // Speichere im Cache nur bei localhost
    if (isLocalRequest) {
      keywordThematicDB[cacheKey] = {
        ...searchResult,
        timestamp: new Date().toISOString()
      };
      
      // Speichere Cache-DB (non-blocking)
      saveKeywordThematicDatabase(keywordThematicDB).then(() => {
      }).catch(err => {
        console.warn('[KEYWORD-THEMATIC-CACHE] Fehler beim Cachen:', err.message);
      });
    } else {
    }
    
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
app.post('/api/concepts-save', async (req, res) => {
  try {
    const { keyword, alphabetical, text, gaReferences } = req.body;
    
    if (!keyword || !text) {
      return res.status(400).json({ 
        error: 'keyword und text sind erforderlich',
        received: { keyword, alphabetical, text, gaReferences }
      });
    }
    
    
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
      }
    } catch (error) {
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
    } else {
      // Add new keyword
      allKeywords.push(newKeyword);
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

// Concepts-Thematic-Search-Cache-Database
const CONCEPTS_THEMATIC_DB_FILE = path.join(__dirname, 'concepts-thematic-search.json');

// Lade Keyword-Thematische-Suche-Cache-Datenbank
async function loadKeywordThematicDatabase() {
  try {
    const data = await fs.readFile(CONCEPTS_THEMATIC_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return {};
  }
}

// Speichere Keyword-Thematische-Suche-Cache-Datenbank
async function saveKeywordThematicDatabase(keywordThematicDB) {
  try {
    await fs.writeFile(CONCEPTS_THEMATIC_DB_FILE, JSON.stringify(keywordThematicDB, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Keyword-Thematische-Suche-Cache-DB:', error);
    return false;
  }
}

// API-Endpunkt: Batch-Schlagwort-Generierung
// Verarbeitet bis zu 10 Schlagwörter parallel
app.post('/api/concepts-batch-add', async (req, res) => {
  try {
    const { keywords, overwrite = false, batchId = null, concurrency = 10 } = req.body;
    
    if (!keywords || !Array.isArray(keywords) || keywords.length === 0) {
      return res.status(400).json({ 
        error: 'keywords Array erforderlich (mindestens 1 Schlagwort)',
        received: { keywords, overwrite, batchId }
      });
    }
    
    // Maximale Concurrency: 10 (um API Rate Limits zu vermeiden)
    const effectiveConcurrency = Math.min(concurrency, 10);
    
    
    const results = {
      batchId: batchId || `batch_${Date.now()}`,
      totalKeywords: keywords.length,
      processed: 0,
      successful: [],
      failed: [],
      skipped: [],
      startTime: new Date().toISOString()
    };
    
    // Lade concepts-database.json einmalig vor der Verarbeitung
    const conceptsFile = path.join(__dirname, 'concepts-database.json');
    let allConcepts = [];
    
    try {
      const fileContent = await fs.readFile(conceptsFile, 'utf8');
      allConcepts = JSON.parse(fileContent);
    } catch (error) {
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
      
      
      // Prüfe auf Duplikate
      const existingConceptIndex = allConcepts.findIndex(k => 
        k.keyword.toLowerCase() === trimmedKeyword.toLowerCase()
      );
      
      if (existingConceptIndex !== -1 && !overwrite) {
        return {
          status: 'skipped',
          keyword: trimmedKeyword,
          reason: 'Concept bereits vorhanden',
          index: i,
          existingKeyword: allConcepts[existingConceptIndex].keyword
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
      
      // Führe BEIDE KI-Prompts parallel aus (unabhängig voneinander):
      // 1. Bestehender Prompt für KI-Suchergebnis (Content Fenster)
      // 2. Themen_Übersicht-Prompt (Main Viewer)
      
      const [analysisResult, overviewResult] = await Promise.allSettled([
        generateConceptAnalysis(trimmedKeyword, keywordResults),
        generateConceptOverviewData(trimmedKeyword, '')
      ]);
      
      // Verarbeite Ergebnisse unabhängig voneinander
      let analysis;
      if (analysisResult.status === 'fulfilled') {
        analysis = analysisResult.value;
      } else {
        console.error(`[KEYWORDS-BATCH-ADD] KI-Suchergebnis fehlgeschlagen für "${trimmedKeyword}":`, analysisResult.reason?.message || analysisResult.reason);
        analysis = `Fehler bei der Generierung des KI-Suchergebnisses: ${analysisResult.reason?.message || 'Unbekannter Fehler'}`;
      }
      
      let overviewData;
      if (overviewResult.status === 'fulfilled') {
        overviewData = overviewResult.value;
      } else {
        console.error(`[KEYWORDS-BATCH-ADD] Themen_Übersicht fehlgeschlagen für "${trimmedKeyword}":`, overviewResult.reason?.message || overviewResult.reason);
        overviewData = {
          overview: {
            alternativeTerms: [],
            definitionText: 'Themen_Übersicht konnte nicht generiert werden.',
            functionText: 'Themen_Übersicht konnte nicht generiert werden.',
            interactionText: 'Themen_Übersicht konnte nicht generiert werden.',
            specialText: 'Themen_Übersicht konnte nicht generiert werden.'
          }
        };
      }
      
      // Erstelle neues Concept-Objekt mit vollständigem Text und Themen_Übersicht
      const newConcept = {
        keyword: trimmedKeyword,
        alphabetical: trimmedKeyword.charAt(0).toUpperCase(),
        text: analysis, // ← VOLLSTÄNDIGER Text für Content Fenster (KI-Suchergebnis)
        overview: overviewData.overview, // ← Themen_Übersicht für Main Viewer
        sources: keywordResults.slice(0, 20).map(result => ({
          id: result.ID,
          index: result.index,
          title: result.title,
          fileName: result.fileName
        })),
        gaReferences: keywordResults.slice(0, 20).map(r => r.ID),
        source: 'ki-generated-batch',
        promptVersion: 'concept-v1', // Markierung für neuen Concept-Prompt
        overviewVersion: 'overview-v1', // Markierung für Themen_Übersicht
        generatedAt: new Date().toISOString(),
        totalMatches: keywordResults.length,
        batchId: results.batchId,
        batchIndex: i
      };
      
      
      return {
        status: 'successful',
        keyword: trimmedKeyword,
        index: i,
        resultCount: keywordResults.length,
        analysisLength: analysis.length,
        newConcept: newConcept,
        existingConceptIndex: existingConceptIndex
      };
    };
    
    // Verarbeite alle Schlagwörter parallel
    // Concurrency: 5 = Bis zu 5 API-Anfragen gleichzeitig
    // Delay: 200ms = Verzögerung zwischen Starts (Rate-Limit-Schutz)
    const batchResults = await processBatchWithConcurrency(
      keywords,
      processKeyword,
      effectiveConcurrency,  // Concurrency Limit (max 5)
      200 // Delay zwischen Starts in ms
    );
    
    // Sammle Ergebnisse und aktualisiere concepts.json
    for (const result of batchResults) {
      if (result.success) {
        const data = result.result;
        
        if (data.status === 'successful') {
          // Aktualisiere allConcepts Array
          if (data.existingConceptIndex !== -1 && overwrite) {
            allConcepts[data.existingConceptIndex] = data.newConcept;
          } else if (data.existingConceptIndex === -1) {
            allConcepts.push(data.newConcept);
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
    
    // Speichere aktualisierte concepts-database.json
    await fs.writeFile(conceptsFile, JSON.stringify(allConcepts, null, 2), 'utf8');
    
    results.endTime = new Date().toISOString();
    results.duration = new Date(results.endTime) - new Date(results.startTime);
    
    
    res.json({
      success: true,
      message: `Batch-Verarbeitung abgeschlossen: ${results.successful.length}/${results.totalKeywords} Schlagwörter erfolgreich`,
      concurrency: effectiveConcurrency,
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
app.post('/api/concepts-add', async (req, res) => {
  try {
    const { keyword, overwrite = false } = req.body;
    
    if (!keyword || !keyword.trim()) {
      return res.status(400).json({ error: 'Schlagwort erforderlich' });
    }
    
    const cleanKeyword = keyword.trim();
    
    // Prüfe ob Schlagwort bereits existiert
    const keywordsFile = path.join(__dirname, 'keywords.json');
    let allKeywords = [];
    
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
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
    
    let keywordResults = performThematicKeywordSearch(cleanKeyword, paragraphsFromLectures);
    
    if (keywordResults.length === 0) {
      return res.status(404).json({ 
        error: 'Keine relevanten Textstellen für dieses Schlagwort gefunden',
        keyword: cleanKeyword
      });
    }
    
    // Führe BEIDE KI-Prompts parallel aus (unabhängig voneinander):
    // 1. Bestehender Prompt für KI-Suchergebnis (Content Fenster)
    // 2. Themen_Übersicht-Prompt (Main Viewer)
    
    const [analysisResult, overviewResult] = await Promise.allSettled([
      generateConceptAnalysis(cleanKeyword, keywordResults),
      generateConceptOverviewData(cleanKeyword, '')
    ]);
    
    // Verarbeite Ergebnisse unabhängig voneinander
    let analysis;
    if (analysisResult.status === 'fulfilled') {
      analysis = analysisResult.value;
    } else {
      console.error(`[KEYWORDS-ADD] KI-Suchergebnis fehlgeschlagen:`, analysisResult.reason?.message || analysisResult.reason);
      analysis = `Fehler bei der Generierung des KI-Suchergebnisses: ${analysisResult.reason?.message || 'Unbekannter Fehler'}`;
    }
    
    let overviewData;
    if (overviewResult.status === 'fulfilled') {
      overviewData = overviewResult.value;
    } else {
      console.error(`[KEYWORDS-ADD] Themen_Übersicht fehlgeschlagen:`, overviewResult.reason?.message || overviewResult.reason);
      overviewData = {
        overview: {
          alternativeTerms: [],
          definitionText: 'Themen_Übersicht konnte nicht generiert werden.',
          functionText: 'Themen_Übersicht konnte nicht generiert werden.',
          interactionText: 'Themen_Übersicht konnte nicht generiert werden.',
          specialText: 'Themen_Übersicht konnte nicht generiert werden.'
        }
      };
    }
    
    // Erstelle neues Schlagwort-Objekt mit vollständigem Text, Sources und Themen_Übersicht
    const conceptsFile = path.join(__dirname, 'concepts-database.json');
    
    const newConcept = {
      keyword: cleanKeyword,
      alphabetical: cleanKeyword.charAt(0).toUpperCase(),
      text: analysis, // ← VOLLSTÄNDIGER Text für Content Fenster (KI-Suchergebnis)
      overview: overviewData.overview, // ← Themen_Übersicht für Main Viewer
      sources: keywordResults.slice(0, 20).map(result => ({
        id: result.ID,
        index: result.index,
        title: result.title,
        fileName: result.fileName
      })),
      gaReferences: keywordResults.slice(0, 20).map(r => r.ID),
      source: 'ki-generated',
      promptVersion: 'concept-v1', // Markierung für neuen Concept-Prompt
      overviewVersion: 'overview-v1', // Markierung für Themen_Übersicht
      generatedAt: new Date().toISOString(),
      totalMatches: keywordResults.length
    };
    
    // Lade concepts-database.json
    let allConcepts = [];
    try {
      const conceptsContent = await fs.readFile(conceptsFile, 'utf8');
      allConcepts = JSON.parse(conceptsContent);
    } catch (error) {
    }
    
    // Prüfe auf Duplikate in concepts-database.json
    const existingConceptIndex = allConcepts.findIndex(k => 
      k.keyword.toLowerCase() === cleanKeyword.toLowerCase()
    );
    
    if (existingConceptIndex !== -1 && overwrite) {
      // Überschreibe bestehendes Concept
      allConcepts[existingConceptIndex] = newConcept;
    } else if (existingConceptIndex === -1) {
      // Füge zur Liste hinzu
      allConcepts.push(newConcept);
    }
    
    // Speichere direkt in concepts-database.json
    await fs.writeFile(conceptsFile, JSON.stringify(allConcepts, null, 2), 'utf8');
    
    
    res.json({ 
      success: true, 
      message: 'Concept erfolgreich hinzugefügt und analysiert',
      keyword: newConcept,
      // Beide Ergebnisse zurückgeben
      analysis: analysis, // Für Content Fenster (KI-Suchergebnis)
      overview: overviewData.overview, // Für Main Viewer (Themen_Übersicht)
      totalConcepts: allConcepts.length,
      analysisLength: analysis.length,
      resultCount: keywordResults.length
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
      }
    });

    // Lösche aus zentraler DB mit robustem Locking
    deletedCount = await deleteSummariesFromDatabase(toDelete);



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

app.post('/api/concepts-delete', async (req, res) => {
  try {
    const { keyword } = req.body;
    if (!keyword || !keyword.trim()) {
      return res.status(400).json({ error: 'Schlagwort erforderlich' });
    }

    const cleanKeyword = keyword.trim();

    // Entferne aus concepts-database.json
    const conceptsFile = path.join(__dirname, 'concepts-database.json');
    let allConcepts = [];
    try {
      const fileContent = await fs.readFile(conceptsFile, 'utf8');
      allConcepts = JSON.parse(fileContent);
    } catch (error) {
    }

    const beforeCount = allConcepts.length;
    
    // Finde das zu löschende Concept
    const conceptToDelete = allConcepts.find(k => k.keyword.toLowerCase() === cleanKeyword.toLowerCase());
    
    // Filter heraus
    allConcepts = allConcepts.filter(k => k.keyword.toLowerCase() !== cleanKeyword.toLowerCase());
    const removedCount = beforeCount - allConcepts.length;

    if (beforeCount !== allConcepts.length) {
      await fs.writeFile(conceptsFile, JSON.stringify(allConcepts, null, 2), 'utf8');
      
      // Wenn es ein Obsidian-Concept war, zur Blacklist hinzufügen
      if (conceptToDelete && conceptToDelete.source === 'obsidian-az') {
        const blacklistFile = path.join(__dirname, 'concepts-blacklist.json');
        let blacklist = [];
        
        try {
          const blacklistContent = await fs.readFile(blacklistFile, 'utf8');
          blacklist = JSON.parse(blacklistContent);
        } catch (error) {
        }
        
        if (!blacklist.includes(cleanKeyword)) {
          blacklist.push(cleanKeyword);
          await fs.writeFile(blacklistFile, JSON.stringify(blacklist, null, 2), 'utf8');
        }
      }
    } else {
    }

    return res.json({
      success: true,
      message: removedCount > 0 ? 'Concept erfolgreich gelöscht' : 'Concept nicht gefunden',
      removed: removedCount > 0,
      deletedCount: removedCount,
      wasObsidian: conceptToDelete?.source === 'obsidian-az'
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
// KONZEPT-NETZWERK API (Semantische + Kontext-basierte Analyse)
// ============================================================================

const CONCEPT_NETWORK_FILE = path.join(__dirname, 'concepts-network.json');

// Cache für Netzwerk-Daten (in-memory)
let conceptNetworkCache = {};

// Lade Netzwerk-Daten aus Datei
async function loadConceptNetwork() {
  try {
    if (fsSync.existsSync(CONCEPT_NETWORK_FILE)) {
      const content = await fs.readFile(CONCEPT_NETWORK_FILE, 'utf8');
      conceptNetworkCache = JSON.parse(content);
      console.log(`[CONCEPT-NETWORK] Cache geladen: ${Object.keys(conceptNetworkCache).length} Konzepte`);
    }
  } catch (error) {
    console.error('[CONCEPT-NETWORK] Fehler beim Laden:', error.message);
    conceptNetworkCache = {};
  }
  return conceptNetworkCache;
}

// Speichere Netzwerk-Daten in Datei
async function saveConceptNetwork() {
  try {
    await fs.writeFile(CONCEPT_NETWORK_FILE, JSON.stringify(conceptNetworkCache, null, 2), 'utf8');
  } catch (error) {
    console.error('[CONCEPT-NETWORK] Fehler beim Speichern:', error.message);
  }
}

/**
 * Generiert verwandte Begriffe für ein Konzept durch:
 * 1. Semantische KI-Analyse (findet thematisch verwandte Begriffe)
 * 2. Kontext-basierte Analyse (Co-Occurrence - welche Begriffe kommen oft zusammen vor)
 */
async function generateConceptNetwork(concept, forceRefresh = false) {
  const conceptLower = concept.toLowerCase();
  
  // Prüfe Cache (wenn nicht force refresh)
  if (!forceRefresh && conceptNetworkCache[conceptLower]) {
    const cached = conceptNetworkCache[conceptLower];
    // Cache ist gültig wenn weniger als 30 Tage alt
    const cacheAge = Date.now() - new Date(cached.generated_at).getTime();
    const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 Tage
    if (cacheAge < maxAge) {
      console.log(`[CONCEPT-NETWORK] Cache-Hit für "${concept}" (${cached.connections?.length || 0} Verbindungen)`);
      return { ...cached, fromCache: true };
    }
  }
  
  console.log(`[CONCEPT-NETWORK] Generiere Netzwerk für: "${concept}"`);
  
  // === 1. KONTEXT-BASIERTE ANALYSE (Co-Occurrence) ===
  // Finde Begriffe, die häufig im gleichen Kontext vorkommen
  const contextIndex = generateContextIndex(concept, 50, 3); // 50 Wörter Kontext, min 3 Vorkommen
  let coOccurrenceTerms = [];
  
  if (contextIndex && contextIndex.context_terms) {
    // Filtere die Top-Begriffe aus dem Kontext
    const sortedTerms = Object.entries(contextIndex.context_terms)
      .filter(([term]) => {
        const termLower = term.toLowerCase();
        // Filtere das Suchwort selbst und sehr kurze Wörter
        return termLower !== conceptLower && 
               term.length > 3 &&
               !termLower.includes(conceptLower) &&
               !conceptLower.includes(termLower);
      })
      .sort((a, b) => b[1] - a[1])
      .slice(0, 30); // Top 30 Co-Occurrence Begriffe
    
    coOccurrenceTerms = sortedTerms.map(([term, count]) => ({
      term,
      count,
      source: 'context'
    }));
  }
  
  // === 2. SEMANTISCHE KI-ANALYSE ===
  // Finde thematisch verwandte Begriffe durch KI
  let semanticTerms = [];
  
  try {
    // Führe Keyword-Suche durch für Kontext
    let keywordResults = performThematicKeywordSearch(concept, paragraphsFromLectures);
    
    if (keywordResults.length > 0) {
      // Begrenze auf Top 50 für KI-Analyse
      const topResults = keywordResults.slice(0, 50);
      
      // Erstelle Kontext-Text für KI
      const contextText = topResults
        .map((result, index) => {
          const content = result.content.length > 300 
            ? result.content.substring(0, 300) + '...' 
            : result.content;
          return `[${index + 1}] ${content}`;
        })
        .join('\n\n');
      
      // KI-Prompt für verwandte Begriffe
      const prompt = `Analysiere die folgenden Textstellen aus Rudolf Steiners Werk zum Begriff "${concept}".

AUFGABE:
Identifiziere die WICHTIGSTEN VERWANDTEN KONZEPTE, die mit "${concept}" in direkter Beziehung stehen.

REGELN:
1. Finde 8-15 zentrale Begriffe, die mit "${concept}" eng verbunden sind
2. Priorisiere anthroposophische Fachbegriffe und Konzepte
3. Kategorisiere jeden Begriff nach Beziehungstyp:
   - "hierarchisch": Über-/Unterordnung (z.B. "Alter Saturn" → "Weltentwicklung")
   - "komponente": Teil von / besteht aus (z.B. "1. Hierarchie" → "Throne")
   - "prozess": Wirkt auf / wird beeinflusst von
   - "korrespondenz": Entspricht / steht in Analogie zu
   - "gegensatz": Polarität / Gegenbegriff

4. WICHTIG: 
   - NUR Begriffe aus den Textstellen verwenden
   - Keine allgemeinen Wörter (der, die, das, und, oder, etc.)
   - Keine Verben, nur Substantive/Konzepte
   - Deutsche Begriffe bevorzugen

TEXTSTELLEN:
${contextText}

AUSGABE (JSON-Array):
[
  {"term": "Begriffsname", "type": "hierarchisch|komponente|prozess|korrespondenz|gegensatz", "relevance": 0.0-1.0},
  ...
]

Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text oder Markdown.`;

      // Rufe KI auf
      const response = await generateCompletionWithFallback(prompt, {
        temperature: 0.3,
        maxTokens: 2000
      }, 'analysis');
      
      const responseText = response.text || response.content || '';
      
      // Parse JSON-Antwort
      try {
        // Extrahiere JSON aus Antwort (falls in Markdown eingebettet)
        let jsonStr = responseText;
        const jsonMatch = responseText.match(/\[[\s\S]*\]/);
        if (jsonMatch) {
          jsonStr = jsonMatch[0];
        }
        
        const parsed = JSON.parse(jsonStr);
        if (Array.isArray(parsed)) {
          semanticTerms = parsed
            .filter(item => item.term && item.term.length > 2)
            .map(item => ({
              term: item.term,
              type: item.type || 'prozess',
              relevance: item.relevance || 0.5,
              source: 'semantic'
            }));
        }
      } catch (parseError) {
        console.error('[CONCEPT-NETWORK] JSON-Parse-Fehler:', parseError.message);
      }
    }
  } catch (error) {
    console.error('[CONCEPT-NETWORK] KI-Analyse-Fehler:', error.message);
  }
  
  // === 3. KOMBINIERE UND RANKE ERGEBNISSE ===
  const combinedTerms = new Map();
  
  // Füge semantische Begriffe hinzu (höhere Gewichtung)
  semanticTerms.forEach(item => {
    const key = item.term.toLowerCase();
    if (!combinedTerms.has(key)) {
      combinedTerms.set(key, {
        term: item.term,
        type: item.type,
        score: item.relevance * 1.5, // Semantische Begriffe gewichten
        sources: ['semantic']
      });
    }
  });
  
  // Füge Co-Occurrence Begriffe hinzu
  coOccurrenceTerms.forEach(item => {
    const key = item.term.toLowerCase();
    if (combinedTerms.has(key)) {
      // Begriff existiert bereits - erhöhe Score
      const existing = combinedTerms.get(key);
      existing.score += 0.3;
      existing.sources.push('context');
    } else {
      // Neuer Begriff
      const normalizedScore = Math.min(1, item.count / 20); // Normalisiere Count
      combinedTerms.set(key, {
        term: item.term,
        type: 'prozess', // Default-Typ für Co-Occurrence
        score: normalizedScore,
        sources: ['context']
      });
    }
  });
  
  // Sortiere nach Score und begrenze auf Top 15
  const connections = Array.from(combinedTerms.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, 15)
    .map(item => ({
      term: item.term,
      type: item.type,
      strength: Math.round(item.score * 100) / 100,
      sources: item.sources
    }));
  
  // === 4. ERSTELLE ERGEBNIS ===
  const result = {
    concept: concept,
    connections: connections,
    totalOccurrences: contextIndex?.total_occurrences || 0,
    lecturesWithTerm: contextIndex?.lectures_with_term || 0,
    generated_at: new Date().toISOString()
  };
  
  // Speichere im Cache
  conceptNetworkCache[conceptLower] = result;
  
  // === 5. ERGÄNZE RÜCKVERBINDUNGEN ===
  // Füge bei allen gefundenen Verbindungen eine Rückverbindung zum aktuellen Konzept hinzu
  let backlinksAdded = 0;
  connections.forEach(conn => {
    const connLower = conn.term.toLowerCase();
    
    // Prüfe ob der verbundene Begriff bereits ein Netzwerk hat
    if (conceptNetworkCache[connLower]) {
      const existingNetwork = conceptNetworkCache[connLower];
      
      // Prüfe ob Rückverbindung bereits existiert
      const hasBacklink = existingNetwork.connections?.some(
        c => c.term.toLowerCase() === conceptLower
      );
      
      if (!hasBacklink && existingNetwork.connections) {
        // Füge Rückverbindung hinzu
        const backlink = {
          term: concept,
          type: getInverseRelationType(conn.type),
          strength: conn.strength * 0.8, // Etwas schwächer als Original
          sources: ['backlink'],
          addedFrom: concept,
          addedAt: new Date().toISOString()
        };
        
        existingNetwork.connections.push(backlink);
        existingNetwork.lastUpdated = new Date().toISOString();
        backlinksAdded++;
      }
    }
  });
  
  if (backlinksAdded > 0) {
    console.log(`[CONCEPT-NETWORK] ${backlinksAdded} Rückverbindungen ergänzt`);
  }
  
  await saveConceptNetwork();
  
  console.log(`[CONCEPT-NETWORK] Generiert: ${connections.length} Verbindungen für "${concept}"`);
  
  return result;
}

/**
 * Gibt den inversen Beziehungstyp zurück
 * z.B. wenn A → B "hierarchisch" ist, dann ist B → A auch "hierarchisch"
 */
function getInverseRelationType(type) {
  const inverseMap = {
    'hierarchisch': 'hierarchisch', // Bleibt gleich (bidirektional)
    'komponente': 'komponente',      // Teil-von ist bidirektional
    'prozess': 'prozess',            // Prozess ist bidirektional
    'korrespondenz': 'korrespondenz', // Entsprechung ist bidirektional
    'gegensatz': 'gegensatz'         // Gegensatz ist bidirektional
  };
  return inverseMap[type] || 'prozess';
}

// API-Endpunkt: Konzept-Netzwerk abrufen
app.post('/api/concept-network', async (req, res) => {
  try {
    const { concept, forceRefresh = false } = req.body;
    
    if (!concept || !concept.trim()) {
      return res.status(400).json({ error: 'Konzept ist erforderlich' });
    }
    
    const result = await generateConceptNetwork(concept.trim(), forceRefresh);
    res.json(result);
    
  } catch (error) {
    console.error('[CONCEPT-NETWORK] API-Fehler:', error);
    res.status(500).json({ 
      error: 'Fehler bei der Netzwerk-Generierung',
      details: error.message 
    });
  }
});

// API-Endpunkt: Alle gecachten Netzwerke auflisten
app.get('/api/concept-network/list', async (req, res) => {
  try {
    const concepts = Object.keys(conceptNetworkCache).map(key => ({
      concept: conceptNetworkCache[key].concept,
      connectionCount: conceptNetworkCache[key].connections?.length || 0,
      generatedAt: conceptNetworkCache[key].generated_at,
      lastUpdated: conceptNetworkCache[key].lastUpdated
    }));
    res.json({ concepts, total: concepts.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// API-Endpunkt: Verbindung manuell hinzufügen
app.post('/api/concept-network/add-connection', async (req, res) => {
  try {
    const { concept, targetConcept, type = 'prozess', bidirectional = true } = req.body;
    
    if (!concept || !targetConcept) {
      return res.status(400).json({ error: 'concept und targetConcept sind erforderlich' });
    }
    
    const conceptLower = concept.trim().toLowerCase();
    const targetLower = targetConcept.trim().toLowerCase();
    
    // Prüfe ob Quell-Konzept existiert
    if (!conceptNetworkCache[conceptLower]) {
      return res.status(404).json({ error: `Netzwerk für "${concept}" nicht gefunden. Bitte zuerst generieren.` });
    }
    
    const network = conceptNetworkCache[conceptLower];
    
    // Prüfe ob Verbindung bereits existiert
    const existingConn = network.connections?.find(c => c.term.toLowerCase() === targetLower);
    if (existingConn) {
      return res.json({ 
        message: 'Verbindung existiert bereits',
        connection: existingConn 
      });
    }
    
    // Füge neue Verbindung hinzu
    const newConnection = {
      term: targetConcept.trim(),
      type: type,
      strength: 0.7,
      sources: ['manual'],
      addedAt: new Date().toISOString()
    };
    
    network.connections.push(newConnection);
    network.lastUpdated = new Date().toISOString();
    
    // Bidirektionale Verbindung hinzufügen
    if (bidirectional && conceptNetworkCache[targetLower]) {
      const targetNetwork = conceptNetworkCache[targetLower];
      const hasBacklink = targetNetwork.connections?.some(c => c.term.toLowerCase() === conceptLower);
      
      if (!hasBacklink) {
        targetNetwork.connections.push({
          term: concept.trim(),
          type: getInverseRelationType(type),
          strength: 0.7,
          sources: ['manual', 'backlink'],
          addedAt: new Date().toISOString()
        });
        targetNetwork.lastUpdated = new Date().toISOString();
      }
    }
    
    await saveConceptNetwork();
    
    res.json({ 
      message: 'Verbindung hinzugefügt',
      connection: newConnection,
      bidirectional: bidirectional
    });
    
  } catch (error) {
    console.error('[CONCEPT-NETWORK] Fehler beim Hinzufügen:', error);
    res.status(500).json({ error: error.message });
  }
});

// API-Endpunkt: Verbindung entfernen
app.post('/api/concept-network/remove-connection', async (req, res) => {
  try {
    const { concept, targetConcept, bidirectional = true } = req.body;
    
    if (!concept || !targetConcept) {
      return res.status(400).json({ error: 'concept und targetConcept sind erforderlich' });
    }
    
    const conceptLower = concept.trim().toLowerCase();
    const targetLower = targetConcept.trim().toLowerCase();
    
    if (!conceptNetworkCache[conceptLower]) {
      return res.status(404).json({ error: `Netzwerk für "${concept}" nicht gefunden` });
    }
    
    const network = conceptNetworkCache[conceptLower];
    const initialCount = network.connections?.length || 0;
    
    // Entferne Verbindung
    network.connections = network.connections?.filter(c => c.term.toLowerCase() !== targetLower) || [];
    network.lastUpdated = new Date().toISOString();
    
    // Bidirektionale Entfernung
    if (bidirectional && conceptNetworkCache[targetLower]) {
      const targetNetwork = conceptNetworkCache[targetLower];
      targetNetwork.connections = targetNetwork.connections?.filter(c => c.term.toLowerCase() !== conceptLower) || [];
      targetNetwork.lastUpdated = new Date().toISOString();
    }
    
    await saveConceptNetwork();
    
    const removed = initialCount - (network.connections?.length || 0);
    res.json({ 
      message: removed > 0 ? 'Verbindung entfernt' : 'Verbindung nicht gefunden',
      removed: removed
    });
    
  } catch (error) {
    console.error('[CONCEPT-NETWORK] Fehler beim Entfernen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Lade Netzwerk-Cache beim Server-Start (wird später aufgerufen)
loadConceptNetwork().catch(console.error);

// ============================================================================
// ZENTRALE SUMMARY-DATENBANK
// ============================================================================

const SUMMARY_DB_FILE = path.join(__dirname, 'summary-database.json');
const SUMMARY_KEYWORDS_DB_FILE = path.join(__dirname, 'summary-keywords-database.json');
const THEMATIC_SEARCH_DB_FILE = path.join(__dirname, 'thematic-search-database.json');
const KEYWORDS_DB_FILE = path.join(__dirname, 'keywords-database.json');
const THEMES_DB_FILE = path.join(__dirname, 'themes-database.json');
const CLUSTERS_FILE = path.join(__dirname, 'thematic-clusters.json');
const THEMES_KEYWORDS_TEMPLATE_FILE = path.join(__dirname, 'themes-keywords-template.json');
const QUOTES_DB_FILE = path.join(__dirname, 'quotes-database.json');

// Backup-Verzeichnisse
const BACKUP_BASE_DIR = path.join(__dirname, 'backups');
const KEYWORDS_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'keywords');
const SUMMARY_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'summary');
const THEMES_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'themes');
const CLUSTERS_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'clusters');
const CODE_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'code');
const HTML_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'html');
const IMAGES_BACKUP_DIR = path.join(BACKUP_BASE_DIR, 'images');

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
    HTML_BACKUP_DIR,
    IMAGES_BACKUP_DIR
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
      return null;
    }
    
    // Erstelle Backup mit Timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(backupDir, `${prefix}-${timestamp}.json`);
    
    const data = await fs.readFile(sourceFile, 'utf8');
    await fs.writeFile(backupFile, data, 'utf8');
    
    
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
      .filter(f => f.startsWith(prefix) && (f.endsWith('.json') || f.endsWith('.js') || f.endsWith('.html')))
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

async function createImagesBackup() {
  const imagesFile = path.join(__dirname, 'steiner-images.json');
  return await createBackup(imagesFile, IMAGES_BACKUP_DIR, 'steiner-images', 10);
}

async function createCodeBackup() {
  try {
    await ensureBackupDirectories();
    
    const sourceFile = path.join(__dirname, 'backend.js');
    
    // Prüfe ob Datei existiert
    try {
      const stats = await fs.stat(sourceFile);
      if (stats.size === 0) {
        console.warn('[BACKUP] backend.js ist leer - kein Backup erstellt');
        return null;
      }
    } catch (error) {
      return null;
    }
    
    // Erstelle Backup mit Timestamp (behalte .js Endung!)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(CODE_BACKUP_DIR, `backend-${timestamp}.js`);
    
    const data = await fs.readFile(sourceFile, 'utf8');
    await fs.writeFile(backupFile, data, 'utf8');
    
    
    // Bereinige alte Backups
    await cleanOldBackupsGeneric(CODE_BACKUP_DIR, 'backend', 20);
    
    return backupFile;
  } catch (error) {
    console.error('[BACKUP] Fehler beim Code-Backup:', error);
    return null;
  }
}

async function createHtmlBackup(htmlFile = 'index.html') {
  try {
    await ensureBackupDirectories();
    
    const sourceFile = path.join(__dirname, htmlFile);
    
    // Prüfe ob Datei existiert
    try {
      const stats = await fs.stat(sourceFile);
      if (stats.size === 0) {
        console.warn(`[BACKUP] ${htmlFile} ist leer - kein Backup erstellt`);
        return null;
      }
    } catch (error) {
      return null;
    }
    
    // Erstelle Backup mit Timestamp (behalte .html Endung!)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const prefix = htmlFile.replace('.html', '');
    const backupFile = path.join(HTML_BACKUP_DIR, `${prefix}-${timestamp}.html`);
    
    const data = await fs.readFile(sourceFile, 'utf8');
    await fs.writeFile(backupFile, data, 'utf8');
    
    
    // Bereinige alte Backups (nur für diesen Dateityp)
    await cleanOldBackupsGeneric(HTML_BACKUP_DIR, prefix, 10);
    
    return backupFile;
  } catch (error) {
    console.error(`[BACKUP] Fehler beim HTML-Backup:`, error);
    return null;
  }
}

// Backup für members.html
async function createMembersHtmlBackup() {
  return await createHtmlBackup('members.html');
}

// Backup für members-panel.js
async function createMembersPanelBackup() {
  try {
    await ensureBackupDirectories();
    
    const sourceFile = path.join(__dirname, 'members-panel.js');
    
    // Prüfe ob Datei existiert
    try {
      const stats = await fs.stat(sourceFile);
      if (stats.size === 0) {
        console.warn(`[BACKUP] members-panel.js ist leer - kein Backup erstellt`);
        return null;
      }
    } catch (error) {
      return null;
    }
    
    // Erstelle Backup mit Timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(HTML_BACKUP_DIR, `members-panel-${timestamp}.js`);
    
    const data = await fs.readFile(sourceFile, 'utf8');
    await fs.writeFile(backupFile, data, 'utf8');
    
    
    // Bereinige alte Backups
    await cleanOldBackupsGeneric(HTML_BACKUP_DIR, 'members-panel', 10);
    
    return backupFile;
  } catch (error) {
    console.error(`[BACKUP] Fehler beim Members-Panel-Backup:`, error);
    return null;
  }
}

// Umfassendes Backup aller wichtigen Dateien
async function createFullBackup() {
  const results = await Promise.all([
    createKeywordsBackup(),
    createSummaryBackup(),
    createThemesBackup(),
    createClustersBackup(),
    createImagesBackup(),
    createCodeBackup(),
    createHtmlBackup('index.html'),
    createHtmlBackup('keyword-manager.html'),
    createHtmlBackup('app.html'),
    createMembersHtmlBackup(),
    createMembersPanelBackup()
  ]);
  
  const successful = results.filter(r => r !== null).length;
  
  return successful;
}

// Sichere Funktion zum Speichern der Cluster-Datei (mit Backup)
async function saveClustersFile(clustersData) {
  const clustersPath = path.join(__dirname, 'thematic-clusters.json');
  
  // Erstelle Backup vor dem Speichern
  await createClustersBackup();
  
  // Validiere Daten
  if (!clustersData || (clustersData.clusters && Object.keys(clustersData.clusters).length === 0)) {
    console.warn('[CLUSTERS] WARNUNG: Leere Cluster-Daten - Speichern übersprungen');
    return false;
  }
  
  fsSync.writeFileSync(clustersPath, JSON.stringify(clustersData, null, 2));
  return true;
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
// KEIN Cache für summary-database.json - wird bei jedem Request neu geladen
async function loadSummaryDatabase() {
  try {
    // Lade Datei IMMER neu (kein Cache)
    const data = await fs.readFile(SUMMARY_DB_FILE, 'utf8');
    const parsed = JSON.parse(data);
    const entryCount = Object.keys(parsed).length;
    if (entryCount === 0) {
      console.warn('[SUMMARY-DB] ⚠️  WARNUNG: summary-database.json ist leer!');
    }
    
    // Debug: Prüfe GA001 Überschriften
    if (parsed['GA001'] && parsed['GA001'].headings && parsed['GA001'].headings.length > 0) {
      const firstHeading = parsed['GA001'].headings[0];
      console.log(`[SUMMARY-DB] GA001 erste Überschrift Index: ${firstHeading.index}, Text: ${firstHeading.text.substring(0, 40)}`);
    }
    
    return parsed;
  } catch (error) {
    console.error('[SUMMARY-DB] ❌ Fehler beim Laden:', error.message);
    return {};
  }
}

// Speichere zentrale Summary-Datenbank (veraltet - verwende saveSummaryToDatabase)
async function saveSummaryDatabase(summaryDB) {
  try {
    await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Summary-DB:', error);
    return false;
  }
}

// ============================================================================
// SUMMARY-KEYWORDS-DATENBANK
// ============================================================================

// Lade Summary-Keywords-Datenbank
async function loadSummaryKeywordsDatabase() {
  try {
    const data = await fs.readFile(SUMMARY_KEYWORDS_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return {};
  }
}

// Speichere Summary-Keywords-Datenbank
async function saveSummaryKeywordsDatabase(keywordsDB) {
  try {
    await fs.writeFile(SUMMARY_KEYWORDS_DB_FILE, JSON.stringify(keywordsDB, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Fehler beim Speichern der Summary-Keywords-DB:', error);
    return false;
  }
}

// ROBUSTE FUNKTION: Speichere einzelne Summary in Datenbank (mit Locking & Backup)
// Diese Funktion verhindert Race Conditions bei parallelen Schreibzugriffen
async function saveSummaryToDatabase(lectureId, summaryData) {
  // Reihe diese Operation in die Queue ein
  return new Promise((resolve, reject) => {
    summaryDbWriteQueue = summaryDbWriteQueue.then(async () => {
      try {
        
        // Erstelle Backup vor dem Speichern
        await createSummaryBackup();
        
        // Lade immer die aktuellste Version der Datenbank
        const summaryDB = await loadSummaryDatabase();
        
        // Füge neue Summary hinzu oder aktualisiere bestehende
        summaryDB[lectureId] = {
          summary: summaryData.summary,
          headings: summaryData.headings || [],
          tableOfContents: summaryData.tableOfContents || [],
          lectureKeywords: summaryData.lectureKeywords || [],
          version: summaryData.version || 'v1',
          timestamp: new Date().toISOString()
        };
        
        // Speichere Datenbank
        await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
        
        
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

// ROBUSTE FUNKTION: Speichere komplette Summary-Database (mit Locking)
async function saveCompleteSummaryDatabase(summaryDB) {
  return new Promise((resolve, reject) => {
    summaryDbWriteQueue = summaryDbWriteQueue.then(async () => {
      try {
        
        // Erstelle Backup vor dem Speichern
        await createSummaryBackup();
        
        // Validiere dass wir nicht versuchen, leere Daten zu speichern
        if (!summaryDB || Object.keys(summaryDB).length === 0) {
          console.error('[SUMMARY-LOCK] ✗ WARNUNG: Versuch, leere Datenbank zu speichern - ABGEBROCHEN!');
          reject(new Error('Datenbank ist leer - Speichern abgebrochen'));
          return;
        }
        
        // Speichere Datenbank
        await fs.writeFile(SUMMARY_DB_FILE, JSON.stringify(summaryDB, null, 2), 'utf8');
        
        
        resolve(true);
        
      } catch (error) {
        console.error('[SUMMARY-LOCK] ✗ Fehler beim Speichern:', error);
        reject(error);
      }
    }).catch(error => {
      console.error('[SUMMARY-LOCK] Queue-Fehler:', error);
      reject(error);
    });
  });
}

// API: Summary speichern
// API: Keyword löschen (aus allen Vorträgen)
app.post('/api/keywords-delete', async (req, res) => {
  try {
    const { keyword } = req.body;
    
    if (!keyword) {
      return res.status(400).json({ error: 'keyword ist erforderlich' });
    }
    
    
    // 1. Aktualisiere Keywords-Database
    const keywordsDB = await loadKeywordsDatabase();
    let deletedFromLectures = 0;
    let totalDeleted = 0;
    
    for (const [lectureId, lectureData] of Object.entries(keywordsDB)) {
      if (lectureData.keywords && Array.isArray(lectureData.keywords)) {
        const beforeCount = lectureData.keywords.length;
        lectureData.keywords = lectureData.keywords.filter(kw => kw.term !== keyword);
        const afterCount = lectureData.keywords.length;
        
        if (beforeCount > afterCount) {
          deletedFromLectures++;
          totalDeleted += (beforeCount - afterCount);
        }
      }
    }
    
    await saveCompleteKeywordsDatabase(keywordsDB);
    
    // 2. Aktualisiere Summary-Database
    const summaryDB = await loadSummaryDatabase();
    let deletedFromSummary = 0;
    
    for (const [lectureId, summaryData] of Object.entries(summaryDB)) {
      if (summaryData.lectureKeywords && Array.isArray(summaryData.lectureKeywords)) {
        const beforeCount = summaryData.lectureKeywords.length;
        summaryData.lectureKeywords = summaryData.lectureKeywords.filter(kw => kw.term !== keyword);
        const afterCount = summaryData.lectureKeywords.length;
        
        if (beforeCount > afterCount) {
          deletedFromSummary++;
        }
      }
    }
    
    await saveCompleteSummaryDatabase(summaryDB);
    
    // 3. Aktualisiere Clusters (entferne Keyword aus allen Clustern)
    try {
      const clustersData = await loadClustersFile();
      const clusters = clustersData.clusters || {};
      let removedFromClusters = 0;
      
      for (const [clusterName, clusterInfo] of Object.entries(clusters)) {
        if (clusterInfo.keywords && Array.isArray(clusterInfo.keywords)) {
          const beforeCount = clusterInfo.keywords.length;
          clusterInfo.keywords = clusterInfo.keywords.filter(kw => kw !== keyword);
          
          if (beforeCount > clusterInfo.keywords.length) {
            removedFromClusters++;
          }
        }
      }
      
      if (removedFromClusters > 0) {
        await saveClustersFile({ ...clustersData, clusters });
      }
    } catch (error) {
      console.warn(`[DELETE-KW] Warnung: Clusters konnten nicht aktualisiert werden:`, error.message);
    }
    
    res.json({ 
      success: true, 
      message: `Keyword "${keyword}" gelöscht`,
      deletedFromLectures: deletedFromLectures,
      totalOccurrences: totalDeleted
    });
    
  } catch (error) {
    console.error('[DELETE-KW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Keyword zu Vortrag hinzufügen (aktualisiert beide DBs)
app.post('/api/add-keyword-to-lecture', async (req, res) => {
  try {
    const { lectureId, keyword } = req.body;
    
    if (!lectureId || !keyword || !keyword.term) {
      return res.status(400).json({ error: 'lectureId und keyword.term sind erforderlich' });
    }
    
    
    // 1. Aktualisiere Summary-Database
    const summaryDB = await loadSummaryDatabase();
    
    if (!summaryDB[lectureId]) {
      return res.status(404).json({ error: 'Vortrag nicht in Summary-Database gefunden' });
    }
    
    // Finde echte Überschrift aus headings basierend auf index
    // ABER: Nur wenn KEINE benutzerdefinierte Beschreibung vorhanden ist
    if (!keyword.customDescription && keyword.index && summaryDB[lectureId].headings) {
      const cleanIndex = keyword.index.startsWith('^') ? keyword.index.substring(1) : keyword.index;
      const matchingHeading = summaryDB[lectureId].headings.find(h => {
        const hIndex = h.index.startsWith('^') ? h.index.substring(1) : h.index;
        return hIndex === cleanIndex;
      });
      
      if (matchingHeading) {
        keyword.heading = matchingHeading.text;
        keyword.level = matchingHeading.level || 'h3';
      } else {
        console.warn(`[ADD-KW] Keine passende Überschrift für Index ${keyword.index} gefunden`);
      }
    } else if (keyword.customDescription) {
    }
    
    // ✅ Markiere manuell hinzugefügtes Keyword
    const manualKeyword = {
      ...keyword,
      manuallyEdited: true,
      lastEditedAt: new Date().toISOString()
    };
    
    summaryDB[lectureId].lectureKeywords = summaryDB[lectureId].lectureKeywords || [];
    summaryDB[lectureId].lectureKeywords.push(manualKeyword);
    
    await saveCompleteSummaryDatabase(summaryDB);
    
    // 2. Aktualisiere Keywords-Database
    const keywordsDB = await loadKeywordsDatabase();
    
    // Hole Datum/Jahr aus fullLectures (IMMER, auch bei bestehenden Einträgen)
    const lecture = fullLectures[lectureId];
    let date = lecture?.date || lecture?.dateString || '';
    
    // FALLBACK: Wenn date null/leer, versuche aus fileName oder location zu extrahieren
    if (!date && lecture) {
      // Beispiel: "GA073/3 - ANTHROPOSOPHIE UND NATURWISSENSCHAFT, 12. November 1917"
      // Oder: "location": "12. November 1917"
      const locationMatch = (lecture.location || lecture.fileName || '').match(/(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})/i);
      
      if (locationMatch) {
        const day = locationMatch[1].padStart(2, '0');
        const monthNames = {
          'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
          'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
          'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
        };
        const month = monthNames[locationMatch[2].toLowerCase()];
        const year = locationMatch[3];
        date = `${year}-${month}-${day}`;
      }
    }
    
    const year = date ? parseInt(date.substring(0, 4)) : null;
    const gaMatch = lectureId.match(/^GA(\d+)/);
    const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
    
    if (!keywordsDB[lectureId]) {
      // Erstelle neuen Eintrag
      keywordsDB[lectureId] = {
        lectureId: lectureId,
        date: date,
        year: year,
        gaVolume: gaVolume,
        summary: summaryDB[lectureId].summary || '',
        keywords: [manualKeyword],
        generated: new Date().toISOString(),
        generationMethod: 'manual-add'
      };
    } else {
      // Aktualisiere bestehenden Eintrag: Füge Keyword hinzu UND aktualisiere Datum/Jahr
      keywordsDB[lectureId].keywords = keywordsDB[lectureId].keywords || [];
      keywordsDB[lectureId].keywords.push(manualKeyword);
      
      // Aktualisiere Datum/Jahr falls leer (wichtig für alte Einträge ohne Datum)
      if (!keywordsDB[lectureId].date && date) {
        keywordsDB[lectureId].date = date;
      }
      if (!keywordsDB[lectureId].year && year) {
        keywordsDB[lectureId].year = year;
      }
      
      keywordsDB[lectureId].generationMethod = keywordsDB[lectureId].generationMethod || 'manual-add';
    }
    
    await saveCompleteKeywordsDatabase(keywordsDB);
    
    res.json({ 
      success: true, 
      message: `Keyword "${keyword.term}" zu ${lectureId} hinzugefügt`,
      keywordCount: summaryDB[lectureId].lectureKeywords.length
    });
    
  } catch (error) {
    console.error('[ADD-KW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Keywords eines spezifischen Absatzes abrufen
app.post('/api/get-paragraph-keywords', async (req, res) => {
  try {
    const { lectureId, paragraphIndex } = req.body;
    
    if (!lectureId || !paragraphIndex) {
      return res.status(400).json({ error: 'lectureId und paragraphIndex sind erforderlich' });
    }
    
    
    // Lade Keywords aus beiden Datenbanken
    const keywordsDB = await loadKeywordsDatabase();
    const summaryDB = await loadSummaryDatabase();
    
    const keywords = [];
    
    // Prüfe Keywords-Database
    if (keywordsDB[lectureId] && keywordsDB[lectureId].keywords) {
      const matchingKW = keywordsDB[lectureId].keywords.filter(kw => kw.index === paragraphIndex);
      keywords.push(...matchingKW);
    }
    
    // Prüfe Summary-Database (falls unterschiedlich)
    if (summaryDB[lectureId] && summaryDB[lectureId].lectureKeywords) {
      const matchingKW = summaryDB[lectureId].lectureKeywords.filter(kw => kw.index === paragraphIndex);
      // Füge nur hinzu wenn noch nicht vorhanden
      matchingKW.forEach(kw => {
        if (!keywords.some(existing => existing.term === kw.term)) {
          keywords.push(kw);
        }
      });
    }
    
    
    res.json({ 
      success: true, 
      keywords: keywords 
    });
    
  } catch (error) {
    console.error('[GET-PARA-KW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Keyword von einem spezifischen Absatz löschen
app.post('/api/remove-keyword-from-paragraph', async (req, res) => {
  try {
    const { lectureId, paragraphIndex, keywordTerm } = req.body;
    
    if (!lectureId || !paragraphIndex || !keywordTerm) {
      return res.status(400).json({ error: 'lectureId, paragraphIndex und keywordTerm sind erforderlich' });
    }
    
    
    let removedCount = 0;
    
    // 1. Aktualisiere Keywords-Database
    const keywordsDB = await loadKeywordsDatabase();
    
    if (keywordsDB[lectureId] && keywordsDB[lectureId].keywords) {
      const beforeCount = keywordsDB[lectureId].keywords.length;
      keywordsDB[lectureId].keywords = keywordsDB[lectureId].keywords.filter(kw => 
        !(kw.index === paragraphIndex && kw.term === keywordTerm)
      );
      const afterCount = keywordsDB[lectureId].keywords.length;
      removedCount += (beforeCount - afterCount);
      
      await saveCompleteKeywordsDatabase(keywordsDB);
    }
    
    // 2. Aktualisiere Summary-Database
    const summaryDB = await loadSummaryDatabase();
    
    if (summaryDB[lectureId] && summaryDB[lectureId].lectureKeywords) {
      const beforeCount = summaryDB[lectureId].lectureKeywords.length;
      summaryDB[lectureId].lectureKeywords = summaryDB[lectureId].lectureKeywords.filter(kw => 
        !(kw.index === paragraphIndex && kw.term === keywordTerm)
      );
      const afterCount = summaryDB[lectureId].lectureKeywords.length;
      removedCount += (beforeCount - afterCount);
      
      await saveSummaryDatabase(summaryDB);
    }
    
    if (removedCount === 0) {
      return res.status(404).json({ error: 'Keyword nicht gefunden' });
    }
    
    res.json({ 
      success: true, 
      message: `Keyword "${keywordTerm}" von Absatz ${paragraphIndex} entfernt`,
      removedCount: removedCount
    });
    
  } catch (error) {
    console.error('[REMOVE-PARA-KW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Update Keyword in einem Vortrag
app.post('/api/update-lecture-keyword', async (req, res) => {
  try {
    const { lectureId, oldKeyword, newKeyword } = req.body;
    
    if (!lectureId || !oldKeyword || !newKeyword) {
      return res.status(400).json({ error: 'Lecture ID, oldKeyword und newKeyword erforderlich' });
    }
    
    
    // 1. Aktualisiere Keywords-Database
    const keywordsDB = await loadKeywordsDatabase();
    
    if (keywordsDB[lectureId] && keywordsDB[lectureId].keywords) {
      const kwIndex = keywordsDB[lectureId].keywords.findIndex(kw => 
        kw.term === oldKeyword.term && kw.index === oldKeyword.index
      );
      
      if (kwIndex !== -1) {
        keywordsDB[lectureId].keywords[kwIndex] = {
          ...keywordsDB[lectureId].keywords[kwIndex],
          ...newKeyword,
          manuallyEdited: true,  // ✅ Markiere als manuell bearbeitet
          lastEditedAt: new Date().toISOString()
        };
        await saveCompleteKeywordsDatabase(keywordsDB);
      }
    }
    
    // 2. Aktualisiere Summary-Database
    const summaryDB = await loadSummaryDatabase();
    
    if (summaryDB[lectureId] && summaryDB[lectureId].lectureKeywords) {
      const kwIndex = summaryDB[lectureId].lectureKeywords.findIndex(kw => 
        kw.term === oldKeyword.term && kw.index === oldKeyword.index
      );
      
      if (kwIndex !== -1) {
        summaryDB[lectureId].lectureKeywords[kwIndex] = {
          ...summaryDB[lectureId].lectureKeywords[kwIndex],
          ...newKeyword,
          manuallyEdited: true,  // ✅ Markiere als manuell bearbeitet
          lastEditedAt: new Date().toISOString()
        };
        await saveCompleteSummaryDatabase(summaryDB);
      }
    }
    
    res.json({
      success: true,
      message: `Keyword "${newKeyword.term}" aktualisiert`
    });
    
  } catch (error) {
    console.error('[UPDATE-KW] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

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
    // Cache-Control Header: Kein Caching, damit immer die neueste Version geladen wird
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    
    // WICHTIG: Deaktiviere Kompression für große Dateien, um Content-Length-Probleme zu vermeiden
    res.setHeader('Content-Encoding', 'identity');
    
    console.log(`[SUMMARY-DB-ENDPOINT] Request empfangen`);
    const summaryDB = await loadSummaryDatabase();
    
    // Debug: Prüfe was zurückgegeben wird
    if (summaryDB['GA001'] && summaryDB['GA001'].headings && summaryDB['GA001'].headings.length > 0) {
      const firstHeading = summaryDB['GA001'].headings[0];
      console.log(`[SUMMARY-DB-ENDPOINT] GA001 erste Überschrift Index: ${firstHeading.index}`);
    }
    
    // Stringify und senden - setze Content-Length explizit
    const jsonString = JSON.stringify(summaryDB);
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Content-Length', Buffer.byteLength(jsonString, 'utf8'));
    res.send(jsonString);
  } catch (error) {
    console.error('Fehler beim Laden der Summary-DB:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SHORT SUMMARY GENERATION (2-3 Sätze aus bestehender Summary)
// ============================================================================

/**
 * Generiert Kurzzusammenfassung (1-2 Sätze) aus bestehender Summary
 */
async function generateShortSummary(fullSummary, lectureId, preferredProvider = null) {
  try {
    // Standardmäßig Claude verwenden, oder bevorzugten Provider
    let provider;
    if (preferredProvider) {
      const { createProvider } = require('./llm-providers');
      provider = createProvider(preferredProvider);
      if (!provider.isAvailable()) {
        console.warn(`[SHORT-SUMMARY] ${preferredProvider} nicht verfügbar, verwende Claude`);
        provider = createProvider('claude');
      }
    } else {
      // Default: Claude
      const { createProvider } = require('./llm-providers');
      provider = createProvider('claude');
    }
    
    const prompt = `Fasse diese Vortrags-Zusammenfassung in MAXIMAL 2 Sätzen zusammen. Sei extrem prägnant.

REGELN:
- Maximal 1-2 Sätze (nicht mehr!)
- Nur die allerwichtigste Kernaussage
- Keine Meta-Sprache ("Rudolf Steiner beschreibt...")
- Direkt und sachlich

ZUSAMMENFASSUNG:
${fullSummary}

Antworte NUR mit 1-2 Sätzen.`;

    const response = await provider.generateCompletion(prompt, {
      maxTokens: 150,
      temperature: 0.3
    });
    
    return response.trim();
  } catch (error) {
    console.error(`[SHORT-SUMMARY] Fehler bei ${lectureId}:`, error.message);
    throw error;
  }
}

/**
 * Batch-Generierung von Kurzzusammenfassungen für alle Vorträge
 */
app.post('/api/batch-generate-short-summaries', async (req, res) => {
  try {
    const { 
      lectureIds = null,
      forceRegenerate = false,
      preferredProvider = null
    } = req.body;
    
    
    // Lade Summary-Datenbank
    const summaryDB = await loadSummaryDatabase();
    
    // Bestimme zu verarbeitende Vorträge
    let lectureIdsToProcess;
    if (lectureIds && lectureIds.length > 0) {
      lectureIdsToProcess = lectureIds;
    } else {
      // Alle Vorträge aus summary-database
      lectureIdsToProcess = Object.keys(summaryDB);
    }
    
    // Filtere: Nur Vorträge MIT Summary aber OHNE shortSummary (oder force)
    const toProcess = lectureIdsToProcess.filter(id => {
      const entry = summaryDB[id];
      if (!entry || !entry.summary) return false;
      if (forceRegenerate) return true;
      return !entry.shortSummary;
    });
    
    
    if (toProcess.length === 0) {
      return res.json({
        success: true,
        message: 'Alle Vorträge haben bereits Kurzzusammenfassungen',
        processed: 0,
        failed: 0
      });
    }
    
    const results = {
      processed: 0,
      failed: 0,
      errors: []
    };
    
    // Verarbeite Vorträge in Batches von 10
    const BATCH_SIZE = 10;
    
    for (let batchStart = 0; batchStart < toProcess.length; batchStart += BATCH_SIZE) {
      const batchEnd = Math.min(batchStart + BATCH_SIZE, toProcess.length);
      const batch = toProcess.slice(batchStart, batchEnd);
      
      
      // Verarbeite alle Vorträge in diesem Batch parallel
      const batchPromises = batch.map(async (lectureId, idx) => {
        const entry = summaryDB[lectureId];
        const overallIdx = batchStart + idx + 1;
        
        try {
          
          // Generiere Kurzzusammenfassung mit bevorzugtem Provider
          const shortSummary = await generateShortSummary(entry.summary, lectureId, preferredProvider);
          
          
          return {
            success: true,
            lectureId,
            shortSummary
          };
          
        } catch (error) {
          console.error(`[SHORT-SUMMARY-BATCH] ✗ ${lectureId}: Fehler:`, error.message);
          return {
            success: false,
            lectureId,
            error: error.message
          };
        }
      });
      
      // Warte auf alle Generierungen in diesem Batch
      const batchResults = await Promise.all(batchPromises);
      
      // Aktualisiere Datenbank mit allen erfolgreichen Ergebnissen dieses Batches
      const updatedSummaryDB = await loadSummaryDatabase();
      let savedInThisBatch = 0;
      
      batchResults.forEach(result => {
        if (result.success) {
          updatedSummaryDB[result.lectureId].shortSummary = result.shortSummary;
          results.processed++;
          savedInThisBatch++;
        } else {
          results.failed++;
          results.errors.push({
            lectureId: result.lectureId,
            error: result.error
          });
        }
      });
      
      // Speichere Batch in Datenbank
      if (savedInThisBatch > 0) {
        await saveCompleteSummaryDatabase(updatedSummaryDB);
      }
    }
    
    
    res.json({
      success: true,
      processed: results.processed,
      failed: results.failed,
      total: toProcess.length,
      errors: results.errors
    });
    
  } catch (error) {
    console.error('[SHORT-SUMMARY-BATCH] Kritischer Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// SUMMARY-KEYWORDS API
// ============================================================================

// Funktion: Generiere 1-2 Keywords aus jeder H3-Überschrift mit LLM
async function generateKeywordsFromHeadings(lectureId, headings) {
  try {
    // Filtere nur H3-Überschriften
    const h3Headings = headings.filter(h => h.level === 'h3');
    
    if (h3Headings.length === 0) {
      return [];
    }
    
    const provider = getProviderForTask('summary');
    
    // Erstelle Liste der H3-Überschriften für den Prompt
    const headingsList = h3Headings.map((h, idx) => `${idx + 1}. ${h.text}`).join('\n');
    
    const prompt = `Fasse jede dieser H3-Überschriften aus einem Vortrag von Rudolf Steiner in 1-2 prägnante Schlagworte zusammen.

H3-ÜBERSCHRIFTEN:
${headingsList}

REGELN:
1. Pro Überschrift genau 1-2 Schlagworte generieren
2. Die Schlagworte sollen das Kernthema der Überschrift erfassen
3. Verwende prägnante, aussagekräftige Begriffe
4. Bevorzuge anthroposophische/geisteswissenschaftliche Fachbegriffe wo angebracht
5. Wenn eine Überschrift schon prägnant ist, kannst du sie auch leicht gekürzt übernehmen

AUSGABE als JSON-Array mit Strings (ein String pro Überschrift, 1-2 Worte):
["Schlagwort 1", "Schlagwort 2", "Schlagwort 3", ...]

Antworte NUR mit dem JSON-Array, ohne zusätzlichen Text.`;

    const responseText = await provider.generateCompletion(prompt, 300, 0.3);
    
    // Extrahiere JSON aus der Antwort
    const jsonMatch = responseText.match(/\[[\s\S]*?\]/);
    if (!jsonMatch) {
      throw new Error('Keine gültige JSON-Antwort vom LLM erhalten');
    }
    
    const keywords = JSON.parse(jsonMatch[0]);
    
    // Validiere: Soll so viele Keywords wie H3-Überschriften geben (oder ähnlich)
    if (!Array.isArray(keywords)) {
      throw new Error('Ungültiges Keywords-Array erhalten');
    }
    
    // Wenn zu viele/wenige Keywords, versuche anzupassen
    if (keywords.length !== h3Headings.length) {
      console.warn(`[SUMMARY-KEYWORDS] ${lectureId}: ${keywords.length} Keywords für ${h3Headings.length} H3-Überschriften (erwartet gleiche Anzahl)`);
    }
    
    return keywords;
    
  } catch (error) {
    console.error(`[SUMMARY-KEYWORDS] Fehler bei ${lectureId}:`, error.message);
    throw error;
  }
}

// API: Generiere Keywords für alle Summaries (Batch)
app.post('/api/generate-summary-keywords-batch', async (req, res) => {
  try {
    const { startIndex = 0, batchSize = 10 } = req.body;
    
    
    // Lade Datenbanken
    const summaryDB = await loadSummaryDatabase();
    const summaryKeywordsDB = await loadSummaryKeywordsDatabase();
    
    const lectureIds = Object.keys(summaryDB);
    const totalLectures = lectureIds.length;
    
    if (startIndex >= totalLectures) {
      return res.json({
        success: true,
        message: 'Alle Summaries bereits verarbeitet',
        processed: 0,
        total: totalLectures,
        completed: true
      });
    }
    
    // Verarbeite Batch
    const batchLectureIds = lectureIds.slice(startIndex, startIndex + batchSize);
    let processedCount = 0;
    let errorCount = 0;
    
    for (const lectureId of batchLectureIds) {
      // Skip wenn bereits Keywords vorhanden
      if (summaryKeywordsDB[lectureId] && summaryKeywordsDB[lectureId].keywords) {
        processedCount++;
        continue;
      }
      
      const lectureData = summaryDB[lectureId];
      if (!lectureData || !lectureData.summary) {
        errorCount++;
        continue;
      }
      
      try {
        const keywords = await generateKeywordsFromSummary(lectureId, lectureData.summary);
        
        // Speichere in Datenbank
        summaryKeywordsDB[lectureId] = {
          lectureId: lectureId,
          keywords: keywords,
          generatedAt: new Date().toISOString()
        };
        
        processedCount++;
        
      } catch (error) {
        console.error(`[SUMMARY-KEYWORDS-BATCH] ${lectureId}: Fehler -`, error.message);
        errorCount++;
      }
    }
    
    // Speichere aktualisierte Datenbank
    await saveSummaryKeywordsDatabase(summaryKeywordsDB);
    
    const nextIndex = startIndex + batchSize;
    const isCompleted = nextIndex >= totalLectures;
    
    
    res.json({
      success: true,
      processed: processedCount,
      errors: errorCount,
      total: totalLectures,
      nextIndex: nextIndex,
      completed: isCompleted,
      progress: Math.round((nextIndex / totalLectures) * 100)
    });
    
  } catch (error) {
    console.error('[SUMMARY-KEYWORDS-BATCH] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Summary-Keywords-Datenbank abrufen
app.get('/summary-keywords-database.json', async (req, res) => {
  try {
    const summaryKeywordsDB = await loadSummaryKeywordsDatabase();
    res.json(summaryKeywordsDB);
  } catch (error) {
    console.error('Fehler beim Laden der Summary-Keywords-DB:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Generiere Keywords für spezifische Lecture-IDs (für einzelne GA-Bände)
app.post('/api/generate-summary-keywords-for-lectures', async (req, res) => {
  try {
    const { lectureIds } = req.body;
    
    if (!lectureIds || !Array.isArray(lectureIds)) {
      return res.status(400).json({ error: 'lectureIds Array ist erforderlich' });
    }
    
    
    // Lade Datenbanken
    const summaryDB = await loadSummaryDatabase();
    const summaryKeywordsDB = await loadSummaryKeywordsDatabase();
    
    let processedCount = 0;
    let errorCount = 0;
    
    for (const lectureId of lectureIds) {
      // Skip wenn bereits Keywords vorhanden
      if (summaryKeywordsDB[lectureId] && summaryKeywordsDB[lectureId].keywords) {
        processedCount++;
        continue;
      }
      
      const lectureData = summaryDB[lectureId];
      if (!lectureData || !lectureData.summary) {
        errorCount++;
        continue;
      }
      
      try {
        const keywords = await generateKeywordsFromSummary(lectureId, lectureData.summary);
        
        // Speichere in Datenbank
        summaryKeywordsDB[lectureId] = {
          lectureId: lectureId,
          keywords: keywords,
          generatedAt: new Date().toISOString()
        };
        
        processedCount++;
        
      } catch (error) {
        console.error(`[SUMMARY-KEYWORDS-LECTURES] ${lectureId}: Fehler -`, error.message);
        errorCount++;
      }
    }
    
    // Speichere aktualisierte Datenbank
    await saveSummaryKeywordsDatabase(summaryKeywordsDB);
    
    
    res.json({
      success: true,
      processed: processedCount,
      errors: errorCount,
      total: lectureIds.length
    });
    
  } catch (error) {
    console.error('[SUMMARY-KEYWORDS-LECTURES] Fehler:', error);
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
    return {};
  }
}

// ROBUSTE FUNKTION: Speichere gesamte Keywords-Datenbank (mit Locking & Backup)
async function saveCompleteKeywordsDatabase(keywordsDB) {
  return new Promise((resolve, reject) => {
    keywordsDbWriteQueue = keywordsDbWriteQueue.then(async () => {
      try {
        
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
        
        
        resolve(true);
        
      } catch (error) {
        console.error('[KEYWORDS-LOCK] ✗ Fehler beim Speichern:', error);
        reject(error);
      }
    });
  });
}

// ROBUSTE FUNKTION: Speichere Keywords in Datenbank (mit Locking & Merge)
async function saveKeywordsToDatabase(lectureId, keywordsData) {
  return new Promise((resolve, reject) => {
    keywordsDbWriteQueue = keywordsDbWriteQueue.then(async () => {
      try {
        
        // WICHTIG: Erstelle Backup BEVOR wir speichern
        await createKeywordsBackup();
        
        // Lade immer die aktuellste Version der Datenbank
        const keywordsDB = await loadKeywordsDatabase();
        
        // ============================================================================
        // MERGE-STRATEGIE: Manuelle Bearbeitungen erhalten
        // ============================================================================
        
        const existingEntry = keywordsDB[lectureId];
        let mergedKeywords = keywordsData.keywords || [];
        
        if (existingEntry && existingEntry.keywords && Array.isArray(existingEntry.keywords)) {
          
          // 1. Behalte alle manuell bearbeiteten Keywords
          const manualKeywords = existingEntry.keywords.filter(kw => kw.manuallyEdited === true);
          
          // 2. Erstelle Set der bestehenden Keyword-Signaturen (term + index)
          const existingSignatures = new Set(
            existingEntry.keywords.map(kw => `${kw.term}|${kw.index}`)
          );
          
          // 3. Füge nur neue Keywords hinzu (keine Duplikate)
          const newKeywords = (keywordsData.keywords || []).filter(kw => {
            const signature = `${kw.term}|${kw.index}`;
            return !existingSignatures.has(signature);
          });
          
          
          // 4. Merge: Manuelle zuerst, dann neue
          mergedKeywords = [...manualKeywords, ...newKeywords];
          
        } else {
        }
        
        // Speichere gemergten Eintrag
        keywordsDB[lectureId] = {
          ...keywordsData,
          keywords: mergedKeywords,
          timestamp: new Date().toISOString(),
          lastMerge: existingEntry ? new Date().toISOString() : null
        };
        
        // Validiere dass Datenbank nicht leer ist
        if (Object.keys(keywordsDB).length === 0) {
          console.error('[KEYWORDS-LOCK] ✗ WARNUNG: Datenbank wäre leer - ABGEBROCHEN!');
          reject(new Error('Datenbank ist leer - Speichern abgebrochen'));
          return;
        }
        
        // Speichere Datenbank
        await fs.writeFile(KEYWORDS_DB_FILE, JSON.stringify(keywordsDB, null, 2), 'utf8');
        
        
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
    return extractKeywordsFromHeadings(headings);
  }
  
  // Formatiere alle Überschriften für den Prompt
  const headingsText = headings
    .map((h, idx) => `${idx + 1}. ${h.text} [${h.level}, Index: ${h.index}]`)
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
    
    return seedKeywords;
  } catch (error) {
    console.error('[SEED] Fehler beim Laden der Seed-Keywords:', error.message);
    return [];
  }
}

// Extrahiere Hauptbegriffe aus Summary
async function extractKeyTermsFromSummary(summary, existingVocabulary) {
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  let provider;
  try {
    provider = getProviderForTask('keywords');
  } catch (error) {
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
    // Verwende Provider-Abstraction
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 1024,
      temperature: 0.5
    });
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    const terms = JSON.parse(responseText);
    return terms;
    
  } catch (error) {
    console.error(`[SUMMARY-TERMS] Fehler bei ${provider.name} API:`, error.message);
    return [];
  }
}

// Generiere Keywords iterativ mit Summary-Kontext und bestehendem Vokabular
async function generateKeywordsIterativeWithSummary(lectureId, summary, headings, vocabulary, frequencyMap = {}) {
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  let provider;
  try {
    provider = getProviderForTask('keywords');
  } catch (error) {
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
    .map((h, idx) => `${idx + 1}. ${h.text} [${h.level}, Index: ${h.index}]`)
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
Für JEDE Überschrift: WÄHLE DAS PASSENDSTE EXISTIERENDE Keyword aus dem Vokabular.
NUR wenn KEIN passendes existiert (Confidence < 0.7): Erstelle ein NEUES Keyword.

HIERARCHIE (ZWINGEND BEACHTEN):
1. 🏆 HÖCHSTE PRIORITÄT: Summary-erwähnte Begriffe aus dem Vokabular
2. 🥈 HOHE PRIORITÄT: Thematisch passende Vokabular-Begriffe
3. 🥉 MITTLERE PRIORITÄT: Häufige Vokabular-Begriffe  
4. ⚠️ LETZTE OPTION: Neues Keyword (NUR bei Confidence < 0.7)

STRIKTE REGELN:
- ✅ IMMER zuerst im Vokabular suchen (auch semantisch ähnliche)
- ✅ Bei Synonymen: Wähle das HÄUFIGSTE aus dem Vokabular
- ✅ Bei Varianten (z.B. "Karma", "Karmagesetz"): Wähle den ALLGEMEINEREN Begriff
- ✅ Korrekte deutsche Großschreibung (Substantive groß)
- ❌ NICHT neu erfinden, was bereits existiert!

SEMANTIC MATCHING (Beispiele):
- Überschrift: "Der astralische Leib und seine Funktionen"
  → Vokabular hat: "Astralleib" (150x), "astralischer Leib" (12x)
  → WÄHLE: "Astralleib" (häufiger, matchType: "existing-exact", confidence: 0.95)
  
- Überschrift: "Wiederverkörperung und Schicksalsausgleich"  
  → Vokabular hat: "Reinkarnation" (200x), "Karma" (180x)
  → WÄHLE: "Reinkarnation" (semantisch identisch, matchType: "existing-similar", confidence: 0.9)
  
- Überschrift: "Die vier Äther-Arten"
  → Vokabular hat: "Ätherleib" (100x), "Äther" (45x), "Lebenskräfte" (30x)
  → WÄHLE: "Ätherleib" (thematisch passend, matchType: "existing-similar", confidence: 0.8)
  
- Überschrift: "Spezifisches neues Konzept ohne Vokabular-Match"
  → Vokabular hat nichts passendes
  → ERSTELLE NEU: matchType: "new", confidence: 0.6

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
    
    // Verwende Provider-Abstraction
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 4096,
      temperature: 0.5
    });
    
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
    
    
    return keywords;

  } catch (error) {
    console.error(`[KEYWORDS-ITER] ${lectureId}: Fehler bei ${provider.name} API:`, error.message);
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
// NEUE KEYWORD-GENERIERUNG MIT THEMES-KEYWORDS-TEMPLATE
// ============================================================================

/**
 * Lädt die Themes-Keywords-Template Datei mit vordefinierten Themen und Keywords
 */
async function loadThemesKeywordsTemplate() {
  try {
    const data = await fs.readFile(THEMES_KEYWORDS_TEMPLATE_FILE, 'utf8');
    const template = JSON.parse(data);
    return template;
  } catch (error) {
    console.error('[TEMPLATE] Fehler beim Laden:', error.message);
    throw new Error('Themes-Keywords-Template nicht gefunden. Bitte themes-keywords-template.json erstellen.');
  }
}

/**
 * Extrahiert alle Keywords aus dem Template als flache Liste
 */
function extractVocabularyFromTemplate(template) {
  const vocabulary = new Set();
  const themeMapping = {}; // Keyword -> Theme
  const synonymMap = {}; // Kanonischer Begriff -> Synonyme
  
  for (const [themeName, themeData] of Object.entries(template.themes)) {
    // Keywords sammeln
    themeData.keywords.forEach(kw => {
      vocabulary.add(kw);
      themeMapping[kw.toLowerCase().trim()] = themeName;
    });
    
    // Synonym-Gruppen verarbeiten
    if (themeData.synonymGroups && Array.isArray(themeData.synonymGroups)) {
      themeData.synonymGroups.forEach(group => {
        // Erstes Element ist der kanonische Begriff
        const canonical = group[0];
        synonymMap[canonical.toLowerCase()] = group.slice(1).map(s => s.toLowerCase());
      });
    }
  }
  
  
  return {
    vocabulary: Array.from(vocabulary),
    themeMapping,
    synonymMap
  };
}

/**
 * Extrahiert Hauptbegriffe aus H3 und H4 Überschriften
 * Statt aus der Summary
 */
function extractKeyTermsFromHeadings(headings) {
  // Filtere H3 und H4
  const relevantHeadings = headings.filter(h => h.level === 'h3' || h.level === 'h4');
  
  // Extrahiere wichtige Begriffe (Substantive, Namen)
  const keyTerms = new Set();
  
  relevantHeadings.forEach(heading => {
    const text = heading.text || '';
    
    // Teile in Wörter
    const words = text.split(/[\s\-–—,;:()]+/);
    
    words.forEach(word => {
      // Filtere kurze Wörter und Artikel
      if (word.length < 4) return;
      if (['über', 'durch', 'nach', 'beim', 'sein', 'sind', 'wird', 'werden', 'wurde', 'wurden', 'haben', 'hatte'].includes(word.toLowerCase())) return;
      
      // Großgeschriebene Wörter sind oft Substantive/Namen
      if (word[0] === word[0].toUpperCase()) {
        keyTerms.add(word);
      }
    });
  });
  
  return Array.from(keyTerms);
}

/**
 * NEUE HAUPT-FUNKTION: Generiere Keywords aus H3/H4 mit Template-Vokabular
 * Verwendet die vordefinierte Themen-Keywords-Struktur
 */
async function generateKeywordsFromHeadingsWithTemplate(lectureId, headings, template, existingVocabulary = [], frequencyMap = {}, preferredProvider = null) {
  // Hole Provider - DIREKT wenn preferredProvider gesetzt
  let provider;
  
  if (preferredProvider) {
    // Nutzer hat explizit einen Provider gewählt - verwende NUR diesen
    const { createProvider } = require('./llm-providers');
    try {
      provider = createProvider(preferredProvider);
      if (!provider.isAvailable()) {
        throw new Error(`${preferredProvider} nicht verfügbar (kein API-Key)`);
      }
    } catch (error) {
      console.error(`[KEYWORDS-NEW] ${lectureId}: Gewählter Provider ${preferredProvider} nicht verfügbar:`, error.message);
      return extractKeywordsFromHeadings(headings);
    }
  } else {
    // Kein expliziter Provider - verwende automatischen Fallback
    const { getAllAvailableProviders } = require('./llm-providers');
    const availableProviders = getAllAvailableProviders('keywords');
    
    if (availableProviders.length === 0) {
      return extractKeywordsFromHeadings(headings);
    }
    
    provider = availableProviders[0];
  }
  
  // Extrahiere Template-Vokabular
  const { vocabulary: templateVocab, themeMapping, synonymMap } = extractVocabularyFromTemplate(template);
  
  // Kombiniere Template-Vokabular mit existierenden Keywords
  const fullVocabulary = [...new Set([...templateVocab, ...existingVocabulary])];
  
  // Extrahiere Hauptbegriffe aus Überschriften
  const headingKeyTerms = extractKeyTermsFromHeadings(headings);
  
  // Finde thematisch passende Keywords aus Vokabular
  const relatedKeywords = fullVocabulary.filter(kw => 
    headingKeyTerms.some(term => 
      kw.toLowerCase().includes(term.toLowerCase()) || 
      term.toLowerCase().includes(kw.toLowerCase())
    )
  ).slice(0, 50);
  
  // Häufigste Keywords (Top 100)
  const sortedByFreq = Object.entries(frequencyMap)
    .sort((a, b) => b[1] - a[1])
    .map(([term]) => term)
    .slice(0, 100);
  
  // Formatiere Überschriften (nur H3 und H4)
  const relevantHeadings = headings.filter(h => h.level === 'h3' || h.level === 'h4');
  const headingsText = relevantHeadings
    .map((h, idx) => `${idx + 1}. ${h.text} [${h.level}, Index: ${h.index}]`)
    .join('\n');
  
  // Formatiere Synonym-Gruppen für Prompt
  const synonymInfo = Object.entries(synonymMap)
    .map(([canonical, syns]) => `"${canonical}" (bevorzugt) = ${syns.join(', ')}`)
    .join('\n');
  
  const confidenceThreshold = template.metadata.confidenceThreshold || 0.6;
  
  // Erstelle vollständige Vokabular-Liste (alle Template-Keywords + Top-Häufige)
  const templateKeywordsOnly = Array.from(templateVocab);
  const priorityVocab = [...new Set([...relatedKeywords, ...sortedByFreq.slice(0, 100)])];
  
  const prompt = `STRIKTE VERSCHLAGWORTUNG - Verwende NUR Begriffe aus dem VOKABULAR!

⚠️ ZWINGEND: Wähle für JEDE Überschrift ein Keyword AUS DEM VOKABULAR (unten).
⚠️ NUR wenn KEIN passender Begriff existiert (confidence < ${confidenceThreshold}): Erstelle neues Keyword.

TEMPLATE-VOKABULAR (${templateKeywordsOnly.length} vordefinierte Begriffe):
${templateKeywordsOnly.slice(0, 200).join(', ')}

ZUSÄTZLICH VERFÜGBAR (häufig verwendet):
${priorityVocab.slice(0, 100).join(', ')}

SYNONYME (verwende IMMER den kanonischen Begriff):
${synonymInfo || 'keine'}

ÜBERSCHRIFTEN (H3/H4):
${headingsText}

VORGEHEN FÜR JEDE ÜBERSCHRIFT:
1. Kern-Konzept identifizieren (z.B. "Geisteswissenschaft", "Reinkarnation", "Kant")
2. Im VOKABULAR oben suchen (exakt, Wortstamm, oder Synonym)
3. Wenn gefunden → verwenden (confidence 0.8-1.0)
4. Wenn NICHT gefunden → NUR DANN neues Keyword (confidence < ${confidenceThreshold})
5. Füllwörter entfernen: "Wesen", "Problem", "Lehre", "Stellung", "Bedeutung"
6. Adjektive entfernen: "griechischen", "suggestive", "materialistische"
7. ZIEL: 1 Wort (selten 2, maximal 3)

KRITISCHE BEISPIELE (GENAU SO):

KRITISCHE REGEL - NUR EIN WORT ODER KOMPAKTE BEGRIFFE:

❌ FALSCH: "Wesen Geisteswissenschaft" (Füllwort + falsches Format)
✅ RICHTIG: "Geisteswissenschaft" (nur 1 Wort)

❌ FALSCH: "suggestive Macht Naturwissenschaft" (viel zu lang)
✅ RICHTIG: "Naturwissenschaft" (nur 1 Wort)

❌ FALSCH: "Methoden geisteswissenschaftlichen Forschung" (zu lang + falsche Grammatik)
✅ RICHTIG: "Geisteswissenschaftliche Forschung" (kompakt, korrekt)

❌ FALSCH: "erwachende Bedürfnis nach Geisteswissenschaft" (viel zu lang)
✅ RICHTIG: "Erkenntnisbedürfnisse" (1 Wort)

❌ FALSCH: "Materialistische geisteswissenschaftliche Betrachtung Leben und" (viel zu lang)
✅ RICHTIG: "Materialistische Betrachtung" (2 Worte, kompakt)

❌ FALSCH: "geisteswissenschaftliche Analogie biologischen Grundsatz" (zu lang + falsch)
✅ RICHTIG: "biologischer Grundsatz" (2 Worte, korrekt)

❌ FALSCH: "Lebensprozess Wechselwirkung Leben und Tod" (zu lang)
✅ RICHTIG: "Leben und Tod" (kompakt, korrekt)

❌ FALSCH: "Problem Erinnerung frühere Leben" (zu lang)
✅ RICHTIG: "Erinnerung an frühere Leben" (kompakt, grammatisch korrekt)

❌ FALSCH: "ewige Natur menschlichen Wesenskerns" (zu lang + falsch)
✅ RICHTIG: "Wesenskern" (1 Wort, oder "Ewigkeit")

❌ FALSCH: "Unterscheidung zwischen Seele und Geist" (zu lang)
✅ RICHTIG: "Seele und Geist" (kompakt)

❌ FALSCH: "viergliederige Wesenheit Menschen" (zu lang + falsch)
✅ RICHTIG: "Viergliederigkeit Mensch" (kompakt, korrekt)

❌ FALSCH: "Geist Tierreich" (falsche Grammatik, unklar)
✅ RICHTIG: "Tierreich" (1 Wort)

❌ FALSCH: "seelische Erleben Tier und Mensch" (falsche Grammatik)
✅ RICHTIG: "Tier und Mensch" (kompakt)

❌ FALSCH: "Emanzipation menschlichen Seele" (falsche Grammatik)
✅ RICHTIG: "Emanzipation der Seele" (grammatisch korrekt)

❌ FALSCH: "Neue Erkenntnisbedürfnisse Gegenwart" (zu lang)
✅ RICHTIG: "Erkenntnisbedürfnisse" (1 Wort)

❌ FALSCH: "Geisteswissenschaft und Monismus" (wird getrennt)
✅ RICHTIG: "Monismus" (1 Wort, "Geisteswissenschaft" separat wenn nötig)

❌ FALSCH: "Widerstand und Widerlegungen" (redundant)
✅ RICHTIG: "Widerlegungen" (1 Wort)

❌ FALSCH: "Theosophische Methodik und Zielsetzung" (zu lang)
✅ RICHTIG: "Theosophische Methodik" (kompakt)

❌ FALSCH: "Dreigliederung Seele" (ohne Artikel klingt falsch)
✅ RICHTIG: "Dreigliederung Seele" (akzeptabel, kompakt)

❌ FALSCH: "Ursprung individuellen Seele" (grammatisch falsch)
✅ RICHTIG: "Ursprung der Seele" (grammatisch korrekt)

❌ FALSCH: "Aufgabe Theosophischen Gesellschaft" (falsch)
✅ RICHTIG: "Theosophische Gesellschaft" (korrekt)

WEITERE BEISPIELE AUS GA060:

❌ FALSCH: "Wesen Geisteswissenschaft"
✅ RICHTIG: "Geisteswissenschaft"

❌ FALSCH: "suggestive Macht Naturwissenschaft"
✅ RICHTIG: "Naturwissenschaft"

❌ FALSCH: "Methoden geisteswissenschaftlichen Forschung"
✅ RICHTIG: "Geisteswissenschaftliche Forschung"

❌ FALSCH: "Materialistische geisteswissenschaftliche Betrachtung Leben und"
✅ RICHTIG: "Materialistische Betrachtung"

❌ FALSCH: "viergliederige Wesenheit Menschen"
✅ RICHTIG: "Viergliederigkeit Mensch"

❌ FALSCH: "Emanzipation menschlichen Seele"
✅ RICHTIG: "Emanzipation der Seele"

STRIKTE REGELN FÜR KEYWORD-BILDUNG:
1. ✅ BEVORZUGE 1 WORT (z.B. "Karma", "Christentum", "Parmenides")
2. ✅ MAXIMAL 2-3 Worte (z.B. "Ich-Entwicklung", "deutscher Idealismus")
3. ❌ ENTFERNE Füllwörter: "Problem", "Lehre", "Stellung", "Wendung zu"
4. ❌ ENTFERNE überflüssige Adjektive: "griechischen", "individuellen"
5. ❌ ENTFERNE Artikel: "die", "der", "das", "dem", "den"
6. ✅ Bei Personen: Nur Name (z.B. "Kant", "Platon", "Aristoteles")
7. ✅ Bei Personen mit Kontext: "Person: Konzept" (z.B. "Platon: Ideenwelt")
8. ✅ Verwende Substantive (keine ganzen Phrasen)

KEYWORD-LÄNGE: Bevorzuge 1 Wort. Maximal 3 Worte NUR wenn unbedingt nötig!

ZWINGEND BEFOLGEN:
1. ✅ Suche ZUERST im Vokabular (oben) - verwende exakte/ähnliche Begriffe
2. ✅ ZIEL: 1 Wort (z.B. "Karma", "Parmenides", "Christentum")
3. ✅ Maximal 2-3 Worte bei Komposita (z.B. "Leben und Tod", "deutscher Idealismus")
4. ❌ Entferne Füllwörter: "Wesen", "Problem", "Lehre", "Stellung", "Aufgabe"
5. ❌ Entferne Adjektive: "griechischen", "suggestive", "materialistische"
6. ❌ NUR neue Keywords wenn im Vokabular NICHTS passt (confidence < ${confidenceThreshold})
7. ✅ Korrekte Grammatik (z.B. "biologischer Grundsatz" nicht "biologischen Grundsatz")

BEISPIELE (KORREKTE VERSCHLAGWORTUNG):

Überschrift: "Das Problem der Unsterblichkeitsfrage"
→ Keyword: "Unsterblichkeitsfrage" (NICHT: "Problem Unsterblichkeitsfrage")

Überschrift: "Die Ewige und die Vergängliche Natur des Menschen"
→ Keyword: "Vergänglichkeit" (NICHT: "Ewige Vergängliche Natur")

Überschrift: "Die Entwicklung der Menschenseele"
→ Keyword: "Seelenentwicklung" (NICHT: "Menschenseele Entwicklung")

Überschrift: "Die Lehre von der Reinkarnation"
→ Keyword: "Reinkarnation" (NICHT: "Lehre Reinkarnation")

Überschrift: "Die Stellung der Theosophie zwischen Wissenschaft und Religion"
→ Keyword: "Theosophie" (NICHT: "Stellung Theosophie zwischen...")

Überschrift: "Historische Parallelen zur zukünftigen Entwicklung"
→ Keyword: "Zukünftige Entwicklung" (NICHT: "Historische Parallelen...")

Überschrift: "Die griechischen Naturphilosophen"
→ Keyword: "Naturphilosophen" (NICHT: "griechischen Naturphilosophen")

Überschrift: "Parmenides und seine Kritik der Sinnenwelt"
→ Keyword: "Parmenides" (NICHT: "Parmenides Kritik Sinnenwelt")

Überschrift: "Die Sophistik und die Wendung zum Menschen"
→ Keyword: "Sophistik" (NICHT: "Sophistik Wendung Menschen")

Überschrift: "Platon und die Welt der Ideen"
→ Keywords: "Platon", "Ideenwelt" (NICHT: "Platon Ideenwelt")

Überschrift: "Die hellenistischen Schulen der Philosophie"
→ Keyword: "Hellenismus" (NICHT: "hellenistischen Schulen")

Überschrift: "Das Christentum und der Glaube"
→ Keyword: "Christentum" (NICHT: "Christentum Glaube")

Überschrift: "Kant und die Kritik der reinen Vernunft"
→ Keyword: "Kant" (NICHT: "Kant Kritik Vernunft")

Überschrift: "Der deutsche Idealismus von Fichte bis Hegel"
→ Keyword: "deutscher Idealismus" (NICHT: "deutsche Idealismus")

WICHTIG:
- 95% der Keywords MÜSSEN aus dem VOKABULAR stammen!
- Nur 5% dürfen neu sein (wenn wirklich nichts passt)
- matchType: "exact" (im Vokabular), "wordstem" (ähnlich), "synonym", "new" (selten!)
- confidence: 0.9-1.0 wenn im Vokabular, <${confidenceThreshold} für neu

JSON (NUR Array, kein Markdown, kein Text):
[{"term":"Schlagwort","index":"^abc","heading":"...","level":"h3","matchType":"exact","confidence":0.95}]`;

  try {
    
    // Verwende DIREKT den ausgewählten Provider (kein Fallback)
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 4096,
      temperature: 0.2  // SEHR niedrig für strikte Befolgung
    });
    
    const usedProvider = provider.name;
    
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    let keywords = JSON.parse(responseText);
    
    // VALIDIERUNG: Filtere zu lange Keywords und bereinige
    const validatedKeywords = [];
    const rejectedKeywords = [];
    const cleanedKeywords = [];
    
    keywords.forEach(kw => {
      let term = kw.term.trim();
      const wordCount = term.split(/\s+/).length;
      
      // AUTOMATISCHE BEREINIGUNG - VIEL AGGRESSIVER
      const originalTerm = term;
      
      // 1. Entferne häufige Füllwörter (am Anfang ODER in der Mitte)
      const fillWords = [
        'Problem', 'Lehre', 'Stellung', 'Wendung', 'Bedeutung', 'Wesen', 'Begriff', 'Frage',
        'Aufgabe', 'Prozess', 'Natur', 'Macht', 'Bedürfnis', 'Wesenheit'
      ];
      fillWords.forEach(fw => {
        // Am Anfang
        term = term.replace(new RegExp(`^${fw}\\s+`, 'i'), '');
        // In der Mitte (ohne Kontext)
        if (term.split(/\s+/).length > 3) {
          term = term.replace(new RegExp(`\\s+${fw}\\s+`, 'i'), ' ');
        }
      });
      
      // 2. Entferne Adjektive am Anfang
      const adjectives = [
        'griechischen', 'individuellen', 'historische', 'hellenistischen', 'neuzeitlichen',
        'suggestive', 'erwachende', 'ewige', 'materialistische', 'geisteswissenschaftliche',
        'viergliederige', 'menschlichen', 'seelische'
      ];
      adjectives.forEach(adj => {
        term = term.replace(new RegExp(`^${adj}\\s+`, 'i'), '');
      });
      
      // 3. Repariere häufige grammatische Fehler
      term = term.replace(/geisteswissenschaftlichen Forschung/i, 'Geisteswissenschaftliche Forschung');
      term = term.replace(/biologischen Grundsatz/i, 'biologischer Grundsatz');
      term = term.replace(/menschlichen Wesenskern/i, 'Wesenskern');
      term = term.replace(/menschlichen Seele/i, 'der Seele');
      term = term.replace(/Viergliederige Wesenheit Menschen/i, 'Viergliederigkeit Mensch');
      
      // 4. Entferne unvollständige Phrasen (endet mit "und", "oder", "zwischen")
      term = term.replace(/\s+(und|oder|zwischen|nach|zu)\s*$/i, '');
      
      // 5. Kürze wenn immer noch zu lang - suche im Vokabular
      if (term.split(/\s+/).length > 3) {
        const words = term.split(/\s+/);
        
        // Strategie A: Letztes Wort (oft das Hauptsubstantiv)
        const lastWord = words[words.length - 1];
        if (fullVocabulary.some(v => v.toLowerCase() === lastWord.toLowerCase())) {
          term = lastWord;
        }
        // Strategie B: Letzte 2 Worte
        else if (words.length >= 2) {
          const lastTwo = words.slice(-2).join(' ');
          if (fullVocabulary.some(v => v.toLowerCase() === lastTwo.toLowerCase())) {
            term = lastTwo;
          }
          // Strategie C: Erste 2 Worte
          else {
            const firstTwo = words.slice(0, 2).join(' ');
            if (fullVocabulary.some(v => v.toLowerCase() === firstTwo.toLowerCase())) {
              term = firstTwo;
            }
          }
        }
      }
      
      // Log wenn bereinigt
      if (term !== originalTerm) {
        cleanedKeywords.push({ old: originalTerm, new: term });
      }
      
      // Prüfe Länge nach Bereinigung - NOCH STRENGER
      const finalWordCount = term.split(/\s+/).length;
      
      if (finalWordCount > 3) {
        // Immer noch zu lang - aggressiv kürzen
        const words = term.split(/\s+/);
        let found = false;
        
        // Strategie 1: Letztes Wort im Vokabular?
        const lastWord = words[words.length - 1];
        if (fullVocabulary.some(v => v.toLowerCase() === lastWord.toLowerCase())) {
          term = lastWord;
          found = true;
        }
        // Strategie 2: Letzte 2 Worte im Vokabular?
        else if (words.length >= 2) {
          const lastTwo = words.slice(-2).join(' ');
          if (fullVocabulary.some(v => v.toLowerCase() === lastTwo.toLowerCase())) {
            term = lastTwo;
            found = true;
          }
        }
        // Strategie 3: Erste 2 Worte im Vokabular?
        if (!found && words.length >= 2) {
          const firstTwo = words.slice(0, 2).join(' ');
          if (fullVocabulary.some(v => v.toLowerCase() === firstTwo.toLowerCase())) {
            term = firstTwo;
            found = true;
          }
        }
        // Strategie 4: Hauptsubstantiv finden (Wörter mit Großbuchstaben am Anfang)
        if (!found) {
          const capitalWords = words.filter(w => /^[A-ZÄÖÜ]/.test(w));
          if (capitalWords.length === 1) {
            term = capitalWords[0];
            found = true;
          } else if (capitalWords.length >= 2) {
            const twoCapitals = capitalWords.slice(0, 2).join(' ');
            term = twoCapitals;
            found = true;
          }
        }
        // Strategie 5: Verwerfen wenn nichts funktioniert
        if (!found) {
          rejectedKeywords.push(originalTerm);
          return; // Nicht hinzufügen
        }
      }
      
      // STRIKTE VOKABULAR-VALIDIERUNG
      const existsInTemplate = templateVocab.some(v => v.toLowerCase() === term.toLowerCase());
      const existsInFull = fullVocabulary.some(v => v.toLowerCase() === term.toLowerCase());
      
      // Prüfe ob Keyword aus Template stammt oder legitim neu ist
      if (existsInTemplate) {
        // Perfekt - aus Template
        validatedKeywords.push({
          ...kw,
          term: term,
          matchType: kw.matchType === 'new' ? 'exact' : kw.matchType, // Korrigiere matchType
          confidence: Math.max(kw.confidence || 0.9, 0.9) // Mindestens 0.9
        });
      } else if (existsInFull) {
        // Aus erweiterten Vokabular (existingVocabulary)
        validatedKeywords.push({
          ...kw,
          term: term
        });
      } else if (kw.matchType === 'new' && (kw.confidence || 0) < confidenceThreshold) {
        // Legitim neues Keyword (niedrige Confidence)
        validatedKeywords.push({
          ...kw,
          term: term
        });
      } else {
        // Nicht im Vokabular und nicht legitim neu → verwerfen
        rejectedKeywords.push(originalTerm);
      }
    });
    
    if (rejectedKeywords.length > 0) {
    }
    if (cleanedKeywords.length > 0) {
    }
    
    // Füge Themen-Zuordnung hinzu basierend auf themeMapping
    const finalKeywords = validatedKeywords.map(kw => {
      const theme = themeMapping[kw.term.toLowerCase().trim()];
      return {
        ...kw,
        theme: theme || null
      };
    });
    
    // Statistiken
    const newKws = finalKeywords.filter(k => k.matchType === 'new');
    const exactKws = finalKeywords.filter(k => k.matchType === 'exact');
    const synKws = finalKeywords.filter(k => k.matchType === 'synonym');
    
    
    return finalKeywords;

  } catch (error) {
    console.error(`[KEYWORDS-NEW] ${lectureId}: Alle Provider fehlgeschlagen:`, error.message);
    return extractKeywordsFromHeadings(headings);
  }
}

/**
 * NEU: Ordnet ein neues Keyword einem passenden Thema zu (oder null)
 * Verwendet LLM um das beste Thema aus den 81 vordefinierten zu finden
 */
async function assignThemeToNewKeyword(keyword, themesList, provider) {
  try {
    const themeNames = Object.keys(themesList);
    
    // Erstelle kompakte Themen-Beschreibungen für Prompt
    const themesDescription = themeNames.map((name, idx) => {
      const desc = themesList[name].description || '';
      const keywords = themesList[name].keywords || [];
      const sampleKw = keywords.slice(0, 5).join(', ');
      return `${idx + 1}. ${name}\n   ${desc}\n   Beispiel-KW: ${sampleKw}`;
    }).join('\n\n');
    
    const prompt = `Ordne das folgende Schlagwort aus Rudolf Steiners Werk EINEM der ${themeNames.length} Themen zu.

SCHLAGWORT: "${keyword}"

VERFÜGBARE THEMEN:
${themesDescription}

REGELN:
1. Wähle das thematisch am besten passende Thema
2. Wenn KEIN Thema wirklich gut passt (Confidence < 0.6): Antworte mit "NONE"
3. Antworte NUR mit dem exakten Themennamen (oder "NONE")

BEISPIELE:
- "Ätherkräfte" → "Wesensglieder"
- "Soziale Gerechtigkeit" → "Soziale Dreigliederung"
- "Quantenphysik" → "NONE" (passt zu keinem Thema gut)

ANTWORT (nur Themenname oder "NONE"):`;

    const responseText = await provider.generateCompletion(prompt, {
      maxTokens: 100,
      temperature: 0.3
    });
    
    const themeName = responseText.trim().replace(/["']/g, '');
    
    // Validiere dass Thema existiert
    if (themeName === 'NONE' || !themesList[themeName]) {
      return null;
    }
    
    return themeName;
    
  } catch (error) {
    console.error(`[THEME-ASSIGN] Fehler bei Themen-Zuordnung für "${keyword}":`, error.message);
    return null;
  }
}

/**
 * NEU: Flexible Keyword-Generierung mit Budget-System
 * Generiert so viele Keywords wie nötig (nicht fest 10-12)
 * Budget-System begrenzt neue Keywords (z.B. max 3-4 pro Vortrag)
 */
async function generateKeywordsFlexibleWithBudget(
  lectureId, 
  headings, 
  template, 
  existingVocabulary = [], 
  frequencyMap = {},
  provider = null,
  maxNewKeywords = 4  // Budget: Max. neue Keywords
) {
  // Extrahiere Template-Vokabular
  const { vocabulary: templateVocab, themeMapping, synonymMap } = extractVocabularyFromTemplate(template);
  
  // Kombiniere Template-Vokabular mit existierenden Keywords
  const fullVocabulary = [...new Set([...templateVocab, ...existingVocabulary])];
  
  // Extrahiere Hauptbegriffe aus Überschriften
  const headingKeyTerms = extractKeyTermsFromHeadings(headings);
  
  // Finde thematisch passende Keywords aus Vokabular
  const relatedKeywords = fullVocabulary.filter(kw => 
    headingKeyTerms.some(term => 
      kw.toLowerCase().includes(term.toLowerCase()) || 
      term.toLowerCase().includes(kw.toLowerCase())
    )
  ).slice(0, 80);
  
  // Häufigste Keywords (Top 120)
  const sortedByFreq = Object.entries(frequencyMap)
    .sort((a, b) => b[1] - a[1])
    .map(([term]) => term)
    .slice(0, 120);
  
  // Formatiere Überschriften (nur H3 und H4)
  const relevantHeadings = headings.filter(h => h.level === 'h3' || h.level === 'h4');
  const headingsText = relevantHeadings
    .map((h, idx) => `${idx + 1}. ${h.text} [${h.level}, Index: ${h.index}]`)
    .join('\n');
  
  const confidenceThreshold = template.metadata.confidenceThreshold || 0.6;
  
  // NEUER PROMPT: Keine feste Anzahl, sondern flexible Generierung
  const prompt = `FLEXIBLE VERSCHLAGWORTUNG - Verwende bevorzugt EXISTIERENDES Vokabular!

VORTRAG: ${lectureId}
ÜBERSCHRIFTEN: ${relevantHeadings.length}

VERFÜGBARES VOKABULAR (${fullVocabulary.length} Begriffe):
Thematisch passend (Top 80): ${relatedKeywords.join(', ') || 'keine'}
Häufigste (Top 120): ${sortedByFreq.slice(0, 120).join(', ')}

ÜBERSCHRIFTEN ZU VERSCHLAGWORTEN:
${headingsText}

AUFGABE:
Analysiere den INHALT dieser Überschriften und erstelle eine FLEXIBLE Anzahl von Schlagworten.

BUDGET & REGELN:
1. ✅ BEVORZUGE STARK existierende Vokabular-Begriffe
2. ✅ Mehrere Überschriften können das GLEICHE Keyword verwenden
3. ✅ Nicht jede Überschrift braucht ein eigenes Keyword
4. ⚠️ BUDGET: Maximal ${maxNewKeywords} NEUE Keywords für diesen Vortrag
5. ✅ Ziel: 6-10 Keywords TOTAL (Mischung aus existierend + wenige neue)
6. ✅ Confidence > ${confidenceThreshold} für existierende, < ${confidenceThreshold} für neue

MATCHING-HIERARCHIE:
1. Exaktes Match im Vokabular → VERWENDEN (matchType: "exact", confidence: 0.9-1.0)
2. Wortstamm-Match → VERWENDEN (matchType: "wordstem", confidence: 0.8-0.9)
3. Semantisch ähnlich → VERWENDEN (matchType: "similar", confidence: 0.7-0.85)
4. Wenn Budget erlaubt UND nichts passt → NEU (matchType: "new", confidence: 0.5-0.65)
5. Wenn Budget erschöpft → Verwende generischeres existierendes Keyword

BEISPIELE:
Überschrift: "Der ätherische Leib und seine Funktionen"
→ Vokabular hat: "Ätherleib" (150x)
→ WÄHLE: "Ätherleib" (exact, 0.95)

Überschrift: "Karma in verschiedenen Kulturen"
→ Vokabular hat: "Karma" (200x), "Reinkarnation" (180x)
→ WÄHLE: "Karma" (exact, 0.95)

Überschriften: "Das Ich im Denken", "Die Entwicklung des Ich", "Ich und Selbst"
→ Vokabular hat: "Ich-Entwicklung" (80x)
→ WÄHLE für ALLE 3: "Ich-Entwicklung" (similar, 0.85)
→ Ergebnis: 3 Überschriften, aber nur 1 Keyword

Überschrift: "Spezifisches neues Konzept XYZ"
→ Vokabular hat nichts passendes
→ Budget erlaubt noch 2 neue
→ ERSTELLE NEU: "Konzept XYZ" (new, 0.6)

JSON-AUSGABE (NUR Array, kein Text):
[
  {
    "term": "Schlagwort",
    "index": "^abc123",
    "heading": "Original-Überschrift",
    "level": "h3",
    "matchType": "exact|wordstem|similar|new",
    "matchedExisting": "Name des gematchten Keywords (oder null bei new)",
    "confidence": 0.0-1.0
  }
]

WICHTIG: Antworte NUR mit dem JSON-Array. Keine Erklärungen!`;

  try {
    
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 4000,
      temperature: 0.4
    });
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    const keywords = JSON.parse(responseText);
    
    if (!Array.isArray(keywords)) {
      throw new Error('LLM gab kein Array zurück');
    }
    
    
    // VALIDIERUNG & BUDGET-ENFORCEMENT
    const validatedKeywords = [];
    const rejectedKeywords = [];
    let newKeywordsCount = 0;
    
    for (const kw of keywords) {
      let term = kw.term.trim();
      
      // Bereinige zu lange Keywords
      const wordCount = term.split(/\s+/).length;
      if (wordCount > 3) {
        // Versuche zu kürzen
        const words = term.split(/\s+/);
        
        // Strategie: Letztes Wort wenn im Vokabular
        const lastWord = words[words.length - 1];
        if (fullVocabulary.some(v => v.toLowerCase() === lastWord.toLowerCase())) {
          term = lastWord;
        } else if (words.length >= 2) {
          term = words.slice(-2).join(' ');
        }
        
      }
      
      // Prüfe ob neu
      const isNew = kw.matchType === 'new' || !fullVocabulary.some(
        v => v.toLowerCase() === term.toLowerCase()
      );
      
      // Budget-Check
      if (isNew) {
        if (newKeywordsCount >= maxNewKeywords) {
          rejectedKeywords.push({ term, reason: 'Budget erschöpft' });
          continue;
        }
        newKeywordsCount++;
      }
      
      // Akzeptiere Keyword
      validatedKeywords.push({
        term: term,
        index: kw.index,
        heading: kw.heading,
        level: kw.level || 'h3',
        matchType: isNew ? 'new' : (kw.matchType || 'existing'),
        matchedExisting: kw.matchedExisting || null,
        confidence: kw.confidence || (isNew ? 0.6 : 0.85),
        theme: null  // Wird nachher zugeordnet
      });
    }
    
    // Deduplizierung (gleiche Keywords zusammenfassen)
    const uniqueKeywords = [];
    const seen = new Set();
    
    for (const kw of validatedKeywords) {
      const normalizedTerm = kw.term.toLowerCase().trim();
      if (!seen.has(normalizedTerm)) {
        seen.add(normalizedTerm);
        uniqueKeywords.push(kw);
      }
    }
    
    
    // THEMEN-ZUORDNUNG für neue Keywords
    const themesList = template.themes;
    const finalKeywords = [];
    
    for (const kw of uniqueKeywords) {
      let theme = themeMapping[kw.term.toLowerCase().trim()];
      
      // Wenn nicht im Template UND neu → versuche Thema zu finden
      if (!theme && kw.matchType === 'new') {
        theme = await assignThemeToNewKeyword(kw.term, themesList, provider);
      }
      
      finalKeywords.push({
        ...kw,
        theme: theme || null
      });
    }
    
    // Statistiken
    const newKws = finalKeywords.filter(k => k.matchType === 'new');
    const exactKws = finalKeywords.filter(k => k.matchType === 'exact');
    const withTheme = finalKeywords.filter(k => k.theme !== null);
    
    
    return finalKeywords;
    
  } catch (error) {
    console.error(`[KEYWORDS-FLEX] ${lectureId}: Fehler:`, error.message);
    return extractKeywordsFromHeadings(headings);
  }
}

/**
 * OPTIMIERTE VERSION: Generiere Keywords OHNE Template neu zu laden
 * Provider wird als Parameter übergeben (bereits initialisiert)
 */
async function generateKeywordsFromHeadingsWithTemplateOptimized(lectureId, headings, template, existingVocabulary = [], frequencyMap = {}, provider = null) {
  // Verwende übergebenen Provider (bereits initialisiert) oder erstelle neuen
  if (!provider) {
    // Fallback wenn kein Provider übergeben wurde
    const { getAllAvailableProviders } = require('./llm-providers');
    const availableProviders = getAllAvailableProviders('keywords');
    
    if (availableProviders.length === 0) {
      return extractKeywordsFromHeadings(headings);
    }
    
    provider = availableProviders[0];
  }
  
  // Extrahiere Template-Vokabular (nur einmal pro Batch wäre besser, aber ok)
  const { vocabulary: templateVocab, themeMapping, synonymMap } = extractVocabularyFromTemplate(template);
  
  // Kombiniere Template-Vokabular mit existierenden Keywords
  const fullVocabulary = [...new Set([...templateVocab, ...existingVocabulary])];
  
  // Extrahiere Hauptbegriffe aus Überschriften
  const headingKeyTerms = extractKeyTermsFromHeadings(headings);
  
  // Finde thematisch passende Keywords aus Vokabular
  const relatedKeywords = fullVocabulary.filter(kw => 
    headingKeyTerms.some(term => 
      kw.toLowerCase().includes(term.toLowerCase()) || 
      term.toLowerCase().includes(kw.toLowerCase())
    )
  ).slice(0, 50);
  
  // Häufigste Keywords (Top 100)
  const sortedByFreq = Object.entries(frequencyMap)
    .sort((a, b) => b[1] - a[1])
    .map(([term]) => term)
    .slice(0, 100);
  
  // Formatiere Überschriften (nur H3 und H4)
  const relevantHeadings = headings.filter(h => h.level === 'h3' || h.level === 'h4');
  const headingsText = relevantHeadings
    .map((h, idx) => `${idx + 1}. ${h.text} [${h.level}, Index: ${h.index}]`)
    .join('\n');
  
  // Formatiere Synonym-Gruppen für Prompt
  const synonymInfo = Object.entries(synonymMap)
    .map(([canonical, syns]) => `"${canonical}" (bevorzugt) = ${syns.join(', ')}`)
    .join('\n');
  
  const confidenceThreshold = template.metadata.confidenceThreshold || 0.6;
  
  // Erstelle vollständige Vokabular-Liste
  const templateKeywordsOnly = Array.from(templateVocab);
  const priorityVocab = [...new Set([...relatedKeywords, ...sortedByFreq.slice(0, 100)])];
  
  // Verwende den GLEICHEN Prompt wie in der Hauptfunktion
  const prompt = `STRIKTE VERSCHLAGWORTUNG - Verwende NUR Begriffe aus dem VOKABULAR!

⚠️ ZWINGEND: Wähle für JEDE Überschrift ein Keyword AUS DEM VOKABULAR (unten).
⚠️ NUR wenn KEIN passender Begriff existiert (confidence < ${confidenceThreshold}): Erstelle neues Keyword.

TEMPLATE-VOKABULAR (${templateKeywordsOnly.length} vordefinierte Begriffe):
${templateKeywordsOnly.slice(0, 200).join(', ')}

ZUSÄTZLICH VERFÜGBAR (häufig verwendet):
${priorityVocab.slice(0, 100).join(', ')}

SYNONYME (verwende IMMER den kanonischen Begriff):
${synonymInfo || 'keine'}

ÜBERSCHRIFTEN (H3/H4):
${headingsText}

VORGEHEN FÜR JEDE ÜBERSCHRIFT:
1. Kern-Konzept identifizieren (z.B. "Geisteswissenschaft", "Reinkarnation", "Kant")
2. Im VOKABULAR oben suchen (exakt, Wortstamm, oder Synonym)
3. Wenn gefunden → verwenden (confidence 0.8-1.0)
4. Wenn NICHT gefunden → NUR DANN neues Keyword (confidence < ${confidenceThreshold})
5. Füllwörter entfernen: "Wesen", "Problem", "Lehre", "Stellung", "Bedeutung"
6. Adjektive entfernen: "griechischen", "suggestive", "materialistische"
7. ZIEL: 1 Wort (selten 2, maximal 3)

ZWINGEND BEFOLGEN:
1. ✅ Suche ZUERST im Vokabular (oben) - verwende exakte/ähnliche Begriffe
2. ✅ ZIEL: 1 Wort (z.B. "Karma", "Parmenides", "Christentum")
3. ✅ Maximal 2-3 Worte bei Komposita (z.B. "Leben und Tod", "deutscher Idealismus")
4. ❌ Entferne Füllwörter: "Wesen", "Problem", "Lehre", "Stellung", "Aufgabe"
5. ❌ Entferne Adjektive: "griechischen", "suggestive", "materialistische"
6. ❌ NUR neue Keywords wenn im Vokabular NICHTS passt (confidence < ${confidenceThreshold})
7. ✅ Korrekte Grammatik (z.B. "biologischer Grundsatz" nicht "biologischen Grundsatz")

WICHTIG:
- 95% der Keywords MÜSSEN aus dem VOKABULAR stammen!
- Nur 5% dürfen neu sein (wenn wirklich nichts passt)
- matchType: "exact" (im Vokabular), "wordstem" (ähnlich), "synonym", "new" (selten!)
- confidence: 0.9-1.0 wenn im Vokabular, <${confidenceThreshold} für neu

JSON (NUR Array, kein Markdown, kein Text):
[{"term":"Schlagwort","index":"^abc","heading":"...","level":"h3","matchType":"exact","confidence":0.95}]`;

  try {
    // Verwende DIREKT den übergebenen Provider (KEINE neue Initialisierung)
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 4096,
      temperature: 0.2
    });
    
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    let keywords = JSON.parse(responseText);
    
    // Validierung und Bereinigung (gleicher Code wie in Hauptfunktion)
    const validatedKeywords = [];
    const rejectedKeywords = [];
    const cleanedKeywords = [];
    
    keywords.forEach(kw => {
      let term = kw.term.trim();
      const originalTerm = term;
      
      // Automatische Bereinigung
      const fillWords = [
        'Problem', 'Lehre', 'Stellung', 'Wendung', 'Bedeutung', 'Wesen', 'Begriff', 'Frage',
        'Aufgabe', 'Prozess', 'Natur', 'Macht', 'Bedürfnis', 'Wesenheit'
      ];
      fillWords.forEach(fw => {
        term = term.replace(new RegExp(`^${fw}\\s+`, 'i'), '');
        if (term.split(/\s+/).length > 3) {
          term = term.replace(new RegExp(`\\s+${fw}\\s+`, 'i'), ' ');
        }
      });
      
      const adjectives = [
        'griechischen', 'individuellen', 'historische', 'hellenistischen', 'neuzeitlichen',
        'suggestive', 'erwachende', 'ewige', 'materialistische', 'geisteswissenschaftliche',
        'viergliederige', 'menschlichen', 'seelische'
      ];
      adjectives.forEach(adj => {
        term = term.replace(new RegExp(`^${adj}\\s+`, 'i'), '');
      });
      
      term = term.replace(/geisteswissenschaftlichen Forschung/i, 'Geisteswissenschaftliche Forschung');
      term = term.replace(/biologischen Grundsatz/i, 'biologischer Grundsatz');
      term = term.replace(/menschlichen Wesenskern/i, 'Wesenskern');
      term = term.replace(/menschlichen Seele/i, 'der Seele');
      term = term.replace(/Viergliederige Wesenheit Menschen/i, 'Viergliederigkeit Mensch');
      term = term.replace(/\s+(und|oder|zwischen|nach|zu)\s*$/i, '');
      
      // Weitere Bereinigung bei zu langen Keywords
      if (term.split(/\s+/).length > 3) {
        const words = term.split(/\s+/);
        const lastWord = words[words.length - 1];
        if (fullVocabulary.some(v => v.toLowerCase() === lastWord.toLowerCase())) {
          term = lastWord;
        } else if (words.length >= 2) {
          const lastTwo = words.slice(-2).join(' ');
          if (fullVocabulary.some(v => v.toLowerCase() === lastTwo.toLowerCase())) {
            term = lastTwo;
          }
        }
      }
      
      if (term !== originalTerm) {
        cleanedKeywords.push({ old: originalTerm, new: term });
      }
      
      const finalWordCount = term.split(/\s+/).length;
      if (finalWordCount > 3) {
        const words = term.split(/\s+/);
        const capitalWords = words.filter(w => /^[A-ZÄÖÜ]/.test(w));
        if (capitalWords.length <= 2 && capitalWords.length > 0) {
          term = capitalWords.slice(0, 2).join(' ');
        } else if (words.length >= 2) {
          term = words.slice(0, 2).join(' ');
        }
      }
      
      // Vokabular-Validierung
      const existsInTemplate = templateVocab.some(v => v.toLowerCase() === term.toLowerCase());
      const existsInFull = fullVocabulary.some(v => v.toLowerCase() === term.toLowerCase());
      
      if (existsInTemplate || existsInFull) {
        validatedKeywords.push({ ...kw, term: term });
      } else if (kw.matchType === 'new' && (kw.confidence || 0) < confidenceThreshold) {
        validatedKeywords.push({ ...kw, term: term });
      } else if (finalWordCount <= 3) {
        validatedKeywords.push({ ...kw, term: term, matchType: 'new', confidence: 0.5 });
      } else {
        rejectedKeywords.push(originalTerm);
      }
    });
    
    // Themen-Zuordnung
    const finalKeywords = validatedKeywords.map(kw => {
      const theme = themeMapping[kw.term.toLowerCase().trim()];
      return { ...kw, theme: theme || null };
    });
    
    const newKws = finalKeywords.filter(k => k.matchType === 'new');
    const exactKws = finalKeywords.filter(k => k.matchType === 'exact');
    
    
    return finalKeywords;
    
  } catch (error) {
    console.error(`[KEYWORDS-OPT] ${lectureId}: Fehler:`, error.message);
    return extractKeywordsFromHeadings(headings);
  }
}

/**
 * Synonym-Konsolidierung: Findet und merged ähnliche Keywords
 */
async function consolidateSynonymsInKeywords(keywordsDB, synonymMap) {
  
  let consolidatedCount = 0;
  
  for (const [lectureId, data] of Object.entries(keywordsDB)) {
    if (!data.keywords || !Array.isArray(data.keywords)) continue;
    
    data.keywords.forEach(kw => {
      const term = kw.term.toLowerCase().trim();
      
      // Prüfe ob dieser Begriff ein Synonym ist
      for (const [canonical, synonyms] of Object.entries(synonymMap)) {
        if (synonyms.map(s => s.toLowerCase()).includes(term)) {
          // Ersetze durch kanonischen Begriff
          const originalTerm = kw.term;
          kw.term = canonical.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          
          if (originalTerm !== kw.term) {
            consolidatedCount++;
          }
        }
      }
    });
  }
  
  
  return consolidatedCount;
}

/**
 * Aktualisiert themes-database.json basierend auf Template
 * Frontend erwartet diese Struktur für Timeline-Tab
 */
async function updateThemesDatabaseFromTemplate(template) {
  
  try {
    // Konvertiere Template-Struktur in themes-database Format
    const themesDB = {};
    
    for (const [themeName, themeData] of Object.entries(template.themes)) {
      themesDB[themeName] = {
        description: themeData.description || '',
        keywords: themeData.keywords || []
      };
    }
    
    // Speichere in themes-database.json
    await saveThemesDatabase(themesDB);
    
    
    return themesDB;
  } catch (error) {
    console.error('[THEMES-UPDATE] Fehler:', error);
    throw error;
  }
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
    
    return result;
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler bei Expansion:', error);
    throw error;
  }
}

// Endpoint: Liste verfügbare GA-Bände
app.get('/api/keywords/available-ga-volumes', async (req, res) => {
  try {
    
    // Lade Summary-Database
    let summaryDB = {};
    try {
      summaryDB = JSON.parse(fsSync.readFileSync(SUMMARY_DB_FILE, 'utf8'));
    } catch (error) {
    }
    
    // Lade Keywords-Database
    let keywordsDB = {};
    try {
      keywordsDB = JSON.parse(fsSync.readFileSync(KEYWORDS_DB_FILE, 'utf8'));
    } catch (error) {
    }
    
    // Sammle ALLE GA-Bände aus fullLectures, fullBooks UND summaryDB
    const allGABands = new Set();
    
    // GA-Bände aus fullLectures
    Object.keys(fullLectures).forEach(lectureId => {
      const gaMatch = lectureId.match(/^(GA\d{3}[a-z]?)\//i);
      if (gaMatch) {
        allGABands.add(gaMatch[1].toLowerCase());
      }
    });
    
    // GA-Bände aus fullBooks (Schriften)
    Object.values(fullBooks).forEach(book => {
      const gaNumber = book.ID || book.gaNumber;
      if (gaNumber && typeof gaNumber === 'string') {
        allGABands.add(gaNumber.toLowerCase());
      }
    });
    
    // GA-Bände aus summaryDB
    Object.keys(summaryDB).forEach(lectureId => {
      const gaMatch = lectureId.match(/^(GA\d{3}[a-z]?)\//i);
      if (gaMatch) {
        allGABands.add(gaMatch[1].toLowerCase());
      }
    });
    
    // Gruppiere Vorträge nach GA-Band
    const gaGroups = {};
    Object.keys(fullLectures).forEach(lectureId => {
      const gaMatch = lectureId.match(/^(GA\d{3}[a-z]?)\//i);
      if (gaMatch) {
        const ga = gaMatch[1].toLowerCase();
        if (!gaGroups[ga]) gaGroups[ga] = [];
        gaGroups[ga].push(lectureId);
      }
    });
    
    // Sortiere GA-Bände
    const sortedGAs = Array.from(allGABands).sort((a, b) => {
      const numA = parseInt(a.replace(/^ga/i, ''));
      const numB = parseInt(b.replace(/^ga/i, ''));
      return numA - numB;
    });
    
    const volumes = sortedGAs.map(ga => {
      const lectures = gaGroups[ga] || [];
      
      // Prüfe ob ALLE Vorträge des Bandes vollständig bearbeitet sind
      const allLecturesComplete = lectures.length > 0 && lectures.every(lectureId => {
        // Prüfe ob Vortrag in summaryDB existiert
        const summaryEntry = summaryDB[lectureId];
        if (!summaryEntry) return false;
        
        // Prüfe ob V2-Struktur vorhanden (mit tableOfContents und lectureKeywords)
        const hasTableOfContents = summaryEntry.tableOfContents && summaryEntry.tableOfContents.length > 0;
        const hasLectureKeywords = summaryEntry.lectureKeywords && summaryEntry.lectureKeywords.length > 0;
        
        // Prüfe ob Keywords-Eintrag vorhanden
        const hasKeywordsEntry = keywordsDB[lectureId] && 
                                  keywordsDB[lectureId].keywords && 
                                  keywordsDB[lectureId].keywords.length > 0;
        
        // Alle drei müssen vorhanden sein
        return hasTableOfContents && hasLectureKeywords && hasKeywordsEntry;
      });
      
      // Wenn mindestens ein Vortrag vollständig ist, markiere als "teilweise bearbeitet"
      const someLecturesComplete = lectures.length > 0 && lectures.some(lectureId => {
        const summaryEntry = summaryDB[lectureId];
        if (!summaryEntry) return false;
        
        const hasTableOfContents = summaryEntry.tableOfContents && summaryEntry.tableOfContents.length > 0;
        const hasLectureKeywords = summaryEntry.lectureKeywords && summaryEntry.lectureKeywords.length > 0;
        const hasKeywordsEntry = keywordsDB[lectureId] && 
                                  keywordsDB[lectureId].keywords && 
                                  keywordsDB[lectureId].keywords.length > 0;
        
        return hasTableOfContents && hasLectureKeywords && hasKeywordsEntry;
      });
      
      return {
        volume: ga,
        lectureCount: lectures.length,
        lectures: lectures.sort(),
        hasKeywords: someLecturesComplete,  // Mindestens ein Vortrag vollständig
        isComplete: allLecturesComplete     // ALLE Vorträge vollständig
      };
    });
    
    res.json({ volumes });
  } catch (error) {
    console.error('[API/AVAILABLE-GA-VOLUMES] Fehler:', error);
    console.error('[API/AVAILABLE-GA-VOLUMES] Stack:', error.stack);
    res.status(500).json({ error: error.message, details: error.stack });
  }
});

// Endpoint: Regeneriere einen GA-Band
app.post('/api/keywords/regenerate-ga-volume', async (req, res) => {
  const { gaVolume, useExistingVocab, updateClusters, parallelBatchSize, forceReprocess } = req.body;
  const PARALLEL_BATCH_SIZE = parallelBatchSize || 10; // Default: 10 parallel
  
  
  try {
    // 1. Lade Seed-Keywords
    const seedKeywords = loadSeedKeywords();
    if (seedKeywords.length === 0) {
      throw new Error('Keine Seed-Keywords gefunden');
    }
    
    // 2. Lade Full Lectures für Datum/Jahr
    if (Object.keys(fullLectures).length === 0) {
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
        
      } catch (error) {
      }
    }
    
    // 4. Filtere Vorträge für diesen GA-Band
    const { gaGroups } = groupLecturesByGA(summaryDB);
    const lectures = gaGroups[gaVolume];
    
    if (!lectures || lectures.length === 0) {
      throw new Error(`Keine Vorträge für ${gaVolume} gefunden`);
    }
    
    
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
      
      
      // Erstelle Array von Promises für parallele Verarbeitung
      const batchPromises = batch.map(async (lectureId, batchIndex) => {
        const globalIndex = batchStart + batchIndex;
        const data = summaryDB[lectureId];
        
        if (!data.headings || data.headings.length === 0) {
          return { lectureId, skipped: true };
        }
        
        // Überspringe bereits verarbeitete Vorträge (nur wenn useExistingVocab aktiv)
        if (useExistingVocab && existingKeywordsDB[lectureId]) {
          return { lectureId, skipped: true, reason: 'already_processed' };
        }
        
        try {
          
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
      
      
      // Kleine Pause zwischen Batches (Rate Limit Protection)
      if (batchEnd < sortedLectures.length) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    // 7. Finale Statistiken
    const startVocabSize = useExistingVocab ? Object.keys(existingKeywordsDB).length * 10 : seedKeywords.length; // Schätzung
    if (stats.skipped > 0) {
    }
    
    // 8. Merge mit bestehender Datenbank (falls useExistingVocab)
    let finalDB = newKeywordsDB;
    if (useExistingVocab) {
      finalDB = { ...existingKeywordsDB, ...newKeywordsDB };
    }
    
    // 9. Speichere Ergebnis
    const resultPath = path.join(__dirname, `keywords-database-${gaVolume}.json`);
    fsSync.writeFileSync(resultPath, JSON.stringify(finalDB, null, 2));
    
    // 10. Optional: Aktualisiere Haupt-Datenbank
    if (useExistingVocab) {
      // BACKUP erstellen vor dem Speichern
      await createKeywordsBackup();
      
      // Validiere dass Datenbank nicht leer ist
      if (Object.keys(finalDB).length === 0) {
        console.error('[GA-BATCH] ✗ WARNUNG: finalDB ist leer - Haupt-Datenbank wird NICHT überschrieben!');
      } else {
        fsSync.writeFileSync(KEYWORDS_DB_FILE, JSON.stringify(finalDB, null, 2));
      }
    }
    
    // 11. Optional: Erweitere Cluster mit neuen Keywords
    let clusterUpdateInfo = null;
    if (updateClusters && stats.newKeywords > 0) {
      
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
            
            // Speichere erweiterte Cluster (mit Backup)
            await saveClustersFile(existingClusters);
            
            clusterUpdateInfo = {
              newKeywordsProcessed: newKeywords.length,
              clustersExtended: Object.keys(expansion.assignments || {}).length,
              newClustersCreated: Object.keys(expansion.newClusters || {}).length,
              totalClusters: Object.keys(existingClusters).length
            };
            
          } else {
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
    
    clusterNames.forEach(name => {
    });
    
    // 5. Speichere Ergebnis
    await saveClustersFile({
      generated: new Date().toISOString(),
      seedKeywordsCount: seedKeywords.length,
      clustersCount: clusterNames.length,
      coverage: coverage + '%',
      clusters: clusters
    });
    
    
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
    // Lade themes-database.json (neue Struktur) und konvertiere zu Cluster-Format
    const themesPath = path.join(__dirname, 'themes-database.json');
    const themes = JSON.parse(fsSync.readFileSync(themesPath, 'utf8'));
    
    // Konvertiere zu Cluster-Format für Keyword-Manager
    const clusters = {};
    Object.entries(themes).forEach(([name, data]) => {
      clusters[name] = {
        keywords: data.keywords || [],
        description: data.description || ''
      };
    });
    
    res.json({ clusters });
  } catch (error) {
    // Fallback auf alte thematic-clusters.json
    try {
      const clustersPath = path.join(__dirname, 'thematic-clusters.json');
      const data = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
      res.json(data);
    } catch (fallbackError) {
      res.status(404).json({ error: 'Keine Cluster gefunden. Bitte erst generieren.' });
    }
  }
});

// Manuell Cluster hinzufügen
app.post('/api/themes/add-cluster', async (req, res) => {
  const { name, description, keywords } = req.body;
  
  
  try {
    // Validierung
    if (!name || !name.trim()) {
      throw new Error('Themen-Name ist erforderlich');
    }
    
    // Keywords sind optional - leere Themen sind erlaubt
    const validKeywords = (keywords && Array.isArray(keywords)) ? keywords.filter(kw => kw && kw.trim()) : [];
    
    // GEÄNDERT: Speichere in themes-database.json statt thematic-clusters.json
    const themesDB = await loadThemesDatabase();
    
    // Prüfe ob Thema bereits existiert
    if (themesDB[name]) {
      throw new Error(`Themenbereich "${name}" existiert bereits`);
    }
    
    // Füge neuen Themenbereich hinzu
    themesDB[name] = {
      description: description || `Manuell hinzugefügter Themenbereich: ${name}`,
      keywords: validKeywords
    };
    
    // Speichere in themes-database.json
    await saveThemesDatabase(themesDB);
    
    
    res.json({
      success: true,
      clusterName: name,
      keywordCount: validKeywords.length,
      totalClusters: Object.keys(themesDB).length
    });
    
  } catch (error) {
    console.error('[THEMES] Fehler beim Hinzufügen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Cluster reorganisieren (Keywords neu zuordnen)
app.post('/api/themes/reorganize-clusters', async (req, res) => {
  
  try {
    // GEÄNDERT: Verwende themes-database.json statt thematic-clusters.json
    const themesDB = await loadThemesDatabase();
    
    if (Object.keys(themesDB).length === 0) {
      throw new Error('Keine Themen gefunden. Bitte erst generieren.');
    }
    
    const clusters = themesDB;
    
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
      
    } catch (error) {
      // Fallback: Sammle Keywords aus Clustern
      Object.values(clusters).forEach(cluster => {
        if (cluster.keywords && Array.isArray(cluster.keywords)) {
          cluster.keywords.forEach(kw => allKeywords.add(kw));
        }
      });
    }
    
    const keywordsList = Array.from(allKeywords);
    
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
          keywords: data.keywords
        };
      });
    }
    
    // GEÄNDERT: Speichere direkt in themes-database.json (ohne Metadaten-Wrapper)
    await saveThemesDatabase(finalClusters);
    
    
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
  
  
  try {
    if (!keyword || !keyword.trim()) {
      throw new Error('Keyword erforderlich');
    }
    
    if (!targetCluster || !targetCluster.trim()) {
      throw new Error('Ziel-Cluster erforderlich');
    }
    
    // Lade themes-database.json (neue Struktur)
    const themesPath = path.join(__dirname, 'themes-database.json');
    const themes = JSON.parse(fsSync.readFileSync(themesPath, 'utf8'));
    
    if (!themes[targetCluster]) {
      throw new Error(`Cluster "${targetCluster}" existiert nicht`);
    }
    
    const normalizedKeyword = keyword.trim().toLowerCase();
    let foundInCluster = null;
    let removed = false;
    
    // Suche Keyword in allen Clustern und entferne es
    for (const [clusterName, clusterData] of Object.entries(themes)) {
      if (!clusterData.keywords || !Array.isArray(clusterData.keywords)) continue;
      
      const index = clusterData.keywords.findIndex(kw => kw.toLowerCase() === normalizedKeyword);
      if (index !== -1) {
        foundInCluster = clusterName;
        clusterData.keywords.splice(index, 1);
        removed = true;
      }
    }
    
    if (!removed) {
    }
    
    // Füge Keyword zum Ziel-Cluster hinzu (wenn nicht schon vorhanden)
    if (!themes[targetCluster].keywords) {
      themes[targetCluster].keywords = [];
    }
    
    const keywordsArray = themes[targetCluster].keywords;
    if (!keywordsArray.some(kw => kw.toLowerCase() === normalizedKeyword)) {
      keywordsArray.push(keyword.trim());
    } else {
    }
    
    // Speichere aktualisierte themes-database.json
    await fs.writeFile(themesPath, JSON.stringify(themes, null, 2), 'utf8');
    
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
    
    // Speichere aktualisierte Keywords-Database mit Locking-Mechanismus
    await saveCompleteKeywordsDatabase(keywordsDB);
    
    // SYNC: Aktualisiere auch Summary-Database (für Vorträge im Texte-Tab)
    const summaryDB = await loadSummaryDatabase();
    let summaryAffected = 0;
    let summaryChecked = 0;
    
    for (const [lectureId, data] of Object.entries(summaryDB)) {
      if (!data.lectureKeywords || !Array.isArray(data.lectureKeywords)) continue;
      summaryChecked++;
      
      let lectureModified = false;
      const updatedKeywords = [];
      
      // Prüfe ob Vortrag bereits das neue Keyword hat
      const hasNewKeyword = newKwLower && data.lectureKeywords.some(kw => 
        kw.term.toLowerCase() === newKwLower
      );
      
      data.lectureKeywords.forEach(kw => {
        const kwLower = kw.term.toLowerCase();
        
        if (kwLower === oldKwLower) {
          lectureModified = true;
          
          if (newKeyword && newKeyword.trim()) {
            // Zusammenführen/Umbenennen
            if (!hasNewKeyword) {
              // Kein Duplikat: Umbenennen
              updatedKeywords.push({
                ...kw,
                term: newKeyword.trim()
              });
            }
            // Bei Duplikat: altes Keyword einfach entfernen
          }
          // Wenn newKeyword leer: löschen
        } else {
          updatedKeywords.push(kw);
        }
      });
      
      if (lectureModified) {
        summaryDB[lectureId].lectureKeywords = updatedKeywords;
        summaryAffected++;
      }
    }
    
    
    if (summaryAffected > 0) {
      await saveCompleteSummaryDatabase(summaryDB); // Speichere komplette DB mit Locking
    } else {
    }
    
    
    res.json({
      success: true,
      affectedLectures: affectedLectures,
      summaryAffected: summaryAffected,
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
  
  
  try {
    if (!oldName || !newName) {
      throw new Error('Alter und neuer Name erforderlich');
    }
    
    if (oldName === newName) {
      throw new Error('Namen sind identisch');
    }
    
    // GEÄNDERT: Verwende themes-database.json
    const themesDB = await loadThemesDatabase();
    
    if (Object.keys(themesDB).length === 0) {
      throw new Error('Keine Themen gefunden');
    }
    
    if (!themesDB[oldName]) {
      throw new Error(`Themenbereich "${oldName}" nicht gefunden`);
    }
    
    if (themesDB[newName]) {
      throw new Error(`Themenbereich "${newName}" existiert bereits. Verwenden Sie Zusammenführen.`);
    }
    
    // Umbenennen
    themesDB[newName] = { ...themesDB[oldName] };
    delete themesDB[oldName];
    
    // Speichern
    await saveThemesDatabase(themesDB);
    
    
    res.json({
      success: true,
      totalClusters: Object.keys(themesDB).length
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler beim Umbenennen:', error);
    res.status(500).json({ error: error.message });
  }
});

// Endpoint: Cluster zusammenführen
app.post('/api/themes/merge-clusters', async (req, res) => {
  const { sourceCluster, targetCluster } = req.body;
  
  
  try {
    if (!sourceCluster || !targetCluster) {
      throw new Error('Quell- und Ziel-Cluster erforderlich');
    }
    
    if (sourceCluster === targetCluster) {
      throw new Error('Cluster müssen unterschiedlich sein');
    }
    
    // GEÄNDERT: Verwende themes-database.json
    const themesDB = await loadThemesDatabase();
    
    if (Object.keys(themesDB).length === 0) {
      throw new Error('Keine Themen gefunden');
    }
    
    if (!themesDB[sourceCluster]) {
      throw new Error(`Quell-Themenbereich "${sourceCluster}" nicht gefunden`);
    }
    
    if (!themesDB[targetCluster]) {
      throw new Error(`Ziel-Themenbereich "${targetCluster}" nicht gefunden`);
    }
    
    // Merge Keywords
    const sourceKeywords = themesDB[sourceCluster].keywords || [];
    const targetKeywords = themesDB[targetCluster].keywords || [];
    
    // Kombiniere und dedupliziere
    const mergedKeywords = [...new Set([...targetKeywords, ...sourceKeywords])];
    
    themesDB[targetCluster].keywords = mergedKeywords;
    
    // Lösche Quell-Themenbereich
    delete themesDB[sourceCluster];
    
    // Speichern
    await saveThemesDatabase(themesDB);
    
    
    res.json({
      success: true,
      keywordsMerged: sourceKeywords.length,
      totalClusters: Object.keys(themesDB).length
    });
    
  } catch (error) {
    console.error('[CLUSTERS] Fehler beim Zusammenführen:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================

// HAUPTFUNKTION: Extrahiere Keywords aus Überschriften (regel-basiert, ohne KI)
function extractKeywordsFromHeadings(headings) {
  
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
      
      
      const volumeResults = [];
      let totalProcessed = 0;
      let totalSkipped = 0;
      let totalErrors = 0;
      
      // Verarbeite jeden GA-Band sequenziell
      for (const volume of volumes) {
        
        // Filtere Vorträge für diesen GA-Band
        const volumeLectures = Object.keys(summaryDB).filter(lid => 
          lid.startsWith(volume + '/')
        );
        
        if (volumeLectures.length === 0) {
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
        
        
        let volumeProcessed = 0;
        let volumeSkipped = 0;
        let volumeErrors = 0;
        
        // Definiere Verarbeitungsfunktion für einen Vortrag
        const processLecture = async (lid, index) => {
          // Überspringe, wenn bereits Keywords existieren
          if (keywordsDB[lid]) {
            return { status: 'skipped', lectureId: lid, reason: 'bereits vorhanden' };
          }
          
          const summaryData = summaryDB[lid];
          if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
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
          
          
          return { 
            status: 'processed', 
            lectureId: lid, 
            keywords: keywords.length, 
            success: true 
          };
        };
        
        // Verarbeite alle Vorträge dieses Bandes parallel (max 10 gleichzeitig)
        const startTime = Date.now();
        
        const batchResults = await processBatchWithConcurrency(
          volumeLectures,
          processLecture,
          10,  // Concurrency Limit
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
        allLectureIds = allLectureIds.filter(lid => {
          const gaNumber = lid.split('/')[0]; // z.B. "GA110"
          return gaFilter.includes(gaNumber);
        });
      }
      
      const total = allLectureIds.length;
      const toProcess = allLectureIds.slice(startIndex, startIndex + batchSize);
      
      
      // Definiere Verarbeitungsfunktion für einen Vortrag
      const processLecture = async (lid, index) => {
        // Überspringe, wenn bereits Keywords existieren
        if (keywordsDB[lid]) {
          return { status: 'skipped', lectureId: lid, reason: 'bereits vorhanden' };
        }
        
        const summaryData = summaryDB[lid];
        if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
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
        
        
        return { 
          status: 'processed', 
          lectureId: lid, 
          keywords: keywords.length, 
          success: true 
        };
      };
      
      // Verarbeite alle Vorträge parallel (max 10 gleichzeitig)
      const batchResults = await processBatchWithConcurrency(
        toProcess,
        processLecture,
        10,  // Concurrency Limit
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

// API: Bilder-Datenbank abrufen (nur für einen bestimmten Vortrag)
// Lädt die Bilder aus den Part-Dateien bei Bedarf, ohne alle beim Start zu laden
app.get('/api/steiner-images/:lectureId?', async (req, res) => {
  try {
    const lectureId = req.params.lectureId;
    
    if (lectureId) {
      // VALIDIERUNG ENTFERNT - verursachte Probleme
      // Prüfe zuerst ob bereits im Memory-Cache
      if (steinerImages[lectureId]) {
        const images = steinerImages[lectureId];
        return res.json(images);
      }
      
      // Suche in Part-Dateien nach diesem Vortrag
      const files = await fs.readdir(__dirname);
      const partFiles = files
        .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
        .sort();
      
      for (const partFile of partFiles) {
        const partPath = path.join(__dirname, partFile);
        const data = await fs.readFile(partPath, 'utf8');
        const partData = JSON.parse(data);
        
        // Prüfe ob Array oder Objekt
        if (Array.isArray(partData)) {
          // Suche nach Bildern für diesen Vortrag
          const imagesForLecture = partData.filter(img => img.lectureId === lectureId);
          if (imagesForLecture.length > 0) {
            // Cache für zukünftige Anfragen
            steinerImages[lectureId] = imagesForLecture;
            return res.json(imagesForLecture);
          }
        } else {
          // Objekt-Format (legacy)
          if (partData[lectureId]) {
            const images = Array.isArray(partData[lectureId]) ? partData[lectureId] : [partData[lectureId]];
            // Cache für zukünftige Anfragen
            steinerImages[lectureId] = images;
            return res.json(images);
          }
        }
      }
      
      // Keine Bilder gefunden
      steinerImages[lectureId] = []; // Cache leeres Array
      res.json([]);
    } else {
      // Liste aller verfügbaren Vortrags-IDs (ohne Bilder zu laden)
      // Lese nur die ersten Zeilen jeder Part-Datei um lectureIds zu extrahieren
      const files = await fs.readdir(__dirname);
      const partFiles = files
        .filter(f => f.startsWith('steiner-images-part') && f.endsWith('.json'))
        .sort();
      
      const lectureIdsSet = new Set();
      
      for (const partFile of partFiles) {
        const partPath = path.join(__dirname, partFile);
        const data = await fs.readFile(partPath, 'utf8');
        const partData = JSON.parse(data);
        
        if (Array.isArray(partData)) {
          partData.forEach(img => {
            if (img.lectureId) {
              lectureIdsSet.add(img.lectureId);
            }
          });
        } else {
          Object.keys(partData).forEach(id => lectureIdsSet.add(id));
        }
      }
      
      const lectureIds = Array.from(lectureIdsSet);
      res.json({ lectureIds: lectureIds, count: lectureIds.length });
    }
  } catch (error) {
    console.error('[IMAGES-API] Fehler beim Laden:', error);
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
// FLEXIBLE KEYWORD-GENERIERUNG V3 (mit Budget-System)
// ============================================================================

/**
 * API: Flexible Keyword-Generierung mit Budget-System
 * - Keine feste Anzahl von Keywords (6-10 statt 10-12)
 * - Budget begrenzt neue Keywords pro Vortrag
 * - Automatische Themen-Zuordnung für neue Keywords
 * - Iteratives Vokabular-Wachstum
 */
app.post('/api/generate-keywords-v3', async (req, res) => {
  try {
    const { 
      lectureIds = [], 
      gaVolumes = [], 
      useExistingVocab = true,
      maxNewKeywordsPerLecture = 4,  // Budget pro Vortrag
      forceReprocess = false,
      preferredProvider = null
    } = req.body;
    
    
    // Lade Template
    const template = await loadThemesKeywordsTemplate();
    if (!template) {
      return res.status(500).json({ error: 'Template konnte nicht geladen werden' });
    }
    
    // Initialisiere Provider EINMAL
    let provider;
    try {
      if (preferredProvider) {
        const { createProvider } = require('./llm-providers');
        provider = createProvider(preferredProvider);
        if (!provider.isAvailable()) {
          throw new Error(`${preferredProvider} nicht verfügbar`);
        }
      } else {
        provider = getProviderForTask('keywords');
      }
    } catch (error) {
      return res.status(500).json({ 
        error: 'Kein LLM-Provider verfügbar',
        details: error.message 
      });
    }
    
    // Sammle Lecture IDs
    let lectureIdsToProcess = [...lectureIds];
    
    if (gaVolumes.length > 0) {
      for (const gaVolume of gaVolumes) {
        const volumeLectures = Object.keys(fullLectures).filter(id => id.startsWith(gaVolume));
        lectureIdsToProcess.push(...volumeLectures);
      }
    }
    
    lectureIdsToProcess = [...new Set(lectureIdsToProcess)];
    
    if (lectureIdsToProcess.length === 0) {
      return res.status(400).json({ error: 'Keine Lecture IDs angegeben' });
    }
    
    
    // Lade existierende Keywords für iteratives Vokabular
    const existingKeywordsDB = await loadKeywordsDatabase();
    const summaryDB = await loadSummaryDatabase();
    
    // Extrahiere existierendes Vokabular und Frequenzen
    let existingVocabulary = [];
    const frequencyMap = {};
    
    if (useExistingVocab) {
      Object.values(existingKeywordsDB).forEach(lecture => {
        if (lecture.keywords && Array.isArray(lecture.keywords)) {
          lecture.keywords.forEach(kw => {
            const term = kw.term.trim();
            if (!existingVocabulary.includes(term)) {
              existingVocabulary.push(term);
            }
            frequencyMap[term] = (frequencyMap[term] || 0) + 1;
          });
        }
      });
    }
    
    // Verarbeite Vorträge iterativ
    const results = [];
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    let totalNewKeywords = 0;
    let totalKeywords = 0;
    
    for (let i = 0; i < lectureIdsToProcess.length; i++) {
      const lectureId = lectureIdsToProcess[i];
      
      // Prüfe ob bereits verarbeitet
      if (!forceReprocess && existingKeywordsDB[lectureId] && existingKeywordsDB[lectureId].keywords) {
        skipped++;
        continue;
      }
      
      // Prüfe ob Summary vorhanden
      const summaryData = summaryDB[lectureId];
      if (!summaryData || !summaryData.headings) {
        skipped++;
        continue;
      }
      
      try {
        
        // FLEXIBLE GENERIERUNG mit Budget
        const keywords = await generateKeywordsFlexibleWithBudget(
          lectureId,
          summaryData.headings,
          template,
          existingVocabulary,
          frequencyMap,
          provider,
          maxNewKeywordsPerLecture
        );
        
        // Extrahiere Metadaten
        const lecture = fullLectures[lectureId];
        const date = lecture?.date || lecture?.dateString || '';
        const year = date ? parseInt(date.substring(0, 4)) : null;
        const gaMatch = lectureId.match(/^GA(\d+)/);
        const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
        
        // Speichere in Keywords-DB
        await saveKeywordsToDatabase(lectureId, {
          lectureId: lectureId,
          date: date,
          year: year,
          gaVolume: gaVolume,
          summary: summaryData.summary || '',
          keywords: keywords,
          generated: new Date().toISOString(),
          generationMethod: 'flexible-v3',
          maxNewKeywordsBudget: maxNewKeywordsPerLecture
        });
        
        // Aktualisiere Vokabular für nächste Iteration
        keywords.forEach(kw => {
          if (!existingVocabulary.includes(kw.term)) {
            existingVocabulary.push(kw.term);
          }
          frequencyMap[kw.term] = (frequencyMap[kw.term] || 0) + 1;
        });
        
        const newKws = keywords.filter(k => k.matchType === 'new');
        totalKeywords += keywords.length;
        totalNewKeywords += newKws.length;
        
        
        results.push({
          lectureId,
          keywordsCount: keywords.length,
          newKeywordsCount: newKws.length,
          existingKeywordsCount: keywords.length - newKws.length,
          withTheme: keywords.filter(k => k.theme).length,
          withoutTheme: keywords.filter(k => !k.theme).length,
          success: true
        });
        
        processed++;
        
        // Rate Limiting: 200ms zwischen Requests
        if (i < lectureIdsToProcess.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
      } catch (error) {
        console.error(`[KEYWORDS-V3] ${lectureId}: Fehler:`, error.message);
        errors++;
        results.push({
          lectureId,
          success: false,
          error: error.message
        });
      }
    }
    
    
    res.json({
      success: true,
      stats: {
        totalRequested: lectureIdsToProcess.length,
        processed,
        skipped,
        errors,
        totalKeywords,
        newKeywords: totalNewKeywords,
        existingKeywords: totalKeywords - totalNewKeywords,
        newKeywordsPercentage: totalKeywords > 0 ? ((totalNewKeywords / totalKeywords) * 100).toFixed(1) : 0,
        vocabularySize: existingVocabulary.length,
        budgetPerLecture: maxNewKeywordsPerLecture
      },
      results
    });
    
  } catch (error) {
    console.error('[KEYWORDS-V3] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// NEUE TEMPLATE-BASIERTE KEYWORD-GENERIERUNG (V2)
// ============================================================================

/**
 * API: Neue Template-basierte Keyword-Generierung
 * Verwendet themes-keywords-template.json als Vokabular-Basis
 * Extrahiert Keywords aus H3/H4 Überschriften (nicht aus Summary)
 * Confidence-Schwelle: 0.6 (aus Template)
 */
app.post('/api/generate-keywords-v2', async (req, res) => {
  try {
    const { 
      lectureIds = [], 
      gaVolumes = [], 
      startIndex = 0, 
      batchSize = 50,
      useExistingVocab = true,
      consolidateSynonyms = true,
      forceReprocess = false,
      preferredProvider = null  // NEU: Expliziter Provider vom Frontend
    } = req.body;
    
    
    // 1. Lade Template
    const template = await loadThemesKeywordsTemplate();
    const { synonymMap } = extractVocabularyFromTemplate(template);
    
    // 1b. Setze bevorzugten Provider falls angegeben
    if (preferredProvider) {
      // Temporär für diese Anfrage den Provider setzen
      process.env.LLM_PROVIDER_KEYWORDS = preferredProvider;
    }
    
    // 2. Lade bestehende Datenbanken
    const summaryDB = await loadSummaryDatabase();
    let keywordsDB = await loadKeywordsDatabase();
    
    // 3. Baue Vokabular auf
    let existingVocabulary = [];
    let frequencyMap = {};
    
    if (useExistingVocab) {
      for (const [lid, data] of Object.entries(keywordsDB)) {
        if (!data.keywords) continue;
        data.keywords.forEach(kw => {
          existingVocabulary.push(kw.term);
          frequencyMap[kw.term] = (frequencyMap[kw.term] || 0) + 1;
        });
      }
    }
    
    // 4. Bestimme zu verarbeitende Vorträge
    let lectureIdsToProcess = [];
    
    if (gaVolumes.length > 0) {
      // Filtere nach GA-Bänden
      gaVolumes.forEach(gaVol => {
        const volumeLectures = Object.keys(summaryDB).filter(lid => 
          lid.startsWith(gaVol + '/')
        );
        lectureIdsToProcess.push(...volumeLectures);
      });
    } else if (lectureIds.length > 0) {
      lectureIdsToProcess = lectureIds;
    } else {
      return res.status(400).json({ 
        error: 'Bitte lectureIds oder gaVolumes angeben' 
      });
    }
    
    
    // 5. Provider-Setup (EINMAL für alle Vorträge)
    let provider = null;
    if (preferredProvider) {
      const { createProvider } = require('./llm-providers');
      try {
        provider = createProvider(preferredProvider);
        if (!provider.isAvailable()) {
          throw new Error(`${preferredProvider} nicht verfügbar`);
        }
      } catch (error) {
        console.error(`[KEYWORDS-V2] Gewählter Provider nicht verfügbar:`, error.message);
        return res.status(400).json({ error: `Provider ${preferredProvider} nicht verfügbar: ${error.message}` });
      }
    }
    
    // 6. Verarbeite Vorträge
    const results = [];
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    for (let i = 0; i < lectureIdsToProcess.length; i++) {
      const lectureId = lectureIdsToProcess[i];
      
      // Überspringe bereits verarbeitete (außer bei forceReprocess)
      if (keywordsDB[lectureId] && !forceReprocess) {
        skipped++;
        continue;
      }
      
      // Bei forceReprocess: Log dass wir überschreiben
      if (keywordsDB[lectureId] && forceReprocess) {
      }
      
      const summaryData = summaryDB[lectureId];
      if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
        skipped++;
        continue;
      }
      
      try {
        
        // Generiere Keywords - mit VORBEREITETEM Provider
        const keywords = await generateKeywordsFromHeadingsWithTemplateOptimized(
          lectureId,
          summaryData.headings,
          template,
          existingVocabulary,
          frequencyMap,
          provider  // Bereits initialisierter Provider
        );
        
        // Extrahiere Metadaten
        const lecture = fullLectures[lectureId];
        const date = lecture?.date || lecture?.dateString || '';
        const year = date ? parseInt(date.substring(0, 4)) : null;
        const gaMatch = lectureId.match(/^GA(\d+)/);
        const gaVolume = gaMatch ? `GA${gaMatch[1]}` : null;
        
        // Speichere in Keywords-DB
        await saveKeywordsToDatabase(lectureId, {
          lectureId: lectureId,
          date: date,
          year: year,
          gaVolume: gaVolume,
          summary: summaryData.summary || '',
          keywords: keywords,
          generated: new Date().toISOString(),
          generationMethod: 'template-v2',
          confidenceThreshold: template.metadata.confidenceThreshold
        });
        
        // NEU: Übertrage Keywords auch in Summary-DB (für Side Panel Anzeige)
        try {
          await saveSummaryToDatabase(lectureId, {
            summary: summaryData.summary,
            headings: summaryData.headings || [],
            tableOfContents: summaryData.tableOfContents || [],
            lectureKeywords: keywords,
            version: summaryData.version || 'v2'
          });
        } catch (syncError) {
          console.warn(`[KEYWORDS-V2] Warnung: Summary-DB für ${lectureId} konnte nicht aktualisiert werden:`, syncError.message);
        }
        
        // Aktualisiere Vokabular für nächste Iteration
        keywords.forEach(kw => {
          if (!existingVocabulary.includes(kw.term)) {
            existingVocabulary.push(kw.term);
          }
          frequencyMap[kw.term] = (frequencyMap[kw.term] || 0) + 1;
        });
        
        const newKws = keywords.filter(k => k.matchType === 'new');
        
        results.push({
          lectureId,
          keywordsCount: keywords.length,
          newKeywordsCount: newKws.length,
          success: true
        });
        
        processed++;
        
        // Rate Limiting: 200ms zwischen Requests
        if (i < lectureIdsToProcess.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
        
      } catch (error) {
        console.error(`[KEYWORDS-V2] ${i+1}/${lectureIdsToProcess.length} ${lectureId}: FEHLER:`, error.message);
        results.push({
          lectureId,
          error: error.message,
          success: false
        });
        errors++;
      }
    }
    
    // 7. Optional: Synonym-Konsolidierung
    let consolidatedCount = 0;
    if (consolidateSynonyms && processed > 0) {
      keywordsDB = await loadKeywordsDatabase();
      consolidatedCount = await consolidateSynonymsInKeywords(keywordsDB, synonymMap);
      
      if (consolidatedCount > 0) {
        await saveCompleteKeywordsDatabase(keywordsDB);
      }
    }
    
    // 8. Aktualisiere themes-database.json für Frontend-Kompatibilität
    if (processed > 0) {
      try {
        await updateThemesDatabaseFromTemplate(template);
      } catch (error) {
        console.error('[KEYWORDS-V2] Fehler beim Aktualisieren der themes-database:', error);
      }
    }
    
    // 9. Statistiken
    const finalStats = {
      totalRequested: lectureIdsToProcess.length,
      processed: processed,
      skipped: skipped,
      errors: errors,
      newVocabularySize: existingVocabulary.length,
      synonymsConsolidated: consolidatedCount
    };
    
    
    res.json({
      success: true,
      stats: finalStats,
      results: results
    });
    
  } catch (error) {
    console.error('[KEYWORDS-V2] Fehler:', error);
    res.status(500).json({ 
      error: error.message,
      stack: error.stack 
    });
  }
});

// API: Template-Info abrufen
app.get('/api/keywords-template-info', async (req, res) => {
  try {
    const template = await loadThemesKeywordsTemplate();
    const { vocabulary, themeMapping, synonymMap } = extractVocabularyFromTemplate(template);
    
    res.json({
      metadata: template.metadata,
      stats: {
        totalThemes: Object.keys(template.themes).length,
        totalKeywords: vocabulary.length,
        synonymGroups: Object.keys(synonymMap).length,
        confidenceThreshold: template.metadata.confidenceThreshold
      },
      themes: Object.keys(template.themes),
      providers: {
        gemini: { available: !!process.env.GEMINI_API_KEY, rateLimited: isProviderRateLimited('gemini') },
        openai: { available: !!process.env.OPENAI_API_KEY, rateLimited: isProviderRateLimited('openai') },
        claude: { available: !!process.env.CLAUDE_API_KEY, rateLimited: isProviderRateLimited('claude') }
      }
    });
  } catch (error) {
    console.error('[TEMPLATE-INFO] Fehler:', error);
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
    return {};
  }
}

// Speichere Themes-Datenbank
async function saveThemesDatabase(themesDB) {
  try {
    await fs.writeFile(THEMES_DB_FILE, JSON.stringify(themesDB, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('[THEMES-DB] Fehler beim Speichern:', error);
    return false;
  }
}

// Funktion: Themen aus allen Keywords mit LLM generieren
async function generateThemesFromKeywords(targetThemeCount = 30) {
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  // Bevorzuge OpenAI für Themen-Generierung (stabiler JSON, höheres Token-Limit)
  let provider;
  try {
    // Versuche zuerst OpenAI (falls verfügbar)
    try {
      const { OpenAIProvider } = require('./llm-providers');
      const openaiProvider = new OpenAIProvider();
      if (openaiProvider.isAvailable()) {
        provider = openaiProvider;
      }
    } catch (e) {
      // OpenAI nicht verfügbar, verwende configurierten Provider
    }
    
    if (!provider) {
      provider = getProviderForTask('themes');
    }
  } catch (error) {
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
  
  // Sortiere nach Häufigkeit und nimm die Top 1000 (erweitert von 300)
  const topKeywords = Object.entries(keywordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 1000)
    .map(([term, freq]) => `${term} (${freq}x)`)
    .join(', ');
  
  
  const prompt = `Analysiere die folgenden Schlagwörter aus Rudolf Steiners Vortragswerk und erstelle genau ${targetThemeCount} übergeordnete Themenbereiche.

HÄUFIGSTE SCHLAGWÖRTER (Top 1000):
${topKeywords}

AUFGABE - ZWEIPHASIGER ANSATZ:
Erstelle NUR die THEMEN-NAMEN und BESCHREIBUNGEN.
Die Keyword-Zuordnung erfolgt später automatisch per Batch.

ANFORDERUNGEN:
- Genau ${targetThemeCount} Themenbereiche
- Themen sollten die Hauptgebiete der Anthroposophie abdecken
- Deutsche Namen (z.B. "Erkenntnistheorie", "Christologie und Evangelien", "Soziale Dreigliederung")
- Kurze prägnante Beschreibung pro Thema (1 Satz)
- Themen sollten ausgewogen und komplementär sein
- Decke das gesamte Spektrum ab

BEISPIELE FÜR THEMEN:
- Erkenntnistheorie und Methodologie
- Christologie und Evangelien
- Karma und Reinkarnation
- Soziale Dreigliederung und Wirtschaft
- Pädagogik und Erziehung
- Anthroposophische Medizin und Heilkunst
- Kosmologie und Planetensphären
- Mysterien und Einweihung
- Deutsche Mystik und Geistesgeschichte
- Goetheanismus und Naturwissenschaft
- Kunst und Eurythmie
- Menschenkunde und Wesensglieder
[... weitere]

ANTWORT-FORMAT (JSON) - NUR Namen + Beschreibung, KEINE Keywords-Liste!
{
  "Erkenntnistheorie und Methodologie": {
    "description": "Theoretische Grundlagen der Geisteswissenschaft, Erkenntnismethoden, Goetheanismus"
  },
  "Christologie und Evangelien": {
    "description": "Christuswesen, Mysterium von Golgatha, Evangelien-Auslegung"
  },
  ...
}

WICHTIG: Gib KEINE keywords-Arrays zurück, nur description!
Die Keywords werden später automatisch zugeordnet.

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.`;

  try {
    
    // Verwende Provider-Abstraction
    // Phase 1: Nur Themen-Namen (klein, passt in alle Provider)
    let responseText = await provider.generateCompletion(prompt, {
      maxTokens: 8192,
      temperature: 0.3
      // Kein model-Parameter - jeder Provider nutzt sein Default-Modell
    });
    
    
    // DEBUG: Speichere rohe Antwort für Analyse
    const fs = require('fs');
    fs.writeFileSync('debug-gemini-response.txt', responseText);
    
    // Entferne Markdown Code-Blöcke falls vorhanden
    responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    
    // Robustes JSON Parsing mit Fehlerbehandlung
    let themes;
    try {
      themes = JSON.parse(responseText);
    } catch (parseError) {
      
      // Strategie 1: Finde das JSON-Objekt im Text
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          themes = JSON.parse(jsonMatch[0]);
        } catch (e2) {
          throw parseError; // Original Error werfen
        }
      } else {
        throw parseError;
      }
    }
    
    
    // Initialisiere leere Keywords-Arrays (werden in Phase 2 per Batch gefüllt)
    for (const [themeName, themeData] of Object.entries(themes)) {
      // Phase 1 sollte KEINE Keywords zurückgeben, aber falls doch...
      if (!themeData.keywords || !Array.isArray(themeData.keywords)) {
        themeData.keywords = [];
      } else if (themeData.keywords.length > 0) {
        // Falls doch Keywords da sind, normalisiere sie
        const keywordObjects = themeData.keywords.map(kw => 
          typeof kw === 'string' ? { term: kw } : kw
        );
        const normalized = normalizeKeywords(keywordObjects);
        themeData.keywords = normalized.map(kw => kw.term);
      }
    }
    
    
    return themes;

  } catch (error) {
    console.error(`[THEMES-GEN] Fehler bei ${provider?.name || 'LLM'} API:`, error);
    return generateFallbackThemes();
  }
}

// Fallback: Einfache Themengruppierung (ohne KI)
function generateFallbackThemes() {
  
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

// ============================================================================
// BATCH-ZUORDNUNG: Alle Keywords zu bestehenden Themen zuordnen
// ============================================================================

/**
 * Ordnet ALLE Keywords aus der keywords-database den generierten Themen zu
 * Verwendet Batch-Verarbeitung für Skalierbarkeit (500 Keywords/Batch)
 */
async function assignAllKeywordsToThemes(themesDB, keywordsDB) {
  const BATCH_SIZE = 200; // Reduziert von 500 - passt besser in Gemini's 4k Token-Limit
  
  const themeNames = Object.keys(themesDB);
  
  // Sammle ALLE unique Keywords
  const allKeywords = new Set();
  const keywordFrequency = {};
  
  Object.values(keywordsDB).forEach(lecture => {
    if (lecture.keywords && Array.isArray(lecture.keywords)) {
      lecture.keywords.forEach(kw => {
        const term = kw.term.trim();
        allKeywords.add(term);
        keywordFrequency[term] = (keywordFrequency[term] || 0) + 1;
      });
    }
  });
  
  const allKeywordsArray = Array.from(allKeywords);
  
  // Filtere bereits zugeordnete Keywords
  const alreadyAssignedSet = new Set();
  Object.values(themesDB).forEach(theme => {
    if (theme.keywords && Array.isArray(theme.keywords)) {
      theme.keywords.forEach(kw => {
        const term = typeof kw === 'string' ? kw : kw.term;
        alreadyAssignedSet.add(term.toLowerCase().trim());
      });
    }
  });
  
  const unassignedKeywords = allKeywordsArray.filter(kw => 
    !alreadyAssignedSet.has(kw.toLowerCase().trim())
  );
  
  
  if (unassignedKeywords.length === 0) {
    return { assigned: 0, total: allKeywordsArray.length };
  }
  
  // Hole Provider
  let provider;
  try {
    provider = getProviderForTask('batch');
  } catch (error) {
    console.error('[BATCH-ASSIGN] Kein Provider verfügbar:', error.message);
    return { assigned: 0, total: allKeywordsArray.length, error: error.message };
  }
  
  // Erstelle Batches
  const batches = [];
  for (let i = 0; i < unassignedKeywords.length; i += BATCH_SIZE) {
    batches.push(unassignedKeywords.slice(i, i + BATCH_SIZE));
  }
  
  
  // Sammle Zuordnungen
  const assignments = {};
  
  // Verarbeite jeden Batch
  for (let batchIdx = 0; batchIdx < batches.length; batchIdx++) {
    const batch = batches[batchIdx];
    const batchNum = batchIdx + 1;
    
    
    // Keywords mit Häufigkeit
    const keywordsWithFreq = batch.map(kw => {
      const freq = keywordFrequency[kw] || 1;
      return `${kw} (${freq}x)`;
    }).join(', ');
    
    const prompt = `Ordne diese ${batch.length} Keywords aus Rudolf Steiners Werk jeweils EINEM der folgenden ${themeNames.length} Themen zu.

VERFÜGBARE THEMEN:
${themeNames.map((name, idx) => `${idx + 1}. ${name}`).join('\n')}

KEYWORDS (mit Häufigkeit):
${keywordsWithFreq}

REGELN:
1. Jedes Keyword genau EINEM Thema zuordnen
2. Wähle das thematisch am besten passende Thema
3. Bei Unsicherheit: Wähle das allgemeinste/breiteste Thema
4. Häufige Keywords (hohe Zahl) sind wichtiger → sorgfältig zuordnen

AUSGABE als JSON-Objekt:
{
  "keyword1": "Themenname",
  "keyword2": "Themenname",
  ...
}

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.`;

    try {
      const responseText = await provider.generateCompletion(prompt, {
        maxTokens: 8192, // Erhöht von 4096 für größere Batches
        temperature: 0.3
      });
      
      // Parse JSON
      let cleanedResponse = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      const batchAssignments = JSON.parse(cleanedResponse);
      
      // Merge
      Object.assign(assignments, batchAssignments);
      
      const progress = ((batchNum / batches.length) * 100).toFixed(1);
      
      // Pause zwischen Batches
      if (batchNum < batches.length) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
    } catch (error) {
      console.error(`[BATCH-ASSIGN] Fehler in Batch ${batchNum}:`, error.message);
      continue;
    }
  }
  
  
  // Merge mit bestehenden Themen
  const updatedThemesDB = { ...themesDB };
  
  for (const [keyword, themeName] of Object.entries(assignments)) {
    if (updatedThemesDB[themeName]) {
      if (!updatedThemesDB[themeName].keywords) {
        updatedThemesDB[themeName].keywords = [];
      }
      // Füge hinzu wenn noch nicht vorhanden
      const existingTerms = updatedThemesDB[themeName].keywords.map(kw => 
        typeof kw === 'string' ? kw : kw.term
      );
      if (!existingTerms.includes(keyword)) {
        updatedThemesDB[themeName].keywords.push(keyword);
      }
    }
  }
  
  // Speichere erweiterte Themes-Database
  await saveThemesDatabase(updatedThemesDB);
  
  return {
    assigned: Object.keys(assignments).length,
    total: allKeywordsArray.length,
    coverage: (((alreadyAssignedSet.size + Object.keys(assignments).length) / allKeywordsArray.length) * 100).toFixed(1),
    provider: provider.name
  };
}

// API: Batch-Zuordnung aller Keywords zu Themen
app.post('/api/themes/assign-all-keywords', async (req, res) => {
  try {
    
    // Lade Themen und Keywords
    const themesDB = await loadThemesDatabase();
    if (!themesDB || Object.keys(themesDB).length === 0) {
      return res.status(400).json({ 
        error: 'Keine Themen gefunden. Bitte zuerst Themen generieren.' 
      });
    }
    
    const keywordsDB = await loadKeywordsDatabase();
    
    // Führe Batch-Zuordnung durch
    const result = await assignAllKeywordsToThemes(themesDB, keywordsDB);
    
    if (result.error) {
      return res.status(500).json({ error: result.error });
    }
    
    res.json({
      success: true,
      message: 'Batch-Zuordnung erfolgreich abgeschlossen',
      stats: result
    });
    
  } catch (error) {
    console.error('[BATCH-ASSIGN-API] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Themen generieren
app.post('/api/generate-themes', async (req, res) => {
  try {
    const { targetThemeCount = 30 } = req.body;
    
    
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

// API: Cluster löschen
app.post('/api/themes/delete-cluster', async (req, res) => {
  try {
    const { clusterName } = req.body;
    
    if (!clusterName) {
      return res.status(400).json({ error: 'clusterName ist erforderlich' });
    }
    
    
    // Lade themes-database
    const themesDB = await loadThemesDatabase();
    
    if (!themesDB[clusterName]) {
      return res.status(404).json({ error: `Cluster "${clusterName}" nicht gefunden` });
    }
    
    const keywordCount = themesDB[clusterName].keywords?.length || 0;
    
    // Lösche Cluster
    delete themesDB[clusterName];
    
    // Speichere
    await saveThemesDatabase(themesDB);
    
    
    res.json({ 
      success: true, 
      message: `Cluster "${clusterName}" gelöscht`,
      keywordsWereInCluster: keywordCount
    });
    
  } catch (error) {
    console.error('[DELETE-CLUSTER] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Cluster zusammenführen
app.post('/api/themes/merge-clusters', async (req, res) => {
  try {
    const { sourceCluster, targetCluster } = req.body;
    
    if (!sourceCluster || !targetCluster) {
      return res.status(400).json({ error: 'sourceCluster und targetCluster sind erforderlich' });
    }
    
    if (sourceCluster === targetCluster) {
      return res.status(400).json({ error: 'Quell- und Ziel-Cluster müssen unterschiedlich sein' });
    }
    
    
    // Lade themes-database
    const themesDB = await loadThemesDatabase();
    
    if (!themesDB[sourceCluster]) {
      return res.status(404).json({ error: `Quell-Cluster "${sourceCluster}" nicht gefunden` });
    }
    
    if (!themesDB[targetCluster]) {
      return res.status(404).json({ error: `Ziel-Cluster "${targetCluster}" nicht gefunden` });
    }
    
    // Merge Keywords
    const sourceKeywords = themesDB[sourceCluster].keywords || [];
    const targetKeywords = themesDB[targetCluster].keywords || [];
    
    // Füge Quell-Keywords zum Ziel hinzu (ohne Duplikate)
    const mergedKeywords = [...new Set([...targetKeywords, ...sourceKeywords])];
    themesDB[targetCluster].keywords = mergedKeywords;
    
    // Merge Beschreibungen
    if (themesDB[sourceCluster].description && themesDB[targetCluster].description) {
      themesDB[targetCluster].description = `${themesDB[targetCluster].description}; ${themesDB[sourceCluster].description}`;
    } else if (themesDB[sourceCluster].description) {
      themesDB[targetCluster].description = themesDB[sourceCluster].description;
    }
    
    // Lösche Quell-Cluster
    delete themesDB[sourceCluster];
    
    // Speichere
    await saveThemesDatabase(themesDB);
    
    
    res.json({ 
      success: true, 
      message: `Cluster "${sourceCluster}" wurde in "${targetCluster}" zusammengeführt`,
      mergedKeywords: sourceKeywords.length,
      totalKeywordsInTarget: mergedKeywords.length
    });
    
  } catch (error) {
    console.error('[MERGE-CLUSTER] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Themes-Datenbank abrufen (nutzt themes-database.json)
app.get('/api/themes-database', async (req, res) => {
  try {
    // Versuche zuerst themes-database.json zu laden (neue Struktur)
    const themesPath = path.join(__dirname, 'themes-database.json');
    if (fsSync.existsSync(themesPath)) {
      const data = JSON.parse(fsSync.readFileSync(themesPath, 'utf8'));
      return res.json(data);
    }
    
    // Fallback auf alte thematic-clusters.json
    const clustersPath = path.join(__dirname, 'thematic-clusters.json');
    if (fsSync.existsSync(clustersPath)) {
      const data = JSON.parse(fsSync.readFileSync(clustersPath, 'utf8'));
      // Extrahiere nur die Cluster selbst (nicht die Metadaten)
      const clusters = data.clusters || data;
      res.json(clusters);
      return;
    }
    
    // Fallback: alte themes-database.json
    const themesDB = await loadThemesDatabase();
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
    }
  }
  
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
  
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
  
  // Aktiviere konsolidierte Datenbank
  const consolidatedDB = await fs.readFile(consolidatedFile, 'utf-8');
  
  // Validiere dass konsolidierte DB nicht leer ist
  const parsedDB = JSON.parse(consolidatedDB);
  if (Object.keys(parsedDB).length === 0) {
    throw new Error('Konsolidierte Datenbank ist leer - Aktivierung abgebrochen');
  }
  
  await fs.writeFile(KEYWORDS_DB_FILE, consolidatedDB);
  
  return {
    preConsolidationFile,
    activeFile: KEYWORDS_DB_FILE
  };
}

app.post('/api/consolidate-keywords-preview', async (req, res) => {
  try {
    const { factor } = req.body;
    
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
    return {};
  }
}

// Speichere Themensuchen-Cache-Datenbank
async function saveThematicSearchDatabase(thematicDB) {
  try {
    await fs.writeFile(THEMATIC_SEARCH_DB_FILE, JSON.stringify(thematicDB, null, 2), 'utf8');
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

// Synchronisiere concepts.json mit concepts-thematic-search.json
async function synchronizeKeywordSystems() {
  try {
    
    const keywordsFile = path.join(__dirname, 'concepts.json');
    const keywordThematicDB = await loadKeywordThematicDatabase();
    
    let allKeywords = [];
    try {
      const fileContent = await fs.readFile(keywordsFile, 'utf8');
      allKeywords = JSON.parse(fileContent);
    } catch (error) {
      return;
    }
    
    let syncCount = 0;
    
    // Prüfe jedes Keyword in keywords.json
    for (const keyword of allKeywords) {
      const cacheKey = `keyword_${keyword.keyword.toLowerCase().trim()}_allgemein_30`;
      
      // Wenn Keyword in keywords.json existiert, aber nicht im Cache
      if (!keywordThematicDB[cacheKey] && keyword.hasDetailedAnalysis) {
        
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
    } else {
    }
    
  } catch (error) {
    console.error('[SYNC] Fehler bei Synchronisation:', error);
  }
}

// Generiere Keyword-spezifische Analyse
// ============================================================================
// KEYWORD ANALYSIS - Für Thematische Suchen (Tab Themen)
// ============================================================================
// Hinweis: Für Concept-Einträge (Tab Index) wird generateConceptAnalysis verwendet!

async function generateKeywordAnalysis(query, results, depth = 'allgemein') {
  
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  let provider;
  try {
    provider = getProviderForTask('analysis');
  } catch (error) {
    return generateFallbackKeywordAnalysis(query, results);
  }
  
  // Verwende alle übergebenen Ergebnisse, aber begrenze auf maximal 100 für Token-Limit
  // Mit optimierter Kürzung sollte das Token-Limit eingehalten werden
  const MAX_RESULTS_FOR_ANALYSIS = 100;
  const topResults = results.slice(0, Math.min(results.length, MAX_RESULTS_FOR_ANALYSIS));
  
  if (results.length > MAX_RESULTS_FOR_ANALYSIS) {
  }

  // Hilfsfunktion: Kürze Textpassage auf maximal 400 Zeichen (optimiert für mehr Passagen)
  const truncateContent = (content, maxLength = 400) => {
    if (!content || content.length <= maxLength) {
      return content;
    }
    // Versuche bei Satzende zu kürzen
    const truncated = content.substring(0, maxLength);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastExclamation = truncated.lastIndexOf('!');
    const lastQuestion = truncated.lastIndexOf('?');
    const lastSentenceEnd = Math.max(lastPeriod, lastExclamation, lastQuestion);
    
    if (lastSentenceEnd > maxLength * 0.7) {
      // Wenn Satzende gefunden wurde (nicht zu weit am Anfang), kürze dort
      return truncated.substring(0, lastSentenceEnd + 1) + '...';
    }
    // Sonst kürze einfach und füge ... hinzu
    return truncated + '...';
  };
  
  const contextText = topResults
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      // Kürze jede Textpassage auf maximal 500 Zeichen
      const truncatedContent = truncateContent(result.content, 500);
      return `[${refId}] ${result.fileName || result.title}\n${truncatedContent}`;
    })
    .join('\n\n---\n\n');
    
  const availableRefs = topResults.map(r => `${r.ID}:${r.index}`).join(', ');
  
  
  const maxTokens = {
    'allgemein': 8000,    // Erhöht von 4000 auf 8000
    'genau': 12000,       // Erhöht von 6000 auf 12000  
    'ausführlich': 16000  // Erhöht von 8000 auf 16000
  };

  // Erzwinge immer die ausführliche Tiefe unabhängig vom übergebenen depth
  const effectiveDepth = 'ausführlich';

  const prompt = `Analysiere die folgenden Textstellen zum Schlagwort: "${query}"

ANALYSE-TIEFE: ${effectiveDepth}

QUELLENANGABEN:
- Format für VORTRÄGE: (GA###/Y:index) - z.B. (GA052/7:n5x6ru) oder (GA068a/7:p5fg67)
- Format für BÜCHER: (GA###:^index) - z.B. (GA013:^xba9rk) oder (GA007:^iyj24c)
- WICHTIG: Bücher haben KEINEN Slash nach der GA-Nummer, nur einen Doppelpunkt!
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
- Zitate: "Text" (GA###/Y:index) für Vorträge oder "Text" (GA###:^index) für Bücher
- Überschriften: ## Überschrift
- Nutze die ${topResults.length} verfügbaren Textstellen ausführlich (von insgesamt ${results.length} gefundenen)

TEXTPASSAGEN:
${contextText}

ANALYSE:`;

  try {
    
    // Verwende Provider-Abstraction
    const analysisText = await provider.generateCompletion(prompt, {
      maxTokens: maxTokens[effectiveDepth] || 8000,
      temperature: 0.7
    });
    
    
    return analysisText.trim();
    
  } catch (error) {
    console.error(`[KEYWORD-ANALYSIS] ${provider.name} API Fehler:`, error.message);
    return generateFallbackKeywordAnalysis(query, results);
  }
}

// ============================================================================
// CONCEPT ANALYSIS - Speziell für Index-Tab Einträge
// ============================================================================

async function generateConceptAnalysis(query, results) {
  
  // Hole passenden LLM-Provider (mit Fallback-Chain)
  let provider;
  try {
    provider = getProviderForTask('analysis');
  } catch (error) {
    return generateFallbackConceptAnalysis(query, results);
  }
  
  // WICHTIG: Begrenze auf maximal 100 Textstellen um Token-Limit nicht zu überschreiten
  // Mit optimierter Kürzung sollte das Token-Limit eingehalten werden
  const MAX_RESULTS = 100; // Erhöht von 30 auf 100
  const topResults = results.slice(0, Math.min(results.length, MAX_RESULTS));
  
  if (results.length > MAX_RESULTS) {
  }

  // Hilfsfunktion: Kürze Textpassage auf maximal 400 Zeichen (optimiert für mehr Passagen)
  const truncateContent = (content, maxLength = 400) => {
    if (!content || content.length <= maxLength) {
      return content;
    }
    // Versuche bei Satzende zu kürzen
    const truncated = content.substring(0, maxLength);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastExclamation = truncated.lastIndexOf('!');
    const lastQuestion = truncated.lastIndexOf('?');
    const lastSentenceEnd = Math.max(lastPeriod, lastExclamation, lastQuestion);
    
    if (lastSentenceEnd > maxLength * 0.7) {
      // Wenn Satzende gefunden wurde (nicht zu weit am Anfang), kürze dort
      return truncated.substring(0, lastSentenceEnd + 1) + '...';
    }
    // Sonst kürze einfach und füge ... hinzu
    return truncated + '...';
  };
  
  const contextText = topResults
    .map((result, index) => {
      const refId = `${result.ID}:${result.index}`;
      // Kürze jede Textpassage auf maximal 500 Zeichen
      const truncatedContent = truncateContent(result.content, 500);
      return `[${refId}] ${result.fileName || result.title}\n${truncatedContent}`;
    })
    .join('\n\n---\n\n');
    
  const availableRefs = topResults.map(r => `${r.ID}:${r.index}`).join(', ');
  

  const prompt = `Erstelle einen prägnanten Lexikon-Eintrag zum Begriff: "${query}"

🚨 KRITISCHE REGEL - KEINE META-SPRACHE:
❌ NIEMALS: "Rudolf Steiner beschreibt...", "Steiner erklärt...", "Im Vortrag wird..."
❌ NIEMALS: "Nach Steiner...", "Steiner sagt...", "Der Text behandelt..."
❌ NIEMALS: Extra-Überschrift mit dem Begriff selbst
❌ NIEMALS: Einleitende Zusammenfassung wie "Der Begriff XY bezeichnet..."

✅ RICHTIG: Beginne DIREKT mit den inhaltlichen Aussagen
✅ RICHTIG: Schreibe wie in einem Lexikon - sachlich, direkt, über die Sache selbst

BEISPIEL FALSCH: 
"**Karma**
Rudolf Steiner beschreibt Karma als..."

BEISPIEL RICHTIG:
"Das Gesetz von Ursache und Wirkung durchzieht alle Inkarnationen..." (GA120/5:abc123)

---

VORGEHEN:

1. FINDE alle Textstellen zu "${query}" in den folgenden Passagen

2. IDENTIFIZIERE relevante Textstellen mit inhaltlichen Aussagen über "${query}"
   - Fokus auf Definitionen, Eigenschaften, Funktionen, Zusammenhänge
   - Überspringe bloße Erwähnungen ohne Erklärung

3. INHALTLICHES DEDUPE - Schließe ähnliche Aussagen aus
   - Wenn mehrere Stellen das Gleiche sagen: Wähle die prägnanteste
   - Vermeide Wiederholungen des gleichen Gedankens

4. ZUSAMMENFASSENDE DARSTELLUNG:

   ❌ KEINE extra Überschrift (nicht "**${query}**" oder "## ${query}")
   ❌ KEINE einleitende Zusammenfassung
   ❌ KEINE Meta-Sprache (siehe oben)
   
   ✅ Beginne DIREKT mit der ersten inhaltlichen Aussage
   ✅ Bei längeren Darstellungen: Gliedere mit #### Zwischenüberschriften (OHNE Nummerierung)
   ✅ Verwende direkte Zitate in "Anführungszeichen" mit Quellenangaben
   ✅ Zitate dürfen gekürzt sein (mit ...)
   ✅ Minimaler erläuternder Text - nur zur Verbindung der Zitate
   ✅ Schreibe sachlich wie in einem Lexikon - DIREKT über die Sache

5. QUELLENLINKS am Ende:
   - Liste NUR weitere RELEVANTE Quellen auf (zusätzlich zu den bereits zitierten)
   - Format: "**Weitere Quellen:** GA###/Y:index, GA###/Y:index, ..."
   - WICHTIG: OHNE Klammern um die einzelnen Quellenangaben!
   - Nur wenn es tatsächlich weitere relevante Quellen gibt

FORMATIERUNG:
- **Fette wenige, wichtige Wörter** (sparsam einsetzen)
- Zitate: "Text" (GA###/Y:index) oder "Text" (GA###a/Y:index)
- Zwischenüberschriften: #### Überschrift (ohne Nummerierung)
- KEINE Leerzeichen um Klammern bei Quellenangaben

QUELLENANGABEN:
- Format: (GA###/Y:index) - z.B. (GA052/7:n5x6ru) oder (GA068a/7:p5fg67)
- Verfügbare Referenzen: ${availableRefs}

TEXTPASSAGEN ZU "${query}":
${contextText}

LEXIKON-EINTRAG (beginne DIREKT mit Inhalt, OHNE Überschrift):`;

  try {
    
    const analysisText = await provider.generateCompletion(prompt, {
      maxTokens: 8000,
      temperature: 0.7
    });
    
    
    return analysisText.trim();
    
  } catch (error) {
    console.error(`[CONCEPT-ANALYSIS] ${provider.name} API Fehler:`, error.message);
    
    // Prüfe ob es ein Token-Limit-Fehler war
    if (error.message.includes('too long') || error.message.includes('maximum')) {
      console.error(`[CONCEPT-ANALYSIS] ⚠️ Token-Limit überschritten trotz Begrenzung auf ${topResults.length} Textstellen`);
      return generateFallbackConceptAnalysis(query, results, 'token-limit');
    }
    
    // Prüfe ob es ein API-Limit-Fehler war
    if (error.message.includes('usage limits') || error.message.includes('Nutzungslimit')) {
      console.error(`[CONCEPT-ANALYSIS] ⚠️ API-Nutzungslimit erreicht`);
      return generateFallbackConceptAnalysis(query, results, 'api-limit', error.message);
    }
    
    return generateFallbackConceptAnalysis(query, results, 'api-error', error.message);
  }
}

// Fallback-Analyse für Concepts
function generateFallbackConceptAnalysis(query, results, reason = 'no-api-key', errorMessage = '') {
  if (reason === 'token-limit') {
    return `⚠️ Der Begriff "${query}" kommt zu häufig vor (${results.length} Textstellen).

Eine automatische Analyse würde das Token-Limit überschreiten. Bitte verwenden Sie eine spezifischere Suchanfrage oder kontaktieren Sie den Administrator.

**Verfügbare Quellen (erste 20):**
${results.slice(0, 20).map(r => `${r.ID}:${r.index}`).join(', ')}`;
  }
  
  if (reason === 'api-limit') {
    const limitInfo = errorMessage.includes('regain access') 
      ? errorMessage.match(/regain access on ([^.]+)/)?.[1] || ''
      : '';
    return `⚠️ API-Nutzungslimit erreicht

Der Begriff "${query}" konnte nicht automatisch analysiert werden, da das API-Nutzungslimit erreicht wurde.

${limitInfo ? `**Zugriff wird wiederhergestellt:** ${limitInfo} UTC` : ''}

Gefundene Textstellen: ${results.length}

**Verfügbare Quellen:**
${results.slice(0, 10).map(r => `${r.ID}:${r.index}`).join(', ')}`;
  }
  
  if (reason === 'api-error' && errorMessage) {
    return `⚠️ API-Fehler bei der Analyse

Der Begriff "${query}" konnte nicht automatisch analysiert werden.

**Fehler:** ${errorMessage}

Gefundene Textstellen: ${results.length}

**Verfügbare Quellen:**
${results.slice(0, 10).map(r => `${r.ID}:${r.index}`).join(', ')}`;
  }
  
  return `Automatische Analyse nicht verfügbar (kein API-Schlüssel konfiguriert). 

Gefundene Textstellen: ${results.length}

Für eine detaillierte KI-Analyse des Begriffs "${query}" benötigt das System einen API-Schlüssel in der .env Datei.

**Verfügbare Quellen:**
${results.slice(0, 10).map(r => `${r.ID}:${r.index}`).join(', ')}`;
}

// Fallback-Analyse für Keywords (Themensuche)
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

// API: Themensuche löschen
app.post('/api/delete-thematic-search', async (req, res) => {
  try {
    const { cacheKey } = req.body;
    
    if (!cacheKey) {
      return res.status(400).json({ error: 'Cache-Key erforderlich' });
    }
    
    
    // Lade Datenbank
    const thematicDB = await loadThematicSearchDatabase();
    
    // Prüfe ob Key existiert
    if (!thematicDB[cacheKey]) {
      return res.status(404).json({ error: 'Themensuche nicht gefunden' });
    }
    
    // Lösche Eintrag
    delete thematicDB[cacheKey];
    
    // Speichere aktualisierte Datenbank
    await saveThematicSearchDatabase(thematicDB);
    
    
    res.json({
      success: true,
      message: 'Themensuche erfolgreich gelöscht',
      deletedKey: cacheKey
    });
    
  } catch (error) {
    console.error('[DELETE-THEMATIC] Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// QUOTES DATABASE (Zitate-Verwaltung)
// ============================================================================

// Lade Zitate-Datenbank
async function loadQuotesDatabase() {
  try {
    const data = await fs.readFile(QUOTES_DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return { quotes: [] };
  }
}

// Speichere Zitate-Datenbank
async function saveQuotesDatabase(quotesDB) {
  try {
    await fs.writeFile(QUOTES_DB_FILE, JSON.stringify(quotesDB, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('[QUOTES] Fehler beim Speichern:', error);
    throw error;
  }
}

// API: Alle Zitate abrufen
app.get('/api/quotes', async (req, res) => {
  try {
    const quotesDB = await loadQuotesDatabase();
    res.json(quotesDB);
  } catch (error) {
    console.error('[QUOTES] Fehler beim Laden:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Neues Zitat hinzufügen
app.post('/api/quotes/add', async (req, res) => {
  try {
    const { text, lectureId, paragraphIndex, date } = req.body;
    
    if (!text || !lectureId || !paragraphIndex) {
      return res.status(400).json({ error: 'Text, lectureId und paragraphIndex erforderlich' });
    }
    
    const quotesDB = await loadQuotesDatabase();
    
    // Erstelle neues Zitat
    const newQuote = {
      id: Date.now().toString(),
      text: text,
      lectureId: lectureId,
      paragraphIndex: paragraphIndex,
      addedAt: new Date().toISOString(),
      isActive: false // Standardmäßig nicht im Popup aktiv
    };
    
    // Füge Datum nur hinzu, wenn es vorhanden ist (nicht das aktuelle Datum als Fallback)
    if (date) {
      newQuote.date = date;
    }
    
    quotesDB.quotes.push(newQuote);
    
    await saveQuotesDatabase(quotesDB);
    
    
    res.json({
      success: true,
      quote: newQuote,
      message: 'Zitat erfolgreich hinzugefügt'
    });
    
  } catch (error) {
    console.error('[QUOTES] Fehler beim Hinzufügen:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Zitat löschen
app.post('/api/quotes/delete', async (req, res) => {
  try {
    const { quoteId } = req.body;
    
    if (!quoteId) {
      return res.status(400).json({ error: 'Quote ID erforderlich' });
    }
    
    const quotesDB = await loadQuotesDatabase();
    
    const beforeLength = quotesDB.quotes.length;
    quotesDB.quotes = quotesDB.quotes.filter(q => q.id !== quoteId);
    const afterLength = quotesDB.quotes.length;
    
    if (beforeLength === afterLength) {
      return res.status(404).json({ error: 'Zitat nicht gefunden' });
    }
    
    await saveQuotesDatabase(quotesDB);
    
    
    res.json({
      success: true,
      message: 'Zitat erfolgreich gelöscht'
    });
    
  } catch (error) {
    console.error('[QUOTES] Fehler beim Löschen:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Thematische Suchanfrage löschen
app.post('/api/thematic-search/delete', async (req, res) => {
  try {
    const { cacheKey } = req.body;
    
    if (!cacheKey) {
      return res.status(400).json({ error: 'Cache-Key erforderlich' });
    }
    
    // Lade Thematic-Search-Datenbank
    const thematicDB = await loadThematicSearchDatabase();
    
    // Prüfe ob Key existiert
    if (!thematicDB[cacheKey]) {
      return res.status(404).json({ 
        success: false,
        error: 'Suchanfrage nicht in Datenbank gefunden' 
      });
    }
    
    // Speichere Query für Logging
    const deletedQuery = thematicDB[cacheKey].query || 'unbekannt';
    
    // Lösche den Eintrag
    delete thematicDB[cacheKey];
    
    // Speichere aktualisierte Datenbank
    await saveThematicSearchDatabase(thematicDB);
    
    
    res.json({
      success: true,
      message: 'Suchanfrage erfolgreich gelöscht',
      deletedQuery: deletedQuery
    });
    
  } catch (error) {
    console.error('[THEMATIC-DELETE] Fehler beim Löschen:', error);
    res.status(500).json({ 
      success: false,
      error: error.message 
    });
  }
});

// API: Zitat aktivieren/deaktivieren für Popup
app.post('/api/quotes/toggle-active', async (req, res) => {
  try {
    const { quoteId, isActive } = req.body;
    
    if (!quoteId) {
      return res.status(400).json({ error: 'Quote ID erforderlich' });
    }
    
    const quotesDB = await loadQuotesDatabase();
    
    const quote = quotesDB.quotes.find(q => q.id === quoteId);
    if (!quote) {
      return res.status(404).json({ error: 'Zitat nicht gefunden' });
    }
    
    quote.isActive = isActive;
    
    await saveQuotesDatabase(quotesDB);
    
    
    res.json({
      success: true,
      quote: quote,
      message: `Zitat ${isActive ? 'aktiviert' : 'deaktiviert'}`
    });
    
  } catch (error) {
    console.error('[QUOTES] Fehler beim Toggle:', error);
    res.status(500).json({ error: error.message });
  }
});

// API: Zitat aktualisieren
app.post('/api/quotes/update', async (req, res) => {
  try {
    const { quoteId, text } = req.body;
    
    if (!quoteId || !text) {
      return res.status(400).json({ error: 'Quote ID und Text erforderlich' });
    }
    
    const quotesDB = await loadQuotesDatabase();
    
    const quote = quotesDB.quotes.find(q => q.id === quoteId);
    if (!quote) {
      return res.status(404).json({ error: 'Zitat nicht gefunden' });
    }
    
    // Aktualisiere den Text
    quote.text = text.trim();
    
    await saveQuotesDatabase(quotesDB);
    
    res.json({
      success: true,
      quote: quote,
      message: 'Zitat aktualisiert'
    });
    
  } catch (error) {
    console.error('[QUOTES] Fehler beim Aktualisieren:', error);
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
// API: MARKIERTE WÖRTER (FEHLERHAFTE TEXTSTELLEN)
// ============================================================================

// GET: Alle markierten Wörter laden (JSON)
app.get('/api/marked-words', async (req, res) => {
  try {
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      // Datei existiert noch nicht - leeres Array zurückgeben
    }
    
    res.json(markedWords);
  } catch (error) {
    console.error('[MARKED-WORDS] Fehler beim Laden:', error);
    res.status(500).json({ error: error.message });
  }
});

// GET: Marked-words als Datei herunterladen (für Online-Export)
app.get('/api/marked-words/download', async (req, res) => {
  try {
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      // Datei existiert noch nicht
    }
    
    const filename = `marked-words-${new Date().toISOString().split('T')[0]}.json`;
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Type', 'application/json');
    res.send(JSON.stringify(markedWords, null, 2));
  } catch (error) {
    console.error('[MARKED-WORDS] Download-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST: Markierte Wörter importieren (merge mit existierenden)
app.post('/api/marked-words/import', async (req, res) => {
  try {
    const { words, mode } = req.body; // mode: 'merge' oder 'replace'
    
    if (!Array.isArray(words)) {
      return res.status(400).json({ error: 'Ungültiges Format - Array erwartet' });
    }
    
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    let existingWords = [];
    if (mode !== 'replace') {
      try {
        const fileContent = await fs.readFile(markedWordsFile, 'utf8');
        existingWords = JSON.parse(fileContent);
      } catch (error) {
        // Datei existiert noch nicht
      }
    }
    
    // Merge: Füge nur neue Einträge hinzu (basierend auf word + gaTitle + timestamp)
    let added = 0;
    const existingKeys = new Set(existingWords.map(w => `${w.word}|${w.gaTitle}|${w.timestamp}`));
    
    for (const word of words) {
      const key = `${word.word}|${word.gaTitle}|${word.timestamp}`;
      if (!existingKeys.has(key)) {
        existingWords.push(word);
        existingKeys.add(key);
        added++;
      }
    }
    
    await fs.writeFile(markedWordsFile, JSON.stringify(existingWords, null, 2), 'utf8');
    
    res.json({ 
      success: true, 
      imported: added,
      total: existingWords.length,
      message: mode === 'replace' 
        ? `${words.length} Einträge importiert (ersetzt)` 
        : `${added} neue Einträge hinzugefügt (${existingWords.length} gesamt)`
    });
  } catch (error) {
    console.error('[MARKED-WORDS] Import-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// DELETE: Einzelnes markiertes Wort löschen
app.delete('/api/marked-words/:index', async (req, res) => {
  try {
    const index = parseInt(req.params.index);
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      return res.status(404).json({ error: 'Keine markierten Wörter gefunden' });
    }
    
    if (index < 0 || index >= markedWords.length) {
      return res.status(400).json({ error: 'Ungültiger Index' });
    }
    
    const deleted = markedWords.splice(index, 1)[0];
    await fs.writeFile(markedWordsFile, JSON.stringify(markedWords, null, 2), 'utf8');
    
    res.json({ 
      success: true, 
      deleted: deleted,
      remaining: markedWords.length 
    });
  } catch (error) {
    console.error('[MARKED-WORDS] Fehler beim Löschen:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST: Markiertes Wort anhand von Inhalt löschen (für Cross-Server Sync)
app.post('/api/marked-words/delete-by-content', async (req, res) => {
  try {
    const { word, gaTitle, timestamp } = req.body;
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      return res.json({ success: true, deleted: null, message: 'Keine Einträge vorhanden' });
    }
    
    // Finde den Eintrag anhand von word, gaTitle und optional timestamp
    const index = markedWords.findIndex(entry => 
      entry.word === word && 
      entry.gaTitle === gaTitle &&
      (!timestamp || entry.timestamp === timestamp)
    );
    
    if (index === -1) {
      return res.json({ success: true, deleted: null, message: 'Eintrag nicht gefunden' });
    }
    
    const deleted = markedWords.splice(index, 1)[0];
    await fs.writeFile(markedWordsFile, JSON.stringify(markedWords, null, 2), 'utf8');
    
    console.log('[MARKED-WORDS] Per Content gelöscht:', deleted.word);
    res.json({ success: true, deleted, remaining: markedWords.length });
  } catch (error) {
    console.error('[MARKED-WORDS] Fehler beim Löschen per Content:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST: Neues markiertes Wort speichern
app.post('/api/save-marked-word', async (req, res) => {
  try {
    const { word, gaTitle, timestamp } = req.body;
    
    if (!word || !gaTitle) {
      return res.status(400).json({ error: 'Wort und GA-Titel erforderlich' });
    }
    
    
    const markedWordsFile = path.join(__dirname, 'marked-words.json');
    
    // Lade existierende Einträge
    let markedWords = [];
    try {
      const fileContent = await fs.readFile(markedWordsFile, 'utf8');
      markedWords = JSON.parse(fileContent);
    } catch (error) {
      // Datei existiert noch nicht
    }
    
    // Füge neuen Eintrag hinzu
    markedWords.push({
      word: word,
      gaTitle: gaTitle,
      timestamp: timestamp || new Date().toISOString()
    });
    
    // Speichere aktualisierte Datei
    await fs.writeFile(markedWordsFile, JSON.stringify(markedWords, null, 2), 'utf8');
    
    
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
// API: FEHLERKORREKTUR IN MD-DATEIEN
// ============================================================================

// Hilfsfunktion zum Escapen von Regex-Sonderzeichen
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// POST: Vorschau der Korrektur (zeigt wo der Fehler überall vorkommt)
app.post('/api/marked-words/preview-correction', async (req, res) => {
  try {
    const { wrongText, gaTitle, caseSensitive = true } = req.body;
    
    if (!wrongText) {
      return res.status(400).json({ error: 'Fehlerhafter Text erforderlich' });
    }
    
    const steinerGAPath = path.join(__dirname, 'Steiner_GA');
    const results = [];
    const regexFlags = caseSensitive ? 'g' : 'gi';
    
    // Parse GA-Nummer aus dem Titel (z.B. "GA117/3 - ...")
    let targetFolder = null;
    if (gaTitle) {
      const gaMatch = gaTitle.match(/GA(\d+)/);
      if (gaMatch) {
        const gaNumber = gaMatch[1];
        const folders = await fs.readdir(steinerGAPath);
        targetFolder = folders.find(f => f.startsWith(`GA${gaNumber}-`) || f.startsWith(`GA${gaNumber} `));
      }
    }
    
    const searchPath = targetFolder ? path.join(steinerGAPath, targetFolder) : steinerGAPath;
    
    async function searchInDirectory(dirPath) {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        
        if (entry.isDirectory()) {
          await searchInDirectory(fullPath);
        } else if (entry.name.endsWith('.md')) {
          try {
            const content = await fs.readFile(fullPath, 'utf8');
            const occurrences = (content.match(new RegExp(escapeRegExp(wrongText), regexFlags)) || []).length;
            
            if (occurrences > 0) {
              results.push({
                file: fullPath.replace(steinerGAPath + path.sep, ''),
                occurrences
              });
            }
          } catch (err) {
            console.error(`[CORRECTION] Fehler beim Lesen von ${fullPath}:`, err.message);
          }
        }
      }
    }
    
    await searchInDirectory(searchPath);
    
    const totalOccurrences = results.reduce((sum, r) => sum + r.occurrences, 0);
    
    res.json({
      wrongText,
      totalOccurrences,
      fileCount: results.length,
      files: results,
      caseSensitive
    });
    
  } catch (error) {
    console.error('[CORRECTION] Preview-Fehler:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST: Korrektur durchführen
app.post('/api/marked-words/apply-correction', async (req, res) => {
  try {
    const { wrongText, correctText, mode, gaTitle, markedWordIndex, includeHtml, caseSensitive = true } = req.body;
    // mode: 'single' (nur in der spezifischen GA) oder 'all' (überall)
    // includeHtml: true = auch HTML-Dateien im Root korrigieren
    // caseSensitive: true = Groß/Kleinschreibung beachten
    
    if (!wrongText || !correctText) {
      return res.status(400).json({ error: 'Fehlerhafter und korrigierter Text erforderlich' });
    }
    
    if (wrongText === correctText) {
      return res.status(400).json({ error: 'Fehlerhafter und korrigierter Text sind identisch' });
    }
    
    const steinerGAPath = path.join(__dirname, 'Steiner_GA');
    const correctedFiles = [];
    let totalCorrections = 0;
    const regexFlags = caseSensitive ? 'g' : 'gi';
    
    // Parse GA-Nummer für single-mode
    let targetFolder = null;
    if (mode === 'single' && gaTitle) {
      const gaMatch = gaTitle.match(/GA(\d+)/);
      if (gaMatch) {
        const gaNumber = gaMatch[1];
        const folders = await fs.readdir(steinerGAPath);
        targetFolder = folders.find(f => f.startsWith(`GA${gaNumber}-`) || f.startsWith(`GA${gaNumber} `));
      }
    }
    
    const searchPath = targetFolder ? path.join(steinerGAPath, targetFolder) : steinerGAPath;
    
    async function correctInDirectory(dirPath) {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        
        if (entry.isDirectory()) {
          await correctInDirectory(fullPath);
        } else if (entry.name.endsWith('.md')) {
          try {
            const content = await fs.readFile(fullPath, 'utf8');
            const regex = new RegExp(escapeRegExp(wrongText), regexFlags);
            const occurrences = (content.match(regex) || []).length;
            
            if (occurrences > 0) {
              const newContent = content.replace(regex, correctText);
              await fs.writeFile(fullPath, newContent, 'utf8');
              
              correctedFiles.push({
                file: fullPath.replace(steinerGAPath + path.sep, ''),
                corrections: occurrences
              });
              totalCorrections += occurrences;
            }
          } catch (err) {
            console.error(`[CORRECTION] Fehler bei ${fullPath}:`, err.message);
          }
        }
      }
    }
    
    await correctInDirectory(searchPath);
    
    // JSON-Dateien korrigieren wenn gewünscht (Vorträge UND Bücher)
    if (includeHtml) { // Parameter heißt noch includeHtml, bedeutet jetzt aber +JSON
      try {
        const rootFiles = await fs.readdir(__dirname);
        // Vorträge UND Bücher
        const jsonFiles = rootFiles.filter(f => 
          (f.startsWith('steiner-full-lectures') || f.startsWith('steiner-books')) && 
          f.endsWith('.json')
        );
        
        for (const jsonFile of jsonFiles) {
          const jsonPath = path.join(__dirname, jsonFile);
          try {
            const content = await fs.readFile(jsonPath, 'utf8');
            const regex = new RegExp(escapeRegExp(wrongText), regexFlags);
            const occurrences = (content.match(regex) || []).length;
            
            if (occurrences > 0) {
              // Sicherheitscheck: Prüfe ob JSON nach Korrektur noch valide ist
              const newContent = content.replace(regex, correctText);
              
              try {
                // Validiere dass die JSON-Struktur intakt bleibt
                JSON.parse(newContent);
                
                // JSON ist valide - speichern
                await fs.writeFile(jsonPath, newContent, 'utf8');
                
                correctedFiles.push({
                  file: `[JSON] ${jsonFile}`,
                  corrections: occurrences
                });
                totalCorrections += occurrences;
              } catch (parseErr) {
                // JSON wäre nach Korrektur ungültig - nicht speichern!
                console.error(`[CORRECTION] WARNUNG: ${jsonFile} würde durch Korrektur ungültig werden - übersprungen!`);
                correctedFiles.push({
                  file: `[JSON] ${jsonFile} (ÜBERSPRUNGEN - würde JSON ungültig machen)`,
                  corrections: 0
                });
              }
            }
          } catch (err) {
            console.error(`[CORRECTION] Fehler bei ${jsonFile}:`, err.message);
          }
        }
      } catch (err) {
        console.error('[CORRECTION] Fehler beim Lesen der JSON-Dateien:', err.message);
      }
    }
    
    // Lösche den Eintrag aus marked-words.json nur wenn Korrekturen erfolgreich waren
    const indexValid = markedWordIndex !== undefined && markedWordIndex !== null && !isNaN(markedWordIndex) && markedWordIndex >= 0;
    console.log('[CORRECTION] totalCorrections:', totalCorrections, 'markedWordIndex:', markedWordIndex, 'indexValid:', indexValid);
    
    if (totalCorrections > 0 && indexValid) {
      const markedWordsFile = path.join(__dirname, 'marked-words.json');
      try {
        const fileContent = await fs.readFile(markedWordsFile, 'utf8');
        let markedWords = JSON.parse(fileContent);
        console.log('[CORRECTION] Lösche Eintrag', markedWordIndex, 'von', markedWords.length);
        if (markedWordIndex < markedWords.length) {
          markedWords.splice(markedWordIndex, 1);
          await fs.writeFile(markedWordsFile, JSON.stringify(markedWords, null, 2), 'utf8');
          console.log('[CORRECTION] Eintrag gelöscht, verbleibend:', markedWords.length);
        }
      } catch (err) {
        console.error('[CORRECTION] Fehler beim Löschen aus marked-words:', err.message);
      }
    } else if (!indexValid) {
      console.log('[CORRECTION] Kein gültiger markedWordIndex');
    } else {
      console.log('[CORRECTION] Keine Korrekturen durchgeführt - Eintrag bleibt erhalten');
    }
    
    res.json({
      success: true,
      wrongText,
      correctText,
      mode,
      totalCorrections,
      fileCount: correctedFiles.length,
      files: correctedFiles,
      message: `${totalCorrections} Korrektur${totalCorrections !== 1 ? 'en' : ''} in ${correctedFiles.length} Datei${correctedFiles.length !== 1 ? 'en' : ''} durchgeführt`
    });
    
  } catch (error) {
    console.error('[CORRECTION] Fehler:', error);
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
    
    // Erkenne Backup-Typ aus Dateiname
    let backupDir, targetFile, backupFunc;
    
    if (backupName.startsWith('keywords-database-')) {
      backupDir = KEYWORDS_BACKUP_DIR;
      targetFile = KEYWORDS_DB_FILE;
      backupFunc = createKeywordsBackup;
    } else if (backupName.startsWith('summary-database-')) {
      backupDir = SUMMARY_BACKUP_DIR;
      targetFile = SUMMARY_DB_FILE;
      backupFunc = createSummaryBackup;
    } else if (backupName.startsWith('themes-database-')) {
      backupDir = THEMES_BACKUP_DIR;
      targetFile = THEMES_DB_FILE;
      backupFunc = createThemesBackup;
    } else if (backupName.startsWith('thematic-clusters-')) {
      backupDir = CLUSTERS_BACKUP_DIR;
      targetFile = CLUSTERS_FILE;
      backupFunc = createClustersBackup;
    } else if (backupName.startsWith('steiner-images-')) {
      backupDir = IMAGES_BACKUP_DIR;
      targetFile = path.join(__dirname, 'steiner-images.json');
      backupFunc = createImagesBackup;
    } else if (backupName.startsWith('backend-')) {
      backupDir = CODE_BACKUP_DIR;
      targetFile = path.join(__dirname, 'backend.js');
      backupFunc = createCodeBackup;
    } else if (backupName.startsWith('index-')) {
      backupDir = HTML_BACKUP_DIR;
      targetFile = path.join(__dirname, 'index.html');
      backupFunc = () => createHtmlBackup('index.html');
    } else if (backupName.startsWith('keyword-manager-advanced-') || backupName.startsWith('keyword-manager-')) {
      backupDir = HTML_BACKUP_DIR;
      targetFile = path.join(__dirname, 'keyword-manager.html');
      backupFunc = () => createHtmlBackup('keyword-manager.html');
    } else if (backupName.startsWith('app-')) {
      backupDir = HTML_BACKUP_DIR;
      targetFile = path.join(__dirname, 'app.html');
      backupFunc = () => createHtmlBackup('app.html');
    } else if (backupName.startsWith('members-') && backupName.endsWith('.html')) {
      backupDir = HTML_BACKUP_DIR;
      targetFile = path.join(__dirname, 'members.html');
      backupFunc = createMembersHtmlBackup;
    } else if (backupName.startsWith('members-panel-')) {
      backupDir = HTML_BACKUP_DIR;
      targetFile = path.join(__dirname, 'members-panel.js');
      backupFunc = createMembersPanelBackup;
    } else {
      return res.status(400).json({ error: 'Unbekannter Backup-Typ' });
    }
    
    const backupPath = path.join(backupDir, backupName);
    
    // Prüfe ob Backup existiert
    try {
      await fs.access(backupPath);
    } catch (error) {
      console.error(`[BACKUP-API] Backup nicht gefunden: ${backupPath}`);
      return res.status(404).json({ error: 'Backup nicht gefunden' });
    }
    
    // Erstelle Backup der aktuellen Datei vor der Wiederherstellung
    await backupFunc();
    
    // Lade Backup
    const backupData = await fs.readFile(backupPath, 'utf8');
    
    // Validiere Backup (nur für JSON-Dateien)
    if (backupName.endsWith('.json')) {
      const parsedBackup = JSON.parse(backupData);
      if (Object.keys(parsedBackup).length === 0) {
        return res.status(400).json({ error: 'Backup ist leer' });
      }
    }
    
    // Stelle Backup wieder her
    await fs.writeFile(targetFile, backupData, 'utf8');
    
    
    res.json({
      success: true,
      restored: backupName,
      targetFile: path.basename(targetFile),
      entries: backupName.endsWith('.json') ? Object.keys(JSON.parse(backupData)).length : 'N/A'
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
      case 'images':
        backupFile = await createImagesBackup();
        break;
      case 'code':
        backupFile = await createCodeBackup();
        break;
      case 'html':
        // Erstelle Backups für alle HTML-Dateien
        const indexBackup = await createHtmlBackup('index.html');
        const managerBackup = await createHtmlBackup('keyword-manager.html');
        const appBackup = await createHtmlBackup('app.html');
        const membersHtmlBackup = await createMembersHtmlBackup();
        const membersPanelBackup = await createMembersPanelBackup();
        const htmlBackups = [indexBackup, managerBackup, appBackup, membersHtmlBackup, membersPanelBackup].filter(b => b !== null);
        return res.json({
          success: true,
          backups: htmlBackups.map(b => path.basename(b)),
          count: htmlBackups.length,
          type: 'html'
        });
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
      case 'images':
        backupDir = IMAGES_BACKUP_DIR;
        prefix = 'steiner-images';
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
    console.log('\n' + '='.repeat(70));
    console.log('  STEINER GA-SUCHE SERVER - START');
    console.log('='.repeat(70));
    
    console.log('\n[1/8] Erstelle Backups...');
// Erstelle automatisches Backup beim Start
await createCodeBackup();
await createHtmlBackup('index.html');
await createHtmlBackup('keyword-manager.html');
// Wichtige Datenbank-Backups beim Start
await createKeywordsBackup();
await createSummaryBackup();
await createImagesBackup();
    console.log('  ✓ Backups erstellt');

    console.log('\n[2/8] Lade Synonyme...');
await loadSynonyms();
    console.log(`  ✓ Synonyme geladen: ${Object.keys(synonyms).length} Gruppen`);

    console.log('\n[3/8] Lade Vorträge...');
await loadFullLectures();
    console.log(`  ✓ Vorträge geladen: ${Object.keys(fullLectures).length} Vorträge`);

    console.log('\n[4/8] Lade Bücher...');
const loadedBooks = await loadBooks();
    console.log(`  ✓ Bücher geladen: ${Object.keys(fullBooks).length} Bücher`);
// Lade Bilder-Datenbank NICHT beim Start (zu groß)
// Bilder werden bei Bedarf aus Part-Dateien geladen
// await loadSteinerImages(); // Deaktiviert - Lazy Loading statt dessen

    console.log('\n[5/8] Synchronisiere Keyword-Systeme...');
// Synchronisiere Keyword-Systeme beim Start
await synchronizeKeywordSystems();
    console.log('  ✓ Keyword-Systeme synchronisiert');

    console.log('\n[6/8] Konvertiere zu Absatz-Format...');
// Konvertiere Lectures zu Absatz-Format
let lectureParagraphsCount = 0;
Object.values(fullLectures).forEach(lecture => {
  lecture.paragraphs?.forEach((para, idx) => {
    paragraphsFromLectures.push({
      ID: lecture.ID,
      index: para.index || `para_${idx}`,
      title: lecture.title,
      fileName: lecture.fileName,
      content: para.content || para.text || '',
      location: lecture.location,
      date: lecture.date,
      isBook: false
    });
    lectureParagraphsCount++;
  });
});

// Konvertiere auch Bücher zu Absatz-Format
let bookParagraphsCount = 0;
Object.values(fullBooks).forEach(book => {
  const bookParagraphs = getBookParagraphsForSearch(book);
  bookParagraphs.forEach((para, idx) => {
    paragraphsFromLectures.push({
      ID: book.ID || book.gaNumber,
      index: para.index || null,
      title: book.title || book.fileName || book.ID,
      fileName: book.fileName || book.title || book.ID,
      content: para.content || para.text || '',
      location: null, // Bücher haben keinen Ort
      date: book.yearRange || null, // Bücher haben Jahr-Range statt Datum
      isBook: true
    });
    bookParagraphsCount++;
  });
});
    console.log(`  ✓ Absätze erstellt: ${lectureParagraphsCount} Vortrags-Absätze, ${bookParagraphsCount} Buch-Absätze`);

    console.log('\n[7/8] Lade Query-Log und Cache...');
    await loadQueryLog();
    
    // Lade Themensuchen-Cache-DB
    const thematicDB = await loadThematicSearchDatabase();
    console.log(`  ✓ Query-Log geladen, Themensuchen-Cache: ${Object.keys(thematicDB || {}).length} Einträge`);
    
    
    // ENTFERNT: Relevanz-Scoring-Test wurde entfernt
    
    console.log('\n[8/8] Starte Server...');
    app.listen(PORT, () => {
      console.log('\n' + '='.repeat(70));
      console.log(`  ✓ SERVER GESTARTET`);
      console.log(`  URL: http://localhost:${PORT}`);
      console.log('='.repeat(70));
      console.log(`\n  DATEN GELADEN:`);
      console.log(`    • ${Object.keys(fullLectures).length} Vorträge`);
      console.log(`    • ${Object.keys(fullBooks).length} Bücher`);
      console.log(`    • ${paragraphsFromLectures.length} Absätze (für Suche)`);
      console.log(`    • ${Object.keys(synonyms).length} Synonym-Gruppen`);
      console.log(`\n  Server bereit für Anfragen!\n`);
    });
    
  } catch (error) {
    console.error('\n✗ Fehler beim Server-Start:', error);
    process.exit(1);
  }
}

startServer();
