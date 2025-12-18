#!/usr/bin/env python3
"""
Spezielles Export-Skript für GA069a
Die Seitenzahlen sind in diesem PDF nicht im Footer, sondern weiter oben auf der Seite.
"""

import fitz
import json
import re
from pathlib import Path

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\page-break-markers.json")

LEFT_CHARS = 200
RIGHT_CHARS = 200

def main():
    # Lade existierende Marker
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for pdf_path in PDF_DIR.glob("*069a*"):
        print(f"PDF: {pdf_path.name}")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Seiten: {total_pages}")
        
        # Extrahiere Seitenzahlen mit angepasster Methode
        page_numbers = {}
        
        for page_idx in range(total_pages):
            page = doc[page_idx]
            h = page.rect.height
            
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        bbox = line.get("bbox", [0,0,0,0])
                        y = bbox[1]
                        spans = line.get("spans", [])
                        text = "".join(s.get("text", "") for s in spans).strip()
                        
                        # Suche nach kurzen Zahlenzeilen (1-4 Zeichen, nur Ziffern)
                        # im Bereich Y > 300 (untere Hälfte der Seite)
                        if text and text.isdigit() and len(text) <= 4 and y > 300:
                            num = int(text)
                            if 1 <= num <= 500:  # Plausible Seitenzahl
                                page_numbers[page_idx] = num
                                break
        
        print(f"Extrahierte Seitenzahlen: {len(page_numbers)} von {total_pages}")
        
        # Zeige ein paar Beispiele
        samples = list(page_numbers.items())[:5]
        for idx, num in samples:
            print(f"  PDF-Index {idx} -> Seite {num}")
        
        # Erstelle Breaks mit korrekten Seitenzahlen
        breaks = []
        
        # Erste Seite mit Text
        first_page_num = None
        for i in range(total_pages):
            if i in page_numbers:
                page = doc[i]
                body = page.get_text("text").strip()
                # Entferne Seitenzahl am Ende
                lines = body.split("\n")
                if lines and lines[-1].strip().isdigit():
                    lines = lines[:-1]
                    body = "\n".join(lines)
                
                if len(body) > 100:
                    right = body[:RIGHT_CHARS]
                    first_page_num = page_numbers[i]
                    breaks.append({
                        "page": first_page_num,
                        "pdfFrom": None,
                        "pdfTo": i,
                        "left": None,
                        "right": right,
                        "hyphenated": False,
                        "printedPageConfidence": "extracted",
                        "isFirstPage": True
                    })
                    print(f"\nErste Textseite: Seite {first_page_num} (PDF-Index {i})")
                    break
        
        # Reguläre Breaks
        for i in range(total_pages - 1):
            if (i + 1) not in page_numbers:
                continue
                
            left_page = doc[i]
            right_page = doc[i + 1]
            
            left_text = left_page.get_text("text").strip()
            right_text = right_page.get_text("text").strip()
            
            if not left_text and not right_text:
                continue
            
            # Entferne die Seitenzahl aus dem Text (sie ist am Ende)
            left_lines = left_text.split("\n")
            if left_lines and left_lines[-1].strip().isdigit():
                left_lines = left_lines[:-1]
                left_text = "\n".join(left_lines)
            
            right_lines = right_text.split("\n")
            if right_lines and right_lines[-1].strip().isdigit():
                right_lines = right_lines[:-1]
                right_text = "\n".join(right_lines)
            
            left = left_text[-LEFT_CHARS:] if len(left_text) > LEFT_CHARS else left_text
            right = right_text[:RIGHT_CHARS] if len(right_text) > RIGHT_CHARS else right_text
            
            hyphenated = bool(left.rstrip()) and left.rstrip()[-1] in {"-", "¬", "–"}
            next_page = page_numbers[i + 1]
            
            # Überspringe wenn gleich wie firstPage
            if first_page_num and next_page == first_page_num:
                continue
            
            conf = "extracted" if (i + 1) in page_numbers else "interpolated"
            
            breaks.append({
                "page": next_page,
                "pdfFrom": i,
                "pdfTo": i + 1,
                "left": left,
                "right": right,
                "hyphenated": hyphenated,
                "printedPageConfidence": conf
            })
        
        doc.close()
        
        print(f"\nBreaks erstellt: {len(breaks)}")
        if breaks:
            print(f"Beispiel: page={breaks[0]['page']} (pdf {breaks[0]['pdfFrom']}->{breaks[0]['pdfTo']})")
        
        # Speichern
        data["GA069A"] = {
            "title": "Wahrheiten und Irrtümer der Geistesforschung",
            "pdfSource": pdf_path.name,
            "pdfPageCount": total_pages,
            "contentRange": [1, 500],
            "breaks": breaks
        }
        
        # Sortiere die Keys
        sorted_data = {"_info": data.get("_info", "")}
        ga_keys = sorted(k for k in data.keys() if k.startswith("GA"))
        for k in ga_keys:
            sorted_data[k] = data[k]
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] GA069A in {OUTPUT_FILE} aktualisiert")

if __name__ == "__main__":
    main()

