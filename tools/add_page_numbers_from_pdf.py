#!/usr/bin/env python3
"""
Fügt Seitenzahlen zu --- Markern hinzu durch Vergleich mit PDF.

Konvertiert --- Marker zu |XX| Seitenmarkern:
- Findet die korrekte Seitenzahl durch Text-Matching mit PDF
- Formatiert Marker korrekt (Leerzeichen je nach Kontext)
- Behält --- Marker, wenn keine Seitenzahl gefunden wird
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF nicht installiert. Installieren mit: pip install PyMuPDF")
    sys.exit(1)


def normalize_text_for_matching(text: str) -> str:
    """
    Normalisiere Text für Matching:
    - Entferne Seitenmarker
    - Normalisiere Whitespace
    - Entferne Sonderzeichen
    """
    # Entferne existierende Seitenmarker
    text = re.sub(r'\|(\d+)\|', '', text)
    # Entferne --- Marker
    text = re.sub(r'---', '', text)
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_pdf_pages(pdf_path: Path) -> List[Dict]:
    """
    Extrahiere Text aus PDF mit Seitenzahlen.
    
    Rückgabe: Liste von Dicts mit 'page_num', 'text', 'normalized_text'
    """
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text()
        
        # Versuche gedruckte Seitenzahl zu extrahieren
        printed_page = extract_printed_page_number(text, page_idx + 1)
        
        normalized = normalize_text_for_matching(text)
        
        pages.append({
            'pdf_index': page_idx,
            'pdf_page': page_idx + 1,
            'printed_page': printed_page,
            'text': text,
            'normalized_text': normalized
        })
    
    doc.close()
    return pages


def extract_page_number_from_footer(lines: List[str]) -> Optional[int]:
    """
    Extrahiert die Seitenzahl aus den Footer-Zeilen.
    
    Unterstützte Formate:
    1. "Seite: XX" (ältere PDFs mit Copyright-Footer)
    2. Einzelne Zahl DIREKT gefolgt von "RUDOLF STEINER" (GA069b-Format)
    3. "Seite XX" nur wenn es eine der letzten 3 nicht-leeren Zeilen ist
    """
    # Finde nicht-leere Zeilen
    non_empty = [(i, l.strip()) for i, l in enumerate(lines) if l.strip()]
    if not non_empty:
        return None
    
    last_lines = lines[-15:] if len(lines) >= 15 else lines
    
    # Format 1: "Seite: XX" (mit Doppelpunkt - typisch für Copyright-Footer)
    for line in reversed(last_lines):
        match = re.search(r"Seite:\s*([\d\s]+)", line, re.IGNORECASE)
        if match:
            page_str = match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                return int(page_str)
    
    # Format 2: Zahl DIREKT gefolgt von "RUDOLF STEINER" (auf nächster Zeile)
    for i in range(1, len(non_empty) - 1):
        _, prev_line = non_empty[i - 1]
        _, current = non_empty[i]
        _, next_line = non_empty[i + 1]
        
        if re.match(r"^\d{1,3}$", current):
            if "RUDOLF STEINER" in next_line.upper():
                if len(prev_line) >= 30 and not re.match(r"^\d+$", prev_line):
                    if not re.search(r"\d{2,3}\s*$", prev_line):
                        return int(current)
    
    # Format 3: "Seite XX" nur in den letzten 3 nicht-leeren Zeilen
    for _, line in non_empty[-3:]:
        match = re.match(r"^Seite\s+(\d+)$", line, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def extract_printed_page_number(text: str, pdf_page: int) -> Optional[int]:
    """
    Versuche die gedruckte Seitenzahl aus dem Text zu extrahieren.
    """
    lines = text.strip().split('\n')
    
    # Format 1: Copyright-Zeile mit "Seite: XX"
    copyright_match = re.search(
        r'Copyright\s+Rudolf\s+Stein\w*.*?Seite:\s*([\d\s]+)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if copyright_match:
        page_str = copyright_match.group(1).replace(" ", "").strip()
        if page_str.isdigit():
            return int(page_str)
    
    # Format 2-4: Verwende extract_page_number_from_footer
    return extract_page_number_from_footer(lines)


def find_page_number_for_marker(
    marker_text_before: str,
    marker_text_after: str,
    pdf_pages: List[Dict],
    last_found_page: int = 0
) -> Optional[int]:
    """
    Finde die Seitenzahl für einen --- Marker durch Text-Matching.
    
    Args:
        marker_text_before: Text vor dem Marker (normalisiert)
        marker_text_after: Text nach dem Marker (normalisiert)
        pdf_pages: Liste der PDF-Seiten
        last_found_page: Letzte gefundene Seitenzahl (für Monotonie)
    
    Returns:
        Seitenzahl oder None
    """
    if not marker_text_before and not marker_text_after:
        return None
    
    # Extrahiere charakteristische Textsegmente für Matching
    # Verwende längere Segmente für bessere Trefferquote
    search_before = marker_text_before[-150:].strip() if len(marker_text_before) > 150 else marker_text_before
    search_after = marker_text_after[:150].strip() if len(marker_text_after) > 150 else marker_text_after
    
    # Suche in PDF-Seiten (beginne bei last_found_page für Monotonie)
    best_match = None
    best_score = 0
    
    for page in pdf_pages:
        page_num = page['printed_page'] or page['pdf_page']
        
        # Überspringe Seiten vor der letzten gefundenen Seite (Monotonie)
        if page_num < last_found_page:
            continue
        
        normalized = page['normalized_text'].lower()
        
        # Prüfe ob beide Textsegmente in dieser Seite vorkommen
        before_found = False
        after_found = False
        before_pos = -1
        after_pos = -1
        
        if search_before:
            before_pos = normalized.find(search_before.lower())
            before_found = before_pos >= 0
        
        if search_after:
            after_pos = normalized.find(search_after.lower())
            after_found = after_pos >= 0
        
        # Wenn beide gefunden werden UND "after" nach "before" kommt → perfekter Match
        if before_found and after_found and after_pos > before_pos:
            # Prüfe ob sie nah beieinander sind (innerhalb von 500 Zeichen)
            distance = after_pos - before_pos
            if distance < 500:
                score = 100 - (distance // 10)  # Je näher, desto besser
                if score > best_score:
                    best_score = score
                    best_match = page_num
        
        # Wenn nur "after" gefunden wird und es am Anfang der Seite ist → möglicher Match
        elif after_found and not before_found and after_pos < 200:
            if best_score < 50:
                best_score = 50
                best_match = page_num
        
        # Wenn nur "before" gefunden wird und es am Ende der Seite ist → möglicher Match
        elif before_found and not after_found:
            page_length = len(normalized)
            if before_pos > page_length - 200:
                if best_score < 50:
                    best_score = 50
                    best_match = page_num
    
    return best_match


def format_page_marker(
    text_before: str,
    text_after: str,
    page_num: int
) -> str:
    """
    Formatiere Seitenmarker korrekt:
    - Leerzeichen davor/danach, wenn zwischen Wörtern
    - Kein Leerzeichen, wenn Wort getrennt wird
    
    Args:
        text_before: Text vor dem Marker
        text_after: Text nach dem Marker
        page_num: Seitenzahl
    
    Returns:
        Formatierter Marker: " |XX| " oder "|XX|"
    """
    # Prüfe ob Wort getrennt wird
    # Wenn text_before nicht mit Satzzeichen/Leerzeichen endet UND
    # text_after mit Kleinbuchstabe beginnt → Worttrennung
    
    before_ends = text_before.rstrip()
    after_starts = text_after.lstrip()
    
    if not before_ends:
        return f"|{page_num}| "
    if not after_starts:
        return f" |{page_num}|"
    
    # Prüfe ob Wort getrennt wird
    before_last_char = before_ends[-1] if before_ends else ''
    after_first_char = after_starts[0] if after_starts else ''
    
    # Wenn vorherige Zeile nicht mit Satzzeichen/Leerzeichen endet UND
    # nächste Zeile mit Kleinbuchstabe beginnt → Worttrennung (kein Leerzeichen)
    if (before_last_char.isalnum() and 
        after_first_char.islower() and 
        not before_last_char in '.!?:;»"'):
        return f"|{page_num}|"
    
    # Sonst: zwischen Wörtern (mit Leerzeichen)
    return f" |{page_num}| "


def add_page_numbers_to_md(
    md_path: Path,
    pdf_path: Path,
    output_path: Path = None
) -> str:
    """
    Füge Seitenzahlen zu --- Markern hinzu durch Vergleich mit PDF.
    """
    print(f"Lade MD-Datei: {md_path.name}")
    md_content = md_path.read_text(encoding='utf-8')
    
    print(f"Lade PDF-Datei: {pdf_path.name}")
    pdf_pages = extract_pdf_pages(pdf_path)
    print(f"  {len(pdf_pages)} Seiten im PDF gefunden")
    
    # Normalisiere MD-Text für Matching
    md_lines = md_content.split('\n')
    
    # Finde alle --- Marker
    result_lines = []
    last_found_page = 0
    marker_count = 0
    found_count = 0
    skip_indices = set()  # Indizes von Zeilen, die bereits kombiniert wurden
    
    i = 0
    while i < len(md_lines):
        # Überspringe bereits kombinierte Zeilen
        if i in skip_indices:
            i += 1
            continue
            
        line = md_lines[i]
        
        if line.strip() == '---':
            marker_count += 1
            
            # Finde Text vor und nach dem Marker
            # Text vor Marker: Sammle bis zu 5 Zeilen rückwärts
            text_before_parts = []
            before_line_idx = None
            for j in range(i - 1, max(-1, i - 6), -1):
                stripped = md_lines[j].strip()
                if stripped and not stripped.startswith('#'):
                    text_before_parts.insert(0, stripped)
                    before_line_idx = j
                    # Sammle bis zu 300 Zeichen
                    if len(' '.join(text_before_parts)) > 300:
                        break
            
            # Text nach Marker: Sammle bis zu 5 Zeilen vorwärts
            text_after_parts = []
            after_line_idx = None
            for j in range(i + 1, min(len(md_lines), i + 6)):
                stripped = md_lines[j].strip()
                if stripped and not stripped.startswith('#'):
                    text_after_parts.append(stripped)
                    after_line_idx = j
                    # Sammle bis zu 300 Zeichen
                    if len(' '.join(text_after_parts)) > 300:
                        break
            
            text_before_raw = ' '.join(text_before_parts)
            text_after_raw = ' '.join(text_after_parts)
            
            text_before = normalize_text_for_matching(text_before_raw)
            text_after = normalize_text_for_matching(text_after_raw)
            
            # Prüfe ob --- ein echter Absatzumbruch ist oder innerhalb eines Absatzes steht
            is_paragraph_break = False
            if before_line_idx is not None and after_line_idx is not None:
                before_line = md_lines[before_line_idx].rstrip()
                after_line = md_lines[after_line_idx].lstrip()
                
                # Prüfe ob vorherige Zeile mit Satzzeichen endet
                before_ends_sentence = before_line.endswith(('.', '!', '?', ':', ';', '»', '"'))
                # Prüfe ob nächste Zeile mit Großbuchstabe beginnt
                after_starts_capital = after_line and after_line[0].isupper()
                # Prüfe ob leere Zeilen zwischen den Zeilen sind
                has_empty_between = False
                for k in range(before_line_idx + 1, after_line_idx):
                    if not md_lines[k].strip():
                        has_empty_between = True
                        break
                
                # Echter Absatzumbruch wenn:
                # - Vorherige Zeile endet mit Satzzeichen ODER
                # - Nächste Zeile beginnt mit Großbuchstabe UND
                # - Es gibt keine leere Zeile zwischen ihnen (--- ist der einzige Umbruch)
                if (before_ends_sentence or after_starts_capital) and not has_empty_between:
                    is_paragraph_break = True
            
            # Finde Seitenzahl
            page_num = find_page_number_for_marker(
                text_before,
                text_after,
                pdf_pages,
                last_found_page
            )
            
            if page_num:
                # Formatiere Marker
                marker = format_page_marker(
                    text_before_raw,
                    text_after_raw,
                    page_num
                )
                
                if is_paragraph_break:
                    # Echter Absatzumbruch → Marker einfügen, aber Absatzumbruch BEHALTEN
                    if before_line_idx is not None:
                        # Stelle sicher, dass die vorherige Zeile bereits hinzugefügt wurde
                        if result_lines and result_lines[-1].rstrip() == md_lines[before_line_idx].rstrip():
                            result_lines.pop()
                        before_line = md_lines[before_line_idx].rstrip()
                        # Marker am Ende der Zeile mit Absatzumbruch
                        result_lines.append(before_line + marker)
                    else:
                        # Marker am Anfang der nächsten Zeile
                        if after_line_idx is not None:
                            after_line = md_lines[after_line_idx]
                            result_lines.append(marker + after_line.lstrip())
                            i = after_line_idx + 1
                        else:
                            result_lines.append(marker)
                            i += 1
                else:
                    # Innerhalb eines Absatzes → Zeilen verbinden mit Marker
                    if before_line_idx is not None and after_line_idx is not None:
                        # Stelle sicher, dass alle Zeilen zwischen i-1 und after_line_idx hinzugefügt wurden
                        # (einschließlich Überschriften und leere Zeilen, aber NICHT andere --- Marker!)
                        for k in range(max(0, i - 1), after_line_idx):
                            if k == i:
                                continue  # Überspringe den aktuellen Marker
                            if k == before_line_idx:
                                continue  # Diese Zeile wird gleich kombiniert
                            # WICHTIG: Überspringe andere --- Marker NICHT - die müssen später verarbeitet werden!
                            # Sie werden durch den normalen else-Zweig verarbeitet, wenn i sie erreicht
                            if md_lines[k].strip() == '---':
                                continue  # Überspringe andere --- Marker - die werden später verarbeitet
                            if not result_lines or result_lines[-1] != md_lines[k]:
                                result_lines.append(md_lines[k])
                        
                        # Entferne die letzte Zeile aus result_lines (falls sie bereits hinzugefügt wurde)
                        if result_lines and result_lines[-1].rstrip() == md_lines[before_line_idx].rstrip():
                            result_lines.pop()
                        
                        # Kombiniere: letzte Zeile + Marker + nächste Zeile
                        before_line = md_lines[before_line_idx].rstrip()
                        after_line = md_lines[after_line_idx].lstrip()
                        
                        # Kombiniere die Zeilen mit dem Marker
                        combined = before_line + marker + after_line
                        result_lines.append(combined)
                        
                        # Markiere die kombinierten Zeilen als zu überspringen
                        skip_indices.add(before_line_idx)
                        skip_indices.add(after_line_idx)
                        
                        # Setze i auf i+1, damit alle Zeilen zwischen i und after_line_idx
                        # beim nächsten Durchlauf verarbeitet werden (inklusive andere --- Marker!)
                        i += 1
                    elif before_line_idx is not None:
                        # Nur Zeile davor vorhanden → Marker am Ende der Zeile
                        if result_lines and result_lines[-1].rstrip() == md_lines[before_line_idx].rstrip():
                            result_lines.pop()
                        before_line = md_lines[before_line_idx].rstrip()
                        combined = before_line + marker
                        result_lines.append(combined)
                        i += 1
                    elif after_line_idx is not None:
                        # Nur Zeile danach vorhanden → Marker am Anfang der Zeile
                        after_line = md_lines[after_line_idx].lstrip()
                        combined = marker + after_line
                        result_lines.append(combined)
                        i = after_line_idx + 1
                    else:
                        # Fallback: Marker als eigene Zeile (sollte nicht vorkommen)
                        result_lines.append(marker)
                        i += 1
                
                last_found_page = page_num
                found_count += 1
                if marker_count % 10 == 0:
                    print(f"  [{marker_count}] Seite {page_num} gefunden")
            else:
                # Keine Seitenzahl gefunden → behalte IMMER --- Marker
                result_lines.append('---')
                i += 1
                
                if marker_count % 10 == 0:
                    print(f"  [{marker_count}] Keine Seitenzahl gefunden")
        else:
            # Normale Zeile - füge hinzu
            result_lines.append(line)
            i += 1
    
    result_content = '\n'.join(result_lines)
    
    # Speichere Ergebnis
    if output_path is None:
        output_path = md_path.parent / f"{md_path.stem}_with_pages.md"
    
    output_path.write_text(result_content, encoding='utf-8')
    print(f"\nErgebnis gespeichert: {output_path.name}")
    print(f"  Marker gefunden: {found_count}/{marker_count}")
    
    return result_content


def main():
    parser = argparse.ArgumentParser(
        description='Fügt Seitenzahlen zu --- Markern hinzu durch Vergleich mit PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python tools/add_page_numbers_from_pdf.py prepared.md --pdf "Steiner, Rudolf GA 052.pdf"
  python tools/add_page_numbers_from_pdf.py prepared.md --pdf "GA052.pdf" --output "final.md"
        """
    )
    parser.add_argument('md_file', help='Pfad zur vorbereiteten MD-Datei (mit --- Markern)')
    parser.add_argument('--pdf', required=True, help='Pfad zur PDF-Datei')
    parser.add_argument('--output', '-o', help='Ausgabedatei (Standard: <input>_with_pages.md)')
    
    args = parser.parse_args()
    
    md_path = Path(args.md_file)
    pdf_path = Path(args.pdf)
    
    if not md_path.exists():
        print(f"FEHLER: MD-Datei nicht gefunden: {md_path}")
        sys.exit(1)
    
    if not pdf_path.exists():
        print(f"FEHLER: PDF-Datei nicht gefunden: {pdf_path}")
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else None
    add_page_numbers_to_md(md_path, pdf_path, output_path)


if __name__ == '__main__':
    main()
