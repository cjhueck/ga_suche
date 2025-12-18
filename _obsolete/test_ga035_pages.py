#!/usr/bin/env python3
"""Teste GA035 Seitennummern"""

import json
import re

data = json.load(open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\pagebreak-books\GA035.json', encoding='utf-8'))
lectures = data.get('lectures', [])

print(f'Anzahl Vortraege: {len(lectures)}')
print()

for i, lec in enumerate(lectures[:3]):
    title = lec.get('title', '?')[:50]
    paras = lec.get('paragraphs', [])
    
    # Finde alle Seitenmarker im Vortrag
    all_markers = []
    for p in paras:
        content = p.get('content', '')
        markers = re.findall(r'\|(\d+)\|', content)
        all_markers.extend(markers)
    
    print(f'=== Vortrag {i+1}: {title} ===')
    if all_markers:
        print(f'  Seitenmarker: {all_markers[0]} bis {all_markers[-1]} ({len(all_markers)} total)')
    else:
        print(f'  Keine Seitenmarker gefunden!')
    
    # Zeige ersten Absatz
    if paras:
        first_content = paras[0].get('content', '')[:150]
        print(f'  Erster Absatz: {first_content}...')
    print()

