#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erhöht alle Seitenzahlen ab einer bestimmten Seitenzahl um +1.
"""

import re
import sys

def increment_page_numbers(file_path, start_page=18):
    """
    Erhöht alle Seitenmarker ab start_page (inklusive) um +1.
    
    Args:
        file_path: Pfad zur Markdown-Datei
        start_page: Ab dieser Seitenzahl (inklusive) werden alle Marker um +1 erhöht
    """
    try:
        # Datei lesen
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Finde alle Seitenmarker |N|
        def replace_marker(match):
            page_num = int(match.group(1))
            if page_num >= start_page:
                # Erhöhe um +1
                new_page_num = page_num + 1
                return f'|{new_page_num}|'
            else:
                # Unverändert lassen
                return match.group(0)
        
        # Ersetze alle Marker
        pattern = r'\|(\d+)\|'
        new_content = re.sub(pattern, replace_marker, content)
        
        # Zähle Änderungen
        old_markers = re.findall(pattern, content)
        new_markers = re.findall(pattern, new_content)
        
        print(f'\nGefundene Marker insgesamt: {len(old_markers)}')
        if old_markers:
            unique_old = sorted(set([int(m) for m in old_markers]))
            print(f'Einzigartige Seitenzahlen: {unique_old[:30]}')
            print(f'Maximale Seitenzahl: {max([int(m) for m in old_markers])}')
            print(f'Minimale Seitenzahl: {min([int(m) for m in old_markers])}')
        
        changed_count = 0
        changed_pages = []
        for old, new in zip(old_markers, new_markers):
            if int(old) >= start_page and int(old) != int(new):
                changed_count += 1
                changed_pages.append((int(old), int(new)))
        
        # Datei speichern
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f'Datei verarbeitet: {file_path}')
        print(f'Seitenzahlen ab {start_page} (inklusive) um +1 erhöht')
        print(f'Anzahl geänderter Marker: {changed_count}')
        
        # Zeige geänderte Seitenzahlen
        if changed_pages:
            print(f'\nGeänderte Seitenzahlen (erste 20):')
            for old, new in changed_pages[:20]:
                print(f'  {old} -> {new}')
            if len(changed_pages) > 20:
                print(f'  ... und {len(changed_pages) - 20} weitere')
        
        return True
        
    except FileNotFoundError:
        print(f'Fehler: Datei nicht gefunden: {file_path}')
        return False
    except Exception as e:
        print(f'Fehler beim Verarbeiten der Datei: {e}')
        return False

if __name__ == '__main__':
    file_path = r'Steiner_GA\GA002_Test\GA002_test_output_korrigiert.md'
    start_page = 18
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    if len(sys.argv) > 2:
        start_page = int(sys.argv[2])
    
    increment_page_numbers(file_path, start_page)

