#!/usr/bin/env python3
"""
Testet warum bestimmte Seiten in der PDF-Extraktion fehlen.
"""

import json
import fitz  # PyMuPDF
from pathlib import Path
import re

def main():
    # Lade vorhandene Marker
    with open('page-markers.json', 'r', encoding='utf-8') as f:
        markers = json.load(f)
    
    ga051 = markers.get('GA051', {})
    found_pages = set(m['page'] for m in ga051.get('markers', []))
    all_pages = set(range(18, 358))
    missing_pages = sorted(all_pages - found_pages)
    
    print(f"Fehlende Seiten: {len(missing_pages)}")
    print(f"Erste 5 fehlende: {missing_pages[:5]}")
    
    # Lade JSON-Content
    json_content = ""
    for json_file in Path('.').glob('steiner-full-lectures-051*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for lecture in data.get('lectures', []):
                if lecture.get('gaNumber', '').upper() == 'GA051':
                    for para in lecture.get('paragraphs', []):
                        json_content += para.get('content', '') + "\n\n"
    
    print(f"JSON-Content: {len(json_content):,} Zeichen")
    
    # Finde PDF
    pdf_dir = Path("Steiner_GA_pdf")
    pdf_files = list(pdf_dir.glob("*051*.pdf"))
    if not pdf_files:
        print("PDF nicht gefunden!")
        return
    
    pdf_path = pdf_files[0]
    print(f"PDF: {pdf_path.name}")
    
    doc = fitz.open(pdf_path)
    print(f"PDF-Seiten: {len(doc)}")
    
    # Erstelle Mapping: gedruckte Seitenzahl -> PDF-Seitenindex
    page_mapping = {}
    for pdf_idx in range(len(doc)):
        page = doc[pdf_idx]
        text = page.get_text()
        lines = text.strip().split('\n')
        
        # Suche Seitenzahl in letzten Zeilen
        for line in lines[-5:]:
            clean = line.strip().replace(' ', '')
            if clean.isdigit() and 1 <= len(clean) <= 3:
                page_num = int(clean)
                if page_num not in page_mapping:
                    page_mapping[page_num] = pdf_idx
                break
    
    print(f"Erkannte Seiten: {len(page_mapping)}")
    
    # Prüfe fehlende Seiten
    print("\n--- Analyse fehlender Seiten ---")
    
    for page_num in missing_pages[:5]:
        print(f"\n[Seite {page_num}]")
        
        if page_num not in page_mapping:
            print("  -> Seitenzahl nicht in PDF-Fußzeile erkannt!")
            continue
        
        pdf_idx = page_mapping[page_num]
        page = doc[pdf_idx]
        
        # Hole ersten Textblock
        blocks = page.get_text('blocks')
        first_text = None
        
        for block in blocks:
            if len(block) >= 6 and block[6] == 0:  # Text-Block
                txt = block[4].strip()
                # Ignoriere kurze Texte, Seitenzahlen, Copyright
                if len(txt) < 10:
                    continue
                if txt.replace(' ', '').isdigit():
                    continue
                if 'Copyright' in txt or 'Buch:' in txt or 'Seite:' in txt:
                    continue
                first_text = txt.replace('\n', ' ')
                break
        
        if not first_text:
            print("  -> Kein erster Text gefunden!")
            continue
        
        print(f"  PDF-Text: \"{first_text[:60]}...\"")
        
        # Suche im JSON
        search_text = first_text[:50]
        if search_text in json_content:
            print("  JSON: GEFUNDEN (direkt)")
        else:
            # Normalisiere für Suche
            normalized_search = ' '.join(search_text.split())[:40]
            if normalized_search in json_content:
                print("  JSON: GEFUNDEN (normalisiert)")
            else:
                # Suche Teilstring
                found = False
                for length in range(30, 10, -5):
                    if first_text[:length] in json_content:
                        print(f"  JSON: GEFUNDEN (nur erste {length} Zeichen)")
                        found = True
                        break
                
                if not found:
                    print("  JSON: NICHT GEFUNDEN!")
                    # Zeige mögliche Ursache
                    print(f"  Suchtext: \"{first_text[:40]}\"")
    
    doc.close()

if __name__ == "__main__":
    main()

