#!/usr/bin/env python3
"""
Fügt Seitenmarker in Obsidian-MD-Dateien ein.
Verwendet dieselbe Logik wie apply_pagebreaks_from_pdf.py
"""

import re
import sys
import json
from pathlib import Path

# Import from main script
sys.path.insert(0, str(Path(__file__).parent))
from apply_pagebreaks_from_pdf import (
    extract_pdf_pages,
    find_pagebreak_position,
    normalize_for_comparison,
    remove_existing_markers
)


def insert_markers_in_md(
    md_path: Path,
    pdf_pages: list,
    start_page: int,
    end_page: int,
    dry_run: bool = False
) -> int:
    """
    Fügt Seitenmarker in eine MD-Datei ein.
    
    WICHTIG: Marker werden streng sequentiell gesucht und eingefügt.
    Jede Seitenzahl kommt nur einmal vor, in aufsteigender Reihenfolge.
    """
    # Lade MD-Datei
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Schritt 1: Entferne ALLE existierenden Marker
    content_clean = remove_existing_markers(content)
    
    # Schritt 2: Sammle Marker-Positionen (streng sequentiell)
    markers = []  # (position, page_num)
    search_start = 0
    current_page = start_page
    
    # Filtere relevante PDF-Seiten
    relevant_pages = [(idx, pn, pe, ts) for idx, pn, pe, ts in pdf_pages 
                      if start_page <= pn <= end_page]
    
    for pdf_idx, page_num, prev_end, this_start in relevant_pages:
        # Überspringe wenn Seitenzahl nicht die erwartete nächste ist
        if page_num < current_page:
            continue
        
        # Erste Seite: Marker nach Header
        if page_num == start_page:
            header_match = re.search(r'Quelle:\s*\[\[.*?\]\]\s*\n\n', content_clean)
            if header_match:
                pos = header_match.end()
            else:
                first_para = re.search(r'\n\n', content_clean)
                pos = first_para.end() if first_para else 0
            
            markers.append((pos, page_num))
            search_start = pos + 1
            current_page = page_num + 1
            continue
        
        # Finde Position
        pos = find_pagebreak_position(prev_end, this_start, content_clean, search_start)
        
        if pos is not None and pos > search_start:
            markers.append((pos, page_num))
            search_start = pos + 1
            current_page = page_num + 1
    
    if not markers:
        return 0
    
    # Schritt 3: Finale Validierung - streng aufsteigend
    valid_markers = []
    last_pos = -1
    last_page = -1
    
    for pos, page_num in sorted(markers, key=lambda x: x[0]):
        if pos > last_pos and page_num > last_page:
            valid_markers.append((pos, page_num))
            last_pos = pos
            last_page = page_num
    
    # Schritt 4: Füge Marker ein (von hinten nach vorne)
    valid_markers.sort(key=lambda x: x[0], reverse=True)
    
    new_content = content_clean
    for pos, page_num in valid_markers:
        marker = f"|{page_num}|"
        
        # Prüfe ob direkt vor einem Obsidian Block-ID (^xxxxx)
        before_pos = new_content[max(0, pos-15):pos]
        block_id_match = re.search(r'\s*\^[a-z0-9]+$', before_pos)
        
        if block_id_match:
            block_id_start = pos - len(before_pos) + block_id_match.start()
            new_content = new_content[:block_id_start] + marker + new_content[block_id_start:]
        else:
            new_content = new_content[:pos] + marker + new_content[pos:]
    
    if not dry_run:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return len(valid_markers)


