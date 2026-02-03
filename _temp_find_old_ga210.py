#!/usr/bin/env python3
"""Sucht alte GA210-Daten in D:\steiner-full-lectures"""

import json
import os

parts_dir = 'D:/steiner-full-lectures'
found_lectures = []

print("Suche GA210 in Part-Dateien auf D:...")
print()

for filename in sorted(os.listdir(parts_dir)):
    if not filename.endswith('.json'):
        continue
    
    filepath = os.path.join(parts_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        lectures = data.get('lectures', [])
        for lecture in lectures:
            lid = lecture.get('ID', '')
            if lid.upper().startswith('GA210'):
                paras = lecture.get('paragraphs', [])
                first_id = paras[0].get('index', '?') if paras else '?'
                found_lectures.append({
                    'file': filename,
                    'lecture_id': lid,
                    'paragraph_count': len(paras),
                    'first_id': first_id
                })
                print(f"Gefunden: {lid} in {filename}")
                print(f"  Paragraphen: {len(paras)}, Erste ID: {first_id}")
    except Exception as e:
        pass

print()
print(f"Gesamt: {len(found_lectures)} GA210-Vorträge gefunden")

if found_lectures:
    # Zeige Beispiel-IDs
    print()
    print("Beispiel alte IDs:")
    filepath = os.path.join(parts_dir, found_lectures[0]['file'])
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for lecture in data.get('lectures', []):
        if lecture.get('ID', '').upper().startswith('GA210'):
            paras = lecture.get('paragraphs', [])[:5]
            for p in paras:
                print(f"  {p.get('index', '?')}: {p.get('content', '')[:60]}...")
            break
