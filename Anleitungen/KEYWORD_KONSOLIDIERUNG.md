# Keyword-Konsolidierung und Themen-Generierung

## Übersicht

Dieses Dokument beschreibt die Funktionen zur Konsolidierung ähnlicher Keywords und zur Generierung thematischer Gruppierungen in der GA-Suche Anwendung.

---

## 1. Themen-Generierung (Standard)

### Zweck
Gruppiert alle Keywords mittels KI (Claude Sonnet 4) in übergeordnete Themen. Dies erleichtert die Navigation und ermöglicht thematische Filterung in der Timeline-Ansicht.

### Voraussetzungen
- `keywords-database.json` muss existieren und Keywords enthalten
- Backend-Server läuft auf Port 3003
- Claude API Key ist konfiguriert

### Ablauf

1. **Navigation**: 
   - Wechseln Sie zum **Timeline-Tab** in der linken Sidebar
   - Scrollen Sie im Admin-Bereich nach unten zu **"Themen-Generierung"**

2. **Konfiguration**:
   - **Anzahl Themen**: Legen Sie fest, wie viele Themen erstellt werden sollen (Standard: 30)
   - Empfohlener Bereich: 20-40 Themen
   - Weniger Themen = breitere Kategorien
   - Mehr Themen = spezifischere Kategorien

3. **Generierung starten**:
   - Klicken Sie auf **"Themen generieren"**
   - Der Prozess analysiert die Top 300 Keywords
   - Dauer: ca. 30-60 Sekunden
   - Kosten: ca. $0.30-$0.50 pro Generierung

4. **Ergebnis**:
   - Neue `themes-database.json` wird erstellt
   - Jedes Thema enthält:
     - Themenname
     - Liste charakteristischer Keywords
     - Zuordnung zu Vorträgen
   - Die Themes sind sofort in den Filter-Dropdowns verfügbar

### Aktuelle Einschränkung (Stand: Oktober 2025)
⚠️ **Wichtig**: Die Themen-Generierung verwendet aktuell nur die **Top 300 häufigsten Keywords** aus der Datenbank (~23.000 Keywords). Dies ist eine temporäre Lösung aufgrund von:
- Claude API Token-Limits (max ~8192 Tokens)
- HTTP 500 Fehler bei zu großen Keyword-Listen

📋 **Geplante Erweiterung**: Siehe Abschnitt 10 für die vollständige Batch-Verarbeitung aller Keywords.

### Wann verwenden?
- Erstmalige Einrichtung der thematischen Navigation
- Nach größeren Änderungen an der Keyword-Datenbank
- Wenn Sie die Anzahl der Themen anpassen möchten
- Nach einer Keyword-Konsolidierung (siehe unten)

---

## 2. Keyword-Konsolidierung

### Zweck
Reduziert die Anzahl ähnlicher oder redundanter Keywords durch intelligente Zusammenführung. Dies verbessert:
- Übersichtlichkeit der Keyword-Liste
- Suchgenauigkeit
- Performance der Anwendung

### Beispiele für Konsolidierung
```
Vorher:                    Nachher:
├─ karma                   → Karma
├─ Karma
├─ karmagesetz
├─ karmabildung
└─ karmisch

├─ atlantis               → Atlantis
├─ Atlantis
└─ atlantische Zeit

├─ reinkarnation          → Reinkarnation
└─ Wiederverkörperung
```

---

## 3. Konsolidierungs-Workflow (Komplett)

### Phase 1: Vorschau generieren

1. **Navigation**:
   - Timeline-Tab → Admin-Bereich → **"Keyword-Konsolidierung"**

2. **Konsolidierungsstärke wählen**:
   - **Slider** von 0.0 bis 1.0
   
   **0.0 - 0.3 (Sehr streng)**:
   - Nur fast identische Keywords
   - Beispiel: "karma" + "Karma" → "Karma"
   - Geringe Reduktion, sehr sicher
   
   **0.3 - 0.7 (Mittel) ⭐ Empfohlen**:
   - Wortstämme werden zusammengeführt
   - Beispiel: "karma", "karmagesetz", "karmisch" → "Karma"
   - Gute Balance zwischen Reduktion und Genauigkeit
   
   **0.7 - 1.0 (Locker)**:
   - Semantisch ähnliche Keywords
   - Beispiel: "reinkarnation", "wiederverkörperung" → "Reinkarnation"
   - Hohe Reduktion, prüfen Sie die Vorschau sorgfältig

