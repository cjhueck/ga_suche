# -*- coding: utf-8 -*-
"""
Skript zum Behandeln von alleinstehenden --- als CR-Umbrüche.
Diese haben keine Copyright-Zeile und müssen interpolierte Seitenzahlen bekommen.
"""

import re
import os

GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

def fix_dividers(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Finde alle SM und ihre Positionen, um die letzte Seitenzahl zu tracken
    sm_pattern = re.compile(r'\*\*\|(\d+)\|\*\*')
    
    # Finde alle alleinstehenden --- (nicht nach Copyright)
    # Pattern: Text ohne Copyright, dann Leerzeile, ---, Leerzeile, Text
    divider_pattern = re.compile(
        r'([^\n]+)\n\n'  # Vorheriger Text (keine Copyright-Zeile)
        r'---\n\n'  # Trennlinie
        r'([^\n]+)',  # Folgender Text
        re.MULTILINE
    )
    
    def is_copyright_line(text):
        return 'Copyright Rudolf Steiner' in text or 'copyright Rudolf Steiner' in text
    
    changes = 0
    
    def replace_divider(match):
        nonlocal changes
        before = match.group(1)
        after = match.group(2)
        
        # Überspringe, wenn vor dem --- eine Copyright-Zeile steht
        if is_copyright_line(before):
            return match.group(0)  # Keine Änderung
        
        # Finde die letzte Seitenzahl vor dieser Position
        text_before_match = content[:match.start()]
        sm_matches = list(sm_pattern.finditer(text_before_match))
        
        if sm_matches:
            last_page = int(sm_matches[-1].group(1))
            next_page = last_page + 1
        else:
            next_page = 1  # Fallback
        
        sm = f"**|{next_page}|**"
        
        # Bestimme den Fall
        last_char = before.strip()[-1] if before.strip() else ''
        first_char = after.strip()[0] if after.strip() else ''
        
        changes += 1
        
        # Fall 3: Worttrennung (Bindestrich am Ende)
        if last_char == '-':
            # Entferne Bindestrich, füge SM ohne Leerzeichen ein
            return before.rstrip()[:-1] + sm + after
        
        # Fall 1: Nach Satzende (Punkt + Großbuchstabe)
        elif last_char in '.!?' and first_char.isupper():
            return before + '\n\n' + sm + ' ' + after
        
        # Fall 2: Mitten im Satz
        else:
            return before + ' ' + sm + ' ' + after
    
    # Da wir die letzte Seitenzahl vor jeder Position brauchen, 
    # müssen wir das iterativ machen
    new_content = content
    offset = 0
    
    for match in divider_pattern.finditer(content):
        before = match.group(1)
        after = match.group(2)
        
        if is_copyright_line(before):
            continue
        
        # Finde die letzte Seitenzahl vor dieser Position im AKTUELLEN content
        text_before = new_content[:match.start() + offset]
        sm_matches = list(sm_pattern.finditer(text_before))
        
        if sm_matches:
            last_page = int(sm_matches[-1].group(1))
            next_page = last_page + 1
        else:
            next_page = 1
        
        sm = f"**|{next_page}|**"
        
        last_char = before.strip()[-1] if before.strip() else ''
        first_char = after.strip()[0] if after.strip() else ''
        
        # Erstelle Ersetzung
        if last_char == '-':
            replacement = before.rstrip()[:-1] + sm + after
        elif last_char in '.!?' and first_char.isupper():
            replacement = before + '\n\n' + sm + ' ' + after
        else:
            replacement = before + ' ' + sm + ' ' + after
        
        # Führe Ersetzung durch
        original = match.group(0)
        new_content = new_content[:match.start() + offset] + replacement + new_content[match.end() + offset:]
        offset += len(replacement) - len(original)
        changes += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'{changes} alleinstehende --- wurden durch SM ersetzt.')

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    file_path = os.path.join(workspace_root, GA203_PATH)
    print(f"Bearbeite: {file_path}")
    fix_dividers(file_path)
