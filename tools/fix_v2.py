# -*- coding: utf-8 -*-
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

path = os.path.join(folder, 'alt', 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921.md')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix [|34|]: Einfluss -> Ein[|34|]fluss
content = content.replace('Einfluss aus auf', 'Ein[|34|]fluss aus auf', 1)

# Fix [|42|]: Entwickelungsstufen früherer -> Entwickelungsstufen [|42|] früherer
content = content.replace('geistigen Entwickelungsstufen früherer', 'geistigen Entwickelungsstufen [|42|] früherer', 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fertig!')

# Verifiziere
import re
sm = re.findall(r'\[\|(\d+)\|\]', content)
print(f'SM: {sorted([int(x) for x in sm])}')
