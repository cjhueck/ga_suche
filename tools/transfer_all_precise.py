# -*- coding: utf-8 -*-
"""
Praezise SM-Uebertragung fuer alle Vortraege 3-18
"""
import re
import os

def clean_for_matching(text):
    """Entferne SM, Block-IDs und normalisiere fuer Matching"""
    text = re.sub(r'\[\|\d+\|\]', '', text)
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_sm_with_long_context(source):
    """Extrahiere SM mit langem Kontext"""
    sm_list = []
    
    for match in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(match.group(1))
        pos = match.start()
        
        before_start = max(0, pos - 80)
        before_text = source[before_start:pos]
        if '\n\n' in before_text:
            before_text = before_text.split('\n\n')[-1]
        before_text = clean_for_matching(before_text).strip()[-50:]
        
        after_end = min(len(source), match.end() + 80)
        after_text = source[match.end():after_end]
        if '\n\n' in after_text:
            after_text = after_text.split('\n\n')[0]
        after_text = clean_for_matching(after_text).strip()[:50]
        
        is_word_break = bool(re.match(r'\w$', source[pos-1:pos]) and re.match(r'^\w', source[match.end():match.end()+1])) if pos > 0 else False
        
        sm_list.append({
            'page': page,
            'sm': match.group(0),
            'before': before_text,
            'after': after_text,
            'is_word_break': is_word_break
        })
    
    return sm_list

def insert_sm_precise(target, sm_data):
    """Fuege SM praezise ein"""
    result = target
    inserted = 0
    not_found = []
    
    for item in sm_data:
        sm = item['sm']
        before = item['before']
        after = item['after']
        
        if len(before) < 5:
            # SM am Anfang - suche nach after
            after_pattern = re.escape(after[:30])
            match = re.search(after_pattern, result, re.IGNORECASE)
            if match and '[|' not in result[max(0,match.start()-5):match.start()]:
                result = result[:match.start()] + sm + ' ' + result[match.start():]
                inserted += 1
                continue
            not_found.append(item)
            continue
        
        if len(after) < 5:
            not_found.append(item)
            continue
        
        before_esc = re.escape(before[-25:])
        after_esc = re.escape(after[:25])
        
        pattern = before_esc + r'\s*' + after_esc
        target_clean = clean_for_matching(result)
        match = re.search(pattern, target_clean, re.IGNORECASE)
        
        if match:
            before_search = before[-15:]
            for orig_match in re.finditer(re.escape(before_search), result, re.IGNORECASE):
                check_area = result[orig_match.end():orig_match.end()+15]
                if '[|' not in check_area:
                    if item['is_word_break']:
                        new_result = result[:orig_match.end()] + sm + result[orig_match.end():]
                    else:
                        new_result = result[:orig_match.end()] + ' ' + sm + ' ' + result[orig_match.end():]
                    result = new_result
                    inserted += 1
                    break
            else:
                not_found.append(item)
        else:
            not_found.append(item)
    
    return result, inserted, not_found

def process_lecture(num, folder, alt_folder):
    """Verarbeite einen Vortrag"""
    # Finde Dateien
    source_file = None
    target_file = None
    
    for f in os.listdir(folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            source_file = os.path.join(folder, f)
            break
    
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            target_file = os.path.join(alt_folder, f)
            break
    
    if not source_file or not target_file:
        print(f'Vortrag {num}: Dateien nicht gefunden')
        return None
    
    print(f'\n=== Vortrag {num} ===')
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_file, 'r', encoding='utf-8') as f:
        target = f.read()
    
    # Entferne alle SM
    target_clean = re.sub(r'\[\|\d+\|\]', '', target)
    target_clean = re.sub(r'\|\d+\|', '', target_clean)
    target_clean = re.sub(r'  +', ' ', target_clean)
    
    # Extrahiere und fuege ein
    sm_data = extract_sm_with_long_context(source)
    result, inserted, not_found = insert_sm_precise(target_clean, sm_data)
    
    print(f'  Quelle: {len(sm_data)} SM')
    print(f'  Eingefuegt: {inserted}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    # Speichern
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    return {
        'num': num,
        'total': len(sm_data),
        'inserted': inserted,
        'not_found': not_found
    }

# Hauptprogramm
base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

results = []
for num in range(3, 19):
    result = process_lecture(num, folder, alt_folder)
    if result:
        results.append(result)

# Zusammenfassung
print('\n' + '='*50)
print('ZUSAMMENFASSUNG')
print('='*50)
total = sum(r['total'] for r in results)
inserted = sum(r['inserted'] for r in results)
not_found_count = sum(len(r['not_found']) for r in results)

print(f'Gesamt SM: {total}')
print(f'Eingefuegt: {inserted}')
print(f'Nicht gefunden: {not_found_count}')

if not_found_count > 0:
    print('\nNicht gefundene SM:')
    for r in results:
        if r['not_found']:
            print(f"\n  Vortrag {r['num']}:")
            for item in r['not_found']:
                print(f"    [|{item['page']}|]: ...{item['before'][-15:]}|{item['after'][:15]}...")
