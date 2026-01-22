#!/usr/bin/env python3
"""
Fügt Seitenmarker in MD-Dateien ein.
Verwendet die Breaks aus page-break-markers.json (nicht PDF).
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Pfade
PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
PAGE_BREAK_MARKERS_FILE = PROJECT_DIR / "page-break-markers.json"


def normalize_ga(ga_input: str) -> Optional[str]:
    """Normalisiert GA-Nummer zu Format GA001."""
    match = re.search(r'(\d+)([a-z]?)', ga_input, re.IGNORECASE)
    if not match:
        return None
    num = match.group(1).zfill(3)
    suffix = match.group(2).lower() if match.group(2) else ""
    return f"GA{num}{suffix}".upper()


def load_breaks_from_json(ga_norm: str) -> List[Dict]:
    """Lädt die Breaks aus page-break-markers.json."""
    if not PAGE_BREAK_MARKERS_FILE.exists():
        return []
    
    with open(PAGE_BREAK_MARKERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ga_data = data.get(ga_norm, {})
    return ga_data.get('breaks', [])


def find_md_folder_for_ga(ga_norm: str) -> Optional[Path]:
    """Findet den MD-Ordner für eine GA."""
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            return folder
    return None


def find_md_files_in_folder(folder: Path) -> List[Path]:
    """Findet alle MD-Dateien in einem Ordner."""
    return sorted(folder.glob("*.md"))


def remove_existing_markers(text: str) -> str:
    """Entfernt alle existierenden Seitenmarker."""
    return re.sub(r'\|(\d+)\|', '', text)


def normalize_text(text: str) -> str:
    """Normalisiert Text für Vergleich."""
    if not text:
        return ""
    s = text.lower()
    # ß -> ss
    s = s.replace("ß", "ss")
    # Umlaute normalisieren
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    # Nur alphanumerisch
    s = re.sub(r'[^a-z0-9]', '', s)
    return s


def find_break_position(
    left_text: str,
    right_text: str,
    content: str,
    min_pos: int,
    hyphenated: bool
) -> Optional[int]:
    """
    Findet die Position eines Seitenumbruchs im MD-Text.
    
    left_text: Text am Ende der vorherigen Seite
    right_text: Text am Anfang der neuen Seite
    hyphenated: True wenn Wort über Umbruch getrennt
    """
    content_lower = content.lower()
    content_norm = normalize_text(content)
    
    # Normalisiere die Suchtexte
    left_norm = normalize_text(left_text) if left_text else ""
    right_norm = normalize_text(right_text) if right_text else ""
    
    # Strategie 1: Bei Silbentrennung - suche kombiniertes Wort
    if hyphenated and left_text and right_text:
        # Extrahiere letztes Wortfragment von left (vor dem Bindestrich)
        left_clean = left_text.replace('\n', ' ').strip()
        # Entferne trailing Bindestrich
        if left_clean.endswith('-'):
            left_clean = left_clean[:-1]
        
        # Letztes Wort(fragment) von left
        left_words = left_clean.split()
        if left_words:
            fragment = left_words[-1].lower()
            
            # Erstes Wort von right
            right_clean = right_text.replace('\n', ' ').strip()
            right_words = right_clean.split()
            if right_words:
                continuation = right_words[0].lower()
                
                # Kombiniere: fragment + continuation
                combined = fragment + continuation
                
                # Suche im Content
                pos = content_lower.find(combined, min_pos)
                if pos != -1:
                    # Position nach dem Fragment
                    return pos + len(fragment)
    
    # Strategie 2: Suche nach right_text (Anfang der neuen Seite)
    if right_text:
        # Versuche verschiedene Längen
        for length in [60, 50, 40, 30, 20, 15]:
            if len(right_norm) < length:
                continue
            
            snippet = right_norm[:length]
            
            # Suche im normalisierten Content
            search_start = int(min_pos * 0.7)  # Approximation
            pos = content_norm.find(snippet, search_start)
            if pos != -1:
                # Mappe zurück zur Original-Position
                orig_pos = map_norm_to_original(content, pos)
                if orig_pos >= min_pos:
                    return orig_pos
    
    # Strategie 3: Suche nach left_text (Ende der vorherigen Seite)
    if left_text:
        # Letzten Teil von left suchen
        for length in [40, 30, 20, 15]:
            if len(left_norm) < length:
                continue
            
            snippet = left_norm[-length:]
            
            search_start = int(min_pos * 0.7)
            pos = content_norm.find(snippet, search_start)
            if pos != -1:
                # Position nach dem gefundenen Text
                orig_pos = map_norm_to_original(content, pos + length)
                if orig_pos >= min_pos:
                    return orig_pos
    
    return None


def map_norm_to_original(text: str, norm_pos: int) -> int:
    """Mappt Position im normalisierten Text zurück zum Original."""
    if norm_pos <= 0:
        return 0
    
    norm_count = 0
    for i, char in enumerate(text):
        # Prüfe ob Zeichen in normalisiertem Text erscheint
        if char.lower().isalnum() or char.lower() in 'äöüß':
            norm_count += 1
            if char.lower() == 'ß':
                norm_count += 1  # ß -> ss
        
        if norm_count >= norm_pos:
            return i + 1
    
    return len(text)


def is_heading(line: str) -> bool:
    """Prüft ob eine Zeile eine Markdown-Überschrift ist."""
    stripped = line.strip()
    return stripped.startswith('#') and len(stripped) > 1


def move_markers_around_headings(content: str) -> Tuple[str, int]:
    """
    Verschiebt Marker die vor/in Überschriften stehen.
    """
    lines = content.split('\n')
    changes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Marker am Anfang einer Überschrift
        if is_heading(line):
            match = re.match(r'^(\s*)(\|(\d+)\|)\s*(#+\s+.*)$', line)
            if match:
                marker = match.group(2)
                heading = match.group(4)
                lines[i] = heading
                j = i + 1
                while j < len(lines):
                    if lines[j].strip() and not is_heading(lines[j]):
                        lines[j] = marker + ' ' + lines[j].lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Marker innerhalb einer Überschrift (## |42| Title)
        if is_heading(line):
            match = re.match(r'^(\s*)(#+)\s*(\|(\d+)\|)\s*(.*)$', line)
            if match:
                hashes = match.group(2)
                marker = match.group(3)
                title = match.group(5)
                lines[i] = hashes + ' ' + title
                j = i + 1
                while j < len(lines):
                    if lines[j].strip() and not is_heading(lines[j]):
                        lines[j] = marker + ' ' + lines[j].lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Marker am Ende vor Überschrift
        marker_at_end = re.search(r'\|(\d+)\|\s*$', line)
        if marker_at_end and not is_heading(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_heading(lines[j]):
                marker = marker_at_end.group(0).strip()
                lines[i] = re.sub(r'\s*\|(\d+)\|\s*$', '', line)
                k = j + 1
                while k < len(lines):
                    if lines[k].strip() and not is_heading(lines[k]):
                        lines[k] = marker + ' ' + lines[k].lstrip()
                        changes += 1
                        break
                    k += 1
        
        i += 1
    
    return '\n'.join(lines), changes


def insert_markers_from_json(
    md_path: Path,
    breaks: List[Dict],
    dry_run: bool = False
) -> int:
    """
    Fügt Seitenmarker basierend auf page-break-markers.json ein.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Entferne existierende Marker
    content_clean = remove_existing_markers(content)
    
    # Sammle Marker-Positionen
    markers = []  # (position, page_num)
    search_start = 0
    
    for brk in breaks:
        page = brk.get('page')
        left = brk.get('left', '')
        right = brk.get('right', '')
        hyphenated = brk.get('hyphenated', False)
        is_first = brk.get('isFirstPage', False)
        
        if not page:
            continue
        
        # Erste Seite: am Anfang
        if is_first:
            markers.append((0, page))
            search_start = 1
            continue
        
        # Finde Position
        pos = find_break_position(left, right, content_clean, search_start, hyphenated)
        
        if pos is not None and pos > search_start:
            markers.append((pos, page))
            search_start = pos + 1
    
    if not markers:
        return 0
    
    # Validierung: streng aufsteigend
    valid_markers = []
    last_pos = -1
    last_page = -1
    
    for pos, page in sorted(markers, key=lambda x: x[0]):
        if pos > last_pos and page > last_page:
            valid_markers.append((pos, page))
            last_pos = pos
            last_page = page
    
    # Füge Marker ein (von hinten nach vorne)
    valid_markers.sort(key=lambda x: x[0], reverse=True)
    
    new_content = content_clean
    for pos, page in valid_markers:
        marker = f"|{page}|"
        new_content = new_content[:pos] + marker + new_content[pos:]
    
    # Verschiebe Marker um Überschriften
    new_content, _ = move_markers_around_headings(new_content)
    
    if not dry_run:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return len(valid_markers)


