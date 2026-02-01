# -*- coding: utf-8 -*-
"""
Überträgt Seitenmarker (SM) von einer Quelldatei in eine Zieldatei.
Das Skript:
1. Entfernt zuerst alle vorhandenen SM im Format |X|, |XX|, |XXX| aus der Zieldatei
2. Findet die SM aus der Quelldatei anhand des umgebenden Textkontexts
3. Fügt sie an den entsprechenden Stellen in der Zieldatei ein

Verwendung:
    python transfer_sm_from_source.py <quelldatei> <zieldatei> [ausgabedatei] [--dry-run]
    
Beispiel:
    python transfer_sm_from_source.py "Quelle/GA203 (1.) ERSTER VORTRAG.md" "Ziel/GA203 (1.) ERSTER VORTRAG.md"
    
Optionen:
    --dry-run    Zeigt an, was geändert würde, ohne zu speichern
"""
import re
import os
import sys

def remove_existing_sm(content):
    """
    Entfernt alle vorhandenen Seitenmarker im Format |X|, |XX|, |XXX| aus dem Text.
    Behandelt auch SM, die mitten in Wörtern stehen können, am Zeilenanfang oder -ende.
    
    Args:
        content: Der Textinhalt
        
    Returns:
        tuple: (bereinigter_text, anzahl_entfernte_sm)
    """
    # Pattern für SM: |X|, |XX|, |XXX| (1-3 Ziffern zwischen |)
    pattern = r'\|\d{1,3}\|'
    
    # Finde alle SM
    matches = list(re.finditer(pattern, content))
    removed_count = len(matches)
    
    if removed_count == 0:
        result = content
    else:
        # Entferne SM (rückwärts, damit Positionen nicht verschoben werden)
        result = content
        for match in reversed(matches):
            start = match.start()
            end = match.end()
            
            # Prüfe Zeichen vor und nach dem SM
            before_char = result[start - 1] if start > 0 else ''
            after_char = result[end] if end < len(result) else ''
            
            # Prüfe ob SM mitten im Wort steht
            is_in_word = False
            if start > 0:
                if re.match(r'[a-zA-ZäöüÄÖÜß]', before_char):
                    if end < len(result) and re.match(r'[a-zA-ZäöüÄÖÜß]', after_char):
                        is_in_word = True
                    elif end < len(result) and result[end] not in ' \n\r\t.,;:!?)]}':
                        is_in_word = True
            
            if is_in_word:
                result = result[:start] + result[end:]
            else:
                is_after_newline = (start == 0) or (start > 0 and result[start - 1] == '\n')
                is_before_newline = (end < len(result) and result[end] == '\n')
                
                if is_after_newline and is_before_newline:
                    if start == 0:
                        result = result[end+1:]
                    else:
                        result = result[:start-1] + result[end+1:]
                elif is_after_newline:
                    if start == 0:
                        if after_char == ' ':
                            result = result[end+1:]
                        else:
                            result = result[end:]
                    else:
                        if after_char == ' ':
                            result = result[:start-1] + result[end+1:]
                        else:
                            result = result[:start-1] + result[end:]
                elif is_before_newline:
                    if before_char == ' ':
                        result = result[:start-1] + result[end:]
                    else:
                        result = result[:start] + result[end:]
                elif before_char == ' ' and after_char == ' ':
                    result = result[:start] + result[end+1:]
                elif before_char == ' ':
                    result = result[:start] + result[end:]
                elif after_char == ' ':
                    result = result[:start] + result[end:]
                else:
                    result = result[:start] + result[end:]
    
    return result, removed_count

