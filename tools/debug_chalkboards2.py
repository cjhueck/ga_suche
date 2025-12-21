#!/usr/bin/env python3
"""Debug-Skript für Wandtafelzeichnungen - Teil 2."""

import json
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent

lectures_file = BASE_PATH / "steiner-full-lectures" / "steiner-full-lectures-030-354-part04.json"
data = json.load(open(lectures_file, 'r', encoding='utf-8'))
lectures = data.get('lectures', [])

# Finde alle GA074 Lectures
print("GA074 Lectures:")
for lec in lectures:
    if lec.get('gaNumber') == 'GA074':
        print(f"  lectureNumber: {lec.get('lectureNumber')} (type: {type(lec.get('lectureNumber')).__name__})")
        print(f"  ID: {lec.get('ID')}")
        print(f"  title: {lec.get('title', '')[:50]}")
        paras = lec.get('paragraphs', [])
        print(f"  Paragraphen: {len(paras)}")
        # Prüfe ob Tafel-Paragraphen vorhanden sind
        tafel_paras = [p for p in paras if 'Tafel' in p.get('content', '') or 'ga074' in p.get('index', '').lower()]
        print(f"  Tafel-Paragraphen: {len(tafel_paras)}")
        for tp in tafel_paras:
            print(f"    {tp.get('index')}: {tp.get('content')[:50]}")
        print()






