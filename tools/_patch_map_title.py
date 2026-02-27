import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Nach "const map = COGGLE_MAPS.find..." den document-title setzen
old = """  const map = COGGLE_MAPS.find(m => m.id === selectedId) || COGGLE_MAPS[0];
  const usePublish = (window._mapsViewMode || 'local') === 'publish' && map.publishUrl;"""

new = """  const map = COGGLE_MAPS.find(m => m.id === selectedId) || COGGLE_MAPS[0];
  const usePublish = (window._mapsViewMode || 'local') === 'publish' && map.publishUrl;
  const titleEl = document.getElementById('document-title');
  if (titleEl) titleEl.textContent = map.name || 'Karten';"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: document-title = map.name')
else:
    print('Nicht gefunden')
