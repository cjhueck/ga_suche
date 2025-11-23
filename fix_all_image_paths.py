#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiert Bildplatzhalter und -pfade in ALLEN GA-Markdown-Dateien.

1. Entfernt < > und ' aus Bildpfaden: <'assets/...'> -> assets/...
2. Konvertiert Alt-Text von .jpeg/.jpg zu .png wenn Pfad bereits .png ist
"""

import re
from pathlib import Path
from typing import List, Tuple

def fix_image_paths_in_content(content: str) -> Tuple[str, List[str]]:
    """
    Korrigiert Bildpfade im Text.
    
    Returns:
        (korrigierter_content, liste_der_änderungen)
    """
    changes = []
    original_content = content
    
    # Fix 1: Entferne < > und ' aus Bildpfaden
    # ![alt](<'assets/...'>) -> ![alt](assets/...)
    pattern1 = r'!\[([^\]]+)\]\(<[\'"]?([^>\'"]+)[\'"]?>\)'
    
    def remove_brackets(match):
        alt = match.group(1)
        path = match.group(2)
        changes.append(f"  - Pfad-Brackets entfernt: {alt}")
        return f'![{alt}]({path})'
    
    content = re.sub(pattern1, remove_brackets, content)
    
    # Fix 2: Alt-Text mit .jpeg/.jpg, aber Pfad mit .png
    # ![img-0.jpeg](assets/...img-0.png) -> ![img-0.png](assets/...img-0.png)
    pattern2 = r'!\[([^\]]*\.jpe?g)\](\([^)]*\.png[^)]*\))'
    
    def convert_alt_jpeg_to_png(match):
        alt_text = match.group(1)
        path_part = match.group(2)
        alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
        changes.append(f"  - Alt-Text korrigiert: {alt_text} -> {alt_text_converted}")
        return f'![{alt_text_converted}]{path_part}'
    
    content = re.sub(pattern2, convert_alt_jpeg_to_png, content)
    
    return content, changes


def fix_image_paths_in_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    Korrigiert Bildpfade in einer einzelnen Datei.
    
    Args:
        filepath: Pfad zur Markdown-Datei
        dry_run: Wenn True, werden keine Änderungen gespeichert
    
    Returns:
        True wenn Änderungen gefunden wurden, sonst False
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content, changes = fix_image_paths_in_content(content)
        
        if content != original_content:
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] {filepath.name}: {len(changes)} Änderungen")
                if len(changes) <= 5:
                    for change in changes:
                        print(change)
            else:
                print(f"[DRY RUN] {filepath.name}: {len(changes)} Änderungen würden durchgeführt")
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
    
    # Standardverzeichnis: Steiner_GA
    base_dir = Path('Steiner_GA')
    
    # Kommandozeilenargumente
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
Korrigiert Bildpfade in ALLEN GA-Markdown-Dateien.

Verwendung:
  python fix_all_image_paths.py [OPTIONEN]

Optionen:
  --dry-run, -n    Zeigt Änderungen an, ohne sie zu speichern
  --help, -h       Zeigt diese Hilfe an

Beispiel:
  python fix_all_image_paths.py --dry-run
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
    total_changes = 0
    
    for ga_dir in ga_dirs:
        # Finde alle Markdown-Dateien
        md_files = list(ga_dir.glob('*.md'))
        
        if not md_files:
            continue
        
        ga_changed = 0
        ga_changes = 0
        
        for md_file in md_files:
            total_files += 1
            if fix_image_paths_in_file(md_file, dry_run=dry_run):
                total_changed += 1
                ga_changed += 1
                # Zähle Änderungen (ungefähr)
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    _, changes = fix_image_paths_in_content(content)
                    ga_changes += len(changes)
        
        if ga_changed > 0:
            print(f"  {ga_dir.name}: {ga_changed} Dateien, {ga_changes} Änderungen")
        
        total_changes += ga_changes
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Verarbeitete Dateien: {total_files}")
    print(f"  Geänderte Dateien: {total_changed}")
    print(f"  Gesamt-Änderungen: {total_changes}")
    if dry_run:
        print(f"\nHinweis: Keine Änderungen wurden gespeichert (Dry Run Modus)")
        print(f"Führen Sie das Skript ohne --dry-run aus, um Änderungen zu speichern.")


if __name__ == '__main__':
    main()
