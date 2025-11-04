# Download-Anleitung für Rudolf Steiner Vortragstexte

**Stand:** November 2025  
**Quelle:** rsarchive.org

---

## 📥 Download-Scripts

### Haupt-Script für einzelne GA-Bände:
```bash
python download_german_lectures.py <GA-Nummer>
```

**Beispiele:**
```bash
python download_german_lectures.py 121
python download_german_lectures.py 332a
python download_german_lectures.py 266/I
```

### Spezial-Scripts für manuelle Reihenfolge:
```bash
python rebuild_ga130_v2.py    # Für GA130 mit offizieller Nummerierung
python rebuild_ga140_correct_order.py  # Für GA140
```

---

## ✅ Automatische Features

Das Script erkennt automatisch:

### 1. Editorische Reihenfolge
- **Nummern im Titel** (I., II., 1., 2., etc.) → Verwendet diese für Sortierung
- **Keine Nummern** → Chronologisch nach Datum sortiert
- **Duplikate** (gleiche Nummer) → Nur eine Version behalten

### 2. Deutsche Städtenamen mit Umlauten
- Munich → **München**
- Vienna → **Wien**
- Cologne → **Köln**
- Nuremberg → **Nürnberg**
- Dusseldorf → **Düsseldorf**
- Strasbourg → **Straßburg**
- Milan → **Mailand**
- Neuchâtel → **Neuchatel** (â entfernt)

### 3. Alle HTML-Formate
- Altes Format: `<div id="original">`
- Neues Format: `<div class="German">`

### 4. Alle Dateinamen-Muster
- `p01` - Afternoon/PM Vortrag
- `a01` - Morning/AM Vortrag
- `e01` - Event/Essay
- `d01` - Discussion
- `preface` - Vorreden

### 5. Duplikat-Erkennung
- Bevorzugt `p01` vor `p02` (erste Version)
- Erkennt gleiche Textlänge (±10 Zeichen)
- Bei gleichem Datum/Ort wird nur eine Version behalten

---

## 📂 Ausgabe-Format

### Verzeichnisstruktur:
```
Steiner_GA/
  lectures/
    GA140/
      assets/
        140-01.webp
      GA140 (1.) TITEL IN GROSSBUCHSTABEN, Ort, Datum.md
      GA140 (2.) TITEL IN GROSSBUCHSTABEN, Ort, Datum.md
      ...
```

### Dateiname-Format:
```
GAXXX (N.) TITEL IN GROSSBUCHSTABEN, Ort, Datum.md
```

**Beispiele:**
- `GA140 (1.) UNTERSUCHUNGEN ÜBER DAS LEBEN ZWISCHEN TOD UND NEUER GEBURT I, Mailand, 26. Oktober 1912.md`
- `GA130 (4.) DAS ROSENKREUZERISCHE CHRISTENTUM, Neuchatel, 27. September 1911.md`
- `GA121 (1.) EINE VORREDE, Unbekannter Ort, .md`

### Dateiinhalt:
- **Kein Header** - beginnt direkt mit Text
- **Bilder**: `![Alt](assets/bild.webp)` an richtiger Stelle
- **Listen**: Korrekt formatiert mit Zeilenumbrüchen
- **Encoding**: UTF-8-BOM mit korrekten Umlauten (ä, ö, ü, ß)

---

## 🎯 Wichtige Regeln

### Titel:
- **GROSSBUCHSTABEN** (wie im Original HTML)
- Nummern (I., II., 1., 2.) werden entfernt

### Städtenamen:
- **Deutsche Namen** verwenden
- **Deutsche Umlaute** BEHALTEN (ä, ö, ü, ß)
- **Französische Akzente** ENTFERNEN (â → a, ê → e)

### Nummerierung:
- **Wenn Nummern im Titel** → Diese Reihenfolge verwenden
- **Ohne Nummern** → Chronologisch nach Datum
- **Duplikate** (gleiche Nummer) → Nur erste Version (p01)

### Vorreden:
- **Inkludiert** wenn vorhanden
- **Als Nummer 0 oder 1** (vor Vorträgen)
- **Marie Steiner Vorworte** manuell aussortieren

---

## 📊 Erfolgreich heruntergeladen

**Getestet und verifiziert:**
- ✅ **GA121**: 12 Dateien (1 Vorrede + 11 Vorträge)
- ✅ **GA125**: 14 Vorträge
- ✅ **GA127**: 15 Vorträge
- ✅ **GA130**: 23 Vorträge (offizielle Nummerierung!)
- ✅ **GA133**: 9 Vorträge
- ✅ **GA140**: 20 Vorträge (editorische Reihenfolge!)
- ✅ **GA159**: 15 Vorträge + 4 Bilder

**Gesamt:**
- ~**250+ GA-Bände**
- ~**2000+ Vorträge**
- **Hunderte Tafelzeichnungen** in assets/

---

## 🚀 Für zukünftige Downloads

**Standard-Verwendung:**
```bash
python download_german_lectures.py <GA-Nummer>
```

Das Script macht automatisch:
- ✓ Editorische Nummerierung (falls vorhanden)
- ✓ Deutsche Städtenamen
- ✓ Duplikat-Erkennung
- ✓ Bilder-Download
- ✓ Korrekte Formatierung

**Für spezielle Fälle** (komplexe Nummerierung):
1. Liste von rsarchive.org kopieren
2. Eigenes rebuild-Script erstellen (wie GA130/GA140)
3. Mapping-Tabelle verwenden

---

**Alle Scripts bereit für produktiven Einsatz!** 🎉


