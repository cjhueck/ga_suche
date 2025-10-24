# Neue Keyword-Generierung V2 - Dokumentation

## Übersicht

Die neue Keyword-Generierung V2 verwendet ein vordefiniertes Template mit Themen und Keywords, um Keywords konservativ und konsistent zu generieren.

## Änderungen gegenüber V1

### 1. **Keyword-Extraktion aus H3/H4 Überschriften**
- **ALT (V1):** Hauptbegriffe wurden aus der Summary extrahiert
- **NEU (V2):** Hauptbegriffe werden aus H3 und H4 Überschriften extrahiert
- **Vorteil:** Präzisere und strukturiertere Begriffe

### 2. **Vordefinierte Themen und Keywords**
- **ALT (V1):** Themen wurden NACH der Keyword-Generierung aus den Keywords abgeleitet
- **NEU (V2):** Themen und ihre zugehörigen Keywords sind in `themes-keywords-template.json` vordefiniert
- **Vorteil:** Konsistente Struktur von Anfang an, Qualitätskontrolle

### 3. **Konservative Keyword-Generierung**
- **Confidence-Schwelle:** 0.6 (konfigurierbar in Template)
- **Hierarchie:**
  1. 🏆 Exakte Übereinstimmung (Überschrift enthält existierendes Keyword)
  2. 🥈 Wortstamm-Match (z.B. "Ich-Entwicklung" für "Entwicklung des Ich")
  3. 🥉 Synonym-Match (z.B. "Reinkarnation" statt "Wiederverkörperung")
  4. 🏅 Thematisch passend aus Vokabular
  5. ⚠️ Neues Keyword (NUR wenn confidence < 0.6)

### 4. **Maximal 2 Keywords pro Überschrift**
- **ALT (V1):** Beliebig viele Keywords pro Überschrift
- **NEU (V2):** Maximal 2 Keywords (meist 1)
- **Vorteil:** Fokussierung auf das Wesentliche

### 5. **Synonym-Konsolidierung**
- Automatische Zusammenführung von Synonymen basierend auf Template-Definitionen
- Beispiel: "Wiederverkörperung" → "Reinkarnation" (kanonischer Begriff)

### 6. **Automatische Themen-Zuordnung**
- Jedes Keyword wird automatisch seinem Thema zugeordnet
- Basierend auf der Template-Struktur

---

## Dateien

### 1. `themes-keywords-template.json`
**Vordefinierte Struktur mit Themen und Keywords**

```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-10-24",
    "confidenceThreshold": 0.6,
    "rules": { ... }
  },
  "themes": {
    "Anthroposophie & Theosophie": {
      "description": "Grundlagen und Methodik...",
      "keywords": ["Anthroposophie", "Theosophie", ...],
      "synonymGroups": [
        ["Kanonischer Begriff", "Synonym1", "Synonym2"]
      ]
    }
  }
}
```

**Statistiken:**
- 74 Themen
- ~560 Keywords (bereinigt)
- 4 Synonym-Gruppen

### 2. `backend.js` - Neue Funktionen

#### Kernfunktionen:
```javascript
// Lädt Template
loadThemesKeywordsTemplate()

// Extrahiert Vokabular, Themen-Mapping, Synonyme
extractVocabularyFromTemplate(template)

// Extrahiert Begriffe aus H3/H4
extractKeyTermsFromHeadings(headings)

// HAUPTFUNKTION: Generiert Keywords
generateKeywordsFromHeadingsWithTemplate(
  lectureId, 
  headings, 
  template, 
  existingVocabulary, 
  frequencyMap
)

// Konsolidiert Synonyme
consolidateSynonymsInKeywords(keywordsDB, synonymMap)
```

---

## API-Endpoints

### POST `/api/generate-keywords-v2`
**Generiert Keywords mit neuer Template-Methode**

#### Request Body:
```json
{
  "lectureIds": ["GA068a/11", "GA068a/12"],  // Optional
  "gaVolumes": ["GA068", "GA110"],           // Optional
  "useExistingVocab": true,                  // Default: true
  "consolidateSynonyms": true                // Default: true
}
```

#### Response:
```json
{
  "success": true,
  "stats": {
    "totalRequested": 10,
    "processed": 8,
    "skipped": 2,
    "errors": 0,
    "newVocabularySize": 580,
    "synonymsConsolidated": 5
  },
  "results": [
    {
      "lectureId": "GA068a/11",
      "keywordsCount": 12,
      "newKeywordsCount": 2,
      "success": true
    }
  ]
}
```

### GET `/api/keywords-template-info`
**Gibt Template-Informationen zurück**

#### Response:
```json
{
  "metadata": { ... },
  "stats": {
    "totalThemes": 74,
    "totalKeywords": 560,
    "synonymGroups": 4,
    "confidenceThreshold": 0.6
  },
  "themes": ["Anthroposophie & Theosophie", ...]
}
```

---

## Workflow

### 1. **Einmalig: Template erstellen**
```bash
# Template ist bereits erstellt
# themes-keywords-template.json
```

### 2. **Keywords generieren für GA-Band**
```javascript
// API-Call
POST /api/generate-keywords-v2
{
  "gaVolumes": ["GA068"],
  "useExistingVocab": true,
  "consolidateSynonyms": true
}
```

