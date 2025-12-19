#!/usr/bin/env python3
"""Analysiert den Status einer GA im Seitenzahlen-Workflow"""
import json
import sys
import io
from pathlib import Path

# Windows UTF-8 Support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068A'
if not ga.startswith('GA'):
    ga = f'GA{ga}'

print(f"=== Analyse für {ga} ===\n")

# 1. PDF vorhanden?
pdf_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
pdfs = list(pdf_dir.glob(f"*{ga.replace('GA', 'GA ')}*")) + list(pdf_dir.glob(f"*{ga}*"))
print(f"1. PDF vorhanden:")
if pdfs:
    for p in pdfs[:3]:
        print(f"   ✓ {p.name}")
else:
    print(f"   ✗ Kein PDF gefunden")

# 2. Seitenzahlen extrahiert?
print(f"\n2. Seitenzahlen extrahiert (page-break-markers.json):")
try:
    markers = json.load(open('page-break-markers.json', 'r', encoding='utf-8'))
    ga_markers = markers.get(ga, {})
    if ga_markers:
        print(f"   ✓ {len(ga_markers.get('breaks', []))} Breaks")
    else:
        print(f"   ✗ Nicht vorhanden")
except Exception as e:
    print(f"   ✗ Fehler: {e}")

# 3. Lecture-Mapping vorhanden?
print(f"\n3. Lecture-Page-Mapping (lecture-page-mapping.json):")
try:
    mapping = json.load(open('lecture-page-mapping.json', 'r', encoding='utf-8'))
    ga_entries = [k for k in mapping.keys() if ga in k.upper()]
    if ga_entries:
        print(f"   ✓ {len(ga_entries)} Einträge")
    else:
        print(f"   ✗ Keine Einträge")
except Exception as e:
    print(f"   ✗ Fehler: {e}")

# 4. In steiner-full-lectures vorhanden?
print(f"\n4. In steiner-full-lectures-*.json:")
found_lectures = 0
source_file = None
for f in Path('.').glob('steiner-full-lectures-*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        lectures = data.get('lectures', [])
        matching = [l for l in lectures if (l.get('gaNumber', '') or '').upper() == ga]
        if matching:
            found_lectures += len(matching)
            source_file = f.name
    except:
        pass
if found_lectures:
    print(f"   ✓ {found_lectures} Vorträge in {source_file}")
else:
    print(f"   ✗ Nicht vorhanden")

# 5. pagebreak-books Datei vorhanden?
print(f"\n5. pagebreak-books/{ga}.json:")
pb_file = Path(f'pagebreak-books/{ga}.json')
if pb_file.exists():
    try:
        data = json.load(open(pb_file, 'r', encoding='utf-8'))
        lectures = data.get('lectures', [])
        if lectures:
            # Zähle Marker in Vorträgen
            total_markers = 0
            for lec in lectures:
                for p in lec.get('paragraphs', []):
                    content = p.get('content', '')
                    if '|' in content:
                        import re
                        total_markers += len(re.findall(r'\|\d+\|', content))
            print(f"   ✓ {len(lectures)} Vorträge, {total_markers} Seitenmarker")
        else:
            book = data.get('book', data)
            paras = book.get('paragraphs', [])
            print(f"   ✓ Buch mit {len(paras)} Paragraphen")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
else:
    print(f"   ✗ Nicht vorhanden")

# 6. Empfehlung
print(f"\n=== Empfehlung ===")
if not pdfs:
    print("→ Kein PDF vorhanden - kann nicht verarbeitet werden")
elif not ga_markers:
    print("→ Führe aus: python export_page_markers_v4.py " + ga)
elif not ga_entries:
    print("→ Führe aus: python generate_lecture_page_mapping.py " + ga)
elif not pb_file.exists():
    print("→ Führe aus: python apply_page_break_markers_v4.py " + ga)
    print("→ Dann: Copy-Item -Path \"" + ga + "-with-pagebreaks.json\" -Destination \"pagebreak-books\\" + ga + ".json\" -Force")
else:
    print("→ Alles vorhanden! Server neu laden: Invoke-RestMethod -Uri 'http://localhost:3003/api/reload-books' -Method POST")









