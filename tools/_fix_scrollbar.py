import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Doppelte Scrollbar: pdf-viewer-panel und pdf-canvas-container oder #main
# Loesung: Nur pdf-canvas-container soll scrollen. Pruefe ob #main auch scrollt wenn Panel offen.
# 
# Versuch: overflow-y: hidden auf #pdf-viewer-panel, overflow-y: auto NUR auf .pdf-canvas-container
# Das Panel hat bereits overflow:hidden. 
#
# Evtl. Ursache: #main scrollt UND pdf-canvas-container scrollt - beide rechts sichtbar.
# Fix: Wenn #pdf-viewer-panel.visible, dann overflow-y: hidden auf #main um Doppel-Scrollbar zu vermeiden?
# Nein - dann kann man main nicht scrollen.
#
# Alternative: pdf-viewer-panel komplett ohne eigene Scrollbalken - alles ueber einen Container.
# Der pdf-canvas-container hat overflow:auto. Vielleicht gibt es noch ein anderes Element mit overflow.
#
# Einfachster Fix: overflow-x: hidden auf pdf-canvas-container um horizontale Scrollbar zu vermeiden,
# und sicherstellen dass nur EIN overflow-auto da ist.
#
# Oder: body/html scrollt und pdf-canvas-container scrollt? 
# pdf-viewer-panel ist position:fixed, also nicht im normalen Flow. 
#
# Ich versuche: .pdf-canvas-container overflow-x: hidden (nur vertikal scrollen)
# und overflow-y: auto. Vielleicht hatte overflow:auto beide Richtungen und irgendwas erzeugt 2 Balken.

old = """    .pdf-canvas-container {
      flex: 1;
      min-height: 0;
      overflow: auto;
      display: flex;"""

new = """    .pdf-canvas-container {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      display: flex;"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: pdf-canvas-container overflow angepasst')
else:
    print('Nicht gefunden')
