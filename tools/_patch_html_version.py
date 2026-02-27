import io, sys, re, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze <script src="app.js"> oder <script src="app.js?v=..."> mit neuer Version
old_tag = re.search(r'<script src="app\.js(?:\?[^"]*)?"></script>', content)
if old_tag:
    old_str = old_tag.group(0)
    new_str = '<script src="app.js?v=20260227b"></script>'
    content = content.replace(old_str, new_str, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'OK: {old_str!r} -> {new_str!r}')
else:
    print('FEHLER: <script src="app.js"> nicht gefunden')
    idx = content.find('app.js')
    print(repr(content[max(0,idx-40):idx+60]))
