# -*- coding: utf-8 -*-
"""
Skript zur Korrektur von duplizierten SM.
Wenn eine SM-Nummer <= der vorherigen ist, wird sie und alle folgenden um 1 erhöht.
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
matches = list(sm_pattern.finditer(content))

print(f"Gefundene SM: {len(matches)}")

# Sammle alle SM-Nummern und ihre Positionen
sm_list = []
for m in matches:
    sm_list.append({
        'start': m.start(),
        'end': m.end(),
        'original': int(m.group(1)),
        'new': int(m.group(1))
    })

# Korrigiere Duplikate: Wenn eine Nummer <= der vorherigen ist, erhöhe sie
corrections = 0
for i in range(1, len(sm_list)):
    if sm_list[i]['new'] <= sm_list[i-1]['new']:
        # Diese und alle folgenden SM müssen erhöht werden
        diff = sm_list[i-1]['new'] - sm_list[i]['new'] + 1
        for j in range(i, len(sm_list)):
            sm_list[j]['new'] += diff
        corrections += 1

print(f"Korrekturen: {corrections}")

# Erstelle neuen Content (von hinten nach vorne ersetzen, um Positionen nicht zu verschieben)
new_content = content
for sm in reversed(sm_list):
    if sm['original'] != sm['new']:
        old_sm = f"**|{sm['original']}|**"
        new_sm = f"**|{sm['new']}|**"
        new_content = new_content[:sm['start']] + new_sm + new_content[sm['end']:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verifiziere
sm_pattern = re.compile(r'\*\*\|(\d+)\|\*\*')
new_matches = sm_pattern.findall(new_content)
from collections import Counter
counts = Counter(new_matches)
duplicates = {k: v for k, v in counts.items() if v > 1}

print(f"SM nach Korrektur: {len(new_matches)}")
if duplicates:
    print(f"Verbleibende Duplikate: {duplicates}")
else:
    print("Keine Duplikate mehr!")
print(f"SM-Bereich: {min(int(x) for x in new_matches)} bis {max(int(x) for x in new_matches)}")
