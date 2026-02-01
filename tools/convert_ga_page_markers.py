# -*- coding: utf-8 -*-
"""
Universelles Skript zur Umwandlung von CR-Umbrüchen in Seitenmarker (SM) für alle GA-Bände.

Verwendung:
    python convert_ga_page_markers.py <pfad_zur_md_datei>

Regeln:
1. JEDER "---" = Seitenumbruch -> current_page += 1, SM für nächsten Text
2. "Copyright...Seite: XX" = Validierung/Korrektur von current_page auf XX
3. SM-Format: [|XX|] wobei XX = Seitenzahl
4. SM-Positionierung:
   - Fall 1 (Absatz): Nach Satzende (.!?:) + Großbuchstabe -> neuer Absatz mit SM
   - Fall 2 (Inline): Kein Satzende -> SM inline mit Leerzeichen
   - Fall 3 (Worttrennung): Bindestrich am Ende -> SM ohne Leerzeichen
5. Bei Überschriften (#): SM nach Überschrift + Datum, vor erstem Text
"""
import sys
import os
import re
from collections import Counter
from datetime import datetime

def is_heading(text):
    """Prüft ob Text eine Überschrift ist."""
    return text.strip().startswith('#')

def is_h1_heading(text):
    """Prüft ob Text eine H1-Überschrift ist (nur ein #)."""
    stripped = text.strip()
    return stripped.startswith('# ') and not stripped.startswith('## ')

def is_date_line(text):
    """Prüft ob Text eine Datum-Zeile ist (z.B. 'Stuttgart, 6. Januar 1921')."""
    text = text.strip()
    if re.match(r'^[A-ZÄÖÜ][a-zäöüß]+,?\s+\d{1,2}\.\s+\w+\s+\d{4}', text):
        return True
    return False

def merge_h1_with_date(content):
    """
    Verschiebt Ort- und Datumszeilen nach H1-Überschriften in die Überschrift.
    
    Aus:
        # ERSTER VORTRAG
        
        Stuttgart, 16. Juni 1921
    
    Wird:
        # ERSTER VORTRAG, Stuttgart, 16. Juni 1921
    """
    # Pattern: H1-Überschrift, gefolgt von Leerzeilen und Datum-Zeile
    # Datum-Pattern: Ort, Tag. Monat Jahr
    pattern = r'^(# [^\n]+)\n\n+([A-ZÄÖÜ][a-zäöüß]+,?\s+\d{1,2}\.\s+\w+\s+\d{4})(\n|$)'
    
    def replace_func(m):
        heading = m.group(1).rstrip()
        date_line = m.group(2).strip()
        ending = m.group(3)
        return f'{heading}, {date_line}{ending}'
    
    result = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
    return result

def is_copyright_line(text):
    """Prüft ob Text eine Copyright-Zeile ist."""
    return bool(re.search(r'[Cc]opyright Rudolf Steiner', text))

def extract_page_number(copyright_text):
    """Extrahiert die Seitenzahl aus einer Copyright-Zeile."""
    match = re.search(r'Seite:\s*(\d[\d\s]*)', copyright_text)
    if match:
        return int(match.group(1).replace(' ', ''))
    return None

def analyze_blocks(blocks):
    """
    Analysiert alle Blöcke und klassifiziert sie.
    
    Returns:
        list of dicts mit:
        - block: Der Textblock
        - type: 'copyright', 'divider', 'heading', 'date', 'text'
        - copyright_page: Seitenzahl aus Copyright-Zeile (oder None)
    """
    analyzed = []
    for i, block in enumerate(blocks):
        block_stripped = block.strip()
        info = {
            'index': i,
            'block': block_stripped,
            'type': 'text',
            'copyright_page': None
        }
        
        if not block_stripped:
            info['type'] = 'empty'
        elif is_copyright_line(block_stripped):
            info['type'] = 'copyright'
            info['copyright_page'] = extract_page_number(block_stripped)
        elif block_stripped == '---':
            info['type'] = 'divider'
        elif is_heading(block_stripped):
            info['type'] = 'heading'
        elif is_date_line(block_stripped):
            info['type'] = 'date'
        
        analyzed.append(info)
    
    return analyzed

