import re
from pathlib import Path

folder = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
for d in folder.iterdir():
    if 'GA019' in d.name:
        ga_folder = d
        break

# Finde GA019/2 _new.md
for f in ga_folder.iterdir():
    if '(2.)' in f.name and '_new.md' in f.name:
        content = f.read_text(encoding='utf-8')
        
        # Finde alle Marker
        markers = re.findall(r'\|(\d+)\|', content)
        print(f'Marker: {len(markers)}')
        if markers:
            print(f'Seiten: {markers}')
        
        # Zeige Position von nackter '69'
        for m in re.finditer(r'(?<!\|)\b69\b(?!\|)', content):
            idx = m.start()
            print(f'\nNackte 69 gefunden bei Position {idx}:')
            print(repr(content[max(0,idx-30):idx+40]))
        
        # Zeige erste 300 Zeichen
        print(f'\n=== Anfang ===')
        print(content[:300])
        break

