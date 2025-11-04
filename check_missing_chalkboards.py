"""
Überprüfung auf fehlende Tafelzeichnungen für beliebige GA-Bereiche
Check for missing chalkboard drawings for any GA range

Usage:
    python check_missing_chalkboards.py [start_ga] [end_ga]
    
Example:
    python check_missing_chalkboards.py 120 209
"""

import requests
import sys
import time
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Path to your chalkboards directory
CHALKBOARDS_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\chalkboards")

def check_ga_chalkboards_direct(ga_number):
    """
    Check if a GA volume has chalkboard drawings by testing direct URLs
    """
    # Common URL patterns used by rsarchive.org
    patterns = [
        f"https://rsarchive.org/Lectures/GA{ga_number}/{ga_number}-T01.webp",
        f"https://rsarchive.org/Lectures/GA{ga_number}/GA{ga_number}-T01.webp",
    ]
    
    for pattern in patterns:
        try:
            response = requests.head(pattern, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type or 'webp' in content_type:
                    return True
        except:
            pass
    
    return False

def get_existing_ga_volumes():
    """
    Get list of GA volumes that already have chalkboards downloaded
    """
    if not CHALKBOARDS_DIR.exists():
        return set()
    
    existing = set()
    for folder in CHALKBOARDS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith("GA"):
            # Extract numeric part
            ga_num = folder.name.replace("GA", "").rstrip('ABCD')
            try:
                existing.add(int(ga_num))
            except ValueError:
                pass
    
    return existing

def check_range(start_ga, end_ga):
    """
    Check a range of GA volumes for chalkboards
    """
    print(f"\n{'='*70}")
    print(f"Überprüfung: GA{start_ga} bis GA{end_ga}")
    print(f"{'='*70}\n")
    
    existing_ga = get_existing_ga_volumes()
    existing_in_range = [ga for ga in existing_ga if start_ga <= ga <= end_ga]
    
    print(f"Bereits heruntergeladen ({len(existing_in_range)} Bände):")
    if existing_in_range:
        for ga in sorted(existing_in_range):
            print(f"  ✓ GA{ga}")
    else:
        print("  (keine)")
    
    print(f"\nPrüfe fehlende Bände...\n")
    
    missing_with_chalkboards = []
    checked = 0
    
    for ga_num in range(start_ga, end_ga + 1):
        if ga_num in existing_ga:
            continue
        
        checked += 1
        print(f"  GA{ga_num:03d}... ", end='', flush=True)
        
        has_chalkboards = check_ga_chalkboards_direct(ga_num)
        
        if has_chalkboards:
            print("✓ Tafelzeichnungen gefunden!")
            missing_with_chalkboards.append(ga_num)
        else:
            print("keine")
        
        # Be nice to the server
        if checked % 10 == 0:
            time.sleep(1)
        else:
            time.sleep(0.2)
    
    print(f"\n{'='*70}")
    print("ERGEBNIS")
    print(f"{'='*70}\n")
    
    if missing_with_chalkboards:
        print(f"✓ Fehlende Bände MIT Tafelzeichnungen: {len(missing_with_chalkboards)}")
        for ga in missing_with_chalkboards:
            print(f"    GA{ga}")
            # Show first image URL
            url = f"https://rsarchive.org/Lectures/GA{ga}/{ga}-T01.webp"
            print(f"    URL: {url}")
    else:
        print("✓ Keine fehlenden Tafelzeichnungen gefunden!")
        print(f"\nAlle verfügbaren Tafelzeichnungen im Bereich GA{start_ga}-GA{end_ga}")
        print("sind bereits heruntergeladen.")
    
    return missing_with_chalkboards

def main():
    """Main function"""
    print("\nTafelzeichnungen-Checker für Rudolf Steiner GA-Bände")
    print("rsarchive.org")
    
    # Parse command line arguments
    if len(sys.argv) == 3:
        try:
            start_ga = int(sys.argv[1])
            end_ga = int(sys.argv[2])
        except ValueError:
            print("Fehler: Ungültige GA-Nummern")
            sys.exit(1)
    else:
        # Default: Check the original requested range
        start_ga = 120
        end_ga = 209
        print(f"\nStandardbereich: GA{start_ga}-GA{end_ga}")
        print("(Verwendung: python check_missing_chalkboards.py START END)\n")
    
    if start_ga > end_ga:
        print("Fehler: Start-GA muss kleiner oder gleich End-GA sein")
        sys.exit(1)
    
    results = check_range(start_ga, end_ga)
    
    print("\n")

if __name__ == "__main__":
    main()

