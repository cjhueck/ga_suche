#!/usr/bin/env python3
"""
Text Cleanup Script für Steiner GA Markdown-Dateien

Führt folgende Bereinigungen durch:
1. Entfernt Absatz-IDs (^xxxxx) hinter H1, H2, H3 Überschriften
2. Entfernt Seitenumbrüche (---) inklusive der vorherigen Absatz-ID und der umgebenden Leerzeilen
3. Fügt Zeilenumbrüche vor Überschriften ein, die nach der Bereinigung inline stehen

Verwendung:
    python text_cleanup.py <datei.md>
    python text_cleanup.py <datei.md> --dry-run  (zeigt nur Änderungen an)
"""

import re
import sys
import argparse
from pathlib import Path


def remove_heading_ids(content: str) -> tuple[str, int]:
    """
    Entfernt Absatz-IDs hinter H1, H2, H3 Überschriften.
    
    Beispiel:
        # ERSTER VORTRAG, Stuttgart, 16. Juni 1921 ^4mm8mu
        wird zu:
        # ERSTER VORTRAG, Stuttgart, 16. Juni 1921
    """
    pattern = r'^(#{1,3} .+?) \^[a-z0-9]+$'
    
    # Zähle Treffer
    matches = re.findall(pattern, content, re.MULTILINE)
    count = len(matches)
    
    # Ersetze
    new_content = re.sub(pattern, r'\1', content, flags=re.MULTILINE)
    
    return new_content, count


def remove_page_breaks(content: str) -> tuple[str, int]:
    """
    Entfernt Seitenumbrüche (---) inklusive der vorherigen Absatz-ID und Leerzeilen.
    
    Beispiel:
        der ^tdhrkd
        
        ---
        
        Natur sind.
        
        wird zu:
        der Natur sind.
    """
    pattern = r' \^[a-z0-9]+\n\n---\n\n'
    
    # Zähle Treffer
    count = len(re.findall(pattern, content))
    
    # Ersetze mit einem Leerzeichen
    new_content = re.sub(pattern, ' ', content)
    
    return new_content, count


def fix_inline_headings(content: str) -> tuple[str, int]:
    """
    Fügt Zeilenumbrüche vor Überschriften ein, die nach Seitenumbruch-Entfernung
    am Ende einer Zeile stehen.
    
    Beispiel:
        ...wiederum sehen. # ZWEITER VORTRAG, Bern, 28. Juni 1921
        
        wird zu:
        ...wiederum sehen.
        
        # ZWEITER VORTRAG, Bern, 28. Juni 1921
    """
    # Muster: Zeichen (kein Newline) + Leerzeichen + # + Großbuchstabe/Umlaut
    pattern = r'([^\n]) (# [A-Z\u00C4\u00D6\u00DC])'
    
    # Zähle Treffer
    count = len(re.findall(pattern, content))
    
    # Ersetze mit Zeilenumbrüchen
    new_content = re.sub(pattern, r'\1\n\n\2', content)
    
    return new_content, count


def cleanup_text(content: str) -> tuple[str, dict]:
    """
    Führt alle Bereinigungen durch.
    
    Returns:
        tuple: (bereinigter_text, statistik_dict)
    """
    stats = {}
    
    # 1. Überschriften-IDs entfernen
    content, count = remove_heading_ids(content)
    stats['heading_ids_removed'] = count
    
    # 2. Seitenumbrüche entfernen
    content, count = remove_page_breaks(content)
    stats['page_breaks_removed'] = count
    
    # 3. Zeilenumbrüche vor Überschriften einfügen (nach Seitenumbruch-Entfernung)
    content, count = fix_inline_headings(content)
    stats['inline_headings_fixed'] = count
    
    return content, stats


def main():
    parser = argparse.ArgumentParser(
        description='Bereinigt Steiner GA Markdown-Dateien'
    )
    parser.add_argument(
        'file',
        type=Path,
        help='Pfad zur Markdown-Datei'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Zeigt nur an, was geändert würde, ohne die Datei zu speichern'
    )
    
    args = parser.parse_args()
    
    if not args.file.exists():
        print(f'Fehler: Datei nicht gefunden: {args.file}')
        sys.exit(1)
    
    # Datei lesen
    content = args.file.read_text(encoding='utf-8')
    
    # Bereinigen
    new_content, stats = cleanup_text(content)
    
    # Statistik ausgeben
    print(f'Datei: {args.file}')
    print(f'  Überschriften-IDs entfernt: {stats["heading_ids_removed"]}')
    print(f'  Seitenumbrüche entfernt: {stats["page_breaks_removed"]}')
    print(f'  Inline-Überschriften korrigiert: {stats["inline_headings_fixed"]}')
    
    total_changes = (stats['heading_ids_removed'] + 
                     stats['page_breaks_removed'] + 
                     stats['inline_headings_fixed'])
    
    if args.dry_run:
        print('\n[Dry-Run] Keine Änderungen gespeichert.')
    else:
        if total_changes > 0:
            args.file.write_text(new_content, encoding='utf-8')
            print('\nÄnderungen gespeichert.')
        else:
            print('\nKeine Änderungen notwendig.')


if __name__ == '__main__':
    main()
