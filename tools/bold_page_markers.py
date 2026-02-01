# -*- coding: utf-8 -*-
"""
Skript zum Fett-Formatieren der Seitenmarker |XX| -> **|XX|**
"""

import re
import os

# Hartcodierter Pfad für GA 203
GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

def bold_markers(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ersetze |XX| durch **|XX|**
    new_content = re.sub(r'\|(\d+)\|', r'**|\1|**', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Zähle Ersetzungen
    count = len(re.findall(r'\*\*\|\d+\|\*\*', new_content))
    print(f'{count} Seitenmarker wurden fett formatiert.')

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    file_path = os.path.join(workspace_root, GA203_PATH)
    print(f"Bearbeite: {file_path}")
    bold_markers(file_path)
