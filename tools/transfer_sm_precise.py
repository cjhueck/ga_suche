# -*- coding: utf-8 -*-
"""
Praezise SM-Uebertragung mit langem Kontext
- Verwendet 50+ Zeichen Kontext vor und nach SM
- Entfernt Sonderzeichen fuer robusteres Matching
"""
import re
import os

def clean_for_matching(text):
    """Entferne SM, Block-IDs und normalisiere fuer Matching"""
    text = re.sub(r'\[\|\d+\|\]', '', text)  # SM entfernen
    text = re.sub(r'\^[a-z0-9]+', '', text)   # Block-IDs entfernen
    text = re.sub(r'\s+', ' ', text)          # Whitespace normalisieren
    return text

def extract_sm_with_long_context(source):
    """Extrahiere SM mit langem Kontext (50 Zeichen)"""
    sm_list = []
    
    # Finde alle SM
    for match in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(match.group(1))
        pos = match.start()
        
        # Kontext vor SM (50 Zeichen, aber stoppe bei Absatz)
        before_start = max(0, pos - 80)
        before_text = source[before_start:pos]
        # Nimm nur nach letztem Absatz
        if '\n\n' in before_text:
            before_text = before_text.split('\n\n')[-1]
        before_text = clean_for_matching(before_text).strip()[-50:]
        
        # Kontext nach SM (50 Zeichen)
        after_end = min(len(source), match.end() + 80)
        after_text = source[match.end():after_end]
        if '\n\n' in after_text:
            after_text = after_text.split('\n\n')[0]
        after_text = clean_for_matching(after_text).strip()[:50]
        
        sm_list.append({
            'page': page,
            'sm': match.group(0),
            'before': before_text,
            'after': after_text,
            'is_word_break': bool(re.match(r'\w$', before_text) and re.match(r'^\w', after_text) and not before_text.endswith(' ') and not after_text.startswith(' '))
        })
    
    return sm_list

def insert_sm_precise(target, sm_data):
    """Fuege SM praezise in Zieldatei ein"""
    result = target
    inserted = 0
    not_found = []
    
    # Bereite Zieldatei fuer Matching vor
    target_clean = clean_for_matching(target)
    
    for item in sm_data:
        sm = item['sm']
        before = item['before']
        after = item['after']
        
        # Suche den exakten Kontext
        # Erstelle Suchmuster: before + after (ohne SM dazwischen)
        if len(before) < 10 or len(after) < 10:
            not_found.append(item)
            continue
        
        # Escape fuer Regex
        before_esc = re.escape(before[-30:]) if len(before) >= 30 else re.escape(before)
        after_esc = re.escape(after[:30]) if len(after) >= 30 else re.escape(after)
        
        # Suche in bereinigtem Ziel
        pattern = before_esc + r'\s*' + after_esc
        match = re.search(pattern, target_clean, re.IGNORECASE)
        
        if match:
            # Finde die Position im Original
            # Suche den before-Text im Original
            before_pattern = re.escape(before[-20:])
            
            # Suche im Original-Target
            for orig_match in re.finditer(before_pattern, result, re.IGNORECASE):
                # Pruefe ob hier noch kein SM ist
                check_area = result[orig_match.end():orig_match.end()+20]
                if '[|' not in check_area:
                    # Hier einfuegen
                    if item['is_word_break']:
                        # Worttrennung - kein Leerzeichen
                        new_result = result[:orig_match.end()] + sm + result[orig_match.end():]
                    else:
                        # Normal - mit Leerzeichen
                        new_result = result[:orig_match.end()] + ' ' + sm + ' ' + result[orig_match.end():]
                    
                    result = new_result
                    inserted += 1
                    break
            else:
                not_found.append(item)
        else:
            not_found.append(item)
    
    return result, inserted, not_found

def process_lecture(source_path, target_path):
    """Verarbeite einen Vortrag"""
    print(f'\nQuelle: {os.path.basename(source_path)}')
    print(f'Ziel: {os.path.basename(target_path)}')
    
    with open(source_path, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_path, 'r', encoding='utf-8') as f:
        target = f.read()
    
    # 1. Entferne alle SM aus Zieldatei
    target_clean = re.sub(r'\[\|\d+\|\]', '', target)
    target_clean = re.sub(r'\|\d+\|', '', target_clean)
    target_clean = re.sub(r'  +', ' ', target_clean)
    
    # 2. Extrahiere SM aus Quelle
    sm_data = extract_sm_with_long_context(source)
    print(f'SM in Quelle: {len(sm_data)}')
    
    # 3. Fuege SM ein
    result, inserted, not_found = insert_sm_precise(target_clean, sm_data)
    
    print(f'Eingefuegt: {inserted}')
    print(f'Nicht gefunden: {len(not_found)}')
    
    if not_found:
        for item in not_found[:5]:
            print(f"  [|{item['page']}|]: ...{item['before'][-20:]}|{item['after'][:20]}...")
    
    # 4. Speichern
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Pruefe Ergebnis
    final_sm = re.findall(r'\[\|\d+\|\]', result)
    print(f'SM in Ergebnis: {len(final_sm)}')
    
    return inserted, len(not_found)

# Test mit Vortrag 2
if __name__ == '__main__':
    base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
    folder = None
    for item in os.listdir(base):
        if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
            folder = os.path.join(base, item)
            break
    
    source = os.path.join(folder, 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921-2.md')
    target = os.path.join(folder, 'alt', 'GA203 (2.) ZWEITER VORTRAG, Stuttgart, 6. Januar 1921.md')
    
    process_lecture(source, target)
