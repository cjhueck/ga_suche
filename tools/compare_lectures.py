#!/usr/bin/env python3
"""Vergleiche GA216/6 (funktioniert) mit GA074/1 (funktioniert nicht)."""

import json
from pathlib import Path

base = Path(__file__).parent.parent

def find_lecture(lecture_id):
    """Finde Vortrag in allen steiner-full-lectures Dateien."""
    lectures_dir = base / 'steiner-full-lectures'
    for f in lectures_dir.glob('*.json'):
        data = json.load(open(f, 'r', encoding='utf-8'))
        for lec in data.get('lectures', []):
            if lec.get('ID') == lecture_id:
                return lec, f.name
    return None, None

# GA216/6 - funktioniert
lec216, file216 = find_lecture('GA216/6')
if lec216:
    print("=" * 60)
    print("GA216/6 (funktioniert):")
    print(f"  Datei: {file216}")
    tafel = [p for p in lec216.get('paragraphs', []) if 'Tafel' in p.get('content', '') or 'img' in p.get('content', '').lower()]
    print(f"  Bild-Paragraphen: {len(tafel)}")
    for p in tafel[:3]:
        print(f"\n  Index: {p.get('index')}")
        print(f"  Content:")
        print(f"    {repr(p.get('content')[:150])}")
else:
    print("GA216/6 nicht gefunden!")

# GA074/1 - funktioniert nicht
lec074, file074 = find_lecture('GA074/1')
if lec074:
    print("\n" + "=" * 60)
    print("GA074/1 (funktioniert NICHT):")
    print(f"  Datei: {file074}")
    tafel = [p for p in lec074.get('paragraphs', []) if 'Tafel' in p.get('content', '') or 'img' in p.get('content', '').lower()]
    print(f"  Bild-Paragraphen: {len(tafel)}")
    for p in tafel[:3]:
        print(f"\n  Index: {p.get('index')}")
        print(f"  Content:")
        print(f"    {repr(p.get('content')[:150])}")
else:
    print("GA074/1 nicht gefunden!")






