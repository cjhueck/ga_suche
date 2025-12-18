#!/usr/bin/env python3
"""Prüfe API-Antworten für GA035 Vorträge"""
import urllib.request
import json
import re

def check_lecture(lecture_num):
    url = f'http://localhost:3003/api/full-lecture/GA035/{lecture_num}'
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
        
        lecture = data.get('lecture', {})
        paragraphs = lecture.get('paragraphs', [])
        
        # Finde Marker in allen Absätzen
        all_text = ' '.join(p.get('text', '') for p in paragraphs)
        markers = re.findall(r'\|(\d+)\|', all_text)
        
        if markers:
            return f'GA035/{lecture_num}: {len(paragraphs)} Absätze, Seiten {markers[0]}-{markers[-1]} ({len(markers)} Marker)'
        else:
            # Zeige ersten Absatz
            first_text = paragraphs[0].get('text', '')[:100] if paragraphs else 'LEER'
            return f'GA035/{lecture_num}: {len(paragraphs)} Absätze, KEINE MARKER! Erster Text: {first_text}...'
    except Exception as e:
        return f'GA035/{lecture_num}: FEHLER - {e}'

print('=== API-Antworten für GA035 ===')
for i in range(1, 20):
    result = check_lecture(i)
    print(result)

