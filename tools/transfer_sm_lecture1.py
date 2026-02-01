# -*- coding: utf-8 -*-
"""
SM-Uebertragung fuer Vortrag 1:
1. Extrahiere SM mit Kontext aus Quelle
2. Suche Kontext in Ziel
3. Fuege SM ein
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

source_path = os.path.join(folder, 'GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md')
target_path = os.path.join(folder, 'alt', 'GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md')

# Lese Dateien
with open(source_path, 'r', encoding='utf-8') as f:
    source = f.read()
with open(target_path, 'r', encoding='utf-8') as f:
    target = f.read()

print(f'Quelle: {len(source)} Zeichen')
print(f'Ziel: {len(target)} Zeichen')

# Extrahiere SM mit Kontext
sm_list = []
for match in re.finditer(r'\[\|(\d+)\|\]', source):
    page = int(match.group(1))
    pos = match.start()
    end = match.end()
    
    # 40 Zeichen Kontext vor und nach
    before = source[max(0, pos-40):pos]
    after = source[end:end+40]
    
    # Bereinige von anderen SM
    before = re.sub(r'\[\|\d+\|\]', '', before).strip()
    after = re.sub(r'\[\|\d+\|\]', '', after).strip()
    
    sm_list.append({
        'page': page,
        'sm': match.group(0),
        'before': before[-30:],
        'after': after[:30]
    })

print(f'\nSM in Quelle: {len(sm_list)}')
for item in sm_list:
    print(f"  [{item['page']}]: ...{item['before'][-20:]} | {item['after'][:20]}...")

# Fuege SM in Ziel ein
result = target
inserted = 0
not_found = []

for item in sm_list:
    before = item['before'][-25:]
    after = item['after'][:25]
    sm = item['sm']
    
    # Suche: before + whitespace + after
    pattern = re.escape(before) + r'\s*' + re.escape(after)
    
    match = re.search(pattern, result)
    if match:
        # Ersetze mit SM dazwischen
        replacement = before + ' ' + sm + ' ' + after
        result = result[:match.start()] + replacement + result[match.end():]
        inserted += 1
    else:
        not_found.append(item)

print(f'\nEingefuegt: {inserted}/{len(sm_list)}')
if not_found:
    print('Nicht gefunden:')
    for item in not_found:
        print(f"  [{item['page']}]: '{item['before'][-20:]}' | '{item['after'][:20]}'")

# Speichere
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

# Verifiziere
final_sm = re.findall(r'\[\|(\d+)\|\]', result)
print(f'\nSM in Ziel nach Uebertragung: {len(final_sm)}')
print(f'Seiten: {sorted([int(x) for x in final_sm])}')
