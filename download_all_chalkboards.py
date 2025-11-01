#!/usr/bin/env python3
"""
Download Chalkboard Drawings für MEHRERE GA-Bände
=================================================
Lädt Wandtafelzeichnungen für eine Liste von GA-Bänden herunter

Verwendung:
    python download_all_chalkboards.py                    # Alle bekannten GA-Bände mit Zeichnungen
    python download_all_chalkboards.py --list GA211 GA212 # Nur spezifische Bände
    python download_all_chalkboards.py --dry-run          # Nur testen
    
Dependencies:
    pip install requests
"""

import requests
import re
import os
import sys
import time

BASE_URL = 'https://rsarchive.org'

# GA-Bände von denen bekannt ist, dass sie Wandtafelzeichnungen haben
# Basierend auf Ihrer Datenbank
GA_BANDS_WITH_DRAWINGS = [
    'GA089', 'GA090a', 'GA090b', 'GA091', 'GA093', 'GA094', 'GA095', 'GA096',
    'GA097', 'GA098', 'GA100', 'GA101', 'GA102', 'GA103', 'GA104', 'GA104a',
    'GA105', 'GA108', 'GA110', 'GA111', 'GA112', 'GA114', 'GA115', 'GA117a',
    'GA118', 'GA119',
    'GA210', 'GA211', 'GA212', 'GA213', 'GA214', 'GA216', 'GA218', 'GA219',
    'GA220', 'GA221', 'GA222', 'GA223',
    'GA291', 'GA291a', 'GA292', 'GA293', 'GA294', 'GA295', 'GA296', 'GA299',
    'GA300a', 'GA300b', 'GA300c', 'GA301', 'GA302', 'GA303', 'GA304', 'GA304a',
    'GA305', 'GA306', 'GA307', 'GA309', 'GA310', 'GA311'
]

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
    "{base}/images/GA{ga_num}/{ga_num}-T{num:02d}.webp",
]

def download_webp(url, output_path):
    """Lädt eine WebP-Datei herunter"""
    try:
        response = requests.get(url, timeout=30, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:  # Mind. 1KB
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True, len(response.content)
        return False, 0
    except Exception:
        return False, 0

def process_ga_band(ga_number, max_images=50, dry_run=False):
    """
    Verarbeitet einen einzelnen GA-Band
    """
    ga_num = re.sub(r'^GA', '', ga_number, flags=re.IGNORECASE)
    
    print(f"\n{'='*70}")
    print(f"{ga_number.upper()}")
    print(f"{'='*70}")
    
    output_dir = os.path.join('downloads', 'chalkboards', ga_number.upper())
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    found = 0
    downloaded = 0
    skipped = 0
    total_size = 0
    
    # Versuche Nummern 1 bis max_images
    for num in range(1, max_images + 1):
        filename = f"{ga_num}-T{num:02d}.webp"  # MIT T-Präfix!
        output_path = os.path.join(output_dir, filename)
        
        # Überspringe wenn existiert
        if not dry_run and os.path.exists(output_path):
            skipped += 1
            continue
        
        # Versuche alle URL-Patterns
        for pattern in URL_PATTERNS:
            url = pattern.format(base=BASE_URL, ga_num=ga_num, num=num)
            
            try:
                head = requests.head(url, timeout=5, allow_redirects=True)
                if head.status_code == 200:
                    found += 1
                    
                    if dry_run:
                        print(f"  ✓ Gefunden: {filename}")
                    else:
                        success, size = download_webp(url, output_path)
                        if success:
                            downloaded += 1
                            total_size += size
                            print(f"  ✓ {filename} ({size/1024:.1f} KB)")
                            time.sleep(0.3)  # Höflich
                    
                    break  # Nächste Nummer
            except:
                continue
    
    # Ergebnis für diesen GA-Band
    if found > 0:
        print(f"\n  → Gefunden: {found} Zeichnungen")
        if not dry_run:
            print(f"  → Heruntergeladen: {downloaded}")
            print(f"  → Übersprungen: {skipped}")
            print(f"  → Gesamtgröße: {total_size/1024/1024:.2f} MB")
            print(f"  → Ordner: {output_dir}")
    else:
        print(f"  - Keine Wandtafelzeichnungen gefunden")
    
    return found, downloaded, skipped

def main():
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)
    
    dry_run = '--dry-run' in args
    
    # Parse GA-Bände
    ga_list = []
    if '--list' in args:
        idx = args.index('--list')
        # Sammle alle GA-Bände nach --list
        for i in range(idx + 1, len(args)):
            if args[i].startswith('--'):
                break
            if args[i].startswith('GA') or args[i].startswith('ga'):
                ga_list.append(args[i].upper())
    else:
        # Verwende Standard-Liste
        ga_list = GA_BANDS_WITH_DRAWINGS
    
    if not ga_list:
        print("\nFEHLER: Keine GA-Bände angegeben!")
        print("\nBeispiele:")
        print("  python download_all_chalkboards.py --list GA211 GA212 GA213")
        print("  python download_all_chalkboards.py  # Alle bekannten Bände\n")
        sys.exit(1)
    
    # Prüfe Dependencies
    try:
        import requests
    except ImportError:
        print("\nFEHLER: 'requests' nicht installiert")
        print("Installieren Sie: pip install requests\n")
        sys.exit(1)
    
    print("=" * 70)
    print("RSARCHIVE.ORG - WANDTAFELZEICHNUNGEN BATCH-DOWNLOAD")
    print("=" * 70)
    print(f"Modus: {'DRY-RUN (nur testen)' if dry_run else 'DOWNLOAD'}")
    print(f"GA-Bände: {len(ga_list)}")
    print(f"Max. Bilder pro Band: 50")
    print("=" * 70)
    
    # Statistik
    total_found = 0
    total_downloaded = 0
    total_skipped = 0
    bands_with_images = 0
    
    # Verarbeite jeden GA-Band
    for ga in ga_list:
        found, downloaded, skipped = process_ga_band(ga, max_images=50, dry_run=dry_run)
        
        total_found += found
        total_downloaded += downloaded
        total_skipped += skipped
        
        if found > 0:
            bands_with_images += 1
    
    # Finale Statistik
    print(f"\n{'='*70}")
    print("GESAMT-STATISTIK")
    print(f"{'='*70}")
    print(f"  GA-Bände verarbeitet: {len(ga_list)}")
    print(f"  GA-Bände mit Zeichnungen: {bands_with_images}")
    print(f"  Zeichnungen gefunden: {total_found}")
    
    if not dry_run:
        print(f"  Heruntergeladen: {total_downloaded}")
        print(f"  Übersprungen (existieren bereits): {total_skipped}")
        print(f"\n  Alle Downloads in: downloads/chalkboards/")
        print(f"\nNächste Schritte:")
        print(f"  1. Prüfen: downloads/chalkboards/")
        print(f"  2. Kopieren nach: Steiner_GA/GA.../assets/")
        print(f"  3. Integrieren mit: python export_master.py")
    else:
        print(f"\n  Führen Sie ohne --dry-run aus, um zu downloaden")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

