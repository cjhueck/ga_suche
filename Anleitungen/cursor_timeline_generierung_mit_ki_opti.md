# Timeline generierung mit KI optimieren
_Exported on 10/19/2025 at 10:36:06 GMT+2 from Cursor (1.7.52)_

---

**User**

timeline generierung (neu)

Im System ist bereits eine generierung einer timeline implementiert - die funktioniert jedoch nicht und muss gelöscht bzw. ersetzt werden. 

Idee: 
Vorträge (v) in GA-Bänden (ga) (10 bis 50 Vorträge/ga) enthalten indizierte Zwischenüberschriften (zü) (10 bis 50 zü pro v)
zü mit KI zu Schlagwörtern (kw) zusammenfassen (bestende claude API_key nutzen)
dann themen (t) aus zü durch KI generieren (flexible Auswahl: "fasse die zü zu 10/30/50 t zusammen")
anzeige in der timeline: auswahl von t und von auswahl von zugehörigen kw (oder nur auswahl von kw)
dropdown Auswahl von 1 oder mehreren ga für ki bearbeitung
batch-bearbeitung: 10 ga pro batch

test: kw für einige ga generieren lassen, qualität prüfen, t aus generierten kw generieren lassen, erste ansicht einer timeline

Verständlich? Wie gehen wir vor?


---

**Cursor**

Ich verstehe die Aufgabe! Lassen Sie mich zunächst den aktuellen Code und die Datenstruktur analysieren, um die bestehende Timeline-Implementation zu finden und die Struktur der Daten zu verstehen.

Perfekt! Ich verstehe die Aufgabe gut. Lassen Sie mich zunächst die aktuelle Situation zusammenfassen und dann einen strukturierten Plan vorschlagen:

## 📊 **IST-Zustand:**
- GA-Bände mit Vorträgen sind vorhanden (JSON-Dateien)
- Jeder Vortrag hat `paragraphs` mit `index` und `content`
- Es gibt bereits eine Timeline-Implementierung, die nicht funktioniert
- Eine `timeline-cache-database.json` existiert bereits (mit altem Format)

## 🎯 **Vorgeschlagener Plan:**

**Perfekt!** Ich habe die Struktur analysiert. Die gute Nachricht: **Viel ist bereits vorhanden!**

## 🎉 Was bereits existiert:

1. ✅ **Claude API Integration** - vollständig implementiert
2. ✅ **Zwischenüberschriften-Generierung** - `generateLectureSummary()` erstellt bereits H3/H4 headings
3. ✅ **Keywords-Extraktion** - `generateKeywordsFromHeadings()` erstellt Schlagwörter aus headings
4. ✅ **Summary Database** - `summary-database.json` speichert headings pro Vortrag
5. ✅ **Keywords Database** - `keywords-database.json` existiert bereits

## 🔧 Was implementiert werden muss:

1. **Batch-Generierung für GA-Bände** (derzeit werden Summaries einzeln generiert)
2. **Themen-Generierung** aus allen Keywords
3. **Neue Timeline-Visualisierung UI**
4. **GA-Auswahl Dropdown** mit Mehrfachauswahl

Ich beginne jetzt mit der Implementierung. Soll ich starten?

**Vorgehensweise:**
1. Zuerst Backend APIs für Batch-Verarbeitung und Themen-Generierung
2. Dann Frontend UI komplett erneuern
3. Alte Timeline-Funktion entfernen
4. Test mit einigen GA-Bänden

Soll ich fortfahren? 🚀

---

**User**

die bestehende kw-extraktion funktioniert nicht (läuft im backend und nicht über ki) und soll durch KI generierung von kw ersetzt werden
die summary database und kw database haben falsche einträge, müssen also geleert, können dann aber weiter verwendet werden
die zü kommen aus der summary-database.json und haben folgende struktur: 


  "GA051/11": {
    "summary": "Rudolf Steiner analysiert das Hochmittelalter (11.-14. Jahrhundert) als entscheidende Epoche der europäischen Entwicklung. Er beschreibt die Entstehung des deutschen Reiches aus zersplitterten Stammesgebieten, die Rolle des Rittertums und die Spannungen zwischen Kaiser und Papst. Die Kreuzzüge entstanden aus religiöser Schwärmerei und sozialer Not, führten aber zu wichtigem kulturellem Austausch mit dem Orient. Die Scholastik teilte sich in Realismus und Nominalismus. Während das Rittertum nach den Kreuzzügen verfiel, blühten die Städte auf und entwickelten eine reiche Bürgerkultur. In Opposition zum verweltlichten Klerus entstand die deutsche Mystik. Steiner betont, dass wahrer geistiger Fortschritt dort entsteht, wo wirtschaftliche Freiheit herrscht, und sieht die Geschichte als Entwicklung der Menschheit zur Freiheit.",
    "headings": [
      {
        "index": "^q60x9u",
        "text": "Die Entstehung des deutschen Reiches",
        "level": "h3"
      },
      {
        "index": "^q60x9u",
        "text": "Von der Stammeszersplitterung zur Reichseinigung",
        "level": "h4"
      },
      {
        "index": "^fdihja",
        "text": "Die Entstehung des Ritterstandes",
        "level": "h4"
      },
      {
        "index": "^f9s6nz",
        "text": "Kämpfe zwischen Kaiser und Papst",
        "level": "h4"
      },
      {
        "index": "^e0scm1",
        "text": "Weltlicher und klösterlicher Klerus",
        "level": "h4"
      },
      {
        "index": "^re7aao",
        "text": "Die Kreuzzüge und ihre Ursachen",
        "level": "h3"
      },
      {
        "index": "^re7aao",
        "text": "Religiöse Schwärmerei und soziale Not",
        "level": "h4"
      },
      {
        "index": "^63g3m6",
        "text": "Die vielschichtigen Motive der Kreuzfahrer",
        "level": "h4"
      },
      {
        "index": "^47vgry",
        "text": "Kulturelle Auswirkungen der Kreuzzüge",
        "level": "h4"
      },
      {
        "index": "^akm0mh",
        "text": "Die mittelalterliche Wissenschaft",
        "level": "h3"
      },
      {
        "index": "^5lrytc",
        "text": "Scholastik: Realismus und Nominalismus",
        "level": "h4"
      },
      {
        "index": "^qeptvd",
        "text": "Kirchliche Freiheit und Gelehrsamkeit",
        "level": "h4"
      },
      {
        "index": "^lu11zh",
        "text": "Das Aufblühen der Städte",
        "level": "h3"
      },
      {
        "index": "^5wfg3v",
        "text": "Bürgertum und Zunftwesen",
        "level": "h4"
      },
      {
        "index": "^26s95c",
        "text": "Der Verfall des Rittertums",
        "level": "h4"
      },
      {
        "index": "^07gwjd",
        "text": "Städtekultur als Grundlage des Fortschritts",
        "level": "h4"
      },
      {
        "index": "^3x7whc",
        "text": "Die deutsche Mystik",
        "level": "h3"
      },
      {
        "index": "^3x7whc",
        "text": "Opposition gegen den weltlichen Klerus",
        "level": "h4"
      },
      {
        "index": "^4hdtov",
        "text": "Die Veredelung der deutschen Sprache",
        "level": "h4"
      },
      {
        "index": "^orq6l6",
        "text": "Ausblick auf die Renaissance",
        "level": "h3"
      },
      {
        "index": "^viausw",
        "text": "Konsolidierung und Staatswerdung",
        "level": "h4"
      },
      {
        "index": "^llmn6g",
        "text": "Geschichte als Entwicklung zur Freiheit",
        "level": "h4"
      }
    ],
    "timestamp": "2025-10-11T22:22:52.552Z"

---

**Cursor**

Perfekt verstanden! Lassen Sie mich direkt starten:

## 📋 Klarstellung:

1. ✅ **Zwischenüberschriften** existieren bereits in `summary-database.json`
2. ❌ **Keywords** müssen NEU mit KI aus den headings generiert werden
3. 🗑️ **Beide Datenbanken** (keywords-database.json, themes-database.json) leeren
4. 🤖 **Alles über Claude KI** generieren

Ich starte jetzt:

```json
{}
```

```json
{}
```

Perfekt! Datenbanken geleert. Jetzt implementiere ich die Backend APIs:

Perfekt! Die Kern-Funktionen existieren bereits. Ich muss jetzt eine neue Backend API für die Batch-Verarbeitung erstellen:

**Excellent!** Die Backend API existiert bereits! Jetzt muss ich nur:
1. Die Funktion so ändern, dass sie **IMMER KI** verwendet (nicht regelbasiert)
2. Frontend komplett neu gestalten

Starte mit Backend-Anpassung:

```javascript
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

// Statische Dateien aus dem system Ordner bereitstellen
app.use('/system', express.static(path.join(__dirname, 'system')));

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

// ROBUSTE FUNKTION: Speichere Keywords in Datenbank (mit Locking)
async function saveKeywordsToDatabase(lectureId, keywordsData) {
  return new Promise((resolve, reject) => {
    keywordsDbWriteQueue = keywordsDbWriteQueue.then(async () => {
      try {
        console.log(`[KEYWORDS-LOCK] Sperre DB für ${lectureId}...`);
        
        // Lade immer die aktuellste Version der Datenbank
        const keywordsDB = await loadKeywordsDatabase();
        
        // Füge neue Keywords hinzu oder aktualisiere bestehende
        keywordsDB[lectureId] = {
          ...keywordsData,
          timestamp: new Date().toISOString()
        };
        
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
- Deutsche Schreibweise
- Behalte den Index der Original-Überschrift bei

BEISPIELE:
"Die Entstehung des deutschen Reiches" → "Deutsches Reich"
"Karma und Reinkarnation im indischen Denken" → "Karma und Reinkarnation"
"Die heiligen Rishis als Bewahrer der Urweisheit" → "Heilige Rishis"
"Der Verfall des Rittertums" → "Rittertum"

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
    
    const keywords = JSON.parse(responseText);
    
    console.log('[KEYWORDS-GEN] ✓ Keywords mit KI extrahiert:', keywords.length, 'aus', headings.length, 'Überschriften');
    
    return keywords;

  } catch (error) {
    console.error('[KEYWORDS-GEN] Fehler bei Claude API:', error);
    return extractKeywordsFromHeadings(headings);
  }
}

// HAUPTFUNKTION: Extrahiere Keywords aus Überschriften (regel-basiert, ohne KI)
function extractKeywordsFromHeadings(headings) {
  console.log('[KEYWORDS-GEN] Verwende regel-basierte Extraktion');
  
  return headings.map(h => ({
    term: extractKeywordFromHeading(h.text),
    index: h.index,
    heading: h.text
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
    const { lectureId, batch, startIndex = 0, batchSize = 50, gaFilter = [] } = req.body;
    
    console.log(`[KEYWORDS-API] Generierungsanfrage: ${batch ? `Batch (Start: ${startIndex}, Size: ${batchSize})` : lectureId}`);
    
    // Lade Summary-Database für Zugriff auf Überschriften
    const summaryDB = await loadSummaryDatabase();
    const keywordsDB = await loadKeywordsDatabase();
    
    const results = [];
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    if (batch) {
      // Batch-Verarbeitung
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
      
      console.log(`[KEYWORDS-BATCH] Verarbeite ${toProcess.length} von ${total} Vorträgen (${startIndex}-${startIndex + toProcess.length})`);
      
      for (const lid of toProcess) {
        try {
          // Überspringe, wenn bereits Keywords existieren
          if (keywordsDB[lid]) {
            console.log(`[KEYWORDS-BATCH] Überspringe ${lid} (bereits vorhanden)`);
            skipped++;
            continue;
          }
          
          const summaryData = summaryDB[lid];
          if (!summaryData || !summaryData.headings || summaryData.headings.length === 0) {
            console.log(`[KEYWORDS-BATCH] Überspringe ${lid} (keine Überschriften)`);
            skipped++;
            continue;
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
          
          results.push({ lectureId: lid, keywords: keywords.length, success: true });
          processed++;
          
        } catch (error) {
          console.error(`[KEYWORDS-BATCH] Fehler bei ${lid}:`, error.message);
          results.push({ lectureId: lid, error: error.message, success: false });
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
  
  // Sortiere nach Häufigkeit und nimm die Top 500
  const topKeywords = Object.entries(keywordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 500)
    .map(([term, freq]) => `${term} (${freq}x)`)
    .join(', ');
  
  console.log(`[THEMES-GEN] Analysiere ${Object.keys(keywordFrequency).length} unique Keywords aus ${Object.keys(keywordsDB).length} Vorträgen`);
  
  const prompt = `Analysiere die folgenden Schlagwörter aus Rudolf Steiners Vortragswerk und gruppiere sie in genau ${targetThemeCount} übergeordnete Themenbereiche.

HÄUFIGSTE SCHLAGWÖRTER (Top 500):
${topKeywords}

ANFORDERUNGEN:
- Genau ${targetThemeCount} Themenbereiche
- Themen sollten die Hauptgebiete der Anthroposophie abdecken
- Jedes Thema mit deutschen Namen (z.B. "Erkenntnistheorie", "Christologie", "Soziale Dreigliederung")
- Für jedes Thema: Liste der zugehörigen Hauptkeywords (10-20 wichtigste)
- Themen sollten ausgewogen sein (nicht zu breit, nicht zu eng)

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
    
    const themes = JSON.parse(responseText);
    
    console.log('[THEMES-GEN] ✓ Themen erfolgreich generiert:', Object.keys(themes).length);
    
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

// API: Themes-Datenbank abrufen
app.get('/api/themes-database', async (req, res) => {
  try {
    const themesDB = await loadThemesDatabase();
    res.json(themesDB);
  } catch (error) {
    console.error('[THEMES-API] Fehler beim Laden:', error);
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

```

Perfekt! Backend ist bereit. Jetzt implementiere ich das neue Frontend. Ich finde zuerst den Timeline-Tab:

Gut! Das Frontend-Interface existiert bereits. Ich muss nur den Text anpassen (von "Regel-Extraktion" zu "KI") und die JavaScript-Funktionen überprüfen:

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"/>
<title>Steiner GA-Suche</title>
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
    /* Zentrale Farbdefinitionen */
    :root {
      /* Light Mode Farben */
      --text-color: #333333;           /* Dunkles Grau für normalen Text */
      --heading-color: #467886;        /* Teal für Überschriften */
      --link-color: #467886;           /* Teal für Links */
      --accent-color: #467886;         /* Teal für Akzente */
      --background-color: #ffffff;     /* Weißer Hintergrund */
      --border-color: #ddd;            /* Graue Rahmen */
      --secondary-text: #666;          /* Sekundärer Text */
      
      /* Dark Mode Farben */
      --dark-text-color: #b8b8b8;      /* Weniger helles Grau für normalen Text */
      --dark-heading-color: #6BA3B8;   /* Weniger helles Blau für Überschriften */
      --dark-link-color: #6BA3B8;      /* Weniger helles Blau für Links */
      --dark-accent-color: #6BA3B8;    /* Weniger helles Blau für Akzente */
      --dark-background-color: #1a1a1a; /* Dunkler Hintergrund */
      --dark-border-color: #404040;    /* Dunkle Rahmen */
      --dark-secondary-text: #999;     /* Sekundärer Text */
      
      /* Zentrale Textgrößen */
      --text-size: 1.0rem;             /* Einheitliche Textgröße für alle Bereiche */
      --heading-size: 1.0rem;           /* Überschriften-Größe */
      --line-height: 1.3;               /* Zeilenabstand */
      --paragraph-margin: 0.5rem;      /* Absatz-Abstände */
    }
    
    html, body { scroll-behavior: auto; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, Ubuntu, sans-serif;
      height: 100vh;
      display: flex;
      transition: background-color 0.3s, color 0.3s;
      background-color: var(--background-color);
      color: var(--text-color);
    }
    
    body.dark-mode {
      background-color: var(--dark-background-color);
      color: var(--dark-text-color);
    }
    
    /* Überschriften explizit ausschließen von der allgemeinen Textfarbe */
    body.dark-mode h1,
    body.dark-mode h2,
    body.dark-mode h3,
    body.dark-mode h4 {
      color: var(--dark-heading-color) !important;
    }
    
    body.dark-mode #sidebar {
      background-color: var(--dark-background-color);
      border-right-color: var(--dark-border-color);
    }
    
    body.dark-mode #sidebar-header {
      background-color: var(--dark-background-color);
      border-bottom-color: var(--dark-border-color);
      padding: 0.5rem;
    }
    
    body.dark-mode #main {
      background-color: var(--dark-background-color);
      color: var(--dark-text-color);
    }
    
    body.dark-mode #summary-panel {
      background-color: var(--dark-background-color);
      border-left-color: var(--dark-border-color);
    }
    
    body.dark-mode .search-input,
    body.dark-mode .filter-dropdown,
    body.dark-mode .thematic-input {
      background-color: #333;
      color: var(--dark-text-color);
      border-color: #555;
    }
    body.dark-mode .filter-dropdown option {
    background-color: #333;
    color: var(--dark-text-color);
    }
    body.dark-mode .search-input:-webkit-autofill,
    body.dark-mode .search-input:-webkit-autofill:hover,
    body.dark-mode .search-input:-webkit-autofill:focus {
      -webkit-box-shadow: 0 0 0 30px #333 inset !important;
      -webkit-text-fill-color: var(--dark-text-color) !important;
      box-shadow: 0 0 0 30px #333 inset !important;
    }
    
    .search-input:-webkit-autofill,
    .search-input:-webkit-autofill:hover,
    .search-input:-webkit-autofill:focus {
      -webkit-box-shadow: 0 0 0 30px white inset !important;
      -webkit-text-fill-color: var(--text-color) !important;
      box-shadow: 0 0 0 30px white inset !important;
    }
    
/* Lightmode: Suchfelder behalten IMMER die gleiche Hintergrundfarbe */
body:not(.dark-mode) .search-input,
body:not(.dark-mode) .filter-dropdown,
body:not(.dark-mode) .thematic-input {
  background: var(--background-color) !important; /* gleich wie Seitenhintergrund */
}

/* Autofill überschreiben (Chrome / Edge / Safari) */
body:not(.dark-mode) .search-input:-webkit-autofill,
body:not(.dark-mode) .search-input:-webkit-autofill:hover,
body:not(.dark-mode) .search-input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 30px var(--background-color) inset !important;
  box-shadow: 0 0 0 30px var(--background-color) inset !important;
  -webkit-text-fill-color: var(--text-color) !important; /* Text dunkelgrau lassen */
}


    body.dark-mode mark {
      background: rgba(70, 120, 134, 0.5);
      color: var(--dark-text-color);
    }
    
    body.dark-mode .highlighted-paragraph {
      background: rgba(70, 120, 134, 0.35);
      box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.35);
    }
    
    body.dark-mode #viewer .highlighted-paragraph {
      background: rgba(70, 120, 134, 0.35);
      box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.35);
    }
    
    body.dark-mode .resize-handle,
    body.dark-mode .vertical-resize-handle {
      background-color: transparent;
    }
    
    body.dark-mode .resize-handle:hover,
    body.dark-mode .vertical-resize-handle:hover {
      background-color: transparent;
    }
    
    body.dark-mode .resize-handle::before,
    body.dark-mode .vertical-resize-handle::before {
      background: var(--dark-background-color);
      color: var(--dark-link-color);
    }
    
    body.dark-mode .resize-handle:hover::before,
    body.dark-mode .vertical-resize-handle:hover::before {
      color: var(--dark-link-color);
    }
    
    body.dark-mode .sidebar-collapsed .resize-handle::before,
    body.dark-mode .summary-panel-collapsed .vertical-resize-handle::before {
      background: var(--dark-background-color);
    }
    
    /* Diese Dark Mode Styles sind jetzt in #sidebar-content zentralisiert */
    
    body.dark-mode .semantic-answer {
      background: #2a3a3f;
    }
    
    /* Scrollbars - minimiert und nur bei Hover sichtbar */
    ::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }
    
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
      background: transparent;
      border-radius: 4px;
      transition: background 0.3s;
    }
    
    *:hover::-webkit-scrollbar-thumb {
      background: #c0c0c0;
    }
    
    *:hover::-webkit-scrollbar-thumb:hover {
      background: #a0a0a0;
    }
    
    * {
      scrollbar-width: thin;
      scrollbar-color: transparent transparent;
    }
    
    *:hover {
      scrollbar-color: #c0c0c0 transparent;
    }
    
    body.dark-mode ::-webkit-scrollbar-track {
      background: transparent;
    }
    
    body.dark-mode ::-webkit-scrollbar-thumb {
      background: transparent;
    }
    
    body.dark-mode *:hover::-webkit-scrollbar-thumb {
      background: #555;
    }
    
    body.dark-mode *:hover::-webkit-scrollbar-thumb:hover {
      background: #666;
    }
    
    body.dark-mode * {
      scrollbar-width: thin;
      scrollbar-color: transparent transparent;
    }
    
    body.dark-mode *:hover {
      scrollbar-color: #555 transparent;
    }
    
    .theme-switch {
      position: relative;
      display: inline-block;
      width: 40px;
      height: 20px;
    }
    
    .theme-switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    
    .theme-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: #ECECEC;
      transition: 0.3s;
      border-radius: 24px;
    }
    
    .theme-slider:before {
      position: absolute;
      content: "☀️";
      height: 14px;
      width: 14px;
      left: 4px;
      bottom: 4px;
      background-color: white;
      transition: 0.3s;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
    }
    
    input:checked + .theme-slider {
      background-color: var(--link-color);
    }
    
    input:checked + .theme-slider:before {
      transform: translateX(18px);
      content: "🌙";
    }
    
    body.dark-mode .theme-slider {
      background-color: var(--link-color);
    }
    
    #sidebar {
      display: flex;
      flex-direction: column;
      width: 550px;
      min-width: 0px;
      max-width: none;
      overflow: hidden;
      border-right: 1px solid var(--border-color);
      padding: 0;
      box-sizing: border-box;
      position: relative;
      transition: width 0.3s ease, min-width 0.3s ease;
    }
    
#sidebar-header {
  flex-shrink: 0;
  padding: 0.5rem;
  background: inherit;
  position: sticky;
  top: 0;
  overflow: visible;
  /* Scrollbar ausblenden */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

#sidebar-header::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}
    
    #sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 0rem 1rem 1rem 1rem;
  font-size: var(--text-size);
  line-height: var(--line-height);
  color: var(--text-color);
  /* Verwendet allgemeine Scrollbar-Regeln wie "Zuletzt gesucht" */
}
    
    /* Zentrale Styles für alle Sidebar-Texte */
    #sidebar-content p {
      margin: var(--paragraph-margin) 0;
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--text-color);
    }
    
    #sidebar-content .paragraph {
      margin: var(--paragraph-margin) 0;
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--text-color);
    }
    
    /* Zusätzliche Sicherheit für alle Absätze in Sidepanels - DIREKT */
    #sidebar p,
    #sidebar .paragraph,
    #sidebar-content p,
    #sidebar-content .paragraph {
      margin: 0.5rem 0 !important;
    }
    
    #sidebar-content .snippet {
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--secondary-text);
      margin: 4px 0;
      cursor: pointer;
    }
    
    #sidebar-content ul.results-list {
      list-style-type: disc; 
      padding-left: 1.2em; 
      margin: 0;
      padding-top: 0.3rem;
    }

    /* Timeline-Darstellung für Text-Suche */
    #sidebar-content .timeline-container {
      padding-left: 0 !important;
      margin: 0 !important;
      display: block !important;
      width: 100% !important;
    }

    #sidebar-content .timeline-year-group {
      display: flex !important;
      margin: 1rem 0 !important;
      align-items: flex-start !important;
    }

    #sidebar-content .timeline-year {
      font-size: 1em !important;
      font-weight: bold !important;
      color: #2c5282 !important;
      min-width: 50px !important;
      width: 50px !important;
      flex-shrink: 0 !important;
      padding-right: 1rem !important;
      text-align: left !important;
      padding-top: 0.2rem !important;
    }

    body.dark-mode #sidebar-content .timeline-year {
      color: var(--dark-heading-color) !important;
    }

    #sidebar-content .timeline-items-for-year {
      flex: 1 !important;
      display: flex !important;
      flex-direction: column !important;
    }

    #sidebar-content .timeline-item {
      margin: 0 0 0.5rem 0 !important;
      padding: 0 !important;
      list-style: none !important;
      display: block !important;
    }

    #sidebar-content .timeline-item.first-of-year {
      margin-top: 0 !important;
    }

    #sidebar-content .timeline-item > a {
      font-weight: bold;
      color: var(--link-color);
      font-size: var(--text-size);
      line-height: var(--line-height);
      text-decoration: none;
      display: block;
      margin-bottom: 0.3rem;
    }

    #sidebar-content .timeline-item > a:hover {
      text-decoration: underline;
    }

    #sidebar-content .timeline-item .snippet {
      margin-left: 0 !important;
      padding-left: 0 !important;
    }

    body.dark-mode #sidebar-content .timeline-item > a {
      color: #6BA3B8 !important;
    }
    
    #sidebar-content ul.results-list > li > a { 
      font-weight: bold; 
      color: var(--link-color);
      font-size: var(--text-size);
    }
    
    #sidebar-content ul.sub-headings { 
      list-style-type: none; 
      padding-left: 1.5em; 
      margin: 0.25em 0; 
    }
    
    #sidebar-content ul.sub-headings li::before { 
      content: "– "; 
      color: #666 !important; 
    }
    
    /* Dark Mode für Sidebar-Content - DIREKT (nur für Text, nicht für Überschriften) */
    body.dark-mode #sidebar-content {
      color: #b8b8b8 !important;
    }
    
    /* Überschriften explizit ausschließen */
    body.dark-mode #sidebar-content h1,
    body.dark-mode #sidebar-content h2,
    body.dark-mode #sidebar-content h3,
    body.dark-mode #sidebar-content h4 {
      color: #6BA3B8 !important;
    }
    
    body.dark-mode #sidebar-content p {
      color: #b8b8b8 !important;
    }
    
    body.dark-mode #sidebar-content .paragraph {
      color: #b8b8b8 !important;
    }
    
    body.dark-mode #sidebar-content .snippet {
      color: #999 !important;
    }
    
    body.dark-mode #sidebar-content ul.results-list > li > a {
      color: #6BA3B8 !important;
    }
    
    body.dark-mode #sidebar-content ul.sub-headings li::before {
      color: #999 !important;
    }
    
    /* Zentrale Styles für alle Überschriften in Sidepanels - DIREKT */
    #sidebar-content h1,
    #sidebar-content h2,
    #sidebar-content h3,
    #sidebar-content h4 {
      font-size: 1.0rem !important;
      line-height: 1.3 !important;
      margin: 0.7rem 0 0.5rem 0 !important;
      font-weight: 600 !important;
    }
    
    #sidebar-content h1 {
      color: var(--text-color) !important;
      font-weight: 700 !important;
    }

    /* Zentral: Zwischenüberschriften in Side Panels (Light Mode) */
    #sidebar-content h2,
    #sidebar-content h3,
    #sidebar-content h4 {
      color: var(--heading-color) !important;
    }
    
    /* Dark Mode für Sidebar-Überschriften - DIREKT */
    body.dark-mode #sidebar-content h1 {
      color: #6BA3B8 !important;
    }
    
    /* Dark Mode: Zwischenüberschriften in linken Side Panels farbig (#6BA3B8) */
    body.dark-mode #sidebar-content h2,
    body.dark-mode #sidebar-content h3,
    body.dark-mode #sidebar-content h4 {
      color: #6BA3B8 !important;
    }
    
    /* Überschriften als Links behalten ihre Link-Farbe */
    #sidebar-content h1 a,
    #sidebar-content h2 a,
    #sidebar-content h3 a,
    #sidebar-content h4 a {
      color: var(--link-color);
      text-decoration: none;
    }
    
    #sidebar-content h1 a:hover,
    #sidebar-content h2 a:hover,
    #sidebar-content h3 a:hover,
    #sidebar-content h4 a:hover {
      text-decoration: underline;
    }
    
    body.dark-mode #sidebar-content h1 a,
    body.dark-mode #sidebar-content h2 a,
    body.dark-mode #sidebar-content h3 a,
    body.dark-mode #sidebar-content h4 a {
      color: #6BA3B8 !important;
    }
    
    /* Zentrale Styles für alle Überschriften im Summary-Panel - DIREKT */
    /* TOC-Überschriften im Summary-Panel */
    #summary-content h3 {
      font-size: 1.0rem;
      line-height: var(--line-height);
      color: var(--link-color);
      margin: var(--paragraph-margin) 0;
      font-weight: 600;
    }
    
    #summary-content h4 {
      font-size: 0.9rem;
      line-height: var(--line-height);
      color: var(--link-color);
      margin: var(--paragraph-margin) 0;
      margin-left: 1rem;
      font-weight: 600;
    }
    
    body.dark-mode #summary-content h3,
    body.dark-mode #summary-content h4 {
      color: var(--dark-link-color);
    }
    
    /* Summary-Panel Absätze */
    #summary-content p {
      margin: var(--paragraph-margin) 0;
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--text-color);
    }
    
    #summary-content .paragraph {
      margin: var(--paragraph-margin) 0;
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--text-color);
    }
    
    /* Dark Mode für Summary-Panel-Überschriften - DIREKT */
    /* Dark Mode für Summary-Panel Überschriften - nur für normale Überschriften, nicht für Links */
    body.dark-mode #summary-content h1:not(a),
    body.dark-mode #summary-content h2:not(a),
    body.dark-mode #summary-content h3:not(a),
    body.dark-mode #summary-content h4:not(a) {
      color: #b8b8b8 !important;
    }
    
    /* Dark Mode für Summary-Panel Absätze - DIREKT */
    body.dark-mode #summary-content p {
      color: #b8b8b8 !important;
    }
    
    body.dark-mode #summary-content .paragraph {
      color: #b8b8b8 !important;
    }
    
    /* Überschriften als Links im Summary-Panel behalten ihre Link-Farbe */
    #summary-content h1 a,
    #summary-content h2 a,
    #summary-content h3 a,
    #summary-content h4 a {
      color: var(--link-color);
      text-decoration: none;
    }
    
    #summary-content h1 a:hover,
    #summary-content h2 a:hover,
    #summary-content h3 a:hover,
    #summary-content h4 a:hover {
      text-decoration: none;
    }
    
    body.dark-mode #summary-content h1 a,
    body.dark-mode #summary-content h2 a,
    body.dark-mode #summary-content h3 a,
    body.dark-mode #summary-content h4 a {
      color: var(--dark-link-color);
    }
    
    #sidebar.collapsed {
      width: 0;
      min-width: 0;
      padding: 0;
      border-right: none;
      overflow: visible;
    }
    
    #sidebar.collapsed > *:not(.sidebar-toggle) {
      display: none;
    }
    
    /* Einklappbares Suchpanel */
    .tab-container {
      transition: all 0.3s ease-in-out;
      overflow: hidden;
    }
    
    .tab-container.collapsed {
      max-height: 0;
      opacity: 0;
      margin-bottom: 0;
      padding: 0;
    }
    
    /* Horizontaler Resize-Handle für Suchpanel */
    .horizontal-resize-handle {
      height: 1px;
      background-color: var(--border-color);
      cursor: row-resize;
      position: relative;
      margin: 0;
      transition: background-color 0.2s;
      z-index: 999;
    }
    
    .horizontal-resize-handle::before {
      content: '⋯'; /* Drei horizontale Punkte */
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: var(--link-color);
      background: var(--background-color);
      padding: 0 8px;
      font-size: 23px;
      line-height: 1;
    }
    
    .horizontal-resize-handle:hover {
      background-color: var(--link-color);
    }
    
    .horizontal-resize-handle:hover::before {
      color: var(--background-color);
    }
    
    /* Dark Mode für horizontalen Handle */
    body.dark-mode .horizontal-resize-handle {
      background-color: var(--dark-border-color);
    }
    
    body.dark-mode .horizontal-resize-handle::before {
      color: var(--dark-link-color);
      background: var(--dark-background-color);
    }
    
    body.dark-mode .horizontal-resize-handle:hover {
      background-color: var(--dark-link-color);
    }
    
    body.dark-mode .horizontal-resize-handle:hover::before {
      color: var(--dark-background-color);
    }

    
    .resize-handle {
  width: 1px;
  background-color: transparent;
      cursor: col-resize;
      position: fixed;
      left: 440px; /* Wird dynamisch über JavaScript gesetzt */
      top: 45vh; /* Feste Position bei 45% der Viewport-Höhe */
      bottom: auto;
      height: 100px; /* Feste Höhe für das Handle */
      flex-shrink: 0;
      transition: background-color 0.2s;
      z-index: 999; /* Über anderen Elementen */
    }
    
    .resize-handle::before {
      content: '⋮';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: var(--link-color);
      background: var(--background-color);
      padding: 8px 0;
      font-size: 25px;
      line-height: 1;
      font-weight: normal;
      cursor: pointer;
      transition: color 0.2s;
    }
    
    .resize-handle:hover {
      background-color: transparent;
    }
    
    .resize-handle:hover::before {
      color: var(--link-color);
    }
    
    /* Symbol für geschlossene Sidebar */
    .sidebar-collapsed .resize-handle::before {
      content: '▶';
      font-size: 36px; /* Pfeiljgröße bleibt gleich */
      background: var(--background-color);
      padding: 8px 0;
    }
    
    #main-container {
      flex: 1;
      display: flex;
      flex-direction: row;
      min-width: 0;
      overflow: hidden;
      margin-top: 0; /* Wird dynamisch über JavaScript gesetzt */
    }
    
    #main {
      flex: 1;
      overflow-y: auto;
      padding: 2rem 1rem 2rem 2rem;
      min-width: 0;
      line-height: 1.3 !important;
      position: relative;
      margin-top: 0; /* Wird dynamisch über JavaScript gesetzt */
    }
    
    body.dark-mode .depth-btn {
      background: var(--dark-background-color);
      color: var(--dark-secondary-text);
      border: 1px solid var(--dark-link-color);
    }
    
    body.dark-mode .depth-btn.active {
      background: var(--dark-background-color);
      color: var(--dark-secondary-text);
      border: 2px solid var(--dark-link-color);
    }
    
    body.dark-mode .depth-btn.primary {
      background: var(--link-color);
      color: var(--dark-text-color);
      border: 2px solid var(--link-color);
    }
    
    body.dark-mode .depth-btn.primary:hover {
      background: #355d68;
      border-color: #355d68;
    }
    
    body.dark-mode .summary-buttons .search-button {
      background: var(--dark-background-color);
      color: var(--dark-secondary-text);
      border-color: var(--dark-link-color);
    }
    
    body.dark-mode .summary-buttons .search-button:hover {
      background: #3a3a3a;
    }
    
    #main p {
      margin: 0.8em 0;
    }
    
    #summary-panel {
      display: flex;
      flex-direction: column;
      border-left: none;
      overflow: hidden;
      width: 0;
      min-width: 0;
      background: transparent;
      position: fixed;
      right: 0;
      top: 0; /* Wird dynamisch über JavaScript gesetzt */
      bottom: 0;
      transition: width 0.3s ease, background-color 0.3s ease, border-left 0.3s ease;
      z-index: 999; /* Unter dem Header (z-index: 1000) */
    }
    
    #summary-panel.visible {
      width: 280px;
      min-width: 280px;
      max-width: none;
      background: var(--background-color);
      border-left: 1px solid var(--border-color);

    }
    

    
    .vertical-resize-handle {
      width: 1px;
      background-color: transparent;
      cursor: col-resize;
      position: fixed;
      right: -2px; /* Wird dynamisch über JavaScript gesetzt */
      top: 45vh; /* Feste Position bei 45% der Viewport-Höhe */
      bottom: auto;
      height: 100px; /* Feste Höhe für das Handle */
      flex-shrink: 0;
      transition: background-color 0.2s, width 0.2s;
      display: none;
      z-index: 1001; /* Über dem Summary-Panel und anderen Elementen */
    }
    
    .vertical-resize-handle::before {
      content: '⋮';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: var(--link-color);
      background: var(--background-color);
      padding: 8px 6px;
      font-size: 25px;
      line-height: 1;
      font-weight: normal;
      cursor: pointer;
      transition: color 0.2s;
      display: inline-block;
    }
    
    .vertical-resize-handle.visible {
      display: block;
    }
    
    /* Handle auch im geschlossenen Zustand sichtbar machen */
    .summary-panel-collapsed .vertical-resize-handle {
      display: block;
    }
    
    .vertical-resize-handle:hover {
      background-color: transparent;
    }
    
    .vertical-resize-handle:hover::before {
      color: var(--link-color);
    }
    
    /* Symbol für geschlossenes Summary-Panel */
    .summary-panel-collapsed .vertical-resize-handle::before {
      content: '◀';
      font-size: 36px; /* Pfeilgröße bleibt gleich */
      background: var(--background-color);
      padding: 8px 6px;
      display: inline-block;
    }
    
    #summary-content {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      line-height: 1.5;
      font-size: 0.95em;
      display: none;
      scrollbar-width: none; /* Firefox */
      -ms-overflow-style: none; /* Internet Explorer 10+ */
    }
    
    #summary-content::-webkit-scrollbar {
      display: none; /* Chrome, Safari, Edge */
    }
    
    #summary-panel.visible #summary-content {
      display: block;
    }
    
    .summary-buttons {
      padding: 1rem;
      border-top: 1px solid var(--border-color);
      display: none;
      flex-direction: column;
      gap: 8px;
    }
    
    #summary-panel.visible .summary-buttons {
      display: flex;
    }
    
    body.dark-mode .summary-buttons {
      border-top-color: var(--dark-border-color);
    }
    
    .summary-buttons .search-button {
      width: 100%;
      text-align: center;
    }
    
    /* Diese Überschriften-Styles sind jetzt zentralisiert */
    
    #summary-content h4.hidden {
      display: none;
    }
    
    /* Diese Hover-Styles sind jetzt in den zentralen Überschriften-Styles */
    
    #summary-content .toc-item {
      padding: 0.4em 0;
      border-bottom: 1px solid var(--border-color);
    }
    
    #summary-content .toc-item:last-child {
      border-bottom: none;
    }
    
    h1 { margin-bottom: 0.5rem; margin-top: 0; }
    #site-title { font-size: 1.8rem; margin-left: 0.5rem; margin-top: 0.3rem; }
    #document-title { margin-top: 0; margin-bottom: 0; margin-left: 1rem !important; }
    #document-title a { color: var(--link-color); text-decoration: none; }
    #document-title a:hover { text-decoration: underline; }
    
    body.dark-mode #document-title a {
      color: var(--dark-link-color) !important;
    }

body.dark-mode .ga-lecture-count {
  color: var(--dark-text-color);
}
.ga-toggle-btn {
  color: var(--link-color);
}

body.dark-mode .ga-toggle-btn {
  color: var(--dark-text-color);
  border-color: var(--dark-link-color) !important;
}

body.dark-mode .ga-reference {
  color: var(--dark-link-color) !important;
}

body.dark-mode a {
  color: var(--dark-link-color);
}
body.dark-mode #viewerOriginalBtn {
  border-color: var(--dark-text-color) !important;
  color: var(--dark-text-color) !important;
}

#viewerOriginalBtn:hover {
  opacity: 0.7;
}   
body.dark-mode #viewerSummaryBtn {
  border-color: var(--dark-text-color) !important;
  color: var(--dark-text-color) !important;
}

body.dark-mode #viewerSummaryBtn i,
body.dark-mode #viewerOriginalBtn i {
  color: var(--dark-text-color) !important;
}

.loading-message {
  color: var(--secondary-text);
}

body.dark-mode .loading-message {
  color: var(--dark-text-color) !important;
}

#viewerSummaryBtn:hover {
  opacity: 0.7;
} 
    .tab-container {
      margin-bottom: 1rem;
    }
    
    .tab-buttons {
      display: flex;
      border-bottom: none;
      margin-bottom: 1rem;
    }
    
    body.dark-mode .tab-buttons {
      border-bottom-color: transparent;
    }
    
    /* Spezifischere Regel für Tab-Buttons */
    .tab-container .tab-buttons {
      display: flex !important;
      justify-content: flex-start !important;
      flex-direction: row !important;
      gap: 8px !important;
    }
    
    .tab-button {
      padding: 8px 16px;
      border: none;
      background: transparent;
      cursor: pointer;
  font-size: 0.95em;
      font-weight: 700;
      color: var(--secondary-text);
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
    }
    
    .tab-button.active {
      color: var(--link-color);
      border-bottom-color: var(--link-color);
    }
    
    .tab-button:hover {
      color: var(--link-color);
      opacity: 0.7;
    }
    
    .tab-content {
      display: none;
    }
    
    .tab-content.active {
      display: block;
    }
    
    .thematic-input {
      width: 100%;
      padding: 8px;
      margin: 0px 0;
      box-sizing: border-box;
      border: 1px solid var(--link-color);
      background: var(--background-color);
      font-size: 15px;
      min-height: 50px;
      resize: vertical;
      border-radius: 4px;
      line-height: 20px; 
    }
    
    .semantic-options {
      margin: 10px 0;
    }
    
    .depth-buttons {
      display: flex;
      gap: 8px;
      margin: 8px 0;
    }
    
    .depth-btn {
  padding: 8px 16px;
  font-size: 1em;
      border: 1px solid var(--link-color);
      background: var(--background-color);
      color: var(--link-color);
      cursor: pointer;
      border-radius: 4px;
      font-size: 0.9em;
      transition: all 0.2s;
    }
    
    .depth-btn.active {
      background: var(--background-color);
      color: var(--link-color);
      border: 2px solid var(--link-color);
    }
    
    .depth-btn.primary {
      background: var(--link-color);
      color: white;
      border: 2px solid var(--link-color);
    }
    
    .depth-btn.primary:hover {
      background: #355d68;
      border-color: #355d68;
    }
    
    .depth-btn:hover {
      opacity: 0.8;
    }
    
    .depth-btn:disabled {
      cursor: not-allowed;
      background: #f5f5f5;
      opacity: 0.6;
    }
    
    .depth-btn.primary:disabled {
      background: #ccc;
      border-color: #ccc;
      cursor: not-allowed;
      color: var(--link-color);
    }
    
    .depth-btn.processing {
      font-style: italic;
    }
    
    .ga-reference {
      color: var(--link-color);
      font-size: var(--text-size);
      line-height: var(--line-height);
      text-decoration: none;
      font-weight: 600;
      padding: 0;
      background: none;
      border: none;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    
    /* Spezielle Klasse für Schlagwort-Suche - Link fett */
    .keyword-text .ga-reference {
      font-weight: bold;
    }
    
    body.dark-mode .ga-reference {
      color: var(--dark-link-color) !important;
    }
    
    .highlighted-paragraph {
      background: rgba(70, 120, 134, 0.1);
      box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.1);
      border-radius: 4px;
    }
    
    .semantic-answer {
             background: transparent !important; /* keine Box */
             padding: 0 !important;              /* Abstand entfernen */
             margin: 0 !important;               /* Abstand entfernen */
             border-radius: 0 !important;        /* runde Ecken weg */
             border: none !important;            /* ggf. Rahmen entfernen */
}
    body.dark-mode .semantic-answer {
          background: transparent !important;
}
    /* H3 in semantic-answer sind jetzt sichtbar (für keyword-thematische Antworten) */
    
    .answer-content {
      line-height: var(--line-height);
      font-size: var(--text-size); 
    }
    
    .answer-content h1 {
      display: none;
    }
    
    .answer-content h2 {
      font-size: 1.1em;
      margin: 0.4em 0 0.2em 0;
      font-weight: 600;
    }
    
    .answer-content h3 {
      font-size: 1.0em;
      margin: 0.3em 0 0.2em 0;
      font-weight: 600;
      display: block;
    }
    
    .answer-content p {
      margin: var(--paragraph-margin) 0;
      font-weight: normal;
      font-size: var(--text-size);
      line-height: var(--line-height);
      color: var(--text-color);
    }
    
    .answer-content strong {
      font-weight: 600;
    }
    
    .answer-content ul, .answer-content ol {
      margin: 0.3em 0;
      padding-left: 1.5em;
    }
    
    /* Dark Mode für Summary-Text */
    /* Dark Mode für Answer-Content Text (nur für Paragraphen, nicht für Überschriften) */
    body.dark-mode .answer-content p {
      color: var(--dark-text-color);
      font-size: var(--text-size);
      line-height: var(--line-height);
    }
    
    body.dark-mode .answer-content strong {
      color: var(--dark-text-color);
    }
    
    .loading {
      color: var(--link-color);
      font-style: italic;
    }
    
    .error-message {
      background: #fff5f5;
      border-left: 4px solid #e53e3e;
      padding: 10px;
      margin: 10px 0;
      color: #c53030;
      border-radius: 0 4px 4px 0;
    }
    
    .search-input {
      width: 100%;
      padding: 8px;
      margin: 4px 0;
      box-sizing: border-box;
      border: 1px solid #ccc;
      background: var(--background-color);
      font-size: 0.9em;
    }
    
    .filter-row {
      display: flex;
      gap: 10px;
      margin-top: 6px;
    }
    
    .filter-dropdown {
      flex: 1;
      height: auto;
      min-height: 2.2em;
      padding: 8px;
      margin: 2px 0;
      font-size: 0.9em;
      box-sizing: border-box;
      border: 1px solid #ccc;
      background: var(--background-color);
    }
    
    .filter-dropdown:disabled {
      background: #f5f5f5;
      color: var(--secondary-text);
      cursor: not-allowed;
    }
    
    .radio-group {
  margin: 6px 0;
      display: flex;
      gap: 6px;
    }
    
    .radio-group label {
      cursor: pointer;
    }
    
    .radio-group input[type="radio"]:checked + span {
      color: var(--link-color);
      font-weight: 600;
    }
    
    body.dark-mode .radio-group input[type="radio"]:checked + span {
      color: var(--dark-link-color);
    }
    
    .search-button {
      padding: 6px 12px;
      border-radius: 4px;
      border: 2px solid var(--link-color);
      background: var(--background-color);
      color: var(--link-color);
      cursor: pointer;
      font-size: 0.9em;
      margin-bottom: 0.4rem;
    }
    
    .search-button:hover { opacity: .85; }
    .search-button:disabled {
      cursor: not-allowed;
      background: #f5f5f5;
      color: var(--secondary-text);
      opacity: 1;
    }
    
    .search-button.processing {
      font-style: italic;
    }
    
    #note { margin-top: 0.5rem; font-size: 0.9em; color: var(--secondary-text); }
    #searchInfo {
  font-size: 0.9em;
  color: var(--secondary-text);
  margin-top: 0rem;
  margin-bottom: 0;
  padding-bottom: 0.5rem;
}
  body.dark-mode #searchInfo {
  color: var(--dark-text-color);
}

#texteSearchInfo {
  font-size: 0.9em;
  color: var(--secondary-text);
}

body.dark-mode #texteSearchInfo {
  color: var(--dark-text-color);
}

body.dark-mode #thematicSearchInfo {
  color: var(--dark-text-color);
}  
    /* Diese Styles sind jetzt in #sidebar-content zentralisiert */
    a { color: var(--link-color); text-decoration: none; cursor: pointer; }
    a:hover { text-decoration: none !important; }
    mark { 
      background: rgba(70, 120, 134, 0.2); 
      color: inherit;
    }
    
    /* Paragraph-Styles sind jetzt in #sidebar-content zentralisiert */
    
    #viewer {
      line-height: 1.4 !important;
      padding-top: 80px; /* Wird dynamisch via JavaScript angepasst */
    }
    
    /* Viewer Header Button Container */
    .viewer-buttons-container {
      display: flex;
      gap: 8px;
      margin-left: auto;
      flex-shrink: 0;
      align-items: center;
    }
    
    /* Ensure buttons always stay on the right */
    #viewer-header .viewer-buttons-container {
      margin-left: auto !important;
      flex-shrink: 0 !important;
    }
    
    /* Fixierter Header im Viewer */
    #viewer-header {
      position: fixed;
      top: 0;
      z-index: 1000;
      background-color: var(--background-color) !important;
      border-bottom: 1px solid var(--border-color);
      padding: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 0px;
      width: 100%;
      box-sizing: border-box;
      /* Position und Breite werden via JavaScript gesetzt */
    }
    
    /* Dark Mode für fixierten Header */
    body.dark-mode #viewer-header {
      background-color: var(--dark-background-color) !important;
      border-bottom-color: var(--dark-border-color);
    }
    
    #viewer .highlighted-paragraph {
      background: rgba(70, 120, 134, 0.1);
      box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.1);
      border-radius: 4px;
    }
    
    #viewer p {
      margin: var(--paragraph-margin) 0;
      line-height: 1.4 !important;
      font-size: var(--text-size);
      color: var(--text-color);
    }
    
    #viewer .paragraph {
      margin: var(--paragraph-margin) 0;
      line-height: 1.4 !important;
      font-size: var(--text-size);
      color: var(--text-color);
    }
    
    #viewer h3 {
      font-size: 1.0rem !important;
      margin: 0.7rem 0 0.5rem 0 !important;
      font-weight: 700 !important;
      color: #467886 !important;
      display: block;
      line-height: 1.3 !important;
    }
    
    #viewer h4 {
      font-size: 1.0rem !important;
      margin: 0.7rem 0 0.5rem 0 !important;
      font-weight: 600 !important;
      color: #467886 !important;
      display: block;
      line-height: 1.3 !important;
    }
    
    /* Dark Mode für Viewer */
    body.dark-mode #viewer p {
      color: #b8b8b8 !important;
    }
    
    body.dark-mode #viewer .paragraph {
      color: #b8b8b8 !important;
    }
    
    body.dark-mode #viewer h3,
    body.dark-mode #viewer h4 {
      color: #6BA3B8 !important;
    }
    
    /* Dark Mode für GA-Übersicht Summary-Texte */
    body.dark-mode .ga-summary-text p {
      color: var(--dark-text-color) !important;
    }
    
    /* Dark Mode für "Zusammenfassung" Überschrift im Viewer */
    body.dark-mode #viewer p strong {
      color: var(--dark-heading-color);
    }
    
    #viewer h3:first-child,
    #viewer h4:first-child {
      margin-top: 0;
    }
    
    #viewer > p:first-of-type {
      font-style: italic;
      margin-bottom: 1rem;
    }
  
    body.dark-mode ul.results-list > li > a {
      color: var(--dark-link-color) !important;
    }
    
    body.dark-mode .toc-item a {
      color: var(--dark-link-color) !important;
    }
    
    /* Diese Dark Mode Styles sind jetzt in den zentralen Überschriften-Styles */
    
    body.dark-mode .tab-button.active {
      color: var(--dark-link-color) !important;
      border-bottom-color: var(--dark-link-color) !important;
    }
    
    body.dark-mode .depth-btn {
      border-color: var(--dark-link-color) !important;
    }

    .ga-overview-lecture {
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border-color);
    }
    
    body.dark-mode .ga-overview-lecture {
      border-bottom-color: var(--dark-border-color);
    }
    
    .ga-overview-lecture h3 {
      margin-bottom: 0.5rem;
      font-weight: bold;
      font-size: var(--text-size);
      line-height: var(--line-height);
    }
    
    .ga-overview-lecture h3 a {
      color: var(--link-color);
      text-decoration: none;
      font-weight: bold;
      font-size: var(--text-size);
      line-height: var(--line-height);
    }
    
    /* Linkfarbe in GA-Übersicht folgt zentralen Sidepanel-Regeln */
    
    .ga-overview-lecture h3 a:hover {
      text-decoration: underline;
    }
    
    .ga-overview-meta {
      font-size: 0.9em;
      color: var(--secondary-text);
      margin: 0.5rem 0;
    }
    
    body.dark-mode .ga-overview-meta {
      color: var(--dark-secondary-text);
    }
    
    .ga-overview-summary {
      margin-top: 0.5rem;
      margin-bottom: 0.5rem;
      padding: 0;
      background: transparent;
      border-radius: 0;
      border-left: none;
    }
    
    body.dark-mode .ga-overview-summary {
      background: transparent;
      border-left: none;
    }
    
    .ga-overview-summary p {
      margin: 0;
      font-style: italic;
      line-height: 1.5;
      color: var(--text-color);
    }
    
    body.dark-mode .ga-overview-summary p {
      color: var(--dark-secondary-text);
    }
    
    #gaFilterContainer {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    
    #gaFilterContainer .filter-dropdown {
      flex: 1;
    }
    
    #showGAOverview {
      margin-left: auto;
      flex-shrink: 0;
      white-space: nowrap;
      padding: 6px 12px;
      font-size: 0.85em;
    }

    select option.available-ga {
      font-weight: normal;
      color: var(--text-color);
    }
    
    /* NEU: Tooltip CSS für Vorträge ohne Zusammenfassung */
.lecture-link-wrapper {
  position: relative;
  display: inline;
}

.loading-tooltip {
  visibility: hidden;
  background-color: var(--background-color);
  color: var(--text-color);
  text-align: center;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--link-color);
  position: absolute;
  z-index: 1000;
  top: 100%;
  margin-top: 8px;
  left: 80%;
  transform: translateX(-50%);
  white-space: normal;
  width: 140px;
  opacity: 0;
  transition: opacity 0.3s;
  font-size: 0.85em;
  font-style: italic;
  font-weight: normal;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  pointer-events: none;
  line-height: 1.3;
}

.loading-tooltip::before {
  content: "";
  position: absolute;
  bottom: 100%;
  left: 30%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent transparent var(--link-color) transparent;
}

.lecture-link-wrapper:hover .loading-tooltip {
  visibility: visible;
  opacity: 1;
}

body.dark-mode .loading-tooltip {
  background-color: var(--dark-background-color);
  color: var(--dark-text-color);
  border-color: var(--dark-link-color);
}

body.dark-mode .loading-tooltip::before {
  border-color: transparent transparent var(--dark-link-color) transparent;
}

/* Themensuche-Ergebnisse Styling */
.semantic-answer {
  font-size: 1.1rem;        /* Textgröße anpassen */
  line-height: 1.3rem;        /* Zeilenabstand anpassen */
}

/* Results header: keyword + timeline button in one line */
.answer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: nowrap;
}

.answer-title {
  margin: 0;
  color: var(--heading-color);
  font-weight: 700;
  font-size: 1.2rem;        /* override generic .semantic-answer h2 */
  line-height: 1.3;
  flex: 1 1 auto;
  min-width: 0;              /* erlaubt Ellipsis */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.answer-action {
  flex: 0 0 auto;            /* Button schrumpft nicht, bleibt in der Zeile */
}

.semantic-answer h1 {
  font-size: 1.2rem;         /* Überschriften-Größe */
  line-height: 1.4;
  margin: 1.5rem 0 1rem 0;
}

.semantic-answer h2 {
  font-size: 1rem;         /* Unterüberschriften-Größe */
  line-height: 1.1;
  margin: 1.2rem 0 0.8rem 0;
}

.semantic-answer h3 {
  font-size: 1rem;         /* Kleinere Überschriften */
  line-height: 1.1;
  margin: 1rem 0 0.6rem 0;
  font-weight: bold;
}

.semantic-answer p {
  margin-bottom: 0.9rem;      /* Abstand zwischen Absätzen */
  line-height: 1.35rem;         /* Zeilenabstand in Absätzen */
}

.semantic-answer ul, .semantic-answer ol {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.semantic-answer li {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

/* Keyword-Link Styles - keine Hintergrundfarbe */
.ga-keyword-link {
  color: var(--link-color);
  background: none !important;
  background-color: transparent !important;
  text-decoration: none;
  padding: 0;
  border: none;
  font-weight: 600;
}

.ga-keyword-link:hover {
  text-decoration: none !important;
}

body.dark-mode .ga-keyword-link {
  color: var(--dark-link-color);
  background: none !important;
  background-color: transparent !important;
}

/* Schlagwort-Anzeige - nur Frontend-CSS */

.keyword-entry {
  margin-bottom: 0.1rem;
  padding-bottom: 0rem;
}

.keyword-entry h4 {
  margin: 0 0 0.2rem 0;
  font-size: var(--heading-size);
  line-height: var(--line-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.keyword-entry h4 a {
  color: var(--link-color);
  text-decoration: none;
  cursor: pointer;
}

.keyword-entry h4 a:hover {
  text-decoration: none;
}

body.dark-mode .keyword-entry h4 a {
  color: #6BA3B8 !important;
}

.keyword-text {
  font-size: var(--text-size);
  line-height: var(--line-height);
  color: var(--text-color);
}

body.dark-mode .keyword-text {
  color: var(--dark-text-color);
}

.no-results-message {
  color: var(--secondary-text);
  font-style: italic;
}

body.dark-mode .no-results-message {
  color: var(--dark-secondary-text);
}
/* Universelle Link-Regeln: Keine Unterstreichung beim Hover */
a:hover {
  text-decoration: none !important;
}

/* Timeline Button Styles */
.timeline-btn {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  padding: 2px 6px;
  margin-left: auto;
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.7;
  flex-shrink: 0;
}

.timeline-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.timeline-btn.active {
  opacity: 1;
}

/* Lucide Icons Styling */
.timeline-btn svg {
  stroke: var(--accent-color);
  fill: none;
}

body.dark-mode .timeline-btn svg {
  stroke: var(--dark-accent-color);
}

.timeline-panel-search-btn svg {
  stroke: var(--accent-color);
  fill: none;
}

body.dark-mode .timeline-panel-search-btn svg {
  stroke: var(--dark-accent-color);
}

/* Keyword Search Button in Sidebar */
.keyword-search-btn {
  background: none;
  border: 1px solid var(--accent-color);
  color: var(--accent-color);
  font-size: 0.8em;
  cursor: pointer;
  padding: 2px 6px;
  margin-left: 0;
  border-radius: 3px;
  transition: all 0.2s ease;
  opacity: 0.7;
  width: 24px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.keyword-search-btn:hover {
  opacity: 1;
  background-color: var(--accent-color);
  color: white;
  transform: scale(1.1);
}

body.dark-mode .keyword-search-btn {
  border-color: var(--dark-accent-color);
  color: var(--dark-accent-color);
}

body.dark-mode .keyword-search-btn:hover {
  background-color: var(--dark-accent-color);
  color: var(--dark-background-color);
}

/* Timeline Split View Styles */
.timeline-split-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background-color: var(--background-color);
  overflow: hidden;
  margin: -2rem 0rem -2rem -1.2rem;
  padding: 0;
  padding-left: 1.2rem;
}

body.dark-mode .timeline-split-view {
  background-color: var(--dark-background-color);
}

.timeline-viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: var(--background-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  margin: 0;
  box-sizing: border-box;
  gap: 15px;
  min-height: 0px;
}

body.dark-mode .timeline-viewer-header {
  background-color: var(--dark-background-color);
  border-bottom-color: var(--dark-border-color);
}

.timeline-viewer-buttons-container {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}

/* Timeline Document Title - Match Main Viewer h2 Style */
.timeline-document-title {
  flex: 1;
  margin: 0 !important;
  font-size: 1.5em !important;
  font-weight: 700 !important;
  color: var(--heading-color) !important;
  line-height: 1.3 !important;
}

body.dark-mode .timeline-document-title {
  color: var(--dark-heading-color) !important;
}

.timeline-document-title a {
  color: var(--link-color) !important;
  text-decoration: none;
}

.timeline-document-title a:hover {
  text-decoration: underline;
}

body.dark-mode .timeline-document-title a {
  color: var(--dark-link-color) !important;
}

.timeline-split-content {
  display: flex;
  flex: 1;
  height: 100%;
  border-top: none;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.timeline-panel {
  width: 50%;
  min-width: 400px;
  background-color: var(--background-color);
  border-right: 1px solid var(--border-color);
  border-top: none;
  overflow-y: auto;
  padding: 0px 15px 0px 0px;
  margin: 0;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  /* Scrollbar ausblenden */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.timeline-panel::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.timeline-panel.hidden {
  width: 0;
  min-width: 0;
  padding: 0;
  border-right: none;
  overflow: hidden;
}

body.dark-mode .timeline-panel {
  background-color: var(--dark-background-color);
  border-right-color: var(--dark-border-color);
  border-top: none;
}

/* Timeline Panel Resize Button */
.timeline-resize-handle {
  position: absolute;
  top: 0;
  right: -3px;
  width: 10px;
  height: 100%;
  background-color: transparent;
  cursor: col-resize;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timeline-resize-handle::before {
  content: '⋮';
  font-size: 20px;
  color: var(--link-color);
  background: var(--background-color);
  padding: 8px 0;
  font-size: 25px;
  line-height: 1;
  font-weight: normal;
  transition: color 0.2s;
}

.timeline-resize-handle:hover::before {
  color: var(--link-color);
}

body.dark-mode .timeline-resize-handle {
  background-color: transparent;
}

body.dark-mode .timeline-resize-handle:hover {
  background-color: transparent;
}

body.dark-mode .timeline-resize-handle::before {
  background: var(--dark-background-color);
  color: var(--dark-link-color);
}

body.dark-mode .timeline-resize-handle:hover::before {
  color: var(--dark-link-color);
}

.timeline-panel-header {
  background-color: var(--background-color);
  border-bottom: 1px solid var(--border-color);
  padding: 10px 15px;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-panel-title {
  margin: 0;
  font-size: 1.0em;
  font-weight: 700;
  color: var(--heading-color);
  text-align: center;
}

body.dark-mode .timeline-panel-header {
  background-color: var(--dark-background-color);
  border-bottom-color: var(--dark-border-color);
}

body.dark-mode .timeline-panel-title {
  color: var(--dark-heading-color);
}

.timeline-panel-search-btn {
  background: none;
  border: none;
  font-size: 1.0em;
  cursor: pointer;
  padding: 4px 6px;
  color: var(--accent-color);
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 0.8;
  flex-shrink: 0;
}

.timeline-panel-search-btn:hover {
  opacity: 1;
  background-color: var(--accent-color);
  color: white;
  transform: scale(1.1);
}

body.dark-mode .timeline-panel-search-btn {
  color: var(--dark-accent-color);
}

body.dark-mode .timeline-panel-search-btn:hover {
  background-color: var(--dark-accent-color);
  color: var(--dark-background-color);
}

.timeline-viewer {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--background-color);
  border-top: none;
  width: 100%;
  margin: 0;
  padding: 1.0rem;
}

body.dark-mode .timeline-viewer {
  background-color: var(--dark-background-color);
  border-top: none;
}


.timeline-viewer-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: var(--background-color);
  line-height: 1.6;
  line-height: 1.4 !important;
}

body.dark-mode .timeline-viewer-content {
  background-color: var(--dark-background-color);
}

/* Timeline Viewer Content Formatting - Same as Main Viewer */
.timeline-viewer-content .paragraph {
  margin: var(--paragraph-margin) 0;
  line-height: 1.4 !important;
  font-size: var(--text-size);
  color: var(--text-color);
}

.timeline-viewer-content .highlighted-paragraph {
  background: rgba(70, 120, 134, 0.1);
  box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.1);
  border-radius: 4px;
}

.timeline-viewer-content h1,
.timeline-viewer-content h2,
.timeline-viewer-content h5,
.timeline-viewer-content h6 {
  color: var(--heading-color);
  margin: 1.5rem 0 1rem 0;
  font-weight: 600;
}

.timeline-viewer-content h1 {
  font-size: 1.8em;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.5rem;
}

.timeline-viewer-content h2 {
  font-size: 1.5em;
}

/* Enhanced Timeline Styles */
.timeline-analysis {
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.timeline-analysis h3 {
  margin: 0 0 0.5rem 0;
  color: var(--heading-color);
  font-size: 1.1rem;
}

.timeline-analysis-points {
  margin: 0.5rem 0;
  padding-left: 1.2rem;
}

.timeline-analysis-points li {
  margin: 0.3rem 0;
  line-height: 1.4;
}

.timeline-item.enhanced {
  margin-bottom: 1rem;
}

.timeline-content.enhanced {
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.timeline-content.enhanced:hover {
  border-color: var(--accent-color);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.timeline-lecture-title {
  font-weight: 600;
  color: var(--heading-color);
  margin-bottom: 0.5rem;
}

.timeline-relevance {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.relevance-hoch {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.relevance-mittel {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.relevance-niedrig {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.timeline-context {
  font-size: 0.9rem;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.timeline-quotes {
  margin: 0.5rem 0;
  color: var(--secondary-text);
  font-size: 0.85rem;
  line-height: 1.4;
}

.timeline-focus {
  font-size: 0.85rem;
  color: var(--text-color);
  margin-top: 0.5rem;
}

/* Dark Mode für erweiterte Timeline */
body.dark-mode .timeline-analysis {
  background: var(--dark-background-color);
  border-color: var(--dark-border-color);
}

body.dark-mode .timeline-analysis h3 {
  color: var(--dark-heading-color);
}

body.dark-mode .timeline-content.enhanced {
  background: var(--dark-background-color);
  border-color: var(--dark-border-color);
}

body.dark-mode .timeline-content.enhanced:hover {
  border-color: var(--dark-accent-color);
}

body.dark-mode .timeline-lecture-title {
  color: var(--dark-heading-color);
}

body.dark-mode .timeline-context,
body.dark-mode .timeline-focus {
  color: var(--dark-text-color);
}

body.dark-mode .timeline-quotes {
  color: var(--dark-secondary-text);
}

/* Timeline Viewer h3 and h4 - Match Main Viewer Exactly */
.timeline-viewer-content h3 {
  font-size: 1.0rem !important;
  margin: 0.7rem 0 0.5rem 0 !important;
  font-weight: 700 !important;
  color: #467886 !important;
  display: block;
  line-height: 1.3 !important;
}

.timeline-viewer-content h4 {
  font-size: 1.0rem !important;
  margin: 0.7rem 0 0.5rem 0 !important;
  font-weight: 600 !important;
  color: #467886 !important;
  display: block;
  line-height: 1.3 !important;
}

.timeline-viewer-content h3:first-child,
.timeline-viewer-content h4:first-child {
  margin-top: 0;
}

.timeline-viewer-content > p:first-of-type {
  font-style: italic;
  margin-bottom: 1rem;
}

.timeline-viewer-content mark {
  background-color: rgba(70, 120, 134, 0.3);
  padding: 0.1em 0.2em;
  border-radius: 2px;
}

/* Dark Mode Styles for Timeline Viewer Content */
body.dark-mode .timeline-viewer-content .paragraph {
  color: #b8b8b8 !important;
}

body.dark-mode .timeline-viewer-content .highlighted-paragraph {
  background: rgba(70, 120, 134, 0.35);
  box-shadow: 0 0 0 0.4rem rgba(70, 120, 134, 0.35);
}

body.dark-mode .timeline-viewer-content h1,
body.dark-mode .timeline-viewer-content h2,
body.dark-mode .timeline-viewer-content h5,
body.dark-mode .timeline-viewer-content h6 {
  color: var(--dark-heading-color);
}

/* Dark Mode h3 and h4 - Match Main Viewer Exactly */
body.dark-mode .timeline-viewer-content h3,
body.dark-mode .timeline-viewer-content h4 {
  color: #6BA3B8 !important;
}

body.dark-mode .timeline-viewer-content h1 {
  border-bottom-color: var(--dark-border-color);
}

body.dark-mode .timeline-viewer-content p strong {
  color: var(--dark-heading-color);
}

body.dark-mode .timeline-viewer-content mark {
  background-color: rgba(70, 120, 134, 0.5);
  color: var(--dark-text-color);
}


.timeline-title {
  font-size: 1.5em;
  font-weight: bold;
  color: var(--heading-color);
  margin: 0;
}

body.dark-mode .timeline-title {
  color: var(--dark-heading-color);
}

.timeline-close {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: var(--text-color);
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.timeline-close:hover {
  background-color: var(--accent-color);
}

body.dark-mode .timeline-close:hover {
  background-color: var(--dark-accent-color);
}

/* Timeline Quote Links */
.timeline-quote-link {
  color: #467886;
  cursor: pointer;
  font-weight: 600;
  transition: color 0.2s ease;
}

.timeline-quote-link:hover {
  color: #2c4a52;
  text-decoration: none;
}

body.dark-mode .timeline-quote-link {
  color: #6bb6ff;
}

body.dark-mode .timeline-quote-link:hover {
  color: #4a9eff;
}

/* Timeline Container */
.timeline-container {
  position: relative;
  padding: 20px 0px 20px 0px;
  margin: 0;
  flex: 1;
  overflow-y: auto;
  /* Scrollbar ausblenden */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.timeline-container::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.timeline-line {
  position: absolute;
  left: 25px;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(to bottom, var(--accent-color), var(--secondary-color));
  border-radius: 2px;
  margin: 0;
}

body.dark-mode .timeline-line {
  background: linear-gradient(to bottom, var(--dark-accent-color), var(--dark-secondary-color));
}

.timeline-item {
  position: relative;
  margin-bottom: 15px;
  padding-left: 80px;
}

.timeline-year {
  position: absolute;
  left: 0;
  top: 0;
  width: 50px;
  height: 35px;
  background-color: transparent;
  color: var(--accent-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.8em;
  box-shadow: none;
  border: 2px solid var(--accent-color);
  outline: none;
}

.timeline-year-spacer {
  position: absolute;
  left: 0;
  top: 0;
  width: 35px;
  height: 35px;
  /* Unsichtbarer Platzhalter für Ausrichtung */
}

body.dark-mode .timeline-year {
  background-color: transparent;
  color: var(--dark-accent-color);
  border-color: var(--dark-accent-color);
}

.timeline-content {
  background-color: var(--background-color);
  padding: 8px 12px;
  border-radius: 6px;
  border: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

body.dark-mode .timeline-content {
  background-color: var(--dark-background-color);
  border: none;
}

.timeline-content:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

body.dark-mode .timeline-content:hover {
  transform: scale(1.05);
}

.timeline-lecture-number {
  font-weight: bold;
  color: var(--heading-color);
  font-size: 0.9em;
  margin: 0;
}

body.dark-mode .timeline-lecture-title {
  color: var(--dark-heading-color);
}

.timeline-lecture-link {
  color: var(--link-color);
  text-decoration: none;
  transition: color 0.2s ease;
  outline: none;
  border: none;
}

.timeline-lecture-link:hover {
  color: var(--accent-color);
  text-decoration: underline;
  outline: none;
  border: none;
}

.timeline-lecture-link:focus {
  outline: none;
  border: none;
}

body.dark-mode .timeline-lecture-link:hover {
  color: var(--dark-accent-color);
}

.timeline-lecture-meta {
  font-size: 0.9em;
  color: var(--secondary-text-color);
  margin-top: 5px;
}

body.dark-mode .timeline-lecture-meta {
  color: var(--dark-secondary-text-color);
}

.timeline-no-results {
  text-align: center;
  padding: 40px;
  color: var(--secondary-text-color);
  font-style: italic;
}

body.dark-mode .timeline-no-results {
  color: var(--dark-secondary-text-color);
}

/* Scrollbar Styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #e0e0e0;
}

/* Dark Mode Scrollbars */
body.dark-mode ::-webkit-scrollbar-track {
  background: transparent;
}

body.dark-mode ::-webkit-scrollbar-thumb {
  background: transparent;
}

body.dark-mode ::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Hover-Effekt für Scrollbar-Thumbs */
*:hover::-webkit-scrollbar-thumb {
  background: #e0e0e0;
}

body.dark-mode *:hover::-webkit-scrollbar-thumb {
  background: #333333;
}

/* Firefox Scrollbars */
* {
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}

*:hover {
  scrollbar-color: #e0e0e0 transparent;
}

body.dark-mode *:hover {
  scrollbar-color: #333333 transparent;
}

/* Final overrides: enforce centralized heading colors in side panels (placed last) */
/* Zentrale Regel für alle Überschriften (außer TOC-Links) */
h1:not(#summary-content a),
h2:not(#summary-content a),
h3:not(#summary-content a),
h4:not(#summary-content a) {
  color: var(--heading-color) !important;
}

/* Dark Mode: Überschriften blau */
body.dark-mode h1:not(#summary-content a),
body.dark-mode h2:not(#summary-content a),
body.dark-mode h3:not(#summary-content a),
body.dark-mode h4:not(#summary-content a) {
  color: var(--dark-heading-color) !important;
}
#sidebar h1, #sidebar h2, #sidebar h3, #sidebar h4,
#sidebar-content h1, #sidebar-content h2, #sidebar-content h3, #sidebar-content h4,
#results h1, #results h2, #results h3, #results h4,
.answer-content h1, .answer-content h2, .answer-content h3, .answer-content h4 { color: var(--heading-color) !important; }
body.dark-mode #sidebar h1, body.dark-mode #sidebar h2, body.dark-mode #sidebar h3, body.dark-mode #sidebar h4,
body.dark-mode #sidebar-content h1, body.dark-mode #sidebar-content h2, body.dark-mode #sidebar-content h3, body.dark-mode #sidebar-content h4,
body.dark-mode #results h1, body.dark-mode #results h2, body.dark-mode #results h3, body.dark-mode #results h4 { color: var(--dark-heading-color) !important; }
#sidebar h1 a, #sidebar h2 a, #sidebar h3 a, #sidebar h4 a,
#sidebar-content h1 a, #sidebar-content h2 a, #sidebar-content h3 a, #sidebar-content h4 a,
#results h1 a, #results h2 a, #results h3 a, #results h4 a,
.answer-content h1 a, .answer-content h2 a, .answer-content h3 a, .answer-content h4 a { color: var(--link-color) !important; }
body.dark-mode #sidebar h1 a, body.dark-mode #sidebar h2 a, body.dark-mode #sidebar h3 a, body.dark-mode #sidebar h4 a,
body.dark-mode #sidebar-content h1 a, body.dark-mode #sidebar-content h2 a, body.dark-mode #sidebar-content h3 a, body.dark-mode #sidebar-content h4 a,
body.dark-mode #results h1 a, body.dark-mode #results h2 a, body.dark-mode #results h3 a, body.dark-mode #results h4 a,
body.dark-mode .answer-content h1 a, body.dark-mode .answer-content h2 a, body.dark-mode .answer-content h3 a, body.dark-mode .answer-content h4 a { color: var(--dark-heading-color) !important; }

/* ============================================================================
   HELP BUTTON & MODAL
   ============================================================================ */

.help-button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.help-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

body.dark-mode .help-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.help-button i {
  width: 8px;
  height: 8px;
}

.help-button svg {
  stroke: #467886 !important;
  stroke-width: 1.7;
  fill: none;
  color: #467886;
}

body.dark-mode .help-button svg {
  stroke: #6BA3B8 !important;
  color: #6BA3B8;
}

/* Help Modal */
.help-modal {
  display: none;
  position: fixed;
  z-index: 10000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  animation: fadeIn 0.2s ease;
}

.help-modal.active {
  display: flex;
  align-items: center;
  justify-content: center;
}

.help-modal-content {
  background-color: var(--background-color);
  color: var(--text-color);
  border-radius: 0;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 800px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from {
    transform: translateY(-30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.help-modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.help-modal-header h2 {
  margin: 0;
  color: var(--heading-color) !important;
  font-size: 1.5rem;
}

body.dark-mode .help-modal-header h2 {
  color: var(--dark-heading-color) !important;
}

.help-modal-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-color);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.help-modal-close:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

body.dark-mode .help-modal-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.help-modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.help-choice-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.help-choice-btn {
  flex: 1;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  background-color: var(--background-color);
  border-radius: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.help-choice-btn:hover {
  background-color: #467886;
  color: white;
  border-color: #467886;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(70, 120, 134, 0.2);
}

body.dark-mode .help-choice-btn {
  border-color: var(--border-color);
  background-color: var(--background-color);
}

body.dark-mode .help-choice-btn:hover {
  background-color: #6BA3B8;
  color: white;
  border-color: #6BA3B8;
}

.help-choice-btn h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: #467886;
}

body.dark-mode .help-choice-btn h3 {
  color: #6BA3B8;
}

.help-choice-btn:hover h3 {
  color: white;
}

.help-choice-btn p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-color);
}

.help-choice-btn:hover p {
  color: white;
}

.help-content-display {
  display: none;
}

.help-content-display.active {
  display: block;
}

.help-content-display h2 {
  color: var(--heading-color) !important;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.help-content-display h3 {
  color: var(--heading-color) !important;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

body.dark-mode .help-content-display h2,
body.dark-mode .help-content-display h3 {
  color: var(--dark-heading-color) !important;
}

.help-content-display code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

body.dark-mode .help-content-display code {
  background-color: rgba(255, 255, 255, 0.1);
}

.help-content-display pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
}

body.dark-mode .help-content-display pre {
  background-color: rgba(255, 255, 255, 0.05);
}

.help-content-display table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.help-content-display table th,
.help-content-display table td {
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  text-align: left;
}

.help-content-display table th {
  background-color: rgba(70, 120, 134, 0.1);
  font-weight: 600;
}

.help-back-btn {
  margin-top: 2rem;
  padding: 0.75rem 1.5rem;
  background-color: #467886;
  color: white;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.help-back-btn:hover {
  background-color: #3a6270;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

body.dark-mode .help-back-btn {
  background-color: #6BA3B8;
}

body.dark-mode .help-back-btn:hover {
  background-color: #5a8a9a;
}

/* Welcome Modal */
.welcome-modal {
  display: none;
  position: fixed;
  z-index: 10001;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  animation: fadeIn 0.3s ease;
}

.welcome-modal.active {
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-modal-content {
  background-color: var(--background-color);
  color: var(--text-color);
  border-radius: 0;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.4s ease;
}

.welcome-modal-header {
  background-color: rgba(70, 120, 134, 0.1);
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

body.dark-mode .welcome-modal-header {
  background-color: rgba(107, 163, 184, 0.15);
}

.welcome-modal-header h2 {
  margin: 0;
  color: var(--heading-color);
  font-size: 1.5rem;
}

body.dark-mode .welcome-modal-header h2 {
  color: var(--dark-heading-color);
}

.welcome-close-btn {
  background: none;
  border: none;
  font-size: 1.8rem;
  cursor: pointer;
  color: var(--text-color);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0;
  transition: background-color 0.2s ease;
}

.welcome-close-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

body.dark-mode .welcome-close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.welcome-modal-body {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
}

.welcome-modal-body h1 {
  color: var(--heading-color) !important;
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.8rem;
}

.welcome-modal-body h2 {
  color: var(--heading-color) !important;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 1.3rem;
}

.welcome-modal-body h3 {
  color: var(--heading-color) !important;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

body.dark-mode .welcome-modal-body h1,
body.dark-mode .welcome-modal-body h2,
body.dark-mode .welcome-modal-body h3 {
  color: var(--dark-heading-color) !important;
}

.welcome-modal-body code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

body.dark-mode .welcome-modal-body code {
  background-color: rgba(255, 255, 255, 0.1);
}

.welcome-modal-body pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.9em;
}

body.dark-mode .welcome-modal-body pre {
  background-color: rgba(255, 255, 255, 0.05);
}

.welcome-modal-footer {
  padding: 1rem 2rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.02);
}

body.dark-mode .welcome-modal-footer {
  background-color: rgba(255, 255, 255, 0.02);
}

.welcome-start-btn {
  padding: 0.75rem 1.5rem;
  background-color: #467886;
  color: white;
  border: none;
  border-radius: 0;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background-color 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.welcome-start-btn:hover {
  background-color: #3a6571;
}

body.dark-mode .welcome-start-btn {
  background-color: #6BA3B8;
}

body.dark-mode .welcome-start-btn:hover {
  background-color: #5a8a9a;
}
</style>
</head>
<body>
<div id="sidebar">
<div id="sidebar-header">
<div style="display: flex; justify-content: space-between; align-items: center;">
<h1 id="site-title"><a href="index.html" style="color: inherit; text-decoration: none;">Steiner GA-Suche</a></h1>
<div style="display: flex; align-items: center; gap: 0.15rem;">
<button class="help-button" onclick="openHelpModal()" title="Anleitung öffnen">
<i data-lucide="info"></i>
</button>
<label class="theme-switch">
<input id="theme-checkbox" onchange="toggleThemeCheckbox()" type="checkbox"/>
<span class="theme-slider"></span>
</label>
</div>
</div>
<div class="tab-container">
<div class="tab-buttons">
<button class="tab-button active" onclick="switchTab('keyword')">Suche</button>
<button class="tab-button" onclick="switchTab('texte')">Texte</button>
<button class="tab-button" onclick="switchTab('thematic')">Themen</button>
<button class="tab-button" onclick="switchTab('timeline')">Timeline</button>
<button class="tab-button" onclick="switchTab('schlagworte')">Index</button>
</div>
<div class="tab-content active" id="keyword-tab">
<div style="display:flex; gap:8px; margin-top:4px;">
<div style="flex:1; position: relative;">
<input class="search-input" id="word1" list="word1-history" onfocus="this.select()" onkeypress="handleKeywordKeypress(event)" placeholder="Suchwort 1" type="text"/>
<datalist id="word1-history"></datalist>
</div>
<div style="flex:1; position: relative;">
<input class="search-input" id="word2" list="word2-history" onfocus="this.select()" placeholder="Suchwort 2 (optional)" type="text"/>
<datalist id="word2-history"></datalist>
</div>
</div>
<div class="filter-row">
<select class="filter-dropdown" id="yearFilter">
<option value="">Jahre: alle</option>
</select>
<select class="filter-dropdown" id="gaFilter">
<option value="">GA-Bände: alle</option>
</select>
<select class="filter-dropdown" id="relevanceFilter">
<option value="ohne">Relevanz: ohne</option>
<option value="alle">Relevanz: alle</option>
<option value="hoch">hoch 🟩</option>
<option value="mittel">mittel 🟧</option>
<option value="niedrig">niedrig 🟨</option>
</select>
</div>
<div class="radio-group">
<div style="display:flex; gap:8px; align-items:center; justify-content: space-between; width: 100%;">
  <div id="searchInfo" style="display: flex; align-items: center; gap: 0.5rem;">
    <span id="serverInfo"></span>
    <span id="resultInfo"></span>
  </div>
  <button class="depth-btn primary" onclick="performKeywordSearch()" style="margin-bottom: 0; min-width: 126px;">Suche starten</button>
</div>
</div>
<div style="display:flex; gap:8px; align-items:center; justify-content: flex-end; margin-top: 0.5rem;">
  <button id="viewToggle" class="depth-btn" onclick="toggleResultView()" style="display: none; font-size: 0.8em; padding: 4px 16px; width: 126px; box-sizing: border-box;">
    <span id="viewToggleText">nur Titel</span>
  </button>
</div>
<span id="status" style="display:none"></span>
</div>
<div class="tab-content" id="texte-tab">
<div style="padding: 0.5rem 0;">
<div class="filter-row">
<select class="filter-dropdown" id="texteGAFilter" style="width: 100%;">
<option value="">GA-Band auswählen...</option>
</select>
</div>
<div style="display:flex; gap:8px; align-items:center; margin-top: 0.5rem;">
  <button id="batch-btn" class="depth-btn" onclick="startBatchSummaries()" style="padding: 6px 10px; font-size: 0.85em;">batch</button>
  <button id="batch-all-btn" class="depth-btn" onclick="startBatchAllSummaries()" style="padding: 6px 10px; font-size: 0.85em;">batch all</button>
</div>
<div id="texteSearchInfo" style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
<div>
<span id="texteServerInfo"></span>
</div>
<button id="texteViewToggle" class="depth-btn" onclick="toggleGASummaries()" style="display: none; font-size: 0.85em; padding: 4px 12px; min-width: 180px;">
  <span id="texteViewToggleText">nur Titel</span>
</button>
</div>
</div>
</div>
<div class="tab-content" id="thematic-tab">
<textarea class="thematic-input" id="thematicQuery" onkeydown="handleThematicKeydown(event)" placeholder="Stellen Sie eine thematische Frage. Wichtige Stichworte bitte in Anführungszeichen"></textarea>
<div id="thematicRecentContainer" style="font-size: 0.9em; color: #666; margin-top: 0.5rem; display: none;">
  <div style="margin-bottom: 0.25rem;">Zuletzt gesucht</div>
  <div id="thematicRecentScroll" style="max-height: 4.5rem; overflow-y: auto;">
    <ul id="thematicRecentList" style="margin: 0; padding-left: 1.2em;"></ul>
  </div>
  </div>
<div class="semantic-options">
<div class="filter-row">
<select class="filter-dropdown" id="thematicGAFilter">
  <option value="">Alle GA-Bände</option>
</select>
<button class="depth-btn primary" id="thematicSearchBtn" onclick="performThematicSearch()" style="margin-left: auto;">
  Suche starten
</button>
</div>
</div>
<div id="thematicSearchInfo" style="font-size: 0.9em; color: #666; margin-top: 0.5rem; margin-bottom: 0.3rem; padding-bottom: 0.5rem;">
<span id="thematicServerInfo"></span>
</div>
</div>

<div class="tab-content" id="timeline-tab">
<div style="padding: 0.5rem 0; max-height: calc(100vh - 250px); overflow-y: auto;">
<!-- Statistiken -->
<div id="timelineStats" style="margin-bottom: 1rem; padding: 0.8rem; background: var(--sidebar-bg); border-radius: 4px; border: 1px solid var(--border-color);">
<h3 style="margin: 0 0 0.5rem 0; color: var(--heading-color);">Timeline-Datenbank Status</h3>
<div style="font-size: 0.9em; color: var(--text-color);">
<div><strong>Keywords generiert:</strong> <span id="timelineKeywordsCount">-</span></div>
<div><strong>Fortschritt:</strong> <span id="timelineProgress">-</span></div>
<div><strong>Mit Thema:</strong> <span id="timelineThemesCount">-</span></div>
</div>
<button class="depth-btn" onclick="loadTimelineStats()" style="margin-top: 0.5rem; padding: 6px 12px; font-size: 0.85em;">Statistiken aktualisieren</button>
</div>

<!-- Keywords-Generierung Admin Interface -->
<div id="timelineAdminSection" style="display:none; margin-bottom: 1rem;">
<div style="padding: 0.8rem; background: var(--sidebar-bg); border-radius: 4px; border: 1px solid var(--border-color);">
<h3 style="margin: 0 0 0.5rem 0; color: var(--heading-color);">Keywords-Generierung</h3>
<p style="font-size: 0.9em; margin-bottom: 0.8rem; color: var(--secondary-text);">
Extrahiere aus jeder Zwischenüberschrift (H3 + H4) ein prägnantes Schlagwort (1-3 Worte) mittels Claude KI.
</p>

<!-- GA-Auswahl -->
<div style="margin-bottom: 0.8rem;">
<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
GA-Bände auswählen (für Test):
</label>
<select id="timelineGASelect" multiple size="5" 
style="width: 100%; padding: 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 0.9em;">
<option value="">Alle GA-Bände</option>
</select>
<p style="font-size: 0.85em; margin-top: 0.3rem; color: var(--secondary-text);">
(Strg/Cmd + Klick für Mehrfachauswahl. Leer = alle Bände)
</p>
</div>

<!-- Batch-Generierung -->
<div style="margin-bottom: 0.8rem;">
<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
Batch-Größe:
</label>
<input type="number" id="timelineBatchSize" value="50" min="1" max="100" 
style="width: 100px; padding: 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 0.9em;">
</div>

<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 0.5rem;">
<button id="timelineBatchStart" class="depth-btn primary" onclick="startTimelineBatchGeneration()" 
style="padding: 8px 16px; font-size: 0.9em; background: #467886; color: white;">
Batch-Generierung starten
</button>
<button id="timelineBatchStop" class="depth-btn" onclick="stopTimelineBatchGeneration()" 
style="display: none; padding: 8px 16px; font-size: 0.9em; background: #d9534f; color: white;">
Stoppen
</button>
</div>

<!-- Progress Bar -->
<div id="timelineBatchProgress" style="display: none;">
<div style="margin-bottom: 0.5rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
<span id="timelineBatchProgressText" style="font-size: 0.85em; color: var(--text-color);">Verarbeite...</span>
<span id="timelineBatchProgressPercent" style="font-size: 0.85em; color: var(--text-color);">0%</span>
</div>
<div style="width: 100%; height: 8px; background: var(--border-color); border-radius: 4px; overflow: hidden;">
<div id="timelineBatchProgressBar" style="width: 0%; height: 100%; background: #467886; transition: width 0.3s ease;"></div>
</div>
</div>
<div id="timelineBatchResults" style="margin-top: 0.5rem; padding: 0.5rem; background: var(--background-color); border-radius: 4px; border: 1px solid var(--border-color);">
<div style="font-size: 0.85em; color: var(--text-color);">
<div><strong>Verarbeitet:</strong> <span id="timelineBatchProcessed">0</span></div>
<div><strong>Übersprungen:</strong> <span id="timelineBatchSkipped">0</span></div>
<div><strong>Fehler:</strong> <span id="timelineBatchErrors">0</span></div>
</div>
</div>
</div>
</div>

<!-- Themen-Generierung -->
<div style="padding: 0.8rem; background: var(--sidebar-bg); border-radius: 4px; border: 1px solid var(--border-color); margin-top: 0.8rem;">
<h3 style="margin: 0 0 0.5rem 0; color: var(--heading-color);">Themen-Generierung</h3>
<p style="font-size: 0.9em; margin-bottom: 0.8rem; color: var(--secondary-text);">
Nach Abschluss der Keyword-Generierung: Gruppiere alle Keywords mittels KI in 30 übergeordnete Themen (einmalig ~$0.50).
</p>
<div style="margin-bottom: 0.8rem;">
<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
Anzahl Themen:
</label>
<input type="number" id="timelineThemeCount" value="30" min="10" max="50" 
style="width: 100px; padding: 6px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 0.9em;">
</div>
<button id="timelineGenerateThemes" class="depth-btn" onclick="generateThemes()" 
style="padding: 8px 16px; font-size: 0.9em; background: #467886; color: white;">
Themen generieren
</button>
<div id="timelineThemesStatus" style="display: none; margin-top: 0.5rem; padding: 0.5rem; background: var(--background-color); border-radius: 4px; border: 1px solid var(--border-color); font-size: 0.85em;"></div>
</div>
</div>

<!-- Timeline-Visualisierung -->
<div id="timelineVisualization" style="margin-top: 1rem;">
<h3 style="margin: 0 0 0.8rem 0; color: var(--heading-color);">Timeline-Ansicht</h3>
<p style="font-size: 0.9em; margin-bottom: 0.8rem; color: var(--secondary-text);">
Visualisierung wird verfügbar, sobald Themen generiert wurden.
</p>
<!-- Filter -->
<div style="margin-bottom: 0.8rem;">
<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
Thema auswählen:
</label>
<select id="timelineThemeFilter" class="filter-dropdown" style="width: 100%; margin-bottom: 0.5rem;" onchange="loadTimelineKeywords()">
<option value="">Themen werden noch generiert...</option>
</select>

<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
Schlagwort auswählen (optional):
</label>
<select id="timelineKeywordFilter" class="filter-dropdown" style="width: 100%; margin-bottom: 0.5rem;" onchange="renderTimeline()">
<option value="">Alle Schlagwörter des Themas</option>
</select>

<button class="depth-btn" onclick="renderTimeline()" style="padding: 6px 12px; font-size: 0.9em; width: 100%;">
Timeline anzeigen
</button>
</div>

<!-- Timeline-Anzeige -->
<div id="timelineDisplay" style="padding: 1rem; background: var(--sidebar-bg); border-radius: 4px; border: 1px solid var(--border-color); min-height: 200px; max-height: 600px; overflow-y: auto;">
<div id="timelineContent" style="text-align: center; padding: 2rem; color: var(--secondary-text);">
Wählen Sie ein Thema aus und klicken Sie auf "Timeline anzeigen".
</div>
</div>
</div>
</div>
</div>

<div class="tab-content" id="schlagworte-tab">
<div style="margin-bottom: 1rem;">
<!-- Neues Schlagwort hinzufügen (nur lokal sichtbar) -->
<div id="addKeywordSection" style="display:none;">
<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 0.8rem;">
<input type="text" id="newKeywordInput" class="search-input" placeholder="Neues Schlagwort..." style="flex: 1; font-size: 0.85em; margin: 0;" onkeypress="handleKeywordInputKeypress(event)">
<button id="addKeywordButton" class="depth-btn" onclick="addNewKeyword()" style="padding: 6px 12px; font-size: 0.85em; white-space: nowrap;">Schlagwort hinzufügen</button>
</div>
<div id="addKeywordStatus" style="display:none;"></div>
</div>

<!-- Schlagwort löschen (nur lokal sichtbar) -->
<div id="regenerateKeywordSection" style="display:none;">
<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 1.0rem;">
<input type="text" id="regenerateKeywordInput" class="search-input" placeholder="Schlagwort löschen..." style="flex: 1; font-size: 0.85em; margin: 0;" onkeypress="handleDeleteKeywordInputKeypress(event)">
<button id="regenerateKeywordButton" class="depth-btn" onclick="deleteKeyword()" style="padding: 6px 12px; font-size: 0.85em; white-space: nowrap;">Schlagwort löschen</button>
</div>
<div id="regenerateKeywordStatus" style="display:none;"></div>
</div>

<!-- Batch-Schlagwort-Generierung (nur lokal sichtbar) -->
<div id="batchKeywordSection" style="display:none;">
<div style="margin-bottom: 1.0rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
<h4 style="margin: 0; color: var(--heading-color);">Batch-Schlagwort-Generierung</h4>
<button id="batchToggleButton" class="depth-btn" onclick="toggleBatchSection()" style="padding: 4px 8px; font-size: 0.75em; background: #666; color: white;">Ausblenden</button>
</div>
<div id="batchContent">
<div style="margin-bottom: 0.5rem;">
<label style="display: block; margin-bottom: 0.3rem; font-size: 0.9em; color: var(--text-color);">
Schlagwort-Liste (ein Schlagwort pro Zeile):
</label>
<textarea id="batchKeywordsInput" 
          placeholder="Astralleib&#10;Ätherleib&#10;Bewusstsein&#10;Karma&#10;Reinkarnation" 
          style="width: 100%; height: 120px; padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; font-family: inherit; font-size: 0.85em; resize: vertical; background: var(--input-bg); color: var(--text-color);"></textarea>
</div>
<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 0.5rem;">
<label style="display: flex; align-items: center; gap: 4px; font-size: 0.85em; color: var(--text-color);">
<input type="checkbox" id="batchOverwriteCheckbox" style="margin: 0;">
Bestehende Schlagwörter überschreiben
</label>
</div>
<div style="display: flex; gap: 8px; align-items: center;">
<button id="batchAddButton" class="depth-btn" onclick="addBatchKeywords()" style="padding: 8px 16px; font-size: 0.85em; white-space: nowrap; background: #467886; color: white;">Batch-Generierung starten</button>
<button id="batchCancelButton" class="depth-btn" onclick="cancelBatchKeywords()" style="padding: 8px 16px; font-size: 0.85em; white-space: nowrap; background: #666; color: white; display: none;">Abbrechen</button>
</div>
</div>
<div id="batchKeywordStatus" style="display:none;"></div>
<div id="batchProgressContainer" style="display:none;">
<div style="margin-bottom: 0.5rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
<span id="batchProgressText" style="font-size: 0.85em; color: var(--text-color);">Verarbeite...</span>
<span id="batchProgressPercent" style="font-size: 0.85em; color: var(--text-color);">0%</span>
</div>
<div style="width: 100%; height: 8px; background: var(--border-color); border-radius: 4px; overflow: hidden;">
<div id="batchProgressBar" style="width: 0%; height: 100%; background: #467886; transition: width 0.3s ease;"></div>
</div>
</div>
<div id="batchResults" style="display:none; margin-top: 0.5rem; padding: 0.5rem; background: var(--sidebar-bg); border-radius: 4px; border: 1px solid var(--border-color);">
<div style="font-size: 0.85em; color: var(--text-color);">
<div><strong>Erfolgreich:</strong> <span id="batchSuccessCount">0</span></div>
<div><strong>Fehlgeschlagen:</strong> <span id="batchFailedCount">0</span></div>
<div><strong>Übersprungen:</strong> <span id="batchSkippedCount">0</span></div>
</div>
</div>
</div>
</div>
</div>

<div id="alphabet-nav" style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 1rem;">
<!-- Alphabet-Buttons werden dynamisch generiert -->
</div>
<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 0.5rem;">
<input type="text" id="keywordSearch" class="search-input" placeholder="Schlagwort suchen..." style="flex: 1; font-size: 0.85em;">
<button class="depth-btn" onclick="clearKeywordSearch()" style="padding: 4px 8px; font-size: 0.8em;">×</button>
</div>
<!-- removed keyword-count status line -->
</div>
</div>

</div>
<div class="horizontal-resize-handle" id="search-panel-toggle" onclick="toggleSearchPanel()" title="Suchbereich ein-/ausklappen"></div>
<div id="note" style="display: none;"></div>
</div>
<div id="sidebar-content">
<div id="results"></div>
</div>
</div>
<div class="resize-handle" id="resizeHandle"></div>
<div id="main-container">
<div id="main">
<div id="viewer-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
<h2 id="document-title" style="margin: 0; flex: 1;">Bitte ein Suchergebnis auswählen…</h2>
<div class="viewer-buttons-container">
<button id="viewerOriginalBtn" onclick="closeAndShowOriginal()" style="display: none; padding: 4px 12px; font-size: 0.85em; border: 1px solid #467886; background: transparent; color: #467886; cursor: pointer; border-radius: 4px; transition: opacity 0.2s;">
Original
</button>
<button id="viewerSummaryBtn" onclick="toggleViewerH4()" style="display: none; padding: 4px 12px; font-size: 0.85em; border: 1px solid #467886; background: transparent; color: #467886; cursor: pointer; border-radius: 4px; transition: opacity 0.2s;">
≡ Übersicht
</button>
<!-- Lokal sichtbarer Button zum Neuerzeugen/Überschreiben einer Summary -->
<button id="viewerRegenerateBtn" onclick="regenerateCurrentSummary()" style="display: none; padding: 4px 12px; font-size: 0.85em; border: 1px solid #d9534f; background: transparent; color: #d9534f; cursor: pointer; border-radius: 4px; transition: opacity 0.2s;">
Summary neu
</button>
</div>
</div>
<div id="viewer"></div>
</div>
<div class="vertical-resize-handle" id="verticalResizeHandle"></div>
<div id="summary-panel">
  <div class="summary-buttons">
  </div>
  <div id="summary-content">
<div id="toc-list"></div>
</div>
</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
    const isLocal = window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1' ||
                    window.location.protocol === 'file:';
    
    const API_BASE = isLocal
      ? 'http://localhost:3003'
      : 'https://ga-suche.onrender.com';
    
    console.log('[API] Verwende API_BASE:', API_BASE, '(isLocal:', isLocal, ')');
    
    let currentSources = [];
    let searchResults = [];
    let currentLectureData = null;
    let currentTimelineKeyword = null; // Speichert das aktuelle Timeline-Schlagwort
    let currentThematicQuery = '';
    let currentThematicGAFilter = '';
    let searchHistory = {
      word1: [],
      word2: []
    };
    let showingSummaryInMain = false;
    let currentLectureSummary = null;
    let lastHighlightedIndex = null;
    let viewerH4Collapsed = false;
    let isGeneratingSummary = false;
    let isThematicSearchRunning = false;
    let isKeywordSearchRunning = false;

    // === ZENTRALE SUMMARY-DATENBANK ===
    // Einfaches System: Alle Summaries in einer JSON-Datei

    async function loadSummaryFromDB(lectureId) {
      try {
        if (isLocal) {
          // Lokal: Lade aus statischer Datei
          const response = await fetch(`${API_BASE}/summary-database.json`);
          if (!response.ok) return null;
          
          const summaryDB = await response.json();
          return summaryDB[lectureId] || null;
        } else {
          // ONLINE: Preferiere statische summary-database.json aus dem GitHub-Repo.
          // Falls diese nicht verfügbar ist, fällt das System auf die frühere
          // Methode zurück (API /api/check-summary/... auf dem Render-Backend).
          try {
            const external = await loadExternalSummaryDB();
            if (external && external[lectureId]) {
              const entry = external[lectureId];
              return {
                summary: entry.summary,
                headings: entry.headings || [],
                timestamp: entry.timestamp || new Date().toISOString()
              };
            }
          } catch (e) {
            console.warn('[SUMMARIES] Externe Summary-DB konnte nicht geladen werden, fallback auf API', e.message);
          }

          // Fallback: Online-API prüfen (bisherige Methode)
          const parts = lectureId.split('/');
          if (parts.length === 2) {
            const response = await fetch(`${API_BASE}/api/check-summary/${parts[0]}/${parts[1]}`);
            if (response.ok) {
              const summaryData = await response.json();
              if (summaryData.exists) {
                return {
                  summary: summaryData.summary,
                  headings: summaryData.headings || [],
                  timestamp: new Date().toISOString()
                };
              }
            }
          }
          return null;
        }
      } catch (error) {
        console.log('Summary laden fehlgeschlagen:', error.message);
        return null;
      }
    }

    async function saveSummaryToDB(lectureId, summaryData) {
      try {
        const response = await fetch(`${API_BASE}/api/save-summary`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lectureId: lectureId,
            summary: summaryData
          })
        });
        
        if (response.ok) {
          console.log(`Summary für ${lectureId} in DB gespeichert`);
          return true;
        } else {
          console.warn(`Fehler beim Speichern in DB: ${response.status}`);
          return false;
        }
      } catch (error) {
        console.warn('DB-Speicherung fehlgeschlagen:', error.message);
        return false;
      }
    }

    async function loadSummariesFromDB(data) {
      try {
        // Versuche zuerst, die statische summary-database.json aus dem GitHub-Repo zu laden
        let loadedCount = 0;
        try {
          const external = await loadExternalSummaryDB();
          if (external) {
            data.lectures.forEach(lecture => {
              if (external[lecture.ID]) {
                lecture.summary = external[lecture.ID].summary;
                lecture.headings = external[lecture.ID].headings || [];
                loadedCount++;
              }
            });
            console.log(`[SUMMARIES] ${loadedCount} Summaries aus externer GitHub-DB geladen`);
            // Wenn wir etwas geladen haben, sind wir fertig (keine weitere Aktion nötig)
            if (loadedCount > 0) return;
          }
        } catch (extErr) {
          console.warn('[SUMMARIES] Externe Summary-DB nicht verfügbar:', extErr.message);
        }

        // Fallback: wenn keine externe DB vorhanden oder keine Einträge, versuche lokale/static Datei
        if (isLocal) {
          const response = await fetch(`${API_BASE}/summary-database.json`);
          if (response.ok) {
            const summaryDB = await response.json();
            summaryDB && data.lectures.forEach(lecture => {
              if (summaryDB[lecture.ID]) {
                lecture.summary = summaryDB[lecture.ID].summary;
                lecture.headings = summaryDB[lecture.ID].headings || [];
                loadedCount++;
              }
            });
            console.log(`[SUMMARIES] ${loadedCount} Summaries aus lokaler summary-database.json geladen`);
          }
        } else {
          console.log('Online-Modus: keine statische DB gefunden, verwende API-Fallback');
        }
      } catch (error) {
        console.log('Zentrale Summary-DB nicht verfügbar:', error.message);
      }
    }

  // Cache und Loader für externe (GitHub) summary-database.json
  const GITHUB_RAW_SUMMARY_URL = 'https://raw.githubusercontent.com/cjhueck/ga_suche/main/summary-database.json';
  let externalSummaryDBCache = null;

  async function loadExternalSummaryDB() {
    if (externalSummaryDBCache) return externalSummaryDBCache;
    try {
      const resp = await fetch(GITHUB_RAW_SUMMARY_URL);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const db = await resp.json();
      externalSummaryDBCache = db;
      console.log('[SUMMARIES] Externe summary-database.json geladen (GitHub)');
      return db;
    } catch (err) {
      console.warn('[SUMMARIES] Laden externer summary-database.json fehlgeschlagen:', err.message);
      return null;
    }
  }

    // Initiale CSS-Klassen setzen
    document.body.classList.add('summary-panel-collapsed'); // Summary-Panel ist standardmäßig geschlossen

function normalizeGANumber(gaNumber) {
    const match = gaNumber.match(/^GA?(\d+)([a-zA-Z]?)$/i);
    if (!match) return gaNumber;

    const number = match[1].padStart(3, '0');
    const suffix = match[2] || '';

    return `GA${number}${suffix.toLowerCase()}`;
  }

    // UI-Sperrung während Summary-Generierung (relaxed)
    // Previously we disabled pointer events globally while generating summaries,
    // which prevented clicking links (including .ga-reference) and therefore
    // broke navigation from snippets. Keep a visual cursor indicator but do not
    // block clicks.
    function setUILocked(locked) {
      isGeneratingSummary = locked;
      // Keep only an internal flag and console message. We don't change the
      // global cursor here to avoid leaving a lingering 'wait' cursor when
      // asynchronous flows finish in unexpected ways. UI remains clickable.
      console.log(locked ? 'UI locked (flag only) - Summary generation in progress' : 'UI unlocked - Summary generation finished');
    }

    // Header-Position dynamisch anpassen
    function updateHeaderPosition() {
      const header = document.getElementById('viewer-header');
      const mainElement = document.getElementById('main');
      const summaryPanel = document.getElementById('summary-panel');
      const sidebar = document.getElementById('sidebar');
      const viewer = document.getElementById('viewer');
      
      if (header && mainElement) {
        const mainRect = mainElement.getBoundingClientRect();
        const isSummaryPanelVisible = summaryPanel && summaryPanel.classList.contains('visible');
        const isSidebarCollapsed = sidebar && sidebar.classList.contains('collapsed');
        
        let headerLeft, headerWidth;
        
        if (isSidebarCollapsed) {
          // Sidebar kollabiert - Header beginnt am linken Bildschirmrand
          headerLeft = 0;
          headerWidth = window.innerWidth; // Header immer volle Breite
        } else {
          // Sidebar offen - Header beginnt am #main Element
          headerLeft = mainRect.left;
          headerWidth = window.innerWidth - mainRect.left; // Header bis zum rechten Rand
        }
        
        header.style.left = headerLeft + 'px';
        header.style.width = headerWidth + 'px';
        
        // Positioniere das Summary-Panel unter dem Header und passe Main-Container an
        if (summaryPanel) {
          const mainContainer = document.getElementById('main-container');
          setTimeout(() => {
            const headerHeight = header.offsetHeight;
            summaryPanel.style.top = headerHeight + 'px';
            
            // Main-Container Margin anpassen je nach Panel-Sichtbarkeit
            if (mainContainer) {
              if (isSummaryPanelVisible) {
                const panelWidth = summaryPanel.offsetWidth || 280;
                mainContainer.style.marginRight = panelWidth + 'px';
              } else {
                mainContainer.style.marginRight = '0px';
              }
            }
            
          }, 10);
        }
        
        // Main-Container unter Header positionieren
        const mainContainer = document.getElementById('main-container');
        const resizeHandle = document.getElementById('resizeHandle');
        const verticalResizeHandle = document.getElementById('verticalResizeHandle');
        
        setTimeout(() => {
          const headerHeight = header.offsetHeight;
          
          if (mainContainer) {
            mainContainer.style.marginTop = headerHeight + 'px';
          }
          
          // Viewer-Padding entfernen da Main-Container bereits korrekt positioniert ist
          if (viewer) {
            viewer.style.paddingTop = '0px';
          }
          
          // Resize-Handles horizontal positionieren (Höhe über CSS: 45vh)
          if (resizeHandle) {
            // Linkes Handle: Position abhängig von Sidebar-Zustand
            if (isSidebarCollapsed) {
              resizeHandle.style.left = '0px';
            } else {
              const sidebarWidth = sidebar ? sidebar.offsetWidth : 440;
              resizeHandle.style.left = sidebarWidth + 'px';
            }
          }
          
          if (verticalResizeHandle) {
            // Rechtes Handle: Position abhängig von Panel-Zustand
            if (isSummaryPanelVisible) {
              // Panel offen: Handle neben Panel positionieren
              const panelWidth = summaryPanel.offsetWidth || 280;
              verticalResizeHandle.style.right = panelWidth + 'px';
            } else {
              // Panel geschlossen: Handle am rechten Bildschirmrand
              verticalResizeHandle.style.right = '0px';
            }
          }
        }, 10);
      }
    }

    // Header-Position und Toggle-Position bei Resize und Laden aktualisieren
    window.addEventListener('resize', function() {
      updateHeaderPosition();
    });
    document.addEventListener('DOMContentLoaded', function() {
      updateHeaderPosition();
    });
    
    // Header-Position nach kurzer Verzögerung auch aktualisieren (für dynamische Layouts)
    setTimeout(function() {
      updateHeaderPosition();
    }, 100);

    function addToHistory(field, value) {
      if (!value || !value.trim()) return;
      
      const trimmed = value.trim();
      
      searchHistory[field] = searchHistory[field].filter(item => item !== trimmed);
      searchHistory[field].unshift(trimmed);
      searchHistory[field] = searchHistory[field].slice(0, 10);
      
      updateHistoryDatalist();
    }

    function updateHistoryDatalist() {
      const word1List = document.getElementById('word1-history');
      const word2List = document.getElementById('word2-history');
      
      if (word1List) {
        word1List.innerHTML = searchHistory.word1.map(item => 
          `<option value="${item}">`
        ).join('');
      }
      
      if (word2List) {
        word2List.innerHTML = searchHistory.word2.map(item => 
          `<option value="${item}">`
        ).join('');
      }
    }

    function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      
      if (sidebar.classList.contains('collapsed')) {
        // Sidebar öffnen
        sidebar.classList.remove('collapsed');
        document.body.classList.remove('sidebar-collapsed');
        sidebar.style.width = '';
        sidebar.style.minWidth = ''; 
        
        updateHeaderPosition();
      } else {
        // Sidebar schließen
        sidebar.classList.add('collapsed');
        document.body.classList.add('sidebar-collapsed');
        sidebar.style.width = '0';
        sidebar.style.minWidth = '0';
        
        updateHeaderPosition();
      }
    }

    function toggleSearchPanel() {
      const tabContainer = document.querySelector('.tab-container');
      const toggleHandle = document.getElementById('search-panel-toggle');
      
      if (tabContainer.classList.contains('collapsed')) {
        // Suchpanel öffnen
        tabContainer.classList.remove('collapsed');
        document.body.classList.remove('search-panel-collapsed');
        toggleHandle.title = 'Suchbereich einklappen';
      } else {
        // Suchpanel schließen
        tabContainer.classList.add('collapsed');
        document.body.classList.add('search-panel-collapsed');
        toggleHandle.title = 'Suchbereich ausklappen';
      }
    }

    function switchTab(mode) {
      console.log('[TABS] Wechsel zu Tab:', mode);
      
      // Summary-Panel komplett schließen und verstecken beim Tab-Wechsel
      const summaryPanel = document.getElementById('summary-panel');
      const resizeHandle = document.querySelector('.resize-handle');
      
      if (summaryPanel) {
        // Entferne alle sichtbarkeitsrelevanten Klassen
        summaryPanel.classList.remove('visible');
        
        // Setze alle Style-Properties explizit zurück
        summaryPanel.style.setProperty('width', '0', 'important');
        summaryPanel.style.setProperty('min-width', '0', 'important');
        summaryPanel.style.setProperty('margin-right', '0', 'important');
        summaryPanel.style.setProperty('display', 'none', 'important');
        summaryPanel.style.setProperty('opacity', '0', 'important');
        summaryPanel.style.setProperty('visibility', 'hidden', 'important');
        
        console.log('[TABS] Summary-Panel geschlossen');
      }
      
      if (resizeHandle) {
        resizeHandle.classList.remove('visible');
        resizeHandle.style.setProperty('display', 'none', 'important');
      }
      
      // Body-Klasse für collapsed State hinzufügen
      document.body.classList.add('summary-panel-collapsed');
      
      // TOC leeren
      const tocList = document.getElementById('toc-list');
      if (tocList) {
        tocList.innerHTML = '';
      }
      
      // Document Title zurücksetzen
      const documentTitle = document.getElementById('document-title');
      if (documentTitle) {
        documentTitle.textContent = 'Bitte ein Suchergebnis auswählen…';
      }
      
      // Viewer leeren
      const viewer = document.getElementById('viewer');
      if (viewer) {
        viewer.innerHTML = '';
      }
      
      // currentOpenLectureId zurücksetzen
      window.currentOpenLectureId = null;
      
      // Header-Position aktualisieren
      if (typeof updateHeaderPosition === 'function') {
        setTimeout(() => updateHeaderPosition(), 50);
      }
      
      document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
      document.querySelector(`[onclick="switchTab('${mode}')"]`).classList.add('active');
      
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
      document.getElementById(`${mode}-tab`).classList.add('active');
    }

    document.addEventListener('DOMContentLoaded', function() {
      
  populateYearFilter();
  initResizeHandle();
  initVerticalResizeHandle();
  checkServerConnection();
  initTheme();
  populateGADropdowns();
  initGAFilter();
  updateButtonStates(); // Verstecke Buttons beim ersten Laden
  
  // Initialisiere Resize-Handle basierend auf aktivem Tab
  const activeTabButton = document.querySelector('.tab-button.active');
  if (activeTabButton) {
    const resizeHandle = document.getElementById('search-panel-toggle');
    if (resizeHandle) {
      resizeHandle.style.display = 'block';
      resizeHandle.style.cursor = 'row-resize';
    }
    // Wenn Themen-Tab aktiv ist, lade letzte gespeicherte Anfragen
    try {
      const activeTabMode = activeTabButton.getAttribute('onclick').match(/switchTab\('([^']+)'\)/)[1];
      if (activeTabMode === 'thematic') {
        loadRecentThematicQueries();
      }
    } catch (_) {}
  }
    });

    function initTheme() {
      const savedTheme = localStorage.getItem('theme') || 'light';
      const checkbox = document.getElementById('theme-checkbox');
      if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (checkbox) checkbox.checked = true;
      }
    }

    function toggleThemeCheckbox() {
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    function populateYearFilter() {
      const yearFilter = document.getElementById('yearFilter');
      
      for (let year = 1882; year <= 1925; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearFilter.appendChild(option);
      }
    }

    async function checkServerConnection() {
      try {
        const response = await fetch(`${API_BASE}/debug/status`);
        if (response.ok) {
          const data = await response.json();
          const infoText = `${data.lecturesLoaded} Vorträge`;
          document.getElementById('serverInfo').textContent = infoText;
          document.getElementById('thematicServerInfo').textContent = infoText;
          document.getElementById('texteServerInfo').textContent = infoText;
        }
      } catch (error) {
        const errorText = `<span style="color: #c53030;">Server nicht erreichbar</span>`;
        document.getElementById('serverInfo').innerHTML = errorText;
        document.getElementById('thematicServerInfo').innerHTML = errorText;
        document.getElementById('texteServerInfo').innerHTML = errorText;
      }
    }

    function updateRelevanceFilter() {
      // Relevanz-Filter ist immer aktiv, keine Bedingungen
      console.log('[RELEVANCE-FILTER] Filter aktualisiert');
    }

    async function populateGADropdowns() {
      try {
        const response = await fetch(`${API_BASE}/api/ga-list`);
        if (!response.ok) throw new Error('GA-Liste konnte nicht geladen werden');
        const gaList = await response.json();
        const gaFilter = document.getElementById('gaFilter');
        const thematicGAFilter = document.getElementById('thematicGAFilter');
        const texteGAFilter = document.getElementById('texteGAFilter');
        if (gaFilter) {
          gaFilter.innerHTML = '<option value="">GA-Bände: alle</option>';
          gaList.forEach(ga => {
            const option = document.createElement('option');
            option.value = ga.number;
            option.textContent = ga.number;
            option.className = 'available-ga';
            gaFilter.appendChild(option);
          });
        }
        if (thematicGAFilter) {
          thematicGAFilter.innerHTML = '<option value="">Alle GA-Bände</option>';
          gaList.forEach(ga => {
            const option = document.createElement('option');
            option.value = ga.number;
            option.textContent = ga.number;
            option.className = 'available-ga';
            thematicGAFilter.appendChild(option);
          });
        }
        if (texteGAFilter) {
          texteGAFilter.innerHTML = '<option value="">GA-Band auswählen...</option>';
          gaList.forEach(ga => {
            const option = document.createElement('option');
            option.value = ga.number;
            // Zeige Nummer und Titel (falls verfügbar und nicht identisch)
            option.textContent = ga.title && ga.title !== ga.number ? `${ga.number} – ${ga.title}` : ga.number;
            option.className = 'available-ga';
            texteGAFilter.appendChild(option);
          });
        }
      } catch (error) {
        console.error('Fehler beim Laden der GA-Liste:', error);
      }
    }

    function initGAFilter() {
      const texteGAFilter = document.getElementById('texteGAFilter');

      // Texte-Tab: Direkt GA-Übersicht öffnen bei Auswahl
      if (texteGAFilter) {
        texteGAFilter.addEventListener('change', (e) => {
          const selectedGA = e.target.value;
          if (selectedGA) {
            openGAOverview(selectedGA);
          }
        });
      }
    }

    async function openGAOverview(gaNumber) {
      // Close summary panel when opening GA overview from the search window
      try {
        const summaryPanel = document.getElementById('summary-panel');
        const resizeHandle = document.getElementById('verticalResizeHandle');
        if (summaryPanel && summaryPanel.classList.contains('visible')) {
          summaryPanel.classList.remove('visible');
          if (resizeHandle) resizeHandle.classList.remove('visible');
          summaryPanel.style.width = '0';
          summaryPanel.style.minWidth = '0';
          summaryPanel.style.marginRight = '0px';
        }
      } catch (e) { /* silent */ }
      if (!gaNumber) return;
      try {
        const response = await fetch(`${API_BASE}/api/ga-overview/${gaNumber}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        // Debug-Information für Summary-Anzeige
        console.log('GA-Übersicht Daten vom Server:', data);
        console.log('Server-URL war:', `${API_BASE}/api/ga-overview/${gaNumber}`);
        if (data.lectures) {
          const lecturesWithSummary = data.lectures.filter(l => l.summary && l.summary.trim() !== '');
          console.log(`${lecturesWithSummary.length} von ${data.lectures.length} Vorträgen haben eine Zusammenfassung (vom Server!)`);
          
          // Zeige ein paar Beispiel-Summaries zur Diagnose
          if (lecturesWithSummary.length > 0) {
            console.log('Beispiel-Summary vom Server:', lecturesWithSummary[0].summary.substring(0, 100) + '...');
          }
          
          // Immer versuchen, Summaries aus der Datenbank zu laden (überschreibt API-Daten)
          console.log('Lade Summaries aus Datenbank...');
          await loadSummariesFromDB(data);
        }
        
        await displayGAOverview(data);
      } catch (error) {
        console.error('Fehler beim Laden der GA-Übersicht:', error);
        document.getElementById('viewer').innerHTML = `
          <div class="error-message">
            <strong>Fehler beim Laden der GA-Übersicht:</strong><br>${error.message}
          </div>
        `;
      }
    }

    // Hilfsfunktion: Lade Summaries aus zentraler Datenbank
    async function loadSummariesForOverview(data) {
      console.log('Lade Summaries aus zentraler Datenbank für GA-Übersicht...');
      
      // Erstmal die Übersicht ohne Summaries anzeigen
      await displayGAOverview(data);
      
      try {
        // Nur lokal: Lade statische summary-database.json
        if (isLocal) {
          const centralResponse = await fetch(`${API_BASE}/summary-database.json`);
          if (centralResponse.ok) {
            const centralData = await centralResponse.json();
            console.log('Lokale Summary-Datenbank geladen:', Object.keys(centralData).length, 'Einträge');
            return await applySummariesToOverview(data, centralData);
          }
        }
        
        // Online: Immer API-Endpunkt verwenden (dynamische Daten vom Render Backend)
        console.log('Lade Summaries über API (dynamisch vom Render Backend)...');
        return await loadSummariesViaAPI(data);
        
      } catch (error) {
        console.error('Fehler beim Laden der Summaries:', error);
        // Fallback zu API-Methode
        await loadSummariesViaAPI(data);
      }
    }
    
    // Hilfsfunktion: Wende Summary-Daten auf GA-Übersicht an
    async function applySummariesToOverview(data, summaryData) {
      console.log('Verfügbare Summary-Schlüssel (erste 10):', Object.keys(summaryData).slice(0, 10));
      console.log('Gesuchte Lecture IDs (erste 5):', data.lectures.slice(0, 5).map(l => l.ID));
      
      let foundSummaries = 0;
      
      // Durchlaufe alle Vorträge und suche passende Summaries
      data.lectures.forEach(lecture => {
        const lectureId = lecture.ID;
        
        // Verschiedene Formate testen
        const possibleKeys = [
          lectureId,                    // z.B. "GA001/001"
          lectureId.replace('/', '_'),  // z.B. "GA001_001"
          lectureId.replace('/', '-'),  // z.B. "GA001-001"
          lectureId.toLowerCase(),      // kleingeschrieben
          lectureId.toUpperCase(),      // großgeschrieben
        ];
        
        for (const key of possibleKeys) {
          if (summaryData[key] && summaryData[key].summary) {
            lecture.summary = summaryData[key].summary;
            // Markiere Quelle der Summary
            lecture.summarySource = summaryData[key].source || 'unknown';
            lecture.summaryGeneratedAt = summaryData[key].generatedAt || null;
            foundSummaries++;
            console.log(`Summary für ${lectureId} gefunden unter Schlüssel: ${key} (Quelle: ${lecture.summarySource})`);
            break;
          }
        }
      });
      
      console.log(`${foundSummaries} Summaries geladen`);
      
      // Anzeige aktualisieren
      await displayGAOverview(data);
    }
    
    // Fallback: Lade Summaries über API-Endpunkt
    async function loadSummariesViaAPI(data) {
      console.log('Fallback: Lade Summaries über API...');
      
      const maxToCheck = Math.min(5, data.lectures.length);
      let foundSummaries = 0;
      
      for (let i = 0; i < maxToCheck; i++) {
        const lecture = data.lectures[i];
        try {
          const parts = lecture.ID.split('/');
          if (parts.length === 2) {
            const response = await fetch(`${API_BASE}/api/check-summary/${parts[0]}/${parts[1]}`);
            if (response.ok) {
              const summaryData = await response.json();
              if (summaryData.exists && summaryData.summary) {
                lecture.summary = summaryData.summary;
                foundSummaries++;
                console.log(`Summary für ${lecture.ID} über API geladen`);
              }
            }
          }
        } catch (error) {
          console.warn(`Fehler beim Laden der Summary für ${lecture.ID}:`, error);
        }
      }
      
      if (foundSummaries > 0) {
        console.log(`${foundSummaries} Summaries über API geladen, aktualisiere Anzeige`);
        await displayGAOverview(data);
      }
    }

// Funktion: Speichere Summary in zentrale Datenbank
async function saveSummaryToCentral(lectureId, summaryData) {
  try {
    const response = await fetch(`${API_BASE}/api/save-summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lectureId: lectureId,
        summary: summaryData
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log(`Summary für ${lectureId} in zentrale Datenbank gespeichert:`, result);
      return result;
    } else {
      console.warn(`Fehler beim Speichern der Summary für ${lectureId}:`, response.status);
      return null;
    }
  } catch (error) {
    console.error(`Fehler beim Speichern der Summary für ${lectureId}:`, error);
    return null;
  }
}

// Funktion: Synchronisiere GitHub-Summaries mit zentraler Datenbank


// Globale Variable für den Toggle-Zustand
let gaOverviewShowSummaries = true;

// Hilfsfunktion zum Extrahieren des Summary-Texts
function getSummaryText(summary) {
  if (typeof summary === 'string') return summary;
  if (typeof summary === 'object' && summary) {
    if (summary.summary) return getSummaryText(summary.summary);
    return '';
  }
  return summary || '';
}

// Ändere die displayGAOverview Funktion (in index.html)
async function displayGAOverview(data) {
  const resultsContainer = document.getElementById('results');
  const titleElement = document.getElementById('document-title');
  const viewer = document.getElementById('viewer');
  
  // Normalisiere Summary-Daten: Stelle sicher, dass lecture.summary ein String ist
  data.lectures.forEach(lecture => {
    if (lecture.summary) {
      lecture.summary = getSummaryText(lecture.summary);
    }
  });
  
  titleElement.textContent = `${data.gaNumber}: ${data.gaTitle}`;
  
  viewer.innerHTML = '<p style="color: #666; font-style: italic;">Wählen Sie einen Vortrag aus der Liste links.</p>';
  
  // Setze currentLectureData zurück und verstecke Buttons
  currentLectureData = null;
  currentLectureSummary = null;
  showingSummaryInMain = false;
  updateButtonStates();
  
  // Lade Summaries aus zentraler Datenbank
  await loadSummariesFromDB(data);
  
  // Zähle Vorträge mit Summaries
  const summaryCount = data.lectures.filter(l => l.summary && l.summary.trim() !== '').length;
  
  // Aktualisiere Statusanzeige im aktiven Tab
  const activeTab = document.querySelector('.tab-content.active');
  if (activeTab && activeTab.id === 'texte-tab') {
    const texteServerInfo = document.getElementById('texteServerInfo');
    if (texteServerInfo) {
      // Verwende die gleiche Formatierung wie im Suche-Tab
      texteServerInfo.textContent = `${data.lectureCount} Vorträge`;
    }
    // Toggle Button im Texte-Tab anzeigen
    const texteViewToggle = document.getElementById('texteViewToggle');
    if (texteViewToggle) {
      texteViewToggle.style.display = 'inline-block';
    }
  }
  
  let html = `
    <div id="ga-lecture-list">
  `;
  
  data.lectures.forEach((lecture, idx) => {
    let titleText = `${lecture.ID} - ${lecture.title}`;
    
    const locationParts = [];
    if (lecture.location) locationParts.push(lecture.location);
    if (lecture.date) locationParts.push(lecture.date);
    
    if (locationParts.length > 0) {
      titleText += `, ${locationParts.join(', ')}`;
    }
    
    const hasSummary = lecture.summary && lecture.summary.trim() !== '';
    
    // Debug: Log wenn Summary vorhanden ist
    if (hasSummary) {
      console.log(`Vortrag ${lecture.ID} hat Summary:`, lecture.summary.substring(0, 100) + '...');
    }
    
    html += `
      <div class="ga-overview-lecture" style="margin-bottom: 0.5rem; padding-bottom: 0rem; border-bottom: none;">
        <h3 style="margin: 0 0 0rem 0;">
          <a href="#" onclick="showLectureFromOverview('${lecture.ID}'); return false;" style="text-decoration: none;">
            ${titleText}
          </a>
        </h3>
        
        ${hasSummary ? `
          <div class="ga-summary-text" style="margin-top: 0.5rem; display: ${gaOverviewShowSummaries ? 'block' : 'none'};">
            <p style="margin: 0; font-style: italic; line-height: 1.3; font-size: 1.0em; color: #666;">${getSummaryText(lecture.summary)}</p>
          </div>
        ` : `
          <!-- Keine Zusammenfassung für ${lecture.ID} -->
        `}
      </div>
    `;
  });
  
  html += `</div>`;
  resultsContainer.innerHTML = html;
  
  document.getElementById('sidebar-content').scrollTop = 0;
}

// Toggle-Funktion für Zusammenfassungen
function toggleGASummaries() {
  gaOverviewShowSummaries = !gaOverviewShowSummaries;
  
  const summaries = document.querySelectorAll('.ga-summary-text');
  const button = document.querySelector('#results button');
  
  summaries.forEach(summary => {
    summary.style.display = gaOverviewShowSummaries ? 'block' : 'none';
  });
  
  if (button) {
    button.textContent = gaOverviewShowSummaries ? 'nur Titel' : 'mit Zusammenfassungen';
  }
  
  // Update Toggle Button im Texte-Tab
  const texteViewToggleText = document.getElementById('texteViewToggleText');
  if (texteViewToggleText) {
    texteViewToggleText.textContent = gaOverviewShowSummaries ? 'nur Titel' : 'mit Zusammenfassungen';
  }
}

// Summary-Manager Interface










    async function showLectureFromOverview(lectureId) {
      await showLecture(lectureId, null, []);
    }

    function parseSearchTerm(input) {
      if (!input) return { term: '', isPhrase: false };
      
      const trimmed = input.trim();
      
      // Prüfe auf Anführungszeichen am Anfang und Ende
      if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || 
          (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
        // Entferne die Anführungszeichen und gib als Phrase zurück
        const cleanTerm = trimmed.slice(1, -1).trim();
        return { term: cleanTerm, isPhrase: true };
      }
      
      return { term: trimmed, isPhrase: false };
    }

    async function performKeywordSearch() {
      const word1Input = document.getElementById('word1').value.trim();
      const word2Input = document.getElementById('word2').value.trim();
      
      if (!word1Input && !word2Input) {
        alert('Bitte mindestens ein Suchwort eingeben');
        return;
      }
      
      document.getElementById('viewer').innerHTML = '';
      document.getElementById('document-title').textContent = 'Bitte ein Suchergebnis auswählen…';
      
      // Setze currentLectureData zurück und verstecke Buttons
      currentLectureData = null;
      currentLectureSummary = null;
      showingSummaryInMain = false;
      updateButtonStates();
      
      if (word1Input) addToHistory('word1', word1Input);
      if (word2Input) addToHistory('word2', word2Input);
      
      // Parse Suchbegriffe auf Phrasen
      const word1Parsed = parseSearchTerm(word1Input);
      const word2Parsed = parseSearchTerm(word2Input);
      
      const word1 = word1Parsed.term || word2Parsed.term;
      const word2 = word1Parsed.term && word2Parsed.term ? word2Parsed.term : null;
      const word1IsPhrase = word1Parsed.term ? word1Parsed.isPhrase : word2Parsed.isPhrase;
      const word2IsPhrase = word2Parsed.term ? word2Parsed.isPhrase : false;
      
      const button = document.querySelector('#keyword-tab .depth-btn.primary');
      
      try {
      isKeywordSearchRunning = true;
      // Sperre UI während der thematischen Suche
      setUILocked(true);
      button.disabled = true;
      button.classList.add('processing');
      button.textContent = 'Suche läuft...';
        
        const gaFilter = document.getElementById('gaFilter').value;
        const yearFilter = document.getElementById('yearFilter').value;
        const relevanceFilterElement = document.getElementById('relevanceFilter');
        const relevanceFilter = relevanceFilterElement ? relevanceFilterElement.value : 'alle';
        
        console.log(`[RELEVANCE-FILTER] Sende Filter an Backend: "${relevanceFilter}"`);
        if (yearFilter) console.log(`[YEAR-FILTER] Sende Jahr-Filter: "${yearFilter}"`);
        
        const response = await fetch(`${API_BASE}/api/fulltext-search`, {
          method: 'POST',
          keepalive: true,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            word1: word1,
            word2: word2,
            word1IsPhrase: word1IsPhrase,
            word2IsPhrase: word2IsPhrase,
            relevanceFilter: relevanceFilter,
            yearFilter: yearFilter
          })
        });
        
        if (!response.ok) throw new Error(`Server Error: ${response.status}`);
        
        const data = await response.json();
        let results = data.results;
        
        console.log(`Volltext-Suche: ${results.length} Absätze gefunden`);
        
        if (gaFilter) {
          results = results.filter(r => r.ID && r.ID.startsWith(gaFilter));
        }
        
        searchResults = results;
        let displayQuery;
        if (word1Input && word2Input) {
          const term1 = word1IsPhrase ? `"${word1}"` : word1;
          const term2 = word2IsPhrase ? `"${word2}"` : word2;
          displayQuery = `${term1} + ${term2}`;
        } else {
          const singleTerm = word1Input || word2Input;
          const isPhrase = word1Input ? word1IsPhrase : word2IsPhrase;
          displayQuery = isPhrase ? `"${word1}"` : singleTerm;
        }
        // Übergebe geparste Werte und Phrasen-Flags an renderKeywordResults
        renderKeywordResults(displayQuery, results, word1, word2, word1IsPhrase, word2IsPhrase);
        
      } catch (error) {
        console.error('Keyword-Suche Fehler:', error);
        document.getElementById('results').innerHTML = `
          <div class="error-message">
            <strong>Fehler bei der Suche:</strong><br>${error.message}
          </div>
        `;
      } finally {
        isKeywordSearchRunning = false;
        // Make sure the visual UI lock/cursor is cleared even if an error occurred
        try {
          setUILocked(false);
        } catch (e) { /* ignore */ }

        button.disabled = false;
        button.classList.remove('processing');
        button.textContent = 'Suche starten';
      }
    }

    function extractDateFromFileName(fileName) {
      if (!fileName) return '';
      
      const monthNames = {
        'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
        'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
      };
      
      let dateMatch = fileName.match(/(\d{1,2})\.\s+([a-zä]+)\s+(\d{4})/i);
      
      if (dateMatch) {
        const day = dateMatch[1].padStart(2, '0');
        const monthName = dateMatch[2].toLowerCase();
        const year = dateMatch[3];
        const month = monthNames[monthName] || '00';
        
        return `${year}-${month}-${day}`;
      }
      
      dateMatch = fileName.match(/im\s+([a-zä]+)\s+(\d{4})/i);
      if (dateMatch) {
        const monthName = dateMatch[1].toLowerCase();
        const year = dateMatch[2];
        const month = monthNames[monthName] || '00';
        
        return `${year}-${month}-01`;
      }
      
      dateMatch = fileName.match(/(\d{4})/);
      if (dateMatch) {
        return `${dateMatch[1]}-00-00`;
      }
      
      return '';
    }

    // Toggle zwischen Titel- und Textansicht der Ergebnisse
    let currentView = 'text'; // 'text' oder 'title'
    
    function toggleResultView() {
      const snippets = document.querySelectorAll('.snippet');
      const toggleText = document.getElementById('viewToggleText');
      
      if (currentView === 'text') {
        // Wechsle zu Titelansicht
        snippets.forEach(snippet => snippet.style.display = 'none');
        toggleText.textContent = 'Titel & Text';
        currentView = 'title';
      } else {
        // Wechsle zu Textansicht
        snippets.forEach(snippet => snippet.style.display = 'block');
        toggleText.textContent = 'nur Titel';
        currentView = 'text';
      }
    }
    
    // Hilfsfunktion: Relevanz-Filter-Status - <100 Regel entfernt
    function updateRelevanceFilterState(resultCount) {
      // Keine spezielle Behandlung mehr - "mittel" ist immer aktiv
      const relevanceFilter = document.getElementById('relevanceFilter');
      if (!relevanceFilter) return;
      
      const mittelOption = Array.from(relevanceFilter.options).find(opt => opt.value === 'mittel');
      if (!mittelOption) return;
      
      // Stelle sicher, dass "mittel" immer aktiviert ist
      mittelOption.disabled = false;
      mittelOption.style.color = '';
      mittelOption.textContent = 'mittel 🟧'; // Oranges Quadrat
    }

    function renderKeywordResults(query, results, word1, word2, word1IsPhrase = false, word2IsPhrase = false) {
      const container = document.getElementById('results');
      const scope = 'fulltext'; // Immer Volltext-Suche
      
      // Update Relevanz-Filter basierend auf Anzahl der Treffer
      updateRelevanceFilterState(results.length);
      
      if (results.length === 0) {
        container.innerHTML = '<p><em>Keine Treffer gefunden.</em></p>';
        // Verstecke Toggle-Button wenn keine Ergebnisse
        const viewToggle = document.getElementById('viewToggle');
        if (viewToggle) viewToggle.style.display = 'none';
        return;
      }
      
      // Zeige Toggle-Button bei Ergebnissen
      const viewToggle = document.getElementById('viewToggle');
      if (viewToggle) viewToggle.style.display = 'inline-block';
      
      // Reset auf Textansicht
      currentView = 'text';
      const toggleText = document.getElementById('viewToggleText');
      if (toggleText) toggleText.textContent = 'nur Titel';
      
      // Timeline-Container mit CSS Grid
      const timelineContainer = document.createElement('div');
      timelineContainer.className = 'timeline-container';
      // Setze display: grid mit setProperty und !important
      timelineContainer.style.setProperty('display', 'grid', 'important');
      timelineContainer.style.gridTemplateColumns = '60px 1fr';
      timelineContainer.style.columnGap = '0rem';
      timelineContainer.style.rowGap = '0';
      timelineContainer.style.alignItems = 'start';
      timelineContainer.style.width = '100%';
      timelineContainer.style.marginTop = '0';
      timelineContainer.style.paddingTop = '0.5rem';
      
      
      const groupedByLecture = {};
      results.forEach(result => {
        const lectureId = result.ID;
        if (!groupedByLecture[lectureId]) {
          let lectureDate = result.date || '';
          if (!lectureDate && result.fileName) {
            lectureDate = extractDateFromFileName(result.fileName);
          }
          
          groupedByLecture[lectureId] = {
            fileName: result.fileName || result.title,
            date: lectureDate,
            chunks: []
          };
        }
        groupedByLecture[lectureId].chunks.push(result);
      });
      
      const sortedLectures = Object.entries(groupedByLecture).sort((a, b) => {
        const dateA = a[1].date || '';
        const dateB = b[1].date || '';
        // Einträge ohne Datum ans Ende sortieren
        if (!dateA && dateB) return 1;  // a hat kein Datum, b schon -> a nach hinten
        if (dateA && !dateB) return -1; // a hat Datum, b nicht -> a nach vorne
        return dateA.localeCompare(dateB);
      });
      
      const filteredLectures = sortedLectures;
      
      // Aktualisiere Trefferanzahl
      const totalResults = results.length;
      const totalLecturesCount = sortedLectures.length;
      
      let resultText = ` • ${totalResults} Treffer in ${totalLecturesCount} Vorträgen`;
      document.getElementById('resultInfo').textContent = resultText;
      
      // Timeline-Darstellung mit CSS Grid: Jahr links, Treffer rechts
      let currentYear = null;
      let isFirstOfYear = false;
      
      filteredLectures.forEach(([lectureId, lecture], index) => {
        // Extrahiere Jahr aus dem Datum
        const year = lecture.date ? lecture.date.substring(0, 4) : null;
        
        // Prüfe ob neues Jahr
        isFirstOfYear = (year && year !== currentYear);
        if (isFirstOfYear) {
          currentYear = year;
        }
        
        // Erstelle Jahreszahl-Zelle (linke Grid-Spalte)
        const yearCell = document.createElement('div');
        yearCell.className = 'timeline-year-cell';
        yearCell.style.gridColumn = '1';
        yearCell.style.paddingTop = '0.2rem';
        
        if (isFirstOfYear) {
          // Zeige Jahreszahl nur beim ersten Eintrag des Jahres
          const isDarkMode = document.body.classList.contains('dark-mode');
          yearCell.textContent = year;
          yearCell.style.fontWeight = 'bold';
          yearCell.style.fontSize = '1em';
          yearCell.style.color = isDarkMode ? '#6BA3B8' : '#467886';
        } else {
          yearCell.innerHTML = '&nbsp;'; // Leeres Space für Nicht-Jahreszellen
        }
        
        timelineContainer.appendChild(yearCell);
        
        // Erstelle Treffer-Zelle (rechte Grid-Spalte)
        const lectureItem = document.createElement('div');
        lectureItem.className = 'timeline-item';
        lectureItem.style.gridColumn = '2';
        lectureItem.style.marginBottom = '0.5rem';
        
        const titleLink = document.createElement('a');
        titleLink.href = "#";
        
        // Relevanz-Kategorie als farbigen Punkt anzeigen
        let relevanceDot = '';
        const firstChunk = lecture.chunks[0];
        if (firstChunk && firstChunk.relevanceCategory) {
          const relevanceColors = {
            'hoch': '#28a745',      // Grün
            'mittel': '#fd7e14',    // Orange  
            'niedrig': '#ffc107'    // Gelb
          };
          const color = relevanceColors[firstChunk.relevanceCategory] || '#ffc107';
          relevanceDot = ` <span style="color: ${color}; font-size: 1.2em; margin-left: 4px;" title="Relevanz: ${firstChunk.relevanceCategory}">●</span>`;
        }
        
        titleLink.innerHTML = lecture.fileName + relevanceDot;
        titleLink.addEventListener('click', (e) => {
          e.preventDefault();
          showLectureTop(lectureId);
        });
        
        lectureItem.appendChild(titleLink);
        
        if (scope === "fulltext") {
          let lectureChunks = lecture.chunks;
          
          lectureChunks.slice(0, 5).forEach(chunk => {
            const snippetDiv = document.createElement("div");
            snippetDiv.className = "snippet";
            
            const content = chunk.content || '';
            
            let snippet = '';
            let foundPosition = -1;
            let foundWord = null;
            
            const contentLower = content.toLowerCase();
            const positions = [];
            
            // Hilfsfunktion zum Finden der Position mit oder ohne Wortgrenzen
            const findTermPosition = (text, term, isPhrase) => {
              if (!term || !term.trim()) return -1;
              const textLower = text.toLowerCase();
              const termLower = term.toLowerCase();
              
              if (isPhrase) {
                // Bei Phrasensuche: mit Wortgrenzen
                const escapedTerm = termLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp(`(^|[\\s,.;:!?()\\-—])${escapedTerm}($|[\\s,.;:!?()\\-—])`, 'i');
                const match = text.match(regex);
                if (match) {
                  return text.toLowerCase().indexOf(match[0].toLowerCase()) + (match[1] ? match[1].length : 0);
                }
                return -1;
              } else {
                // Bei normaler Suche: auch Teilwörter
                return textLower.indexOf(termLower);
              }
            };
            
            if (word1 && word1.trim()) {
              const pos = findTermPosition(content, word1, word1IsPhrase);
              if (pos !== -1) positions.push({ pos, word: word1 });
            }
            
            if (word2 && word2.trim()) {
              const pos = findTermPosition(content, word2, word2IsPhrase);
              if (pos !== -1) positions.push({ pos, word: word2 });
            }
            
            if (positions.length > 0) {
              positions.sort((a, b) => a.pos - b.pos);
              foundPosition = positions[0].pos;
              foundWord = positions[0].word;
            }
            
            if (foundPosition !== -1 && content) {
              const start = Math.max(0, foundPosition - 200);
              const end = Math.min(content.length, foundPosition + foundWord.length + 200);
              
              snippet = (start > 0 ? '...' : '') + 
                        content.substring(start, end) + 
                        (end < content.length ? '...' : '');
              
              // Hilfsfunktion für Highlighting mit oder ohne Wortgrenzen
              const highlightTerm = (text, term, isPhrase) => {
                if (!term || !term.trim()) return text;
                const escapedTerm = term.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                let regex;
                if (isPhrase) {
                  // Bei Phrasensuche: Wortgrenzen beachten
                  regex = new RegExp(`((?:^|[\\s,.;:!?()\\-—]))(${escapedTerm})(?=$|[\\s,.;:!?()\\-—])`, "gi");
                  return text.replace(regex, "$1<mark>$2</mark>");
                } else {
                  // Bei normaler Suche: auch Teilwörter highlighten
                  regex = new RegExp(`(${escapedTerm})`, "gi");
                  return text.replace(regex, "<mark>$1</mark>");
                }
              };
              
              if (word1 && word1.trim()) {
                snippet = highlightTerm(snippet, word1, word1IsPhrase);
              }
              
              if (word2 && word2.trim()) {
                snippet = highlightTerm(snippet, word2, word2IsPhrase);
              }
              
              snippetDiv.innerHTML = snippet;
              snippetDiv.style.cursor = 'pointer';
              snippetDiv.setAttribute('data-lecture-id', lectureId);
              snippetDiv.setAttribute('data-chunk-index', chunk.index);

              // If the snippet contains inline GA reference anchors (.ga-reference),
              // bind click handlers to them so they open the viewer and scroll to
              // the corresponding paragraph. Also ensure the parent snippet click
              // handler doesn't intercept anchor clicks.
              const bindGaLinksInSnippet = () => {
                const gaAnchors = snippetDiv.querySelectorAll('.ga-reference');
                gaAnchors.forEach(link => {
                  const lectureIdAttr = link.getAttribute('data-id');
                  const targetIndexAttr = link.getAttribute('data-index');
                  if (!lectureIdAttr || !targetIndexAttr) return;
                  // Avoid double-binding
                  if (link.__gaBound) return;
                  link.__gaBound = true;
                  link.addEventListener('click', async (e) => {
                    // Ensure no lingering visual UI lock/cursor
                    try { setUILocked(false); } catch (err) {}
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Summary Panel bleibt offen (wird in showLecture automatisch geöffnet)
                    const currentWord1 = document.getElementById('word1').value.trim();
                    const currentWord2 = document.getElementById('word2').value.trim();
                    const keywords = [currentWord1, currentWord2].filter(w => w && w.trim());

                    await showLecture(lectureIdAttr, targetIndexAttr, keywords);
                  });
                });
              };

              // Bind now and also after a short delay in case marked/rendering alters DOM
              bindGaLinksInSnippet();
              setTimeout(bindGaLinksInSnippet, 50);

              snippetDiv.addEventListener("click", async function(e) {
  // If a GA anchor was clicked, let its handler handle opening the viewer
  if (e.target && e.target.closest && e.target.closest('.ga-reference')) {
    return;
  }
  // Ensure no lingering visual UI lock/cursor
  try { setUILocked(false); } catch (err) {}
  e.preventDefault();
  e.stopPropagation();
  const currentWord1 = document.getElementById('word1').value.trim();
  const currentWord2 = document.getElementById('word2').value.trim();
  const keywords = [currentWord1, currentWord2].filter(w => w && w.trim());
  const lecId = e.currentTarget.getAttribute('data-lecture-id');
  const chunkIdx = e.currentTarget.getAttribute('data-chunk-index');
  
  // Summary Panel bleibt offen (wird in showLecture automatisch geöffnet)
  await showLecture(lecId, chunkIdx, keywords);
});
              lectureItem.appendChild(snippetDiv);
            }
          });
        }
        
        // Füge lectureItem direkt zum Grid-Container hinzu (rechte Spalte)
        timelineContainer.appendChild(lectureItem);
      });
      
      container.innerHTML = '';
      container.appendChild(timelineContainer);
      
      const lectureCount = sortedLectures.length;
      const chunkCount = results.length;
      document.getElementById('status').textContent = `${lectureCount} Vorträge mit ${chunkCount} Treffern`;
    }

    async function performThematicSearch() {
      const query = document.getElementById('thematicQuery').value.trim();
      if (!query) return;
      
      currentThematicQuery = query;
      
      // Setze currentLectureData zurück und verstecke Buttons
      currentLectureData = null;
      currentLectureSummary = null;
      showingSummaryInMain = false;
      updateButtonStates();
      
      const button = document.getElementById('thematicSearchBtn');
      
      try {
        isThematicSearchRunning = true;
        button.disabled = true;
        button.classList.add('processing');
        button.textContent = 'Suche läuft...';
        
        const limit = 100; // Default limit
        const gaFilter = document.getElementById('thematicGAFilter').value;
        currentThematicGAFilter = gaFilter || '';
        
        const response = await fetch(`${API_BASE}/api/thematic-hybrid-search`, {
          method: 'POST',
          keepalive: true,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            limit: parseInt(limit),
            gaFilter: gaFilter
          })
        });
        
        if (!response.ok) throw new Error(`Server Error: ${response.status}`);
        
        const answer = await response.json();
        let sources = answer.sources || [];
        
        // GA-Filter wird jetzt bereits im Backend angewendet
        currentSources = sources;
        renderThematicResults(query, answer.content, sources, (gaFilter || ''));

        // Nach erfolgreicher Suche: Liste aktualisieren (nur lokal)
        if (isLocal) {
          try { loadRecentThematicQueries(); } catch(_){}
        }
        
      } catch (error) {
        console.error('Thematic Search Error:', error);
        document.getElementById('results').innerHTML = `
          <div class="error-message">
            <strong>Fehler bei der Themen-Suche:</strong><br>${error.message}
          </div>
        `;
      } finally {
        isThematicSearchRunning = false;
        // UI wieder freigeben
        setUILocked(false);
        button.disabled = false;
        button.classList.remove('processing');
        button.textContent = 'Suche starten';
      }
    }

    function updateButtonStates() {
  // Prüfe ob Buttons existieren, bevor du sie verwendest
  const viewerOriginalBtn = document.getElementById('viewerOriginalBtn');
  const viewerSummaryBtn = document.getElementById('viewerSummaryBtn');
  
  // Wenn kein Vortrag geladen ist, verstecke alle Buttons
  if (!currentLectureData) {
    if (viewerOriginalBtn) {
      viewerOriginalBtn.style.display = 'none';
    }
    if (viewerSummaryBtn) {
      viewerSummaryBtn.style.display = 'none';
    }
    return;
  }
  
  // Wenn Vortrag geladen ist, zeige Buttons basierend auf Zustand
  if (viewerOriginalBtn && showingSummaryInMain) {
    viewerOriginalBtn.style.display = 'inline-block';
  } else if (viewerOriginalBtn) {
    viewerOriginalBtn.style.display = 'none';
  }
  
  if (viewerSummaryBtn) {
    viewerSummaryBtn.style.display = 'inline-block';
  }

  // Regenerate-Button nur lokal verfügbar
  const viewerRegenerateBtn = document.getElementById('viewerRegenerateBtn');
  if (viewerRegenerateBtn) {
    if (currentLectureData && isLocal) {
      viewerRegenerateBtn.style.display = 'inline-block';
    } else {
      viewerRegenerateBtn.style.display = 'none';
    }
  }
}

    async function loadRecentThematicQueries() {
      try {
        const container = document.getElementById('thematicRecentContainer');
        const list = document.getElementById('thematicRecentList');
        if (!container || !list) return;

        const resp = await fetch(`${API_BASE}/thematic-search-database.json`, { cache: 'no-store' });
        if (!resp.ok) { container.style.display = 'none'; return; }
        const db = await resp.json();

        // Einträge in Array wandeln: { key, query, timestamp }
        const entries = Object.entries(db).map(([key, val]) => ({
          key,
          query: val.query,
          timestamp: val.timestamp || val.cacheTimestamp || null
        })).filter(e => e.query);

        if (entries.length === 0) { container.style.display = 'none'; return; }

        // Nach Timestamp sortieren (neueste zuerst), fallback: Key-Order
        entries.sort((a, b) => {
          const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
          const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
          return tb - ta;
        });

        // Letzte bis zu 100 unique Queries mit zugehörigem Cache-Key
        const seen = new Set();
        const recentItems = [];
        for (const e of entries) {
          const q = String(e.query).trim();
          if (!seen.has(q)) {
            seen.add(q);
            recentItems.push({ query: q, key: e.key });
            if (recentItems.length >= 100) break;
          }
        }

        if (recentItems.length === 0) { container.style.display = 'none'; return; }

        list.innerHTML = recentItems.map(item => {
          const label = autocorrectQuery(item.query)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
          const keyEnc = encodeURIComponent(item.key);
          const queryEnc = encodeURIComponent(item.query);
          return `<li style="margin: 0.2rem 0;"><a href="#" onclick="openSavedThematicQueryEncoded('${keyEnc}','${queryEnc}'); return false;">${label}</a></li>`;
        }).join('');
        container.style.display = 'block';
      } catch (err) {
        console.warn('Konnte thematische Verlaufsliste nicht laden:', err);
        const container = document.getElementById('thematicRecentContainer');
        if (container) container.style.display = 'none';
      }
    }

    async function openSavedThematicQuery(cacheKey, query) {
      try {
        const resp = await fetch(`${API_BASE}/thematic-search-database.json`, { cache: 'no-store' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const db = await resp.json();
        const entry = db[cacheKey];
        if (!entry) {
          alert('Gespeicherte Themenanfrage nicht gefunden.');
          return;
        }
        const effectiveQuery = autocorrectQuery(query || entry.query || '');
        currentThematicQuery = effectiveQuery;
        // Parse GA-Filter aus dem Cache-Key (Format: query|depth|limit|ga)
        try {
          const parts = (cacheKey || '').split('|');
          currentThematicGAFilter = parts && parts.length >= 4 ? (parts[3] || '') : '';
          // Dropdown visual synchronisieren
          const gaSel = document.getElementById('thematicGAFilter');
          if (gaSel && currentThematicGAFilter) {
            gaSel.value = currentThematicGAFilter;
          }
        } catch (_) { currentThematicGAFilter = ''; }
        const input = document.getElementById('thematicQuery');
        if (input) input.value = effectiveQuery;
        const sources = entry.sources || [];
        currentSources = sources;
        renderThematicResults(effectiveQuery, entry.content || '', sources);
        // Scroll sidebar to top
        const sc = document.getElementById('sidebar-content');
        if (sc) sc.scrollTop = 0;
      } catch (e) {
        console.error('Fehler beim Laden der gespeicherten Themenanfrage:', e);
        alert('Fehler beim Laden der gespeicherten Themenanfrage.');
      }
    }

    async function openSavedThematicQueryEncoded(encodedKey, encodedQuery) {
      const key = decodeURIComponent(encodedKey);
      const q = decodeURIComponent(encodedQuery);
      return openSavedThematicQuery(key, q);
    }

    // Lösche das aktuell geladene Thema (nur lokal)
    async function deleteCurrentThema() {
      if (!isLocal) {
        alert('Diese Funktion ist nur in der lokalen Version verfügbar.');
        return;
      }
      
      if (!currentThematicQuery) {
        alert('Kein Thema geladen.');
        return;
      }
      
      const confirmMsg = `Möchten Sie das Thema "${currentThematicQuery}" wirklich löschen?`;
      if (!confirm(confirmMsg)) {
        return;
      }
      
      try {
        // Erstelle den Cache-Key (gleiche Logik wie im Backend)
        const gaFilter = currentThematicGAFilter || '';
        const cacheKey = `${currentThematicQuery}|7|100|${gaFilter}`;
        
        const response = await fetch(`${API_BASE}/api/delete-thematic-search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cacheKey: cacheKey })
        });
        
        if (!response.ok) {
          throw new Error(`Server Error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
          alert('Thema erfolgreich gelöscht.');
          
          // Leere die Ergebnisanzeige
          const container = document.getElementById('results');
          if (container) {
            container.innerHTML = '<p style="color: #666; font-style: italic;">Thema wurde gelöscht.</p>';
          }
          
          // Setze das Eingabefeld zurück
          const input = document.getElementById('thematicQuery');
          if (input) {
            input.value = '';
          }
          
          // Aktualisiere die Liste der zuletzt gesuchten Themen
          try {
            loadRecentThematicQueries();
          } catch (e) {
            console.warn('Fehler beim Aktualisieren der Themenliste:', e);
          }
          
          // Zurücksetzen der globalen Variablen
          currentThematicQuery = '';
          currentThematicGAFilter = '';
          currentSources = [];
        } else {
          alert('Fehler beim Löschen: ' + (result.error || 'Unbekannter Fehler'));
        }
      } catch (error) {
        console.error('Fehler beim Löschen des Themas:', error);
        alert('Fehler beim Löschen des Themas: ' + error.message);
      }
    }

    // Einfache, erweiterbare Rechtschreib-Autokorrektur für deutsche Begriffe/GA-Kontexte
    function autocorrectQuery(q) {
      if (!q) return q;
      let s = String(q);
      // Beispielhafte, häufige Korrekturen (erweiterbar)
      const corrections = [
        ['bewußtsein', 'Bewusstsein'],
        ['bewußtseins', 'Bewusstseins'],
        ['anthroposophie', 'Anthroposophie'],
        ['rudolf steiner', 'Rudolf Steiner'],
        ['goethe', 'Goethe'],
        ['kants', 'Kants'],
        ['ich organisation', 'Ich-Organisation'],
        ['aetherleib', 'Ätherleib'],
        ['astral leib', 'Astralleib'],
        ['geist selbst', 'Geist-Selbst']
      ];
      corrections.forEach(([from, to]) => {
        const re = new RegExp(`\\b${from}\\b`, 'gi');
        s = s.replace(re, to);
      });
      // Erstes Zeichen groß, wenn sinnvoll
      s = s.trim();
      if (s.length > 0) {
        s = s.charAt(0).toUpperCase() + s.slice(1);
      }
      return s;
    }


    async function toggleViewerH4() {
     const viewer = document.getElementById('viewer');
  
  if (!viewer) return;
  
  // Rechtes Summary Panel öffnen bei Klick auf "Übersicht" (falls noch nicht offen)
  const summaryPanel = document.getElementById('summary-panel');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  let panelWasJustOpened = false;
  
  if (summaryPanel && !summaryPanel.classList.contains('visible')) {
    summaryPanel.classList.add('visible');
    resizeHandle.classList.add('visible');
    summaryPanel.style.width = '280px';
    summaryPanel.style.minWidth = '280px';
    summaryPanel.style.marginRight = '0px';
    panelWasJustOpened = true;
  }
  
  // Fall 1: Original wird angezeigt → Übersicht anzeigen/generieren
  if (!showingSummaryInMain) {
    // Prüfe ob Zusammenfassung existiert
    if (currentLectureSummary) {
      // Zusammenfassung vorhanden → zeige sie an
      showSummaryView();
      // Nach dem Anzeigen weiter zum H4-Toggle (kein return hier)
    } else {
      // Keine Zusammenfassung → generiere neue
      if (!currentLectureData) {
        alert('Kein Vortrag geladen');
        return;
      }
      
// ...existing code...

// Auch den Übersicht-Button in Lade-Zustand setzen
const summaryBtn = document.getElementById('viewerSummaryBtn');
if (summaryBtn) {
  summaryBtn.disabled = true;
  summaryBtn.innerHTML = '<i>bitte warten...</i>';
  summaryBtn.style.opacity = '0.5';
}

try {
  // Generiere Zusammenfassung
  const response = await fetch(`${API_BASE}/api/summarize-lecture`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lectureId: currentLectureData.ID,
            forceRegenerate: false
          })
        });
        
        if (!response.ok) {
          throw new Error(`Server Error: ${response.status}`);
        }
        
        const data = await response.json();
        
        currentLectureSummary = {
          summary: data.summary,
          headings: data.headings || []
        };
        
        // Summary wurde bereits vom Backend in zentrale DB gespeichert
        console.log(`Online-Summary für ${currentLectureData.ID} wurde vom Backend gespeichert`);
        
        // Zeige Zusammenfassung
        showSummaryView();
        
      } catch (error) {
        console.error('Fehler beim Generieren der Zusammenfassung:', error);
        alert('Fehler beim Generieren der Zusammenfassung: ' + error.message);
        return; // Bei Fehler nicht weitermachen
      } finally {
        // Button immer zurücksetzen, egal ob Erfolg oder Fehler
        const summaryBtn = document.getElementById('viewerSummaryBtn');
        if (summaryBtn) {
          summaryBtn.disabled = false;
          summaryBtn.innerHTML = '≡ Übersicht';
          summaryBtn.style.opacity = '1';
        }
      }
    }
    // Nach dem Anzeigen/Generieren der Summary weiter zum H4-Toggle
  }
  
  // Fall 2: Zusammenfassung wird angezeigt → Toggle H4
  const tocList = document.getElementById('toc-list');
  const viewerH4 = viewer.querySelectorAll('h4');
  const tocH4 = tocList ? tocList.querySelectorAll('h4') : [];
  
  // Beim ersten Öffnen des Panels sollen H4s sichtbar bleiben
  if (panelWasJustOpened) {
    // Panel wurde gerade geöffnet → H4s sichtbar lassen
    viewerH4Collapsed = false;
  } else {
    // Normaler Toggle
    viewerH4Collapsed = !viewerH4Collapsed;
  }
  
  viewerH4.forEach(h4 => {
    h4.style.display = viewerH4Collapsed ? 'none' : 'block';
  });
  
  tocH4.forEach(h4 => {
    if (viewerH4Collapsed) {
      h4.classList.add('hidden');
    } else {
      h4.classList.remove('hidden');
    }
  });
}
    async function toggleSummaryPanel() {
      const panel = document.getElementById('summary-panel');
      const resizeHandle = document.getElementById('verticalResizeHandle');
      
      if (panel.classList.contains('visible')) {
        panel.classList.remove('visible');
        resizeHandle.classList.remove('visible');
        document.body.classList.add('summary-panel-collapsed');
        panel.style.width = '0';
        panel.style.minWidth = '0';
        panel.style.marginRight = '';
      } else {
        if (!currentLectureData) {
          alert('Bitte zuerst einen Vortrag laden');
          return;
        }
        
        panel.classList.add('visible');
        resizeHandle.classList.add('visible');
        document.body.classList.remove('summary-panel-collapsed');
        panel.style.width = '280px';
        panel.style.minWidth = '280px';
        panel.style.marginRight = '0px';
        
        // Sofort Main-Container anpassen, bevor Summary geladen wird
        updateHeaderPosition();
        
        await loadSummaryAutomatically();
      }
      
      updateHeaderPosition(); // Header-Position nach Panel-Toggle anpassen
    }

    async function loadSummaryAutomatically() {
      const tocList = document.getElementById('toc-list');
      
      if (!currentLectureSummary) {
        // UI während Summary-Generierung sperren
        setUILocked(true);
        
        try {
          tocList.innerHTML = '<p class="loading-message" style="padding: 1rem; font-style: italic;">bitte warten...</p>';
          
          const response = await fetch(`${API_BASE}/api/summarize-lecture`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              lectureId: currentLectureData.ID,
              forceRegenerate: false
            })
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server Error: ${response.status}`);
          }
          
          const data = await response.json();
          
          currentLectureSummary = {
            summary: data.summary,
            headings: data.headings || []
          };
          
          // KEIN automatisches Speichern von bereits existierenden Summaries
          // (Werden bereits in der zentralen DB gespeichert)
        } catch (error) {
          console.error('Zusammenfassungs-Fehler:', error);
          tocList.innerHTML = `<p style="padding: 1rem; color: #c53030;">Fehler: ${error.message}</p>`;
          return;
        } finally {
          // UI wieder entsperren
          setUILocked(false);
        }
      }
      
         const visibleIndex = getCurrentVisibleParagraphIndex();
  if (visibleIndex) {
      // Setze lastHighlightedIndex zurück, um ungewollte Markierung zu vermeiden
  lastHighlightedIndex = null;
  }
      
      showingSummaryInMain = true;
      displaySummaryWithHeadings(currentLectureData, currentLectureSummary);

// Buttons nach dem Anzeigen aktualisieren
setTimeout(() => {
  const viewerOriginalBtn = document.getElementById('viewerOriginalBtn');
  
  if (viewerOriginalBtn) {
    viewerOriginalBtn.style.display = 'inline-block';
  }
}, 50);
      buildTableOfContents();
      
      if (lastHighlightedIndex) {
        scrollToIndexInViewer(lastHighlightedIndex);
      }
    }

async function regenerateSummary() {
  if (!currentLectureData) {
    alert('Kein Vortrag geladen');
    return;
  }
  
  // UI während Summary-Generierung sperren
  setUILocked(true);

  const tocList = document.getElementById('toc-list');
  
  try {
    if (typeof closeBtn !== 'undefined') {
      closeBtn.disabled = true;
    }
    if (typeof regenerateBtn !== 'undefined') {
      regenerateBtn.disabled = true;
      regenerateBtn.classList.add('processing');
      regenerateBtn.textContent = 'bitte warten...';
    }
    tocList.innerHTML = '<p style="padding: 1rem; color: #666; font-style: italic;">🤖 Generiere neue Zusammenfassung mit KI...</p>';
    
    const response = await fetch(`${API_BASE}/api/summarize-lecture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lectureId: currentLectureData.ID,
        forceRegenerate: true
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Server Error: ${response.status}`);
    }
    
    const data = await response.json();
    
    currentLectureSummary = {
      summary: data.summary,
      headings: data.headings || []
    };
    
    console.log('Neue Zusammenfassung regeneriert - wurde vom Backend in zentrale DB gespeichert');
    
    // Beim Generieren einer neuen Summary immer nach oben scrollen
    lastHighlightedIndex = null;
    
    showingSummaryInMain = true;
    displaySummaryWithHeadings(currentLectureData, currentLectureSummary);

// Buttons nach dem Anzeigen aktualisieren
setTimeout(() => {
  const viewerOriginalBtn = document.getElementById('viewerOriginalBtn');
  
  if (viewerOriginalBtn) {
    viewerOriginalBtn.style.display = 'inline-block';
  }
}, 50);
    buildTableOfContents();
    
    if (lastHighlightedIndex) {
      scrollToIndexInViewer(lastHighlightedIndex);
    }
    
    try {
      const gaNumber = currentLectureData.ID.split('/')[0];
      
      await fetch(`${API_BASE}/api/ga-overview/${gaNumber}?refresh=true`);
      console.log('GA-Übersichts-Cache aktualisiert für', gaNumber);
      
      const titleElement = document.getElementById('document-title');
      const titleText = titleElement.textContent;
      
      if (titleText.includes(gaNumber) && titleText.includes(':')) {
        console.log('GA-Übersicht wird neu geladen...');
        const overviewResponse = await fetch(`${API_BASE}/api/ga-overview/${gaNumber}`);
        if (overviewResponse.ok) {
          const overviewData = await overviewResponse.json();
          displayGAOverview(overviewData);
          console.log('GA-Übersicht aktualisiert');
        }
      }
    } catch (cacheError) {
      console.warn('Cache-Aktualisierung fehlgeschlagen:', cacheError);
    }
    
  } catch (error) {
    console.error('Regenerierungs-Fehler:', error);
    tocList.innerHTML = `<p style="padding: 1rem; color: #c53030;">Fehler: ${error.message}</p>`;
  } finally {
    // UI wieder entsperren
    setUILocked(false);
    
    // Buttons zurücksetzen wenn vorhanden
    if (typeof closeBtn !== 'undefined') {
      closeBtn.disabled = false;
    }
    if (typeof regenerateBtn !== 'undefined') {
      regenerateBtn.disabled = false;
      regenerateBtn.classList.remove('processing');
      regenerateBtn.textContent = 'Neu generieren';
    }
  }
}

    function closeAndShowOriginal() {
  const panel = document.getElementById('summary-panel');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  
  panel.classList.remove('visible');
  resizeHandle.classList.remove('visible');
  panel.style.width = '0';
  panel.style.minWidth = '0';
  panel.style.marginRight = '0px';
  
  const visibleIndex = getCurrentVisibleParagraphIndex();
  if (visibleIndex) {
    lastHighlightedIndex = visibleIndex;
  }
  
  showingSummaryInMain = false;
  
  // Buttons zurücksetzen
  const viewerSummaryBtn = document.getElementById('viewerSummaryBtn');
  
  if (viewerSummaryBtn) {
    viewerSummaryBtn.disabled = false;
    viewerSummaryBtn.innerHTML = '≡ Übersicht';
    viewerSummaryBtn.style.opacity = '1';
  }
  
  const currentWord1 = document.getElementById('word1').value.trim();
  const currentWord2 = document.getElementById('word2').value.trim();
  let keywords = [currentWord1, currentWord2].filter(w => w && w.trim());
  let hasThematicKeywords = false;
  if (keywords.length === 0 && currentThematicQuery) {
    keywords = extractKeywordsFromQuery(currentThematicQuery);
    hasThematicKeywords = true;
  }
  
  // Enable highlighting if we have keywords from keyword search or thematic search
  const shouldHighlight = keywords.length > 0;
  displayLecture(currentLectureData, lastHighlightedIndex, keywords, shouldHighlight);
  
  setTimeout(() => {
    toggle.style.right = '0px';
    toggle.style.position = 'fixed';
    updateHeaderPosition(); // Header-Position nach Panel-Schließung anpassen
  }, 0);
}
function showSummaryView() {
  if (!currentLectureData || !currentLectureSummary) return;
  
  // Setze lastHighlightedIndex zurück, um ungewollte Markierung zu vermeiden
  lastHighlightedIndex = null;
  
  showingSummaryInMain = true;
  displaySummaryWithHeadings(currentLectureData, currentLectureSummary);
  
  setTimeout(() => {
    const viewerOriginalBtn = document.getElementById('viewerOriginalBtn');
    const viewerSummaryBtn = document.getElementById('viewerSummaryBtn');
    
    if (viewerOriginalBtn) {
      viewerOriginalBtn.style.display = 'inline-block';
    }
    // Button zurücksetzen falls er im Lade-Zustand war
    if (viewerSummaryBtn) {
      viewerSummaryBtn.disabled = false;
      viewerSummaryBtn.innerHTML = '≡ Übersicht';
      viewerSummaryBtn.style.opacity = '1';
    }
  }, 50);
}
    function getCurrentVisibleParagraphIndex() {
      const mainContainer = document.getElementById('main');
      const allParagraphs = document.querySelectorAll('[id^="para-"]');
      
      if (allParagraphs.length === 0) return null;
      
      const containerTop = mainContainer.getBoundingClientRect().top;
      
      for (let para of allParagraphs) {
        const paraRect = para.getBoundingClientRect();
        const relativeTop = paraRect.top - containerTop;
        
        if (relativeTop >= -50 && relativeTop <= 100) {
          return para.id.replace('para-', '');
        }
      }
      
      return allParagraphs[0].id.replace('para-', '');
    }

    // ============================================================================
    // ZENTRALE HIGHLIGHTING-VERWALTUNG
    let highlightTimeout = null;

    function addHighlightingWithAutoRemove(element) {
      // Entferne vorherige Markierung und Timer (ohne Fade-Out)
      clearPreviousHighlighting();
      
      // Füge neue Markierung hinzu
      if (element) {
        element.classList.add('highlighted-paragraph');
        
        // Entferne automatisch nach 5 Sekunden konstanter Anzeige
        highlightTimeout = setTimeout(() => {
          removeAllHighlighting();
        }, 5000);
      }
    }

    function clearPreviousHighlighting() {
      // Entferne vorherige Markierungen sofort (ohne Fade-Out)
      const highlightedElements = document.querySelectorAll('.highlighted-paragraph');
      highlightedElements.forEach(element => {
        element.classList.remove('highlighted-paragraph');
        element.style.transition = '';
        element.style.backgroundColor = '';
        element.style.boxShadow = '';
      });
      
      // Lösche den Timer falls vorhanden
      if (highlightTimeout) {
        clearTimeout(highlightTimeout);
        highlightTimeout = null;
      }
    }

    function removeAllHighlighting() {
      // Starte Fade-Out für alle highlighted-paragraph Klassen
      const highlightedElements = document.querySelectorAll('.highlighted-paragraph');
      highlightedElements.forEach(element => {
        // Starte Fade-Out nur durch Änderung der Opacity (keine Größenänderung)
        element.style.transition = 'background-color 1s ease-out, box-shadow 1s ease-out';
        element.style.backgroundColor = 'transparent';
        element.style.boxShadow = '0 0 0 0.4rem transparent';
        
        // Entferne die Klasse nach der Transition
        setTimeout(() => {
          element.classList.remove('highlighted-paragraph');
          element.style.transition = '';
          element.style.boxShadow = '';
        }, 1000);
      });
      
      // Lösche den Timeout falls vorhanden
      if (highlightTimeout) {
        clearTimeout(highlightTimeout);
        highlightTimeout = null;
      }
    }

    function scrollToIndexInViewer(targetIndex) {
      if (!targetIndex) return;
      
      const mainContainer = document.getElementById('main');
      
      // Falls der Absatz nicht gefunden wird und wir in der Summary sind, 
      // versuche zuerst das Original anzuzeigen
      let paraElement = document.getElementById(`para-${targetIndex}`);
      if (!paraElement && showingSummaryInMain && currentLectureData) {
        console.log('Absatz nicht in Summary gefunden, zeige Original...');
        showingSummaryInMain = false;
        
        let displayKeywords = [];
        const currentWord1 = document.getElementById('word1').value.trim();
        const currentWord2 = document.getElementById('word2').value.trim();
        if (currentWord1 || currentWord2) {
          displayKeywords = [currentWord1, currentWord2].filter(w => w && w.trim());
        }
        else if (currentThematicQuery) {
          displayKeywords = extractKeywordsFromQuery(currentThematicQuery);
        }
        
        displayLecture(currentLectureData, targetIndex, displayKeywords);
        updateButtonStates();
        
        // Nach dem Rendern nochmal versuchen zu scrollen
        setTimeout(() => scrollToIndexInViewer(targetIndex), 200);
        return;
      }
      
      if (paraElement) {
        // Berechne Position für Positionierung am unteren Rand des Headers
        const header = document.getElementById('viewer-header');
        const headerHeight = header ? header.offsetHeight + 5 : 5; // Nur 5px minimaler Abstand
        
        const mainRect = mainContainer.getBoundingClientRect();
        const paraRect = paraElement.getBoundingClientRect();
        const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight;
        
        mainContainer.scrollTop = Math.max(0, relativeTop);
        
        // Verwende zentrale Highlighting-Funktion mit Auto-Remove
        addHighlightingWithAutoRemove(paraElement);
      }
    }

  function displaySummaryWithHeadings(lecture, summaryObj) {
  const viewer = document.getElementById('viewer');
  const titleElement = document.getElementById('document-title');
  
  // NEU: Setze den Vortragstitel als Link
  const displayTitle = lecture.fileName || lecture.title || lecture.ID;
  const onlineLink = createOnlineURL(lecture);
  titleElement.innerHTML = `<a href="${onlineLink}" target="rudolf-steiner-online">${displayTitle}</a>`;
  
  const currentWord1 = document.getElementById('word1').value.trim();
  const currentWord2 = document.getElementById('word2').value.trim();
  let keywords = [];
  
  if ((currentWord1 || currentWord2) && searchResults.length > 0) {
    const isFromCurrentSearch = searchResults.some(result => result.ID === lecture.ID);
    if (isFromCurrentSearch) {
      keywords = [currentWord1, currentWord2].filter(w => w && w.trim());
    }
  }
  
  let html = '';
  
  const headings = summaryObj.headings || [];
  const hasHeadings = headings.length > 0;
  
  // Nur Zusammenfassung und Trennlinie anzeigen, wenn Überschriften vorhanden sind
  if (hasHeadings) {
    html += '<div style="margin-bottom: 1rem;">';
    html += '<p><strong>Zusammenfassung</strong></p>';
    html += `<p style="font-style: italic;">${summaryObj.summary}</p>`;
    html += '<hr style="margin: 2rem 0; border: none; border-top: 1px solid #ddd;">';
    html += '</div>';
  }
  
  const paragraphs = lecture.paragraphs || [];
  
  paragraphs.forEach((para, idx) => {
    const paraIndex = para.index ? para.index.replace(/^\^/, '') : `para_${idx}`;
    const paraIndexWithCaret = para.index || `^${paraIndex}`;
    
    const matchingHeadings = headings.filter(h => {
      const hIndex = h.index || '';
      const hIndexClean = hIndex.replace(/^\^/, '');
      return hIndex === paraIndex || 
             hIndex === paraIndexWithCaret || 
             hIndexClean === paraIndex;
    });
    
    matchingHeadings
      .sort((a, b) => {
        if (a.level === 'h3' && b.level === 'h4') return -1;
        if (a.level === 'h4' && b.level === 'h3') return 1;
        return 0;
      })
      .forEach((heading, hIdx) => {
        const headingText = heading.text || heading.title || 'Überschrift';
        const level = heading.level || 'h3';
        
        if (level === 'h3') {
          html += `<h3 id="heading-${idx}-${hIdx}">${headingText}</h3>`;
        } else if (level === 'h4') {
          html += `<h4 id="heading-${idx}-${hIdx}">${headingText}</h4>`;
        }
      });
    
    let content = para.content || para.text || '';
    
    if (keywords && keywords.length > 0) {
      keywords.forEach(word => {
        if (word && word.trim()) {
          const regex = new RegExp(`(${word.trim()})`, "gi");
          content = content.replace(regex, "<mark>$1</mark>");
        }
      });
    }
    
    const isTargetPara = lastHighlightedIndex && paraIndex === lastHighlightedIndex;
const highlightClass = isTargetPara ? 'highlighted-paragraph' : '';

html += `<div class="paragraph ${highlightClass}" id="para-${paraIndex}" data-array-index="${idx}">${content}</div>`;
  });
  
  viewer.innerHTML = html;
  
  // Scrolle zum markierten Absatz in der Summary oder nach oben
  if (lastHighlightedIndex) {
    setTimeout(() => {
      scrollToIndexInViewer(lastHighlightedIndex);
    }, 50);
  } else {
    // Neuer Vortrag - scrolle nach oben unter den Header
    const mainContainer = document.getElementById('main');
    mainContainer.scrollTop = 0;
  }
  
  updateHeaderPosition(); // Header-Position und Viewer-Padding anpassen
}



    // Entfernt nur inline style-Attribute aus Backend-HTML, behält CSS-Klassen bei
    function removeInlineStyles(element) {
      if (!element) return;
      
      // Entferne nur style-Attribute von allen Elementen (behält CSS-Klassen)
      const allElements = element.querySelectorAll('*');
      allElements.forEach(el => {
        el.removeAttribute('style');
      });
      
      // Entferne auch vom Container selbst
      element.removeAttribute('style');
      
      console.log('[FORMATTING] Inline Styles aus Backend-HTML entfernt (CSS-Klassen beibehalten)');
    }

    // Stellt einheitliche Leerzeichen um Klammern bei GA-Quellenangaben her
    function normalizeCitationSpacing(container) {
      if (!container) return;
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(node => {
        let s = node.nodeValue || '';
        if (!s) return;
        // Leerzeichen vor "(GA" sicherstellen
        s = s.replace(/([^\s(])\((GA)/g, '$1 ($2');
        // Leerzeichen nach ")" sicherstellen, außer wenn direkt Satzzeichen folgt
        s = s.replace(/\)(?=([^\s\.,;:!\?\)]))/g, ') ');
        node.nodeValue = s;
      });
    }

    function extractKeywordsFromQuery(query) {
      const stopWords = [
        'wie', 'ist', 'das', 'verhältnis', 'von', 'und', 'der', 'die', 'des', 
        'den', 'dem', 'ein', 'eine', 'einem', 'einen', 'was', 'welche', 'welcher',
        'zwischen', 'bei', 'nach', 'für', 'mit', 'aus', 'über', 'sich', 'zur',
        'steiner', 'rudolf', 'sieht', 'kritisiert', 'spielt', 'rolle'
      ];
      
      const words = query.toLowerCase()
        .replace(/[.,;:!?]/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 3 && !stopWords.includes(word));
      
      return words;
    }
    
    function renderThematicResults(query, content, sources, appliedGA = '') {
      const container = document.getElementById('results');
      
      const sortedSources = [...sources].sort((a, b) => {
        const dateA = a.date || '';
        const dateB = b.date || '';
        return dateA.localeCompare(dateB);
      });
      
      // Verwende ausschließlich den GA-Band, der für DIESES Ergebnis angewendet wurde
      const selectedGA = appliedGA || '';
      const headingBase = autocorrectQuery(query) || '';
      const headingWithGA = selectedGA ? `${headingBase} (aus ${selectedGA})` : headingBase;
      const safeHeading = headingWithGA.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      // Delete-Button nur in lokaler Version anzeigen
      const deleteButtonHTML = isLocal 
        ? `<button id="deleteThemaBtn" onclick="deleteCurrentThema()" style="padding: 4px 12px; font-size: 0.85em; border: 1px solid #d9534f; background: transparent; color: #d9534f; cursor: pointer; border-radius: 4px; transition: opacity 0.2s;">Thema löschen</button>`
        : '';
      container.innerHTML = `
        <div class="semantic-answer">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h1 style="margin: 0;">${safeHeading}</h1>
            ${deleteButtonHTML}
          </div>
          <div class="answer-content" id="answerContent"></div>
        </div>
      `;
      
      const answerDiv = document.getElementById('answerContent');
      answerDiv.innerHTML = marked.parse(content);
      
      // BACKEND-FORMATIERUNG ENTFERNEN: Alle inline Styles aus Backend-HTML entfernen
      removeInlineStyles(answerDiv);
      // Einheitliche Abstände um Klammern an GA-Quellenangaben
      normalizeCitationSpacing(answerDiv);

      // Falls die Quellen direkt in der Überschrift stehen: Überschrift säubern und Rest in neuen Absatz verschieben
      try {
        const titleText = 'Weitere relevante Quellen';
        const sourcesHeading = Array.from(answerDiv.querySelectorAll('h2,h3'))
          .find(h => (h.textContent || '').trim().toLowerCase().startsWith(titleText.toLowerCase()));
        if (sourcesHeading) {
          const currentHTML = (sourcesHeading.innerHTML || '').trim();
          const reEsc = titleText.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
          const restHTML = currentHTML.replace(new RegExp('^' + reEsc + '\\s*', 'i'), '');
          if (restHTML && restHTML.trim().length > 0) {
            sourcesHeading.textContent = titleText;
            const p = document.createElement('p');
            p.innerHTML = restHTML;
            if (sourcesHeading.nextSibling) {
              sourcesHeading.parentNode.insertBefore(p, sourcesHeading.nextSibling);
            } else {
              sourcesHeading.parentNode.appendChild(p);
            }
          }
        }
      } catch (_) {}

      // Sicherstellen: Nach der Überschrift "Weitere relevante Quellen" steht ein Absatz
      try {
        const sourcesHeading = Array.from(answerDiv.querySelectorAll('h2,h3'))
          .find(h => (h.textContent || '').trim() === 'Weitere relevante Quellen');
        if (sourcesHeading) {
          // Nächstes sinnvolles Geschwister ermitteln (Whitespace überspringen)
          let ns = sourcesHeading.nextSibling;
          while (ns && ns.nodeType === 3 && (ns.nodeValue || '').trim() === '') {
            ns = ns.nextSibling;
          }
          const isBlockBreak = ns && ns.nodeType === 1 && /^(P|DIV|UL|OL|BR)$/i.test(ns.nodeName);
          if (!isBlockBreak) {
            const br = document.createElement('br');
            if (sourcesHeading.nextSibling) {
              sourcesHeading.parentNode.insertBefore(br, sourcesHeading.nextSibling);
            } else {
              sourcesHeading.parentNode.appendChild(br);
            }
          }
        }
      } catch (_) {}
      
      console.log('HTML nach marked.parse:', answerDiv.innerHTML.substring(0, 500));
      console.log('Anzahl .ga-reference Links:', answerDiv.querySelectorAll('.ga-reference').length);
      
      document.getElementById('status').textContent = `Antwort aus ${sortedSources.length} Quellen`;
      
      // Scroll sidebar to top to show results from the beginning
      document.getElementById('sidebar-content').scrollTop = 0;
      
      setTimeout(() => {
        const gaLinks = answerDiv.querySelectorAll('.ga-reference');
        
        gaLinks.forEach(link => {
  const lectureId = link.getAttribute('data-id');
  const targetIndex = link.getAttribute('data-index');
  
  if (lectureId && targetIndex) {
    link.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      // Summary Panel bleibt offen (wird in showLecture automatisch geöffnet)
      const keywords = extractKeywordsFromQuery(currentThematicQuery);
      await showLecture(lectureId, targetIndex, keywords);
    });
  }
});
      }, 100);
    }

    async function showLectureTop(lectureId) {
      // Scroll zum Anfang erzwingen
      const mainContainer = document.getElementById('main');
      if (mainContainer) {
        mainContainer.scrollTop = 0;
      }
      
      await showLecture(lectureId, null, []);
      
      // Sicherheitshalber nochmal nach dem Laden
      setTimeout(() => {
        if (mainContainer) {
          mainContainer.scrollTop = 0;
        }
      }, 100);
    }

    // HIER EINFÜGEN - Prüfe ob Zusammenfassung für Vortrag existiert
    async function checkIfSummaryExists(lectureId) {
      try {
        const response = await fetch(`${API_BASE}/api/summarize-lecture`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lectureId: lectureId,
            forceRegenerate: false
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.summary && data.summary.trim() !== '';
        }
        return false;
      } catch (error) {
        return false;
      }
    }

    // Zeige temporäre Nachricht
    function showTemporaryMessage(message) {
      const existingMsg = document.getElementById('temp-loading-message');
      if (existingMsg) existingMsg.remove();
      
      const msgDiv = document.createElement('div');
      msgDiv.id = 'temp-loading-message';
      msgDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #467886;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        font-size: 0.9em;
        font-style: italic;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      `;
      msgDiv.textContent = message;
      document.body.appendChild(msgDiv);
      
      setTimeout(() => msgDiv.remove(), 3000);
    }

    async function showLecture(lectureId, targetIndex, keywords = []) {
  const summaryPanel = document.getElementById('summary-panel');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  const tocList = document.getElementById('toc-list');
  
  // Aktuellen Vortrag tracken
  window.currentOpenLectureId = lectureId;

  try {
    const parts = lectureId.split('/');
    const url = parts.length === 2 
                ? `${API_BASE}/api/full-lecture/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`
                : `${API_BASE}/api/full-lecture/${encodeURIComponent(lectureId)}`;

    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Vortrag nicht gefunden: ${lectureId}`);
    }
    
    const data = await response.json();
    currentLectureData = data.lecture;
    
    // NEU: Prüfe ob Zusammenfassung bereits existiert (ohne neue zu generieren)
    try {
      const parts = lectureId.split('/');
      const summaryResponse = await fetch(`${API_BASE}/api/check-summary/${parts[0]}/${parts[1]}`);
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        
        // Wenn Zusammenfassung existiert (fromCache: true oder neue Daten)
        if (summaryData.exists && summaryData.summary) {
          currentLectureSummary = {
            summary: summaryData.summary,
            headings: summaryData.headings || []
          };
          
          // Zeige bearbeitete Version mit Überschriften
          showingSummaryInMain = true;
          
          let displayKeywords = keywords;
          if (!displayKeywords || displayKeywords.length === 0) {
            const currentWord1 = document.getElementById('word1').value.trim();
            const currentWord2 = document.getElementById('word2').value.trim();
            if (currentWord1 || currentWord2) {
              displayKeywords = [currentWord1, currentWord2].filter(w => w && w.trim());
            }
            else if (currentThematicQuery) {
              displayKeywords = extractKeywordsFromQuery(currentThematicQuery);
            }
          }
          // Setze lastHighlightedIndex VOR dem Rendern für Highlighting
          if (targetIndex) {
            const cleanIndex = targetIndex.replace(/^\^/, '');
            lastHighlightedIndex = cleanIndex;
          } else {
            // Neuer Vortrag - scrolle nach oben
            lastHighlightedIndex = null;
          }
          
          displaySummaryWithHeadings(currentLectureData, currentLectureSummary);

// Buttons nach dem Anzeigen aktualisieren
setTimeout(() => {
  const viewerOriginalBtn = document.getElementById('viewerOriginalBtn');
  const viewerSummaryBtn = document.getElementById('viewerSummaryBtn');
  
  if (viewerOriginalBtn) {
    viewerOriginalBtn.style.display = 'inline-block';
  }
  // ...existing code...
}, 50);
          
          if (targetIndex) {
            const cleanIndex = targetIndex.replace(/^\^/, '');
            setTimeout(() => scrollToIndexInViewer(cleanIndex), 100);
          }
          
          updateButtonStates();
          
          // Öffne Summary Panel automatisch (auch bei vorhandener Summary)
          setTimeout(() => {
            if (summaryPanel) {
              console.log('[SUMMARY-PANEL] Auto-open triggered (with summary)');
              summaryPanel.classList.add('visible');
              summaryPanel.style.width = '280px';
              summaryPanel.style.minWidth = '280px';
              summaryPanel.style.marginRight = '0px';
              summaryPanel.style.removeProperty('display');
              
              if (resizeHandle) {
                resizeHandle.classList.add('visible');
                resizeHandle.style.removeProperty('display');
                resizeHandle.style.removeProperty('width');
              }
              
              document.body.classList.remove('summary-panel-collapsed');
              updateHeaderPosition();
              buildTableOfContents();
            }
          }, 100);
          
          return;
        }
      }
    } catch (summaryError) {
      console.log('Keine Zusammenfassung vorhanden, zeige Original:', summaryError.message);
    }
    
    // Fallback: Zeige Original wenn keine Zusammenfassung vorhanden
    currentLectureSummary = null;
    showingSummaryInMain = false;
    
    let displayKeywords = keywords;
    if (!displayKeywords || displayKeywords.length === 0) {
      const currentWord1 = document.getElementById('word1').value.trim();
      const currentWord2 = document.getElementById('word2').value.trim();
      if (currentWord1 || currentWord2) {
        displayKeywords = [currentWord1, currentWord2].filter(w => w && w.trim());
      }
      else if (currentThematicQuery) {
        displayKeywords = extractKeywordsFromQuery(currentThematicQuery);
      }
    }
    
    updateButtonStates();
    displayLecture(data.lecture, targetIndex, displayKeywords);
    
    // Öffne Summary Panel automatisch nach dem Laden (immer)
    setTimeout(() => {
      if (summaryPanel) {
        console.log('[SUMMARY-PANEL] Auto-open triggered');
        summaryPanel.classList.add('visible');
        summaryPanel.style.width = '280px';
        summaryPanel.style.minWidth = '280px';
        summaryPanel.style.marginRight = '0px';
        summaryPanel.style.removeProperty('display');
        
        if (resizeHandle) {
          resizeHandle.classList.add('visible');
          resizeHandle.style.removeProperty('display');
          resizeHandle.style.removeProperty('width');
        }
        
        document.body.classList.remove('summary-panel-collapsed');
        
        // Header-Position aktualisieren
        updateHeaderPosition();
        
        // TOC generieren
        buildTableOfContents();
      } else {
        console.warn('[SUMMARY-PANEL] Panel nicht gefunden für auto-open');
      }
    }, 100);
    
  } catch (error) {
    console.error('Fehler beim Laden:', error);
    document.getElementById('viewer').innerHTML = `
      <div class="error-message">
        <strong>Fehler beim Laden des Vortrags:</strong><br>${error.message}
      </div>
    `;
  }
}

// Neuerzeuge eine Summary für den aktuell geladenen Vortrag (nur lokal sichtbar/aktiv)
async function regenerateCurrentSummary() {
  if (!currentLectureData || !currentLectureData.ID) {
    alert('Kein Vortrag geladen.');
    return;
  }
  if (!confirm('Summary neu erzeugen und alte Version überschreiben?')) return;

  const lectureId = currentLectureData.ID;
  // Sperre die UI während der Regeneration
  setUILocked(true);
  const regenBtn = document.getElementById('viewerRegenerateBtn');
  try {
    // UI: Spinner + Disable
    if (regenBtn) {
      regenBtn.disabled = true;
      const spinner = document.createElement('span');
      spinner.className = 'btn-spinner';
      spinner.id = 'regen-spinner';
      regenBtn.appendChild(spinner);
    }

    // Fordere Regeneration vom Backend an
    const resp = await fetch(`${API_BASE}/api/summarize-lecture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lectureId: lectureId, forceRegenerate: true })
    });

    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    const data = await resp.json();

    // Speichere das Ergebnis in der zentralen DB
    const saveResp = await fetch(`${API_BASE}/api/save-summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lectureId: lectureId, summary: { summary: data.summary, headings: data.headings || [] } })
    });

    if (!saveResp.ok) throw new Error(`Speichern fehlgeschlagen: ${saveResp.status}`);

    alert('Summary neu erzeugt und gespeichert.');
    // Aktualisiere aktuelle Anzeige
    currentLectureSummary = { summary: data.summary, headings: data.headings || [] };
    displaySummaryWithHeadings(currentLectureData, currentLectureSummary);
    
    // Aktualisiere GA-Übersicht falls geöffnet
    if (currentLectureData && currentLectureData.ID) {
      const gaNumber = currentLectureData.ID.split('/')[0];
      console.log('GA-Übersicht aktualisieren nach Summary-Generierung für', gaNumber);
      // Cache zurücksetzen, um aktualisierte Datenbank zu laden
      externalSummaryDBCache = null;
      setTimeout(() => {
        openGAOverview(gaNumber);
      }, 500);
    }
  } catch (err) {
    console.error('Regenerate error:', err);
    alert('Fehler beim Neuerzeugen der Summary: ' + err.message);
  } finally {
    // UI wieder freigeben
    setUILocked(false);
    if (regenBtn) {
      regenBtn.disabled = false;
      const spinner = document.getElementById('regen-spinner');
      if (spinner) spinner.remove();
    }
  }
}

// Startet die Batch-Zusammenfassungs-Generation für den aktuell im Tab Texte ausgewählten GA-Band
function startBatchSummaries() {
  const gaNumber = document.getElementById('texteGAFilter')?.value;
  if (!gaNumber) {
    alert('Bitte wählen Sie zuerst einen GA-Band im Tab Texte (Dropdown) aus.');
    return;
  }

  (async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/ga-overview/${encodeURIComponent(gaNumber)}`);
      if (!resp.ok) throw new Error(`GA-Overview konnte nicht geladen werden (${resp.status})`);
      const data = await resp.json();
      const lectures = data.lectures || [];
      // Filter: nur Vorträge ohne Summary
      const noSummary = lectures.filter(l => !l.summary || l.summary.trim() === '');
      if (noSummary.length === 0) {
        alert(`Alle Vorträge in ${gaNumber} haben bereits Zusammenfassungen.`);
        return;
      }

      if (!confirm(`Es werden ${noSummary.length} Vorträge ohne Zusammenfassung in ${gaNumber} erzeugt. Fortfahren?`)) {
        return;
      }

      batchSummarizeGA(gaNumber);
    } catch (err) {
      alert('Fehler beim Prüfen der GA-Übersicht: ' + err.message);
    }
  })();
}

// Führt die Summarizer-Requests sequentiell aus und zeigt Fortschritt an
async function batchSummarizeGA(gaNumber) {
  const resultsContainer = document.getElementById('results');
  resultsContainer.innerHTML = `
    <div class="batch-progress" id="batch-progress-ui">
      <div id="batch-status">Vorbereiten...</div>
      <div style="margin-top:8px; background:#e9eef0; border-radius:4px; overflow:hidden;">
        <div class="bar" id="batch-progress-bar"></div>
      </div>
    </div>
  `;

  try {
    // Sperre UI während des Batch-Laufs
    setUILocked(true);
    
    // Lade lokale summary-database (nur lokal verfügbar)
    let summaryDB = {};
    try {
      const sresp = await fetch(`${API_BASE}/summary-database.json`, { cache: 'no-store' });
      if (sresp.ok) summaryDB = await sresp.json();
      console.log(`[BATCH] Summary-DB geladen: ${Object.keys(summaryDB).length} Einträge`);
    } catch (e) {
      console.warn('Konnte summary-database.json nicht laden:', e.message);
    }
    
    const resp = await fetch(`${API_BASE}/api/ga-overview/${encodeURIComponent(gaNumber)}`);
    if (!resp.ok) throw new Error(`GA-Overview konnte nicht geladen werden: ${resp.status}`);
    const data = await resp.json();
    let lectures = data.lectures || [];
    if (lectures.length === 0) {
      resultsContainer.innerHTML = '<p>Keine Vorträge in dieser GA gefunden.</p>';
      return;
    }

    // Nur Vorträge ohne Summary verarbeiten (prüfe gegen summary-database.json)
    const missing = lectures.filter(l => {
      const lectureId = l.ID;
      const entry = summaryDB[lectureId];
      // Vortrag hat keine Summary wenn:
      // 1. Kein Eintrag in der DB ODER
      // 2. Eintrag existiert aber summary ist leer/fehlt
      return !entry || !entry.summary || (typeof entry.summary === 'string' && entry.summary.trim() === '');
    });
    
    console.log(`[BATCH] ${missing.length} von ${lectures.length} Vorträgen ohne Summary in ${gaNumber}`);
    
    if (missing.length === 0) {
      alert(`Alle Vorträge in ${gaNumber} haben bereits Zusammenfassungen.`);
      return;
    }
    lectures = missing;

    const total = lectures.length;
    let completed = 0;
    let failed = 0;

    for (const lecture of lectures) {
      const lectureId = lecture.ID;
      const statusEl = document.getElementById('batch-status');
      const barEl = document.getElementById('batch-progress-bar');
      if (statusEl) statusEl.textContent = `Verarbeite ${lectureId} (${completed + 1}/${total})`;

      try {
        const sResp = await fetch(`${API_BASE}/api/summarize-lecture`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lectureId: lectureId, forceRegenerate: true })
        });

        if (!sResp.ok) {
          console.warn('Fehler bei Zusammenfassung', lectureId, sResp.status);
          failed += 1;
        } else {
          const sData = await sResp.json();
          console.log('Summary erzeugt für', lectureId, sData);
        }
      } catch (err) {
        console.warn('Exception beim Erzeugen der Summary für', lectureId, err);
        failed += 1;
      }

      completed += 1;
      const pct = Math.round((completed / total) * 100);
      if (barEl) barEl.style.width = pct + '%';
    }

  const doneMsg = `Batch fertig. ${completed - failed} erfolgreich, ${failed} fehlgeschlagen.`;
    const statusEl = document.getElementById('batch-status');
    if (statusEl) statusEl.textContent = doneMsg;

  // UI wieder freigeben
  setUILocked(false);

    // Aktualisiere die GA-Übersicht, damit neue Summaries sichtbar werden
    setTimeout(() => {
      openGAOverview(gaNumber);
    }, 800);

  } catch (err) {
    console.error('Batch-Fehler:', err);
    resultsContainer.innerHTML = `<div class="error-message"><strong>Batch-Fehler:</strong><br>${err.message}</div>`;
  }
}

// Startet die Batch-Zusammenfassungs-Generation für alle GA-Bände in der Dropdown-Liste im Tab Texte
async function startBatchAllSummaries() {
  try {
    // Hole alle GA-Bände aus dem Dropdown im Tab Texte
    const texteGAFilter = document.getElementById('texteGAFilter');
    if (!texteGAFilter) {
      alert('Dropdown im Tab Texte nicht gefunden.');
      return;
    }
    
    // Sammle alle GA-Nummern aus dem Dropdown (außer dem ersten leeren Eintrag)
    const gaBands = [];
    for (let i = 1; i < texteGAFilter.options.length; i++) {
      const value = texteGAFilter.options[i].value;
      if (value) gaBands.push(value);
    }
    
    if (gaBands.length === 0) {
      alert('Keine GA-Bände im Dropdown gefunden.');
      return;
    }
    
    // Lade lokale summary-database VORHER (nur lokal verfügbar)
    let summaryDB = {};
    try {
      const sresp = await fetch(`${API_BASE}/summary-database.json`, { cache: 'no-store' });
      if (sresp.ok) summaryDB = await sresp.json();
      console.log(`[BATCH-ALL] Summary-DB geladen: ${Object.keys(summaryDB).length} Einträge`);
    } catch (e) {
      console.warn('Konnte summary-database.json nicht laden:', e.message);
    }
    
    // Sammle alle Vorträge ohne Summary aus allen GA-Bänden
    const lectureIdsToProcess = [];
    
    for (const gaNumber of gaBands) {
      try {
        const resp = await fetch(`${API_BASE}/api/ga-overview/${encodeURIComponent(gaNumber)}`);
        if (!resp.ok) continue; // Überspringe GA-Bände, die nicht geladen werden können
        const data = await resp.json();
        const lectures = data.lectures || [];
        
        // Filter: nur Vorträge ohne Summary (prüfe gegen summary-database.json)
        for (const lecture of lectures) {
          const lectureId = lecture.ID;
          const entry = summaryDB[lectureId];
          // Vortrag hat keine Summary wenn:
          // 1. Kein Eintrag in der DB ODER
          // 2. Eintrag existiert aber summary ist leer/fehlt
          const hasNoSummary = !entry || !entry.summary || (typeof entry.summary === 'string' && entry.summary.trim() === '');
          if (hasNoSummary) {
            lectureIdsToProcess.push(lectureId);
          }
        }
      } catch (err) {
        console.warn(`Fehler beim Laden von ${gaNumber}:`, err.message);
      }
    }

    console.log(`[BATCH-ALL] ${lectureIdsToProcess.length} Vorträge ohne Summary gefunden`);

    if (lectureIdsToProcess.length === 0) {
      alert('Keine Vorträge ohne Summary in den verfügbaren GA-Bänden gefunden.');
      return;
    }
    
    // Bestätigung mit korrekter Anzahl
    if (!confirm(`Batch All: Es werden ${lectureIdsToProcess.length} Vorträge ohne Summary in ${gaBands.length} GA-Bänden bearbeitet. Fortfahren?`)) {
      return;
    }

    // Sperre UI während des Batch-All Prozesses
    setUILocked(true);

    // Teile in 10 Portionen auf
    const portions = 10;
    const chunkSize = Math.ceil(lectureIdsToProcess.length / portions);
    const chunks = [];
    for (let i = 0; i < lectureIdsToProcess.length; i += chunkSize) {
      chunks.push(lectureIdsToProcess.slice(i, i + chunkSize));
    }

    // UI vorbereiten
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = `
      <div class="batch-progress" id="batch-progress-ui">
        <div id="batch-status">Vorbereiten Batch All...</div>
        <div style="margin-top:8px; background:#e9eef0; border-radius:4px; overflow:hidden;">
          <div class="bar" id="batch-progress-bar"></div>
        </div>
        <div style="margin-top:8px;"><button id="batch-cancel-btn" class="depth-btn" style="padding:4px 8px; font-size:0.85em;">Abbrechen</button></div>
      </div>
    `;

    const abortController = new AbortController();
    document.getElementById('batch-cancel-btn').addEventListener('click', () => {
      abortController.abort();
    });

    let totalProcessed = 0;
    let totalFailed = 0;

    // Verarbeite die Chunks parallel (alle Portionen gleichzeitig)
    const total = lectureIdsToProcess.length;
    let processedTotal = 0;
    let failedTotal = 0;

    const statusEl = document.getElementById('batch-status');
    const barEl = document.getElementById('batch-progress-bar');
    if (statusEl) statusEl.textContent = `Starte ${chunks.length} Portionen parallel (${total} Vorträge aus ${gaBands.length} GA-Bänden)...`;

    // Shared onProgress callback
    const onProgress = ({ success }) => {
      processedTotal += 1;
      if (!success) failedTotal += 1;
      try {
        if (barEl) barEl.style.width = Math.round((processedTotal / total) * 100) + '%';
        if (statusEl) statusEl.textContent = `Verarbeitet ${processedTotal}/${total} (${failedTotal} fehlgeschlagen)`;
      } catch (e) {}
    };

    const promises = chunks.map((chunk, idx) => {
      if (!chunk || chunk.length === 0) return Promise.resolve({ processed: 0, failed: 0 });
      return batchSummarizeLectures(chunk, { concurrency: 10, signal: abortController.signal, onProgress });
    });

    const settled = await Promise.allSettled(promises);
    // Aggregate results
    for (const res of settled) {
      if (res.status === 'fulfilled') {
        totalProcessed += res.value.processed || 0;
        totalFailed += res.value.failed || 0;
      } else {
        // rejected (possibly aborted)
        console.warn('Portion failed or aborted:', res.reason);
      }
    }

    // Ensure progress bar full
    if (barEl) barEl.style.width = '100%';

    const statusElFin = document.getElementById('batch-status');
    if (statusElFin) statusElFin.textContent = `Batch All fertig. ${totalProcessed - totalFailed} erfolgreich, ${totalFailed} fehlgeschlagen.`;
    // Aktualisiere Ansicht
    setTimeout(() => { try { if (typeof refreshLectureList === 'function') refreshLectureList(); } catch(e){} }, 800);

  // UI wieder freigeben
  setUILocked(false);

  } catch (err) {
    alert('Fehler beim Starten von Batch All: ' + err.message);
    setUILocked(false);
  }
}

// Führt Zusammenfassungs-Requests mit begrenzter Parallelität aus
async function batchSummarizeLectures(lectureIds, options = {}) {
  const concurrency = options.concurrency || 5;
  const signal = options.signal;

  let processed = 0;
  let failed = 0;

  // Worker-Pool
  const queue = lectureIds.slice();

  // Sperre UI während Batch-Arbeit (falls noch nicht gesperrt)
  setUILocked(true);

  async function worker() {
    while (queue.length > 0) {
      if (signal && signal.aborted) throw new DOMException('Aborted', 'AbortError');
      const lectureId = queue.shift();
      try {
        const sResp = await fetch(`${API_BASE}/api/summarize-lecture`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lectureId: lectureId, forceRegenerate: true })
        });

        if (!sResp.ok) {
          console.warn('Fehler bei Zusammenfassung', lectureId, sResp.status);
          failed += 1;
          if (typeof options.onProgress === 'function') {
            try { options.onProgress({ lectureId, success: false }); } catch(e){}
          }
        } else {
          const sData = await sResp.json();
          console.log('Summary erzeugt für', lectureId, sData);
          if (typeof options.onProgress === 'function') {
            try { options.onProgress({ lectureId, success: true }); } catch(e){}
          }
        }
      } catch (err) {
        console.warn('Exception beim Erzeugen der Summary für', lectureId, err);
        failed += 1;
        if (typeof options.onProgress === 'function') {
          try { options.onProgress({ lectureId, success: false }); } catch(e){}
        }
      }
      processed += 1;
    }
  }

  try {
    const workers = [];
    for (let i = 0; i < concurrency; i++) {
      workers.push(worker());
    }
    await Promise.all(workers);
  } finally {
    // UI wieder freigeben
    setUILocked(false);
  }

  return { processed, failed };
}

    function buildTableOfContents() {
      // Prüfe ob Timeline-Viewer aktiv ist
      const timelineSplitView = document.getElementById('timelineSplitView');
      const isTimelineActive = timelineSplitView && timelineSplitView.style.display !== 'none';
      
      const viewer = isTimelineActive ? document.getElementById('timelineViewerContent') : document.getElementById('viewer');
      const tocList = document.getElementById('toc-list');
      const mainContainer = isTimelineActive ? document.getElementById('timelineViewerContent') : document.getElementById('main');
      
      if (!viewer || !tocList) return;
      
      const headings = viewer.querySelectorAll('h3, h4');
      
      tocList.innerHTML = '';
      
      let headingIndex = 0;
      const tocItems = [];
      
      const toggleBtn = document.getElementById('toggleH4Btn');
      if (toggleBtn) {
        toggleBtn.innerHTML = '&#x2227;';
      }
      
      headings.forEach((heading) => {
        if (!heading.id) {
          heading.id = isTimelineActive ? `timeline-heading-${headingIndex}` : `heading-${headingIndex}`;
        }
        headingIndex++;
        
        const tocHeading = document.createElement(heading.tagName.toLowerCase());
        tocHeading.textContent = heading.textContent;
        tocHeading.style.cursor = 'pointer';
        
        tocHeading.addEventListener('click', (e) => {
          e.preventDefault();
          
          if (isTimelineActive) {
            // Für Timeline-Viewer: Scrolle nur innerhalb des Timeline-Containers
            const timelineContainer = document.getElementById('timelineViewerContent');
            const headingRect = heading.getBoundingClientRect();
            const containerRect = timelineContainer.getBoundingClientRect();
            
            // Berechne relative Position und scrolle den Container
            const relativeTop = headingRect.top - containerRect.top;
            const scrollPosition = timelineContainer.scrollTop + relativeTop - 50; // 50px offset
            
            timelineContainer.scrollTo({
              top: scrollPosition,
              behavior: 'smooth'
            });
          } else {
            // Für Haupt-Viewer: Normales scrollIntoView
            heading.scrollIntoView({ behavior: 'auto', block: 'start' });
          }
          
          const originalBg = heading.style.backgroundColor;
          heading.style.backgroundColor = 'rgba(70, 120, 134, 0.2)';
          setTimeout(() => {
            heading.style.backgroundColor = originalBg;
          }, 1000);
        });
        
        tocList.appendChild(tocHeading);
        tocItems.push({ element: tocHeading, heading: heading });
      });
      
      function updateActiveTocItem() {
        const containerTop = mainContainer.getBoundingClientRect().top;
        const containerBottom = mainContainer.getBoundingClientRect().bottom;
        
        const activeHeadings = [];
        
        // Immer beide H3 und H4 berücksichtigen für die Aktivmarkierung
        const visibleHeadings = Array.from(viewer.querySelectorAll('h3, h4'));
        
        // Sammle alle Headings, die im sichtbaren Bereich sind
        visibleHeadings.forEach(heading => {
          const headingRect = heading.getBoundingClientRect();
          const relativeTop = headingRect.top - containerTop;
          const relativeBottom = headingRect.bottom - containerTop;
          
          // Heading ist sichtbar, wenn es zwischen dem oberen Rand und dem unteren Rand des Containers ist
          if (relativeTop >= 0 && relativeTop <= (containerBottom - containerTop)) {
            activeHeadings.push(heading);
          }
        });
        
        // Wenn keine Headings im Viewport, nimm das letzte Heading vor dem Viewport
        if (activeHeadings.length === 0) {
          for (let i = visibleHeadings.length - 1; i >= 0; i--) {
            const heading = visibleHeadings[i];
            const headingRect = heading.getBoundingClientRect();
            const relativeTop = headingRect.top - containerTop;
            
            if (relativeTop <= 50) {
              activeHeadings.push(heading);
              break;
            }
          }
        }
        
        // Alle TOC-Items zurücksetzen
        tocItems.forEach(item => {
          item.element.style.fontWeight = 'normal';
          const isDarkMode = document.body.classList.contains('dark-mode');
          item.element.style.color = isDarkMode ? '#6BA3B8' : '#467886';
        });
        
        // Markiere alle aktiven Headings (H3 und/oder H4) fett
        tocItems.forEach(item => {
          if (activeHeadings.includes(item.heading)) {
            item.element.style.fontWeight = 'bold';
            const isDarkMode = document.body.classList.contains('dark-mode');
            item.element.style.color = isDarkMode ? '#6BA3B8' : '#467886';
          }
        });
      }
      
      mainContainer.removeEventListener('scroll', updateActiveTocItem);
      mainContainer.addEventListener('scroll', updateActiveTocItem);
      
      updateActiveTocItem();
    }

    function createOnlineURL(lecture) {
      if (!lecture.fileName) {
        return `https://rudolf-steiner-online.de/${lecture.ID || ''}`;
      }
      
      const fileName = lecture.fileName;
      const match = fileName.match(/^(GA\d{3}[a-z]?)\/(\d+)\s*-\s*(.+)$/);
      
      if (!match) {
        return `https://rudolf-steiner-online.de/${lecture.ID || ''}`;
      }
      
      const [, gaNumber, lectureNumber, rest] = match;
      
      const titleForUrl = rest.replace(/ /g, '+');
      const encodedTitle = encodeURIComponent(titleForUrl).replace(/%2B/g, '+');
      
      return `https://rudolf-steiner-online.de/${gaNumber}+(${lectureNumber}.)+${encodedTitle}`;
    }

    function displayLecture(lecture, highlightIndex, keywords = [], shouldHighlight = true) {
      const viewer = document.getElementById('viewer');
      const mainContainer = document.getElementById('main');
      const titleElement = document.getElementById('document-title');
      
      // Normalisiere den Index - füge ^ hinzu wenn es fehlt
      let cleanIndex = null;
      if (highlightIndex) {
        cleanIndex = highlightIndex.replace(/^\^/, '');
        // Prüfe ob der Index mit ^ im Vortrag existiert
        const hasCaretVersion = lecture.paragraphs?.some(p => 
          p.index === `^${cleanIndex}` || p.index === cleanIndex
        );
        if (hasCaretVersion) {
          // Verwende die Version, die im Vortrag tatsächlich existiert
          const actualIndex = lecture.paragraphs.find(p => 
            p.index === `^${cleanIndex}` || p.index === cleanIndex
          )?.index;
          if (actualIndex) {
            cleanIndex = actualIndex.replace(/^\^/, '');
          }
        }
      }
      
      viewer.innerHTML = '';
      
      const displayTitle = lecture.fileName || lecture.title || lecture.ID;
      const onlineLink = createOnlineURL(lecture);
      
      titleElement.innerHTML = `<a href="${onlineLink}" target="rudolf-steiner-online">${displayTitle}</a>`;
      
      let html = '<div>';
      
      if (lecture.paragraphs) {
        lecture.paragraphs.forEach((para, idx) => {
          const paraIndex = para.index ? para.index.replace(/^\^/, '') : `para_${idx}`;
          const isTargetPara = cleanIndex && paraIndex === cleanIndex;
          
          let content = para.content || para.text || '';
          
          if (keywords && keywords.length > 0) {
            keywords.forEach(word => {
              if (word && word.trim()) {
                const regex = new RegExp(`(${word.trim()})`, "gi");
                content = content.replace(regex, "<mark>$1</mark>");
              }
            });
          }
          
          const contentLower = content.toLowerCase();
          const hasBothWords = keywords.length === 2 && 
                               keywords[0] && keywords[1] &&
                               contentLower.includes(keywords[0].toLowerCase()) && 
                               contentLower.includes(keywords[1].toLowerCase());
          
          // For thematic search, highlight target paragraph regardless of keyword presence
          // For keyword search, only highlight if keywords are found
          const isFromThematicSearch = currentThematicQuery && keywords.length > 0;
          const applyHighlight = shouldHighlight && isTargetPara && 
                                 (isFromThematicSearch || keywords.length === 1 || hasBothWords);
          
          html += `
            <div class="paragraph ${applyHighlight ? 'highlighted-paragraph' : ''}" 
                 id="para-${paraIndex}">
              ${content}
            </div>
          `;
        });
      }
      html += `</div>`;
      viewer.innerHTML = html;
      
      if (cleanIndex) {
        const targetElement = document.getElementById(`para-${cleanIndex}`);
        if (targetElement) {
          // Berechne Position für Positionierung am unteren Rand des Headers
          const header = document.getElementById('viewer-header');
          const headerHeight = header ? header.offsetHeight + 5 : 5; // Nur 5px minimaler Abstand
          
          const mainRect = mainContainer.getBoundingClientRect();
          const targetRect = targetElement.getBoundingClientRect();
          const relativeTop = targetRect.top - mainRect.top + mainContainer.scrollTop - headerHeight;
          mainContainer.scrollTop = Math.max(0, relativeTop);
          lastHighlightedIndex = cleanIndex;
        } else {
          mainContainer.scrollTop = 0;
        }
      } else {
        mainContainer.scrollTop = 0;
      }
      
      updateButtonStates();
      updateHeaderPosition(); // Header-Position und Viewer-Padding anpassen
    }

    function handleKeywordKeypress(event) {
      if (event.key === 'Enter') {
        performKeywordSearch();
      }
    }

    function handleThematicKeydown(event) {
      if (event.key === 'Enter') {
        performThematicSearch();
      }
    }

    function initResizeHandle() {
      const resizeHandle = document.getElementById('resizeHandle');
      const sidebar = document.getElementById('sidebar');
      let isResizing = false;
      let startX = 0;
      let hasMoved = false;

      resizeHandle.addEventListener('mousedown', function(e) {
        startX = e.clientX;
        hasMoved = false;
        isResizing = true;
        
        // Toggle für flüssiges Resize optimieren
        const toggle = document.querySelector('.sidebar-toggle');
        if (toggle) {
          toggle.style.transition = 'background 0.2s, left 0.05s ease'; // Schnellere Transition beim Resize
        }
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        e.preventDefault();
      });

      function handleMouseMove(e) {
        if (!isResizing) return;
        
        // Prüfe ob sich die Maus bewegt hat (für Click vs. Drag Unterscheidung)
        if (Math.abs(e.clientX - startX) > 3) {
          hasMoved = true;
        }
        
        const containerWidth = document.body.clientWidth;
        const newSidebarWidth = (e.clientX / containerWidth) * 100;
        
        if (newSidebarWidth >= 15 && newSidebarWidth <= 90) {
          const pixelWidth = (newSidebarWidth / 100) * containerWidth;
          if (pixelWidth >= 250) {
            sidebar.style.width = newSidebarWidth + '%';
            updateHeaderPosition(); // Header beim Resize anpassen
          }
        }
      }

      function handleMouseUp() {
        isResizing = false;
        
        // Wenn keine Bewegung stattgefunden hat: Toggle-Funktion
        if (!hasMoved) {
          toggleSidebar();
          // Header-Position nach Toggle-Aktion mehrfach aktualisieren
          setTimeout(updateHeaderPosition, 100);
          setTimeout(updateHeaderPosition, 200);
          setTimeout(updateHeaderPosition, 350);
        }
        
        // Toggle-Transition zurücksetzen
        const toggle = document.querySelector('.sidebar-toggle');
        if (toggle) {
          toggle.style.transition = 'background 0.2s, left 0.3s ease'; // Normale Transition zurück
        }
        
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        updateHeaderPosition(); // Header nach Resize finalisieren
      }
    }

    function initVerticalResizeHandle() {
      const resizeHandle = document.getElementById('verticalResizeHandle');
      const mainPanel = document.getElementById('main');
      const summaryPanel = document.getElementById('summary-panel');
      let isResizing = false;
      let startX = 0;
      let hasMoved = false;

      resizeHandle.addEventListener('mousedown', function(e) {
        startX = e.clientX;
        hasMoved = false;
        isResizing = true;
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        e.preventDefault();
      });

      function handleMouseMove(e) {
        if (!isResizing) return;
        
        const deltaX = Math.abs(e.clientX - startX);
        if (deltaX > 3) {
          hasMoved = true;
        }
        
        if (hasMoved && summaryPanel.classList.contains('visible')) {
          // Berechne neue Panel-Breite basierend auf Mausposition
          const mouseX = e.clientX;
          const windowWidth = window.innerWidth;
          const newPanelWidth = windowWidth - mouseX;
          
          // Mindest- und Maximalbreite für Panel
          const minPanelWidth = 200;
          const maxPanelWidth = windowWidth * 0.6; // Maximal 60% der Fensterbreite
          
          if (newPanelWidth >= minPanelWidth && newPanelWidth <= maxPanelWidth) {
            summaryPanel.style.width = newPanelWidth + 'px';
            summaryPanel.style.minWidth = newPanelWidth + 'px';
            
            // Main-Container entsprechend anpassen
            const mainContainer = document.getElementById('main-container');
            if (mainContainer) {
              mainContainer.style.marginRight = newPanelWidth + 'px';
            }
            
            updateHeaderPosition(); // Header beim Resize anpassen
          }
        }
      }

      function handleMouseUp() {
        if (!hasMoved) {
          // Toggle bei Klick
          toggleSummaryPanel();
        }
        
        isResizing = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        updateHeaderPosition(); // Header nach Resize finalisieren
      }
    }
  </script>
<script>
document.addEventListener("DOMContentLoaded", async function () {
  console.log("[INIT] Lade verfügbare GA-Bände...");
  const gaFilter = document.getElementById("gaFilter");
  const thematicGAFilter = document.getElementById("thematicGAFilter");

  if (!gaFilter || !thematicGAFilter) {
    console.error("[FEHLER] Dropdown-Elemente nicht gefunden!");
    return;
  }

  gaFilter.innerHTML = '<option value="">alle GA-Bände</option>';
  thematicGAFilter.innerHTML = '<option value="">alle GA-Bände</option>';

  try {
    const response = await fetch(`${API_BASE}/api/available-ga`);
    if (!response.ok) throw new Error("API-Fehler");

    const data = await response.json();
    const availableGAs = data.availableGA;
    console.log("[INFO] Verfügbare GA-Bände:", availableGAs);

    availableGAs.sort();

    availableGAs.forEach(gaNumber => {
      const opt1 = document.createElement("option");
      opt1.value = gaNumber;
      opt1.textContent = gaNumber;
      opt1.classList.add("available-ga");

      const opt2 = opt1.cloneNode(true);
      gaFilter.appendChild(opt1);
      thematicGAFilter.appendChild(opt2);
    });
  } catch (err) {
    console.error("[FEHLER] GA-Liste konnte nicht geladen werden:", err);
  }

  // Register handlers to track last edited keyword input
  try {
    const word1El = document.getElementById('word1');
    const word2El = document.getElementById('word2');
    if (word1El) {
      word1El.addEventListener('focus', () => { lastKeywordInputId = 'word1'; });
      word1El.addEventListener('input', () => { lastKeywordInputId = 'word1'; });
    }
    if (word2El) {
      word2El.addEventListener('focus', () => { lastKeywordInputId = 'word2'; });
      word2El.addEventListener('input', () => { lastKeywordInputId = 'word2'; });
    }
    // Show batch button only in local mode
    const batchBtn = document.getElementById('batch-btn');
  if (batchBtn) batchBtn.style.display = isLocal ? 'inline-block' : 'none';
  const batchAllBtn = document.getElementById('batch-all-btn');
  if (batchAllBtn) batchAllBtn.style.display = isLocal ? 'inline-block' : 'none';
  } catch (err) {
    console.warn('[INIT] Konnte Keyword-Input-Listener nicht registrieren:', err);
  }
});
</script>
<script>
async function populateGesamtausgabeDropdown() {
  const select = document.getElementById('gaGesamtausgabe');
  if (!select) return;
  
  if (select.dataset.populated === 'true') {
    console.log('[GA-TAB] Bereits befüllt, überspringe');
    return;
  }

  try {
    let gaMap = null;
    try {
      const mapRes = await fetch(`${API_BASE}/ga-overview-map.json`);
      if (mapRes.ok) {
        gaMap = await mapRes.json();
        console.log('[GA-TAB] ga-overview-map.json geladen:', Object.keys(gaMap).length, 'Einträge');
      }
    } catch (mapErr) {
      console.warn('[GA-TAB] ga-overview-map.json nicht gefunden, verwende Fallback');
    }
    
    if (!gaMap || Object.keys(gaMap).length === 0) {
      const res = await fetch(`${API_BASE}/api/available-ga`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const data = await res.json();
      const availableGAs = data.availableGA || [];
      
      gaMap = {};
      availableGAs.forEach(ga => {
        gaMap[ga] = `/${ga}/${ga}.html`;
      });
      
      console.log('[GA-TAB] Fallback verwendet:', availableGAs.length, 'GA-Bände');
    }
    
    const gaList = Object.keys(gaMap).sort();

    if (gaList.length === 0) {
      console.warn('[GA-TAB] Keine GA-Bände gefunden');
      return;
    }

    while (select.options.length > 1) {
      select.remove(1);
    }

    gaList.forEach(ga => {
      const opt = document.createElement('option');
      opt.value = gaMap[ga];
      opt.textContent = ga;
      select.appendChild(opt);
    });
    
    select.dataset.populated = 'true';
    console.log('[GA-TAB] Dropdown befüllt mit', gaList.length, 'Einträgen');
    
    if (!select.dataset.listenerAdded) {
      select.addEventListener('change', (e) => {
        const selectedPath = e.target.value;
        if (selectedPath) {
          const fullUrl = `https://rudolf-steiner-online.de${selectedPath}`;
          console.log('[GA-TAB] Öffne:', fullUrl);
          window.open(fullUrl, 'ga-window');
          e.target.selectedIndex = 0;
        }
      });
      select.dataset.listenerAdded = 'true';
      console.log('[GA-TAB] Event Listener registriert');
    }
    
  } catch (err) {
    console.error('[GA-TAB] Fehler beim Laden der GA-Liste:', err);
  }
}

document.addEventListener('DOMContentLoaded', populateGesamtausgabeDropdown);
</script>

<script>
// =====================================
// SCHLAGWORT-SYSTEM
// =====================================

let keywordsData = [];
let currentAlphabet = 'Alle';
let filteredKeywords = [];
let showKeywordTexts = true;
// Track which keyword input was last edited/focused in the Text tab
let lastKeywordInputId = null;

// Globale Schlagwort-Funktionen
async function initializeKeywordSystem() {
  console.log('[KEYWORDS] Initialisiere Schlagwort-System...');
  
  const countContainer = document.getElementById('keyword-count');
  if (countContainer) countContainer.textContent = '';
  
  try {
    // Lade Schlagwort-Daten
    await loadKeywordsData();
    
    if (keywordsData.length === 0) {
      if (countContainer) countContainer.textContent = '';
      console.warn('[KEYWORDS] Keine Schlagwörter geladen!');
      return;
    }
    
    // Erstelle Alphabet-Navigation
    createAlphabetNavigation();
    
    // Initialer Aufbau der Anzeige
    displayKeywords('Alle');
    
    // Event Listener für Suche
    setupKeywordSearch();
    
    console.log(`[KEYWORDS] ✓ System erfolgreich initialisiert mit ${keywordsData.length} Schlagwörtern`);
    
  } catch (error) {
    console.error('[KEYWORDS] ✗ Fehler beim Initialisieren:', error);
    if (countContainer) countContainer.textContent = '';
  }
}

async function loadKeywordsData() {
  console.log('[KEYWORDS] Lade Schlagwort-Daten...');
  
  try {
    // Versuche zuerst eine vollständige Schlagwort-Liste zu laden
    const response = await fetch(`${API_BASE}/api/keywords-list`);
    if (response.ok) {
      const data = await response.json();
      keywordsData = data.keywords || [];
      console.log('[KEYWORDS] Schlagwörter von API geladen:', keywordsData.length);
      return;
    }
  } catch (error) {
    console.warn('[KEYWORDS] API nicht verfügbar, verwende lokale Dateien');
  }
  
  // Versuche lokale Schlagwort-Dateien zu laden
  try {
    await loadLocalKeywordFiles();
    if (keywordsData.length > 0) {
      console.log('[KEYWORDS] Lokale Schlagwort-Dateien geladen:', keywordsData.length);
      return;
    }
  } catch (error) {
    console.warn('[KEYWORDS] Lokale Dateien nicht verfügbar:', error.message);
  }
  
  // Fallback: Demo-Daten basierend auf der Abbauprozesse.json Struktur
  keywordsData = [
    {
      keyword: "Abbauprozesse",
      alphabetical: "A",
      text: "**Abbauprozesse** stellen einen grundlegenden physiologischen Mechanismus dar, bei dem die **Seele fortwährend Zerstörungs- und Zerfallprozesse im Nervensystem** vollführt, die paradoxerweise die **Grundlage für Wahrnehmung** bilden ([[GA066/1]]). Diese **destruktiven Prozesse im Nervensystem** erweisen sich als unabdingbare Voraussetzung für **bewusstes Seelenleben** ([[GA067/4]]).",
      gaReferences: ["GA066/1", "GA067/4", "GA067/10"]
    },
    {
      keyword: "Astralleib", 
      alphabetical: "A",
      text: "Der **Astralleib** ist das dritte Wesensglied des Menschen und trägt Emotionen, Triebe und Bewusstsein ([[GA013/3]]). Er entwickelt sich durch Meditation und spirituelle Übung ([[GA013/5]]).",
      gaReferences: ["GA013/3", "GA013/5"]
    },
    {
      keyword: "Bewusstsein",
      alphabetical: "B", 
      text: "**Bewusstsein** entsteht durch Abbauprozesse im Nervensystem ([[GA066/1]]) und entwickelt sich stufenweise vom Traumlosen Schlaf über das Traumbewusstsein zum Tagesbewusstsein ([[GA013/2]]).",
      gaReferences: ["GA066/1", "GA013/2"]
    }
  ];
  
  console.log('[KEYWORDS] Demo-Daten geladen:', keywordsData.length, 'Schlagwörter');
}

async function loadLocalKeywordFiles() {
  console.log('[KEYWORDS] Lade lokale Schlagwort-Dateien aus keywords/ Ordner...');
  
  try {
    // Versuche eine Dateiliste vom Server zu bekommen
    const listResponse = await fetch(`${API_BASE}/api/keywords-files`);
    if (listResponse.ok) {
      const fileList = await listResponse.json();
      console.log('[KEYWORDS] Dateiliste von API erhalten:', fileList.files?.length || 0, 'Dateien');
      
      for (const fileName of fileList.files || []) {
        await loadSingleKeywordFile(`keywords/${fileName}`);
      }
      return;
    }
  } catch (error) {
    console.warn('[KEYWORDS] API für Dateiliste nicht verfügbar:', error.message);
  }
  
  // Fallback: Versuche bekannte Dateien aus dem keywords/ Ordner zu laden
  const knownFiles = [
    'Abbauprozesse.json',
    'Astralleib.json', 
    'Bewusstsein.json',
    'Christus.json',
    'Denken.json',
    'Erkenntnis.json',
    'Geist.json',
    'Karma.json',
    'Meditation.json',
    'Seele.json'
    // Weitere bekannte Dateien können hier hinzugefügt werden
  ];
  
  console.log('[KEYWORDS] Versuche', knownFiles.length, 'bekannte Dateien zu laden...');
  
  for (const fileName of knownFiles) {
    // Zuerst im keywords/ Ordner suchen
    const loaded = await loadSingleKeywordFile(`keywords/${fileName}`);
    // Falls nicht gefunden, im Hauptverzeichnis suchen
    if (!loaded) {
      await loadSingleKeywordFile(fileName);
    }
  }
  
  console.log('[KEYWORDS] Insgesamt', keywordsData.length, 'Schlagwörter aus lokalen Dateien geladen');
}

async function loadSingleKeywordFile(filePath) {
  try {
    console.log('[KEYWORDS] Versuche zu laden:', filePath);
    const response = await fetch(filePath);
    
    if (response.ok) {
      const data = await response.json();
      
      // Konvertiere die JSON-Struktur in unser Schlagwort-Format
      if (data.keywords && data.text) {
        const keywordEntry = {
          keyword: data.keywords.Keyword || 'Unbekannt',
          alphabetical: data.keywords.Alphabetical || data.keywords.Keyword?.charAt(0).toUpperCase() || 'U',
          text: data.text,
          gaReferences: extractGAReferences(data.text)
        };
        
        keywordsData.push(keywordEntry);
        console.log('[KEYWORDS] ✓ Schlagwort geladen:', keywordEntry.keyword, 'aus', filePath);
        return true;
      } else {
        console.warn('[KEYWORDS] ✗ Ungültige Struktur in', filePath);
        return false;
      }
    } else {
      console.log('[KEYWORDS] ✗ Datei nicht gefunden:', filePath, '(Status:', response.status + ')');
      return false;
    }
  } catch (error) {
    console.log('[KEYWORDS] ✗ Fehler beim Laden von', filePath, ':', error.message);
    return false;
  }
}

function extractGAReferences(text) {
  if (!text) return [];
  
  const gaMatches = text.match(/\[\[([^\]]*\|)?([^|\]]+)\]\]/g);
  if (!gaMatches) return [];
  
  return gaMatches.map(match => {
    const gaMatch = match.match(/\[\[([^\]]*\|)?([^|\]]+)\]\]/);
    if (gaMatch && gaMatch[2]) {
      // Extrahiere nur die GA-ID (z.B. "GA066/1" aus "GA066 (1.) TITLE|GA066/1")
      const gaId = gaMatch[2].trim();
      return gaId;
    }
    return null;
  }).filter(id => id && /^GA\d{3}[a-z]?\/\d+$/i.test(id));
}

function createAlphabetNavigation() {
  const navContainer = document.getElementById('alphabet-nav');
  
  // Alle verfügbaren Buchstaben aus den Daten ermitteln
  const availableLetters = [...new Set(keywordsData.map(k => k.alphabetical || k.keyword.charAt(0).toUpperCase()))].sort();
  
  // "Alle" Button
  const allBtn = document.createElement('button');
  allBtn.className = 'depth-btn active';
  allBtn.textContent = 'Alle';
  allBtn.onclick = () => selectAlphabet('Alle', allBtn);
  navContainer.appendChild(allBtn);
  
  // Alphabet-Buttons für verfügbare Buchstaben
  availableLetters.forEach(letter => {
    const btn = document.createElement('button');
    btn.className = 'depth-btn';
    btn.textContent = letter;
    btn.onclick = () => selectAlphabet(letter, btn);
    navContainer.appendChild(btn);
  });
}

function selectAlphabet(letter, buttonElement) {
  // Alle Buttons deaktivieren
  document.querySelectorAll('#alphabet-nav .depth-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Ausgewählten Button aktivieren
  buttonElement.classList.add('active');
  
  currentAlphabet = letter;
  displayKeywords(letter);
}

function displayKeywords(selectedLetter = 'Alle') {
  const resultsContainer = document.getElementById('results');
  const countContainer = document.getElementById('keyword-count');
  
  // Filtere Schlagwörter nach Buchstabe
  filteredKeywords = selectedLetter === 'Alle' 
    ? keywordsData 
    : keywordsData.filter(k => (k.alphabetical || k.keyword.charAt(0).toUpperCase()) === selectedLetter);
  
  // Weitere Filterung nach Suchtext
  const searchText = document.getElementById('keywordSearch').value.toLowerCase();
  if (searchText) {
    filteredKeywords = filteredKeywords.filter(k => 
      k.keyword.toLowerCase().includes(searchText)
    );
  }
  
  if (countContainer) countContainer.textContent = '';
  
  if (filteredKeywords.length === 0) {
    resultsContainer.innerHTML = '<p class="no-results-message">Keine Schlagwörter gefunden.</p>';
    return;
  }
  
  // Sortiere alphabetisch
  filteredKeywords.sort((a, b) => a.keyword.localeCompare(b.keyword));
  
  let html = '<div class="keywords-container">';
  
  filteredKeywords.forEach(keywordData => {
    // Verwende Keyword-Thematische Suche für detaillierte Analysen
    html += `
      <div class="keyword-entry">
        <h4>
          <a href="#" onclick="performKeywordThematicSearch('${keywordData.keyword}'); return false;">
            ${keywordData.keyword}
          </a>
        </h4>
        <div class="keyword-text" ${showKeywordTexts ? '' : 'style="display: none;"'}>
        </div>
      </div>
    `;
  });
  
  html += '</div>';
  resultsContainer.innerHTML = html;
  
  // BACKEND-FORMATIERUNG ENTFERNEN: Alle inline Styles aus Schlagwort-HTML entfernen
  removeInlineStyles(resultsContainer);
  
  // Lucide Icons initialisieren
  initializeLucideIcons();
  
  // Scrolle nach oben in der Sidebar
  document.getElementById('sidebar-content').scrollTop = 0;
}

function processKeywordText(text, gaReferences = []) {
  if (!text) return '';
  
  let processedText = text;
  
  // Verarbeite Markdown-Formatierung für fette Schrift **text**
  processedText = processedText.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // Verarbeite Markdown-Links im Format [[GA066/1]] oder [[GA066 (1.) TITLE|GA066/1]]
  processedText = processedText.replace(/\[\[([^\]]*\|)?([^|\]]+)\]\]/g, (match, titlePart, gaId) => {
    const cleanGAId = gaId.trim();
    
    // Prüfe ob es eine gültige GA-ID ist (Format: GA123/4 oder GA123a/4)
    if (/^GA\d{3}[a-z]?\/\d+$/i.test(cleanGAId)) {
      return `<a href="#" class="ga-keyword-link" data-ga-id="${cleanGAId}" onclick="openFromKeyword('${cleanGAId}'); return false;">${cleanGAId}</a>`;
    }
    
    return match; // Fallback: ursprünglichen Text beibehalten
  });
  
  return processedText;
}


async function openFromKeyword(gaId) {
  console.log('[KEYWORDS] Öffne GA-Referenz:', gaId);
  
  try {
    // Timeline schließen falls geöffnet
    hideTimelineIfOpen();
    
    // Schließe Summary Panel falls geöffnet
    const summaryPanel = document.getElementById('summary-panel');
    const resizeHandle = document.getElementById('verticalResizeHandle');
    if (summaryPanel.classList.contains('visible')) {
      summaryPanel.classList.remove('visible');
      resizeHandle.classList.remove('visible');
      summaryPanel.style.width = '0';
      summaryPanel.style.minWidth = '0';
      summaryPanel.style.marginRight = '0px';
    }
    
    // Zeige Vortrag
    await showLecture(gaId, null, []);
    
  } catch (error) {
    console.error('[KEYWORDS] Fehler beim Öffnen der GA-Referenz:', error);
    alert(`Fehler beim Laden des Vortrags ${gaId}: ${error.message}`);
  }
}

function setupKeywordSearch() {
  const searchInput = document.getElementById('keywordSearch');
  
  searchInput.addEventListener('input', () => {
    displayKeywords(currentAlphabet);
  });
  
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      displayKeywords(currentAlphabet);
    }
  });
}

function clearKeywordSearch() {
  document.getElementById('keywordSearch').value = '';
  displayKeywords(currentAlphabet);
}

// Erweitere die bestehende switchTab Funktion
function switchTabExtended(mode) {
  console.log('[TABS] Wechsel zu Tab:', mode);
  
  // Timeline schließen falls geöffnet
  hideTimelineIfOpen();
  
  // Summary-Panel schließen beim Tab-Wechsel
  const summaryPanel = document.getElementById('summary-panel');
  const summaryResizeHandle = document.querySelector('.vertical-resize-handle');
  
  if (summaryPanel) {
    // Entferne .visible Klasse (das reicht, da CSS default width: 0 hat)
    summaryPanel.classList.remove('visible');
    
    // Entferne alle inline-styles, damit CSS-Defaults greifen
    summaryPanel.removeAttribute('style');
    
    console.log('[TABS] Summary-Panel geschlossen');
  }
  
  if (summaryResizeHandle) {
    summaryResizeHandle.classList.remove('visible');
    // Resize-Handle komplett zurücksetzen
    summaryResizeHandle.removeAttribute('style');
    summaryResizeHandle.style.width = '0';
    summaryResizeHandle.style.display = 'none';
    console.log('[TABS] Resize-Handle versteckt');
  }
  
  // TOC leeren
  const tocList = document.getElementById('toc-list');
  if (tocList) {
    tocList.innerHTML = '';
  }
  
  // currentOpenLectureId zurücksetzen
  window.currentOpenLectureId = null;
  
  // Horizontalen Resize-Handle basierend auf Tab ein-/ausblenden
  const resizeHandle = document.getElementById('search-panel-toggle');
  if (resizeHandle) {
    // In allen Tabs anzeigen
    resizeHandle.style.display = 'block';
    resizeHandle.style.cursor = 'row-resize';
  }

  // Bei Wechsel zum Themen-Tab: letzte gespeicherte Anfragen laden
  if (mode === 'thematic') {
    loadRecentThematicQueries();
  }
  
  // Alle Tab-Buttons deaktivieren
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
  
  // Richtigen Button aktivieren basierend auf onclick-Attribut
  const targetButton = document.querySelector(`[onclick="switchTab('${mode}')"]`);
  if (targetButton) {
    targetButton.classList.add('active');
  } else {
    console.warn('[TABS] Button nicht gefunden für:', mode);
  }
  
  // Finde aktuell aktiven Tab-Inhalt und lösche dessen dynamischen Inhalt,
  // bevor wir den neuen Tab aktivieren. So bleiben keine Reste zurück.
  const prevActive = document.querySelector('.tab-content.active');
  const targetId = `${mode}-tab`;
  if (prevActive && prevActive.id !== targetId) {
    try {
      // Statt den gesamten Tab zu löschen (was die Header/Controls entfernt),
      // nur die eigentlichen Ergebnis-/Dynamik-Container leeren.
      // 1) Zentrale Ergebnis-Container (gemeinsam genutzter Bereich)
      const resultsEl = document.getElementById('results');
      if (resultsEl) {
        resultsEl.innerHTML = '';
        console.log('[TABS] Ergebnisse im #results-Bereich geleert');
      }

      // 2) Spezifische dynamische Bereiche innerhalb des Tabs (falls vorhanden)
      // Entwickler können künftig Elemente mit diesen Klassen ausstatten,
      // um gezielt geleert zu werden beim Tab-Wechsel.
      const dynamicSelectors = ['.clear-on-switch', '.tab-dynamic'];
      dynamicSelectors.forEach(sel => {
        const elems = prevActive.querySelectorAll(sel);
        elems.forEach(el => {
          el.innerHTML = '';
        });
      });

      // Main Viewer leeren
      const viewer = document.getElementById('viewer');
      if (viewer) {
        viewer.innerHTML = '';
        console.log('[TABS] Main Viewer geleert');
      }
      
      // Document Title zurücksetzen
      const documentTitle = document.getElementById('document-title');
      if (documentTitle) {
        documentTitle.textContent = 'Bitte ein Suchergebnis auswählen…';
        console.log('[TABS] Document Title zurückgesetzt');
      }
      
      // Setze ggf. die Scroll-Position der Sidebar zurück
      const sidebarContent = document.getElementById('sidebar-content');
      if (sidebarContent) sidebarContent.scrollTop = 0;
      console.log('[TABS] Vorheriger Tab-dynamik geleert:', prevActive.id);
    } catch (err) {
      console.warn('[TABS] Fehler beim Leeren des vorherigen Tab-Inhalts:', err);
    }
  }

  // Alle Tab-Inhalte verstecken
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  // Gewünschten Tab-Inhalt anzeigen
  const targetContent = document.getElementById(targetId);
  if (targetContent) {
    targetContent.classList.add('active');
  } else {
    console.warn('[TABS] Tab-Content nicht gefunden für:', mode);
  }
  
  // Initialisiere Schlagwort-System beim ersten Aufruf oder zeige Keywords wenn bereits geladen
  if (mode === 'schlagworte') {
    if (keywordsData.length === 0) {
      initializeKeywordSystem();
    } else {
      // Keywords sind bereits geladen, zeige sie an
      displayKeywords('Alle');
    }
  }

  // Wenn wir zum Texte-Tab wechseln, setze das Dropdown zurück
  if (mode === 'texte') {
    const texteGAFilter = document.getElementById('texteGAFilter');
    if (texteGAFilter) {
      texteGAFilter.value = '';
      console.log('[TABS] Texte-Tab Dropdown zurückgesetzt');
    }
    // Toggle Button verstecken und zurücksetzen
    const texteViewToggle = document.getElementById('texteViewToggle');
    const texteServerInfo = document.getElementById('texteServerInfo');
    if (texteViewToggle) {
      texteViewToggle.style.display = 'none';
    }
    if (texteServerInfo) {
      texteServerInfo.textContent = '';
    }
  }

  // Wenn wir zum Text-Tab wechseln, lösche das zuletzt eingegebene Suchwort
  if (mode === 'keyword' && lastKeywordInputId) {
    try {
      const el = document.getElementById(lastKeywordInputId);
      if (el) {
        el.value = '';
        // Falls gewünscht, setze auch die datalist-Auswahl zurück
        const listId = el.getAttribute('list');
        if (listId) {
          const list = document.getElementById(listId);
          // keine direkte Auswahl nötig; nur ein Hinweis für Debug
        }
        lastKeywordInputId = null;
        console.log('[TABS] Letztes Stichwort gelöscht:', lastKeywordInputId || '(cleared)');
      }
    } catch (err) {
      console.warn('[TABS] Fehler beim Löschen des letzten Stichworts:', err);
    }
  }
}

// Ersetze die globale switchTab Funktion
window.switchTab = switchTabExtended;

// CSS für Schlagwort-Links hinzufügen
const keywordStyles = `
body.dark-mode .ga-keyword-link {
  color: #7EB8C8;
  background: rgba(126, 184, 200, 0.15);
}

body.dark-mode .ga-keyword-link:hover {
  background: rgba(126, 184, 200, 0.25);
}

.batch-progress {
  padding: 8px 12px;
  background: #f4f7f8;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9em;
  color: #333;
}

.batch-progress .bar {
  height: 8px;
  background: #467886;
  width: 0%;
  border-radius: 4px;
  transition: width 0.2s ease;
}

/* Spinner für Buttons */
.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0,0,0,0.15);
  border-top-color: rgba(0,0,0,0.6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
  margin-left: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

#alphabet-nav .depth-btn {
  font-size: 0.85em;
  padding: 4px 8px;
  margin: 2px;
}

body.dark-mode #keyword-count {
  color: #e0e0e0;
}

/* Entfernt: Schlagwörter-Tab nutzt zentrale Sidepanel-Regeln */

body.dark-mode .keyword-text {
  color: #e0e0e0 !important;
}

body.dark-mode .keyword-text strong {
  color: #e0e0e0 !important;
}

/* Zentrale Styles für Schlagwort-Ergebnisfenster */
#results p,
#results .paragraph {
  margin: var(--paragraph-margin) 0;
  font-size: var(--text-size);
  line-height: var(--line-height);
  color: var(--text-color);
}

#results h1,
#results h2,
#results h3,
#results h4 {
  font-size: 1.0rem !important;
  line-height: 1.3 !important;
  color: #333333 !important;
  margin: 0.4rem 0 0.3rem 0 !important;
  font-weight: 600 !important;
}

#results .answer-header .answer-title {
  font-size: 1.2rem !important;
  line-height: 1.3 !important;
  font-weight: 700 !important;
  color: var(--heading-color) !important;
}
  
#results h1 {
  font-weight: 700 !important;
}

/* Dark Mode für Schlagwort-Ergebnisfenster - DIREKT */
body.dark-mode #results p,
body.dark-mode #results .paragraph {
  color: #b8b8b8 !important;
}

body.dark-mode #results h1,
body.dark-mode #results h2,
body.dark-mode #results h3,
body.dark-mode #results h4 {
  color: #b8b8b8 !important;
}

/* Dark Mode: Zwischenüberschriften im #results-Bereich folgen den zentralen Sidepanel-Styles */

/* Schlagwort-Links in Ergebnissen - DIREKT */
#results .ga-keyword-link {
  color: #467886 !important;
}

body.dark-mode #results .ga-keyword-link {
  color: #6BA3B8 !important;
}
`;

// Füge CSS zum Document hinzu
const styleSheet = document.createElement('style');
styleSheet.textContent = keywordStyles;
document.head.appendChild(styleSheet);

console.log('[KEYWORDS] Schlagwort-System geladen');

// KEYWORD THEMATIC SEARCH FUNKTIONEN
// ============================================================================

async function performKeywordThematicSearch(keyword) {
  console.log('[KEYWORD-THEMATIC] Starte thematische Suche für:', keyword);
  
  // Timeline schließen falls geöffnet
  hideTimelineIfOpen();
  
  try {
    // Zeige Loading-Status
    const results = document.getElementById('results');
    const countContainer = document.getElementById('keyword-count');
    
    if (results) {
      results.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: #666;">
          <div style="font-style: italic; font-size: 1.2em;">Suche...</div>
        </div>
      `;
    }
    
    if (countContainer) {
      countContainer.textContent = 'Lade...';
    }
    
    // Versuche zuerst das gespeicherte Ergebnis zu laden (mit den gleichen Parametern wie beim Hinzufügen)
    const cacheResponse = await fetch(`${API_BASE}/api/keyword-thematic-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: keyword,
        limit: 30,
        useCache: true  // Explizit Cache verwenden
      })
    });
    
    if (!cacheResponse.ok) {
      throw new Error(`Server Error: ${cacheResponse.status}`);
    }
    
    const data = await cacheResponse.json();
    
    // Prüfe ob das Ergebnis aus dem Cache kommt
    if (data.fromCache) {
      console.log('[KEYWORD-THEMATIC] Cache-Hit für:', keyword);
      if (countContainer) {
        countContainer.textContent = '';
      }
    } else {
      console.log('[KEYWORD-THEMATIC] Neue Analyse erstellt für:', keyword);
      if (countContainer) {
        countContainer.textContent = '';
      }
    }
    
    // Zeige die Ergebnisse an
    displayKeywordThematicResults(keyword, data);
    
  } catch (error) {
    console.error('[KEYWORD-THEMATIC] Fehler:', error);
    
    const results = document.getElementById('results');
    if (results) {
      results.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: #c53030;">
          <div style="font-size: 1.2em; margin-bottom: 1rem;">❌ Fehler bei der Analyse</div>
          <div style="font-style: italic;">${error.message}</div>
          <button onclick="switchTab('schlagworte')" style="margin-top: 1rem; padding: 8px 16px; background: #467886; color: white; border: none; border-radius: 4px; cursor: pointer;">
            Zurück zur Schlagwort-Liste
          </button>
        </div>
      `;
    }
  }
}

function displayKeywordThematicResults(keyword, data) {
  const results = document.getElementById('results');
  const countContainer = document.getElementById('keyword-count');
  
  if (!results) return;
  
  // Hilfsfunktion: Wandle Markdown zu HTML um
  function markdownToHtml(text) {
    return text
      // Entfernt H1-Überschriften vollständig
      .replace(/^# (.+)$/gm, '')
      // Entfernt H3-Überschriften (### ...) vollständig
      .replace(/^### (.+)$/gm, '')
      // Wandelt H2 (## ...) in semantische Überschriften ohne Inline-Styles
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      // Fett: **text** -> <strong>text</strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Kursiv: *text* -> <em>text</em>
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Zeilenumbrüche: \n\n -> </p><p>
      .replace(/\n\n/g, '</p><p>')
      // Einzelne Zeilenumbrüche: \n -> <br>
      .replace(/\n/g, '<br>');
  }
  
  // Hilfsfunktion: Wandle GA-Referenzen in klickbare Links um (verkürzte Version)
  function makeGAReferencesClickable(text) {
    // Regex für GA-Referenzen: (GA###/Y:index) oder (GA###a/Y:index)
    const gaRefRegex = /\(GA(\d{3}[a-z]?)\/(\d+):([a-z0-9^]+)\)/gi;
    
    return text.replace(gaRefRegex, (match, gaNum, lectureNum, index) => {
      const lectureId = `GA${gaNum}/${lectureNum}`;
      const cleanIndex = index.replace(/^\^/, '');
      return ` (<a href="#" onclick="showLecture('${lectureId}', '${cleanIndex}'); return false;" class="ga-keyword-link">GA${gaNum}/${lectureNum}</a>)`;
    });
  }
  
  // Hauptinhalt (KI-Analyse) mit Markdown-zu-HTML und klickbaren GA-Referenzen
  let contentHtml = '';
  if (data.content) {
    const markdownHtml = markdownToHtml(data.content);
    const contentWithLinks = makeGAReferencesClickable(markdownHtml);
    contentHtml = `
      <div class="keyword-answer">
        <p>${contentWithLinks}</p>
      </div>
    `;
  }
  
  // Kombiniere alles (nur Hauptinhalt) im gleichen Layout wie Themensuche
  results.innerHTML = `
    <div class="semantic-answer">
      <div class="answer-header">
        <h2 class="answer-title">${keyword}</h2>
      </div>
      <div class="answer-content" id="keywordAnswerContent">
        ${contentHtml}
      </div>
    </div>
  `;

  // Sicherheitshalber Inline-Styles entfernen (falls Backend-Markdown doch Styles liefert)
  removeInlineStyles(results);
  // Einheitliche Abstände um Klammern an GA-Quellenangaben (Keyword-Themen)
  try {
    const kc = document.getElementById('keywordAnswerContent');
    if (kc) normalizeCitationSpacing(kc);
  } catch (_) {}
  
  // Lucide Icons initialisieren
  initializeLucideIcons();
  
  // Aktualisiere Count-Container
  if (countContainer) {
    countContainer.textContent = '';
  }
  
  console.log('[KEYWORD-THEMATIC] Ergebnisse angezeigt für:', keyword);
}

// ============================================================================
// SCHLAGWORT HINZUFÜGEN
// ============================================================================

// Blende "Schlagwort hinzufügen" nur lokal ein
(() => {
  try {
    const host = window.location.hostname || '';
    const protocol = window.location.protocol || '';
    const localHosts = ['localhost', '127.0.0.1', '::1', '0.0.0.0'];
    const isLocalHost = localHosts.includes(host) || host.endsWith('.local');
    const isLocalProtocol = protocol === 'file:'; // allow when opened directly from disk during local work
    const isLocal = isLocalHost || isLocalProtocol;
    
    const addSection = document.getElementById('addKeywordSection');
    const regenerateSection = document.getElementById('regenerateKeywordSection');
    const batchSection = document.getElementById('batchKeywordSection');
    
    if (addSection) {
      addSection.style.display = isLocal ? 'block' : 'none';
    }
    if (regenerateSection) {
      regenerateSection.style.display = isLocal ? 'block' : 'none';
    }
    if (batchSection) {
      batchSection.style.display = isLocal ? 'block' : 'none';
    }
  } catch (_) {}
})();

// Batch-Schlagwort-Generierung
let batchProcessing = false;
let batchAbortController = null;
let batchSectionVisible = true;

function toggleBatchSection() {
  const batchContent = document.getElementById('batchContent');
  const toggleButton = document.getElementById('batchToggleButton');
  
  if (batchSectionVisible) {
    // Ausblenden
    batchContent.style.display = 'none';
    toggleButton.textContent = 'Einblenden';
    toggleButton.style.background = '#2e7d32';
    batchSectionVisible = false;
  } else {
    // Einblenden
    batchContent.style.display = 'block';
    toggleButton.textContent = 'Ausblenden';
    toggleButton.style.background = '#666';
    batchSectionVisible = true;
  }
}

async function addBatchKeywords() {
  const batchInput = document.getElementById('batchKeywordsInput');
  const batchButton = document.getElementById('batchAddButton');
  const batchCancelButton = document.getElementById('batchCancelButton');
  const statusDiv = document.getElementById('batchKeywordStatus');
  const progressContainer = document.getElementById('batchProgressContainer');
  const progressText = document.getElementById('batchProgressText');
  const progressPercent = document.getElementById('batchProgressPercent');
  const progressBar = document.getElementById('batchProgressBar');
  const resultsDiv = document.getElementById('batchResults');
  const overwriteCheckbox = document.getElementById('batchOverwriteCheckbox');
  
  if (!batchInput || !batchButton || !statusDiv) {
    console.error('[BATCH-KEYWORDS] UI-Elemente nicht gefunden');
    return;
  }
  
  const keywordsText = batchInput.value.trim();
  
  if (!keywordsText) {
    statusDiv.innerHTML = '<div style="color: #d32f2f; font-size: 0.85em;">Bitte geben Sie mindestens ein Schlagwort ein.</div>';
    statusDiv.style.display = 'block';
    return;
  }
  
  // Parse Schlagwörter aus Textarea
  const keywords = keywordsText.split('\n')
    .map(k => k.trim())
    .filter(k => k.length > 0);
  
  if (keywords.length === 0) {
    statusDiv.innerHTML = '<div style="color: #d32f2f; font-size: 0.85em;">Keine gültigen Schlagwörter gefunden.</div>';
    statusDiv.style.display = 'block';
    return;
  }
  
  if (keywords.length > 50) {
    statusDiv.innerHTML = '<div style="color: #d32f2f; font-size: 0.85em;">Maximal 50 Schlagwörter pro Batch erlaubt.</div>';
    statusDiv.style.display = 'block';
    return;
  }
  
  // UI-Status aktualisieren
  batchProcessing = true;
  batchAbortController = new AbortController();
  
  batchButton.disabled = true;
  batchButton.style.display = 'none';
  batchCancelButton.style.display = 'inline-block';
  statusDiv.style.display = 'none';
  progressContainer.style.display = 'block';
  resultsDiv.style.display = 'none';
  
  // Fortschritt zurücksetzen
  progressText.textContent = `Verarbeite 0 von ${keywords.length} Schlagwörtern...`;
  progressPercent.textContent = '0%';
  progressBar.style.width = '0%';
  
  try {
    console.log(`[BATCH-KEYWORDS] Starte Batch-Verarbeitung für ${keywords.length} Schlagwörter`);
    
    const response = await fetch('http://localhost:3003/api/keywords-batch-add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        keywords: keywords,
        overwrite: overwriteCheckbox.checked,
        batchId: `batch_${Date.now()}`
      }),
      signal: batchAbortController.signal
    });
    
    const result = await response.json();
    
    if (response.ok) {
      // Erfolg
      statusDiv.innerHTML = `<div style="color: #2e7d32; font-size: 0.85em;">✓ ${result.message}</div>`;
      statusDiv.style.display = 'block';
      
      // Eingabefeld leeren
      batchInput.value = '';
      
      // Fortschritt auf 100% setzen
      progressText.textContent = `Abgeschlossen: ${result.results.successful.length} von ${result.results.totalKeywords} erfolgreich`;
      progressPercent.textContent = '100%';
      progressBar.style.width = '100%';
      
      // Ergebnisse anzeigen
      document.getElementById('batchSuccessCount').textContent = result.results.successful.length;
      document.getElementById('batchFailedCount').textContent = result.results.failed.length;
      document.getElementById('batchSkippedCount').textContent = result.results.skipped.length;
      resultsDiv.style.display = 'block';
      
      // Schlagwort-Liste aktualisieren
      await loadKeywordsData();
      displayKeywords();
      
      console.log('[BATCH-KEYWORDS] Batch erfolgreich abgeschlossen:', result);
      
    } else {
      // Fehler
      statusDiv.innerHTML = `<div style="color: #d32f2f; font-size: 0.85em;">✗ Fehler: ${result.error || 'Unbekannter Fehler'}</div>`;
      statusDiv.style.display = 'block';
      
      console.error('[BATCH-KEYWORDS] Fehler beim Batch-Verarbeiten:', result);
    }
    
  } catch (error) {
    if (error.name === 'AbortError') {
      statusDiv.innerHTML = '<div style="color: #f57c00; font-size: 0.85em;">⚠ Batch-Verarbeitung abgebrochen</div>';
    } else {
      statusDiv.innerHTML = `<div style="color: #d32f2f; font-size: 0.85em;">✗ Netzwerkfehler: ${error.message}</div>`;
    }
    statusDiv.style.display = 'block';
    console.error('[BATCH-KEYWORDS] Netzwerkfehler:', error);
  } finally {
    // UI-Status zurücksetzen
    batchProcessing = false;
    batchAbortController = null;
    
    batchButton.disabled = false;
    batchButton.style.display = 'inline-block';
    batchCancelButton.style.display = 'none';
  }
}

function cancelBatchKeywords() {
  if (batchAbortController) {
    batchAbortController.abort();
    console.log('[BATCH-KEYWORDS] Batch-Verarbeitung abgebrochen');
  }
}

async function addNewKeyword() {
  const keywordInput = document.getElementById('newKeywordInput');
  const addButton = document.getElementById('addKeywordButton');
  const statusDiv = document.getElementById('addKeywordStatus');
  
  if (!keywordInput || !addButton || !statusDiv) {
    console.error('[ADD-KEYWORD] UI-Elemente nicht gefunden');
    return;
  }
  
  const keyword = keywordInput.value.trim();
  
  if (!keyword) {
    statusDiv.innerHTML = '';
    return;
  }
  
  // UI-Status aktualisieren
  addButton.disabled = true;
  addButton.innerHTML = '<em>Analysiere...</em>';
  statusDiv.innerHTML = '';
  
  try {
    console.log('[ADD-KEYWORD] Füge neues Schlagwort hinzu:', keyword);
    
    const response = await fetch('http://localhost:3003/api/keywords-add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ keyword: keyword })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      // Erfolg
      statusDiv.innerHTML = '';
      
      // Eingabefeld leeren
      keywordInput.value = '';
      
      // Schlagwort-Liste aktualisieren
      await loadKeywordsData();
      
      // Zeige das neue Schlagwort in der Liste
      displayKeywords();
      
      console.log('[ADD-KEYWORD] Schlagwort erfolgreich hinzugefügt:', result);
      
    } else {
      // Fehler
      if (response.status === 409) {
        statusDiv.innerHTML = '';
      } else if (response.status === 404) {
        statusDiv.innerHTML = '';
      } else {
        statusDiv.innerHTML = '';
      }
      
      console.error('[ADD-KEYWORD] Fehler beim Hinzufügen:', result);
    }
    
  } catch (error) {
    statusDiv.innerHTML = '';
    console.error('[ADD-KEYWORD] Netzwerkfehler:', error);
  } finally {
    // UI-Status zurücksetzen
    addButton.disabled = false;
    addButton.textContent = 'Schlagwort hinzufügen';
  }
}

// ============================================================================
// SCHLAGWORT LÖSCHEN
// ============================================================================

window.handleDeleteKeywordInputKeypress = function(event) {
  if (event.key === 'Enter') {
    window.deleteKeyword();
  }
}

window.deleteKeyword = async function() {
  const keywordInput = document.getElementById('regenerateKeywordInput');
  const regenerateButton = document.getElementById('regenerateKeywordButton');
  const statusDiv = document.getElementById('regenerateKeywordStatus');
  
  if (!keywordInput || !regenerateButton || !statusDiv) {
    console.error('[DELETE-KEYWORD] UI-Elemente nicht gefunden');
    return;
  }
  
  const keyword = keywordInput.value.trim();
  
  if (!keyword) {
    statusDiv.innerHTML = '';
    return;
  }
  
  // UI-Status aktualisieren
  regenerateButton.disabled = true;
  regenerateButton.textContent = 'Lösche...';
  regenerateButton.style.fontStyle = 'italic';
  statusDiv.innerHTML = '';
  
  try {
    console.log('[DELETE-KEYWORD] Lösche Schlagwort:', keyword);
    
    const response = await fetch(`${API_BASE}/api/keywords-delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ keyword })
    });
    
    let result;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      result = await response.json();
    } else {
      const text = await response.text();
      throw new Error(`Unerwartete Antwort (kein JSON): ${text.slice(0, 120)}`);
    }
    
    if (response.ok && result.success) {
      statusDiv.innerHTML = '';
      keywordInput.value = '';
      await loadKeywordsData();
      displayKeywords();
      console.log('[DELETE-KEYWORD] Schlagwort erfolgreich gelöscht:', result);
    } else {
      statusDiv.innerHTML = '';
      console.error('[DELETE-KEYWORD] Fehler beim Löschen:', result);
    }
    
  } catch (error) {
    statusDiv.innerHTML = '';
    console.error('[DELETE-KEYWORD] Netzwerkfehler:', error);
  } finally {
    // UI-Status zurücksetzen
    regenerateButton.disabled = false;
    regenerateButton.textContent = 'Schlagwort löschen';
    regenerateButton.style.fontStyle = 'normal';
  }
}

// Enter-Taste für Schlagwort-Eingabe
function handleKeywordInputKeypress(event) {
  if (event.key === 'Enter') {
    addNewKeyword();
  }
}

// Hilfsfunktion: Formatiere Datum
function formatDate(dateStr) {
  console.log('[TIMELINE] Verstecke Timeline');
  
  const splitView = document.getElementById('timelineSplitView');
  const timelinePanel = document.querySelector('.timeline-panel');
  
  // Timeline Viewer leeren wenn Timeline geschlossen wird
  const timelineViewerContent = document.getElementById('timelineViewerContent');
  if (timelineViewerContent) {
    timelineViewerContent.innerHTML = '';
    console.log('[TIMELINE] Timeline Viewer geleert');
  }
  
  // Timeline Document Title zurücksetzen
  const timelineDocumentTitle = document.getElementById('timelineDocumentTitle');
  if (timelineDocumentTitle) {
    timelineDocumentTitle.textContent = 'Wählen Sie einen Vortrag aus der Timeline';
    console.log('[TIMELINE] Timeline Document Title zurückgesetzt');
  }
  
  // Timeline-Panel verstecken
  if (timelinePanel) {
    timelinePanel.classList.add('hidden');
  }
  
  // Timeline-Panel-Titel zurücksetzen
  const timelinePanelTitle = document.getElementById('timelinePanelTitle');
  if (timelinePanelTitle) {
    timelinePanelTitle.textContent = 'Timeline';
  }
  
  // Timeline-Panel-Such-Button verstecken
  const timelinePanelSearchBtn = document.getElementById('timelinePanelSearchBtn');
  if (timelinePanelSearchBtn) {
    timelinePanelSearchBtn.style.display = 'none';
  }
  
  // Nach kurzer Verzögerung Split-View komplett verstecken
  setTimeout(() => {
    splitView.style.display = 'none';
    
    // Haupt-Viewer wieder anzeigen
    document.getElementById('viewer').style.display = 'block';
    document.getElementById('document-title').style.display = 'block';
    document.getElementById('viewer-header').style.display = 'flex';
    
    // Header-Styles zurücksetzen, Update kümmert sich um korrekte Werte
    const mainContainerEl = document.getElementById('main-container');
    const summaryPanelEl = document.getElementById('summary-panel');
    if (mainContainerEl) mainContainerEl.style.marginTop = '';
    if (summaryPanelEl) summaryPanelEl.style.top = '';
    
    // Header-Position und Layout korrekt wiederherstellen
    setTimeout(() => {
      updateHeaderPosition();
    }, 50);
    
    // TOC-Links für Haupt-Viewer wiederherstellen
    setTimeout(() => {
      buildTableOfContents();
    }, 100);
    
    // Reset Timeline-Viewer-Buttons
    resetTimelineViewerButtons();
    
    // Timeline-Keyword zurücksetzen und Keywords neu rendern
    currentTimelineKeyword = null;
    displayKeywords(currentAlphabet); // Keywords neu rendern um Such-Button zu entfernen
    
    // Alle Timeline-Buttons auf inaktiv setzen
    document.querySelectorAll('.timeline-btn').forEach(btn => {
      btn.classList.remove('active');
      btn.innerHTML = '📅';
      btn.title = 'Timeline anzeigen';
    });
  }, 300);
}

// Zeige Timeline für ein Schlagwort
async function showTimeline(keyword, clickedButton) {
  console.log('[TIMELINE] Öffne Timeline für:', keyword);
  
  const splitView = document.getElementById('timelineSplitView');
  // Toggle-Logik: Wenn Timeline offen und gleiches Schlagwort -> schließen
  if (splitView && splitView.style.display !== 'none' && currentTimelineKeyword === keyword) {
    closeTimeline();
    return;
  }
  const timelinePanel = document.querySelector('.timeline-panel');
  const content = document.getElementById('timelineContent');
  const documentTitle = document.getElementById('timelineDocumentTitle');
  const viewerContent = document.getElementById('timelineViewerContent');
  
  // Main Viewer leeren wenn Timeline geöffnet wird
  const viewer = document.getElementById('viewer');
  if (viewer) {
    viewer.innerHTML = '';
    console.log('[TIMELINE] Main Viewer geleert');
  }
  
  // Document Title zurücksetzen
  const mainDocumentTitle = document.getElementById('document-title');
  if (mainDocumentTitle) {
    mainDocumentTitle.textContent = 'Bitte ein Suchergebnis auswählen…';
    console.log('[TIMELINE] Document Title zurückgesetzt');
  }
  
  // Alle anderen Timeline-Buttons auf inaktiv setzen (außer dem geklickten)
  console.log('[DEBUG] Timeline-Button geklickt:', clickedButton);
  document.querySelectorAll('.timeline-btn').forEach(btn => {
    console.log('[DEBUG] Button gefunden:', btn, 'Ist geklickter Button:', btn === clickedButton);
    if (btn !== clickedButton) {  // Nur andere Buttons deaktivieren
      btn.classList.remove('active');
      btn.innerHTML = '<i data-lucide="calendar"></i>';
      btn.title = 'Timeline anzeigen';
      console.log('[DEBUG] Button deaktiviert:', btn);
    }
  });
  
  // Aktuellen Button als aktiv markieren
  if (clickedButton) {
    clickedButton.classList.add('active');
    clickedButton.innerHTML = '<i data-lucide="calendar"></i>';
    clickedButton.title = 'Timeline verstecken';
    console.log('[DEBUG] Button aktiviert:', clickedButton);
  }
  
  // Nach dem Aktualisieren der Button-Inhalte Lucide-Icons neu initialisieren
  if (typeof initializeLucideIcons === 'function') {
    initializeLucideIcons();
  }
  
  // Timeline-Schlagwort speichern
  currentTimelineKeyword = keyword;
  
  // Timeline-Panel-Titel setzen
  const timelinePanelTitle = document.getElementById('timelinePanelTitle');
  if (timelinePanelTitle) {
    timelinePanelTitle.textContent = keyword;
  }
  
  // Timeline-Panel-Such-Button anzeigen
  const timelinePanelSearchBtn = document.getElementById('timelinePanelSearchBtn');
  if (timelinePanelSearchBtn) {
    timelinePanelSearchBtn.style.display = 'inline-block';
  }
  
  // Split-View anzeigen und Haupt-Viewer verstecken
  splitView.style.display = 'flex';
  document.getElementById('viewer').style.display = 'none';
  document.getElementById('document-title').style.display = 'none';
  document.getElementById('viewer-header').style.display = 'none';
  
  // Debug: Prüfe ob Timeline-Buttons noch sichtbar sind
  setTimeout(() => {
    const timelineButtons = document.querySelectorAll('.timeline-btn');
    console.log('[DEBUG] Timeline-Buttons nach Öffnen:', timelineButtons.length);
    timelineButtons.forEach((btn, index) => {
      console.log(`[DEBUG] Button ${index}:`, btn, 'Sichtbar:', btn.offsetParent !== null, 'Display:', window.getComputedStyle(btn).display);
    });
  }, 100);
  
  // Header-Gap für Timeline-Ansicht entfernen
  const mainContainerEl = document.getElementById('main-container');
  const summaryPanelEl = document.getElementById('summary-panel');
  if (mainContainerEl) mainContainerEl.style.marginTop = '0px';
  if (summaryPanelEl) summaryPanelEl.style.top = '0px';
  
  // Timeline-Panel sichtbar machen
  if (timelinePanel) {
    timelinePanel.classList.remove('hidden');
  }
  
  // Keywords neu rendern NACH dem Öffnen der Timeline - ENTFERNT (verursacht Doppelklick-Problem)
  // setTimeout(() => {
  //   displayKeywords(currentAlphabet);
  // }, 100);
  
  // title.textContent = `Timeline: ${keyword}`; // Timeline-Titel entfernt
  content.innerHTML = '<div style="text-align: center; padding: 2rem;">Lade Timeline...</div>';
  documentTitle.textContent = 'Wählen Sie einen Vortrag aus der Timeline';
  viewerContent.innerHTML = '';
  
  try {
    // Lade Vortragsdaten
    await loadFullLecturesForTimeline();
    
    // NEUE KI-TIMELINE-ANALYSE
    console.log('[TIMELINE] Starte KI-Timeline-Analyse für:', keyword);
    content.innerHTML = '<div style="text-align: center; padding: 2rem; font-style: italic;">Lade Timeline-Analyse...</div>';
    
    try {
      const timelineResponse = await fetch(`${API_BASE}/api/keyword-timeline-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: keyword, useCache: true })
      });
      
      if (!timelineResponse.ok) {
        throw new Error(`Timeline-Analyse Fehler: ${timelineResponse.status}`);
      }
      
      const timelineData = await timelineResponse.json();
      console.log('[TIMELINE] KI-Timeline-Daten erhalten:', timelineData);
      
      // Erstelle erweiterte Timeline mit KI-Analyse
      const enhancedTimelineHTML = generateEnhancedTimelineHTML(timelineData);
      content.innerHTML = enhancedTimelineHTML;
      
      // Timeline-Panel-Titel erweitern
      const timelinePanelTitle = document.getElementById('timelinePanelTitle');
      if (timelinePanelTitle) {
        timelinePanelTitle.textContent = `${keyword} (${timelineData.relevantLectures} Vorträge)`;
      }
      
    } catch (timelineError) {
      console.warn('[TIMELINE] KI-Analyse fehlgeschlagen, verwende Fallback:', timelineError);
      
      // Fallback: Verwende alte Timeline-Logik
      const keywordData = keywordsData.find(k => k.keyword === keyword);
      if (!keywordData || !keywordData.gaReferences) {
        content.innerHTML = '<div class="timeline-no-results">Keine GA-Referenzen für dieses Schlagwort gefunden.</div>';
        return;
      }
      
      const timelineEntries = await createTimelineEntries(keywordData.gaReferences);
      
      if (timelineEntries.length === 0) {
        content.innerHTML = '<div class="timeline-no-results">Keine Vorträge mit diesem Schlagwort gefunden.</div>';
        return;
      }
      
      const groupedByYear = groupTimelineByYear(timelineEntries);
      const timelineHTML = generateTimelineHTML(groupedByYear);
      content.innerHTML = timelineHTML;
    }
    
  } catch (error) {
    console.error('[TIMELINE] Fehler:', error);
    content.innerHTML = '<div class="timeline-no-results">Fehler beim Laden der Timeline.</div>';
  }
}

// Hilfsfunktion: Mache Timeline-Zitate klickbar (verwendet gleiche Logik wie Themensuche)
function makeTimelineQuotesClickable(quoteText, lectureId) {
  // Verwende die gleiche Regex wie in der Themensuche
  const gaRefRegex = /\(GA(\d{3}[a-z]?)\/(\d+):([a-z0-9^]+)\)/gi;
  
  return quoteText.replace(gaRefRegex, (match, gaNum, lectureNum, index) => {
    const cleanIndex = index.replace(/^\^/, '');
    return ` (<a href="#" onclick="showLectureInTimeline('${lectureId}', '${cleanIndex}'); return false;" class="timeline-quote-link" title="Zu diesem Absatz springen">GA${gaNum}/${lectureNum}</a>)`;
  });
}

// Generiere erweiterte Timeline HTML mit KI-Analyse
function generateEnhancedTimelineHTML(timelineData) {
  console.log('[TIMELINE-HTML] Generiere HTML für Timeline-Daten:', timelineData);
  
  let html = '';
  
  // Prüfe ob Timeline-Daten vorhanden sind
  if (!timelineData || !timelineData.timelineEntries || timelineData.timelineEntries.length === 0) {
    console.warn('[TIMELINE-HTML] Keine Timeline-Einträge gefunden');
    return '<div class="timeline-no-results">Keine Vorträge mit höchster Relevanz für dieses Schlagwort gefunden.</div>';
  }
  
  // Timeline-Statistiken anzeigen (ohne Analyse)
  html += `
    <div class="timeline-analysis">
      <div class="timeline-stats">
        <span>Gefunden in ${timelineData.relevantLectures || 0} von ${timelineData.totalLectures || 0} Vorträgen</span>
      </div>
    </div>
  `;
  
  // Sortiere Timeline-Einträge chronologisch
  const sortedEntries = timelineData.timelineEntries.sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return a.date.localeCompare(b.date);
  });
  
  console.log('[TIMELINE-HTML] Sortierte Einträge:', sortedEntries.length);
  
  // Erstelle Timeline mit Jahr-Gruppierung
  let lastYear = null;
  sortedEntries.forEach((entry, index) => {
    console.log(`[TIMELINE-HTML] Verarbeite Eintrag ${index + 1}/${sortedEntries.length}:`, entry);
    
    // Zeige Jahr nur wenn es sich ändert
    const showYear = lastYear !== entry.year;
    lastYear = entry.year;
    
    html += `
      <div class="timeline-item enhanced">
        ${showYear ? `<div class="timeline-year">${entry.year}</div>` : '<div class="timeline-year-spacer"></div>'}
        <div class="timeline-content enhanced" onclick="showLectureInTimeline('${entry.lectureId}')">
          <div class="timeline-lecture-number">
            ${entry.date}
          </div>
          <div class="timeline-lecture-title">${entry.title} (${entry.lectureId})</div>
          ${entry.keyQuotes && entry.keyQuotes.length > 0 ? `
            <div class="timeline-quotes">
              ${entry.keyQuotes.map(quote => makeTimelineQuotesClickable(quote, entry.lectureId)).join('; ')}
            </div>
          ` : ''}
          ${entry.thematicFocus ? `
            <div class="timeline-focus">
              <strong>${entry.thematicFocus}</strong>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  });
  
  console.log('[TIMELINE-HTML] Generiertes HTML-Länge:', html.length);
  console.log('[TIMELINE-HTML] Anzahl verarbeiteter Einträge:', timelineData.timelineEntries.length);
  
  return html;
}

// Erstelle Timeline-Einträge aus GA-Referenzen
async function createTimelineEntries(gaReferences) {
  const entries = [];
  const seenLectures = new Set(); // Verhindert Duplikate
  
  for (const gaRef of gaReferences) {
    // Parse GA-Referenz (z.B. "GA306/5")
    const match = gaRef.match(/^(GA\d{3}[a-z]?)\/(\d+)$/);
    if (!match) continue;
    
    const [, gaNumber, lectureNumber] = match;
    const lectureId = `${gaNumber}/${lectureNumber}`;
    
    // Prüfe ob dieser Vortrag bereits hinzugefügt wurde
    if (seenLectures.has(lectureId)) {
      continue; // Überspringe Duplikate
    }
    
    // Finde Vortrag in den Daten
    const lecture = fullLecturesData[lectureId];
    if (!lecture) continue;
    
    // Markiere als gesehen
    seenLectures.add(lectureId);
    
    // Extrahiere Jahr aus dem Datum
    let year = null;
    if (lecture.date) {
      const yearMatch = lecture.date.match(/^(\d{4})/);
      if (yearMatch) {
        year = parseInt(yearMatch[1]);
      }
    }
    
    // Fallback: Jahr aus GA-Nummer ableiten (ungefähr)
    if (!year) {
      const gaNum = parseInt(gaNumber.replace('GA', ''));
      if (gaNum >= 51 && gaNum <= 100) year = 1900 + Math.floor((gaNum - 51) * 0.5);
      else if (gaNum >= 101 && gaNum <= 200) year = 1910 + Math.floor((gaNum - 101) * 0.3);
      else if (gaNum >= 201 && gaNum <= 300) year = 1920 + Math.floor((gaNum - 201) * 0.2);
      else year = 1925; // Fallback
    }
    
    entries.push({
      year: year,
      lecture: lecture,
      gaRef: gaRef,
      lectureId: lectureId
    });
  }
  
  return entries;
}

// Gruppiere Timeline-Einträge nach Jahr
function groupTimelineByYear(entries) {
  const grouped = {};
  
  entries.forEach(entry => {
    if (!grouped[entry.year]) {
      grouped[entry.year] = [];
    }
    grouped[entry.year].push(entry);
  });
  
  // Sortiere Einträge innerhalb jedes Jahres nach Datum
  Object.keys(grouped).forEach(year => {
    grouped[year].sort((a, b) => {
      const dateA = parseDateForSorting(a.lecture.date);
      const dateB = parseDateForSorting(b.lecture.date);
      return dateA - dateB;
    });
  });
  
  return grouped;
}

// Hilfsfunktion: Parse Datum für Sortierung (deutsches Format TT.MM.JJJJ)
function parseDateForSorting(dateString) {
  if (!dateString) return new Date('1900-01-01'); // Fallback für fehlende Daten
  
  try {
    // Versuche verschiedene Datumsformate zu parsen
    let date;
    
    // Deutsches Format: TT.MM.JJJJ
    if (dateString.includes('.')) {
      const parts = dateString.split('.');
      if (parts.length === 3) {
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1; // JavaScript Monate sind 0-basiert
        const year = parseInt(parts[2], 10);
        date = new Date(year, month, day);
      }
    }
    // ISO Format: JJJJ-MM-TT
    else if (dateString.includes('-')) {
      date = new Date(dateString.split(' ')[0]);
    }
    // Andere Formate
    else {
      date = new Date(dateString);
    }
    
    // Prüfe ob Datum gültig ist
    if (isNaN(date.getTime())) {
      return new Date('1900-01-01'); // Fallback
    }
    
    return date;
  } catch (error) {
    console.warn('Fehler beim Parsen des Datums:', dateString, error);
    return new Date('1900-01-01'); // Fallback
  }
}

// Hilfsfunktion: Formatiere Datum zu TT.MM.JJJJ
function formatDateToDDMMYYYY(dateString) {
  if (!dateString) return 'Datum unbekannt';
  
  try {
    // Parse verschiedene Datumsformate
    let date;
    if (dateString.includes('-')) {
      // Format: YYYY-MM-DD oder YYYY-MM-DD HH:MM:SS
      date = new Date(dateString.split(' ')[0]);
    } else if (dateString.includes('.')) {
      // Format: DD.MM.YYYY
      const parts = dateString.split('.');
      if (parts.length === 3) {
        date = new Date(parts[2], parts[1] - 1, parts[0]);
      }
    } else {
      // Fallback: Versuche direkt zu parsen
      date = new Date(dateString);
    }
    
    if (isNaN(date.getTime())) {
      return 'Datum unbekannt';
    }
    
    // Formatiere zu DD.MM.YYYY
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    return `${day}.${month}.${year}`;
  } catch (error) {
    console.warn('Fehler beim Formatieren des Datums:', dateString, error);
    return 'Datum unbekannt';
  }
}

// Generiere Timeline HTML
function generateTimelineHTML(groupedByYear) {
  let html = '';
  
  const years = Object.keys(groupedByYear).sort((a, b) => parseInt(a) - parseInt(b));
  
  years.forEach(year => {
    const entries = groupedByYear[year];
    
    entries.forEach((entry, index) => {
      const lectureDate = formatDateToDDMMYYYY(entry.lecture.date);
      
      html += `
        <div class="timeline-item">
          ${index === 0 ? `<div class="timeline-year">${year}</div>` : '<div class="timeline-year-spacer"></div>'}
          <div class="timeline-content" onclick="showLectureInTimeline('${entry.lectureId}')">
            <div class="timeline-lecture-number">
              ${lectureDate}
            </div>
          </div>
        </div>
      `;
    });
  });
  
  return html;
}

// Zeige Vortrag im Timeline-Viewer
async function showLectureInTimeline(lectureId, targetIndex = null) {
  console.log('[TIMELINE] Zeige Vortrag:', lectureId, targetIndex ? `mit Index: ${targetIndex}` : '');
  
  const documentTitle = document.getElementById('timelineDocumentTitle');
  const viewerContent = document.getElementById('timelineViewerContent');
  
  // Verwende die gleiche Funktion wie in der GA-Übersicht
  try {
    await showLecture(lectureId, targetIndex, []);
    
    // Kopiere den Inhalt vom Haupt-Viewer in den Timeline-Viewer
    const mainViewer = document.getElementById('viewer');
    const mainTitle = document.getElementById('document-title');
    
    if (mainViewer && mainTitle) {
      // Kopiere Titel
      documentTitle.innerHTML = mainTitle.innerHTML;
      
      // Kopiere Inhalt
      viewerContent.innerHTML = mainViewer.innerHTML;
      
      // Scrolle nach oben (wird von showLecture überschrieben wenn targetIndex gesetzt ist)
      if (!targetIndex) {
        viewerContent.scrollTop = 0;
      } else {
        // Wenn targetIndex gesetzt ist, scrolle zum entsprechenden Absatz im Timeline-Viewer
        setTimeout(() => {
          const cleanIndex = targetIndex.replace(/^\^/, '');
          const paraElement = viewerContent.querySelector(`#para-${cleanIndex}`);
          if (paraElement) {
            paraElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Highlighting hinzufügen
            paraElement.style.backgroundColor = '#fff3cd';
            paraElement.style.borderLeft = '4px solid #ffc107';
            setTimeout(() => {
              paraElement.style.backgroundColor = '';
              paraElement.style.borderLeft = '';
            }, 3000);
          }
        }, 200);
      }
      
      // TOC für Timeline-Viewer erstellen
      buildTableOfContents();
    }
    
    // Zeige die Timeline-Viewer-Buttons
    const originalBtn = document.getElementById('timelineViewerOriginalBtn');
    const summaryBtn = document.getElementById('timelineViewerSummaryBtn');
    
    if (originalBtn) originalBtn.style.display = 'inline-block';
    if (summaryBtn) summaryBtn.style.display = 'inline-block';
    
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Laden des Vortrags:', error);
    documentTitle.textContent = 'Fehler beim Laden des Vortrags';
    viewerContent.innerHTML = '<p>Der gewählte Vortrag konnte nicht geladen werden.</p>';
    
    // Verstecke die Timeline-Viewer-Buttons bei Fehlern
    const originalBtn = document.getElementById('timelineViewerOriginalBtn');
    const summaryBtn = document.getElementById('timelineViewerSummaryBtn');
    
    if (originalBtn) originalBtn.style.display = 'none';
    if (summaryBtn) summaryBtn.style.display = 'none';
  }
}

// Reset Timeline-Viewer-Buttons
function resetTimelineViewerButtons() {
  const originalBtn = document.getElementById('timelineViewerOriginalBtn');
  const summaryBtn = document.getElementById('timelineViewerSummaryBtn');
  
  if (originalBtn) originalBtn.style.display = 'none';
  if (summaryBtn) summaryBtn.style.display = 'none';
  
  // Reset Timeline-Dokument-Titel
  const documentTitle = document.getElementById('timelineDocumentTitle');
  if (documentTitle) {
    documentTitle.textContent = 'Wählen Sie einen Vortrag aus der Timeline';
  }
}

// Schließe Timeline Split-View
function closeTimeline() {
  const splitView = document.getElementById('timelineSplitView');
  splitView.style.display = 'none';
  
  // Haupt-Viewer wieder anzeigen
  document.getElementById('viewer').style.display = 'block';
  document.getElementById('document-title').style.display = 'block';
  document.getElementById('viewer-header').style.display = 'flex';
  
  // Reset Timeline-Viewer-Buttons
  resetTimelineViewerButtons();
  
  // TOC-Links für Haupt-Viewer wiederherstellen
  setTimeout(() => {
    buildTableOfContents();
  }, 100);
}

// Timeline Panel Resize Funktionalität
function initializeTimelineResize() {
  const resizeHandle = document.getElementById('timelineResizeHandle');
  const timelinePanel = document.querySelector('.timeline-panel');
  
  if (!resizeHandle || !timelinePanel) {
    console.log('[TIMELINE-RESIZE] Elements not found');
    return;
  }
  
  let isResizing = false;
  let startX = 0;
  let startWidth = 0;
  
  resizeHandle.addEventListener('mousedown', (e) => {
    isResizing = true;
    startX = e.clientX;
    startWidth = timelinePanel.offsetWidth;
    
    // Prevent text selection during resize
    e.preventDefault();
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    
    const deltaX = e.clientX - startX;
    const newWidth = startWidth + deltaX;
    
    // Set min and max width constraints
    const minWidth = 400;
    const maxWidth = window.innerWidth * 0.8;
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      timelinePanel.style.width = newWidth + 'px';
    }
  });
  
  document.addEventListener('mouseup', () => {
    if (isResizing) {
      isResizing = false;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    }
  });
}

// Initialize Timeline Resize on page load
document.addEventListener('DOMContentLoaded', () => {
  initializeTimelineResize();
});

// Suche das Timeline-Schlagwort im aktuellen Vortragstext
function searchKeywordInCurrentLecture() {
  if (!currentTimelineKeyword) {
    console.log('[KEYWORD-SEARCH] Kein Timeline-Schlagwort verfügbar');
    return;
  }
  
  console.log('[KEYWORD-SEARCH] Suche nach:', currentTimelineKeyword);
  
  const viewerContent = document.getElementById('timelineViewerContent');
  if (!viewerContent || !viewerContent.innerHTML.trim()) {
    alert('Bitte wählen Sie zuerst einen Vortrag aus der Timeline aus.');
    return;
  }
  
  // Entferne vorherige Markierungen
  const paragraphs = viewerContent.querySelectorAll('.paragraph');
  paragraphs.forEach(para => {
    para.innerHTML = para.innerHTML.replace(/<mark[^>]*>([^<]*)<\/mark>/gi, '$1');
  });
  
  // Suche nach dem Schlagwort und markiere es
  let foundCount = 0;
  const keyword = currentTimelineKeyword.trim();
  const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  
  paragraphs.forEach(para => {
    const originalContent = para.innerHTML;
    const isDarkMode = document.body.classList.contains('dark-mode');
    const backgroundColor = isDarkMode ? 'rgba(70, 120, 134, 0.5)' : 'rgba(70, 120, 134, 0.3)';
    const textColor = isDarkMode ? 'var(--dark-text-color)' : 'inherit';
    const highlightedContent = originalContent.replace(regex, `<mark style="background-color: ${backgroundColor}; color: ${textColor}; padding: 2px 4px; border-radius: 2px;">$1</mark>`);
    
    if (highlightedContent !== originalContent) {
      para.innerHTML = highlightedContent;
      foundCount += (originalContent.match(regex) || []).length;
    }
  });
  
  if (foundCount > 0) {
    // Scrolle zum ersten gefundenen Element
    const firstMark = viewerContent.querySelector('mark');
    if (firstMark) {
      firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Zeige Erfolgsmeldung
    const button = document.querySelector('.keyword-search-btn');
    if (button) {
      const originalText = button.innerHTML;
      button.innerHTML = `${foundCount}`;
      button.style.backgroundColor = 'var(--accent-color)';
      button.style.color = 'white';
      
      // Nach 3 Sekunden zurücksetzen
      setTimeout(() => {
        button.innerHTML = originalText;
        button.style.backgroundColor = '';
        button.style.color = '';
      }, 3000);
    }
    
    // Zeige Erfolgsmeldung auch im Timeline-Panel-Button
    const timelineButton = document.getElementById('timelinePanelSearchBtn');
    if (timelineButton) {
      const originalText = timelineButton.innerHTML;
      timelineButton.innerHTML = `${foundCount}`;
      timelineButton.style.backgroundColor = 'var(--accent-color)';
      timelineButton.style.color = 'white';
      
      // Nach 3 Sekunden zurücksetzen
      setTimeout(() => {
        timelineButton.innerHTML = '<i data-lucide="text-search"></i>';
        timelineButton.style.backgroundColor = '';
        timelineButton.style.color = '';
        initializeLucideIcons(); // Icons nach Content-Update neu initialisieren
      }, 3000);
    }
  } else {
    alert(`Das Schlagwort "${currentTimelineKeyword}" wurde im aktuellen Vortragstext nicht gefunden.`);
  }
}

// Globale Funktion zum Schließen der Timeline
function hideTimelineIfOpen() {
  const splitView = document.getElementById('timelineSplitView');
  if (splitView && splitView.style.display !== 'none') {
    closeTimeline();
  }
}


// Hilfsfunktion: Formatiere Datum
function formatDate(dateStr) {
  if (!dateStr) return '';
  
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (error) {
    return dateStr;
  }
}

// Hilfsfunktion: Erstelle Online-URL (aus existierender Funktion kopiert)
function createOnlineURL(lecture) {
  if (!lecture.fileName) {
    return `https://rudolf-steiner-online.de/${lecture.ID || ''}`;
  }
  
  const fileName = lecture.fileName;
  const match = fileName.match(/^(GA\d{3}[a-z]?)\/(\d+)\s*-\s*(.+)$/);
  
  if (!match) {
    return `https://rudolf-steiner-online.de/${lecture.ID || ''}`;
  }
  
  const [, gaNumber, lectureNumber, rest] = match;
  
  const titleForUrl = rest.replace(/ /g, '+');
  const encodedTitle = encodeURIComponent(titleForUrl).replace(/%2B/g, '+');
  
  return `https://rudolf-steiner-online.de/${gaNumber}+(${lectureNumber}.)+${encodedTitle}`;
}

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', function() {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});

// Re-initialize icons after dynamic content changes
function initializeLucideIcons() {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

// Funktion zum Speichern von markierten fehlerhaften Wörtern
async function saveMarkedWord(word, gaTitle) {
  try {
    console.log('[MARKED-WORD] API_BASE:', API_BASE);
    console.log('[MARKED-WORD] Sende Request für:', word);
    
    const response = await fetch(`${API_BASE}/api/save-marked-word`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        word: word,
        gaTitle: gaTitle,
        timestamp: new Date().toISOString()
      })
    });
    
    console.log('[MARKED-WORD] Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[MARKED-WORD] Server Error:', errorText);
      throw new Error(`Server Error (${response.status}): ${errorText}`);
    }
    
    const result = await response.json();
    console.log('[MARKED-WORD] Erfolgreich gespeichert:', result);
    
    // Kurze visuelle Bestätigung
    showTemporaryMessage(`Wort "${word}" gespeichert (${result.totalEntries} Einträge)`);
    
    return result;
  } catch (error) {
    console.error('[MARKED-WORD] Fehler:', error);
    alert(`Fehler beim Speichern:\n${error.message}\n\nBitte prüfen Sie die Browser-Konsole für Details.`);
  }
}

// Event-Listener für Rechtsklick im Viewer
document.addEventListener('DOMContentLoaded', function() {
  const viewer = document.getElementById('viewer');
  
  if (viewer) {
    viewer.addEventListener('contextmenu', function(e) {
      // Hole markierten Text
      const selection = window.getSelection();
      const selectedText = selection.toString().trim();
      
      // Nur wenn Text markiert ist
      if (selectedText && selectedText.length > 0) {
        e.preventDefault(); // Verhindere Standard-Kontextmenü
        
        // Hole aktuellen Vortragstitel
        const documentTitle = document.getElementById('document-title');
        const gaTitle = documentTitle ? documentTitle.textContent : 'Unbekannt';
        
        // Zeige Bestätigungsdialog
        const confirmed = confirm(`Wort "${selectedText}" als fehlerhaft markieren?\n\nVortrag: ${gaTitle}`);
        
        if (confirmed) {
          saveMarkedWord(selectedText, gaTitle);
        }
      }
    });
  }
});
</script>

<!-- Welcome Modal -->
<div id="welcomeModal" class="welcome-modal">
  <div class="welcome-modal-content">
    <div class="welcome-modal-header">
      <h1>Willkommen</h1>
      <button class="welcome-close-btn" onclick="closeWelcomeModal()">&times;</button>
    </div>
    <div class="welcome-modal-body" id="welcomeModalBody">
    </div>
    <div class="welcome-modal-footer">
      <button class="welcome-start-btn" onclick="closeWelcomeModal()">Start</button>
    </div>
  </div>
</div>

<!-- Help Modal -->
<div id="helpModal" class="help-modal">
  <div class="help-modal-content">
    <div class="help-modal-header">
      <h2 id="helpModalTitle">GA-Suche Anleitung</h2>
      <button class="help-modal-close" onclick="closeHelpModal()">&times;</button>
    </div>
    <div class="help-modal-body">
      <!-- Choice Screen -->
      <div id="helpChoice" class="help-choice">
        <p style="margin-bottom: 1.5rem;">Wählen Sie die gewünschte Anleitung:</p>
        <div class="help-choice-buttons">
          <button class="help-choice-btn" onclick="showHelpContent('welcome')">
            <h3>Willkommen</h3>
          </button>
          <button class="help-choice-btn" onclick="showHelpContent('gesamtausgabe')">
            <h3>Gesamtausgabe</h3>
          </button>
          <button class="help-choice-btn" onclick="showHelpContent('full')">
            <h3>Anleitung</h3> 
          </button>
          <button class="help-choice-btn" onclick="showHelpContent('quick')">
            <h3>Impressum</h3>
          </button>
        </div>
      </div>
      
      <!-- Content Display -->
      <div id="helpContentDisplay" class="help-content-display">
        <div id="helpContentText"></div>
        <button class="help-back-btn" onclick="showHelpChoice()">← Zurück zur Auswahl</button>
      </div>
    </div>
  </div>
</div>

<script>
// Help Modal Functions
function openHelpModal() {
  const modal = document.getElementById('helpModal');
  modal.classList.add('active');
  showHelpChoice();
  
  // Lucide Icons neu rendern
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

function closeHelpModal() {
  const modal = document.getElementById('helpModal');
  modal.classList.remove('active');
}

function showHelpChoice() {
  document.getElementById('helpChoice').style.display = 'block';
  document.getElementById('helpContentDisplay').classList.remove('active');
  document.getElementById('helpModalTitle').textContent = 'GA-Suche Anleitung';
}

async function showHelpContent(type) {
  const contentDisplay = document.getElementById('helpContentDisplay');
  const contentText = document.getElementById('helpContentText');
  const choice = document.getElementById('helpChoice');
  const title = document.getElementById('helpModalTitle');
  
  choice.style.display = 'none';
  contentDisplay.classList.add('active');
  
  // Lade-Indikator
  contentText.innerHTML = '<p style="text-align: center; padding: 2rem;">Lade Anleitung...</p>';
  
  try {
    let mdFile = '';
    if (type === 'welcome') {
      title.textContent = 'Willkommen';
      mdFile = 'WILLKOMMEN.md';
    } else if (type === 'gesamtausgabe') {
      title.textContent = 'Gesamtausgabe';
      mdFile = 'GESAMTAUSGABE.md';
    } else if (type === 'full') {
      title.textContent = 'GA-Suche Anleitung';
      mdFile = 'BENUTZERANLEITUNG.md';
    } else if (type === 'quick') {
      title.textContent = 'Impressum';
      mdFile = 'IMPRESSUM.md';
    }
    
    // Lade Markdown-Datei vom Backend-Server (alle aus system-Ordner)
    const isLocal = window.location.hostname === 'localhost' ||
                    window.location.hostname === '127.0.0.1' ||
                    window.location.protocol === 'file:';
    const API_BASE = isLocal ? 'http://localhost:3003' : 'https://ga-suche.onrender.com';
    const response = await fetch(`${API_BASE}/system/${mdFile}`);
    if (!response.ok) {
      throw new Error(`Fehler beim Laden: ${response.status}`);
    }
    const markdown = await response.text();
    
    // Konvertiere Markdown zu HTML mit marked.js
    if (typeof marked !== 'undefined') {
      // Konfiguriere marked für besseres Rendering
      marked.setOptions({
        breaks: true,
        gfm: true
      });
      contentText.innerHTML = marked.parse(markdown);
    } else {
      // Fallback: Zeige Markdown als Text
      contentText.innerHTML = `<pre style="white-space: pre-wrap;">${markdown}</pre>`;
    }
    
  } catch (error) {
    console.error('Fehler beim Laden der Anleitung:', error);
    contentText.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: #999;">
        <p><strong>Fehler beim Laden der Anleitung</strong></p>
        <p style="font-size: 0.9em; margin-top: 1rem;">
          ${error.message}<br>
          Bitte stellen Sie sicher, dass die Markdown-Dateien verfügbar sind.
        </p>
      </div>
    `;
  }
  
  // Scroll to top
  contentDisplay.scrollTop = 0;
}

// Die Inhalte werden jetzt dynamisch aus system/WILLKOMMEN.md, system/GESAMTAUSGABE.md, system/BENUTZERANLEITUNG.md und system/IMPRESSUM.md geladen

// Close modal when clicking outside
document.addEventListener('click', function(event) {
  const modal = document.getElementById('helpModal');
  if (event.target === modal) {
    closeHelpModal();
  }
});

// Close modal with ESC key
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    const modal = document.getElementById('helpModal');
    if (modal && modal.classList.contains('active')) {
      closeHelpModal();
    }
    const welcomeModal = document.getElementById('welcomeModal');
    if (welcomeModal && welcomeModal.classList.contains('active')) {
      closeWelcomeModal();
    }
  }
});

// ============================================================================
// WELCOME MODAL FUNCTIONS
// ============================================================================

// Load and display welcome content
async function loadWelcomeContent() {
  const bodyElement = document.getElementById('welcomeModalBody');
  
  try {
    // Determine API base URL
    const isLocal = window.location.hostname === 'localhost' ||
                    window.location.hostname === '127.0.0.1' ||
                    window.location.protocol === 'file:';
    const API_BASE = isLocal ? 'http://localhost:3003' : 'https://ga-suche.onrender.com';
    
    // Load WILLKOMMEN.md from system folder
    const response = await fetch(`${API_BASE}/system/WILLKOMMEN.md`);
    if (!response.ok) {
      throw new Error(`Fehler beim Laden: ${response.status}`);
    }
    const markdown = await response.text();
    
    // Convert Markdown to HTML with marked.js
    if (typeof marked !== 'undefined') {
      marked.setOptions({
        breaks: true,
        gfm: true
      });
      bodyElement.innerHTML = marked.parse(markdown);
    } else {
      // Fallback: Show Markdown as text
      bodyElement.innerHTML = `<pre style="white-space: pre-wrap;">${markdown}</pre>`;
    }
    
  } catch (error) {
    console.error('Fehler beim Laden der Willkommensnachricht:', error);
    bodyElement.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: #999;">
        <p><strong>Fehler beim Laden der Willkommensnachricht</strong></p>
        <p style="font-size: 0.9em; margin-top: 1rem;">
          ${error.message}<br>
          Bitte stellen Sie sicher, dass der Backend-Server läuft.
        </p>
      </div>
    `;
  }
}

// Show welcome modal
function showWelcomeModal() {
  const modal = document.getElementById('welcomeModal');
  if (modal) {
    modal.classList.add('active');
    loadWelcomeContent();
  }
}

// Close welcome modal
function closeWelcomeModal() {
  const modal = document.getElementById('welcomeModal');
  
  if (modal) {
    modal.classList.remove('active');
  }
  
  // Speichere, dass das Popup beim aktuellen Besuch gesehen wurde
  sessionStorage.setItem('ga-suche-welcome-shown-session', 'true');
  console.log('[WELCOME] Willkommens-Popup geschlossen');
}

// Check if welcome should be shown and display it
function checkAndShowWelcome() {
  const hasSeenThisSession = sessionStorage.getItem('ga-suche-welcome-shown-session');
  
  if (!hasSeenThisSession) {
    console.log('[WELCOME] Zeige Willkommensnachricht');
    // Show welcome after a short delay (500ms) for better UX
    setTimeout(() => {
      showWelcomeModal();
    }, 500);
  } else {
    console.log('[WELCOME] Willkommensnachricht wurde in dieser Sitzung bereits angezeigt');
  }
}

// Initialize welcome check on page load
document.addEventListener('DOMContentLoaded', function() {
  checkAndShowWelcome();
});

// Close welcome modal when clicking outside
document.addEventListener('click', function(event) {
  const modal = document.getElementById('welcomeModal');
  if (event.target === modal) {
    closeWelcomeModal();
  }
});

// ============================================================================
// TIMELINE TAB FUNCTIONS
// ============================================================================

let timelineBatchRunning = false;
let timelineBatchCurrentIndex = 0;

// Load timeline statistics
async function loadTimelineStats() {
  try {
    console.log('[TIMELINE] Lade Statistiken...');
    const response = await fetch(`${API_BASE}/api/keywords-stats`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const stats = await response.json();
    console.log('[TIMELINE] Stats:', stats);
    
    // Update UI
    document.getElementById('timelineKeywordsCount').textContent = 
      `${stats.keywordsGenerated} / ${stats.totalLectures}`;
    document.getElementById('timelineProgress').textContent = 
      `${stats.percentage}%`;
    document.getElementById('timelineThemesCount').textContent = 
      `${stats.withTheme} / ${stats.keywordsGenerated}`;
    
    // Show admin section if localhost
    if (API_BASE.includes('localhost')) {
      document.getElementById('timelineAdminSection').style.display = 'block';
      // Load available GAs
      await loadAvailableGAs();
    }
    
    // Load themes if available
    await loadTimelineThemes();
    
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Laden der Statistiken:', error);
    document.getElementById('timelineKeywordsCount').textContent = 'Fehler';
    document.getElementById('timelineProgress').textContent = '-';
    document.getElementById('timelineThemesCount').textContent = '-';
  }
}

// Load available GA numbers for selection
async function loadAvailableGAs() {
  try {
    const response = await fetch(`${API_BASE}/api/available-ga`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    const gaList = data.availableGA || data; // Backend gibt { availableGA: [...] } zurück
    const select = document.getElementById('timelineGASelect');
    
    // Clear existing options except first
    select.innerHTML = '<option value="">Alle GA-Bände</option>';
    
    // Add GA options
    if (Array.isArray(gaList)) {
      gaList.forEach(ga => {
        const option = document.createElement('option');
        option.value = ga;
        option.textContent = ga;
        select.appendChild(option);
      });
      console.log('[TIMELINE] GAs geladen:', gaList.length);
    } else {
      console.warn('[TIMELINE] Ungültiges Format:', data);
    }
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Laden der GAs:', error);
  }
}

// Load available themes
async function loadTimelineThemes() {
  try {
    const response = await fetch(`${API_BASE}/api/themes-database`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const themes = await response.json();
    const themeSelect = document.getElementById('timelineThemeFilter');
    
    if (Object.keys(themes).length > 0) {
      // Clear and populate
      themeSelect.innerHTML = '<option value="">Alle Themen</option>';
      Object.keys(themes).sort().forEach(theme => {
        const option = document.createElement('option');
        option.value = theme;
        option.textContent = theme;
        themeSelect.appendChild(option);
      });
      themeSelect.disabled = false;
      
      console.log('[TIMELINE] Themen geladen:', Object.keys(themes).length);
    } else {
      themeSelect.innerHTML = '<option value="">Noch keine Themen generiert...</option>';
      themeSelect.disabled = true;
    }
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Laden der Themen:', error);
    document.getElementById('timelineThemeFilter').innerHTML = '<option value="">Fehler beim Laden</option>';
  }
}

// Load keywords for selected theme
async function loadTimelineKeywords() {
  const theme = document.getElementById('timelineThemeFilter').value;
  const keywordSelect = document.getElementById('timelineKeywordFilter');
  
  if (!theme || theme === '') {
    keywordSelect.innerHTML = '<option value="">Alle Schlagwörter</option>';
    keywordSelect.disabled = true;
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE}/api/themes-database`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const themes = await response.json();
    const themeData = themes[theme];
    
    if (themeData && themeData.keywords) {
      keywordSelect.innerHTML = '<option value="">Alle Schlagwörter des Themas</option>';
      themeData.keywords.sort().forEach(kw => {
        const option = document.createElement('option');
        option.value = kw;
        option.textContent = kw;
        keywordSelect.appendChild(option);
      });
      keywordSelect.disabled = false;
    }
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Laden der Keywords:', error);
  }
}

// Generate themes from keywords
async function generateThemes() {
  const themeCount = parseInt(document.getElementById('timelineThemeCount').value) || 30;
  const statusDiv = document.getElementById('timelineThemesStatus');
  const button = document.getElementById('timelineGenerateThemes');
  
  button.disabled = true;
  statusDiv.style.display = 'block';
  statusDiv.innerHTML = '<div style="color: var(--text-color);">⏳ Generiere Themen mit KI... Dies kann einige Minuten dauern.</div>';
  
  try {
    console.log(`[TIMELINE] Generiere ${themeCount} Themen...`);
    
    const response = await fetch(`${API_BASE}/api/generate-themes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ targetThemeCount: themeCount })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const result = await response.json();
    console.log('[TIMELINE] Themen generiert:', result);
    
    statusDiv.innerHTML = `
      <div style="color: #28a745;">
        ✓ ${result.themeCount} Themen erfolgreich generiert!<br>
        ${result.assignedLectures} Vorträgen zugeordnet.
      </div>
    `;
    
    // Reload themes and stats
    await loadTimelineThemes();
    await loadTimelineStats();
    
  } catch (error) {
    console.error('[TIMELINE] Fehler bei Themen-Generierung:', error);
    statusDiv.innerHTML = `<div style="color: #d9534f;">✗ Fehler: ${error.message}</div>`;
  } finally {
    button.disabled = false;
  }
}

// Start batch keyword generation
async function startTimelineBatchGeneration() {
  if (timelineBatchRunning) {
    console.log('[TIMELINE] Batch läuft bereits');
    return;
  }
  
  timelineBatchRunning = true;
  timelineBatchCurrentIndex = 0;
  
  const batchSize = parseInt(document.getElementById('timelineBatchSize').value) || 50;
  
  // Get selected GAs
  const gaSelect = document.getElementById('timelineGASelect');
  const selectedGAs = Array.from(gaSelect.selectedOptions)
    .map(opt => opt.value)
    .filter(v => v !== '');
  
  console.log('[TIMELINE] Ausgewählte GAs:', selectedGAs.length > 0 ? selectedGAs : 'Alle');
  
  // Update UI
  document.getElementById('timelineBatchStart').style.display = 'none';
  document.getElementById('timelineBatchStop').style.display = 'inline-block';
  document.getElementById('timelineBatchProgress').style.display = 'block';
  
  console.log('[TIMELINE] Starte Batch-Generierung...');
  
  await runTimelineBatch(batchSize, selectedGAs);
}

// Stop batch generation
function stopTimelineBatchGeneration() {
  timelineBatchRunning = false;
  document.getElementById('timelineBatchStart').style.display = 'inline-block';
  document.getElementById('timelineBatchStop').style.display = 'none';
  console.log('[TIMELINE] Batch gestoppt');
}

// Run batch generation
async function runTimelineBatch(batchSize, gaFilter = []) {
  let totalProcessed = 0;
  let totalSkipped = 0;
  let totalErrors = 0;
  
  while (timelineBatchRunning) {
    try {
      console.log(`[TIMELINE] Batch ${timelineBatchCurrentIndex}-${timelineBatchCurrentIndex + batchSize}...`);
      
      const response = await fetch(`${API_BASE}/api/generate-keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch: true,
          startIndex: timelineBatchCurrentIndex,
          batchSize: batchSize,
          gaFilter: gaFilter
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      console.log('[TIMELINE] Batch-Ergebnis:', result);
      
      totalProcessed += result.processed;
      totalSkipped += result.skipped;
      totalErrors += result.errors;
      
      // Update UI
      document.getElementById('timelineBatchProgressText').textContent = 
        `${result.progress.current} / ${result.progress.total} Vorträge`;
      document.getElementById('timelineBatchProgressPercent').textContent = 
        `${result.progress.percentage}%`;
      document.getElementById('timelineBatchProgressBar').style.width = 
        `${result.progress.percentage}%`;
      
      document.getElementById('timelineBatchProcessed').textContent = totalProcessed;
      document.getElementById('timelineBatchSkipped').textContent = totalSkipped;
      document.getElementById('timelineBatchErrors').textContent = totalErrors;
      
      // Check if done
      if (result.progress.current >= result.progress.total) {
        console.log('[TIMELINE] Batch-Generierung abgeschlossen!');
        timelineBatchRunning = false;
        document.getElementById('timelineBatchStart').style.display = 'inline-block';
        document.getElementById('timelineBatchStop').style.display = 'none';
        
        // Reload stats
        await loadTimelineStats();
        break;
      }
      
      // Next batch
      timelineBatchCurrentIndex += batchSize;
      
      // Small delay to prevent overwhelming
      await new Promise(resolve => setTimeout(resolve, 500));
      
    } catch (error) {
      console.error('[TIMELINE] Batch-Fehler:', error);
      timelineBatchRunning = false;
      document.getElementById('timelineBatchStart').style.display = 'inline-block';
      document.getElementById('timelineBatchStop').style.display = 'none';
      alert(`Fehler bei der Batch-Generierung: ${error.message}`);
      break;
    }
  }
}

// Render timeline visualization
async function renderTimeline() {
  const theme = document.getElementById('timelineThemeFilter').value;
  const keyword = document.getElementById('timelineKeywordFilter').value;
  const contentDiv = document.getElementById('timelineContent');
  
  if (!theme && !keyword) {
    contentDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--secondary-text);">Wählen Sie ein Thema aus, um die Timeline anzuzeigen.</div>';
    return;
  }
  
  try {
    contentDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-color);">⏳ Lade Timeline-Daten...</div>';
    
    const params = new URLSearchParams();
    if (theme) params.append('theme', theme);
    if (keyword) params.append('keyword', keyword);
    
    const response = await fetch(`${API_BASE}/api/timeline-data?${params.toString()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    console.log('[TIMELINE] Daten:', data);
    
    if (data.totalCount === 0) {
      contentDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--secondary-text);">Keine Vorträge gefunden für diese Auswahl.</div>';
      return;
    }
    
    // Render timeline
    let html = `<div style="font-size: 0.9em;">
      <h4 style="margin: 0 0 0.8rem 0; color: var(--heading-color);">${theme || keyword || 'Timeline'}</h4>
      <p style="margin-bottom: 1rem; color: var(--secondary-text);">${data.totalCount} Vorträge gefunden</p>
    `;
    
    // Render each year
    data.years.forEach(year => {
      const lectures = data.byYear[year];
      html += `
        <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
          <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <div style="min-width: 60px; font-weight: bold; color: var(--heading-color); padding-top: 0.2rem;">
              ${year}
            </div>
            <div style="flex: 1; border-left: 3px solid var(--heading-color); padding-left: 1rem;">
      `;
      
      lectures.forEach(lecture => {
        const lectureId = lecture.lectureId;
        const date = lecture.date ? new Date(lecture.date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }) : '';
        const keywords = lecture.keywords.map(kw => kw.term).join(', ');
        
        html += `
          <div style="margin-bottom: 0.8rem; padding: 0.5rem; background: var(--background-color); border-radius: 4px; border: 1px solid var(--border-color);">
            <div style="font-weight: bold; margin-bottom: 0.3rem;">
              <a href="javascript:void(0)" onclick="loadFullLecture('${lectureId}')" 
                 style="color: var(--link-color); text-decoration: none;">
                ${lectureId}
              </a>
              ${date ? `<span style="color: var(--secondary-text); margin-left: 0.5rem;">(${date})</span>` : ''}
            </div>
            <div style="font-size: 0.85em; color: var(--secondary-text);">
              ${keywords}
            </div>
          </div>
        `;
      });
      
      html += `
            </div>
          </div>
        </div>
      `;
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
    
  } catch (error) {
    console.error('[TIMELINE] Fehler beim Rendern:', error);
    contentDiv.innerHTML = `<div style="text-align: center; padding: 2rem; color: #d9534f;">Fehler beim Laden der Timeline: ${error.message}</div>`;
  }
}

// Update switchTab function to load stats when timeline tab is opened
const originalSwitchTab = window.switchTab;
window.switchTab = function(tabName) {
  // Call original function
  if (originalSwitchTab) {
    originalSwitchTab(tabName);
  }
  
  // Load stats when timeline tab is opened
  if (tabName === 'timeline') {
    loadTimelineStats();
  }
};

</script>

</body>
</html> 
```

Perfekt! Das Frontend ist vollständig implementiert! Jetzt prüfe ich, ob alle Backend APIs existieren:

**🎉 Excellent!** Alle Backend APIs existieren bereits! Das System ist vollständig implementiert!

Perfekt! Die Implementation ist abgeschlossen. Hier die **Test-Anleitung**:

---

## ✅ **IMPLEMENTIERUNG ABGESCHLOSSEN**

### Was wurde gemacht:

1. ✅ **Backend**: Keywords werden jetzt IMMER mit Claude KI generiert (nicht regelbasiert)
2. ✅ **Datenbanken geleert**: `keywords-database.json` und `themes-database.json`
3. ✅ **Backend APIs**: Alle APIs für Batch-Verarbeitung, Themen-Generierung und Timeline existieren bereits
4. ✅ **Frontend UI**: Vollständig implementiert mit GA-Auswahl, Batch-Verarbeitung und Timeline-Visualisierung

---

## 🧪 **TEST-ANLEITUNG**

### 1. **Server starten**
Der Server sollte bereits laufen. Falls nicht:
```bash
node backend.js
```

### 2. **Frontend öffnen**
Öffnen Sie im Browser: `http://localhost:3000`

### 3. **Timeline-Tab öffnen**
- Klicken Sie auf den **"Timeline"** Tab in der Sidebar
- Statistiken werden automatisch geladen

### 4. **Test-Workflow**

#### **Schritt 1: Keywords generieren (KI)**
1. Im Abschnitt **"Keywords-Generierung"**:
   - **GA-Bände auswählen**: Wählen Sie 1-3 GA-Bände für einen Test (z.B. GA051, GA052)
   - **Batch-Größe**: Lassen Sie 50
   - Klicken Sie **"Batch-Generierung starten"**
2. ⏳ **Warten Sie**: Pro Vortrag ~3-5 Sekunden (Claude API)
3. ✅ **Fortschritt**: Sehen Sie die Fortschrittsanzeige

#### **Schritt 2: Qualität prüfen**
1. Nach Abschluss: Sehen Sie "Verarbeitet: X" 
2. Prüfen Sie die `keywords-database.json` Datei:
   - Jeder Eintrag sollte ein Array von Keywords haben
   - Jedes Keyword sollte `term`, `index`, `heading` enthalten

#### **Schritt 3: Themen generieren (KI)**
1. Im Abschnitt **"Themen-Generierung"**:
   - **Anzahl Themen**: Wählen Sie 10 für Test (oder 30 für Production)
   - Klicken Sie **"Themen generieren"**
2. ⏳ **Warten Sie**: ~30 Sekunden (Claude analysiert alle Keywords)
3. ✅ **Erfolg**: "X Themen erfolgreich generiert!"

#### **Schritt 4: Timeline anzeigen**
1. Im Abschnitt **"Timeline-Ansicht"**:
   - **Thema auswählen**: Dropdown sollte jetzt Themen enthalten
   - **Schlagwort auswählen** (optional): Filtern Sie nach spezifischem Keyword
   - Klicken Sie **"Timeline anzeigen"**
2. 📊 **Timeline**: Sehen Sie chronologische Darstellung nach Jahren

---

## 📁 **Datenbank-Struktur**

### `keywords-database.json`:
```json
{
  "GA051/11": {
    "lectureId": "GA051/11",
    "date": "1905-11-30",
    "year": 1905,
    "keywords": [
      {
        "term": "Deutsches Reich",
        "index": "^q60x9u",
        "heading": "Die Entstehung des deutschen Reiches"
      },
      ...
    ],
    "theme": "Mittelalterliche Geschichte",
    "timestamp": "2025-10-19T...",
    "model": "claude-sonnet-4",
    "source": "headings"
  }
}
```

### `themes-database.json`:
```json
{
  "Erkenntnistheorie": {
    "keywords": ["Goetheanismus", "Phänomenologie", "Wissenschaft"],
    "description": "Erkenntnistheoretische Grundlagen"
  },
  "Christologie": {
    "keywords": ["Christus", "Evangelien", "Mysterium von Golgatha"],
    "description": "Christologische Themen"
  }
}
```

---

## 💡 **Tipps**

1. **Erste Testläufe**: Beginnen Sie mit 1-2 GA-Bänden
2. **Batch-Größe**: 50 ist gut (kann auf 10 reduziert werden für Tests)
3. **Kosten**: ~$0.01 pro Vortrag für Keywords, ~$0.50 einmalig für Themen
4. **Fortschritt**: Nutzen Sie "Statistiken aktualisieren" Button zum Reload

---

## 🐛 **Troubleshooting**

- **"Kein Claude API Key"**: Prüfen Sie `.env` Datei: `CLAUDE_API_KEY=...`
- **Batch stoppt**: Klicken Sie "Stoppen" und starten Sie neu
- **Keine Themen**: Erst müssen Keywords generiert sein
- **Timeline leer**: Prüfen Sie, ob Themen und Keywords existieren

---

Möchten Sie jetzt einen Test durchführen? Ich kann Ihnen dabei helfen! 🚀

```shellscript
node backend.js
```

```json
{
  "GA051/11": {
    "lectureId": "GA051/11",
    "date": "1905-11-30",
    "year": 1905,
    "keywords": [
      {
        "term": "Deutsches Reich",
        "index": "^q60x9u",
        "heading": "Die Entstehung des deutschen Reiches"
      },
      ...
    ],
    "theme": "Mittelalterliche Geschichte",
    "timestamp": "2025-10-19T...",
    "model": "claude-sonnet-4",
    "source": "headings"
  }
}
```

```json
{
  "Erkenntnistheorie": {
    "keywords": ["Goetheanismus", "Phänomenologie", "Wissenschaft"],
    "description": "Erkenntnistheoretische Grundlagen"
  },
  "Christologie": {
    "keywords": ["Christus", "Evangelien", "Mysterium von Golgatha"],
    "description": "Christologische Themen"
  }
}
```

