#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiert Bildplatzhalter in ALLEN GA-Markdown-Dateien.

1. Korrigiert Alt-Text: img-X.jpeg -> img-X.png
2. Bereinigt Pfade: <'assets/...'> -> assets/...
3. Benennt Dateien um: .jpeg -> .png (falls Dateien existieren)
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

def fix_image_placeholders_in_content(content: str) -> Tuple[str, List[str]]:
    """Korrigiert Bildplatzhalter im Text."""
    changes = []
    original_content = content
    
    # Pattern 1: Alt-Text mit .jpeg/.jpg, aber Pfad mit .png
    pattern1 = r'!\[([^\]]*\.jpe?g)\](\([^)]*\.png[^)]*\))'
    
    def convert_alt_jpeg_to_png(match):
        alt_text = match.group(1)
        path_part = match.group(2)
        alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
        changes.append(f"  - Alt-Text korrigiert: {alt_text} -> {alt_text_converted}")
        return f'![{alt_text_converted}]{path_part}'
    
    content = re.sub(pattern1, convert_alt_jpeg_to_png, content)
    
    # Pattern 2: Pfade mit < > und ' bereinigen
    # ![alt](<'assets/...'>) -> ![alt](assets/...)
    pattern2 = r'!\[([^\]]+)\]\(<[\'"]?([^>\'"]+)[\'"]?>\)'
    
    def clean_path(match):
        alt = match.group(1)
        path = match.group(2)
        changes.append(f"  - Pfad bereinigt: <'{path}'> -> {path}")
        return f'![{alt}]({path})'
    
    content = re.sub(pattern2, clean_path, content)
    
    return content, changes


def rename_image_files(assets_dir: Path) -> int:
    """Benennt .jpeg Dateien zu .png um (falls entsprechende .png nicht existiert)."""
    if not assets_dir.exists():
        return 0
    
    renamed = 0
    
    # Finde alle .jpeg Dateien
    jpeg_files = list(assets_dir.glob('*.jpeg')) + list(assets_dir.glob('*.jpg'))
    
    for jpeg_file in jpeg_files:
        png_file = jpeg_file.with_suffix('.png')
        
        # Überspringe wenn .png bereits existiert
        if png_file.exists():
            continue
        
        try:
            jpeg_file.rename(png_file)
            renamed += 1
        except Exception as e:
            print(f"    [FEHLER] Konnte {jpeg_file.name} nicht umbenennen: {e}")
    
    return renamed


def fix_image_placeholders_in_file(filepath: Path, dry_run: bool = False) -> bool:
    """Korrigiert Bildplatzhalter in einer einzelnen Datei."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content, changes = fix_image_placeholders_in_content(content)
        
        if content != original_content:
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] {filepath.name}: {len(changes)} Änderungen")
                for change in changes:
                    print(change)
            else:
                print(f"[DRY RUN] {filepath.name}: {len(changes)} Änderungen würden durchgeführt")
                for change in changes:
                    print(change)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[FEHLER] {filepath.name}: {e}")
        return False


def find_ga_directories(base_dir: Path) -> List[Path]:
    """Findet alle GA-Verzeichnisse."""
    ga_dirs = []
    if not base_dir.exists():
        return ga_dirs
    
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith('GA'):
            ga_dirs.append(item)
    
    return sorted(ga_dirs)


def main():
    """Hauptfunktion."""
    import sys
    
    base_dir = Path('Steiner_GA')
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
Korrigiert Bildplatzhalter in ALLEN GA-Markdown-Dateien.

Verwendung:
  python fix_all_image_placeholders.py [OPTIONEN]

Optionen:
  --dry-run, -n    Zeigt Änderungen an, ohne sie zu speichern
  --help, -h       Zeigt diese Hilfe an

Beispiel:
  python fix_all_image_placeholders.py --dry-run
        """)
        return
    
    if not base_dir.exists():
        print(f"Fehler: Verzeichnis '{base_dir}' nicht gefunden!")
        return
    
    print(f"Suche nach GA-Verzeichnissen in '{base_dir}'...")
    ga_dirs = find_ga_directories(base_dir)
    
    if not ga_dirs:
        print("Keine GA-Verzeichnisse gefunden!")
        return
    
    print(f"Gefunden: {len(ga_dirs)} GA-Verzeichnisse\n")
    
    if dry_run:
        print("=== DRY RUN MODUS - Keine Änderungen werden gespeichert ===\n")
    
    total_files = 0
    total_changed = 0
    total_renamed = 0
    
    for ga_dir in ga_dirs:
        print(f"\nVerarbeite {ga_dir.name}...")
        
        # Benenne Bilddateien um (falls vorhanden)
        assets_dir = ga_dir / 'assets'
        if assets_dir.exists() and not dry_run:
            renamed = rename_image_files(assets_dir)
            if renamed > 0:
                print(f"  {renamed} Bilddatei(en) umbenannt (.jpeg -> .png)")
                total_renamed += renamed
        
        # Finde alle Markdown-Dateien
        md_files = list(ga_dir.glob('*.md'))
        
        if not md_files:
            print(f"  Keine Markdown-Dateien gefunden")
            continue
        
        for md_file in md_files:
            total_files += 1
            if fix_image_placeholders_in_file(md_file, dry_run=dry_run):
                total_changed += 1
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Verarbeitete Dateien: {total_files}")
    print(f"  Geänderte Dateien: {total_changed}")
    print(f"  Umbenannte Bilddateien: {total_renamed}")
    if dry_run:
        print(f"\nHinweis: Keine Änderungen wurden gespeichert (Dry Run Modus)")
        print(f"Führen Sie das Skript ohne --dry-run aus, um Änderungen zu speichern.")


if __name__ == '__main__':
    main()

