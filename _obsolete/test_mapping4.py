#!/usr/bin/env python3
"""Test: Korrekte Seitenzahl-Extraktion"""

import re
from pathlib import Path
import fitz

PDF_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')

def extract_page_number(page, pdf_index):
    """Korrekte Seitenzahl-Extraktion (wie im Original)"""
    page_height = page.rect.height
    blocks = page.get_text("blocks")
    max_page = 1000
    
    footer_threshold = page_height * 0.85
    candidates = []
    
    for block in blocks:
        if len(block) < 7 or block[6] != 0:
            continue
        y_bottom = float(block[3])
        text = (block[4] or "").strip()
        if not text or y_bottom < footer_threshold:
            continue
        
        # Muster: "Seite: X" oder "Seite: 2 3" (mit Leerzeichen!)
        m = re.search(r"Seite:\s*([\d\s]+)", text)
        if m:
            num_str = m.group(1).replace(" ", "").strip()
            if num_str.isdigit():
                num = int(num_str)
                if 1 <= num <= max_page:
                    candidates.append((num, 10, y_bottom))
                    continue
        
        # Muster: "- 123 -"
        m = re.search(r"[-–—]\s*(\d+)\s*[-–—]", text)
        if m:
            num = int(m.group(1))
            if 1 <= num <= max_page:
                candidates.append((num, 8, y_bottom))
                continue
        
        # Muster: Standalone-Zahl
        compact = text.replace(" ", "")
        if re.fullmatch(r"[\(\[\{<]*\d{1,4}[\)\]\}>]*[.\-–—,:;!]*", compact):
            num = int(re.search(r"\d{1,4}", compact).group(0))
            if 1 <= num <= max_page and num < 1000:
                candidates.append((num, 5, y_bottom))
    
    if candidates:
        candidates.sort(key=lambda c: (-c[1], -c[2]))
        return candidates[0][0]
    
    return pdf_index + 1

# PDF finden
pdf_path = None
for p in PDF_DIR.glob('*.pdf'):
    if 'ga 030' in p.name.lower():
        pdf_path = p
        break

doc = fitz.open(pdf_path)

print("Teste Seitenzahl-Extraktion für PDF-Index 20-25:")
print()

for i in range(20, 26):
    page = doc[i]
    page_num = extract_page_number(page, i)
    print(f"  PDF-Index {i:2d} -> Seitenzahl: {page_num}")

doc.close()

