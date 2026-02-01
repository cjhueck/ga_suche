# -*- coding: utf-8 -*-
"""
SM-Uebertragung mit Fuzzy Matching
- Verwendet 100+ Zeichen Kontext
- Fuzzy matching mit difflib fuer beste Uebereinstimmung
"""
import re
import os
from difflib import SequenceMatcher

def clean_text(text):
    """Entferne SM, Block-IDs, normalisiere"""
    text = re.sub(r'\[\|\d+\|\]', '', text)
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_sm_with_context(source, context_len=100):
    """Extrahiere SM mit langem Kontext (100 Zeichen vor und nach)"""
    sm_list = []
    source_clean = clean_text(source)
    
    for match in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(match.group(1))
        pos = match.start()
        
        # Position im bereinigten Text finden
        source_before_sm = source[:pos]
        clean_before = clean_text(source_before_sm)
        clean_pos = len(clean_before)
        
        # Kontext extrahieren (100 Zeichen)
        before_start = max(0, clean_pos - context_len)
        before_text = source_clean[before_start:clean_pos]
        
        after_end = min(len(source_clean), clean_pos + context_len)
        after_text = source_clean[clean_pos:after_end]
        
        # Pruefe ob Worttrennung
        is_word_break = False
        if pos > 0 and match.end() < len(source):
            char_before = source[pos-1:pos]
            char_after = source[match.end():match.end()+1]
            is_word_break = bool(re.match(r'\w', char_before) and re.match(r'\w', char_after))
        
        sm_list.append({
            'page': page,
            'sm': match.group(0),
            'before': before_text,
            'after': after_text,
            'is_word_break': is_word_break
        })
    
    return sm_list

def find_best_match(target_clean, before_text, after_text, min_ratio=0.7):
    """
    Finde die beste Uebereinstimmung fuer den Kontext im Zieltext.
    Verwendet fuzzy matching um die Position zu finden.
    """
    search_text = before_text[-50:] + after_text[:50]
    best_pos = -1
    best_ratio = 0
    
    # Sliding window durch Zieltext
    window_size = len(search_text)
    for i in range(len(target_clean) - window_size + 1):
        window = target_clean[i:i + window_size]
        ratio = SequenceMatcher(None, search_text, window).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_pos = i + len(before_text[-50:])  # Position nach "before"
    
    if best_ratio >= min_ratio:
        return best_pos, best_ratio
    return -1, 0

def insert_sm_fuzzy(target, sm_data):
    """Fuege SM mit fuzzy matching ein"""
    target_clean = clean_text(target)
    
    # Erstelle Mapping: Position in clean -> Position in original
    pos_map = []
    clean_idx = 0
    for orig_idx, char in enumerate(target):
        if not re.match(r'\s', char) or (clean_idx > 0 and target_clean[clean_idx-1:clean_idx] != ' '):
            if clean_idx < len(target_clean) and target_clean[clean_idx] == char:
                pos_map.append(orig_idx)
                clean_idx += 1
            elif re.match(r'\s', char) and clean_idx < len(target_clean) and target_clean[clean_idx] == ' ':
                pos_map.append(orig_idx)
                clean_idx += 1
    
    # Einfache Methode: Suche exakt im Original
    result = target
    inserted = 0
    not_found = []
    
    # Sortiere nach Seitenzahl rueckwaerts (von hinten einfuegen)
    sm_data_sorted = sorted(sm_data, key=lambda x: x['page'], reverse=True)
    
    for item in sm_data_sorted:
        sm = item['sm']
        before = item['before']
        after = item['after']
        
        # Erstelle Suchkontext: letzte 60 Zeichen vor + erste 60 nach
        search_before = before[-60:] if len(before) >= 60 else before
        search_after = after[:60] if len(after) >= 60 else after
        
        # Suche im bereinigten Zieltext
        result_clean = clean_text(result)
        pos, ratio = find_best_match(result_clean, search_before, search_after, min_ratio=0.75)
        
        if pos > 0:
            # Finde die Position im Original
            # Suche nach dem "before" Text
            before_search = clean_text(before[-40:])
            after_search = clean_text(after[:20])
            
            # Finde exakte Position durch Suche des Kontexts
            pattern = re.escape(before_search[-20:]) + r'\s*' + re.escape(after_search[:20])
            match = re.search(pattern, result, re.IGNORECASE)
            
            if match:
                # Pruefe ob hier schon ein SM ist
                insert_pos = match.start() + len(before_search[-20:])
                check = result[max(0, insert_pos-5):insert_pos+5]
                
                if '[|' not in check:
                    if item['is_word_break']:
                        # Bei Worttrennung: Finde genaue Position
                        # Suche das letzte Zeichen von before und erste von after
                        word_pattern = re.escape(before[-5:]) + re.escape(after[:5])
                        word_match = re.search(word_pattern, result, re.IGNORECASE)
                        if word_match:
                            insert_pos = word_match.start() + len(before[-5:])
                            result = result[:insert_pos] + sm + result[insert_pos:]
                            inserted += 1
                            continue
                    else:
                        # Normal: mit Leerzeichen
                        result = result[:insert_pos] + ' ' + sm + result[insert_pos:]
                        inserted += 1
                        continue
            
            not_found.append(item)
        else:
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
        return None
    
    print(f'\n=== Vortrag {num} ===')
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_file, 'r', encoding='utf-8') as f:
        target = f.read()
    
    # Entferne alle SM
    target_clean = re.sub(r'\[\|\d+\|\]', '', target)
    target_clean = re.sub(r'\|\d+\|', '', target_clean)
    
    # Extrahiere und fuege ein
    sm_data = extract_sm_with_context(source, context_len=100)
    result, inserted, not_found = insert_sm_fuzzy(target_clean, sm_data)
    
    print(f'  Quelle: {len(sm_data)} SM')
    print(f'  Eingefuegt: {inserted}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    if not_found:
        for item in not_found[:3]:
            print(f"    [|{item['page']}|]: ...{item['before'][-20:]}|{item['after'][:20]}...")
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    return {'num': num, 'total': len(sm_data), 'inserted': inserted, 'not_found': len(not_found)}

# Test mit Vortrag 2
if __name__ == '__main__':
    base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
    folder = None
    for item in os.listdir(base):
        if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
            folder = os.path.join(base, item)
            break
    
    alt_folder = os.path.join(folder, 'alt')
    
    # Teste nur Vortrag 2
    result = process_lecture(2, folder, alt_folder)
    
    if result:
        # Verifiziere
        target_path = os.path.join(alt_folder, 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921.md')
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sm = re.findall(r'\[\|(\d+)\|\]', content)
        pages = sorted([int(x) for x in sm])
        print(f'\nVerifikation: {len(sm)} SM gefunden')
        print(f'Seiten: {pages}')
