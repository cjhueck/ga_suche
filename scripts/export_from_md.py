#!/usr/bin/env python3
"""
Exportiert Wandtafeln aus MD-Dateien nach chalkboards/.

Parst die MD-Datei, findet Bilder mit zugehörigen GA/Tafel/Datum-Infos,
und kopiert sie mit korrektem Namen in den chalkboards-Ordner.
"""

import os
import sys
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STEINER_GA_DIR = PROJECT_ROOT / "Steiner_GA"
CHALKBOARDS_DIR = STEINER_GA_DIR / "chalkboards"

# Monats-Mapping
MONTHS_DE = {
    'januar': '01', 'februar': '02', 'märz': '03', 'maerz': '03', 'marz': '03',
    'april': '04', 'mai': '05', 'juni': '06',
    'juli': '07', 'august': '08', 'september': '09',
    'oktober': '10', 'november': '11', 'dezember': '12'
}


def parse_date(text: str) -> str | None:
    """Parst deutsches Datum zu ISO-Format."""
    text_lower = text.lower()
    
    # Format: 26. NOVEMBER 1920
    match = re.search(r'(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})', text_lower)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).strip()
        year = match.group(3)
        month = MONTHS_DE.get(month_name)
        if month:
            return f"{year}-{month}-{day:02d}"
    
    return None


def parse_ga_tafel(text: str) -> tuple[str, int] | None:
    """Parst GA-Nummer und Tafel-Nummer."""
    text_upper = text.upper()
    
    # Tolerant für OCR-Fehler: G.A, GA, TAFEL, TAFELN, etc.
    # Pattern: G.?A (optional Punkt) + Nummer + TAFEL(N) + Nummer
    match = re.search(r'G\.?A\.?\s*(\d+[A-Z]?)\s*TAFELN?\s*(\d+)', text_upper)
    if match:
        ga_raw = match.group(1)
        tafel = int(match.group(2))
        
        # Normalisiere GA-Nummer
        num_match = re.match(r'(\d+)([A-Z])?', ga_raw)
        if num_match:
            ga = f"{int(num_match.group(1)):03d}"
            if num_match.group(2):
                ga += num_match.group(2)
            return ga, tafel
    
    # Fallback: Nur GA-Nummer ohne Tafel (Tafel = 1)
    ga_only = re.search(r'G\.?A\.?\s*(\d+[A-Z]?)\b', text_upper)
    if ga_only:
        ga_raw = ga_only.group(1)
        num_match = re.match(r'(\d+)([A-Z])?', ga_raw)
        if num_match:
            ga = f"{int(num_match.group(1)):03d}"
            if num_match.group(2):
                ga += num_match.group(2)
            return ga, 1  # Default Tafel 1
    
    return None


def find_section_for_line(lines: list[str], line_idx: int) -> str:
    """
    Findet den Abschnitt (zwischen --- Trennlinien) für eine bestimmte Zeile.
    """
    # Suche nach oben zur vorherigen Trennlinie
    start = line_idx
    while start > 0:
        if lines[start].strip() == '---':
            start += 1
            break
        start -= 1
    
    # Suche nach unten zur nächsten Trennlinie
    end = line_idx
    while end < len(lines):
        if lines[end].strip() == '---':
            break
        end += 1
    
    return '\n'.join(lines[start:end])


