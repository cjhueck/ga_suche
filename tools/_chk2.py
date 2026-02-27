import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Suche nach express.static oder app.js serving
for i,l in enumerate(lines,1):
    low = l.lower()
    if 'static' in low or 'app.js' in l or 'maxage' in low or 'cache' in low:
        print(f'{i}: {l.rstrip()[:100]}')
