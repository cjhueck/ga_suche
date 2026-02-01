# -*- coding: utf-8 -*-
"""
Überträgt Seitenmarker (SM) von einer Quelldatei in eine Zieldatei.
Die SM werden anhand des umgebenden Textkontexts zugeordnet.
"""
import re
import os

def extract_sm_with_context(content, context_words=8):
    """
    Extrahiert alle SM mit ihrem Textkontext.
    
    Returns:
        list of dicts: [{'sm': '[|15|]', 'before': 'worte davor', 'after': 'worte danach'}]
    """
    # Entferne Block-IDs wie ^xxxxxx für die Suche
    clean_content = re.sub(r'\s*\^[a-z0-9]+\s*', ' ', content)
    
    pattern = r'(\S+(?:\s+\S+){0,' + str(context_words-1) + r'})\s*(\[\|\d+\|\])\s*(\S+(?:\s+\S+){0,' + str(context_words-1) + r'})'
    
    results = []
    for match in re.finditer(pattern, clean_content):
        before = match.group(1).strip()
        sm = match.group(2)
        after = match.group(3).strip()
        
        # Bereinige Kontext
        before = re.sub(r'\s+', ' ', before)
        after = re.sub(r'\s+', ' ', after)
        
        results.append({
            'sm': sm,
            'before': before,
            'after': after,
            'search_before': ' '.join(before.split()[-4:]),  # Letzte 4 Worte
            'search_after': ' '.join(after.split()[:4])      # Erste 4 Worte
        })
    
    return results

def transfer_sm(source_file, target_file, output_file=None):
    """
    Überträgt SM von source_file nach target_file.
    Verwendet direktes Wort-Matching mit 2 Worten vor und 2 nach dem SM.
    """
    if output_file is None:
        output_file = target_file
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(target_file, 'r', encoding='utf-8') as f:
        target_content = f.read()
    
    # Finde alle SM mit 2 Worten davor und danach
    # Pattern: Wort Wort [|XX|] Wort Wort
    pattern = r'(\S+)\s+(\S+)\s*(\[\|\d+\|\])\s*(\S+)\s+(\S+)'
    
    sm_list = []
    for match in re.finditer(pattern, source_content):
        sm_list.append({
            'w1': match.group(1),  # 2. Wort davor
            'w2': match.group(2),  # 1. Wort davor
            'sm': match.group(3),  # Der SM
            'w3': match.group(4),  # 1. Wort danach
            'w4': match.group(5),  # 2. Wort danach
        })
    
    print(f"Gefundene SM in Quelle: {len(sm_list)}")
    
    # Prüfe ob Zieldatei bereits SM hat
    existing_sm = re.findall(r'\[\|\d+\|\]', target_content)
    if existing_sm:
        print(f"WARNUNG: Zieldatei hat bereits {len(existing_sm)} SM!")
    
    result = target_content
    transferred = 0
    not_found = []
    
    for item in sm_list:
        sm = item['sm']
        w2 = item['w2']  # Wort direkt vor SM
        w3 = item['w3']  # Wort direkt nach SM
        
        # Bereinige Worte (entferne Block-IDs)
        w2_clean = re.sub(r'\^[a-z0-9]+', '', w2)
        w3_clean = re.sub(r'\^[a-z0-9]+', '', w3)
        
        # Suche: w2 gefolgt von w3 (mit optionalem Whitespace/Block-ID dazwischen)
        # Aber OHNE bereits eingefügten SM
        search_pattern = re.escape(w2_clean) + r'(\s*(?:\^[a-z0-9]+)?\s*)' + re.escape(w3_clean)
        
        match = re.search(search_pattern, result)
        
        if match:
            # Prüfe ob an dieser Stelle bereits ein SM ist
            full_match = match.group(0)
            if '[|' not in full_match:
                # Ersetze mit SM eingefügt
                replacement = w2_clean + ' ' + sm + ' ' + w3_clean
                result = result[:match.start()] + replacement + result[match.end():]
                transferred += 1
            else:
                not_found.append(item)
        else:
            not_found.append(item)
    
    print(f"Übertragen: {transferred}")
    print(f"Nicht gefunden: {len(not_found)}")
    
    # Speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\nGespeichert: {output_file}")
    
    # Statistik
    final_sm = re.findall(r'\[\|\d+\|\]', result)
    print(f"SM in Ausgabedatei: {len(final_sm)}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Verwendung: python transfer_sm.py <quelldatei> <zieldatei> [ausgabedatei]")
        sys.exit(1)
    
    source = sys.argv[1]
    target = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None
    
    transfer_sm(source, target, output)
