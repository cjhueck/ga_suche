#!/usr/bin/env python3
"""
Einfacher Downloader für rsarchive.org Wandtafelzeichnungen
============================================================
Verwendet das bestätigte URL-Pattern:
https://rsarchive.org/Lectures/GA{NUM}/German/images/{NUM}-T{01-99}.webp

Verwendung:
    python download_chalkboards_simple.py GA211
    python download_chalkboards_simple.py GA211 --range 1-10
    python download_chalkboards_simple.py GA089 GA211 GA212
"""

import requests
import os
import sys
import time

def download_chalkboards(ga_number, start=1, end=30):
    """Lädt Wandtafelzeichnungen für einen GA-Band"""
    
    # Extrahiere Nummer (GA211 → 211)
    ga_num = ga_number.replace('GA', '').replace('ga', '')
    
    print(f"\n{'='*70}")
    print(f"{ga_number.upper()} - Wandtafelzeichnungen")
    print(f"{'='*70}")
    
    # Output-Ordner
    output_dir = os.path.join('downloads', 'chalkboards', ga_number.upper())
    os.makedirs(output_dir, exist_ok=True)
    print(f"Speicherort: {output_dir}")
    print(f"Bereich: {ga_num}-T{start:02d}.webp bis {ga_num}-T{end:02d}.webp\n")
    
    downloaded = 0
    skipped = 0
    not_found = 0
    total_size = 0
    
    for num in range(start, end + 1):
        filename = f"{ga_num}-T{num:02d}.webp"
        filepath = os.path.join(output_dir, filename)
        
        # Überspringe wenn existiert
        if os.path.exists(filepath):
            print(f"  = {filename} (existiert bereits)")
            skipped += 1
            continue
        
        # Konstruiere URL
        url = f"https://rsarchive.org/Lectures/GA{ga_num}/German/images/{filename}"
        
        try:
            response = requests.get(url, timeout=15, allow_redirects=True)
            
            if response.status_code == 200 and len(response.content) > 1000:
                # Speichere
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                size = len(response.content)
                total_size += size
                downloaded += 1
                
                print(f"  + {filename} ({size/1024:.1f} KB)")
                time.sleep(0.3)  # Höfliche Pause
                
            else:
                # Nicht gefunden (404 oder anderer Fehler)
                not_found += 1
                if num <= 5:  # Zeige nur erste paar Fehler
                    print(f"  - {filename} (nicht verfügbar)")
                
        except Exception as e:
            not_found += 1
            if num <= 5:
                print(f"  x {filename} (Fehler: {str(e)[:40]})")
    
    # Zusammenfassung
    print(f"\n{'-'*70}")
    print(f"Heruntergeladen: {downloaded}")
    print(f"Uebersprungen: {skipped}")
    print(f"Nicht gefunden: {not_found}")
    if total_size > 0:
        print(f"Gesamtgroesse: {total_size/1024/1024:.2f} MB")
    print(f"{'-'*70}")
    
    return downloaded, skipped, not_found

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if not args or '--help' in args:
        print(__doc__)
        print("\nBeispiele:")
        print("  python download_chalkboards_simple.py GA211")
        print("  python download_chalkboards_simple.py GA211 --range 1-15")
        print("  python download_chalkboards_simple.py GA089 GA211 GA212\n")
        sys.exit(0)
    
    # Parse Range
    start, end = 1, 30
    if '--range' in args:
        idx = args.index('--range')
        if idx + 1 < len(args):
            range_str = args[idx + 1]
            if '-' in range_str:
                parts = range_str.split('-')
                start = int(parts[0])
                end = int(parts[1])
    
    # Parse GA-Nummern
    ga_numbers = [arg for arg in args if arg.startswith('GA') or arg.startswith('ga')]
    ga_numbers = [arg for arg in ga_numbers if not arg.startswith('--')]
    
    if not ga_numbers:
        print("Fehler: Keine GA-Nummer angegeben!")
        print("Beispiel: python download_chalkboards_simple.py GA211\n")
        sys.exit(1)
    
    print("="*70)
    print("RSARCHIVE.ORG - Wandtafelzeichnungen Downloader")
    print("="*70)
    print(f"GA-Baende: {', '.join(ga_numbers)}")
    print(f"Bereich pro Band: {start}-{end}")
    print("="*70)
    
    # Download für jeden GA-Band
    total_downloaded = 0
    total_skipped = 0
    total_not_found = 0
    
    for ga in ga_numbers:
        d, s, nf = download_chalkboards(ga, start, end)
        total_downloaded += d
        total_skipped += s
        total_not_found += nf
    
    # Gesamt-Statistik
    if len(ga_numbers) > 1:
        print(f"\n{'='*70}")
        print("GESAMT-STATISTIK")
        print(f"{'='*70}")
        print(f"GA-Baende: {len(ga_numbers)}")
        print(f"Heruntergeladen: {total_downloaded}")
        print(f"Uebersprungen: {total_skipped}")
        print(f"Nicht gefunden: {total_not_found}")
        print(f"{'='*70}\n")
    
    if total_downloaded > 0:
        print("\nNaechste Schritte:")
        print("  1. Pruefen: downloads/chalkboards/")
        print("  2. Kopieren nach: Steiner_GA/GA.../assets/")
        print("  3. Export: python export_master.py\n")

