import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Wenn Popup offen: Panel-Scrollbar ausblenden (nur Popup-Container soll scrollen)
old = """    body:has(#pdf-popup-modal.visible) {
      overflow: hidden !important;
    }
    
    #pdf-popup-container {"""

new = """    body:has(#pdf-popup-modal.visible) {
      overflow: hidden !important;
    }
    
    body:has(#pdf-popup-modal.visible) #pdf-viewer-panel .pdf-canvas-container,
    body:has(#pdf-popup-modal.visible) #pdf-viewer-panel {
      overflow: hidden !important;
    }
    
    #pdf-popup-container {"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: Panel-Scrollbar ausgeblendet wenn Popup offen')
else:
    print('Block nicht gefunden')
