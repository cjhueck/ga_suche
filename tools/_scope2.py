import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Nur Zeilen mit indent <=4 zwischen 11260 und 12163
for i in range(11259, 12163):
    l = lines[i]
    if l.strip():
        ind = len(l) - len(l.lstrip())
        if ind <= 4:
            print(f'{i+1} [{ind}]: {l.rstrip()[:90]}')