### 3. **Iterativer Aufbau**
- **Vortrag 1:** Verwendet Template-Vokabular (560 Keywords)
- **Vortrag 2:** Template + Keywords aus Vortrag 1
- **Vortrag N:** Template + alle bisher generierten Keywords
- **Ziel:** Minimales Wachstum neuer Keywords (<5%)

### 4. **Konsolidierung**
Nach jedem Durchlauf:
- Automatische Synonym-Zusammenführung
- Duplikat-Erkennung

---

## Beispiele

### Beispiel 1: Exakte Übereinstimmung
**Überschrift:** "Die Entwicklung des Ich"  
**Vokabular:** "Ich-Entwicklung" (50x)  
**Ergebnis:**
```json
{
  "term": "Ich-Entwicklung",
  "matchType": "exact",
  "confidence": 0.95,
  "theme": "Wesensglieder"
}
```

### Beispiel 2: Synonym-Match
**Überschrift:** "Das Karmagesetz"  
**Vokabular:** "Karma" (180x)  
**Ergebnis:**
```json
{
  "term": "Karma",
  "matchType": "wordstem",
  "confidence": 0.85,
  "theme": "Wiederverkörperung"
}
```

### Beispiel 3: Neues Keyword
**Überschrift:** "Ätherische Bildekräfte"  
**Vokabular:** "Ätherleib" (100x) - keine "Bildekräfte"  
**Confidence:** 0.55 < 0.6  
**Ergebnis:**
```json
{
  "term": "Ätherleib",
  "matchType": "thematic",
  "confidence": 0.60,
  "theme": "Wesensglieder"
}
```
*Neues Keyword wird NICHT erstellt, da confidence < 0.6*

---

## Konfiguration

### Confidence-Schwelle ändern
In `themes-keywords-template.json`:
```json
{
  "metadata": {
    "confidenceThreshold": 0.6  // <- Hier ändern
  }
}
```

**Empfohlene Werte:**
- **0.55:** Sehr konservativ (mehr neue Keywords)
- **0.60:** Konservativ (empfohlen)
- **0.65:** Moderat
- **0.70:** Liberal (weniger neue Keywords)

---

## Qualitätssicherung

### Bereinigungen in Template:
1. **15 Duplikate entfernt:**
   - Menschheitsentwicklung, Ich-Entwicklung, Seelenentwicklung, etc.

2. **4 Synonym-Gruppen definiert:**
   - Entwicklung ↔ Evolution
   - Reinkarnation ↔ Wiederverkörperung ↔ Wiedergeburt
   - Geistige Welt ↔ Übersinnliche Welten
   - Bewusstseinsschulung ↔ Geistige Schulung

3. **Hierarchische Struktur:**
   - Generische Begriffe: "Bewusstsein", "Entwicklung"
   - Spezifische Begriffe: "Bewusstseinsseele", "Ich-Entwicklung"

---

## Vorteile V2 vs V1

| Aspekt | V1 | V2 |
|--------|----|----|
| **Keyword-Quelle** | Summary | H3/H4 Überschriften |
| **Themen** | Nachträglich | Vordefiniert |
| **Vokabular** | Wächst unkontrolliert | Konservativ, Template-basiert |
| **Duplikate** | Häufig | Minimal |
| **Synonyme** | Manuell | Automatisch konsolidiert |
| **Themen-Zuordnung** | Nachträglich | Automatisch |
| **Keywords/Überschrift** | Beliebig | Max. 2 |
| **Qualität** | Variabel | Konsistent |

---

## Migration von V1 zu V2

1. **Backup erstellen:**
   ```bash
   # Automatisch durch Backend
   ```

2. **Template laden:**
   ```javascript
   GET /api/keywords-template-info
   ```

3. **Neue Keywords generieren:**
   ```javascript
   POST /api/generate-keywords-v2
   {
     "gaVolumes": ["GA068"],
     "useExistingVocab": false  // Startet fresh
   }
   ```

4. **Bestehende Keywords konsolidieren:**
   ```javascript
   POST /api/generate-keywords-v2
   {
     "lectureIds": [...],
     "consolidateSynonyms": true
   }
   ```

---

## Troubleshooting

### Problem: "Template nicht gefunden"
**Lösung:** Stelle sicher, dass `themes-keywords-template.json` im Root-Verzeichnis liegt

### Problem: "Zu viele neue Keywords"
**Lösung:** Erhöhe `confidenceThreshold` in Template (z.B. auf 0.65)

### Problem: "Synonyme werden nicht konsolidiert"
**Lösung:** Setze `consolidateSynonyms: true` im Request

---

## Statistiken (erwartet)

Bei Verarbeitung der gesamten GA:
- **Start-Vokabular:** 560 Keywords (aus Template)
- **Nach 100 Vorträgen:** ~580 Keywords (+3.5%)
- **Nach 500 Vorträgen:** ~620 Keywords (+10%)
- **Nach 1000 Vorträgen:** ~680 Keywords (+21%)

**Ziel:** <30% Wachstum bei 1000+ Vorträgen

---

## Nächste Schritte

1. **Testing:** Teste mit GA068 (kleiner Band)
2. **Validierung:** Prüfe Keyword-Qualität
3. **Iteration:** Passe Template und Confidence an
4. **Rollout:** Verarbeite weitere GA-Bände
5. **Monitoring:** Tracke Vokabular-Wachstum

---

**Version:** 2.0  
**Datum:** 2025-10-24  
**Autor:** AI Assistant

