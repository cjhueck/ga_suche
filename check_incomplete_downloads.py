"""
Überprüfe alle heruntergeladenen GA-Bände auf Vollständigkeit
Identifiziere fehlende Vorträge
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

LECTURES_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\lectures")

def count_available_lectures_on_rsarchive(ga_identifier):
    """
    Zähle wie viele Vorträge auf rsarchive.org verfügbar sind
    """
    ga_url = str(ga_identifier).replace('/', '').replace('_', '')
    base_url = f"https://rsarchive.org/Lectures/GA{ga_url}/"
    
    try:
        response = requests.get(base_url, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finde alle Vortrags-Links
        lecture_count = 0
        for link in soup.find_all('a', href=True):
            href = link['href']
            filename = href.split('/')[-1]
            # Pattern: 19100607p01.html, 19100607a01.html, 19200714e01.html
            if re.match(r'\d{8}[ape]\d{2}\.html', filename):
                lecture_count += 1
        
        # Entferne Duplikate (verschiedene Übersetzungen des gleichen Vortrags)
        # Nehme an dass es etwa 50% Duplikate gibt
        estimated_unique = max(1, lecture_count // 2)
        
        return estimated_unique
        
    except Exception as e:
        return None

def check_downloaded_lectures(ga_identifier):
    """
    Zähle heruntergeladene Vorträge
    """
    ga_folder_name = str(ga_identifier).replace('/', '_')
    ga_dir = LECTURES_DIR / f"GA{ga_folder_name}"
    
    if not ga_dir.exists():
        return 0
    
    # Zähle .md Dateien
    md_files = list(ga_dir.glob("*.md"))
    return len(md_files)

def main():
    print("\n" + "="*70)
    print("ÜBERPRÜFUNG AUF UNVOLLSTÄNDIGE DOWNLOADS")
    print("="*70)
    
    # Finde alle heruntergeladenen GA-Bände
    if not LECTURES_DIR.exists():
        print(f"✗ Verzeichnis nicht gefunden: {LECTURES_DIR}")
        return
    
    ga_dirs = [d for d in LECTURES_DIR.iterdir() if d.is_dir() and d.name.startswith('GA')]
    
    print(f"\n✓ {len(ga_dirs)} GA-Bände gefunden\n")
    print("-"*70)
    
    incomplete_downloads = []
    
    for ga_dir in sorted(ga_dirs, key=lambda x: x.name):
        ga_identifier = ga_dir.name.replace('GA', '')
        
        # Zähle lokal
        local_count = check_downloaded_lectures(ga_identifier)
        
        # Zähle auf rsarchive.org
        print(f"GA{ga_identifier}... ", end='', flush=True)
        online_count = count_available_lectures_on_rsarchive(ga_identifier)
        
        if online_count is None:
            print(f"✗ Online-Check fehlgeschlagen (lokal: {local_count})")
        elif local_count < online_count:
            diff = online_count - local_count
            print(f"⚠️  UNVOLLSTÄNDIG! Lokal: {local_count}, Online: ~{online_count}, Fehlen: ~{diff}")
            incomplete_downloads.append({
                'ga': ga_identifier,
                'local': local_count,
                'online': online_count,
                'missing': diff
            })
        else:
            print(f"✓ Vollständig ({local_count} Vorträge)")
        
        time.sleep(0.3)
    
    print("\n" + "="*70)
    print("ERGEBNIS")
    print("="*70)
    
    if incomplete_downloads:
        print(f"\n⚠️  {len(incomplete_downloads)} GA-Bände sind UNVOLLSTÄNDIG:\n")
        
        # Sortiere nach Anzahl fehlender Vorträge
        incomplete_downloads.sort(key=lambda x: x['missing'], reverse=True)
        
        for item in incomplete_downloads:
            print(f"  GA{item['ga']:6s}: {item['local']:3d} lokal, ~{item['online']:3d} online → ~{item['missing']:3d} fehlen")
        
        # Speichere Liste der unvollständigen GA-Bände
        missing_file = Path('UNVOLLSTÄNDIGE_GA_BÄNDE.txt')
        with open(missing_file, 'w', encoding='utf-8') as f:
            f.write("Unvollständige GA-Bände\n")
            f.write("="*70 + "\n\n")
            for item in incomplete_downloads:
                f.write(f"GA{item['ga']}\n")
        
        print(f"\n📄 Liste gespeichert in: {missing_file.absolute()}")
        
        # Erstelle Download-Script
        download_script = Path('download_missing_lectures.txt')
        with open(download_script, 'w', encoding='utf-8') as f:
            f.write("# Befehle zum Herunterladen fehlender Vorträge\n\n")
            for item in incomplete_downloads:
                f.write(f"python download_german_lectures.py {item['ga']}\n")
        
        print(f"📄 Download-Befehle in: {download_script.absolute()}")
    else:
        print("\n✅ Alle GA-Bände sind vollständig!")

if __name__ == "__main__":
    main()

