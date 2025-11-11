**Die GA-Suche ermöglicht inhaltliche Orientierung in der Rudolf Steiner Gesamtausgabe mit vier Hauptfunktionen**

- **GA** - Auswahl einzelner GA-Bände, Anzeige der darin enthaltenen Vorträge mit Kurzusammenfassungen, sowie eine chronologische Liste der Vorträge Rudolf Steiners
- **Suche**: Stichwortsuche in Texten und Vorträgen (mit Bewertung der Relevanz gefundener Stellen) 
- **Suche erweitert**: bis zu sieben Stichworte gleichzeitig suchen
- **Texte**: Übersicht über die Texte und Vorträge aus den aufgelisteten GA-Bänden, mit Zusammenfassungen, Schlagwörtern und Zwischenüberschriften
- **Themen**: Thematische Suche (KI-gestützt)
- **Timeline**: Zeitlicher Verlauf einzelner Such- und Schlagwörter in der GA
- **Index**: Liste wichtiger Begriffe

Suche, Themen, Timeline und Schlagwörter sind mit den entsprechenden Quellen verlinkt.
Die Fenster können über die **drei blauen Punkte** geöffnet und geschlossen werden.
Das rechte Seitenfenster zeigt Zwischenüberschriften zu den angezeigten Vorträgen; oben rechts kann man zwischen zwei Überschriftenniveaus wechseln. 

---

#### Tab "Suche"

- Findet alle Vorkommen des eingegebenen Suchworts in allen Vorträgen
- Auch Teilwörter werden gefunden
- Für exakte Ergebnisse Suchwort oder -Phrase in Anführungszeichen setzen 
- Bei Eingabe von zwei Suchwörtern werden Textstellen gefunden, bei denen beide Wörter innerhalb von max. 2 Absätzen vorkommen

**Relevanz-Filter**

- **Alle**: Zeigt alle Treffer (Standard)
- **Hoch 🟩**: Suchwort/e kommt mehrfach vor, häufig und nah beieinander, starker thematischer Kontext
- **Mittel 🟧**: Suchwort/e kommt mehrfach vor, aber seltener oder weiter entfernt
- **Niedrig 🟨**: Suchwort/e kommt einfach oder mehrfach, aber dann selten oder weit auseinander vor

Der Relevanzfilter funktioniert vor der Suche. Bei Auswahl von "hoch" werden nur hochrelevante Treffer angezeigt.

**Ergebnisanzeige**

- Chronologische Liste der Text- oder Vortragstitel und Textausschnitte mit Relevanz-Markierung
- Klick auf ein Ergebnis öffnet die Textquelle an der entsprechenden Stelle

---

#### Tab "Texte"

- Chronologische Übersicht aller hier verfügbaren GA-Bände mit Titel, Jahresangabe und Vortragsliste
- Klicken auf einen **Band-Titel** öffnet die Liste aller Vorträge des Bandes
- Klicken auf einen **Vortragstitel** öffnet den vollständigen Vortragstext
- Zusammenfassungen und Zwischenüberschriften wurden von KI generiert

---

#### Tab "Themen"

KI-gestützte thematische Suchen mit Claude AI (Anthropic)

- Fragestellung eingeben
- Setzen Sie zentrale Begriffe in Anführungszeichen für bessere Ergebnisse

**Ergebnisanzeige**

- Zusammenfassende Antwort auf die eingegebene Frage
- Basierend auf gefundenen Textstellen

---

#### Tab "Timeline"

Themenspezifische Darstellung.

- Thema auswählen, zusätzlich optional Schlagwort auswählen
- Schlagwörter können auch ohne vorherige Themenwahl ausgewählt werden 

---

#### Tab "Index"

- Wachsende Liste wichtiger Schlagwörter, mit KI-Unterstützung erstellt

---

#### Relevanz-Berechnung

**Faktoren für hohe Relevanz**
1. **Häufigkeit**: Wie oft kommt der Begriff im Vortrag vor?
2. **Kompaktheit**: Kommen mehrere Vorkommen in einem kleinen Textbereich vor?
3. **Thematischer Kontext**: Werden typische Begleitbegriffe verwendet?
4. **Nähe** (bei 2 Wörtern): Wie nah stehen die Begriffe beieinander?
5. **Phrase-Bonus**: Kommt die exakte Phrase vor?

**Sliding Window-Analyse**
- System analysiert Text in 1000-Wörter-Fenstern
- Findet Bereiche mit höchster Begriffsdichte
- Normalisiert auf Textlänge

---

#### Datenschutz & Server

**Backend**
- Die Datenbank läuft auf eigenem Server

**KI-Integration**
- Claude API (Anthropic) liefert Zusammenfassungen und Ergebnisse von thematischer Suche

**Daten**
- Alle Vorträge sind lokal gespeichert
- Suchindex wird automatisch erstellt

---

#### Version & Technik

**Version** 2.1 

**Entwickelt für**
- Rudolf Steiner Gesamtausgabe (GA)
- Volltext-Recherche und thematische Analyse
- Wissenschaftliche und private Nutzung

**Technologie**
- Frontend: HTML5, CSS3, JavaScript (ES6+)
- Backend: Node.js, Express
- KI: Claude API (Anthropic)
- Datenbank: JSON-basiert






