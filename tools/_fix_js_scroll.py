import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# openPdfPopup: auch html und pdf-viewer-panel
old_open = """      // Modal anzeigen
      modal.classList.add('visible');
      document.body.style.overflow = 'hidden';"""

new_open = """      // Modal anzeigen - aeusseren Scrollbar verhindern
      modal.classList.add('visible');
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';
      const pdfPanel = document.getElementById('pdf-viewer-panel');
      if (pdfPanel) pdfPanel.style.overflow = 'hidden';"""

# closePdfPopup: zuruecksetzen
old_close = """    if (modal) {
      modal.classList.remove('visible');
      document.body.style.overflow = '';
      popupPage = null;"""

new_close = """    if (modal) {
      modal.classList.remove('visible');
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
      const pdfPanel = document.getElementById('pdf-viewer-panel');
      if (pdfPanel) pdfPanel.style.overflow = '';
      popupPage = null;"""

if old_open in c and old_close in c:
    c = c.replace(old_open, new_open, 1)
    c = c.replace(old_close, new_close, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: JS overflow fix')
else:
    print('open:', old_open[:50] in c)
    print('close:', old_close[:50] in c)
