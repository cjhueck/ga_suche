#!/usr/bin/env python3
"""
Korrigiert Seitenmarker anhand des PDFs.
Bei Silbentrennungen wird nur der Text NACH dem Marker geprüft
(weil vor dem Marker Fußnoten stehen können).
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional

PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
PDF_DIR = PROJECT_DIR / "Steiner_GA_pdf"


def find_pdf_for_ga(ga_norm: str) -> Optional[Path]:
    """Findet das PDF für eine GA."""
    ga_num = ga_norm.replace("GA", "").lstrip("0")
    
    for pdf in PDF_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        if "steiner" in name_lower:
            if f"ga {ga_num}," in name_lower or f"ga {ga_num.zfill(3)}," in name_lower:
                return pdf
    return None


def extract_hyphenations_from_pdf(pdf_path: Path) -> Dict[int, str]:
    """
    Extrahiert für jede Seite mit Silbentrennung das erste Wort/Fragment.
    
    Returns: {page_num: this_start_word}
    """
    doc = fitz.open(pdf_path)
    hyphenations = {}
    
    prev_page_ends_hyphen = False
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        # Extrahiere Seitenzahl
        page_num = None
        match = re.search(r"Seite:\s*([\d\s]+)", text, re.IGNORECASE)
        if match:
            page_str = match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                page_num = int(page_str)
        
        # Entferne Copyright-Footer
        body_text = text
        copyright_match = re.search(r"Copyright Rudolf Steiner", text)
        if copyright_match:
            body_text = text[:copyright_match.start()].strip()
        
        if page_num and prev_page_ends_hyphen:
            # Erstes Wort dieser Seite (Fortsetzung der Silbentrennung)
            body_clean = body_text.strip()
            # Erstes Wort - kann Satzzeichen enthalten
            first_word_match = re.match(r'^([a-zA-ZäöüÄÖÜß]+)', body_clean)
            if first_word_match:
                this_start = first_word_match.group(1).lower()
                hyphenations[page_num] = this_start
        
        # Prüfe ob diese Seite mit Bindestrich endet
        prev_page_ends_hyphen = body_text.rstrip().endswith('-')
    
    doc.close()
    return hyphenations


def correct_markers_in_md(
    md_path: Path,
    hyphenations: Dict[int, str],
    dry_run: bool = False
) -> Tuple[int, int, List[str]]:
    """
    Korrigiert Marker basierend auf PDF-Silbentrennungen.
    
    Regel: Bei Silbentrennung muss nach dem Marker das Wort-Fragment aus dem PDF stehen.
    
    Returns: (corrected_count, already_ok_count, messages)
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_lower = content.lower()
    corrected = 0
    already_ok = 0
    messages = []
    
    # Für jede Silbentrennung im PDF
    for page_num, this_start in sorted(hyphenations.items()):
        marker = f"|{page_num}|"
        marker_pos = content.find(marker)
        
        if marker_pos == -1:
            messages.append(f"Seite {page_num}: Marker nicht gefunden")
            continue
        
        # Text nach dem Marker
        after_marker = content_lower[marker_pos + len(marker):marker_pos + len(marker) + 30]
        
        # Prüfe ob this_start direkt nach dem Marker kommt
        if after_marker.lstrip().startswith(this_start):
            already_ok += 1
            continue
        
        # Marker ist falsch positioniert - suche die richtige Position
        # Finde das Wort, das mit this_start beginnt, nach dem aktuellen Marker
        search_start = marker_pos
        
        # Suche nach this_start im Text (als Wort-Fragment)
        pattern = re.compile(r'\b(\w*' + re.escape(this_start) + r')', re.IGNORECASE)
        
        # Suche im Bereich um den Marker
        search_area = content[max(0, marker_pos - 200):marker_pos + 500]
        search_offset = max(0, marker_pos - 200)
        
        best_match = None
        best_distance = float('inf')
        
        for match in pattern.finditer(search_area):
            word = match.group(1).lower()
            # Prüfe ob das Wort mit this_start endet oder this_start enthält
            if word.endswith(this_start) or this_start in word:
                # Position im Original
                pos_in_original = search_offset + match.start()
                
                # Wenn das Wort VOR dem Marker endet und mit this_start endet,
                # ist die korrekte Marker-Position am Anfang von this_start
                word_start = pos_in_original
                word_end = pos_in_original + len(match.group(0))
                
                # Finde Position wo this_start beginnt
                if word.endswith(this_start):
                    fragment_start = word_end - len(this_start)
                    distance = abs(fragment_start - marker_pos)
                    if distance < best_distance and fragment_start != marker_pos:
                        best_match = fragment_start
                        best_distance = distance
        
        if best_match is not None and best_match != marker_pos:
            # Entferne alten Marker und füge neuen ein
            content_without_marker = content[:marker_pos] + content[marker_pos + len(marker):]
            
            # Korrigiere Position nach Entfernung
            new_pos = best_match if best_match < marker_pos else best_match - len(marker)
            
            content = content_without_marker[:new_pos] + marker + content_without_marker[new_pos:]
            
            messages.append(f"Seite {page_num}: Korrigiert ('{this_start}')")
            corrected += 1
        else:
            messages.append(f"Seite {page_num}: Konnte nicht korrigieren ('{this_start}')")
    
    if not dry_run and corrected > 0:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return corrected, already_ok, messages


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Korrigiert Seitenmarker bei Silbentrennungen anhand des PDFs"
    )
    parser.add_argument("ga", help="GA-Nummer (z.B. 1, GA001)")
    parser.add_argument("--dry-run", action="store_true", help="Nur simulieren")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mehr Ausgabe")
    args = parser.parse_args()
    
    # Normalisiere GA
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = match.group(1).zfill(3)
    ga_norm = f"GA{ga_num}"
    
    print(f"\n{'='*60}")
    print(f"Korrigiere Silbentrennungen für {ga_norm}")
    print(f"{'='*60}")
    
    # Finde PDF
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print(f"FEHLER: Kein PDF gefunden für {ga_norm}")
        return
    
    print(f"PDF: {pdf_path.name}")
    
    # Extrahiere Silbentrennungen
    print("Extrahiere Silbentrennungen aus PDF...")
    hyphenations = extract_hyphenations_from_pdf(pdf_path)
    print(f"Gefunden: {len(hyphenations)} Silbentrennungen")
    
    if args.verbose:
        print("\nSilbentrennungen:")
        for page, start in sorted(hyphenations.items())[:20]:
            print(f"  Seite {page}: ...{start}")
    
    # Finde MD-Dateien (alle im Ordner)
    md_folder = None
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            md_folder = folder
            break
    
    if not md_folder:
        print(f"FEHLER: Kein MD-Ordner gefunden")
        return
    
    md_files = list(md_folder.glob("*.md"))
    if not md_files:
        print(f"FEHLER: Keine MD-Dateien gefunden")
        return
    
    print(f"MD-Dateien: {len(md_files)} gefunden")
    print("\nKorrigiere Marker..." + (" (Dry-Run)" if args.dry_run else ""))
    
    # Korrigiere alle Dateien
    total_corrected = 0
    total_ok = 0
    all_messages = []
    
    for md_path in sorted(md_files):
        corrected, ok, messages = correct_markers_in_md(md_path, hyphenations, args.dry_run)
        total_corrected += corrected
        total_ok += ok
        if corrected > 0 or args.verbose:
            all_messages.append(f"\n{md_path.name}:")
            all_messages.extend(messages)
    
    print(f"\nErgebnis:")
    print(f"  Bereits korrekt: {total_ok}")
    print(f"  Korrigiert: {total_corrected}")
    print(f"  Silbentrennungen gesamt: {len(hyphenations)}")
    
    if args.verbose or total_corrected > 0:
        print("\nDetails:")
        for msg in all_messages:
            print(f"  {msg}")
    
    if args.dry_run:
        print("\n(Dry-Run - keine Änderungen gespeichert)")


if __name__ == "__main__":
    main()
