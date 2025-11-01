# Steiner Lectures Export - Anleitung

## Übersicht

Es gibt zwei Möglichkeiten, Vorträge aus Obsidian zu exportieren:

1. **Obsidian Plugin** (für gelegentlichen Gebrauch)
2. **Node.js Script** (schnell, automatisiert, empfohlen für große Mengen)

Beide Methoden exportieren jetzt:
- ✅ Vollständigen Text der Vorträge
- ✅ Metadaten (GA-Nummer, Datum, Ort, etc.)
- ✅ **NEU: Inhaltsverzeichnis** (Table of Contents)
- ⏳ Keywords (kommt später)

---

## Option 1: Obsidian Plugin

### Installation
Das Plugin ist bereits installiert unter:
```
Steiner_GA/.obsidian/plugins/steiner-full-lectures-exporter/
```

### Verwendung in Obsidian

1. **Öffne Obsidian** mit dem Steiner_GA Vault
2. **Öffne Command Palette** (Ctrl/Cmd + P)
3. **Suche nach**: "Steiner Full Lectures Exporter"
4. **Gib GA-Nummern ein**:
   - Einzelne: `GA051, GA052`
   - Bereich: `GA051-GA060`
   - Alle: Feld leer lassen
5. **Warte** auf Export-Bestätigung
6. **Dateien** werden im Vault-Root erstellt

### Ausgabe
- `steiner-full-lectures-XXX-YYY.json` (eine Datei)
- Oder `steiner-full-lectures-XXX-YYY-partNN.json` (mehrere Teile bei >10 MB)

---

## Option 2: Node.js Script (EMPFOHLEN)

### Vorteile
- ⚡ 5-10x schneller als Plugin
- 🤖 Automatisierbar
- 💻 Läuft ohne Obsidian
- 📦 Ideal für 3000+ Vorträge

### Verwendung

#### Alle Vorträge exportieren:
```bash
npm run export-lectures
```

#### Nur bestimmte GAs exportieren:
```bash
npm run export-lectures:ga GA051,GA052
```

oder mit Bereich:
```bash
npm run export-lectures:ga GA051-GA060
```

#### Direkter Aufruf:
```bash
# Alle Vorträge (mit automatischer Sync)
node export-lectures.js

# Bestimmte GAs (mit automatischer Sync)
node export-lectures.js GA051,GA052
node export-lectures.js GA051-GA060

# Ohne automatische Sync (schneller)
node export-lectures.js --no-sync
node export-lectures.js GA051,GA052 --no-sync
```

### Ausgabe
Die Dateien werden im `ga_suche/` Ordner erstellt:
- `steiner-full-lectures-051-311.json` (alle Vorträge)
- Oder mehrere Teile: `steiner-full-lectures-051-311-part01.json`, etc.

---

## Nach dem Export

### 🔄 Automatische Metadaten-Synchronisation (NEU!)

Nach jedem Export werden automatisch die Metadaten (Datum, Jahr, Ort) in bestehenden Datenbanken aktualisiert:

✅ **Synchronisiert automatisch:**
- `keywords-database.json` → Datum/Jahr aus fullLectures
- Extrahiert Datum aus `location`/`fileName` wenn nötig
- Aktualisiert nur geänderte Einträge

**Deaktivieren (falls gewünscht):**
```bash
node export-lectures.js --no-sync
```

### Neue Vorträge hinzufügen

Wenn neue Vorträge in Obsidian hinzugefügt werden:

1. **Einfach neu exportieren**:
   ```bash
   npm run export-lectures
   # oder
   node export-lectures.js
   ```
   
2. Die alten JSON-Dateien werden überschrieben
3. **Automatische Sync** aktualisiert keywords-database.json
4. Das Frontend lädt automatisch die neuen Daten

### Manuelle Synchronisation

Falls Sie nur Metadaten aktualisieren möchten (ohne Export):
```bash
node sync-metadata-from-fulllectures.js
```

### Prüfen, ob es funktioniert hat

