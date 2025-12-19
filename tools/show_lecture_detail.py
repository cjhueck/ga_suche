#!/usr/bin/env python3
"""Zeigt Details zu einem Vortrag"""
import json
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
lec_num = sys.argv[2] if len(sys.argv) > 2 else '5'

pb_file = f'pagebreak-books/{ga}.json'
try:
    data = json.load(open(pb_file, 'r', encoding='utf-8'))
except FileNotFoundError:
    print(f"Datei nicht gefunden: {pb_file}")
    sys.exit(1)

lectures = data.get('lectures', [])

# Finde den Vortrag
target = None
for lec in lectures:
    if str(lec.get('lectureNumber', '')) == lec_num:
        target = lec
        break

if not target:
    print(f"Vortrag {lec_num} nicht gefunden")
    sys.exit(1)

print(f"=== Vortrag {lec_num}: {target.get('title', '')} ===\n")

# Zeige alle Marker mit Kontext
for i, p in enumerate(target.get('paragraphs', [])):
    content = p.get('content', '')
    markers = re.findall(r'\|(\d+)\|', content)
    if markers:
        # Zeige Kontext um die Marker
        for m in markers:
            pattern = f'|{m}|'
            pos = content.find(pattern)
            if pos != -1:
                start = max(0, pos - 30)
                end = min(len(content), pos + len(pattern) + 30)
                context = content[start:end].replace('\n', ' ')
                print(f"  Seite {m}: ...{context}...")


