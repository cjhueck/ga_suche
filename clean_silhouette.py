#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bereinigt Scherenschnitt-Bilder:
- Entfernt graue Hintergründe (macht sie transparent)
- Entfernt doppelte Schatten
- Behält saubere schwarze Konturen
"""

from PIL import Image
import numpy as np
import sys
import io
from pathlib import Path

# Stelle sicher, dass UTF-8 für stdout verwendet wird
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def clean_silhouette(input_path, output_path=None):
    """
    Bereinigt ein Scherenschnitt-Bild:
    - Entfernt graue Hintergründe (transparent)
    - Entfernt doppelte Schatten
    - Behält saubere schwarze Konturen
    """
    # Lade Bild
    img = Image.open(input_path)
    
    # Konvertiere zu RGBA falls nötig
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Konvertiere zu NumPy Array
    data = np.array(img)
    
    # Trenne Kanäle
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    
    # Erkenne schwarze Bereiche (sehr dunkle Pixel)
    # Schwellenwert für "schwarz" - anpassbar je nach Bild
    black_threshold = 60  # Pixel mit RGB < 60 gelten als schwarz (etwas höher für bessere Erkennung)
    
    # Berechne Helligkeit und Farbunterschiede
    brightness = (r.astype(float) + g.astype(float) + b.astype(float)) / 3.0
    max_rgb = np.maximum(np.maximum(r, g), b)
    min_rgb = np.minimum(np.minimum(r, g), b)
    rgb_diff = max_rgb.astype(float) - min_rgb.astype(float)
    
    # Erstelle Maske für schwarze Konturen
    # Schwarze Konturen: alle RGB-Werte sehr niedrig UND ähnlich (keine starke Farbabweichung)
    is_black = (
        (r < black_threshold) & 
        (g < black_threshold) & 
        (b < black_threshold) &
        (rgb_diff < 20)  # Schwarze Bereiche sollten ähnliche RGB-Werte haben
    )
    
    # Erkenne graue Hintergrundbereiche (heller als schwarz, aber nicht zu bunt)
    # Grau = alle RGB-Werte ähnlich und heller als schwarz
    gray_threshold_min = 70  # Mindesthelligkeit für Grau (niedriger, um auch dunklere Grautöne zu erfassen)
    gray_threshold_max = 250  # Maximale Helligkeit für Grau
    gray_similarity = 40  # Maximale Differenz zwischen R, G, B für Grau (höher für bessere Erkennung)
    
    # Erstelle Maske für graue Hintergründe und Schatten
    is_gray = (
        (brightness >= gray_threshold_min) & 
        (brightness <= gray_threshold_max) & 
        (rgb_diff < gray_similarity) &
        (~is_black)  # Nicht schwarz
    )
    
    # Erstelle Maske für sehr helle Bereiche (auch entfernen)
    is_very_light = brightness > 240
    
    # Kombiniere Masken: Alles außer schwarzen Konturen wird transparent
    # Behalte schwarze Konturen, entferne alles andere (Grau, sehr hell, etc.)
    mask = is_black
    
    # Erstelle neues Alpha-Kanal
    new_alpha = np.where(mask, 255, 0).astype(np.uint8)
    
    # Für schwarze Bereiche: Setze auf reines Schwarz (0,0,0)
    new_r = np.where(mask, 0, 0).astype(np.uint8)
    new_g = np.where(mask, 0, 0).astype(np.uint8)
    new_b = np.where(mask, 0, 0).astype(np.uint8)
    
    # Kombiniere zu neuem Bild
    cleaned_data = np.stack([new_r, new_g, new_b, new_alpha], axis=2)
    
    # Erstelle neues Bild
    cleaned_img = Image.fromarray(cleaned_data)
    
    # Speichere Ergebnis
    input_path_obj = Path(input_path)
    
    if output_path is None:
        # Erstelle Backup des Originals
        backup_path = input_path_obj.parent / f"{input_path_obj.stem}_backup{input_path_obj.suffix}"
        img.save(backup_path, img.format if img.format else 'PNG')
        print(f"[INFO] Backup erstellt: {backup_path}")
        # Ersetze Original
        output_path = input_path
    else:
        output_path = Path(output_path)
    
    # Speichere als PNG (unterstützt Transparenz) oder WebP
    output_path_str = str(output_path)
    if output_path_str.lower().endswith('.webp'):
        cleaned_img.save(output_path_str, 'WEBP', lossless=True)
    else:
        # Falls ursprünglich WebP, speichere als PNG
        if input_path.lower().endswith('.webp'):
            output_path_str = str(Path(output_path).with_suffix('.png'))
        cleaned_img.save(output_path_str, 'PNG')
    
    print(f"[OK] Bild bereinigt: {output_path_str}")
    print(f"  Original: {img.size[0]}x{img.size[1]}, Modus: {img.mode}")
    print(f"  Bereinigt: {cleaned_img.size[0]}x{cleaned_img.size[1]}, Modus: {cleaned_img.mode}")
    
    return cleaned_img

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Verwendung: python clean_silhouette.py <bildpfad> [ausgabepfad]")
        print("\nBeispiel:")
        print("  python clean_silhouette.py Abb.123-01.webp")
        print("  python clean_silhouette.py Abb.123-01.webp Abb.123-01_cleaned.png")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"Fehler: Datei nicht gefunden: {input_file}")
        sys.exit(1)
    
    try:
        clean_silhouette(input_file, output_file)
    except Exception as e:
        print(f"Fehler beim Bearbeiten: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

