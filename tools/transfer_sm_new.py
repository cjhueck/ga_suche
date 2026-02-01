# -*- coding: utf-8 -*-
"""
SM-Uebertragung: Einfacher Ansatz
- Extrahiere Text VOR und NACH jedem SM aus Quelle
- Suche diesen Text im Ziel (mit flexiblem Whitespace)
- Fuege SM ein
"""
import re

source_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Quelle\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'
target_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Ziel\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(source_path, 'r', encoding='utf-8') as f:
    source = f.read()
with open(target_path, 'r', encoding='utf-8') as f:
    target = f.read()

# Extrahiere alle SM mit Kontext
sm_data = []
for m in re.finditer(r'\[\|(\d+)\|\]', source):
    page = int(m.group(1))
    pos = m.start()
    end = m.end()
    
    # Text direkt vor und nach SM (ohne andere SM)
    before_raw = source[max(0, pos-30):pos]
    after_raw = source[end:end+30]
    
    # Entferne andere SM aus Kontext
    before = re.sub(r'\[\|\d+\|\]', '', before_raw)
    after = re.sub(r'\[\|\d+\|\]', '', after_raw)
    
    sm_data.append({
        'page': page,
        'sm': m.group(0),
        'before': before,
        'after': after
    })

print(f'SM in Quelle: {len(sm_data)}')

# Fuege SM in Ziel ein
result = target
inserted = 0
not_found = []

for item in sm_data:
    before = item['before']
    after = item['after']
    sm = item['sm']
    page = item['page']
    
    # Kuerze auf die letzten/ersten 20 Zeichen
    before_search = before[-20:]
    after_search = after[:20]
    
    # Baue Suchmuster: before + beliebiges Whitespace + after
    # Escape Sonderzeichen
    before_esc = re.escape(before_search)
    after_esc = re.escape(after_search)
    
    # Suche mit flexiblem Whitespace (inkl. Zeilenumbruch und Block-IDs)
    # Block-IDs haben Format ^xxxxx
    pattern = before_esc + r'(\s*\^[a-z0-9]+)?\s*' + after_esc
    
    match = re.search(pattern, result)
    
    if match:
        # Behalte Block-ID falls vorhanden
        block_id = match.group(1) if match.group(1) else ''
        
        # Erstelle Ersetzung
        if block_id:
            # Block-ID am Ende des Absatzes: before + block_id + newlines + SM + after
            replacement = before_search + block_id + '\n\n' + sm + ' ' + after_search
        else:
            # Kein Block-ID: before + SM + after
            replacement = before_search + ' ' + sm + ' ' + after_search
        
        result = result[:match.start()] + replacement + result[match.end():]
        inserted += 1
        print(f'[{page}]: eingefuegt')
    else:
        not_found.append(item)
        print(f'[{page}]: NICHT GEFUNDEN')
        print(f'       Suche: "{before_search}" ... "{after_search}"')

print(f'\nEingefuegt: {inserted}/{len(sm_data)}')

# Speichern
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

# Verifiziere
final_sm = re.findall(r'\[\|(\d+)\|\]', result)
print(f'SM in Ziel: {len(final_sm)}')
print(f'Seiten: {sorted([int(x) for x in final_sm])}')
