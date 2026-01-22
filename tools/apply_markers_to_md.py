#!/usr/bin/env python3
"""
Überträgt Seitenmarker aus pagebreaks-JSON dauerhaft in MD-Dateien.

Formatierungsregeln:
- Marker zwischen Wörtern: Leerzeichen davor und danach, z.B. "es hat |22| sich ergeben"
- Marker innerhalb eines getrennten Wortes: Keine Leerzeichen, z.B. "Tages|33|bewusstsein"
- Marker nie vor Überschriften (#, ##, etc.), sondern am Anfang des folgenden Absatzes

Verwendung:
  python tools/apply_markers_to_md.py GA001
  python tools/apply_markers_to_md.py GA001 --dry-run
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


PROJECT_DIR = Path(__file__).parent.parent
PAGEBREAKS_DIR = PROJECT_DIR / "pagebreaks"
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"


def normalize_ga(ga: str) -> str:
    """Normalisiert GA-Nummer zu Format GA001, GA001a, etc."""
    match = re.search(r'(\d+)([a-z]?)', ga, re.IGNORECASE)
    if match:
        num = match.group(1).zfill(3)
        suffix = match.group(2).lower() if match.group(2) else ""
        return f"GA{num}{suffix}"
    return ga.upper()


def find_pagebreaks_file(ga_norm: str) -> Optional[Path]:
    """Findet die pagebreaks-JSON für eine GA."""
    # Zuerst im Hauptverzeichnis suchen
    main_file = PAGEBREAKS_DIR / f"{ga_norm}.json"
    if main_file.exists():
        return main_file
    
    # Dann im archive Ordner
    archive_file = PAGEBREAKS_DIR / "archive" / f"{ga_norm}.json"
    if archive_file.exists():
        return archive_file
    
    return None


def find_ga_folder(ga_norm: str) -> Optional[Path]:
    """Findet den GA-Ordner in Steiner_GA/."""
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            return folder
    return None


def fix_marker_spacing(text: str) -> str:
    """
    Korrigiert die Leerzeichen um Seitenmarker.
    
    Regeln:
    - Wenn der Marker zwischen zwei Buchstaben steht (Worttrennung): kein Leerzeichen
    - Wenn der Marker zwischen Wörtern steht: Leerzeichen davor und danach
    """
    # Pattern für Marker: |123|
    marker_pattern = r'\|(\d+)\|'
    
    def fix_single_marker(match):
        page_num = match.group(1)
        marker = f"|{page_num}|"
        
        # Finde Position im Text
        start = match.start()
        end = match.end()
        
        # Zeichen vor und nach dem Marker
        char_before = text[start - 1] if start > 0 else ' '
        char_after = text[end] if end < len(text) else ' '
        
        # Prüfe ob Worttrennung (Buchstabe vor UND nach dem Marker)
        is_word_split = char_before.isalpha() and char_after.isalpha()
        
        if is_word_split:
            # Worttrennung: kein Leerzeichen
            return marker
        else:
            # Zwischen Wörtern: Leerzeichen
            result = marker
            # Leerzeichen davor, wenn nicht schon vorhanden und nicht am Anfang
            if start > 0 and char_before not in ' \n\t':
                result = ' ' + result
            # Leerzeichen danach, wenn nicht schon vorhanden und nicht am Ende
            if end < len(text) and char_after not in ' \n\t':
                result = result + ' '
            return result
    
    # Wir müssen das iterativ machen, da sich Positionen ändern
    result = text
    offset = 0
    
    for match in re.finditer(marker_pattern, text):
        page_num = match.group(1)
        marker = f"|{page_num}|"
        
        start = match.start() + offset
        end = match.end() + offset
        
        # Zeichen vor und nach dem Marker im aktuellen result
        char_before = result[start - 1] if start > 0 else ' '
        char_after = result[end] if end < len(result) else ' '
        
        # Prüfe ob Worttrennung
        is_word_split = char_before.isalpha() and char_after.isalpha()
        
        if is_word_split:
            # Worttrennung: stelle sicher, dass KEINE Leerzeichen sind
            # Entferne evtl. vorhandene Leerzeichen
            new_start = start
            new_end = end
            
            # Prüfe ob Leerzeichen vor dem Marker
            if start > 0 and result[start - 1] == ' ':
                new_start = start - 1
                offset -= 1
            # Prüfe ob Leerzeichen nach dem Marker
            if end < len(result) and result[end] == ' ':
                new_end = end + 1
                offset -= 1
            
            result = result[:new_start] + marker + result[new_end:]
        else:
            # Zwischen Wörtern: füge Leerzeichen hinzu wenn nötig
            new_marker = marker
            
            # Leerzeichen davor
            if start > 0 and char_before not in ' \n\t':
                new_marker = ' ' + new_marker
                offset += 1
            
            # Leerzeichen danach
            if end < len(result) and char_after not in ' \n\t':
                new_marker = new_marker + ' '
                offset += 1
            
            result = result[:start] + new_marker + result[end:]
    
    return result


def extract_paragraph_id(line: str) -> Optional[str]:
    """Extrahiert die Paragraph-ID aus einer Zeile (z.B. ^abc123)."""
    match = re.search(r'\^([a-z0-9]+)\s*$', line)
    if match:
        return f"^{match.group(1)}"
    return None


def is_heading(line: str) -> bool:
    """Prüft ob eine Zeile eine Markdown-Überschrift ist (#, ##, ###, ####)."""
    stripped = line.lstrip()
    return bool(re.match(r'^#{1,6}\s', stripped))


def extract_leading_markers(line: str) -> Tuple[List[str], str]:
    """
    Extrahiert führende Seitenmarker am Anfang einer Zeile.
    
    Returns: (liste_der_marker, rest_der_zeile)
    """
    markers = []
    rest = line
    
    # Pattern für Marker am Anfang (mit optionalem Leerzeichen danach)
    while True:
        match = re.match(r'^(\|(\d+)\|)\s*', rest)
        if match:
            markers.append(match.group(1))
            rest = rest[match.end():]
        else:
            break
    
    return markers, rest


def extract_trailing_markers(line: str) -> Tuple[str, List[str]]:
    """
    Extrahiert abschließende Seitenmarker am Ende einer Zeile.
    
    Returns: (rest_der_zeile, liste_der_marker)
    """
    markers = []
    rest = line.rstrip()
    
    # Pattern für Marker am Ende (mit optionalem Leerzeichen davor)
    # Aber NICHT wenn danach noch eine Paragraph-ID kommt (^abc123)
    while True:
        # Prüfe ob am Ende ein Marker steht (vor evtl. Paragraph-ID)
        match = re.search(r'\s*(\|(\d+)\|)\s*$', rest)
        if match:
            # Prüfe dass es keine Paragraph-ID ist
            potential_marker = match.group(1)
            markers.insert(0, potential_marker)  # Am Anfang einfügen (Reihenfolge beibehalten)
            rest = rest[:match.start()].rstrip()
        else:
            break
    
    return rest, markers


def find_next_content_line(lines: List[str], start_idx: int) -> Tuple[int, str]:
    """
    Findet die nächste nicht-leere Zeile ab start_idx.
    
    Returns: (index, zeile) oder (-1, '') wenn keine gefunden
    """
    for i in range(start_idx, len(lines)):
        if lines[i].strip():
            return i, lines[i]
    return -1, ''


def move_markers_around_headings(lines: List[str]) -> List[str]:
    """
    Verschiebt Seitenmarker von/vor Überschriften zum nächsten Absatz.
    
    Regeln:
    1. Marker am Anfang einer Überschrift → zum nächsten Absatz verschieben
    2. Marker am Ende eines Absatzes, wenn die nächste nicht-leere Zeile eine 
       Überschrift ist → zum ersten Absatz nach der Überschrift verschieben
    """
    result = []
    pending_markers = []  # Marker, die zum nächsten Absatz verschoben werden sollen
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Prüfe ob die Zeile eine Überschrift ist
        if is_heading(line):
            # Extrahiere führende Marker von der Überschrift
            markers, rest = extract_leading_markers(stripped)
            
            if markers:
                # Marker gefunden - merken und Überschrift ohne Marker speichern
                pending_markers.extend(markers)
                result.append(rest)
            else:
                result.append(line)
        
        elif stripped == '':
            # Leere Zeile - behalten, keine Marker einfügen
            result.append(line)
        
        else:
            # Normaler Absatz
            # Zuerst: Füge aufgestaute Marker am Anfang ein
            if pending_markers:
                marker_str = ' '.join(pending_markers) + ' '
                line = marker_str + line
                pending_markers = []
            
            # Dann: Prüfe ob dieser Absatz Marker am Ende hat, die vor einer Überschrift stehen
            # Finde die nächste nicht-leere Zeile
            next_idx, next_line = find_next_content_line(lines, i + 1)
            
            if next_idx != -1 and is_heading(next_line):
                # Die nächste nicht-leere Zeile ist eine Überschrift
                # Extrahiere Marker am Ende dieses Absatzes
                rest, trailing_markers = extract_trailing_markers(line)
                
                if trailing_markers:
                    # Marker gefunden - entferne sie vom Ende und merke sie
                    pending_markers.extend(trailing_markers)
                    # Behalte evtl. Paragraph-ID
                    para_id_match = re.search(r'(\s*\^[a-z0-9]+)\s*$', line)
                    if para_id_match:
                        # Paragraph-ID wieder anhängen
                        result.append(rest + para_id_match.group(1))
                    else:
                        result.append(rest)
                else:
                    result.append(line)
            else:
                result.append(line)
        
        i += 1
    
    # Falls noch Marker übrig sind (am Ende des Dokuments), ans Ende hängen
    if pending_markers:
        # Füge sie zur letzten nicht-leeren Zeile hinzu oder als neue Zeile
        for j in range(len(result) - 1, -1, -1):
            if result[j].strip() and not is_heading(result[j]):
                result[j] = ' '.join(pending_markers) + ' ' + result[j]
                break
        else:
            result.append(' '.join(pending_markers))
    
    return result


def load_pagebreaks_data(pb_file: Path) -> Dict[str, str]:
    """
    Lädt die pagebreaks-Daten und erstellt ein Mapping von paragraph_id -> text_mit_markern.
    """
    with open(pb_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mapping = {}
    
    # Für Bücher (GA001 etc.)
    if 'book' in data and 'paragraphs' in data['book']:
        for para in data['book']['paragraphs']:
            para_id = para.get('index', '')
            content = para.get('content', para.get('text', ''))
            if para_id and content:
                # Korrigiere Leerzeichen
                content = fix_marker_spacing(content)
                mapping[para_id] = content
    
    # Für Vorträge
    if 'lectures' in data:
        for lecture in data['lectures']:
            for para in lecture.get('paragraphs', []):
                para_id = para.get('index', '')
                content = para.get('content', para.get('text', ''))
                if para_id and content:
                    content = fix_marker_spacing(content)
                    mapping[para_id] = content
    
    return mapping


def process_md_file(md_file: Path, pb_mapping: Dict[str, str], dry_run: bool = False) -> Tuple[int, int]:
    """
    Verarbeitet eine MD-Datei und fügt Marker ein.
    
    Returns: (markers_added, paragraphs_updated)
    """
    content = md_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    new_lines = []
    markers_added = 0
    paragraphs_updated = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        para_id = extract_paragraph_id(line)
        
        if para_id and para_id in pb_mapping:
            # Dieser Paragraph hat markierten Text in der pagebreaks-JSON
            pb_text = pb_mapping[para_id]
            
            # Zähle vorhandene Marker in der aktuellen Zeile
            existing_markers = len(re.findall(r'\|\d+\|', line))
            new_markers = len(re.findall(r'\|\d+\|', pb_text))
            
            if new_markers > existing_markers:
                # Ersetze den Paragraphentext, behalte aber die ID
                # Die ID ist am Ende der Zeile
                new_line = pb_text
                if not new_line.rstrip().endswith(para_id):
                    # ID fehlt, füge sie hinzu
                    new_line = new_line.rstrip() + ' ' + para_id
                
                new_lines.append(new_line)
                markers_added += (new_markers - existing_markers)
                paragraphs_updated += 1
            else:
                # Korrigiere nur die Leerzeichen
                fixed_line = fix_marker_spacing(line)
                new_lines.append(fixed_line)
        else:
            # Kein Mapping - nur Leerzeichen korrigieren falls Marker vorhanden
            if '|' in line and re.search(r'\|\d+\|', line):
                fixed_line = fix_marker_spacing(line)
                new_lines.append(fixed_line)
            else:
                new_lines.append(line)
        
        i += 1
    
    # Verschiebe Marker von/vor Überschriften zum nächsten Absatz
    new_lines = move_markers_around_headings(new_lines)
    
    new_content = '\n'.join(new_lines)
    
    if not dry_run and new_content != content:
        md_file.write_text(new_content, encoding='utf-8')
    
    return markers_added, paragraphs_updated


def process_ga(ga_number: str, dry_run: bool = False) -> None:
    """Verarbeitet alle MD-Dateien für eine GA."""
    ga_norm = normalize_ga(ga_number)
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_norm}")
    print(f"{'='*60}")
    
    # Finde pagebreaks-JSON
    pb_file = find_pagebreaks_file(ga_norm)
    if not pb_file:
        print(f"  FEHLER: Keine pagebreaks-JSON gefunden für {ga_norm}")
        return
    print(f"  Pagebreaks: {pb_file.name}")
    
    # Finde GA-Ordner
    ga_folder = find_ga_folder(ga_norm)
    if not ga_folder:
        print(f"  FEHLER: Kein GA-Ordner gefunden für {ga_norm}")
        return
    print(f"  GA-Ordner: {ga_folder.name}")
    
    # Lade pagebreaks-Daten
    pb_mapping = load_pagebreaks_data(pb_file)
    print(f"  Geladene Paragraphen mit Markern: {len(pb_mapping)}")
    
    # Zähle Marker im Mapping
    total_pb_markers = sum(len(re.findall(r'\|\d+\|', text)) for text in pb_mapping.values())
    print(f"  Marker in pagebreaks: {total_pb_markers}")
    
    # Verarbeite alle MD-Dateien
    md_files = list(ga_folder.glob(f"{ga_norm}*.md"))
    if not md_files:
        print(f"  WARNUNG: Keine MD-Dateien gefunden mit Pattern {ga_norm}*.md")
        # Versuche alternatives Pattern
        md_files = list(ga_folder.glob("*.md"))
        print(f"  Gefundene MD-Dateien: {[f.name for f in md_files]}")
    
    total_markers_added = 0
    total_paras_updated = 0
    
    for md_file in sorted(md_files):
        markers, paras = process_md_file(md_file, pb_mapping, dry_run)
        if markers > 0 or paras > 0:
            print(f"  {md_file.name}: +{markers} Marker, {paras} Paragraphen aktualisiert")
        total_markers_added += markers
        total_paras_updated += paras
    
    print(f"\n  Zusammenfassung:")
    print(f"    Neue Marker eingefügt: {total_markers_added}")
    print(f"    Paragraphen aktualisiert: {total_paras_updated}")
    
    if dry_run:
        print(f"\n  [DRY-RUN] Keine Dateien wurden geändert.")


def main():
    parser = argparse.ArgumentParser(description="Überträgt Seitenmarker in MD-Dateien")
    parser.add_argument("ga", help="GA-Nummer (z.B. GA001, 001, 1)")
    parser.add_argument("--dry-run", "-n", action="store_true", 
                        help="Nur anzeigen, nichts ändern")
    
    args = parser.parse_args()
    process_ga(args.ga, args.dry_run)


if __name__ == "__main__":
    main()
