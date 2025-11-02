# Keyword-Merge-Strategie

## Übersicht

Das System schützt jetzt **manuell bearbeitete Keywords** vor versehentlichem Überschreiben bei der iterativen Neugenerierung von Schlagwörtern.

## Wie es funktioniert

### 1. Automatisches Tracking manueller Bearbeitungen

Wenn Sie Keywords mit dem **Keyword-Manager** bearbeiten, werden diese automatisch markiert:

```javascript
{
  term: "Astralleib",
  index: "^abc123",
  manuallyEdited: true,           // ✅ Markiert als manuell bearbeitet
  lastEditedAt: "2025-11-02T..."  // Zeitstempel der Bearbeitung
}
```

**Folgende Aktionen setzen das Flag:**
- ✅ Keyword hinzufügen (`/api/add-keyword-to-lecture`)
- ✅ Keyword bearbeiten/umbenennen (`/api/update-lecture-keyword`)
- ✅ Keyword-Beschreibung ändern

### 2. Intelligente Merge-Strategie bei Neugenerierung

Wenn Sie **Schlagwörter neu generieren** (iteratives Verfahren):

```
VORHER (ALT):
❌ Alle Keywords eines Vortrags wurden komplett überschrieben
❌ Ihre manuellen Änderungen gingen verloren

NACHHER (NEU):
✅ Manuell bearbeitete Keywords bleiben erhalten
✅ Neu generierte Keywords werden hinzugefügt
✅ Duplikate werden automatisch vermieden
```

**Ablauf beim Speichern:**

```javascript
// 1. Lade bestehende Keywords aus Datenbank
const existingKeywords = keywordsDB[lectureId].keywords;

// 2. Filtere manuell bearbeitete Keywords
const manualKeywords = existingKeywords.filter(kw => kw.manuallyEdited === true);

// 3. Filtere neue Keywords (keine Duplikate)
const newKeywords = generatedKeywords.filter(kw => {
  const signature = `${kw.term}|${kw.index}`;
  return !existingSignatures.has(signature);
});

// 4. Merge: Manuelle zuerst, dann neue
const mergedKeywords = [...manualKeywords, ...newKeywords];
```

### 3. Duplikatserkennung

Duplikate werden anhand einer **Signatur** erkannt:
```
Signatur = term + "|" + index
Beispiel: "Astralleib|^GA123_p5_h2"
```

Wenn ein neu generiertes Keyword die gleiche Signatur hat wie ein bestehendes, wird es **nicht hinzugefügt**.

## Praktisches Beispiel

### Ausgangssituation

Sie haben Vortrag `GA001_01` mit folgenden Keywords:

```javascript
[
  { term: "Astralleib", index: "^abc", manuallyEdited: false },
  { term: "Karma", index: "^def", manuallyEdited: false },
  { term: "Reinkarnation", index: "^ghi", manuallyEdited: false }
]
```

### Schritt 1: Manuelle Bearbeitung

Sie bearbeiten "Karma" im Keyword-Manager → umbenennen zu "Karmagesetz":

```javascript
[
  { term: "Astralleib", index: "^abc", manuallyEdited: false },
  { term: "Karmagesetz", index: "^def", manuallyEdited: true, lastEditedAt: "..." },  // ✅ Geschützt
  { term: "Reinkarnation", index: "^ghi", manuallyEdited: false }
]
```

### Schritt 2: Neugenerierung starten

Sie führen die iterative Keyword-Generierung erneut für GA001_01 durch.

Die KI generiert:
```javascript
[
  { term: "Astralleib", index: "^abc" },        // Duplikat (gleiche Signatur)
  { term: "Ätherleib", index: "^jkl" },         // NEU
  { term: "Ich-Organisation", index: "^mno" }   // NEU
]
```

### Schritt 3: Automatischer Merge

Das System führt automatisch den Merge durch:

```javascript
[
  // ✅ Manuell bearbeitetes Keyword bleibt erhalten
  { term: "Karmagesetz", index: "^def", manuallyEdited: true },
  
  // ❌ "Astralleib" wird NICHT doppelt hinzugefügt (Duplikat)
  
  // ✅ Neue Keywords werden hinzugefügt
  { term: "Ätherleib", index: "^jkl", manuallyEdited: false },
  { term: "Ich-Organisation", index: "^mno", manuallyEdited: false }
]
```

**Ergebnis:** Ihr manuell bearbeitetes "Karmagesetz" bleibt erhalten! 🎉

## Log-Ausgaben

Sie können den Merge-Prozess in den Backend-Logs verfolgen:

```
[KEYWORDS-MERGE] Merge für GA001_01: 3 bestehende + 3 neue Keywords
[KEYWORDS-MERGE] Erhalte 1 manuell bearbeitete Keywords
[KEYWORDS-MERGE] Füge 2 neue Keywords hinzu
[KEYWORDS-MERGE] ✓ Merge abgeschlossen: 3 Keywords total
```

## Wichtige Hinweise

### ✅ Was geschützt wird
- Alle im Keyword-Manager bearbeiteten Keywords
- Alle manuell hinzugefügten Keywords
- Umbenennung von Keywords
- Geänderte Beschreibungen

### ⚠️ Was NICHT geschützt wird
- Keywords, die Sie **löschen** (werden nicht wiederhergestellt)
- Keywords, die **nie bearbeitet** wurden (können bei Neugenerierung entfernt werden)

### 💡 Best Practice
1. **Backup:** Die Datenbank wird vor jedem Speichern automatisch gesichert
2. **Iterativ arbeiten:** Bearbeiten Sie Keywords nach und nach, das System merkt sich alle Änderungen
3. **Regenerieren:** Sie können jederzeit neu generieren - Ihre Bearbeitungen bleiben erhalten

## Technische Details

### Betroffene Dateien
- `backend.js`:
  - `saveKeywordsToDatabase()` - Merge-Logik
  - `/api/add-keyword-to-lecture` - Flag setzen
  - `/api/update-lecture-keyword` - Flag setzen

### Datenstruktur
```javascript
{
  "GA001_01": {
    "lectureId": "GA001_01",
    "keywords": [
      {
        "term": "Astralleib",
        "index": "^abc123",
        "heading": "Der astralische Leib",
        "manuallyEdited": true,      // ✅ NEU
        "lastEditedAt": "2025-11-02T10:30:00Z"  // ✅ NEU
      }
    ],
    "timestamp": "2025-11-02T10:30:00Z",
    "lastMerge": "2025-11-02T10:30:00Z"  // ✅ NEU
  }
}
```

## FAQ

**Q: Was passiert, wenn ich ein Keyword lösche und dann neu generiere?**  
A: Gelöschte Keywords werden NICHT wiederhergestellt. Nur bestehende manuelle Keywords werden geschützt.

**Q: Kann ich die Neugenerierung erzwingen und alles überschreiben?**  
A: Aktuell nicht - das System schützt alle manuellen Bearbeitungen. Falls gewünscht, kann eine "Force Override"-Option implementiert werden.

**Q: Was passiert mit automatisch generierten Keywords bei Neugenerierung?**  
A: Sie werden durch die neuen ersetzt, sofern keine Duplikate. Nur `manuallyEdited: true` Keywords bleiben garantiert erhalten.

**Q: Werden auch die Timestamps aktualisiert?**  
A: Ja, `timestamp` zeigt den letzten Speichervorgang, `lastMerge` zeigt wann der letzte Merge stattfand.

---

**Stand:** 2025-11-02  
**Version:** 1.0