def clean_whitespace(content):
    """
    Bereinigt Whitespace-Probleme:
    - Entfernt doppelte Leerzeichen (mehr als 1 Leerzeichen hintereinander)
    - Entfernt Leerzeichen vor Absatzbeginn (nach Zeilenumbruch)
    - Entfernt Leerzeichen am Zeilenende (vor Zeilenumbruch)
    
    Args:
        content: Der Textinhalt
        
    Returns:
        str: Bereinigter Text
    """
    result = content
    
    # Entferne doppelte Leerzeichen (2 oder mehr Leerzeichen werden zu 1)
    result = re.sub(r' {2,}', ' ', result)
    
    # Entferne Leerzeichen vor Absatzbeginn (nach Zeilenumbruch)
    result = re.sub(r'\n +', '\n', result)
    
    # Entferne Leerzeichen am Zeilenende (vor Zeilenumbruch)
    result = re.sub(r' +\n', '\n', result)
    
    # Entferne Leerzeichen am Anfang der Datei
    result = re.sub(r'^ +', '', result, flags=re.MULTILINE)
    
    return result

def extract_sm_with_context(content):
    """
    Extrahiert alle Seitenmarker mit ihrem Kontext aus dem Text.
    
    Returns:
        list of dicts: [{
            'sm': '[|15|]',
            'page': 15,
            'before': 'text davor',
            'after': 'text danach',
            'is_word_break': True/False  # SM mitten im Wort?
        }]
    """
    sm_list = []
    
    for match in re.finditer(r'\[\|(\d+)\|\]', content):
        page = int(match.group(1))
        sm = match.group(0)
        pos = match.start()
        end = match.end()
        
        # Kontext vor und nach dem SM (ca. 100 Zeichen)
        before_start = max(0, pos - 100)
        after_end = min(len(content), end + 100)
        
        before = content[before_start:pos]
        after = content[end:after_end]
        
        # Entferne andere SM aus dem Kontext für bessere Suche
        before_clean = re.sub(r'\[\|\d+\|\]', '', before)
        after_clean = re.sub(r'\[\|\d+\|\]', '', after)
        
        # Prüfe ob SM mitten im Wort steht
        is_word_break = False
        if pos > 0 and end < len(content):
            char_before = content[pos - 1]
            char_after = content[end]
            if re.match(r'\w', char_before) and re.match(r'\w', char_after):
                is_word_break = True
        
        sm_list.append({
            'sm': sm,
            'page': page,
            'before': before_clean.strip(),
            'after': after_clean.strip(),
            'is_word_break': is_word_break,
            'char_before': content[pos - 1] if pos > 0 else '',
            'char_after': content[end] if end < len(content) else ''
        })
    
    return sm_list

def normalize_text(text, for_search=False):
    """
    Normalisiert Text für Vergleich (entfernt Block-IDs, normalisiert Whitespace).
    
    Args:
        text: Der zu normalisierende Text
        for_search: Wenn True, werden auch ß/ss normalisiert und Varianten erlaubt
    """
    # Entferne Block-IDs
    text = re.sub(r'\s*\^[a-z0-9]+\s*', ' ', text)
    # Entferne leere [] Platzhalter
    text = re.sub(r'\[\s*\]', ' ', text)
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    if for_search:
        # Normalisiere ss/ß für Suche (beide Varianten werden gleich behandelt)
        text = text.replace('ß', 'ss')
        # Normalisiere auch andere häufige Unterschiede
        text = text.replace('daß', 'dass')
        text = text.replace('muß', 'muss')
    return text.strip()