3. **Vorschau starten**:
   - Klicken Sie auf **"Vorschau generieren"**
   - Dauer: ca. 10-30 Sekunden (bei ~23.000 Keywords)
   - Der Button zeigt "Wird verarbeitet..." während der Berechnung

4. **Vorschau analysieren**:
   Die Vorschau zeigt:
   - **Anzahl vor Konsolidierung**: z.B. 23.051 Keywords
   - **Anzahl nach Konsolidierung**: z.B. 18.500 Keywords
   - **Reduktion**: z.B. 19,7%
   - **Top 50 Beispiele**: Welche Keywords zusammengeführt werden
   
   Beispiel-Anzeige:
   ```
   Karma ← karma, Karmagesetz, karmabildung, karmisch (5 Keywords)
   Atlantis ← atlantis, atlantische Zeit, Atlantische Epoche (3 Keywords)
   ```

5. **Entscheidung**:
   - ✅ Vorschau sieht gut aus → Weiter zu Phase 2
   - ❌ Zu viele/wenige Zusammenführungen → Stärke anpassen und neue Vorschau

### Phase 2: Konsolidierung ausführen

1. **Button erscheint**: Nach erfolgreicher Vorschau wird **"Konsolidierung ausführen"** sichtbar

2. **Konsolidierung starten**:
   - Klicken Sie auf **"Konsolidierung ausführen"**
   - Bestätigen Sie den Dialog

3. **Was passiert**:
   - ✅ **Backup erstellt**: `keywords-database-backup-[timestamp].json`
   - ✅ **Konsolidierte DB erstellt**: `keywords-database-consolidated-[timestamp].json`
   - ✅ **Original bleibt unverändert**: `keywords-database.json`
   
4. **Ergebnis**:
   ```
   ✓ Konsolidierung erfolgreich!
   Backup: keywords-database-backup-2025-10-19T14-30-00.json
   Konsolidierte DB: keywords-database-consolidated-2025-10-19T14-30-00.json
   
   Nächster Schritt: Klicken Sie auf "Aktivieren" um die 
   konsolidierte Datenbank zu verwenden und Themen neu zu generieren.
   ```

### Phase 3: Aktivierung und Themen-Generierung

1. **Button erscheint**: Nach erfolgreicher Konsolidierung wird **"Aktivieren + Themen neu generieren"** sichtbar

2. **Aktivierung starten**:
   - Klicken Sie auf **"Aktivieren + Themen neu generieren"**
   - Bestätigen Sie den Dialog

3. **Was passiert automatisch**:
   
   **Schritt 1: Datenbank-Aktivierung**
   - Aktuelle DB wird gesichert: `keywords-database.json` → `keywords-database-pre-consolidation.json`
   - Konsolidierte DB wird aktiviert: `keywords-database-consolidated-[timestamp].json` → `keywords-database.json`
   
   **Schritt 2: Themen-Generierung**
   - Automatischer Start der Themen-Generierung
   - Verwendet die frisch aktivierte, konsolidierte Datenbank
   - Erstellt neue `themes-database.json` mit konsolidierten Keywords
   - Dauer: ca. 30-60 Sekunden

4. **Abschluss**:
   ```
   ✓ Konsolidierung abgeschlossen!
   ✓ Datenbank aktiviert
   ✓ Themen neu generiert
   
   Bitte laden Sie die Seite neu (F5).
   ```

5. **Seite neu laden**: 
   - Drücken Sie **F5** um die Änderungen zu sehen
   - Alle Dropdowns und Filter verwenden jetzt die konsolidierten Keywords

---

## 4. Dateien und Backups

### Dateien nach Konsolidierung

