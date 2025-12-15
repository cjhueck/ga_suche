#!/usr/bin/env python3
"""
Analysiert DOCX-Dateien um zu verstehen, wie Seitenzahlen extrahiert werden können.
"""

import zipfile
import re
from pathlib import Path

def analyze_docx(docx_path):
    """Analysiert eine DOCX-Datei auf Seitenmarker."""
    print(f"\n{'='*60}")
    print(f"Analysiere: {Path(docx_path).name}")
    print(f"{'='*60}")
    
    with zipfile.ZipFile(docx_path, 'r') as z:
        # 1. Zähle Footer-Dateien
        footer_files = [f for f in z.namelist() if 'footer' in f.lower()]
        print(f"\nAnzahl Footer-Dateien: {len(footer_files)}")
        
        # 2. Extrahiere Seitenzahlen aus allen Footern
        page_numbers = {}
        for footer_file in footer_files:
            try:
                content = z.read(footer_file).decode('utf-8', errors='ignore')
                # Suche nach "Seite: X" oder "Seite: PAGE X"
                match = re.search(r'Seite:\s*(?:PAGE\s*)?(\d+(?:\s+\d+)?)', content)
                if match:
                    # Entferne Leerzeichen aus der Zahl (z.B. "1 3 0" -> "130")
                    page_str = match.group(1).replace(' ', '')
                    if page_str.isdigit():
                        page_num = int(page_str)
                        footer_num = int(re.search(r'footer(\d+)', footer_file).group(1))
                        page_numbers[footer_num] = page_num
            except Exception as e:
                pass
        
        print(f"Footer mit Seitenzahlen: {len(page_numbers)}")
        
        # Sortiere nach Seitenzahl
        sorted_pages = sorted(page_numbers.items(), key=lambda x: x[1])
        print(f"Seitenzahl-Bereich: {sorted_pages[0][1]} bis {sorted_pages[-1][1]}" if sorted_pages else "Keine Seiten gefunden")
        
        # 3. Lade das Hauptdokument
        doc_content = z.read('word/document.xml').decode('utf-8', errors='ignore')
        
        # 4. Lade Beziehungen (welcher Footer gehört wohin)
        rels_content = z.read('word/_rels/document.xml.rels').decode('utf-8')
        
        # Extrahiere Footer-Referenz-Mapping
        footer_refs = {}
        for match in re.finditer(r'Id="(rId\d+)"[^>]*Target="(footer\d+\.xml)"', rels_content):
            ref_id = match.group(1)
            footer_name = match.group(2)
            footer_num = int(re.search(r'footer(\d+)', footer_name).group(1))
            footer_refs[ref_id] = footer_num
        
        print(f"Footer-Referenzen in rels: {len(footer_refs)}")
        
        # 5. Finde Abschnitte mit ihren Footer-Referenzen
        # Jeder Abschnitt endet mit <w:sectPr> und enthält <w:footerReference>
        section_pattern = r'<w:sectPr[^>]*>(.*?)</w:sectPr>'
        sections = re.findall(section_pattern, doc_content, re.DOTALL)
        
        print(f"Abschnitte im Dokument: {len(sections)}")
        
        # 6. Analysiere ein paar Beispiel-Abschnitte
        print("\n--- Beispiel: Erste 3 Footer-Zuordnungen ---")
        for footer_num, page_num in list(sorted_pages[:5]):
            print(f"  footer{footer_num}.xml -> Seite {page_num}")
        
        # 7. Extrahiere Text zwischen Abschnitten
        # Vereinfachter Ansatz: Finde den Text VOR jedem sectPr
        print("\n--- Textextraktion Test ---")
        
        # Teile das Dokument bei sectPr
        parts = re.split(r'<w:sectPr[^>]*>.*?</w:sectPr>', doc_content, flags=re.DOTALL)
        print(f"Teile nach sectPr-Split: {len(parts)}")
        
        # Extrahiere reinen Text aus den letzten Zeichen jedes Teils
        for i, part in enumerate(parts[:3]):
            # Extrahiere Text (ohne XML-Tags)
            text = re.sub(r'<[^>]+>', ' ', part)
            text = ' '.join(text.split())
            last_words = text[-100:] if len(text) > 100 else text
            print(f"  Teil {i}: ...{last_words}")

