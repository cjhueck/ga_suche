import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# #pdf-popup-modal: overflow:hidden hinzufuegen - aeusserer Scrollbar soll weg
old = """    #pdf-popup-modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.85);
      z-index: 10000;
      justify-content: center;
      align-items: center;
      cursor: zoom-out;
    }"""

new = """    #pdf-popup-modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.85);
      z-index: 10000;
      justify-content: center;
      align-items: center;
      cursor: zoom-out;
      overflow: hidden;
    }"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: #pdf-popup-modal overflow:hidden')
else:
    print('Nicht gefunden - pruefe Format')
    if '#pdf-popup-modal' in c:
        idx = c.find('#pdf-popup-modal')
        print(repr(c[idx:idx+350]))
