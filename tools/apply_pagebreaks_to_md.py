#!/usr/bin/env python3
"""
Fügt Seitenmarker in Obsidian-MD-Dateien ein.
Verwendet dieselbe Logik wie generate_pagebreaks_with_pdf.py
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from main script
sys.path.insert(0, str(Path(__file__).parent))
from generate_pagebreaks_with_pdf import (
    extract_pdf_pages,
    find_pagebreak_position,
    normalize_for_comparison,
    remove_existing_markers,
    normalize_ga,
    find_pdf_for_ga,
    load_page_mapping,
    adjust_position_after_punctuation
)

# Pfade
PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
PAGE_BREAK_MARKERS_FILE = PROJECT_DIR / "page-break-markers.json"


def load_first_content_page(ga_norm: str) -> Optional[int]:
    """
    Lädt die erste Inhaltsseite aus page-break-markers.json.
    Verwendet contentRange[0] oder den ersten Break mit isFirstPage=true.
    """
    if not PAGE_BREAK_MARKERS_FILE.exists():
        return None
    
    try:
        with open(PAGE_BREAK_MARKERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ga_data = data.get(ga_norm, {})
        
        # Methode 1: contentRange[0]
        content_range = ga_data.get('contentRange', [])
        if content_range and len(content_range) >= 1:
            return content_range[0]
        
        # Methode 2: erster Break mit isFirstPage=true
        breaks = ga_data.get('breaks', [])
        for b in breaks:
            if b.get('isFirstPage'):
                return b.get('page')
        
        # Methode 3: erster Break überhaupt
        if breaks:
            return breaks[0].get('page')
        
    except Exception as e:
        print(f"    Warnung: Konnte page-break-markers.json nicht lesen: {e}")
    
    return None


def find_md_folder_for_ga(ga_norm: str) -> Optional[Path]:
    """Findet den MD-Ordner für eine GA."""
    # Suche nach Ordner der Form GA051-*, GA052-*, etc.
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            return folder
    return None


def find_md_files_in_folder(folder: Path) -> List[Path]:
    """Findet alle MD-Dateien in einem Ordner."""
    return sorted(folder.glob("*.md"))


def extract_lecture_number_from_md(md_path: Path) -> Optional[int]:
    """
    Extrahiert die Vortragsnummer aus dem MD-Dateinamen.
    Z.B. "GA051 (1.) TITEL.md" -> 1
    
    Für Bücher (ohne Vortragsnummer) wird 0 zurückgegeben.
    """
    name = md_path.stem
    # Pattern: GA051 (1.) oder GA051 (12.)
    match = re.search(r'\((\d+)\.\)', name)
    if match:
        return int(match.group(1))
    
    # Prüfe ob es eine Buch-Datei ist (enthält GA-Nummer aber keine Vortragsnummer)
    # Z.B. "GA012 - Die Stufen der höheren Erkenntnis (1905-1908).md"
    if re.match(r'^GA\d{3}', name):
        return 0  # 0 bedeutet "Buch" (keine Vortragsnummer)
    
    return None


def get_page_range_for_md(
    md_path: Path,
    ga_norm: str,
    mapping: Dict,
    all_md_files: List[Path],
    pdf_pages: List
) -> Tuple[Optional[int], Optional[int]]:
    """
    Ermittelt den Seitenbereich für eine MD-Datei.
    Verwendet das lecture-page-mapping falls vorhanden.
    
    Für Bücher (lec_num = 0) werden alle Seiten der PDF verwendet.
    """
    lec_num = extract_lecture_number_from_md(md_path)
    if lec_num is None:
        return None, None
    
    # Für Bücher (lec_num = 0): verwende contentRange aus page-break-markers.json
    if lec_num == 0:
        if pdf_pages:
            # Erste Inhaltsseite aus Konfiguration laden
            first_content = load_first_content_page(ga_norm)
            if first_content:
                start_page = first_content
            else:
                # Fallback: erste PDF-Seite (kann falsch sein!)
                start_page = pdf_pages[0][1]
                print(f"    WARNUNG: Keine contentRange für {ga_norm} - verwende Seite {start_page}")
            return start_page, pdf_pages[-1][1]
        return None, None
    
    ga_mapping = mapping.get(ga_norm, {})
    lec_id = f"{ga_norm}/{lec_num}"
    
    # Start-Seite aus Mapping
    start_page = ga_mapping.get(lec_id)
    
    # End-Seite: nächster Vortrag oder letzte PDF-Seite
    end_page = None
    next_id = f"{ga_norm}/{lec_num + 1}"
    next_start = ga_mapping.get(next_id)
    if next_start:
        end_page = next_start - 1
    
    # Fallback: letzte Seite der PDF
    if end_page is None and pdf_pages:
        end_page = pdf_pages[-1][1]
    
    # Fallback für Start: erste Seite
    if start_page is None and pdf_pages:
        start_page = pdf_pages[0][1]
    
    return start_page, end_page


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
    
    # Filtere relevante PDF-Seiten (unterstützt 4-Tupel und 5-Tupel Format)
    relevant_pages = []
    for page_tuple in pdf_pages:
        if len(page_tuple) == 5:
            idx, pn, pe, ts, tsw = page_tuple
        else:
            idx, pn, pe, ts = page_tuple
            tsw = ""
        if start_page <= pn <= end_page:
            relevant_pages.append((idx, pn, pe, ts, tsw))
    
    for pdf_idx, page_num, prev_end, this_start, this_start_words in relevant_pages:
        # Überspringe wenn Seitenzahl nicht die erwartete nächste ist
        if page_num < current_page:
            continue
        
        # Erste Seite: Marker am Anfang des Inhalts
        if page_num == start_page:
            # Suche nach Obsidian-Header (Quelle: [[...]])
            header_match = re.search(r'Quelle:\s*\[\[.*?\]\]\s*\n\n', content_clean)
            if header_match:
                pos = header_match.end()
            else:
                # Kein Header: Marker am Anfang (Position 0)
                pos = 0
            
            markers.append((pos, page_num))
            search_start = pos + 1
            current_page = page_num + 1
            continue
        
        # Finde Position
        pos = find_pagebreak_position(prev_end, this_start, content_clean, search_start, this_start_words)
        
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
        
        # Position nach Satzzeichen verschieben
        pos = adjust_position_after_punctuation(new_content, pos)
        
        # Prüfe ob direkt vor einem Obsidian Block-ID (^xxxxx)
        before_pos = new_content[max(0, pos-15):pos]
        block_id_match = re.search(r'\s*\^[a-z0-9]+$', before_pos)
        
        if block_id_match:
            block_id_start = pos - len(before_pos) + block_id_match.start()
            new_content = new_content[:block_id_start] + marker + new_content[block_id_start:]
        else:
            new_content = new_content[:pos] + marker + new_content[pos:]
    
    # Schritt 5: Verschiebe Marker um Überschriften
    new_content, heading_changes = move_markers_around_headings(new_content)
    
    if not dry_run:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return len(valid_markers)


def is_heading(line: str) -> bool:
    """Prüft ob eine Zeile eine Markdown-Überschrift ist."""
    stripped = line.strip()
    return stripped.startswith('#') and len(stripped) > 1


def move_markers_around_headings(content: str) -> Tuple[str, int]:
    """
    Verschiebt Seitenmarker, die vor/in Überschriften oder am Ende von Absätzen
    vor Überschriften stehen, an den Anfang des ersten Absatzes nach der Überschrift.
    
    Regeln:
    1. Marker sollen nie direkt vor einer Überschrift stehen (|42| ## Title)
    2. Marker sollen nie innerhalb einer Überschrift stehen (## |42| Title)
    3. Marker am Ende eines Absatzes vor einer Überschrift sollen zum Anfang
       des ersten Absatzes nach der Überschrift verschoben werden
    """
    lines = content.split('\n')
    changes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Regel 1: Marker am Anfang einer Überschriftszeile
        if is_heading(line):
            match = re.match(r'^(\s*)(\|(\d+)\|)\s*(#+\s+.*)$', line)
            if match:
                indent = match.group(1)
                marker = match.group(2)
                heading = match.group(4)
                lines[i] = indent + heading
                # Finde nächsten Nicht-Überschrift-Absatz
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Regel 2: Marker INNERHALB einer Überschrift
        if is_heading(line):
            match = re.match(r'^(\s*)(#+)\s*(\|(\d+)\|)\s*(.*)$', line)
            if match:
                indent = match.group(1)
                hashes = match.group(2)
                marker = match.group(3)
                title = match.group(5)
                lines[i] = indent + hashes + ' ' + title
                # Finde nächsten Nicht-Überschrift-Absatz
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Regel 3: Marker am Ende einer Zeile, gefolgt von Leerzeilen und dann Überschrift
        marker_at_end = re.search(r'\|(\d+)\|\s*$', line)
        if marker_at_end and not is_heading(line):
            # Prüfe ob nach Leerzeilen eine Überschrift folgt
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_heading(lines[j]):
                marker = marker_at_end.group(0).strip()
                lines[i] = re.sub(r'\s*\|(\d+)\|\s*$', '', line)
                # Finde nächsten Nicht-Überschrift-Absatz nach der Überschrift
                k = j + 1
                while k < len(lines):
                    content_line = lines[k]
                    if content_line.strip() and not is_heading(content_line):
                        lines[k] = marker + ' ' + content_line.lstrip()
                        changes += 1
                        break
                    k += 1
        
        i += 1
    
    return '\n'.join(lines), changes


def process_ga_md(ga_number: str, dry_run: bool = False, lecture_id: str = None) -> Dict:
    """
    Verarbeitet alle MD-Dateien für eine GA.
    
    lecture_id: Optional - wenn angegeben, wird nur die MD-Datei für diesen Vortrag verarbeitet (z.B. "GA201 (1.)")
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return {"error": f"Ungültige GA-Nummer: {ga_number}"}
    
    print(f"\n{'='*60}")
    if lecture_id:
        print(f"Verarbeite einzelnen Vortrag: {lecture_id} (MD)")
    else:
        print(f"Verarbeite {ga_norm} (MD)")
    print(f"{'='*60}")
    
    # Finde MD-Ordner
    md_folder = find_md_folder_for_ga(ga_norm)
    if not md_folder:
        print(f"  FEHLER: Kein MD-Ordner gefunden")
        return {"error": "Kein MD-Ordner"}
    
    print(f"  MD-Ordner: {md_folder.name}")
    
    # Finde PDF
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print(f"  FEHLER: Keine PDF gefunden")
        return {"error": "Keine PDF"}
    
    print(f"  PDF: {pdf_path.name}")
    
    # Lade Page-Mapping frühzeitig (für Optimierung)
    mapping = load_page_mapping()
    
    # Finde MD-Dateien
    md_files = find_md_files_in_folder(md_folder)
    print(f"  {len(md_files)} MD-Dateien gefunden")
    
    # Wenn lecture_id angegeben, filtere nur die entsprechende MD-Datei
    page_range = None  # Für optimierte PDF-Extraktion
    if lecture_id:
        # Normalisiere lecture_id (z.B. "GA201 (1.)" -> suche nach Datei mit "(1.)")
        lecture_id_normalized = lecture_id.strip()
        # Entferne mögliche GA-Präfixe am Anfang
        if lecture_id_normalized.startswith(ga_norm):
            lecture_id_normalized = lecture_id_normalized[len(ga_norm):].strip()
        
        # Suche nach passender MD-Datei
        matching_md_file = None
        for md_path in md_files:
            md_name = md_path.stem
            # Prüfe verschiedene Formate: "GA201 (1.)", "(1.)", "1"
            if (lecture_id_normalized in md_name or 
                md_name.endswith(lecture_id_normalized) or
                lecture_id_normalized.replace("(", "").replace(")", "").replace(".", "").strip() in md_name):
                matching_md_file = md_path
                break
        
        if not matching_md_file:
            return {"error": f"MD-Datei für Vortrag '{lecture_id}' nicht gefunden"}
        
        md_files = [matching_md_file]
        print(f"  Gefundene MD-Datei: {matching_md_file.name}")
        
        # Versuche Seitenbereich für Optimierung zu ermitteln
        lec_num = extract_lecture_number_from_md(matching_md_file)
        if lec_num is not None:
            ga_mapping = mapping.get(ga_norm, {})
            lec_id = f"{ga_norm}/{lec_num}"
            start_page = ga_mapping.get(lec_id)
            if start_page:
                # Finde End-Seite
                next_id = f"{ga_norm}/{lec_num + 1}"
                next_start = ga_mapping.get(next_id)
                if next_start:
                    end_page = next_start - 1
                else:
                    # Schätze basierend auf Textlänge
                    with open(matching_md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    text_length = len(content)
                    estimated_pages = max(5, text_length // 500)
                    end_page = start_page + estimated_pages
                
                # Füge Puffer hinzu
                page_range = (max(1, start_page - 10), end_page + 10)
                print(f"  Optimierung: Extrahiere nur Seiten {page_range[0]}-{page_range[1]} aus PDF")
    
    # Extrahiere PDF-Seiten (mit optionaler Optimierung)
    print(f"  Extrahiere PDF-Seiten...")
    pdf_pages = extract_pdf_pages(pdf_path, page_range=page_range)
    print(f"  {len(pdf_pages)} Seiten mit Seitenzahlen")
    
    if not pdf_pages:
        return {"error": "Keine Seiten mit Seitenzahlen"}
    
    # Verarbeite jede MD-Datei
    total_inserted = 0
    processed = 0
    
    for md_path in md_files:
        lec_num = extract_lecture_number_from_md(md_path)
        if lec_num is None:
            continue
        
        start_page, end_page = get_page_range_for_md(
            md_path, ga_norm, mapping, md_files, pdf_pages
        )
        
        if start_page is None or end_page is None:
            print(f"    {ga_norm}/{lec_num}: Kein Seitenbereich")
            continue
        
        count = insert_markers_in_md(md_path, pdf_pages, start_page, end_page, dry_run)
        total_inserted += count
        processed += 1
        
        expected = end_page - start_page + 1
        title = md_path.stem[:40]
        print(f"    {ga_norm}/{lec_num}: {count}/{expected} Marker (S.{start_page}-{end_page})")
    
    print(f"\n  Gesamt: {total_inserted} Marker in {processed} Dateien")
    
    return {
        "ga": ga_norm,
        "files": processed,
        "markers_inserted": total_inserted
    }


def main():
    parser = argparse.ArgumentParser(description="Fügt Seitenmarker in Obsidian-MD-Dateien ein")
    parser.add_argument("ga", nargs="+", help="GA-Nummer(n) oder Bereich (z.B. 51 67)")
    parser.add_argument("--dry-run", action="store_true", help="Nur simulieren")
    
    args = parser.parse_args()
    
    # Parse GA-Nummern
    ga_numbers = []
    if len(args.ga) == 2 and args.ga[0].isdigit() and args.ga[1].isdigit():
        # Bereich: 51 67 -> GA051 bis GA067
        start = int(args.ga[0])
        end = int(args.ga[1])
        for i in range(start, end + 1):
            ga_numbers.append(str(i))
    else:
        ga_numbers = args.ga
    
    results = []
    total_markers = 0
    
    for ga in ga_numbers:
        result = process_ga_md(ga, args.dry_run)
        results.append(result)
        if "markers_inserted" in result:
            total_markers += result["markers_inserted"]
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    success = sum(1 for r in results if "markers_inserted" in r)
    errors = sum(1 for r in results if "error" in r)
    
    print(f"  Erfolgreich: {success}")
    print(f"  Fehler: {errors}")
    print(f"\n  Gesamt Marker: {total_markers}")
    
    if args.dry_run:
        print("\n  (Dry-Run - keine Änderungen gespeichert)")


if __name__ == "__main__":
    main()
