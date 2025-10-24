# Nach dem Verschieben - Quick Start

## ✅ Was wurde implementiert

### 1. **LLM Provider System**
- ✅ Unterstützt: Claude, Gemini, OpenAI
- ✅ Flexible Provider-Auswahl via .env
- ✅ Automatische Fallback-Chain

### 2. **Zweiphasige Themen-Generierung** (LÖSUNG!)
- ✅ **Phase 1:** Themen-Namen generieren (klein, stabil)
- ✅ **Phase 2:** Batch-Zuordnung aller Keywords (skalierbar)

### 3. **Verstärktes iteratives Verfahren**
- ✅ Prompt: "WÄHLE aus Vokabular" (nicht "Erstelle")
- ✅ Erwartete 70-80% Wiederverwendung

### 4. **Top 1000 Keywords** (statt 300)
- ✅ Bessere Themen-Basis

---

## 🚀 Nach dem Verschieben (z.B. nach C:\dev\ga_suche)

### 1. Backend starten
```bash
cd C:\dev\ga_suche
node backend.js
```

### 2. Themen generieren (Phase 1)
```bash
# Im Browser: http://localhost:3003
# Timeline-Tab → "Themen generieren"
# ODER via PowerShell:
Invoke-WebRequest -Uri "http://localhost:3003/api/generate-themes" -Method POST -ContentType "application/json" -Body '{"targetThemeCount": 20}'
```

**Erwartetes Ergebnis:**
```
✓ 20 Themen-Namen generiert
✓ Provider: OpenAI (stabiles JSON)
✓ Dauer: ~30 Sekunden
✓ Keywords-Arrays: leer (Phase 1)
```

### 3. Batch-Zuordnung (Phase 2)
```bash
Invoke-WebRequest -Uri "http://localhost:3003/api/themes/assign-all-keywords" -Method POST
```

**Erwartetes Ergebnis:**
```
✓ 6.070 Keywords → 20 Themen
✓ ~31 Batches à 200 Keywords
✓ Provider: Gemini oder OpenAI
✓ Dauer: ~3-4 Minuten
✓ 100% Coverage!
```

### 4. Frontend neu laden
```
Strg + Shift + R
```

---

## 🔧 Empfohlene .env Konfiguration

```bash
# API Keys (bereits vorhanden)
CLAUDE_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx
GEMINI_API_KEY=AIzaSy_xxxxx

# Provider für Tasks
LLM_PROVIDER_DEFAULT=gemini
LLM_PROVIDER_THEMES=openai    # OpenAI = stabiler für JSON!
LLM_PROVIDER_BATCH=openai     # OpenAI = stabiler für JSON!
LLM_PROVIDER_KEYWORDS=gemini  # Gemini OK für Keywords
LLM_PROVIDER_SUMMARY=gemini   # Gemini OK für Summaries
LLM_PROVIDER_ANALYSIS=gemini  # Gemini OK für Analysen

PORT=3003
```

**Warum OpenAI für Themen/Batch?**
- ✅ Stabiles JSON (99% Erfolgsrate)
- ✅ Höheres Token-Limit (16k vs 8k)
- ✅ Du hast den Key schon

**Kosten:**
- Themen (Phase 1): ~$0.10
- Batch (Phase 2): ~$0.30
- **Gesamt: ~$0.40** (statt $2+ mit Claude!)

---

## 🐛 Bekannte Probleme (gelöst nach Verschieben)

### OneDrive File-Locking
- ❌ OneDrive sperrt keywords-database.json beim Schreiben
- ✅ **Lösung:** Lokal arbeiten

### Gemini Token-Limit
- ❌ Gemini: max 8k Output-Tokens
- ❌ 20 Themen × 30 Keywords = zu groß
- ✅ **Lösung:** Zweiphasiger Ansatz (implementiert!)

### JSON-Parsing
- ❌ Gemini gibt manchmal unvollständiges JSON
- ✅ **Lösung:** OpenAI für strukturierte Tasks

---

## 📊 Erwartete Ergebnisse (volle DB)

```
Vorträge: 1.897
Unique Keywords: 6.070
Themen: 20-30

Nach Phase 1:
├─ 20 Themen mit Namen + Beschreibung
└─ Keywords-Arrays: leer

Nach Phase 2:
├─ 20 Themen mit ~300 Keywords/Thema
├─ 100% Coverage (6.070/6.070)
└─ Frontend zeigt alle Themen + Keywords
```

---

## 🎯 Nächste Schritte

1. **Projekt verschieben** (machst du gerade)
2. **Backend starten** (im neuen Ordner)
3. **Phase 1: Themen generieren** (OpenAI, ~30 Sek)
4. **Phase 2: Batch-Zuordnung** (OpenAI/Gemini, ~3-4 Min)
5. **Frontend testen** (Strg+Shift+R)
6. **Bei Erfolg:** Backup wiederherstellen, OneDrive reaktivieren

---

**Viel Erfolg! Nach dem Verschieben sollte alles reibungslos funktionieren!** 🚀

**Erstellt:** Oktober 2025  
**Version:** 2.0 (LLM Provider + Zweiphasig)