def find_tafeln_in_md(md_path: Path) -> list[dict]:
    """
    Findet alle Tafeln in einer MD-Datei.
    
    Sucht nach Bildern und zugehörigen GA/Tafel/Datum-Infos im gleichen Abschnitt.
    """
    content = md_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    tafeln = []
    
    for i, line in enumerate(lines):
        # Suche nach Bild - Markdown Format mit URL-encoded Pfad
        # Der Pfad kann Klammern enthalten, daher bis .jpeg/.png/.webp suchen
        img_match = re.search(r'!\[.*?\]\((assets/[^)]*?\.(?:jpeg|jpg|png|webp))\)', line, re.IGNORECASE)
        
        if not img_match:
            # Format mit Klammern im Pfad - suche bis zum letzten .jpeg/.png
            img_match = re.search(r'!\[.*?\]\((assets/.*?\.(?:jpeg|jpg|png|webp))\)', line, re.IGNORECASE)
        
        if not img_match:
            # Format mit <> Klammern: ![alt](<assets/...(U1-U4>)_img-X.jpeg)
            # Der > ist an der falschen Stelle, korrigiere zu (U1-U4)
            img_match = re.search(r'!\[.*?\]\(<(assets/[^>]+\(U1-U4)>\)_img-(\d+)\.(?:jpeg|jpg|png|webp)\)', line, re.IGNORECASE)
            if img_match:
                # Rekonstruiere den korrekten Pfad - ersetze (U1-U4 mit (U1-U4)
                base_path = img_match.group(1) + ")"
                img_num = img_match.group(2)
                img_path = f"{base_path}_img-{img_num}.jpeg"
                # Fahre mit der Verarbeitung fort
                section = find_section_for_line(lines, i)
                ga_tafel = parse_ga_tafel(section)
                date = parse_date(section)
                if not ga_tafel and i > 0:
                    prev_section = find_section_for_line(lines, max(0, i-5))
                    ga_tafel = parse_ga_tafel(prev_section)
                    if not date:
                        date = parse_date(prev_section)
                if not ga_tafel and i < len(lines) - 1:
                    next_section = find_section_for_line(lines, min(len(lines)-1, i+5))
                    ga_tafel = parse_ga_tafel(next_section)
                    if not date:
                        date = parse_date(next_section)
                if ga_tafel:
                    ga, tafel = ga_tafel
                    tafeln.append({
                        'img_path': img_path,
                        'ga': ga,
                        'tafel': tafel,
                        'date': date,
                        'line': i
                    })
                continue
        
        if not img_match:
            # Obsidian-Format mit assets/
            img_match = re.search(r'!\[\[(assets/[^\]]+\.(?:jpeg|jpg|png|webp))\]\]', line, re.IGNORECASE)
        
        if not img_match:
            # Obsidian-Format ohne assets/ (z.B. Pasted image...)
            img_match = re.search(r'!\[\[([^\]]+\.(?:jpeg|jpg|png|webp))\]\]', line, re.IGNORECASE)
            if img_match:
                # Füge assets/ hinzu
                img_path = 'assets/' + img_match.group(1)
            else:
                continue
        else:
            img_path = unquote(img_match.group(1))
        
        # Finde den Abschnitt zwischen den --- Trennlinien
        section = find_section_for_line(lines, i)
        
        # Wenn im Abschnitt nichts gefunden, suche auch in angrenzenden Abschnitten
        ga_tafel = parse_ga_tafel(section)
        date = parse_date(section)
        
        # Fallback: Suche in erweitertem Bereich (30 Zeilen)
        if not ga_tafel or not date:
            start = max(0, i - 30)
            end = min(len(lines), i + 30)
            extended_context = '\n'.join(lines[start:end])
            if not ga_tafel:
                ga_tafel = parse_ga_tafel(extended_context)
            if not date:
                date = parse_date(extended_context)
        
        if ga_tafel:
            ga, tafel = ga_tafel
            tafeln.append({
                'img_path': img_path,
                'ga': ga,
                'tafel': tafel,
                'date': date,
                'line': i + 1
            })
    
    return tafeln


def process_ga_k(ga_k_num: int, dry_run: bool = False) -> int:
    """
    Verarbeitet einen GA K Band.
    
    Returns: Anzahl exportierter Tafeln
    """
    # Finde den GA K Ordner
    ga_k_pattern = f"GA K 58_{ga_k_num} *"
    ga_k_folders = list(STEINER_GA_DIR.glob(ga_k_pattern))
    
    if not ga_k_folders:
        print(f"  Ordner nicht gefunden: {ga_k_pattern}")
        return 0
    
    ga_k_folder = ga_k_folders[0]
    
    # Finde MD-Datei - bevorzuge Unterordner mit "_1" suffix
    md_files = list(ga_k_folder.rglob("*.md"))
    
    if not md_files:
        print(f"  Keine MD-Datei gefunden in {ga_k_folder}")
        return 0
    
    # Bevorzuge MD-Dateien in "_1" Unterordnern (bessere OCR-Qualität)
    md_files_in_subfolders = [f for f in md_files if "_1" in f.parent.name]
    
    if md_files_in_subfolders:
        # Nimm die größte aus den Unterordnern
        md_file = max(md_files_in_subfolders, key=lambda f: f.stat().st_size)
    else:
        # Fallback: größte MD-Datei
        md_file = max(md_files, key=lambda f: f.stat().st_size)
    
    assets_folder = md_file.parent / "assets"
    
    print(f"  MD-Datei: {md_file.name}")
    print(f"  Assets: {assets_folder}")
    
    # Parse MD-Datei
    tafeln = find_tafeln_in_md(md_file)
    print(f"  Gefunden: {len(tafeln)} Tafeln")
    
    if not tafeln:
        return 0
    
    # Zähler für Tafeln pro GA+Datum
    tafel_counters = {}
    exported = 0
    
    for tafel in tafeln:
        ga = tafel['ga']
        date = tafel['date'] or 'unknown'
        
        # Zähle Tafeln pro GA+Datum
        counter_key = f"{ga}_{date}"
        if counter_key not in tafel_counters:
            tafel_counters[counter_key] = 0
        tafel_counters[counter_key] += 1
        tafel_num = tafel_counters[counter_key]
        
        # Quell-Bild
        src_path = assets_folder / Path(tafel['img_path']).name
        
        if not src_path.exists():
            # Versuche URL-dekodiert
            src_path = assets_folder / unquote(Path(tafel['img_path']).name)
        
        if not src_path.exists():
            # Versuche alternative Endungen (.jpeg <-> .png)
            alt_path = src_path.with_suffix('.png') if src_path.suffix.lower() in ['.jpeg', '.jpg'] else src_path.with_suffix('.jpeg')
            if alt_path.exists():
                src_path = alt_path
        
        if not src_path.exists():
            print(f"    FEHLER: Bild nicht gefunden: {tafel['img_path']}")
            continue
        
        # Ziel-Dateiname
        new_filename = f"GA{ga}-{date}-T{tafel_num:02d}.webp"
        ga_folder = CHALKBOARDS_DIR / f"GA{ga}"
        dest_path = ga_folder / new_filename
        
        print(f"    {src_path.name} -> {new_filename}")
        
        if not dry_run:
            # Erstelle Ordner
            ga_folder.mkdir(parents=True, exist_ok=True)
            
            # Lade, konvertiere und speichere
            img = Image.open(src_path)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(dest_path, 'WEBP', quality=90, method=6)
        
        exported += 1
    
    return exported


