import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige aktuellen Block ab "GA-Links nach Zitat"
for i,l in enumerate(lines, 1):
    if 'GA-Links nach Zitat' in l:
        for j in range(i-1, min(i+60, len(lines))):
            print(f'{j+1}: {repr(lines[j].rstrip()[:80])}')
        break
