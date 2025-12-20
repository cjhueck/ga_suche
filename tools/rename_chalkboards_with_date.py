#!/usr/bin/env python3
"""
Skript zum Umbenennen der Wandtafelzeichnungen mit Datum im Dateinamen.

Das Skript:
1. Liest die MD-Datei eines GA K 58_* Bandes
2. Extrahiert die Zuordnung: Bild (img-X) → GA → Datum → Tafel-Nr
3. Benennt die Bilder um zu: GA194-1919-11-22-T03.webp
4. Konvertiert JPEG zu WebP und dreht um 90°
5. Kopiert in den assets-Ordner des jeweiligen GA-Bandes
6. Fügt WZ-Links am Ende der korrekten Vorträge ein

Verwendung:
    python rename_chalkboards_with_date.py 2
    python rename_chalkboards_with_date.py --dry-run 2
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image

# Basispfad zum Steiner_GA Ordner
BASE_PATH = Path(__file__).parent.parent / "Steiner_GA"

# Deutsche Monatsnamen
MONTH_MAP = {
    'januar': 1, 'februar': 2, 'märz': 3, 'april': 4,
    'mai': 5, 'juni': 6, 'juli': 7, 'august': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'dezember': 12
}


def find_ga_k58_folder(band_nummer: int) -> Path | None:
    """Findet den GA K 58_X Ordner."""
    pattern = f"GA K 58_{band_nummer} - Wandtafelzeichnungen*"
    folders = list(BASE_PATH.glob(pattern))
    
    # Bevorzuge Ordner ohne "(1)" Suffix
    for folder in folders:
        if "(1)" not in folder.name:
            return folder
    
    return folders[0] if folders else None


def find_ga_folder(ga_number: str) -> Path | None:
    """Findet den GA-Ordner für eine GA-Nummer."""
    if not ga_number.startswith("GA"):
        ga_number = f"GA{ga_number}"
    
    pattern = f"{ga_number}-*"
    folders = list(BASE_PATH.glob(pattern))
    
    return folders[0] if folders else None


def parse_german_date(date_str: str) -> tuple[int, int, int] | None:
    """
    Parst ein deutsches Datum und gibt (Jahr, Monat, Tag) zurück.
    Beispiel: "3. Oktober 1919" -> (1919, 10, 3)
    """
    pattern = r'(\d{1,2})\.\s*(\w+)\s+(\d{4})'
    match = re.search(pattern, date_str, re.IGNORECASE)
    if match:
        tag = int(match.group(1))
        monat_name = match.group(2).lower()
        jahr = int(match.group(3))
        
        monat = MONTH_MAP.get(monat_name)
        if monat:
            return (jahr, monat, tag)
    return None


def format_date_for_filename(date_tuple: tuple[int, int, int]) -> str:
    """Formatiert (Jahr, Monat, Tag) zu 'YYYY-MM-DD'."""
    jahr, monat, tag = date_tuple
    return f"{jahr}-{monat:02d}-{tag:02d}"


def parse_ga_k58_md_with_dates(md_file: Path) -> list[dict]:
    """
    Parst die MD-Datei und extrahiert Zuordnungen mit Datum.
    
    Returns: Liste von {
        'img_number': int,
        'ga_number': str,
        'tafel_nr': str,
        'date_str': str (original),
        'date_tuple': (Jahr, Monat, Tag),
        'date_formatted': 'YYYY-MM-DD'
    }
    """
    content = md_file.read_text(encoding='utf-8')
    mappings = []
    lines = content.split('\n')
    
    # Pattern für "GA XXX TAFEL Y" mit Datum
    tafel_pattern = r'GA\s*(\d+[a-zA-Z]?)\s+TAFELN?\s+(\d+[a-zA-Z]?)'
    date_pattern = r'(?:DORNACH|STUTTGART|BERLIN|KÖLN|MÜNCHEN)[,\s]+(\d{1,2})\.\s*(\w+)\s+(\d{4})'
    img_pattern = r'!\[img-(\d+)\.jpe?g\]'
    
    for i, line in enumerate(lines):
        tafel_match = re.search(tafel_pattern, line, re.IGNORECASE)
        if tafel_match:
            ga_num = f"GA{tafel_match.group(1)}"
            tafel_nr = tafel_match.group(2).upper()
            
            # Suche Datum in den umgebenden Zeilen
            search_range = lines[max(0, i-3):i+8]
            search_text = '\n'.join(search_range)
            date_match = re.search(date_pattern, search_text, re.IGNORECASE)
            
            if not date_match:
                continue
            
            date_str = f"{date_match.group(1)}. {date_match.group(2).capitalize()} {date_match.group(3)}"
            date_tuple = parse_german_date(date_str)
            
            if not date_tuple:
                continue
            
            # Suche das Bild (vorwärts und rückwärts)
            img_number = None
            
            for j in range(i, min(i + 15, len(lines))):
                img_match = re.search(img_pattern, lines[j])
                if img_match:
                    img_number = int(img_match.group(1))
                    break
            
            if img_number is None:
                for j in range(i - 1, max(0, i - 10), -1):
                    img_match = re.search(img_pattern, lines[j])
                    if img_match:
                        img_number = int(img_match.group(1))
                        break
            
            if img_number is None:
                continue
            
            # Prüfe ob diese Zuordnung schon existiert
            exists = any(
                m['ga_number'] == ga_num and m['tafel_nr'] == tafel_nr 
                for m in mappings
            )
            
            if not exists:
                mappings.append({
                    'img_number': img_number,
                    'ga_number': ga_num,
                    'tafel_nr': tafel_nr,
                    'date_str': date_str,
                    'date_tuple': date_tuple,
                    'date_formatted': format_date_for_filename(date_tuple)
                })
    
    # Sortiere nach GA und Datum
    mappings.sort(key=lambda m: (m['ga_number'], m['date_tuple'], m['tafel_nr']))
    
    return mappings


def find_lecture_by_date(ga_folder: Path, date_tuple: tuple[int, int, int]) -> Path | None:
    """Findet die Vortrags-MD-Datei anhand des Datums."""
    jahr, monat, tag = date_tuple
    
    # Deutsche Monatsnamen für Suche
    monat_namen = {
        1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
        5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
    }
    
    monat_name = monat_namen.get(monat, '')
    date_patterns = [
        f"{tag}. {monat_name} {jahr}",
        f"{tag}. {monat_name.lower()} {jahr}",
    ]
    
    for md_file in ga_folder.glob("*.md"):
        # Überspringe Übersichtsdateien (die ohne Nummer am Anfang)
        if not re.search(r'\(\d+\.\)', md_file.name):
            continue
        
        for pattern in date_patterns:
            if pattern in md_file.name:
                return md_file
    
    return None


def process_image(source_file: Path, target_file: Path, rotate: bool = True) -> bool:
    """Verarbeitet ein Bild: Optional drehen und als WebP speichern."""
    try:
        with Image.open(source_file) as img:
            if rotate:
                img = img.rotate(90, expand=True)
            img.save(target_file, 'WEBP', quality=90)
            return True
    except Exception as e:
        print(f"  [FEHLER] bei {source_file.name}: {e}")
        return False


def remove_old_chalkboard_section(md_file: Path) -> bool:
    """Entfernt existierenden Wandtafelzeichnungen-Abschnitt."""
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Finde und entferne den Wandtafelzeichnungen-Abschnitt
        pattern = r'\n---\n\n## Wandtafelzeichnungen\n.*$'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        if new_content != content:
            md_file.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"  [FEHLER] beim Entfernen: {e}")
        return False


def add_chalkboard_to_md(md_file: Path, image_filename: str, tafel_nr: str, date_formatted: str) -> bool:
    """Fügt Wandtafelzeichnungen-Abschnitt am Ende der MD-Datei ein."""
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Block-ID aus Dateiname extrahieren
        block_id = image_filename.replace('.webp', '').replace('-', '').lower()
        
        if "## Wandtafelzeichnungen" in content:
            if image_filename in content:
                return True  # Bereits vorhanden
            new_content = content.rstrip() + f"\n\n![Tafel {tafel_nr}](assets/{image_filename}) ^{block_id}"
        else:
            new_content = content.rstrip() + f"\n\n---\n\n## Wandtafelzeichnungen\n\n![Tafel {tafel_nr}](assets/{image_filename}) ^{block_id}"
        
        md_file.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  [FEHLER] beim Aktualisieren: {e}")
        return False


def process_ga_k58_band(band_nummer: int, dry_run: bool = False, no_rotate: bool = False, clean: bool = False) -> dict:
    """Verarbeitet einen GA K 58_X Band mit Datum im Dateinamen."""
    stats = {
        'mappings_found': 0,
        'images_processed': 0,
        'md_files_updated': 0,
        'errors': []
    }
    
    print(f"\n{'='*60}")
    print(f"Verarbeite GA K 58_{band_nummer} (mit Datum im Dateinamen)")
    print(f"{'='*60}")
    
    k58_folder = find_ga_k58_folder(band_nummer)
    if not k58_folder:
        stats['errors'].append(f"GA K 58_{band_nummer} Ordner nicht gefunden")
        return stats
    
    print(f"Ordner: {k58_folder.name}")
    
    md_files = list(k58_folder.glob("*.md"))
    if not md_files:
        stats['errors'].append("Keine MD-Datei gefunden")
        return stats
    
    md_file = md_files[0]
    print(f"MD-Datei: {md_file.name}")
    
    # Parse MD-Datei
    mappings = parse_ga_k58_md_with_dates(md_file)
    stats['mappings_found'] = len(mappings)
    print(f"\nGefundene Zuordnungen: {len(mappings)}")
    
    if not mappings:
        stats['errors'].append("Keine Zuordnungen gefunden")
        return stats
    
    # Zeige Zuordnungen
    current_ga = None
    for m in mappings:
        if m['ga_number'] != current_ga:
            current_ga = m['ga_number']
            print(f"\n  {current_ga}:")
        print(f"    Tafel {m['tafel_nr']}: {m['date_str']} (img-{m['img_number']}) -> {m['date_formatted']}")
    
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen durchgeführt")
        return stats
    
    k58_assets = k58_folder / "assets"
    if not k58_assets.exists():
        stats['errors'].append("Assets-Ordner nicht gefunden")
        return stats
    
    print(f"\n{'='*60}")
    print("Verarbeite Bilder...")
    print(f"{'='*60}")
    
    updated_md_files = set()
    
    for mapping in mappings:
        ga_number = mapping['ga_number']
        tafel_nr = mapping['tafel_nr']
        date_formatted = mapping['date_formatted']
        img_number = mapping['img_number']
        
        print(f"\n{ga_number} Tafel {tafel_nr} ({mapping['date_str']}):")
        
        # Finde Quellbild
        source_patterns = [f"*_img-{img_number}.jpeg", f"*_img-{img_number}.jpg", f"*_img-{img_number}.png"]
        source_file = None
        for pattern in source_patterns:
            matches = list(k58_assets.glob(pattern))
            if matches:
                source_file = matches[0]
                break
        
        if not source_file:
            stats['errors'].append(f"Quellbild nicht gefunden: img-{img_number}")
            print(f"  [FEHLER] Quellbild nicht gefunden")
            continue
        
        print(f"  Quelle: {source_file.name}")
        
        # Finde Ziel-GA-Ordner
        ga_folder = find_ga_folder(ga_number)
        if not ga_folder:
            stats['errors'].append(f"GA-Ordner nicht gefunden: {ga_number}")
            print(f"  [FEHLER] GA-Ordner nicht gefunden")
            continue
        
        # Erstelle assets-Ordner
        target_assets = ga_folder / "assets"
        target_assets.mkdir(exist_ok=True)
        
        # Neuer Dateiname mit Datum: GA194-1919-11-22-T03.webp
        tafel_nr_normalized = tafel_nr.zfill(2) if tafel_nr.isdigit() else tafel_nr
        target_filename = f"{ga_number}-{date_formatted}-T{tafel_nr_normalized}.webp"
        target_file = target_assets / target_filename
        
        # Verarbeite Bild
        if target_file.exists() and not clean:
            print(f"  [SKIP] Ziel existiert bereits: {target_filename}")
        else:
            if process_image(source_file, target_file, rotate=not no_rotate):
                stats['images_processed'] += 1
                print(f"  [OK] Bild erstellt: {target_filename}")
            else:
                continue
        
        # Finde Vortrags-MD nach Datum
        lecture_md = find_lecture_by_date(ga_folder, mapping['date_tuple'])
        if not lecture_md:
            stats['errors'].append(f"Vortrags-MD nicht gefunden: {ga_number}, {mapping['date_str']}")
            print(f"  [FEHLER] Vortrags-MD nicht gefunden")
            continue
        
        print(f"  Vortrag: {lecture_md.name}")
        
        # Entferne alte WZ-Abschnitte wenn clean
        if clean and lecture_md not in updated_md_files:
            remove_old_chalkboard_section(lecture_md)
        
        # Füge WZ-Link hinzu
        if add_chalkboard_to_md(lecture_md, target_filename, tafel_nr, date_formatted):
            updated_md_files.add(lecture_md)
            print(f"  [OK] MD aktualisiert")
    
    stats['md_files_updated'] = len(updated_md_files)
    
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Zuordnungen gefunden: {stats['mappings_found']}")
    print(f"Bilder verarbeitet: {stats['images_processed']}")
    print(f"MD-Dateien aktualisiert: {stats['md_files_updated']}")
    
    if stats['errors']:
        print(f"\nFehler ({len(stats['errors'])}):")
        for error in stats['errors']:
            print(f"  - {error}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Benennt Wandtafelzeichnungen mit Datum im Dateinamen um"
    )
    parser.add_argument('band', nargs='?', help="Band-Nummer (z.B. 2)")
    parser.add_argument('--dry-run', action='store_true', help="Nur Vorschau")
    parser.add_argument('--no-rotate', action='store_true', help="Bilder nicht drehen")
    parser.add_argument('--clean', action='store_true', help="Alte WZ-Abschnitte entfernen")
    parser.add_argument('--list', action='store_true', help="Zeige verfügbare Bände")
    
    args = parser.parse_args()
    
    if args.list:
        print("Verfügbare GA K 58_* Bände:")
        for folder in sorted(BASE_PATH.glob("GA K 58_*")):
            print(f"  - {folder.name}")
        return
    
    if not args.band:
        parser.print_help()
        return
    
    try:
        band_nr = int(args.band)
        process_ga_k58_band(band_nr, args.dry_run, args.no_rotate, args.clean)
    except ValueError:
        print(f"Ungültige Band-Nummer: {args.band}")


if __name__ == "__main__":
    main()

