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


def is_compound_word_prefix(word_part: str) -> bool:
    """
    Prüfe ob ein Wortteil ein vollständiges Wort sein könnte (für Verbindungswörter).
    
    Typische Adjektiv-/Adverb-Endungen, die auf vollständige Wörter hindeuten:
    - -isch (fränkisch, christlich, deutsch)
    - -lich (menschlich, geistlich)
    - -ell (spirituell, materiell)
    - -iv (aktiv, positiv)
    - -är (revolutionär)
    - -ös (religiös)
    
    NICHT -ig (zu kurz, erzeugt falsche Positive wie "Ereig-nisse")
    NICHT -al (zu kurz, erzeugt falsche Positive)
    """
    word_part = word_part.lower()
    # Mindestens 4 Zeichen lang für Endung + mind. 3 Zeichen Wortstamm
    if len(word_part) < 6:
        return False
    
    compound_endings = (
        'isch', 'lich', 'ell', 'tiv', 'när', 'iös',  # Adjektiv-Endungen (mind. 3 Zeichen)
        'sche', 'chen', 'lein',  # Substantiv-Endungen
        'ung', 'heit', 'keit', 'schaft', 'tum',  # Weitere Substantiv-Endungen
    )
    return any(word_part.endswith(ending) for ending in compound_endings)


