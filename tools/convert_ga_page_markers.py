# -*- coding: utf-8 -*-
"""
Universelles Skript zur Umwandlung von CR-Umbrüchen in Seitenmarker (SM) für alle GA-Bände.

Verwendung:
    python convert_ga_page_markers.py <pfad_zur_md_datei>

Regeln:
1. JEDER "---" = Seitenumbruch -> current_page += 1, SM für nächsten Text
2. "Copyright...Seite: XX" = Validierung/Korrektur von current_page auf XX
3. SM-Format: |XX| wobei XX = Seitenzahl
4. Bildpfade: Falsche Bildpfade werden durch korrekte PNG-Pfade aus dem assets-Ordner ersetzt
5. SM-Positionierung:
   - Fall 1 (Absatz): Nach Satzende (.!?:) + Großbuchstabe -> neuer Absatz mit SM
   - Fall 2 (Inline): Kein Satzende -> SM inline mit Leerzeichen
   - Fall 3 (Worttrennung): Bindestrich am Ende -> SM ohne Leerzeichen
6. Bei Überschriften (#): SM nach Überschrift + Datum, vor erstem Text
7. Überschriften-Korrektur:
   - Großbuchstaben-Zeilen mit Ort/Datum werden zu # Überschriften
   - Datum auf separater Zeile wird in Überschrift integriert
8. "Tafel" oder "Tafel x" als einzelne Zeile wird gelöscht
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

def is_tafel_line(text):
    """Prüft ob Text eine Tafel-Zeile ist, die gelöscht werden soll."""
    text = text.strip()
    # "Tafel", "Tafel 1", "Tafel 1*", "Tafel I" etc. als einzelne Zeile
    if re.match(r'^Tafel(\s+[\dIVXivx]+\*?)?$', text, re.IGNORECASE):
        return True
    return False

def is_lecture_heading_without_hash(text):
    """
    Prüft ob Text eine Vortrags-Überschrift ohne # ist.
    Erkennungsmerkmale:
    - Überwiegend Großbuchstaben
    - Enthält typische Vortragswörter (VORTRAG, ERSTER, ZWEITER, etc.)
    - Relativ kurz (unter 200 Zeichen)
    """
    text = text.strip()
    
    # Bereits eine Überschrift
    if text.startswith('#'):
        return False
    
    # Zu lang für eine Überschrift
    if len(text) > 200:
        return False
    
    # Prüfe auf typische Vortragstitel-Muster
    patterns = [
        r'^(ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|ACHTER|NEUNTER|ZEHNTER)\s+VORTRAG',
        r'^(ERSTE|ZWEITE|DRITTE|VIERTE|FÜNFTE|SECHSTE|SIEBTE|ACHTE|NEUNTE|ZEHNTE)\s+',
        r'^I+V?I*\.?\s+VORTRAG',  # I., II., III., IV. VORTRAG
        r'^[IVX]+\.?\s+',  # Römische Zahlen
        r'^VORTRAG\s',
        r'^DIE\s+[A-ZÄÖÜ]',  # DIE MICHAEL-IMAGINATION
        r'^DAS\s+[A-ZÄÖÜ]',  # DAS MITERLEBEN
        r'^DER\s+[A-ZÄÖÜ]',  # DER MENSCH
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    
    # Prüfe ob Text überwiegend aus Großbuchstaben besteht (>60%)
    letters = [c for c in text if c.isalpha()]
    if letters:
        uppercase_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if uppercase_ratio > 0.6 and len(text) < 100:
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
        # Prüfe ob Datum bereits in Überschrift enthalten
        if date_line.split(',')[0] in heading or re.search(r'\d{4}', heading):
            return m.group(0)  # Keine Änderung
        return f'{heading}, {date_line}{ending}'
    
    result = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
    return result

def add_hash_to_headings(content):
    """
    Fügt # zu Überschriften hinzu, die keins haben.
    Erkennt Überschriften an:
    - Großbuchstaben
    - Typische Vortragstitel-Muster
    """
    lines = content.split('\n')
    result_lines = []
    stats = {'headings_fixed': 0}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Prüfe ob diese Zeile eine Überschrift ohne # ist
        if is_lecture_heading_without_hash(stripped):
            # Füge # hinzu
            result_lines.append('# ' + stripped)
            stats['headings_fixed'] += 1
            i += 1
            continue
        
        result_lines.append(line)
        i += 1
    
    return '\n'.join(result_lines), stats

def remove_tafel_lines(content):
    """
    Entfernt "Tafel" oder "Tafel x" Zeilen.
    """
    lines = content.split('\n')
    result_lines = []
    stats = {'tafel_removed': 0}
    
    for line in lines:
        if is_tafel_line(line):
            stats['tafel_removed'] += 1
            continue
        result_lines.append(line)
    
    return '\n'.join(result_lines), stats

def fix_headings_comprehensive(content):
    """
    Umfassende Überschriften-Korrektur:
    1. Fügt # zu Überschriften ohne # hinzu
    2. Fügt Datum in Überschrift ein wenn auf separater Zeile
    3. Entfernt Tafel-Zeilen
    """
    stats = {
        'headings_fixed': 0,
        'dates_merged': 0,
        'tafel_removed': 0
    }
    
    # Schritt 1: # zu Überschriften hinzufügen
    content, add_stats = add_hash_to_headings(content)
    stats['headings_fixed'] = add_stats['headings_fixed']
    
    # Schritt 2: Datum in Überschrift integrieren
    # Zähle vorher die Anzahl der separaten Datumszeilen nach Überschriften
    before_count = len(re.findall(r'^# [^\n]+\n\n+[A-ZÄÖÜ][a-zäöüß]+,?\s+\d{1,2}\.\s+\w+\s+\d{4}', content, re.MULTILINE))
    content = merge_h1_with_date(content)
    after_count = len(re.findall(r'^# [^\n]+\n\n+[A-ZÄÖÜ][a-zäöüß]+,?\s+\d{1,2}\.\s+\w+\s+\d{4}', content, re.MULTILINE))
    stats['dates_merged'] = before_count - after_count
    
    # Schritt 3: Tafel-Zeilen entfernen
    content, tafel_stats = remove_tafel_lines(content)
    stats['tafel_removed'] = tafel_stats['tafel_removed']
    
    return content, stats

def is_copyright_line(text):
    """Prüft ob Text eine Copyright-Zeile ist."""
    return bool(re.search(r'[Cc]opyright Rudolf Steiner', text))

def extract_page_number(copyright_text):
    """Extrahiert die Seitenzahl aus einer Copyright-Zeile."""
    match = re.search(r'Seite:\s*(\d[\d\s]*)', copyright_text)
    if match:
        return int(match.group(1).replace(' ', ''))
    return None

def fix_image_paths(content, input_file):
    """
    Korrigiert Bildpfade im Markdown.
    
    Ersetzt falsche Bildpfade (z.B. aus Mistral-Konvertierung) durch korrekte
    PNG-Pfade aus dem assets-Ordner.
    
    Args:
        content: Der Markdown-Inhalt
        input_file: Pfad zur MD-Datei (für assets-Ordner-Ermittlung)
    
    Returns:
        tuple: (korrigierter_content, stats_dict)
    """
    stats = {
        'images_found': 0,
        'images_replaced': 0,
        'images_missing': []
    }
    
    # Assets-Ordner ermitteln (relativ zur MD-Datei)
    md_dir = os.path.dirname(os.path.abspath(input_file))
    assets_dir = os.path.join(md_dir, 'assets')
    
    # Prüfe ob assets-Ordner existiert
    if not os.path.exists(assets_dir):
        return content, stats
    
    # Finde alle PNG-Dateien im assets-Ordner
    available_images = {}
    for img_file in os.listdir(assets_dir):
        if img_file.lower().endswith('.png'):
            # Extrahiere Bildnummer aus Dateinamen (z.B. "img-0" aus "img-0.png")
            match = re.search(r'img-(\d+)', img_file, re.IGNORECASE)
            if match:
                img_num = int(match.group(1))
                available_images[img_num] = img_file
    
    if not available_images:
        return content, stats
    
    # Pattern für Markdown-Bilder: ![alt](pfad)
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        old_path = match.group(2)
        stats['images_found'] += 1
        
        # Extrahiere Bildnummer aus Alt-Text oder Pfad
        img_num = None
        
        # Versuche aus Alt-Text (z.B. "img-0.jpeg")
        num_match = re.search(r'img-(\d+)', alt_text, re.IGNORECASE)
        if num_match:
            img_num = int(num_match.group(1))
        
        # Fallback: aus Pfad extrahieren
        if img_num is None:
            num_match = re.search(r'img-(\d+)', old_path, re.IGNORECASE)
            if num_match:
                img_num = int(num_match.group(1))
        
        if img_num is None:
            # Keine Bildnummer gefunden, beibehalten
            return match.group(0)
        
        # Prüfe ob entsprechende PNG existiert
        if img_num in available_images:
            new_path = f'assets/{available_images[img_num]}'
            stats['images_replaced'] += 1
            return f'![]({new_path})'
        else:
            # Bild nicht gefunden
            stats['images_missing'].append(f'img-{img_num}')
            return match.group(0)
    
    result = re.sub(img_pattern, replace_image, content)
    
    return result, stats


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
    
    # Bildpfade korrigieren
    content, image_stats = fix_image_paths(content, input_file)
    
    # Überschriften korrigieren (vor Block-Verarbeitung)
    content, heading_stats = fix_headings_comprehensive(content)
    
    # Teile den Text in Blöcke (getrennt durch Leerzeilen)
    blocks = re.split(r'\n\n+', content)
    
    # Analysiere Blöcke bidirektional
    analyzed = analyze_blocks(blocks)
    
    # Statistiken
    stats = {'fall1': 0, 'fall2': 0, 'fall3': 0, 'heading': 0, 'copyright_removed': 0, 'conflicts': 0}
    
    # Überschriften-Statistiken übernehmen
    stats['headings_fixed'] = heading_stats.get('headings_fixed', 0)
    stats['dates_merged'] = heading_stats.get('dates_merged', 0)
    stats['tafel_removed'] = heading_stats.get('tafel_removed', 0)
    
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
                        sm = f'|{pending_sm}|'
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
                sm = f'|{pending_sm}|'
                
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
    result = re.sub(r'[Cc]opyright[^\|]*(\|\d+\|)', r'\1', result)
    result = re.sub(r'\n\n[Cc]opyright[^\n]*\n\n', '\n\n', result)
    result = re.sub(r'^[Cc]opyright[^\n]*\n\n', '', result)
    
    # SM-Positionen korrigieren
    # Pattern 1: # ÜBERSCHRIFT\n\n|XX|\n\nDatum -> # ÜBERSCHRIFT\n\nDatum\n\n|XX|
    def fix_heading_sm_1(m):
        heading = m.group(1)
        sm = m.group(2)
        date = m.group(3)
        first_char = m.group(4)
        return f'{heading}\n\n{date}\n\n{sm} {first_char}'
    
    result = re.sub(
        r'(# [^\n]+)\n\n(\|\d+\|)\n\n([^\n]+, \d+\. \w+ \d{4})\n\n([A-ZÄÖÜ])',
        fix_heading_sm_1,
        result
    )
    
    # Pattern 2: |XX|\n\n# ÜBERSCHRIFT -> # ÜBERSCHRIFT (SM bleibt pending)
    def fix_heading_sm_2(m):
        sm = m.group(1)
        heading = m.group(2)
        date = m.group(3)
        first_char = m.group(4)
        return f'{heading}\n\n{date}\n\n{sm} {first_char}'
    
    result = re.sub(
        r'(\|\d+\|)\s*\n\n(# [^\n]+)\n\n([^\n]+, \d+\. \w+ \d{4})\n\n([A-ZÄÖÜ])',
        fix_heading_sm_2,
        result
    )
    
    # H1-Überschriften mit Datum zusammenführen
    result = merge_h1_with_date(result)
    
    # Speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    # Statistik berechnen
    all_sm = re.findall(r'\|(\d+)\|', result)
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
    has_problems = missing or duplicates or image_stats['images_missing']
    if has_problems:
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
            
            if image_stats['images_missing']:
                f.write("FEHLENDE BILDER (nicht im assets-Ordner gefunden):\n")
                for img in image_stats['images_missing']:
                    f.write(f"  {img}.png\n")
                f.write("\n")
            
            f.write("Diese Stellen sollten manuell überprüft werden.\n")
        print(f"Probleme protokolliert: {log_file}")
        stats['conflicts'] = len(missing) + len(duplicates) + len(image_stats['images_missing'])
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
    
    # Bildstatistiken hinzufügen
    stats['images_found'] = image_stats['images_found']
    stats['images_replaced'] = image_stats['images_replaced']
    stats['images_missing'] = image_stats['images_missing']
    
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
    print(f"\nÜberschriften:")
    print(f"  # hinzugefügt: {stats.get('headings_fixed', 0)}")
    print(f"  Datum zusammengeführt: {stats.get('dates_merged', 0)}")
    print(f"  Tafel-Zeilen entfernt: {stats.get('tafel_removed', 0)}")
    print(f"\nAufräumen:")
    print(f"  Copyright entfernt: {stats['copyright_removed']}")
    print(f"  Copyright verbleibend: {stats['copyright_remaining']}")
    print(f"  --- verbleibend: {stats['dividers_remaining']}")
    print(f"\nBilder:")
    print(f"  Gefunden: {stats.get('images_found', 0)}")
    print(f"  Korrigiert: {stats.get('images_replaced', 0)}")
    if stats.get('images_missing'):
        print(f"  Fehlend: {stats['images_missing']}")

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