def convert_page_markers(input_file, output_file=None, backup=True):
    """
    Konvertiert CR-Umbrüche in Seitenmarker.
    """
    if output_file is None:
        output_file = input_file
    
    # Log-Datei im selben Verzeichnis
    log_file = input_file.replace('.md', '_conversion.log')
    conflicts = []
    missing = []
    
    # Backup erstellen
    if backup and os.path.exists(input_file):
        backup_file = input_file.replace('.md', '_backup.md')
        if not os.path.exists(backup_file):
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Backup erstellt: {backup_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Teile den Text in Blöcke (getrennt durch Leerzeilen)
    blocks = re.split(r'\n\n+', content)
    
    # Analysiere Blöcke bidirektional
    analyzed = analyze_blocks(blocks)
    
    # Statistiken
    stats = {'fall1': 0, 'fall2': 0, 'fall3': 0, 'heading': 0, 'copyright_removed': 0, 'conflicts': 0}
    
    # Verarbeite die Blöcke
    output_blocks = []
    current_page = 0
    pending_sm = None
    last_used_sm = None
    
    i = 0
    while i < len(analyzed):
        info = analyzed[i]
        block = info['block']
        
        # Leerer Block
        if info['type'] == 'empty':
            i += 1
            continue
        
        # Copyright-Zeile - validiert current_page, entfernen
        if info['type'] == 'copyright':
            page = info['copyright_page']
            if page is not None:
                # Copyright X erscheint am Ende von Seite X
                # Wenn current_page != page, gibt es eine Abweichung
                if current_page != page and current_page > 0:
                    conflicts.append({
                        'type': 'validation',
                        'expected': current_page,
                        'found': page,
                        'text': block[:60]
                    })
                # Korrigiere current_page auf den Copyright-Wert
                current_page = page
            
            stats['copyright_removed'] += 1
            i += 1
            continue
        
        # Divider (---) - JEDER --- ist ein Seitenumbruch
        if info['type'] == 'divider':
            current_page += 1
            # Nur SM setzen wenn nicht bereits für diese Seite gesetzt
            if current_page != last_used_sm:
                pending_sm = current_page
            stats['divider_count'] = stats.get('divider_count', 0) + 1
            i += 1
            continue
        
        # Überschrift
        if info['type'] == 'heading':
            output_blocks.append(block)
            i += 1
            
            # Datum-Zeilen übernehmen
            while i < len(analyzed) and analyzed[i]['type'] == 'date':
                output_blocks.append(analyzed[i]['block'])
                i += 1
            
            # SM vor erstem Text nach Überschrift/Datum
            if pending_sm is not None:
                while i < len(analyzed):
                    if analyzed[i]['type'] in ('empty', 'copyright'):
                        if analyzed[i]['type'] == 'copyright':
                            # Neue Copyright-Zeile übernimmt
                            break
                        i += 1
                        continue
                    if analyzed[i]['type'] == 'divider':
                        i += 1
                        continue
                    if analyzed[i]['type'] == 'text':
                        sm = f'[|{pending_sm}|]'
                        output_blocks.append(sm + ' ' + analyzed[i]['block'])
                        stats['heading'] += 1
                        last_used_sm = pending_sm
                        pending_sm = None
                        i += 1
                        break
                    break
            continue
        
        # Datum-Zeile (außerhalb von Überschrift-Kontext)
        if info['type'] == 'date':
            output_blocks.append(block)
            i += 1
            continue
        
        # Normaler Textblock
        if info['type'] == 'text':
            if pending_sm is not None:
                sm = f'[|{pending_sm}|]'
                
                # Prüfe vorherigen Block für Fall-Bestimmung
                if output_blocks:
                    prev_block = output_blocks[-1].rstrip()
                    last_char = prev_block[-1] if prev_block else ''
                    first_char = block[0] if block else ''
                    
                    # Fall 3: Worttrennung
                    if last_char == '-':
                        output_blocks[-1] = prev_block[:-1] + sm + block
                        stats['fall3'] += 1
                        last_used_sm = pending_sm
                        pending_sm = None
                        i += 1
                        continue
                    
                    # Fall 1: Satzende + Großbuchstabe
                    if last_char in '.!?:' and first_char.isupper():
                        output_blocks.append(sm + ' ' + block)
                        stats['fall1'] += 1
                        last_used_sm = pending_sm
                        pending_sm = None
                        i += 1
                        continue
                    
                    # Fall 2: Inline
                    output_blocks[-1] = prev_block + ' ' + sm + ' ' + block
                    stats['fall2'] += 1
                    last_used_sm = pending_sm
                    pending_sm = None
                    i += 1
                    continue
                else:
                    output_blocks.append(sm + ' ' + block)
                    stats['fall1'] += 1
                    last_used_sm = pending_sm
                    pending_sm = None
                    i += 1
                    continue
            
            output_blocks.append(block)
            i += 1
            continue
        
        # Fallback
        output_blocks.append(block)
        i += 1
    
    # Zusammenfügen
    result = '\n\n'.join(output_blocks)
    
    # Aufräumen - verbleibende Copyright-Zeilen entfernen
    result = re.sub(r'[Cc]opyright[^\[]*(\[\|\d+\|\])', r'\1', result)
    result = re.sub(r'\n\n[Cc]opyright[^\n]*\n\n', '\n\n', result)
    result = re.sub(r'^[Cc]opyright[^\n]*\n\n', '', result)
    
    # SM-Positionen korrigieren
    # Pattern 1: # ÜBERSCHRIFT\n\n[|XX|]\n\nDatum -> # ÜBERSCHRIFT\n\nDatum\n\n[|XX|]
    def fix_heading_sm_1(m):
        heading = m.group(1)
        sm = m.group(2)
        date = m.group(3)
        first_char = m.group(4)
        return f'{heading}\n\n{date}\n\n{sm} {first_char}'
    
    result = re.sub(
        r'(# [^\n]+)\n\n(\[\|\d+\|\])\n\n([^\n]+, \d+\. \w+ \d{4})\n\n([A-ZÄÖÜ])',
        fix_heading_sm_1,
        result
    )
    
    # Pattern 2: [|XX|]\n\n# ÜBERSCHRIFT -> # ÜBERSCHRIFT (SM bleibt pending)
    def fix_heading_sm_2(m):
        sm = m.group(1)
        heading = m.group(2)
        date = m.group(3)
        first_char = m.group(4)
        return f'{heading}\n\n{date}\n\n{sm} {first_char}'
    
    result = re.sub(
        r'(\[\|\d+\|\])\s*\n\n(# [^\n]+)\n\n([^\n]+, \d+\. \w+ \d{4})\n\n([A-ZÄÖÜ])',
        fix_heading_sm_2,
        result
    )
    
    # H1-Überschriften mit Datum zusammenführen
    result = merge_h1_with_date(result)
    
    # Speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Statistik berechnen
    all_sm = re.findall(r'\[\|(\d+)\|\]', result)
    counts = Counter(all_sm)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    
    # Lücken und Duplikate identifizieren
    if all_sm:
        sm_numbers = sorted([int(x) for x in all_sm])
        min_sm, max_sm = sm_numbers[0], sm_numbers[-1]
        expected = set(range(min_sm, max_sm + 1))
        actual = set(sm_numbers)
        missing = sorted(expected - actual)
        
        if missing:
            conflicts.append({
                'type': 'missing',
                'pages': missing
            })
        
        if duplicates:
            for page, count in duplicates.items():
                conflicts.append({
                    'type': 'duplicate',
                    'page': page,
                    'count': count
                })
    
    # Log-Datei schreiben wenn Probleme vorhanden
    if missing or duplicates:
        sm_range = (min(int(x) for x in all_sm), max(int(x) for x in all_sm)) if all_sm else (0, 0)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Konvertierung: {input_file}\n")
            f.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"SM-Bereich: {sm_range[0]} bis {sm_range[1]}\n")
            f.write(f"Gesamt SM: {len(all_sm)}\n")
            f.write(f"Eindeutige SM: {len(counts)}\n\n")
            f.write("=" * 80 + "\n\n")
            
            if missing:
                f.write("FEHLENDE SEITENZAHLEN:\n")
                f.write(f"  {missing}\n\n")
            
            if duplicates:
                f.write("DUPLIKATE:\n")
                for page, count in duplicates.items():
                    f.write(f"  Seite {page}: {count}x vorhanden\n")
                f.write("\n")
            
            f.write("Diese Stellen sollten manuell anhand des PDFs überprüft werden.\n")
        print(f"Probleme protokolliert: {log_file}")
        stats['conflicts'] = len(missing) + len(duplicates)
    else:
        stats['conflicts'] = 0
    
    # Statistik berechnen
    stats['total_sm'] = len(all_sm)
    stats['unique_sm'] = len(counts)
    stats['duplicates'] = duplicates
    stats['sm_range'] = (min(int(x) for x in all_sm), max(int(x) for x in all_sm)) if all_sm else (0, 0)
    stats['copyright_remaining'] = len(re.findall(r'[Cc]opyright', result))
    stats['dividers_remaining'] = len(re.findall(r'\n---\n', result))
    stats['missing'] = missing
    
    return stats

