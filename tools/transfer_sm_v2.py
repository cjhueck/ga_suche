# -*- coding: utf-8 -*-
"""
SM-Uebertragung v2: Kurze, eindeutige Suchmuster
"""
import re

source_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Quelle\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'
target_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Ziel\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(source_path, 'r', encoding='utf-8') as f:
    source = f.read()
with open(target_path, 'r', encoding='utf-8') as f:
    target = f.read()

# Entferne zuerst alle existierenden SM aus Ziel
target = re.sub(r'\[\|\d+\|\]', '', target)
target = re.sub(r'\|\d+\|', '', target)
target = re.sub(r'  +', ' ', target)

print('Existierende SM entfernt.')

# Extrahiere SM mit kurzem Kontext (10 Zeichen)
sm_data = []
for m in re.finditer(r'\[\|(\d+)\|\]', source):
    page = int(m.group(1))
    pos = m.start()
    end = m.end()
    
    before = source[max(0, pos-15):pos]
    after = source[end:end+15]
    
    # Entferne andere SM
    before = re.sub(r'\[\|\d+\|\]', '', before)
    after = re.sub(r'\[\|\d+\|\]', '', after)
    
    sm_data.append({
        'page': page,
        'sm': m.group(0),
        'before': before.strip(),
        'after': after.strip()
    })

print(f'SM in Quelle: {len(sm_data)}')

# Zeige alle SM
for item in sm_data:
    print(f"  [{item['page']}]: '{item['before'][-10:]}' | '{item['after'][:10]}'")

# Fuege SM ein
result = target
inserted = 0
not_found = []

for item in sm_data:
    before = item['before'][-10:]  # Letzte 10 Zeichen
    after = item['after'][:10]     # Erste 10 Zeichen
    sm = item['sm']
    page = item['page']
    
    if not before:
        # SM am Dateianfang
        if after in result:
            result = sm + ' ' + result
            inserted += 1
            continue
    
    # Suche: before + (Block-ID + Whitespace ODER nur Whitespace) + after
    before_esc = re.escape(before)
    after_esc = re.escape(after)
    
    # Muster: before, dann optional Block-ID, dann Whitespace, dann after
    pattern = before_esc + r'(\s*\^[a-z0-9]+)?\s+' + after_esc
    
    match = re.search(pattern, result)
    
    if match:
        block_id = match.group(1) if match.group(1) else ''
        if block_id:
            replacement = before + block_id + '\n\n' + sm + ' ' + after
        else:
            replacement = before + ' ' + sm + ' ' + after
        result = result[:match.start()] + replacement + result[match.end():]
        inserted += 1
    else:
        not_found.append(item)

print(f'\nEingefuegt: {inserted}/{len(sm_data)}')

if not_found:
    print('\nNicht gefunden:')
    for item in not_found:
        print(f"  [{item['page']}]: '{item['before'][-10:]}' | '{item['after'][:10]}'")

# Speichern
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

final_sm = re.findall(r'\[\|(\d+)\|\]', result)
print(f'\nSM in Ziel: {len(final_sm)}')
