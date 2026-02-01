# -*- coding: utf-8 -*-
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt = os.path.join(folder, 'alt')

# Pruefe verbleibende fehlende SM
missing = [
    (2, 42, 'Entwicklungsstufen'),
    (5, 91, '321'),
    (8, 135, 'werden'),
    (9, 149, 'keit'),
    (9, 157, 'Christus'),
    (10, 167, 'aus'),
    (14, 257, 'Tafel'),
    (15, 266, 'Nun'),
    (15, 272, 'Jahve'),
]

for num, page, word in missing:
    for f in os.listdir(alt):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            path = os.path.join(alt, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Suche Wort mit Kontext
            pattern = r'.{30}' + re.escape(word) + r'.{30}'
            matches = re.findall(pattern, content, re.DOTALL)
            print(f'\nVortrag {num}, [|{page}|], suche "{word}":')
            if matches:
                for m in matches[:3]:
                    clean = m.replace('\n', ' ')
                    print(f'  ...{clean}...')
            else:
                print(f'  Nicht gefunden')
            break
