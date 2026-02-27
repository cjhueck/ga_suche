import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige Bereich um font-size 0.9rem in showMapsInViewer (nach Zeile 30990)
for i, l in enumerate(lines[30985:31010], start=30986):
    print(f'{i}: {repr(l.rstrip()[:80])}')
