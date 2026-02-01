# -*- coding: utf-8 -*-
"""Finde genauen Kontext in Zieldateien"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

# Fehlende SM mit Suchwort
missing = [
    (5, 91, 'Seite 321'),
    (7, 120, 'aus einer'),
    (8, 135, 'wiedergeboren'),
    (9, 149, 'Gesetzlichkeit'),
    (9, 151, 'Zwiespältigkeit'),
    (9, 152, 'erkennen'),
    (9, 157, 'Christus'),
    (10, 163, 'Zivilisation'),
    (10, 167, 'Nun, das ist'),
    (10, 174, 'Petrus'),
    (11, 182, 'theosophische'),
    (11, 190, 'Telegramm'),
    (12, 205, 'Menschenleben'),
    (12, 212, 'Tat'),
    (12, 214, 'heranzuziehen'),
    (13, 230, 'Inneren'),
    (15, 266, 'Tafel'),
    (15, 268, 'Umstände'),
    (15, 269, 'Jahve-Religion'),
    (15, 272, 'Jahve'),
    (18, 307, 'Wenn dasjenige'),
]

def get_file(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

for num, page, keyword in missing:
    path = get_file(num)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Suche Keyword und zeige Kontext
    matches = list(re.finditer(re.escape(keyword), content, re.IGNORECASE))
    print(f'\n=== V{num} SM {page}: "{keyword}" ===')
    
    for i, m in enumerate(matches):
        before = content[max(0, m.start()-30):m.start()]
        after = content[m.end():m.end()+30]
        print(f'  {i+1}: ...{before}>>>{m.group()}<<<{after}...')
