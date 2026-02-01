# -*- coding: utf-8 -*-
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

path = os.path.join(folder, 'alt', 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921.md')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

sm = re.findall(r'\[\|(\d+)\|\]', content)
print(f'SM: {sorted([int(x) for x in sm])}')
print(f'[|34|]: {"JA" if "[|34|]" in content else "NEIN"}')
print(f'[|42|]: {"JA" if "[|42|]" in content else "NEIN"}')