```
Projektordner/
├─ keywords-database.json                              [AKTIV - konsolidiert]
├─ keywords-database-pre-consolidation.json            [BACKUP - vor Aktivierung]
├─ keywords-database-backup-2025-10-19T14-30-00.json  [BACKUP - vor Konsolidierung]
├─ keywords-database-consolidated-2025-10-19T14-30-00.json  [Konsolidierte Version]
└─ themes-database.json                                [AKTIV - mit konsolidierten KW]
```

### Rückkehr zur Original-Datenbank

Falls Sie zur Original-Datenbank zurückkehren möchten:

1. **Backend-Server stoppen** (Strg+C)

2. **Dateien umbenennen**:
   ```powershell
   # Aktuelle (konsolidierte) DB sichern
   Rename-Item keywords-database.json keywords-database-consolidated-active.json
   
   # Original wiederherstellen
   Copy-Item keywords-database-pre-consolidation.json keywords-database.json
   ```

3. **Themen neu generieren** (mit Original-Keywords)

4. **Server neu starten**: `node backend.js`

---

## 5. Best Practices

### Empfohlene Reihenfolge für neue Projekte

1. **Batch-Keyword-Generierung** für alle Vorträge durchführen
2. **Konsolidierung** mit Stärke 0.5 durchführen
3. **Themen generieren** mit 30 Themen
4. **Testen und anpassen**:
   - Filter ausprobieren
   - Timeline navigieren
   - Ggf. Themenanzahl anpassen (20-40)

### Wann konsolidieren?

**Ja, konsolidieren wenn**:
- Viele ähnliche Keywords existieren (z.B. "karma", "Karma", "karmisch")
- Die Keyword-Liste unübersichtlich ist
- Sie häufig falsche/fehlende Treffer haben
- Ersteinrichtung eines großen Datensatzes

**Nein, nicht konsolidieren wenn**:
- Nuancen wichtig sind (z.B. "Karma" vs. "Karmagesetz" als separate Konzepte)
- Die Datenbank bereits sauber ist
- Sie nur die Themenanzahl ändern wollen

### Wartung

**Regelmäßig** (nach größeren Änderungen):
- Themen neu generieren bei geänderten Keywords
- Alte Backup-Dateien archivieren (älter als 30 Tage)

**Einmalig** (bei Bedarf):
- Konsolidierung nur bei großen Datenbank-Änderungen
- Nicht nach jeder kleinen Keyword-Änderung

---

## 6. Performance und Kosten

### Themen-Generierung
- **Dauer**: 30-60 Sekunden
- **Kosten**: ~$0.30-$0.50 pro Durchlauf
- **Frequenz**: Nach Bedarf, typisch 1-5x bei Einrichtung

### Konsolidierung
- **Vorschau-Dauer**: 10-30 Sekunden (bei ~23.000 Keywords)
- **Ausführung-Dauer**: 10-30 Sekunden
- **Kosten**: Keine (lokal berechnet)
- **Frequenz**: Typisch 1-2x bei Einrichtung

### Optimierungen im Code
- Top 300 Keywords für Themen-Generierung (Qualität vs. Kosten)
- Substring-basierte Konsolidierung (Geschwindigkeit)
- Levenshtein-Distanz nur für kurze Keywords bei hohem Factor
- Progress-Logging alle 2000 Keywords

---

## 7. Fehlerbehebung

### Vorschau dauert sehr lange (>2 Minuten)
- **Ursache**: Zu viele Keywords, zu niedriger Factor
- **Lösung**: 
  - Backend-Server neu starten
  - Factor auf 0.5-0.7 erhöhen
  - Bei Wiederholung: Backend-Code überprüfen

### Themen-Generierung schlägt fehl
- **Mögliche Ursachen**:
  - Keine Verbindung zur Claude API
  - API-Key ungültig/abgelaufen
  - Rate Limit erreicht
- **Lösung**:
  - Backend-Log prüfen (Terminal)
  - API-Key in `backend.js` überprüfen
  - 1 Minute warten und erneut versuchen

### "Keine Keywords gefunden" nach Konsolidierung
- **Ursache**: Themen-Datenbank nicht aktualisiert
- **Lösung**: 
  - Themen neu generieren (Button)
  - Seite neu laden (F5)

