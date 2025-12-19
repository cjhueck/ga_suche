#!/usr/bin/env python3
"""Zeigt den vollständigen Text einer PDF-Seite nach gedruckter Seitenzahl"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
target_pages = [int(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else [28]

# Finde PDF
ga_num = ga.replace('GA', '').lower()
pdfs = [p for p in pdf_dir.glob("*.pdf") if ga_num in p.name.lower()]
if not pdfs:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"PDF: {pdf_path.name}\n")

doc = fitz.open(pdf_path)

# Finde alle Seiten und ihre gedruckten Seitenzahlen
for target in target_pages:
    # Suche die PDF-Seite, die diese gedruckte Seitenzahl hat
    for i in range(max(0, target - 5), min(len(doc), target + 5)):
        page = doc[i]
        text = page.get_text("text")
        lines = text.strip().split('\n')
        
        # Prüfe ob diese Seite die gesuchte Seitenzahl enthält
        found_num = None
        for line in lines[-5:]:
            line_clean = line.strip()
            if line_clean.isdigit():
                found_num = int(line_clean)
                break
            if f"- {target} -" in line_clean or f"Seite: {target}" in line_clean:
                found_num = target
                break
        
        if found_num == target:
            print(f"=== Gedruckte Seite {target} (PDF-Index {i}) ===")
            print(text)
            print("=" * 60 + "\n")
            break
    else:
        # Fallback: verwende PDF-Index direkt
        if target < len(doc):
            page = doc[target]
            text = page.get_text("text")
            print(f"=== PDF-Index {target} (Fallback) ===")
            print(text)
            print("=" * 60 + "\n")

doc.close()










