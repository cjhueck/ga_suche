#!/usr/bin/env python3
"""Extrahiert das Inhaltsverzeichnis aus einem PDF."""

import fitz
from pathlib import Path
import re
import json

def extract_toc_from_pdf(pdf_path: Path, toc_pages: range = range(6, 12)):
    """
    Extrahiert Vortragstitel und Seitenzahlen aus dem Inhaltsverzeichnis.
    
    Rückgabe: Liste von {title, location_date, page}
    """
    doc = fitz.open(pdf_path)
    
    # Sammle alle Zeilen aus dem Inhaltsverzeichnis
    toc_lines = []
    for i in toc_pages:
        if i >= len(doc):
            break
        page = doc[i]
        text = page.get_text()
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and stripped not in ['RUDOLF STEINER', 'VERLAG', 'INHALT']:
                # Entferne 'Seite X' Header
                if not re.match(r'^Seite \d+$', stripped):
                    toc_lines.append(stripped)
    
    doc.close()
    
    # Finde Vortragstitel und Seitenzahlen
    # Muster: Titel, dann Ort/Datum, dann Seitenzahl
    entries = []
    i = 0
    while i < len(toc_lines):
        line = toc_lines[i]
        
        # Prüfe ob nächste Zeilen Ort/Datum und Seitenzahl sind
        if i + 2 < len(toc_lines):
            next1 = toc_lines[i+1]
            next2 = toc_lines[i+2]
            
            # Ort/Datum Muster
            date_pattern = r'\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)'
            if re.search(date_pattern, next1, re.IGNORECASE):
                # Seitenzahl ist eine 2-3 stellige Zahl
                if re.match(r'^\d{2,3}$', next2):
                    entries.append({
                        'title': line,
                        'location_date': next1,
                        'page': int(next2)
                    })
                    i += 3
                    continue
        i += 1
    
    return entries


def create_mapping_from_toc(ga_number: str, entries: list) -> dict:
    """
    Erstellt ein lecture-page-mapping aus den TOC-Einträgen.
    """
    ga_upper = ga_number.upper()
    mapping = {}
    
    for i, entry in enumerate(entries, 1):
        lec_id = f"{ga_upper}/{i}"
        mapping[lec_id] = entry['page']
    
    return {ga_upper: mapping}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Verwendung: python extract_toc.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        # Suche in Steiner_GA_pdf
        matches = list(Path("Steiner_GA_pdf").glob(f"*{sys.argv[1]}*"))
        if matches:
            pdf_path = matches[0]
        else:
            print(f"PDF nicht gefunden: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"PDF: {pdf_path.name}")
    entries = extract_toc_from_pdf(pdf_path)
    
    print(f"\nGefundene Einträge: {len(entries)}")
    for i, e in enumerate(entries, 1):
        print(f"  {i}. S.{e['page']:3d}: {e['title'][:40]} ({e['location_date'][:30]})")
    
    # Erstelle Mapping
    ga_match = re.search(r'GA\s*(\d+[a-z]?)', pdf_path.name, re.IGNORECASE)
    if ga_match:
        ga_num = f"GA{ga_match.group(1)}"
        mapping = create_mapping_from_toc(ga_num, entries)
        print(f"\nMapping für {ga_num}:")
        print(json.dumps(mapping, indent=2))

