#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA MD Page Marker Script
Verarbeitet MD-Dateien von GA-Bänden (Mistral OCR Output) und fügt Seitenmarker |N| ein.

Das Skript:
1. Findet alle Copyright-Marker (mit und ohne Seitenzahl)
2. Extrapoliert fehlende Seitenzahlen
3. Ersetzt Marker durch |N| im Text
4. Entfernt Seitenumbrüche innerhalb von Absätzen
"""

import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Regex-Patterns
RE_MARKER_LINE = re.compile(r'^Copyright Rudolf Steiner Nachlass-Verwaltung Buch: \d+(?:\s+Seite:\s*(\d+))?$', re.IGNORECASE)
RE_PAGE_LINE = re.compile(r'^Seite\s+(\d+)$', re.IGNORECASE)  # Für "Seite X" Format
RE_VERLAG_LINE = re.compile(r'^RUDOLF STEINER\s*VERLAG$', re.IGNORECASE)  # Für "RUDOLF STEINER VERLAG" Format (eine Zeile)
RE_STEINER_LINE = re.compile(r'^RUDOLF STEINER$', re.IGNORECASE)  # Für "RUDOLF STEINER" Format (separate Zeile)
RE_VERLAG_ONLY_LINE = re.compile(r'^VERLAG$', re.IGNORECASE)  # Für "VERLAG" Format (separate Zeile)
RE_PAGE_MARKER = re.compile(r'\|(\d+)\|')
RE_LETTER = re.compile(r'[A-Za-zÄÖÜäöüß]')


def extract_page_number(line: str) -> Optional[int]:
    """Extrahiert die Seitenzahl aus einer Copyright-Zeile oder "Seite X" Zeile."""
    # Format 1: "Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 2 Seite: X"
    match = RE_MARKER_LINE.search(line.strip())
    if match and match.group(1):
        return int(match.group(1))
    
    # Format 2: "Seite X"
    match = RE_PAGE_LINE.search(line.strip())
    if match:
        return int(match.group(1))
    
    return None


def is_marker_line(line: str) -> bool:
    """Prüft, ob eine Zeile ein Copyright-Marker ist."""
    return bool(RE_MARKER_LINE.search(line.strip()))


def is_verlag_line(line: str) -> bool:
    """Prüft, ob eine Zeile "RUDOLF STEINER VERLAG" oder "RUDOLF STEINER" oder "VERLAG" ist."""
    return bool(RE_VERLAG_LINE.search(line.strip()) or RE_STEINER_LINE.search(line.strip()) or RE_VERLAG_ONLY_LINE.search(line.strip()))


def is_page_line(line: str) -> bool:
    """Prüft, ob eine Zeile "Seite X" ist."""
    return bool(RE_PAGE_LINE.search(line.strip()))


def is_separator_line(line: str) -> bool:
    """Prüft, ob eine Zeile ein Separator (---) ist."""
    return line.strip() == "---"


def is_boilerplate(line: str) -> bool:
    """Prüft, ob eine Zeile entfernt werden soll (Boilerplate)."""
    t = line.strip()
    if not t:
        return False
    if t == "---":
        return True
    if RE_MARKER_LINE.search(t):
        return True
    if is_verlag_line(line):
        return True
    if is_page_line(line):
        return True
    # Weitere Boilerplate-Patterns können hier hinzugefügt werden
    return False


def find_marker_positions(lines: List[str]) -> List[Tuple[int, Optional[int]]]:
    """
    Findet alle Marker-Positionen und ihre Seitenzahlen.
    Unterstützt zwei Formate:
    1. "Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 2 Seite: X"
    2. "RUDOLF STEINER VERLAG" gefolgt von "Seite X"
    Returns: Liste von (line_index, page_number oder None)
    """
    markers = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Format 1: Copyright-Marker mit Seitenzahl
        if is_marker_line(lines[i]):
            page_num = extract_page_number(lines[i])
            markers.append((i, page_num))
            i += 1
            continue
        
        # Format 2: "Seite X" Zeile (kann nach "RUDOLF STEINER VERLAG" kommen oder alleine stehen)
        if is_page_line(lines[i]):
            page_num = extract_page_number(lines[i])
            # Prüfe, ob es eine "RUDOLF STEINER VERLAG" Struktur davor gibt
            # Wenn ja, verwende diese "Seite X" Zeile als Marker
            markers.append((i, page_num))
            i += 1
            continue
        
        # Format 2a: "RUDOLF STEINER" gefolgt von "VERLAG" (wird bereits durch "Seite X" erfasst)
        if RE_STEINER_LINE.search(lines[i].strip()):
            i += 1
            continue
        
        i += 1
    
    return markers


def interpolate_page_numbers(markers: List[Tuple[int, Optional[int]]]) -> List[Tuple[int, int]]:
    """
    Interpoliert fehlende Seitenzahlen zwischen bekannten Seitenzahlen.
    Returns: Liste von (line_index, page_number) mit allen Seitenzahlen gefüllt.
    """
    if not markers:
        return []
    
    result = []
    
    # Finde den ersten Marker mit Seitenzahl
    first_known_idx = None
    first_known_page = None
    for i, (line_idx, page_num) in enumerate(markers):
        if page_num is not None:
            first_known_idx = i
            first_known_page = page_num
            break
    
    if first_known_idx is None:
        # Keine bekannte Seitenzahl gefunden, starte bei 1
        first_known_page = 1
        first_known_idx = 0
    
    # Setze alle Marker vor dem ersten bekannten auf aufsteigende Seitenzahlen
    start_page = max(1, first_known_page - first_known_idx)
    for i in range(first_known_idx):
        result.append((markers[i][0], start_page + i))
    
    # Verarbeite den Rest
    i = first_known_idx
    while i < len(markers):
        current_line_idx, current_page = markers[i]
        
        if current_page is not None:
            result.append((current_line_idx, current_page))
            i += 1
        else:
            # Finde den nächsten Marker mit Seitenzahl
            next_known_idx = None
            next_known_page = None
            for j in range(i + 1, len(markers)):
                if markers[j][1] is not None:
                    next_known_idx = j
                    next_known_page = markers[j][1]
                    break
            
            if next_known_idx is None:
                # Kein nächster bekannter Marker, extrapoliere linear
                last_page = result[-1][1] if result else first_known_page
                for j in range(i, len(markers)):
                    result.append((markers[j][0], last_page + (j - i) + 1))
                break
            else:
                # Interpoliere zwischen current und next
                last_page = result[-1][1] if result else first_known_page
                num_missing = next_known_idx - i  # Anzahl der Marker ohne Seitenzahl
                page_diff = next_known_page - last_page  # Differenz zwischen den Seitenzahlen
                
                if num_missing > 0 and page_diff > 0:
                    # Verteile die Seitenzahlen gleichmäßig zwischen last_page und next_known_page
                    # Beispiel: last_page=6, next_known_page=10, num_missing=3
                    # Dann sollten die Marker die Seiten 7, 8, 9 bekommen
                    for j in range(i, next_known_idx):
                        # Berechne die Seitenzahl: last_page + 1 + (j - i)
                        # Das gibt: 6 + 1 + 0 = 7, 6 + 1 + 1 = 8, 6 + 1 + 2 = 9
                        interpolated_page = last_page + 1 + (j - i)
                        # Stelle sicher, dass wir nicht über next_known_page hinausgehen
                        if interpolated_page < next_known_page:
                            result.append((markers[j][0], interpolated_page))
                        else:
                            # Fallback: verwende einfach aufsteigende Zahlen
                            result.append((markers[j][0], last_page + (j - i) + 1))
                else:
                    # Fallback: einfach aufsteigend
                    for j in range(i, next_known_idx):
                        result.append((markers[j][0], last_page + (j - i) + 1))
                
                i = next_known_idx
    
    return result


def is_word_break(prev_line: str, next_line: str) -> bool:
    """
    Prüft, ob ein Seitenumbruch innerhalb eines Wortes ist (durch Trennungszeichen erkannt).
    Returns: True wenn es ein Wortumbruch innerhalb eines Wortes ist, False wenn zwischen Wörtern.
    
    Beispiele:
    - "die ge" + "kennzeichnete" -> True (Wortumbruch innerhalb eines Wortes)
    - "Erfahrung" + "und Denken" -> False (zwischen Wörtern)
    """
    prev_stripped = prev_line.rstrip()
    next_stripped = next_line.lstrip()
    
    if not prev_stripped or not next_stripped:
        return False
    
    prev_last = prev_stripped[-1]
    next_first = next_stripped[0]
    
    # Wenn die vorherige Zeile mit Bindestrich endet, ist es ein Wortumbruch innerhalb eines Wortes
    if prev_stripped.endswith('-'):
        return True
    
    # Wenn beide Buchstaben sind
    if RE_LETTER.search(prev_last) and RE_LETTER.search(next_first):
        # Wenn die vorherige Zeile mit Satzzeichen oder Leerzeichen endet, ist es zwischen Wörtern
        if prev_stripped.endswith(('.', '!', '?', ':', ';', ',', ' ', '"', '»', '«', '—', '–')):
            return False
        
        # Wenn die nächste Zeile mit Großbuchstabe beginnt, ist es wahrscheinlich zwischen Wörtern
        if next_first.isupper():
            return False
        
        # Wenn beide Kleinbuchstaben sind, könnte es ein Wortumbruch sein
        if prev_last.islower() and next_first.islower():
            # Prüfe die letzten Zeichen der vorherigen Zeile (nach dem letzten Leerzeichen)
            # Beispiel: "die ge" -> letzte 2 Zeichen "ge" sind nur Buchstaben
            # Finde das letzte Wort (Zeichen nach dem letzten Leerzeichen)
            last_space_idx = prev_stripped.rfind(' ')
            if last_space_idx >= 0:
                last_word = prev_stripped[last_space_idx+1:]
            else:
                last_word = prev_stripped
            
            # Wenn das letzte Wort kurz ist (weniger als 6 Zeichen) und nur Buchstaben enthält,
            # ist es wahrscheinlich ein Wortumbruch innerhalb eines Wortes
            # z.B. "ge", "Fried", "kenn"
            if len(last_word) <= 5 and all(c.isalpha() for c in last_word):
                return True
            
            # Wenn die gesamte Zeile kurz ist (weniger als 6 Zeichen), ist es wahrscheinlich ein Wortumbruch
            if len(prev_stripped) <= 5:
                return True
    
    return False


def should_join_lines(prev_line: str, next_line: str) -> bool:
    """Prüft, ob zwei Zeilen zusammengefügt werden sollten (Seitenumbruch innerhalb eines Absatzes)."""
    prev_stripped = prev_line.rstrip()
    next_stripped = next_line.lstrip()
    
    if not prev_stripped or not next_stripped:
        return False
    
    prev_last = prev_stripped[-1]
    next_first = next_stripped[0]
    
    # Wenn die vorherige Zeile mit Bindestrich endet, sollte zusammengefügt werden
    if prev_stripped.endswith('-'):
        return True
    
    # Wenn beide Buchstaben sind und die vorherige Zeile nicht mit Satzzeichen endet
    if RE_LETTER.search(prev_last) and RE_LETTER.search(next_first):
        # Prüfe, ob die vorherige Zeile mit Satzzeichen endet (dann wahrscheinlich kein Absatzumbruch)
        if prev_stripped.endswith(('.', '!', '?', ':', ';')):
            return False
        # Wenn die nächste Zeile mit Kleinbuchstabe beginnt, ist es wahrscheinlich ein Absatzumbruch
        if next_first.islower():
            return True
        # Wenn die vorherige Zeile mit Komma endet, ist es wahrscheinlich kein Absatzumbruch
        if prev_stripped.endswith(','):
            return False
        # Sonst prüfe, ob es wie ein Wortumbruch aussieht
        return True
    
    return False


def process_markdown(raw: str) -> Tuple[str, dict]:
    """Verarbeitet die Markdown-Datei und fügt Seitenmarker ein."""
    stats = {
        'markers_found': 0,
        'markers_with_page': 0,
        'markers_interpolated': 0,
        'markers_inserted': 0,
        'paragraph_joins': 0,
    }
    
    lines = raw.replace('\r\n', '\n').split('\n')
    
    # PHASE 1: Finde alle Marker
    marker_positions = find_marker_positions(lines)
    stats['markers_found'] = len(marker_positions)
    stats['markers_with_page'] = sum(1 for _, page in marker_positions if page is not None)
    
    # PHASE 2: Interpoliere fehlende Seitenzahlen
    interpolated_markers = interpolate_page_numbers(marker_positions)
    stats['markers_interpolated'] = len(interpolated_markers) - stats['markers_with_page']
    
    # PHASE 2a: Erhöhe alle Seitenzahlen um +1 (PDF-Marker stehen am Seitenende, MD-Marker am Seitenanfang)
    # Beispiel: Wenn im PDF "Seite 6" am Ende steht, wird der Marker |7| am Anfang der nächsten Seite (Seite 7) eingefügt
    interpolated_markers = [(line_idx, page_num + 1 if page_num is not None else None) 
                            for line_idx, page_num in interpolated_markers]
    
    # Erstelle ein Dictionary für schnellen Zugriff (nur Marker mit gültiger Seitenzahl)
    marker_dict = {line_idx: page_num for line_idx, page_num in interpolated_markers if page_num is not None}
    
    # PHASE 3: Verarbeite Zeilen
    output = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Wenn es ein Separator ist, überspringe ihn
        if is_separator_line(line):
            i += 1
            continue
        
        # Wenn es ein Marker ist, verarbeite ihn (Format 1: Copyright-Marker)
        if is_marker_line(line):
            if i in marker_dict:
                page_num = marker_dict[i]
                
                # Finde die letzte nicht-leere Ausgabezeile
                last_output_idx = len(output) - 1
                while last_output_idx >= 0 and not output[last_output_idx].strip():
                    last_output_idx -= 1
                
                # Finde die nächste nicht-Boilerplate Zeile nach dem Marker
                next_idx = i + 1
                while next_idx < len(lines):
                    if is_separator_line(lines[next_idx]) or is_marker_line(lines[next_idx]) or is_verlag_line(lines[next_idx]) or is_page_line(lines[next_idx]):
                        next_idx += 1
                        continue
                    if lines[next_idx].strip():
                        break
                    next_idx += 1
                
                next_line = lines[next_idx] if next_idx < len(lines) else ""
                
                # Füge Marker ein
                if last_output_idx >= 0:
                    # Füge Marker an die letzte Ausgabezeile an
                    last_line = output[last_output_idx].rstrip()
                    
                    # Prüfe, ob wir die Zeilen zusammenfügen sollten
                    if next_line and should_join_lines(last_line, next_line):
                        # Entferne Bindestrich am Ende der letzten Zeile falls vorhanden
                        if last_line.endswith('-'):
                            last_line = last_line[:-1].rstrip()
                        
                        # Prüfe, ob es ein Wortumbruch innerhalb eines Wortes ist
                        if is_word_break(last_line, next_line):
                            # Kein Leerzeichen: Wortumbruch innerhalb eines Wortes (z.B. "ge|9|kennzeichnete")
                            output[last_output_idx] = last_line + f"|{page_num}|" + next_line.lstrip()
                        else:
                            # Mit Leerzeichen: Zwischen Wörtern (z.B. "Erfahrung |8| und Denken")
                            output[last_output_idx] = last_line + f" |{page_num}| " + next_line.lstrip()
                        
                        stats['paragraph_joins'] += 1
                        # Überspringe die nächste Zeile, da sie bereits eingefügt wurde
                        i = next_idx + 1
                        continue
                    else:
                        # Füge Marker mit Leerzeichen ein (zwischen Wörtern)
                        if last_line:
                            output[last_output_idx] = last_line + f" |{page_num}|"
                        else:
                            output[last_output_idx] = f"|{page_num}|"
                    
                    stats['markers_inserted'] += 1
                else:
                    # Am Anfang der Datei oder keine vorherige Zeile
                    if next_line:
                        output.append(f"|{page_num}| " + next_line.lstrip())
                        stats['markers_inserted'] += 1
                        i = next_idx + 1
                        continue
                    else:
                        output.append(f"|{page_num}|")
                        stats['markers_inserted'] += 1
            
            # Überspringe Marker-Zeile und mögliche Separator-Zeilen
            i += 1
            continue
        
        # Format 2: "Seite X" Zeile (nach "RUDOLF STEINER VERLAG")
        if is_page_line(line):
            if i in marker_dict:
                page_num = marker_dict[i]
                
                # Finde die letzte nicht-leere Ausgabezeile
                last_output_idx = len(output) - 1
                while last_output_idx >= 0 and not output[last_output_idx].strip():
                    last_output_idx -= 1
                
                # Finde die nächste nicht-Boilerplate Zeile nach dem Marker
                next_idx = i + 1
                while next_idx < len(lines):
                    if is_separator_line(lines[next_idx]) or is_marker_line(lines[next_idx]) or is_verlag_line(lines[next_idx]) or is_page_line(lines[next_idx]):
                        next_idx += 1
                        continue
                    if lines[next_idx].strip():
                        break
                    next_idx += 1
                
                next_line = lines[next_idx] if next_idx < len(lines) else ""
                
                # Füge Marker ein
                if last_output_idx >= 0:
                    # Füge Marker an die letzte Ausgabezeile an
                    last_line = output[last_output_idx].rstrip()
                    
                    # Prüfe, ob wir die Zeilen zusammenfügen sollten
                    if next_line and should_join_lines(last_line, next_line):
                        # Entferne Bindestrich am Ende der letzten Zeile falls vorhanden
                        if last_line.endswith('-'):
                            last_line = last_line[:-1].rstrip()
                        
                        # Prüfe, ob es ein Wortumbruch innerhalb eines Wortes ist
                        if is_word_break(last_line, next_line):
                            # Kein Leerzeichen: Wortumbruch innerhalb eines Wortes (z.B. "ge|9|kennzeichnete")
                            output[last_output_idx] = last_line + f"|{page_num}|" + next_line.lstrip()
                        else:
                            # Mit Leerzeichen: Zwischen Wörtern (z.B. "Erfahrung |8| und Denken")
                            output[last_output_idx] = last_line + f" |{page_num}| " + next_line.lstrip()
                        
                        stats['paragraph_joins'] += 1
                        # Überspringe die nächste Zeile, da sie bereits eingefügt wurde
                        i = next_idx + 1
                        continue
                    else:
                        # Füge Marker mit Leerzeichen ein (zwischen Wörtern)
                        if last_line:
                            output[last_output_idx] = last_line + f" |{page_num}|"
                        else:
                            output[last_output_idx] = f"|{page_num}|"
                    
                    stats['markers_inserted'] += 1
                else:
                    # Am Anfang der Datei oder keine vorherige Zeile
                    if next_line:
                        output.append(f"|{page_num}| " + next_line.lstrip())
                        stats['markers_inserted'] += 1
                        i = next_idx + 1
                        continue
                    else:
                        output.append(f"|{page_num}|")
                        stats['markers_inserted'] += 1
            
            # Überspringe Marker-Zeile
            i += 1
            continue
        
        # Überspringe "RUDOLF STEINER VERLAG" Zeilen
        if is_verlag_line(line):
            i += 1
            continue
        
        # Normale Zeile - füge hinzu
        output.append(line)
        i += 1
    
    # PHASE 4: Post-Processing
    text = '\n'.join(output)
    
    # Entferne mehrfache Leerzeichen (aber behalte Leerzeichen um Marker, die zwischen Wörtern stehen)
    text = re.sub(r' +', ' ', text)
    
    # Entferne mehrfache Leerzeilen
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # WICHTIG: Bereinige Marker-Formatierung NICHT mehr automatisch,
    # da wir bereits korrekt zwischen Worttrennungen innerhalb von Wörtern
    # (keine Leerzeichen) und zwischen Wörtern (mit Leerzeichen) unterscheiden.
    # Die Marker sollten bereits korrekt formatiert sein.
    
    return text.strip() + '\n', stats


def validate_page_markers(text: str) -> List[str]:
    """Validiert die Seitenmarker auf Konsistenz."""
    markers = []
    for match in RE_PAGE_MARKER.finditer(text):
        markers.append(int(match.group(1)))
    
    issues = []
    for i in range(1, len(markers)):
        if markers[i] < markers[i-1]:
            issues.append(f"Marker nimmt ab bei #{i+1}: {markers[i-1]} -> {markers[i]}")
        elif markers[i] - markers[i-1] > 5:
            issues.append(f"Großer Sprung bei #{i+1}: {markers[i-1]} -> {markers[i]}")
    
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python ga_md_page_marker.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Fehler: Datei nicht gefunden: {input_path}")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path.parent / f"{input_path.stem}_final.md"
    
    print(f"Lese Datei: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception as e:
        print(f"Fehler beim Lesen: {e}")
        sys.exit(1)
    
    print("Verarbeite...")
    text, stats = process_markdown(raw)
    
    # Validiere Marker
    issues = validate_page_markers(text)
    
    # Füge Debug-Informationen hinzu
    debug_line = f"<!-- GA Page Marker: markers_found={stats['markers_found']}, with_page={stats['markers_with_page']}, interpolated={stats['markers_interpolated']}, inserted={stats['markers_inserted']}, paragraph_joins={stats['paragraph_joins']} -->\n"
    final_text = debug_line + text
    
    if issues:
        final_text += "\n\n---\n\n## Page-marker validation report\n"
        final_text += '\n'.join(f"- {issue}" for issue in issues) + "\n"
    
    print(f"Speichere nach: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")
        sys.exit(1)
    
    print("\n[OK] Verarbeitung abgeschlossen!")
    print(f"   Marker gefunden: {stats['markers_found']}")
    print(f"   Marker mit Seitenzahl: {stats['markers_with_page']}")
    print(f"   Marker interpoliert: {stats['markers_interpolated']}")
    print(f"   Marker eingefügt: {stats['markers_inserted']}")
    print(f"   Absatz-Verbindungen: {stats['paragraph_joins']}")
    
    if issues:
        print(f"\n[WARN] Warnungen: {len(issues)}")
        for issue in issues[:10]:
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... und {len(issues) - 10} weitere")


if __name__ == '__main__':
    main()

