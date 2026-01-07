#!/usr/bin/env python3
import re
import sys

filepath = sys.argv[1] if len(sys.argv) > 1 else 'Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben/GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917.md'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

markers = re.findall(r'\|(\d+)\|', content)
print(f'Anzahl Marker: {len(markers)}')
print(f'Seitenzahlen: {sorted([int(m) for m in markers])}')

