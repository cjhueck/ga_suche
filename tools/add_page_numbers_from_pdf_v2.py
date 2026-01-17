#!/usr/bin/env python3
"""
Fügt Seitenzahlen zu --- Markern hinzu durch Matching mit PDF.

Version 2: Kombiniert exakte Suche mit Fuzzy-Fallback.
Keine strikte Monotonie - erlaubt Sprünge zurück (für Inhaltsverzeichnis etc.)

Regeln:
1. Bei Silbentrennung (Zeile endet mit -): 
   "unzäh-" + --- + "lige" → "unzäh|XX|lige"
   
2. Bei Wortgrenzen innerhalb eines Absatzes:
   "Text" + --- + "weiterer" → "Text |XX| weiterer"
   
3. Bei echtem Absatzumbruch (Satz endet mit . ! ?):
   Absatz erhalten mit Marker

4. --- ohne Seitenzahl bleibt stehen

5. Bei Vortragsüberschriften: Seitenzahl am Anfang des ersten Absatzes
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import fitz
except ImportError:
    print("PyMuPDF nicht installiert. pip install PyMuPDF")
    sys.exit(1)


def normalize_for_matching(text: str) -> str:
    """Normalisiere Text für Matching."""
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'---', '', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'#', '', text)
    
    replacements = {
        'ä': 'a', 'ö': 'o', 'ü': 'u',
        'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        'ß': 'ss',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = ''.join(c if ord(c) < 128 else ' ' for c in text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def extract_pdf_pages(pdf_path: Path) -> List[Dict]:
    """Extrahiere Text aus PDF."""
    doc = fitz.open(pdf_path)
    pages = []
    
    for idx in range(len(doc)):
        page = doc[idx]
        text = page.get_text()
        normalized = normalize_for_matching(text)
        
        printed_page = None
        lines = text.strip().split('\n')
        for line in reversed(lines[-10:]):
            if re.match(r'^\d{1,3}$', line.strip()):
                printed_page = int(line.strip())
                break
        
        pages.append({
            'pdf_page': idx + 1,
            'printed_page': printed_page,
            'normalized': normalized
        })
    
    doc.close()
    return pages


def find_page_for_text(
    text: str, 
    pdf_pages: List[Dict]
) -> Tuple[Optional[int], int]:
    """
    Finde die Seite für einen Text.
    
    Strategie:
    1. Exakte Suche nach den ersten 60 Zeichen
    2. Fuzzy-Vergleich mit Seitenanfang als Fallback
    
    Returns: (page_num, position)
    """
    text_norm = normalize_for_matching(text[:200]) if text else ""
    
    if len(text_norm) < 20:
        return None, -1
    
    search_text = text_norm[:60]
    
    matches = []
    
    for page in pdf_pages:
        page_num = page['printed_page'] or page['pdf_page']
        page_text = page['normalized']
        
        # Exakte Suche
        if search_text in page_text:
            pos = page_text.find(search_text)
            matches.append((page_num, pos, 'exact', 1.0))
        else:
            # Fuzzy mit Seitenanfang
            page_start = page_text[:200]
            ratio = SequenceMatcher(None, search_text, page_start[:60]).ratio()
            if ratio > 0.7:
                matches.append((page_num, 0, 'fuzzy', ratio))
    
    if not matches:
        return None, -1
    
    # Priorisiere: exakt vor fuzzy, dann nach Position
    exact_matches = [(p, pos, t, s) for p, pos, t, s in matches if t == 'exact' and pos < 300]
    fuzzy_matches = [(p, pos, t, s) for p, pos, t, s in matches if t == 'fuzzy']
    
    if exact_matches:
        exact_matches.sort(key=lambda x: x[1])
        return exact_matches[0][0], exact_matches[0][1]
    
    if fuzzy_matches:
        fuzzy_matches.sort(key=lambda x: -x[3])
        return fuzzy_matches[0][0], fuzzy_matches[0][1]
    
    return None, -1


def add_lecture_start_markers(content: str, pdf_pages: List[Dict]) -> str:
    """
    Füge Seitenzahlen am Anfang von Vorträgen hinzu.
    
    Erkennt Überschriften (# ...) und fügt |XX| am Anfang des ersten Absatzes ein.
    """
    lines = content.split('\n')
    result_lines = []
    
    i = 0
    lecture_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf Überschrift (beginnt mit # und enthält typische Vortragstitel-Merkmale)
        # z.B. "# DAS EWIGE UND DAS VERGÄNGLICHE DES MENSCHEN, Berlin, 6. September 1903"
        if line.strip().startswith('#') and not line.strip().startswith('# INHALT'):
            # Prüfe ob es ein Vortragstitel ist (enthält Ort und Datum)
            is_lecture_title = bool(re.search(r'\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}', line, re.IGNORECASE))
            
            if is_lecture_title:
                lecture_count += 1
                result_lines.append(line)
                i += 1
                
                # Überspringe Leerzeilen nach der Überschrift
                while i < len(lines) and not lines[i].strip():
                    result_lines.append(lines[i])
                    i += 1
                
                # Finde den ersten echten Absatz
                if i < len(lines):
                    first_para = lines[i]
                    
                    # Hat der Absatz schon einen Seitenmarker am Anfang?
                    if not re.match(r'^\|?\d+\|', first_para.strip()):
                        # Finde Seitenzahl für diesen Absatz
                        page_num, _ = find_page_for_text(first_para, pdf_pages)
                        
                        if page_num:
                            # Füge Seitenmarker am Anfang ein
                            result_lines.append(f"|{page_num}| {first_para.lstrip()}")
                            print(f"  Vortrag {lecture_count}: Seite {page_num}")
                            i += 1
                            continue
                    
                    result_lines.append(first_para)
                    i += 1
                continue
        
        result_lines.append(line)
        i += 1
    
    print(f"  {lecture_count} Vortragsanfänge verarbeitet")
    return '\n'.join(result_lines)


def is_heading(text: str) -> bool:
    """Prüfe ob ein Text eine Überschrift ist (beginnt mit #)."""
    return text.strip().startswith('#')


def is_lecture_title(text: str) -> bool:
    """Prüfe ob ein Text eine Vortragsüberschrift ist (mit Datum)."""
    if not text.strip().startswith('#'):
        return False
    return bool(re.search(
        r'\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}',
        text, re.IGNORECASE
    ))


def process_content(content: str, pdf_pages: List[Dict]) -> str:
    """Verarbeite Content und ersetze --- Marker."""
    marker_pattern = r'(\n*\s*---\s*\n*)'
    parts = re.split(marker_pattern, content)
    
    result = []
    marker_count = 0
    found_count = 0
    skipped_count = 0
    
    i = 0
    while i < len(parts):
        part = parts[i]
        
        if re.match(r'^\n*\s*---\s*\n*$', part):
            marker_count += 1
            
            text_before = parts[i - 1] if i > 0 else ""
            text_after = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Prüfe ob nach dem Marker eine neue Vortragsüberschrift kommt
            # In diesem Fall: kein Seitenmarker am Ende des vorherigen Vortrags
            first_line_after = ""
            for ln in text_after.lstrip().split('\n'):
                if ln.strip():
                    first_line_after = ln.strip()
                    break
            
            if is_heading(first_line_after):
                # Überspringe Seitenmarker vor Überschriften
                skipped_count += 1
                result.append('\n\n')  # Nur Absatzumbruch, kein Marker
                i += 1
                continue
            
            # Finde letzte/erste echte Textzeile
            before_lines = text_before.rstrip().split('\n')
            line_before = ""
            for ln in reversed(before_lines):
                stripped = ln.strip()
                if stripped and not stripped.startswith('#'):
                    line_before = stripped
                    break
            
            after_lines = text_after.lstrip().split('\n')
            line_after = ""
            for ln in after_lines:
                stripped = ln.strip()
                if stripped and not stripped.startswith('#'):
                    line_after = stripped
                    break
            
            # Finde Seitenzahl
            page_num, _ = find_page_for_text(text_after, pdf_pages)
            
            if page_num:
                found_count += 1
                
                is_hyphenated = line_before.endswith('-')
                is_paragraph = (
                    line_before and line_before[-1] in '.!?:;»"' and
                    line_after and line_after[0].isupper()
                )
                
                if is_hyphenated:
                    # SILBENTRENNUNG
                    if result:
                        prev = result[-1].rstrip()
                        if prev.endswith('-'):
                            result[-1] = prev[:-1]
                    result.append(f"|{page_num}|")
                    if i + 1 < len(parts):
                        parts[i + 1] = parts[i + 1].lstrip()
                
                elif is_paragraph:
                    # ABSATZUMBRUCH - Marker am Anfang des neuen Absatzes
                    result.append(f"\n\n|{page_num}| ")
                    if i + 1 < len(parts):
                        parts[i + 1] = parts[i + 1].lstrip()
                
                else:
                    # FLIESSTEXT
                    if result:
                        result[-1] = result[-1].rstrip()
                    result.append(f" |{page_num}| ")
                    if i + 1 < len(parts):
                        parts[i + 1] = parts[i + 1].lstrip()
                
                if marker_count % 50 == 0:
                    print(f"  [{marker_count}] Seite {page_num}")
            else:
                result.append(part)
                if marker_count % 50 == 0:
                    print(f"  [{marker_count}] ?")
        else:
            result.append(part)
        
        i += 1
    
    print(f"\n  {found_count}/{marker_count} Marker mit Seitenzahlen")
    if skipped_count:
        print(f"  {skipped_count} Marker vor Überschriften übersprungen")
    
    output = ''.join(result)
    output = re.sub(r'\n{4,}', '\n\n\n', output)
    # Entferne Leerzeichen vor #
    output = re.sub(r' +(#)', r'\1', output)
    return output


def main():
    parser = argparse.ArgumentParser(description='Seitenzahlen zu --- hinzufügen (v2)')
    parser.add_argument('md_file', help='MD-Datei mit --- Markern')
    parser.add_argument('--pdf', required=True, help='PDF-Datei')
    parser.add_argument('--output', '-o', help='Ausgabedatei')
    
    args = parser.parse_args()
    
    md_path = Path(args.md_file)
    pdf_path = Path(args.pdf)
    
    if not md_path.exists():
        sys.exit(f"MD nicht gefunden: {md_path}")
    if not pdf_path.exists():
        sys.exit(f"PDF nicht gefunden: {pdf_path}")
    
    print(f"Lade: {md_path.name}")
    content = md_path.read_text(encoding='utf-8')
    
    print(f"PDF: {pdf_path.name}")
    pages = extract_pdf_pages(pdf_path)
    print(f"  {len(pages)} Seiten")
    
    # Schritt 1: --- Marker verarbeiten
    print("\nVerarbeite --- Marker...")
    result = process_content(content, pages)
    
    # Schritt 2: Vortragsanfänge markieren
    print("\nVerarbeite Vortragsanfänge...")
    result = add_lecture_start_markers(result, pages)
    
    output_path = Path(args.output) if args.output else md_path.parent / f"{md_path.stem}_with_pages.md"
    output_path.write_text(result, encoding='utf-8')
    print(f"\nGespeichert: {output_path}")


if __name__ == '__main__':
    main()
