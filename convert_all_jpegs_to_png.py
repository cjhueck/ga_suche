#!/usr/bin/env python3
"""
Konvertiert alle JPEG-Bilder in den GA-Ordnern zu transparenten PNG-Dateien.
Weiße Hintergründe werden transparent gemacht, schwarze Zeichnungen bleiben erhalten.
"""

import os
from PIL import Image
from pathlib import Path

def convert_jpeg_to_transparent_png(jpeg_path, png_path, threshold=240):
    """
    Konvertiert JPEG zu PNG mit transparentem Hintergrund.
    
    Args:
        jpeg_path: Pfad zur JPEG-Datei
        png_path: Pfad zur zu erstellenden PNG-Datei
        threshold: RGB-Schwellenwert für Transparenz (Standard: 240)
                   Pixel mit allen RGB-Werten > threshold werden transparent
    """
    try:
        # Öffne JPEG
        img = Image.open(jpeg_path)
        
        # Konvertiere zu RGBA (für Transparenz)
        img = img.convert("RGBA")
        
        # Lade Pixel-Daten
        datas = img.getdata()
        new_data = []
        
        # Mache weiße/helle Bereiche transparent
        for item in datas:
            # Wenn Pixel fast weiß ist (R, G, B alle > threshold)
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                # Mache transparent (Alpha = 0)
                new_data.append((255, 255, 255, 0))
            else:
                # Behalte Pixel wie es ist
                new_data.append(item)
        
        # Setze neue Pixel-Daten
        img.putdata(new_data)
        
        # Speichere als PNG
        img.save(png_path, "PNG")
        return True
        
    except Exception as e:
        print(f"  X Fehler: {e}")
        return False


def process_ga_folder(ga_folder_path, folder_name):
    """
    Verarbeitet einen einzelnen GA-Ordner.
    """
    assets_path = os.path.join(ga_folder_path, 'assets')
    
    if not os.path.exists(assets_path):
        return 0, 0, 0
    
    converted = 0
    skipped = 0
    errors = 0
    
    # Finde alle JPEG-Dateien
    jpeg_files = []
    for file_name in os.listdir(assets_path):
        if file_name.lower().endswith(('.jpg', '.jpeg')):
            jpeg_files.append(file_name)
    
    if not jpeg_files:
        return 0, 0, 0
    
    print(f"\n{folder_name}:")
    print(f"  Gefunden: {len(jpeg_files)} JPEG-Dateien")
    
    for file_name in jpeg_files:
        jpeg_path = os.path.join(assets_path, file_name)
        
        # Erstelle PNG-Dateiname
        png_name = file_name.rsplit('.', 1)[0] + '.png'
        png_path = os.path.join(assets_path, png_name)
        
        # Überspringe, wenn PNG bereits existiert
        if os.path.exists(png_path):
            skipped += 1
            continue
        
        # Konvertiere
        if convert_jpeg_to_transparent_png(jpeg_path, png_path):
            converted += 1
        else:
            errors += 1
    
    if converted > 0 or skipped > 0:
        print(f"  > {converted} konvertiert, {skipped} uebersprungen, {errors} Fehler")
    
    return converted, skipped, errors


if __name__ == "__main__":
    # Bestimme Projekt-Root dynamisch
    project_root = os.path.dirname(os.path.abspath(__file__))
    steiner_ga_dir = os.path.join(project_root, "Steiner_GA")
    
    print("=" * 60)
    print("JPEG zu PNG Konverter - Alle GA-Bände")
    print("=" * 60)
    print(f"Basis-Ordner: {steiner_ga_dir}")
    print(f"Schwellenwert: 240 (Pixel > 240 werden transparent)\n")
    
    # Prüfe ob Pillow installiert ist
    try:
        from PIL import Image
    except ImportError:
        print("X Fehler: Pillow ist nicht installiert!")
        print("  Installieren Sie es mit: pip install Pillow")
        exit(1)
    
    total_converted = 0
    total_skipped = 0
    total_errors = 0
    folders_processed = 0
    
    # Durchlaufe alle GA-Ordner
    for folder_name in sorted(os.listdir(steiner_ga_dir)):
        folder_path = os.path.join(steiner_ga_dir, folder_name)
        
        # Überspringe Dateien
        if not os.path.isdir(folder_path):
            continue
        
        # Überspringe Ordner, die nicht mit GA anfangen
        if not folder_name.startswith('GA'):
            continue
        
        converted, skipped, errors = process_ga_folder(folder_path, folder_name)
        
        if converted > 0 or skipped > 0 or errors > 0:
            folders_processed += 1
            total_converted += converted
            total_skipped += skipped
            total_errors += errors
    
    print(f"\n{'='*60}")
    print(f"Fertig!")
    print(f"  GA-Ordner verarbeitet: {folders_processed}")
    print(f"  Bilder konvertiert: {total_converted}")
    print(f"  Bilder übersprungen (existieren bereits): {total_skipped}")
    print(f"  Fehler: {total_errors}")
    print(f"{'='*60}")
    
    if total_converted > 0:
        print(f"\nNächster Schritt:")
        print(f"  python export_images_from_lectures.py")

