#!/usr/bin/env python3
"""
Erweitertes Skript zur Integration der Wandtafelzeichnungen aus GA K 58_* Bänden.

Das Skript:
1. Parst die MD-Datei eines GA K 58_* Bandes automatisch
2. Extrahiert die Zuordnungen (Tafel-Nr, GA-Nr, Datum)
3. Konvertiert JPEG zu WebP und dreht um 90°
4. Kopiert in den assets-Ordner des jeweiligen GA-Bandes
5. Fügt Bildverweise am Ende der korrekten MD-Vorträge ein

Verwendung:
    python integrate_chalkboards_v2.py GA_K_58_2
    python integrate_chalkboards_v2.py --all
    python integrate_chalkboards_v2.py --dry-run GA_K_58_2
"""

import os
import re
import sys
import argparse
from pathlib import Path
from PIL import Image

# Basispfad zum Steiner_GA Ordner
BASE_PATH = Path(__file__).parent.parent / "Steiner_GA"


def find_ga_k58_folder(band_nummer: int) -> Path | None:
    """Findet den GA K 58_X Ordner."""
    pattern = f"GA K 58_{band_nummer} - Wandtafelzeichnungen*"
    folders = list(BASE_PATH.glob(pattern))
    
    # Bevorzuge Ordner ohne "(1)" Suffix
    for folder in folders:
        if "(1)" not in folder.name:
            return folder
    
    # Falls alle "(1)" haben, nimm den ersten
    return folders[0] if folders else None


def find_ga_folder(ga_number: str) -> Path | None:
    """Findet den GA-Ordner für eine GA-Nummer."""
    # Normalisiere GA-Nummer (z.B. "191" -> "GA191")
    if not ga_number.startswith("GA"):
        ga_number = f"GA{ga_number}"
    
    # Suche nach Ordner der mit der GA-Nummer beginnt
    pattern = f"{ga_number}*"
    folders = list(BASE_PATH.glob(pattern))
    
    if folders:
        return folders[0]
    
    # Versuche mit Kleinbuchstaben (z.B. GA073a)
    pattern_lower = f"{ga_number.lower()}*"
    folders = list(BASE_PATH.glob(pattern_lower))
    
    return folders[0] if folders else None


def parse_date(date_str: str) -> tuple[int, str, int] | None:
    """
    Parst ein deutsches Datum und gibt (Tag, Monat, Jahr) zurück.
    Beispiel: "3. Oktober 1919" -> (3, "Oktober", 1919)
    """
    # Pattern für deutsches Datum
    pattern = r'(\d{1,2})\.\s*(\w+)\s+(\d{4})'
    match = re.search(pattern, date_str)
    if match:
        return (int(match.group(1)), match.group(2), int(match.group(3)))
    return None


def parse_ga_k58_md(md_file: Path) -> list[dict]:
    """
    Parst die MD-Datei eines GA K 58 Bandes und extrahiert die Zuordnungen.
    
    WICHTIG: Findet die tatsächliche img-Nummer durch Suche nach dem Bild
    das direkt nach der "GA XXX TAFEL Y" Zeile kommt.
    
    Returns: Liste von {
        'tafel_nr': str,
        'ga_number': str,
        'date': str,
        'img_number': int (tatsächliche Nummer aus Dateiname)
    }
    """
    content = md_file.read_text(encoding='utf-8')
    mappings = []
    lines = content.split('\n')
    
    # Pattern für "GA XXX TAFEL Y" mit Datum
    tafel_pattern = r'GA\s*(\d+[a-zA-Z]?)\s+TAFELN?\s+(\d+[a-zA-Z]?)'
    date_pattern = r'(?:DORNACH|STUTTGART|BERLIN|KÖLN|MÜNCHEN)[,\s]+(\d{1,2})\.\s*(\w+)\s+(\d{4})'
    img_pattern = r'!\[img-(\d+)\.jpe?g\]'
    
    # Durchsuche die Datei nach TAFEL-Definitionen
    for i, line in enumerate(lines):
        tafel_match = re.search(tafel_pattern, line, re.IGNORECASE)
        if tafel_match:
            ga_num = f"GA{tafel_match.group(1)}"
            tafel_nr = tafel_match.group(2).upper()
            
            # Suche Datum in den umgebenden Zeilen (vorher und nachher)
            search_range = lines[max(0, i-3):i+8]
            search_text = '\n'.join(search_range)
            date_match = re.search(date_pattern, search_text, re.IGNORECASE)
            
            if not date_match:
                continue
            
            date_str = f"{date_match.group(1)}. {date_match.group(2).capitalize()} {date_match.group(3)}"
            
            # Suche das Bild in den umgebenden Zeilen (vorher und nachher)
            # Manche MD-Dateien haben das Bild vor der TAFEL-Zeile, manche danach
            img_number = None
            
            # Erst vorwärts suchen (häufigster Fall)
            for j in range(i, min(i + 15, len(lines))):
                img_match = re.search(img_pattern, lines[j])
                if img_match:
                    img_number = int(img_match.group(1))
                    break
            
            # Falls nicht gefunden, rückwärts suchen
            if img_number is None:
                for j in range(i - 1, max(0, i - 10), -1):
                    img_match = re.search(img_pattern, lines[j])
                    if img_match:
                        img_number = int(img_match.group(1))
                        break
            
            if img_number is None:
                # Kein Bild gefunden, überspringe
                continue
            
            # Prüfe ob diese Zuordnung (GA + Tafel) schon existiert
            exists = any(
                m['ga_number'] == ga_num and m['tafel_nr'] == tafel_nr 
                for m in mappings
            )
            
            if not exists:
                mappings.append({
                    'tafel_nr': tafel_nr,
                    'ga_number': ga_num,
                    'date': date_str,
                    'img_number': img_number
                })
    
    # Sortiere Mappings nach GA-Nummer und Tafel-Nummer
    def sort_key(m):
        nr = m['tafel_nr']
        # Extrahiere Nummer und optionalen Buchstaben (z.B. "5A" -> (5, 'A'))
        num_match = re.match(r'(\d+)([A-Za-z]?)', nr)
        if num_match:
            num = int(num_match.group(1))
            suffix = num_match.group(2).upper() if num_match.group(2) else ''
            return (m['ga_number'], num, suffix)
        return (m['ga_number'], 0, '')
    
    mappings.sort(key=sort_key)
    
    return mappings


