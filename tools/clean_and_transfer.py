# -*- coding: utf-8 -*-
"""
Schritt 1: Alle SM entfernen
Schritt 2: SM uebertragen mit Worttrennung-Erkennung
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

print('=== SCHRITT 1: SM entfernen ===')
# Entferne beide Formate
target = re.sub(r'\[\|\d+\|\]', '', target)
target = re.sub(r'\|\d+\|', '', target)
# Bereinige Leerzeichen
target = re.sub(r'  +', ' ', target)
target = re.sub(r'^ ', '', target)  # Am Anfang
target = re.sub(r'\n ', '\n', target)  # Nach Zeilenumbruch
print('SM entfernt.')

print('\n=== SCHRITT 2: SM uebertragen ===')

# Extrahiere SM mit Kontext
sm_list = []
for match in re.finditer(r'\[\|(\d+)\|\]', source):
    page = int(match.group(1))
    pos = match.start()
    end = match.end()
    
    # Pruefe Worttrennung (Buchstabe vor UND nach SM)
    is_word_break = False
    if pos > 0 and end < len(source):
        char_before = source[pos-1]
        char_after = source[end]
        if re.match(r'[a-zA-ZäöüÄÖÜß]', char_before) and re.match(r'[a-zA-ZäöüÄÖÜß]', char_after):
            is_word_break = True
    
    # Kontext
    before = source[max(0, pos-50):pos]
    after = source[end:end+50]
    before = re.sub(r'\[\|\d+\|\]', '', before).strip()
    after = re.sub(r'\[\|\d+\|\]', '', after).strip()
    
    if is_word_break:
        # Finde ganzes Wort
        word_before = re.search(r'(\w+)$', source[:pos])
        word_after = re.search(r'^(\w+)', source[end:])
        if word_before and word_after:
            full_word = word_before.group(1) + word_after.group(1)
            sm_list.append({
                'page': page,
                'sm': match.group(0),
                'is_word_break': True,
                'word_part1': word_before.group(1),
                'word_part2': word_after.group(1),
                'full_word': full_word
            })
            continue
    
    sm_list.append({
        'page': page,
        'sm': match.group(0),
        'is_word_break': False,
        'before': before[-30:],
        'after': after[:30]
    })

print(f'SM in Quelle: {len(sm_list)}')

# Fuege SM ein
result = target
inserted = 0
not_found = []

for item in sm_list:
    sm = item['sm']
    
    if item['is_word_break']:
        # Suche ganzes Wort, fuege SM in der Mitte ein
        full_word = item['full_word']
        if full_word in result:
            # Finde Position und ersetze
            new_word = item['word_part1'] + sm + item['word_part2']
            result = result.replace(full_word, new_word, 1)
            inserted += 1
            print(f"  [{item['page']}]: Worttrennung '{full_word}' -> '{new_word}'")
        else:
            not_found.append(item)
    else:
        before = item['before'][-25:]
        after = item['after'][:25]
        
        # Suche mit flexiblem Whitespace
        pattern = re.escape(before) + r'\s+' + re.escape(after)
        match = re.search(pattern, result)
        
        if match:
            replacement = before + ' ' + sm + ' ' + after
            result = result[:match.start()] + replacement + result[match.end():]
            inserted += 1
            print(f"  [{item['page']}]: eingefuegt")
        else:
            not_found.append(item)

print(f'\nEingefuegt: {inserted}/{len(sm_list)}')

if not_found:
    print('\nNicht gefunden:')
    for item in not_found:
        if item['is_word_break']:
            print(f"  [{item['page']}]: Wort '{item['full_word']}'")
        else:
            print(f"  [{item['page']}]: '{item['before'][-20:]}' | '{item['after'][:20]}'")

# Speichere
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

# Verifiziere
final_sm = re.findall(r'\[\|(\d+)\|\]', result)
print(f'\nSM in Ziel: {len(final_sm)}')
print(f'Seiten: {sorted([int(x) for x in final_sm])}')