def process_ga072():
    """Verarbeitet alle GA072 Vorträge."""
    
    # Mapping: Vortragsnummer -> (Start-Seite, End-Seite)
    lectures = {
        1: (15, 63),
        2: (64, 106),
        3: (107, 149),
        4: (150, 186),
        5: (187, 230),
        6: (231, 273),
        7: (274, 306),
        8: (307, 338),
        9: (339, 375),
        10: (376, 438),
    }
    
    # MD-Dateien
    md_files = {
        1: "GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917.md",
        2: "GA072 (2.) ANTHROPOSOPHIE STÖRT NIEMANDES RELIGIÖSES BEKENNTNIS, Basel, 19. Oktober 1917.md",
        3: "GA072 (3.) GEISTESWISSENSCHAFTLICHE (ANTHROPOSOPHISCHE9 FORSCHUNGSERGEBNISSE ÜBER DAS EWIGE IN DER MENSCHENSEELE UND ÜBER DAS WESEN DER FREIHEIT, Basel, 23. November 1917.md",
        4: "GA072 (4.) DIE WISSENSCHAFT DES ÜBERSINNLICHEN UND DIE SITTLICH-SOZIALEN IDEEN, Basel, 24. November 1917.md",
        5: "GA072 (5.) DAS WIRKEN DER SEELENKRÄFTE IM MENSCHEN UND IHR ZUSAMMENHANG MIT DESSEN EWIGER WESENHEIT, Bern, 28. November 1917.md",
        6: "GA072 (6.) GEISTESWISSENSCHAFTLICHE ERGEBNISSE ÜBER DIE IDEEN DER FREIHEIT UND DES SOZIAL-SITTLICHEN LEBENS, Bern, 30. November 1917.md",
        7: "GA072 (7.) DAS WESEN DER MENSCHENSEELE UND DIE NATUR DES MENSCHENLEIBES, Basel, 30. Oktober 1918.md",
        8: "GA072 (8.) RECHTFERTIGUNG DER ÜBERSINNLICHEN ERKENNTNIS DURCH DIE NATURWISSENSCHAFT, Basel, 31. Oktober 1918.md",
        9: "GA072 (9.) RECHTFERTIGUNG DER SEELENWISSENSCHAFT IM SINNE DER ANTHROPOSOPHIE, Bern, 9. Dezember 1918.md",
        10: "GA072 (10.) SITTLICHES, SOZIALES UND RELIGIÖSES LEBEN VOM GESICHTSPUNKTE DER ANTHROPOSOPHIE, Bern, 11. Dezember 1918.md",
    }
    
    md_folder = Path("Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben")
    pdf_path = Path("Steiner_GA_pdf/Steiner, Rudolf GA 072, 1990 - Freiheit, Unsterblichkeit, soziales Leben.pdf")
    
    # Extrahiere PDF-Seiten einmal
    print("Extrahiere PDF-Seiten...")
    pdf_pages = extract_pdf_pages(pdf_path)
    print(f"  {len(pdf_pages)} Seiten extrahiert")
    print()
    
    total_markers = 0
    
    for num, (start_page, end_page) in lectures.items():
        if num not in md_files:
            continue
        
        md_path = md_folder / md_files[num]
        if not md_path.exists():
            print(f"  GA072/{num}: Datei nicht gefunden")
            continue
        
        expected = end_page - start_page + 1
        count = insert_markers_in_md(md_path, pdf_pages, start_page, end_page)
        total_markers += count
        
        print(f"  GA072/{num}: {count}/{expected} Marker (S.{start_page}-{end_page})")
    
    print()
    print(f"Gesamt: {total_markers} Marker eingefügt")
    return total_markers


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "GA072":
        process_ga072()
    else:
        # Einzelner Vortrag GA072/1
        md_path = Path("Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben/GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917.md")
        pdf_path = Path("Steiner_GA_pdf/Steiner, Rudolf GA 072, 1990 - Freiheit, Unsterblichkeit, soziales Leben.pdf")
        
        start_page = 15
        end_page = 63
        
        dry_run = "--dry-run" in sys.argv
        
        print(f"Verarbeite: {md_path.name}")
        print(f"PDF: {pdf_path.name}")
        print(f"Seiten: {start_page}-{end_page}")
        print()
        
        pdf_pages = extract_pdf_pages(pdf_path)
        count = insert_markers_in_md(md_path, pdf_pages, start_page, end_page, dry_run)
        print(f"\n{count} Marker {'würden eingefügt' if dry_run else 'eingefügt'}")


if __name__ == "__main__":
    main()
