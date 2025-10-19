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

**Stand**: Oktober 2025  
**Version**: 1.0  
**Projekt**: GA-Suche (Rudolf Steiner Gesamtausgabe)
