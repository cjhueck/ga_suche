#!/usr/bin/env python3
"""Zeigt die Sequenz der extrahierten Seitenzahlen"""
import json
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'

markers = json.load(open('page-break-markers.json', 'r', encoding='utf-8'))
if ga not in markers:
    print(f"{ga} nicht gefunden")
    sys.exit(1)

breaks = markers[ga].get('breaks', [])

print(f"=== Seitenzahlen-Sequenz für {ga} (erste 50) ===\n")

prev_page = 0
for i, b in enumerate(breaks[:50]):
    page = b.get('page', 0)
    gap = "" if page == prev_page + 1 else f" [SPRUNG von {prev_page}!]" if page > prev_page + 1 else ""
    right_preview = (b.get('right', '') or '')[:40].replace('\n', ' ')
    print(f"PDF-Index {i:3d}: Seite {page:4d}{gap} - {right_preview}")
    prev_page = page

print(f"\n... (insgesamt {len(breaks)} Breaks)")










