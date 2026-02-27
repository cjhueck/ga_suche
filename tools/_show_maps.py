import io, sys
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# showMapsInViewer Anfang - Zeilen 30733-30820
for i in range(30732, 30830):
    print(f'{i+1}: {lines[i].rstrip()}')
