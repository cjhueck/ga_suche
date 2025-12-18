#!/usr/bin/env python3
"""Test: Wo kommt der Text von GA030/2 im PDF vor?"""

import json
import re
from pathlib import Path
import fitz

SCRIPT_DIR = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche')
PDF_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')

def normalize_text(text):
    s = re.sub(r'<[^>]+>', ' ', text)
    s = s.replace('\u00ad', '').replace('\u00a0', ' ')
    s = s.lower().replace('ß', 'ss')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# PDF finden
pdf_path = None
for p in PDF_DIR.glob('*.pdf'):
    if 'ga 030' in p.name.lower():
        pdf_path = p
        break

# Vorträge laden - GA030/2
lectures = []
for jf in sorted(SCRIPT_DIR.glob('steiner-full-lectures-*.json')):
    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lec in data.get('lectures', []):
        if lec.get('ID') == 'GA030/2':
            lectures.append(lec)
            break

lec = lectures[0]
first_para = lec['paragraphs'][0]['content']
search_text = normalize_text(first_para)[:80]

print(f"Suche nach GA030/2:")
print(f'  "{search_text}..."')
print()

# PDF durchsuchen - ALLE Vorkommen
doc = fitz.open(pdf_path)
print(f"PDF: {len(doc)} Seiten")
print()

found_pages = []
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text") or ""
    page_norm = normalize_text(text)
    
    if search_text[:60] in page_norm:
        # Seitenzahl aus Footer
        page_num = i + 1
        blocks = page.get_text("blocks")
        for block in blocks:
            if len(block) >= 7 and block[6] == 0:
                t = (block[4] or "").strip()
                m = re.search(r"Seite:\s*(\d+)", t)
                if m:
                    page_num = int(m.group(1))
                    break
        found_pages.append((i, page_num))
        print(f"  GEFUNDEN auf PDF-Index {i} (Seitenzahl: {page_num})")

doc.close()

print()
print(f"Gesamt: {len(found_pages)} Vorkommen")

