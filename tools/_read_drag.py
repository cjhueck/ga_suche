with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines[16724:16815], start=16725):
    print(f'{i}: {l.rstrip()}')
