# -*- coding: utf-8 -*-
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

path = os.path.join(folder, 'Ziel', 'GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md')
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

sm = re.findall(r'\[\|(\d+)\|\]', c)
pages = sorted([int(x) for x in sm])
print(f'SM: {len(sm)}')
print(f'Seiten: {pages}')
print(f'Erwartet 15-32: {pages == list(range(15, 33))}')
