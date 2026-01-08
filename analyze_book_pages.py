#!/usr/bin/env python3
"""Analysiert PDFs von Büchern um korrekte Startseiten zu finden."""

import fitz  # PyMuPDF
import re
import os
import sys
import io
from pathlib import Path

# Windows UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path("Steiner_GA_pdf")

def find_pdf(ga_num):
    """Findet PDF für eine GA-Nummer."""
    pattern = f"ga {ga_num:03d}" if isinstance(ga_num, int) else ga_num.lower()
    
    for pdf in PDF_DIR.glob("*.pdf"):
        if pattern in pdf.name.lower().replace(",", " "):
            return pdf
    return None

def analyze_pdf(ga_num):
    """Analysiert PDF und findet Seitennummerierung."""
    pdf_path = find_pdf(ga_num)
    if not pdf_path:
        print(f"GA{ga_num:03d}: Kein PDF gefunden")
        return
    
    print(f"\n{'='*60}")
    print(f"GA{ga_num:03d}: {pdf_path.name}")
    print(f"{'='*60}")
    
    doc = fitz.open(pdf_path)
    print(f"Gesamtseiten: {len(doc)}")
    
    # Suche nach Seitenzahlen in den ersten 30 Seiten
    print("\nErste Seiten mit erkannten Seitenzahlen:")
    
    page_numbers_found = []
    
    for i in range(min(30, len(doc))):
        page = doc[i]
        text = page.get_text("text")
        
        # Suche Seitenzahl am Anfang oder Ende der Seite
        lines = text.strip().split('\n')
        
        # Prüfe nur letzte 2 Zeilen (Seitenzahl meist unten)
        found = False
        for line in lines[-2:]:
            line = line.strip()
            # Nur einzelne Zahlen 1-999 (Seitenzahlen)
            if re.match(r'^\d{1,3}$', line):
                page_num = int(line)
                # Erwarte aufsteigende Seitenzahlen
                if 1 <= page_num <= 500:
                    # Prüfe ob plausibel (nahe am PDF-Index)
                    if not page_numbers_found or page_num > page_numbers_found[-1][1]:
                        page_numbers_found.append((i, page_num, line))
                        found = True
                        break
        
        # Zeige Seite mit Text-Preview
        preview = text[:200].replace('\n', ' ')[:80]
        
        # Seitenzahl in dieser Seite?
        found_num = None
        for pdf_idx, pn, _ in page_numbers_found:
            if pdf_idx == i:
                found_num = pn
                break
        
        if found_num or i < 15:
            status = f"[Seite {found_num}]" if found_num else "[keine SZ]"
            print(f"  PDF-Index {i:2d}: {status:12s} {preview}...")
    
    doc.close()
    
    # Zusammenfassung
    print(f"\nErkannte Seitenzahlen:")
    for pdf_idx, page_num, raw in page_numbers_found[:10]:
        print(f"  PDF-Index {pdf_idx} → Seitenzahl {page_num}")
    
    if page_numbers_found:
        first_page = page_numbers_found[0][1]
        print(f"\n→ Erste erkannte Seitenzahl: {first_page}")
        return first_page
    
    return None

# Analysiere GA001 und GA002
if __name__ == "__main__":
    for ga in [1, 2]:
        analyze_pdf(ga)