### Konsolidierung rückgängig machen
- Siehe Abschnitt 4: "Rückkehr zur Original-Datenbank"

---

## 8. Technische Details

### Konsolidierungs-Algorithmus

**Stufe 1: Substring-Matching** (schnell)
```javascript
if (keyword1.includes(keyword2)) {
  similarity = shorterLength / longerLength
  // Beispiel: "karma" in "karmagesetz"
  // similarity = 5/11 = 0.45
}
```

**Stufe 2: Levenshtein-Distanz** (bei Factor >= 0.6, kurze Keywords)
```javascript
distance = levenshtein("karma", "karme")
similarity = 1 - (distance / maxLength)
// Beispiel: distance=1, maxLength=5
// similarity = 1 - (1/5) = 0.8
```

**Stufe 3: Prefix-Matching**
```javascript
commonPrefix = countCommonPrefix("karmabildung", "karmagesetz")
similarity = commonPrefix / maxLength
// Beispiel: "karma" = 5 Zeichen gemeinsam
```

### Datenbank-Struktur

**keywords-database.json**:
```json
{
  "GA051/4": {
    "lectureId": "GA051/4",
    "date": "1903-10-08",
    "year": 1903,
    "theme": "Erkenntnistheorie",
    "keywords": [
      {
        "term": "Karma",
        "index": 123,
        "heading": "Die Entwicklung des Ich",
        "level": "h3"
      }
    ]
  }
}
```

**themes-database.json**:
```json
{
  "Erkenntnistheorie": {
    "keywords": [
      "Bewusstsein",
      "Erkenntnis",
      "Wahrnehmung",
      "Denken"
    ]
  }
}
```

---

## 9. Zusammenfassung

### Quick Reference: Nur Themenanzahl ändern
```
1. Timeline-Tab öffnen
2. Anzahl Themen eingeben (z.B. 25)
3. "Themen generieren" klicken
4. 30-60 Sekunden warten
5. Fertig!
```

### Quick Reference: Komplette Konsolidierung
```
1. Konsolidierungsstärke wählen (0.5 empfohlen)
2. "Vorschau generieren" → Prüfen
3. "Konsolidierung ausführen" → Backups werden erstellt
4. "Aktivieren + Themen neu generieren" → Automatischer Ablauf
5. Seite neu laden (F5)
6. Fertig!
```

### Sicherheit
- ✅ Mehrfache Backups werden automatisch erstellt
- ✅ Original-Datenbank bleibt immer erhalten
- ✅ Rückkehr zur Original-DB jederzeit möglich
- ✅ Kein Datenverlust bei Fehlern

---

## 10. Geplante Erweiterung: Vollständige Keyword-Erfassung

### Problem: Top 300 Limitierung

**Aktueller Stand**:
- Nur die 300 häufigsten Keywords werden für Themen-Generierung verwendet
- Restliche ~22.700 Keywords werden nicht erfasst
- Resultat: Viele Keywords erscheinen nicht in thematischen Zuordnungen

**Warum die Limitierung?**:
- Claude API Token-Limit: ~8.000 Tokens Input
- 23.000 Keywords = ~100.000+ Tokens (überschreitet Limit massiv)
- HTTP 500 Fehler bei zu großen Anfragen

### Geplante Lösung: Hierarchische Batch-Verarbeitung (Option 2)

#### Phase 1: Haupt-Themen generieren (einmalig)

1. **Flexible Themenanzahl**: 
   - Benutzer wählt Anzahl (10-50 Themen)
   - Standard: 30 Themen

2. **Basis-Keywords**: 
   - Top 300-500 häufigste Keywords
   - Diese bilden die Kern-Charakteristik jedes Themas

3. **Ergebnis**: 
   - 30 klar definierte Haupt-Themen
   - Jedes Thema hat charakteristische Keywords
   - Beispiel: "Karma und Reinkarnation", "Christologie", "Atlantis und Mysterien"

#### Phase 2: Batch-Zuordnung aller restlichen Keywords

**Prozess**:

1. **Batch-Größe**: 500 Keywords pro Anfrage

