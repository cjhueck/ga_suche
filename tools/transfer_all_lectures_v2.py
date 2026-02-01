# -*- coding: utf-8 -*-
"""
Verbesserte SM-Uebertragung fuer GA203 Vortraege 2-18
- Block-IDs werden ignoriert
- Flexible Worttrennung-Suche
- Umlaut-tolerante Suche
- Kuerzerer Kontext (1 Wort)
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

lectures = {
    2: 'ZWEITER', 3: 'DRITTER', 4: 'VIERTER', 5: 'FÜNFTER',
    6: 'SECHSTER', 7: 'SIEBENTER', 8: 'ACHTER', 9: 'NEUNTER',
    10: 'ZEHNTER', 11: 'ELFTER', 12: 'ZWÖLFTER', 13: 'DREIZEHNTER',
    14: 'VIERZEHNTER', 15: 'FÜNFZEHNTER', 16: 'SECHZEHNTER',
    17: 'SIEBZEHNTER', 18: 'ACHTZEHNTER',
}

def clean_text(text):
    """Entferne Block-IDs, Bilder, und normalisiere"""
    text = re.sub(r'\^[a-z0-9]+', '', text)  # Block-IDs
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Bilder
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_umlaut(text):
    """Normalisiere Umlaute fuer flexiblere Suche"""
    replacements = {
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
        'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        'ae': 'a', 'oe': 'o', 'ue': 'u',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def find_source_file(folder, num, name):
    """Finde Quelldatei"""
    pattern = f'({num}.) {name}'
    for f in os.listdir(folder):
        if pattern in f and f.endswith('.md'):
            return os.path.join(folder, f)
    # Fallback: suche mit Nummer
    for f in os.listdir(folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(folder, f)
    return None

def find_target_file(alt_folder, num, name):
    """Finde Zieldatei"""
    pattern = f'({num}.) {name}'
    for f in os.listdir(alt_folder):
        if pattern in f and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

def extract_sm_data(source):
    """Extrahiere alle SM mit verschiedenen Kontexten"""
    sm_data = []
    
    # 1. Worttrennungen (ohne Leerzeichen): wort1[|XX|]wort2
    for match in re.finditer(r'(\S*?)(\[\|\d+\|\])(\S*)', source):
        before = match.group(1)
        sm = match.group(2)
        after = match.group(3)
        page = re.search(r'\d+', sm).group()
        
        # Nur echte Worttrennungen (beide Teile haben Buchstaben)
        if before and after and re.search(r'[a-zA-ZäöüÄÖÜß]', before) and re.search(r'[a-zA-ZäöüÄÖÜß]', after):
            sm_data.append({
                'type': 'word_break',
                'before': before,
                'after': after,
                'page': int(page),
                'sm': sm,
                'full_match': match.group(0)
            })
    
    # 2. Normale SM mit Kontext
    # Finde SM die nicht Teil einer Worttrennung sind
    for match in re.finditer(r'(\S+)\s+(\[\|\d+\|\])\s+(\S+)', source):
        word_before = match.group(1)
        sm = match.group(2)
        word_after = match.group(3)
        page = int(re.search(r'\d+', sm).group())
        
        # Pruefe ob schon als Worttrennung erfasst
        if not any(d['page'] == page for d in sm_data):
            sm_data.append({
                'type': 'normal',
                'before': clean_text(word_before),
                'after': clean_text(word_after),
                'page': page,
                'sm': sm
            })
    
    # Sortiere nach Seitenzahl
    sm_data.sort(key=lambda x: x['page'])
    return sm_data

def insert_sm(result, item):
    """Versuche SM einzufuegen mit verschiedenen Strategien"""
    sm = item['sm']
    
    if item['type'] == 'word_break':
        # Strategie 1: Suche zusammengeschriebenes Wort
        word = item['before'] + item['after']
        if word in result:
            return result.replace(word, item['before'] + sm + item['after'], 1), True
        
        # Strategie 2: Normalisierte Suche (ohne Umlaute)
        word_norm = normalize_umlaut(word)
        for match in re.finditer(r'\b\w+\b', result):
            if normalize_umlaut(match.group()) == word_norm:
                orig_word = match.group()
                # Finde Trennposition
                split_pos = len(item['before'])
                if split_pos < len(orig_word):
                    new_word = orig_word[:split_pos] + sm + orig_word[split_pos:]
                    return result.replace(orig_word, new_word, 1), True
        
        # Strategie 3: Suche Wortteile separat mit flexiblem Abstand
        before_clean = clean_text(item['before'])
        after_clean = clean_text(item['after'])
        if len(before_clean) >= 2 and len(after_clean) >= 2:
            pattern = re.escape(before_clean) + r'\s*' + re.escape(after_clean)
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                replacement = before_clean + sm + after_clean
                return result[:match.start()] + replacement + result[match.end():], True
        
        return result, False
    
    else:  # normal
        before = item['before']
        after = item['after']
        
        # Strategie 1: Exakte Suche
        pattern = re.escape(before) + r'\s+' + re.escape(after)
        match = re.search(pattern, result)
        if match:
            replacement = before + ' ' + sm + ' ' + after
            return result[:match.start()] + replacement + result[match.end():], True
        
        # Strategie 2: Case-insensitive
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            # Behalte Originalschreibweise
            orig = match.group()
            parts = re.split(r'\s+', orig)
            if len(parts) >= 2:
                replacement = parts[0] + ' ' + sm + ' ' + parts[1]
                return result[:match.start()] + replacement + result[match.end():], True
        
        # Strategie 3: Normalisierte Suche
        before_norm = normalize_umlaut(before)
        after_norm = normalize_umlaut(after)
        result_norm = normalize_umlaut(result)
        pattern_norm = re.escape(before_norm) + r'\s+' + re.escape(after_norm)
        match_norm = re.search(pattern_norm, result_norm, re.IGNORECASE)
        if match_norm:
            # Finde Position im Original
            start = match_norm.start()
            # Suche naechstes passendes Wortpaar ab dieser Position
            pattern_flex = r'(\S+)\s+(\S+)'
            for m in re.finditer(pattern_flex, result[start:start+100]):
                w1, w2 = m.group(1), m.group(2)
                if normalize_umlaut(w1).lower() == before_norm.lower():
                    pos = start + m.start()
                    replacement = w1 + ' ' + sm + ' ' + w2
                    return result[:pos] + replacement + result[pos+m.end():], True
        
        return result, False

def process_lecture(num, name):
    """Verarbeite einen Vortrag"""
    print(f'\n=== Vortrag {num}: {name} ===')
    
    source_file = find_source_file(folder, num, name)
    target_file = find_target_file(alt_folder, num, name)
    
    if not source_file or not target_file:
        print(f'  FEHLER: Dateien nicht gefunden')
        return None
    
    print(f'  Quelle: {os.path.basename(source_file)}')
    print(f'  Ziel: {os.path.basename(target_file)}')
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_file, 'r', encoding='utf-8') as f:
        target = f.read()
    
    # 1. Entferne alle SM aus Zieldatei
    target_clean = re.sub(r'\[\|\d+\|\]', '', target)
    target_clean = re.sub(r'\|\d+\|', '', target_clean)
    target_clean = re.sub(r'  +', ' ', target_clean)
    
    # 2. Extrahiere SM aus Quelldatei
    sm_data = extract_sm_data(source)
    print(f'  SM in Quelle: {len(sm_data)}')
    
    # 3. Fuege SM ein
    result = target_clean
    transferred = 0
    not_found = []
    
    for item in sm_data:
        result, success = insert_sm(result, item)
        if success:
            transferred += 1
        else:
            not_found.append(item)
    
    print(f'  Uebertragen: {transferred}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    # Speichern
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    final_sm = re.findall(r'\[\|\d+\|\]', result)
    print(f'  SM in Ergebnis: {len(final_sm)}')
    
    return {
        'num': num,
        'source_sm': len(sm_data),
        'transferred': transferred,
        'not_found': not_found,
        'final_sm': len(final_sm)
    }

# Hauptprogramm
results = []
for num in range(2, 19):
    name = lectures[num]
    result = process_lecture(num, name)
    if result:
        results.append(result)

# Zusammenfassung
print('\n' + '='*50)
print('ZUSAMMENFASSUNG')
print('='*50)
total_source = sum(r['source_sm'] for r in results)
total_transferred = sum(r['transferred'] for r in results)
total_not_found = sum(len(r['not_found']) for r in results)
total_final = sum(r['final_sm'] for r in results)

print(f'SM in Quellen: {total_source}')
print(f'Uebertragen: {total_transferred}')
print(f'Nicht gefunden: {total_not_found}')
print(f'SM in Ergebnissen: {total_final}')

if total_not_found > 0:
    print('\nNICHT GEFUNDENE SM:')
    for r in results:
        if r['not_found']:
            print(f"\n  Vortrag {r['num']}:")
            for item in r['not_found']:
                print(f"    [|{item['page']}|]: {item['before']} | {item['after']}")
