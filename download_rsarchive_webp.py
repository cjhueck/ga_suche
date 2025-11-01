#!/usr/bin/env python3
"""
Download WebP Chalkboard Drawings from rsarchive.org
=====================================================
Lädt Wandtafelzeichnungen im Format XXX-YY.webp herunter

Verwendung:
    python download_rsarchive_webp.py GA211 --range 1-10
    python download_rsarchive_webp.py GA211 --dry-run
    
Dependencies:
    pip install requests
"""

import requests
import re
import os
import sys
import time

BASE_URL = 'https://rsarchive.org'

# Bekannte URL-Patterns für WebP-Bilder auf rsarchive.org
# Basierend auf https://rsarchive.org/Lectures/GA211/German/images/211-T01.webp
URL_PATTERNS = [
    # HAUPTPATTERN: German/images mit T-Präfix (Tafelzeichnungen)
    "{base}/Lectures/GA{ga_num}/German/images/{ga_num}-T{num:02d}.webp",
    
    # Alternative: English/images mit T-Präfix
    "{base}/Lectures/GA{ga_num}/English/images/{ga_num}-T{num:02d}.webp",
    
    # Fallback ohne T-Präfix
    "{base}/Lectures/GA{ga_num}/German/images/{ga_num}-{num:02d}.webp",
    "{base}/Lectures/GA{ga_num}/English/images/{ga_num}-{num:02d}.webp",
    
    # Weitere Alternativen
    "{base}/Lectures/GA{ga_num}/images/{ga_num}-T{num:02d}.webp",
    "{base}/Lectures/GA{ga_num}/{ga_num}-T{num:02d}.webp",
    "{base}/images/GA{ga_num}/{ga_num}-T{num:02d}.webp",
]

def download_webp(url, output_path):
    """Lädt eine WebP-Datei herunter"""
    try:
        response = requests.get(url, timeout=30, allow_redirects=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        return False

def find_and_download_chalkboards(ga_number, start=1, end=30, dry_run=False):
    """
    Findet und lädt Wandtafelzeichnungen für einen GA-Band
    """
    # Extrahiere GA-Nummer (z.B. GA211 → 211)
    ga_num = re.sub(r'^GA', '', ga_number, flags=re.IGNORECASE)
    
    print("=" * 70)
    print(f"RSARCHIVE.ORG - Wandtafelzeichnungen Download")
    print("=" * 70)
    print(f"GA-Band: {ga_number.upper()}")
    print(f"Bereich: {ga_num}-T{start:02d}.webp bis {ga_num}-T{end:02d}.webp")
    print(f"Modus: {'DRY-RUN (nur testen)' if dry_run else 'DOWNLOAD'}")
    print("=" * 70 + "\n")
    
    # Output-Ordner
    output_dir = os.path.join('downloads', 'chalkboards', ga_number.upper())
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output-Ordner: {output_dir}\n")
    
    found_urls = {}  # {num: url}
    downloaded = 0
    skipped = 0
    not_found = 0
    
    # Für jede Nummer
    for num in range(start, end + 1):
        filename = f"{ga_num}-T{num:02d}.webp"  # MIT T-Präfix!
        output_path = os.path.join(output_dir, filename) if not dry_run else None
        
        # Überspringe wenn bereits existiert
        if not dry_run and os.path.exists(output_path):
            print(f"  ⊘ {filename} (existiert bereits)")
            skipped += 1
            continue
        
        # Versuche alle URL-Patterns
        found = False
        for pattern_idx, pattern in enumerate(URL_PATTERNS):
            url = pattern.format(
                base=BASE_URL,
                ga_num=ga_num,
                num=num
            )
            
            try:
                # GET-Request statt HEAD (zuverlässiger)
                response = requests.get(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200 and len(response.content) > 1000:  # Mind. 1KB
                    print(f"  ✓ {filename} - gefunden (Pattern {pattern_idx + 1}): {url}")
                    found_urls[num] = url
                    
                    if not dry_run:
                        # Speichere direkt (haben schon die Daten)
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        downloaded += 1
                        print(f"    → Gespeichert ({len(response.content)/1024:.1f} KB)")
                        time.sleep(0.5)  # Höfliche Pause
                    
                    found = True
                    break  # Gefunden, nächste Nummer
                    
            except Exception as e:
                # Nur bei erstem Pattern loggen (sonst zu viel Output)
                if pattern_idx == 0 and num <= 3:
                    print(f"  - {filename}: Versuche verschiedene Patterns...")
                continue  # Nächstes Pattern versuchen
        
        if not found:
            not_found += 1
    
    # Ergebnisse
    print(f"\n{'='*70}")
    print(f"FERTIG!")
    print(f"{'='*70}")
    
    if dry_run:
        print(f"  Gefunden: {len(found_urls)} von {end - start + 1} möglichen Bildern")
        if found_urls:
            print(f"\nGefundene URLs:")
            for num, url in sorted(found_urls.items()):
                print(f"    {ga_num}-{num:02d}.webp → {url}")
            print(f"\nFühren Sie ohne --dry-run aus, um zu downloaden:")
            print(f"  python download_rsarchive_webp.py {ga_number} --range {start}-{end}")
    else:
        print(f"  Heruntergeladen: {downloaded}")
        print(f"  Übersprungen (existieren bereits): {skipped}")
        print(f"  Nicht gefunden: {not_found}")
        print(f"  Gespeichert in: {output_dir}")
        
        if downloaded > 0:
            print(f"\nNächste Schritte:")
            print(f"  1. Bilder prüfen: {output_dir}")
            print(f"  2. Nach Steiner_GA/{ga_number.upper()}/assets/ kopieren")
            print(f"  3. Export mit: python export_master.py {ga_number}")
    
    print("=" * 70 + "\n")

def parse_range(range_str):
    """Parse Bereich-String (z.B. '1-10' oder '5-15')"""
    if '-' in range_str:
        parts = range_str.split('-')
        return int(parts[0]), int(parts[1])
    return 1, 30  # Default

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args or len(args) == 0:
        print(__doc__)
        sys.exit(0)
    
    # Parse Argumente
    ga_number = None
    dry_run = '--dry-run' in args
    start, end = 1, 30
    
    for i, arg in enumerate(args):
        if arg.startswith('GA') or arg.startswith('ga'):
            ga_number = arg
        elif arg == '--range' and i + 1 < len(args):
            start, end = parse_range(args[i + 1])
    
    if not ga_number:
        print("\nFEHLER: Bitte geben Sie einen GA-Band an!")
        print("\nBeispiel: python download_rsarchive_webp.py GA211")
        print("          python download_rsarchive_webp.py GA211 --range 1-10\n")
        sys.exit(1)
    
    # Prüfe Dependencies
    try:
        import requests
    except ImportError:
        print("\nFEHLER: 'requests' nicht installiert")
        print("Installieren Sie: pip install requests\n")
        sys.exit(1)
    
    find_and_download_chalkboards(ga_number, start, end, dry_run)

