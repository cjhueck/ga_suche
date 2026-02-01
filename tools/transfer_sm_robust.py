# -*- coding: utf-8 -*-
"""
Robuste SM-Uebertragung mit:
- Flexiblem Whitespace-Matching
- Worttrennung-Erkennung
- ß/ss Normalisierung
"""
import re
import os

def normalize(text):
    """Normalisiere Text fuer Suche"""
    text = text.replace('ß', 'ss')
    text = re.sub(r'\s+', ' ', text)
    return text

def clean_text(text):
    """Entferne SM und Block-IDs"""
    text = re.sub(r'\[\|\d+\|\]', '', text)
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_sm_contexts(source):
    """Extrahiere SM mit Kontext"""
    sm_list = []
    
    for match in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(match.group(1))
        pos = match.start()
        end = match.end()
        
        # Pruefe Worttrennung
        is_word_break = False
        if pos > 0 and end < len(source):
            char_before = source[pos-1]
            char_after = source[end]
            is_word_break = bool(re.match(r'\w', char_before) and re.match(r'\w', char_after))
        
        # Extrahiere Kontext
        before_raw = source[max(0, pos-60):pos]
        after_raw = source[end:end+60]
        
        # Bereinige Kontext
        before = clean_text(before_raw).strip()
        after = clean_text(after_raw).strip()
        
        # Bei Worttrennung: Wortteil vor und nach SM
        if is_word_break:
            # Finde Wort vor SM
            word_before_match = re.search(r'(\w+)$', source[:pos])
            word_after_match = re.search(r'^(\w+)', source[end:])
            if word_before_match and word_after_match:
                full_word = word_before_match.group(1) + word_after_match.group(1)
                sm_list.append({
                    'page': page,
                    'sm': match.group(0),
                    'before': before[-40:],
                    'after': after[:40],
                    'is_word_break': True,
                    'word_part_before': word_before_match.group(1),
                    'word_part_after': word_after_match.group(1),
                    'full_word': full_word
                })
                continue
        
        sm_list.append({
            'page': page,
            'sm': match.group(0),
            'before': before[-40:],
            'after': after[:40],
            'is_word_break': False
        })
    
    return sm_list

def insert_sm(target, sm_list):
    """Einfuegen der SM mit robustem Matching"""
    result = clean_text(target)
    inserted = 0
    not_found = []
    
    for item in sm_list:
        # Sonderfall: SM am Anfang (kein before-Kontext)
        if not item['before'].strip() and not item['is_word_break']:
            after = item['after'][:30]
            after_pattern = re.escape(after).replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
            match = re.search(after_pattern, result, re.IGNORECASE)
            if match:
                result = result[:match.start()] + item['sm'] + ' ' + result[match.start():]
                inserted += 1
                continue
        sm = item['sm']
        
        if item['is_word_break']:
            # Worttrennung: Suche ganzes Wort, fuege SM ein
            full_word = item['full_word']
            word_before = item['word_part_before']
            word_after = item['word_part_after']
            
            # Suche mit flexibler Schreibweise
            pattern = re.escape(full_word)
            # Ersetze ss durch (ss|ß) für flexible Suche
            pattern = pattern.replace('ss', '(ss|ß)')
            
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                # Finde Position zum Einfuegen
                found_word = match.group(0)
                # Berechne wo der SM hin muss
                split_pos = len(word_before)
                new_word = found_word[:split_pos] + sm + found_word[split_pos:]
                result = result[:match.start()] + new_word + result[match.end():]
                inserted += 1
                continue
        else:
            # Normal: Suche Kontext
            before = item['before'][-25:] if len(item['before']) >= 25 else item['before']
            after = item['after'][:25] if len(item['after']) >= 25 else item['after']
            
            if not before or not after:
                not_found.append(item)
                continue
            
            # Baue flexibles Pattern
            before_pattern = re.escape(before)
            after_pattern = re.escape(after)
            
            # Ersetze ss/ß für flexible Suche
            before_pattern = before_pattern.replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
            after_pattern = after_pattern.replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
            
            # Erlaube flexibles Whitespace
            pattern = before_pattern + r'\s*' + after_pattern
            
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                # Ersetze mit SM dazwischen
                replacement = before + ' ' + sm + ' ' + after
                result = result[:match.start()] + replacement + result[match.end():]
                inserted += 1
                continue
        
        not_found.append(item)
    
    return result, inserted, not_found

def process_lecture(num, folder, alt_folder):
    """Verarbeite einen Vortrag"""
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
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_file, 'r', encoding='utf-8') as f:
        target = f.read()
    
    sm_list = extract_sm_contexts(source)
    result, inserted, not_found = insert_sm(target, sm_list)
    
    print(f'\n=== Vortrag {num} ===')
    print(f'  Quelle: {len(sm_list)} SM')
    print(f'  Eingefuegt: {inserted}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    for item in not_found:
        if item['is_word_break']:
            print(f"    [|{item['page']}|]: Worttrennung '{item['full_word']}'")
        else:
            print(f"    [|{item['page']}|]: '{item['before'][-20:]}' | '{item['after'][:20]}'")
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Verifiziere
    final_sm = re.findall(r'\[\|(\d+)\|\]', result)
    pages = sorted([int(x) for x in final_sm])
    print(f'  Ergebnis: {len(final_sm)} SM')
    
    return {'num': num, 'total': len(sm_list), 'inserted': inserted, 'not_found': not_found}

if __name__ == '__main__':
    base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
    folder = None
    for item in os.listdir(base):
        if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
            folder = os.path.join(base, item)
            break
    
    alt_folder = os.path.join(folder, 'alt')
    
    # Verarbeite alle Vortraege
    total_sm = 0
    total_inserted = 0
    all_not_found = []
    
    for num in range(1, 19):
        result = process_lecture(num, folder, alt_folder)
        if result:
            total_sm += result['total']
            total_inserted += result['inserted']
            all_not_found.extend([(num, item) for item in result['not_found']])
    
    print(f'\n=== GESAMT ===')
    print(f'Total SM: {total_sm}')
    print(f'Eingefuegt: {total_inserted}')
    print(f'Fehlend: {len(all_not_found)}')
