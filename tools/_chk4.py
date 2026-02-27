import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# resolve-lecture Endpoint
print('=== /api/resolve-lecture ===')
for i in range(3718, 3770):
    print(f'{i+1}: {lines[i].rstrip()[:100]}')

print()
# Zeige wie paragraphsFromLectures befüllt wird
print('=== paragraphsFromLectures Befüllung ===')
for i,l in enumerate(lines,1):
    if 'paragraphsFromLectures' in l and ('push' in l or 'index' in l.lower()):
        print(f'{i}: {l.rstrip()[:100]}')
    if i > 3720:
        break
