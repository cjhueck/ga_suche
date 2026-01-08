#!/usr/bin/env python3
"""Analysiert Fußnoten und Seitenmarker-Positionen in GA001"""

import json
import re

# Lade GA001
with open('steiner-books/steiner-books-001-001.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for book in data.get('books', []):
    if book.get('gaNumber', '').upper() == 'GA001':
        paras = book.get('paragraphs', [])
        
        print(f"GA001: {len(paras)} Absätze")
        
        # Suche nach Fußnoten-Patterns
        footnote_paras = []
        for i, p in enumerate(paras):
            content = p.get('content', '')
            # Typische Fußnoten-Patterns
            if re.search(r'^\s*\d+\s+[A-Z]', content) or re.search(r'^\s*\*\s', content):
                footnote_paras.append((i, content[:80]))
        
        print(f"\nMögliche Fußnoten-Absätze: {len(footnote_paras)}")
        for idx, text in footnote_paras[:5]:
            print(f"  [{idx}]: {text}...")
        
        # Zeige Absätze mit Seitenmarkern |9| bis |12|
        print("\n" + "="*60)
        print("Absätze mit Seitenmarkern |9| bis |15|:")
        print("="*60)
        
        for p in paras:
            content = p.get('content', '')
            for page in range(9, 16):
                marker = f"|{page}|"
                if marker in content:
                    idx = p.get('index', '?')
                    # Zeige Kontext um den Marker
                    pos = content.find(marker)
                    before = content[max(0, pos-50):pos]
                    after = content[pos+len(marker):pos+len(marker)+100]
                    print(f"\n{marker} in Absatz [{idx}]:")
                    print(f"  ...{before}{marker}{after}...")

