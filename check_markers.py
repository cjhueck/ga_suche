#!/usr/bin/env python3
"""Prüft page-break-markers.json für GA001 und GA002."""

import json
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for ga in ['GA001', 'GA002']:
    info = data.get(ga, {})
    breaks = info.get('breaks', [])
    print(f'{ga}:')
    print(f'  title: {info.get("title", "?")}')
    print(f'  contentRange: {info.get("contentRange", "?")}')
    print(f'  Anzahl breaks: {len(breaks)}')
    
    if breaks:
        print(f'  Erste 5 breaks:')
        for b in breaks[:5]:
            page = b.get("page", "?")
            left = (b.get("left") or "")[-40:]
            right = (b.get("right") or "")[:40]
            is_first = b.get("isFirstPage", False)
            print(f'    Seite {page}: {"[FIRST] " if is_first else ""}')
            print(f'      left: ...{left}')
            print(f'      right: {right}...')
    print()

