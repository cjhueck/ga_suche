#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konvertiert JPEG-Dateien in GA267 und GA268 zu PNG-Format.
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_jpeg_to_png(ga_folder_path):
    """
    Konvertiert alle JPEG-Dateien (jpg, jpeg) in einem GA-Ordner zu PNG.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner (z.B. "Steiner_GA/GA267-Seelenübungen I")
    """
    ga_path = Path(ga_folder_path)
    
    if not ga_path.exists():
        print(f"❌ Ordner nicht gefunden: {ga_folder_path}")
        return 0, 0
    
    # Finde alle JPEG-Dateien rekursiv
    jpeg_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        jpeg_files.extend(ga_path.rglob(ext))
    
    if not jpeg_files:
        print(f"ℹ️  Keine JPEG-Dateien gefunden in: {ga_folder_path}")
        return 0, 0
    
    converted = 0
    errors = 0
    
    print(f"\n📁 Verarbeite: {ga_folder_path}")
    print(f"   Gefundene JPEG-Dateien: {len(jpeg_files)}")
    
    for jpeg_file in jpeg_files:
        try:
            # Erstelle PNG-Dateinamen (ersetze Extension)
            png_file = jpeg_file.with_suffix('.png')
            
            # Wenn PNG bereits existiert, lösche es zuerst (wird überschrieben)
            if png_file.exists():
                print(f"   🔄 Überschreibe vorhandene PNG: {png_file.name}")
                png_file.unlink()
            
            # Öffne und konvertiere Bild
            print(f"   🔄 Konvertiere: {jpeg_file.name} → {png_file.name}")
            with Image.open(jpeg_file) as img:
                # Konvertiere zu RGB falls notwendig (für JPEG mit Transparenz)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Behalte Transparenz bei
                    img.save(png_file, 'PNG', optimize=True)
                else:
                    # Konvertiere zu RGB für maximale Kompatibilität
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[3])  # Alpha-Kanal als Maske
                    else:
                        rgb_img.paste(img)
                    rgb_img.save(png_file, 'PNG', optimize=True)
            
            converted += 1
            
            # Lösche die ursprüngliche JPEG-Datei nach erfolgreicher Konvertierung
            jpeg_file.unlink()
            print(f"   ✅ Konvertiert und JPEG gelöscht: {jpeg_file.name}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {jpeg_file.name}: {str(e)}")
            errors += 1
    
    return converted, errors

def main():
    """Hauptfunktion"""
    base_dir = Path(__file__).parent
    steiner_ga_dir = base_dir / "Steiner_GA"
    
    # GA267 und GA268 Ordner
    ga_folders = [
        steiner_ga_dir / "GA267-Seelenübungen I",
        steiner_ga_dir / "GA268-Mantrische Sprüche Seelenübungen II"
    ]
    
    total_converted = 0
    total_errors = 0
    
    print("=" * 70)
    print("JPEG zu PNG Konvertierung für GA267 und GA268")
    print("=" * 70)
    
    for ga_folder in ga_folders:
        converted, errors = convert_jpeg_to_png(ga_folder)
        total_converted += converted
        total_errors += errors
    
    print("\n" + "=" * 70)
    print(f"✅ Konvertierung abgeschlossen!")
    print(f"   Konvertiert: {total_converted} Dateien")
    if total_errors > 0:
        print(f"   Fehler: {total_errors} Dateien")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unerwarteter Fehler: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

