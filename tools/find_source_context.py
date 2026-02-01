# -*- coding: utf-8 -*-
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

# Suche SM in Quelldateien mit mehr Kontext
missing_sm = [42, 91, 135, 149, 157, 167, 257, 266, 272]

for f in os.listdir(folder):
    if f.endswith('.md') and 'VORTRAG' in f.upper():
        path = os.path.join(folder, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        for page in missing_sm:
            pattern = rf'.{{50}}\[\|{page}\|\].{{50}}'
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                num = re.search(r'\((\d+)\.\)', f)
                if num:
                    print(f'\nVortrag {num.group(1)}, [|{page}|]:')
                    for m in matches:
                        clean = m.replace('\n', ' ')
                        print(f'  ...{clean}...')