def check_missing_pages():
    """Prüft, warum bestimmte Seiten in der Extraktion fehlen."""
    import json
    import fitz  # PyMuPDF
    
    # Lade vorhandene Marker
    with open('page-markers.json', 'r', encoding='utf-8') as f:
        markers = json.load(f)
    
    ga051 = markers.get('GA051', {})
    found_pages = set(m['page'] for m in ga051.get('markers', []))
    all_pages = set(range(18, 358))  # Seiten 18-357
    missing_pages = sorted(all_pages - found_pages)
    
    print(f"\n{'='*60}")
    print("Analyse fehlender Seiten in GA051")
    print(f"{'='*60}")
    print(f"Fehlende Seiten: {len(missing_pages)}")
    print(f"Erste 10 fehlende: {missing_pages[:10]}")
    
    # Lade JSON-Content für Vergleich
    json_content = ""
    for json_file in Path('.').glob('steiner-full-lectures-051*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for lecture in data.get('lectures', []):
                if lecture.get('gaNumber', '').upper() == 'GA051':
                    for para in lecture.get('paragraphs', []):
                        json_content += para.get('content', '') + "\n\n"
    
    print(f"JSON-Content Länge: {len(json_content):,} Zeichen")
    
    # Prüfe PDF für fehlende Seiten
    pdf_dir = Path("Steiner_GA_pdf")
    pdf_files = list(pdf_dir.glob("*051*.pdf"))
    
    if not pdf_files:
        print(f"Keine PDF mit '051' im Namen gefunden in {pdf_dir}")
        return
    
    pdf_path = pdf_files[0]
    print(f"PDF gefunden: {pdf_path.name}")
    
    doc = fitz.open(pdf_path)
    
    # Prüfe erste 5 fehlende Seiten
    for page_num in missing_pages[:5]:
        # Suche PDF-Seite mit dieser gedruckten Seitenzahl
        for pdf_page_idx in range(len(doc)):
            page = doc[pdf_page_idx]
            text = page.get_text()
            
            # Suche Seitenzahl in Fußzeile
            lines = text.strip().split('\n')
            found_page = None
            for line in lines[-5:]:
                clean = line.strip().replace(' ', '')
                if clean.isdigit() and int(clean) == page_num:
                    found_page = True
                    break
            
            if found_page:
                # Hole ersten Text der Seite
                blocks = page.get_text('blocks')
                first_text = None
                for block in blocks:
                    if len(block) >= 6 and block[6] == 0:  # Text-Block
                        txt = block[4].strip()
                        if len(txt) > 5 and not txt.replace(' ', '').isdigit():
                            if 'Copyright' not in txt and 'Buch:' not in txt:
                                first_text = txt.replace('\n', ' ')[:80]
                                break
                
                if first_text:
                    print(f"\nSeite {page_num}:")
                    print(f"  PDF-Text: \"{first_text}...\"")
                    
                    # Suche im JSON
                    search_phrase = first_text[:40]
                    if search_phrase in json_content:
                        print(f"  JSON: GEFUNDEN")
                    else:
                        # Versuche kürzeren Text
                        search_phrase = first_text[:20]
                        if search_phrase in json_content:
                            print(f"  JSON: Gefunden mit kürzerem Text")
                        else:
                            print(f"  JSON: NICHT GEFUNDEN")
                            # Zeige mögliche Unterschiede
                            clean_search = search_phrase.lower().replace(' ', '')
                            for i in range(len(json_content) - 30):
                                if json_content[i:i+15].lower().replace(' ', '') == clean_search[:15].lower().replace(' ', ''):
                                    print(f"  Ähnlich bei: \"{json_content[i:i+60]}...\"")
                                    break
                break
    
    doc.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-missing":
        check_missing_pages()
    else:
        docx_files = [
            r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\GA051.docx",
            r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\GA001.docx"
        ]
        
        for docx_path in docx_files:
            if Path(docx_path).exists():
                analyze_docx(docx_path)
            else:
                print(f"Datei nicht gefunden: {docx_path}")

