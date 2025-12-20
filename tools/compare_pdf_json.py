#!/usr/bin/env python3
"""Vergleicht PDF-Text mit JSON-Text für einen Vortrag"""
import json
import sys
import io
import re
import fitz
from pathlib import Path
from difflib import SequenceMatcher

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068C'
lec_num = sys.argv[2] if len(sys.argv) > 2 else '26'

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")

def normalize(text):
    s = re.sub(r"<[^>]+>", " ", text)
    s = s.lower()
    s = s.replace("ß", "ss")
    s = s.replace("\u00ad", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Lade Vortrag aus JSON
lecture = None
for f in Path('.').glob('steiner-full-lectures-*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        for lec in data.get('lectures', []):
            if lec.get('gaNumber', '').upper() == ga and str(lec.get('lectureNumber')) == lec_num:
                lecture = lec
                break
    except:
        pass
    if lecture:
        break

if not lecture:
    print(f"Vortrag {ga}/{lec_num} nicht gefunden")
    sys.exit(1)

print(f"=== Vortrag {ga}/{lec_num}: {lecture.get('title', '')} ===\n")

# JSON-Text
paras = lecture.get('paragraphs', [])
json_text = ""
for p in paras[:5]:
    json_text += " " + (p.get('content', ''))
json_norm = normalize(json_text)

print(f"JSON-Text (erste 300 Zeichen):")
print(f"  {json_norm[:300]}")
print()

# Lade PDF
pdf_path = None
ga_num = ga.replace('GA', '').lower()
for p in PDF_DIR.glob("*.pdf"):
    if ga_num in p.name.lower():
        pdf_path = p
        break

if not pdf_path:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

print(f"PDF: {pdf_path.name}\n")

# Suche im PDF nach Titel
title = lecture.get('title', '')
title_norm = normalize(title)[:30]

doc = fitz.open(pdf_path)
print(f"Suche nach Titel '{title_norm}'...\n")

for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text")
    text_norm = normalize(text)
    
    if title_norm in text_norm:
        # Zeige die Seite
        print(f"=== Titel gefunden auf PDF-Seite {i} ===")
        print(f"PDF-Text (erste 500 Zeichen):")
        print(f"  {text_norm[:500]}")
        print()
        
        # Vergleiche mit JSON
        json_key = json_norm[:100]
        if json_key in text_norm:
            print("  ✓ JSON-Text gefunden in dieser PDF-Seite!")
        else:
            print("  ✗ JSON-Text NICHT gefunden")
            print(f"\n  JSON-Anfang: {json_norm[:150]}")
            print(f"\n  PDF-Anfang (nach Titel):")
            pos = text_norm.find(title_norm)
            if pos >= 0:
                print(f"    {text_norm[pos:pos+300]}")
        break
else:
    print(f"Titel '{title_norm}' nicht im PDF gefunden")
    print("\nSuche nach ähnlichen Seiten...")
    
    # Zeige alle Seiten mit "goethe" und "faust"
    for i in range(len(doc)):
        text = normalize(doc[i].get_text("text"))
        if "faust" in text and i > 300:
            lines = text.split()[:20]
            print(f"  Seite {i}: {' '.join(lines)[:80]}...")

doc.close()