def find_md_file_by_date(ga_folder: Path, date_str: str) -> Path | None:
    """Findet die MD-Datei für einen Vortrag anhand des Datums."""
    parsed = parse_date(date_str)
    if not parsed:
        return None
    
    tag, monat, jahr = parsed
    
    # Verschiedene Datumsformate für die Suche
    date_patterns = [
        f"{tag}. {monat} {jahr}",
        f"{tag}. {monat.lower()} {jahr}",
        f"{tag}. {monat.capitalize()} {jahr}",
    ]
    
    for md_file in ga_folder.glob("*.md"):
        # Überspringe Übersichtsdateien
        if " - " in md_file.name and md_file.name.count("(") == 0:
            continue
        
        for pattern in date_patterns:
            if pattern in md_file.name:
                return md_file
    
    return None


def process_image(source_file: Path, target_file: Path, rotate: bool = True) -> bool:
    """
    Verarbeitet ein Bild: Optional 90° nach links drehen und als WebP speichern.
    """
    try:
        with Image.open(source_file) as img:
            if rotate:
                # 90° nach links drehen (counterclockwise)
                img = img.rotate(90, expand=True)
            # Als WebP speichern mit guter Qualität
            img.save(target_file, 'WEBP', quality=90)
            return True
    except Exception as e:
        print(f"  [FEHLER] bei {source_file.name}: {e}")
        return False


def add_chalkboard_to_md(md_file: Path, image_filename: str, tafel_nr: str) -> bool:
    """
    Fügt einen Wandtafelzeichnungen-Abschnitt am Ende der MD-Datei ein.
    """
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Erzeuge Block-ID (z.B. "ga191t01")
        ga_match = re.search(r'GA(\d+[a-zA-Z]?)', image_filename, re.IGNORECASE)
        ga_num = ga_match.group(1) if ga_match else "000"
        block_id = f"ga{ga_num.lower()}t{tafel_nr.lower().replace('a', 'a')}"
        
        # Prüfen ob bereits Wandtafelzeichnungen-Abschnitt existiert
        if "## Wandtafelzeichnungen" in content:
            # Prüfe ob dieses Bild schon existiert
            if image_filename in content:
                return True  # Bereits vorhanden
            # Füge Bild am Ende des Abschnitts hinzu
            new_content = content.rstrip() + f"\n\n![Tafel {tafel_nr}](assets/{image_filename}) ^{block_id}"
        else:
            # Ersten Abschnitt mit Überschrift hinzufügen
            new_content = content.rstrip() + f"\n\n---\n\n## Wandtafelzeichnungen\n\n![Tafel {tafel_nr}](assets/{image_filename}) ^{block_id}"
        
        md_file.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  [FEHLER] beim Aktualisieren von {md_file.name}: {e}")
        return False


