import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
old = r'(?=[ \[;])'
new = r'(?=[ \[;\s]|$)'
if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: Regex erweitert')
else:
    print('Nicht gefunden')
