#!/usr/bin/env python3
"""Debug: Zeige GA035/17 vollständig"""
import json
import os

# Lade Vortrag aus steiner-full-lectures
lectures_dir = r'c:\Users\chuec\OneDrive\GitHub\ga_suche'
for fname in os.listdir(lectures_dir):
    if fname.startswith('steiner-full-lectures-') and fname.endswith('.json'):
        with open(os.path.join(lectures_dir, fname), encoding='utf-8') as f:
            data = json.load(f)
        for lec in data.get('lectures', []):
            if lec.get('ID') == 'GA035/17':
                print(f'Gefunden in: {fname}')
                print(f'Title: {lec.get("title", "N/A")}')
                paragraphs = lec.get('paragraphs', [])
                print(f'Anzahl Absaetze: {len(paragraphs)}')
                
                # Zeige ALLE Absätze
                print('\n=== Alle Absaetze ===')
                for i, p in enumerate(paragraphs):
                    text = p.get('text', '')
                    if text:
                        print(f'  [{i}] ({len(text)} Zeichen): {text[:80]}...')
                    else:
                        print(f'  [{i}] LEER (keys: {list(p.keys())})')
                
                # Zeige rohe Struktur eines Absatzes
                print('\n=== Rohe Struktur Absatz 0 ===')
                if paragraphs:
                    print(json.dumps(paragraphs[0], indent=2, ensure_ascii=False)[:500])
                break
        else:
            continue
        break