1. **Öffne**: `ga_suche/index.html` im Browser
2. **Lade einen Vortrag**: z.B. GA051/1
3. **Prüfe das Summary Panel** (rechts):
   - ✅ "Inhaltsverzeichnis" sollte sichtbar sein
   - ✅ Klickbare Links zu Kapiteln
   - ✅ Kursive Beschreibungen unter jedem Link

---

## Dateistruktur

### Input (Obsidian Markdown)
```markdown
Quelle: [[GA051 - Über Philosophie...]]

_Zusammenfassung..._

[[Schlagwort1]] - [[Schlagwort2]] - [[Schlagwort3]]

### Inhaltsverzeichnis ^abc123

- [[#Die griechischen Naturphilosophen]] - _Beschreibung..._
- [[#Heraklit und die Lehre vom ewigen Wandel]] - _Beschreibung..._

---

### Die griechischen Naturphilosophen ^xyz789

Text text text...
```

### Output (JSON)
```json
{
  "lectures": [
    {
      "gaNumber": "GA051",
      "lectureNumber": "1",
      "ID": "GA051/1",
      "title": "WELT- UND LEBENSANSCHAUUNGEN...",
      "date": "1901-03-11",
      "location": "Berlin",
      "tableOfContents": [
        {
          "heading": "Die griechischen Naturphilosophen",
          "description": "Die ersten westlichen Denker..."
        },
        {
          "heading": "Heraklit und die Lehre vom ewigen Wandel",
          "description": "Heraklits Philosophie..."
        }
      ],
      "paragraphs": [
        {
          "index": "^xyz789",
          "content": "Text text text..."
        }
      ]
    }
  ]
}
```

---

## Troubleshooting

### "No matching lectures found"
- Prüfe, ob die Markdown-Dateien das richtige Format haben
- Dateinamen müssen beginnen mit: `GA051 (1.) TITEL...`

### "Cannot find module..."
- Installiere Dependencies: `npm install`

### JSON-Dateien sind leer
- Prüfe Pfade in `export-lectures.js`:
  - `sourceDir`: `../Steiner_GA`
  - `outputDir`: `./` (aktuelles Verzeichnis)

### TOC erscheint nicht im Frontend
- Prüfe, ob `tableOfContents` im JSON vorhanden ist
- Öffne JSON-Datei und suche nach `"tableOfContents": [`
- Öffne Browser DevTools (F12) und prüfe Console auf Fehler

### Nur alte TOC-Struktur sichtbar
- Exportiere neu mit aktualisierten Scripten
- Leere Browser-Cache (Ctrl+F5)

---

## Features

- ✅ Volltext-Export (Vorträge + Überschriften)
- ✅ Metadaten-Extraktion (Datum, Ort, GA-Info)
- ✅ **Verbesserte Datum-Extraktion** (findet Datum auch in der Mitte, mit Präfixen, etc.)
- ✅ **Automatische Metadaten-Synchronisation** (nach jedem Export)
- ✅ Chunking (automatische Aufteilung bei großen Exporten)
- ✅ CLI mit Optionen (--no-sync)

## Nächste Schritte

- [ ] Incremental updates (nur geänderte Dateien)
- [ ] File watcher (automatischer Export bei Änderungen)

---

## Technische Details

### Parse-Logik

Das Inhaltsverzeichnis wird wie folgt erkannt:

1. **Start**: Zeile mit `### Inhaltsverzeichnis`
2. **Einträge**: Zeilen mit Format: `- [[#Überschrift]] - _Beschreibung_`
3. **Ende**: Trennlinie `---` oder nächste H3-Überschrift

### Regex für TOC-Einträge
```javascript
/^-\s*\[\[#(.+?)\]\]\s*-\s*_(.+?)_\s*$/
```

### Frontend-Matching
Die TOC-Links suchen nach H3-Überschriften mit identischem Text und scrollen dorthin.

---

**Erstellt**: 2025-10-25  
**Version**: 1.0  
**Autor**: Export Script Extension

