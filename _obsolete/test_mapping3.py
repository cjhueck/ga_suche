#!/usr/bin/env python3
"""Test: Was steht auf PDF-Index 22?"""

import re
from pathlib import Path
import fitz

PDF_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')

# PDF finden
pdf_path = None
for p in PDF_DIR.glob('*.pdf'):
    if 'ga 030' in p.name.lower():
        pdf_path = p
        break

doc = fitz.open(pdf_path)
page = doc[22]  # PDF-Index 22

print(f"PDF-Index 22:")
print(f"="*60)

# Alle Blöcke mit Y-Position anzeigen
blocks = page.get_text("blocks")
page_height = page.rect.height

print(f"Seitenhöhe: {page_height}")
print()
print("Blöcke (sortiert nach Y-Position):")
print()

sorted_blocks = sorted([b for b in blocks if len(b) >= 7 and b[6] == 0], key=lambda b: b[1])

for b in sorted_blocks[-5:]:  # Letzte 5 Blöcke (unten)
    y0, y1 = b[1], b[3]
    text = b[4].strip()[:80] if b[4] else ""
    y_ratio = y0 / page_height
    print(f"  Y={y0:.0f} ({y_ratio*100:.0f}%): \"{text}\"")

print()
print("Suche nach 'Seite:' im Text:")
full_text = page.get_text("text")
for line in full_text.split("\n"):
    if "Seite" in line or line.strip().isdigit():
        print(f"  {line.strip()}")

doc.close()

