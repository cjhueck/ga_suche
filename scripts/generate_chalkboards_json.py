#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generiert chalkboards.json aus den WebP-Dateien in Steiner_GA/chalkboards/

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

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHALKBOARDS_DIR = PROJECT_DIR / "Steiner_GA" / "chalkboards"
OUTPUT_FILE = PROJECT_DIR / "chalkboards.json"


def parse_filename(filename: str) -> dict | None:
    """
    Parst einen Dateinamen wie GA199-1920-08-06-T01.webp
    
    Returns:
        dict mit ga, date, tafel oder None bei Fehler
    """
    # Pattern: GA + Nummer (optional mit Suffix) + Datum + Tafel-Nummer
    # Beispiele: GA199-1920-08-06-T01.webp, GA073A-1920-03-27-T02.webp
    pattern = r'^GA(\d+[A-Z]?)-(\d{4}-\d{2}-\d{2})-T(\d+)\.webp$'
    match = re.match(pattern, filename, re.IGNORECASE)
    
    if not match:
        return None
    
    ga = match.group(1).upper()
    date = match.group(2)
    tafel = int(match.group(3))
    
    return {
        'ga': ga,
        'date': date,
        'tafel': tafel
    }


def generate_chalkboards_json():
    """Scannt alle Tafeln und generiert die JSON-Datei."""
    
    if not CHALKBOARDS_DIR.exists():
        print(f"FEHLER: Verzeichnis nicht gefunden: {CHALKBOARDS_DIR}")
        return
    
    chalkboards = []
    stats = defaultdict(int)
    
    # Scanne alle GA-Unterordner
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
            
            chalkboards.append({
                'ga': info['ga'],
                'date': info['date'],
                'tafel': info['tafel'],
                'path': rel_path,
                'filename': webp_file.name
            })
            
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
    
    if stats['errors'] > 0:
        print(f"Fehler: {stats['errors']}")
    
    # Zeige Top 10 GA-Bände
    print(f"\nTop 10 GA-Bände nach Anzahl Tafeln:")
    ga_counts = [(k, v) for k, v in stats.items() if k.startswith('GA')]
    ga_counts.sort(key=lambda x: -x[1])
    for ga, count in ga_counts[:10]:
        print(f"  {ga}: {count} Tafeln")


if __name__ == "__main__":
    generate_chalkboards_json()

