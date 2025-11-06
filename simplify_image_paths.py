# -*- coding: utf-8 -*-
"""
Vereinfacht Bildpfade in Markdown-Dateien
Von: assets/GA091-Kosmologie und menschliche Evolution_img-19.png
Zu:  assets/img-19.png
"""
import os
import sys
import re
from pathlib import Path

# Setze UTF-8 für Console-Output
sys.stdout = sys.__stdout__
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

STEINER_GA_DIR = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

def simplify_image_paths_in_file(filepath):
    """Vereinfacht Bildpfade in einer Markdown-Datei"""
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
    print("Vereinfache Bildpfade in Steiner_GA Markdown-Dateien")
    print("=" * 80)
    print()
    
    if not os.path.exists(STEINER_GA_DIR):
        print(f"[X] Fehler: Steiner_GA-Ordner nicht gefunden: {STEINER_GA_DIR}")
        return
    
    total_files = 0
    total_changes = 0
    folders_processed = 0
    
    # Durchlaufe alle GA-Ordner
    for folder_name in sorted(os.listdir(STEINER_GA_DIR)):
        folder_path = os.path.join(STEINER_GA_DIR, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Finde alle Markdown-Dateien
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files:
            continue
        
        folder_had_changes = False
        folder_changes = 0
        folder_files = 0
        
        for md_file in md_files:
            md_path = os.path.join(folder_path, md_file)
            num_changes = simplify_image_paths_in_file(md_path)
            
            if num_changes > 0:
                if not folder_had_changes:
                    print(f"\n{folder_name}:")
                    folder_had_changes = True
                
                print(f"  [OK] {md_file}: {num_changes} Bildpfad(e) vereinfacht")
                folder_changes += num_changes
                folder_files += 1
        
        if folder_had_changes:
            folders_processed += 1
            total_files += folder_files
            total_changes += folder_changes
    
    print()
    print("=" * 80)
    print(f"Zusammenfassung:")
    print(f"  Ordner verarbeitet: {folders_processed}")
    print(f"  Dateien geaendert: {total_files}")
    print(f"  Bildpfade vereinfacht: {total_changes}")
    print("=" * 80)
    
    if total_changes > 0:
        print("\n[OK] Fertig! Alle Bildpfade wurden vereinfacht.")
        print("\nHinweis: Die Bilder haben jetzt einfache Pfade wie 'assets/img-19.png'")
    else:
        print("\n[OK] Keine Vereinfachungen notwendig.")

if __name__ == "__main__":
    main()

