# -*- coding: utf-8 -*-
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

# Erwartete SM pro Vortrag (Startseite, Endseite)
expected = {
    1: (15, 32),
    2: (33, 46),
    3: (47, 65),
    4: (66, 82),
    5: (83, 96),
    6: (97, 112),
    7: (113, 129),
    8: (130, 144),
    9: (145, 161),
    10: (162, 177),
    11: (178, 199),
    12: (200, 224),
    13: (225, 243),
    14: (244, 261),
    15: (262, 277),
    16: (278, 290),
    17: (291, 306),
    18: (307, 320),
}

total_expected = 0
total_found = 0
all_missing = []

for num in range(1, 19):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            path = os.path.join(alt_folder, f)
            break
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sm = [int(x) for x in re.findall(r'\[\|(\d+)\|\]', content)]
    start, end = expected[num]
    exp_pages = list(range(start, end + 1))
    
    total_expected += len(exp_pages)
    total_found += len(sm)
    
    missing = [p for p in exp_pages if p not in sm]
    if missing:
        print(f'Vortrag {num}: {len(sm)}/{len(exp_pages)} SM, fehlen: {missing}')
        all_missing.extend([(num, p) for p in missing])
    else:
        print(f'Vortrag {num}: {len(sm)}/{len(exp_pages)} SM - VOLLSTAENDIG')

print(f'\n=== GESAMT ===')
print(f'Erwartet: {total_expected}')
print(f'Gefunden: {total_found}')
print(f'Fehlend: {len(all_missing)}')
