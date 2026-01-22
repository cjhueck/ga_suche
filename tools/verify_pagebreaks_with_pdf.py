#!/usr/bin/env python3
"""
Verifiziert und korrigiert Seitenmarker anhand des PDFs.
Prüft insbesondere Silbentrennungen.
"""

import re
import sys
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
        # Suche nach "Steiner" PDFs mit der GA-Nummer
        if "steiner" in name_lower:
            if f"ga {ga_num}," in name_lower or f"ga {ga_num.zfill(3)}," in name_lower:
                return pdf
    return None


def extract_page_boundaries_from_pdf(pdf_path: Path) -> Dict[int, Tuple[str, str, bool]]:
    """
    Extrahiert für jede Seite:
    - Ende der vorherigen Seite (letztes Wort/Fragment)
    - Anfang dieser Seite (erstes Wort/Fragment)
    - Ob Silbentrennung vorliegt
    
    Returns: {page_num: (prev_end_word, this_start_word, is_hyphenated)}
    """
    doc = fitz.open(pdf_path)
    boundaries = {}
    
    prev_page_text = ""
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        # Extrahiere Seitenzahl aus Footer
        page_num = None
        match = re.search(r"Seite:\s*([\d\s]+)", text, re.IGNORECASE)
        if match:
            page_str = match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                page_num = int(page_str)
        
        if page_num is None:
            prev_page_text = text
            continue
        
        # Entferne Copyright-Footer vom Body
        body_text = text
        copyright_match = re.search(r"Copyright Rudolf Steiner", text)
        if copyright_match:
            body_text = text[:copyright_match.start()].strip()
        
        # Extrahiere erstes Wort dieser Seite
        body_clean = body_text.strip()
        first_word_match = re.match(r'^(\S+)', body_clean)
        this_start = first_word_match.group(1) if first_word_match else ""
        
        # Prüfe ob vorherige Seite mit Bindestrich endet (Silbentrennung)
        is_hyphenated = False
        prev_end = ""
        
        if prev_page_text:
            # Entferne Copyright-Footer
            prev_body = prev_page_text
            prev_copyright = re.search(r"Copyright Rudolf Steiner", prev_page_text)
            if prev_copyright:
                prev_body = prev_page_text[:prev_copyright.start()].strip()
            
            # Letztes Wort der vorherigen Seite
            prev_words = prev_body.split()
            if prev_words:
                last_word = prev_words[-1]
                # Prüfe auf Bindestrich am Ende
                if last_word.endswith('-'):
                    is_hyphenated = True
                    prev_end = last_word[:-1]  # Ohne Bindestrich
                else:
                    prev_end = last_word
        
        boundaries[page_num] = (prev_end.lower(), this_start.lower(), is_hyphenated)
        prev_page_text = text
    
    doc.close()
    return boundaries


