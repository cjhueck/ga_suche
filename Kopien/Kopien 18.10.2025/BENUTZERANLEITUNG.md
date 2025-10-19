# GA-Suche – Anleitung

**Rudolf Steiner Gesamtausgabe – Volltext- und thematische Suche**

---

## Übersicht

Die GA-Suche ermöglicht die Suche und inhaltliche Orientierung in der Rudolf Steiner Gesamtausgabe mit vier Hauptfunktionen:
- **Texte**: Übersicht über die Texte und Vorträge aus den aufgelisteten GA-Bänden
- **Suche**: Stichwortsuche in Texten und Vorträgen (mit Bewertung der Relevanz gefundener Stellen)
- **Themen**: KI-gestützte thematische Suche
- **Index**: Liste von wichtigen Schlagworten

Suche, Themen und Schlagworte sind mit den entsprechenden Quellen verlinkt.
---

## Tab "Texte" – GA-Übersichten

### Grundfunktion

- Chronologische Übersicht aller hier verfügbaren GA-Bände mit Titel, Jahresangabe und Vortragsliste

### Benutzung

**Filteroptionen:**
- **Jahre-Filter**: Auswahl einzelner Jahre oder Jahresbereiche (z.B. "1910", "1910-1915")
- **GA-Bände-Filter**: Auswahl spezifischer GA-Nummern (z.B. "GA052", "GA088")

**Navigation:**
1. Klicken Sie auf einen **Band-Titel** → Zeigt Liste aller Vorträge des Bandes
2. Klicken Sie auf einen **Vortragstitel** → Öffnet vollständigen Vortragstext im Viewer

**Besonderheiten:**
- Jahresangaben werden automatisch aus Vortragsdaten extrahiert
- KI-generierte Zusammenfassungen werden automatisch angezeigt (wenn verfügbar)

---

## 2. Tab "SUCHE" – Intelligente Stichwortsuche

### 2.1 Einzelwort-Suche

**Eingabe:**
- Geben Sie ein Suchwort in das erste Eingabefeld ein
- Beispiel: `anthroposophie`

**Funktionsweise:**
- Findet alle Vorkommen des Begriffs in allen Vorträgen
- Auch Teilwörter werden gefunden (z.B. "Anthroposophiebegriff")

### 2.2 Zwei-Wort-Suche

**Eingabe:**
- Suchwort 1: `karma`
- Suchwort 2: `seele`

**Funktionsweise:**
- Findet Textstellen, wo **beide Wörter innerhalb von max. 2 Absätzen** vorkommen
- Intelligente Relevanzbewertung basierend auf:
  - Häufigkeit beider Wörter
  - Nähe der Wörter zueinander (≤50 Zeichen Abstand = Bonus)
  - Exakte Phrase "karma seele" = Extra-Bonus
  - Thematischer Kontext für beide Begriffe

**Beispiele:**
| Konstellation | Wird gefunden? |
|---------------|----------------|
| Beide im gleichen Absatz | Ja |
| Wort 1 in Absatz 5, Wort 2 in Absatz 6 | Ja (1 Absatz dazwischen) |
| Wort 1 in Absatz 5, Wort 2 in Absatz 7 | Ja (2 Absätze dazwischen) |
| Wort 1 in Absatz 5, Wort 2 in Absatz 9 | Nein (>2 Absätze) |

### 2.3 Phrasensuche (Exakte Suche)

**Eingabe mit Anführungszeichen:**
- `"geistige welt"` – sucht exakt diese Phrase
- `"astralleib"` – sucht nur das exakte Wort (nicht "Astralleibtrennung")

**Funktionsweise:**
- **MIT Anführungszeichen**: Nur exakte Treffer mit Wortgrenzen
  - `"anthroposophie"` findet: "Anthroposophie"
  - findet NICHT: "Anthroposophiebegriff"
  
- **OHNE Anführungszeichen**: Flexible Suche
  - `anthroposophie` findet: "Anthroposophie", "Anthroposophiebegriff", etc.

