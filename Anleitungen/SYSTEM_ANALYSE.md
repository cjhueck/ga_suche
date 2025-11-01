# GA-Suche System - Vollständige Systemanalyse

**Stand:** 26. Oktober 2025  
**Version:** V3 (Keywords mit flexiblem Budget)

---

## 📋 INHALTSVERZEICHNIS

1. [Systemübersicht](#systemübersicht)
2. [Architektur](#architektur)
3. [Datenbanken & Dateien](#datenbanken--dateien)
4. [Tabs & Funktionen](#tabs--funktionen)
5. [Datenflüsse](#datenflüsse)
6. [KI-Provider System](#ki-provider-system)
7. [Backup-System](#backup-system)

---

## 🏗️ SYSTEMÜBERSICHT

### Zweck
Durchsuchbare Datenbank der Rudolf Steiner Gesamtausgabe (GA) mit:
- Volltext-Suche in Vorträgen
- KI-generierte Zusammenfassungen
- Thematische Suche
- Keyword-Extraktion und Timeline-Visualisierung
- Thematische Cluster-Organisation

### Tech-Stack
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Backend:** Node.js + Express.js (Port 3003)
- **KI-Provider:** OpenAI (GPT-4o), Claude (Sonnet 4), Gemini (2.0 Flash)
- **Datenformat:** JSON-Datenbanken (keine SQL)
- **Deployment:** Lokal + Online (Render.com)

---

## 🔧 ARCHITEKTUR

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (index.html)                     │
│  ┌────────┬────────┬────────┬──────────┬──────────┬────────┐│
│  │ Suche  │ Texte  │ Themen │ Timeline │ Keywords │ Index  ││
│  └────────┴────────┴────────┴──────────┴──────────┴────────┘│
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (backend.js - Port 3003)                │
│  ┌──────────────┬─────────────────┬───────────────────────┐ │
│  │ API Routes   │ LLM Providers   │ Database Management   │ │
│  └──────────────┴─────────────────┴───────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   DATENBANKEN (JSON)                         │
│  ┌─────────────────┬──────────────────┬──────────────────┐  │
│  │ fullLectures    │ summary-database │ keywords-database│  │
│  │ (Volltexte)     │ (Summaries+TOC)  │ (KW+Themen)      │  │
│  └─────────────────┴──────────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 DATENBANKEN & DATEIEN

### Primäre Datenquellen

#### 1. **steiner-full-lectures-051-053.json**
- **Typ:** Volltexte (Read-Only)
- **Inhalt:** Komplette Vorträge mit Absatz-Indizes
- **Struktur:**
  ```json
  {
    "lectures": [
      {
        "ID": "GA051/1",
        "fileName": "GA051/1 - Titel",
        "gaNumber": "GA051",
        "lectureNumber": "1",
        "title": "Vortragstitel",
        "date": "1905-01-23",
        "location": "Berlin",
        "paragraphs": [
          {
            "index": "^abc123",
            "content": "Absatztext..."
          }
        ],
        "headings": [
          {
            "id": "^abc123",
            "text": "Überschrift",
            "level": 3
          }
        ]
      }
    ]
  }
  ```
- **Geladen:** Beim Server-Start in `fullLectures` (im RAM)
- **Verwendet von:** Alle Such- und Anzeige-Funktionen

---

### Generierte Datenbanken (Schreibzugriff)

#### 2. **summary-database.json**
- **Typ:** KI-generierte Zusammenfassungen
- **Generiert durch:** Tab "Texte" → Buttons "Übersicht" / "batch" / "TOC&KW neu"
- **Struktur:**
  ```json
  {
    "GA051/1": {
      "summary": "KI-Zusammenfassung (100-150 Wörter)",
      "headings": [
        {
          "index": "^abc123",
          "text": "H3 Überschrift",
          "level": "h3"
        }
      ],
      "tableOfContents": [
        {
          "heading": "H3 Überschrift",
          "description": "20-30 Wörter Inhaltsbeschreibung",
          "index": "^abc123"
        }
      ],
      "lectureKeywords": [
        {
          "term": "Keyword",
          "index": "^abc123",
          "confidence": 0.95
        }
      ],
      "version": "v2",
      "timestamp": "2025-10-26T..."
    }
  }
  ```
- **Versionen:**
  - **V1:** Nur `summary` + `headings`
  - **V2:** + `tableOfContents` + `lectureKeywords`
- **Angezeigt in:** 
  - Tab "Texte" (Keywords unter jedem Vortrag)
  - Viewer (TOC im Summary-Panel rechts)

#### 3. **keywords-database.json**
- **Typ:** Strukturierte Keywords mit Metadaten
- **Generiert durch:** 
  - Tab "Texte" → "TOC&KW neu" (V3 flexible)
  - Tab "Texte" → "batch" (nur fehlende Daten)
  - Tab "Keywords" → "Batch starten (V2)"
- **Struktur:**
  ```json
  {
    "GA051/1": {
      "lectureId": "GA051/1",
      "date": "1905-01-23",
      "year": 1905,
      "gaVolume": "GA051",
      "summary": "Zusammenfassung...",
      "keywords": [
        {
          "term": "Theosophie",
          "index": "^abc123",
          "heading": "H3-Überschrift wo das Keyword vorkommt",
          "level": "h3",
          "matchType": "existing-exact",
          "matchedExisting": "Theosophie",
          "confidence": 0.95
        }
      ],
      "generated": "2025-10-26T...",
      "generationMethod": "flexible-v3-auto",
      "maxNewKeywordsBudget": 4
    }
  }
  ```
- **Enthält:** ~2.673 Vorträge (~173.152 Zeilen)
- **Angezeigt in:** 
  - Tab "Timeline" → Dropdown "Schlagwort auswählen"
  - Tab "Timeline" → Ergebnisfenster (chronologische Liste)

#### 4. **themes-database.json** ⭐ AKTIV
- **Typ:** Thematische Cluster von Keywords
- **Generiert durch:** Tab "Keywords" → "Themenbereiche generieren"
- **Struktur:**
  ```json
  {
    "Anthroposophie & Theosophie": {
      "description": "Grundlagen und Methodik...",
      "keywords": [
        "Anthroposophie",
        "Theosophie",
        "Anthroposophische Methode",
        ...
      ]
    }
  }
  ```
- **Verwendet von:** 
  - Tab "Timeline" → Dropdown "Thema auswählen"
  - Automatische Themen-Zuordnung bei Keyword-Auswahl

#### 5. **thematic-clusters.json** ⚠️ LEGACY
- **Status:** Veraltet, nur Fallback-Kompatibilität
- **Verwendet:** Nur wenn `themes-database.json` nicht existiert
- **Kann ignoriert werden**

#### 6. **thematic-search-database.json**
- **Typ:** Cache für thematische Suchanfragen
- **Generiert durch:** Tab "Themen" → "Suche starten"
- **Struktur:**
  ```json
  {
    "query|depth|limit|gaFilter": {
      "query": "Wie entwickelt sich das Ich-Bewusstsein?",
      "content": "KI-generierte thematische Analyse...",
      "sources": [...],
      "timestamp": "2025-10-26T..."
    }
  }
  ```
- **Cache-Key Format:** `{query}|{depth}|{limit}|{gaFilter}`

#### 7. **summary-keywords-database.json**
- **Status:** Veraltet - Keywords jetzt in `summary-database.json`
- **Wird nicht mehr aktiv verwendet**

#### 8. **themes-keywords-template.json**
- **Typ:** Vordefiniertes Vokabular (Seed-Keywords)
- **Struktur:**
  ```json
  {
    "metadata": {
      "name": "Anthroposophie Keywords Template",
      "version": "2.0",
      "confidenceThreshold": 0.6,
      "totalKeywords": 560
    },
    "themes": [
      {
        "name": "Anthroposophie & Theosophie",
        "keywords": ["Anthroposophie", "Theosophie", ...]
      }
    ]
  }
  ```
- **Verwendet von:** V2/V3 Keyword-Generierung als Basis-Vokabular
- **Quelle:** Manuell kuratiert aus "Keywords - merged.md"

---

### Hilfsdateien

- **concepts.json / concepts-thematic-search.json:** Schlagwort-Index (Legacy)
- **synonyms.json:** Synonym-Expansion für Suche
- **query-log.json:** Tracking von Suchanfragen
- **timeline-cache-database.json:** Cache für Timeline-KI-Analysen
- **context-indices.json:** Kontext-Indizes für bessere Suche
- **marked-words.json:** Markierte fehlerhafte Wörter (Rechtsklick-Funktion)

---

## 📑 TABS & FUNKTIONEN

### Tab 1: **SUCHE** (Keyword-Search)

**Funktion:** Volltext-Suche in allen Vorträgen

**UI-Elemente:**
- 2 Suchfelder: `word1`, `word2` (optional)
- Phrase-Suche: Text in "Anführungszeichen"
- Filter: Jahre (1882-1925), GA-Bände, Relevanz (hoch/mittel/niedrig)

**Workflow:**
1. User gibt Suchwörter ein
2. Button "Suche starten" → `performKeywordSearch()`
3. API: `POST /api/fulltext-search`
4. Backend durchsucht `fullLectures` (im RAM)
5. Relevanz-Scoring (Keyword-Nähe, Häufigkeit)
6. **Ergebnisanzeige (links):** Chronologische Timeline
   - Jahr (links) | Vortragstitel mit Snippets (rechts)
   - Suchbegriffe sind highlighted (`<mark>`)
7. **Click auf Snippet:** Öffnet Vortrag im Viewer (rechts)
   - Absatz wird gehighlighted
   - Summary-Panel (rechts) öffnet sich automatisch

**Datenfluss:**
```
User Input → API → fullLectures (RAM) → Relevanz-Scoring → Timeline-View
```

---

### Tab 2: **TEXTE** (GA-Übersichten)

**Funktion:** Browsing durch GA-Bände mit Zusammenfassungen

**UI-Elemente:**
- Dropdown: GA-Band auswählen
- Buttons: "batch", "batch all"
- Toggle: "nur Titel" / "mit Schlagwörtern"

**Workflow 1: GA-Übersicht anzeigen**
1. User wählt GA-Band im Dropdown
2. → `openGAOverview(gaNumber)`
3. API: `GET /api/ga-overview/{gaNumber}`
4. Backend: Lädt Vorträge aus `fullLectures`, ergänzt mit `summary-database.json`
5. **Anzeige (links):**
   - Liste aller Vorträge mit Titel, Datum, Ort
   - Darunter: V2-Keywords als klickbare Links
6. **Click auf Keyword-Link:** → Tab "Timeline" mit diesem Keyword

**Workflow 2: Vortrag öffnen**
1. Click auf Vortragstitel
2. → `showLectureFromOverview(lectureId)`
3. API: `GET /api/full-lecture/{ga}/{num}`
4. API: `GET /api/check-summary/{ga}/{num}` (prüft Summary)
5. **Anzeige (rechts - Main Viewer):**
   - **Wenn Summary vorhanden:** Übersicht mit H3/H4 + TOC
   - **Wenn keine Summary:** Original-Text
6. **Summary-Panel (rechts):** TOC mit klickbaren Überschriften

**Workflow 3: Buttons im Viewer**

**Button "Übersicht":**
- Falls keine Summary: Generiert neue Summary (V2)
- Falls Summary vorhanden: Zeigt Summary-View
- Toggle H4-Überschriften ein/aus

**Button "TOC&KW neu":** ⭐ NEU
- API: `POST /api/summarize-lecture` mit `forceRegenerate: true`
- **Verhalten:**
  - Summary + Headings: **BEHALTEN**
  - TOC: **NEU generieren** (KI)
  - Keywords: **NEU generieren** (V3 flexible, Budget: 4 neue KW)
- Speichert in **BEIDEN** Datenbanken:
  - `summary-database.json` (für Anzeige im Texte-Tab)
  - `keywords-database.json` (für Timeline-Tab)

**Workflow 4: Batch-Verarbeitung**

**Button "batch":** (nur lokal sichtbar)
- Generiert Summary+TOC+Keywords für **fehlende** Vorträge im aktuellen GA-Band
- API: `POST /api/summarize-lecture` mit `forceRegenerate: false`
- **Verhalten:**
  - Prüft gegen `summary-database.json`
  - Überspringt Vorträge mit vollständigen Daten (Summary + TOC + Keywords)
  - Ergänzt nur fehlende Teile

**Button "batch all":** (nur lokal sichtbar)
- Wie "batch", aber für **alle** GA-Bände
- Parallele Verarbeitung (10 Threads)

**Datenfluss:**
```
GA-Auswahl → fullLectures + summary-database → Anzeige
Vortrag öffnen → /api/full-lecture → Viewer
TOC&KW neu → /api/summarize-lecture (force=true) → V3 Keywords
              ↓
        summary-database.json + keywords-database.json
```

---

### Tab 3: **THEMEN** (Thematische Suche)

**Funktion:** KI-gestützte thematische Textanalyse

**UI-Elemente:**
- Textarea: Freitext-Frage
- Filter: GA-Bände
- Liste: Zuletzt gesuchte Themen

**Workflow:**
1. User stellt Frage (z.B. "Wie entwickelt sich das Ich-Bewusstsein?")
2. Button "Suche starten" → `performThematicSearch()`
3. API: `POST /api/thematic-hybrid-search`
4. **Backend-Prozess:**
   - Prüft Cache (`thematic-search-database.json`)
   - Falls nicht cached:
     - Führt Volltext-Suche durch
     - Sendet Top-Ergebnisse an KI (Claude/OpenAI/Gemini)
     - KI erstellt thematische Analyse mit Quellenangaben
     - Speichert in Cache
5. **Anzeige (links):**
   - Thematische Analyse mit Markdown-Formatierung
   - GA-Referenzen als klickbare Links: `(GA051/1:abc123)`
6. **Click auf GA-Referenz:** Öffnet Vortrag + scrollt zu Absatz

**KI-Prompt-Struktur:**
- Identifiziere Suchwörter
- Vergleiche Textstellen
- Gliedere mit eigenen Überschriften
- Schreibe Fazit
- Liste weitere relevante Quellen

**Cache-Strategie:**
- Cache-Key: `{query}|7|100|{gaFilter}`
- Hybrid-Matching: Exact, Synonyme, Levenshtein, Keyword-Overlap
- Cache-Hit → Sofortige Anzeige
- Cache-Miss → KI-Generierung

**Datenfluss:**
```
Frage → thematic-search-database (Cache-Check)
  ├─ Hit: Cached Result → Anzeige
  └─ Miss: fullLectures → KI-Analyse → Cache → Anzeige
```

---

### Tab 4: **TIMELINE** (Chronologische Keyword-Visualisierung)

**Funktion:** Zeigt Vorträge chronologisch nach Thema/Keyword

**UI-Elemente:**
- Dropdown: "Thema auswählen" (themes-database)
- Dropdown: "Schlagwort auswählen" (keywords-database)
- Statistik: X Themen • Y Schlagwörter

**Workflow 1: Keyword auswählen**
1. User wählt Keyword im Dropdown
2. → `updateTimelineFilters()`
3. **Automatische Themen-Zuordnung:** ⭐ NEU
   - Sucht in `themes-database.json` nach Thema, das dieses Keyword enthält
   - Setzt "Thema auswählen" Dropdown automatisch
4. Lädt alle Vorträge mit diesem Keyword aus `keywords-database.json`
5. **Anzeige (unten - Results):**
   - Chronologische Timeline (Jahr links | Einträge rechts)
   - Format: `Datum | GA051/1 | H3-Überschrift`
   - H3-Keywords: **fett**, H4-Keywords: normal

**Workflow 2: Thema auswählen**
1. User wählt Thema im Dropdown
2. Keyword-Dropdown wird gefiltert (nur Keywords dieses Themas)
3. Anzeige aller Keywords des Themas chronologisch

**Workflow 3: Link im Ergebnisfenster klicken**
1. Click auf GA051/1 Link
2. → `showLecture(lectureId, targetIndex)`
3. Öffnet Vortrag im Viewer
4. **KEIN Highlighting** (nur im Timeline-Tab deaktiviert) ⭐ NEU

**Besonderheit:**
- Keywords im Timeline-Dropdown kommen aus `keywords-database.json`
- Diese enthält ~2.673 Vorträge (viele GA-Bände)
- Obwohl nur GA051-053 als Volltexte geladen sind!
- Grund: `keywords-database.json` wurde von einem System mit mehr Volltexten übernommen

**Datenfluss:**
```
Keyword-Auswahl → keywords-database.json
     ↓
Auto-Themen-Zuordnung (themes-database.json)
     ↓
Timeline-Anzeige (chronologisch)
     ↓
Click → Vortrag öffnen (OHNE Highlighting)
```

---

### Tab 5: **KEYWORDS** (Keyword-Generierung & Verwaltung)

**Funktion:** Batch-Generierung und Management von Keywords

**UI-Bereiche:**

#### 5.1 GA-Band Keyword-Generierung (V2)

**UI:**
- Button "GA-Bände laden"
- Checkboxen: GA-Bände auswählen
- Radio Buttons: KI-Provider (OpenAI/Claude/Gemini)
- Checkboxen: 
  - Bestehendes Vokabular verwenden
  - Synonyme konsolidieren
  - Bereits verarbeitete NEU verarbeiten (⚠️)
- Button "Batch starten (V2)"

**Workflow:**
1. User wählt GA-Bände + Provider
2. Button "Batch starten (V2)" → `startGABatchV2()`
3. API: `POST /api/generate-keywords-v2`
4. **Backend-Prozess:**
   - Lädt Template (`themes-keywords-template.json`)
   - Lädt bestehendes Vokabular (`keywords-database.json`)
   - Für jeden Vortrag:
     - Filtert H3/H4 Überschriften
     - Extrahiert Keywords via KI
     - Matching gegen Template (Confidence ≥ 0.6)
     - Max 2 Keywords pro Überschrift
     - Themen-Zuordnung
   - Konsolidiert Synonyme (optional)
5. **Speichert in:**
   - `keywords-database.json` (Haupt-Datenbank)
   - `summary-database.json` (sync für Side Panel)

**Keyword-Generierungs-Methoden:**

| Methode | Quelle | Budget | Verwendet von |
|---------|--------|--------|---------------|
| **V3 Flexible** | H3/H4 + Summary | 4 neue KW/Vortrag | "TOC&KW neu" Button |
| **V2 Template** | H3/H4 | 1-2 KW/Überschrift | "Batch starten (V2)" |
| **V1** | Summary | 10-12 KW | Veraltet |

#### 5.2 Themenbereiche erstellen

**Buttons:**
- "Themenbereiche generieren" → Erstellt ~30 Themen via KI
- "Bestehende laden" → Zeigt vorhandene Cluster
- "Cluster reorganisieren" → KI ordnet Keywords neu zu

**Workflow "Themenbereiche generieren":**
1. → `generateThematicClusters()`
2. API: `POST /api/themes/generate-clusters-from-seeds`
3. Backend: Lädt Seed-Keywords aus `themes-keywords-template.json`
4. KI (Claude) erstellt ~30 thematische Cluster
5. Speichert in `themes-database.json`
6. Zeigt Cluster-Übersicht im Viewer

#### 5.3 Manueller Themenbereich

**UI:**
- Input: Cluster-Name
- Textarea: Beschreibung
- Textarea: Keywords (eins pro Zeile)
- Button "Cluster hinzufügen"

**Workflow:**
1. User gibt Themenbereich-Daten ein
2. → `addManualCluster()`
3. API: `POST /api/themes/add-cluster`
4. Speichert in `themes-database.json`

#### 5.4 Keyword & Cluster Management

**Button "📝 Keywords bearbeiten":**
- Öffnet Modal
- **Funktionen:**
  - **Zusammenführen:** Quell-KW → Ziel-KW (keine Duplikate)
  - **Umbenennen:** Quell-KW → Neuer Name
  - **Löschen:** Quell-KW → (leer lassen)
  - **In Cluster verschieben:** Keyword → Anderer Themenbereich
- API: `POST /api/keywords/rename`
- Aktualisiert `keywords-database.json` + `themes-database.json`

**Button "🗂️ Cluster bearbeiten":**
- **Umbenennen:** Cluster-Name ändern
- **Zusammenführen:** 2 Cluster vereinen
- API: `POST /api/themes/rename-cluster`
- API: `POST /api/themes/merge-clusters`

#### 5.5 Top 100 Keywords

**Button "Top 100 anzeigen":**
- Analysiert `keywords-database.json`
- Zählt Vorkommen jedes Keywords
- Zeigt Top 100 im Viewer (sortiert nach Häufigkeit)

**Datenfluss:**
```
GA-Auswahl → /api/generate-keywords-v2
     ↓
  H3/H4 Überschriften + Template
     ↓
  KI-Extraktion + Matching
     ↓
  keywords-database.json + summary-database.json
```

---

### Tab 6: **INDEX** (Schlagwort-Verzeichnis)

**Funktion:** Alphabetisches Verzeichnis aller Schlagwörter

**UI-Elemente:**
- Alphabet-Navigation (A-Z, "Alle")
- Suchfeld
- Buttons (nur lokal):
  - "Schlagwort hinzufügen"
  - "Schlagwort löschen"
  - "Batch-Schlagwort-Generierung"

**Workflow 1: Schlagwort anzeigen**
1. User wählt Buchstabe
2. → `displayKeywords(letter)`
3. Lädt aus `concepts.json` / API
4. **Anzeige (links):** Alphabetische Liste
5. **Click auf Schlagwort:** → Keyword-Thematische Suche

**Workflow 2: Keyword-Thematische Suche**
1. Click auf Keyword → `performKeywordThematicSearch(keyword)`
2. API: `POST /api/keyword-thematic-search`
3. **Backend:**
   - Prüft Cache (`thematic-search-database.json`)
   - Falls nicht cached:
     - Volltext-Suche nach Keyword
     - Top 30 Ergebnisse → KI-Analyse (ausführlich)
     - Cache speichern
4. **Anzeige (links):** Thematische Analyse (wie Tab "Themen")

**Workflow 3: Schlagwort hinzufügen** (nur lokal)
1. User gibt Keyword ein
2. Button "Schlagwort hinzufügen" → `addNewKeyword()`
3. API: `POST /api/concepts-add`
4. **Backend:**
   - Volltext-Suche nach Keyword
   - KI-Analyse (ausführlich)
   - Erstellt Schlagwort-Eintrag
   - Speichert in `concepts.json`

**Datenfluss:**
```
Buchstabe → concepts.json → Alphabetische Liste
Click → /api/keyword-thematic-search → KI-Analyse → Anzeige
```

---

## 🔄 DATENFLÜSSE IM DETAIL

### Datenfluss 1: Summary-Generierung

```
┌─────────────────────────────────────────────────────────┐
│ TRIGGER: Button "Übersicht" / "TOC&KW neu" / "batch"    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ API: POST /api/summarize-lecture                        │
│   Body: { lectureId, forceRegenerate, preferredProvider}│
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ BACKEND: Lade Vortrag aus fullLectures (RAM)            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Prüfe summary-database.json                             │
│  ├─ forceRegenerate=false + V2 vollständig → Cache-Hit  │
│  └─ forceRegenerate=true ODER unvollständig → Generiere │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ KI-GENERIERUNG (OpenAI/Claude/Gemini)                   │
│  ├─ Summary (100-150 Wörter)                            │
│  ├─ H3/H4 Überschriften (6-12 H3, 1-4 H4/H3)           │
│  ├─ TOC (Beschreibung pro H3, 20-30 Wörter)            │
│  └─ Keywords (max 12, Haupt-Person/-Thema PFLICHT)     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Bei forceRegenerate: TOC + Keywords V3 NEU generieren   │
│  ├─ Lade Template (themes-keywords-template.json)       │
│  ├─ Lade Vokabular (keywords-database.json)             │
│  ├─ generateKeywordsFlexibleWithBudget()                │
│  │   ├─ Budget: 4 neue Keywords max                     │
│  │   ├─ Matching gegen Template (Confidence ≥ 0.6)      │
│  │   └─ Themen-Zuordnung                                │
│  └─ generateTableOfContents() via KI                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ SPEICHERN (mit Locking)                                 │
│  ├─ summary-database.json (Summary+TOC+lectureKeywords) │
│  └─ keywords-database.json (Keywords+Metadaten)         │
└─────────────────────────────────────────────────────────┘
```

---

### Datenfluss 2: Keyword-Generierung (V2 Batch)

```
┌─────────────────────────────────────────────────────────┐
│ TRIGGER: Tab "Keywords" → "Batch starten (V2)"          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ API: POST /api/generate-keywords-v2                     │
│   Body: { gaVolumes, useExistingVocab, ...Provider }    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ BACKEND: Lade Ressourcen                                │
│  ├─ Template: themes-keywords-template.json             │
│  ├─ Summary-DB: summary-database.json (für Headings)    │
│  └─ Keywords-DB: keywords-database.json (Vokabular)     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ FÜR JEDEN GA-BAND:                                      │
│   FÜR JEDEN VORTRAG (parallel, Concurrency: 5):        │
│     ├─ Filtere H3/H4 Überschriften                      │
│     ├─ KI-Extraktion (mit Template-Kontext)             │
│     ├─ Matching: Confidence ≥ 0.6                       │
│     ├─ Max 2 Keywords pro Überschrift                   │
│     ├─ Vokabular wächst iterativ                        │
│     └─ Synonym-Konsolidierung (optional)                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ SPEICHERN (mit Locking)                                 │
│  ├─ keywords-database.json (Keywords+Thema)             │
│  └─ summary-database.json (Sync: lectureKeywords)       │
└─────────────────────────────────────────────────────────┘
```

---

### Datenfluss 3: Timeline-Keyword-Navigation

```
┌─────────────────────────────────────────────────────────┐
│ TRIGGER: Tab "Texte" → Click auf Keyword-Link          │
│   Beispiel: "Kant" unter GA051/1                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ navigateToTimelineKeyword('Kant', 'GA051')              │
│  ├─ Speichert: timelineBackToGA = 'GA051'               │
│  └─ Speichert: timelinePendingKeyword = 'Kant'          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ switchTab('timeline')                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ renderTimeline()                                        │
│  ├─ Lädt themes-database.json                           │
│  ├─ Lädt keywords-database.json                         │
│  ├─ Befüllt Themen-Dropdown                             │
│  └─ Befüllt Keyword-Dropdown                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Setze Keyword-Dropdown = 'Kant'                         │
│   → updateTimelineFilters()                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ AUTO-THEMEN-ZUORDNUNG ⭐                                │
│  ├─ Sucht in themes-database.json                       │
│  ├─ Findet: "Philosophie" enthält "Kant"                │
│  └─ Setzt Themen-Dropdown = "Philosophie"               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ renderTimelineContent()                                 │
│  ├─ Filtert keywords-database.json nach "Kant"          │
│  ├─ Gruppiert nach Jahr                                 │
│  └─ Zeigt chronologische Timeline                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Button "← Zurück zu Texte" (visible)                    │
│   Click → switchTab('texte') + openGAOverview('GA051')  │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 KI-PROVIDER SYSTEM

### Provider-Abstraction (`llm-providers.js`)

**Verfügbare Provider:**
1. **OpenAI** (GPT-4o) - Standard für Keywords
2. **Claude** (Sonnet 4) - Standard für Summary/Themen
3. **Gemini** (2.0 Flash) - Fallback

**Provider-Auswahl:**
- **Automatisch:** `getProviderForTask(taskType)`
  - `taskType: 'summary'` → Claude bevorzugt
  - `taskType: 'keywords'` → OpenAI bevorzugt
- **Manuell:** User wählt im Keywords-Tab (Radio Buttons)
  - Wird verwendet von: "TOC&KW neu", "batch", "Batch starten (V2)"

**Fallback-Logik:**
```
Primärer Provider
  ↓ (Rate-Limited oder Fehler)
Sekundärer Provider
  ↓ (Rate-Limited oder Fehler)
Tertiärer Provider
  ↓ (Alle fehlgeschlagen)
Error
```

**Rate-Limit-Handling:**
- Provider-Status wird getrackt
- Bei Rate-Limit: Automatischer Wechsel zu nächstem Provider
- Status-Anzeige im Keywords-Tab (✅ / 🔴 / ❌)

---

## 💾 BACKUP-SYSTEM

### Automatische Backups

**Beim Server-Start:**
```javascript
createCodeBackup()           // backend.js
createHtmlBackup('index.html')
createHtmlBackup('keyword-manager-advanced.html')
```

**Beim Laden der Webseite:** (nur lokal)
```javascript
createAutoHtmlBackup()  // index.html
```

**Bei Datenbank-Schreibvorgängen:**
- Vor jedem Write: Automatisches Backup
- Funktionen: `createKeywordsBackup()`, `createSummaryBackup()`, etc.

### Backup-Verzeichnisse

```
ga_suche/backups/
  ├── keywords/    (keywords-database-*.json)
  ├── summary/     (summary-database-*.json)
  ├── themes/      (themes-database-*.json)
  ├── clusters/    (thematic-clusters-*.json)
  ├── code/        (backend-*.js)
  └── html/        (index-*.html, keyword-manager-advanced-*.html)
```

**Retention:** Letzte 10 Backups pro Datei

### Manuelles Backup (via Backup-Modal)

**UI:** Datenbank-Symbol (🗄️) im Header (nur lokal)

**Funktionen:**
1. **Backup erstellen:** Dropdown + Button "Neues Backup erstellen"
2. **Backups anzeigen:** Liste mit Timestamp + Dateigröße
3. **Wiederherstellen:** Button bei jedem Backup-Eintrag

**API-Endpunkte:**
- `POST /api/backups/create` (type: keywords/summary/themes/clusters/code/html/full)
- `GET /api/backups/list/:type`
- `POST /api/backups/restore` (backupName)

---

## 📈 WICHTIGE UNTERSCHEIDUNGEN

### "batch" vs "TOC&KW neu" vs "Batch starten (V2)"

| Button | Tab | forceRegenerate | Überspringt vollständige? | Generiert was? | API |
|--------|-----|-----------------|---------------------------|----------------|-----|
| **batch** | Texte | `false` | ✅ JA | Summary+TOC+KW (nur fehlende) | `/api/summarize-lecture` |
| **TOC&KW neu** | Texte | `true` | ❌ NEIN | TOC+KW IMMER neu (Summary behält) | `/api/summarize-lecture` |
| **Batch starten (V2)** | Keywords | N/A | Nach Checkbox | Nur Keywords (aus H3/H4) | `/api/generate-keywords-v2` |

### Summary-Versionen

| Version | Enthält | Generiert durch | Status |
|---------|---------|-----------------|--------|
| **V1** | Summary + Headings | Alte Version | Veraltet |
| **V2** | Summary + Headings + TOC + lectureKeywords | "Übersicht" Button (initial) | Standard |
| **V2 Enhanced** | V2 + V3 Keywords | "TOC&KW neu" Button | Empfohlen |

### Keyword-Quellen

**Im Tab "Texte":**
- Quelle: `summary-database.json` → Feld `lectureKeywords`
- Angezeigt unter jedem Vortrag

**Im Tab "Timeline":**
- Quelle: `keywords-database.json` → Alle Einträge
- Dropdown zeigt ~2.673 Vorträge (nicht nur GA051-053!)

**Synchronisation:**
- "TOC&KW neu" Button speichert in BEIDEN Datenbanken
- "Batch starten (V2)" speichert in BEIDEN Datenbanken
- → Konsistenz gewährleistet

---

## 🎯 HIGHLIGHTING-SYSTEM

### Standard-Verhalten
- Absätze werden mit `.highlighted-paragraph` Klasse markiert
- Gelb-orange Hintergrund + Border
- Automatisches Fade-Out nach 5 Sekunden

### Wo Highlighting aktiv ist:
✅ Tab "Suche" (Snippet-Clicks)  
✅ Tab "Texte" (Vortrag öffnen)  
✅ Tab "Themen" (GA-Referenz-Clicks)  
✅ Tab "Keywords" (Keyword-Thematische Suche)  
✅ Tab "Index" (Schlagwort-Clicks)  
❌ Tab "Timeline" ⭐ DEAKTIVIERT (seit letztem Update)

### Implementierung
```javascript
function isTimelineTabActive() {
  const activeTab = document.querySelector('.tab-content.active');
  return activeTab && activeTab.id === 'timeline-tab';
}

function addHighlightingWithAutoRemove(element) {
  if (element && !isTimelineTabActive()) {
    element.classList.add('highlighted-paragraph');
    // ... Auto-Remove nach 5s
  }
}
```

---

## 🗂️ DATEI-ÜBERSICHT

### Hauptdateien

| Datei | Zeilen | Funktion |
|-------|--------|----------|
| `index.html` | ~13.000 | Frontend (UI + JavaScript) |
| `backend.js` | ~10.263 | Node.js Server + API |
| `llm-providers.js` | - | KI-Provider Abstraktion |

### Datenbanken (JSON)

| Datei | Größe | Einträge | Generiert durch | Verwendet von |
|-------|-------|----------|-----------------|---------------|
| `summary-database.json` | 214k Zeilen | ~3.500 Vorträge | Tab "Texte" | Tab "Texte" (Anzeige) |
| `keywords-database.json` | 173k Zeilen | ~2.673 Vorträge | Tab "Texte"/"Keywords" | Tab "Timeline" |
| `themes-database.json` | ~850 Zeilen | ~30 Themen | Tab "Keywords" | Tab "Timeline" |
| `steiner-full-lectures-*.json` | - | GA051-053 | Extern | Alle Tabs (Lesen) |
| `thematic-search-database.json` | - | Cache | Tab "Themen" | Tab "Themen" |
| `themes-keywords-template.json` | - | ~560 Keywords | Manuell | V2/V3 Generation |

---

## 🔀 KRITISCHE WORKFLOWS

### Workflow: Keywords im Timeline-Tab anzeigen

**Voraussetzung:** Keywords müssen in `keywords-database.json` vorhanden sein

**Wie kommen Keywords dahin?**

1. **Methode 1: Einzelner Vortrag**
   - Tab "Texte" → Vortrag öffnen
   - Button "TOC&KW neu" (forceRegenerate=true)
   - → V3 Keywords generiert + gespeichert

2. **Methode 2: Batch für einen GA-Band**
   - Tab "Texte" → GA-Band auswählen
   - Button "batch" (forceRegenerate=false)
   - → Nur Vorträge ohne vollständige Daten werden verarbeitet

3. **Methode 3: Batch für mehrere GA-Bände**
   - Tab "Keywords" → GA-Bände auswählen
   - Button "Batch starten (V2)"
   - → V2 Template-basierte Keywords

**Ergebnis:** Keywords erscheinen in beiden Tabs:
- ✅ Tab "Texte": Unter jedem Vortrag (aus `summary-database.json`)
- ✅ Tab "Timeline": Im Dropdown + Timeline (aus `keywords-database.json`)

### Workflow: Thema zu Keyword finden

**Automatisch im Timeline-Tab:**
1. User wählt Keyword im Dropdown
2. System sucht in `themes-database.json`
3. Findet Thema das Keyword enthält
4. Setzt Themen-Dropdown automatisch

**Manuell im Keywords-Tab:**
- Themen werden bei Generierung automatisch zugeordnet
- Basiert auf Template-Struktur

---

## 🚨 WICHTIGE HINWEISE

### Lokale vs. Online-Umgebung

| Feature | Lokal | Online |
|---------|-------|--------|
| Keywords-Tab | ✅ Sichtbar | ❌ Versteckt |
| Batch-Buttons | ✅ Sichtbar | ❌ Versteckt |
| TOC&KW neu Button | ✅ Sichtbar | ❌ Versteckt |
| Backup-Modal | ✅ Verfügbar | ❌ Nicht verfügbar |
| Schlagwort hinzufügen | ✅ Verfügbar | ❌ Nicht verfügbar |

### Datenbank-Konsistenz

**Problem:** `summary-database.json` und `keywords-database.json` können inkonsistent werden

**Lösung:**
- Beide Datenbanken werden synchron aktualisiert
- Bei "TOC&KW neu": Schreibt in beide DBs
- Bei V2 Batch: Schreibt in beide DBs

**Prüfen:**
```javascript
// In summary-database.json:
lectureKeywords: [...]  // Angezeigt im Texte-Tab

// In keywords-database.json:
keywords: [...]  // Angezeigt im Timeline-Tab
```

### Performance-Optimierungen

**Keyword-Editor Modal:**
- Lädt 2.673+ Keywords on-demand (nicht beim Öffnen)
- Batch-Processing beim Befüllen (100er Batches)
- DocumentFragment für DOM-Performance

**Timeline-Rendering:**
- CSS Grid Layout (nicht JavaScript)
- Jahreszahlen werden dynamisch positioniert
- Lazy Loading von Vortragsinhalten

---

## 📚 API-ENDPUNKTE ÜBERSICHT

### Volltext-Suche
- `POST /api/fulltext-search` → Keyword-Suche
- `POST /api/thematic-hybrid-search` → Thematische Suche
- `POST /api/keyword-thematic-search` → Keyword-Thematische Suche

### Vorträge & Summaries
- `GET /api/full-lecture/{ga}/{num}` → Volltext laden
- `GET /api/ga-overview/{gaNumber}` → GA-Übersicht
- `POST /api/summarize-lecture` → Summary generieren/laden
- `GET /api/check-summary/{ga}/{num}` → Summary-Existenz prüfen

### Keywords
- `POST /api/generate-keywords-v2` → V2 Template-basierte Generierung
- `POST /api/generate-keywords-v3` → V3 Flexible Generierung
- `GET /api/keywords-database` → Keywords-DB laden
- `POST /api/keywords/rename` → Keyword umbenennen/zusammenführen
- `POST /api/keywords/move-to-cluster` → Keyword verschieben

### Themen/Cluster
- `POST /api/themes/generate-clusters-from-seeds` → Cluster generieren
- `GET /api/themes-database` → Themes-DB laden
- `POST /api/themes/add-cluster` → Manueller Cluster
- `POST /api/themes/rename-cluster` → Cluster umbenennen
- `POST /api/themes/merge-clusters` → Cluster zusammenführen
- `POST /api/themes/reorganize-clusters` → KI-Reorganisation

### Backups
- `POST /api/backups/create` → Backup erstellen
- `GET /api/backups/list/:type` → Backups auflisten
- `POST /api/backups/restore` → Backup wiederherstellen

### System
- `GET /debug/status` → Server-Status (Vortragszahl)
- `GET /api/available-ga` → Verfügbare GA-Bände
- `GET /api/ga-list` → GA-Liste mit Titeln

---

## 🔄 ZUSAMMENFASSUNG: DATENFLUSS-MATRIX

| Datenquelle | Generiert durch | Angezeigt in | Editierbar über |
|-------------|-----------------|--------------|-----------------|
| `steiner-full-lectures-*.json` | Extern | Alle Tabs | ❌ Read-Only |
| `summary-database.json` | Tab "Texte" (Buttons) | Tab "Texte" (Keywords unter Vorträgen) | "TOC&KW neu" |
| `keywords-database.json` | Tab "Texte"/"Keywords" | Tab "Timeline" (Dropdown + Timeline) | V2 Batch, "TOC&KW neu" |
| `themes-database.json` | Tab "Keywords" (Themen generieren) | Tab "Timeline" (Themen-Dropdown) | Cluster-Management |
| `thematic-search-database.json` | Tab "Themen" (Suche) | Tab "Themen" (Zuletzt gesucht) | Automatisch (Cache) |
| `themes-keywords-template.json` | Manuell | - | ❌ Read-Only |

---

## 🎨 UI-LAYOUT

```
┌──────────────────────────────────────────────────────────────────┐
│ HEADER                                                            │
│   Steiner GA-Suche  [Info] [Dark Mode Toggle]                   │
│   [Suche] [Texte] [Themen] [Timeline] [Keywords] [Index] ← TABS │
└──────────────────────────────────────────────────────────────────┘
┌─────────────────────┬──────────────────────────┬───────────────┐
│                     │                          │               │
│   SIDEBAR (links)   │   MAIN VIEWER (Mitte)    │  SUMMARY      │
│   450px             │   Flex                   │  PANEL        │
│                     │                          │  (rechts)     │
│ ┌─────────────────┐ │ ┌──────────────────────┐ │ 280px         │
│ │  Tab-Content    │ │ │ #viewer-header       │ │ (optional)    │
│ │  (Suchfelder,   │ │ │   [Original] [≡]     │ │               │
│ │   Dropdowns)    │ │ │   [TOC&KW neu]       │ │ ┌───────────┐ │
│ ├─────────────────┤ │ ├──────────────────────┤ │ │ TOC       │ │
│ │  #results       │ │ │ #viewer              │ │ │ (H3/H4    │ │
│ │  (Ergebnisse)   │ │ │  - Absätze           │ │ │  klickbar)│ │
│ │                 │ │ │  - Überschriften     │ │ │           │ │
│ │                 │ │ │  - Highlighting      │ │ └───────────┘ │
│ │                 │ │ │                      │ │               │
│ └─────────────────┘ │ └──────────────────────┘ │               │
│                     │                          │               │
└─────────────────────┴──────────────────────────┴───────────────┘
       [⋮] Resize           [⋮] Resize (TOC Panel)
```

---

## 🔍 DETAILLIERTE FUNKTIONSBESCHREIBUNGEN

### Keyword-Generierungs-Algorithmen

#### V3 Flexible (mit Budget)
**Verwendet bei:** "TOC&KW neu" Button

```
1. Lade Template (themes-keywords-template.json)
2. Lade existierendes Vokabular (keywords-database.json)
3. Erstelle Frequenz-Map
4. Für jede H3/H4 Überschrift:
   a) Extrahiere 1-3 potentielle Keywords
   b) Matching gegen Template:
      - Exact Match → Confidence 1.0
      - Fuzzy Match → Confidence 0.6-0.95
   c) Budget-Check: Max 4 NEUE Keywords
   d) Validierung (nicht zu kurz, nicht Stopword)
5. Deduplizierung
6. Themen-Zuordnung (aus Template oder KI)
7. Return: 6-10 Keywords mit Metadaten
```

#### V2 Template
**Verwendet bei:** "Batch starten (V2)"

```
1. Lade Template
2. Für jede H3/H4 Überschrift:
   a) KI extrahiert 1-2 Keywords
   b) Matching gegen Template (Confidence ≥ 0.6)
   c) Konservativ: Max 2 KW/Überschrift
