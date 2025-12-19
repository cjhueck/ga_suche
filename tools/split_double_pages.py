#!/usr/bin/env python3
"""
Teilt ein Doppelseiten-PDF in Einzelseiten auf.

Verwendung:
  python tools/split_double_pages.py GA069D
  python tools/split_double_pages.py "Pfad/zum/input.pdf" "Pfad/zum/output.pdf"
"""
import sys
import io
import re
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")


def find_pdf_for_ga(ga_number: str) -> Path:
    """Findet die PDF-Datei für eine GA-Nummer."""
    ga_num = ga_number.upper().replace('GA', '').lower()
    for pdf_file in PDF_DIR.glob("*.pdf"):
        if ga_num in pdf_file.name.lower():
            return pdf_file
    raise FileNotFoundError(f"Kein PDF für {ga_number} gefunden")


def split_double_pages(input_path: Path, output_path: Path = None):
    """
    Teilt ein Doppelseiten-PDF in Einzelseiten auf.
    
    Jede Doppelseite wird in zwei Einzelseiten aufgeteilt:
    - Linke Hälfte -> erste neue Seite
    - Rechte Hälfte -> zweite neue Seite
    """
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_einzelseiten.pdf"
    
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    
    # Öffne das Quell-PDF
    src_doc = fitz.open(input_path)
    
    # Erstelle ein neues PDF
    dst_doc = fitz.open()
    
    total_pages = len(src_doc)
    print(f"Quell-Seiten: {total_pages}")
    
    # Schwellwert für Doppelseiten-Erkennung
    # Wenn Breite > 1.3 * Höhe, ist es wahrscheinlich eine Doppelseite
    ASPECT_THRESHOLD = 1.3
    
    single_count = 0
    double_count = 0
    
    for i in range(total_pages):
        src_page = src_doc[i]
        width = src_page.rect.width
        height = src_page.rect.height
        aspect = width / height if height > 0 else 1
        
        if aspect > ASPECT_THRESHOLD:
            # Doppelseite -> in zwei Einzelseiten aufteilen
            double_count += 1
            
            # Linke Hälfte (gerade Seitenzahl im Buch)
            left_rect = fitz.Rect(0, 0, width / 2, height)
            left_page = dst_doc.new_page(width=width/2, height=height)
            left_page.show_pdf_page(left_page.rect, src_doc, i, clip=left_rect)
            
            # Rechte Hälfte (ungerade Seitenzahl im Buch)
            right_rect = fitz.Rect(width / 2, 0, width, height)
            right_page = dst_doc.new_page(width=width/2, height=height)
            right_page.show_pdf_page(right_page.rect, src_doc, i, clip=right_rect)
            
        else:
            # Einzelseite -> direkt kopieren
            single_count += 1
            dst_doc.insert_pdf(src_doc, from_page=i, to_page=i)
        
        # Fortschritt
        if (i + 1) % 50 == 0:
            print(f"  Verarbeitet: {i + 1}/{total_pages}")
    
    print(f"\nErgebnis:")
    print(f"  Einzelseiten (unverändert): {single_count}")
    print(f"  Doppelseiten (aufgeteilt):  {double_count}")
    print(f"  Neue Seitenanzahl: {len(dst_doc)}")
    
    # Speichern
    dst_doc.save(output_path)
    dst_doc.close()
    src_doc.close()
    
    print(f"\n✓ Gespeichert: {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python tools/split_double_pages.py GA069D")
        print("  python tools/split_double_pages.py input.pdf [output.pdf]")
        sys.exit(1)
    
    arg1 = sys.argv[1]
    
    # Prüfe ob es eine GA-Nummer ist
    if re.match(r"^GA?\d+[a-z]?$", arg1, re.IGNORECASE):
        input_path = find_pdf_for_ga(arg1)
        output_path = input_path.parent / f"{input_path.stem}_einzelseiten.pdf"
    else:
        input_path = Path(arg1)
        if len(sys.argv) > 2:
            output_path = Path(sys.argv[2])
        else:
            output_path = input_path.parent / f"{input_path.stem}_einzelseiten.pdf"
    
    if not input_path.exists():
        print(f"Datei nicht gefunden: {input_path}")
        sys.exit(1)
    
    split_double_pages(input_path, output_path)


if __name__ == "__main__":
    main()