**Kombination:**
- Suchwort 1: `"karma"` (exakt)
- Suchwort 2: `bewusstsein` (flexibel)
- Findet: Exaktes "Karma" + jede Form von "Bewusstsein"/"Bewusstseinsentwicklung"

### 2.4 Filteroptionen

**Jahre-Filter:**
- Schränkt Suche auf bestimmte Jahre ein
- Beispiel: "1910" oder "1910-1915"

**GA-Bände-Filter:**
- Schränkt Suche auf bestimmte GA-Nummern ein
- Beispiel: "GA052" oder "GA088"

**Relevanz-Filter:**
- **Alle**: Zeigt alle Treffer (Standard)
- **Hoch 🟩**: Nur hoch relevante Treffer
  - Beide Wörter häufig und nah beieinander
  - Starker thematischer Kontext
- **Mittel 🟧**: Mittlere Relevanz
  - Beide Wörter vorhanden, aber seltener oder weiter entfernt
- **Niedrig 🟨**: Niedrige Relevanz
  - Beide Wörter vorhanden, aber selten oder weit auseinander

> **Hinweis**: Der Relevanzfilter funktioniert **vor** der Suche. Wenn Sie "Hoch" auswählen, werden nur hochrelevante Treffer gesucht und angezeigt.

### 2.5 Ergebnisanzeige

**Timeline-Ansicht:**
- Chronologische Liste nach Jahren sortiert
- Jahr in linker Spalte, Vorträge in rechter Spalte
- **Relevanz-Markierung**: 🟩 Hoch | 🟧 Mittel | 🟨 Niedrig

**Ansichts-Modi:**
1. **Vollansicht** (Standard):
   - Vortragstitel + bis zu 5 Text-Snippets pro Vortrag
   - Suchbegriffe sind im Snippet markiert
   - Klick auf Snippet → Öffnet Vortrag an genau dieser Stelle

2. **Nur Titel** (umschalten mit Button):
   - Zeigt nur Vortragstitel
   - Für bessere Übersicht bei vielen Treffern

**Trefferanzeige:**
- Oberhalb der Ergebnisse: Anzahl der gefundenen Absätze und Vorträge
- Beispiel: "234 Absätze in 45 Vorträgen gefunden"

---

## 3. Tab "THEMATISCH" – KI-gestützte Suche

### 3.1 Grundfunktion

Nutzt Claude AI (Anthropic) für semantische, thematische Suchen, die über einfache Stichwortsuchen hinausgehen.

### 3.2 Eingabe

**Fragestellung eingeben:**
- Formulieren Sie eine natürlichsprachliche Frage
- Beispiele:
  - "Wie beschreibt Steiner die Entwicklung des Bewusstseins?"
  - "Was sagt Steiner über die Beziehung zwischen Karma und Reinkarnation?"
  - "Wie unterscheidet sich der Ätherleib vom Astralleib?"

**Wichtige Begriffe markieren:**
- Setzen Sie zentrale Begriffe in Anführungszeichen für bessere Ergebnisse
- Beispiel: `Was sagt Steiner über "Karma" und "Freiheit"?`

### 3.3 Such-Optionen

**Suchtiefe:**
- **Allgemein**: Schnelle Übersicht (Standard)
- **Detailliert**: Tiefergehende Analyse mit mehr Kontext
- **Umfassend**: Sehr ausführliche Analyse (dauert länger)

**Maximale Treffer:**
- Dropdown: 10, 20, 50, 100, 200 Treffer
- Standard: 20
- Bei hoher Anzahl kann die Verarbeitung länger dauern

**Filter:**
- **Jahre-Filter**: Beschränkung auf Zeitraum
- **GA-Bände-Filter**: Beschränkung auf bestimmte Bände

### 3.4 Ergebnisanzeige

**KI-Analyse:**
- Zusammenfassende Antwort auf Ihre Frage
- Basiert auf gefundenen Textstellen
- Wird oben in farbiger Box angezeigt

