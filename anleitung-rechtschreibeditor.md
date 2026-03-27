# Anleitung: GA Rechtschreib-Editor

## Anmeldung / Registrierung

Beim Öffnen des Editors erscheint ein Login-Dialog. Falls Sie noch kein Konto haben, klicken Sie auf **Registrieren** und erstellen Sie ein Konto mit Ihrer E-Mail und einem Passwort (mindestens 6 Zeichen). Nach der Registrierung erhalten Sie eine Bestätigungs-E-Mail. Bestätigen Sie Ihre E-Mail-Adresse und melden Sie sich danach an.

Nach der Anmeldung werden die Server-Funktionen (Dateien laden/speichern) freigeschaltet.

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

## Schritt 2: Prüfen -- vor Auto-Korrektur durchführen!

Klicken Sie auf den Button **Prüfen**, um die Rechtschreibprüfung durchzuführen.

**Wichtig: Die Prüfung sollte immer vor der Auto-Korrektur durchgeführt werden. Ohne vorherige Prüfung kann die Auto-Korrektur nicht optimal arbeiten.**

Nach der Prüfung werden fehlerhafte oder unbekannte Wörter im Text farbig markiert:
- **Rot (RF):** Rechtschreibfehler (Wort nicht im Wörterbuch)
- **Orange (ST):** Silbentrennung (Wort mit Trennstrich am Zeilenende)
- **Blau (SZ):** Sonderzeichen-Probleme

Die gefundenen Fehler erscheinen im Tab **Fehler** im rechten Panel (siehe unten).

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

**Nach der Auto-Korrektur können Sie erneut auf "Prüfen" klicken, um die verbleibenden fehlerhaften Wörter anzeigen zu lassen.**

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

## Rechtes Panel -- Tabs im Detail

### Tab: Fehler

Nach dem Klick auf **Prüfen** erscheint hier die Liste aller gefundenen Probleme. Jeder Eintrag zeigt das markierte Wort und seinen Fehlertyp.

- **Klick auf einen Fehler:** Der Editor scrollt automatisch zur entsprechenden Stelle im Text und hebt das Wort hervor.
- **Filter-Buttons (Alle / RF / ST / SZ):** Oben im Tab können Sie die Fehlerliste nach Typ filtern, z.B. nur Rechtschreibfehler (RF) oder nur Silbentrennungen (ST) anzeigen.
- Nach einer Auto-Korrektur können Sie erneut **Prüfen** klicken, um die verbleibenden Fehler zu aktualisieren.

### Tab: Wörterbuch

Das Benutzerwörterbuch enthält Wörter, die bei der Prüfung als korrekt gelten sollen (z.B. Eigennamen, Fachbegriffe).

- **Wort hinzufügen:** Oben im Tab ein Wort eingeben und mit **+** hinzufügen.
- **Suchen:** Das Suchfeld filtert die Wörterbuchliste.
- Wörter können auch per Rechtsklick auf ein markiertes Wort im Editor hinzugefügt werden ("Zum Wörterbuch").
- Hinzugefügte Wörter werden bei der nächsten Prüfung nicht mehr als Fehler markiert.

### Tab: Suche

Hier können Sie ein Wort in allen verfügbaren GA-Bänden suchen. Das ist hilfreich, um die korrekte Schreibweise eines Wortes zu überprüfen.

- Geben Sie ein Wort ein und klicken Sie auf **Suchen**.
- Die Ergebnisse zeigen, in welchen GA-Bänden und an welchen Stellen das Wort vorkommt.
- **Tipp:** Per Rechtsklick auf ein markiertes Wort im Editor können Sie direkt "In GA suchen" wählen.

### Tab: PDF

Zeigt ein PDF als visuelle Referenz neben dem Editor an. So können Sie den konvertierten Text mit dem Original vergleichen.

- **PDF laden:** Über die Buttons *Vom Rechner* oder *Vom Server*, oder per Drag&Drop einer PDF-Datei.
- **Navigation:** Mit den Pfeiltasten oben blättern Sie seitenweise. Sie können auch direkt eine Seitenzahl eingeben.
- Das PDF im rechten Panel ist unabhängig vom PDF, das im Editor konvertiert wurde -- Sie können verschiedene Dateien laden.

### Tab: Dateien

Die Dateiverwaltung auf dem Server. Sie können zwischen drei Bereichen wechseln, die als Ordner-Links angezeigt werden:

#### Meine Dateien

Ihr persönlicher Ordner. Hier werden Ihre bearbeiteten Markdown-Dateien und hochgeladenen PDFs gespeichert. Sie können Unterordner anlegen, um Ihre Arbeit zu organisieren.

**Rechtsklick auf eine Datei:**
- Im Editor öffnen (MD) bzw. im PDF-Viewer öffnen (PDF)
- Umbenennen, Verschieben, Herunterladen, Löschen

#### Shared (gemeinsam)

Ein gemeinsamer Ordner, auf den alle Nutzer zugreifen können. Hier können Dateien geteilt werden.

#### GA PDFs (Original)

Hier liegen die **Original-PDFs aller GA-Bände**, numerisch sortiert (GA 001 bis GA 354). Diese Dateien sind **schreibgeschützt** -- Sie können sie nicht verändern oder löschen.

**Rechtsklick auf ein GA-PDF:**
- **Im Viewer öffnen** -- Zeigt das PDF im rechten Panel an
- **In meinen Ordner kopieren** -- Kopiert das PDF in Ihren persönlichen Ordner (dort können Sie es dann bearbeiten)
- **Herunterladen** -- Lädt das PDF auf Ihren Rechner

*Tipp:* Um ein GA-PDF zu bearbeiten, können Sie es direkt über **PDF laden > Vom Server > GA PDFs** im Editor öffnen. Der konvertierte Text wird dann in Ihrem Ordner gespeichert.

#### Toolbar-Funktionen

- **Hochladen:** Eigene PDF- oder MD-Dateien in den aktuellen Ordner hochladen.
- **+ Ordner:** Einen neuen Unterordner erstellen.
- **Pfeil nach oben:** Zum übergeordneten Ordner navigieren.
- **Aktualisieren:** Dateiliste neu laden.

*Hinweis:* In GA PDFs (Original) sind die Toolbar-Buttons ausgeblendet, da dort keine Dateien hochgeladen oder erstellt werden können.

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
| Strg+S | Speichern |
| F2 / Alt+Q | Nächster Seitenmarker (im Seitenmarker-Modus) |
| Enter | Nächster Suchtreffer |
| Shift+Enter | Vorheriger Suchtreffer |
