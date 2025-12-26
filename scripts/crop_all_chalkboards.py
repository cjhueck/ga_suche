#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Croppt alle Wandtafelzeichnungen automatisch.
Entfernt weiße/helle Ränder von dunklen Bildern.

WICHTIG: 
- Helle Bilder werden übersprungen (manuell bearbeiten)
- Nur Bilder mit eindeutigem Kontrast werden gecroppt
- Erstellt Sicherungskopie vor dem Croppen
"""

import shutil
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("FEHLER: Pillow und numpy werden benötigt!")
    print("Installiere mit: pip install Pillow numpy")
    exit(1)

# Pfade
PROJECT_DIR = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_DIR / "Steiner_GA" / "chalkboards"
TARGET_DIR = PROJECT_DIR / "chalkboards"
BACKUP_DIR = PROJECT_DIR / "backups" / f"chalkboards-before-crop-{datetime.now().strftime('%Y-%m-%d_%H-%M')}"

# Parameter
THRESHOLD = 150  # Pixel mit Helligkeit > THRESHOLD gelten als "hell"
EDGE_SCAN_DEPTH = 30  # Wie viele Pixel vom Rand scannen
BRIGHT_RATIO = 0.7  # Wenn 70% der Pixel in einem Streifen hell sind
MAX_CROP_PERCENT = 0.05  # Maximal 5% pro Seite abschneiden

# Kontrast-Prüfung
MIN_CENTER_DARKNESS = 120  # Zentrum muss dunkler als dieser Wert sein (sonst = helles Bild)
MIN_CONTRAST = 50  # Mindestunterschied zwischen Rand und Inhalt


def get_brightness_array(img_array):
    """Konvertiert Bild zu Helligkeits-Array (0-255)."""
    if len(img_array.shape) == 3:
        return np.mean(img_array[:, :, :3], axis=2)
    return img_array.astype(float)


def is_dark_image(brightness):
    """Prüft ob das Bild dunkel genug ist für automatisches Cropping."""
    height, width = brightness.shape
    
    # Nimm das Zentrum des Bildes (mittlere 50%)
    margin_h = height // 4
    margin_w = width // 4
    center = brightness[margin_h:height-margin_h, margin_w:width-margin_w]
    
    avg_center = np.mean(center)
    return avg_center < MIN_CENTER_DARKNESS, avg_center


def has_clear_contrast(brightness, edge_brightness):
    """Prüft ob der Kontrast zwischen Rand und Inhalt eindeutig ist."""
    height, width = brightness.shape
    
    # Durchschnittliche Helligkeit im Zentrum
    margin_h = height // 4
    margin_w = width // 4
    center = brightness[margin_h:height-margin_h, margin_w:width-margin_w]
    avg_center = np.mean(center)
    
    # Vergleiche mit Rand-Helligkeit
    contrast = edge_brightness - avg_center
    return contrast >= MIN_CONTRAST, contrast


def find_diagonal_edge_crop(brightness, threshold, max_depth=50):
    """
    Findet schräge helle Ränder durch Analyse der Ecken.
    Gibt auch die durchschnittliche Rand-Helligkeit zurück.
    """
    height, width = brightness.shape
    edge_brightnesses = []
    
    # Linker Rand
    left_depths = []
    for row in range(height):
        depth = 0
        for col in range(min(max_depth, width)):
            if brightness[row, col] > threshold:
                depth = col + 1
                edge_brightnesses.append(brightness[row, col])
            else:
                break
        left_depths.append(depth)
    left_crop = int(np.percentile(left_depths, 90)) if left_depths else 0
    
    # Rechter Rand
    right_depths = []
    for row in range(height):
        depth = 0
        for col in range(min(max_depth, width)):
            if brightness[row, width - 1 - col] > threshold:
                depth = col + 1
                edge_brightnesses.append(brightness[row, width - 1 - col])
            else:
                break
        right_depths.append(depth)
    right_crop = int(np.percentile(right_depths, 90)) if right_depths else 0
    
    # Oberer Rand
    top_depths = []
    for col in range(width):
        depth = 0
        for row in range(min(max_depth, height)):
            if brightness[row, col] > threshold:
                depth = row + 1
                edge_brightnesses.append(brightness[row, col])
            else:
                break
        top_depths.append(depth)
    top_crop = int(np.percentile(top_depths, 90)) if top_depths else 0
    
    # Unterer Rand
    bottom_depths = []
    for col in range(width):
        depth = 0
        for row in range(min(max_depth, height)):
            if brightness[height - 1 - row, col] > threshold:
                depth = row + 1
                edge_brightnesses.append(brightness[height - 1 - row, col])
            else:
                break
        bottom_depths.append(depth)
    bottom_crop = int(np.percentile(bottom_depths, 90)) if bottom_depths else 0
    
    avg_edge_brightness = np.mean(edge_brightnesses) if edge_brightnesses else 0
    
    return left_crop, top_crop, right_crop, bottom_crop, avg_edge_brightness


def auto_crop(image_path):
    """
    Croppt ein Bild automatisch um helle Ränder zu entfernen.
    
    Returns:
        (cropped_image, stats) oder (None, stats) wenn nichts zu croppen war
    """
    img = Image.open(image_path)
    img_array = np.array(img)
    
    original_size = img.size
    brightness = get_brightness_array(img_array)
    
    stats = {
        'original_size': original_size,
        'cropped': False,
        'new_size': original_size,
        'removed': {'left': 0, 'top': 0, 'right': 0, 'bottom': 0},
        'skip_reason': None,
        'center_brightness': 0,
        'contrast': 0
    }
    
    # 1. Prüfe ob das Bild dunkel genug ist
    is_dark, center_brightness = is_dark_image(brightness)
    stats['center_brightness'] = center_brightness
    
    if not is_dark:
        stats['skip_reason'] = f"Helles Bild (Zentrum: {center_brightness:.0f})"
        return None, stats
    
    # 2. Finde Ränder
    left, top, right, bottom, edge_brightness = find_diagonal_edge_crop(brightness, THRESHOLD)
    
    # 3. Prüfe Kontrast
    clear_contrast, contrast = has_clear_contrast(brightness, edge_brightness)
    stats['contrast'] = contrast
    
    if not clear_contrast and (left + top + right + bottom) > 10:
        stats['skip_reason'] = f"Unklarer Kontrast ({contrast:.0f})"
        return None, stats
    
    # 4. Begrenze auf Maximum
    max_left = int(original_size[0] * MAX_CROP_PERCENT)
    max_right = int(original_size[0] * MAX_CROP_PERCENT)
    max_top = int(original_size[1] * MAX_CROP_PERCENT)
    max_bottom = int(original_size[1] * MAX_CROP_PERCENT)
    
    left = min(left, max_left)
    right = min(right, max_right)
    top = min(top, max_top)
    bottom = min(bottom, max_bottom)
    
    total_removed = left + top + right + bottom
    
    if total_removed < 2:
        stats['skip_reason'] = "Kein Rand erkannt"
        return None, stats
    
    # 5. Croppe
    crop_left = left
    crop_top = top
    crop_right = original_size[0] - right
    crop_bottom = original_size[1] - bottom
    
    cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
    
    stats['cropped'] = True
    stats['new_size'] = cropped.size
    stats['removed'] = {
        'left': left,
        'top': top,
        'right': right,
        'bottom': bottom
    }
    
    return cropped, stats


def main():
    print("=" * 70)
    print("CROP ALL CHALKBOARDS")
    print("=" * 70)
    print(f"Quelle:  {SOURCE_DIR}")
    print(f"Ziel:    {TARGET_DIR}")
    print(f"Backup:  {BACKUP_DIR}")
    print()
    print(f"Parameter:")
    print(f"  Threshold:        {THRESHOLD}")
    print(f"  Max Crop:         {MAX_CROP_PERCENT*100:.0f}% pro Seite")
    print(f"  Min Dunkelheit:   {MIN_CENTER_DARKNESS}")
    print(f"  Min Kontrast:     {MIN_CONTRAST}")
    print()
    
    # Sammle alle Bilder
    all_images = []
    for ga_folder in SOURCE_DIR.iterdir():
        if ga_folder.is_dir():
            for webp_file in ga_folder.glob("*.webp"):
                all_images.append(webp_file)
    
    print(f"Gefunden: {len(all_images)} Bilder")
    print()
    
    # Erstelle Backup-Verzeichnis
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Statistiken
    cropped_count = 0
    skipped_bright = 0
    skipped_contrast = 0
    skipped_no_edge = 0
    skipped_files = []
    
    for i, img_path in enumerate(all_images, 1):
        relative_path = img_path.relative_to(SOURCE_DIR)
        
        # Fortschrittsanzeige
        if i % 50 == 0 or i == len(all_images):
            print(f"Verarbeite {i}/{len(all_images)}...")
        
        # Backup erstellen
        backup_path = BACKUP_DIR / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_path, backup_path)
        
        # Croppe
        cropped_img, stats = auto_crop(img_path)
        
        if cropped_img:
            # Speichere gecropptes Bild
            target_path = TARGET_DIR / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            cropped_img.save(target_path, 'WEBP', quality=90)
            
            # Auch in Steiner_GA überschreiben
            cropped_img.save(img_path, 'WEBP', quality=90)
            
            cropped_count += 1
        else:
            # Kopiere unverändert
            target_path = TARGET_DIR / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_path, target_path)
            
            reason = stats.get('skip_reason', 'Unbekannt')
            if 'Helles Bild' in reason:
                skipped_bright += 1
                skipped_files.append((str(relative_path), reason))
            elif 'Kontrast' in reason:
                skipped_contrast += 1
                skipped_files.append((str(relative_path), reason))
            else:
                skipped_no_edge += 1
    
    print()
    print("=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"Gesamt:              {len(all_images)} Bilder")
    print(f"Gecroppt:            {cropped_count} Bilder")
    print(f"Übersprungen:")
    print(f"  - Helle Bilder:    {skipped_bright}")
    print(f"  - Unklarer Kontrast: {skipped_contrast}")
    print(f"  - Kein Rand:       {skipped_no_edge}")
    print()
    print(f"Backup erstellt in: {BACKUP_DIR}")
    print()
    
    if skipped_files:
        print("=" * 70)
        print("ÜBERSPRUNGENE BILDER (manuell prüfen):")
        print("=" * 70)
        for path, reason in skipped_files:
            print(f"  {path}")
            print(f"    -> {reason}")
        print()


if __name__ == "__main__":
    main()

