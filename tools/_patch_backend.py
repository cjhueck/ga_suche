import io, sys, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''app.use(express.static(__dirname, {
  etag: false,
  lastModified: false,
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
    }
  }
}));'''

new = '''app.use(express.static(__dirname, {
  etag: false,
  lastModified: false,
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html') || filePath.endsWith('.js')) {
      res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
    }
  }
}));'''

if old in content:
    shutil.copy2(path, path + '.bak_cache')
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: no-cache fuer .js hinzugefuegt')
else:
    print('FEHLER: Kontext nicht gefunden')
    idx = content.find('express.static(__dirname')
    print(repr(content[idx:idx+200]))
