#!/usr/bin/env python3
"""
Bereinigt Gemini-generierte Markdown-Dateien:
- Entfernt Block-IDs (^xyz am Zeilenende)
- Entfernt Zeilenumbrüche die keine echten Absatzumbrüche sind
- Behält echte Absatzumbrüche (leere Zeilen, Seitenmarker, Gedichte)
"""

import re
import sys
from pathlib import Path


def is_poem_line(line: str) -> bool:
    """
    Prüft ob eine Zeile Teil eines Gedichts sein könnte.
    Gedichte haben typischerweise kurze Zeilen (< 70 Zeichen).
    """
    stripped = line.strip()
    # Leere Zeilen sind keine Gedichtzeilen
    if not stripped:
        return False
    # Zu lange Zeilen sind keine Gedichtzeilen
    if len(stripped) > 70:
        return False
    # Seitenmarker sind keine Gedichtzeilen
    if re.match(r'^\|\d+\|', stripped):
        return False
    return True


def detect_poem(lines: list, start_idx: int) -> int:
    """
    Erkennt ob ab start_idx ein Gedicht beginnt.
    Gibt die Anzahl der Gedichtzeilen zurück (0 wenn kein Gedicht).
    
    Heuristik: Mindestens 3 aufeinanderfolgende kurze Zeilen (< 70 Zeichen)
    die mit Großbuchstaben beginnen.
    """
    if start_idx >= len(lines):
        return 0
    
    # Prüfe die nächsten Zeilen
    poem_lines = 0
    consecutive_short = 0
    
    for i in range(start_idx, min(start_idx + 10, len(lines))):
        line = lines[i].strip()
        
        # Leere Zeile = Gedichtende
        if not line:
            if poem_lines >= 3:
                return poem_lines
            return 0
        
        # Seitenmarker = Gedichtende
        if re.match(r'^\|\d+\|', line):
            if poem_lines >= 3:
                return poem_lines
            return 0
        
        # Entferne Block-ID für Prüfung
        line_clean = re.sub(r'\s+\^[a-z0-9]+\s*$', '', line)
        
        # Prüfe ob Zeile Gedicht-Charakter hat
        if is_poem_line(line_clean):
            # Beginnt mit Großbuchstabe?
            if line_clean and line_clean[0].isupper():
                consecutive_short += 1
                poem_lines += 1
            else:
                # Wenn wir schon Gedichtzeilen haben, könnte es weitergehen
                if poem_lines >= 3:
                    consecutive_short += 1
                    poem_lines += 1
                else:
                    # Zu früh für Gedicht
                    return 0
        else:
            # Zu lange Zeile = kein Gedicht
            if poem_lines >= 3:
                # Gedicht endet hier
                return poem_lines
            return 0
    
    # Wenn wir am Ende sind und mindestens 3 Zeilen haben
    if poem_lines >= 3:
        return poem_lines
    
    return 0


def clean_gemini_md(content: str) -> str:
    """
    Bereinigt Gemini-generierte Markdown-Dateien.
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Leere Zeile = echter Absatzumbruch
        if not line.strip():
            result.append('')
            i += 1
            continue
        
        # Entferne Block-IDs (^xyz am Zeilenende)
        line_clean = re.sub(r'\s+\^[a-z0-9]+\s*$', '', line)
        
        # Seitenmarker auf eigener Zeile (|XX|)
        if re.match(r'^\|\d+\|\s*$', line_clean.strip()):
            result.append(line_clean.strip())
            i += 1
            continue
        
        # Prüfe ob hier ein Gedicht beginnt
        poem_length = detect_poem(lines, i)
        
        if poem_length > 0:
            # Gedicht: Behalte Zeilenumbrüche
            poem_lines = []
            for j in range(i, min(i + poem_length, len(lines))):
                poem_line = lines[j]
                # Entferne Block-IDs
                poem_line = re.sub(r'\s+\^[a-z0-9]+\s*$', '', poem_line)
                if poem_line.strip():
                    poem_lines.append(poem_line.strip())
            
            # Füge Gedicht hinzu (jede Zeile einzeln)
            if poem_lines:
                result.extend(poem_lines)
                result.append('')  # Leere Zeile nach Gedicht
            
            i += poem_length
            continue
        
        # Normaler Absatz: Sammle Zeilen bis zum nächsten Absatzumbruch
        current_paragraph = []
        
        while i < len(lines):
            line = lines[i]
            
            # Leere Zeile = Absatzende
            if not line.strip():
                break
            
            # Entferne Block-IDs
            line_clean = re.sub(r'\s+\^[a-z0-9]+\s*$', '', line)
            
            # Seitenmarker auf eigener Zeile = Absatzende
            if re.match(r'^\|\d+\|\s*$', line_clean.strip()):
                break
            
            # Prüfe ob hier ein Gedicht beginnt (könnte mitten im Absatz sein)
            poem_check = detect_poem(lines, i)
            if poem_check > 0:
                break
            
            # Füge Zeile zum aktuellen Absatz hinzu
            if line_clean.strip():
                current_paragraph.append(line_clean.strip())
            
            i += 1
        
        # Verbinde Zeilen des Absatzes mit Leerzeichen
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            # Bereinige mehrfache Leerzeichen
            paragraph_text = re.sub(r'  +', ' ', paragraph_text)
            result.append(paragraph_text)
        
        # Wenn wir wegen leerer Zeile gestoppt haben, füge sie hinzu
        if i < len(lines) and not lines[i].strip():
            result.append('')
            i += 1
    
    # Verbinde alle Zeilen
    cleaned = '\n'.join(result)
    
    # Finale Bereinigung:
    # - Entferne mehrfache Leerzeilen (max 2 aufeinanderfolgend)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # - Bereinige Leerzeichen vor Satzzeichen (aber nicht in Gedichten)
    #   Gedichte haben bereits ihre eigenen Zeilenumbrüche
    lines_final = cleaned.split('\n')
    result_final = []
    in_poem = False
    
    for line in lines_final:
        if not line.strip():
            in_poem = False
            result_final.append('')
        elif is_poem_line(line) and len(result_final) > 0 and is_poem_line(result_final[-1] if result_final else ''):
            # Fortsetzung eines Gedichts
            in_poem = True
            result_final.append(line)
        else:
            in_poem = False
            # Bereinige Leerzeichen vor Satzzeichen
            line_clean = re.sub(r' ([.,;:!?])', r'\1', line)
            result_final.append(line_clean)
    
    cleaned = '\n'.join(result_final)
    
    # - Bereinige Leerzeichen nach öffnenden Anführungszeichen
    cleaned = re.sub(r'«\s+', '«', cleaned)
    cleaned = re.sub(r'"\s+', '"', cleaned)
    
    # - Bereinige Leerzeichen vor schließenden Anführungszeichen
    cleaned = re.sub(r'\s+»', '»', cleaned)
    cleaned = re.sub(r'\s+"', '"', cleaned)
    
    return cleaned


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python tools/clean_gemini_md.py <MD-Datei>")
        sys.exit(1)
    
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {md_path}")
        sys.exit(1)
    
    print(f"Bereinige: {md_path.name}")
    
    # Lese Datei
    content = md_path.read_text(encoding='utf-8')
    
    # Bereinige
    cleaned = clean_gemini_md(content)
    
    # Speichere zurück
    md_path.write_text(cleaned, encoding='utf-8')
    
    print(f"Fertig! {len(content)} -> {len(cleaned)} Zeichen")


if __name__ == '__main__':
    main()
