GA124 FRAGENBEANTWORTUNG zum Vortrag vom 18. Dezember 1910


Wieso ist der "Ätherleib" des Mannes "weiblich" und der Ätherleib der Frau "männlich"?


GA001 4 Bände
GA014 4 Dramen
GA019 Aufsätze (zur Zeit des Krieges)
GA024 Aufsätze (Dreigliederung)
GA026 Aufsätze (Leitsätze)
GA029 Aufsätze (Theatherkritiken)
GA030 Aufsätze
GA031 Aufsätze (Zeitgeschichte)
GA032 Aufsätze
GA033 Aufsätze (Biographien)
GA037 Aufsätze (AG)
GA041a Buch 
GA041b Aufsätze (Übertragungen)
GA042 Aufsätze (Bühnenbearbeitungen)
GA043 Aufsätze (Bühnenbearbeitungen)
GA044 Aufsätue (Entwürfe)
GA045 Bücher
GA046 Aufsätze (Fragmente)



GA316 nochmal exportieren
hat am 24.8. ein (a) für Abendvortrag - muss bei Tafeln berücksichtigt werden

wird die rechtschreibkorrektur beim export aus md angewendet?


schreibe ein skript, mit dem die Bände GA 68c,,,, 68d..., 69c, 69d, 70b, 80a, 80b, 80c mit ocr lesbar gemacht werden

Seitenzahlen fehlen in:
- GA041b
- GA024

Seitenzahlen nicht ganz korrekt:
- GA040a

noch nicht bearbeitet: 
- GA037
- GA032
- GA031
- GA029
- GA261



Kategorie	GA-Bände	        Export-Format                    Ordner
Bücher	    GA001-GA028, GA045	steiner-books-*.json             steiner-books/
Aufsätze	GA029-GA036, GA046	steiner-full-lectures-*.json     steiner-full-lectures/
Briefe	    GA262, GA263a	    steiner-letters-*.json           steiner-letters/
Vorträge	GA051+	            steiner-full-lectures-*.json     steiner-full-lectures/


Bearbeitung der Dateien in Obsidian
- von pdf in md konvertieren (mittel Mistral KI, plugin)
- Textbearbeitung mit "Text cleanup" (Löschen von falschen Zeilenumbrüchen und Trennlinien)
- Zuordnung der Überschriften (per Hand)
- Aufspalten in einzenlne Dateien an H1 Überschriften: Split bei roman file names (plugin)
- Absätze in allen Dateien im Ordner indizieren (Rechtsklick: # Block-IDs zu diesem Ordner hinzufügen)
- fertig für Export der Dateien durch Cursor (export_master.py)

Der export_master.py ruft intern alle verschiedenen Exporter auf:
Bücher → export_books_master.py → steiner-books/*.json
Vorträge/Aufsätze → export-lectures.js → steiner-full-lectures/*.json
Bilder → integriert in export-lectures.js → steiner-images/*.json

WICHTIG: Briefe (GA262, GA263a) werden NICHT vom Export berührt!
Sie liegen separat in steiner-letters/ und werden manuell verwaltet.
Dies verhindert, dass der Vortragsexport die Briefe-Dateien überschreibt.

Erst-Popup: 
Klicken Sie Strg+Klick, um Informationen über die einzelnen Bereiche und Funktionen zu erhalten. Strg+Klick auf den Info-Button oben links zeigt weitere Tastenkombinationen.