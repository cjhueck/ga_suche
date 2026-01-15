#!/usr/bin/env python3
"""
Bereitet MD-Referenzdateien für GA-Bände für die Verwendung vor.

Transformationen:
1. Entfernt Copyright-Zeilen
2. Entfernt bibliographische Angaben am Anfang, Inhaltsverzeichnis und Hinweise am Ende
3. Behält nur die Vorträge
4. Wandelt "# Fragebeantwortung" in "## Fragebeantwortung" um
5. Formatiert Vortragstitel (einzeilig und zweizeilig)
6. Verarbeitet Seitenumbrüche (---)
7. Fügt automatisch Seitenzahlen aus PDF hinzu

Verwendung:
    python tools/final_from_mistral_md.py <MD-Datei> --pdf <PDF-Datei> [--output <Ausgabedatei>]
"""

import os
import sys
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def remove_copyright_lines(content: str) -> str:
    """Entferne Copyright-Zeilen und 'Seite: XX' Zeilen."""
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Entferne Copyright-Zeilen (case-insensitive, verschiedene Varianten)
        if 'copyright' in line_lower and 'rudolf steiner' in line_lower:
            continue
        if 'copyright' in line_lower and 'nachlass' in line_lower:
            continue
        if 'copyright' in line_lower and 'nachlaß' in line_lower:
            continue
        # Entferne Zeilen mit "Buch:" und "Seite:" (Copyright-Marker)
        if 'buch:' in line_lower and 'seite:' in line_lower:
            continue
        # Entferne einzelne "Seite: XX" Zeilen
        if line_stripped.startswith('Seite:') or line_lower.startswith('seite:'):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def extract_lectures_only(content: str) -> str:
    """
    Extrahiert nur die Vorträge aus dem Dokument.
    Entfernt:
    - Bibliographische Angaben am Anfang (vor dem ersten Vortrag)
    - Inhaltsverzeichnis (# INHALT oder ähnlich)
    - Hinweise am Ende (nach dem letzten Vortrag)
    """
    lines = content.split('\n')
    
    # Finde den ersten Vortrag (H1 mit Datum)
    first_lecture_idx = None
    last_lecture_end_idx = None
    
    # Pattern für Vortragstitel: H1 mit Ort und Datum
    lecture_pattern = re.compile(
        r'^#\s+[A-ZÄÖÜ].*,\s*\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}',
        re.IGNORECASE
    )
    
    # Alternative: H1 in Großbuchstaben gefolgt von Datum in nächsten Zeilen
    h1_caps_pattern = re.compile(r'^#\s+[A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+$')
    date_pattern = re.compile(r'^[A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*\d{4}$')
    
    # Inhaltsverzeichnis-Pattern
    toc_pattern = re.compile(r'^#\s*(INHALT|Inhalt|INHALTSVERZEICHNIS|Inhaltsverzeichnis)\s*$', re.IGNORECASE)
    
    # Hinweise-Pattern (am Ende)
    notes_pattern = re.compile(r'^#\s*(HINWEISE|Hinweise|ANMERKUNGEN|Anmerkungen|ZU DIESER AUSGABE)\s*$', re.IGNORECASE)
    
    i = 0
    in_toc = False
    lecture_indices = []  # (start_idx, end_idx) für jeden Vortrag
    current_lecture_start = None
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Prüfe auf Inhaltsverzeichnis
        if toc_pattern.match(line):
            in_toc = True
            i += 1
            continue
        
        # Prüfe auf Hinweise am Ende
        if notes_pattern.match(line):
            # Alles ab hier ignorieren
            if current_lecture_start is not None:
                lecture_indices.append((current_lecture_start, i - 1))
            break
        
        # Prüfe auf Vortragstitel (mit Datum in Zeile)
        if lecture_pattern.match(line):
            in_toc = False
            if current_lecture_start is not None:
                lecture_indices.append((current_lecture_start, i - 1))
            current_lecture_start = i
            i += 1
            continue
        
        # Prüfe auf H1 in Großbuchstaben (könnte Vortragstitel sein)
        if h1_caps_pattern.match(line) and not toc_pattern.match(line):
            # Prüfe ob in den nächsten 5 Zeilen ein Datum kommt
            found_date = False
            for j in range(i + 1, min(i + 6, len(lines))):
                if date_pattern.match(lines[j].strip()):
                    found_date = True
                    break
            
            if found_date:
                in_toc = False
                if current_lecture_start is not None:
                    lecture_indices.append((current_lecture_start, i - 1))
                current_lecture_start = i
        
        i += 1
    
    # Letzten Vortrag hinzufügen
    if current_lecture_start is not None:
        lecture_indices.append((current_lecture_start, len(lines) - 1))
    
    if not lecture_indices:
        print("  WARNUNG: Keine Vorträge gefunden, behalte gesamten Inhalt")
        return content
    
    # Extrahiere nur die Vorträge
    result_lines = []
    for start_idx, end_idx in lecture_indices:
        # Entferne führende Leerzeilen
        while start_idx <= end_idx and not lines[start_idx].strip():
            start_idx += 1
        # Entferne nachfolgende Leerzeilen
        while end_idx >= start_idx and not lines[end_idx].strip():
            end_idx -= 1
        
        if start_idx <= end_idx:
            result_lines.extend(lines[start_idx:end_idx + 1])
            result_lines.append('')  # Leerzeile zwischen Vorträgen
    
    print(f"  {len(lecture_indices)} Vorträge extrahiert")
    return '\n'.join(result_lines)


