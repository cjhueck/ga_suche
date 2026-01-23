#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiert die Leerzeichen-Formatierung von Seitenmarkern für alle GA-Bände.

Regeln:
- SM zwischen Wörtern: Leerzeichen vor und nach dem SM
- SM am Absatzbeginn: Nur Leerzeichen nach dem SM
- SM innerhalb eines Wortes: Kein Leerzeichen vor oder nach dem SM
"""

import re
import sys
import io
from pathlib import Path

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = SCRIPT_DIR / "Steiner_GA"


def is_letter(char):
    """Prüft ob ein Zeichen ein Buchstabe ist (inkl. Umlaute)."""
    return char.isalpha() if char else False


def fix_page_marker_spacing(text):
    """
    Korrigiert die Leerzeichen-Formatierung von Seitenmarker.
    
    Regeln:
    1. SM am Zeilenanfang (nach \n oder am Textanfang): Leerzeichen nach dem SM
    2. SM innerhalb eines Wortes (Buchstabe|XX|Buchstabe): Kein Leerzeichen
    3. SM zwischen Wörtern: Leerzeichen vor und nach dem SM
    """
    # Pattern für Seitenmarker: |XX| oder |<XX>|
    marker_pattern = r'\|<?\d+>?\|'
    
    result = text
    # Finde alle Marker mit ihren Positionen
    matches = list(re.finditer(marker_pattern, result))
    
    # Von hinten nach vorne verarbeiten, damit Positionen stimmen bleiben
    for match in reversed(matches):
        marker = match.group(0)
        start_pos = match.start()
        end_pos = match.end()
        
        # Kontext prüfen
        char_before = result[start_pos - 1] if start_pos > 0 else ''
        char_after = result[end_pos] if end_pos < len(result) else ''
        
        # Prüfe ob am Zeilenanfang (nach \n oder am Textanfang)
        is_line_start = (start_pos == 0 or 
                        result[start_pos - 1] == '\n' or
                        (start_pos > 1 and result[start_pos - 2:start_pos] == '\n\n'))
        
        # Prüfe ob innerhalb eines Wortes
        is_inside_word = is_letter(char_before) and is_letter(char_after)
        
        # Entferne vorhandene Leerzeichen um den Marker
        # Zuerst Leerzeichen nach dem Marker entfernen (falls nötig)
        if end_pos < len(result) and result[end_pos] == ' ':
            if is_inside_word:
                # Innerhalb eines Wortes: Leerzeichen entfernen
                result = result[:end_pos] + result[end_pos + 1:]
                end_pos -= 1
        
        # Dann Leerzeichen vor dem Marker entfernen (falls nötig)
        if start_pos > 0 and result[start_pos - 1] == ' ':
            if is_inside_word:
                # Innerhalb eines Wortes: Leerzeichen entfernen
                result = result[:start_pos - 1] + result[start_pos:]
                start_pos -= 1
                end_pos -= 1
        
        # Jetzt die korrekte Formatierung hinzufügen
        if is_inside_word:
            # Innerhalb eines Wortes: Kein Leerzeichen (bereits entfernt)
            pass
        elif is_line_start:
            # Am Zeilenanfang: Leerzeichen nach dem SM
            if end_pos >= len(result) or result[end_pos] != ' ':
                result = result[:end_pos] + ' ' + result[end_pos:]
        else:
            # Zwischen Wörtern: Leerzeichen vor und nach
            # Leerzeichen vor
            if start_pos == 0 or result[start_pos - 1] != ' ':
                result = result[:start_pos] + ' ' + result[start_pos:]
                start_pos += 1
                end_pos += 1
            # Leerzeichen nach
            if end_pos >= len(result) or result[end_pos] != ' ':
                result = result[:end_pos] + ' ' + result[end_pos:]
    
    return result


def has_page_markers(content):
    """Prüft ob der Text Seitenmarker enthält."""
    return bool(re.search(r'\|<?\d+>?\|', content))


def process_file(md_file):
    """Verarbeitet eine einzelne MD-Datei."""
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Prüfe ob Datei Seitenmarker hat
        if not has_page_markers(content):
            return False, 0, 0
        
        original_content = content
        
        # Korrigiere Marker
        fixed_content = fix_page_marker_spacing(content)
        
        if fixed_content != original_content:
            md_file.write_text(fixed_content, encoding='utf-8')
            
            # Zähle Marker
            fixed_markers = len(re.findall(r'\|<?\d+>?\|', fixed_content))
            
            # Zähle tatsächliche Formatierungsänderungen
            changes = 0
            for orig_line, fixed_line in zip(original_content.split('\n'), fixed_content.split('\n')):
                if orig_line != fixed_line:
                    changes += 1
            
            return True, changes, fixed_markers
        else:
            return False, 0, 0
            
    except Exception as e:
        print(f"      [FEHLER] {e}")
        return False, 0, 0


def process_ga_folder(ga_folder):
    """Verarbeitet alle MD-Dateien in einem GA-Ordner."""
    ga_name = ga_folder.name
    
    # Finde alle MD-Dateien
    md_files = list(ga_folder.glob("*.md"))
    
    if not md_files:
        return None
    
    # Prüfe ob mindestens eine Datei Seitenmarker hat
    has_markers = False
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            if has_page_markers(content):
                has_markers = True
                break
        except:
            continue
    
    if not has_markers:
        return None
    
    print(f"  {ga_name}")
    
    total_changed = 0
    total_files_changed = 0
    total_markers = 0
    
    for md_file in sorted(md_files):
        changed, changes, markers = process_file(md_file)
        if changed:
            total_files_changed += 1
            total_changed += changes
            total_markers += markers
    
    if total_files_changed > 0:
        print(f"    -> {total_files_changed} Dateien geaendert, {total_changed} Zeilen, {total_markers} Marker")
        return {
            'ga': ga_name,
            'files_changed': total_files_changed,
            'lines_changed': total_changed,
            'markers': total_markers
        }
    else:
        print(f"    -> Bereits korrekt formatiert")
        return {
            'ga': ga_name,
            'files_changed': 0,
            'lines_changed': 0,
            'markers': 0
        }


def main():
    """Hauptfunktion."""
    if not STEINER_GA_DIR.exists():
        print(f"FEHLER: Steiner_GA-Verzeichnis nicht gefunden: {STEINER_GA_DIR}")
        return
    
    print(f"\n{'='*70}")
    print(f"Korrigiere Seitenmarker-Formatierung für alle GA-Baende")
    print(f"{'='*70}")
    print(f"Verzeichnis: {STEINER_GA_DIR}\n")
    
    # Finde alle GA-Ordner (beginnen mit GA)
    ga_folders = [f for f in STEINER_GA_DIR.iterdir() 
                  if f.is_dir() and (f.name.startswith('GA') or re.match(r'GA\d+', f.name))]
    
    if not ga_folders:
        print("Keine GA-Ordner gefunden!")
        return
    
    print(f"{len(ga_folders)} GA-Ordner gefunden\n")
    
    results = []
    processed = 0
    
    # Sortiere GA-Ordner nach Nummer
    def sort_key(folder):
        match = re.search(r'GA(\d+)', folder.name, re.IGNORECASE)
        if match:
            return (int(match.group(1)), folder.name)
        return (9999, folder.name)
    
    for ga_folder in sorted(ga_folders, key=sort_key):
        result = process_ga_folder(ga_folder)
        if result:
            results.append(result)
        processed += 1
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print(f"Zusammenfassung:")
    print(f"{'='*70}")
    
    total_gas_with_changes = sum(1 for r in results if r['files_changed'] > 0)
    total_gas_already_correct = sum(1 for r in results if r['files_changed'] == 0)
    total_files_changed = sum(r['files_changed'] for r in results)
    total_lines_changed = sum(r['lines_changed'] for r in results)
    total_markers = sum(r['markers'] for r in results)
    
    print(f"  GA-Baende verarbeitet: {len(results)}")
    print(f"  GA-Baende mit Aenderungen: {total_gas_with_changes}")
    print(f"  GA-Baende bereits korrekt: {total_gas_already_correct}")
    print(f"  Dateien geaendert: {total_files_changed}")
    print(f"  Zeilen geaendert: {total_lines_changed}")
    print(f"  Marker insgesamt: {total_markers}")
    print(f"{'='*70}\n")
    
    # Zeige GA-Bände mit Änderungen
    if total_gas_with_changes > 0:
        print("GA-Baende mit Aenderungen:")
        for r in sorted(results, key=lambda x: x['ga']):
            if r['files_changed'] > 0:
                print(f"  {r['ga']}: {r['files_changed']} Dateien, {r['lines_changed']} Zeilen")


if __name__ == "__main__":
    main()