def remove_inline_syllable_breaks(text: str) -> str:
    """
    Entferne Silbentrennungen INNERHALB einer Zeile.
    
    Unterscheidung:
    - Trennungszeichen: "Christen- tum" → "Christentum" (Bindestrich + Leerzeichen + Kleinbuchstabe)
    - Verbindungszeichen: "seelisch-geistig" → bleibt (Bindestrich ohne Leerzeichen)
    - Gedankenstriche: ". - Denn" → bleibt (Leerzeichen + Bindestrich + Leerzeichen + Großbuchstabe)
    
    WICHTIG: Verbindungswörter (fränkisch-christlich) dürfen NICHT zusammengefügt werden!
    """
    def replace_syllable_break(match):
        before = match.group(1)  # Teil vor dem Bindestrich
        after = match.group(2)   # Teil nach dem Bindestrich
        
        # Prüfe ob es ein Verbindungswort sein könnte
        # (wenn der Teil VOR dem Bindestrich ein vollständiges Wort ist)
        if is_compound_word_prefix(before):
            # Verbindungswort: Bindestrich beibehalten (aber Leerzeichen entfernen)
            return before + '-' + after
        else:
            # Silbentrennung: zusammenfügen ohne Bindestrich
            return before + after
    
    # Muster: Wort + Bindestrich + Leerzeichen(n) + Kleinbuchstabe
    result = re.sub(r'(\w+)- +([a-zäöüß])', replace_syllable_break, text)
    return result


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
        
        # Format: "186" oder "Seite 186" oder "Seite: 9 6" (OCR-Fehler mit Leerzeichen)
        if line.isdigit():
            return int(line)
        
        # Normale Seitenzahl
        match = re.match(r'^Seite[:\s]+(\d+)\s*$', line, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # OCR-Fehler: Seitenzahl mit Leerzeichen (z.B. "Seite: 9 6" → 96)
        match = re.match(r'^Seite[:\s]+(\d[\d\s]+)\s*$', line, re.IGNORECASE)
        if match:
            digits = match.group(1).replace(' ', '')
            if digits.isdigit():
                return int(digits)
    
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
    - Weniger als 50 Zeichen (inkl. Leerzeichen, ohne Seitenmarker)
    - Endet nicht mit Bindestrich (Silbentrennung)
    
    ignore_page_marker: Wenn True, wird |XXX| aus der Zeile entfernt bevor die Länge geprüft wird
    """
    line = line.strip()
    if not line:
        return False
    
    # Entferne Seitenmarker für die Längenprüfung
    line_for_check = line
    if ignore_page_marker:
        line_for_check = re.sub(r'\|\d+\|\s*', '', line)
    
    if len(line_for_check) >= 50:
        return False
    # Silbentrennungen sind keine Gedichtzeilen
    if line_for_check.endswith('-'):
        return False
    return True


def detect_verse_sequences(lines: List[str]) -> List[Tuple[int, int]]:
    """
    Finde Sequenzen von Gedichtzeilen im Text.
    Rückgabe: Liste von (start_index, end_index) für Gedichtblöcke.
    
    Ein Gedichtblock besteht aus mindestens 2 aufeinanderfolgenden kurzen Zeilen (<50 Zeichen).
    WICHTIG: Innerhalb eines Gedichts gibt es nur einfache Zeilenumbrüche (keine Absatzabstände).
    Wenn nach einer Zeile ein Absatzabstand kommt (doppelte Leerzeile), ist das das Ende des Gedichts.
    """
    sequences = []
    i = 0
    
    def _has_paragraph_break_after(idx: int) -> bool:
        """
        Prüfe ob nach Zeile idx ein Absatzabstand (doppelte Leerzeile) kommt.
        WICHTIG: Orientiert sich am PDF-Text!
        """
        if idx + 1 >= len(lines):
            return True  # Ende des Textes = Absatzabstand
        
        # Prüfe ob die nächste Zeile leer ist
        if not lines[idx + 1].strip():
            # Prüfe ob die übernächste Zeile auch leer ist
            if idx + 2 < len(lines):
                # Wenn übernächste Zeile leer ist → doppelte Leerzeile = Absatzabstand
                if not lines[idx + 2].strip():
                    return True
                # Wenn übernächste Zeile nicht leer ist → einfache Leerzeile = noch im Gedicht
                return False
            else:
                # Ende des Textes nach Leerzeile = Absatzabstand
                return True
        return False
    
    while i < len(lines):
        # Suche nach Start einer möglichen Verssequenz
        if is_verse_line(lines[i]):
            start = i
            # Zähle aufeinanderfolgende kurze Zeilen
            # ABER: Stoppe wenn nach einer Zeile ein Absatzabstand kommt
            while i < len(lines) and is_verse_line(lines[i]):
                # Prüfe ob nach dieser Zeile ein Absatzabstand kommt
                if _has_paragraph_break_after(i):
                    # Absatzabstand = Ende des Gedichts
                    break
                i += 1
            end = i
            
            # Mindestens 4 Zeilen für ein Gedicht (um falsche Erkennung zu vermeiden)
            if end - start >= 4:
                sequences.append((start, end))
        else:
            i += 1
    
    return sequences


def join_lines_to_paragraphs(text: str) -> str:
    """
    Füge Zeilen zu Absätzen zusammen.
    
    WICHTIG: Gedichte erkennen und Zeilenumbrüche erhalten!
    Ein Gedicht ist:
    - Mindestens 2 kurze Zeilen (<50 Zeichen) hintereinander
    - Zwischen den Zeilen nur einfacher Zeilenabstand (keine Leerzeile)
    - Nach der letzten kurzen Zeile kommt ein Absatzabstand (Leerzeile)
    """
    if not text.strip():
        return text
    
    lines = text.split('\n')
    
    # SCHRITT 1: Finde Gedichtblöcke VOR dem Zusammenfügen
    # Ein Gedichtblock: Sequenz von kurzen Zeilen ohne Leerzeilen dazwischen
    verse_line_indices = set()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Prüfe ob diese Zeile kurz ist und potentiell ein Gedicht beginnt
        if line and is_verse_line(lines[i]):
            # Sammle aufeinanderfolgende kurze Zeilen
            start = i
            j = i
            while j < len(lines):
                current_line = lines[j].strip()
                
                # Leere Zeile = Ende des Gedichtblocks
                if not current_line:
                    break
                
                # Keine kurze Zeile mehr = Ende des Gedichtblocks
                if not is_verse_line(lines[j]):
                    break
                
                j += 1
            
            # Wenn mindestens 2 kurze Zeilen hintereinander → Gedicht
            if j - start >= 2:
                for k in range(start, j):
                    verse_line_indices.add(k)
            
            i = j
        else:
            i += 1
    
    # SCHRITT 2: Zeilen verarbeiten mit Wissen über Gedichtblöcke
    out = []
    
    for i, curr in enumerate(lines):
        curr = curr.rstrip()
        prev = out[-1] if out else None
        
        # Leere Zeilen bleiben als Absatz-Trenner
        if not curr.strip():
            if prev and prev.strip():
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
        
        last_char = prev_trim.rstrip('  ')[-1] if prev_trim.rstrip('  ') else ''
        first_char = curr_stripped[0] if curr_stripped else ''
        
        # GEDICHT: Wenn aktuelle Zeile Teil eines Gedichtblocks ist
        if i in verse_line_indices:
            # Füge Markdown-Zeilenumbruch zur vorherigen Zeile hinzu
            if not prev_trim.endswith('  '):
                out[-1] = prev_trim + '  '
            out.append(curr_stripped)
            continue
        
        # Silbentrennung mit Bindestrich → OHNE Leerzeichen zusammenfügen
        if last_char in '-–—' and first_char.islower():
            # Entferne trailing spaces von prev, dann Bindestrich
            prev_clean = prev_trim.rstrip()
            if prev_clean.endswith('-'):
                out[-1] = prev_clean[:-1] + curr_stripped
            else:
                out[-1] = prev_trim + ' ' + curr_stripped
        # Wenn vorherige Zeile mit Satzzeichen endet und nächste mit Großbuchstabe beginnt
        elif last_char in '.!?' and first_char.isupper():
            # Zusammenfügen mit Leerzeichen (gleicher Absatz)
            out[-1] = prev_trim.rstrip('  ') + ' ' + curr_stripped
        # Wenn vorherige Zeile mit Kleinbuchstabe oder Komma endet → zusammenfügen
        elif last_char.islower() or last_char in ',;:':
            out[-1] = prev_trim.rstrip('  ') + ' ' + curr_stripped
        # Alles andere → MIT Leerzeichen zusammenfügen
        else:
            out[-1] = prev_trim.rstrip('  ') + ' ' + curr_stripped
    
    # SCHRITT 3: Füge Leerzeilen zwischen Absätzen ein (nach Satzende + vor neuem Satz)
    result_lines = []
    for i, line in enumerate(out):
        result_lines.append(line)
        # Prüfe ob nach dieser Zeile eine Leerzeile eingefügt werden soll
        line_clean = line.rstrip('  ').rstrip()
        if line_clean and line_clean[-1] in '.!?' and i + 1 < len(out):
            next_line = out[i + 1]
            if (next_line.strip() and 
                not next_line.startswith(('#', '!', '[')) and
                next_line.strip()[0].isupper() and
                len(line_clean) > 50 and
                not line.rstrip().endswith('  ')):  # Nicht nach Gedichtzeile
                result_lines.append('')
    
    return '\n'.join(result_lines)


def get_raw_page_lines(pdf_path: Path, page_idx: int) -> Tuple[List[str], Optional[int]]:
    """
    Extrahiere Rohzeilen einer PDF-Seite (ohne Zusammenfügen).
    Entfernt nur Header/Footer, behält aber Zeilenstruktur.
    
    Rückgabe: (Liste von Zeilen, Seitenzahl oder None)
    """
    doc = fitz.open(pdf_path)
    if page_idx >= len(doc):
        doc.close()
        return [], None
    
    page = doc[page_idx]
    text = page.get_text("text") or ""
    doc.close()
    
    if not text.strip():
        return [], None
    
    lines = text.split('\n')
    
    # Extrahiere Seitenzahl aus Footer
    page_num = extract_page_number_from_footer(lines)
    
    # Entferne Header/Footer-Zeilen
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
    
    return body_lines, page_num


def normalize_for_search(text: str) -> str:
    """
    Normalisiere Text für tolerante Suche.
    Entfernt Umlaute, Sonderzeichen und normalisiert Leerzeichen.
    """
    # Entferne Silbentrennungen (Bindestrich am Zeilenende)
    text = re.sub(r'-\s*\n\s*', '', text)
    
    # Ersetze Umlaute durch Basiszeichen
    replacements = {
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
        'Ä': 'a', 'Ö': 'o', 'Ü': 'u',
        'é': 'e', 'è': 'e', 'ê': 'e',
        'á': 'a', 'à': 'a', 'â': 'a',
        '\ufffd': '',  # PDF-Encoding-Fehler (Replacement Character)
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Entferne alle Nicht-Alphanumerischen Zeichen
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Normalisiere Leerzeichen
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def find_text_start_in_pdf(pdf_path: Path, search_text: str, start_hint_page: int = 0) -> Optional[Tuple[int, int]]:
    """
    Finde die Position eines Textes im PDF.
    
    Args:
        pdf_path: Pfad zur PDF
        search_text: Text zum Suchen (ca. 100 Zeichen)
        start_hint_page: Ungefähre Startseite (für schnellere Suche)
    
    Rückgabe: (PDF-Seitenindex, Position in Zeile) oder None
    """
    # Normalisiere Suchtext tolerant
    search_normalized = normalize_for_search(search_text)[:60]  # Erste 60 Zeichen (toleranter)
    
    doc = fitz.open(pdf_path)
    
    # Konvertiere Seitenzahl zu Index (Seitenzahlen sind 1-basiert, Indizes 0-basiert)
    # Typischerweise sind die ersten Seiten Vorwort etc., also suche etwas früher
    hint_idx = max(0, start_hint_page - 10)
    
    # Suche ab der Hint-Seite, dann davor
    search_range = list(range(hint_idx, len(doc))) + list(range(0, hint_idx))
    
    for page_idx in search_range:
        page = doc[page_idx]
        text = page.get_text("text") or ""
        text_normalized = normalize_for_search(text)
        
        if search_normalized in text_normalized:
            doc.close()
            return (page_idx, 0)  # Gefunden auf dieser Seite
    
    doc.close()
    return None


def extract_lecture_raw_lines(pdf_path: Path, start_page_idx: int, max_pages: int = 50) -> List[Tuple[int, List[str]]]:
    """
    Extrahiere Rohzeilen für einen Vortrag ab einer Startseite.
    Stoppt beim nächsten Vortragstitel oder nach max_pages.
    
    Rückgabe: Liste von (Seitenzahl, Zeilen) pro Seite
    """
    doc = fitz.open(pdf_path)
    pages_data = []
    
    for i in range(start_page_idx, min(start_page_idx + max_pages, len(doc))):
        lines, page_num = get_raw_page_lines(pdf_path, i)
        
        if page_num is not None and lines:
            pages_data.append((page_num, lines))
    
    doc.close()
    return pages_data


def process_raw_lines_to_text(pages_data: List[Tuple[int, List[str]]]) -> str:
    """
    Verarbeite Rohzeilen zu formatiertem Text mit Seitenmarkern.
    
    WICHTIG: Gedichterkennung auf den Gesamttext anwenden!
    """
    if not pages_data:
        return ""
    
    # SCHRITT 1: Alle Zeilen sammeln mit Seiteninfo
    all_lines = []  # (Zeile, Seitenzahl, ist_erste_zeile_der_seite)
    
    for page_num, lines in pages_data:
        for i, line in enumerate(lines):
            all_lines.append((line, page_num, i == 0))
    
    # SCHRITT 2: Silbentrennungen entfernen (über Seitengrenzen hinweg)
    # WICHTIG: Bei Silbentrennung über Seitengrenzen Seitenmarker ZWISCHEN den Wortteilen einfügen!
    processed_lines = []
    i = 0
    while i < len(all_lines):
        line, page_num, is_first = all_lines[i]
        line = line.rstrip()
        
        # Prüfe ob Zeile mit Silbentrennung endet
        if line.endswith('-'):
            # Suche die nächste nicht-leere Zeile (überspringe leere Zeilen/Footer)
            j = i + 1
            skipped_empty = 0
            while j < len(all_lines):
                next_line, next_page, next_is_first = all_lines[j]
                next_line_stripped = next_line.strip()
                if next_line_stripped:
                    break
                skipped_empty += 1
                j += 1
            
            if j < len(all_lines):
                next_line, next_page, next_is_first = all_lines[j]
                next_line_stripped = next_line.lstrip()
                if next_line_stripped and next_line_stripped[0].islower():
                    # Prüfe ob es ein Verbindungswort oder eine Silbentrennung ist
                    word_before_hyphen = line[:-1].split()[-1] if line[:-1].split() else ""
                    
                    if is_compound_word_prefix(word_before_hyphen):
                        # Verbindungswort: Bindestrich beibehalten!
                        if next_page != page_num:
                            combined = line + f"|{next_page}|" + next_line_stripped
                            # Seitenmarker wurde eingefügt, also page_num aktualisieren
                            # damit nicht nochmal ein Marker für next_page erscheint
                            effective_page = next_page
                        else:
                            combined = line + next_line_stripped
                            effective_page = page_num
                    else:
                        # Silbentrennung: zusammenfügen ohne Bindestrich
                        if next_page != page_num:
                            combined = line[:-1] + f"|{next_page}|" + next_line_stripped
                            # Seitenmarker wurde eingefügt, also page_num aktualisieren
                            effective_page = next_page
                        else:
                            combined = line[:-1] + next_line_stripped
                            effective_page = page_num
                    
                    processed_lines.append((combined, effective_page, is_first))
                    i = j + 1  # Überspringe alle verarbeiteten Zeilen
                    continue
        
        processed_lines.append((line, page_num, is_first))
        i += 1
    
    # SCHRITT 3: Gedichtblöcke erkennen (vor dem Zusammenfügen!)
    verse_indices = set()
    j = 0
    while j < len(processed_lines):
        line, _, _ = processed_lines[j]
        line_stripped = line.strip()
        
        if line_stripped and is_verse_line(line):
            start = j
            k = j
            while k < len(processed_lines):
                curr_line, _, _ = processed_lines[k]
                curr_stripped = curr_line.strip()
                
                # Leere Zeile = Ende des Gedichts
                if not curr_stripped:
                    break
                
                # Keine kurze Zeile mehr = Ende
                if not is_verse_line(curr_line):
                    break
                
                k += 1
            
            # Mindestens 4 kurze Zeilen = Gedicht (um falsche Erkennung zu vermeiden)
            if k - start >= 4:
                for m in range(start, k):
                    verse_indices.add(m)
            
            j = k
        else:
            j += 1
    
    # SCHRITT 4: Zeilen zusammenfügen mit Seitenmarkern
    # WICHTIG: Leere Zeilen sind nur dann Absatzende, wenn die nächste Zeile
    # mit Großbuchstabe beginnt. Sonst ist es nur ein Seitenumbruch im PDF!
    result_parts = []
    current_paragraph = ""
    last_page = None
    pending_page_marker = None  # Seitenmarker der noch eingefügt werden muss
    marked_pages = set()  # Seiten, die bereits inline markiert wurden
    
    # Finde alle bereits inline markierten Seiten (aus Silbentrennungen)
    for line, page_num, _ in processed_lines:
        for m in re.finditer(r'\|(\d+)\|', line):
            marked_pages.add(int(m.group(1)))
    
    for idx, (line, page_num, is_first) in enumerate(processed_lines):
        line_stripped = line.strip()
        
        # Leere Zeile: Prüfe ob echter Absatzumbruch oder nur Seitenumbruch
        if not line_stripped:
            # Suche nächste nicht-leere Zeile
            next_non_empty = None
            for future_idx in range(idx + 1, len(processed_lines)):
                future_line, future_page, _ = processed_lines[future_idx]
                if future_line.strip():
                    next_non_empty = (future_line.strip(), future_page)
                    break
            
            # Prüfe ob es ein echter Absatzumbruch ist
            # Echter Absatzumbruch NUR wenn:
            # 1. Vorheriger Text endet mit Satzzeichen (. ! ?) ODER
            # 2. Vorheriger Text ist leer
            # UND nächste Zeile beginnt mit Großbuchstabe
            is_real_paragraph_break = False
            
            if current_paragraph:
                last_char = current_paragraph.rstrip()[-1] if current_paragraph.rstrip() else ''
                
                if next_non_empty:
                    next_text, next_page = next_non_empty
                    first_char = next_text[0] if next_text else ''
                    
                    # Echter Absatzumbruch: Satzende + Großbuchstabe
                    if last_char in '.!?' and first_char.isupper():
                        is_real_paragraph_break = True
                    # KEIN Absatzumbruch: Satz geht weiter
                    else:
                        # Merke den Seitenmarker für später
                        if next_page != last_page and last_page is not None:
                            pending_page_marker = next_page
                        continue
                else:
                    # Keine nächste Zeile = Ende des Textes
                    is_real_paragraph_break = True
            
            if is_real_paragraph_break:
                if current_paragraph:
                    result_parts.append(current_paragraph.strip())
                    current_paragraph = ""
                pending_page_marker = None
            continue
        
        # Seitenmarker einfügen wenn neue Seite (oder pending)
        # ABER: Nicht wenn die Seite bereits inline markiert wurde (z.B. in Silbentrennung)
        page_to_mark = pending_page_marker if pending_page_marker else (page_num if page_num != last_page and last_page is not None else None)
        pending_page_marker = None
        
        if page_to_mark and page_to_mark not in marked_pages:
            marker = f"|{page_to_mark}|"
            marked_pages.add(page_to_mark)
            if current_paragraph:
                # Prüfe ob mitten im Wort (Silbentrennung wurde schon behandelt,
                # aber für normale Fortsetzung mit Leerzeichen)
                current_paragraph += f" {marker} "
            else:
                current_paragraph = f"{marker} "
        
        last_page = page_num
        
        # Gedichtzeile: Mit Markdown-Zeilenumbruch
        if idx in verse_indices:
            # Prüfe ob dies der BEGINN eines Gedichts ist (vorherige Zeile war kein Gedicht)
            is_verse_start = (idx - 1) not in verse_indices
            
            if is_verse_start and current_paragraph:
                # Absatzumbruch VOR dem Gedicht einfügen
                result_parts.append(current_paragraph.strip())
                current_paragraph = ""
            
            if current_paragraph and not current_paragraph.endswith('  \n'):
                if not current_paragraph.endswith('  '):
                    current_paragraph = current_paragraph.rstrip() + '  '
                current_paragraph += '\n' + line_stripped
            else:
                current_paragraph += line_stripped
        else:
            # Normale Zeile: Zusammenfügen
            if current_paragraph:
                last_char = current_paragraph.rstrip()[-1] if current_paragraph.rstrip() else ''
                first_char = line_stripped[0] if line_stripped else ''
                
                # Silbentrennung bereits behandelt, also normal mit Leerzeichen
                if not current_paragraph.endswith(' ') and not current_paragraph.endswith('\n'):
                    current_paragraph += ' '
                current_paragraph += line_stripped
            else:
                current_paragraph = line_stripped
    
    # Letzten Absatz hinzufügen
    if current_paragraph:
        result_parts.append(current_paragraph.strip())
    
    # Erster Seitenmarker am Anfang
    if pages_data and result_parts:
        first_page = pages_data[0][0]
        if not result_parts[0].startswith(f"|{first_page}|"):
            result_parts[0] = f"|{first_page}| " + result_parts[0]
    
    # Entferne Silbentrennungen innerhalb von Zeilen (z.B. "sukzessi- ves" → "sukzessives")
    result = '\n\n'.join(result_parts)
    result = remove_inline_syllable_breaks(result)
    
    return result


def extract_lecture_from_pdf(pdf_path: Path, start_page: int, end_page: int) -> List[Tuple[int, str, bool]]:
    """
    Extrahiere Vortrag aus PDF (Seitenbereich).
    Rückgabe: Liste von (Seitenzahl, bereinigter Text, endet_mit_silbentrennung)
    
    HINWEIS: Diese Funktion wird für Kompatibilität beibehalten.
    Der neue Ansatz verwendet extract_lecture_raw_lines + process_raw_lines_to_text.
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
        for md_file in folder.glob("*.md"):
            # Backups nicht erneut verarbeiten
            name_lower = md_file.name.lower()
            if name_lower.endswith("_backup.md") or name_lower.endswith(".md.backup"):
                continue
            md_files.append(md_file)
    
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


def find_next_lecture_title(text: str) -> Optional[int]:
    """
    Finde die Position eines neuen Vortragstitels im Text.
    
    Vortragstitel sind erkennbar an:
    - Oft in GROSSBUCHSTABEN
    - Enthalten "VORTRAG" zusammen mit einem Zahlwort (ERSTER, ZWEITER, DRITTER, ...)
    - Enthalten Datum (und optional Ort)
    
    Rückgabe: Position des Titelbeginns, oder None wenn kein Titel gefunden
    """
    # Zahlwörter für Vortragstitel
    zahlwoerter = r'(?:ERSTER?|ZWEITER?|DRITTER?|VIERTER?|FÜNFTER?|SECHSTER?|SIEBTER?|SIEBENTER?|ACHTER?|NEUNTER?|ZEHNTER?|ELFTER?|ZWÖLFTER?|DREIZEHNTER?|VIERZEHNTER?|FÜNFZEHNTER?)'
    datum = r'\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}'
    
    # Muster 1: "ZWEITER VORTRAG, 25. Oktober 1904" oder "ZWEITER VORTRAG 25. Oktober 1904"
    pattern1 = rf'{zahlwoerter}\s+VORTRAG,?\s*{datum}'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return match.start()
    
    # Muster 2: "ZWEITER VORTRAG" auf einer Zeile, Datum auf nächster
    pattern2 = rf'{zahlwoerter}\s+VORTRAG\s*\n+\s*{datum}'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        return match.start()
    
    # Muster 3: Nur "VORTRAG" mit Datum (ohne Zahlwort, aber in Großbuchstaben-Kontext)
    # z.B. "VORTRAG Berlin, 25. Oktober 1904"
    orte = r'(?:Berlin|München|Dornach|Stuttgart|Wien|Hamburg|Köln|Leipzig|Nürnberg|Basel|Zürich|Kassel)'
    pattern3 = rf'VORTRAG\s+{orte},?\s*{datum}'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        return match.start()
    
    # Muster 4: GROSSBUCHSTABEN-TITEL gefolgt von Ort, Datum (ohne "VORTRAG")
    # z.B. "DER URSPRUNG DER SEELE Berlin, 3. Oktober 1903"
    # Der Titel muss mindestens 10 Zeichen haben und komplett in Großbuchstaben sein
    # Suche nach: |Seitenzahl| GROSSBUCHSTABEN-TITEL Ort, Datum
    pattern4 = rf'\|(\d+)\|\s*([A-ZÄÖÜ][A-ZÄÖÜ\s\-«»]+)\s+{orte},?\s*{datum}'
    match = re.search(pattern4, text)
    if match:
        # Prüfe ob der Titel wirklich in Großbuchstaben ist (nicht nur der erste Buchstabe)
        title_part = match.group(2).strip()
        if len(title_part) >= 10 and title_part.replace(' ', '').replace('-', '').replace('«', '').replace('»', '').isupper():
            return match.start()
    
    # Muster 5: GROSSBUCHSTABEN-TITEL Ort, Datum (ohne Seitenmarker)
    pattern5 = rf'([A-ZÄÖÜ][A-ZÄÖÜ\s\-«»]{{10,}})\s+{orte},?\s*{datum}'
    match = re.search(pattern5, text)
    if match:
        title_part = match.group(1).strip()
        if title_part.replace(' ', '').replace('-', '').replace('«', '').replace('»', '').isupper():
            return match.start()
    
    # Muster 6: Wie Muster 4/5, aber mit toleranterem Datum (OCR-Fehler wie "jt" statt "7.")
    # Datum kann auch falsch erkannt sein, z.B. "jt November" statt "7. November"
    datum_tolerant = r'(?:\d{1,2}\.|[a-z]{1,3})\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}'
    pattern6 = rf'\|(\d+)\|\s*([A-ZÄÖÜ][A-ZÄÖÜ\s\-«»]+)\s+{orte},?\s*{datum_tolerant}'
    match = re.search(pattern6, text)
    if match:
        title_part = match.group(2).strip()
        if len(title_part) >= 10 and title_part.replace(' ', '').replace('-', '').replace('«', '').replace('»', '').isupper():
            return match.start()
    
    return None


def truncate_at_next_lecture(text: str) -> Tuple[str, Optional[str]]:
    """
    Schneide Text am Beginn des nächsten Vortrags ab.
    
    Rückgabe: (Text bis zum nächsten Vortrag, gefundener Titel oder None)
    """
    # Überspringe mindestens 500 Zeichen oder 20% des Textes (um den eigenen Titel sicher zu überspringen)
    # Der eigene Titel + Header kann leicht 200-400 Zeichen sein
    min_skip = max(500, len(text) // 5)
    search_start = min(min_skip, len(text) - 100)  # Aber nicht mehr als Text-100
    
    if search_start < 0 or search_start >= len(text):
        return text, None
    
    text_to_search = text[search_start:]
    pos = find_next_lecture_title(text_to_search)
    
    if pos is not None:
        actual_pos = search_start + pos
        # Extrahiere den gefundenen Titel für die Statistik
        title_end = text.find('\n', actual_pos + 50)  # Nimm etwa 50 Zeichen als Titelvorschau
        if title_end == -1:
            title_end = min(actual_pos + 80, len(text))
        found_title = text[actual_pos:title_end].strip()
        
        # Schneide den Text ab
        return text[:actual_pos].strip(), found_title
    
    return text, None


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
    
    # Entferne optionalen Seitenmarker am Anfang für die Mustersuche
    # Merke dir aber den Seitenmarker für später
    page_marker_match = re.match(r'^(\|\d+\|\s*)', text_normalized)
    page_marker = page_marker_match.group(1) if page_marker_match else ""
    original_page_marker = ""
    if page_marker:
        original_page_marker_match = re.match(r'^(\|\d+\|\s*)', text)
        original_page_marker = original_page_marker_match.group(1) if original_page_marker_match else ""
        text_normalized = text_normalized[len(page_marker):]
        text = text[len(original_page_marker):]
    
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
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 2: Mehrzeiliger Titel
    # z.B. "WO UND WIE FINDET MAN DEN GEIST?\nBerlin, 15. Oktober 1908"
    pattern2 = rf'^([A-ZÄÖÜ\s«»\-\?!]+)\n{orte},?\s*{datum}\s*'
    match = re.match(pattern2, text_normalized)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 3: Mehrzeiliger Titel mit Untertitel
    # z.B. "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\n0\n\nBerlin, 12. März 1909"
    # oder "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\nBerlin, 12. März 1909"
    # Erlaubt optionale Leerzeilen zwischen Titel und Ort/Datum
    pattern3 = rf'^([A-ZÄÖÜ\s«»\-\?!]+\n)+(\d+\n)?\n*{orte},?\s*{datum}\s*'
    match = re.match(pattern3, text_normalized)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 4: Nur Titel in GROSSBUCHSTABEN ohne Datum (am Anfang einer neuen Seite)
    # z.B. "DIE RÄTSEL IN GOETHES «FAUST»\nESOTERISCH\n0\n"
    pattern4 = r'^([A-ZÄÖÜ\s«»\-\?!]+\n)+(0\n)?'
    match = re.match(pattern4, text_normalized)
    if match and len(match.group(0).strip()) > 10:  # Mindestens 10 Zeichen Titel
        # Nur entfernen, wenn es wirklich wie ein Titel aussieht (GROSSBUCHSTABEN)
        title_text = match.group(0).strip()
        if title_text.isupper() or (title_text.replace('«', '').replace('»', '').replace('\n', ' ').strip().isupper()):
            matched_text = match.group(0)
            return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 5: Ort, Datum am Anfang (manchmal ohne Titel)
    pattern5 = rf'^{orte},?\s*{datum}\s*'
    match = re.match(pattern5, text_normalized, re.IGNORECASE)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 6: Ort, Datum nach Leerzeile (wenn Titel bereits entfernt wurde)
    # Manchmal bleibt nach der Titel-Entfernung noch "Ort, Datum" übrig
    pattern6 = rf'^\s*{orte},?\s*{datum}\s*'
    match = re.match(pattern6, text_normalized, re.IGNORECASE)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 7: GROSSBUCHSTABEN-TITEL mit nur Datum (ohne Ort)
    # z.B. "ERSTER VORTRAG, 18. Oktober 1904"
    # oder "ERSTER VORTRAG 18. Oktober 1904"
    pattern7 = rf'^([A-ZÄÖÜ][A-ZÄÖÜ\s\-]+),?\s*{datum}\s*'
    match = re.match(pattern7, text_normalized)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 8: Nur Datum am Anfang
    # z.B. "18. Oktober 1904 Der eigentliche Text..."
    pattern8 = rf'^{datum}\s*'
    match = re.match(pattern8, text_normalized)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Muster 9: Mehrzeiliger Header mit Titel und Datum auf separater Zeile
    # z.B. "ERSTER VORTRAG\n18. Oktober 1904"
    pattern9 = rf'^([A-ZÄÖÜ][A-ZÄÖÜ\s\-]+)\n+{datum}\s*'
    match = re.match(pattern9, text_normalized)
    if match:
        matched_text = match.group(0)
        return original_page_marker + _remove_matched_header(text, matched_text)
    
    # Kein Header gefunden - gib Original (mit Seitenmarker) zurück
    return original_page_marker + text


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
        
        # Prüfe ob current mit Gedicht endet (erkennbar an "  \n" am Ende)
        current_ends_with_verse = current.rstrip().endswith('  \n') or current.rstrip().endswith('  ')
        
        # Prüfe ob sentence Teil eines Gedichts ist (enthält "  \n")
        sentence_is_verse = '  \n' in sentence
        
        # Wenn current mit Gedicht endet und sentence nicht Teil des Gedichts ist → Absatzabstand
        if current_ends_with_verse and not sentence_is_verse:
            # Entferne Markdown-Zeilenumbruch vom Ende von current
            current = current.rstrip()
            if current.endswith('  \n'):
                current = current[:-3].rstrip()
            elif current.endswith('  '):
                current = current[:-2].rstrip()
            # Speichere current als Absatz
            if current.strip():
                paragraphs.append(current.strip())
            current = sentence
        # Wenn current + sentence zu lang wird, speichere current und starte neu
        elif current and len(current) + len(sentence) > target_length:
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


def detect_section_headers_in_text(text: str) -> List[str]:
    """
    Erkenne Abschnitts-Überschriften im Text.
    Überschriften sind typischerweise:
    - Mehrere Zeilen in GROSSBUCHSTABEN
    - Gefolgt von normalem Text
    
    Rückgabe: Liste von gefundenen Überschriften
    """
    headers = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Prüfe ob Zeile komplett in Großbuchstaben ist (mind. 10 Zeichen)
        # Ignoriere Seitenmarker und Sonderzeichen für die Prüfung
        line_clean = re.sub(r'\|\d+\|', '', line)
        line_alpha = re.sub(r'[^A-ZÄÖÜ\s]', '', line_clean)
        
        if len(line_alpha.strip()) >= 10 and line_clean.strip() == line_clean.strip().upper():
            # Sammle aufeinanderfolgende Großbuchstaben-Zeilen
            header_lines = [line_clean.strip()]
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                next_clean = re.sub(r'\|\d+\|', '', next_line)
                next_alpha = re.sub(r'[^A-ZÄÖÜ\s]', '', next_clean)
                
                if len(next_alpha.strip()) >= 5 and next_clean.strip() == next_clean.strip().upper():
                    header_lines.append(next_clean.strip())
                    j += 1
                else:
                    break
            
            # Wenn mindestens 2 Zeilen oder eine lange Zeile, ist es wahrscheinlich eine Überschrift
            combined = ' '.join(header_lines)
            if len(header_lines) >= 2 or len(combined) >= 30:
                headers.append(combined)
            
            i = j
        else:
            i += 1
    
    return headers


def check_missing_sections(pdf_text: str, old_md_content: str) -> List[str]:
    """
    Prüfe ob im PDF Abschnitte mit Überschriften vorhanden sind,
    die in der alten MD-Datei fehlen.
    
    Rückgabe: Liste von fehlenden Überschriften
    """
    # Finde Überschriften im PDF
    pdf_headers = detect_section_headers_in_text(pdf_text)
    
    if not pdf_headers:
        return []
    
    # Normalisiere alte MD für Vergleich
    old_md_normalized = normalize_text(old_md_content)
    
    missing = []
    for header in pdf_headers:
        header_normalized = normalize_text(header)
        # Prüfe ob Teile der Überschrift in der alten MD vorkommen
        # Nimm die ersten 30 Zeichen als Suchbegriff
        search_term = header_normalized[:30] if len(header_normalized) > 30 else header_normalized
        if search_term not in old_md_normalized:
            missing.append(header)
    
    return missing


def extract_first_text_from_md(md_content: str, length: int = 100) -> str:
    """
    Extrahiere den ersten Textinhalt aus einer MD-Datei (nach Metadaten).
    Überspringe Quelle-Zeilen, Seitenmarker und Block-IDs.
    """
    lines = md_content.split('\n')
    text_parts = []
    
    for line in lines:
        # Überspringe Metadaten
        if line.startswith('Quelle:') or line.startswith('[['):
            continue
        if not line.strip():
            continue
        
        # Entferne Seitenmarker und Block-IDs
        clean = re.sub(r'\|\d+\|', '', line)
        clean = re.sub(r'\^[a-z0-9]+\s*$', '', clean)
        clean = clean.strip()
        
        if clean:
            text_parts.append(clean)
            if len(' '.join(text_parts)) >= length:
                break
    
    return ' '.join(text_parts)[:length]


def reconstruct_lecture_md_v2(
    pdf_path: Path,
    old_md_content: str,
    metadata: Dict,
    start_page_hint: int = 0
) -> Tuple[str, Dict]:
    """
    Rekonstruiere MD-Datei aus PDF mit neuem Ansatz:
    1. Finde Textanfang aus alter MD im PDF
    2. Extrahiere Rohzeilen ab dieser Stelle
    3. Verarbeite mit Gedichterkennung
    4. Übertrage Block-IDs
    
    Rückgabe: (neuer MD-Text, Statistiken)
    """
    import hashlib
    
    stats = {
        'old_block_ids': 0,
        'matched_ids': 0,
        'new_ids': 0,
        'total_paragraphs': 0,
        'missing_sections': [],
        'search_method': 'text_match'
    }
    
    # Extrahiere Block-IDs aus altem MD
    block_ids = extract_block_ids_from_md(old_md_content)
    stats['old_block_ids'] = len(block_ids)
    
    # SCHRITT 1: Finde Textanfang im PDF
    search_text = extract_first_text_from_md(old_md_content, 100)
    
    if not search_text:
        stats['error'] = "Kein Suchtext gefunden"
        return "", stats
    
    # Suche im PDF
    found = find_text_start_in_pdf(pdf_path, search_text, start_page_hint)
    
    if not found:
        stats['error'] = f"Text nicht im PDF gefunden: {search_text[:50]}..."
        return "", stats
    
    start_page_idx, _ = found
    stats['start_page_idx'] = start_page_idx
    
    # SCHRITT 2: Extrahiere Rohzeilen ab dieser Stelle
    pages_data = extract_lecture_raw_lines(pdf_path, start_page_idx, max_pages=30)
    
    if not pages_data:
        stats['error'] = "Keine Seiten extrahiert"
        return "", stats
    
    stats['pages_extracted'] = len(pages_data)
    
    # SCHRITT 3: Verarbeite zu Text (mit Gedichterkennung!)
    merged_text = process_raw_lines_to_text(pages_data)
    
    # Schneide Text vor dem Suchtext ab (falls Seite auch vorherigen Vortrag enthält)
    # Suche die ersten Wörter des Suchtexts
    search_words = search_text.split()[:5]  # Erste 5 Wörter
    for i in range(len(search_words), 2, -1):  # Von 5 Wörtern runter bis 3
        pattern = r'\s+'.join(re.escape(w) for w in search_words[:i])
        match = re.search(pattern, merged_text, re.IGNORECASE)
        if match:
            cut_pos = match.start()
            
            # Extrahiere den letzten Seitenmarker VOR dem Schnitt
            marker_match = re.search(r'\|(\d+)\|', merged_text[:cut_pos])
            page_marker = ""
            if marker_match:
                # Finde den letzten Seitenmarker
                all_markers = re.findall(r'\|(\d+)\|', merged_text[:cut_pos])
                if all_markers:
                    page_marker = f"|{all_markers[-1]}| "
            
            # Schneide ab und füge Seitenmarker vorne ein
            merged_text = page_marker + merged_text[cut_pos:].strip()
            break
    
    # Entferne Header am Anfang
    merged_text = remove_lecture_header(merged_text)
    
    # Schneide am nächsten Vortragstitel ab
    merged_text, next_lecture_title = truncate_at_next_lecture(merged_text)
    if next_lecture_title:
        stats['truncated_at'] = next_lecture_title
    
    # Prüfe auf fehlende Abschnitte
    missing_sections = check_missing_sections(merged_text, old_md_content)
    stats['missing_sections'] = missing_sections
    
    # SCHRITT 4: Teile in Absätze und übertrage Block-IDs
    paragraphs = split_into_paragraphs(merged_text, target_length=500)
    
    used_ids = set()
    result_lines = []
    
    # Füge Metadaten hinzu
    if metadata.get('source'):
        result_lines.append(metadata['source'])
        result_lines.append('')
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:
            continue
        
        stats['total_paragraphs'] += 1
        
        # Finde passende Block-ID
        para_for_matching = re.sub(r'\|\d+\|', '', para)
        block_id = find_matching_block_id(para_for_matching, block_ids, threshold=0.6)
        
        if block_id and block_id not in used_ids:
            result_lines.append(f'{para} ^{block_id}')
            used_ids.add(block_id)
            stats['matched_ids'] += 1
        else:
            hash_obj = hashlib.md5(para.encode('utf-8'))
            new_id = hash_obj.hexdigest()[:6]
            result_lines.append(f'{para} ^{new_id}')
            stats['new_ids'] += 1
        
        result_lines.append('')
    
    return '\n'.join(result_lines), stats


def reconstruct_lecture_md(
    pdf_pages: List[Tuple[int, str]],
    old_md_content: str,
    metadata: Dict
) -> Tuple[str, Dict]:
    """
    ALTE VERSION - für Kompatibilität beibehalten.
    Rekonstruiere MD-Datei aus PDF-Seiten mit Erhaltung von Block-IDs.
    Rückgabe: (neuer MD-Text, Statistiken)
    """
    import hashlib
    
    # Statistiken
    stats = {
        'old_block_ids': 0,
        'matched_ids': 0,
        'new_ids': 0,
        'total_paragraphs': 0,
        'missing_sections': []
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
    
    # Schneide am nächsten Vortragstitel ab
    merged_text, next_lecture_title = truncate_at_next_lecture(merged_text)
    if next_lecture_title:
        stats['truncated_at'] = next_lecture_title
    
    # Prüfe auf fehlende Abschnitte
    missing_sections = check_missing_sections(merged_text, old_md_content)
    stats['missing_sections'] = missing_sections
    
    # Teile in Absätze
    paragraphs = split_into_paragraphs(merged_text, target_length=500)
    
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:
            continue
        
        stats['total_paragraphs'] += 1
        
        para_for_matching = re.sub(r'\|\d+\|', '', para)
        block_id = find_matching_block_id(para_for_matching, block_ids, threshold=0.6)
        
        if block_id and block_id not in used_ids:
            result_lines.append(f'{para} ^{block_id}')
            used_ids.add(block_id)
            stats['matched_ids'] += 1
        else:
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
        # Wenn single_file eine Zahl ist (z.B. "1"), suche nach "(1.) " im Dateinamen
        # WICHTIG: Mit Leerzeichen danach, damit "(1.)" nicht "(10.)" matcht!
        if single_file.isdigit():
            pattern = f"({single_file}.) "
            md_files = [f for f in md_files if pattern in f.name]
        else:
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
        
        # Finde Seitenbereich (aus Seitenmarkern im alten MD) als Hint für die Suche
        page_markers = re.findall(r'\|(\d+)\|', old_md_content)
        start_page_hint = 0
        if page_markers:
            page_markers_int = [int(m) for m in page_markers]
            start_page_hint = min(page_markers_int)
            print(f"    Seitenhinweis: ab Seite {start_page_hint}")
        
        # Rekonstruiere MD mit neuem Ansatz (Textanfang-Suche)
        print(f"    Starte Rekonstruktion (Textanfang-Suche)...")
        import time
        start_time = time.time()
        new_md_content, stats = reconstruct_lecture_md_v2(pdf_path, old_md_content, metadata, start_page_hint)
        
        # Prüfe auf Fehler
        if stats.get('error'):
            print(f"    FEHLER: {stats['error']}")
            continue
        
        pages_extracted = stats.get('pages_extracted', 0)
        print(f"    {pages_extracted} Seiten aus PDF extrahiert (ab Index {stats.get('start_page_idx', '?')})")
        elapsed = time.time() - start_time
        print(f"    Rekonstruktion abgeschlossen in {elapsed:.2f}s")
        
        # Akkumuliere Statistiken
        for key in total_stats:
            if key != 'missing_sections':
                total_stats[key] += stats.get(key, 0)
        
        # Zeige Block-ID Statistiken
        match_rate = (stats['matched_ids'] / stats['total_paragraphs'] * 100) if stats['total_paragraphs'] > 0 else 0
        print(f"    Block-IDs: {stats['old_block_ids']} alt → {stats['matched_ids']} übernommen ({match_rate:.1f}%), {stats['new_ids']} neu")
        
        # Zeige wenn Text am nächsten Vortrag abgeschnitten wurde
        truncated_at = stats.get('truncated_at')
        if truncated_at:
            display = truncated_at[:60] + "..." if len(truncated_at) > 60 else truncated_at
            print(f"    ✂️  Text abgeschnitten vor: {display}")
        
        # Zeige fehlende Abschnitte (falls vorhanden)
        missing_sections = stats.get('missing_sections', [])
        if missing_sections:
            print(f"    ⚠️  FEHLENDE ABSCHNITTE IM MD ({len(missing_sections)}):")
            for section in missing_sections:
                # Kürze lange Überschriften
                display = section[:80] + "..." if len(section) > 80 else section
                print(f"       → {display}")
        
        # Speichere (oder zeige Preview)
        if dry_run:
            print(f"    [DRY-RUN] Würde speichern:")
            print(f"    Länge alt: {len(old_md_content)} Zeichen")
            print(f"    Länge neu: {len(new_md_content)} Zeichen")
            print(f"    Erste 500 Zeichen:")
            print(new_md_content[:500])
        else:
            # Backup erstellen
            backup_path = md_file.with_name(f"{md_file.stem}_backup.md")
            backup_path.write_text(old_md_content, encoding='utf-8')
            print(f"    Backup erstellt: {backup_path.name}")
            
            # Speichere neue Version
            md_file.write_text(new_md_content, encoding='utf-8')
            print(f"    Gespeichert: {md_file.name}")
        
        results.append({
            'file': md_file.name,
            'pages': stats.get('pages_extracted', 0),
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


# =============================================================================
# NEUER ANSATZ: Rekonstruktion aus PDF-MD-Dateien
# =============================================================================

STEINER_GA_MD = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_md')


def extract_paragraphs_with_ids(md_content: str) -> List[Tuple[str, str]]:
    """
    Extrahiere Absätze mit ihren Block-IDs aus MD-Inhalt.
    
    Rückgabe: Liste von (block_id, text)
    """
    # Teile bei doppelten Zeilenumbrüchen
    parts = re.split(r'\n\n+', md_content)
    result = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Suche Block-ID am Ende
        id_match = re.search(r'\^([\w]+)\s*$', part)
        if id_match:
            block_id = id_match.group(1)
            text = re.sub(r'\s*\^[\w]+\s*$', '', part)
            result.append((block_id, text))
        else:
            # Kein Block-ID, aber trotzdem speichern
            result.append((None, part))
    
    return result


def find_extracted_md_file(ga_number: str) -> Optional[Path]:
    """Finde die _extracted.md Datei für eine GA-Nummer."""
    ga_norm = ga_number.upper().replace('GA', '').replace(' ', '').zfill(3)
    
    # Suche nach _extracted.md Datei
    for md_file in STEINER_GA_MD.glob(f"*GA*{ga_norm}*_extracted.md"):
        return md_file
    
    # Alternative: im Unterordner
    for folder in STEINER_GA_MD.iterdir():
        if folder.is_dir() and (f"GA {ga_norm}" in folder.name or f"GA{ga_norm}" in folder.name):
            extracted = list(folder.glob("*_extracted.md"))
            if extracted:
                return extracted[0]
    
    return None


def extract_pages_from_extracted_md(extracted_md_path: Path) -> List[Dict]:
    """
    Extrahiere Seiten aus einer _extracted.md Datei.
    
    Format: # Page XX^page=XX
    Text kann auf derselben Zeile sein!
    
    Rückgabe: Liste von {page_num, text}
    """
    content = extracted_md_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    pages = []
    current_page = None
    current_text = []
    
    for line in lines:
        # Neue Seite? Format: # Page XX^page=XX [optional Text auf derselben Zeile]
        page_match = re.match(r'^#\s*Page\s+(\d+)\^page=\d+\s*(.*)', line)
        if page_match:
            # Vorherige Seite speichern
            if current_page is not None:
                text = '\n'.join(current_text).strip()
                # Entferne Copyright-Zeile am Ende
                text = re.sub(r'\s*Copyright Rudolf Steiner.*$', '', text)
                pages.append({
                    'page_num': current_page,
                    'text': text
                })
            
            current_page = int(page_match.group(1))
            # Text nach dem Page-Header (auf derselben Zeile)
            inline_text = page_match.group(2).strip()
            current_text = [inline_text] if inline_text else []
            continue
        
        # Copyright-Zeile überspringen (wenn auf eigener Zeile)
        if line.strip().startswith('Copyright Rudolf Steiner'):
            continue
        
        # Text zur aktuellen Seite hinzufügen
        if current_page is not None:
            current_text.append(line)
    
    # Letzte Seite speichern
    if current_page is not None:
        text = '\n'.join(current_text).strip()
        text = re.sub(r'\s*Copyright Rudolf Steiner.*$', '', text)
        pages.append({
            'page_num': current_page,
            'text': text
        })
    
    return pages


def normalize_for_search(text: str) -> str:
    """Normalisiere Text für Suche (entferne Leerzeichen-Variationen)."""
    return re.sub(r'\s+', '', text.upper())


def find_lecture_boundaries_in_extracted(pages: List[Dict], lectures: List[Dict], skip_toc_pages: int = 12) -> Dict[int, Tuple[int, int]]:
    """
    Finde die Seitengrenzen für jeden Vortrag basierend auf den Titeln.
    
    Args:
        pages: Liste der Seiten
        lectures: Liste der Vorträge
        skip_toc_pages: Überspringe die ersten N Seiten (Inhaltsverzeichnis)
    
    Rückgabe: {lecture_idx: (start_page, end_page)}
    """
    # Filtere Seiten: Überspringe Inhaltsverzeichnis
    content_pages = [p for p in pages if p['page_num'] > skip_toc_pages]
    
    if not content_pages:
        return {}
    
    # Kombiniere alle Seiten zu einem Text
    all_text = ""
    char_to_page = []
    
    for page in content_pages:
        text = page['text']
        char_to_page.extend([page['page_num']] * len(text))
        all_text += text
        char_to_page.extend([page['page_num']] * 2)
        all_text += "\n\n"
    
    # Normalisierte Version für Suche
    all_text_norm = normalize_for_search(all_text)
    
    # Finde Startseiten aller Vorträge
    lecture_starts = []
    for idx, lecture in enumerate(lectures):
        title_norm = normalize_for_search(lecture['title'])[:40]
        pos_norm = all_text_norm.find(title_norm)
        
        if pos_norm != -1:
            ratio = pos_norm / len(all_text_norm) if all_text_norm else 0
            approx_pos = min(int(ratio * len(all_text)), len(char_to_page) - 1)
            start_page = char_to_page[approx_pos] if approx_pos < len(char_to_page) else content_pages[-1]['page_num']
            lecture_starts.append((idx, start_page))
    
    # Sortiere nach Startseite
    lecture_starts.sort(key=lambda x: x[1])
    
    # Berechne Boundaries
    boundaries = {}
    for i, (idx, start_page) in enumerate(lecture_starts):
        if i + 1 < len(lecture_starts):
            end_page = lecture_starts[i + 1][1] - 1
        else:
            end_page = content_pages[-1]['page_num']
        
        if end_page < start_page:
            end_page = start_page
        
        boundaries[idx] = (start_page, end_page)
    
    return boundaries


def clean_extracted_text(text: str) -> str:
    """
    Bereinige extrahierten Text:
    - Entferne Silbentrennungen (behalte Verbindungsstriche)
    - Verbinde Zeilen zu Fließtext
    """
    lines = text.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Prüfe auf Silbentrennung am Zeilenende
        if line.endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            word_part = line.rstrip('-').split()[-1] if line.rstrip('-').split() else ''
            
            # Prüfe ob es ein Verbindungsstrich ist
            if word_part and not is_compound_word_prefix(word_part + '-'):
                line_without_hyphen = line[:-1]
                if next_line:
                    result_lines.append(line_without_hyphen + next_line)
                    i += 2
                    continue
        
        result_lines.append(line)
        i += 1
    
    # Verbinde Zeilen zu Fließtext
    paragraphs = []
    current_para = []
    
    for line in result_lines:
        if not line.strip():
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        else:
            current_para.append(line.strip())
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    # Kombiniere zu Text
    result = '\n\n'.join(paragraphs)
    
    # Entferne Silbentrennungen INNERHALB von Zeilen: "Unsterb- lichkeit" -> "Unsterblichkeit"
    # Pattern: Wort- gefolgt von Leerzeichen und Kleinbuchstaben
    result = re.sub(r'(\w)- +([a-zäöüß])', r'\1\2', result)
    
    return result


def remove_title_from_text(text: str) -> str:
    """
    Entferne den Vortragstitel, Ort und Datum vom Anfang des Textes.
    
    Titel-Formate:
    - "DAS EWIGE UN D DAS VERGÄNGLICHE DES MENSCHEN Berlin, 6. September 1903"
    - "TITEL Ort, Datum Text..."
    """
    # Pattern für Titel: GROSSBUCHSTABEN gefolgt von Ort und Datum
    # Der Titel endet meist vor dem ersten Kleinbuchstaben-Wort
    
    # Entferne führenden Seitenmarker temporär
    page_marker_match = re.match(r'^(\|\d+\|\s*)', text)
    page_marker = page_marker_match.group(1) if page_marker_match else ''
    text_without_marker = text[len(page_marker):] if page_marker else text
    
    # Pattern: TITEL (Großbuchstaben) + Ort, Datum
    patterns = [
        # "TITEL TITEL Berlin, 6. September 1903 Der erste Satz..."
        r'^[A-ZÄÖÜ][A-ZÄÖÜ\s\-«»\?\!]+(?:Berlin|München|Dornach|Stuttgart|Wien|Hamburg|Köln|Leipzig|Nürnberg),?\s*\d{1,2}\.?\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}\s*',
        # Nur Großbuchstaben-Titel bis zum ersten normalen Satz
        r'^[A-ZÄÖÜ][A-ZÄÖÜ\s\-«»\?\!\d\.]+(?=\s+[A-ZÄÖÜ][a-zäöü])',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text_without_marker)
        if match:
            text_without_marker = text_without_marker[match.end():].strip()
            break
    
    return page_marker + text_without_marker


def build_lecture_text_with_markers(pages: List[Dict], start_page: int, end_page: int) -> str:
    """
    Baue den Vortragstext mit Seitenmarkern aus den extrahierten Seiten.
    
    1. Extrahiere Text aus relevanten Seiten
    2. Bereinige Silbentrennungen
    3. Füge Seitenmarker ein
    4. Entferne Titel
    """
    result_parts = []
    
    for page in pages:
        if start_page <= page['page_num'] <= end_page:
            text = page['text'].strip()
            if text:
                # Bereinige den Text dieser Seite
                cleaned = clean_extracted_text(text)
                if cleaned:
                    result_parts.append(f"|{page['page_num']}| {cleaned}")
    
    # Kombiniere alle Teile
    full_text = '\n\n'.join(result_parts)
    
    # Entferne den Titel vom Anfang
    full_text = remove_title_from_text(full_text)
    
    return full_text


def process_ga_from_extracted_md(ga_number: str, dry_run: bool = False, single_file: str = None) -> Dict:
    """
    Verarbeite eine GA aus der _extracted.md Datei (mit Seitenmarkern).
    """
    ga_norm = ga_number.upper().replace('GA', '').replace(' ', '').zfill(3)
    
    print(f"\n{'='*60}")
    print(f"Reconstruct MD from Extracted-MD: GA{ga_norm}")
    print(f"{'='*60}")
    
    # Finde _extracted.md Datei
    extracted_md_path = find_extracted_md_file(ga_norm)
    if not extracted_md_path:
        return {'error': f'Keine _extracted.md Datei gefunden für GA{ga_norm}'}
    
    print(f"  Extracted-MD: {extracted_md_path.name}")
    
    # Finde normale PDF-MD für Vortragsabgrenzung
    pdf_md_path = find_pdf_md_file(ga_norm)
    if not pdf_md_path:
        return {'error': f'Keine PDF-MD Datei gefunden für GA{ga_norm}'}
    
    print(f"  PDF-MD (für Titel): {pdf_md_path.name}")
    
    # Extrahiere Seiten aus _extracted.md
    pages = extract_pages_from_extracted_md(extracted_md_path)
    print(f"  {len(pages)} Seiten extrahiert (S. {pages[0]['page_num']} - {pages[-1]['page_num']})")
    
    # Extrahiere Vorträge aus PDF-MD (für Titel und Abgrenzung)
    lectures = extract_lectures_from_pdf_md(pdf_md_path)
    print(f"  {len(lectures)} Vorträge gefunden")
    
    # Finde Seitengrenzen für jeden Vortrag
    boundaries = find_lecture_boundaries_in_extracted(pages, lectures)
    
    # Finde existierende MD-Dateien
    ga_folder = None
    for folder in STEINER_GA_BASE.iterdir():
        if folder.is_dir() and f"GA{ga_norm}" in folder.name.upper().replace(' ', '').replace('-', ''):
            ga_folder = folder
            break
    
    if not ga_folder:
        return {'error': f'Kein GA-Ordner gefunden für GA{ga_norm}'}
    
    md_files = sorted(ga_folder.glob("*.md"))
    md_files = [f for f in md_files if '_backup' not in f.name and f"GA{ga_norm}" in f.name.upper().replace(' ', '').replace('-', '')]
    
    print(f"  {len(md_files)} existierende MD-Dateien")
    
    results = []
    total_stats = {'old_block_ids': 0, 'matched_ids': 0, 'new_ids': 0, 'total_paragraphs': 0}
    
    for idx, lecture in enumerate(lectures):
        lecture_num = idx + 1
        
        if single_file and str(lecture_num) != str(single_file):
            continue
        
        # Finde passende MD-Datei
        matching_md = None
        file_num = f"({lecture_num}.)"
        for md_file in md_files:
            if file_num in md_file.name:
                matching_md = md_file
                break
        
        if not matching_md:
            print(f"  ⚠️  Keine MD-Datei für Vortrag {lecture_num}")
            continue
        
        if idx not in boundaries:
            print(f"  ⚠️  Keine Seitengrenzen für Vortrag {lecture_num}")
            continue
        
        start_page, end_page = boundaries[idx]
        print(f"\n  Verarbeite: {matching_md.name}")
        print(f"    Vortrag: {lecture['title'][:50]}... (S. {start_page}-{end_page})")
        
        old_md_content = matching_md.read_text(encoding='utf-8')
        old_block_ids = re.findall(r'\^([\w]+)', old_md_content)
        old_paragraphs = extract_paragraphs_with_ids(old_md_content)
        
        # Baue neuen Text mit Seitenmarkern
        new_text = build_lecture_text_with_markers(pages, start_page, end_page)
        new_paragraphs = split_into_paragraphs(new_text)
        
        # Übernehme Block-IDs
        new_paragraphs_with_ids = []
        matched_count = 0
        
        for new_para in new_paragraphs:
            new_norm = normalize_text(new_para)
            best_match = None
            best_score = 0
            
            for old_id, old_para in old_paragraphs:
                if old_id is None:
                    continue
                old_norm = normalize_text(old_para)
                from difflib import SequenceMatcher
                score = SequenceMatcher(None, new_norm[:200], old_norm[:200]).ratio()
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = old_id
            
            if best_match:
                new_paragraphs_with_ids.append(f"{new_para} ^{best_match}")
                matched_count += 1
            else:
                import hashlib
                new_id = hashlib.md5(new_para.encode()).hexdigest()[:6]
                new_paragraphs_with_ids.append(f"{new_para} ^{new_id}")
        
        metadata_match = re.match(r'^(Quelle:.*?\n)', old_md_content)
        metadata = metadata_match.group(1) if metadata_match else f"Quelle: [[GA{ga_norm}|GA{ga_norm}]]\n"
        
        new_md_content = metadata + '\n' + '\n\n'.join(new_paragraphs_with_ids)
        
        stats = {
            'old_block_ids': len(old_block_ids),
            'matched_ids': matched_count,
            'new_ids': len(new_paragraphs) - matched_count,
            'total_paragraphs': len(new_paragraphs),
            'pages': f"{start_page}-{end_page}"
        }
        
        match_rate = (matched_count / len(new_paragraphs) * 100) if new_paragraphs else 0
        print(f"    Block-IDs: {len(old_block_ids)} alt → {matched_count} übernommen ({match_rate:.1f}%)")
        
        for key in ['old_block_ids', 'matched_ids', 'new_ids', 'total_paragraphs']:
            total_stats[key] += stats.get(key, 0)
        
        if dry_run:
            print(f"    [DRY-RUN] Länge: {len(old_md_content)} → {len(new_md_content)} Zeichen")
            marker = re.search(r'\|(\d+)\|', new_md_content)
            if marker:
                print(f"    Erster Seitenmarker: |{marker.group(1)}|")
        else:
            backup_path = matching_md.with_name(f"{matching_md.stem}_backup.md")
            backup_path.write_text(old_md_content, encoding='utf-8')
            matching_md.write_text(new_md_content, encoding='utf-8')
            print(f"    Gespeichert: {matching_md.name}")
        
        results.append({
            'file': matching_md.name,
            'pages': stats['pages'],
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


def find_pdf_md_file(ga_number: str) -> Optional[Path]:
    """Finde die PDF-MD-Datei für eine GA-Nummer."""
    ga_norm = ga_number.upper().replace('GA', '').replace(' ', '').zfill(3)
    
    # Suche nach Ordner mit GA-Nummer
    for folder in STEINER_GA_MD.iterdir():
        if folder.is_dir() and f"GA {ga_norm}" in folder.name or f"GA{ga_norm}" in folder.name:
            # Suche MD-Datei im Ordner
            md_files = list(folder.glob("*.md"))
            if md_files:
                return md_files[0]
    
    # Alternativ: Direkt nach MD-Datei suchen
    for md_file in STEINER_GA_MD.glob(f"*GA*{ga_norm}*/*.md"):
        return md_file
    
    return None


def extract_lectures_from_pdf_md(pdf_md_path: Path) -> List[Dict]:
    """
    Extrahiere Vorträge aus einer PDF-MD-Datei.
    
    Rückgabe: Liste von {title, date, text, start_line, end_line}
    """
    content = pdf_md_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    lectures = []
    current_lecture = None
    
    # Ignoriere diese Titel (kein Vortrag) - sie beenden aber den vorherigen Vortrag!
    ignore_titles = ['INHALT', 'HINWEISE', 'PERSONENREGISTER', 'RUDOLF STEINER GESAMTAUSGABE', 
                     'VORWORT', 'EINLEITUNG', 'ANHANG', 'NAMENREGISTER', 'SACHREGISTER']
    
    for i, line in enumerate(lines):
        # H1-Titel gefunden?
        if line.startswith('# '):
            title = line[2:].strip()
            
            # Ist es ein ignorierter Titel?
            is_ignored = any(ignore in title.upper() for ignore in ignore_titles)
            
            # Vorherigen Vortrag IMMER abschließen (auch bei ignorierten Titeln!)
            if current_lecture:
                current_lecture['end_line'] = i - 1
                current_lecture['text'] = '\n'.join(lines[current_lecture['start_line']:i])
                lectures.append(current_lecture)
                current_lecture = None
            
            # Nur neuen Vortrag starten wenn nicht ignoriert
            if is_ignored:
                continue
            
            # Neuen Vortrag starten
            current_lecture = {
                'title': title,
                'date': '',
                'start_line': i,
                'end_line': None,
                'text': ''
            }
            
            # Suche Datum in den nächsten Zeilen
            for j in range(i + 1, min(i + 5, len(lines))):
                date_match = re.search(r'(Berlin|München|Dornach|Stuttgart|Wien|Hamburg|Köln|Leipzig|Nürnberg|Basel|Zürich)?,?\s*(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4})', lines[j])
                if date_match:
                    current_lecture['date'] = lines[j].strip()
                    current_lecture['start_line'] = j + 1  # Text beginnt nach Datum
                    break
    
    # Letzten Vortrag abschließen (falls noch offen)
    if current_lecture:
        current_lecture['end_line'] = len(lines) - 1
        current_lecture['text'] = '\n'.join(lines[current_lecture['start_line']:])
        lectures.append(current_lecture)
    
    return lectures


def clean_pdf_md_text(text: str) -> str:
    """
    Bereinige Text aus PDF-MD:
    - Entferne Copyright-Zeilen
    - Wandle Seitenzahlen in Marker um
    - Entferne --- Trennlinien
    """
    lines = text.split('\n')
    result_lines = []
    pending_page = None  # Seitenzahl für nächsten Absatz
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Copyright-Zeile mit Seitenzahl? (verschiedene Formate)
        # "Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 52 Seite: 14"
        # "Copyright Rudolf Steinet Nachlass-Verwaltung Buch: 52 Seite: 20" (Tippfehler)
        # "Copyright Rudolf Steiner Nachlass-Verwaltung  Buch: 5 2  Seite: 3" (Leerzeichen)
        if 'Copyright' in line and 'Steiner' in line:
            # Suche nach Seitenzahl
            page_match = re.search(r'Seite:\s*(\d[\d\s]*\d|\d)', line)
            if page_match:
                # Entferne Leerzeichen aus der Zahl
                page_num = page_match.group(1).replace(' ', '')
                pending_page = int(page_num)
            i += 1
            continue
        
        # Trennlinie?
        if line.strip() == '---':
            i += 1
            continue
        
        # Text mit pending Seitenmarker?
        if line.strip() and 'Copyright' not in line:
            if pending_page:
                # Füge Seitenmarker am Anfang ein
                line = f'|{pending_page}| {line.strip()}'
                pending_page = None
            result_lines.append(line)
        elif not line.strip():
            result_lines.append(line)
        
        i += 1
    
    # Bereinige Ergebnis
    text = '\n'.join(result_lines)
    
    # Entferne mehrfache Leerzeilen
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def process_ga_from_pdf_md(ga_number: str, dry_run: bool = False, single_file: str = None) -> Dict:
    """
    Verarbeite eine GA aus der PDF-MD-Datei.
    
    Args:
        ga_number: GA-Nummer (z.B. "GA052" oder "052")
        dry_run: Nur Preview, keine Änderungen speichern
        single_file: Optional - nur diesen Vortrag verarbeiten (z.B. "1" für Vortrag 1)
    """
    ga_norm = ga_number.upper().replace('GA', '').replace(' ', '').zfill(3)
    
    print(f"\n{'='*60}")
    print(f"Reconstruct MD from PDF-MD: GA{ga_norm}")
    print(f"{'='*60}")
    
    # Finde PDF-MD-Datei
    pdf_md_path = find_pdf_md_file(ga_norm)
    if not pdf_md_path:
        return {'error': f'Keine PDF-MD-Datei gefunden für GA{ga_norm}'}
    
    print(f"  PDF-MD: {pdf_md_path.name}")
    
    # Extrahiere Vorträge
    lectures = extract_lectures_from_pdf_md(pdf_md_path)
    print(f"  {len(lectures)} Vorträge gefunden")
    
    # Finde existierende MD-Dateien
    ga_folder = None
    for folder in STEINER_GA_BASE.iterdir():
        if folder.is_dir() and f"GA{ga_norm}" in folder.name.upper().replace(' ', '').replace('-', ''):
            ga_folder = folder
            break
    
    if not ga_folder:
        return {'error': f'Kein GA-Ordner gefunden für GA{ga_norm}'}
    
    md_files = sorted(ga_folder.glob("*.md"))
    # Filter Backup-Dateien
    md_files = [f for f in md_files if '_backup' not in f.name and f"GA{ga_norm}" in f.name.upper().replace(' ', '').replace('-', '')]
    
    print(f"  {len(md_files)} existierende MD-Dateien")
    
    results = []
    total_stats = {
        'old_block_ids': 0,
        'matched_ids': 0,
        'new_ids': 0,
        'total_paragraphs': 0
    }
    
    # Verarbeite jeden Vortrag
    for idx, lecture in enumerate(lectures):
        lecture_num = idx + 1
        
        # Filter für single_file (ZUERST prüfen!)
        if single_file:
            if str(lecture_num) != str(single_file):
                continue
        
        # Finde passende MD-Datei über Nummerierung
        matching_md = None
        file_num = f"({lecture_num}.)"
        for md_file in md_files:
            if file_num in md_file.name:
                matching_md = md_file
                break
        
        if not matching_md:
            print(f"  ⚠️  Keine MD-Datei für Vortrag {lecture_num}: {lecture['title'][:50]}...")
            continue
        
        print(f"\n  Verarbeite: {matching_md.name}")
        print(f"    Vortrag: {lecture['title'][:60]}...")
        
        # Lade existierenden MD-Inhalt
        old_md_content = matching_md.read_text(encoding='utf-8')
        
        # Extrahiere Block-IDs aus altem MD
        old_block_ids = re.findall(r'\^([\w]+)', old_md_content)
        old_paragraphs = extract_paragraphs_with_ids(old_md_content)
        
        # Bereinige PDF-MD-Text
        cleaned_text = clean_pdf_md_text(lecture['text'])
        
        # Entferne eventuell noch vorhandene Titel-Zeilen am Anfang
        # (H1-Titel und Datum, die in manchen Extraktionen noch vorhanden sind)
        cleaned_text = re.sub(r'^#\s+[^\n]+\n+', '', cleaned_text)  # H1-Titel
        cleaned_text = re.sub(r'^[^\n]*\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}[^\n]*\n+', '', cleaned_text)  # Datum-Zeile
        
        # Teile in Absätze
        new_paragraphs = split_into_paragraphs(cleaned_text)
        
        # Übernehme Block-IDs durch Text-Matching
        new_paragraphs_with_ids = []
        matched_count = 0
        
        for new_para in new_paragraphs:
            new_norm = normalize_text(new_para)
            best_match = None
            best_score = 0
            
            for old_id, old_para in old_paragraphs:
                old_norm = normalize_text(old_para)
                
                # Berechne Ähnlichkeit
                from difflib import SequenceMatcher
                score = SequenceMatcher(None, new_norm[:200], old_norm[:200]).ratio()
                
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = old_id
            
            if best_match:
                new_paragraphs_with_ids.append(f"{new_para} ^{best_match}")
                matched_count += 1
            else:
                # Generiere neue Block-ID
                import hashlib
                new_id = hashlib.md5(new_para.encode()).hexdigest()[:6]
                new_paragraphs_with_ids.append(f"{new_para} ^{new_id}")
        
        # Extrahiere Metadaten aus altem MD
        metadata_match = re.match(r'^(Quelle:.*?\n)', old_md_content)
        metadata = metadata_match.group(1) if metadata_match else f"Quelle: [[GA{ga_norm}|GA{ga_norm}]]\n"
        
        # Erstelle neuen MD-Inhalt
        new_md_content = metadata + '\n' + '\n\n'.join(new_paragraphs_with_ids)
        
        # Statistiken
        stats = {
            'old_block_ids': len(old_block_ids),
            'matched_ids': matched_count,
            'new_ids': len(new_paragraphs) - matched_count,
            'total_paragraphs': len(new_paragraphs)
        }
        
        match_rate = (matched_count / len(new_paragraphs) * 100) if new_paragraphs else 0
        print(f"    Block-IDs: {len(old_block_ids)} alt → {matched_count} übernommen ({match_rate:.1f}%), {stats['new_ids']} neu")
        
        # Akkumuliere
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
        
        # Speichere
        if dry_run:
            print(f"    [DRY-RUN] Würde speichern:")
            print(f"    Länge alt: {len(old_md_content)} Zeichen")
            print(f"    Länge neu: {len(new_md_content)} Zeichen")
            print(f"    Erste 300 Zeichen:\n{new_md_content[:300]}")
        else:
            # Backup
            backup_path = matching_md.with_name(f"{matching_md.stem}_backup.md")
            backup_path.write_text(old_md_content, encoding='utf-8')
            print(f"    Backup: {backup_path.name}")
            
            # Speichern
            matching_md.write_text(new_md_content, encoding='utf-8')
            print(f"    Gespeichert: {matching_md.name}")
        
        results.append({
            'file': matching_md.name,
            'pages': 0,  # Nicht relevant für PDF-MD-Modus
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
        print("Verwendung: python reconstruct_md_from_pdf.py GA057 [--dry-run] [--from-extracted] [Vortrag-Nr]")
        print("  --dry-run         Keine Änderungen speichern, nur Preview")
        print("  --from-extracted  Verwende _extracted.md als Quelle (MIT Seitenmarkern!)")
        print("  --from-md         Verwende PDF-MD-Datei als Quelle (ohne Seitenmarker)")
        print("  --file NAME       Nur Datei mit NAME im Dateinamen verarbeiten")
        print("  ODER: python reconstruct_md_from_pdf.py GA051 1  (nur Vortrag 1)")
        sys.exit(1)
    
    ga_number = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    from_extracted = '--from-extracted' in sys.argv
    from_md = '--from-md' in sys.argv
    
    # Parse --file Argument oder zweiten Parameter als Dateifilter
    single_file = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            single_file = sys.argv[idx + 1]
    elif len(sys.argv) >= 3 and not sys.argv[2].startswith('--'):
        # Zweiter Parameter ohne -- wird als Dateifilter interpretiert
        single_file = sys.argv[2]
    
    if dry_run:
        print("*** DRY-RUN MODUS - Keine Dateien werden geändert ***\n")
    
    # Wähle Verarbeitungsmethode
    if from_extracted:
        print("*** MODUS: Extracted-MD als Quelle (MIT Seitenmarkern) ***\n")
        result = process_ga_from_extracted_md(ga_number, dry_run=dry_run, single_file=single_file)
    elif from_md:
        print("*** MODUS: PDF-MD als Quelle (ohne Seitenmarker) ***\n")
        result = process_ga_from_pdf_md(ga_number, dry_run=dry_run, single_file=single_file)
    else:
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

