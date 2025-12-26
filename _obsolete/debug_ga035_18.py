#!/usr/bin/env python3
"""Debug: Prüfe GA035/18 Marker"""
import json
import re

# Lade pagebreaks/GA035.json
with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\pagebreaks\GA035.json', encoding='utf-8') as f:
    data = json.load(f)

for lecture in data.get('lectures', []):
    if lecture.get('ID') == 'GA035/18':
        print('=== GA035/18 ===')
        paragraphs = lecture.get('paragraphs', [])
        print(f'Anzahl Absaetze: {len(paragraphs)}')
        
        # Finde alle Marker
        all_text = ' '.join(p.get('content', p.get('text', '')) for p in paragraphs)
        markers = re.findall(r'\|(\d+)\|', all_text)
        
        print(f'Alle Marker: {markers}')
        print(f'Letzter Marker: {markers[-1] if markers else "KEINE"}')
        
        # Zeige letzten Absatz
        if paragraphs:
            last_para = paragraphs[-1].get('content', paragraphs[-1].get('text', ''))
            print(f'\nLetzter Absatz ({len(last_para)} Zeichen):')
            print(last_para[-500:] if len(last_para) > 500 else last_para)
        break

