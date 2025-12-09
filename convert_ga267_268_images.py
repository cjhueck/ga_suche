#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konvertiert JPEG-Bilder in GA267 und GA268 zu PNG und aktualisiert die JSON-Referenzen.
"""

import os
import json
import re
from pathlib import Path
from PIL import Image

def convert_jpeg_to_png(assets_dir, dry_run=False):
    """
    Konvertiert alle JPEG-Dateien im assets-Ordner zu PNG.
    
    Args:
        assets_dir: Pfad zum assets-Ordner
        dry_run: Wenn True, werden keine Dateien konvertiert
        
    Returns:
        Liste der konvertierten Dateien
    """
    converted_files = []
    
    if not os.path.exists(assets_dir):
        print(f"  ⚠ Assets-Ordner nicht gefunden: {assets_dir}")
        return converted_files
    
    # Finde alle JPEG-Dateien
    for filename in os.listdir(assets_dir):
        if filename.lower().endswith(('.jpeg', '.jpg')):
            jpeg_path = os.path.join(assets_dir, filename)
            
            # Erstelle PNG-Dateiname
            png_filename = re.sub(r'\.jpe?g$', '.png', filename, flags=re.IGNORECASE)
            png_path = os.path.join(assets_dir, png_filename)
            
            # Überspringe wenn PNG bereits existiert
            if os.path.exists(png_path):
                print(f"  ⚠ PNG bereits vorhanden: {png_filename}")
                continue
            
            try:
                if not dry_run:
                    # Konvertiere JPEG zu PNG
                    img = Image.open(jpeg_path)
                    img.save(png_path, 'PNG')
                    print(f"  ✓ Konvertiert: {filename} -> {png_filename}")
                else:
                    print(f"  [DRY-RUN] Würde konvertieren: {filename} -> {png_filename}")
                
                converted_files.append({
                    'jpeg': filename,
                    'png': png_filename,
                    'jpeg_path': jpeg_path,
                    'png_path': png_path
                })
            except Exception as e:
                print(f"  ✗ Fehler bei {filename}: {e}")
    
    return converted_files

def update_json_references(json_file, dry_run=False):
    """
    Aktualisiert alle JPEG-Referenzen in der JSON-Datei zu PNG.
    
    Args:
        json_file: Pfad zur JSON-Datei
        dry_run: Wenn True, werden keine Änderungen gespeichert
        
    Returns:
        Anzahl der geänderten Referenzen
    """
    if not os.path.exists(json_file):
        print(f"  ⚠ JSON-Datei nicht gefunden: {json_file}")
        return 0
    
    # Lade JSON-Datei
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_count = 0
    
    # Ersetze alle .jpeg/.jpg Referenzen mit .png
    # Pattern: ![img-X.jpeg](assets/...img-X.jpeg)
    pattern = r'!\[([^\]]*\.jpe?g)\](\(assets/[^)]*\.jpe?g[^)]*\))'
    
    def replace_jpeg(match):
        nonlocal changes_count
        alt_text = match.group(1)
        path_part = match.group(2)
        
        # Ersetze .jpeg/.jpg mit .png in beiden Teilen
        alt_text_png = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
        path_part_png = re.sub(r'\.jpe?g', '.png', path_part, flags=re.IGNORECASE)
        
        changes_count += 1
        return f'![{alt_text_png}]{path_part_png}'
    
    content = re.sub(pattern, replace_jpeg, content)
    
    # Speichere geänderte Datei
    if content != original_content:
        if not dry_run:
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ JSON-Datei aktualisiert: {changes_count} Referenzen geändert")
        else:
            print(f"  [DRY-RUN] Würde {changes_count} Referenzen in JSON ändern")
    else:
        print(f"  ℹ Keine Änderungen in JSON-Datei notwendig")
    
    return changes_count

def main():
    """Hauptfunktion"""
    base_dir = Path(__file__).parent
    steiner_ga_dir = base_dir / 'Steiner_GA'
    
    if not steiner_ga_dir.exists():
        print(f"❌ Steiner_GA Verzeichnis nicht gefunden: {steiner_ga_dir}")
        return
    
    # GA267
    print("\n=== GA267 ===")
    ga267_dir = steiner_ga_dir / 'GA267-Seelenübungen I'
    ga267_assets = ga267_dir / 'assets'
    ga267_json = base_dir / 'steiner-full-lectures-267-267.json'
    
    if ga267_assets.exists():
        print(f"Konvertiere JPEG-Dateien in: {ga267_assets}")
        converted = convert_jpeg_to_png(str(ga267_assets), dry_run=False)
        print(f"  → {len(converted)} Dateien konvertiert")
    else:
        print(f"  ⚠ Assets-Ordner nicht gefunden: {ga267_assets}")
    
    if ga267_json.exists():
        print(f"\nAktualisiere JSON-Referenzen: {ga267_json.name}")
        changes = update_json_references(str(ga267_json), dry_run=False)
    else:
        print(f"  ⚠ JSON-Datei nicht gefunden: {ga267_json}")
    
    # GA268
    print("\n=== GA268 ===")
    ga268_dir = steiner_ga_dir / 'GA268-Mantrische Sprüche Seelenübungen II'
    ga268_assets = ga268_dir / 'assets'
    ga268_json = base_dir / 'steiner-full-lectures-268-268.json'
    
    if ga268_assets.exists():
        print(f"Konvertiere JPEG-Dateien in: {ga268_assets}")
        converted = convert_jpeg_to_png(str(ga268_assets), dry_run=False)
        print(f"  → {len(converted)} Dateien konvertiert")
    else:
        print(f"  ⚠ Assets-Ordner nicht gefunden: {ga268_assets}")
    
    if ga268_json.exists():
        print(f"\nAktualisiere JSON-Referenzen: {ga268_json.name}")
        changes = update_json_references(str(ga268_json), dry_run=False)
    else:
        print(f"  ⚠ JSON-Datei nicht gefunden: {ga268_json}")
    
    print("\n✓ Fertig!")

if __name__ == '__main__':
    main()

