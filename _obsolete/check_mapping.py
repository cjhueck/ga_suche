#!/usr/bin/env python3
"""Prüfe lecture-page-mapping für GA035"""
import json

# Lade lecture-page-mapping
with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\lecture-page-mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)

print('=== lecture-page-mapping.json für GA035 ===')
ga035_entries = {k: v for k, v in mapping.items() if k.startswith('GA035/')}

if not ga035_entries:
    print('KEINE EINTRÄGE für GA035!')
else:
    for k in sorted(ga035_entries.keys(), key=lambda x: int(x.split('/')[1]) if x.split('/')[1].isdigit() else 999):
        v = ga035_entries[k]
        print(f'{k}: start_page={v.get("start_page")}')

# Vergleiche mit pagebreaks Markern
print()
print('=== Vergleich mit pagebreaks/GA035.json ===')
import re
with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\pagebreaks\GA035.json', encoding='utf-8') as f:
    pb_data = json.load(f)

for lecture in pb_data.get('lectures', []):
    lid = lecture.get('ID', 'UNKNOWN')
    paragraphs = lecture.get('paragraphs', [])
    
    # Finde ersten Marker
    all_text = ' '.join(p.get('content', p.get('text', '')) for p in paragraphs)
    markers = re.findall(r'\|(\d+)\|', all_text)
    
    first_marker = markers[0] if markers else 'KEINE'
    mapping_page = ga035_entries.get(lid, {}).get('start_page', 'N/A')
    
    match = '[OK]' if str(first_marker) == str(mapping_page) else '[MISMATCH!]'
    print(f'{lid}: pagebreak-marker={first_marker}, mapping={mapping_page} {match}')

