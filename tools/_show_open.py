import io, sys
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# openPdfPopup - Zeilen 39460-39575
for i in range(39459, 39580):
    print(f'{i+1}: {lines[i].rstrip()}')
