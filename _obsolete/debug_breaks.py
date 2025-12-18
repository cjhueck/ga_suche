#!/usr/bin/env python3
"""Debug page breaks"""
import json

data = json.load(open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\page-break-markers.json', encoding='utf-8'))
ga035 = data.get('GA035', {}).get('breaks', [])

print(f'GA035: {len(ga035)} Breaks')
print()

# Zeige Breaks um Seite 112 (wo das Problem auftrat)
for b in ga035:
    if 110 <= b.get('page', 0) <= 118:
        left = b.get('left', '')
        right = b.get('right', '')
        print(f"Seite {b.get('page')}: hyphenated={b.get('hyphenated')}")
        print(f"  left: ...{left[-60:]}")
        print(f"  right: {right[:60]}...")
        print()

