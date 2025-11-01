# Summary-Regeneration mit automatischer Keyword-Generierung V3

**Version:** 1.0  
**Datum:** 2025-10-25  
**Status:** ✅ Implementiert

---

## 🎯 Feature-Beschreibung

Beim Klick auf **"Summary neu"** im Frontend wird jetzt automatisch:

1. ✅ **Summary V2** neu generiert (mit H3/H4 Überschriften)
2. ✅ **Inhaltsverzeichnis (TOC)** neu erstellt
3. ✅ **Keywords mit V3** automatisch generiert (flexibel + Budget)
4. ✅ Alles gespeichert und angezeigt

---

## 🔄 Workflow

### **Frontend (Button-Klick):**

```javascript
// User klickt auf "Summary neu"
regenerateCurrentSummary()
  ↓
POST /api/summarize-lecture
{
  lectureId: "GA068a/11",
  forceRegenerate: true,
  preferredProvider: "gemini"  // Optional, aus Radio-Button
}
```

### **Backend (automatischer Ablauf):**

```javascript
1. Generiere Summary V2
   - Zusammenfassung (100-150 Wörter)
   - H3/H4 Überschriften (6-12 H3, 1-4 H4 pro H3)
   - Inhaltsverzeichnis (TOC)
   - Speichere in summary-database.json

2. Generiere Keywords V3 (NEU!)
   - Lade Template (81 Themen, 440 Keywords)
   - Lade existierendes Vokabular (iterativ)
   - Rufe generateKeywordsFlexibleWithBudget()
   - Budget: 4 neue Keywords max
   - Automatische Themen-Zuordnung
   - Speichere in keywords-database.json

3. Sende Response mit allen Daten
```

---

## 📊 Response-Format

```json
{
  "lectureId": "GA068a/11",
  "summary": "Zusammenfassung...",
  "headings": [
    {"index": "^abc123", "text": "Überschrift", "level": "h3"}
  ],
  "tableOfContents": [
    {
      "heading": "Überschrift",
      "description": "Beschreibung...",
      "index": "^abc123"
    }
  ],
  "keywords": [
    {
      "term": "Karma",
      "index": "^abc123",
      "heading": "Original-Überschrift",
      "level": "h3",
      "matchType": "exact",
      "confidence": 0.95,
      "theme": "Wiederverkörperung"
    }
  ],
  "version": "v2",
  "keywordsGenerated": true,
  "paragraphCount": 150
}
```

---

## 💬 Erfolgs-Meldung (Frontend)

**Vorher:**
```
Summary V2 neu erzeugt und gespeichert!
```

**Jetzt:**
```
Summary V2 neu erzeugt und gespeichert!

✓ Zusammenfassung erstellt
✓ 8 Überschriften (H3/H4)
✓ 6 Inhaltsverzeichnis-Einträge
✓ 7 Schlagwörter (V3 flexibel)
  - 5 existierend, 2 neu
```

---

## 🔧 Technische Details

### **Backend-Änderung (`backend.js`):**

```javascript
// Zeilen 2104-2186
if (forceRegenerate && summaryData.headings && summaryData.headings.length > 0) {
  // Lade Template & Vokabular
  const template = await loadThemesKeywordsTemplate();
  const existingVocabulary = [/* ... */];
  const frequencyMap = {/* ... */};
  
  // Hole Provider
  const provider = getProviderForTask('keywords');
  
  // Generiere Keywords V3
  generatedKeywords = await generateKeywordsFlexibleWithBudget(
    lectureId,
    summaryData.headings,
    template,
    existingVocabulary,
    frequencyMap,
    provider,
    4  // Budget: 4 neue Keywords
  );
  
  // Speichere in keywords-database.json
  await saveKeywordsToDatabase(lectureId, {
    lectureId,
    keywords: generatedKeywords,
    generationMethod: 'flexible-v3-auto',
    maxNewKeywordsBudget: 4
  });
}
```

### **Frontend-Änderung (`index.html`):**

```javascript
// Zeilen 6816-6844
// Erstelle detaillierte Erfolgsmeldung
let successMessage = `Summary V2 neu erzeugt und gespeichert!\n\n`;
successMessage += `✓ Zusammenfassung erstellt\n`;
successMessage += `✓ ${data.headings.length} Überschriften (H3/H4)\n`;
successMessage += `✓ ${data.tableOfContents.length} Inhaltsverzeichnis-Einträge\n`;

if (keywordsGenerated && data.keywords) {
  const newKws = data.keywords.filter(k => k.matchType === 'new').length;
  const existingKws = data.keywords.length - newKws;
  successMessage += `✓ ${data.keywords.length} Schlagwörter (V3 flexibel)\n`;
  successMessage += `  - ${existingKws} existierend, ${newKws} neu`;
}

alert(successMessage);
```

---

## ✅ Vorteile

### **1. One-Click-Lösung:**
- User muss nur 1x klicken
- Summary + Keywords + TOC werden automatisch erstellt
- Keine manuelle Keyword-Generierung nötig

### **2. Konsistenz:**
- Keywords werden IMMER mit V3 generiert
- Gleiche Qualität und Struktur
- Automatische Themen-Zuordnung

