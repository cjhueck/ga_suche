import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
old = "a.textContent = '(' + (lid || '').replace(/^GA/i, '') + ')';"
new = "a.textContent = '(' + (lid || '') + ')';"
if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: Anzeige (GA307/5)')
else:
    print('Nicht gefunden:', repr(old[:50]))