def delete_existing_ga_k_exports(ga_k_num: int, dry_run: bool = False) -> int:
    """
    Löscht vorhandene Exporte aus einem bestimmten GA K Band.
    
    GA K 6 enthält GA 202, 203, 204
    """
    # Mapping GA K -> GA Nummern (aus den MD-Dateien)
    ga_k_to_ga = {
        1: ['073A', '074', '076', '084'],
        2: ['191', '194'],
        4: ['199', '200'],
        5: ['201'],
        6: ['202', '203', '204'],
        7: ['205', '206'],
        8: ['207', '208', '209'],
        9: ['210', '211', '212'],
        10: ['213', '214', '215'],
        11: ['216', '218', '219', '220'],
        12: ['221', '222', '223', '224', '225'],
        13: ['227', '228', '229', '230'],
        14: ['232', '233'],
        15: ['233A', '234', '243'],
        16: ['235', '236', '237', '238', '240'],
        17: ['257', '258', '260', '260A'],
        18: ['271', '276', '283', '288', '289', '290', '291'],
        19: ['278', '279', '315'],
        20: ['281', '282'],
        21: ['296', '303', '304', '306', '311'],
        22: ['312', '313', '314', '315'],
        23: ['316', '317', '318'],
        24: ['322', '326', '327', '339', '340'],
        25: ['347', '348'],
        26: ['349', '350'],
        27: ['351', '352'],
        28: ['353', '354'],
        29: ['342', '343', '344', '346'],
        30: ['255B', '324A', '336', '337B', '340', '200', '210', '304'],
    }
    
    ga_numbers = ga_k_to_ga.get(ga_k_num, [])
    
    if not ga_numbers:
        print(f"  Keine GA-Nummern bekannt für GA K {ga_k_num}")
        return 0
    
    deleted = 0
    
    for ga in ga_numbers:
        ga_folder = CHALKBOARDS_DIR / f"GA{ga}"
        if ga_folder.exists():
            files = list(ga_folder.glob("*.webp"))
            print(f"  Lösche {len(files)} Dateien aus GA{ga}/")
            
            if not dry_run:
                for f in files:
                    f.unlink()
            
            deleted += len(files)
    
    return deleted


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Exportiere Tafeln aus MD-Datei')
    parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nichts ändern')
    parser.add_argument('--ga-k', type=int, required=True, help='GA K Band (z.B. 6)')
    parser.add_argument('--no-delete', action='store_true', help='Vorhandene Dateien nicht löschen')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Exportiere Tafeln aus GA K 58_{args.ga_k}")
    print("=" * 60)
    
    if args.dry_run:
        print("DRY RUN - keine Änderungen\n")
    
    # Lösche vorhandene Exporte
    if not args.no_delete:
        print("\nLösche vorhandene Exporte...")
        deleted = delete_existing_ga_k_exports(args.ga_k, args.dry_run)
        print(f"  {deleted} Dateien gelöscht")
    
    # Exportiere neue
    print(f"\nExportiere aus GA K 58_{args.ga_k}...")
    exported = process_ga_k(args.ga_k, args.dry_run)
    
    print(f"\n{'='*60}")
    print(f"FERTIG: {exported} Tafeln exportiert")
    
    if args.dry_run:
        print("(DRY RUN - keine Änderungen)")


if __name__ == '__main__':
    main()

