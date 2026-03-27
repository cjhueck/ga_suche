# Anleitung: GA Rechtschreib-Editor

## Anmeldung

Beim Öffnen des Editors erscheint ein Login-Dialog. Melden Sie sich mit der E-Mail-Adresse und dem Passwort an, die Sie erhalten haben. Nach der Anmeldung werden die Server-Funktionen (Dateien laden/speichern) freigeschaltet.

---

## Aufbau der Oberfläche

Der Editor besteht aus zwei Bereichen:

- **Linkes Panel (Editor):** Hier wird der Text bearbeitet, geprüft und korrigiert.
- **Rechtes Panel (Seitenleiste):** Enthält mehrere Tabs: Fehler, Wörterbuch, Suche, PDF-Anzeige und Dateiverwaltung.

---

## Schritt 1: PDF laden

In der Kopfleiste gibt es den Button **PDF laden**. Per Klick öffnet sich ein Dropdown mit zwei Optionen:

- **Vom Rechner:** Wählen Sie eine lokale PDF-Datei von Ihrer Festplatte.
- **Vom Server:** Wählen Sie eine PDF-Datei aus Ihrem persönlichen Ordner oder aus den GA-Originalen auf dem Server.

Das PDF wird automatisch in bearbeitbaren Text (Markdown) konvertiert und im Editor-Fenster angezeigt. Die Seitenmarker (z.B. `|33|`) kennzeichnen die Seitenumbrüche des Originals.

Alternativ können Sie auch eine bereits konvertierte Markdown-Datei laden (**MD laden**).

### PDF im rechten Panel anzeigen

Im rechten Panel unter dem Tab **PDF** können Sie dasselbe oder ein anderes PDF zur Anzeige laden (ebenfalls vom Rechner oder vom Server). So können Sie den Originaltext und die Bearbeitung nebeneinander vergleichen. Seitennavigation erfolgt über die Pfeiltasten oben im PDF-Tab.

---

## Schritt 2: Prüfen (Pflicht vor Auto-Korrektur!)

Klicken Sie auf den Button **Prüfen**, um die Rechtschreibprüfung durchzuführen.

**Wichtig: Die Prüfung muss immer zuerst ausgeführt werden, bevor die Auto-Korrektur gestartet wird.** Die Auto-Korrektur arbeitet auf Grundlage der Prüfergebnisse. Ohne vorherige Prüfung kann sie keine Korrekturen vornehmen.

Nach der Prüfung werden fehlerhafte oder unbekannte Wörter im Text farbig markiert:
- **Rot (RF):** Rechtschreibfehler (Wort nicht im Wörterbuch)
- **Orange (ST):** Silbentrennung (Wort mit Trennstrich am Zeilenende)
- **Blau (SZ):** Sonderzeichen-Probleme

Im rechten Panel unter **Fehler** erscheint eine Liste aller gefundenen Probleme. Mit den Filtern (Alle / RF / ST / SZ) können Sie nach Fehlertyp filtern. Ein Klick auf einen Eintrag springt zur entsprechenden Stelle im Text.

---

## Schritt 3: Auto-Korrektur

Klicken Sie auf **Auto-Korrektur**. Es öffnet sich ein Dialog zur Seitenauswahl:

- **Alle Seiten:** Korrigiert das gesamte Dokument.
- **Einzelne Seiten:** Geben Sie kommagetrennte Seitenzahlen ein (z.B. `3, 7, 12`).
- **Seitenbereich:** Geben Sie einen Von-Bis-Bereich ein.

Die Auto-Korrektur führt automatisch folgende Schritte durch:
- Zusammenführung von silbengetrennten Wörtern am Zeilenende
- Zeichenersetzungen (z.B. typografische Anführungszeichen)
- Entfernung von Copyright-Fußzeilen
- Normalisierung von Seitenmarkern (Leerzeilen vor und nach `|N|`)
- Weitere Standardkorrekturen

Nach der Auto-Korrektur wird angezeigt, wie viele Korrekturen vorgenommen wurden.

---

## Schritt 4: Manuelle Nachbearbeitung

Nach der Auto-Korrektur bleiben in der Regel noch markierte Wörter übrig, die manuell bearbeitet werden müssen. Klicken Sie mit der **rechten Maustaste** auf ein markiertes Wort, um das Kontextmenü zu öffnen:

