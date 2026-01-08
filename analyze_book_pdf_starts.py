#!/usr/bin/env python3
"""
Analysiert die PDFs von Büchern, um die echten Startseiten zu finden.
Die Startseite ist die erste Seite mit dem eigentlichen Buchinhalt
(nach Titelseite, Inhaltsverzeichnis, Vorwort etc.)
"""

import sys
import os
from pathlib import Path

# PDF-Bibliothek
try:
    import fitz  # PyMuPDF
except ImportError:
    print("FEHLER: PyMuPDF nicht installiert. Installieren mit: pip install PyMuPDF")
    sys.exit(1)

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")

def find_pdf(ga_num: str) -> Path | None:
    """Findet PDF für eine GA-Nummer."""
    ga_num = ga_num.lower().replace("ga", "").strip()
    
    for pdf in PDF_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        if f"ga {ga_num}" in name_lower or f"ga{ga_num}" in name_lower:
            return pdf
    return None


def analyze_pdf_pages(pdf_path: Path, max_pages: int = 30):
    """
    Analysiert die ersten Seiten eines PDFs.
    Zeigt für jede Seite die Seitenzahl und den Textanfang.
    """
    doc = fitz.open(pdf_path)
    total = len(doc)
    
    print(f"\nPDF: {pdf_path.name}")
    print(f"Gesamt: {total} Seiten")
    print(f"\n{'='*80}")
    
    for i in range(min(max_pages, total)):
        page = doc[i]
        text = page.get_text("text").strip()
        
        # Erste 200 Zeichen des Textes
        preview = text[:300].replace('\n', ' ').strip()
        if len(text) > 300:
            preview += "..."
        
        # Suche nach gedruckter Seitenzahl im Text
        lines = text.split('\n')
        
        # Typische Seitenzahl-Patterns (erste oder letzte Zeilen)
        page_num_found = None
        for line in lines[:3] + lines[-3:]:
            line = line.strip()
            if line.isdigit() and 1 <= int(line) <= 999:
                page_num_found = int(line)
                break
        
        print(f"\nPDF-Index {i:3d} | Seiten-Nr: {page_num_found or '?':>4}")
        print(f"  {preview[:150]}")
    
    doc.close()


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python analyze_book_pdf_starts.py GA001 [GA002 ...]")
        print("\nVorhandene Bücher-PDFs:")
        for pdf in sorted(PDF_DIR.glob("*.pdf")):
            name = pdf.name.lower()
            # Nur niedrige GA-Nummern (Bücher)
            for i in range(1, 50):
                if f"ga {i:03d}" in name or f"ga{i:03d}" in name:
                    print(f"  {pdf.name}")
                    break
        return
    
    for ga in sys.argv[1:]:
        pdf_path = find_pdf(ga)
        if pdf_path:
            analyze_pdf_pages(pdf_path)
        else:
            print(f"\n{ga}: Keine PDF gefunden")


if __name__ == "__main__":
    main()

