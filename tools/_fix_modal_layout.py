import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Modal: flex column, feste Hoehe, nur container scrollt
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
      overflow: hidden;
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
      flex-direction: column;
      align-items: center;
      cursor: zoom-out;
      overflow: hidden;
      height: 100vh;
      width: 100vw;
    }"""

# justify-content entfernt, da wir column nutzen und container flex:1 bekommt
if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: Modal Layout')
else:
    print('Nicht gefunden')
