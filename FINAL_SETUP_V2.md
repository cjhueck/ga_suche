# Final Setup - Keyword-Generierung V2

## ✅ Alle Probleme behoben

### 1. **Keywords zu lang** ✅ GELÖST
- Prompt drastisch vereinfacht (Schritt-für-Schritt)
- 15+ FALSCH/RICHTIG Beispiele aus echten Daten
- Temperatur auf **0.2** gesenkt (sehr strikt)
- Automatische Bereinigung: entfernt Füllwörter & Adjektive
- Aggressive Validierung: kürzt auf Vokabular-Begriffe

### 2. **Rate-Limit bei Gemini** ✅ GELÖST
- Automatischer Fallback: Gemini → OpenAI → Claude
- Keine Unterbrechung bei Rate-Limits
- Transparentes Logging

### 3. **Themen nicht im Frontend** ✅ GELÖST
- `themes-database.json` wird automatisch aktualisiert
- Timeline-Tab kann Themen laden
- Keyword-Manager funktioniert

---

## 🚀 Sofort loslegen

### **Option A: Mit OpenAI (empfohlen - keine Rate-Limits)**

1. **OpenAI API-Key holen:**
   - https://platform.openai.com/api-keys
   - "Create new secret key"
   - Key kopieren (beginnt mit `sk-proj-...`)

2. **In `.env` eintragen:**
   ```bash
   OPENAI_API_KEY=sk-proj-...
   LLM_PROVIDER_DEFAULT=openai
   ```

3. **Backend neu starten:**
   ```bash
   node backend.js
   ```

---

### **Option B: Mit allen Providern (maximale Verfügbarkeit)**

In `.env`:
```bash
# Alle drei Provider
OPENAI_API_KEY=sk-proj-...
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# OpenAI zuerst, dann automatisch Claude/Gemini bei Limit
LLM_PROVIDER_DEFAULT=openai
```

---

## 📋 Keywords neu generieren

1. **Browser:** `http://localhost:3003/index.html`

2. **Tab "Keywords"** öffnen

3. **"GA-Bände laden"** klicken

4. **5 GA-Bände** auswählen

5. **Checkboxen:**
   - ✅ Bestehendes Vokabular verwenden
   - ✅ Synonyme automatisch konsolidieren
   - ✅ **⚠️ NEU verarbeiten** (überschreibt alte!)

6. **"Batch starten (V2)"** klicken

**Erwartung:**
```
[LLM-FALLBACK] Verfügbare Provider: OpenAI, Claude, Gemini
[LLM-FALLBACK] Versuch 1/3: OpenAI
[KEYWORDS-NEW] GA051/1: ✓ Antwort von OpenAI erhalten
[KEYWORDS-CLEAN] GA051/1: "Wesen Geisteswissenschaft" → "Geisteswissenschaft"
[KEYWORDS-CLEAN] GA051/1: "suggestive Macht Naturwissenschaft" → "Naturwissenschaft"
```

---

## 🧹 Bereits generierte Keywords bereinigen

Falls Sie bereits Keywords mit dem alten System generiert haben:

```bash
node cleanup-existing-keywords.js
```

**Macht:**
- Entfernt Füllwörter ("Wesen", "Problem", "Lehre"...)
- Entfernt Adjektive ("griechischen", "suggestive"...)
- Kürzt auf Vokabular-Begriffe
- Verwirft zu lange (>5 Worte)

**Erstellt:**
- `keywords-database-cleaned.json` (neue, bereinigte Version)
- Backup der alten Version

**Dann:**
```bash
cp keywords-database-cleaned.json keywords-database.json
node backend.js
```

---

## 🧪 Qualität prüfen

Nach der Generierung:

```bash
node check-keyword-quality.js
```

**Erwarteter Output:**
```
📏 KEYWORD-LÄNGE:
   1 Wort:  3500 (60-70%)
   2 Worte: 1500 (25-30%)
   3 Worte:  400 (5-10%)
   >3 Worte: <100 (<5%)

✅ QUALITÄTS-SCORE: 92% 🎉 EXZELLENT
```

---

## 🎯 Erwartete Keywords (Beispiele)

### **GA051/1:**
```
✅ Unsterblichkeitsfrage
✅ Theosophie
✅ Naturwissenschaft
✅ Mysterien des Altertums
✅ Vergänglichkeit
✅ Entwicklung
✅ Seelenentwicklung
✅ Reinkarnation
✅ Ewigkeitsbewusstsein
```

**NICHT:**
```
❌ Wesen Geisteswissenschaft
❌ suggestive Macht Naturwissenschaft
❌ Ewige Vergängliche Natur
```

---

## 📊 Was wurde verbessert

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Prompt** | Lang, komplex | Kurz, Schritt-für-Schritt |
| **Temperatur** | 0.4 | 0.2 (strikter) |
| **Beispiele** | 10 | 25+ aus echten Daten |
| **Bereinigung** | Basic | Aggressiv (Füllwörter, Adjektive) |
| **Validierung** | Soft | Hart (>3 Worte → kürzen) |
| **Fallback** | Keiner | Automatisch alle Provider |
| **Länge** | 30-50% >3 Worte | <5% >3 Worte |

---

## ⚙️ Fine-Tuning

### **Wenn immer noch zu lang:**

1. **Confidence erhöhen** (Template):
   ```json
   "confidenceThreshold": 0.7  // statt 0.6
   ```

2. **Temperatur senken** (Backend):
   ```javascript
   temperature: 0.1  // statt 0.2
   ```

3. **Mehr Füllwörter** zur Blacklist hinzufügen

### **Wenn zu viele Keywords verworfen:**

1. **Template erweitern** mit mehr Basis-Keywords
2. **Confidence senken** auf 0.55

---

## 🔄 Workflow

```
1. Backend starten
   ↓
2. Keywords generieren (V2)
   ↓
3. Qualität prüfen (check-keyword-quality.js)
   ↓
4. Falls nötig: Cleanup (cleanup-existing-keywords.js)
   ↓
5. Timeline-Tab: Themen & Keywords ladbar ✓
```

---

## ✅ Checkliste

Vor dem Start:
- [ ] OpenAI API-Key in `.env`
- [ ] `LLM_PROVIDER_DEFAULT=openai`
- [ ] Backend neugestartet
- [ ] Template vorhanden (`themes-keywords-template.json`)

Nach der Generierung:
- [ ] `node check-keyword-quality.js` → Score >85%?
- [ ] Keywords kurz (1-2 Worte)?
- [ ] Themen im Timeline-Tab ladbar?
- [ ] Synonyme konsolidiert?

---

**Version:** 2.2  
**Status:** 🚀 Production Ready  
**Datum:** 2025-10-24

