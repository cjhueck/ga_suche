"""
Schnellere Methode: Parse die GA-Seiten nach tatsächlichen Bild-Links
statt blind URLs zu testen
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import time
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CHALKBOARDS_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\chalkboards")

def find_chalkboards_in_ga(ga_number):
    """
    Parse die GA-Seite und alle verlinkten Vorträge nach Tafelzeichnungen
    """
    base_url = f"https://rsarchive.org/Lectures/GA{ga_number}/"
    found_images = set()
    
    try:
        # Hole die Hauptseite
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            return []
        
        # Parse für alle .webp Bilder und Bild-Links
        content = response.text
        
        # Methode 1: Suche nach direkten .webp Links im HTML
        webp_pattern = r'["\']([^"\']*\.webp)["\']'
        matches = re.findall(webp_pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Filter für Tafelzeichnungen (ignoriere Banner, Logos, etc.)
            if any(keyword in match.lower() for keyword in ['-t', 'tafel', 'drawing', 'chalk']):
                # Konvertiere relative zu absolute URLs
                if match.startswith('http'):
                    found_images.add(match)
                elif match.startswith('/'):
                    found_images.add(f"https://rsarchive.org{match}")
                else:
                    found_images.add(f"{base_url}{match}")
        
        # Methode 2: Parse mit BeautifulSoup für img tags
        soup = BeautifulSoup(content, 'html.parser')
        
        # Suche nach Links zu "images" Verzeichnissen
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'images' in href.lower() or 'chalkboard' in href.lower():
                # Folge dem Link
                if not href.startswith('http'):
                    if href.startswith('/'):
                        full_url = f"https://rsarchive.org{href}"
                    else:
                        full_url = f"{base_url}{href}"
                else:
                    full_url = href
                
                # Hole die Bilder von dieser Seite
                try:
                    img_response = requests.get(full_url, timeout=10)
                    if img_response.status_code == 200:
                        img_matches = re.findall(webp_pattern, img_response.text, re.IGNORECASE)
                        for img in img_matches:
                            if any(kw in img.lower() for kw in ['-t', 'tafel']):
                                if img.startswith('http'):
                                    found_images.add(img)
                                elif img.startswith('/'):
                                    found_images.add(f"https://rsarchive.org{img}")
                                else:
                                    # Relative zum aktuellen Verzeichnis
                                    base_dir = '/'.join(full_url.split('/')[:-1])
                                    found_images.add(f"{base_dir}/{img}")
                except:
                    pass
        
        # Methode 3: Suche nach bekannten Verzeichnis-Mustern
        common_paths = [
            f"{base_url}images/",
            f"{base_url}English/images/",
            f"{base_url}German/images/",
        ]
        
        for path in common_paths:
            try:
                resp = requests.get(path, timeout=5)
                if resp.status_code == 200:
                    # Extrahiere alle .webp Dateien aus dem Directory Listing oder HTML
                    webp_files = re.findall(r'href=["\']([^"\']*\.webp)["\']', resp.text, re.IGNORECASE)
                    for webp in webp_files:
                        if any(kw in webp.lower() for kw in ['-t', 'tafel']):
                            if not webp.startswith('http'):
                                found_images.add(f"{path}{webp}")
                            else:
                                found_images.add(webp)
            except:
                pass
        
    except Exception as e:
        pass
    
    return list(found_images)

def get_existing_ga_volumes():
    """Get list of GA volumes that already have chalkboards"""
    if not CHALKBOARDS_DIR.exists():
        return set()
    
    existing = set()
    for folder in CHALKBOARDS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith("GA"):
            ga_num = folder.name.replace("GA", "").rstrip('ABCD')
            try:
                existing.add(int(ga_num))
            except ValueError:
                pass
    
    return existing

def main():
    print("\n" + "="*70)
    print("Schnelle Suche nach Tafelzeichnungen GA120-GA209")
    print("="*70 + "\n")
    
    existing = get_existing_ga_volumes()
    existing_in_range = sorted([ga for ga in existing if 120 <= ga <= 209])
    
    if existing_in_range:
        print(f"Bereits heruntergeladen: {existing_in_range}\n")
    else:
        print("Bereits heruntergeladen: (keine)\n")
    
    # Teste zuerst die bekannten Bände
    print("Teste bekannte Bände:")
    print("-" * 70)
    
    known_with_chalkboards = {
        202: "https://rsarchive.org/Lectures/GA202/English/SOL2024/images/202-T06.webp",
        205: "https://rsarchive.org/Lectures/GA205/images/205-Tafel_11.webp",
        206: "https://rsarchive.org/Lectures/GA206/English/APC1958/images/206-T02.webp",
    }
    
    for ga, example_url in known_with_chalkboards.items():
        print(f"\nGA{ga}:")
        print(f"  Bekanntes Beispiel: {example_url}")
        print(f"  Suche... ", end='', flush=True)
        images = find_chalkboards_in_ga(ga)
        if images:
            print(f"✓ {len(images)} gefunden")
            for img in images[:2]:
                print(f"    - {img}")
        else:
            print("✗ Keine gefunden (Methode zu verbessern)")
    
    print("\n" + "="*70)
    print("Vollständige Suche (dies kann 5-10 Minuten dauern)")
    print("="*70 + "\n")
    
    all_results = {}
    
    for ga in range(120, 210):
        if ga in existing:
            print(f"GA{ga:03d}: Bereits heruntergeladen ✓")
            continue
        
        print(f"GA{ga:03d}... ", end='', flush=True)
        images = find_chalkboards_in_ga(ga)
        
        if images:
            print(f"✓ {len(images)} Tafelzeichnung(en)!")
            all_results[ga] = images
        else:
            print("keine")
        
        time.sleep(0.5)  # Sei höflich zum Server
    
    print("\n" + "="*70)
    print("ERGEBNIS")
    print("="*70 + "\n")
    
    if all_results:
        print(f"Fehlende GA-Bände mit Tafelzeichnungen: {len(all_results)}\n")
        
        for ga in sorted(all_results.keys()):
            print(f"\nGA{ga}: {len(all_results[ga])} Tafelzeichnungen")
            for url in sorted(all_results[ga])[:5]:
                print(f"  {url}")
            if len(all_results[ga]) > 5:
                print(f"  ... und {len(all_results[ga]) - 5} weitere")
        
        # Save to file
        output_file = Path("fehlende_tafelzeichnungen_ga120-209.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Fehlende Tafelzeichnungen GA120-GA209\n")
            f.write("="*70 + "\n\n")
            
            for ga in sorted(all_results.keys()):
                f.write(f"\nGA{ga} ({len(all_results[ga])} Bilder):\n")
                for url in sorted(all_results[ga]):
                    f.write(f"  {url}\n")
        
        print(f"\n\nDetails gespeichert in: {output_file.absolute()}")
    else:
        print("Keine fehlenden Tafelzeichnungen gefunden.")
    
    print("\n" + "="*70)
    print("Hinweis: Falls bekannte Tafelzeichnungen nicht gefunden wurden,")
    print("liegt das an versteckten URL-Strukturen. Wir können dann einen")
    print("anderen Ansatz verwenden.")
    print("="*70)

if __name__ == "__main__":
    main()

