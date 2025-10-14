# Batch-Schlagwort-Generierung

## Übersicht

Die neue Batch-Schlagwort-Generierung ermöglicht es, mehrere Schlagwörter gleichzeitig zu verarbeiten und durch die KI analysieren zu lassen. Dies ist besonders nützlich, wenn Sie eine vorgefertigte Liste von Schlagwörtern haben, die Sie alle auf einmal bearbeiten möchten.

## Funktionsweise

### Backend (`/api/keywords-batch-add`)

- **Eingabe**: Array von Schlagwörtern, optional `overwrite` Flag und `batchId`
- **Verarbeitung**: Sequenzielle Verarbeitung mit 1-Sekunden-Pause zwischen API-Calls (Rate Limiting)
- **Ausgabe**: Detaillierte Ergebnisse mit Erfolg/Fehler/Skip-Statistiken

### Frontend

- **UI**: Textarea für Schlagwort-Liste (ein Schlagwort pro Zeile)
- **Optionen**: Checkbox zum Überschreiben bestehender Schlagwörter
- **Fortschritt**: Echtzeit-Fortschrittsanzeige mit Prozentanzeige
- **Ergebnisse**: Übersicht über erfolgreiche, fehlgeschlagene und übersprungene Schlagwörter

## Verwendung

1. **Schlagwörter-Tab öffnen**: Wechseln Sie zum "Schlagwörter" Tab
2. **Batch-Sektion finden**: Die Batch-Generierung ist nur bei localhost sichtbar
3. **Schlagwörter eingeben**: Geben Sie Ihre Schlagwörter ein (ein Schlagwort pro Zeile)
4. **Optionen wählen**: Aktivieren Sie "Bestehende Schlagwörter überschreiben" falls gewünscht
5. **Batch starten**: Klicken Sie auf "Batch-Generierung starten"
6. **Fortschritt verfolgen**: Beobachten Sie die Fortschrittsanzeige
7. **Ergebnisse prüfen**: Nach Abschluss werden detaillierte Statistiken angezeigt

## Beispiel-Eingabe

```
Astralleib
Ätherleib
Bewusstsein
Karma
Reinkarnation
Imagination
Inspiration
Intuition
```

## Limitierungen

- **Maximal 50 Schlagwörter** pro Batch (um Server-Überlastung zu vermeiden)
- **Rate Limiting**: 1 Sekunde Pause zwischen KI-API-Calls
- **Nur bei localhost**: Batch-Funktionalität ist nur bei lokaler Entwicklung sichtbar

## Fehlerbehandlung

- **Leere Schlagwörter**: Werden automatisch übersprungen
- **Duplikate**: Werden übersprungen (außer bei aktiviertem "Überschreiben")
- **Keine Textstellen**: Schlagwörter ohne Treffer werden als fehlgeschlagen markiert
- **Netzwerkfehler**: Werden mit detaillierter Fehlermeldung angezeigt
- **Abbruch**: Batch kann jederzeit mit "Abbrechen" gestoppt werden

## Technische Details

### Backend-Implementierung

```javascript
// API-Endpunkt: /api/keywords-batch-add
app.post('/api/keywords-batch-add', async (req, res) => {
  // Sequenzielle Verarbeitung mit Rate Limiting
  // Detaillierte Fehlerbehandlung pro Schlagwort
  // Umfassende Ergebnisstatistiken
});
```

### Frontend-Implementierung

```javascript
// Batch-Verarbeitung mit AbortController
async function addBatchKeywords() {
  // Validierung der Eingabe
  // Fortschrittsanzeige
  // Fehlerbehandlung mit Abbruch-Möglichkeit
}
```

## Vorteile

1. **Effizienz**: Mehrere Schlagwörter gleichzeitig verarbeiten
2. **Übersicht**: Klare Fortschrittsanzeige und Ergebnisstatistiken
3. **Flexibilität**: Option zum Überschreiben bestehender Schlagwörter
4. **Robustheit**: Umfassende Fehlerbehandlung und Abbruch-Möglichkeit
5. **Rate Limiting**: Respektiert API-Limits der KI-Services

## Sicherheit

- Nur bei localhost verfügbar (Entwicklungsmodus)
- Validierung aller Eingaben
- Rate Limiting verhindert API-Missbrauch
- Detaillierte Logging für Debugging
