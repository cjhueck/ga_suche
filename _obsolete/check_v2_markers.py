#!/usr/bin/env python3
"""Prüfe V2-Marker für GA035"""
import json

data = json.load(open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\page-markers.json', encoding='utf-8'))
ga035 = data.get('GA035', {})

print('=== page-markers.json (V2) für GA035 ===')
if ga035:
    print(f'Keys: {list(ga035.keys())}')
    markers = ga035.get('markers', [])
    print(f'Anzahl Marker: {len(markers)}')
    if markers:
        print(f'Beispiel: {markers[0]}')
else:
    print('GA035 NICHT VORHANDEN in V2-Daten')

