#!/usr/bin/env python3
"""Zeigt detaillierte Informationen über eine PDF-Seite"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA069D'
pdf_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 8

ga_num = ga.replace('GA', '').lower()
pdf_path = None
for p in PDF_DIR.glob("*.pdf"):
    if ga_num in p.name.lower():
        pdf_path = p
        break

if not pdf_path:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

doc = fitz.open(pdf_path)
print(f"PDF: {pdf_path.name}")
print(f"PDF-Index: {pdf_idx}")
print(f"Seitenbreite: {doc[pdf_idx].rect.width:.0f}")
print(f"Seitenhöhe: {doc[pdf_idx].rect.height:.0f}")
print()

page = doc[pdf_idx]

# Zeige alle Textblöcke mit Position
print("=== Textblöcke (sortiert nach Y, dann X) ===\n")
blocks = page.get_text("blocks")

# Sortiere nach Y (oben nach unten), dann X (links nach rechts)
blocks_sorted = sorted(blocks, key=lambda b: (b[1], b[0]))

for i, block in enumerate(blocks_sorted[:30]):
    if len(block) < 7 or block[6] != 0:
        continue
    x0, y0, x1, y1 = block[:4]
    text = (block[4] or "").strip().replace('\n', ' ')[:60]
    
    # Bestimme Position (links/rechts basierend auf Seitenmitte)
    page_mid = page.rect.width / 2
    pos = "LINKS" if x0 < page_mid else "RECHTS"
    
    print(f"Block {i:2d}: x={x0:6.1f}-{x1:6.1f}, y={y0:6.1f}-{y1:6.1f} [{pos:6s}] '{text}'")

# Suche nach Seitenzahlen im unteren Bereich
print("\n=== Mögliche Seitenzahlen (untere 15%) ===\n")
footer_threshold = page.rect.height * 0.85

for block in blocks:
    if len(block) < 7 or block[6] != 0:
        continue
    x0, y0, x1, y1 = block[:4]
    text = (block[4] or "").strip()
    
    if y1 > footer_threshold:
        page_mid = page.rect.width / 2
        pos = "LINKS" if x0 < page_mid else "RECHTS"
        print(f"  x={x0:6.1f}, y={y1:6.1f} [{pos:6s}]: '{text}'")

doc.close()














