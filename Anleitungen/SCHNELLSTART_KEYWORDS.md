# Schnellstart: Obsidian Keywords integrieren

## ✅ Was wurde implementiert?

Ein **statisches Export-System** für die handkuratierten Schlagwörter aus `Steiner_GA/Schlagwörter A-Z/`:

1. **Export-Script:** `export-keywords.js`
2. **Frontend-Integration:** Automatisches Laden und Mergen
3. **Rückgängig-Funktion:** Einfaches Löschen der JSON-Datei

## 🚀 Sofort loslegen

### Schritt 1: Keywords exportieren

```bash
cd ga_suche
node export-keywords.js
```

**Ergebnis:** `schlagworte-az-all.json` mit **1961 Keywords** und **6330 GA-Referenzen**

### Schritt 2: Anwendung öffnen

1. Öffne `index.html` im Browser
2. Wechsle zum Tab **"Index"** (ehemals "Schlagworte")
3. ✨ Die exportierten Keywords erscheinen automatisch!

### Schritt 3: Testen

- **Alphabet-Navigation:** Klicke auf Buchstaben A-Z
- **Suche:** Gebe Suchbegriff ein
- **GA-Links:** Klicke auf GA-Referenzen → Vortrag öffnet sich

## 📋 Verfügbare Export-Optionen

```bash
# Alle Buchstaben
node export-keywords.js

# Einzelner Buchstabe
node export-keywords.js A

# Mehrere Buchstaben
node export-keywords.js A,B,C

# Bereich
node export-keywords.js A-F

# Kombination
node export-keywords.js A,C,E-H,Z
```

## 🔄 Keywords aktualisieren

Nach Änderungen an den Markdown-Dateien:

```bash
node export-keywords.js       # Neu exportieren
# Dann Browser neu laden (F5)
```

## ❌ Integration rückgängig machen

```bash
# Windows
del schlagworte-az-all.json

# Linux/Mac
rm schlagworte-az-all.json

# Danach: Browser neu laden
```

## 📊 Aktuelle Statistik

Nach dem Export:

- **Total Keywords:** 1961
- **GA-Referenzen:** 6330
- **Dateigröße:** 1.80 MB
- **Buchstaben:** A-Z (26)

**Verteilung:**
- **Meiste Keywords:** S (221), G (206), M (140)
- **Wenigste Keywords:** Q (1), X (1), Y (2)

## 🔗 Link-Funktionalität

**Obsidian-Format:**
```markdown
[[GA066 (1.) GEIST UND STOFF|GA066/1]]
```

**Frontend-Konvertierung:**
```html
<a href="#" onclick="showLecture('GA066/1')">GA066/1</a>
```

**Hinweis:** Links öffnen den **gesamten Vortrag** (kein Absatz-Sprung), da die Obsidian-Keywords keine Block-IDs enthalten.

## 🎯 Workflow-Empfehlung

1. **Initial:** Export aller Keywords durchführen
2. **Laufend:** Bei Bedarf einzelne Buchstaben neu exportieren
3. **Testen:** Browser regelmäßig neu laden
4. **Backup:** JSON-Dateien vor größeren Änderungen sichern

## 🔍 Debugging

### Keywords werden nicht angezeigt?

**Browser-Konsole öffnen (F12):**
```
Suche nach: [OBSIDIAN-KW]
Erwartete Meldung: "✓ X neue Schlagwörter aus Obsidian A-Z hinzugefügt"
```

**Prüfen:**
- [ ] Existiert `schlagworte-az-all.json` im `ga_suche` Ordner?
- [ ] Browser-Cache geleert? (Strg+Shift+R)
- [ ] Datei valides JSON? (mit JSON-Validator prüfen)

### GA-Links funktionieren nicht?

**Prüfen:**
- Format in MD-Dateien korrekt? (`[[GA###/#]]`)
- JavaScript-Fehler in Browser-Konsole?
- Vortrag existiert in der Datenbank?

## 📖 Vollständige Dokumentation

Siehe: `EXPORT_KEYWORDS_README.md`

## 💡 Zukünftige Erweiterungen

### Absatz-IDs hinzufügen (optional)

Momentan: `showLecture('GA066/1')` → öffnet Vortrag

Möglich: `showLecture('GA066/1', '^abc123')` → springt zu Absatz

**Voraussetzung:** Block-IDs in Obsidian-Markdown hinzufügen

### Auto-Export (optional)

```bash
# Watch-Modus für automatischen Export
npx nodemon --watch ../Steiner_GA/Schlagwörter\ A-Z/ --exec "node export-keywords.js"
```

## ✨ Features

- ✅ **1961 handkuratierte Keywords** aus Obsidian integriert
- ✅ **Automatisches Merging** mit bestehenden Keywords
- ✅ **Keine Duplikate** durch intelligente Filterung
- ✅ **Klickbare GA-Links** mit automatischer Konvertierung
- ✅ **Markdown-Formatierung** bleibt erhalten (`**fett**`)
- ✅ **Einfache Rückgängig-Funktion** durch Datei-Löschung
- ✅ **Flexibler Export** (einzelne Buchstaben oder alle)
- ✅ **Alphabetische Sortierung** automatisch
- ✅ **Quellen-Markierung** (`source: 'obsidian-az'`)

## 🎉 Fertig!

Die Integration ist komplett und einsatzbereit. Viel Erfolg!