def convert_fragebeantwortung_to_h2(content: str) -> str:
    """
    Wandelt H1-Überschriften 'Fragebeantwortung' in H2 um.
    # Fragebeantwortung → ## Fragebeantwortung
    """
    # Pattern für verschiedene Schreibweisen
    patterns = [
        (r'^#\s+(Fragebeantwortung)\s*$', r'## \1'),
        (r'^#\s+(FRAGEBEANTWORTUNG)\s*$', r'## \1'),
        (r'^#\s+(Frage[-\s]?beantwortung)\s*$', r'## \1'),
        (r'^#\s+(Fragenbeantwortung)\s*$', r'## \1'),
        (r'^#\s+(FRAGENBEANTWORTUNG)\s*$', r'## \1'),
    ]
    
    lines = content.split('\n')
    result = []
    count = 0
    
    for line in lines:
        modified = False
        for pattern, replacement in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                count += 1
                modified = True
                break
        result.append(line)
    
    if count > 0:
        print(f"  {count} Fragebeantwortungen zu H2 konvertiert")
    
    return '\n'.join(result)


def format_lecture_titles(content: str, ga_number: str = "") -> str:
    """
    Formatiere Vortragstitel:
    - Einzeilig: "# TITEL\n\nBerlin, Datum" → "# TITEL, Berlin, Datum"
    - Zweizeilig: "# TITEL\n## UNTERTITEL\n\nBerlin, Datum" → "# TITEL -  UNTERTITEL, Berlin, Datum"
    
    Args:
        content: Der MD-Inhalt
        ga_number: GA-Nummer (optional, für Debugging)
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf H1-Überschrift (Vortragstitel) - muss in Großbuchstaben sein
        h1_match = re.match(r'^#\s+([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+)$', line)
        if h1_match:
            title1 = h1_match.group(1).strip()
            
            # Prüfe ob nächste Zeile H2 ist (zweizeiliger Titel)
            if i + 1 < len(lines):
                h2_match = re.match(r'^##\s+(.+)$', lines[i + 1])
                if h2_match:
                    title2 = h2_match.group(1).strip()
                    
                    # Suche nach Datum in den nächsten 5 Zeilen (kann leere Zeilen dazwischen sein)
                    date = None
                    date_idx = None
                    for j in range(i + 2, min(i + 7, len(lines))):
                        stripped = lines[j].strip()
                        if not stripped:
                            continue  # Überspringe leere Zeilen
                        # Erweitere Regex für Datum: unterstütze Umlaute und verschiedene Formate
                        date_match = re.match(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*\d+\.\s+[A-ZÄÖÜ][a-zäöüß]+\s+\d{4})$', stripped)
                        if date_match:
                            date = date_match.group(1)
                            date_idx = j
                            break
                    
                    if date:
                        # Kombiniere zu: # TITEL -  UNTERTITEL, Datum (mit zwei Leerzeichen nach Bindestrich)
                        result.append(f"# {title1} -  {title2}, {date}")
                        # Überspringe H1, H2, leere Zeilen und Datum
                        i = date_idx + 1
                        continue
            
            # Einzeiliger Titel: Suche nach Datum in den nächsten 5 Zeilen
            date = None
            date_idx = None
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue  # Überspringe leere Zeilen
                if stripped.startswith('Seite:'):
                    continue  # Überspringe "Seite: XX" Zeilen
                # Unterstütze auch Umlaute im Datum
                date_match = re.match(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*\d+\.\s+[A-ZÄÖÜ][a-zäöüß]+\s+\d{4})$', stripped)
                if date_match:
                    date = date_match.group(1)
                    date_idx = j
                    break
            
            if date:
                # Kombiniere zu: # TITEL, Datum
                result.append(f"# {title1}, {date}")
                # Überspringe H1, leere Zeilen und Datum
                i = date_idx + 1
                continue
        
        # Normale Zeile
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def process_page_breaks(content: str) -> str:
    """
    Verarbeite Seitenumbrüche (---):
    - Entferne Seitenumbrüche innerhalb von Absätzen (in Fließtext verwandeln)
    - Behalte Seitenumbrüche zwischen Absätzen als Marker
    
    WICHTIG: Sei konservativ - entferne nur eindeutige Fälle innerhalb von Absätzen!
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf Seitenumbruchmarker (---)
        if line.strip() == '---':
            # Finde vorherige nicht-leere Zeile (ignoriere Überschriften und leere Zeilen)
            prev_idx = i - 1
            prev_text = None
            prev_line_idx = None
            while prev_idx >= 0:
                stripped = lines[prev_idx].strip()
                if stripped and not stripped.startswith('#'):
                    prev_text = stripped
                    prev_line_idx = prev_idx
                    break
                prev_idx -= 1
            
            # Finde nächste nicht-leere Zeile (ignoriere Überschriften und leere Zeilen)
            next_idx = i + 1
            next_text = None
            next_line_idx = None
            while next_idx < len(lines):
                stripped = lines[next_idx].strip()
                if stripped and not stripped.startswith('#'):
                    next_text = stripped
                    next_line_idx = next_idx
                    break
                next_idx += 1
            
            # Entscheide: Seitenumbruch zwischen Absätzen oder innerhalb?
            if prev_text and next_text:
                # Prüfe ob vorherige Zeile mit Satzzeichen endet (Absatzende)
                prev_ends_sentence = prev_text.endswith(('.', '!', '?', ':', ';', '»', '"'))
                
                # Prüfe ob nächste Zeile mit Großbuchstabe beginnt (neuer Satz/Absatz)
                next_starts_capital = next_text[0].isupper() if next_text else False
                
                # Prüfe ob vorherige Zeile bereits in result ist
                prev_in_result = result and result[-1].strip() == prev_text
                
                # NUR entfernen wenn:
                # 1. Vorherige Zeile endet NICHT mit Satzzeichen UND
                # 2. Nächste Zeile beginnt mit Kleinbuchstabe UND
                # 3. Vorherige Zeile ist bereits in result UND
                # 4. Es gibt keine leere Zeile zwischen prev und --- UND
                # 5. Es gibt keine leere Zeile zwischen --- und next
                # → eindeutiger Fall: Worttrennung innerhalb eines Absatzes
                
                # Prüfe ob leere Zeilen zwischen prev und --- oder --- und next
                has_empty_before = False
                has_empty_after = False
                if prev_line_idx is not None and i - prev_line_idx > 1:
                    # Prüfe Zeilen zwischen prev und ---
                    for k in range(prev_line_idx + 1, i):
                        if not lines[k].strip():
                            has_empty_before = True
                            break
                if next_line_idx is not None and next_line_idx - i > 1:
                    # Prüfe Zeilen zwischen --- und next
                    for k in range(i + 1, next_line_idx):
                        if not lines[k].strip():
                            has_empty_after = True
                            break
                
                if (not prev_ends_sentence and next_text[0].islower() and 
                    prev_in_result and not has_empty_before and not has_empty_after):
                    # Seitenumbruch innerhalb eines Absatzes → entfernen und verbinden
                    result.pop()  # Entferne letzte Zeile
                    
                    # Verbinde: Worttrennung ohne Leerzeichen
                    combined = prev_text + next_text
                    result.append(combined)
                    # Überspringe die nächste Zeile, da bereits verbunden
                    i = next_line_idx
                    continue
                else:
                    # Seitenumbruch zwischen Absätzen oder unsicher → Marker behalten
                    result.append('---')
            else:
                # Am Anfang oder Ende → Marker behalten
                result.append('---')
        else:
            result.append(line)
        
        i += 1
    
    return '\n'.join(result)


