import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeilen 3165-3225
for i in range(3164, 3226):
    print(f'{i+1}: {lines[i].rstrip()}')
