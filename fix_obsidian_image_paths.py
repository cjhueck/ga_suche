#!/usr/bin/env python3
"""
Korrigiert fehlerhafte Bildpfade in Obsidian-Markdown-Dateien.

Probleme die behoben werden:
1. Doppelte Ordnernamen: GA115-../GA115-../assets/... → assets/...
2. .jpeg Endungen → .png (da Bilder konvertiert wurden)
3. Falsche URLs (https://claude.ai/...) → korrekte Pfade

Verwendung:
    python fix_obsidian_image_paths.py           # Dry-Run (zeigt nur an)
    python fix_obsidian_image_paths.py --apply   # Führt Änderungen durch
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

def fix_image_paths_in_file(file_path, apply_changes=False):
    """
    Korrigiert Bildpfade in einer einzelnen Markdown-Datei.
    
    Returns:
        tuple: (num_fixes, changes_list)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Pattern 1: Doppelte Ordnernamen
        # ![alt](GA115-Anthroposophie - Psychosophie - Pneumatosophie/GA115-Anthroposophie - Psychosophie - Pneumatosophie/assets/...)
        pattern1 = r'!\[([^\]]*)\]\((GA\d{3}[a-z]?-[^/]+)/\2/(assets/[^)]+)\)'
        
        def replace1(match):
            alt_text = match.group(1)
            ga_folder = match.group(2)  # Nicht verwendet, aber gecaptured
            path = match.group(3)  # assets/...
            
            # Ersetze .jpeg durch .png
            path = re.sub(r'\.(jpe?g)$', '.png', path, flags=re.IGNORECASE)
            
            new_ref = f"![{alt_text}]({path})"
            changes.append(f"  - Doppelter Ordner entfernt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern1, replace1, content)
        
        # Pattern 2: Falsche URLs (Claude-Chat-Links)
        # ![alt](https://claude.ai/chat/GA076-...)
        pattern2 = r'!\[([^\]]*)\]\(https://claude\.ai/chat/([^)]+)\)'
        
        def replace2(match):
            alt_text = match.group(1)
            filename = match.group(2)  # z.B. GA076-Die befruchtende..._img-0.jpeg
            
            # Ersetze .jpeg durch .png
            filename = re.sub(r'\.(jpe?g)$', '.png', filename, flags=re.IGNORECASE)
            
            new_ref = f"![{alt_text}](assets/{filename})"
            changes.append(f"  - Claude-URL korrigiert: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern2, replace2, content)
        
        # Pattern 3: Doppelter "assets/" im Pfad
        # ![alt](assets/GA300b-.../assets/GA300b-..._img-0.jpeg)
        pattern3 = r'!\[([^\]]*)\]\(assets/(GA\d{3}[a-z]?-[^/]+)/assets/([^)]+)\)'
        
        def replace3(match):
            alt_text = match.group(1)
            filename = match.group(3)
            
            # Ersetze .jpeg durch .png
            filename = re.sub(r'\.(jpe?g)$', '.png', filename, flags=re.IGNORECASE)
            
            new_ref = f"![{alt_text}](assets/{filename})"
            changes.append(f"  - Doppelter assets/ entfernt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern3, replace3, content)
        
        # Pattern 4: Einfache .jpeg → .png Konvertierung für bereits korrekte Pfade
        # ![alt](assets/...jpeg)
        pattern4 = r'(!\[[^\]]*\]\(assets/[^)]+)\.(jpe?g)\)'
        
        def replace4(match):
            base = match.group(1)
            ext = match.group(2)
            new_ref = f"{base}.png)"
            changes.append(f"  - .{ext} -> .png: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern4, replace4, content, flags=re.IGNORECASE)
        
        # Wende Änderungen an, falls gewünscht
        if changes and apply_changes:
            # Erstelle Backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Speichere korrigierte Datei
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return len(changes), changes
        
    except Exception as e:
        print(f"  X Fehler bei {file_path}: {e}")
        return 0, []


def process_ga_folders(steiner_ga_dir, apply_changes=False):
    """
    Durchsucht alle GA-Ordner und korrigiert Bildpfade.
    """
    print("=" * 60)
    print("OBSIDIAN BILDPFAD-KORREKTUR")
    print("=" * 60)
    print(f"Basis-Ordner: {steiner_ga_dir}")
    print(f"Modus: {'ANWENDEN' if apply_changes else 'DRY-RUN (nur anzeigen)'}")
    print("=" * 60 + "\n")
    
    if not os.path.exists(steiner_ga_dir):
        print(f"X Fehler: Ordner nicht gefunden: {steiner_ga_dir}")
        return
    
    total_files_checked = 0
    total_files_fixed = 0
    total_fixes = 0
    
    # Durchlaufe alle GA-Ordner
    ga_folders = []
    for folder_name in os.listdir(steiner_ga_dir):
        folder_path = os.path.join(steiner_ga_dir, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith('GA'):
            ga_folders.append((folder_name, folder_path))
    
    ga_folders.sort()
    
    for folder_name, folder_path in ga_folders:
        # Finde alle Markdown-Dateien (Lecture-Dateien: "GA xxx (n.) ...")
        md_files = []
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.md') and '(' in file_name and ')' in file_name:
                md_files.append(os.path.join(folder_path, file_name))
        
        if not md_files:
            continue
        
        folder_fixed = False
        
        for md_file in md_files:
            total_files_checked += 1
            num_fixes, changes = fix_image_paths_in_file(md_file, apply_changes)
            
            if num_fixes > 0:
                if not folder_fixed:
                    print(f"\n{folder_name}:")
                    folder_fixed = True
                
                print(f"  {os.path.basename(md_file)}: {num_fixes} Korrekturen")
                for change in changes:
                    print(change)
                
                total_files_fixed += 1
                total_fixes += num_fixes
    
    print(f"\n{'='*60}")
    print(f"FERTIG!")
    print(f"{'='*60}")
    print(f"  Dateien geprüft: {total_files_checked}")
    print(f"  Dateien mit Korrekturen: {total_files_fixed}")
    print(f"  Gesamt-Korrekturen: {total_fixes}")
    
    if apply_changes and total_files_fixed > 0:
        print(f"\n  Backups erstellt: *.backup")
        print(f"  Änderungen wurden angewendet!")
    elif not apply_changes and total_files_fixed > 0:
        print(f"\n  Führen Sie das Skript mit --apply aus, um Änderungen anzuwenden:")
        print(f"  python fix_obsidian_image_paths.py --apply")
    
    print(f"{'='*60}\n")
    
    # Empfehlung für nächste Schritte
    if apply_changes and total_files_fixed > 0:
        print("Nächste Schritte:")
        print("  1. node export-lectures.js GA112-GA117a")
        print("  2. python export_steiner_images_integrated.py")
        print("  3. Server neu starten: node backend.js")


if __name__ == "__main__":
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    
    # Parse Argumente
    apply_changes = '--apply' in sys.argv or '-a' in sys.argv
    
    if not apply_changes:
        print("\n" + "!" * 60)
        print("DRY-RUN MODUS - Keine Änderungen werden vorgenommen")
        print("!" * 60 + "\n")
    
    process_ga_folders(steiner_ga_dir, apply_changes)

