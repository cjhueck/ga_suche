#!/usr/bin/env python3
"""Zeigt alle Vorträge einer GA und prüft ob sie im PDF sind"""
import json
import sys
import io
import re
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068C'
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")

def normalize(text):
    s = re.sub(r"<[^>]+>", " ", text)
    s = s.lower()
    s = s.replace("ß", "ss")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Lade Vorträge
lectures = []
for f in Path('.').glob('steiner-full-lectures-*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        for lec in data.get('lectures', []):
            if lec.get('gaNumber', '').upper() == ga:
                lectures.append(lec)
    except:
        pass

lectures.sort(key=lambda x: int(x.get('lectureNumber', 0)))
print(f"=== {ga}: {len(lectures)} Vorträge ===\n")

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

doc = fitz.open(pdf_path)
full_pdf_text = ""
for i in range(len(doc)):
    full_pdf_text += doc[i].get_text("text")
doc.close()
full_pdf_norm = normalize(full_pdf_text)

# Prüfe jeden Vortrag
for lec in lectures:
    num = lec.get('lectureNumber', '?')
    title = lec.get('title', '')[:40]
    paras = lec.get('paragraphs', [])
    
    # Finde ersten echten Fließtext
    first_text = ""
    for p in paras[:10]:
        content = normalize(p.get('content', ''))
        if len(content) > 50:
            first_text = content
            break
    
    if not first_text:
        print(f"  {num}: KEIN TEXT - {title}")
        continue
    
    # Suche im PDF
    search_key = first_text[:80]
    found = "✓" if search_key in full_pdf_norm else "✗"
    
    print(f"  {num}: {found} - {title}")
    if found == "✗":
        print(f"       Suchtext: {search_key[:60]}...")












