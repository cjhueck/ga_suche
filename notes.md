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
- Main-Container wird NACH updateHeaderPosition() ERZWUNGEN (20ms, 50ms, 100ms)
- updateHeaderPosition() kann Main-Container nicht mehr überschreiben

✅ Automatische Synchronisation (ROBUSTE LÖSUNG):
- Neue Funktion syncMainContainerWithPanel() läuft alle 100ms
- Liest AKTUELLE Panel-Breite aus dem DOM (offsetWidth)
- Setzt Main-Container marginRight EXAKT auf Panel-Breite
- Positioniert Resize-Handle EXAKT an Panel-Grenze (Breite - 10px)
- Aktualisiert nur bei Breitenänderung (kein unnötiges DOM-Update)
- GARANTIERT keinen Gap zwischen Panel und Main-Viewer
- Funktioniert automatisch für MB (400px) und TOC (280px)

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

✅ MB-Öffnung von Original-Ansicht:
- showMembersContent() setzt explizit display: block, opacity: 1, visibility: visible
- showMembersLoginPanel() setzt explizit display: block, opacity: 1, visibility: visible
- Resize-Handle wird auch explizit auf display: block gesetzt
- Nachkorrektur nach 100ms stellt sicher, dass Panel und Content sichtbar bleiben
- Funktioniert jetzt auch beim Klick auf MB-Icon von Original-Ansicht aus

✅ MB-Icon ersetzt:
- Floating MB-Icon in members-menu.js ENTFERNT
- Stattdessen: Header-Button mit kleinem Icon (16x16) verwendet
- Button im Header ruft openMembersPanel() auf
- Nur EIN Icon statt zwei (Header + floating)
- handleOutsideClick() angepasst (kein member-icon mehr)

✅ MB-Icon Login-Verhalten (Header-Button):
- Button onclick="openMembersPanel()" im Header
- openMembersPanel() prüft Login-Status mit initSupabase()
- Nicht eingeloggt: showMembersLoginPanel() → Login-Form im rechten Side-Panel
- Eingeloggt: showMembersContent() → Mitgliederbereich im rechten Side-Panel
- Button hat kompakte Größe (padding: 4px 8px) mit 16x16 Icon

✅ Emojis von Buttons entfernt (members-panel.js):
- Tab-Buttons: 🔖 Bookmarks → Bookmarks
- Tab-Buttons: 💬 Zitate → Zitate
- Tab-Buttons: 📝 Notizen → Notizen
- Tab-Buttons: 🕸️ Graph → Graph
- Tab-Buttons: 💭 Chat → Chat
- Empty-States: Emojis entfernt (nur Text bleibt)
- Graph-Stats: Emoji-Icons entfernt (nur Zahlen/Text)

✅ Header-Padding korrigiert (app.html):
- padding-right: 70px entfernt (war für altes floating Mitglieder-Icon)
- Jetzt einheitlich padding: 1rem auf allen Seiten
- MB-Button im Header ist jetzt rechtsbündig positioniert

✅ "Zur Stelle" Link optimiert (members-panel.js):
- Bookmarks: Vortragsnummer (ga_number) ist jetzt direkt klickbar
- Zitate: GA-Referenz (ga_reference) ist jetzt direkt klickbar
- Separater "🔗 Zur Stelle" Link unten entfernt
- Link-Farbe: var(--link-color), keine Unterstreichung
- Falls kein paragraph_id vorhanden: Nummer bleibt nicht-klickbar

✅ Member-Item Design vereinfacht (members-panel.css):
- Umrandete Boxen entfernt (border + border-radius)
- Background auf transparent gesetzt
- Stattdessen: dezente border-bottom als Trennlinie zwischen Items
- Padding angepasst: 0.75rem 0 (nur oben/unten, nicht mehr links/rechts)
- Dark Mode ebenfalls angepasst

✅ Zitat-Anzeige und Button-Position angepasst (members-panel.css):
- Farbiger Streifen links vom Zitat entfernt (border-left bei .member-item-quote)
- Mülleimer-Button von oben rechts nach unten rechts verschoben (top → bottom)
- Gilt für Bookmarks und Zitate
- Zeilenabstand (line-height: 1.4) einheitlich für beide

