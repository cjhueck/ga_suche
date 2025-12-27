"""
Wendet die manuellen Crop-Einstellungen auf die hellen Wandtafelzeichnungen an.
"""

from pathlib import Path
from PIL import Image
import shutil
from datetime import datetime

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHALKBOARDS_DIR = PROJECT_DIR / "chalkboards"
BACKUP_DIR = PROJECT_DIR / "backups" / f"manual-crop-backup-{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

# Crop-Einstellungen (Prozent von jeder Seite)
CROP_SETTINGS = {
    "GA201/GA201-1920-04-17-T02.webp": {"left": 1, "right": 0, "top": 0, "bottom": 1},
    "GA206/GA206-1921-08-20-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA207/GA207-1921-09-24-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA214/GA214-1922-08-05-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA220/GA220-1923-01-27-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA229/GA229-1923-10-06-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA229/GA229-1923-10-06-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA230/GA230-1923-10-19-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA230/GA230-1923-10-26-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA230/GA230-1923-10-26-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA230/GA230-1923-11-02-T02.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA230/GA230-1923-11-04-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA230/GA230-1923-11-10-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA235/GA235-1924-02-16-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA235/GA235-1924-02-16-T02.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA235/GA235-1924-03-02-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA235/GA235-1924-03-08-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA235/GA235-1924-03-08-T03.webp": {"left": 0, "right": 0, "top": 1, "bottom": 0},
    "GA235/GA235-1924-03-22-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA237/GA237-1924-07-11-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA237/GA237-1924-08-01-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA237/GA237-1924-08-08-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA238/GA238-1924-09-10-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA279/GA279-1924-07-11-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA282/GA282-1924-09-13-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA291/GA291-1921-05-07-T01.webp": {"left": 0, "right": 0, "top": 1, "bottom": 0},
    "GA291/GA291-1921-05-07-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA291/GA291-1921-05-08-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA296/GA296-1919-08-10-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA296/GA296-1919-08-15-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-21-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 1},
    "GA312/GA312-1920-03-22-T01.webp": {"left": 0, "right": 1, "top": 0, "bottom": 0},
    "GA312/GA312-1920-03-23-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-25-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-25-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-26-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-27-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-27-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-28-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-29-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-30-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-30-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-03-31-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-01-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-01-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-03-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-03-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-07-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-07-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA312/GA312-1920-04-09-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA313/GA313-1921-04-11-T01.webp": {"left": 1, "right": 1, "top": 2, "bottom": 1},
    "GA313/GA313-1921-04-11-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA313/GA313-1921-04-13-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA313/GA313-1921-04-16-T01.webp": {"left": 1, "right": 0, "top": 2, "bottom": 0},
    "GA313/GA313-1921-04-17-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA313/GA313-1921-04-18-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA314/GA314-1920-10-09-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA314/GA314-1920-10-09-T03.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA314/GA314-1924-04-22-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA315/GA315-1921-04-12-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA315/GA315-1921-04-14-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA315/GA315-1921-04-17-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA326/GA326-1923-01-03-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA340/GA340-1922-07-24-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA347/GA347-1922-09-20-T01.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA353/GA353-1924-03-08-T02.webp": {"left": 1, "right": 0, "top": 1, "bottom": 0},
    "GA353/GA353-1924-06-04-T02.webp": {"left": 0, "right": 1, "top": 0, "bottom": 0},
}


def crop_image(img_path: Path, settings: dict) -> bool:
    """Croppt ein Bild basierend auf Prozent-Einstellungen."""
    try:
        with Image.open(img_path) as img:
            width, height = img.size
            
            # Berechne Pixel aus Prozent
            left_px = int(width * settings['left'] / 100)
            right_px = int(width * settings['right'] / 100)
            top_px = int(height * settings['top'] / 100)
            bottom_px = int(height * settings['bottom'] / 100)
            
            # Neue Grenzen
            new_left = left_px
            new_top = top_px
            new_right = width - right_px
            new_bottom = height - bottom_px
            
            # Prüfe ob Crop sinnvoll ist
            if new_right <= new_left or new_bottom <= new_top:
                print(f"  WARNUNG: Ungueltige Crop-Grenzen fuer {img_path.name}")
                return False
            
            # Croppen
            cropped = img.crop((new_left, new_top, new_right, new_bottom))
            
            # Speichern
            cropped.save(img_path, 'WEBP', quality=90)
            
            print(f"  Gecroppt: {img_path.name} ({width}x{height} -> {new_right-new_left}x{new_bottom-new_top})")
            return True
            
    except Exception as e:
        print(f"  FEHLER bei {img_path.name}: {e}")
        return False


def main():
    print("=== Manuelles Cropping der hellen Wandtafelzeichnungen ===\n")
    
    # Backup erstellen
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Erstelle Backup in: {BACKUP_DIR}\n")
    
    success_count = 0
    error_count = 0
    
    for rel_path, settings in CROP_SETTINGS.items():
        img_path = CHALKBOARDS_DIR / rel_path
        
        if not img_path.exists():
            print(f"  NICHT GEFUNDEN: {rel_path}")
            error_count += 1
            continue
        
        # Backup
        backup_path = BACKUP_DIR / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_path, backup_path)
        
        # Croppen
        if crop_image(img_path, settings):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\n=== Fertig ===")
    print(f"Erfolgreich: {success_count}")
    print(f"Fehler: {error_count}")
    print(f"Backup: {BACKUP_DIR}")


if __name__ == '__main__':
    main()

