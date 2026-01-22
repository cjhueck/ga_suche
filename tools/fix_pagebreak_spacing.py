#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_pagebreak_spacing.py
========================
Korrigiert Leerzeichen bei Seitenmarkern:
- Marker zwischen Wörtern: mit Leerzeichen (word |42| word)
- Marker innerhalb Wort-Trennung: ohne Leerzeichen (dar|42|stellt)
- Marker nie vor/in Überschriften
"""

import re
from pathlib import Path
from typing import Tuple

PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"


def is_word_char(char: str) -> bool:
    """Prüft ob ein Zeichen ein Buchstabe ist."""
    return char.isalpha()


def is_heading(line: str) -> bool:
    """Prüft ob eine Zeile eine Markdown-Überschrift ist"""
    stripped = line.strip()
    return stripped.startswith('#') and len(stripped) > 1 and stripped[1] in '# '


def fix_spacing_around_markers(content: str) -> Tuple[str, int]:
    """
    Korrigiert Leerzeichen um Marker herum.
    
    Returns: (korrigierter_content, anzahl_änderungen)
    """
    changes = 0
    
    # Finde alle Marker
    pattern = r'\|(\d+)\|'
    
    def replace_marker(match):
        nonlocal changes
        marker = match.group(0)
        pos = match.start()
        
        # Zeichen vor und nach dem Marker
        char_before = content[pos-1] if pos > 0 else ' '
        char_after = content[pos+len(marker)] if pos+len(marker) < len(content) else ' '
        
        # Prüfe ob Marker innerhalb eines Wortes (Silbentrennung)
        inside_word = is_word_char(char_before) and is_word_char(char_after)
        
        if inside_word:
            # Silbentrennung - Marker ohne Leerzeichen
            # Prüfe ob bereits korrekt (keine Leerzeichen)
            if pos > 0 and content[pos-1] == ' ':
                changes += 1
                return marker  # Entferne Leerzeichen davor
            if pos+len(marker) < len(content) and content[pos+len(marker)] == ' ':
                changes += 1
                return marker  # Entferne Leerzeichen danach
            return marker  # Bereits korrekt
        else:
            # Marker zwischen Wörtern - mit Leerzeichen
            needs_space_before = is_word_char(char_before) and char_before != ' '
            needs_space_after = is_word_char(char_after) and char_after != ' '
            
            prefix = ' ' if needs_space_before else ''
            suffix = ' ' if needs_space_after else ''
            
            if needs_space_before or needs_space_after:
                changes += 1
                return prefix + marker + suffix
            return marker
    
    # Ersetze alle Marker
    content = re.sub(pattern, replace_marker, content)
    
    return content, changes


def move_markers_around_headings(content: str) -> Tuple[str, int]:
    """
    Verschiebt Marker, die vor/in Überschriften stehen.
    
    Returns: (korrigierter_content, anzahl_änderungen)
    """
    lines = content.split('\n')
    changes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Regel 1: Marker am Anfang einer Überschriftszeile
        if is_heading(line):
            match = re.match(r'^(\s*)(\|(\d+)\|)\s*(#+\s+.*)$', line)
            if match:
                indent = match.group(1)
                marker = match.group(2)
                heading = match.group(4)
                lines[i] = indent + heading
                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Regel 2: Marker INNERHALB einer Überschrift
        if is_heading(line):
            match = re.match(r'^(\s*)(#+)\s*(\|(\d+)\|)\s*(.*)$', line)
            if match:
                indent = match.group(1)
                hashes = match.group(2)
                marker = match.group(3)
                title = match.group(5)
                lines[i] = indent + hashes + ' ' + title
                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        # Regel 3: Marker am Ende einer Zeile, gefolgt von Überschrift
        marker_at_end = re.search(r'\|(\d+)\|\s*$', line)
        if marker_at_end and not is_heading(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines) and is_heading(lines[j]):
                marker = marker_at_end.group(0).strip()
                lines[i] = re.sub(r'\s*\|(\d+)\|\s*$', '', line)
                
                k = j + 1
                while k < len(lines):
                    content_line = lines[k]
                    if content_line.strip() and not is_heading(content_line):
                        lines[k] = marker + ' ' + content_line.lstrip()
                        changes += 1
                        break
                    k += 1
        
        i += 1
    
    return '\n'.join(lines), changes


def fix_file(md_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """
    Korrigiert Leerzeichen und Überschriften in einer Datei.
    
    Returns: (spacing_changes, heading_changes)
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Korrigiere Leerzeichen
    content, spacing_changes = fix_spacing_around_markers(content)
    
    # 2. Verschiebe Marker um Überschriften
    content, heading_changes = move_markers_around_headings(content)
    
    if not dry_run and (spacing_changes > 0 or heading_changes > 0):
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return spacing_changes, heading_changes


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Korrigiert Leerzeichen und Überschriften bei Seitenmarkern'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 116, GA116)')
    parser.add_argument('--dry-run', action='store_true', help='Nur simulieren')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mehr Ausgabe')
    
    args = parser.parse_args()
    
    # Normalisiere GA
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = match.group(1).zfill(3)
    ga_norm = f"GA{ga_num}"
    
    print(f"\n{'='*60}")
    print(f"Korrigiere Leerzeichen und Überschriften für {ga_norm}")
    print(f"{'='*60}")
    
    # Finde MD-Dateien
    md_folder = None
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            md_folder = folder
            break
    
    if not md_folder:
        print(f"FEHLER: Kein MD-Ordner gefunden")
        return
    
    md_files = list(md_folder.glob("*.md"))
    if not md_files:
        print(f"FEHLER: Keine MD-Dateien gefunden")
        return
    
    print(f"MD-Dateien: {len(md_files)} gefunden")
    print("\nKorrigiere..." + (" (Dry-Run)" if args.dry_run else ""))
    
    total_spacing = 0
    total_headings = 0
    
    for md_path in sorted(md_files):
        spacing, headings = fix_file(md_path, args.dry_run)
        total_spacing += spacing
        total_headings += headings
        
        if spacing > 0 or headings > 0 or args.verbose:
            print(f"  {md_path.name}: {spacing} Leerzeichen, {headings} Überschriften")
    
    print(f"\nErgebnis:")
    print(f"  Leerzeichen korrigiert: {total_spacing}")
    print(f"  Marker bei Überschriften verschoben: {total_headings}")
    
    if args.dry_run:
        print("\n(Dry-Run - keine Änderungen gespeichert)")
    
    print(f"\n{'='*60}")
    print("FERTIG!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
