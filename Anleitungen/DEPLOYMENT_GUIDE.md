# Deployment Guide: LLM Provider System

**Quick Start für Gemini (kostenlos)**

---

## 📋 Voraussetzungen

- ✅ Node.js v18+ (aktuell: v22.18.0)
- ✅ Bestehende GA-Suche Installation
- ✅ Google Account für Gemini API

---

## 🚀 Deployment Schritte

### 1. Gemini API Key holen (2 Minuten)

1. Gehe zu: **https://aistudio.google.com/**
2. Anmelden mit Google-Account
3. Klicke **"Get API Key"** (oben rechts)
4. Klicke **"Create API key"**
5. **Kopiere den Key** (sieht aus wie: `AIzaSy...`)

---

### 2. .env Datei erstellen

Erstelle eine Datei `.env` im Projektverzeichnis:

```bash
# Google Gemini API (KOSTENLOS - 1500 Requests/Tag)
GEMINI_API_KEY=AIzaSy_DEIN_KEY_HIER

# Provider-Konfiguration
LLM_PROVIDER_DEFAULT=gemini
LLM_PROVIDER_SUMMARY=gemini
LLM_PROVIDER_KEYWORDS=gemini
LLM_PROVIDER_THEMES=gemini
LLM_PROVIDER_BATCH=gemini
LLM_PROVIDER_ANALYSIS=gemini

# Optional: Claude als Fallback (wenn Budget da)
# CLAUDE_API_KEY=sk-ant-xxxxx
# LLM_PROVIDER_ANALYSIS=claude

# Backend Port
PORT=3003
```

**Wichtig:** Ersetze `AIzaSy_DEIN_KEY_HIER` mit deinem echten Gemini API Key!

---

### 3. Backend neu starten

```powershell
# Backend stoppen (falls läuft): Strg+C

# Backend starten
node backend.js
```

**Erwartete Ausgabe:**
```
[LLM-PROVIDER] Modul geladen
Server läuft auf Port 3003
```

---

### 4. Funktionstest

#### Test 1: Provider-System testen

```powershell
node -e "const {getProviderForTask} = require('./llm-providers'); console.log(getProviderForTask('themes').name);"
```

**Erwartete Ausgabe:** `Gemini`

---

#### Test 2: Themen generieren (nutzt jetzt Top 1000 + Gemini)

**Browser öffnen:** http://localhost:3003

1. Wechsle zum **Timeline-Tab**
2. Scrolle zu **"Themen-Generierung"**
3. Klicke **"Themen generieren"** (30 Themen)
4. Warte ~30-60 Sekunden
5. ✅ Erfolg: "Themen erfolgreich generiert"

**Log im Backend:**
```
[THEMES-GEN] Analysiere 6070 unique Keywords (Top 1000 für Themen-Generierung)
[THEMES-GEN] Rufe Gemini API auf...
[THEMES-GEN] ✓ Gemini: Themen erfolgreich generiert: 30
```

---

#### Test 3: Batch-Zuordnung (NEU! - 100% Coverage)

**Derzeit nur via API:**

```powershell
curl -X POST http://localhost:3003/api/themes/assign-all-keywords `
  -H "Content-Type: application/json"
