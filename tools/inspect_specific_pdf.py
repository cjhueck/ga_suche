#!/usr/bin/env python3
"""Inspiziert ein spezifisches PDF"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\GA 68c - Goethe und die Gegenwart (325-510).pdf")

doc = fitz.open(pdf_path)
print(f"PDF: {pdf_path.name}")
print(f"Seiten: {len(doc)}")
print()

# Zeige erste Seiten
for i in range(min(10, len(doc))):
    page = doc[i]
    text = page.get_text("text").strip()
    
    if text:
        preview = text[:200].replace('\n', ' ')
        print(f"Seite {i}: {preview[:100]}...")
    else:
        print(f"Seite {i}: [LEER oder nur Bild]")

doc.close()