3. Vokabular wächst iterativ
4. Optional: Synonym-Konsolidierung
5. Return: Template-konforme Keywords
```

---

### Themen-Generierung

**Trigger:** Tab "Keywords" → "Themenbereiche generieren"

```
1. Lade alle Keywords aus keywords-database.json
2. Erstelle Frequenz-Statistik
3. KI-Prompt an Claude:
   - "Erstelle 30 thematische Cluster"
   - "Jeder Cluster: Name + Beschreibung + 10-50 Keywords"
   - "Anthroposophie-Kontext beachten"
4. Parse JSON-Response
5. Speichere in themes-database.json
6. Ordne allen Vorträgen ihre Themen zu
```

**Ergebnis:**
- ~30 Themen (z.B. "Anthroposophie & Theosophie", "Karma & Reinkarnation")
- Jedes Thema: 10-50 Keywords
- Verwendung: Timeline-Tab Filterung

---

## ⚙️ KONFIGURATION

### Umgebungsvariablen (.env)
```
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=...
PORT=3003
```

### Lokale vs. Online Modi
```javascript
const isLocal = window.location.hostname === 'localhost' || 
                window.location.hostname === '127.0.0.1' ||
                window.location.protocol === 'file:';

const API_BASE = isLocal
  ? 'http://localhost:3003'
  : 'https://ga-suche.onrender.com';
