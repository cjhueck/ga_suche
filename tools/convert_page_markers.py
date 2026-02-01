# -*- coding: utf-8 -*-
"""
Skript zur Umwandlung von CR-Umbrüchen in Seitenmarker

CR-Umbruch Format:
    Copyright Rudolf Steiner Nachlass-Verwaltung Buch: XXX Seite: YY
    
    ---

Wird umgewandelt zu Seitenmarker: |YY+1|

Drei Fälle:
1. Nach Satzende (Punkt + Großbuchstabe): Absatz bleibt, SM am Anfang des neuen Absatzes
2. Mitten im Satz (kein Punkt): Absatz wird entfernt, SM inline mit Leerzeichen
3. Worttrennung (Bindestrich am Ende): Absatz wird entfernt, SM ohne Leerzeichen im Wort
"""

import re
import sys
import os
from pathlib import Path

# Hartcodierter Pfad für GA 203
GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

def extract_page_number(copyright_line):
    """Extrahiert die Seitenzahl aus der Copyright-Zeile."""
    # Verschiedene Formate: "Seite: 15", "Seite:15", "Seite: 1 5", etc.
    match = re.search(r'Seite:\s*(\d+(?:\s*\d+)*)', copyright_line)
    if match:
        # Entferne Leerzeichen aus der Seitenzahl (z.B. "1 5" -> "15")
        page_str = match.group(1).replace(' ', '')
        return int(page_str)
    return None

def process_file(input_path, output_path=None):
    """Verarbeitet die Datei und ersetzt CR-Umbrüche durch Seitenmarker."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex für CR-Umbruch Pattern - verschiedene OCR-Varianten berücksichtigen:
    # "Nachlass-Verwaltung", "Nachiass-Verwaitung", etc.
    
    # Pattern für den gesamten CR-Umbruch Block
    cr_pattern = re.compile(
        r'(\S[^\n]*?)'  # Gruppe 1: Letztes Zeichen/Wort vor dem Umbruch
        r'\n\n'  # Leerzeile vor Copyright
        r'(Copyright Rudolf Steiner Nach[iI]?[lI]?ass-Verwa[lI]tung Buch:\s*\d+(?:\s*\d+)*\s*Seite:\s*(\d+(?:\s*\d+)*)(?:</[^>]+>)*)'  # Gruppe 2: Copyright-Zeile, Gruppe 3: Seitenzahl
        r'\n\n'  # Leerzeile
        r'---'  # Trennlinie
        r'\n\n'  # Leerzeilen nach ---
        r'(\S)',  # Gruppe 4: Erstes Zeichen nach dem Umbruch
        re.MULTILINE
    )
    
    # Zähler für Statistiken
    stats = {'punkt_grossbuchstabe': 0, 'mitten_im_satz': 0, 'worttrennung': 0, 'errors': 0}
    last_page = 0
    
    def replace_cr(match):
        nonlocal last_page
        
        before_text = match.group(1)  # Text vor dem CR-Umbruch
        copyright_line = match.group(2)  # Copyright-Zeile
        page_str = match.group(3)  # Seitenzahl
        first_char_after = match.group(4)  # Erstes Zeichen nach dem Umbruch
        
        # Seitenzahl extrahieren (Leerzeichen entfernen)
        if page_str:
            page_num = int(page_str.replace(' ', ''))
        else:
            # Interpolieren aus letzter bekannter Seite
            page_num = last_page + 1
        
        last_page = page_num
        next_page = page_num + 1
        page_marker = f"|{next_page}|"
        
        # Letztes Zeichen vor dem Umbruch analysieren
        last_char = before_text[-1] if before_text else ''
        
        # Fall 3: Worttrennung (Bindestrich am Ende)
        if last_char == '-':
            stats['worttrennung'] += 1
            # Entferne den Bindestrich und füge SM ohne Leerzeichen ein
            return before_text[:-1] + page_marker + first_char_after
        
        # Fall 1: Nach Satzende (Punkt, Ausrufezeichen, Fragezeichen + Großbuchstabe)
        elif last_char in '.!?' and first_char_after.isupper():
            stats['punkt_grossbuchstabe'] += 1
            # Behalte Absatz, SM am Anfang des neuen Absatzes
            return before_text + '\n\n' + page_marker + ' ' + first_char_after
        
        # Fall 2: Mitten im Satz (kein Satzende)
        else:
            stats['mitten_im_satz'] += 1
            # Entferne Absatz, SM inline mit Leerzeichen
            return before_text + ' ' + page_marker + ' ' + first_char_after
    
    # Erste Ersetzungsrunde
    new_content = cr_pattern.sub(replace_cr, content)
    
    # Prüfe ob noch CR-Umbrüche übrig sind (mit etwas anderen Formatierungen)
    # Manchmal gibt es Variationen im Format
    remaining = re.findall(r'Copyright Rudolf Steiner', new_content)
    
    if remaining:
        print(f"Warnung: {len(remaining)} CR-Umbrüche wurden nicht ersetzt.")
        print("Diese haben möglicherweise ein anderes Format.")
    
    # Ausgabe
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Datei gespeichert: {output_path}")
    else:
        # Überschreibe die Originaldatei
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Datei überschrieben: {input_path}")
    
    print(f"\nStatistik:")
    print(f"  Fall 1 (Punkt + Großbuchstabe): {stats['punkt_grossbuchstabe']}")
    print(f"  Fall 2 (Mitten im Satz): {stats['mitten_im_satz']}")
    print(f"  Fall 3 (Worttrennung): {stats['worttrennung']}")
    print(f"  Gesamt ersetzt: {sum(stats.values())}")
    
    return new_content, stats

if __name__ == '__main__':
    # Wenn keine Argumente, verwende den hartcodierten Pfad
    if len(sys.argv) < 2:
        # Finde den Workspace-Root (ga_suche)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(script_dir)  # tools -> ga_suche
        input_file = os.path.join(workspace_root, GA203_PATH)
        print(f"Verwende hartcodierten Pfad: {input_file}")
    else:
        input_file = sys.argv[1]
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_file(input_file, output_file)
