#!/usr/bin/env python3
"""Kurzer Test: Erste 3 Vorträge von GA030"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher
import fitz

SCRIPT_DIR = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche')
PDF_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')

LIGATURES = {'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'}

def normalize_text(text):
    s = re.sub(r'<[^>]+>', ' ', text)
    s = s.replace('\u00ad', '').replace('\u00a0', ' ')
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    s = s.lower().replace('ß', 'ss')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# PDF finden
pdf_path = None
for p in PDF_DIR.glob('*.pdf'):
    if 'ga 030' in p.name.lower() or 'ga030' in p.name.lower():
        pdf_path = p
        break

print(f'PDF: {pdf_path.name if pdf_path else "NICHT GEFUNDEN"}')

# Vorträge laden
lectures = []
for jf in sorted(SCRIPT_DIR.glob('steiner-full-lectures-*.json')):
    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lec in data.get('lectures', []):
        if lec.get('gaNumber', '').upper() == 'GA030':
            lectures.append(lec)

# Sortieren nach lectureNumber
lectures.sort(key=lambda x: int(x.get('lectureNumber') or 0))
print(f'Vorträge gefunden: {len(lectures)}')
print()

# PDF öffnen und erste 100 Seiten extrahieren
print("Lade PDF...")
doc = fitz.open(pdf_path)
page_texts = []
for i in range(min(100, len(doc))):
    page = doc[i]
    text = page.get_text("text") or ""
    # Seitenzahl aus Footer
    page_num = i + 1  # Fallback
    blocks = page.get_text("blocks")
    for block in blocks:
        if len(block) >= 7 and block[6] == 0:
            t = (block[4] or "").strip()
            m = re.search(r"Seite:\s*(\d+)", t)
            if m:
                page_num = int(m.group(1))
                break
    page_texts.append((page_num, text))
doc.close()
print(f"Seiten geladen: {len(page_texts)}")
print()

# Nur erste 3 Vorträge testen
for i, lec in enumerate(lectures[:3]):
    lec_id = lec.get('ID', f'GA030/{i+1}')
    paras = lec.get('paragraphs', [])
    if not paras:
        print(f'{lec_id}: Keine Absätze')
        continue
    
    first_para = paras[0].get('content', '')
    first_norm = normalize_text(first_para)
    
    print(f'=== {lec_id} ===')
    print(f'Erster Absatz (erste 80 Zeichen):')
    print(f'  "{first_norm[:80]}..."')
    print()
    
    # Suche in PDF
    search_text = first_norm[:150]
    found_page = None
    
    for page_num, page_text in page_texts:
        page_norm = normalize_text(page_text)
        
        # Exakte Suche mit verschiedenen Längen
        for search_len in [120, 100, 80, 60, 40]:
            if search_len > len(search_text):
                continue
            search_key = search_text[:search_len]
            if search_key in page_norm:
                found_page = page_num
                print(f'  GEFUNDEN auf Seite {page_num} (exakt, {search_len} Zeichen)')
                break
        if found_page:
            break
    
    if not found_page:
        print(f'  NICHT GEFUNDEN (exakt)')
        # Fuzzy-Suche
        best_ratio = 0
        best_page = None
        for page_num, page_text in page_texts:
            page_norm = normalize_text(page_text)
            if len(page_norm) < 100:
                continue
            for start in range(0, min(len(page_norm) - 100, 2000), 50):
                window = page_norm[start:start + 100]
                ratio = SequenceMatcher(None, search_text[:100], window).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_page = page_num
        if best_ratio > 0.7:
            print(f'  Bestes Fuzzy-Match: Seite {best_page} ({best_ratio*100:.1f}%)')
        else:
            print(f'  Kein gutes Fuzzy-Match (bestes: {best_ratio*100:.1f}%)')
    print()

