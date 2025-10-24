# Quick Switch zu OpenAI

## 🚀 In 2 Minuten zu OpenAI wechseln

### **Schritt 1: OpenAI API-Key holen**

1. Gehe zu: https://platform.openai.com/api-keys
2. Melde dich an (oder erstelle Account)
3. Klicke auf **"Create new secret key"**
4. **Name:** "GA-Suche" (optional)
5. **Kopiere** den Key (beginnt mit `sk-proj-...`)
   ⚠️ **WICHTIG:** Wird nur EINMAL angezeigt!

---

### **Schritt 2: .env-Datei bearbeiten**

Öffne `.env` im Projekt-Verzeichnis und füge hinzu:

```bash
# OpenAI API-Key
OPENAI_API_KEY=sk-proj-DEIN_KEY_HIER

# Wechsel zu OpenAI als Default
LLM_PROVIDER_DEFAULT=openai

# Oder spezifisch für Keywords
LLM_PROVIDER_KEYWORDS=openai
```

**Empfehlung:** Alle drei Provider für automatischen Fallback:

```bash
# Alle Provider konfigurieren
OPENAI_API_KEY=sk-proj-...
CLAUDE_API_KEY=sk-ant-...  # Falls vorhanden
GEMINI_API_KEY=...         # Falls vorhanden

# OpenAI als Primary
LLM_PROVIDER_DEFAULT=openai
```

---

### **Schritt 3: Backend neu starten**

```bash
# Backend stoppen (Ctrl+C)
node backend.js
```

**Erwartete Ausgabe:**
```
[LLM-PROVIDER] Task 'keywords': Verwende OpenAI
```

---

### **Schritt 4: Testen**

Im Browser (Keywords-Tab):
- 1 GA-Band auswählen
- "Batch starten (V2)"

**Console-Log prüfen:**
```
[LLM-FALLBACK] Verfügbare Provider für 'keywords': OpenAI, Claude, Gemini
[LLM-FALLBACK] Versuch 1/3: OpenAI
[KEYWORDS-NEW] GA051/1: ✓ Antwort von OpenAI erhalten
```

✅ **Fertig!**

---

## 💰 Kosten-Übersicht

### **OpenAI GPT-4o:**
- **Input:** $2.50 / 1M tokens
- **Output:** $10.00 / 1M tokens

### **Für 100 Vorträge Keywords generieren:**

| Komponente | Tokens | Kosten |
|------------|--------|--------|
| Input (Prompts) | ~500k | $1.25 |
| Output (Keywords) | ~100k | $1.00 |
| **TOTAL** | | **~$2.25** |

**Pro Vortrag:** ~$0.02

---

## 🔥 Vorteile OpenAI

1. ✅ **Keine Rate-Limits** (mit Credits)
2. ✅ **Sehr schnell** (schneller als Claude)
3. ✅ **Zuverlässig** (hohe Verfügbarkeit)
4. ✅ **Gute Qualität** für strukturierte Tasks
5. ✅ **Gutes Deutsch**

---

## 🎯 Automatischer Fallback aktiviert!

Wenn OpenAI Limit erreicht:
1. System wechselt zu **Claude** (falls konfiguriert)
2. Sonst zu **Gemini** (falls konfiguriert)
3. **Keine Unterbrechung** der Keyword-Generierung

**Beispiel-Log:**
```
[LLM-FALLBACK] Versuch 1/3: OpenAI
[LLM-FALLBACK] ⚠️ OpenAI Rate Limit erreicht
[LLM-FALLBACK] Wechsel zu Provider 2/3...
[LLM-FALLBACK] Versuch 2/3: Claude
[LLM-FALLBACK] ✓ Erfolg mit Claude
```

---

## 📝 Empfohlene .env (mit allen Providern)

```bash
# API-Keys (alle drei für maximale Verfügbarkeit)
OPENAI_API_KEY=sk-proj-...
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# OpenAI als Primary (schnell, zuverlässig)
LLM_PROVIDER_DEFAULT=openai

# Falls OpenAI Limit erreicht → automatisch Claude → Gemini
```

---

**Ready to go!** 🚀

Starte Backend neu und teste mit 1 GA-Band.

