# LLM Provider Setup

## 🚀 Schnellstart

### 1. Gemini API Key holen (Empfohlen - Kostenlos!)

1. Gehe zu: https://aistudio.google.com/
2. Melde dich mit deinem Google-Account an
3. Klicke auf **"Get API Key"** (oben rechts)
4. Klicke auf **"Create API key"**
5. Kopiere den Key (sieht aus wie: `AIzaSy...`)

### 2. .env Datei erstellen

Erstelle eine Datei namens `.env` im Projektverzeichnis mit folgendem Inhalt:

```bash
# ============================================================================
# LLM API KEYS
# ============================================================================

# Google Gemini API (EMPFOHLEN - Kostenlos, 1500 Requests/Tag)
GEMINI_API_KEY=AIzaSy_DEIN_KEY_HIER

# Anthropic Claude API (Optional - falls Budget vorhanden)
CLAUDE_API_KEY=sk-ant-api03-xxxxx

# OpenAI API (Optional)
OPENAI_API_KEY=sk-proj-xxxxx

# ============================================================================
# LLM PROVIDER KONFIGURATION
# ============================================================================

# Default Provider
LLM_PROVIDER_DEFAULT=gemini

# Task-spezifische Provider
LLM_PROVIDER_SUMMARY=gemini          # Vortrags-Zusammenfassungen
LLM_PROVIDER_KEYWORDS=gemini         # Keyword-Generierung
LLM_PROVIDER_THEMES=gemini           # Themen-Clustering
LLM_PROVIDER_BATCH=gemini            # Batch-Operationen
LLM_PROVIDER_ANALYSIS=gemini         # Textanalyse

# Backend Server Port
PORT=3003
```

### 3. Backend starten

```bash
node backend.js
```

---

## 📊 Provider-Auswahl

### Gemini (Google AI Studio) - **EMPFOHLEN**

**Vorteile:**
- ✅ **Kostenlos:** 1500 Requests/Tag, 15/Minute
- ✅ Sehr günstig bei höherer Nutzung
- ✅ Gute Qualität für strukturierte Aufgaben
- ✅ Schnell (Flash-Modell)

**Kosten (bei Überschreitung Free Tier):**
- Input: $0.075 / 1M tokens
- Output: $0.30 / 1M tokens

**Setup:** https://aistudio.google.com/

---

### Claude (Anthropic)

**Vorteile:**
- ✅ Beste Qualität für Textanalyse
- ✅ Sehr gutes deutsches Verständnis
- ✅ Zuverlässig

**Kosten:**
- Input: $3.00 / 1M tokens
- Output: $15 / 1M tokens

**Setup:** https://console.anthropic.com/

---

### OpenAI (GPT-4o)

**Vorteile:**
- ✅ Sehr gute Qualität
- ✅ Schnell
- ✅ Zuverlässig

**Kosten (GPT-4o):**
- Input: $2.50 / 1M tokens
- Output: $10 / 1M tokens

**Setup:** https://platform.openai.com/api-keys

---

## 🎯 Empfohlene Konfigurationen

### Szenario 1: Kein Budget

```bash
LLM_PROVIDER_DEFAULT=gemini
# Alle Tasks mit Gemini (kostenlos bis 1500 req/Tag)
```

**Kosten:** $0 bis 1500 Requests/Tag

---

### Szenario 2: Knappes Budget

```bash
LLM_PROVIDER_DEFAULT=gemini
LLM_PROVIDER_ANALYSIS=claude    # Nur Textanalyse mit Claude
```

**Kosten:** ~$0.10-0.50/Tag (je nach Nutzung)

---

### Szenario 3: Budget vorhanden

```bash
LLM_PROVIDER_DEFAULT=claude
LLM_PROVIDER_BATCH=gemini       # Massenoperationen günstig
```

**Kosten:** ~$1-5/Tag (je nach Nutzung)

---

## 🔧 Fehlerbehebung

### "Kein verfügbarer LLM-Provider gefunden"

**Lösung:** Mindestens einen API-Key in `.env` setzen

### "Rate Limit erreicht"

**Gemini Free Tier:**
- 15 Requests/Minute
- 1500 Requests/Tag

**Lösung:** Warten oder auf bezahltes Tier upgraden

### "API-Key ungültig"

**Lösung:** 
1. Prüfe ob Key korrekt kopiert wurde (keine Leerzeichen)
2. Prüfe ob Key aktiv ist (im jeweiligen Dashboard)

---

## 📈 Kostenbeispiele für 6.070 Keywords

### Themen-Generierung (Top 1000)

| Provider | Kosten |
|----------|--------|
| Gemini | $0.05 |
| Claude | $0.50 |
| OpenAI | $0.20 |

### Batch-Zuordnung (alle 6.070 KW)

| Provider | Kosten |
|----------|--------|
| Gemini | $0.08 |
| Claude | $1.50 |
| OpenAI | $0.40 |

### Gesamt-Operation

| Provider | Kosten |
|----------|--------|
| Gemini | **$0.13** ✅ |
| Claude | $2.00 |
| OpenAI | $0.60 |

---

## 🌟 Warum Gemini für dieses Projekt ideal ist

1. **Kostenlos für Entwicklung:** 1500 Requests/Tag kostenlos
2. **Strukturierte Aufgaben:** Keyword-Generierung, Clustering → Gemini perfekt
3. **Massenoperationen:** Batch-Zuordnung von 6.070 Keywords für $0.08
4. **Deutsch:** Ausreichend gut für Steiner-Texte
5. **Kein Vendor-Lock:** Einfacher Wechsel zwischen Providern

---

**Erstellt:** Oktober 2025  
**Projekt:** GA-Suche (Rudolf Steiner Gesamtausgabe)

