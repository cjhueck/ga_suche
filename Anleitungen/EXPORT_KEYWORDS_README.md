# Export Keywords (Schlagwörter A-Z)

## Übersicht

Das Script `export-keywords.js` exportiert handkuratierte Schlagwörter aus den Obsidian-Markdown-Dateien (`Steiner_GA/Schlagwörter A-Z/`) in JSON-Format für die Integration in die Web-Anwendung.

## Voraussetzungen

- Node.js installiert
- Markdown-Dateien in `Steiner_GA/Schlagwörter A-Z/` (A.md bis Z.md)

## Verwendung

### Alle Schlagwörter exportieren

```bash
node export-keywords.js
```

Erstellt: `schlagworte-az-all.json`

### Einzelnen Buchstaben exportieren

```bash
node export-keywords.js A
```

Erstellt: `schlagworte-az-a.json`

### Mehrere Buchstaben exportieren

```bash
node export-keywords.js A,B,C
```

Erstellt: `schlagworte-az-a-c.json`

### Bereich exportieren

```bash
node export-keywords.js A-F
```

Erstellt: `schlagworte-az-a-f.json`

### Kombinationen

```bash
node export-keywords.js A,C,E-H,Z
```

## Ausgabe

Das Script erstellt eine JSON-Datei mit folgender Struktur:

```json
{
  "source": "Schlagwörter A-Z (Obsidian)",
  "exportDate": "2025-10-27T...",
  "letters": ["A", "B", "C"],
  "keywords": [
    {
      "keyword": "Abbauprozesse",
      "alphabetical": "A",
      "text": "**Abbauprozesse** stellen einen grundlegenden...",
      "gaReferences": ["GA066/1", "GA067/4", "GA067/10"],
      "source": "obsidian-az"
    }
  ]
}
```

## Frontend-Integration

### Automatisches Laden

Die exportierten Keywords werden automatisch beim Start der Anwendung geladen und mit den bestehenden Keywords zusammengeführt.

**Funktionsweise:**
1. `loadKeywordsData()` lädt zunächst bestehende Keywords
2. `loadObsidianKeywords()` sucht nach exportierten JSON-Dateien
3. Neue Keywords werden hinzugefügt (keine Duplikate)
4. Alphabetische Sortierung

**Unterstützte Dateinamen:**
- `schlagworte-az-all.json`
- `schlagworte-az-a.json` bis `schlagworte-az-z.json`
- `schlagworte-az-a-f.json` (Bereiche)

### Link-Konvertierung

GA-Referenzen in den Obsidian-Dateien werden automatisch in klickbare Links umgewandelt:

**Input (Markdown):**
```markdown
[[GA066 (1.) GEIST UND STOFF|GA066/1]]
```

**Output (HTML):**
```html
<a href="#" onclick="showLecture('GA066/1')">GA066/1</a>
```

**Hinweis:** Links öffnen den Vortrag **ohne** Absatz-Sprung (da die Obsidian-Keywords keine Block-IDs enthalten).

## Integration rückgängig machen

**Einfaches Löschen der JSON-Datei:**

```bash
# Windows
del schlagworte-az-all.json

# Linux/Mac
rm schlagworte-az-all.json
```

Nach dem Löschen:
1. Anwendung neu starten
2. Exportierte Keywords werden nicht mehr geladen
3. Nur noch bestehende Keywords aus anderen Quellen werden angezeigt

## Workflow-Beispiel

### Schritt 1: Export durchführen

```bash
# Alle Buchstaben exportieren
node export-keywords.js

# Ausgabe:
# 🎯 Exporting ALL letters (A-Z)
# 📖 Processing A.md...
#    ✓ Extracted 45 keywords from A.md
# ...
# ✅ Total keywords extracted: 1234
# 💾 Exported to: schlagworte-az-all.json
# 💡 To undo integration: Delete schlagworte-az-all.json
```

### Schritt 2: Anwendung öffnen

1. Öffne `index.html` im Browser
2. Wechsle zum Tab "Index"
3. Die exportierten Keywords erscheinen automatisch

### Schritt 3: Keywords aktualisieren

Wenn Änderungen an den Markdown-Dateien vorgenommen wurden:

```bash
# Neu exportieren
node export-keywords.js

# Datei wird überschrieben
# Anwendung im Browser neu laden (F5)
```

### Schritt 4: Integration entfernen (optional)

```bash
del schlagworte-az-all.json
# Anwendung neu laden
```

## Fehlerbehebung

### Keywords werden nicht angezeigt

**Prüfen:**
1. Wurde das Script erfolgreich ausgeführt?
2. Existiert die JSON-Datei im `ga_suche` Ordner?
3. Browser-Konsole öffnen (F12) und nach `[OBSIDIAN-KW]` Meldungen suchen

**Lösung:**
```bash
# Script erneut ausführen
node export-keywords.js

# Browser-Cache leeren
# Seite neu laden (Strg+Shift+R)
```

### GA-Links funktionieren nicht

**Prüfen:**
- Format der GA-Referenzen in den MD-Dateien: `[[GA###/#]]` oder `[[TITEL|GA###/#]]`
- Browser-Konsole auf JavaScript-Fehler prüfen

### Duplikate erscheinen

Das sollte nicht passieren, da `loadObsidianKeywords()` Duplikate filtert. Falls doch:

**Prüfen:**
- Unterschiedliche Schreibweise? (`Abbauprozesse` vs `Abbau-Prozesse`)
- Verschiedene Quellen aktiv?

## Technische Details

### Parsing-Logik

1. **Keyword-Extraktion:** `## [[Keyword]]` Überschriften
2. **Text-Extraktion:** Alles zwischen zwei `##` Überschriften
3. **GA-Referenzen:** Regex-Matching für `[[GA###/# ...]]` Format
4. **Formatierung:** Behält Markdown-Formatierung (`**fett**`)

### Merge-Strategie

- **Duplikate:** Werden über `keyword`-String erkannt und übersprungen
- **Sortierung:** Alphabetisch nach `keyword.localeCompare()`
- **Metadaten:** `source: 'obsidian-az'` markiert die Herkunft

## Best Practices

1. **Regelmäßiger Export:** Nach jeder Bearbeitung der MD-Dateien neu exportieren
2. **Einzelbuchstaben:** Bei großen Änderungen nur betroffene Buchstaben exportieren
3. **Backup:** JSON-Dateien vor Überschreiben sichern
4. **Versionierung:** Export-Datum ist in JSON enthalten für Tracking

## Erweiterungsmöglichkeiten

### Zukünftig: Absatz-IDs hinzufügen

Momentan verlinken die GA-Referenzen nur auf den Vortrag (ohne Absatz-Sprung).

**Mögliche Erweiterung:**
1. Obsidian-Format erweitern: `[[GA066/1#^abc123]]`
2. Parser anpassen für Block-ID-Extraktion
3. Link-Generierung: `showLecture('GA066/1', '^abc123')`

### Automatischer Export

```bash
# Watch-Script für automatischen Export bei MD-Änderungen
# (Benötigt zusätzliches Tool wie nodemon oder chokidar)

npx nodemon --watch ../Steiner_GA/Schlagwörter\ A-Z/ --exec "node export-keywords.js"
```

## Support

Bei Problemen:
1. Browser-Konsole (F12) prüfen
2. JSON-Datei auf Syntax-Fehler prüfen
3. Script mit Testdaten ausführen

