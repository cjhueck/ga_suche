import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige ALLE nicht-leeren Zeilen 11260-12165
print('=== Alle nicht-leeren Zeilen 11260-12165 ===')
for i in range(11259, 12165):
    l = lines[i]
    if l.strip():
        ind = len(l) - len(l.lstrip())
        print(f'{i+1} [{ind}]: {l.rstrip()[:90]}')
