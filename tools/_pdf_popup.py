import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Suche pdf-popup Kontext
idx = c.find('pdf-popup')
while idx >= 0:
    start = max(0, idx - 100)
    end = min(len(c), idx + 300)
    print('---')
    print(repr(c[start:end]))
    print()
    idx = c.find('pdf-popup', idx + 1)
    if idx < 0:
        break
    if idx > 3200:  # limit
        break