### **3. Effizienz:**
- Nutzt bereits geladene Headings
- Kein separater API-Call nötig
- Vokabular wird iterativ erweitert

---

## 🧪 Testing

### **Test 1: Einzelner Vortrag**

```bash
# 1. Server starten
node backend.js

# 2. Im Browser:
# - Vortrag öffnen (z.B. GA068a/11)
# - "Summary neu" klicken
# - Warten (~30 Sekunden)
# - Erfolgs-Meldung prüfen

# 3. Ergebnis prüfen:
node -e "const fs = require('fs'); const kw = JSON.parse(fs.readFileSync('keywords-database.json')); const lecture = kw['GA068a/11']; console.log('Keywords:', lecture.keywords.length); console.log('Neu:', lecture.keywords.filter(k => k.matchType === 'new').length); console.log('Existierend:', lecture.keywords.filter(k => k.matchType !== 'new').length); console.log('Mit Thema:', lecture.keywords.filter(k => k.theme).length);"
```

**Erwartetes Ergebnis:**
```
Keywords: 7-9
Neu: 2-4
Existierend: 5-6
Mit Thema: 6-8 (>80%)
```

---

### **Test 2: Mehrere Vorträge nacheinander**

```bash
# Im Browser:
# 1. Vortrag 1 öffnen → "Summary neu" → Warten
# 2. Vortrag 2 öffnen → "Summary neu" → Warten
# 3. Vortrag 3 öffnen → "Summary neu" → Warten

# Erwartung:
# - Vortrag 1: 3-4 neue Keywords
# - Vortrag 2: 2-3 neue Keywords (nutzt Keywords von Vortrag 1)
# - Vortrag 3: 1-2 neue Keywords (nutzt Keywords von 1+2)
```

---

## 📝 Konfiguration

### **Budget anpassen:**

In `backend.js`, Zeile 2157:
```javascript
generatedKeywords = await generateKeywordsFlexibleWithBudget(
  lectureId,
  summaryData.headings,
  template,
  existingVocabulary,
  frequencyMap,
  provider,
  4  // ← HIER: Budget ändern (z.B. 3 oder 5)
);
```

**Empfehlungen:**
- **Anfangs:** 5 (mehr neue Keywords erlaubt)
- **Normal:** 4 (Standard)
- **Später:** 3 (weniger neue Keywords)
- **Reif:** 2 (minimal neue Keywords)

---

## 🔍 Debugging

### **Log-Ausgaben im Backend:**

```bash
→ Zusammenfassung für GA068a/11 angefordert...
  → Force-Regenerate, erstelle neue V2...
  ✓ Summary V2 für GA068a/11 sicher in DB gespeichert
  → Generiere Keywords mit V3 (flexible + Budget)...
[KEYWORDS-FLEX] GA068a/11: Rufe Gemini auf (Budget: 4 neue KW)...
[KEYWORDS-FLEX] GA068a/11: 8 Keywords erhalten
[KEYWORDS-FLEX] GA068a/11: Validiert: 7 unique KW (2 neu, 2 verworfen)
[THEME-ASSIGN] "Ätherische Bildekräfte" → "Wesensglieder"
[KEYWORDS-FLEX] GA068a/11: ✓ FINAL: 7 Keywords
[KEYWORDS-FLEX]   Existierend: 5, Neu: 2
[KEYWORDS-FLEX]   Mit Thema: 6, Ohne Thema: 1
  ✓ Keywords V3 generiert: 7 total (2 neu, 5 existierend)
  ✓ Zusammenfassung v2 erstellt und in zentrale DB gespeichert
```

---

## 🚨 Fehlerbehandlung

### **Fall 1: Kein LLM-Provider verfügbar**

```javascript
// Backend loggt:
[KEYWORDS-V3] Provider-Fehler: ..., überspringe Keyword-Generierung

// Frontend zeigt:
Summary V2 neu erzeugt und gespeichert!
✓ Zusammenfassung erstellt
✓ 8 Überschriften (H3/H4)
✓ 6 Inhaltsverzeichnis-Einträge
✓ 10 Schlagwörter  // ← Aus V2-Summary, nicht V3
```

### **Fall 2: Template nicht gefunden**

```javascript
// Backend loggt:
[KEYWORDS-V3] Fehler bei Keyword-Generierung: Template konnte nicht geladen werden

// Fortfahren mit V2-Keywords
```

---

## 📚 Zusammenfassung

**Was wurde geändert:**
1. ✅ `/api/summarize-lecture` erweitert (Backend)
2. ✅ Automatische V3-Keyword-Generierung bei `forceRegenerate: true`
3. ✅ Erfolgs-Meldung im Frontend verbessert
4. ✅ Keywords werden in `keywords-database.json` gespeichert

**Verhalten:**
- **Ohne `forceRegenerate`:** Nur Summary aus Cache/DB
- **Mit `forceRegenerate`:** Summary + Keywords V3 neu generiert

**Budget-System:**
- Max. 4 neue Keywords pro Vortrag
- Existierende Keywords werden stark bevorzugt
- Automatische Themen-Zuordnung

---

**Version:** 1.0  
**Datum:** 2025-10-25  
**Implementiert von:** AI Assistant & User