**Gefundene Textstellen:**
- Chronologisch nach Datum sortiert
- Relevanteste Absätze werden angezeigt
- Klick auf Textstelle → Öffnet vollständigen Vortrag

**"Zuletzt gesucht":**
- Ihre letzten 5 thematischen Suchen werden gespeichert
- Klick auf Eintrag → Führt Suche erneut aus

### 3.5 Abbrechen

- Button "Abbrechen" erscheint während der Suche
- Stoppt laufende KI-Analyse sofort

---

## 4. Vortragsanzeige (Viewer)

### 4.1 Öffnen eines Vortrags

**Aus Tab "Texte":**
- Klick auf Vortragstitel → Öffnet Volltext

**Aus Tab "Suche":**
- Klick auf Snippet → Öffnet Vortrag und scrollt zur Fundstelle
- Suchbegriffe bleiben im Text markiert

**Aus Tab "Thematisch":**
- Klick auf Textstelle → Öffnet Vortrag am entsprechenden Absatz

### 4.2 Funktionen im Viewer

**Kopfzeile:**
- Vortragstitel
- GA-Nummer, Ort, Datum
- Link zu steiner-online.de (externes Popup)

**Text:**
- Vollständiger Vortragstext
- Formatierung: Überschriften, Absätze, Zitate
- Suchbegriffe sind markiert (gelb hinterlegt)

**Navigation:**
- **Inhaltsverzeichnis** (rechts):
  - Zeigt alle Überschriften des Vortrags
  - Klick → Springt zur entsprechenden Stelle
  - Wird automatisch aufgebaut
  - Bei langen Vorträgen scrollbar

**Querverweise:**
- GA-Referenzen im Text sind verlinkt (z.B. "GA123/05")
- Klick → Öffnet referenzierten Vortrag

### 4.3 Zusammenfassung-Panel

**Anzeigen:**
- Button "Zusammenfassung" (oberhalb des Viewers)
- Öffnet seitliches Panel mit KI-generierter Zusammenfassung

**Inhalt:**
- Strukturierte Zusammenfassung des Vortrags
- Hauptthemen und Gliederung
- Kann parallel zum Volltext angezeigt werden

**Generieren:**
- Falls keine Zusammenfassung vorhanden:
  - Button "Zusammenfassung generieren"
  - Nutzt Claude AI (dauert ca. 10-30 Sekunden)
  - Wird automatisch für zukünftige Nutzung gespeichert

**Schließen:**
- Button "Schließen" im Summary-Panel
- Oder Klick außerhalb des Panels

### 4.4 Weitere Funktionen

**Timeline-Viewer:**
- Bei Suche mit Stichwörtern wird eine alternative Ansicht aktiviert
- Zeigt Vorträge in chronologischer Timeline
- Mit Zusammenfassung-Panel kombinierbar

**Responsive Ansicht:**
- Layout passt sich automatisch an Bildschirmgröße an
- Inhaltsverzeichnis wird bei kleinen Bildschirmen ausgeblendet

---

## 5. Erweiterte Funktionen

### 5.1 Such-Historie

**Automatische Speicherung:**
- Suchbegriffe werden automatisch gespeichert
- Dropdown zeigt letzte Suchen beim Klick ins Eingabefeld

**Wiederverwendung:**
- Klick auf historischen Eintrag → Füllt Suchfeld aus

### 5.2 Keyboard-Shortcuts

**Suche:**
- `Enter` im Suchfeld → Startet Suche (bei Einzelwort-Suche)
- Im Thematisch-Tab: `Ctrl+Enter` → Startet Suche

**Navigation:**
- `Esc` → Schließt geöffnete Panels/Viewer (in Planung)

---

## 6. Technische Hinweise

### 6.1 Relevanz-Berechnung