2. **Anzahl Batches**: 
   - ~23.000 Keywords / 500 = ~46 Batches
   - Pro Batch: ca. 3-5 Sekunden

3. **API-Anfrage pro Batch**:
   ```
   Prompt: "Ordne diese 500 Keywords einem der folgenden 30 Themen zu:
   
   Themen:
   1. Karma und Reinkarnation
   2. Christologie und Evangelien
   3. Atlantis und Mysterien
   ... (alle 30 Themen)
   
   Keywords:
   - Astralleib
   - Bewusstseinsentwicklung
   - Chakren
   ... (500 Keywords)
   
   Gib zurück: {keyword: thema}"
   ```

4. **Kosten**:
   - Nur Klassifizierung, keine Themen-Generierung
   - ~$0.01-0.02 pro Batch
   - Gesamt: ~$0.50-1.00 für alle 23.000 Keywords

5. **Dauer**:
   - 46 Batches × 4 Sekunden = ~3 Minuten
   - Mit Progress-Bar sichtbar

#### Phase 3: Zusammenführung und Speicherung

1. **Merge mit Phase 1**:
   - Basis-Themen (Top 300) + zugeordnete Keywords
   - Duplikate entfernen

2. **Neue themes-database.json**:
   ```json
   {
     "Karma und Reinkarnation": {
       "keywords": [
         "Karma", "Reinkarnation", "Wiedergeburt",
         "Schicksal", "Ausgleich", ...
         // ALLE zugeordneten Keywords, nicht nur Top 300
       ],
       "keywordCount": 847,
       "source": "generated+batch"
     }
   }
   ```

### Implementierungs-Schritte (TODO)

#### Backend (backend.js)

**Neue Funktionen**:
```javascript
// 1. Batch-Zuordnung
async function assignKeywordsToBatches(allKeywords, themes, batchSize = 500)

// 2. Claude API für Klassifizierung
async function classifyKeywordBatch(keywords, themeNames)

// 3. Progress-Tracking
function updateBatchProgress(current, total)
```

**Neuer API-Endpoint**:
```javascript
app.post('/api/assign-all-keywords-to-themes', async (req, res) => {
  // 1. Lade themes-database (Haupt-Themen)
  // 2. Sammle ALLE Keywords aus keywords-database
  // 3. Filtere bereits zugeordnete raus
  // 4. Batch-Verarbeitung mit Progress-Updates
  // 5. Merge und speichere erweiterte themes-database
})
```

#### Frontend (index.html)

**Neue UI-Komponente** (nach "Themen generieren"):
```html
<div style="margin-top: 1rem; padding: 0.8rem; background: var(--sidebar-bg); 
     border-radius: 4px; border: 1px solid var(--border-color);">
  <h4>Alle Keywords den Themen zuordnen</h4>
  <p style="font-size: 0.9em; color: var(--secondary-text);">
    Ordnet alle ~23.000 Keywords den generierten Themen zu 
    (Dauer: ~3 Min, Kosten: ~$0.50-1.00)
  </p>
  
  <div id="batchAssignStats">
    <span>Haupt-Themen: <strong>30</strong></span> | 
    <span>Bereits zugeordnet: <strong>300</strong> Keywords</span> | 
    <span>Verbleibend: <strong>22.751</strong> Keywords</span>
  </div>
  
  <button onclick="assignAllKeywordsToThemes()" 
          style="margin-top: 0.5rem; padding: 8px 16px; 
                 background: #467886; color: white;">
    Batch-Zuordnung starten
  </button>
  
  <!-- Progress Bar -->
  <div id="batchAssignProgress" style="display: none; margin-top: 0.8rem;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
      <span>Batch <span id="batchCurrent">0</span> / <span id="batchTotal">46</span></span>
      <span><span id="batchPercent">0</span>%</span>
    </div>
    <div style="width: 100%; height: 8px; background: var(--border-color); 
                border-radius: 4px; overflow: hidden;">
      <div id="batchProgressBar" style="width: 0%; height: 100%; 
           background: #467886; transition: width 0.3s;"></div>
    </div>
  </div>
  
  <div id="batchAssignStatus" style="display: none; margin-top: 0.5rem;"></div>
</div>
```

