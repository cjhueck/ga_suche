# Keyword-Konsolidierung

## Übersicht

Dieses Script konsolidiert die 3.272 Keywords aus `keywords-database.json` unter Verwendung von Claude Sonnet 4.5, um die Gesamtzahl durch intelligente Zusammenführung zu reduzieren.

## Voraussetzungen

1. **Node.js** installiert
2. **Anthropic API Key** vorhanden
3. **@anthropic-ai/sdk** Package installiert:
   ```bash
   npm install @anthropic-ai/sdk
   ```

## Installation & Ausführung

### 1. API Key setzen

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-...

# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Script ausführen

```bash
node consolidate-keywords.js
```

## Was das Script tut

### Phase 1: Daten laden
- Lädt `keywords-database.json` (3.921 Vorträge)
- Lädt `themes-database.json` (Themen-Struktur als Orientierung)
- Extrahiert alle 3.272 unique Keywords

### Phase 2: Konsolidierung
- Verarbeitet Keywords in Batches von 500 (wegen API-Limits)
- Claude Sonnet 4.5 analysiert jeden Batch und:
  - Findet Wortstamm-Varianten (z.B. "Bewusstseinsseele" vs "Bewusstseinseele")
  - Identifiziert inhaltlich sehr ähnliche Begriffe
  - Vereinheitlicht Schreibweisen
  - Ordnet Keywords bestehenden Themen zu
  - Erstellt ggf. neue Themen

### Phase 3: Anwendung
- Erstellt Mapping: `altes Keyword → neues Keyword`
- Wendet Mapping auf alle 3.921 Vorträge an
- Entfernt Duplikate in jedem Vortrag
- **Beispiel:** Vortrag mit 10 Keywords → nach Konsolidierung evtl. nur noch 6

### Phase 4: Speicherung
- Erstellt Backup: `keywords-database-backup-[timestamp].json`
- Speichert konsolidierte Datenbank: **`keywords-database-consolidated.json`**
- Speichert Report: **`keywords-consolidation-report.json`**

## Output-Dateien

### `keywords-database-consolidated.json`
Die konsolidierte Keywords-Datenbank mit derselben Struktur wie das Original, aber:
- Vereinheitlichte Keyword-Schreibweisen
- Zusammengeführte ähnliche Keywords
- Keine Duplikate pro Vortrag

### `keywords-consolidation-report.json`
Detaillierter Report mit:
```json
{
  "timestamp": "2025-11-12T...",
  "summary": {
    "totalKeywordsBefore": 3272,
    "totalKeywordsAfter": 2450,
    "consolidationsMade": 822,
    "newThemesCreated": 5
  },
  "consolidations": [
    {
      "original": "Bewusstseinseele",
      "consolidatedTo": "Bewusstseinsseele",
      "reason": "Wortstamm-Variante",
      "theme": "Seelenglieder"
    }
  ],
  "newThemes": [...],
  "mapping": {
    "Bewusstseinseele": "Bewusstseinsseele",
    "Christus-Impuls": "Christus-Ereignis",
    ...
  }
}
```

## Konsolidierungs-Regeln

Claude verwendet folgende Regeln:

### ✅ WIRD konsolidiert:
1. **Wortstamm-Varianten:** "Budhi" + "Buddhi" → "Buddhi"
2. **Tippfehler/Rechtschreibung:** "Bewusstseinseele" → "Bewusstseinsseele"
3. **Nahezu synonyme Begriffe:** "Christus-Impuls" + "Christus-Ereignis" → "Christus-Ereignis"
4. **Schreibweisen:** "Verstandes- & Gemütsseele" vs "Verstandesseele" → einheitlich

### ❌ WIRD NICHT konsolidiert:
1. **Klar unterschiedliche Konzepte:** "Physischer Leib" ≠ "Ätherleib"
2. **Verschiedene Hierarchien:** "Archai" ≠ "Archangeloi"
3. **Spezifisch vs. allgemein:** Beide behalten wenn relevant

## Geschätzte Laufzeit

- **Batches:** ca. 7 Batches (3.272 ÷ 500)
- **Zeit pro Batch:** ~10-20 Sekunden
- **Gesamtzeit:** ~2-5 Minuten
- **API-Kosten:** ca. $0.50-1.00 (abhängig von Prompt-Größe)

## Nach der Konsolidierung

Die konsolidierte Datenbank kann verwendet werden:
1. In `app.html` (Timeline-Tab)
2. In `keyword-manager.html`
3. Für alle weiteren Analysen

Um die konsolidierte Version zu aktivieren:
```bash
# Backup des Originals (falls noch nicht vorhanden)
cp keywords-database.json keywords-database-original.json

# Konsolidierte Version aktivieren
cp keywords-database-consolidated.json keywords-database.json
```

## Troubleshooting

### "ANTHROPIC_API_KEY nicht gesetzt"
```bash
# Prüfen ob gesetzt:
echo $env:ANTHROPIC_API_KEY  # PowerShell
echo %ANTHROPIC_API_KEY%      # CMD
```

### "Cannot find module '@anthropic-ai/sdk'"
```bash
npm install @anthropic-ai/sdk
```

### "JSON parse error"
Das Script versucht automatisch JSON aus der Claude-Antwort zu extrahieren. Bei Fehlern wird der Batch übersprungen und im Log angezeigt.

## Manuelle Nachbearbeitung

Nach der automatischen Konsolidierung können Sie den Report (`keywords-consolidation-report.json`) prüfen und ggf. manuell nachbessern:

1. Report öffnen und `consolidations` durchsehen
2. Falls nötig: `mapping` im Report anpassen
3. Script `apply-manual-consolidation.js` ausführen (erstelle ich auf Anfrage)

## Fragen?

Bei Fragen oder Problemen bitte melden!

