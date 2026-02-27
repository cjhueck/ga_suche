with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    src = f.read()
# Zeige Bereich um "a[href^=" 
idx = src.find('maps-obsidian-content a[href^="#"]')
if idx >= 0:
    snippet = src[idx-10:idx+500]
    print(repr(snippet))
else:
    print('nicht gefunden')