def find_insertion_point(target_content, sm_item):
    """
    Findet die Stelle in der Zieldatei, wo der SM eingefügt werden soll.
    Einfache Strategie: 3-4 Wörter vor und nach dem SM mit erlaubten kleinen Fehlern.
    
    Returns:
        tuple: (insertion_pos, insertion_text) oder None
    """
    before = sm_item['before']
    after = sm_item['after']
    sm = sm_item['sm']
    is_word_break = sm_item['is_word_break']
    char_before = sm_item['char_before']
    char_after = sm_item['char_after']
    
    # Normalisiere Kontexte
    before_norm = normalize_text(before, for_search=True)
    after_norm = normalize_text(after, for_search=True)
    
    # Extrahiere 3-4 Wörter vor und nach dem SM
    before_words = before_norm.split()[-4:] if len(before_norm.split()) >= 4 else before_norm.split()
    after_words = after_norm.split()[:4] if len(after_norm.split()) >= 4 else after_norm.split()
    
    if not after_words:
        return None
    
    def create_flexible_word_pattern(word):
        """Erstellt ein Pattern für ein Wort, das auch ähnliche Varianten erlaubt."""
        # Entferne Satzzeichen am Ende des Wortes für Pattern
        word_clean = word.rstrip(',.;:!?')
        
        # Erlaube häufige Varianten: "Entwicklung" vs "Entwickelung"
        if 'Entwicklung' in word_clean:
            # Ersetze "Entwicklung" durch Pattern, das beide Varianten erlaubt
            word_pattern = word_clean.replace('Entwicklung', '(?:Entwicklung|Entwickelung)')
        elif 'Entwickelung' in word_clean:
            word_pattern = word_clean.replace('Entwickelung', '(?:Entwicklung|Entwickelung)')
        else:
            word_pattern = word_clean
        
        # Erlaube ß/ss Varianten
        word_pattern = word_pattern.replace('ss', '(?:ss|ß)').replace('ß', '(?:ss|ß)')
        
        # Erlaube auch andere häufige Varianten
        if 'Erkenntnis' in word_pattern and 'Erkenntniss' not in word_pattern:
            word_pattern = word_pattern.replace('Erkenntnis', '(?:Erkenntnis|Erkenntniss)')
        elif 'Erkenntniss' in word_pattern:
            word_pattern = word_pattern.replace('Erkenntniss', '(?:Erkenntnis|Erkenntniss)')
        
        return r'\b' + word_pattern + r'\b[,\.;:!?]*'
    
    # Spezialfall: SM mitten im Wort
    if is_word_break and char_before and char_after:
        before_word_part = before[-20:] if len(before) >= 20 else before
        before_word_match = re.search(r'\w*' + re.escape(char_before) + r'$', before_word_part)
        if before_word_match:
            word_start = before_word_match.group(0)
            char_after_pattern = char_after.replace('ß', '(ss|ß)').replace('ss', '(ss|ß)')
            pattern = re.escape(word_start) + char_after_pattern + r'\w*'
            
            for match in re.finditer(pattern, target_content, re.IGNORECASE):
                match_pos = match.start()
                check_range = target_content[max(0, match_pos-20):min(len(target_content), match_pos+len(match.group(0))+20)]
                if '[|' not in check_range or '|]' not in check_range:
                    insertion_pos = match_pos + len(word_start)
                    return (insertion_pos, sm)
    
    # Spezialfall: SM am Textanfang (keine oder sehr wenige Wörter davor)
    if not before_words or len(before.strip()) < 10:
        # Suche nur nach after_words am Anfang des Textes
        num_after = min(4, len(after_words))
        after_words_to_use = after_words[:num_after]
        
        after_pattern_parts = []
        for word in after_words_to_use:
            after_pattern_parts.append(create_flexible_word_pattern(word))
        after_pattern = r'(\s*[,\.\^][a-z0-9]*\s*)?\s+'.join(after_pattern_parts)
        
        # Suche am Anfang des Textes (erste 500 Zeichen)
        target_start = target_content[:500]
        match = re.search(after_pattern, target_start, re.IGNORECASE)
        
        if match:
            insertion_pos = match.start()
            # Prüfe ob bereits SM vorhanden
            check_range = target_content[max(0, insertion_pos-30):min(len(target_content), insertion_pos+30)]
            if '[|' not in check_range or '|]' not in check_range:
                if is_word_break:
                    return (insertion_pos, sm)
                else:
                    return (insertion_pos, sm + ' ')
    
    if not before_words:
        return None
    
    # Verwende mehrere Wörter für eindeutigere Suche
    # Letzte 3-4 Wörter vor SM und erste 3-4 Wörter nach SM
    num_before = min(4, len(before_words))
    num_after = min(4, len(after_words))
    
    before_words_to_use = before_words[-num_before:]
    after_words_to_use = after_words[:num_after]
    
    # Erstelle Pattern für before_words (erlaube ß/ss Varianten und andere Varianten)
    # Erlaube flexible Abstände zwischen Wörtern (Whitespace, Kommas, Block-IDs, etc.)
    before_pattern_parts = []
    for word in before_words_to_use:
        before_pattern_parts.append(create_flexible_word_pattern(word))
    # Erlaube Whitespace, Kommas, Block-IDs zwischen Wörtern
    before_pattern = r'(\s*[,\.\^][a-z0-9]*\s*)?\s+'.join(before_pattern_parts)
    
    # Erstelle Pattern für after_words (erlaube ß/ss Varianten und andere Varianten)
    after_pattern_parts = []
    for word in after_words_to_use:
        after_pattern_parts.append(create_flexible_word_pattern(word))
    # Erlaube Whitespace, Kommas, Block-IDs zwischen Wörtern
    after_pattern = r'(\s*[,\.\^][a-z0-9]*\s*)?\s+'.join(after_pattern_parts)
    
    # Kombiniertes Pattern: before_words ... after_words
    # Erlaube Whitespace, Block-IDs, Punkte, Kommas dazwischen
    pattern = before_pattern + r'(\s*[,\.\^][a-z0-9]*\s*)?\s+' + after_pattern
    
    candidates = []
    
    for match in re.finditer(pattern, target_content, re.IGNORECASE):
        # Finde die genaue Position des ersten Wortes nach SM
        match_text = target_content[match.start():match.end()]
        first_after_word = after_words_to_use[0].replace('ss', '(ss|ß)').replace('ß', '(ss|ß)')
        first_word_match = re.search(r'\b' + re.escape(first_after_word) + r'\b', match_text, re.IGNORECASE)
        
        if first_word_match:
            insertion_pos = match.start() + first_word_match.start()
        else:
            # Fallback: Position nach dem before_pattern
            insertion_pos = match.start() + len(before_pattern)
        
        # Prüfe ob bereits SM vorhanden
        check_range = target_content[max(0, insertion_pos-30):min(len(target_content), insertion_pos+30)]
        if '[|' in check_range and '|]' in check_range:
            continue
        
        # Score basierend auf Anzahl der gefundenen Wörter
        score = num_before + num_after
        
        candidates.append((insertion_pos, score))
    
    if candidates:
        # Sortiere nach Score (beste Übereinstimmung zuerst)
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_pos = candidates[0][0]
        
        if is_word_break:
            return (best_pos, sm)
        else:
            # Prüfe ob Block-ID davor ist
            block_id_match = re.search(r'\^[a-z0-9]+', target_content[max(0, best_pos-50):best_pos])
            if block_id_match:
                block_id_end = best_pos - 50 + block_id_match.end()
                # Prüfe ob nach dem SM ein Absatzbeginn kommt (best_pos zeigt auf Großbuchstabe)
                # best_pos ist die Position des ersten Wortes nach dem SM
                # Schaue nach dem ersten nicht-Whitespace-Zeichen an best_pos
                text_after = target_content[best_pos:min(len(target_content), best_pos+20)]
                # Wenn nach dem SM ein Großbuchstabe kommt, füge Leerzeile ein
                if re.match(r'\s*[A-ZÄÖÜ]', text_after):
                    return (block_id_end, ' ' + sm + '\n\n')
                return (block_id_end, ' ' + sm + ' ')
            # Prüfe auch wenn keine Block-ID direkt davor ist, ob nach dem SM ein Absatzbeginn kommt
            text_after = target_content[best_pos:min(len(target_content), best_pos+20)]
            if re.match(r'\s*[A-ZÄÖÜ]', text_after):
                # Prüfe ob direkt vor dem SM eine Block-ID ist (in größerem Bereich)
                block_id_match = re.search(r'\^[a-z0-9]+\s*$', target_content[max(0, best_pos-100):best_pos])
                if block_id_match:
                    block_id_end = best_pos - 100 + block_id_match.end()
                    return (block_id_end, ' ' + sm + '\n\n')
            return (best_pos, ' ' + sm + ' ')
    
    return None

