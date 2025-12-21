#!/usr/bin/env python3
"""Zeigt den Text einer PDF-Seite"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
pages = [int(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else [28, 37]

# Finde PDF
ga_num = ga.replace('GA', '').lower()
pdfs = [p for p in pdf_dir.glob("*.pdf") if ga_num in p.name.lower()]
if not pdfs:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"PDF: {pdf_path.name}\n")

doc = fitz.open(pdf_path)

# Wir müssen die PDF-Seite finden, die der gedruckten Seitenzahl entspricht
# Dazu suchen wir nach der Seitenzahl im Footer
def find_pdf_page_by_printed_number(doc, target_page):
    """Findet den PDF-Index für eine gedruckte Seitenzahl."""
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text")
        # Suche nach der Seitenzahl im Footer
        lines = text.strip().split('\n')
        for line in lines[-5:]:  # Letzte 5 Zeilen
            line = line.strip()
            if line.isdigit() and int(line) == target_page:
                return i
            if f"Seite: {target_page}" in line or f"- {target_page} -" in line:
                return i
    # Fallback: approximiere
    return target_page - 1 if target_page > 0 else 0

for target_page in pages:
    pdf_idx = find_pdf_page_by_printed_number(doc, target_page)
    if pdf_idx >= len(doc):
        print(f"Seite {target_page}: existiert nicht")
        continue
    
    page = doc[pdf_idx]
    text = page.get_text("text")
    
    print(f"=== Seite {target_page} (PDF-Index {pdf_idx}) ===")
    print(text[:1500])
    print("\n" + "="*60 + "\n")

doc.close()















