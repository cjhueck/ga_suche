import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige wie fullLectures befüllt wird - suche nach fullLectures[
for i,l in enumerate(lines,1):
    if 'fullLectures[' in l or 'fullLectures =' in l:
        print(f'{i}: {l.rstrip()[:100]}')
    if i > 2500:
        break

print()
# Zeige Struktur eines Lecture-Eintrags (was sind die Felder)
print('=== Lecture-Felder (Suche nach .paragraphs) ===')
for i,l in enumerate(lines,1):
    if '.paragraphs' in l and 'fullLectures' in l:
        print(f'{i}: {l.rstrip()[:100]}')
