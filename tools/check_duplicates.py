# -*- coding: utf-8 -*-
import re
import os
from collections import Counter

GA203_PATH = r"Steiner_GA_md\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung\Steiner, Rudolf GA 203 1989 - Die Verantwortung des Menschen für die Weltentwickelung.md"

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
file_path = os.path.join(workspace_root, GA203_PATH)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Finde alle SM
sm_pattern = re.compile(r'\*\*\|(\d+)\|\*\*')
matches = sm_pattern.findall(content)

# Prüfe auf Duplikate
counts = Counter(matches)
duplicates = {k: v for k, v in counts.items() if v > 1}

print(f'Gesamt SM: {len(matches)}')
print(f'Eindeutige SM: {len(set(matches))}')
if duplicates:
    print(f'Duplikate: {duplicates}')
else:
    print('Keine Duplikate gefunden.')