```

**Erwartete Ausgabe:**
```json
{
  "success": true,
  "message": "Batch-Zuordnung erfolgreich abgeschlossen",
  "stats": {
    "assigned": 5000,
    "total": 6070,
    "coverage": "100%",
    "provider": "Gemini"
  }
}
```

**Backend Log:**
```
[BATCH-ASSIGN] Verfügbare Themen: 30
[BATCH-ASSIGN] Total unique Keywords: 6070
[BATCH-ASSIGN] Bereits zugeordnet: 1000
[BATCH-ASSIGN] Noch zuzuordnen: 5070
[BATCH-ASSIGN] Verarbeite 11 Batches mit Gemini
[BATCH-ASSIGN] Batch 1/11: ✓ 500 Keywords | Progress: 9.1%
[BATCH-ASSIGN] Batch 2/11: ✓ 500 Keywords | Progress: 18.2%
...
[BATCH-ASSIGN] ✓ Verarbeitung abgeschlossen: 5070 neue Zuordnungen
[BATCH-ASSIGN] ✓ Erweiterte themes-database.json gespeichert
```

**Dauer:** ~2-3 Minuten  
**Kosten:** $0.08 (mit Gemini)

---

## ✅ Deployment Checklist

- [ ] Gemini API Key geholt
- [ ] `.env` erstellt mit GEMINI_API_KEY
- [ ] Backend neu gestartet (`node backend.js`)
- [ ] Provider-Test erfolgreich
- [ ] Themen neu generiert (Top 1000!)
- [ ] Batch-Zuordnung durchgeführt (100% Coverage!)
- [ ] Frontend getestet (Themen-Filter, Keywords)

---

## 🔧 Troubleshooting

### Backend startet nicht

**Fehler:** `Cannot find module 'llm-providers'`

**Lösung:** 
```powershell
# Prüfe ob Datei existiert
dir llm-providers.js

# Falls nicht, pull neueste Version von Git
git pull origin main
```

---

### "Kein LLM-Provider verfügbar"

**Lösung:** 
1. Prüfe `.env` Datei existiert
2. Prüfe `GEMINI_API_KEY=...` ist gesetzt
3. Backend neu starten

---

### "Rate Limit erreicht" (Gemini)

**Ursache:** Free Tier Limits überschritten
- 15 Requests/Minute
- 1500 Requests/Tag

**Lösung:**
- **Option 1:** 1 Minute warten
- **Option 2:** Upgrade auf bezahltes Gemini Tier
- **Option 3:** Zurück zu Claude (wenn Budget da)

```bash
# In .env
LLM_PROVIDER_DEFAULT=claude
```

---

### Batch-Zuordnung schlägt fehl

**Lösung 1:** Prüfe ob Themen existieren
```powershell
# themes-database.json muss existieren
dir themes-database.json
```

Falls nicht: Zuerst Themen generieren!

**Lösung 2:** Prüfe Backend-Logs
```
[BATCH-ASSIGN] Fehler in Batch X: ...
```

Bei JSON-Parse-Fehlern: Batch wird übersprungen, Verarbeitung läuft weiter

---

## 📊 Performance-Monitoring

### Keyword-Wiederverwendung überwachen

**Backend-Log ansehen:**
```
[KEYWORDS-ITER] GA051/1: ✓ 15 Keywords generiert
[KEYWORDS-ITER]   Existing: 12, New: 3
```

**Ziel:** Existing > 70% (Verbesserung von ~50%)

---

### Themen-Coverage prüfen

```powershell
# Öffne themes-database.json
notepad themes-database.json

# Zähle Keywords pro Thema (sollte jetzt 100-300 sein statt 10-20)
```

---

## 🌟 Erwartete Verbesserungen

### Nach Deployment

✅ **Keyword-Reduktion:** 20-30% weniger neue Keywords  
✅ **Wiederverwendung:** 70-80% (statt 50-60%)  
✅ **Themen-Coverage:** 100% (statt 5%)  
✅ **Kosten:** 93% günstiger (Gemini vs Claude)

---

## 🔄 Zurück zu Claude (Optional)

Falls später Claude-Budget wieder da ist:

```bash
# In .env
LLM_PROVIDER_DEFAULT=claude
LLM_PROVIDER_BATCH=gemini  # Batch bleibt günstig mit Gemini!
```

Backend neu starten → Fertig!

---

## 📞 Support

Bei Problemen:
1. Prüfe Backend-Logs: `node backend.js`
2. Prüfe `.env` Konfiguration
3. Siehe `IMPLEMENTATION_SUMMARY.md` für Details
4. Siehe `SETUP_LLM_PROVIDERS.md` für Konfiguration

---

**Deployment Date:** Oktober 2025  
**Version:** 2.0  
**Status:** ✅ Ready for Production

