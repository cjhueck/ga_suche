# Quick Start: Inhaltsverzeichnis Export

## 🚀 Schnellstart

### 1. Export durchführen

```bash
cd C:\Users\chuec\OneDrive\GitHub\ga_suche
npm run export-lectures
```

Dies exportiert ALLE Vorträge mit Inhaltsverzeichnis.

### 2. Einen Vortrag testen

Für einen schnellen Test (nur GA051):
```bash
npm run export-lectures:ga GA051
```

### 3. Frontend öffnen

- Öffne `index.html` im Browser
- Lade GA051/1
- Prüfe das Summary Panel rechts → sollte "Inhaltsverzeichnis" zeigen

---

## ✅ Was wurde geändert?

### 1. Obsidian Plugin (`main.js`)
- ✅ Neue Funktion: `extractTableOfContents()`
- ✅ Neue Funktion: `parseTOCEntry()`
- ✅ Erweiterte Lecture-Objekte mit `tableOfContents` Array

### 2. Node.js Export Script (`export-lectures.js`)
- ✅ Komplett neues Script für schnellen Export
- ✅ Gleiche Logik wie Plugin
- ✅ CLI-Interface mit GA-Auswahl
- ✅ Automatisches Chunking bei großen Dateien

### 3. Frontend (`index.html`)
- ✅ Neue Funktion: `displayLectureTableOfContents()`
- ✅ Integration in `showLecture()`
- ✅ Klickbare Links zu H3-Überschriften
- ✅ Hover-Highlighting bei Navigation

### 4. Package.json
- ✅ Neues Script: `npm run export-lectures`
- ✅ Neues Script: `npm run export-lectures:ga`

---

## 📋 Test-Checkliste

### Plugin-Test (in Obsidian)
- [ ] Obsidian öffnen mit Steiner_GA Vault
- [ ] Command Palette öffnen (Ctrl+P)
- [ ] "Steiner Full Lectures Exporter" suchen
- [ ] "GA051" eingeben
- [ ] Warten auf Bestätigung
- [ ] JSON-Datei im Vault-Root prüfen
- [ ] `tableOfContents` im JSON finden

### Node.js Script Test
- [ ] Terminal öffnen in `ga_suche/`
- [ ] `npm run export-lectures:ga GA051` ausführen
- [ ] Ausgabe prüfen: "Processed 10 lectures" (oder ähnlich)
- [ ] JSON-Datei im Ordner finden
- [ ] JSON öffnen und `tableOfContents` prüfen

### Frontend-Test
- [ ] `index.html` im Browser öffnen
- [ ] Nach "griechischen" suchen → sollte GA051/1 finden
- [ ] GA051/1 öffnen
- [ ] Summary Panel (rechts) öffnet automatisch
- [ ] "Inhaltsverzeichnis" Überschrift sichtbar
- [ ] Liste mit ~28 Einträgen sichtbar
- [ ] Auf "Heraklit und die Lehre vom ewigen Wandel" klicken
- [ ] Sollte zu dieser Überschrift scrollen
- [ ] Überschrift sollte kurz aufleuchten

---

## 🔍 Erwartetes Ergebnis

### Im JSON (GA051/1)
```json
{
  "gaNumber": "GA051",
  "lectureNumber": "1",
  "tableOfContents": [
    {
      "heading": "Die griechischen Naturphilosophen",
      "description": "Die ersten westlichen Denker suchten..."
    },
    {
      "heading": "Heraklit und die Lehre vom ewigen Wandel",
      "description": "Heraklits Philosophie des ständigen..."
    }
    // ... 26 weitere Einträge
  ]
}
```

### Im Frontend
```
┌─────────────────────────────┐
│ Inhaltsverzeichnis          │
├─────────────────────────────┤
│ ■ Die griechischen...       │
│   Die ersten westlichen...  │
│                             │
│ ■ Heraklit und die Lehre... │
│   Heraklits Philosophie...  │
│                             │
│ ■ Empedokles und die...     │
│   Die Vier-Elemente-Lehre...│
│   ...                       │
└─────────────────────────────┘
```

---

## ⚠️ Bekannte Einschränkungen

1. **TOC muss im Markdown vorhanden sein**
   - Wenn kein `### Inhaltsverzeichnis` vorhanden ist, wird nichts exportiert
   - Das ist OK - nur Vorträge mit TOC bekommen eines

2. **Text-Matching für Links**
   - Links suchen nach exakter Überschriften-Übereinstimmung
   - Wenn Überschrift im Viewer anders formatiert ist, funktioniert Link nicht

3. **Nur H3-Überschriften**
   - TOC verlinkt nur zu H3-Überschriften
   - H4-Überschriften werden im TOC nicht angezeigt

---

## 🐛 Fehlersuche

### TOC erscheint nicht
1. **Prüfe JSON**: Suche nach `"tableOfContents":`
2. **Prüfe Browser Console** (F12): Fehler angezeigt?
3. **Cache leeren**: Ctrl+F5
4. **Neu exportieren**: `npm run export-lectures:ga GA051`

### Links funktionieren nicht
1. **Prüfe Überschriften im Viewer**: Stimmt der Text überein?
2. **Prüfe Browser Console**: JavaScript-Fehler?
3. **Prüfe DevTools Elements**: Gibt es H3-Elemente?

### Export dauert zu lange
- Verwende GA-Auswahl statt alle: `npm run export-lectures:ga GA051-GA060`
- Obsidian Plugin ist langsamer - nutze Node.js Script

---

## 📞 Support

Bei Problemen:
1. JSON-Datei prüfen (ist `tableOfContents` drin?)
2. Browser Console prüfen (F12 → Console)
3. README lesen: `EXPORT_LECTURES_README.md`

**Viel Erfolg! 🎉**

