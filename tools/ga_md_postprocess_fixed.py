#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA MD Post-Process Script - FIXED VERSION
Verarbeitet MD-Dateien von GA-Bänden (Mistral OCR Output) und fügt Seitenmarker ein.
"""

import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Regex-Patterns
RE_HEADING = re.compile(r'^\s*#{1,6}\s+')
RE_MARKER = re.compile(r'\|\*\*(\d+)\*\*\|')
RE_LETTER = re.compile(r'[A-Za-zÄÖÜäöüß]')


def marker(page_num: int) -> str:
    """Erstellt einen Seitenmarker im Format |**N**|"""
    return f"|**{page_num}**|"


def extract_page_number(line: str) -> Optional[int]:
    """Extrahiert die Seitenzahl aus einer Zeile."""
    if not line:
        return None
    
    m = re.search(r'\bSeite\s*:\s*(\d+)\b', line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    
    m = re.search(r'\bSeite\s+(\d+)\b', line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    
    m = re.search(r'\bBuch\s*:\s*\d+\s+Seite\s*:\s*(\d+)\b', line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    
    m = re.search(r'Seite\s*:\s*(\d+)\s*$', line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    
    return None


def is_removable_boilerplate(line: str) -> bool:
    """Prüft, ob eine Zeile entfernt werden soll (Boilerplate)"""
    t = line.strip()
    if not t:
        return False
    if t == "---":
        return True
    if re.match(r'^Copyright Rudolf Steiner Nachlass-Verwaltung\b', t, re.IGNORECASE):
        return True
    if re.match(r'^Band GA\b', t, re.IGNORECASE):
        return True
    if re.match(r'^ISBN\b', t, re.IGNORECASE):
        return True
    if re.match(r'^Printed in\b', t, re.IGNORECASE):
        return True
    return False


def last_non_ws_char(lines: List[str]) -> str:
    """Findet das letzte Nicht-Leerzeichen in den bisherigen Zeilen"""
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i] if i < len(lines) else ""
        for j in range(len(s) - 1, -1, -1):
            ch = s[j]
            if not ch.isspace():
                return ch
    return ""


def first_non_ws_char(s: str) -> str:
    """Findet das erste Nicht-Leerzeichen in einer Zeile"""
    for ch in s:
        if not ch.isspace():
            return ch
    return ""


def process_markdown(raw: str) -> Tuple[str, dict, List[str]]:
    """Verarbeitet die Markdown-Datei und fügt Seitenmarker ein."""
    stats = {
        'pageLines': 0,
        'inserted': 0,
        'deduped': 0,
        'hyphenJoins': 0,
        'spaced': 0
    }
    
    lines = raw.replace('\r\n', '\n').split('\n')
    lines = [re.sub(r'\s+\^[A-Za-z0-9]{4,}\b', '', ln) for ln in lines]
    
    # PHASE 1: Sammle alle Seitenzahlen und Copyright-Positionen
    page_info = []  # Liste von (line_index, page_number) für alle Seitenzahlen
    copyright_info = []  # Liste von (line_index, last_page_before) für Copyright-Zeilen ohne Seitenzahl
    
    last_known_page = None
    for i, ln in enumerate(lines):
        pg = extract_page_number(ln)
        if pg is not None:
            page_info.append((i, pg))
            last_known_page = pg
        elif is_removable_boilerplate(ln) and 'Copyright' in ln and 'Seite' not in ln and 'Buch' in ln:
            if last_known_page is not None:
                copyright_info.append((i, last_known_page))
    
    # Debug: Ausgabe der gefundenen Informationen
    # print(f"Page info: {page_info[:10]}")
    # print(f"Copyright info: {copyright_info[:10]}")
    
    # PHASE 2: Berechne interpolierte Seitenzahlen für Copyright-Zeilen
    # Gruppiere Copyright-Zeilen nach dem Bereich zwischen zwei Seitenzahlen
    interpolated_pages = {}  # line_index -> page_number
    
    # Gruppiere Seitenzahlen in Bereiche
    for page_idx in range(len(page_info) - 1):
        current_page_line, current_page = page_info[page_idx]
        next_page_line, next_page = page_info[page_idx + 1]
        
        # Finde alle Copyright-Zeilen zwischen diesen beiden Seitenzahlen
        copyrights_between = [ci for ci in copyright_info 
                              if current_page_line < ci[0] < next_page_line and
                              ci[1] == current_page]
        copyrights_between.sort(key=lambda x: x[0])
        
        num_missing = next_page - current_page - 1
        if num_missing > 0 and len(copyrights_between) > 0:
            # Verwende nur so viele Copyright-Zeilen wie fehlende Seiten
            num_to_use = min(num_missing, len(copyrights_between))
            for j, (copyright_line_idx, _) in enumerate(copyrights_between[:num_to_use]):
                interpolated_page = current_page + 1 + j
                interpolated_pages[copyright_line_idx] = interpolated_page
    
    # PHASE 3: Verarbeite Zeilen und füge Marker ein
    out = []
    pending = None
    last_inserted_page = None
    
    def append_marker(mk: str, next_line: str):
        nonlocal last_inserted_page
        if not mk:
            return
        
        m = RE_MARKER.search(mk)
        page = int(m.group(1)) if m else None
        if page is not None and last_inserted_page == page:
            stats['deduped'] += 1
            return
        
        if out and re.search(r'-\s*$', out[-1]):
            out[-1] = re.sub(r'-\s*$', '', out[-1])
            out[-1] += mk
            stats['hyphenJoins'] += 1
            last_inserted_page = page
            return
        
        last_ch = last_non_ws_char(out)
        first_ch = first_non_ws_char(next_line or "")
        tight = bool(RE_LETTER.search(last_ch) and RE_LETTER.search(first_ch))
        
        if not out:
            out.append(mk)
            last_inserted_page = page
            return
        
        out[-1] = re.sub(r'\s+$', '', out[-1])
        if tight:
            out[-1] += mk
        else:
            out[-1] += (" " + mk + " ")
            stats['spaced'] += 1
        
        last_inserted_page = page
    
    for i, ln in enumerate(lines):
        pg = extract_page_number(ln)
        if pg is not None:
            stats['pageLines'] += 1
            pending = marker(pg)
            continue
        
        # Wenn Copyright-Zeile ohne Seitenzahl, prüfe ob wir eine interpolierte Seite haben
        if is_removable_boilerplate(ln) and 'Copyright' in ln and 'Seite' not in ln and 'Buch' in ln:
            if i in interpolated_pages:
                interpolated_page = interpolated_pages[i]
                stats['pageLines'] += 1
                # Finde nächste Textzeile
                next_line_idx = i + 1
                while next_line_idx < len(lines) and is_removable_boilerplate(lines[next_line_idx]):
                    next_line_idx += 1
                next_line = lines[next_line_idx] if next_line_idx < len(lines) else ""
                
                # Füge Marker an letzte nicht-leere Zeile an
                if out:
                    target_idx = len(out) - 1
                    while target_idx >= 0 and not out[target_idx].strip():
                        target_idx -= 1
                    if target_idx >= 0:
                        mk = marker(interpolated_page)
                        last_ch = last_non_ws_char(out[:target_idx+1])
                        first_ch = first_non_ws_char(next_line)
                        tight = bool(RE_LETTER.search(last_ch) and RE_LETTER.search(first_ch))
                        out[target_idx] = re.sub(r'\s+$', '', out[target_idx])
                        if tight:
                            out[target_idx] += mk
                        else:
                            out[target_idx] += (" " + mk + " ")
                        stats['inserted'] += 1
                        last_inserted_page = interpolated_page
                    else:
                        pending = marker(interpolated_page)
                        stats['inserted'] += 1
                else:
                    pending = marker(interpolated_page)
                    stats['inserted'] += 1
            continue
        
        if is_removable_boilerplate(ln):
            continue
        
        if pending:
            append_marker(pending, ln)
            stats['inserted'] += 1
            pending = None
        
        cleaned = ln
        m2 = re.match(r'^\s*(?:\|\*\*\d+\*\*\|\s*)+(#{1,6}\s+.*)$', cleaned)
        if m2:
            cleaned = m2.group(1)
        elif RE_HEADING.match(cleaned.strip()) and RE_MARKER.search(cleaned):
            m = re.search(r'(#{1,6}\s+.*)$', cleaned)
            if m:
                cleaned = m.group(1)
        
        out.append(cleaned)
    
    text = '\n'.join(out)
    text = re.sub(r'(?:\|\*\*\d+\*\*\|\s*)+(?=#{1,6}\s+)', '', text, flags=re.MULTILINE)
    text = re.sub(r'(\S)\n+\|\*\*(\d+)\*\*\|\n+(\S)', r'\1 |**\2**| \3', text)
    text = re.sub(r'(\w+)\s*-\s*\|\*\*(\d+)\*\*\|\s*(\w+)', r'\1|**\2**|\3', text)
    text = re.sub(r'(\w+)\s*-\s*\|\*\*(\d+)\*\*\|\s*(\w+)', r'\1|**\2**|\3', text)
    
    def fix_spacing(m):
        left, n, right = m.group(1), m.group(2), m.group(3)
        looks_split = (left.islower() and right.islower() and len(left) > 2 and len(right) > 2)
        return f"{left}|**{n}**|{right}" if looks_split else f"{left} |**{n}**| {right}"
    
    text = re.sub(r'([A-Za-zÄÖÜäöüß]+)\|\*\*(\d+)\*\*\|([A-Za-zÄÖÜäöüß]+)', fix_spacing, text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
    
    report = validate(text)
    return text, stats, report


def validate(md: str) -> List[str]:
    """Validiert die Seitenmarker auf Konsistenz"""
    nums = []
    for m in RE_MARKER.finditer(md):
        nums.append(int(m.group(1)))
    
    issues = []
    for i in range(1, len(nums)):
        if nums[i] < nums[i-1]:
            issues.append(f"Marker decreases at #{i+1}: {nums[i-1]} -> {nums[i]}")
    
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python ga_md_postprocess_fixed.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Fehler: Datei nicht gefunden: {input_path}")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path.parent / f"{input_path.stem}.v23.ga.md"
    
    print(f"Lese Datei: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception as e:
        print(f"Fehler beim Lesen: {e}")
        sys.exit(1)
    
    print("Verarbeite...")
    text, stats, report = process_markdown(raw)
    
    debug_line = f"<!-- GA v23 ran: pageLines={stats['pageLines']}, inserted={stats['inserted']}, deduped={stats['deduped']}, hyphenJoins={stats['hyphenJoins']}, spaced={stats['spaced']} -->\n"
    final_text = debug_line + text
    
    if report:
        final_text += "\n\n---\n\n## Page-marker check report\n"
        final_text += '\n'.join(f"- {issue}" for issue in report) + "\n"
    
    print(f"Speichere nach: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")
        sys.exit(1)
    
    print("\n[OK] Verarbeitung abgeschlossen!")
    print(f"   Seitenzeilen gefunden: {stats['pageLines']}")
    print(f"   Marker eingefügt: {stats['inserted']}")
    print(f"   Duplikate entfernt: {stats['deduped']}")
    print(f"   Bindestrich-Verbindungen: {stats['hyphenJoins']}")
    print(f"   Mit Leerzeichen eingefügt: {stats['spaced']}")
    if report:
        print(f"\n[WARN] Warnungen: {len(report)}")
        for issue in report[:10]:
            print(f"   - {issue}")
        if len(report) > 10:
            print(f"   ... und {len(report) - 10} weitere")


if __name__ == '__main__':
    main()

