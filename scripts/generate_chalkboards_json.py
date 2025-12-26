#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generiert chalkboards.json aus den WebP-Dateien in Steiner_GA/chalkboards/
Konvertiert automatisch PNG-Dateien zu WebP.

Die JSON-Datei enthält für jede Tafel:
- ga: GA-Nummer (z.B. "199", "073A")
- date: Datum im ISO-Format (z.B. "1920-08-06")
- tafel: Tafel-Nummer für dieses Datum (z.B. 1, 2, 3)
- path: Relativer Pfad zur WebP-Datei
- filename: Dateiname

Verwendung:
  python scripts/generate_chalkboards_json.py
"""

import json
import re
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNUNG: PIL/Pillow nicht verfügbar. PNG-Konvertierung wird übersprungen.")
    print("Installiere mit: pip install Pillow")

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHALKBOARDS_DIR = PROJECT_DIR / "chalkboards"
OUTPUT_FILE = PROJECT_DIR / "chalkboards.json"


def parse_filename(filename: str) -> dict | None:
    """
    Parst einen Dateinamen wie GA199-1920-08-06-T01.webp oder GA199-1920-08-06-T01.png
    
    Unterstützt auch Suffix für mehrere Vorträge am selben Tag:
    - GA316-1924-04-24a-T01.webp  (mit Punkt vor T)
    - GA316-1924-04-24a.T01.webp  (mit Punkt vor T)
    
    Returns:
        dict mit ga, date, tafel, dateSuffix (optional) oder None bei Fehler
    """
    # Pattern: GA + Nummer (optional mit GA-Suffix wie A/B) + Datum + optionales Datums-Suffix (a/b/c) + Tafel-Nummer
    # Beispiele: 
    #   GA199-1920-08-06-T01.webp
    #   GA073A-1920-03-27-T02.webp
    #   GA316-1924-04-24a-T01.webp   (zweiter Vortrag am selben Tag)
    #   GA316-1924-04-24a.T01.webp   (alternative Schreibweise mit Punkt)
    # Unterstützt auch Varianten wie "To2" statt "T02"
    pattern = r'^GA(\d+[A-Z]?)-(\d{4}-\d{2}-\d{2})([a-z])?[.-]T([oO]?\d+)\.(webp|png)$'
    match = re.match(pattern, filename, re.IGNORECASE)
    
    if not match:
        return None
    
    ga = match.group(1).upper()
    date = match.group(2)
    date_suffix = match.group(3).lower() if match.group(3) else None  # z.B. "a" für Abendzusammenkunft
    tafel_str = match.group(4).replace('o', '0').replace('O', '0')
    tafel = int(tafel_str)
    
    result = {
        'ga': ga,
        'date': date,
        'tafel': tafel
    }
    
    # Nur hinzufügen wenn vorhanden (für Abwärtskompatibilität)
    if date_suffix:
        result['dateSuffix'] = date_suffix
    
    return result


def convert_png_to_webp(png_path: Path) -> Path | None:
    """
    Konvertiert eine PNG-Datei zu WebP.
    
    Args:
        png_path: Pfad zur PNG-Datei
        
    Returns:
        Pfad zur neuen WebP-Datei oder None bei Fehler
    """
    if not PIL_AVAILABLE:
        return None
    
    if not png_path.exists():
        print(f"  FEHLER: Datei nicht gefunden: {png_path}")
        return None
    
    try:
        # Öffne PNG-Bild
        img = Image.open(png_path)
        
        # Erstelle WebP-Dateinamen
        webp_path = png_path.with_suffix('.webp')
        
        # Konvertiere zu WebP (Qualität 90 für gute Balance zwischen Größe und Qualität)
        img.save(webp_path, 'WEBP', quality=90)
        
        print(f"  Konvertiert: {png_path.name} -> {webp_path.name}")
        
        # Lösche PNG-Datei
        png_path.unlink()
        print(f"  Gelöscht: {png_path.name}")
        
        return webp_path
        
    except Exception as e:
        print(f"  FEHLER beim Konvertieren von {png_path.name}: {e}")
        return None


def generate_chalkboards_json():
    """Scannt alle Tafeln, konvertiert PNG zu WebP und generiert die JSON-Datei."""
    
    if not CHALKBOARDS_DIR.exists():
        print(f"FEHLER: Verzeichnis nicht gefunden: {CHALKBOARDS_DIR}")
        return
    
    chalkboards = []
    stats = defaultdict(int)
    
    # Schritt 1: Konvertiere alle PNG-Dateien zu WebP
    print("=== Schritt 1: Konvertiere PNG zu WebP ===")
    png_files = list(CHALKBOARDS_DIR.rglob("*.png"))
    
    if png_files:
        print(f"Gefunden: {len(png_files)} PNG-Datei(en)")
        for png_file in sorted(png_files):
            webp_file = convert_png_to_webp(png_file)
            if webp_file:
                stats['converted'] += 1
            else:
                stats['conversion_errors'] += 1
    else:
        print("Keine PNG-Dateien gefunden.")
    
    print()
    
    # Schritt 2: Scanne alle GA-Unterordner und sammle WebP-Dateien
    print("=== Schritt 2: Generiere chalkboards.json ===")
    for ga_folder in sorted(CHALKBOARDS_DIR.iterdir()):
        if not ga_folder.is_dir():
            continue
        
        ga_name = ga_folder.name  # z.B. "GA199"
        
        # Scanne alle WebP-Dateien
        for webp_file in sorted(ga_folder.glob("*.webp")):
            info = parse_filename(webp_file.name)
            
            if not info:
                print(f"  WARNUNG: Konnte nicht parsen: {webp_file.name}")
                stats['errors'] += 1
                continue
            
            # Relativer Pfad für Web-Zugriff
            rel_path = f"chalkboards/{ga_name}/{webp_file.name}"
            
            entry = {
                'ga': info['ga'],
                'date': info['date'],
                'tafel': info['tafel'],
                'path': rel_path,
                'filename': webp_file.name
            }
            
            # Datums-Suffix für mehrere Vorträge am selben Tag (z.B. "a" für Abendzusammenkunft)
            if info.get('dateSuffix'):
                entry['dateSuffix'] = info['dateSuffix']
            
            chalkboards.append(entry)
            
            stats['total'] += 1
            stats[f"GA{info['ga']}"] += 1
    
    # Sortiere nach GA, dann Datum, dann Tafel
    chalkboards.sort(key=lambda x: (x['ga'], x['date'], x['tafel']))
    
    # Speichere JSON
    output_data = {
        'generated': str(Path(__file__).name),
        'count': len(chalkboards),
        'chalkboards': chalkboards
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Chalkboards JSON generiert ===")
    print(f"Ausgabedatei: {OUTPUT_FILE}")
    print(f"Anzahl Tafeln: {stats['total']}")
    print(f"Anzahl GA-Bände: {len([k for k in stats.keys() if k.startswith('GA')])}")
    
    if stats.get('converted', 0) > 0:
        print(f"Konvertiert: {stats['converted']} PNG-Datei(en) zu WebP")
    if stats.get('conversion_errors', 0) > 0:
        print(f"Konvertierungsfehler: {stats['conversion_errors']}")
    if stats['errors'] > 0:
        print(f"Parsing-Fehler: {stats['errors']}")
    
    # Zeige Top 10 GA-Bände
    print(f"\nTop 10 GA-Bände nach Anzahl Tafeln:")
    ga_counts = [(k, v) for k, v in stats.items() if k.startswith('GA')]
    ga_counts.sort(key=lambda x: -x[1])
    for ga, count in ga_counts[:10]:
        print(f"  {ga}: {count} Tafeln")


if __name__ == "__main__":
    generate_chalkboards_json()

