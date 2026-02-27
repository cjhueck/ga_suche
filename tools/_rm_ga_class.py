import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Nur die ga-keyword-link Zeile entfernen
old = "\n              a.className = 'ga-keyword-link';"
new = ""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: ga-keyword-link Klasse entfernt')
else:
    print('Nicht gefunden - evtl. schon entfernt oder anderer Kontext')
