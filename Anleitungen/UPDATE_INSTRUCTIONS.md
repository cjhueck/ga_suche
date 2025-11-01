# Update: Inhaltsverzeichnis mit H3-Überschriften

## ✅ Was wurde geändert

1. **Plugin & Script**: Überschriften (H3/H4) werden jetzt separat exportiert
2. **Frontend**: TOC erscheint im Main Viewer, Links funktionieren zu echten H3-Tags
3. **Struktur**: Überschriften und Paragraphen werden in korrekter Reihenfolge gerendert

---

## 🚀 Neu exportieren (WICHTIG!)

```bash
cd C:\Users\chuec\OneDrive\GitHub\ga_suche
npm run export-lectures:ga GA051
```

Dies erstellt eine neue JSON-Datei mit der erweiterten Struktur.

---

## 📋 Was sollte jetzt passieren

### 1. In der JSON-Datei
```json
{
  "gaNumber": "GA051",
  "lectureNumber": "1",
  "tableOfContents": [...],
  "headings": [
    {
      "level": 3,
      "text": "Die griechischen Naturphilosophen",
      "id": "^i6owvt"
    },
    ...
  ],
  "paragraphs": [...]
}
```

### 2. Im Browser (index.html)

**Am Anfang des Vortrags:**
```
┌─────────────────────────────────────────┐
│ Inhaltsverzeichnis                      │
├─────────────────────────────────────────┤
│ ▸ Die griechischen Naturphilosophen     │
│   Die ersten westlichen Denker...       │
│                                         │
│ ▸ Heraklit und die Lehre vom...        │
│   Heraklits Philosophie...              │
│   ...                                   │
└─────────────────────────────────────────┘

Die griechischen Naturphilosophen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dass der Mensch nicht dabei...
```

### 3. Beim Klick auf einen TOC-Link
- Scrollt zur entsprechenden H3-Überschrift
- Überschrift leuchtet kurz auf
- Smooth Scrolling

---

## 🎨 Styling

Das TOC hat jetzt:
- ✅ Hellblauen Hintergrund
- ✅ Linke Akzentlinie
- ✅ Klickbare Links in Teal
- ✅ Kursive Beschreibungen
- ✅ Hover-Effekt (Unterstreichen)

---

## 🔍 Testen

1. **Export durchführen** (siehe oben)
2. **Backend starten**: `node backend.js`
3. **Browser öffnen**: `http://localhost:3000`
4. **Vortrag laden**: Nach "griechischen" suchen → GA051/1 öffnen
5. **TOC prüfen**: 
   - Sollte am Anfang sichtbar sein
   - 28 Einträge
   - Blau hinterlegt
6. **Link testen**: Auf "Heraklit" klicken → sollte zur Überschrift scrollen

---

## 💡 Unterschied zu vorher

**VORHER:**
- TOC sollte im Summary Panel erscheinen (❌ falsch)
- Keine H3-Tags im Viewer
- Links konnten nicht funktionieren

**JETZT:**
- TOC im Main Viewer unter dem Titel ✅
- Echte H3/H4-Tags werden gerendert ✅
- Links scrollen zu den Überschriften ✅
- Summary Panel hat weiterhin sein automatisches TOC ✅

---

## 🐛 Falls es nicht funktioniert

### TOC nicht sichtbar
1. Browser-Cache leeren (Ctrl+F5)
2. Prüfe JSON: Suche nach `"tableOfContents":`
3. Prüfe JSON: Suche nach `"headings":`

### Links funktionieren nicht
1. Browser Console öffnen (F12)
2. Auf Link klicken
3. Fehler anzeigen?

### Überschriften fehlen
1. Prüfe JSON: Ist `"headings": [...]` vorhanden?
2. Wenn nicht: Neu exportieren
3. Alte JSON-Datei löschen

---

**Viel Erfolg! 🎉**

