import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Kontext um normalizedParagraphs (Zeile 1324)
print('=== normalizedParagraphs Kontext ===')
for i in range(1290, 1340):
    print(f'{i+1}: {lines[i].rstrip()[:100]}')
