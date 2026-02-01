# -*- coding: utf-8 -*-
import os
import re

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

path = os.path.join(folder, 'alt', 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921.md')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix mit Regex (flexibles Whitespace)
content = re.sub(r'Entwickelungsstufen\s+früherer', 'Entwickelungsstufen [|42|] früherer', content, count=1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

sm = re.findall(r'\[\|(\d+)\|\]', content)
print(f'SM: {sorted([int(x) for x in sm])}')
print('Vollstaendig 33-46:', sorted([int(x) for x in sm]) == list(range(33, 47)))