def verify_markers_in_md(md_path: Path, pdf_boundaries: Dict[int, Tuple[str, str, bool]]) -> List[Dict]:
    """
    Verifiziert die Marker im MD gegen das PDF.
    
    Returns: Liste von Korrekturen
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_lower = content.lower()
    corrections = []
    
    # Finde alle Marker und ihre Positionen
    for match in re.finditer(r'\|(\d+)\|', content):
        page_num = int(match.group(1))
        pos = match.start()
        
        if page_num not in pdf_boundaries:
            continue
        
        prev_end, this_start, is_hyphenated = pdf_boundaries[page_num]
        
        if not is_hyphenated:
            continue  # Nur Silbentrennungen prüfen
        
        # Prüfe ob der Marker korrekt positioniert ist
        # Bei Silbentrennung sollte vor dem Marker "prev_end" stehen
        # und nach dem Marker "this_start"
        
        # Text vor dem Marker (letzte 20 Zeichen)
        text_before = content_lower[max(0, pos-20):pos]
        # Text nach dem Marker (erste 20 Zeichen)
        marker_len = len(match.group(0))
        text_after = content_lower[pos+marker_len:pos+marker_len+20]
        
        # Erwartetes kombiniertes Wort
        combined = prev_end + this_start
        
        # Prüfe ob das kombinierte Wort im Kontext vorkommt
        context = content_lower[max(0, pos-30):pos+marker_len+30]
        
        # Finde die tatsächliche Position des kombinierten Wortes
        combined_pos = context.find(combined)
        
        if combined_pos == -1:
            # Wort nicht gefunden - möglicherweise andere Schreibweise
            corrections.append({
                "page": page_num,
                "current_pos": pos,
                "prev_end": prev_end,
                "this_start": this_start,
                "context": content[max(0, pos-30):pos+marker_len+30],
                "status": "not_found"
            })
            continue
        
        # Erwartete Position des Markers: nach prev_end
        expected_marker_pos_in_context = combined_pos + len(prev_end)
        actual_marker_pos_in_context = 30 if pos >= 30 else pos
        
        if abs(expected_marker_pos_in_context - actual_marker_pos_in_context) > 2:
            corrections.append({
                "page": page_num,
                "current_pos": pos,
                "prev_end": prev_end,
                "this_start": this_start,
                "context": content[max(0, pos-30):pos+marker_len+30],
                "expected_offset": expected_marker_pos_in_context - actual_marker_pos_in_context,
                "status": "misplaced"
            })
        else:
            corrections.append({
                "page": page_num,
                "prev_end": prev_end,
                "this_start": this_start,
                "context": content[max(0, pos-30):pos+marker_len+30],
                "status": "ok"
            })
    
    return corrections


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verifiziert Seitenmarker anhand des PDFs")
    parser.add_argument("ga", help="GA-Nummer (z.B. 1, GA001)")
    parser.add_argument("--fix", action="store_true", help="Korrekturen anwenden")
    args = parser.parse_args()
    
    # Normalisiere GA
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = match.group(1).zfill(3)
    ga_norm = f"GA{ga_num}"
    
    print(f"\n{'='*60}")
    print(f"Verifiziere {ga_norm} mit PDF")
    print(f"{'='*60}")
    
    # Finde PDF
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print(f"FEHLER: Kein PDF gefunden für {ga_norm}")
        return
    
    print(f"PDF: {pdf_path.name}")
    
    # Extrahiere Seitengrenzen aus PDF
    print("Extrahiere Seitengrenzen aus PDF...")
    boundaries = extract_page_boundaries_from_pdf(pdf_path)
    
    # Zähle Silbentrennungen
    hyphenated = sum(1 for b in boundaries.values() if b[2])
    print(f"Seiten mit Silbentrennung: {hyphenated}")
    
    # Zeige erste 10 Silbentrennungen
    print("\nErste 10 Silbentrennungen im PDF:")
    count = 0
    for page, (prev, start, is_hyph) in sorted(boundaries.items()):
        if is_hyph and count < 10:
            print(f"  Seite {page}: '{prev}' + '{start}' = '{prev}{start}'")
            count += 1
    
    # Finde MD-Datei
    md_folder = None
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            md_folder = folder
            break
    
    if not md_folder:
        print(f"FEHLER: Kein MD-Ordner gefunden")
        return
    
    # Finde Hauptdatei
    md_path = None
    for f in md_folder.glob("*.md"):
        if not re.search(r'\(\d+\.\)', f.stem):
            md_path = f
            break
    
    if not md_path:
        print(f"FEHLER: Keine MD-Datei gefunden")
        return
    
    print(f"\nMD-Datei: {md_path.name}")
    
    # Verifiziere
    print("\nVerifiziere Marker...")
    results = verify_markers_in_md(md_path, boundaries)
    
    # Statistik
    ok = sum(1 for r in results if r["status"] == "ok")
    misplaced = sum(1 for r in results if r["status"] == "misplaced")
    not_found = sum(1 for r in results if r["status"] == "not_found")
    
    print(f"\nErgebnis:")
    print(f"  Korrekt: {ok}")
    print(f"  Falsch positioniert: {misplaced}")
    print(f"  Nicht gefunden: {not_found}")
    
    # Zeige Probleme
    if misplaced > 0 or not_found > 0:
        print("\nProbleme:")
        for r in results:
            if r["status"] != "ok":
                print(f"  Seite {r['page']}: {r['status']}")
                print(f"    PDF: '{r['prev_end']}' + '{r['this_start']}'")
                print(f"    MD:  ...{r['context']}...")
                print()


if __name__ == "__main__":
    main()