**Neue JavaScript-Funktion**:
```javascript
async function assignAllKeywordsToThemes() {
  // 1. Bestätigung
  if (!confirm('Alle Keywords den Themen zuordnen?\n\nDauer: ~3 Min\nKosten: ~$0.50-1.00')) {
    return;
  }
  
  // 2. UI vorbereiten
  const progressDiv = document.getElementById('batchAssignProgress');
  const statusDiv = document.getElementById('batchAssignStatus');
  progressDiv.style.display = 'block';
  
  try {
    // 3. API-Call mit Server-Sent Events für Progress
    const eventSource = new EventSource(`${API_BASE}/api/assign-all-keywords-to-themes`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        // Update Progress Bar
        document.getElementById('batchCurrent').textContent = data.current;
        document.getElementById('batchTotal').textContent = data.total;
        document.getElementById('batchPercent').textContent = 
          ((data.current / data.total) * 100).toFixed(1);
        document.getElementById('batchProgressBar').style.width = 
          `${(data.current / data.total) * 100}%`;
      }
      
      if (data.type === 'complete') {
        eventSource.close();
        statusDiv.innerHTML = `<div style="color: #5cb85c;">
          ✓ Batch-Zuordnung abgeschlossen!<br>
          ${data.totalAssigned} Keywords zugeordnet<br>
          Neue themes-database.json gespeichert
        </div>`;
        statusDiv.style.display = 'block';
      }
    };
    
  } catch (error) {
    console.error('[BATCH-ASSIGN] Fehler:', error);
    statusDiv.innerHTML = `<div style="color: #d9534f;">✗ Fehler: ${error.message}</div>`;
  }
}
```

### Vorteile der Batch-Lösung

✅ **Vollständigkeit**: Alle 23.000+ Keywords erfasst  
✅ **Kosteneffizient**: Nur Klassifizierung (~$1 statt $10+)  
✅ **Schnell**: ~3 Minuten statt Stunden  
✅ **Skalierbar**: Funktioniert auch bei 50.000+ Keywords  
✅ **Transparent**: Progress-Bar zeigt Fortschritt  
✅ **Flexibel**: Themenanzahl frei wählbar (10-50)  

### Workflow nach Implementierung

```
1. Themen-Generierung (Basis)
   → Input: Top 300-500 Keywords
   → Output: 30 Haupt-Themen mit Kern-Keywords
   → Dauer: 30-60 Sekunden
   → Kosten: ~$0.30

2. Batch-Zuordnung (Vollständig)
   → Input: Restliche ~22.700 Keywords + 30 Themen
   → Output: Erweiterte themes-database mit ALLEN Keywords
   → Dauer: ~3 Minuten
   → Kosten: ~$0.50-1.00

3. Ergebnis
   → Jedes der 30 Themen hat jetzt 500-1500 Keywords
   → ALLE Keywords sind thematisch zugeordnet
   → Filter-Dropdowns zeigen vollständige Listen
```

### Priorisierung

**Phase 1** (Jetzt implementiert):
- ✅ Themen-Generierung mit Top 300
- ✅ Flexible Themenanzahl (10-50)
- ✅ Konsolidierungs-System

**Phase 2** (Nächster Schritt - TODO):
- ⏳ Batch-Zuordnung aller Keywords
- ⏳ Progress-Tracking mit Server-Sent Events
- ⏳ Erweiterte themes-database

**Phase 3** (Optional, später):
- ⏳ Manuelle Keyword-Verschiebung zwischen Themen
- ⏳ Themen-Merge (2 Themen zusammenführen)
- ⏳ Themen-Split (1 Thema in 2 aufteilen)

---

**Stand**: Oktober 2025  
**Version**: 1.1  
**Projekt**: GA-Suche (Rudolf Steiner Gesamtausgabe)

**Status der Batch-Verarbeitung**: 🚧 **Geplant, noch nicht implementiert**  
**Geschätzte Implementierungszeit**: 4-6 Stunden  
**Geschätzter Nutzen**: Vollständige thematische Abdeckung aller Keywords
