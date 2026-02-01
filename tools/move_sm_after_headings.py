# -*- coding: utf-8 -*-
"""
Skript zum Verschieben von Seitenmarkern von vor Überschriften nach dahinter.

Vorher:
**|34|** # ZWEITER VORTRAG

Stuttgart, 6. Januar 1921

Nachher:
# ZWEITER VORTRAG

**|34|** Stuttgart, 6. Januar 1921
"""

import re
import os

# Hartcodierter Pfad für GA 203
GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

def move_markers(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern: SM vor einer Überschrift (auf gleicher Zeile), dann Leerzeile(n), dann Text
    # Format: **|34|** # ZWEITER VORTRAG\n\nStuttgart, 6. Januar 1921
    pattern = re.compile(
        r'(\*\*\|\d+\|\*\*)\s*(#{1,4}\s*[^\n]+)\n\n'  # SM + Überschrift auf einer Zeile
        r'([^\n]+)',  # Erste Textzeile nach der Leerzeile
        re.MULTILINE
    )
    
    def replace_func(match):
        sm = match.group(1)  # Seitenmarker
        heading = match.group(2).strip()  # Überschrift
        first_text = match.group(3).strip()  # Erster Text
        
        # Neues Format: Überschrift, Leerzeile, SM + Text
        return f'{heading}\n\n{sm} {first_text}'
    
    new_content = pattern.sub(replace_func, content)
    
    # Zähle Änderungen
    changes = len(pattern.findall(content))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'{changes} Seitenmarker wurden nach der Überschrift verschoben.')

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    file_path = os.path.join(workspace_root, GA203_PATH)
    print(f"Bearbeite: {file_path}")
    move_markers(file_path)