**Faktoren für hohe Relevanz:**
1. **Häufigkeit**: Wie oft kommt der Begriff im Vortrag vor?
2. **Kompaktheit**: Kommen mehrere Vorkommen in einem kleinen Textbereich vor?
3. **Thematischer Kontext**: Werden typische Begleitbegriffe verwendet?
4. **Nähe** (bei 2 Wörtern): Wie nah stehen die Begriffe beieinander?
5. **Phrase-Bonus**: Kommt die exakte Phrase vor?

**Sliding Window-Analyse:**
- System analysiert Text in 1000-Wörter-Fenstern
- Findet Bereiche mit höchster Begriffsdichte
- Normalisiert auf Textlänge

**Kontext-Index:**
- Automatische Analyse typischer Umgebungswörter
- Wird beim ersten Suchen eines Begriffs erstellt
- Aktualisiert sich automatisch bei Datenbank-Wachstum (>5%)

### 6.2 Performance-Tipps

**Bei vielen Treffern:**
- Nutzen Sie Relevanzfilter "Hoch" für präzisere Ergebnisse
- Schränken Sie mit Jahren- oder GA-Filter ein
- Nutzen Sie Phrasensuche für exaktere Treffer

**Bei thematischen Suchen:**
- Wählen Sie "Allgemein" für schnelle erste Einschätzung
- "Detailliert" oder "Umfassend" nur bei gezielten Fragen
- Begrenzen Sie maximale Treffer auf 20-50

**Bei langsamer Verbindung:**
- Zusammenfassungen werden im Hintergrund geladen
- Viewer ist sofort nutzbar, auch wenn Zusammenfassung noch lädt
- KI-Analysen können abgebrochen werden

### 6.3 Datenschutz & Server

**Backend:**
- Node.js Backend läuft lokal oder auf eigenem Server
- Konfigurierbar via `API_BASE` in index.html

**KI-Integration:**
- Claude API (Anthropic) für Zusammenfassungen und thematische Suche
- Benötigt API-Key (in backend.js konfigurieren)
- Nur bei expliziten KI-Funktionen aktiviert

**Daten:**
- Alle Vorträge werden lokal gespeichert (JSON-Dateien)
- Suchindex wird automatisch erstellt
- Zusammenfassungen werden in Datenbank gecacht

---

## 7. Häufige Fragen (FAQ)

**Q: Warum finde ich bei Zwei-Wort-Suche weniger Treffer?**  
A: Das System sucht nur Textstellen, wo beide Wörter **maximal 2 Absätze** auseinander liegen. Das stellt sicher, dass die Begriffe tatsächlich im gleichen thematischen Kontext stehen.

**Q: Was bedeuten die farbigen Punkte (🟩🟧🟨)?**  
A: Das sind Relevanz-Markierungen:
- 🟩 Hoch: Sehr relevante Treffer
- 🟧 Mittel: Moderat relevant
- 🟨 Niedrig: Weniger relevant

**Q: Warum sehe ich bei Phrasensuche keine Treffer mehr?**  
A: Phrasensuche mit Anführungszeichen sucht nur **exakte** Wortgrenzen. "anthroposophie" findet nicht "Anthroposophiebegriff". Lassen Sie Anführungszeichen weg für flexible Suche.

**Q: Wie lange dauert eine Zusammenfassung?**  
A: Erste Generierung: ca. 10-30 Sekunden. Danach wird sie gecacht und lädt sofort.

**Q: Kann ich mehrere Begriffe thematisch suchen?**  
A: Ja! Formulieren Sie einfach eine Frage mit mehreren Begriffen, z.B. "Wie hängen Karma, Reinkarnation und Freiheit zusammen?"

**Q: Was passiert, wenn die Datenbank wächst?**  
A: Kontext-Indices werden automatisch neu generiert, wenn die Datenbank um >5% wächst. Das passiert im Hintergrund beim ersten Suchen eines Begriffs.

**Q: Werden meine Suchen gespeichert?**  
A: Suchbegriffe werden lokal im Browser gespeichert (localStorage) für Such-Historie. Keine Server-seitige Speicherung.

