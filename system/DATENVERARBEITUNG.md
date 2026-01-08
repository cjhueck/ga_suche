# Datenverarbeitung – Skript-Dokumentation

Diese Dokumentation beschreibt die Python- und JavaScript-Skripte zur Verarbeitung der GA-Daten, insbesondere den Export von Büchern und Vorträgen sowie die Generierung und Einfügung von Seitenzahlen (Page Breaks).

---

## Inhaltsverzeichnis

1. [Übersicht der Skripte](#1-übersicht-der-skripte)
2. [GA-Band-Kategorien](#2-ga-band-kategorien)
3. [Master-Export-Workflow](#3-master-export-workflow)
4. [Export von Büchern (GA001-GA046)](#4-export-von-büchern-ga001-ga046)
5. [Export von Vorträgen (GA051+)](#5-export-von-vorträgen-ga051)
6. [**SEITENZAHLEN-WORKFLOW (KOMPLETT)**](#6-seitenzahlen-workflow-komplett)
   - [6.1 Übersicht: Von PDF zu HTML](#61-übersicht-von-pdf-zu-html)
   - [6.2 Vorträge/Aufsätze: process_pagebreaks.py](#62-vorträgeaufsätze-process_pagebreakspy)
   - [6.3 Bücher: process_books_v4.py](#63-bücher-process_books_v4py)
   - [6.4 contentRange – Bereiche ausschließen](#64-contentrange--bereiche-ausschließen)
7. [Page-Break-Generierung (Details)](#7-page-break-generierung-details)
8. [Page-Break-Anwendung (Details)](#8-page-break-anwendung-details)
9. [Lecture-Page-Mapping](#9-lecture-page-mapping)
10. [Batch-Verarbeitung](#10-batch-verarbeitung)
11. [Datenfluss-Diagramm](#11-datenfluss-diagramm)
12. [Backend-Integration](#12-backend-integration)
13. [Typische Workflow-Beispiele](#13-typische-workflow-beispiele)
14. [Fehlerbehebung](#14-fehlerbehebung)

---

## 1. Übersicht der Skripte

### 1.1 Export-Skripte

| Skript | Funktion |
|--------|----------|
| `export_master.py` | **Haupt-Skript**: Führt kompletten Export-Workflow aus (Bildpfade, Bücher, Vorträge) |
| `export_books_master.py` | Exportiert Bücher (GA001-GA046) als JSON mit Absätzen und Überschriften |
| `export-lectures.js` | Exportiert Vorträge (GA051+) aus Markdown zu JSON (gesplittete part-Dateien) |

### 1.2 Seitenzahlen-Skripte

| Skript | Funktion |
|--------|----------|
| `tools/process_pagebreaks.py` | **Master-Skript für Vorträge/Aufsätze**: Kompletter Workflow (PDF→JSON→MD) |
| `process_books_v4.py` | **Master-Skript für Bücher**: Verarbeitet GA001-028, GA045 mit v4-Verfahren |
| `export_page_markers_v4.py` | Extrahiert Seitenumbruch-Anker aus PDF-Dateien |
| `tools/apply_page_break_markers_v4.py` | Fügt `\|page\|`-Marker in JSON-Daten ein (verwendet Anker aus page-break-markers.json) |
| `tools/apply_pagebreaks_from_pdf.py` | Fügt Marker direkt aus PDF in JSON ein (für Vorträge) |
| `tools/apply_pagebreaks_to_md.py` | Überträgt Marker von JSON in Markdown-Dateien |
| `generate_lecture_page_mapping.py` | Erstellt Mapping: Vortrag-ID → Start-Seitenzahl |
| `batch_generate_pagebreaks.py` | Batch-Verarbeitung für mehrere GA-Bände |

### 1.3 Wichtige Datendateien

| Datei | Funktion |
|-------|----------|
| `page-break-markers.json` | Seitenumbruch-Anker (left/right-Text) pro GA |
| `lecture-page-mapping.json` | Start-Seitenzahlen pro Vortrag/Kapitel |
| `pagebreaks/GAXXX.json` | Override-Dateien mit eingefügten Markern |

---

## 2. GA-Band-Kategorien

Die GA-Bände werden je nach Typ unterschiedlich verarbeitet:

| Kategorie | GA-Nummern | Export-Skript | Output-Dateien |
|-----------|------------|---------------|----------------|
| **Bücher** | GA001-GA028, GA045 | `export_books_master.py` | `steiner-books/*.json` |
| **Aufsätze** | GA029-GA036, GA041b, GA046 | `export-lectures.js` | `steiner-full-lectures/*.json` |
| **Vorträge** | GA051 ff | `export-lectures.js` | `steiner-full-lectures/*.json` |

**Warum die Unterscheidung?**
- **Bücher** sind zusammenhängende Werke mit Kapiteln und Überschriften
- **Aufsätze** und **Vorträge** bestehen aus einzelnen, datierten Einträgen (wie Vorträge behandelt)

---

## 3. Master-Export-Workflow

### Skript: `export_master.py`

Das Master-Skript führt den kompletten Export-Workflow automatisch aus:

```
python export_master.py GA068c
```

### Ablauf im Detail:

```
┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Bildpfade in Obsidian korrigieren               │
│  ─────────────────────────────────────────────────────────  │
│  • Extrahiert Bilder aus PDF-Dateien (falls vorhanden)      │
│  • Konvertiert JPEG-Bilder zu WebP (kleinere Dateigröße)    │
│  • Korrigiert fehlerhafte Markdown/Wiki-Links               │
│  • Vereinfacht GA-Ordner-Pfade zu assets/...                │
│  • Wendet Rechtschreibkorrekturen an                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 2a: Bücher exportieren (GA001-GA028, GA045)        │
│  ─────────────────────────────────────────────────────────  │
│  • Ruft export_books_master.py auf                          │
│  • Exportiert Bücher als JSON mit Absätzen und Überschriften│
│  • Speichert Überschriften in summary-database.json         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 2b: Vorträge exportieren (GA029+, GA051+)          │
│  ─────────────────────────────────────────────────────────  │
│  • Ruft export-lectures.js auf                              │
│  • Exportiert als JSON (gesplittete part-Dateien < 10 MB)   │
│  • Bilder werden automatisch mit exportiert und gesplittet  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 3: Server neu starten (optional mit --restart)     │
└─────────────────────────────────────────────────────────────┘
```

### Aufruf-Beispiele:

```powershell
# Kompletter Export (ALLE GA-Bände)
python export_master.py

# Nur bestimmte GA-Bände
python export_master.py GA068c
python export_master.py GA112-GA117a

# Bildpfad-Korrektur überspringen (schneller)
python export_master.py GA198 --skip-path-fix

# Mit Server-Neustart
python export_master.py GA175-GA209 --restart-server
```

---

## 4. Export von Büchern (GA001-GA046)

### Skript: `export_books_master.py`

Exportiert schriftliche Werke Rudolf Steiners als strukturierte JSON-Dateien.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| Markdown-Dateien | `Steiner_GA/GAXXX-Titel/*.md` | Obsidian-Markdown mit Absatz-Indizes |
| Rechtschreibregeln | `rechtschreibregeln.py` | Korrekturen für alte Orthographie |
| Spelling-Settings | `Steiner_GA/ss-targeted-settings.json` | Zusätzliche Rechtschreibkorrekturen |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Markdown-Datei(en) finden

```python
find_book_files(ga_folder):
    # Unterstützt zwei Formate:
    
    # A) Single-File: "GA001 - Einleitungen zu Goethes... (1884-1897).md"
    #    → Eine Datei enthält das gesamte Buch
    
    # B) Multi-File: "GA001 (1.) ZUR EINFÜHRUNG.md", "GA001 (2.) ERSTER BAND.md"
    #    → Mehrere Dateien, sortiert nach Kapitelnummer
    
    return (is_multi_file, [dateien])
```

#### Schritt 2: Rechtschreibkorrekturen anwenden

```python
fix_spelling(text):
    # 1. Umfassende Korrekturen aus rechtschreibregeln.py
    text = korrigiere_rechtschreibung(text)
    
    # 2. Spezifische Korrekturen:
    #    - Fleiss → Fleiß
    #    - vergeßlich → vergesslich
    #    - Mißverständnis → Missverständnis
    #    - angepaßt → angepasst
    
    # 3. Korrekturen aus ss-targeted-settings.json
    #    (exactReplacements und regexReplacements)
```

#### Schritt 3: Überschriften konvertieren

```python
convert_headings(text):
    # H1 (# Titel) → H3 (### Titel)
    # H2 (## Titel) → H4 (#### Titel)
    # H3 (### Titel) → H4 (#### Titel)
    
    # Grund: Im Frontend sind H1/H2 für die App-Struktur reserviert
```

#### Schritt 4: Absätze extrahieren

```python
extract_paragraphs(text):
    paragraphs = []
    
    für jede Zeile:
        # Überspringe Überschriften (###, ####)
        
        # Suche Index am Zeilenende: "Text ^abc123"
        if zeile.endet_mit("^..."):
            index = extrahiere_index()
            paragraphs.append({
                'index': index,      # z.B. "^4iv2sd"
                'content': text      # Absatzinhalt ohne Index
            })
    
    return paragraphs
```

**Wichtig:** Absätze ohne `^`-Index werden übersprungen!

#### Schritt 5: Überschriften mit Absätzen verknüpfen

```python
link_headings_to_paragraphs(headings, paragraphs, content):
    # Für jede Überschrift: Finde den ersten Absatz danach
    
    # WICHTIG: Sequenzielle Suche!
    # Jede Überschrift wird nur ab der Position der vorherigen gesucht.
    # Verhindert dass "I" aus Kapitel 2 auf Kapitel 1 zeigt.
    
    search_start_pos = 0
    
    für jede überschrift:
        # Finde Position im Content
        heading_pos = content.find(überschrift.text, search_start_pos)
        
        # Finde ersten Absatz nach dieser Position
        für jeden absatz:
            if absatz.position > heading_pos:
                überschrift.index = absatz.index
                break
        
        # Nächste Überschrift nur ab hier suchen
        search_start_pos = heading_pos + 1
```

#### Schritt 6: Fußnoten konvertieren

```python
convert_footnotes(text):
    # Bereits Markdown-Fußnoten vorhanden?
    # [^1]: Fußnotentext ↩
    #   → [^1]: Fußnotentext (ohne Backlink)
    
    # Alte römische Ziffern-Format?
    # .i, .ii → [^1], [^2]
    # i[Text], ii[Text] → [^1]: Text, [^2]: Text
```

### Output

| Datei | Pfad | Format |
|-------|------|--------|
| Bücher-JSON | `steiner-books/steiner-books-001-046.json` | JSON |
| Überschriften | `summary-database.json` | JSON (wird gemergt) |

**Bücher-Output Struktur:**
```json
{
  "metadata": {
    "exportDate": "2024-12-25T10:00:00.000Z",
    "totalBooks": 28,
    "gaRange": "GA001-GA046"
  },
  "books": [
    {
      "ID": "GA001",
      "gaNumber": "GA001",
      "title": "Einleitungen zu Goethes... (1884-1897)",
      "content": "...",
      "paragraphs": [
        {"index": "^abc123", "content": "Erster Absatz..."},
        {"index": "^def456", "content": "Zweiter Absatz..."}
      ],
      "headings": [
        {"id": "^abc123", "text": "Zur Einführung", "level": 3}
      ],
      "wordCount": 45000,
      "charCount": 280000
    }
  ]
}
```

### Aufruf

```powershell
# Alle Bücher (GA001-GA046)
python export_books_master.py

# Nur bestimmte Bücher
python export_books_master.py GA001 GA002 GA003

# Mit Rechtschreibkorrekturen (langsamer)
python export_books_master.py --spelling
```

---

## 5. Export von Vorträgen (GA051+)

### Skript: `export-lectures.js`

Exportiert Vorträge aus Obsidian-Markdown zu JSON. Bilder werden automatisch mit exportiert und gesplittet.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| Markdown-Dateien | `Steiner_GA/GAXXX-Titel/*.md` | Einzelne Vorträge als Markdown |
| Bilder | `Steiner_GA/GAXXX-Titel/assets/*.webp` | Tafelbilder und Illustrationen |

### Dateinamen-Format der Vorträge

```
GA068c (25.) DAS «MÄRCHEN» VON GOETHE, Heidelberg, 21. Januar 1909.md
│      │     │                         │           │
│      │     │                         │           └── Datum
│      │     │                         └── Ort
│      │     └── Titel
│      └── Vortragsnummer
└── GA-Band (mit optionalem Suffix a/b/c/d)
```

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Metadaten aus Dateinamen extrahieren

```javascript
extractMetadataFromFilename(filename):
    // Beispiel: "GA068c (25.) DAS «MÄRCHEN», Heidelberg, 21. Januar 1909.md"
    
    return {
        gaNumber: "GA068c",
        lectureNumber: "25",
        ID: "GA068c/25",
        title: "DAS «MÄRCHEN» VON GOETHE",
        location: "Heidelberg",
        date: "1909-01-21"
    }
```

#### Schritt 2: Absätze aus Markdown extrahieren

```javascript
extractParagraphs(content):
    für jede Zeile:
        // Filtere heraus:
        // - TOC-Einträge: [[#Heading]] - _Description_
        // - Wiki-Link-Zeilen: [[Schlagwort1]] - [[Schlagwort2]]
        // - Inhaltsverzeichnis-Überschriften
        // - H1 (Dokumenttitel)
        // - Nur kursiv/fett (oft Zusammenfassungen)
        // - "Quelle:"-Zeilen
        // - Trennlinien (---, ===)
        
        // BEHALTE:
        // - Normalen Fließtext
        // - H2, H3, H4 (Zwischenüberschriften)
        // - Bildmarkierungen ![](...)
        
        // Suche Index am Zeilenende: "^abc123"
        if zeile.endet_mit("^..."):
            absätze.append({
                index: index,
                content: bereinigter_text
            })
```

#### Schritt 3: Bilder verarbeiten

```javascript
processImages(lecture, gaFolder):
    für jedes Bild in lecture.paragraphs:
        // Suche Bildpfad: ![alt](assets/123-T01.webp)
        
        // Lade Bild als Base64
        imageData = fs.readFileSync(bildpfad)
        base64 = imageData.toString('base64')
        
        // Speichere Bild-Referenz
        images.push({
            imageId: "GA068c/25/123-T01",
            gaNumber: "GA068c",
            lectureId: "GA068c/25",
            filename: "123-T01.webp",
            data: "data:image/webp;base64,..."
        })
```

#### Schritt 4: Listen-Absätze zusammenführen

```javascript
mergeListParagraphs(paragraphs):
    // Nummerierte Listen (1., 2., 3.)
    // und Aufzählungen (-, *, •)
    // werden mit dem vorhergehenden Absatz zusammengeführt
    
    // Grund: Vermeidet fragmentierte Suchergebnisse
```

#### Schritt 5: JSON gesplittet speichern

```javascript
saveAsPartFiles(lectures, images):
    // Maximale Dateigröße: 10 MB (GitHub-kompatibel)
    
    // Lectures:
    // steiner-full-lectures/steiner-full-lectures-068c-068c.json
    
    // Bilder (gesplittet wenn > 10 MB):
    // steiner-images/steiner-images-part01.json
    // steiner-images/steiner-images-part02.json
```

### Output

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Vorträge | `steiner-full-lectures/steiner-full-lectures-XXX-XXX.json` | JSON mit Absätzen |
| Bilder | `steiner-images/steiner-images-partNN.json` | Base64-codierte Bilder |

**Vortrags-Output Struktur:**
```json
{
  "lectures": [
    {
      "gaNumber": "GA068c",
      "lectureNumber": "25",
      "ID": "GA068c/25",
      "title": "DAS «MÄRCHEN» VON GOETHE",
      "location": "Heidelberg",
      "date": "1909-01-21",
      "paragraphs": [
        {"index": "^abc123", "content": "Erster Absatz..."},
        {"index": "^def456", "content": "![](assets/068c-T01.webp)"}
      ]
    }
  ]
}
```

### Aufruf

```powershell
# Wird normalerweise über export_master.py aufgerufen
node export-lectures.js GA068c

# Bereich von GA-Bänden
node export-lectures.js GA051-GA060

# Alle Vorträge
node export-lectures.js
```

---

## 6. SEITENZAHLEN-WORKFLOW (KOMPLETT)

Dieser Abschnitt beschreibt den **vollständigen Workflow**, wie Seitenzahlen aus PDF-Dateien extrahiert und in HTML sichtbar gemacht werden.

### 6.1 Übersicht: Von PDF zu HTML

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DER KOMPLETTE SEITENZAHLEN-WORKFLOW                    │
└─────────────────────────────────────────────────────────────────────────────┘

 SCHRITT 1: PDF-Analyse                    SCHRITT 2: Marker-Einfügung
 ─────────────────────────                 ──────────────────────────────
 
 ┌───────────────┐                         ┌───────────────┐
 │   PDF-Datei   │                         │   JSON-Datei  │
 │  (Steiner_GA_ │                         │ (steiner-full-│
 │   pdf/*.pdf)  │                         │ lectures/*.json│
 └───────┬───────┘                         └───────┬───────┘
         │                                         │
         ▼                                         ▼
 ┌───────────────┐                         ┌───────────────────┐
 │ Seitenzahlen  │                         │ Fuzzy-Matching    │
 │ aus Footer    │ ──────────────────────▶ │ findet Position   │
 │ extrahieren   │   page-break-markers    │ für jeden Break   │
 └───────────────┘         .json           └─────────┬─────────┘
         │                                           │
         ▼                                           ▼
 ┌───────────────┐                         ┌───────────────────┐
 │ Text an       │                         │ |page|-Marker     │
 │ Seitenumbruch │                         │ einfügen:         │
 │ extrahieren   │                         │ "Text|14|weiter"  │
 │ (left/right)  │                         └─────────┬─────────┘
 └───────────────┘                                   │
                                                     ▼
                                           ┌───────────────────┐
                                           │ pagebreaks/       │
                                           │   GAXXX.json      │
                                           └─────────┬─────────┘

 SCHRITT 3: MD-Dateien aktualisieren       SCHRITT 4: HTML-Anzeige
 ──────────────────────────────────        ─────────────────────────
 
 ┌───────────────┐                         ┌───────────────────┐
 │  JSON mit     │                         │ Backend lädt      │
 │  Markern      │ ──────────────────────▶ │ pagebreaks/*.json │
 └───────┬───────┘                         │ als Override      │
         │                                 └─────────┬─────────┘
         ▼                                           │
 ┌───────────────┐                                   ▼
 │ Marker in     │                         ┌───────────────────┐
 │ MD-Dateien    │                         │ Frontend zeigt    │
 │ übertragen    │                         │ Seitenzahlen als  │
 │ (Obsidian)    │                         │ klickbare Badges  │
 └───────────────┘                         └───────────────────┘
```

### 6.2 Vorträge/Aufsätze: process_pagebreaks.py

**Das Master-Skript für Vorträge und Aufsätze (GA029-044, GA051+)**

```powershell
# Einzelne GA verarbeiten
python tools/process_pagebreaks.py GA198

# Bereich verarbeiten (GA151 bis GA200)
python tools/process_pagebreaks.py 151 200

# Parallel mit 4 Workern
python tools/process_pagebreaks.py 151 200 --workers 4
```

#### Was macht das Skript?

```
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 1/4: PDF kopieren                                       │
│  ───────────────────────────────────────────────────────────────│
│  • Kopiert PDF aus Steiner_GA_pdf/ nach Steiner_GA/GAXXX-Titel/ │
│  • Damit PDF im Obsidian-Ordner verfügbar ist                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 2/4: Seitenmarker in JSON einfügen                      │
│  ───────────────────────────────────────────────────────────────│
│  • Ruft apply_pagebreaks_from_pdf.py auf                        │
│  • Extrahiert Seitenzahlen direkt aus PDF                       │
│  • Findet Positionen per Fuzzy-Matching                         │
│  • Fügt |page|-Marker in steiner-full-lectures/*.json ein       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 3/4: Alte Override-Dateien archivieren                  │
│  ───────────────────────────────────────────────────────────────│
│  • Verschiebt alte pagebreaks/*.json nach pagebreaks/archive/   │
│  • Verhindert Konflikte mit alten Versionen                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 4/4: Seitenmarker in MD-Dateien einfügen                │
│  ───────────────────────────────────────────────────────────────│
│  • Ruft apply_pagebreaks_to_md.py auf                           │
│  • Überträgt Marker von JSON nach Markdown                      │
│  • Seitenzahlen werden in Obsidian sichtbar                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Beispiel-Output

```
============================================================
Verarbeite GA198
============================================================
  Typ: lectures

  [1/4] PDF kopieren...
    ✓ PDF kopiert: Steiner, Rudolf GA 198 1984 - Heilfaktoren.pdf
      Nach: GA198-Heilfaktoren für den sozialen Organismus/

  [2/4] Seitenmarker in JSON einfügen...
    GA198/1: 12 Marker (S.13-24) - ERSTER VORTRAG
    GA198/2: 14 Marker (S.25-38) - ZWEITER VORTRAG
    ...
    Gesamt: 265 Marker eingefügt
    Gespeichert in: steiner-full-lectures-198-198.json

  [3/4] Alte Override-Dateien inaktivieren...
    ✓ Keine alte Override-Datei vorhanden

  [4/4] Seitenmarker in MD-Dateien einfügen...
    GA198/1: 12/318 Marker (S.13-318)
    GA198/2: 14/318 Marker (S.13-318)
    ...
    Gesamt: 265 Marker in 17 Dateien

  Ergebnis für GA198:
    - PDF: ✓
    - JSON-Marker: 265
    - Override: ✓
    - MD-Marker: 265
```

### 6.3 Bücher: process_books_v4.py

**Das Master-Skript für Bücher (GA001-028, GA045)**

Bücher werden anders verarbeitet als Vorträge, weil:
- Sie zusammenhängende Texte sind (keine einzelnen Vorträge)
- Sie oft Vorbemerkungen haben, die im PDF anders sind als in der MD-Datei
- Fußnoten die Position der Marker beeinflussen können

```powershell
# Einzelnes Buch verarbeiten
python process_books_v4.py GA001

# Bereich verarbeiten (GA001 bis GA028)
python process_books_v4.py 1 28

# Mehrere einzelne Bücher
python process_books_v4.py GA001 GA002 GA045
```

#### Unterschied zu Vorträgen

| Aspekt | Vorträge (process_pagebreaks.py) | Bücher (process_books_v4.py) |
|--------|----------------------------------|------------------------------|
| Datenquelle | Direkt aus PDF | Anker aus page-break-markers.json |
| Verarbeitung | Pro Vortrag einzeln | Als zusammenhängender Text |
| Fußnoten | Weniger problematisch | Können Positionen verschieben |
| Output | steiner-full-lectures/*.json | pagebreaks/GAXXX.json |

#### Workflow für Bücher

```
┌─────────────────────────────────────────────────────────────────┐
│  VORAUSSETZUNG: page-break-markers.json                          │
│  ───────────────────────────────────────────────────────────────│
│  • Muss Anker (left/right) für das Buch enthalten               │
│  • Erzeugt durch: python export_page_markers_v4.py GA001        │
│  • Prüfen: python -c "import json; print(json.load(             │
│            open('page-break-markers.json'))['GA001'].keys())"   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Anker laden und filtern                              │
│  ───────────────────────────────────────────────────────────────│
│  • Lade breaks aus page-break-markers.json                      │
│  • Filtere nach contentRange (z.B. [11, 104] für GA045)         │
│  • Entferne doppelte Seitenzahlen                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 2: Buch-Paragraphen laden                               │
│  ───────────────────────────────────────────────────────────────│
│  • Lade aus steiner-books/*.json                                │
│  • Entferne alte |page|-Marker (falls vorhanden)                │
│  • Normalisiere Text für Matching                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 3: Fuzzy-Matching                                       │
│  ───────────────────────────────────────────────────────────────│
│  • Für jeden Anker: Suche "right"-Text im normalisierten Buch   │
│  • Bestätige mit "left"-Text (muss kurz vorher sein)            │
│  • Berechne exakte Einfügeposition                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 4: Marker einfügen und speichern                        │
│  ───────────────────────────────────────────────────────────────│
│  • Füge |page|-Marker an berechneten Positionen ein             │
│  • Speichere in pagebreaks/GAXXX.json                           │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 contentRange – Bereiche ausschließen

Die `contentRange` in `page-break-markers.json` definiert, welche PDF-Seiten verarbeitet werden sollen. Dies ist wichtig, wenn:

- **Vorbemerkungen** in PDF und MD unterschiedlich sind
- **Inhaltsverzeichnisse** übersprungen werden sollen
- **Anhänge** nicht verarbeitet werden sollen

#### Beispiel: GA045 (Anthroposophie – Ein Fragment)

```json
// In page-break-markers.json:
{
  "GA045": {
    "title": "Anthroposophie. Ein Fragment",
    "contentRange": [11, 104],  // ← Nur Seiten 11-104 verarbeiten
    "breaks": [...]
  }
}
```

**Warum [11, 104]?**
- Seiten 7-10: Vorbemerkung des Herausgebers (unterschiedlich in MD)
- Seite 11: Beginn von "I. DER CHARAKTER DER ANTHROPOSOPHIE"
- Ab Seite 11 stimmen PDF und MD überein

#### contentRange anpassen

```powershell
# Aktuelle contentRange prüfen
python -c "import json; f=open('page-break-markers.json','r',encoding='utf-8'); d=json.load(f); print(d['GA045'].get('contentRange'))"

# contentRange ändern
python -c "
import json
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
data['GA045']['contentRange'] = [11, 104]  # Neue Range
with open('page-break-markers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('contentRange aktualisiert')
"

# Buch neu verarbeiten
python process_books_v4.py GA045
```

#### Typische contentRange-Werte

| GA | contentRange | Grund |
|----|--------------|-------|
| GA001 | [7, 500] | Normale Bücher beginnen meist bei Seite 7 |
| GA045 | [11, 104] | Vorbemerkung (S.7-10) ist unterschiedlich |
| Vorträge | [1, 10000] | Meist alles verarbeiten |

---

## 7. Page-Break-Generierung (Details)

### Skript: `export_page_markers_v4.py`

Extrahiert Seitenumbruch-Informationen aus PDF-Dateien der Gesamtausgabe und speichert sie als "Break Anchors" für spätere Zuordnung zum JSON-Text.

### Zweck

Die gedruckten GA-Bände haben Seitenzahlen, die im Frontend angezeigt werden sollen. Dieses Skript extrahiert:
- Die gedruckte Seitenzahl jeder PDF-Seite
- Den Fließtext an den Seitenübergängen (für Fuzzy-Matching)

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` | Die gescannten/digitalisierten GA-Bände |
| Bestehende Marker | `page-break-markers.json` | Wird geladen und erweitert (falls vorhanden) |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: PDF laden

```python
find_pdf_for_ga("GA198"):
    # Sucht in Steiner_GA_pdf/ nach:
    # 1. "ga 198" oder "ga198" im Dateinamen
    # 2. Bevorzugt "_einzelseiten" PDFs (aufgeteilte Doppelseiten)
    # 3. Bevorzugt vollständige PDFs ohne Seitenbereich im Namen
    
    # Öffnet PDF mit PyMuPDF (fitz)
```

#### Schritt 2: Running Headers erkennen

```python
build_header_skip_set(doc):
    für jede Seite:
        # Scanne obere 18% der Seite
        für jeden Textblock mit y_top < page_height * 0.18:
            normalisiere Text (lowercase, ohne Zahlen)
            zähle Vorkommen über alle Seiten
    
    # Zeilen die auf ≥8% der Seiten vorkommen = Running Header
    return Set von zu überspringenden Zeilen
```

**Beispiel:** "ERSTER VORTRAG" erscheint auf 50 von 320 Seiten → wird als Running Header erkannt und übersprungen.

#### Schritt 3: Pro PDF-Seite verarbeiten

**3a. Seitenzahl aus Footer extrahieren:**
```python
extract_printed_page_from_footer(page):
    # Scanne untere 15% der Seite (y > page_height * 0.85)
    
    # Priorität der Muster:
    1. "Seite: 123" oder "Seite 123"  → Priorität 10
    2. "- 123 -" (mit Strichen)       → Priorität 8  
    3. Alleinstehende Zahl "123"      → Priorität 5
    
    # Wähle Kandidat mit höchster Priorität
    # Fallback: Plain-Text der letzten 10 Zeilen durchsuchen
```

**3b. Fließtext extrahieren:**
```python
extract_body_text(page, header_skip):
    für jeden Textblock:
        # Überspringe wenn:
        - Im Footer-Bereich UND sieht aus wie Seitenzahl
        - Enthält "Copyright" oder "Buch:"
        - Ist Running Header (in header_skip)
        - Ist ALL CAPS Überschrift (< 90 Zeichen, kein Satzzeichen am Ende)
    
    # Sortiere nach y-Position (Reading Order)
    # Verbinde zu einem String
    # Entferne PDF-Artefakte wie "[34]" (Querverweise)
```

**3c. Fehlende Seitenzahlen interpolieren:**
```python
interpolate_printed_pages(pages):
    # Beispiel: Seite 10, ?, ?, 13 erkannt
    # → Interpoliert zu: 10, 11, 12, 13
    
    für jede Seite ohne printed_page:
        finde vorherigen und nächsten Anker
        berechne lineare Interpolation
```

#### Schritt 4: Breaks erstellen

```python
# Erste Seite (nur "right", kein "left")
first_page_entry = {
    "page": erste_seitenzahl,
    "pdfFrom": None,
    "pdfTo": pdf_index,
    "left": None,
    "right": erste_200_zeichen,
    "hyphenated": False,
    "isFirstPage": True
}

# Reguläre Breaks zwischen Seiten
für i in range(pdf_page_count - 1):
    left_text = pages[i].body_text[-200:]    # Letzte 200 Zeichen
    right_text = pages[i+1].body_text[:200]  # Erste 200 Zeichen
    
    # Prüfe auf Silbentrennung am Seitenende
    hyphenated = left_text.rstrip()[-1] in {"-", "¬", "–"}
    
    breaks.append({
        "page": pages[i+1].printed_page,  # Seitenzahl der NÄCHSTEN Seite
        "pdfFrom": i,
        "pdfTo": i + 1,
        "left": left_text,
        "right": right_text,
        "hyphenated": hyphenated
    })
```

**Beispiel eines Breaks:**
```
PDF-Seite 12 (gedruckt S.13): "...ist ein Unding in der Menschheit"
PDF-Seite 13 (gedruckt S.14): "dieser Weise gleichgültig bleiben..."

→ Break: { page: 14, left: "...Menschheit", right: "dieser Weise..." }
```

### Output

| Datei | Pfad | Format |
|-------|------|--------|
| Page-Break-Markers | `page-break-markers.json` | JSON |

**Struktur:**
```json
{
  "_info": "Page-Break Anchors V4...",
  "GA198": {
    "title": "Heilfaktoren für den sozialen Organismus",
    "pdfSource": "Steiner, Rudolf GA 198 1984 - ....pdf",
    "pdfPageCount": 320,
    "contentRange": [7, 10000],
    "breaks": [
      {
        "page": 13,
        "pdfFrom": null,
        "pdfTo": 12,
        "left": null,
        "right": "Was heute den Menschen als eine fast...",
        "hyphenated": false,
        "printedPageConfidence": "extracted",
        "isFirstPage": true
      },
      {
        "page": 14,
        "pdfFrom": 12,
        "pdfTo": 13,
        "left": "...ist ein Unding in der Menschheit",
        "right": "dieser Weise gleichgültig bleiben...",
        "hyphenated": false,
        "printedPageConfidence": "extracted"
      }
    ]
  }
}
```

### Aufruf

```powershell
# Einzelne GA verarbeiten
python export_page_markers_v4.py GA198

# Mit Validierung (prüft ob Breaks im JSON-Text gefunden werden)
python export_page_markers_v4.py --validate GA198
```

---

## 8. Page-Break-Anwendung (Details)

### Skript: `apply_page_break_markers_v4.py`

Nimmt die Break-Anker aus `page-break-markers.json` und findet im JSON-Text die exakte Einfügeposition für jeden Seitenumbruch. Fügt Marker im Format `|<page>|` ein.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| Break-Anker | `page-break-markers.json` | Output von `export_page_markers_v4.py` |
| Vorträge | `steiner-full-lectures/*.json` | JSON-Dateien mit Vortrags-Paragraphen |
| Bücher | `steiner-books/*.json` | JSON-Dateien mit Buch-Paragraphen |
| Lecture-Mapping | `lecture-page-mapping.json` | Start-Seitenzahlen pro Vortrag |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Daten laden

```python
# Break-Anker laden
anchors = load_json("page-break-markers.json")
breaks = anchors["GA198"]["breaks"]  # z.B. 318 Breaks

# Vorträge oder Buch laden
if GA >= 51:
    lectures = load_lectures_by_ga("GA198")  # 17 Vorträge
else:
    book = load_book_by_ga("GA004")
```

#### Schritt 2: Text normalisieren (für Fuzzy-Matching)

Die Normalisierung ist entscheidend, weil PDF-Text und JSON-Text sich unterscheiden können:

```python
def normalize_simple(text):
    # 1. Soft Hyphen und Non-Breaking Space entfernen
    s = text.replace("\u00ad", "").replace("\u00a0", " ")
    
    # 2. Ligaturen expandieren
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")
    
    # 3. Lowercase
    s = s.lower()
    
    # 4. Alte Orthographie: "th" → "t"
    #    "Thatsachen" → "tatsachen" (PDF) vs "Tatsachen" → "tatsachen" (JSON)
    s = re.sub(r"th", "t", s)  # vereinfacht
    
    # 5. ß → ss
    s = s.replace("ß", "ss")
    
    # 6. Silbentrennung zusammenführen
    #    "Philo-\nsophie" → "philosophie"
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)
    
    # 7. Whitespace normalisieren
    s = re.sub(r"\s+", " ", s)
    
    return s.strip()
```

**Beispiel:**
```
PDF:  "Thatsächlich ist es so, daß die Philo-\nsophie..."
JSON: "Tatsächlich ist es so, dass die Philosophie..."

Nach Normalisierung (beide):
      "tatsachlich ist es so, dass die philosophie..."
```

#### Schritt 3a: Vorträge einzeln verarbeiten

```python
def process_lectures_individually(lectures, breaks):
    # Lade Start-Seitenzahlen aus lecture-page-mapping.json
    mapping = {
        "GA198/1": 13,   # Vortrag 1 beginnt auf Seite 13
        "GA198/2": 25,   # Vortrag 2 beginnt auf Seite 25
        ...
    }
    
    für jeden Vortrag:
        start_page = mapping[vortrag.ID]
        end_page = mapping[nächster_vortrag.ID] oder start_page + 10
        
        # Filtere Breaks für diesen Seitenbereich
        vortrag_breaks = [b for b in breaks if start_page <= b.page < end_page]
        
        # Normalisiere alle Paragraphen des Vortrags
        norm_text, para_map, char_map = normalize_paragraphs_with_map(vortrag.paragraphs)
        
        # Füge Start-Seite am Anfang des ersten Fließtext-Absatzes ein
        insertions.append((0, 0, start_page))
        
        # Finde Position für jeden weiteren Break
        für jeden break in vortrag_breaks:
            position = find_best_insertion(norm_text, break.left, break.right)
            if position:
                insertions.append(position)
```

#### Schritt 3b: Bücher als zusammenhängenden Text verarbeiten

```python
def process_book(book, breaks):
    # Alle Paragraphen zu einem normalisierten Text verbinden
    norm_text, para_map, char_map = normalize_paragraphs_with_map(book.paragraphs)
    
    last_norm_pos = 0  # Monotonie: jeder Break muss NACH dem vorherigen sein
    
    für jeden break in sortiert_nach_seitenzahl(breaks):
        position = find_best_insertion(norm_text, break.left, break.right, 
                                       min_norm_pos=last_norm_pos)
        
        # Schutz gegen Ausreißer: Sprung darf nicht zu groß sein
        if position - last_norm_pos > 40000:
            skip(break)  # Wahrscheinlich False Positive
            continue
        
        insertions.append(position)
        last_norm_pos = position + 1
```

#### Schritt 4: Insertion finden (Kern-Algorithmus)

```python
def find_best_insertion(norm_content, left, right, hyphenated, min_norm_pos=0):
    r_norm = normalize_simple(right)
    l_norm = normalize_simple(left)
    
    best_score = -1
    best_pos = None
    
    # === METHODE 1: Exakte Suche nach RIGHT ===
    für r_len in [140, 120, 100, 80, 60]:  # Verschiedene Längen probieren
        r_key = r_norm[:r_len]
        
        pos = norm_content.find(r_key, min_norm_pos)
        while pos >= 0:
            # Bewerte Fund: Ist LEFT kurz davor?
            score = 1.0 + left_bonus(pos, l_norm)
            
            if score > best_score:
                best_score = score
                best_pos = pos
            
            pos = norm_content.find(r_key, pos + 1)
        
        if best_score >= 8.0:  # Sehr guter Fund (LEFT direkt davor)
            break
    
    # === METHODE 2: Fuzzy-Matching (wenn exakt nicht gefunden) ===
    if best_pos is None:
        # Extrahiere lange Wörter aus RIGHT
        tokens = ["geisteswissenschaft", "menschheit", "entwicklung", ...]
        
        für jedes token:
            # Finde alle Vorkommen im Text
            # Berechne: position - token_offset_in_right = kandidat_start
            kandidaten.append(kandidat_start)
        
        für jeden kandidat:
            # Vergleiche mit SequenceMatcher
            segment = norm_content[kandidat:kandidat+160]
            ratio = SequenceMatcher(None, r_norm[:160], segment).ratio()
            
            if ratio > 0.7:  # Mindestens 70% Übereinstimmung
                score = ratio * 10 + left_bonus(kandidat)
                if score > best_score:
                    best_pos = kandidat
    
    # === METHODE 3: Fallback auf LEFT ===
    if best_pos is None:
        # Finde Ende von LEFT und setze Marker dort
        l_pos = norm_content.find(l_norm[-100:])
        if l_pos >= 0:
            best_pos = l_pos + len(l_norm[-100:])
    
    # Konvertiere norm_pos zurück zu (paragraph_idx, char_idx)
    return (para_map[best_pos], char_map[best_pos], best_pos)


def left_bonus(pos, l_norm):
    """Bonus wenn LEFT kurz vor POS gefunden wird"""
    window = norm_content[max(0, pos-900):pos]
    
    l_pos = window.rfind(l_norm[-100:])
    if l_pos >= 0:
        distance = pos - (window_start + l_pos + len(l_norm[-100:]))
        
        if distance <= 10:   return 10.0  # Perfekt: LEFT endet direkt vor RIGHT
        if distance <= 30:   return 7.0   # Sehr gut
        if distance <= 80:   return 4.0   # Gut
        if distance <= 200:  return 2.0   # Akzeptabel
    
    return -0.5  # LEFT nicht gefunden → Abzug
```

**Beispiel:**
```
Break: { page: 14, left: "...Unding in der Menschheit", right: "dieser Weise gleichgültig" }

1. Suche "dieser weise gleichgultig" (normalisiert) im JSON-Text
2. Gefunden an Position 4523
3. Prüfe: Ist "unding in der menschheit" kurz vor 4523?
   → Gefunden bei Position 4498, Distanz = 25 → Score = 7.0
4. → Einfügeposition: Position 4523 im normalisierten Text
   → Zurückrechnen: Paragraph 3, Zeichen 156
```

#### Schritt 5: Marker einfügen

```python
def apply_insertions_to_paragraphs(paragraphs, insertions):
    # Gruppiere nach Paragraph
    by_para = group_by(insertions, key=para_idx)
    
    für jeden paragraph:
        # WICHTIG: Von hinten nach vorne einfügen (damit Positionen stimmen)
        für (char_idx, page) in sorted(by_para[para_idx], reverse=True):
            
            # Prüfe ob Position in geschützter Struktur liegt
            char_idx = find_safe_insertion_position(content, char_idx)
            # z.B. nicht innerhalb von ![alt](bild.png) oder <img ...>
            
            # Marker einfügen
            content = content[:char_idx] + f"|{page}|" + content[char_idx:]
        
        paragraph["content"] = content
```

**Vorher:**
```
"dieser Weise gleichgültig bleiben. Da war alles..."
```

**Nachher:**
```
"|14|dieser Weise gleichgültig bleiben. Da war alles..."
```

### Output

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Vorträge/Buch mit Markern | `pagebreaks/GA198.json` | JSON mit eingefügten `\|page\|` Markern |
| Report | `pagebreaks/GA198-report.json` | Statistik und Fehler |

**Vortrags-Output Struktur:**
```json
{
  "_info": "Output: Vorträge mit eingefügten |page|-Markern...",
  "ga": "GA198",
  "sourceFile": "steiner-full-lectures-198-198.json",
  "lectureCount": 17,
  "lectures": [
    {
      "gaNumber": "GA198",
      "lectureNumber": "1",
      "ID": "GA198/1",
      "title": "ERSTER VORTRAG",
      "paragraphs": [
        {
          "index": "^4iv2sd",
          "content": "|13|Was heute den Menschen als eine fast unumstrittene..."
        }
      ]
    }
  ]
}
```

**Report Struktur:**
```json
{
  "ga": "GA198",
  "sourceFile": "steiner-full-lectures-198-198.json",
  "anchorsFile": "page-break-markers.json",
  "breaksTotal": 318,
  "breaksWithPage": 318,
  "inserted": 265,
  "insertedRatio": 0.833,
  "failed": 17,
  "failuresSample": [
    {"page": 24, "reason": "no-match", "lecture": 0}
  ]
}
```

### Aufruf

```powershell
# Standard: Output in pagebreaks/
python apply_page_break_markers_v4.py GA198

# Mit explizitem Output-Pfad
python apply_page_break_markers_v4.py GA198 --out pagebreaks/GA198.json

# Mit Report-Pfad
python apply_page_break_markers_v4.py GA198 --out pagebreaks/GA198.json --report pagebreaks/GA198-report.json
```

---

## 9. Lecture-Page-Mapping

### Skript: `generate_lecture_page_mapping.py`

Erstellt ein Mapping von Vortrag-IDs zu ihren Start-Seitenzahlen im PDF. Dieses Mapping wird von `apply_page_break_markers_v4.py` verwendet, um zu wissen, wo im PDF jeder Vortrag beginnt.

### Warum ist dieses Skript nötig?

Bei Vortrags-Bänden (GA051+) enthält ein PDF mehrere Vorträge. Das `apply_page_break_markers_v4.py` muss wissen:
- Wo beginnt Vortrag 1? (z.B. Seite 13)
- Wo beginnt Vortrag 2? (z.B. Seite 25)
- usw.

Ohne dieses Mapping würde das Skript die Breaks falsch zuordnen.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` | GA-Band PDFs |
| Vorträge | `steiner-full-lectures/*.json` | JSON mit Vortrags-Text |
| Page-Breaks (optional) | `page-break-markers.json` | Für bessere Seitenzahl-Erkennung |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Vorträge laden
```python
lectures = load_lectures_for_ga("GA198")
# Lädt aus steiner-full-lectures/steiner-full-lectures-198-198.json
# Sortiert nach lectureNumber: [Vortrag 1, Vortrag 2, ..., Vortrag 17]
```

#### Schritt 2: PDF-Seiten extrahieren
```python
def extract_page_texts(pdf_path, ga_number):
    # Versuche vorberechnete Seitenzahlen zu laden
    precomputed = load_page_breaks(ga_number)  # aus page-break-markers.json
    
    page_texts = []
    für jede PDF-Seite i:
        text = page.get_text("text")
        
        if i in precomputed:
            page_num = precomputed[i]  # Seitenzahl aus page-break-markers.json
        else:
            page_num = extract_page_number(page)  # Aus Footer extrahieren
        
        page_texts.append((i, page_num, text))
    
    return page_texts  # [(0, 7, "Inhalt..."), (1, 8, "Vorwort..."), ...]
```

#### Schritt 3: Für jeden Vortrag die Start-Seite finden

```python
def find_lecture_in_pdf(lecture, page_texts):
    # === SCHRITT 3a: Ersten Fließtext-Absatz finden ===
    collected = []
    für jeden absatz in lecture.paragraphs[:15]:
        text = normalize_text(absatz.content)
        
        # Überspringe Metadaten und kurze Zeilen
        if len(text) < 30: continue
        if text.startswith(("manuskript", "fragment", "undatiert")): continue
        
        collected.append(text)
        
        # Brauchen mindestens 200 Zeichen MIT Satzzeichen (Fließtext)
        combined = " ".join(collected)
        if len(combined) >= 200 and any(p in combined for p in ['. ', ', ', '; ']):
            break
    
    search_text = combined[:1000]  # Maximal 1000 Zeichen für Suche
    
    # === SCHRITT 3b: Im PDF suchen (sequentiell) ===
    für (pdf_idx, page_num, page_text) in page_texts:
        page_norm = normalize_text(page_text)
        
        # Exakte Teilstring-Suche (verschiedene Längen)
        für search_len in [800, 600, 400, 300, 250, 200, 150]:
            search_key = search_text[:search_len]
            if search_key in page_norm:
                return (pdf_idx, page_num)  # GEFUNDEN!
    
    # === SCHRITT 3c: Fallback - Fuzzy Matching ===
    best_match = None
    für (pdf_idx, page_num, page_text) in page_texts:
        page_norm = normalize_text(page_text)
        
        # Sliding Window über die Seite
        für start in range(0, len(page_norm) - 150, 50):
            window = page_norm[start:start + 150]
            ratio = SequenceMatcher(None, search_text[:150], window).ratio()
            
            if ratio > 0.80 and (best_match is None or ratio > best_match[0]):
                best_match = (ratio, pdf_idx, page_num)
    
    if best_match and best_match[0] > 0.80:
        return (best_match[1], best_match[2])
    
    return None  # Nicht gefunden
```

**Beispiel:**
```
Vortrag GA198/1:
  Absatz 1: "ERSTER VORTRAG"                    → zu kurz, übersprungen
  Absatz 2: "Dornach, 20. März 1920"            → Metadaten, übersprungen  
  Absatz 3: "Was heute den Menschen als eine fast unumstrittene Autorität 
             gilt, das ist Wissenschaft..."     → 200+ Zeichen, Fließtext ✓

Suche im PDF:
  Seite 7 (Inhalt): enthält "Erster Vortrag...Seite 13" → Nein (falscher Text)
  Seite 12 (S.13): enthält "Was heute den Menschen als eine fast..." → JA!

Ergebnis: GA198/1 → Seite 13
```

#### Schritt 4: Mapping speichern
```python
mapping = {
    "GA198/1": 13,
    "GA198/2": 25,
    "GA198/3": 42,
    ...
}

# Lade bestehendes Mapping und erweitere
existing = load_json("lecture-page-mapping.json")
existing["GA198"] = mapping
save_json("lecture-page-mapping.json", existing)
```

### Output

| Datei | Pfad | Format |
|-------|------|--------|
| Lecture-Mapping | `lecture-page-mapping.json` | JSON |

**Struktur:**
```json
{
  "_info": "Lecture-ID → Start-Seitenzahl im PDF",
  "GA198": {
    "GA198/1": 13,
    "GA198/2": 25,
    "GA198/3": 42,
    "GA198/4": 57
  },
  "GA199": {
    "GA199/1": 11,
    "GA199/2": 28
  }
}
```

### Aufruf

```powershell
# Mapping für eine GA generieren
python generate_lecture_page_mapping.py GA198

# Nach dem Mapping: Pagebreaks neu generieren
python batch_generate_pagebreaks.py 198 198
```

### Wann dieses Skript verwenden?

- **Vor** dem ersten Pagebreak-Generieren für eine neue GA
- Wenn viele Vorträge mit "no-match" im Report sind
- Wenn die automatische Start-Seiten-Erkennung fehlschlägt

---

## 10. Batch-Verarbeitung

### Skript: `batch_generate_pagebreaks.py`

Batch-Verarbeitung: Führt `export_page_markers_v4.py` und `apply_page_break_markers_v4.py` automatisch für einen Bereich von GA-Bänden aus.

### Input-Daten

| Quelle | Beschreibung |
|--------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` |
| Bestehende Pagebreaks | `pagebreaks/GA*.json` (zum Überspringen bereits verarbeiteter) |

### Verarbeitungsschritte (detailliert)

```python
def main():
    # Parameter: python batch_generate_pagebreaks.py 198 200
    start_ga = 198
    end_ga = 200
    
    für ga_num in range(start_ga, end_ga + 1):
        ga_str = f"GA{ga_num:03d}"  # "GA198"
        
        # === SCHRITT 1: PDF prüfen ===
        pdf_path = find_pdf_for_ga(ga_num)
        if not pdf_path:
            print(f"⚠️ {ga_str}: Keine PDF")
            no_pdf += 1
            continue
        
        # === SCHRITT 2: Bereits verarbeitet? ===
        if (PAGEBREAK_DIR / f"{ga_str}.json").exists():
            print(f"✓ {ga_str}: Bereits verarbeitet (übersprungen)")
            skipped += 1
            continue
        
        # === SCHRITT 3: export_page_markers_v4.py aufrufen ===
        print(f"[1/2] Exportiere Page-Break-Marker für {ga_str}...")
        subprocess.run([
            "python", "export_page_markers_v4.py", ga_str
        ])
        # → Schreibt/erweitert page-break-markers.json
        
        # === SCHRITT 4: apply_page_break_markers_v4.py aufrufen ===
        print(f"[2/2] Wende Marker auf Vorträge an...")
        subprocess.run([
            "python", "apply_page_break_markers_v4.py", ga_str,
            "--out", f"pagebreaks/{ga_str}.json",
            "--report", f"pagebreaks/{ga_str}-report.json"
        ])
        # → Erzeugt pagebreaks/GA198.json und GA198-report.json
        
        processed += 1
    
    # === SCHRITT 5: Zusammenfassung ===
    print(f"Verarbeitet: {processed}")
    print(f"Bereits fertig: {skipped}")
    print(f"Keine PDF: {no_pdf}")
    print(f"Fehlgeschlagen: {failed}")
```

**Beispiel-Ausgabe:**
```
============================================================
Batch-Generierung Seitenzahlen: GA198 bis GA200
============================================================

============================================================
Verarbeite GA198...
PDF: Steiner, Rudolf GA 198 1984 - Heilfaktoren für den sozialen Organismus.pdf
============================================================

[1/2] Exportiere Page-Break-Marker...
  PDF-Seiten: 320, erkannte gedruckte Seiten: 320 (100.0%)
  Breaks erzeugt: 318

[2/2] Wende Marker auf Vorträge an...
  Vorträge mit Start-Seite: 17 von 17
  eingefügt 265/318 (83.3%)
  ✓ GA198 erfolgreich verarbeitet!

  ✓ GA199: Bereits verarbeitet (übersprungen)
  ⚠️ GA200: Keine PDF

============================================================
ZUSAMMENFASSUNG
============================================================
  Verarbeitet:     1
  Bereits fertig:  1
  Keine PDF:       1
  Fehlgeschlagen:  0
============================================================
```

### Output

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Break-Marker | `page-break-markers.json` | Wird erweitert |
| Pagebreaks | `pagebreaks/GA*.json` | Pro GA eine Datei |
| Reports | `pagebreaks/GA*-report.json` | Pro GA ein Report |

### Aufruf

```powershell
# Standardbereich GA052-150
python batch_generate_pagebreaks.py

# Spezifischer Bereich
python batch_generate_pagebreaks.py 198 200

# Einzelne GA
python batch_generate_pagebreaks.py 198 198

# Nur prüfen welche PDFs existieren (ohne Verarbeitung)
python batch_generate_pagebreaks.py --check
```

---

## 11. Datenfluss-Diagramm

### Gesamt-Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        QUELLDATEN                                       │
└─────────────────────────────────────────────────────────────────────────┘
         │                              │                    │
         ▼                              ▼                    ▼
┌─────────────────┐          ┌─────────────────┐   ┌─────────────────┐
│  Markdown (.md) │          │  PDF-Dateien    │   │  Bilder (.webp) │
│  Steiner_GA/    │          │  Steiner_GA_pdf/│   │  Steiner_GA/    │
│  GAXXX-Titel/   │          │  *.pdf          │   │  */assets/      │
└────────┬────────┘          └────────┬────────┘   └────────┬────────┘
         │                            │                      │
         ├────────────────────────────┼──────────────────────┘
         │                            │
         ▼                            │
┌─────────────────────────────────────┴───────────────────────────────────┐
│                        EXPORT_MASTER.PY                                 │
│  ───────────────────────────────────────────────────────────────────── │
│  1. Bildpfade korrigieren (JPEG→WebP, Wiki-Links→Markdown)             │
│  2a. Bücher exportieren (export_books_master.py) → steiner-books/      │
│  2b. Vorträge exportieren (export-lectures.js) → steiner-full-lectures/│
└─────────────────────────────────────────────────────────────────────────┘
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────────────────────────────────┐
│  steiner-books/ │          │  steiner-full-lectures/                    │
│  *.json         │          │  steiner-full-lectures-XXX-XXX.json        │
└────────┬────────┘          └─────────────────────┬───────────────────────┘
         │                                         │
         │                                         │
         │            ┌────────────────────────────┘
         │            │
         │            ▼
         │   ┌─────────────────────────────────────────────────────────────┐
         │   │           PDF-VERARBEITUNG (Seitenzahlen)                   │
         │   │  ─────────────────────────────────────────────────────────  │
         │   │                                                             │
         │   │    ┌─────────────────────┐      ┌─────────────────────────┐ │
         │   │    │ export_page_markers │      │ generate_lecture_page   │ │
         │   │    │     _v4.py          │      │     _mapping.py         │ │
         │   │    │                     │      │                         │ │
         │   │    │ • Seitenzahlen aus  │      │ • Vortrag-Text im PDF   │ │
         │   │    │   PDF extrahieren   │      │   suchen                │ │
         │   │    │ • Fließtext an      │      │ • Start-Seite pro       │ │
         │   │    │   Umbrüchen         │      │   Vortrag finden        │ │
         │   │    └──────────┬──────────┘      └───────────┬─────────────┘ │
         │   │               │                             │               │
         │   │               ▼                             ▼               │
         │   │    ┌─────────────────────┐      ┌─────────────────────────┐ │
         │   │    │ page-break-markers  │      │ lecture-page-mapping    │ │
         │   │    │       .json         │      │        .json            │ │
         │   │    └──────────┬──────────┘      └───────────┬─────────────┘ │
         │   │               │                             │               │
         │   │               └──────────────┬──────────────┘               │
         │   │                              │                              │
         │   │                              ▼                              │
         │   │               ┌───────────────────────────────┐             │
         │   │               │ apply_page_break_markers_v4.py│             │
         │   │               │ (Bücher)                      │             │
         │   │               │ apply_pagebreaks_from_pdf.py  │             │
         │   │               │ (Vorträge - direkt aus PDF)   │             │
         │   │               │                               │             │
         │   │               │ • Fuzzy-Matching im Text      │             │
         │   │               │ • |page| Marker einfügen      │             │
         │   │               └───────────────┬───────────────┘             │
         │   │                               │                             │
         │   └───────────────────────────────┼─────────────────────────────┘
         │                                   │
         │                      ┌────────────┴────────────┐
         │                      │                         │
         │                      ▼                         ▼
         │       ┌───────────────────────┐   ┌───────────────────────┐
         │       │   pagebreaks/         │   │ apply_pagebreaks_to_  │
         │       │   GA*.json            │   │     md.py             │
         │       │   (Override für       │   │                       │
         │       │    HTML-Anzeige)      │   │ • Marker in MD-       │
         │       └───────────┬───────────┘   │   Dateien übertragen  │
         │                   │               │ • Für Obsidian        │
         │                   │               └───────────┬───────────┘
         │                   │                           │
         │                   │                           ▼
         │                   │               ┌───────────────────────┐
         │                   │               │ Steiner_GA/           │
         │                   │               │   GAXXX-Titel/*.md    │
         │                   │               │   (mit |page| Markern)│
         │                   │               └───────────────────────┘
         │                   │
         └───────────────────┼───────────────────────────────────────
                             │
                             ▼
                  ┌─────────────────────────────┐
                  │        backend.js           │
                  │  (lädt alle JSON-Dateien)   │
                  │                             │
                  │  • steiner-books/*.json     │
                  │  • steiner-full-lectures/   │
                  │  • pagebreaks/ (Override)   │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │        Frontend (Browser)   │
                  │                             │
                  │  • Suche in allen Texten    │
                  │  • Seitenzahlen anzeigen    │
                  │  • Überschriften-Navigation │
                  └─────────────────────────────┘
```

---

## 12. Backend-Integration

Das Backend (`backend.js`) lädt beim Start automatisch die Pagebreak-Overrides aus `pagebreaks/`:

```javascript
// Zeile 729-760 in backend.js
const overridesDir = path.join(__dirname, 'pagebreaks');
const overrideFiles = files.filter(f => /^GA\d{3}[a-z]?\.json$/i.test(f));

// Für jeden Override: Ersetze die Vorträge/Bücher mit den Versionen
// die |page|-Marker enthalten
```

**Wichtig:** Nach dem Generieren neuer Pagebreaks muss der Server neu gestartet werden, damit die Änderungen geladen werden!

---

## 13. Typische Workflow-Beispiele

### A) EMPFOHLEN: Vorträge/Aufsätze mit process_pagebreaks.py

**Der einfachste Weg für GA029-044 und GA051+:**

```powershell
# Einzelne GA verarbeiten (PDF → JSON → MD)
python tools/process_pagebreaks.py GA198

# Bereich verarbeiten
python tools/process_pagebreaks.py 151 200

# Parallel (schneller)
python tools/process_pagebreaks.py 151 200 --workers 4

# Server neu starten!
# Im Server-Terminal: Ctrl+C, dann: nb
```

### B) EMPFOHLEN: Bücher mit process_books_v4.py

**Für GA001-028 und GA045:**

```powershell
# Voraussetzung: Anker müssen in page-break-markers.json existieren
# Falls nicht: python export_page_markers_v4.py GA001

# Einzelnes Buch
python process_books_v4.py GA001

# Bereich
python process_books_v4.py 1 28

# Mit GA045
python process_books_v4.py 1 28 GA045

# Server neu starten!
```

### C) Einen neuen GA-Band komplett exportieren

```powershell
# 1. Markdown exportieren (mit Bildpfad-Korrektur)
python export_master.py GA068c

# 2. Seitenzahlen einfügen (Vorträge)
python tools/process_pagebreaks.py GA068c

# 3. Server neu starten
# Ctrl+C im Server-Terminal, dann: nb
```

### D) Batch-Verarbeitung mehrerer GA-Bände

```powershell
# Alte Methode (ohne MD-Update)
python batch_generate_pagebreaks.py 190 200

# Neue Methode (mit MD-Update) - EMPFOHLEN
python tools/process_pagebreaks.py 190 200 --workers 4
```

### E) Wenn Vorbemerkung/Einleitung nicht passt (contentRange)

```powershell
# Beispiel: GA045 - Vorbemerkung (S.7-10) ausschließen
python -c "
import json
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
data['GA045']['contentRange'] = [11, 104]  # Ab Seite 11
with open('page-break-markers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

# Buch neu verarbeiten
python process_books_v4.py GA045
```

### F) Prüfen welche GAs verarbeitet wurden

```powershell
# Zeige alle pagebreaks/*.json Dateien
Get-ChildItem pagebreaks/*.json | Select-Object Name, Length, LastWriteTime

# Prüfe ob Marker in JSON vorhanden sind
python -c "
import json, re
with open('pagebreaks/GA198.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
lecs = data.get('lectures', [])
for l in lecs[:3]:
    markers = sum(len(re.findall(r'\|\d+\|', p.get('content',''))) for p in l.get('paragraphs',[]))
    print(f'{l.get(\"ID\")}: {markers} Marker')
"
```

### G) Wenn viele "no-match" Fehler auftreten

```powershell
# 1. Erst Lecture-Mapping (neu) erstellen
python generate_lecture_page_mapping.py GA198

# 2. Dann mit process_pagebreaks neu verarbeiten
python tools/process_pagebreaks.py GA198
```

### H) Nur MD-Dateien aktualisieren (JSON bereits fertig)

```powershell
# Einzelne GA
python tools/apply_pagebreaks_to_md.py GA198

# Bereich
python tools/apply_pagebreaks_to_md.py 151 200
```

---

## 14. Fehlerbehebung

### Problem: Seitenzahlen nicht sichtbar in HTML

1. **Server neu starten** (wichtigster Schritt!):
   ```powershell
   # Im Server-Terminal: Ctrl+C, dann:
   nb
   ```

2. **Prüfen ob Override-Datei existiert:**
   ```powershell
   Test-Path pagebreaks/GA198.json
   # Muss True sein!
   ```

3. **Prüfen ob Marker in der Datei sind:**
   ```powershell
   python -c "import json,re; d=json.load(open('pagebreaks/GA198.json','r',encoding='utf-8')); print(sum(len(re.findall(r'\|\d+\|',p.get('content',''))) for l in d.get('lectures',[]) for p in l.get('paragraphs',[])))"
   # Sollte > 0 sein
   ```

### Problem: Erste Seitenzahl ist falsch (z.B. |1| statt |7|)

**Ursache:** Die contentRange ist falsch oder fehlt.

**Lösung:**
```powershell
# 1. Prüfe aktuelle contentRange
python -c "import json; d=json.load(open('page-break-markers.json','r',encoding='utf-8')); print(d.get('GA001',{}).get('contentRange'))"

# 2. Setze korrekte contentRange
python -c "
import json
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
data['GA001']['contentRange'] = [7, 500]  # Ab Seite 7
with open('page-break-markers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

# 3. Neu verarbeiten
python process_books_v4.py GA001
```

### Problem: Vorbemerkung hat falsche Seitenzahlen (PDF ≠ MD)

**Ursache:** Die Vorbemerkung im PDF ist anders als in der MD-Datei.

**Lösung:** contentRange so setzen, dass die Vorbemerkung übersprungen wird:
```powershell
# Beispiel: GA045 - Vorbemerkung ist S.7-10, Haupttext ab S.11
python -c "
import json
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
data['GA045']['contentRange'] = [11, 104]  # Überspringe S.7-10
with open('page-break-markers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"
python process_books_v4.py GA045
```

### Problem: GA nicht in page-break-markers.json

**Ursache:** Die Anker wurden noch nicht aus dem PDF extrahiert.

**Lösung:**
```powershell
# Anker aus PDF extrahieren
python export_page_markers_v4.py GA198

# Prüfen
python -c "import json; d=json.load(open('page-break-markers.json','r',encoding='utf-8')); print('GA198' in d)"
```

### Problem: Viele "no-match" Fehler bei Vorträgen

**Mögliche Ursachen:**
- Falsche Start-Seitenzahlen pro Vortrag
- PDF-OCR-Fehler
- Große Textunterschiede zwischen PDF und MD

**Lösungen:**
```powershell
# 1. Lecture-Mapping neu generieren
python generate_lecture_page_mapping.py GA198

# 2. Prüfen ob Mapping korrekt
python -c "import json; d=json.load(open('lecture-page-mapping.json','r',encoding='utf-8')); print(d.get('GA198',{}))"

# 3. Neu verarbeiten
python tools/process_pagebreaks.py GA198
```

### Problem: Seitenzahlen an falscher Stelle (mitten im Wort)

**Hinweis:** Bei Silbentrennung im PDF ist das korrekt! 
Beispiel: `Philo|25|sophie` bedeutet, dass Seite 25 nach "Philo-" beginnt.

**Wenn wirklich falsch:**
- Break-Anker in `page-break-markers.json` manuell prüfen
- PDF mit besserer OCR-Qualität verwenden

### Problem: Export zeigt "Keine Absatz-Indizes gefunden"

- Die Markdown-Datei muss `^`-Indizes am Ende jedes Absatzes haben
- Format: `Text des Absatzes ^abc123`
- Bücher ohne Indizes können nicht korrekt exportiert werden

### Problem: Überschriften werden nicht verknüpft

- Prüfen ob Absätze Indizes haben (`^...` am Zeilenende)
- Überschriften müssen im Format `###` oder `####` vorliegen
- Nach der Umwandlung sollte jede Überschrift einen `index` haben

### Problem: process_pagebreaks.py hängt

**Mögliche Ursachen:**
- Sehr große GA mit vielen Vorträgen
- Windows-spezifisches Threading-Problem

**Lösung:** Sequenziell verarbeiten:
```powershell
python tools/process_pagebreaks.py GA198 --sequential
```

---

## Technische Details

### Normalisierung für Matching

| Original | Normalisiert | Grund |
|----------|--------------|-------|
| `Thatsachen` | `tatsachen` | Alte Orthographie |
| `daß` | `dass` | Alte Rechtschreibung |
| `ﬁnden` | `finden` | Ligatur |
| `Philo-<br>sophie` | `philosophie` | Silbentrennung |

### Marker-Format

```
Text vor Seitenumbruch|14|Text der nächsten Seite
```

Der Marker `|14|` bedeutet: "Hier beginnt Seite 14 des gedruckten Buches."

### Dateigrößen-Limits

| Datei | Max. Größe | Grund |
|-------|-----------|-------|
| JSON-Dateien | 10 MB | GitHub-Limit |
| Bilder (Base64) | ~ 1 MB | Browser-Performance |

---

*Letzte Aktualisierung: Januar 2026*
