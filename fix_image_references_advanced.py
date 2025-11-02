#!/usr/bin/env python3
"""
Korrigiert fehlerhafte Bildreferenzen in Obsidian
==================================================
Behebt:
1. Wiki-Links mit vollem Pfad: ![[GA223-.../assets/223-T01.webp]] → ![[223-T01.webp]]
2. Falsche Dateinamen: 213-T01 3.webp → 213-T01.webp
3. Unterstrich statt Bindestrich: 221_T01.webp → 221-T01.webp

Verwendung:
    python fix_image_references_advanced.py           # Dry-Run
    python fix_image_references_advanced.py --apply   # Anwenden
"""

import os
import re
import sys

def fix_image_refs_in_file(filepath, apply_changes=False):
    """Korrigiert Bildreferenzen in einer Markdown-Datei"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Fix 1: Wiki-Links mit vollem Pfad vereinfachen
        # ![[GA223-Der Jahreskreislauf.../assets/223-T01.webp]] → ![[223-T01.webp]]
        pattern1 = r'!\[\[GA\d{3}[a-z]?-[^/]+/assets/([^\]]+)\]\]'
        
        def replace1(match):
            filename = match.group(1)
            new_ref = f'![[{filename}]]'
            changes.append(f"  - Wiki-Link vereinfacht: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern1, replace1, content)
        
        # Fix 2: Falsche Dateinamen mit Leerzeichen korrigieren
        # ![[213-T01 3.webp]] → ![[213-T01.webp]]
        pattern2 = r'!\[\[(\d{3})-T(\d{2})\s+\d+\.webp\]\]'
        
        def replace2(match):
            num1 = match.group(1)
            num2 = match.group(2)
            new_ref = f'![[{num1}-T{num2}.webp]]'
            changes.append(f"  - Leerzeichen entfernt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern2, replace2, content)
        
        # Fix 3: Unterstrich zu Bindestrich
        # ![[221_T01.webp]] → ![[221-T01.webp]]
        pattern3 = r'!\[\[(\d{3})_T(\d{2})\.webp\]\]'
        
        def replace3(match):
            num1 = match.group(1)
            num2 = match.group(2)
            new_ref = f'![[{num1}-T{num2}.webp]]'
            changes.append(f"  - Unterstrich zu Bindestrich: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern3, replace3, content)
        
        # Fix 4: Markdown-Links mit vollem Pfad
        # ![text](assets/GA223-.../assets/223-T01.webp) → ![text](assets/223-T01.webp)
        pattern4 = r'(!\[[^\]]*\]\()assets/GA\d{3}[a-z]?-[^/]+/assets/([^)]+)\)'
        
        def replace4(match):
            prefix = match.group(1)
            filename = match.group(2)
            new_ref = f'{prefix}assets/{filename})'
            changes.append(f"  - Markdown-Pfad bereinigt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern4, replace4, content)
        
        # Wende Änderungen an
        if changes and apply_changes:
            # Backup
            backup_path = filepath + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Speichere
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return len(changes), changes
        
    except Exception as e:
        print(f"  X Fehler bei {filepath}: {e}")
        return 0, []

def process_steiner_ga(steiner_ga_dir, apply_changes=False):
    """Verarbeitet alle GA-Ordner"""
    
    print("=" * 70)
    print("BILDPFAD-KORREKTUR (Advanced)")
    print("=" * 70)
    print(f"Modus: {'ANWENDEN' if apply_changes else 'DRY-RUN'}")
    print("=" * 70 + "\n")
    
    total_files = 0
    total_fixes = 0
    
    for folder_name in sorted(os.listdir(steiner_ga_dir)):
        folder_path = os.path.join(steiner_ga_dir, folder_name)
        
        if not os.path.isdir(folder_path) or not folder_name.startswith('GA'):
            continue
        
        # Finde Markdown-Dateien
        md_files = [f for f in os.listdir(folder_path) 
                   if f.endswith('.md') and '(' in f and ')' in f]
        
        if not md_files:
            continue
        
        folder_had_changes = False
        
        for md_file in md_files:
            md_path = os.path.join(folder_path, md_file)
            num_fixes, changes = fix_image_refs_in_file(md_path, apply_changes)
            
            if num_fixes > 0:
                if not folder_had_changes:
                    print(f"\n{folder_name}:")
                    folder_had_changes = True
                
                print(f"  {md_file}: {num_fixes} Korrekturen")
                for change in changes:
                    print(change)
                
                total_fixes += num_fixes
                total_files += 1
    
    print(f"\n{'='*70}")
    print("FERTIG")
    print(f"{'='*70}")
    print(f"Dateien mit Korrekturen: {total_files}")
    print(f"Gesamt-Korrekturen: {total_fixes}")
    
    if apply_changes and total_fixes > 0:
        print(f"\nBackups erstellt: *.backup")
        print("Änderungen wurden angewendet!")
    elif not apply_changes and total_fixes > 0:
        print(f"\nFühren Sie mit --apply aus, um anzuwenden:")
        print(f"  python fix_image_references_advanced.py --apply")
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    apply_changes = '--apply' in sys.argv
    
    process_steiner_ga(steiner_ga_dir, apply_changes)

