#!/usr/bin/env python3
"""Prüft das neue Einzelseiten-PDF"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf_path = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\Steiner, Rudolf GA 069d, 2017 - Tod und Unsterblichkeit im Lichte_einzelseiten.pdf")

doc = fitz.open(pdf_path)
print(f"PDF: {pdf_path.name}")
print(f"Seiten: {len(doc)}")
print()

# Zeige erste 10 Seiten
for i in range(min(20, len(doc))):
    page = doc[i]
    text = page.get_text("text").strip()
    
    # Finde Seitenzahl im Footer
    lines = text.split('\n')
    page_num = "?"
    for line in lines[-3:]:
        if line.strip().isdigit():
            page_num = line.strip()
            break
    
    # Zeige ersten 50 Zeichen
    preview = text[:50].replace('\n', ' ')
    print(f"PDF-Index {i:3d}: Seite {page_num:>4s} - {preview}...")

doc.close()


