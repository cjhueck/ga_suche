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

# Finde Kontext um "Entwickelungsstufen"
match = re.search(r'.{50}Entwickelungsstufen.{50}', content)
if match:
    print(f'Gefunden: ...{match.group()}...')

# Fix: Suche den genauen Text
old = 'Entwickelungsstufen früherer'
if old in content:
    content = content.replace(old, 'Entwickelungsstufen [|42|] früherer', 1)
    print('Ersetzt!')
else:
    print(f'"{old}" nicht gefunden')
    # Zeige was wirklich da steht
    match2 = re.search(r'Entwickelungsstufen\s+\S+', content)
    if match2:
        print(f'Stattdessen: "{match2.group()}"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

sm = re.findall(r'\[\|(\d+)\|\]', content)
print(f'SM: {sorted([int(x) for x in sm])}')
