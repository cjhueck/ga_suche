# -*- coding: utf-8 -*-
"""
Benennt Bilddateien um und aktualisiert die Markdown-Pfade
Von: GA091-Kosmologie und menschliche Evolution_img-19.png → img-19.png
Pfad: assets/GA091-Kosmologie und menschliche Evolution_img-19.png → assets/img-19.png
"""
import os
import sys
import re
import shutil
from pathlib import Path

# Setze UTF-8 für Console-Output
sys.stdout = sys.__stdout__
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

STEINER_GA_DIR = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

def rename_images_in_folder(folder_path):
    """Benennt Bilddateien in einem assets-Ordner um"""
    assets_dir = os.path.join(folder_path, 'assets')
    
    if not os.path.exists(assets_dir):
        return 0
    
    renamed_count = 0
    
    # Finde alle Bilddateien mit langem GA-Präfix
    for filename in os.listdir(assets_dir):
        # Pattern: GA123-Titel...._img-5.png
        match = re.match(r'GA\d{3}[a-z]?-.+_(img-\d+\.\w+)$', filename)
        
        if match:
            new_filename = match.group(1)
            old_path = os.path.join(assets_dir, filename)
            new_path = os.path.join(assets_dir, new_filename)
            
            # Prüfe ob Zieldatei bereits existiert
            if os.path.exists(new_path):
                print(f"    [!] Überspringe {filename} - {new_filename} existiert bereits")
                continue
            
            # Benenne um
            os.rename(old_path, new_path)
            renamed_count += 1
    
    return renamed_count

def update_image_paths_in_file(filepath):
    """Aktualisiert Bildpfade in einer Markdown-Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern für Markdown-Bilder mit langem GA-Präfix
        # ![alt](assets/GA123-Titel...._img-5.png) → ![alt](assets/img-5.png)
        pattern = r'!\[([^\]]*)\]\(assets/GA\d{3}[a-z]?-[^_]+_(img-\d+\.\w+)\)'
        
        def simplify_path(match):
            alt_text = match.group(1)
            img_filename = match.group(2)
            return f'![{alt_text}](assets/{img_filename})'
        
        content = re.sub(pattern, simplify_path, content)
        
        # Zähle Änderungen
        num_changes = len(re.findall(pattern, original_content))
        
        # Nur speichern wenn Änderungen vorgenommen wurden
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return num_changes
        
        return 0
        
    except Exception as e:
        print(f"  [X] Fehler bei {filepath}: {e}")
        return 0

def main():
    print("=" * 80)
    print("Benenne Bilder um und vereinfache Bildpfade in Steiner_GA")
    print("=" * 80)
    print()
    
    if not os.path.exists(STEINER_GA_DIR):
        print(f"[X] Fehler: Steiner_GA-Ordner nicht gefunden: {STEINER_GA_DIR}")
        return
    
    total_files = 0
    total_path_changes = 0
    total_renamed_images = 0
    folders_processed = 0
    
    # Durchlaufe alle GA-Ordner
    for folder_name in sorted(os.listdir(STEINER_GA_DIR)):
        folder_path = os.path.join(STEINER_GA_DIR, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Benenne Bilder um
        renamed_count = rename_images_in_folder(folder_path)
        
        # Finde alle Markdown-Dateien
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files and renamed_count == 0:
            continue
        
        folder_had_changes = False
        folder_path_changes = 0
        folder_files = 0
        
        # Aktualisiere Markdown-Pfade
        for md_file in md_files:
            md_path = os.path.join(folder_path, md_file)
            num_changes = update_image_paths_in_file(md_path)
            
            if num_changes > 0:
                folder_path_changes += num_changes
                folder_files += 1
        
        if renamed_count > 0 or folder_path_changes > 0:
            if not folder_had_changes:
                print(f"\n{folder_name}:")
                folder_had_changes = True
            
            if renamed_count > 0:
                print(f"  [OK] {renamed_count} Bild(er) umbenannt")
            if folder_path_changes > 0:
                print(f"  [OK] {folder_path_changes} Pfad(e) in {folder_files} Datei(en) aktualisiert")
        
        if folder_had_changes:
            folders_processed += 1
            total_files += folder_files
            total_path_changes += folder_path_changes
            total_renamed_images += renamed_count
    
    print()
    print("=" * 80)
    print(f"Zusammenfassung:")
    print(f"  Ordner verarbeitet: {folders_processed}")
    print(f"  Bilder umbenannt: {total_renamed_images}")
    print(f"  Markdown-Dateien aktualisiert: {total_files}")
    print(f"  Bildpfade vereinfacht: {total_path_changes}")
    print("=" * 80)
    
    if total_renamed_images > 0 or total_path_changes > 0:
        print("\n[OK] Fertig! Bilder wurden umbenannt und Pfade vereinfacht.")
        print("\nBilder haben jetzt einfache Namen: img-0.png, img-1.png, etc.")
    else:
        print("\n[OK] Keine Aenderungen notwendig.")

if __name__ == "__main__":
    main()

