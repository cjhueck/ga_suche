#!/usr/bin/env python3
"""Debug: Warum werden Marker nicht gefunden?"""

import sys
import re
from pathlib import Path
from difflib import SequenceMatcher

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import fitz

def normalize(text):
    """Normalisiere Text."""
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'---', '', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'#', '', text)
    
    replacements = {
        'ä': 'a', 'ö': 'o', 'ü': 'u',
        'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        'ß': 'ss',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = ''.join(c if ord(c) < 128 else ' ' for c in text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def main():
    pdf_path = Path(r'Steiner_GA\GA052-Spirituelle Seelenlehre und Weltbetrachtung\Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung.pdf')
    md_path = Path(r'Steiner_GA\GA052-Spirituelle Seelenlehre und Weltbetrachtung\Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung_prepared.md')
    
    # Lade PDF
    doc = fitz.open(pdf_path)
    pdf_pages = []
    for idx in range(len(doc)):
        page = doc[idx]
        text = page.get_text()
        normalized = normalize(text)
        
        printed_page = None
        lines = text.strip().split('\n')
        for line in reversed(lines[-10:]):
            if re.match(r'^\d{1,3}$', line.strip()):
                printed_page = int(line.strip())
                break
        
        pdf_pages.append({
            'pdf_page': idx + 1,
            'printed_page': printed_page,
            'normalized': normalized
        })
    doc.close()
    
    print(f"PDF: {len(pdf_pages)} Seiten")
    
    # Lade MD und finde Marker
    md_content = md_path.read_text(encoding='utf-8')
    marker_pattern = r'(\n*\s*---\s*\n*)'
    parts = re.split(marker_pattern, md_content)
    
    # Teste Marker 10-15 (sollten im Vortragstext sein)
    marker_idx = 0
    tested = 0
    
    for i, part in enumerate(parts):
        if re.match(r'^\n*\s*---\s*\n*$', part):
            marker_idx += 1
            
            # Nur Marker 10-20 testen (im Haupttext)
            if marker_idx < 10 or marker_idx > 20:
                continue
            
            tested += 1
            
            text_before = parts[i - 1] if i > 0 else ""
            text_after = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Normalisiere
            before_norm = normalize(text_before[-200:])
            after_norm = normalize(text_after[:200])
            
            print(f"\n{'='*60}")
            print(f"=== Marker #{marker_idx} ===")
            print(f"VOR (letzte 80 Zeichen): ...{before_norm[-80:]}")
            print(f"NACH (erste 80 Zeichen): {after_norm[:80]}...")
            
            # Suche after_norm in allen PDF-Seiten
            search_text = after_norm[:60]
            print(f"\nSuche: '{search_text}'")
            
            found_pages = []
            for page in pdf_pages:
                page_num = page['printed_page'] or page['pdf_page']
                page_text = page['normalized']
                
                # Exakte Suche
                if search_text in page_text:
                    pos = page_text.find(search_text)
                    found_pages.append((page_num, pos, 'exact'))
                else:
                    # Fuzzy: Prüfe Ähnlichkeit mit Seitenanfang
                    page_start = page_text[:200]
                    ratio = SequenceMatcher(None, search_text, page_start[:60]).ratio()
                    if ratio > 0.7:
                        found_pages.append((page_num, 0, f'fuzzy {ratio:.2f}'))
            
            if found_pages:
                print(f"GEFUNDEN auf: {found_pages[:5]}")
            else:
                print("NICHT GEFUNDEN!")
                # Zeige was auf den erwarteten Seiten steht
                expected_page = 13 + marker_idx  # Grobe Schätzung
                if expected_page < len(pdf_pages):
                    page_start = pdf_pages[expected_page - 1]['normalized'][:100]
                    print(f"  Seite ~{expected_page} beginnt mit: {page_start[:60]}...")
            
            if tested >= 5:
                break


if __name__ == '__main__':
    main()
