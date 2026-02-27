import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Patch 1 prüfen
for i, l in enumerate(lines[12605:12615], start=12606):
    print(f'{i}: {l.rstrip()[:90]}')

print()

# Patch 2 prüfen: neue Paragraph-Link Logik
for i, l in enumerate(lines, start=1):
    if 'GA-Links nach Zitat-Absätzen' in l:
        for j in range(i-1, min(i+10, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()[:90]}')
        break
