GA124 FRAGENBEANTWORTUNG zum Vortrag vom 18. Dezember 1910

Abb. 123-01.webp nicht ok

✅ Mitgliederbereich (MB) Verhalten implementiert:
- Bei Klick auf Zitat/Bookmark Links: MB bleibt geöffnet ✓
- Bei Klick auf "Übersicht": MB wechselt zu TOC (Panel bleibt offen) ✓✓
  → Wenn Original angezeigt wird: wechselt zur Übersicht und zeigt TOC
  → Wenn Übersicht bereits angezeigt: baut TOC neu
  → Main-Viewer passt sich automatisch an TOC-Breite an
- Bei Klick auf "Original": MB wird geschlossen (Panel komplett geschlossen) ✓
- Bei Klick auf MB Icon: MB wird wieder eingeblendet ✓
- MB Icon von index.html entfernt (nur auf app.html sichtbar) ✓

✅ Layout-Anpassungen:
- Main-Viewer-Fenster passt sich automatisch an die Breite des rechten Side-Panels an
- Neue Hilfsfunktion setSummaryPanelWidth() in app.html erstellt
- Bug in updateHeaderPosition() behoben (marginRight '0px' statt 'px')
- switchFromMembersPanelToTOC() passt Main-Container SOFORT an TOC-Breite an (280px)
- showMembersContent() passt Main-Container an MB-Breite an (400px)
- toggleViewerH4() ruft updateHeaderPosition() mit Timeouts auf (20ms + 100ms)
- Mehrfache Layout-Updates sichern korrekte Anpassung des Main-Viewers

✅ Resize-Handle Position:
- Resize-Handle wird EXAKT an Panel-Grenze positioniert
- switchFromMembersPanelToTOC(): Handle bei (280px - 10px) = 270px
- showMembersContent(): Handle bei (400px - 10px) = 390px
- Offset von 10px für beide Panels (TOC und MB)
- Kein Gap mehr zwischen Panel und Resize-Handle
- NACHKORREKTUR in toggleViewerH4() nach updateHeaderPosition() (20ms + 100ms)
- NACHKORREKTUR in showSummaryView() nach updateHeaderPosition() (50ms)
- Handle-Position wird nach jedem updateHeaderPosition() neu gesetzt

✅ Cleanup:
- Test-Button (🐛) für Context Menu entfernt
- testContextMenu() Debug-Funktion entfernt
- Debug-Script Block entfernt

