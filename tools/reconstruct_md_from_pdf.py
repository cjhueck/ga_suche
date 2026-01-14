#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstruct MD-Dateien aus PDFs mit Erhaltung von Block-IDs und Metadaten

Workflow:
1. Lade bestehende MD-Dateien (für Metadaten und Block-IDs)
2. Extrahiere und bereinige PDF-Text
3. Übertrage Block-IDs durch Text-Matching
4. Erstelle neue MD-Dateien mit PDF-Struktur
5. Validiere Ergebnis
"""
import sys
import io
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz  # PyMuPDF
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Pfade
STEINER_GA_BASE = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
STEINER_GA_PDF = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')


def normalize_text(text: str) -> str:
    """Normalisiere Text für Vergleich (wie in anderen Tools)"""
    text = re.sub(r'\|\d+\|', '', text)  # Entferne Seitenmarker
    text = re.sub(r'\^[\w]+', '', text)  # Entferne Block-IDs
    text = re.sub(r'\s+', ' ', text)  # Normalisiere Leerzeichen
    text = re.sub(r'[^\w\säöüÄÖÜß]', '', text)  # Entferne Interpunktion
    return text.lower().strip()


def remove_syllable_breaks(text: str) -> str:
    """
    Entferne Silbentrennungen (Bindestrich am Zeilenende).
    WICHTIG: Muss vor join_lines_to_paragraphs aufgerufen werden!
    """
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Prüfe ob Zeile mit Bindestrich endet (Silbentrennung)
        if line.endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1].lstrip()
            if next_line:
                # Prüfe ob nächste Zeile mit Kleinbuchstabe beginnt (Silbentrennung)
                # ODER ob es ein zusammengesetztes Wort sein könnte
                if next_line[0].islower():
                    # Entferne Bindestrich und füge nächste Zeile direkt an
                    result.append(line[:-1] + next_line)
                    i += 2  # Überspringe nächste Zeile
                    continue
                # Auch wenn nächste Zeile mit Großbuchstabe beginnt, könnte es Silbentrennung sein
                # wenn die aktuelle Zeile sehr kurz ist (< 5 Zeichen)
                elif len(line) < 5:
                    result.append(line[:-1] + next_line)
                    i += 2
                    continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def extract_page_number_from_footer(lines: List[str]) -> Optional[int]:
    """Extrahiere Seitenzahl aus Footer (wie in apply_pagebreaks_from_pdf.py)"""
    # Suche von hinten nach vorne (letzte 15 Zeilen)
    for i in range(len(lines) - 1, max(-1, len(lines) - 15), -1):
        line = lines[i].strip()
        
        # Format: "186" oder "Seite 186"
        if line.isdigit():
            return int(line)
        match = re.match(r'^Seite\s+(\d+)\s*$', line, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def clean_pdf_text(text: str) -> Tuple[str, Optional[int], bool]:
    """
    Bereinige PDF-Text:
    - Entferne Copyright-Zeilen
    - Entferne Header/Footer
    - Entferne Silbentrennungen
    - Extrahiere Seitenzahl
    
    Rückgabe: (bereinigter Text, Seitenzahl, endet_mit_silbentrennung)
    """
    original_text = text
    lines = text.split('\n')
    
    # Format 1: Copyright-Zeile (auch mit OCR-Fehlern)
    copyright_match = re.search(
        r'Copyright\s+Rudolf\s+Stein\w*.*?Seite:\s*([\d\s]+)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    page_num = None
    if copyright_match:
        page_str = copyright_match.group(1).replace(" ", "").strip()
        if page_str.isdigit():
            page_num = int(page_str)
            # Entferne alles ab Copyright-Zeile
            text = text[:copyright_match.start()].strip()
            lines = text.split('\n')
    
    # Format 2-4: Verwende extract_page_number_from_footer
    if page_num is None:
        page_num = extract_page_number_from_footer(lines)
        if page_num is not None:
            # Entferne Footer-Zeilen vom Body
            for j in range(len(lines) - 1, -1, -1):
                stripped = lines[j].strip()
                if stripped == str(page_num):
                    text = "\n".join(lines[:j]).strip()
                    lines = text.split('\n')
                    break
                if re.match(rf"^Seite\s+{page_num}\s*$", stripped, re.IGNORECASE):
                    text = "\n".join(lines[:j]).strip()
                    lines = text.split('\n')
                    break
    
    # Entferne Footer-Elemente (RUDOLF STEINER, VERLAG, etc.)
    body_lines = []
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        # Überspringe Footer-Zeilen
        if any(x in line_upper for x in ["RUDOLF STEINER", "VERLAG", "NACHLASS", "COPYRIGHT"]):
            continue
        
        # Überspringe "Buch:XX" oder "Seite: XX" Zeilen
        if re.match(r'^(Buch|Seite):\s*\d+', line, re.IGNORECASE):
            continue
        
        # Überspringe isolierte Seitenzahlen am Ende
        if i >= len(lines) - 3 and line.strip().isdigit():
            if page_num and int(line.strip()) == page_num:
                continue
        
        body_lines.append(line)
    
    # Entferne Header "Seite XX" am Anfang
    while body_lines and re.match(rf"^Seite\s+\d+\s*$", body_lines[0].strip(), re.IGNORECASE):
        body_lines.pop(0)
    
    # WICHTIG: Prüfe BEVOR Silbentrennungen entfernt werden, ob die Seite mit einer endet
    ends_with_hyphen = False
    if body_lines:
        # Finde die letzte nicht-leere Zeile
        for line in reversed(body_lines):
            stripped = line.rstrip()
            if stripped:
                ends_with_hyphen = stripped.endswith('-')
                break
    
    text = "\n".join(body_lines)
    
    # Entferne Silbentrennungen (WICHTIG: vor dem Zusammenfügen)
    text = remove_syllable_breaks(text)
    
    # Zusammenfügen von Zeilen zu Fließtext (wie in pdf_to_md_converter.py)
    text = join_lines_to_paragraphs(text)
    
    # Normalisiere Gedankenstriche (NACH dem Zusammenfügen)
    text = normalize_dashes(text)
    
    # Debug: Prüfe Textlänge
    if len(text.strip()) < 100:
        print(f"      WARNUNG: Sehr wenig Text extrahiert ({len(text)} Zeichen)")
    
    return text.strip(), page_num, ends_with_hyphen


def normalize_dashes(text: str) -> str:
    """
    Normalisiere Gedankenstriche und Bindestriche:
    - Em-Dash (—) ohne Leerzeichen → mit Leerzeichen
    - Bindestrich nach Satzzeichen vor Großbuchstabe → Gedankenstrich
    """
    # Em-Dash (U+2014) und En-Dash (U+2013) ohne Leerzeichen → mit Leerzeichen
    # Aber NUR wenn nicht Teil eines Wortes (nicht zwischen Kleinbuchstaben)
    
    # Fall 1: Gedankenstrich nach Satzzeichen ohne Leerzeichen
    # z.B. "zusammen?—Man" → "zusammen? — Man"
    text = re.sub(r'([.!?])([—–-])([A-ZÄÖÜ])', r'\1 — \3', text)
    
    # Fall 2: Em-Dash/En-Dash ohne Leerzeichen davor
    # z.B. "Wort—anderes" → "Wort — anderes" (aber nur wenn Großbuchstabe folgt)
    text = re.sub(r'([a-zäöüß])([—–])([A-ZÄÖÜ])', r'\1 — \3', text)
    
    # Fall 3: Em-Dash/En-Dash ohne Leerzeichen danach
    # z.B. "—Wort" am Anfang → "— Wort"
    text = re.sub(r'([—–])([A-ZÄÖÜ])', r'— \2', text)
    
    # Fall 4: Einfacher Bindestrich nach Satzzeichen (vor Großbuchstabe)
    # z.B. "zusammen?-Man" → "zusammen? — Man"
    text = re.sub(r'([.!?])\s*-\s*([A-ZÄÖÜ])', r'\1 — \2', text)
    
    return text


def is_verse_line(line: str, ignore_page_marker: bool = True) -> bool:
    """
    Prüfe ob eine Zeile eine Gedichtzeile sein könnte.
    Kriterien:
    - Weniger als 55 Zeichen (inkl. Leerzeichen, ohne Seitenmarker)
    - Endet nicht mit Bindestrich (Silbentrennung)
    - Endet nicht mit Doppelpunkt (das wäre eine Prosa-Einleitung)
    - Enthält keinen Punkt gefolgt von Großbuchstabe (das wäre Prosa nach dem Gedicht)
    
    ignore_page_marker: Wenn True, wird |XXX| aus der Zeile entfernt bevor die Länge geprüft wird
    """
    line = line.strip()
    if not line:
        return False
    
    # Entferne Seitenmarker für die Längenprüfung
    line_for_check = line
    if ignore_page_marker:
        line_for_check = re.sub(r'\|\d+\|\s*', '', line)
    
    if len(line_for_check) >= 55:
        return False
    # Silbentrennungen sind keine Gedichtzeilen
    if line_for_check.endswith('-'):
        return False
    # Zeilen die mit Doppelpunkt enden sind Prosa-Einleitungen, keine Gedichtzeilen
    if line_for_check.endswith(':'):
        return False
    # Wenn die Zeile einen Punkt/!/? gefolgt von Leerzeichen und Großbuchstabe enthält,
    # ist es wahrscheinlich Gedicht + Prosa gemischt (z.B. "mit Donnergang. So muß es")
    if re.search(r'[.!?]\s+[A-ZÄÖÜ]', line_for_check):
        return False
    return True


def detect_verse_sequences(lines: List[str]) -> List[Tuple[int, int]]:
    """
    Finde Sequenzen von Gedichtzeilen im Text.
    Rückgabe: Liste von (start_index, end_index) für Gedichtblöcke.
    
    Ein Gedichtblock besteht aus mindestens 2 aufeinanderfolgenden kurzen Zeilen.
    Die erste Zeile darf nicht mit Punkt enden (das wäre Prosa-Ende).
    Gedichte können durch Seitenmarker (|XXX|) unterbrochen sein - diese werden ignoriert.
    """
    sequences = []
    i = 0
    
    while i < len(lines):
        # Suche nach Start einer möglichen Verssequenz
        if is_verse_line(lines[i]):
            start = i
            # Zähle aufeinanderfolgende kurze Zeilen (Seitenmarker werden ignoriert)
            while i < len(lines) and is_verse_line(lines[i]):
                i += 1
            end = i
            
            # Mindestens 2 Zeilen für ein Gedicht
            if end - start >= 2:
                # Prüfe ob die erste Zeile mit Punkt endet → wahrscheinlich Prosa-Ende
                # Entferne dabei Seitenmarker für die Prüfung
                first_line = re.sub(r'\|\d+\|\s*', '', lines[start].strip())
                if first_line.endswith('.'):
                    # Überspringe diese Zeile, starte Sequenz ab der nächsten
                    start += 1
                
                # Nochmal prüfen ob mindestens 2 Zeilen übrig
                if end - start >= 2:
                    sequences.append((start, end))
        else:
            i += 1
    
    return sequences


def join_lines_to_paragraphs(text: str) -> str:
    """
    Füge Zeilen zu Absätzen zusammen (wie in pdf_to_md_converter.py).
    Entfernt falsche Zeilenumbrüche, behält echte Absätze.
    ERKENNT GEDICHTE und behält deren Zeilenstruktur bei.
    """
    if not text.strip():
        return text
    
    lines = text.split('\n')
    
    # Finde Gedichtsequenzen
    verse_sequences = detect_verse_sequences(lines)
    
    # Erstelle ein Set von Zeilenindizes, die zu Gedichten gehören
    verse_lines = set()
    for start, end in verse_sequences:
        for idx in range(start, end):
            verse_lines.add(idx)
    
    out = []
    
    for i, curr in enumerate(lines):
        prev = out[-1] if out else None
        
        # Leere Zeilen bleiben als Absatz-Trenner
        if not curr.strip():
            if prev and prev.strip():  # Nur wenn vorherige Zeile nicht leer war
                out.append('')
            continue
        
        # Erste Zeile
        if not prev:
            out.append(curr.strip())
            continue
        
        prev_trim = prev.rstrip()
        
        # Wenn vorherige Zeile leer war, starte neuen Absatz
        if not prev_trim:
            out.append(curr.strip())
            continue
        
        curr_stripped = curr.strip()
        if not curr_stripped:
            continue
        
        last_char = prev_trim[-1] if prev_trim else ''
        first_char = curr_stripped[0] if curr_stripped else ''
        
        # GEDICHTERKENNUNG: Wenn diese Zeile Teil eines Gedichts ist
        if i in verse_lines:
            is_first_verse_line = (i - 1) not in verse_lines
            
            if is_first_verse_line:
                # Erste Zeile eines Gedichts → Absatzabstand davor
                if out and out[-1].strip():
                    out.append('')  # Leerzeile vor dem Gedicht
                out.append(curr_stripped)
            else:
                # Folgezeile im Gedicht → Markdown-Zeilenumbruch (zwei Leerzeichen)
                if not prev_trim.endswith('  '):
                    out[-1] = prev_trim + '  '
                out.append(curr_stripped)
            continue
        
        # Prüfe ob VORHERIGE Zeile die LETZTE eines Gedichts war → Absatzabstand danach
        if (i - 1) in verse_lines:
            if out and out[-1].strip():
                out.append('')  # Leerzeile nach dem Gedicht
            out.append(curr_stripped)
            continue
        
        # Silbentrennung mit Bindestrich → OHNE Leerzeichen zusammenfügen
        if last_char in '-–—' and first_char.islower():
            out[-1] = prev_trim[:-1] + curr_stripped
        # Wenn vorherige Zeile mit Punkt/Komma endet und nächste mit Großbuchstabe beginnt → prüfe ob neuer Absatz
        elif last_char in '.!?' and first_char.isupper():
            # Prüfe ob es wirklich ein neuer Absatz ist (nicht nur neuer Satz)
            # Wenn vorherige Zeile sehr kurz ist (< 50 Zeichen), wahrscheinlich Überschrift → neuer Absatz
            if len(prev_trim) < 50:
                out.append(curr_stripped)
            else:
                # Normaler Satzende → zusammenfügen mit Leerzeichen
                out[-1] = prev_trim + ' ' + curr_stripped
        # Wenn vorherige Zeile mit Kleinbuchstabe endet → zusammenfügen
        elif last_char.islower() or last_char in ',;:':
            out[-1] = prev_trim + ' ' + curr_stripped
        # Wenn vorherige Zeile mit Großbuchstabe endet und nächste mit Großbuchstabe beginnt → prüfe
        elif last_char.isupper() and first_char.isupper():
            # Wenn vorherige Zeile sehr kurz (< 30 Zeichen), wahrscheinlich Überschrift → neuer Absatz
            if len(prev_trim) < 30:
                out.append(curr_stripped)
            else:
                # Zusammenfügen mit Leerzeichen
                out[-1] = prev_trim + ' ' + curr_stripped
        # Alles andere → MIT Leerzeichen zusammenfügen
        else:
            out[-1] = prev_trim + ' ' + curr_stripped
    
    # Füge Leerzeilen zwischen Absätzen ein (wenn Zeile mit Punkt endet und nächste mit Großbuchstabe beginnt)
    result_lines = []
    for i, line in enumerate(out):
        result_lines.append(line)
        # Wenn Zeile mit Punkt endet UND nächste Zeile mit Großbuchstabe beginnt → Leerzeile einfügen
        if line.strip() and line.strip()[-1] in '.!?' and i + 1 < len(out):
            next_line = out[i + 1]
            if (next_line.strip() and 
                not next_line.startswith(('#', '!', '[')) and
                next_line.strip()[0].isupper() and
                len(line.strip()) > 50):  # Nur bei längeren Absätzen
                result_lines.append('')
    
    return '\n'.join(result_lines)


def extract_lecture_from_pdf(pdf_path: Path, start_page: int, end_page: int) -> List[Tuple[int, str, bool]]:
    """
    Extrahiere Vortrag aus PDF (Seitenbereich).
    Rückgabe: Liste von (Seitenzahl, bereinigter Text, endet_mit_silbentrennung)
    """
    doc = fitz.open(pdf_path)
    pages_data = []
    
    # Sammle alle Seiten mit Seitenzahlen
    all_pages = []
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        if not text.strip():
            continue
        
        # Bereinige Text
        cleaned_text, page_num, ends_with_hyphen = clean_pdf_text(text)
        
        if page_num is not None:
            all_pages.append((i, page_num, cleaned_text, ends_with_hyphen))
    
    doc.close()
    
    # Sortiere nach Seitenzahl
    all_pages.sort(key=lambda x: x[1])
    
    # Filtere nach gewünschtem Bereich
    for pdf_idx, page_num, cleaned_text, ends_with_hyphen in all_pages:
        if start_page <= page_num <= end_page:
            pages_data.append((page_num, cleaned_text, ends_with_hyphen))
    
    return pages_data


def find_md_files_for_ga(ga_number: str) -> List[Path]:
    """Finde alle MD-Dateien für eine GA"""
    ga_norm = ga_number.upper().replace('GA', '').zfill(3)
    ga_folder = STEINER_GA_BASE / f"GA{ga_norm}-*"
    
    # Finde GA-Ordner
    folders = list(STEINER_GA_BASE.glob(f"GA{ga_norm}-*"))
    if not folders:
        return []
    
    md_files = []
    for folder in folders:
        md_files.extend(folder.glob("*.md"))
    
    return md_files


def extract_block_ids_from_md(md_content: str) -> List[Tuple[str, str]]:
    """
    Extrahiere Block-IDs aus MD-Text.
    Rückgabe: Liste von (normalisierter Text, Block-ID)
    """
    block_ids = []
    
    # Suche nach Block-IDs am Ende von Absätzen: ^xxxxx
    paragraphs = re.split(r'\n\n+', md_content)
    
    for para in paragraphs:
        # Suche Block-ID am Ende
        match = re.search(r'\^([a-z0-9]+)\s*$', para)
        if match:
            block_id = match.group(1)
            # Entferne Block-ID und Seitenmarker für Normalisierung
            para_text = re.sub(r'\^[a-z0-9]+\s*$', '', para)
            para_text = re.sub(r'\|\d+\|', '', para_text)
            normalized = normalize_text(para_text)
            if normalized:
                block_ids.append((normalized, block_id))
    
    return block_ids


def find_matching_block_id(text: str, block_ids: List[Tuple[str, str]], threshold: float = 0.8) -> Optional[str]:
    """
    Finde passende Block-ID für Text durch Text-Matching.
    Verwendet SequenceMatcher für Ähnlichkeitsvergleich.
    """
    from difflib import SequenceMatcher
    
    text_norm = normalize_text(text)
    if not text_norm:
        return None
    
    best_match = None
    best_ratio = 0.0
    
    for norm_text, block_id in block_ids:
        ratio = SequenceMatcher(None, text_norm, norm_text).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = block_id
    
    return best_match


def extract_metadata_from_md(md_content: str) -> Dict:
    """Extrahiere Metadaten aus MD-Datei"""
    metadata = {
        'title': None,
        'date': None,
        'location': None,
        'source': None
    }
    
    lines = md_content.split('\n')
    
    # Suche nach Quelle-Link
    for line in lines[:10]:
        if 'Quelle:' in line or '[[GA' in line:
            metadata['source'] = line.strip()
            break
    
    # Suche nach Titel im Dateinamen oder ersten Zeilen
    # Titel könnte im Dateinamen sein oder in ersten Zeilen
    for line in lines[:20]:
        # Suche nach Datum (verschiedene Formate)
        date_match = re.search(r'(\d{1,2}\.\s*\w+\s*\d{4})', line)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # Suche nach Ort
        if any(ort in line for ort in ['Berlin', 'München', 'Dornach', 'Stuttgart', 'Wien']):
            if not metadata['location']:
                metadata['location'] = line.strip()
    
    return metadata


def remove_lecture_header(text: str) -> str:
    """
    Entferne Vortragstitel, Ort und Datum vom Anfang des Textes.
    Diese Informationen sind bereits im Dateinamen enthalten.
    
    Typisches Muster:
    "TITEL IN GROSSBUCHSTABEN Berlin, 14. Januar 1909 Der eigentliche Text..."
    oder mehrzeilig:
    "TITEL  
    UNTERTITEL  
    Berlin, 14. Januar 1909 Der eigentliche Text..."
    """
    # Normalisiere zuerst: Ersetze "  \n" (Markdown-Zeilenumbruch) durch normalen Zeilenumbruch
    # für die Header-Erkennung
    text_normalized = re.sub(r'  \n', '\n', text)
    
    # Muster für Ort und Datum
    orte = r'(?:Berlin|München|Dornach|Stuttgart|Wien|Hamburg|Köln|Leipzig|Nürnberg|Basel|Zürich|Kassel|Kristiania|Oslo|Den Haag|London|Paris|Prag|Bern|Breslau|Dresden|Frankfurt|Hannover|Karlsruhe|Mannheim|Pforzheim|Penmaenmawr|Torquay|Stratford|Oxford|Ilkley|Arnheim)'
    datum = r'\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}'
    
    # Muster 1: GROSSBUCHSTABEN-TITEL (eine Zeile) gefolgt von Ort, Datum
    # z.B. "GESUNDHEITSFRAGEN IM LICHTE DER GEISTESWISSENSCHAFT Berlin, 14. Januar 1909"
    pattern1 = rf'^([A-ZÄÖÜ\s«»\-\?!]+?)\s*{orte},?\s*{datum}\s*'
    
    match = re.match(pattern1, text_normalized, re.IGNORECASE)
    if match:
        # Berechne wie viele Zeichen im Original-Text zu entfernen sind
        matched_text = match.group(0)
        # Finde diese Position im Original-Text (berücksichtige Markdown-Zeilenumbrüche)
        return _remove_matched_header(text, matched_text)
    
    # Muster 2: Mehrzeiliger Titel
    # z.B. "WO UND WIE FINDET MAN DEN GEIST?\nBerlin, 15. Oktober 1908"
    pattern2 = rf'^([A-ZÄÖÜ\s«»\-\?!]+)\n{orte},?\s*{datum}\s*'
    match = re.match(pattern2, text_normalized)
    if match:
        matched_text = match.group(0)
        return _remove_matched_header(text, matched_text)
    
    # Muster 3: Mehrzeiliger Titel mit Untertitel
    # z.B. "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\n0\n\nBerlin, 12. März 1909"
    # oder "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\nBerlin, 12. März 1909"
    # Erlaubt optionale Leerzeilen zwischen Titel und Ort/Datum
    pattern3 = rf'^([A-ZÄÖÜ\s«»\-\?!]+\n)+(\d+\n)?\n*{orte},?\s*{datum}\s*'
    match = re.match(pattern3, text_normalized)
    if match:
        matched_text = match.group(0)
        return _remove_matched_header(text, matched_text)
    
    # Muster 4: Nur Titel in GROSSBUCHSTABEN ohne Datum (am Anfang einer neuen Seite)
    # z.B. "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\n0\n"
    pattern4 = r'^([A-ZÄÖÜ\s«»\-\?!]+\n)+(0\n)?'
    match = re.match(pattern4, text_normalized)
    if match and len(match.group(0).strip()) > 10:  # Mindestens 10 Zeichen Titel
        # Nur entfernen, wenn es wirklich wie ein Titel aussieht (GROSSBUCHSTABEN)
        title_text = match.group(0).strip()
        if title_text.isupper() or (title_text.replace('«', '').replace('»', '').replace('\n', ' ').strip().isupper()):
            matched_text = match.group(0)
            return _remove_matched_header(text, matched_text)
    
    # Muster 5: Ort, Datum am Anfang (manchmal ohne Titel)
    pattern5 = rf'^{orte},?\s*{datum}\s*'
    match = re.match(pattern5, text_normalized, re.IGNORECASE)
    if match:
        matched_text = match.group(0)
        return _remove_matched_header(text, matched_text)
    
    # Muster 6: Ort, Datum nach Leerzeile (wenn Titel bereits entfernt wurde)
    # Manchmal bleibt nach der Titel-Entfernung noch "Ort, Datum" übrig
    pattern6 = rf'^\s*{orte},?\s*{datum}\s*'
    match = re.match(pattern6, text_normalized, re.IGNORECASE)
    if match:
        matched_text = match.group(0)
        return _remove_matched_header(text, matched_text)
    
    return text


def _remove_matched_header(original_text: str, matched_text: str) -> str:
    """
    Entferne den gematchten Header-Text aus dem Original.
    Berücksichtigt, dass im Original "  \n" statt "\n" stehen kann.
    """
    # Erzeuge eine Version des matched_text, die auch "  \n" matcht
    matched_len = len(matched_text)
    
    # Zähle wie viele "\n" im matched_text sind
    newline_count = matched_text.count('\n')
    
    # Im Original können diese als "  \n" vorliegen (2 extra Zeichen pro Newline)
    max_len = matched_len + (newline_count * 2)
    
    # Suche das Ende des Headers im Original
    # Normalisiere und vergleiche
    for i in range(matched_len, max_len + 5):
        if i > len(original_text):
            break
        original_chunk = original_text[:i]
        normalized_chunk = re.sub(r'  \n', '\n', original_chunk)
        if normalized_chunk == matched_text:
            return original_text[i:].strip()
    
    # Fallback: Einfach die gematchte Länge entfernen
    return original_text[matched_len:].strip()


def split_into_paragraphs(text: str, target_length: int = 500) -> List[str]:
    """
    Teile Text in sinnvolle Absätze.
    Da der PDF-Text bereits Fließtext ist (keine doppelten Leerzeilen),
    teilen wir bei Satzenden an geeigneten Stellen.
    
    WICHTIG: Erhält Markdown-Zeilenumbrüche (zwei Leerzeichen + \n) für Gedichte!
    """
    if len(text) < target_length:
        return [text] if text.strip() else []
    
    paragraphs = []
    current = ""
    
    # Teile bei echten Satzenden:
    # - Nicht nach Zahlen (Datum wie "14. Januar")
    # - Nicht nach einzelnen Großbuchstaben (Abkürzungen wie "Dr. A.")
    # - Nur wenn mindestens 2 Zeichen vor dem Punkt
    # ABER: Teile NICHT innerhalb von Gedichten (erkennbar an "  \n")
    
    # Strategie: Teile den Text in Sätze, aber behandle Gedichtblöcke als Einheit
    # Ein Gedichtblock ist Text, der "  \n" (zwei Leerzeichen + Newline) enthält
    
    # Teile bei Satzenden, ABER erhalte die Gedichtblöcke
    # Regex: Teile bei [kleinbuchstabe.!?][leerzeichen][Großbuchstabe]
    # ABER nicht bei "  \n" (Gedichtzeile)
    
    # Zuerst: Ersetze Gedicht-Zeilenumbrüche durch Platzhalter
    VERSE_BREAK = "<<VERSE_BREAK>>"
    text_with_markers = text.replace('  \n', VERSE_BREAK)
    
    # Jetzt teile bei Satzenden (ohne Gedichtzeilen zu zerstören)
    sentences = re.split(r'(?<=[a-zäöüß][.!?])\s+(?=[A-ZÄÖÜ])', text_with_markers)
    
    for sentence in sentences:
        # Stelle Gedicht-Zeilenumbrüche wieder her
        sentence = sentence.replace(VERSE_BREAK, '  \n').strip()
        if not sentence:
            continue
        
        # Wenn current + sentence zu lang wird, speichere current und starte neu
        if current and len(current) + len(sentence) > target_length:
            paragraphs.append(current.strip())
            current = sentence
        else:
            if current:
                current += " " + sentence
            else:
                current = sentence
    
    # Rest hinzufügen
    if current.strip():
        paragraphs.append(current.strip())
    
    return paragraphs


def merge_pages_with_markers(pdf_pages: List[Tuple[int, str, bool]]) -> str:
    """
    Füge alle PDF-Seiten zusammen mit korrekten Seitenmarkern.
    
    Seitenmarker werden eingefügt:
    - Am Absatzanfang: |186| Text...
    - Mitten im Satz: ...Text |187| Text...
    - Bei Silbentrennung OHNE Leerzeichen: ...Denk|188|weise...
    
    Args:
        pdf_pages: Liste von (Seitenzahl, Text, endet_mit_silbentrennung)
    """
    if not pdf_pages:
        return ""
    
    result = ""
    prev_ends_with_hyphen = False
    
    for i, (page_num, page_text, ends_with_hyphen) in enumerate(pdf_pages):
        page_text = page_text.strip()
        if not page_text:
            continue
        
        marker = f"|{page_num}|"
        
        if i == 0:
            # Erste Seite: Entferne Header (Titel, Ort, Datum) und füge Marker am Anfang ein
            page_text = remove_lecture_header(page_text)
            result = marker + " " + page_text
        else:
            # Analysiere wie die vorherige Seite endet
            prev_text = result.rstrip()
            
            if not prev_text:
                result = marker + " " + page_text
                prev_ends_with_hyphen = ends_with_hyphen
                continue
            
            last_char = prev_text[-1]
            first_char = page_text[0] if page_text else ''
            
            # Fall 1: Vorherige Seite endete mit Silbentrennung (Bindestrich)
            # Der Text endet noch mit '-', das muss entfernt werden
            if prev_ends_with_hyphen and last_char == '-' and first_char.islower():
                # Entferne Bindestrich und füge Marker OHNE Leerzeichen ein (mitten im Wort)
                result = prev_text[:-1] + marker + page_text
            
            # Fall 1b: Flag gesetzt aber kein Bindestrich am Ende (bereits verarbeitet)
            elif prev_ends_with_hyphen and first_char.islower():
                result = prev_text + marker + page_text
            
            # Fall 2: Vorherige Seite endet mitten im Satz
            # (endet mit Kleinbuchstabe, Komma, oder ähnlichem)
            elif last_char.islower() or last_char in ',;:':
                # Füge Marker mit Leerzeichen ein
                result = prev_text + " " + marker + " " + page_text
            
            # Fall 3: Vorherige Seite endet mit Großbuchstabe (Abkürzung, Akronym)
            elif last_char.isupper():
                result = prev_text + " " + marker + " " + page_text
            
            # Fall 4: Vorherige Seite endet mit Satzzeichen (Satzende)
            elif last_char in '.!?':
                # Neuer Satz - Marker am Anfang
                result = prev_text + " " + marker + " " + page_text
            
            # Fall 5: Sonstige Fälle (Zahlen, Sonderzeichen)
            else:
                result = prev_text + " " + marker + " " + page_text
        
        prev_ends_with_hyphen = ends_with_hyphen
    
    return result


def reconstruct_lecture_md(
    pdf_pages: List[Tuple[int, str]],
    old_md_content: str,
    metadata: Dict
) -> Tuple[str, Dict]:
    """
    Rekonstruiere MD-Datei aus PDF-Seiten mit Erhaltung von Block-IDs.
    Rückgabe: (neuer MD-Text, Statistiken)
    """
    import hashlib
    
    # Statistiken
    stats = {
        'old_block_ids': 0,
        'matched_ids': 0,
        'new_ids': 0,
        'total_paragraphs': 0
    }
    
    # Extrahiere Block-IDs aus altem MD
    block_ids = extract_block_ids_from_md(old_md_content)
    stats['old_block_ids'] = len(block_ids)
    
    # Tracking welche IDs verwendet wurden
    used_ids = set()
    
    # Baue neuen Text
    result_lines = []
    
    # Füge Metadaten hinzu
    if metadata.get('source'):
        result_lines.append(metadata['source'])
        result_lines.append('')
    
    # Füge alle Seiten zusammen mit Seitenmarkern
    merged_text = merge_pages_with_markers(pdf_pages)
    
    # Teile in Absätze
    paragraphs = split_into_paragraphs(merged_text, target_length=500)
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:
            continue
        
        stats['total_paragraphs'] += 1
        
        # Finde passende Block-ID (vergleiche ohne Seitenmarker)
        para_for_matching = re.sub(r'\|\d+\|', '', para)
        block_id = find_matching_block_id(para_for_matching, block_ids, threshold=0.6)
        
        # Füge Absatz hinzu
        if block_id and block_id not in used_ids:
            result_lines.append(f'{para} ^{block_id}')
            used_ids.add(block_id)
            stats['matched_ids'] += 1
        else:
            # Generiere neue Block-ID
            hash_obj = hashlib.md5(para.encode('utf-8'))
            new_id = hash_obj.hexdigest()[:6]
            result_lines.append(f'{para} ^{new_id}')
            stats['new_ids'] += 1
        
        result_lines.append('')
    
    return '\n'.join(result_lines), stats


def process_ga(ga_number: str, dry_run: bool = False, single_file: str = None) -> Dict:
    """
    Verarbeite eine GA-Nummer:
    1. Finde MD-Dateien
    2. Finde PDF
    3. Extrahiere Vorträge aus PDF
    4. Rekonstruiere MD-Dateien
    
    Args:
        ga_number: GA-Nummer (z.B. "GA057")
        dry_run: Wenn True, keine Änderungen speichern
        single_file: Wenn angegeben, nur diese Datei verarbeiten (Teil des Dateinamens)
    """
    ga_norm = ga_number.upper().replace('GA', '').zfill(3)
    
    print(f"\n{'='*60}")
    print(f"Reconstruct MD from PDF: GA{ga_norm}")
    print(f"{'='*60}")
    
    # Finde MD-Dateien
    md_files = find_md_files_for_ga(ga_norm)
    if not md_files:
        print(f"  FEHLER: Keine MD-Dateien gefunden")
        return {"error": "Keine MD-Dateien"}
    
    # Filter auf einzelne Datei wenn angegeben
    if single_file:
        md_files = [f for f in md_files if single_file.lower() in f.name.lower()]
        if not md_files:
            print(f"  FEHLER: Datei mit '{single_file}' nicht gefunden")
            return {"error": f"Datei '{single_file}' nicht gefunden"}
    
    print(f"  {len(md_files)} MD-Datei(en) zu verarbeiten")
    
    # Finde PDF
    pdf_paths = list(STEINER_GA_PDF.glob(f"*GA {ga_norm}*")) + list(STEINER_GA_PDF.glob(f"*GA{ga_norm}*"))
    if not pdf_paths:
        print(f"  FEHLER: Keine PDF gefunden")
        return {"error": "Keine PDF"}
    
    pdf_path = pdf_paths[0]
    print(f"  PDF: {pdf_path.name}")
    
    # Verarbeite jede MD-Datei
    results = []
    total_stats = {
        'old_block_ids': 0,
        'matched_ids': 0,
        'new_ids': 0,
        'total_paragraphs': 0
    }
    
    for md_file in md_files:
        print(f"\n  Verarbeite: {md_file.name}")
        
        # Lade altes MD
        old_md_content = md_file.read_text(encoding='utf-8')
        
        # Extrahiere Metadaten
        metadata = extract_metadata_from_md(old_md_content)
        
        # Finde Seitenbereich (aus Seitenmarkern im alten MD)
        page_markers = re.findall(r'\|(\d+)\|', old_md_content)
        if not page_markers:
            print(f"    WARNUNG: Keine Seitenmarker gefunden, überspringe")
            continue
        
        # WICHTIG: Integer-Vergleich, nicht String-Vergleich!
        page_markers_int = [int(m) for m in page_markers]
        start_page = min(page_markers_int)
        end_page = max(page_markers_int)
        
        # Prüfe auf ungültigen Seitenbereich
        if start_page > end_page:
            print(f"    WARNUNG: Ungültiger Seitenbereich ({start_page}-{end_page}), überspringe")
            continue
        
        print(f"    Seitenbereich: {start_page}-{end_page}")
        
        # Extrahiere aus PDF
        pdf_pages = extract_lecture_from_pdf(pdf_path, start_page, end_page)
        
        if not pdf_pages:
            print(f"    WARNUNG: Keine Seiten im PDF gefunden")
            continue
        
        print(f"    {len(pdf_pages)} Seiten aus PDF extrahiert")
        
        # Rekonstruiere MD
        new_md_content, stats = reconstruct_lecture_md(pdf_pages, old_md_content, metadata)
        
        # Akkumuliere Statistiken
        for key in total_stats:
            total_stats[key] += stats[key]
        
        # Zeige Block-ID Statistiken
        match_rate = (stats['matched_ids'] / stats['total_paragraphs'] * 100) if stats['total_paragraphs'] > 0 else 0
        print(f"    Block-IDs: {stats['old_block_ids']} alt → {stats['matched_ids']} übernommen ({match_rate:.1f}%), {stats['new_ids']} neu")
        
        # Speichere (oder zeige Preview)
        if dry_run:
            print(f"    [DRY-RUN] Würde speichern:")
            print(f"    Länge alt: {len(old_md_content)} Zeichen")
            print(f"    Länge neu: {len(new_md_content)} Zeichen")
            print(f"    Erste 500 Zeichen:")
            print(new_md_content[:500])
        else:
            # Backup erstellen
            backup_path = md_file.with_suffix('.md.backup')
            backup_path.write_text(old_md_content, encoding='utf-8')
            print(f"    Backup erstellt: {backup_path.name}")
            
            # Speichere neue Version
            md_file.write_text(new_md_content, encoding='utf-8')
            print(f"    Gespeichert: {md_file.name}")
        
        results.append({
            'file': md_file.name,
            'pages': len(pdf_pages),
            'old_length': len(old_md_content),
            'new_length': len(new_md_content),
            'stats': stats
        })
    
    return {
        'ga': ga_norm,
        'files_processed': len(results),
        'results': results,
        'total_stats': total_stats
    }


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Verwendung: python reconstruct_md_from_pdf.py GA057 [--dry-run] [--file DATEINAME]")
        print("  --dry-run       Keine Änderungen speichern, nur Preview")
        print("  --file NAME     Nur Datei mit NAME im Dateinamen verarbeiten")
        sys.exit(1)
    
    ga_number = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    # Parse --file Argument
    single_file = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            single_file = sys.argv[idx + 1]
    
    if dry_run:
        print("*** DRY-RUN MODUS - Keine Dateien werden geändert ***\n")
    
    result = process_ga(ga_number, dry_run=dry_run, single_file=single_file)
    
    if 'error' in result:
        print(f"\nFEHLER: {result['error']}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  GA: {result['ga']}")
    print(f"  Dateien verarbeitet: {result['files_processed']}")
    
    for r in result['results']:
        stats = r.get('stats', {})
        match_rate = (stats.get('matched_ids', 0) / stats.get('total_paragraphs', 1) * 100) if stats.get('total_paragraphs', 0) > 0 else 0
        print(f"    {r['file']}:")
        print(f"      {r['pages']} Seiten, {r['old_length']} → {r['new_length']} Zeichen")
        print(f"      Block-IDs: {stats.get('matched_ids', 0)}/{stats.get('total_paragraphs', 0)} übernommen ({match_rate:.1f}%)")
    
    # Gesamtstatistik
    ts = result.get('total_stats', {})
    if ts.get('total_paragraphs', 0) > 0:
        total_match_rate = ts['matched_ids'] / ts['total_paragraphs'] * 100
        print(f"\n  GESAMT Block-ID Statistik:")
        print(f"    Alte Block-IDs: {ts['old_block_ids']}")
        print(f"    Übernommen:     {ts['matched_ids']} ({total_match_rate:.1f}%)")
        print(f"    Neu generiert:  {ts['new_ids']}")
        print(f"    Absätze gesamt: {ts['total_paragraphs']}")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

