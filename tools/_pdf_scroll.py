import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# pdf-viewer-panel CSS (3068-3110)
print('=== #pdf-viewer-panel CSS ===')
for i in range(3068, 3125):
    if i < len(lines):
        print(f'{i+1}: {lines[i].rstrip()[:100]}')

print()
# pdf-viewer-panel HTML (9848-9920)
print('=== pdf-viewer-panel HTML ===')
for i in range(9847, 9935):
    if i < len(lines):
        print(f'{i+1}: {lines[i].rstrip()[:100]}')