def process_ga(ga_number: str, dry_run: bool = False) -> Dict:
    """Verarbeitet alle MD-Dateien für eine GA."""
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return {"error": f"Ungültige GA-Nummer: {ga_number}"}
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_norm}")
    print(f"{'='*60}")
    
    # Lade Breaks aus JSON
    breaks = load_breaks_from_json(ga_norm)
    if not breaks:
        print(f"  FEHLER: Keine Breaks in page-break-markers.json")
        return {"error": "Keine Breaks"}
    
    print(f"  {len(breaks)} Breaks geladen")
    
    # Finde MD-Ordner
    md_folder = find_md_folder_for_ga(ga_norm)
    if not md_folder:
        print(f"  FEHLER: Kein MD-Ordner gefunden")
        return {"error": "Kein MD-Ordner"}
    
    print(f"  MD-Ordner: {md_folder.name}")
    
    # Finde MD-Dateien
    md_files = find_md_files_in_folder(md_folder)
    print(f"  {len(md_files)} MD-Dateien gefunden")
    
    # Verarbeite Hauptdatei (ohne Vortragsnummer im Namen)
    total_inserted = 0
    processed = 0
    
    for md_path in md_files:
        # Nur Dateien ohne Vortragsnummer (Bücher)
        if re.search(r'\(\d+\.\)', md_path.stem):
            continue
        
        count = insert_markers_from_json(md_path, breaks, dry_run)
        total_inserted += count
        processed += 1
        
        print(f"    {md_path.name}: {count}/{len(breaks)} Marker")
    
    print(f"\n  Gesamt: {total_inserted} Marker in {processed} Dateien")
    
    return {
        "ga": ga_norm,
        "files": processed,
        "markers_inserted": total_inserted
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fügt Seitenmarker aus page-break-markers.json in MD-Dateien ein"
    )
    parser.add_argument("ga", nargs="+", help="GA-Nummer(n)")
    parser.add_argument("--dry-run", action="store_true", help="Nur simulieren")
    
    args = parser.parse_args()
    
    for ga in args.ga:
        process_ga(ga, args.dry_run)


if __name__ == "__main__":
    main()