def transfer_sm(source_file, target_file, output_file=None, dry_run=False):
    """
    Überträgt Seitenmarker von source_file nach target_file.
    
    Args:
        source_file: Pfad zur Quelldatei mit SM
        target_file: Pfad zur Zieldatei ohne SM
        output_file: Pfad zur Ausgabedatei (default: target_file wird überschrieben)
        dry_run: Wenn True, werden keine Änderungen gespeichert
    """
    if not os.path.exists(source_file):
        print(f"Fehler: Quelldatei nicht gefunden: {source_file}")
        return False
    
    if not os.path.exists(target_file):
        print(f"Fehler: Zieldatei nicht gefunden: {target_file}")
        return False
    
    # Lese Dateien
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(target_file, 'r', encoding='utf-8') as f:
        target_content = f.read()
    
    # Entferne vorhandene SM aus Zieldatei (Format: |X|, |XX|, |XXX|)
    print("Bereinige Zieldatei...")
    target_content, removed_count = remove_existing_sm(target_content)
    if removed_count > 0:
        print(f"  Entfernt: {removed_count} Seitenmarker (Format: |X|, |XX|, |XXX|)")
    else:
        print("  Keine vorhandenen Seitenmarker gefunden")
    
    # Entferne leere [] Platzhalter (auch mehrfache aufeinanderfolgende)
    empty_placeholders = len(re.findall(r'\[\s*\]', target_content))
    if empty_placeholders > 0:
        # Entferne alle leeren [] Platzhalter (auch mehrfache)
        target_content = re.sub(r'\[\s*\]\s*', '', target_content)
        target_content = re.sub(r'\[\s*\]', '', target_content)  # Nochmal für sicher
        print(f"  Entfernt: {empty_placeholders} leere [] Platzhalter")
    
    # Bereinige Whitespace
    target_content = clean_whitespace(target_content)
    print("  Whitespace bereinigt (doppelte Leerzeichen, Leerzeichen vor Absätzen)")
    
    # Prüfe ob Zieldatei bereits SM im Format [|XX|] hat
    existing_sm = re.findall(r'\[\|\d+\|\]', target_content)
    if existing_sm:
        print(f"Warnung: Zieldatei hat bereits {len(existing_sm)} Seitenmarker im Format [|XX|]!")
        if not dry_run:
            response = input("Fortfahren und überschreiben? (j/n): ")
            if response.lower() != 'j':
                return False
    
    # Extrahiere SM aus Quelle
    sm_list = extract_sm_with_context(source_content)
    print(f"\nGefundene Seitenmarker in Quelle: {len(sm_list)}")
    
    # Übertrage SM
    result = target_content
    transferred = 0
    not_found = []
    inserted_positions = set()  # Track bereits eingefügte Positionen
    
    # Sortiere SM nach Position (rückwärts, damit Einfügungen die Positionen nicht verschieben)
    sm_list_sorted = sorted(sm_list, key=lambda x: x['page'], reverse=True)
    
    for sm_item in sm_list_sorted:
        sm = sm_item['sm']
        page = sm_item['page']
        
        # Prüfe ob SM bereits vorhanden
        if sm in result:
            transferred += 1
            continue
        
        # Finde Einfügepunkt
        insertion = find_insertion_point(result, sm_item)
        
        if insertion:
            pos, insert_text = insertion
            
            # Prüfe ob bereits ein SM an dieser Position oder in der Nähe vorhanden ist
            check_range = result[max(0, pos-15):min(len(result), pos+15)]
            if re.search(r'\[\|\d+\|\]', check_range):
                # SM bereits vorhanden, überspringe
                not_found.append(sm_item)
                print(f"  FEHLT {sm} nicht eingefuegt - bereits SM vorhanden (Seite {page})")
                continue
            
            # Prüfe ob Position bereits verwendet wurde (verhindert doppelte Einfügungen)
            if pos in inserted_positions:
                not_found.append(sm_item)
                print(f"  FEHLT {sm} nicht eingefuegt - Position bereits verwendet (Seite {page})")
                continue
            
            result = result[:pos] + insert_text + result[pos:]
            inserted_positions.add(pos)
            
            # Wenn insert_text mit \n\n endet (Leerzeile nach SM), entferne alle zusätzlichen Leerzeilen danach
            if insert_text.endswith('\n\n'):
                # Finde Position nach dem eingefügten Text
                text_end_pos = pos + len(insert_text)
                # Entferne alle Leerzeilen nach dem SM (behalte nur eine)
                text_after = result[text_end_pos:]
                # Entferne alle Leerzeilen am Anfang von text_after
                text_after_cleaned = re.sub(r'^\n+', '\n', text_after)
                result = result[:text_end_pos] + text_after_cleaned
            
            # Entferne leere [] Platzhalter in der Nähe des eingefügten SM
            check_start = max(0, pos - 60)
            check_end = min(len(result), pos + len(insert_text) + 60)
            check_area = result[check_start:check_end]
            if '[]' in check_area:
                before = result[:check_start]
                area = result[check_start:check_end]
                after = result[check_end:]
                area = re.sub(r'\[\s*\]\s*', '', area)
                area = re.sub(r'\[\s*\]', '', area)
                result = before + area + after
            
            transferred += 1
            print(f"  OK {sm} eingefuegt (Seite {page})")
        else:
            not_found.append(sm_item)
            print(f"  FEHLT {sm} nicht gefunden (Seite {page})")
    
    # Entferne alle verbleibenden leeren [] Platzhalter
    result = re.sub(r'\[\s*\]\s*', '', result)
    result = re.sub(r'\[\s*\]', '', result)
    while '[][]' in result:
        result = result.replace('[][]', '')
    
    # Finale Whitespace-Bereinigung nach dem Einfügen der SM
    result = clean_whitespace(result)
    
    # Statistik
    print(f"\n=== Zusammenfassung ===")
    print(f"Gefunden in Quelle: {len(sm_list)}")
    print(f"Übertragen: {transferred}")
    print(f"Nicht gefunden: {len(not_found)}")
    
    if not_found:
        print(f"\nNicht gefundene SM:")
        for item in not_found[:10]:  # Zeige nur erste 10
            print(f"  {item['sm']}: ...{item['before'][-30:]} | {item['after'][:30]}...")
        if len(not_found) > 10:
            print(f"  ... und {len(not_found) - 10} weitere")
    
    # Speichern
    if not dry_run:
        if output_file is None:
            output_file = target_file
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"\nGespeichert: {output_file}")
        
        # Verifiziere
        final_sm = re.findall(r'\[\|\d+\|\]', result)
        print(f"Seitenmarker in Ausgabedatei: {len(final_sm)}")
    else:
        print("\n(Dry-Run: Keine Änderungen gespeichert)")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nVerwendung:")
        print("  python transfer_sm_from_source.py <quelldatei> <zieldatei> [ausgabedatei]")
        print("\nOptionen:")
        print("  --dry-run    Zeigt an, was geändert würde, ohne zu speichern")
        sys.exit(1)
    
    source = sys.argv[1]
    target = sys.argv[2]
    output = None
    dry_run = False
    
    # Parse Argumente
    args = sys.argv[3:]
    for i, arg in enumerate(args):
        if arg == '--dry-run':
            dry_run = True
        elif not arg.startswith('--'):
            output = arg
    
    transfer_sm(source, target, output, dry_run)
