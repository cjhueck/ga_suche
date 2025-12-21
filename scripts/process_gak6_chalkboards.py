#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verarbeitet Wandtafelzeichnungen aus GA K 58_6:
1. Liest die Markdown-Datei, um GA, Tafel und Datum zu extrahieren
2. Konvertiert PNG zu WebP
3. Benennt nach Format GA{nr}-{YYYY-MM-DD}-T{tafel}.webp
4. Verschiebt in Steiner_GA/chalkboards/GA{nr}/

Dann wird generate_chalkboards_json.py aufgerufen.
"""

import re
import os
import sys
from pathlib import Path
from datetime import datetime

# Pillow für Bildkonvertierung
try:
    from PIL import Image
except ImportError:
    print("FEHLER: Pillow nicht installiert. Bitte installieren mit: pip install Pillow")
    sys.exit(1)

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
GAK6_DIR = STEINER_GA_DIR / "GA K 58_6 - Wandtafelzeichnungen zum Vortragswerk 6 (U1-U4)"
CHALKBOARDS_DIR = STEINER_GA_DIR / "chalkboards"

# Monats-Mapping (Deutsch)
MONTHS_DE = {
    'januar': 1, 'februar': 2, 'märz': 3, 'april': 4,
    'mai': 5, 'juni': 6, 'juli': 7, 'august': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'dezember': 12
}


def parse_date(date_str: str) -> str | None:
    """
    Parst deutsches Datum wie '26. NOVEMBER 1920' zu '1920-11-26'
    """
    date_str = date_str.strip().lower()
    
    # Pattern: "26. november 1920"
    match = re.match(r'(\d{1,2})\.?\s*(\w+)\s+(\d{4})', date_str)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        
        month = MONTHS_DE.get(month_name)
        if month:
            return f"{year}-{month:02d}-{day:02d}"
    
    return None


def extract_tafel_info(md_content: str) -> list:
    """
    Extrahiert alle Tafel-Informationen aus der Markdown-Datei.
    Gibt Liste von Dicts zurück: [{'ga': '202', 'tafel': 1, 'date': '1920-11-26', 'image': 'filename.png'}, ...]
    """
    tafeln = []
    
    # Suche nach Pattern: GA XXX TAFEL Y gefolgt von ORT, DATUM und dann Bild
    # Pattern für GA-Nummer und Tafel
    ga_tafel_pattern = re.compile(r'GA\s*(\d+[a-zA-Z]?)\s+TAFEL\s+(\d+)', re.IGNORECASE)
    
    # Pattern für Datum (DORNACH, 26. NOVEMBER 1920)
    date_pattern = re.compile(r'(?:DORNACH|BERN|BASEL|STUTTGART|DEN HAAG|MÜNCHEN|WIEN),?\s*(\d{1,2})\.?\s*(\w+)\s+(\d{4})', re.IGNORECASE)
    
    # Pattern für Bilder
    image_pattern = re.compile(r'!\[\[([^\]]+\.png)\]\]', re.IGNORECASE)
    
    lines = md_content.split('\n')
    
    current_ga = None
    current_tafel = None
    current_date = None
    
    for i, line in enumerate(lines):
        # Suche GA und Tafel
        ga_match = ga_tafel_pattern.search(line)
        if ga_match:
            current_ga = ga_match.group(1)
            current_tafel = int(ga_match.group(2))
        
        # Suche Datum
        date_match = date_pattern.search(line)
        if date_match:
            day = int(date_match.group(1))
            month_name = date_match.group(2).lower()
            year = int(date_match.group(3))
            
            month = MONTHS_DE.get(month_name)
            if month:
                current_date = f"{year}-{month:02d}-{day:02d}"
        
        # Suche Bild
        image_match = image_pattern.search(line)
        if image_match and current_ga and current_tafel and current_date:
            image_name = image_match.group(1)
            
            # Überprüfe ob die Datei existiert (im assets Ordner oder mit "Pasted image")
            tafeln.append({
                'ga': current_ga,
                'tafel': current_tafel,
                'date': current_date,
                'image': image_name
            })
            
            # Reset für nächste Tafel (Datum bleibt, da mehrere Tafeln pro Tag möglich)
            current_tafel = None
    
    return tafeln


def find_image_file(image_name: str, assets_dir: Path) -> Path | None:
    """
    Findet die Bilddatei im assets-Ordner.
    Sucht sowohl exakt als auch nach "Pasted image" Dateien.
    """
    # Direkter Pfad
    direct_path = assets_dir / image_name
    if direct_path.exists():
        return direct_path
    
    # Ohne Pfad-Prefix
    simple_name = Path(image_name).name
    simple_path = assets_dir / simple_name
    if simple_path.exists():
        return simple_path
    
    # Suche nach "Pasted image" Dateien
    if "Pasted image" in image_name:
        for f in assets_dir.iterdir():
            if "Pasted image" in f.name and f.suffix.lower() == '.png':
                # Prüfe ob Dateiname im image_name vorkommt
                if f.name in image_name or image_name in f.name:
                    return f
    
    return None


def convert_and_copy(src_path: Path, dest_path: Path) -> bool:
    """
    Konvertiert PNG zu WebP und speichert am Zielpfad.
    Keine Rotation (Bilder bleiben wie sie sind).
    """
    try:
        with Image.open(src_path) as img:
            # Speichern als WebP (ohne Rotation)
            img.save(dest_path, 'WEBP', quality=90)
            return True
    except Exception as e:
        print(f"  [FEHLER] {src_path.name}: {e}")
        return False


def main():
    # Fix für Windows-Konsole
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("  GA K 58_6 WANDTAFELZEICHNUNGEN VERARBEITEN")
    print("=" * 60)
    print()
    
    # Prüfe ob GAK6-Ordner existiert
    if not GAK6_DIR.exists():
        print(f"FEHLER: Ordner nicht gefunden: {GAK6_DIR}")
        sys.exit(1)
    
    # Finde Markdown-Datei
    md_files = list(GAK6_DIR.glob("*.md"))
    if not md_files:
        print("FEHLER: Keine Markdown-Datei gefunden")
        sys.exit(1)
    
    md_file = md_files[0]
    print(f"Markdown-Datei: {md_file.name}")
    
    # Lese Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extrahiere Tafel-Informationen
    tafeln = extract_tafel_info(md_content)
    print(f"Gefundene Tafeln in MD: {len(tafeln)}")
    
    if not tafeln:
        print("Keine Tafeln gefunden!")
        sys.exit(1)
    
    # Assets-Ordner
    assets_dir = GAK6_DIR / "assets"
    if not assets_dir.exists():
        print(f"FEHLER: Assets-Ordner nicht gefunden: {assets_dir}")
        sys.exit(1)
    
    # Verarbeite jede Tafel
    print()
    print("Verarbeite Tafeln...")
    print("-" * 60)
    
    processed = 0
    errors = 0
    
    for tafel in tafeln:
        ga = tafel['ga']
        tafel_nr = tafel['tafel']
        date = tafel['date']
        image_name = tafel['image']
        
        # Finde Quelldatei
        src_path = find_image_file(image_name, assets_dir)
        if not src_path:
            print(f"  [NICHT GEFUNDEN] {image_name}")
            errors += 1
            continue
        
        # Ziel-Ordner erstellen
        ga_folder = CHALKBOARDS_DIR / f"GA{ga}"
        ga_folder.mkdir(parents=True, exist_ok=True)
        
        # Ziel-Dateiname
        dest_name = f"GA{ga}-{date}-T{tafel_nr:02d}.webp"
        dest_path = ga_folder / dest_name
        
        # Konvertieren und kopieren (ohne Rotation)
        if convert_and_copy(src_path, dest_path):
            print(f"  ✓ GA{ga} Tafel {tafel_nr} ({date}) -> {dest_name}")
            processed += 1
        else:
            errors += 1
    
    print()
    print("=" * 60)
    print(f"  ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Verarbeitet: {processed}")
    print(f"  Fehler: {errors}")
    print("=" * 60)
    
    # Regeneriere chalkboards.json
    print()
    print("Regeneriere chalkboards.json...")
    os.system(f'python "{SCRIPT_DIR / "generate_chalkboards_json.py"}"')


if __name__ == "__main__":
    main()

