# Test-Anleitung: Keyword-Merge-Strategie

## Ziel
Überprüfen, ob manuell bearbeitete Keywords bei der Neugenerierung erhalten bleiben.

## Voraussetzungen
- Backend läuft (`node backend.js`)
- Frontend ist geöffnet
- Keyword-Manager ist zugänglich

## Test-Szenario

### Schritt 1: Ausgangssituation schaffen
1. Wählen Sie einen Vortrag mit bestehenden Keywords (z.B. `GA001_01`)
2. Notieren Sie sich die aktuellen Keywords:
   ```
   Beispiel:
   - Astralleib
   - Karma  
   - Reinkarnation
   ```

### Schritt 2: Manuelle Bearbeitung durchführen
1. Öffnen Sie den **Keyword-Manager**
2. Wählen Sie einen Vortrag aus
3. Bearbeiten Sie ein Keyword:
   - **Umbenennen:** "Karma" → "Karmagesetz"
   - **Oder:** Beschreibung ändern
4. Speichern Sie die Änderung

**Erwartetes Ergebnis in DB:**
```json
{
  "term": "Karmagesetz",
  "manuallyEdited": true,
  "lastEditedAt": "2025-11-02T..."
}
```

### Schritt 3: Backend-Log prüfen
Suchen Sie in der Console nach:
```
[UPDATE-KW] ✓ Keywords-Database aktualisiert (manuallyEdited=true)
```

### Schritt 4: Neugenerierung durchführen
1. Gehen Sie zum **Keywords-Tab**
2. Wählen Sie den GA-Band des Testvortrags
3. Klicken Sie auf **"Batch starten (V2)"** oder **"TOC&KW neu"**
4. Warten Sie auf die Generierung

### Schritt 5: Merge-Log überprüfen
Suchen Sie in der Backend-Console nach:
```
[KEYWORDS-MERGE] Merge für GA001_01: 3 bestehende + X neue Keywords
[KEYWORDS-MERGE] Erhalte 1 manuell bearbeitete Keywords
[KEYWORDS-MERGE] Füge X neue Keywords hinzu
[KEYWORDS-MERGE] ✓ Merge abgeschlossen: X Keywords total
```

### Schritt 6: Ergebnis validieren
1. Öffnen Sie den Vortrag erneut im Keyword-Manager
2. **Prüfen Sie:**
   - ✅ Ist "Karmagesetz" noch vorhanden?
   - ✅ Hat es immer noch `manuallyEdited: true`?
   - ✅ Wurden neue Keywords hinzugefügt?
   - ✅ Gibt es keine Duplikate?

## Erwartete Ergebnisse

### ✅ Erfolg
```json
{
  "GA001_01": {
    "keywords": [
      {
        "term": "Karmagesetz",
        "manuallyEdited": true,
        "lastEditedAt": "2025-11-02T10:30:00Z"
      },
      {
        "term": "Ätherleib",
        "manuallyEdited": false
      }
    ],
    "lastMerge": "2025-11-02T11:00:00Z"
  }
}
```

### ❌ Fehler
- "Karmagesetz" ist verschwunden → Merge-Logik fehlerhaft
- "Karma" ist zurück → Alte Keywords überschreiben manuelle
- Duplikate vorhanden → Duplikatserkennung fehlerhaft

## Zusätzliche Tests

### Test 2: Neues Keyword hinzufügen
1. Fügen Sie manuell ein neues Keyword hinzu
2. Regenerieren Sie
3. **Erwartung:** Das neue Keyword bleibt erhalten

### Test 3: Keyword löschen
1. Löschen Sie ein Keyword
2. Regenerieren Sie
3. **Erwartung:** Das gelöschte Keyword wird NICHT wiederhergestellt

### Test 4: Mehrere manuelle Änderungen
1. Bearbeiten Sie 3 Keywords
2. Regenerieren Sie
3. **Erwartung:** Alle 3 bleiben erhalten

## Debugging

Falls der Test fehlschlägt:

1. **Prüfen Sie die Keywords-Database direkt:**
   ```bash
   # Im Projektverzeichnis
   cat keywords-database.json | grep -A 10 "GA001_01"
   ```

2. **Prüfen Sie Backend-Logs:**
   - Suchen Sie nach `[KEYWORDS-MERGE]`
   - Prüfen Sie ob `manuallyEdited: true` gesetzt wird

3. **Prüfen Sie Backup:**
   ```bash
   ls -la keywords-database-backup-*.json
   ```

## Rollback bei Problemen

Falls etwas schiefgeht:

```bash
# Finde neuestes Backup
ls -t keywords-database-backup-*.json | head -1

# Stelle wieder her
cp keywords-database-backup-YYYY-MM-DD-HH-MM-SS.json keywords-database.json

# Starte Backend neu
```

---

**Test durchgeführt am:** ___________  
**Ergebnis:** ⬜ Erfolgreich  ⬜ Fehlgeschlagen  
**Notizen:**

