GA124 FRAGENBEANTWORTUNG zum Vortrag vom 18. Dezember 1910

Abb. 123-01.webp nicht ok

Zusammenfassung für morgen:
Problem: Beim ersten Öffnen eines Buches ist der RH 3–5px zu weit rechts. Nach Wechsel zu einem Vortrag und zurück funktioniert es.
Bereits versucht:
Verschiedene Verzögerungen und requestAnimationFrame
ResizeObserver
Polling-Mechanismus
Flag-Mechanismus gegen Überschreibung
Verwendung von panelWidth statt offsetWidth (wie in toggleViewerH4())
Mögliche nächste Schritte:
CSS prüfen: Gibt es Styles, die die Positionierung beeinflussen?
Unterschiede beim ersten Öffnen vs. Toggle analysieren: Was passiert genau beim Toggle, das beim ersten Öffnen fehlt?
syncMainContainerWithPanel() genauer untersuchen: Verwendet es offsetWidth und überschreibt die Positionierung?
Bis morgen.


Das ResizeHandle (RH) des rechten SidePanels (rSP) liegt beim Öffnen eines Vortrags direkt auf der Grenzlinie zwischen Hauptfenster (MV) und rSP - das ist korrekt. 
Bei Öffnen eines Buches liegt das RH einige Pixel rechts neben der Grenzlinie. Erst wenn ich einen Vortrag öffne und DANN wieder zu einem Buch zurückspringe, liegt das RH an der korrekten Position. 
Finde die exakte Ursache, bevor du etwas änderst.  