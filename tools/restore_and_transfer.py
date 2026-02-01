# -*- coding: utf-8 -*-
"""
Wiederherstellen der Vortraege aus der grossen Datei
und SM uebertragen OHNE Block-IDs zu entfernen
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')
big_file = os.path.join(alt_folder, 'GA203 - Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der Sternenwelt (1921).md')

# Lese grosse Datei
with open(big_file, 'r', encoding='utf-8') as f:
    big_content = f.read()

# Finde Vortrag-Ueberschriften
# Format: ## (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921
pattern = r'## \((\d+)\.\) ([A-ZÄÖÜ]+) VORTRAG[,\s]+([^\n]+)'
matches = list(re.finditer(pattern, big_content))

print(f'Gefunden: {len(matches)} Vortraege')

# Extrahiere jeden Vortrag
lectures = []
for i, m in enumerate(matches):
    num = int(m.group(1))
    title = m.group(2)
    rest = m.group(3).strip()
    
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else len(big_content)
    
    content = big_content[start:end].strip()
    lectures.append((num, title, rest, content))
    
    print(f'  Vortrag {num}: {title} VORTRAG, {rest[:30]}...')

# Schreibe jeden Vortrag in separate Datei
ordinals = {
    1: 'ERSTER', 2: 'ZWEITER', 3: 'DRITTER', 4: 'VIERTER', 5: 'FÜNFTER',
    6: 'SECHSTER', 7: 'SIEBENTER', 8: 'ACHTER', 9: 'NEUNTER', 10: 'ZEHNTER',
    11: 'ELFTER', 12: 'ZWÖLFTER', 13: 'DREIZEHNTER', 14: 'VIERZEHNTER',
    15: 'FÜNFZEHNTER', 16: 'SECHZEHNTER', 17: 'SIEBZEHNTER', 18: 'ACHTZEHNTER'
}

for num, title, rest, content in lectures:
    # Finde passende Datei
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            path = os.path.join(alt_folder, f)
            # Schreibe wiederhergestellten Inhalt
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f'Wiederhergestellt: {f}')
            break

print('\n=== Jetzt SM uebertragen ===\n')

# SM aus Quelldateien uebertragen
def extract_sm_with_context(source):
    """Extrahiere SM mit 50 Zeichen Kontext"""
    sm_list = []
    for m in re.finditer(r'\[\|(\d+)\|\]', source):
        page = int(m.group(1))
        pos = m.start()
        end = m.end()
        
        # Kontext ohne andere SM
        before = source[max(0, pos-60):pos]
        after = source[end:end+60]
        before = re.sub(r'\[\|\d+\|\]', '', before)
        after = re.sub(r'\[\|\d+\|\]', '', after)
        
        # Worttrennung?
        is_word_break = False
        if pos > 0 and end < len(source):
            if re.match(r'\w', source[pos-1]) and re.match(r'\w', source[end]):
                is_word_break = True
        
        sm_list.append({
            'page': page,
            'sm': m.group(0),
            'before': before.strip()[-40:],
            'after': after.strip()[:40],
            'is_word_break': is_word_break
        })
    return sm_list

def insert_sm_preserve(target, sm_list):
    """Fuege SM ein OHNE Block-IDs zu entfernen"""
    result = target
    inserted = 0
    
    for item in sm_list:
        sm = item['sm']
        
        # Ueberspringe wenn SM schon vorhanden
        if sm in result:
            inserted += 1
            continue
        
        before = item['before'][-25:] if len(item['before']) >= 25 else item['before']
        after = item['after'][:25] if len(item['after']) >= 25 else item['after']
        
        if not before or not after:
            # SM am Anfang
            if after:
                after_pattern = re.escape(after[:30]).replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
                match = re.search(after_pattern, result, re.IGNORECASE)
                if match:
                    result = result[:match.start()] + sm + ' ' + result[match.start():]
                    inserted += 1
            continue
        
        # Suche: before + (Block-ID?) + whitespace + after
        before_pattern = re.escape(before).replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
        after_pattern = re.escape(after).replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
        
        # Erlaube Block-ID und flexibles Whitespace dazwischen
        pattern = before_pattern + r'(\s*\^[a-z0-9]+)?\s*' + after_pattern
        
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            # Behalte Block-ID wenn vorhanden
            block_id = match.group(1) if match.group(1) else ''
            if item['is_word_break']:
                replacement = before + sm + after
            else:
                replacement = before + block_id + '\n\n' + sm + ' ' + after if block_id else before + ' ' + sm + ' ' + after
            result = result[:match.start()] + replacement + result[match.end():]
            inserted += 1
    
    return result, inserted

def get_source(num):
    for f in os.listdir(folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(folder, f)
    return None

def get_target(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

total_sm = 0
total_inserted = 0

for num in range(1, 19):
    src_path = get_source(num)
    tgt_path = get_target(num)
    
    if not src_path or not tgt_path:
        continue
    
    with open(src_path, 'r', encoding='utf-8') as f:
        source = f.read()
    with open(tgt_path, 'r', encoding='utf-8') as f:
        target = f.read()
    
    sm_list = extract_sm_with_context(source)
    result, inserted = insert_sm_preserve(target, sm_list)
    
    total_sm += len(sm_list)
    total_inserted += inserted
    
    with open(tgt_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Verifiziere Block-IDs
    block_ids = len(re.findall(r'\^[a-z0-9]+', result))
    print(f'Vortrag {num}: {inserted}/{len(sm_list)} SM, {block_ids} Block-IDs')

print(f'\n=== GESAMT ===')
print(f'SM: {total_inserted}/{total_sm}')
