"""
Script zum Herunterladen aller gefundenen Tafelzeichnungen
Downloads all found chalkboard drawings and organizes them by GA volume
"""

import requests
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Zielverzeichnis für Downloads
TARGET_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\chalkboards")

def parse_results_file(filepath):
    """
    Parse die Ergebnisdatei und extrahiere alle URLs nach GA-Bänden sortiert
    """
    results = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        current_ga = None
        
        for line in f:
            line = line.strip()
            
            # Suche nach GA-Nummern
            ga_match = re.match(r'^GA(\d+)', line)
            if ga_match:
                current_ga = int(ga_match.group(1))
                results[current_ga] = []
                continue
            
            # Suche nach URLs
            if line.startswith('http'):
                url = line.strip()
                if current_ga:
                    results[current_ga].append(url)
    
    return results

def extract_filename_from_url(url):
    """
    Extrahiere den Dateinamen aus der URL
    """
    parsed = urlparse(url)
    filename = Path(parsed.path).name
    return filename

def download_image(url, target_path):
    """
    Lade ein Bild herunter
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"\n  ✗ Fehler beim Download: {e}")
        return False

def download_all_chalkboards(results_dict):
    """
    Lade alle Tafelzeichnungen herunter
    """
    total_ga_volumes = len(results_dict)
    total_images = sum(len(urls) for urls in results_dict.values())
    
    print(f"\nStarte Download von {total_images} Tafelzeichnungen aus {total_ga_volumes} GA-Bänden")
    print("=" * 70)
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for ga_num in sorted(results_dict.keys()):
        urls = results_dict[ga_num]
        
        if not urls:
            continue
        
        # Erstelle GA-Verzeichnis
        ga_dir = TARGET_DIR / f"GA{ga_num}"
        ga_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nGA{ga_num}: {len(urls)} Tafelzeichnung(en)")
        print("-" * 70)
        
        for i, url in enumerate(urls, 1):
            filename = extract_filename_from_url(url)
            target_path = ga_dir / filename
            
            # Überspringe bereits existierende Dateien
            if target_path.exists():
                print(f"  [{i}/{len(urls)}] {filename} - bereits vorhanden ✓")
                skipped += 1
                continue
            
            print(f"  [{i}/{len(urls)}] {filename} - lade herunter...", end='', flush=True)
            
            if download_image(url, target_path):
                print(" ✓")
                downloaded += 1
            else:
                print(" ✗")
                failed += 1
            
            # Kleine Pause, um den Server nicht zu überlasten
            time.sleep(0.2)
    
    print("\n" + "=" * 70)
    print("DOWNLOAD ABGESCHLOSSEN")
    print("=" * 70)
    print(f"\n✓ Heruntergeladen: {downloaded}")
    print(f"⊘ Übersprungen (bereits vorhanden): {skipped}")
    if failed > 0:
        print(f"✗ Fehlgeschlagen: {failed}")
    print(f"\nGesamt: {downloaded + skipped} / {total_images}")
    print(f"\nZielverzeichnis: {TARGET_DIR.absolute()}")

def main():
    print("\n" + "=" * 70)
    print("Tafelzeichnungen Download-Script")
    print("=" * 70)
    
    # Prüfe ob Ergebnisdatei existiert
    results_file = Path("fehlende_tafelzeichnungen_ga120-209.txt")
    
    if not results_file.exists():
        print(f"\n✗ Fehler: Datei '{results_file}' nicht gefunden!")
        print("Bitte führe zuerst 'find_chalkboards_efficient.py' aus.")
        sys.exit(1)
    
    print(f"\n✓ Lese Ergebnisse aus: {results_file}")
    
    # Parse die Ergebnisse
    results = parse_results_file(results_file)
    
    if not results:
        print("\n✗ Keine URLs in der Datei gefunden!")
        sys.exit(1)
    
    total_images = sum(len(urls) for urls in results.values())
    print(f"✓ {len(results)} GA-Bände mit {total_images} Tafelzeichnungen gefunden")
    
    # Prüfe Zielverzeichnis
    if not TARGET_DIR.exists():
        print(f"\n✗ Warnung: Zielverzeichnis existiert nicht: {TARGET_DIR}")
        response = input("Soll es erstellt werden? (j/n): ")
        if response.lower() != 'j':
            print("Abgebrochen.")
            sys.exit(0)
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Verzeichnis erstellt: {TARGET_DIR}")
    
    print(f"✓ Zielverzeichnis: {TARGET_DIR.absolute()}")
    
    # Starte Download
    print("\nStarte Download in 2 Sekunden...")
    time.sleep(2)
    
    download_all_chalkboards(results)
    
    print("\n" + "=" * 70)
    print("Fertig!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

