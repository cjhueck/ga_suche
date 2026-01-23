#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiert die Leerzeichen-Formatierung von Seitenmarkern in GA117.

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
GA117_DIR = STEINER_GA_DIR / "GA117-Die tieferen Geheimnisse des Menschheitswerdens im Lichte der Evangelien"


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


def process_file(md_file):
    """Verarbeitet eine einzelne MD-Datei."""
    print(f"  Verarbeite: {md_file.name}")
    
    try:
        content = md_file.read_text(encoding='utf-8')
        original_content = content
        
        # Korrigiere Marker
        fixed_content = fix_page_marker_spacing(content)
        
        if fixed_content != original_content:
            md_file.write_text(fixed_content, encoding='utf-8')
            
            # Zähle Änderungen
            original_markers = len(re.findall(r'\|<?\d+>?\|', original_content))
            fixed_markers = len(re.findall(r'\|<?\d+>?\|', fixed_content))
            
            # Zähle tatsächliche Formatierungsänderungen
            changes = 0
            for orig_line, fixed_line in zip(original_content.split('\n'), fixed_content.split('\n')):
                if orig_line != fixed_line:
                    changes += 1
            
            print(f"    [OK] {changes} Zeilen geaendert, {fixed_markers} Marker")
            return True
        else:
            print(f"    [-] Keine Aenderungen noetig")
            return False
            
    except Exception as e:
        print(f"    [FEHLER] {e}")
        return False


def main():
    """Hauptfunktion."""
    if not GA117_DIR.exists():
        print(f"FEHLER: GA117-Verzeichnis nicht gefunden: {GA117_DIR}")
        return
    
    print(f"\n{'='*60}")
    print(f"Korrigiere Seitenmarker-Formatierung für GA117")
    print(f"{'='*60}")
    print(f"Verzeichnis: {GA117_DIR.name}\n")
    
    # Finde alle MD-Dateien
    md_files = list(GA117_DIR.glob("*.md"))
    
    if not md_files:
        print("Keine MD-Dateien gefunden!")
        return
    
    print(f"{len(md_files)} MD-Dateien gefunden\n")
    
    processed = 0
    changed = 0
    
    for md_file in sorted(md_files):
        if process_file(md_file):
            changed += 1
        processed += 1
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Verarbeitet: {processed} Dateien")
    print(f"  Geändert: {changed} Dateien")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