def extract_ga_number(filepath: Path) -> str:
    """Extrahiere GA-Nummer aus Dateinamen oder Pfad."""
    # Suche nach GA gefolgt von Zahlen
    match = re.search(r'GA\s*(\d+)', str(filepath), re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def find_pdf_file(input_path: Path) -> Optional[Path]:
    """Finde die passende PDF-Datei im selben Verzeichnis."""
    # Suche nach PDF mit gleichem Basisnamen
    pdf_candidates = [
        input_path.with_suffix('.pdf'),
        input_path.parent / f"{input_path.stem.replace('_prepared', '')}.pdf",
    ]
    
    # Suche auch nach PDFs mit ähnlichem Namen
    for pdf_file in input_path.parent.glob('*.pdf'):
        pdf_candidates.append(pdf_file)
    
    for pdf_path in pdf_candidates:
        if pdf_path.exists():
            return pdf_path
    
    return None


def run_add_page_numbers(md_path: Path, pdf_path: Path, output_path: Path) -> bool:
    """
    Führt add_page_numbers_from_pdf_v2.py aus.
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    script_path = Path(__file__).parent / 'add_page_numbers_from_pdf_v2.py'
    
    if not script_path.exists():
        print(f"  WARNUNG: Skript nicht gefunden: {script_path}")
        return False
    
    print(f"\n5. Füge Seitenzahlen aus PDF hinzu...")
    print(f"   PDF: {pdf_path.name}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(md_path), '--pdf', str(pdf_path), '-o', str(output_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Zeige relevante Ausgabe
            for line in result.stdout.split('\n'):
                if 'Marker' in line or 'Vortrag' in line or 'Gespeichert' in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"   FEHLER: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   FEHLER: {e}")
        return False


def prepare_reference_md(input_path: Path, pdf_path: Path = None, output_path: Path = None) -> str:
    """
    Hauptfunktion: Bereite MD-Referenzdatei vor.
    
    Args:
        input_path: Pfad zur Eingabe-MD-Datei
        pdf_path: Pfad zur PDF-Datei (optional, wird automatisch gesucht)
        output_path: Pfad zur Ausgabe-MD-Datei (optional)
    
    Returns:
        Der vorbereitete Inhalt als String
    """
    print(f"Lade Datei: {input_path.name}")
    content = input_path.read_text(encoding='utf-8')
    original_size = len(content)
    
    # Extrahiere GA-Nummer für Debugging
    ga_number = extract_ga_number(input_path)
    if ga_number:
        print(f"  GA-Nummer erkannt: GA{ga_number}")
    
    print("\n1. Entferne Copyright-Zeilen...")
    content = remove_copyright_lines(content)
    
    print("2. Extrahiere nur Vorträge (ohne Bibliographie, Inhalt, Hinweise)...")
    content = extract_lectures_only(content)
    
    print("3. Konvertiere Fragebeantwortungen zu H2...")
    content = convert_fragebeantwortung_to_h2(content)
    
    print("4. Formatiere Vortragstitel und verarbeite Seitenumbrüche...")
    content = format_lecture_titles(content, ga_number)
    content = process_page_breaks(content)
    
    # Speichere Zwischenergebnis (_prepared.md)
    prepared_path = input_path.parent / f"{input_path.stem}_prepared.md"
    prepared_path.write_text(content, encoding='utf-8')
    print(f"\n   Zwischenergebnis: {prepared_path.name}")
    print(f"   Original: {original_size:,} Zeichen → Bearbeitet: {len(content):,} Zeichen")
    
    # Finde PDF-Datei falls nicht angegeben
    if pdf_path is None:
        pdf_path = find_pdf_file(input_path)
    
    # Finale Ausgabe mit Seitenzahlen
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_final.md"
    
    if pdf_path and pdf_path.exists():
        # Führe add_page_numbers aus
        success = run_add_page_numbers(prepared_path, pdf_path, output_path)
        if success:
            print(f"\n✓ Finale Ausgabe: {output_path.name}")
            return output_path.read_text(encoding='utf-8')
        else:
            print(f"\n   Seitenzahlen konnten nicht hinzugefügt werden.")
            print(f"   Ausgabe ohne Seitenzahlen: {prepared_path.name}")
            return content
    else:
        print(f"\n   WARNUNG: Keine PDF-Datei gefunden.")
        print(f"   Ausgabe ohne Seitenzahlen: {prepared_path.name}")
        return content


def main():
    parser = argparse.ArgumentParser(
        description='Bereitet MD-Referenzdateien für GA-Bände vor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python tools/final_from_mistral_md.py "Steiner, Rudolf GA 052, 1986 - ...md" --pdf "GA052.pdf"
  python tools/final_from_mistral_md.py "GA052/Steiner, Rudolf GA 052.md"
  
Das Skript:
1. Entfernt Copyright-Zeilen
2. Extrahiert nur Vorträge (ohne Bibliographie, Inhaltsverzeichnis, Hinweise)
3. Konvertiert "# Fragebeantwortung" zu "## Fragebeantwortung"
4. Formatiert Vortragstitel und verarbeitet Seitenumbrüche
5. Fügt automatisch Seitenzahlen aus der PDF hinzu
        """
    )
    parser.add_argument('input_file', help='Pfad zur MD-Referenzdatei')
    parser.add_argument('--pdf', help='Pfad zur PDF-Datei (wird automatisch gesucht wenn nicht angegeben)')
    parser.add_argument('--output', '-o', help='Ausgabedatei (Standard: <input>_final.md)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {input_path}")
        sys.exit(1)
    
    pdf_path = Path(args.pdf) if args.pdf else None
    output_path = Path(args.output) if args.output else None
    
    prepare_reference_md(input_path, pdf_path, output_path)


if __name__ == '__main__':
    main()
