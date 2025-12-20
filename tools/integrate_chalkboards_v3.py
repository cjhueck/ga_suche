#!/usr/bin/env python3
"""
Wandtafelzeichnungen Integration v3
===================================

Verbesserte Version: Parst die klare Struktur in GA K 58 Dateien:
    GA 191 TAFEL 2
    DORNACH, 4. OKTOBER 1919
    ...
    ![img-2.jpeg]...

Verwendung:
    python integrate_chalkboards_v3.py --dry-run 2    # Nur anzeigen
    python integrate_chalkboards_v3.py 2              # Ausführen
    python integrate_chalkboards_v3.py --list         # Alle Bände auflisten
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

# PIL für Bildkonvertierung
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warnung: PIL nicht verfügbar. Bilder werden nur kopiert.")


# Deutsche Monatsnamen
GERMAN_MONTHS = {
    'januar': 1, 'februar': 2, 'märz': 3, 'maerz': 3, 'april': 4,
    'mai': 5, 'juni': 6, 'juli': 7, 'august': 8, 'september': 9,
    'oktober': 10, 'november': 11, 'dezember': 12
}


def parse_german_date(date_str: str) -> tuple:
    """Parst deutsches Datum wie '4. OKTOBER 1919' zu (1919, 10, 4)"""
    # Pattern: ORT, DD. MONAT YYYY oder DD. MONAT YYYY
    pattern = r'(\d{1,2})\.\s*(\w+)\s+(\d{4})'
    match = re.search(pattern, date_str, re.IGNORECASE)
    
    if not match:
        return None
    
    day = int(match.group(1))
    month_name = match.group(2).lower()
    year = int(match.group(3))
    
    month = GERMAN_MONTHS.get(month_name)
    if not month:
        return None
    
    return (year, month, day)


def format_date_iso(date_tuple: tuple) -> str:
    """Formatiert (1919, 10, 4) zu '1919-10-04'"""
    year, month, day = date_tuple
    return f"{year}-{month:02d}-{day:02d}"


def parse_ga_k58_md(md_file: Path) -> list[dict]:
    """
    Parst GA K 58 Markdown-Datei und extrahiert Zuordnungen.
    
    Sucht nach Pattern:
        GA XXX TAFEL Y
        ORT, DD. MONAT YYYY
        ...
        ![img-N.jpeg]...
    """
    content = md_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    mappings = []
    
    # Pattern für "GA XXX TAFEL Y"
    tafel_pattern = r'^GA\s*(\d+[a-zA-Z]?)\s+TAFELN?\s+(\d+[a-zA-Z]?)\b'
    # Pattern für Datum "ORT, DD. MONAT YYYY"
    date_pattern = r'^[A-ZÄÖÜ]+,\s+(\d{1,2})\.\s*([A-ZÄÖÜa-zäöü]+)\s+(\d{4})'
    # Pattern für Bild
    img_pattern = r'!\[img-(\d+)\.jpe?g\]'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Suche nach "GA XXX TAFEL Y"
        tafel_match = re.match(tafel_pattern, line, re.IGNORECASE)
        if tafel_match:
            ga_num = tafel_match.group(1).upper()
            tafel_nr = tafel_match.group(2).upper()
            
            # Suche Datum in den nächsten 3 Zeilen
            date_tuple = None
            date_line = None
            for j in range(i + 1, min(i + 4, len(lines))):
                date_match = re.match(date_pattern, lines[j].strip(), re.IGNORECASE)
                if date_match:
                    day = int(date_match.group(1))
                    month_name = date_match.group(2).lower()
                    year = int(date_match.group(3))
                    month = GERMAN_MONTHS.get(month_name)
                    if month:
                        date_tuple = (year, month, day)
                        date_line = lines[j].strip()
                        break
            
            if not date_tuple:
                i += 1
                continue
            
            # Suche Bild in den nächsten 20 Zeilen
            img_number = None
            for j in range(i, min(i + 25, len(lines))):
                img_match = re.search(img_pattern, lines[j])
                if img_match:
                    img_number = int(img_match.group(1))
                    break
            
            if img_number is None:
                i += 1
                continue
            
            # Prüfe auf Duplikate
            exists = any(
                m['ga_number'] == f"GA{ga_num}" and 
                m['tafel_nr'] == tafel_nr and
                m['img_number'] == img_number
                for m in mappings
            )
            
            if not exists:
                mappings.append({
                    'ga_number': f"GA{ga_num}",
                    'tafel_nr': tafel_nr,
                    'date_tuple': date_tuple,
                    'date_iso': format_date_iso(date_tuple),
                    'date_line': date_line,
                    'img_number': img_number
                })
        
        i += 1
    
    # Sortiere nach GA, Datum, Tafel
    mappings.sort(key=lambda m: (m['ga_number'], m['date_tuple'], m['tafel_nr']))
    
    return mappings


def find_ga_folder(steiner_ga_dir: Path, ga_number: str) -> Path:
    """Findet den GA-Ordner für eine GA-Nummer."""
    # Extrahiere Nummer ohne "GA" Prefix
    ga_match = re.match(r'GA(\d+[a-zA-Z]?)', ga_number, re.IGNORECASE)
    if not ga_match:
        return None
    
    ga_num = ga_match.group(1).upper()
    
    # Suche nach passendem Ordner
    for folder in steiner_ga_dir.iterdir():
        if not folder.is_dir():
            continue
        
        # Pattern: GA191-... oder GA191a-...
        folder_match = re.match(r'GA(\d+[a-zA-Z]?)-', folder.name, re.IGNORECASE)
        if folder_match and folder_match.group(1).upper() == ga_num:
            return folder
    
    return None


def find_lecture_md(ga_folder: Path, date_tuple: tuple) -> Path:
    """Findet die Vortrags-MD für ein bestimmtes Datum."""
    year, month, day = date_tuple
    
    # Monate auf Deutsch
    month_names = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }
    month_name = month_names[month]
    
    # Suche nach MD-Datei mit diesem Datum
    date_pattern = f"{day}. {month_name} {year}"
    date_pattern_alt = f"{day}\\. {month_name} {year}"
    
    for md_file in ga_folder.glob('*.md'):
        # Nur Vortrags-Dateien (mit Nummer in Klammern)
        if not re.search(r'\(\d+\.\)', md_file.name):
            continue
        
        if date_pattern in md_file.name:
            return md_file
    
    return None


def process_image(src_path: Path, dst_path: Path, rotate: bool = True) -> bool:
    """Konvertiert Bild zu WebP und optional rotiert."""
    try:
        if PIL_AVAILABLE:
            img = Image.open(src_path)
            if rotate:
                img = img.rotate(-90, expand=True)
            img.save(dst_path, 'WEBP', quality=85)
        else:
            shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        print(f"    [FEHLER] Bildverarbeitung: {e}")
        return False


def add_wz_to_md(md_file: Path, images: list[dict], dry_run: bool = True) -> bool:
    """Fügt Wandtafelzeichnungen-Abschnitt zur MD-Datei hinzu."""
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Prüfe ob bereits WZ-Abschnitt vorhanden
        if '## Wandtafelzeichnungen' in content:
            # Entferne alten Abschnitt
            content = re.sub(r'\n## Wandtafelzeichnungen\n.*', '', content, flags=re.DOTALL)
        
        # Erstelle neuen Abschnitt
        wz_lines = ['\n## Wandtafelzeichnungen\n']
        for img in images:
            filename = img['target_filename']
            block_id = f"^{img['ga_number'].lower()}t{img['tafel_nr'].lower().zfill(2)}"
            wz_lines.append(f"![Tafel {img['tafel_nr']}](assets/{filename}) {block_id}\n")
        
        new_content = content.rstrip() + '\n' + ''.join(wz_lines)
        
        if not dry_run:
            md_file.write_text(new_content, encoding='utf-8')
        
        return True
    except Exception as e:
        print(f"    [FEHLER] MD-Update: {e}")
        return False


def main():
    # Argumente parsen
    args = sys.argv[1:]
    
    dry_run = '--dry-run' in args
    list_only = '--list' in args
    
    # Band-Nummer
    band_num = None
    for arg in args:
        if arg.isdigit():
            band_num = int(arg)
            break
    
    # Pfade
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    steiner_ga_dir = project_root / 'Steiner_GA'
    
    if not steiner_ga_dir.exists():
        print(f"FEHLER: Steiner_GA nicht gefunden: {steiner_ga_dir}")
        sys.exit(1)
    
    # Liste alle GA K 58 Ordner
    gak_folders = sorted([
        f for f in steiner_ga_dir.iterdir()
        if f.is_dir() and 'GA K 58_' in f.name and not f.name.endswith('.pdf')
    ])
    
    if list_only:
        print("Verfügbare GA K 58 Bände:")
        for folder in gak_folders:
            print(f"  - {folder.name}")
        return
    
    if band_num is None:
        print("Verwendung: python integrate_chalkboards_v3.py [--dry-run] BAND_NR")
        print("            python integrate_chalkboards_v3.py --list")
        sys.exit(1)
    
    # Finde passenden Ordner
    target_folder = None
    for folder in gak_folders:
        match = re.search(r'GA K 58_(\d+)', folder.name)
        if match and int(match.group(1)) == band_num:
            # Bevorzuge Ordner ohne "(1)" Suffix
            if '(1)' not in folder.name or target_folder is None:
                target_folder = folder
    
    if not target_folder:
        print(f"FEHLER: GA K 58_{band_num} nicht gefunden")
        sys.exit(1)
    
    print("=" * 70)
    print(f"  WANDTAFELZEICHNUNGEN INTEGRATION v3")
    print("=" * 70)
    print(f"\nQuelle: {target_folder.name}")
    
    if dry_run:
        print("[DRY-RUN] Keine Änderungen werden durchgeführt\n")
    
    # Finde MD-Datei
    md_files = list(target_folder.glob('*.md'))
    if not md_files:
        print("FEHLER: Keine MD-Datei gefunden")
        sys.exit(1)
    
    md_file = md_files[0]
    print(f"MD-Datei: {md_file.name}\n")
    
    # Parse Zuordnungen
    mappings = parse_ga_k58_md(md_file)
    print(f"Gefundene Zuordnungen: {len(mappings)}\n")
    
    if not mappings:
        print("Keine Zuordnungen gefunden!")
        sys.exit(1)
    
    # Gruppiere nach GA
    by_ga = {}
    for m in mappings:
        ga = m['ga_number']
        if ga not in by_ga:
            by_ga[ga] = []
        by_ga[ga].append(m)
    
    # Zeige Zuordnungen
    for ga in sorted(by_ga.keys()):
        items = by_ga[ga]
        print(f"  {ga}: {len(items)} Tafeln")
        for item in items[:3]:
            print(f"    - Tafel {item['tafel_nr']}: {item['date_iso']} (img-{item['img_number']})")
        if len(items) > 3:
            print(f"    ... und {len(items) - 3} weitere")
    
    print()
    
    # Verarbeite jede GA
    stats = {'images': 0, 'md_files': 0, 'errors': []}
    
    for ga in sorted(by_ga.keys()):
        items = by_ga[ga]
        
        # Finde GA-Ordner
        ga_folder = find_ga_folder(steiner_ga_dir, ga)
        if not ga_folder:
            stats['errors'].append(f"{ga}: GA-Ordner nicht gefunden")
            print(f"  [FEHLER] {ga}: GA-Ordner nicht gefunden")
            continue
        
        print(f"\n{ga} -> {ga_folder.name}")
        
        # Erstelle assets-Ordner
        assets_dir = ga_folder / 'assets'
        if not dry_run:
            assets_dir.mkdir(exist_ok=True)
        
        # Gruppiere nach Datum (= Vortrag)
        by_date = {}
        for item in items:
            date_key = item['date_iso']
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(item)
        
        # Verarbeite jeden Vortrag
        for date_iso in sorted(by_date.keys()):
            date_items = by_date[date_iso]
            date_tuple = date_items[0]['date_tuple']
            
            # Finde Vortrags-MD
            lecture_md = find_lecture_md(ga_folder, date_tuple)
            if not lecture_md:
                stats['errors'].append(f"{ga} {date_iso}: Vortrags-MD nicht gefunden")
                print(f"  [FEHLER] {date_iso}: Vortrags-MD nicht gefunden")
                continue
            
            print(f"  {date_iso}: {len(date_items)} Tafel(n) -> {lecture_md.name[:50]}...")
            
            # Verarbeite Bilder
            images_for_md = []
            for item in date_items:
                # Quelldatei
                src_filename = f"img-{item['img_number']}.jpeg"
                src_path = target_folder / 'assets' / f"{target_folder.name}_img-{item['img_number']}.jpeg"
                
                # Alternative Pfade
                if not src_path.exists():
                    src_path = target_folder / 'assets' / src_filename
                if not src_path.exists():
                    alt_name = f"{target_folder.name.replace('(', '>)').replace(')', '')}_img-{item['img_number']}.jpeg"
                    src_path = target_folder / 'assets' / alt_name
                
                if not src_path.exists():
                    # Suche nach Bild mit passender Nummer
                    for f in (target_folder / 'assets').glob(f'*img-{item["img_number"]}.jpeg'):
                        src_path = f
                        break
                
                if not src_path.exists():
                    stats['errors'].append(f"{ga} Tafel {item['tafel_nr']}: Bild nicht gefunden")
                    print(f"    [FEHLER] img-{item['img_number']}.jpeg nicht gefunden")
                    continue
                
                # Zieldatei
                target_filename = f"{ga}-{date_iso}-T{item['tafel_nr'].zfill(2)}.webp"
                dst_path = assets_dir / target_filename
                
                # Kopiere/Konvertiere Bild
                if not dry_run:
                    if process_image(src_path, dst_path):
                        stats['images'] += 1
                else:
                    stats['images'] += 1
                
                item['target_filename'] = target_filename
                images_for_md.append(item)
            
            # Update MD-Datei
            if images_for_md:
                if add_wz_to_md(lecture_md, images_for_md, dry_run):
                    stats['md_files'] += 1
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"  Bilder verarbeitet: {stats['images']}")
    print(f"  MD-Dateien aktualisiert: {stats['md_files']}")
    
    if stats['errors']:
        print(f"\n  Fehler ({len(stats['errors'])}):")
        for err in stats['errors'][:10]:
            print(f"    - {err}")
        if len(stats['errors']) > 10:
            print(f"    ... und {len(stats['errors']) - 10} weitere")
    
    if dry_run:
        print("\n  [DRY-RUN] Keine Änderungen durchgeführt")
        print(f"  Zum Ausführen: python integrate_chalkboards_v3.py {band_num}")
    
    print("=" * 70)


if __name__ == '__main__':
    main()
