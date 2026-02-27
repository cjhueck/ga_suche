import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# html und body beide overflow hidden wenn Popup
old = """    body:has(#pdf-popup-modal.visible) {
      overflow: hidden !important;
    }"""

new = """    html:has(#pdf-popup-modal.visible),
    body:has(#pdf-popup-modal.visible) {
      overflow: hidden !important;
      height: 100%;
    }"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: html overflow hidden hinzugefuegt')
else:
    print('Nicht gefunden - evtl. schon geaendert')