```

---

## 📝 CHANGELOG WICHTIGER UPDATES

### 26. Oktober 2025
- ✅ Highlighting im Timeline-Tab deaktiviert
- ✅ Auto-Themen-Zuordnung bei Keyword-Auswahl
- ✅ "TOC&KW neu" Button unterscheidet sich von "batch"
- ✅ Button-Umbenennung: "Summary neu" → "TOC&KW neu"
- ✅ HTML-Backup-System vervollständigt

### Frühere Updates
- V3 Keywords mit flexiblem Budget
- Multi-Provider-System (OpenAI/Claude/Gemini)
- Timeline-Tab Implementierung
- Template-basierte V2 Keywords

---

## 🎓 BEST PRACTICES

### Für Batch-Verarbeitung:
1. **Erste Verarbeitung:** "batch" Button (überspringt Vorhandene)
2. **Keywords aktualisieren:** "TOC&KW neu" für einzelne Vorträge
3. **Neu-Generierung:** Tab "Keywords" → "Batch starten (V2)" mit Checkbox "Neu verarbeiten"

### Für Themen-Organisation:
1. Keywords generieren (V2/V3)
2. Themenbereiche generieren (Tab "Keywords")
3. Optional: Manuell nachbearbeiten (Cluster-Editor)
4. Optional: Reorganisieren (KI ordnet neu zu)

### Für Backups:
1. Automatische Backups laufen immer (lokal)
2. Vor großen Änderungen: Manuelles Full-Backup
3. Bei Problemen: Backup-Modal → Wiederherstellen

---

## 🐛 BEKANNTE LIMITIERUNGEN

1. **Volltexte:** Nur GA051-053 geladen (Frontend limitiert)
2. **Keywords-Database:** Enthält Daten für mehr GA-Bände als Volltexte verfügbar
3. **Online-Deployment:** Keine Admin-Funktionen (Keywords-Tab versteckt)
4. **KI-Rate-Limits:** Automatischer Fallback, aber Generierung kann langsam sein
5. **Große Dropdowns:** Keyword-Editor kann bei >2000 Keywords langsam sein

---

## 📞 SUPPORT & DOKUMENTATION

**Weitere Dokumentationen:**
- `BENUTZERANLEITUNG.md` - End-User Anleitung
- `KEYWORD_GENERATION_V3_README.md` - V3 Details
- `DEPLOYMENT_GUIDE.md` - Deployment Anleitung
- `SETUP_LLM_PROVIDERS.md` - Provider-Konfiguration

**System-Dateien (Modal im Frontend):**
- `system/WILLKOMMEN.md` - Welcome-Screen
- `system/BENUTZERANLEITUNG.md` - Anleitung
- `system/GESAMTAUSGABE.md` - GA-Übersicht
- `system/IMPRESSUM.md` - Impressum

---

**Ende der Systemanalyse**

Erstellt: 26. Oktober 2025  
Letzte Aktualisierung: Heute

