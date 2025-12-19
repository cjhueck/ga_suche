#!/usr/bin/env python3
"""Zeigt Seitenmarker pro Vortrag"""
import json
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'

pb_file = f'pagebreak-books/{ga}.json'
try:
    data = json.load(open(pb_file, 'r', encoding='utf-8'))
except FileNotFoundError:
    print(f"Datei nicht gefunden: {pb_file}")
    sys.exit(1)

lectures = data.get('lectures', [])
if not lectures:
    print("Keine Vorträge in der Datei")
    sys.exit(1)

print(f"=== Seitenmarker pro Vortrag in {ga} ===\n")

total_markers = 0
for lec in lectures:
    lec_id = lec.get('ID', '?')
    lec_num = lec.get('lectureNumber', '?')
    title = lec.get('title', '')[:40]
    
    markers = []
    for p in lec.get('paragraphs', []):
        content = p.get('content', '')
        found = re.findall(r'\|(\d+)\|', content)
        markers.extend(found)
    
    total_markers += len(markers)
    
    if markers:
        marker_range = f"{markers[0]}-{markers[-1]}" if len(markers) > 1 else markers[0]
        print(f"  {lec_num}: {len(markers):3d} Marker (S.{marker_range}) - {title}")
    else:
        print(f"  {lec_num}:   0 Marker - {title}")

print(f"\nGesamt: {total_markers} Marker in {len(lectures)} Vorträgen")






