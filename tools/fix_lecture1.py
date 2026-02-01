# -*- coding: utf-8 -*-
import re
import os

# Dateipfade
base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

source_path = os.path.join(folder, 'GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md')
target_path = os.path.join(folder, 'alt', 'GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md')

with open(source_path, 'r', encoding='utf-8') as f:
    source = f.read()

with open(target_path, 'r', encoding='utf-8') as f:
    target = f.read()

# 1. Entferne alle defekten SM aus Zieldatei
# Formate: |XX|, [|XX|], |XX|X (am Wortanfang)
target_clean = re.sub(r'\|(\d+)\|(?=[a-zA-Z])', '', target)  # |XX| vor Wort
target_clean = re.sub(r'\[\|(\d+)\|\]', '', target_clean)     # [|XX|]
target_clean = re.sub(r'\|(\d+)\|', '', target_clean)         # |XX|
target_clean = re.sub(r'  +', ' ', target_clean)              # Doppelte Leerzeichen

print(f'Defekte SM entfernt')

# 2. Extrahiere SM mit Kontext aus Quelle
pattern = r'(\S+)\s+(\S+)\s*(\[\|\d+\|\])\s*(\S+)\s+(\S+)'
sm_list = []
for match in re.finditer(pattern, source):
    sm_list.append({
        'w1': match.group(1),
        'w2': match.group(2),  
        'sm': match.group(3),
        'w3': match.group(4),
        'w4': match.group(5),
    })

print(f'SM in Quelle: {len(sm_list)}')

# 3. Fuege SM in bereinigte Zieldatei ein
result = target_clean
transferred = 0
not_found = []

for item in sm_list:
    sm = item['sm']
    w2 = re.sub(r'\^[a-z0-9]+', '', item['w2'])
    w3 = re.sub(r'\^[a-z0-9]+', '', item['w3'])
    
    # Suche w2 gefolgt von w3
    search = re.escape(w2) + r'(\s*(?:\^[a-z0-9]+)?\s*)' + re.escape(w3)
    match = re.search(search, result, re.IGNORECASE)
    
    if match:
        if '[|' not in match.group(0):
            replacement = w2 + ' ' + sm + ' ' + w3
            result = result[:match.start()] + replacement + result[match.end():]
            transferred += 1
        else:
            not_found.append(item)
    else:
        not_found.append(item)

print(f'Uebertragen: {transferred}')
print(f'Nicht gefunden: {len(not_found)}')

if not_found:
    print('\nNicht gefundene SM:')
    for item in not_found:
        print(f"  {item['sm']}: {item['w2']} | {item['w3']}")

# Speichern
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

# Pruefe Ergebnis
final_sm = re.findall(r'\[\|\d+\|\]', result)
print(f'\nSM in Ergebnis: {len(final_sm)}')
