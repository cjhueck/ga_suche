import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeile 523-545
for i in range(522, 548):
    print(f'{i+1}: {lines[i].rstrip()[:100]}')