def print_stats(stats):
    """Druckt die Statistiken."""
    print("\n=== Konvertierung abgeschlossen ===")
    print(f"Gesamt SM: {stats['total_sm']}")
    print(f"Eindeutige SM: {stats['unique_sm']}")
    if stats['duplicates']:
        print(f"Duplikate: {stats['duplicates']}")
    else:
        print("Keine Duplikate!")
    print(f"SM-Bereich: {stats['sm_range'][0]} bis {stats['sm_range'][1]}")
    print(f"\nFälle:")
    print(f"  Fall 1 (Absatz): {stats['fall1']}")
    print(f"  Fall 2 (Inline): {stats['fall2']}")
    print(f"  Fall 3 (Worttrennung): {stats['fall3']}")
    print(f"  Nach Überschrift: {stats['heading']}")
    print(f"\n--- verarbeitet: {stats.get('divider_count', 0)}")
    print(f"Konflikte/Warnungen: {stats['conflicts']}")
    print(f"\nAufräumen:")
    print(f"  Copyright entfernt: {stats['copyright_removed']}")
    print(f"  Copyright verbleibend: {stats['copyright_remaining']}")
    print(f"  --- verbleibend: {stats['dividers_remaining']}")

def main():
    if len(sys.argv) < 2:
        print("Verwendung: python convert_ga_page_markers.py <pfad_zur_md_datei>")
        print("\nBeispiel:")
        print("  python convert_ga_page_markers.py 'Steiner_GA_md/GA 203.md'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Fehler: Datei nicht gefunden: {input_file}")
        sys.exit(1)
    
    print(f"Verarbeite: {input_file}")
    
    stats = convert_page_markers(input_file)
    print_stats(stats)

if __name__ == '__main__':
    main()
