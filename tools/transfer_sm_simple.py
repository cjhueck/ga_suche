# -*- coding: utf-8 -*-
"""
Einfache SM-Uebertragung:
1. Extrahiere 30-40 Zeichen vor und nach SM aus Quelle
2. Suche "before + after" in Ziel
3. Fuege SM dazwischen ein
"""
import re
import os

def clean_text(text):
    """Entferne SM und Block-IDs"""
    text = re.sub(r'\[\|\d+\|\]', '', text)
    text = re.sub(r'\^[a-z0-9]+', '', text)
    return text

def extract_sm_contexts(source):
    """Extrahiere SM mit 40 Zeichen Kontext vor und nach"""
    sm_list = []
    source_clean = clean_text(source)
    
    for match in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(match.group(1))
        pos = match.start()
        
        # Berechne Position im bereinigten Text
        before_source = source[:pos]
        before_clean = clean_text(before_source)
        clean_pos = len(before_clean)
        
        # Extrahiere 40 Zeichen vor und nach
        before_text = source_clean[max(0, clean_pos-40):clean_pos]
        after_text = source_clean[clean_pos:clean_pos+40]
        
        # Pruefe Worttrennung
        is_word_break = False
        if pos > 0 and match.end() < len(source):
            char_before = source[pos-1]
            char_after = source[match.end()]
            is_word_break = bool(re.match(r'\w', char_before) and re.match(r'\w', char_after))
        
        sm_list.append({
            'page': page,
            'sm': match.group(0),
            'before': before_text.strip(),
            'after': after_text.strip(),
            'is_word_break': is_word_break
        })
    
    return sm_list

def insert_sm_simple(target, sm_list):
    """Einfache Suche und Ersetzung"""
    result = clean_text(target)  # Entferne existierende SM
    inserted = 0
    not_found = []
    
    for item in sm_list:
        before = item['before']
        after = item['after']
        sm = item['sm']
        
        # Suche: before + whitespace + after
        # Verwende die letzten 25 Zeichen von before und ersten 25 von after
        search_before = before[-25:] if len(before) >= 25 else before
        search_after = after[:25] if len(after) >= 25 else after
        
        # Escape fuer Regex und erlaube flexibles Whitespace
        pattern = re.escape(search_before) + r'\s*' + re.escape(search_after)
        
        match = re.search(pattern, result, re.IGNORECASE)
        
        if match:
            # Gefunden! Ersetze mit SM dazwischen
            if item['is_word_break']:
                # Worttrennung: kein Leerzeichen
                replacement = search_before + sm + search_after
            else:
                # Normal: mit Leerzeichen
                replacement = search_before + ' ' + sm + ' ' + search_after
            
            result = result[:match.start()] + replacement + result[match.end():]
            inserted += 1
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
    
    sm_list = extract_sm_contexts(source)
    result, inserted, not_found = insert_sm_simple(target, sm_list)
    
    print(f'  Quelle: {len(sm_list)} SM')
    print(f'  Eingefuegt: {inserted}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    for item in not_found:
        print(f"    [|{item['page']}|]: '{item['before'][-20:]}' | '{item['after'][:20]}'")
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Verifiziere
    final_sm = re.findall(r'\[\|(\d+)\|\]', result)
    pages = sorted([int(x) for x in final_sm])
    print(f'  Ergebnis: {len(final_sm)} SM - Seiten: {pages}')
    
    return {'num': num, 'inserted': inserted, 'not_found': not_found}

# Test mit Vortrag 2
if __name__ == '__main__':
    base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
    folder = None
    for item in os.listdir(base):
        if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
            folder = os.path.join(base, item)
            break
    
    alt_folder = os.path.join(folder, 'alt')
    process_lecture(2, folder, alt_folder)
