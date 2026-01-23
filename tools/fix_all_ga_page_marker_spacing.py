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


def has_page_markers(md_file):
    """Prüft ob eine MD-Datei Seitenmarker enthält."""
    try:
        content = md_file.read_text(encoding='utf-8')
        return bool(re.search(r'\|<?\d+>?\|', content))
    except:
        return False


def process_file(md_file):
    """Verarbeitet eine einzelne MD-Datei."""
    try:
        content = md_file.read_text(encoding='utf-8')
        original_content = content
        
        # Korrigiere Marker
        fixed_content = fix_page_marker_spacing(content)
        
        if fixed_content != original_content:
            md_file.write_text(fixed_content, encoding='utf-8')
            
            # Zähle Änderungen
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
        return None, 0, str(e)


def find_ga_folders():
    """Findet alle GA-Ordner im Steiner_GA Verzeichnis."""
    if not STEINER_GA_DIR.exists():
        return []
    
    ga_folders = []
    for item in STEINER_GA_DIR.iterdir():
        if item.is_dir():
            # Prüfe ob es ein GA-Ordner ist (beginnt mit GA gefolgt von Zahlen)
            if re.match(r'^GA\d+', item.name, re.IGNORECASE):
                ga_folders.append(item)
    
    return sorted(ga_folders, key=lambda x: (
        int(re.search(r'GA(\d+)', x.name, re.IGNORECASE).group(1)) if re.search(r'GA(\d+)', x.name, re.IGNORECASE) else 9999,
        x.name
    ))


def process_ga_folder(ga_folder):
    """Verarbeitet alle MD-Dateien in einem GA-Ordner."""
    md_files = list(ga_folder.glob("*.md"))
    
    if not md_files:
        return None
    
    # Prüfe ob mindestens eine Datei Seitenmarker hat
    has_markers = any(has_page_markers(f) for f in md_files)
    if not has_markers:
        return None
    
    ga_name = ga_folder.name
    print(f"\n{ga_name}:")
    
    total_changed = 0
    total_files_changed = 0
    total_markers = 0
    errors = []
    
    for md_file in sorted(md_files):
        if not has_page_markers(md_file):
            continue
        
        result = process_file(md_file)
        if result[0] is True:
            changed, changes, markers = result
            total_changed += changes
            total_files_changed += 1
            total_markers += markers
            print(f"  [OK] {md_file.name}: {changes} Zeilen geaendert, {markers} Marker")
        elif result[0] is None:
            errors.append(f"{md_file.name}: {result[2]}")
        # result[0] == False bedeutet keine Änderungen nötig
    
    if errors:
        for error in errors:
            print(f"  [FEHLER] {error}")
    
    if total_files_changed > 0:
        print(f"  Zusammenfassung: {total_files_changed} Dateien geaendert, {total_changed} Zeilen, {total_markers} Marker")
        return True
    else:
        print(f"  [-] Keine Aenderungen noetig")
        return False


def main():
    """Hauptfunktion."""
    if not STEINER_GA_DIR.exists():
        print(f"FEHLER: Steiner_GA-Verzeichnis nicht gefunden: {STEINER_GA_DIR}")
        return
    
    print(f"\n{'='*60}")
    print(f"Korrigiere Seitenmarker-Formatierung für alle GA-Baende")
    print(f"{'='*60}")
    print(f"Verzeichnis: {STEINER_GA_DIR.name}\n")
    
    # Finde alle GA-Ordner
    ga_folders = find_ga_folders()
    
    if not ga_folders:
        print("Keine GA-Ordner gefunden!")
        return
    
    print(f"{len(ga_folders)} GA-Ordner gefunden\n")
    
    processed = 0
    changed = 0
    
    for ga_folder in ga_folders:
        result = process_ga_folder(ga_folder)
        if result:
            changed += 1
        processed += 1
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Verarbeitet: {processed} GA-Baende")
    print(f"  Geaendert: {changed} GA-Baende")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
