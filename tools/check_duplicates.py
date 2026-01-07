#!/usr/bin/env python3
"""Prüft auf doppelte Seitenzahlen in allen GA072 Vorträgen."""
import json
import re
from collections import Counter

with open('steiner-full-lectures/steiner-full-lectures-014-354-part04.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Prüfe GA072 Vorträge auf Duplikate und Reihenfolge-Probleme:\n")

for lec in data['lectures']:
    if not lec['ID'].startswith('GA072/'):
        continue
    
    text = ' '.join([p.get('content', '') for p in lec['paragraphs']])
    markers = re.findall(r'\|(\d+)\|', text)
    page_nums = [int(m) for m in markers]
    
    # Prüfe auf Duplikate
    counts = Counter(page_nums)
    duplicates = {p: c for p, c in counts.items() if c > 1}
    
    # Prüfe auf nicht-aufsteigende Reihenfolge
    out_of_order = []
    for i in range(1, len(page_nums)):
        if page_nums[i] <= page_nums[i-1]:
            out_of_order.append((page_nums[i-1], page_nums[i]))
    
    if duplicates or out_of_order:
        print(f"{lec['ID']}:")
        if duplicates:
            print(f"  Duplikate: {duplicates}")
        if out_of_order:
            print(f"  Reihenfolge-Fehler: {out_of_order[:5]}...")
        print()