**Q: Kann ich Ergebnisse exportieren?**  
A: Aktuell nicht direkt. Sie können aber Textstellen kopieren (Rechtsklick → Kopieren) oder den Vortrag über steiner-online.de Link abrufen.

---

## 8. Tastenkombinationen & Shortcuts

| Aktion | Tastenkombination |
|--------|-------------------|
| Suche starten (Stichwort) | `Enter` in Suchfeld |
| Suche starten (Thematisch) | `Ctrl + Enter` in Textfeld |
| Feld auswählen | `Tab` / `Shift + Tab` |
| Autofokus auf Eingabefeld | Automatisch bei Tab-Wechsel |
| Suchfeld leeren | Text markieren + `Entf` oder `Backspace` |

---

## 9. Fehlerbehebung

**Problem: Suche liefert keine Ergebnisse**
- ✓ Prüfen Sie Rechtschreibung
- ✓ Versuchen Sie flexible Suche (ohne Anführungszeichen)
- ✓ Entfernen Sie Filter (Jahre, GA-Bände, Relevanz)
- ✓ Bei Zwei-Wort-Suche: Möglicherweise stehen Begriffe zu weit auseinander (>2 Absätze)

**Problem: Zusammenfassung lädt nicht**
- ✓ Prüfen Sie Internetverbindung
- ✓ Backend-Server muss laufen
- ✓ Claude API-Key muss konfiguriert sein
- ✓ Warten Sie ca. 30 Sekunden, Generation kann dauern

**Problem: Seite lädt langsam**
- ✓ Große Datenmengen können beim ersten Laden Zeit brauchen
- ✓ Browser-Cache wird nach erstem Laden verwendet
- ✓ Reduzieren Sie Anzahl gleichzeitiger Suchen

**Problem: Relevanz-Filter zeigt keine Unterschiede**
- ✓ Bei sehr allgemeinen Begriffen können fast alle Treffer "niedrig" sein
- ✓ Bei sehr spezifischen Begriffen können fast alle Treffer "hoch" sein
- ✓ System passt sich an Trefferverteilung an

**Problem: Text wird nicht markiert**
- ✓ Markierung funktioniert nur bei Suche über Tab "Suche"
- ✓ Bei direktem Öffnen aus "Texte" keine Markierung
- ✓ Bei Phrasensuche wird nur exakte Phrase markiert

---

## 10. Version & Support

**Version**: 2.0 (mit Zwei-Wort-Relevanz und Phrasensuche)

**Entwickelt für**:
- Rudolf Steiner Gesamtausgabe (GA)
- Volltext-Recherche und thematische Analyse
- Wissenschaftliche und private Nutzung

**Technologie-Stack**:
- Frontend: HTML5, CSS3, JavaScript (ES6+)
- Backend: Node.js, Express
- KI: Claude API (Anthropic)
- Datenbank: JSON-basiert

---

## 11. Best Practices

### Für präzise Suchen:
1. Starten Sie mit Einzelwort-Suche
2. Verfeinern Sie mit Zwei-Wort-Suche
3. Nutzen Sie Phrasensuche für exakte Zitate
4. Aktivieren Sie Relevanzfilter "Hoch" bei vielen Treffern

### Für thematische Recherche:
1. Formulieren Sie präzise Fragen
2. Markieren Sie Kernbegriffe mit Anführungszeichen
3. Starten Sie mit "Allgemein", vertiefen Sie bei Bedarf
4. Nutzen Sie Filter für zeitliche/thematische Eingrenzung

### Für effizientes Arbeiten:
1. Nutzen Sie Such-Historie für wiederkehrende Begriffe
2. Speichern Sie relevante Vorträge extern (via steiner-online.de)
3. Kombinieren Sie Tabs: "Texte" für Überblick, "Suche" für Details
4. Nutzen Sie Zusammenfassungen für schnellen Einstieg