- **Zusammenführen:** Fügt ein silbengetrenntes Wort zusammen (bei Trennstrichen am Zeilenende).
- **Autokorrektur:** Wendet den automatischen Korrekturvorschlag auf dieses einzelne Wort an.
- **Zum Wörterbuch:** Nimmt das Wort als korrekt ins Wörterbuch auf (es wird dann bei künftigen Prüfungen nicht mehr markiert).
- **In GA suchen:** Sucht das Wort in allen GA-Bänden, um die korrekte Schreibweise zu verifizieren.
- **Ignorieren:** Überspringt dieses Wort, ohne es zu ändern.

Sie können den Text auch direkt im Editor bearbeiten (tippen, löschen, einfügen). Änderungen lassen sich mit **Strg+Z** (Rückgängig) bzw. **Strg+Y** (Wiederherstellen) steuern.

### Suche im Editor

Mit **Strg+F** öffnen Sie die Suchleiste im Editor.

---

## Schritt 5: Speichern

- **Speichern:** Speichert die Datei unter dem aktuellen Namen auf dem Server (in Ihrem persönlichen Ordner).
- **Speichern unter...:** Speichert die Datei unter einem neuen Namen.

Ungespeicherte Änderungen werden in der Kopfleiste angezeigt. Beim Schließen eines ungespeicherten Dokuments erscheint eine Warnung.

---

## Rechtes Panel: Tabs im Detail

### Fehler

Zeigt die Liste aller bei der Prüfung gefundenen Probleme. Ein Klick auf einen Fehler scrollt im Editor zur entsprechenden Stelle.

### Wörterbuch

Hier können Sie:
- Neue Wörter manuell zum Benutzerwörterbuch hinzufügen
- Das Wörterbuch durchsuchen
- Vorhandene Einträge einsehen

Wörter im Wörterbuch werden bei der Prüfung nicht als Fehler markiert.

### Suche

Sucht ein Wort in allen verfügbaren GA-Bänden. So können Sie überprüfen, wie ein Wort in anderen Bänden geschrieben wird. Tipp: Rechtsklick auf ein markiertes Wort und dann "In GA suchen" ist der schnellste Weg.

### PDF

Zeigt ein PDF zur visuellen Referenz an. Sie können das PDF vom Rechner oder vom Server laden und seitenweise navigieren. Das ist besonders hilfreich, um den konvertierten Text mit dem Original zu vergleichen.

### Dateien

Die Dateiverwaltung auf dem Server. Hier sehen Sie:
- **Ihren persönlichen Ordner** mit Ihren gespeicherten Dateien (MD- und PDF-Dateien).
- **GA PDF's (Original):** Die Original-PDFs der GA-Bände. Diese können Sie lesen und in Ihren eigenen Ordner kopieren, aber nicht verändern.

Funktionen:
- **Hochladen:** Eigene PDFs in Ihren Ordner hochladen.
- **+ Ordner:** Einen neuen Unterordner erstellen.
- **Rechtsklick** auf eine Datei: Öffnen, umbenennen, verschieben, herunterladen oder löschen.
- **Rechtsklick** auf ein GA-Original: Im PDF-Viewer öffnen, in den eigenen Ordner kopieren oder herunterladen.

---

## Seitenmarker-Modus

Der Button **Seitenmarker** aktiviert einen speziellen Modus zum schnellen Navigieren zwischen Seitenmarkern (`|1|`, `|2|`, ...). Mit **F2** oder **Alt+Q** springen Sie zum nächsten Marker.

---

## Typischer Arbeitsablauf (Zusammenfassung)

1. **PDF laden** (vom Server oder Rechner)
2. **PDF im rechten Panel laden** (zum Vergleich)
3. **Prüfen** klicken
4. **Auto-Korrektur** durchführen
5. **Verbleibende Fehler** manuell bearbeiten (Kontextmenü, direkte Textbearbeitung)
6. **Speichern**

---

## Tastenkombinationen

| Taste | Funktion |
|---|---|
| Strg+Z | Rückgängig |
| Strg+Y | Wiederherstellen |
| Strg+F | Suche im Editor öffnen |
| F2 / Alt+Q | Nächster Seitenmarker (im Seitenmarker-Modus) |
| Enter | Nächster Suchtreffer |
| Shift+Enter | Vorheriger Suchtreffer |
