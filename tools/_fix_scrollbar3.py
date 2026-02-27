import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Exakter Match basierend auf Ausgabe
old = """    #pdf-popup-modal.visible {
      display: flex;
    }
    
    #pdf-popup-container {"""

new = """    #pdf-popup-modal.visible {
      display: flex;
    }
    
    body:has(#pdf-popup-modal.visible) {
      overflow: hidden !important;
    }
    
    #pdf-popup-container {"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: body overflow hidden')
else:
    # Zeige genaue Zeichen
    idx = c.find('#pdf-popup-modal.visible')
    snippet = c[idx:idx+120]
    print('Snippet:', repr(snippet))
