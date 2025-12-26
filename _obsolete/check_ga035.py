#!/usr/bin/env python3
"""Prüfe GA035 Vorträge und Seitenzahlen"""
import json
import re

# Lade pagebreaks/GA035.json
with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\pagebreaks\GA035.json', encoding='utf-8') as f:
    data = json.load(f)

lectures = data.get('lectures', [])
print(f'Anzahl Vorträge in pagebreaks/GA035.json: {len(lectures)}')
print()

# Prüfe jeden Vortrag
for lecture in lectures:
    lecture_id = lecture.get('ID', 'UNKNOWN')
    paragraphs = lecture.get('paragraphs', [])
    
    # Finde alle Seitenmarker im Text
    all_text = ' '.join(p.get('text', '') for p in paragraphs)
    markers = re.findall(r'\|(\d+)\|', all_text)
    
    if markers:
        first_page = markers[0]
        last_page = markers[-1]
        print(f'{lecture_id}: {len(paragraphs)} Absätze, Seiten {first_page}-{last_page} ({len(markers)} Marker)')
    else:
        print(f'{lecture_id}: {len(paragraphs)} Absätze, KEINE MARKER!')

# Prüfe lecture-page-mapping
print()
print('=== lecture-page-mapping.json ===')
try:
    with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\lecture-page-mapping.json', encoding='utf-8') as f:
        mapping = json.load(f)
    
    ga035_entries = {k: v for k, v in mapping.items() if k.startswith('GA035/')}
    for k, v in sorted(ga035_entries.items(), key=lambda x: int(x[0].split('/')[1]) if x[0].split('/')[1].isdigit() else 999):
        print(f'{k}: start_page={v.get("start_page")}')
except Exception as e:
    print(f'Fehler: {e}')

