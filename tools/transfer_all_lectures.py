# -*- coding: utf-8 -*-
"""
Uebertrage SM von Quelldateien zu Zieldateien fuer GA203 Vortraege 2-18
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

# Mapping von Vortragsnummern zu Dateinamen
lectures = {
    2: ('ZWEITER', 'Stuttgart, 6. Januar 1921'),
    3: ('DRITTER', 'Stuttgart, 9. Januar 1921'),
    4: ('VIERTER', 'Stuttgart, 16. Januar 1921'),
    5: ('FÜNFTER', 'Dornach, 21. Januar 1921'),
    6: ('SECHSTER', 'Dornach, 22. Januar 1921'),
    7: ('SIEBENTER', 'Dornach, 23. Januar 1921'),
    8: ('ACHTER', 'Dornach, 29. Januar 1921'),
    9: ('NEUNTER', 'Dornach, 30. Januar 1921'),
    10: ('ZEHNTER', 'Dornach, 5. Februar 1921'),
    11: ('ELFTER', 'Dornach, 6. Februar 1921'),
    12: ('ZWÖLFTER', 'Dornach, 8. Februar 1921'),
    13: ('DREIZEHNTER', 'Den Haag, 27. Februar 1921'),
    14: ('VIERZEHNTER', 'Dornach, 11. März 1921'),
    15: ('FÜNFZEHNTER', 'Dornach, 13. März 1921'),
    16: ('SECHZEHNTER', 'Dornach, 27. März 1921'),
    17: ('SIEBZEHNTER', 'Dornach, 28. März 1921'),
    18: ('ACHTZEHNTER', 'Dornach, 1. April 1921'),
}

def find_file(directory, pattern):
    """Finde Datei die pattern enthaelt"""
    for f in os.listdir(directory):
        if pattern in f and f.endswith('.md'):
            return os.path.join(directory, f)
    return None

def normalize(text):
    """Entferne Block-IDs und normalisiere Whitespace"""
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_lecture(num, name, date):
    """Verarbeite einen Vortrag"""
    print(f'\n=== Vortrag {num}: {name} ===')
    
    # Finde Quelldatei (mit oder ohne -2)
    source_pattern = f'({num}.) {name}'
    source_file = None
    for f in os.listdir(folder):
        if source_pattern in f and f.endswith('.md'):
            source_file = os.path.join(folder, f)
            break
    
    if not source_file:
        print(f'  FEHLER: Quelldatei nicht gefunden')
        return None
    
    # Finde Zieldatei
    target_pattern = f'({num}.) {name}'
    target_file = None
    for f in os.listdir(alt_folder):
        if target_pattern in f and f.endswith('.md'):
            target_file = os.path.join(alt_folder, f)
            break
    
    if not target_file:
        print(f'  FEHLER: Zieldatei nicht gefunden')
        return None
    
    print(f'  Quelle: {os.path.basename(source_file)}')
    print(f'  Ziel: {os.path.basename(target_file)}')
    
    # Lese Dateien
    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(target_file, 'r', encoding='utf-8') as f:
        target = f.read()
    
    # 1. Entferne alle SM aus Zieldatei
    target_clean = re.sub(r'\[\|\d+\|\]', '', target)
    target_clean = re.sub(r'\|\d+\|', '', target_clean)
    target_clean = re.sub(r'  +', ' ', target_clean)
    
    # 2. Extrahiere SM aus Quelldatei
    # Finde alle SM mit Kontext
    sm_data = []
    
    # Pattern fuer SM mit Worttrennung (ohne Leerzeichen)
    for match in re.finditer(r'(\S+)\[\|(\d+)\|\](\S+)', source):
        sm_data.append({
            'type': 'word_break',
            'before': match.group(1),
            'page': match.group(2),
            'after': match.group(3),
            'sm': f'[|{match.group(2)}|]'
        })
    
    # Pattern fuer SM mit Leerzeichen (normal)
    for match in re.finditer(r'(\S+)\s+(\S+)\s+(\S+)\s*\[\|(\d+)\|\]\s*(\S+)\s+(\S+)\s+(\S+)', source):
        page = match.group(4)
        # Pruefe ob schon als Worttrennung erfasst
        if not any(d['page'] == page for d in sm_data):
            sm_data.append({
                'type': 'normal',
                'before3': [match.group(1), match.group(2), match.group(3)],
                'page': page,
                'after3': [match.group(5), match.group(6), match.group(7)],
                'sm': f'[|{page}|]'
            })
    
    # Sortiere nach Seitenzahl
    sm_data.sort(key=lambda x: int(x['page']))
    
    print(f'  SM in Quelle: {len(sm_data)}')
    
    # 3. Fuege SM in Zieldatei ein
    result = target_clean
    transferred = 0
    not_found = []
    
    for item in sm_data:
        sm = item['sm']
        
        if item['type'] == 'word_break':
            # Worttrennung: suche das zusammengeschriebene Wort
            word = item['before'] + item['after']
            if word in result:
                # Ersetze erstes Vorkommen
                result = result.replace(word, item['before'] + sm + item['after'], 1)
                transferred += 1
            else:
                not_found.append(item)
        else:
            # Normal: suche mit Kontext
            before = [normalize(w) for w in item['before3']]
            after = [normalize(w) for w in item['after3']]
            
            before_pattern = r'\s+'.join([re.escape(w) for w in before])
            after_pattern = r'\s+'.join([re.escape(w) for w in after])
            search = before_pattern + r'(\s+)' + after_pattern
            
            match = re.search(search, result, re.IGNORECASE | re.DOTALL)
            if match:
                before_text = ' '.join(before)
                after_text = ' '.join(after)
                replacement = before_text + ' ' + sm + ' ' + after_text
                result = result[:match.start()] + replacement + result[match.end():]
                transferred += 1
            else:
                not_found.append(item)
    
    print(f'  Uebertragen: {transferred}')
    print(f'  Nicht gefunden: {len(not_found)}')
    
    # Speichern
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Statistik
    final_sm = re.findall(r'\[\|(\d+)\|\]', result)
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
    name, date = lectures[num]
    result = process_lecture(num, name, date)
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

# Zeige nicht gefundene SM
if total_not_found > 0:
    print('\nNICHT GEFUNDENE SM:')
    for r in results:
        if r['not_found']:
            print(f"\n  Vortrag {r['num']}:")
            for item in r['not_found']:
                if item['type'] == 'word_break':
                    print(f"    {item['sm']}: {item['before']}|{item['after']}")
                else:
                    print(f"    {item['sm']}: {item['before3'][-1]} | {item['after3'][0]}")
