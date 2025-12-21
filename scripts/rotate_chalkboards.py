#!/usr/bin/env python3
"""
Dreht Wandtafelzeichnungen um 90 Grad im Uhrzeigersinn.

Pillow verwendet negative Winkel für Uhrzeigersinn:
- rotate(-90) = 90 Grad im Uhrzeigersinn
"""

from pathlib import Path
from PIL import Image
import sys

PROJECT_DIR = Path(__file__).parent.parent
CHALKBOARDS_DIR = PROJECT_DIR / "Steiner_GA" / "chalkboards"


def rotate_image(filepath: Path, degrees: int = -90) -> bool:
    """
    Dreht ein Bild um die angegebenen Grad.
    -90 = 90 Grad im Uhrzeigersinn
    +90 = 90 Grad gegen den Uhrzeigersinn
    
    Returns: True wenn erfolgreich
    """
    try:
        with Image.open(filepath) as img:
            # expand=True sorgt dafür, dass das Bild nicht abgeschnitten wird
            rotated = img.rotate(degrees, expand=True)
            rotated.save(filepath, quality=95)
        return True
    except Exception as e:
        print(f"  FEHLER bei {filepath.name}: {e}")
        return False


def main(ga_filter: set = None):
    print("=" * 60)
    print("  DREHE WANDTAFELZEICHNUNGEN (90 Grad im Uhrzeigersinn)")
    print("=" * 60)
    print()
    
    if not CHALKBOARDS_DIR.exists():
        print(f"FEHLER: Verzeichnis nicht gefunden: {CHALKBOARDS_DIR}")
        return
    
    if ga_filter:
        print(f"GA-Filter: {', '.join(sorted(ga_filter))}")
        print()
    
    total_rotated = 0
    total_errors = 0
    
    # Durchlaufe alle GA-Ordner
    for ga_folder in sorted(CHALKBOARDS_DIR.iterdir()):
        if not ga_folder.is_dir():
            continue
        
        # Extrahiere GA-Nummer aus Ordnername (z.B. "GA076" -> "076")
        ga_name = ga_folder.name
        ga_number = ga_name.replace("GA", "")
        
        # Prüfe GA-Filter
        if ga_filter and ga_number not in ga_filter:
            continue
        
        # Finde alle WebP-Dateien
        webp_files = list(ga_folder.glob("*.webp"))
        if not webp_files:
            continue
        
        print(f"{ga_name}: {len(webp_files)} Bilder")
        
        for webp_file in sorted(webp_files):
            if rotate_image(webp_file):
                print(f"  + {webp_file.name}")
                total_rotated += 1
            else:
                total_errors += 1
    
    print()
    print("=" * 60)
    print(f"  ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Bilder gedreht: {total_rotated}")
    if total_errors:
        print(f"  Fehler: {total_errors}")
    print("=" * 60)


if __name__ == "__main__":
    # GA-Filter aus Kommandozeile
    ga_filter = None
    if len(sys.argv) > 1:
        ga_filter = set()
        for arg in sys.argv[1:]:
            # Normalisiere: "GA076" -> "076", "ga191" -> "191"
            ga = arg.upper().replace("GA", "")
            ga_filter.add(ga)
    
    main(ga_filter)