def process_ga_k58_band(band_nummer: int, dry_run: bool = False, no_rotate: bool = False) -> dict:
    """
    Verarbeitet einen GA K 58_X Band.
    
    Returns: Statistik-Dictionary
    """
    stats = {
        'mappings_found': 0,
        'images_processed': 0,
        'md_files_updated': 0,
        'errors': []
    }
    
    print(f"\n{'='*60}")
    print(f"Verarbeite GA K 58_{band_nummer}")
    print(f"{'='*60}")
    
    # Finde den GA K 58_X Ordner
    k58_folder = find_ga_k58_folder(band_nummer)
    if not k58_folder:
        stats['errors'].append(f"GA K 58_{band_nummer} Ordner nicht gefunden")
        print(f"FEHLER: Ordner nicht gefunden")
        return stats
    
    print(f"Ordner: {k58_folder.name}")
    
    # Finde die MD-Datei
    md_files = list(k58_folder.glob("*.md"))
    if not md_files:
        stats['errors'].append(f"Keine MD-Datei in {k58_folder.name}")
        print(f"FEHLER: Keine MD-Datei gefunden")
        return stats
    
    md_file = md_files[0]
    print(f"MD-Datei: {md_file.name}")
    
    # Parse die MD-Datei
    mappings = parse_ga_k58_md(md_file)
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
        print(f"    Tafel {m['tafel_nr']}: {m['date']} (img-{m['img_number']})")
    
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen durchgeführt")
        return stats
    
    # Finde den Assets-Ordner des K58-Bandes
    k58_assets = k58_folder / "assets"
    if not k58_assets.exists():
        stats['errors'].append(f"Assets-Ordner nicht gefunden: {k58_assets}")
        print(f"\nFEHLER: Assets-Ordner nicht gefunden")
        return stats
    
    # Verarbeite jede Zuordnung
    print(f"\n{'='*60}")
    print("Verarbeite Bilder...")
    print(f"{'='*60}")
    
    updated_md_files = set()
    
    for mapping in mappings:
        ga_number = mapping['ga_number']
        tafel_nr = mapping['tafel_nr']
        date_str = mapping['date']
        img_number = mapping['img_number']
        
        print(f"\n{ga_number} Tafel {tafel_nr} ({date_str}):")
        
        # Finde Quellbild
        # Verschiedene Namenskonventionen probieren
        source_patterns = [
            f"*_img-{img_number}.jpeg",
            f"*_img-{img_number}.jpg",
            f"*_img-{img_number}.png",
        ]
        
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
        
        # Erstelle assets-Ordner falls nötig
        target_assets = ga_folder / "assets"
        target_assets.mkdir(exist_ok=True)
        
        # Ziel-Dateiname
        # Normalisiere Tafel-Nummer (z.B. "5a" -> "05a")
        tafel_nr_normalized = tafel_nr
        if tafel_nr[0].isdigit() and len(tafel_nr) == 1:
            tafel_nr_normalized = f"0{tafel_nr}"
        elif tafel_nr[:-1].isdigit() and len(tafel_nr) == 2 and tafel_nr[-1].isalpha():
            tafel_nr_normalized = f"0{tafel_nr}"
        
        target_filename = f"{ga_number}-T{tafel_nr_normalized}.webp"
        target_file = target_assets / target_filename
        
        # Verarbeite Bild
        if target_file.exists():
            print(f"  [SKIP] Ziel existiert bereits: {target_filename}")
        else:
            if process_image(source_file, target_file, rotate=not no_rotate):
                stats['images_processed'] += 1
                print(f"  [OK] Bild erstellt: {target_filename}")
            else:
                continue
        
        # Finde die MD-Datei des Vortrags
        lecture_md = find_md_file_by_date(ga_folder, date_str)
        if not lecture_md:
            stats['errors'].append(f"Vortrags-MD nicht gefunden: {ga_number}, {date_str}")
            print(f"  [FEHLER] Vortrags-MD nicht gefunden für {date_str}")
            continue
        
        print(f"  Vortrag: {lecture_md.name}")
        
        # Füge Bild zur MD-Datei hinzu
        if add_chalkboard_to_md(lecture_md, target_filename, tafel_nr):
            updated_md_files.add(lecture_md.name)
            print(f"  [OK] MD aktualisiert")
    
    stats['md_files_updated'] = len(updated_md_files)
    
    # Zusammenfassung
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
        description="Integriert Wandtafelzeichnungen aus GA K 58_* in GA-Vorträge"
    )
    parser.add_argument(
        'band',
        nargs='?',
        help="Band-Nummer (z.B. 2 für GA K 58_2) oder 'all' für alle"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Zeigt nur Zuordnungen, führt keine Änderungen durch"
    )
    parser.add_argument(
        '--no-rotate',
        action='store_true',
        help="Bilder nicht drehen (falls bereits korrekt orientiert)"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="Zeigt alle verfügbaren GA K 58_* Bände"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Verfügbare GA K 58_* Bände:")
        for folder in sorted(BASE_PATH.glob("GA K 58_*")):
            print(f"  - {folder.name}")
        return
    
    if not args.band:
        parser.print_help()
        return
    
    if args.band.lower() == 'all':
        # Verarbeite alle Bände (2-30, da 1 bereits gemacht wurde)
        for band_nr in range(2, 31):
            if find_ga_k58_folder(band_nr):
                process_ga_k58_band(band_nr, args.dry_run, args.no_rotate)
    else:
        try:
            band_nr = int(args.band)
            process_ga_k58_band(band_nr, args.dry_run, args.no_rotate)
        except ValueError:
            print(f"Ungültige Band-Nummer: {args.band}")
            return


if __name__ == "__main__":
    main()

