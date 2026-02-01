# -*- coding: utf-8 -*-
"""
SM-Uebertragung: 
- ß durch ss ersetzen beim Suchen
- 2-3 Woerter vor/nach SM fuer eindeutige Treffer
"""
import re

source_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Quelle\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'
target_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\Ziel\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(source_path, 'r', encoding='utf-8') as f:
    source = f.read()
with open(target_path, 'r', encoding='utf-8') as f:
    target = f.read()

# Entferne existierende SM aus Ziel
target = re.sub(r'\[\|\d+\|\]', '', target)
target = re.sub(r'\|\d+\|', '', target)
target = re.sub(r'  +', ' ', target)
print('Existierende SM entfernt.')

def normalize(text):
    """ß -> ss fuer Suche"""
    return text.replace('ß', 'ss').replace('–', '-')

# Extrahiere SM mit 3 Woertern Kontext
sm_data = []
for m in re.finditer(r'\[\|(\d+)\|\]', source):
    page = int(m.group(1))
    pos = m.start()
    end = m.end()
    
    # 50 Zeichen vor und nach
    before = source[max(0, pos-50):pos]
    after = source[end:end+50]
    
    # Entferne andere SM
    before = re.sub(r'\[\|\d+\|\]', '', before)
    after = re.sub(r'\[\|\d+\|\]', '', after)
    
    # Extrahiere 3 Woerter vor und nach
    words_before = before.split()[-3:]
    words_after = after.split()[:3]
    
    sm_data.append({
        'page': page,
        'sm': m.group(0),
        'before': ' '.join(words_before),
        'after': ' '.join(words_after)
    })

print(f'SM in Quelle: {len(sm_data)}')

# Fuege SM ein
result = target
inserted = 0
not_found = []

for item in sm_data:
    before = item['before']
    after = item['after']
    sm = item['sm']
    page = item['page']
    
    # Normalisiere fuer Suche (ß -> ss)
    before_norm = normalize(before)
    after_norm = normalize(after)
    
    # Suche im normalisierten Ziel
    target_norm = normalize(result)
    
    # Baue Suchmuster mit flexiblem Whitespace
    before_esc = re.escape(before_norm)
    after_esc = re.escape(after_norm)
    
    # Erlaube Block-IDs und flexible Whitespace/Zeilenumbrueche
    pattern = before_esc + r'(\s*\^[a-z0-9]+)?\s+' + after_esc
    
    match = re.search(pattern, target_norm)
    
    if match:
        # Finde gleiche Position im Original
        start = match.start()
        end_pos = match.end()
        
        # Extrahiere Block-ID falls vorhanden
        original_match = result[start:end_pos]
        block_id_match = re.search(r'(\^[a-z0-9]+)', original_match)
        block_id = block_id_match.group(1) if block_id_match else ''
        
        # Finde original before/after im result
        orig_before = result[start:start+len(before)]
        
        if block_id:
            # Mit Block-ID: before + block_id + newlines + SM + after
            replacement = result[start:match.end()].replace(
                block_id, 
                block_id + '\n\n' + sm
            )
        else:
            # Ohne Block-ID: Fuege SM zwischen before und after
            # Finde die Whitespace-Position
            ws_start = start + len(before)
            ws_end = end_pos - len(after)
            replacement = result[start:ws_start] + ' ' + sm + ' ' + result[ws_end:end_pos]
        
        result = result[:start] + replacement + result[end_pos:]
        inserted += 1
        print(f'[{page}]: eingefuegt')
    else:
        not_found.append(item)
        print(f'[{page}]: NICHT GEFUNDEN - "{before}" | "{after}"')

print(f'\nEingefuegt: {inserted}/{len(sm_data)}')

# Speichern
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

final_sm = re.findall(r'\[\|(\d+)\|\]', result)
print(f'SM in Ziel: {len(final_sm)}')
print(f'Seiten: {sorted([int(x) for x in final_sm])}')
