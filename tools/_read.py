import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige Zeilen mit Einrückung 0-2 zwischen 11250 und 12200
print('=== indent <=2, Bereich 11250-12200 ===')
for i, l in enumerate(lines[11249:12200], start=11250):
    stripped = l.lstrip()
    indent = len(l) - len(stripped)
    if indent <= 2 and stripped.strip():
        print(f'{i} [{indent}]: {l.rstrip()[:100]}')
