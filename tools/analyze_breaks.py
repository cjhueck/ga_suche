#!/usr/bin/env python3
"""Analysiert die Breaks für eine GA"""
import json
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 28
end_page = int(sys.argv[3]) if len(sys.argv) > 3 else 43

# Lade Breaks
markers = json.load(open('page-break-markers.json', 'r', encoding='utf-8'))
if ga not in markers:
    print(f"{ga} nicht in page-break-markers.json")
    sys.exit(1)

breaks = markers[ga].get('breaks', [])
print(f"=== Breaks für {ga}, Seiten {start_page}-{end_page} ===\n")

# Lade auch den JSON-Text des ersten Vortrags
json_text = ""
for f in ['steiner-full-lectures-030-100-part01.json', 'steiner-full-lectures-030-100-part02.json', 
          'steiner-full-lectures-030-100-part03.json', 'steiner-full-lectures-030-354-part02.json',
          'steiner-full-lectures-030-354-part03.json']:
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        for lec in data.get('lectures', []):
            if lec.get('gaNumber', '').upper() == ga and str(lec.get('lectureNumber')) == '5':
                paras = lec.get('paragraphs', [])
                json_text = ' '.join(p.get('content', '') for p in paras)
                print(f"Quelle: {f}")
                break
    except:
        pass
    if json_text:
        break

# Normalisierungsfunktion (vereinfacht)
def normalize(text):
    if not text:
        return ""
    s = text.lower()
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('ß', 'ss')
    return s.strip()

json_norm = normalize(json_text)

# Zeige Breaks und prüfe Matching
for b in sorted(breaks, key=lambda x: x.get('page', 0)):
    page = b.get('page', 0)
    if page < start_page or page > end_page:
        continue
    
    left = b.get('left', '')[-50:]
    right = b.get('right', '')[:50]
    
    # Prüfe ob right im JSON vorkommt
    right_norm = normalize(right)
    found = "✓" if right_norm[:30] in json_norm else "✗"
    
    print(f"Seite {page}: {found}")
    print(f"  LEFT:  ...{left}")
    print(f"  RIGHT: {right}...")
    print()











