"""
Effiziente Methode: Analysiere die GA Index-Seiten für Links zu Vorträgen,
dann prüfe diese Vorträge auf Tafelzeichnungen
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CHALKBOARDS_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\chalkboards")

def find_all_webp_images_on_page(url):
    """Finde alle .webp Bilder auf einer Seite"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        
        images = set()
        
        # Regex für .webp Dateien
        webp_pattern = r'["\']([^"\']*\.webp)["\']'
        matches = re.findall(webp_pattern, response.text, re.IGNORECASE)
        
        for match in matches:
            # Konvertiere zu absoluter URL
            absolute_url = urljoin(url, match)
            images.add(absolute_url)
        
        return list(images)
    except:
        return []

def is_chalkboard_image(url):
    """Prüfe ob ein Bild eine Tafelzeichnung ist"""
    url_lower = url.lower()
    # Filterkriterien
    if any(exclude in url_lower for exclude in ['banner', 'logo', 'button', 'cots', 'shop']):
        return False
    # Inklusionskriterien
    if any(include in url_lower for include in ['-t', 'tafel', 'drawing', 'chalk']):
        return True
    # Wenn es im images/ Verzeichnis ist und eine Nummer hat
    if 'images/' in url_lower and re.search(r'\d+-\w+\d+\.webp', url_lower):
        return True
    return False

def find_chalkboards_in_ga(ga_number):
    """Finde Tafelzeichnungen für einen GA-Band"""
    base_url = f"https://rsarchive.org/Lectures/GA{ga_number}/"
    
    all_chalkboards = set()
    
    try:
        # Hole die GA Indexseite
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finde alle Links auf der Seite
        links = soup.find_all('a', href=True)
        
        # Sammle alle Vortragslinks (HTML-Dateien)
        lecture_urls = set()
        for link in links:
            href = link['href']
            # Nur .html Dateien, aber nicht index Dateien
            if href.endswith('.html') and 'index' not in href.lower():
                full_url = urljoin(base_url, href)
                lecture_urls.add(full_url)
        
        print(f"  → {len(lecture_urls)} Vortragsseiten gefunden, analysiere...", end=' ', flush=True)
        
        # Analysiere die ersten paar Vorträge auf Tafelzeichnungen
        checked = 0
        for lecture_url in list(lecture_urls)[:10]:  # Prüfe nur die ersten 10
            webp_images = find_all_webp_images_on_page(lecture_url)
            
            for img_url in webp_images:
                if is_chalkboard_image(img_url):
                    all_chalkboards.add(img_url)
                    
                    # Wenn wir eine Tafelzeichnung gefunden haben, extrahiere das Muster
                    # und suche nach weiteren im gleichen Verzeichnis
                    if '-T' in img_url or '-t' in img_url or 'Tafel' in img_url:
                        # Extrahiere Basis-URL und Muster
                        base_img_url = '/'.join(img_url.split('/')[:-1]) + '/'
                        
                        # Suche nach weiteren Tafelzeichnungen im gleichen Verzeichnis
                        for i in range(1, 30):
                            for pattern in [f'{ga_number}-T{i:02d}.webp', f'{ga_number}-Tafel_{i:02d}.webp']:
                                test_url = base_img_url + pattern
                                try:
                                    resp = requests.head(test_url, timeout=3)
                                    if resp.status_code == 200:
                                        all_chalkboards.add(test_url)
                                except:
                                    pass
            
            checked += 1
            if checked >= 10:
                break
    
    except Exception as e:
        pass
    
    return list(all_chalkboards)

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
    print("Effiziente Suche nach Tafelzeichnungen GA120-GA209")
    print("="*70 + "\n")
    
    existing = get_existing_ga_volumes()
    existing_in_range = sorted([ga for ga in existing if 120 <= ga <= 209])
    
    if existing_in_range:
        print(f"Bereits heruntergeladen: {existing_in_range}")
    else:
        print("Bereits heruntergeladen: (keine)")
    
    print("\nHinweis: Prüfe nur erste 10 Vorträge pro Band für Geschwindigkeit")
    print("Geschätzte Dauer: 3-5 Minuten\n")
    print("-" * 70 + "\n")
    
    all_results = {}
    start_time = time.time()
    
    for ga in range(120, 210):
        if ga in existing:
            print(f"GA{ga:03d}: Bereits heruntergeladen ✓")
            continue
        
        print(f"GA{ga:03d}...", end=' ', flush=True)
        images = find_chalkboards_in_ga(ga)
        
        if images:
            print(f"✓ {len(images)} Tafelzeichnung(en)!")
            all_results[ga] = images
        else:
            print("keine")
        
        time.sleep(0.3)
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print(f"ERGEBNIS (Dauer: {elapsed/60:.1f} Minuten)")
    print("="*70 + "\n")
    
    if all_results:
        print(f"Fehlende GA-Bände mit Tafelzeichnungen: {len(all_results)}\n")
        
        total_images = sum(len(imgs) for imgs in all_results.values())
        print(f"Gesamt: {total_images} Tafelzeichnungen\n")
        
        for ga in sorted(all_results.keys()):
            print(f"\nGA{ga}: {len(all_results[ga])} Tafelzeichnungen")
            for url in sorted(all_results[ga])[:3]:
                print(f"  {url}")
            if len(all_results[ga]) > 3:
                print(f"  ... und {len(all_results[ga]) - 3} weitere")
        
        # Save to file
        output_file = Path("fehlende_tafelzeichnungen_ga120-209.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Fehlende Tafelzeichnungen GA120-GA209\n")
            f.write("="*70 + "\n\n")
            f.write(f"Gesamt: {len(all_results)} GA-Bände, {total_images} Bilder\n\n")
            
            for ga in sorted(all_results.keys()):
                f.write(f"\n{'='*70}\n")
                f.write(f"GA{ga} ({len(all_results[ga])} Bilder):\n")
                f.write(f"{'='*70}\n")
                for url in sorted(all_results[ga]):
                    f.write(f"{url}\n")
        
        print(f"\n\nDetails gespeichert in: {output_file.absolute()}")
    else:
        print("Keine fehlenden Tafelzeichnungen gefunden.")

if __name__ == "__main__":
    main()

