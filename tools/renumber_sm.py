# -*- coding: utf-8 -*-
"""
Skript zum Neu-Nummerieren aller SM, sodass sie fortlaufend sind.
"""
import re
import os

GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
file_path = os.path.join(workspace_root, GA203_PATH)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Finde alle SM mit ihren Positionen
sm_pattern = re.compile(r'\*\*\|(\d+)\|\*\*')

# Zähler für neue Seitenzahlen
current_page = 1

def replace_sm(match):
    global current_page
    new_sm = f'**|{current_page}|**'
    current_page += 1
    return new_sm

# Ersetze alle SM mit fortlaufenden Nummern
new_content = sm_pattern.sub(replace_sm, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Alle SM wurden neu nummeriert (1 bis {current_page - 1}).')
