#!/usr/bin/env python3
"""
generate_pagebreaks_with_pdf.py
===============================
Generiert Seitenmarker (Pagebreaks) durch Extraktion aus PDF-Dateien.

Verwendet die PDFs mit Seitenzahlen (Format: "Steiner, Rudolf GA XXX, YYYY - Titel")
aus Steiner_GA_pdf/ um |XX| Marker in die Vorträge/Bücher einzufügen.

Verwendung:
  python tools/generate_pagebreaks_with_pdf.py GA061
  python tools/generate_pagebreaks_with_pdf.py GA061 --update-source
  python tools/generate_pagebreaks_with_pdf.py 61 67  # Bereich
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

SCRIPT_DIR = Path(__file__).parent.parent
PDF_DIR = SCRIPT_DIR / "Steiner_GA_pdf"
LECTURES_DIR = SCRIPT_DIR / "steiner-full-lectures"
BOOKS_DIR = SCRIPT_DIR / "steiner-books"
PAGEBREAKS_DIR = SCRIPT_DIR / "pagebreaks"
MAPPING_FILE = SCRIPT_DIR / "lecture-page-mapping.json"
SUMMARY_DB_FILE = SCRIPT_DIR / "summary-database.json"
PAGE_BREAK_MARKERS_FILE = SCRIPT_DIR / "page-break-markers.json"

# Ligaturen für Normalisierung
LIGATURES = {
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    "ﬅ": "st", "ﬆ": "st", "Ꜳ": "AA", "ꜳ": "aa", "Æ": "AE", "æ": "ae",
    "Œ": "OE", "œ": "oe",
}


def load_first_content_page(ga_number: str) -> Optional[int]:
    """
    Lädt die erste Inhaltsseite aus page-break-markers.json.
    Verwendet entweder contentRange[0] oder den ersten Break mit isFirstPage=true.
    """
    if not PAGE_BREAK_MARKERS_FILE.exists():
        return None
    
    try:
        with open(PAGE_BREAK_MARKERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        ga_data = data.get(ga_number.upper(), {})
        if not ga_data or not isinstance(ga_data, dict):
            return None
        
        # Priorität 1: contentRange[0]
        content_range = ga_data.get("contentRange")
        if content_range and isinstance(content_range, list) and len(content_range) >= 1:
            first_page = content_range[0]
            if isinstance(first_page, int) and first_page > 0:
                return first_page
        
        # Priorität 2: Erster Break mit isFirstPage=true
        breaks = ga_data.get("breaks", [])
        for b in breaks:
            if b.get("isFirstPage"):
                page = b.get("page")
                if isinstance(page, int) and page > 0:
                    return page
        
        # Priorität 3: Erster Break überhaupt
        if breaks and isinstance(breaks[0], dict):
            page = breaks[0].get("page")
            if isinstance(page, int) and page > 0:
                return page
        
        return None
    except Exception:
        return None


def load_chapter_indices(ga_number: str) -> List[str]:
    """Lädt Kapitel-Index-IDs aus summary-database.json für ein Buch."""
    if not SUMMARY_DB_FILE.exists():
        return []
    
    try:
        with open(SUMMARY_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        ga_data = data.get(ga_number.upper(), {})
        headings = ga_data.get("headings", [])
        return [h["index"] for h in headings if "index" in h]
    except Exception:
        return []


def split_book_into_chapters(book: Dict, ga_number: str) -> List[Dict]:
    """
    Teilt ein Buch in Kapitel auf, basierend auf summary-database.json.
    Jedes Kapitel wird wie ein Vortrag behandelt.
    """
    chapter_indices = load_chapter_indices(ga_number)
    if not chapter_indices:
        # Keine Kapitel-Info -> Buch als Ganzes behandeln
        return [book]
    
    paragraphs = book.get("paragraphs", [])
    if not paragraphs:
        return [book]
    
    # Finde Kapitel-Grenzen
    chapter_starts = []
    for i, para in enumerate(paragraphs):
        if para.get("index") in chapter_indices:
            chapter_starts.append(i)
    
    if not chapter_starts:
        # Keine Kapitel gefunden -> Buch als Ganzes
        return [book]
    
    # Erstelle Kapitel-"Vorträge"
    chapters = []
    for idx, start in enumerate(chapter_starts):
        end = chapter_starts[idx + 1] if idx + 1 < len(chapter_starts) else len(paragraphs)
        
        chapter_paras = paragraphs[start:end]
        if not chapter_paras:
            continue
        
        # Kapitel-Titel aus erstem Absatz oder Index
        first_para = chapter_paras[0]
        title = first_para.get("content", "")[:50] if first_para else f"Kapitel {idx + 1}"
        
        chapter = {
            "ID": f"{ga_number}/{idx + 1}",
            "gaNumber": ga_number,
            "title": title,
            "lectureNumber": idx + 1,
            "paragraphs": chapter_paras,
            "_chapter_start_idx": start,  # Für spätere Zuordnung
            "_chapter_end_idx": end,
        }
        chapters.append(chapter)
    
    return chapters


def normalize_ga(ga_arg: str) -> Optional[str]:
    """Normalisiert GA-Nummer (z.B. '61' -> 'GA061', 'ga065' -> 'GA065')."""
    m = re.search(r"(\d+[a-z]?)", ga_arg, re.IGNORECASE)
    if not m:
        return None
    num_part = m.group(1)
    # Zahl mit führenden Nullen auf 3 Stellen, Suffix in Großbuchstaben
    if num_part[-1].isalpha():
        return f"GA{num_part[:-1].zfill(3)}{num_part[-1].upper()}"
    return f"GA{num_part.zfill(3)}"


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """
    Findet die PDF-Datei für eine GA-Nummer.
    Sucht nach Format: "Steiner, Rudolf GA XXX, YYYY - Titel.pdf"
    """
    m = re.search(r"(\d+)([a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    
    ga_num = m.group(1).zfill(3)
    ga_suffix = m.group(2).lower() if m.group(2) else ""
    
    # Muster für die Suche
    patterns = [
        f"ga {ga_num}{ga_suffix}",
        f"ga{ga_num}{ga_suffix}",
        f"ga {ga_num} {ga_suffix}" if ga_suffix else f"ga {ga_num}",
    ]
    
    candidates = []
    for pdf in PDF_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        # Muss "steiner" enthalten (die richtigen PDFs)
        if "steiner" not in name_lower:
            continue
        # Tafelzeichnungen-PDFs ausschließen
        if "tafelzeichnungen" in name_lower:
            continue
        
        for pattern in patterns:
            if pattern in name_lower.replace(",", " ").replace("  ", " "):
                candidates.append(pdf)
                break
    
    if not candidates:
        return None
    
    # Bevorzuge "_einzelseiten" PDFs
    for c in candidates:
        if "_einzelseiten" in c.name.lower():
            return c
    
    # Vermeide "_doppelseiten" PDFs
    for c in candidates:
        if "_doppelseiten" not in c.name.lower():
            return c
    
    return candidates[0]


def normalize_for_match(text: str) -> str:
    """
    Längenerhaltende Normalisierung für Positionsfindung.
    WICHTIG: Die Länge muss erhalten bleiben für korrektes Position-Mapping!
    """
    if not text:
        return ""
    
    s = text
    
    # Soft hyphen und nbsp durch Leerzeichen ersetzen (gleiche Länge)
    s = s.replace("\u00ad", " ").replace("\u00a0", " ")
    
    # Ligaturen expandieren - ACHTUNG: ändert Länge!
    # Wir müssen das anders handhaben für längenerhaltende Normalisierung
    # Für jetzt: einfach lowercase
    s = s.lower()
    
    return s


def normalize_for_comparison(text: str) -> str:
    """
    Aggressive Normalisierung für Fuzzy-Vergleiche.
    Entfernt alles außer alphanumerischen Zeichen.
    """
    if not text:
        return ""
    
    s = text.lower()
    
    # Ligaturen expandieren
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    
    # ß -> ss
    s = s.replace("ß", "ss")
    
    # Nur alphanumerisch behalten
    s = re.sub(r"[^a-z0-9äöü]", "", s)
    
    return s


def extract_page_number_from_footer(lines: List[str]) -> Optional[int]:
    """
    Extrahiert die Seitenzahl aus den Footer-Zeilen.
    
    Unterstützte Formate:
    1. "Seite: XX" (ältere PDFs mit Copyright-Footer)
    2. Einzelne Zahl DIREKT gefolgt von "RUDOLF STEINER" (GA069b-Format)
       - ABER: vorherige Zeile muss wie normaler Text aussehen (min. 30 Zeichen)
       - Verhindert Erkennung im Inhaltsverzeichnis
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
    # KRITERIEN:
    # - Die Zahl muss auf einer eigenen Zeile stehen
    # - Direkt danach kommt RUDOLF STEINER
    # - VOR der Zahl muss normaler Fließtext stehen (min. 30 Zeichen)
    # - Die vorherige Zeile darf NICHT wie Inhaltsverzeichnis aussehen
    for i in range(1, len(non_empty) - 1):  # Start bei 1, um prev_line zu haben
        _, prev_line = non_empty[i - 1]
        _, current = non_empty[i]
        _, next_line = non_empty[i + 1]
        
        if re.match(r"^\d{1,3}$", current):
            # Nächste Zeile muss "RUDOLF STEINER" sein
            if "RUDOLF STEINER" in next_line.upper():
                # Vorherige Zeile muss wie Fließtext aussehen:
                # - Mindestens 30 Zeichen lang
                # - Nicht nur eine Zahl
                # - Nicht wie Inhaltsverzeichnis (diese enden typisch mit Zahlen)
                if len(prev_line) >= 30 and not re.match(r"^\d+$", prev_line):
                    # Inhaltsverzeichnis-Zeilen enden oft mit Seitenzahlen
                    # Fließtext endet mit Buchstaben oder Satzzeichen
                    if not re.search(r"\d{2,3}\s*$", prev_line):
                        return int(current)
    
    # Format 3: "Seite XX" nur in den letzten 3 nicht-leeren Zeilen
    for _, line in non_empty[-3:]:
        match = re.match(r"^Seite\s+(\d+)$", line, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def extract_body_text(page_text: str) -> str:
    """
    Extrahiert den Body-Text ohne Copyright-Footer.
    """
    lines = page_text.split("\n")
    
    # Finde Copyright-Zeile und schneide ab
    body_lines = []
    for i, line in enumerate(lines):
        if "copyright" in line.lower() and "steiner" in line.lower():
            break
        body_lines.append(line)
    
    return "\n".join(body_lines)


def extract_first_words(text: str, num_words: int = 20) -> str:
    """
    Extrahiert die ersten N Wörter aus einem Text.
    Überspringt dabei Header wie "Seite XX" und leere Zeilen.
    Optimiert für neue GA-Ausgabe: Durchsucht mehr Zeilen und ist weniger restriktiv.
    """
    if not text or not text.strip():
        return ""
    
    lines = text.split("\n")
    words = []
    skipped_header_lines = 0
    max_header_lines = 3  # Maximal 3 Header-Zeilen überspringen
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Überspringe nur eindeutige Header-Zeilen (maximal 3)
        is_header = False
        if skipped_header_lines < max_header_lines:
            # Eindeutige Header-Muster
            if re.match(r"^Seite\s+\d+\s*$", line, re.IGNORECASE):
                is_header = True
            elif line.upper() in ["RUDOLF STEINER", "VERLAG"]:
                is_header = True
            elif "COPYRIGHT" in line.upper() and "STEINER" in line.upper():
                is_header = True
            elif len(line) < 5 and line.isdigit():  # Einzelne Zahl (wahrscheinlich Seitenzahl)
                is_header = True
        
        if is_header:
            skipped_header_lines += 1
            continue
        
        # Sammle Wörter aus dieser Zeile
        line_words = line.split()
        if line_words:
            words.extend(line_words)
        
        # Wenn wir genug Wörter haben, stoppe
        if len(words) >= num_words:
            break
    
    # Wenn zu wenige Wörter gefunden wurden, nimm einfach die ersten Zeichen des Textes
    if len(words) < 5:
        # Fallback: Nimm die ersten 150 Zeichen und extrahiere Wörter daraus
        fallback_text = text.strip()[:150]
        fallback_words = fallback_text.split()
        # Entferne sehr kurze "Wörter" (wahrscheinlich OCR-Fehler)
        fallback_words = [w for w in fallback_words if len(w) >= 2]
        words = fallback_words[:num_words]
    
    return " ".join(words[:num_words])


def extract_pdf_pages(pdf_path: Path) -> List[Tuple[int, int, str, str, str]]:
    """
    Extrahiert alle Seiten mit Seitenzahlen aus der PDF.
    
    Unterstützte Formate:
    1. Copyright Rudolf Steiner...Seite: XX (ältere PDFs)
    2. "Seite X" am Ende der Seite (neuere PDFs)
    3. Einzelne Zahl + "RUDOLF STEINER" + "VERLAG" (GA069b-Format)
    4. Einzelne Zahl am Ende der Seite
    
    Für Marker |N| brauchen wir:
        - prev_end: Ende von Seite N-1
        - this_start: Anfang von Seite N (erste 300 Zeichen)
        - this_start_words: Erste Wörter von Seite N (für neue GA-Ausgabe)
    
    Rückgabe: Liste von (PDF-Index, Seitenzahl N, Ende-Seite-N-1, Anfang-Seite-N, Erste-Wörter-Seite-N)
    """
    doc = fitz.open(pdf_path)
    
    # Sammle alle Seiten mit Seitenzahlen
    page_data = []  # (pdf_index, page_num, text_start, text_end)
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        if not text.strip():
            continue
        
        lines = text.split("\n")
        page_num = None
        body_text = text  # Default: gesamter Text
        
        # Format 1: Copyright-Zeile (auch mit OCR-Fehlern)
        copyright_match = re.search(
            r'Copyright\s+Rudolf\s+Stein\w*.*?Seite:\s*([\d\s]+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if copyright_match:
            page_str = copyright_match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                page_num = int(page_str)
                body_text = text[:copyright_match.start()].strip()
        
        # Format 2-4: Verwende extract_page_number_from_footer
        if page_num is None:
            page_num = extract_page_number_from_footer(lines)
            if page_num is not None:
                # Entferne Footer-Zeilen vom Body
                # Suche nach der Zeile mit der Seitenzahl und entferne alles danach
                for j in range(len(lines) - 1, -1, -1):
                    stripped = lines[j].strip()
                    if stripped == str(page_num):
                        body_text = "\n".join(lines[:j]).strip()
                        break
                    # Auch "Seite XX" am Ende entfernen
                    if re.match(rf"^Seite\s+{page_num}\s*$", stripped, re.IGNORECASE):
                        body_text = "\n".join(lines[:j]).strip()
                        break
        
        if page_num is None:
            continue
        
        # Entferne Footer-Elemente (RUDOLF STEINER, VERLAG, etc.)
        body_lines = body_text.split("\n")
        while body_lines and any(x in body_lines[-1].upper() for x in ["RUDOLF STEINER", "VERLAG"]):
            body_lines.pop()
        
        # Entferne Header "Seite XX" am Anfang (GA069b-Format)
        while body_lines and re.match(rf"^Seite\s+\d+\s*$", body_lines[0].strip(), re.IGNORECASE):
            body_lines.pop(0)
        
        body_text = "\n".join(body_lines).strip()
        
        if not body_text:
            continue
        
        # Anfang dieser Seite (erste 300 Zeichen)
        text_start = body_text[:300] if len(body_text) > 300 else body_text
        # Ende dieser Seite (letzte 300 Zeichen)
        text_end = body_text[-300:] if len(body_text) > 300 else body_text
        # Erste Wörter vom Seitenanfang (für neue GA-Ausgabe)
        # Erhöht auf 20 Wörter für bessere Erkennung
        first_words = extract_first_words(body_text, num_words=20)
        
        # Fallback: Wenn extract_first_words zu wenige Wörter zurückgibt, 
        # verwende einfach die ersten Zeichen von text_start
        if len(first_words.split()) < 5:
            # Nimm die ersten 100 Zeichen und extrahiere Wörter daraus
            fallback_text = text_start[:100].strip()
            fallback_words = [w for w in fallback_text.split() if len(w) >= 2]
            if len(fallback_words) >= 5:
                first_words = " ".join(fallback_words[:20])
        
        page_data.append((i, page_num, text_start, text_end, first_words))
    
    doc.close()
    
    # Korrigiere nicht-fortlaufende Seitenzahlen (OCR-Fehler)
    # z.B. wenn Seite 383 zweimal vorkommt und 388 fehlt
    page_data = fix_page_numbers(page_data)
    
    # Für jeden Marker |N|: prev_end (Ende S.N-1) + this_start (Anfang S.N) + this_start_words
    pages = []
    
    for idx, (pdf_idx, page_num, text_start, text_end, first_words) in enumerate(page_data):
        # prev_end = Ende der VORHERIGEN Seite (N-1)
        if idx > 0:
            prev_end = page_data[idx - 1][3]  # text_end der vorherigen Seite
        else:
            prev_end = ""
        
        # this_start = Anfang DIESER Seite (N) - erste 300 Zeichen
        this_start = text_start
        
        # this_start_words = Erste Wörter dieser Seite (für neue GA-Ausgabe)
        this_start_words = first_words
        
        # Marker |page_num| kommt zwischen prev_end und this_start
        pages.append((pdf_idx, page_num, prev_end, this_start, this_start_words))
    
    return pages


def fix_page_numbers(page_data: List[Tuple[int, int, str, str, str]]) -> List[Tuple[int, int, str, str, str]]:
    """
    Korrigiert nicht-fortlaufende Seitenzahlen.
    
    Wenn eine Seitenzahl nicht zur Sequenz passt (z.B. 383 statt 388),
    wird sie basierend auf der erwarteten Fortlaufung korrigiert.
    """
    if len(page_data) < 3:
        return page_data
    
    corrected = []
    
    for idx, (pdf_idx, page_num, text_start, text_end, first_words) in enumerate(page_data):
        expected_page = None
        
        if idx > 0:
            prev_page = corrected[-1][1]
            expected_page = prev_page + 1
            
            # Prüfe ob die aktuelle Seitenzahl zur Sequenz passt
            # Toleranz: max 2 Seiten Sprung (für fehlende Seiten)
            if abs(page_num - expected_page) > 2:
                # Seitenzahl passt nicht - korrigiere sie
                corrected.append((pdf_idx, expected_page, text_start, text_end, first_words))
                continue
        
        corrected.append((pdf_idx, page_num, text_start, text_end, first_words))
    
    return corrected


def load_lectures_for_ga(ga_number: str) -> Tuple[Dict[Path, List[Dict]], List[Dict]]:
    """
    Lädt alle Vorträge/Aufsätze für eine GA-Nummer.
    Rückgabe: (Dict von Datei → Vorträge in dieser Datei, Gesamtliste aller Vorträge)
    """
    ga_upper = ga_number.upper()
    files_map: Dict[Path, List[Dict]] = {}  # Datei → Liste der Vorträge in dieser Datei
    all_lectures = []
    
    # Suche in steiner-full-lectures
    for path in sorted(LECTURES_DIR.glob("steiner-full-lectures-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for lec in data.get("lectures", []):
                if (lec.get("gaNumber") or "").upper() == ga_upper:
                    if path not in files_map:
                        files_map[path] = []
                    files_map[path].append(lec)
                    all_lectures.append(lec)
        except Exception:
            continue
    
    # Sortiere nach lectureNumber
    all_lectures.sort(key=lambda x: int(x.get("lectureNumber") or 0))
    return files_map, all_lectures


def load_books_for_ga(ga_number: str) -> Tuple[Optional[Path], Optional[Dict], List[Path]]:
    """
    Lädt ein Buch für eine GA-Nummer.
    Rückgabe: (Quell-Datei, Buch-Dict, Liste aller Dateien die dieses Buch enthalten)
    
    WICHTIG: Bevorzugt die spezifische GA-Datei (z.B. steiner-books-012-012.json für GA012)
    vor allgemeinen Dateien (z.B. steiner-books-001-012-part01.json)
    """
    ga_upper = ga_number.upper()
    # Extrahiere nur die Nummer (z.B. "012" aus "GA012" oder "040a" aus "GA040a")
    ga_match = re.search(r"(\d{3}[a-z]?)", ga_number, re.IGNORECASE)
    ga_num = ga_match.group(1).lower() if ga_match else ga_number.lower()
    
    all_files = []  # Alle Dateien die dieses Buch enthalten
    specific_book = None  # Aus der spezifischen GA-Datei
    specific_path = None
    fallback_book = None  # Aus einer anderen Datei
    fallback_path = None
    
    for path in sorted(BOOKS_DIR.glob("steiner-books-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for book in data.get("books", []):
                if (book.get("gaNumber") or "").upper() == ga_upper:
                    all_files.append(path)
                    
                    # Prüfe ob das die spezifische GA-Datei ist
                    # Pattern: steiner-books-XXX-XXX*.json (z.B. steiner-books-012-012.json)
                    # NICHT: steiner-books-002-012.json (Bereich von 002 bis 012)
                    filename = path.name.lower()
                    # Die spezifische Datei hat die gleiche GA-Nummer zweimal
                    is_specific = f"-{ga_num}-{ga_num}" in filename
                    
                    if is_specific and specific_book is None:
                        specific_book = book
                        specific_path = path
                    elif fallback_book is None:
                        fallback_book = book
                        fallback_path = path
                    break  # Nur einmal pro Datei
        except Exception:
            continue
    
    # Bevorzuge die spezifische Datei
    if specific_book is not None:
        return specific_path, specific_book, all_files
    else:
        return fallback_path, fallback_book, all_files


def load_page_mapping() -> Dict:
    """Lädt das Lecture-Page-Mapping."""
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_page_mapping(mapping: Dict) -> None:
    """Speichert das Lecture-Page-Mapping."""
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def is_old_pdf_format(pdf_path: Path) -> bool:
    """
    Prüft, ob das PDF das "alte" Format hat (mit Copyright-Footer).
    Altes Format: "Copyright Rudolf Steiner...Seite: XX"
    Neues Format: Seitenzahl einzeln oder "Seite XX" am Ende
    """
    doc = fitz.open(pdf_path)
    copyright_count = 0
    pages_checked = 0
    
    # Prüfe 20 Seiten in der Mitte des PDFs
    start_page = min(20, len(doc) // 4)
    end_page = min(start_page + 30, len(doc))
    
    for i in range(start_page, end_page):
        page = doc[i]
        text = page.get_text("text") or ""
        pages_checked += 1
        
        # Suche nach Copyright-Zeile
        if re.search(r'Copyright\s+Rudolf\s+Stein\w*.*?Seite:\s*\d+', text, re.IGNORECASE | re.DOTALL):
            copyright_count += 1
    
    doc.close()
    
    # Wenn mehr als 50% der Seiten Copyright haben → altes Format
    return copyright_count > pages_checked * 0.5


def extract_toc_entries(pdf_path: Path, num_lectures: int) -> List[Dict]:
    """
    Extrahiert Vortragstitel und Seitenzahlen aus dem Inhaltsverzeichnis.
    Versucht verschiedene Muster zu erkennen.
    
    Rückgabe: Liste von {title, page}
    """
    doc = fitz.open(pdf_path)
    
    # Sammle alle Zeilen aus dem Inhaltsverzeichnis (Seiten 4-15)
    toc_lines = []
    for i in range(3, min(16, len(doc))):
        page = doc[i]
        text = page.get_text()
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and stripped not in ['RUDOLF STEINER', 'VERLAG', 'INHALT', 'Inhalt']:
                # Entferne 'Seite X' Header
                if not re.match(r'^Seite\s+\d+$', stripped, re.IGNORECASE):
                    toc_lines.append(stripped)
    
    doc.close()
    
    entries = []
    
    # Muster 1: Titel mit Datum, dann Seitenzahl auf nächster Zeile
    # z.B. "Erkenntnis und Unsterblichkeit (Düsseldorf, 19. Februar 1910)"
    #      "13"
    date_pattern = r'\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)'
    
    i = 0
    while i < len(toc_lines):
        line = toc_lines[i]
        
        # Hat diese Zeile ein Datum?
        if re.search(date_pattern, line, re.IGNORECASE):
            # Nächste Zeile sollte Seitenzahl sein
            if i + 1 < len(toc_lines):
                next_line = toc_lines[i + 1].strip()
                if re.match(r'^\d{1,3}$', next_line):
                    entries.append({
                        'title': line,
                        'page': int(next_line)
                    })
                    i += 2
                    continue
        
        # Muster 2: Titel, Ort/Datum auf nächster Zeile, Seitenzahl auf übernächster
        if i + 2 < len(toc_lines):
            next1 = toc_lines[i + 1]
            next2 = toc_lines[i + 2].strip()
            
            if re.search(date_pattern, next1, re.IGNORECASE) and re.match(r'^\d{1,3}$', next2):
                entries.append({
                    'title': f"{line} ({next1})",
                    'page': int(next2)
                })
                i += 3
                continue
        
        # Muster 3: "Titel ... Seitenzahl" auf einer Zeile (mit Punkten oder Leerzeichen)
        match = re.match(r'^(.+?)\s*[\.\s]{3,}\s*(\d{1,3})$', line)
        if match:
            entries.append({
                'title': match.group(1).strip(),
                'page': int(match.group(2))
            })
            i += 1
            continue
        
        # Muster 4: Zeile endet mit Seitenzahl
        match = re.match(r'^(.+?)\s+(\d{1,3})$', line)
        if match and len(match.group(1)) > 10:  # Titel mind. 10 Zeichen
            entries.append({
                'title': match.group(1).strip(),
                'page': int(match.group(2))
            })
            i += 1
            continue
        
        i += 1
    
    # Sortiere nach Seitenzahl und entferne Duplikate
    entries.sort(key=lambda x: x['page'])
    
    # Entferne Einträge mit gleicher Seitenzahl (behalte ersten)
    seen_pages = set()
    unique_entries = []
    for e in entries:
        if e['page'] not in seen_pages:
            seen_pages.add(e['page'])
            unique_entries.append(e)
    
    # Filtere nur Einträge mit plausiblen Seitenzahlen (> 5 und < 500)
    unique_entries = [e for e in unique_entries if 5 < e['page'] < 500]
    
    return unique_entries


def find_first_text_page(pdf_path: Path, toc_page: int) -> int:
    """
    Findet die erste Seite mit echtem Textinhalt ab einer TOC-Seitenzahl.
    
    Das Inhaltsverzeichnis zeigt oft die Titelseite an, aber der eigentliche
    Text beginnt erst 1-2 Seiten später. Diese Funktion prüft, ob die
    angegebene Seite eine Titelseite ist und sucht dann die erste Textseite.
    
    Kriterien für Titelseite:
    - Weniger als 500 Zeichen Text
    - Enthält typische Titelseiten-Elemente
    
    Rückgabe: Seitenzahl der ersten Textseite
    """
    doc = fitz.open(pdf_path)
    
    # Konvertiere Seitenzahl zu PDF-Index (Seite 9 = Index 8)
    # Wir müssen die richtige PDF-Seite finden
    for pdf_idx in range(len(doc)):
        page = doc[pdf_idx]
        text = page.get_text("text") or ""
        
        # Prüfe ob diese Seite die gesuchte Seitenzahl hat
        if f"Seite {toc_page}" in text or re.search(rf'\b{toc_page}\b', text[-100:]):
            # Gefunden! Prüfe ob es eine Titelseite ist
            # Entferne Header/Footer für Textlängenprüfung
            body_lines = text.split('\n')
            body_lines = [l for l in body_lines if not any(x in l.upper() for x in 
                          ['RUDOLF STEINER', 'VERLAG', 'SEITE'])]
            body_text = '\n'.join(body_lines).strip()
            
            # Weniger als 500 Zeichen = wahrscheinlich Titelseite
            if len(body_text) < 500:
                # Suche nächste Seite mit mehr Text
                for next_idx in range(pdf_idx + 1, min(pdf_idx + 4, len(doc))):
                    next_page = doc[next_idx]
                    next_text = next_page.get_text("text") or ""
                    
                    # Finde Seitenzahl dieser Seite
                    page_match = re.search(r'Seite\s+(\d+)', next_text)
                    if not page_match:
                        # Versuche Zahl am Ende
                        lines = next_text.strip().split('\n')
                        for line in reversed(lines[-5:]):
                            if line.strip().isdigit():
                                page_num = int(line.strip())
                                if page_num > toc_page and page_num < toc_page + 5:
                                    # Prüfe Textlänge
                                    body_lines = next_text.split('\n')
                                    body_lines = [l for l in body_lines if not any(x in l.upper() for x in 
                                                  ['RUDOLF STEINER', 'VERLAG', 'SEITE'])]
                                    if len('\n'.join(body_lines).strip()) > 500:
                                        doc.close()
                                        return page_num
                                break
                    else:
                        page_num = int(page_match.group(1))
                        # Prüfe Textlänge
                        body_lines = next_text.split('\n')
                        body_lines = [l for l in body_lines if not any(x in l.upper() for x in 
                                      ['RUDOLF STEINER', 'VERLAG', 'SEITE'])]
                        if len('\n'.join(body_lines).strip()) > 500:
                            doc.close()
                            return page_num
            break
    
    doc.close()
    return toc_page  # Fallback: Original-Seitenzahl


def auto_generate_mapping(ga_number: str, pdf_path: Path, num_lectures: int) -> Dict:
    """
    Generiert automatisch ein Mapping aus dem PDF-Inhaltsverzeichnis.
    Speichert es in lecture-page-mapping.json.
    
    Korrigiert automatisch Titelseiten: Wenn die erste TOC-Seite eine
    Titelseite ist (wenig Text), wird die erste echte Textseite verwendet.
    
    Rückgabe: Das Mapping für diese GA (leer wenn nichts gefunden)
    """
    entries = extract_toc_entries(pdf_path, num_lectures)
    
    if not entries:
        print(f"  ⚠️  Kein Inhaltsverzeichnis gefunden")
        return {}
    
    # Wenn wir deutlich weniger Einträge als Vorträge haben, könnte es ein Problem sein
    if len(entries) < num_lectures * 0.5:
        print(f"  ⚠️  Nur {len(entries)} TOC-Einträge für {num_lectures} Vorträge gefunden")
        # Trotzdem verwenden, wenn wir überhaupt was haben
    
    ga_upper = ga_number.upper()
    ga_mapping = {}
    
    for i, entry in enumerate(entries, 1):
        lec_id = f"{ga_upper}/{i}"
        page = entry['page']
        
        # Für den ersten Eintrag: Prüfe ob es eine Titelseite ist
        if i == 1:
            actual_page = find_first_text_page(pdf_path, page)
            if actual_page != page:
                print(f"  ℹ️  Titelseite erkannt: S.{page} → erste Textseite S.{actual_page}")
                page = actual_page
        
        ga_mapping[lec_id] = page
    
    # Lade bestehendes Mapping und füge hinzu
    mapping = load_page_mapping()
    mapping[ga_upper] = ga_mapping
    save_page_mapping(mapping)
    
    print(f"  ✓ Mapping aus TOC generiert: {len(ga_mapping)} Einträge")
    for i, entry in enumerate(entries[:5], 1):
        page = ga_mapping.get(f"{ga_upper}/{i}", entry['page'])
        print(f"      {ga_upper}/{i}: S.{page} - {entry['title'][:40]}")
    if len(entries) > 5:
        print(f"      ... und {len(entries) - 5} weitere")
    
    return ga_mapping


def find_text_position(needle: str, haystack: str, start_offset: int = 0) -> int:
    """
    Findet die Position von needle in haystack.
    Verwendet normalisierte Suche mit Position-Mapping.
    """
    needle_norm = normalize_for_comparison(needle)
    haystack_norm = normalize_for_comparison(haystack)
    
    if not needle_norm:
        return -1
    
    # Suche in normalisiertem Text
    pos_norm = haystack_norm.find(needle_norm, start_offset)
    if pos_norm == -1:
        return -1
    
    # Mappe zurück zur Original-Position
    # Zähle wie viele Original-Zeichen wir brauchen für pos_norm normalisierte Zeichen
    orig_pos = 0
    norm_count = 0
    
    for i, char in enumerate(haystack):
        if norm_count >= pos_norm:
            return i
        
        # Prüfe ob dieses Zeichen in der Normalisierung erhalten bleibt
        char_norm = normalize_for_comparison(char)
        if char_norm:
            norm_count += len(char_norm)
    
    return orig_pos


def remove_existing_markers(text: str) -> str:
    """Entfernt bestehende |XX| Marker aus dem Text."""
    return re.sub(r"\|(\d+)\|", "", text)


def adjust_position_after_punctuation(text: str, pos: int) -> int:
    """
    Verschiebt die Position nach einem Satzzeichen, falls eines direkt davor steht.
    
    Beispiel: "durchgemacht haben|." → "durchgemacht haben.|"
    
    HINWEIS: Marker KÖNNEN mitten in Wörtern stehen, wenn im PDF dort
    Silbentrennung am Zeilenende mit Seitenwechsel ist!
    """
    punctuation = ".,:;!?»\"')"
    
    # Prüfe ob das Zeichen an pos ein Satzzeichen ist
    while pos < len(text) and text[pos] in punctuation:
        pos += 1
    
    return pos


def insert_marker_at_position(text: str, pos: int, page_num: int) -> str:
    """Fügt einen Marker an der angegebenen Position ein."""
    # Position nach Satzzeichen verschieben
    pos = adjust_position_after_punctuation(text, pos)
    marker = f"|{page_num}|"
    return text[:pos] + marker + text[pos:]


def find_pagebreak_position(
    prev_end: str,
    this_start: str,
    lecture_text: str,
    min_position: int = 0,
    this_start_words: str = ""
) -> Optional[int]:
    """
    Findet die exakte Position eines Seitenumbruchs im Vortrag.
    
    Strategien:
    1. Prüfe auf Silbentrennung (prev_end endet mit Bindestrich)
       -> Finde kombiniertes Wort und setze Marker nach dem Fragment
    2. Suche mit this_start_words (erste Wörter vom Seitenanfang)
    3. Suche mit this_start (erste 300 Zeichen vom Seitenanfang)
    4. Suche ab erstem vollständigen Wort (überspringe Silbentrennungs-Fragment)
    
    this_start_words: Erste Wörter vom Seitenanfang (für neue GA-Ausgabe)
    """
    lecture_clean = remove_existing_markers(lecture_text)
    lecture_norm = normalize_for_comparison(lecture_clean)
    
    # Approximiere min_position im normalisierten Text
    norm_min = int(min_position * 0.6) if min_position > 0 else 0
    
    # Für erste Seite: Position 0
    if not prev_end:
        return 0
    
    # STRATEGIE 0: Prüfe auf Silbentrennung
    # Wenn prev_end mit Bindestrich endet, ist das Wort über den Seitenumbruch getrennt
    prev_clean = prev_end.replace("\n", " ").strip()
    
    # Erkenne Silbentrennung: endet mit Buchstabe-Bindestrich oder nur Bindestrich
    hyphen_match = re.search(r'(\w+)-\s*$', prev_clean)
    if hyphen_match:
        # Extrahiere das Fragment vor dem Bindestrich (z.B. "un" aus "un-")
        fragment = hyphen_match.group(1).lower()
        
        # Extrahiere das erste Wort vom Seitenanfang (z.B. "geeignet")
        this_clean_temp = this_start.replace("-\n", "").replace("\n", " ").strip()
        first_word_match = re.match(r'^(\w+)', this_clean_temp)
        if first_word_match:
            continuation = first_word_match.group(1).lower()
            
            # Kombiniere: "un" + "geeignet" = "ungeeignet"
            combined_word = fragment + continuation
            
            # Suche das kombinierte Wort direkt im Original-Text (case-insensitive)
            lecture_lower = lecture_clean.lower()
            pos = lecture_lower.find(combined_word, min_position)
            if pos != -1:
                # Position ist am Anfang des kombinierten Wortes
                # Wir wollen den Marker NACH dem Fragment setzen
                final_pos = pos + len(fragment)
                if final_pos >= min_position:
                    return final_pos
    
    # Normalisiere für weitere Strategien
    this_clean = this_start.replace("-\n", "").replace("\n", " ")
    this_norm = normalize_for_comparison(this_clean)
    
    # NEUE STRATEGIE: Für neue GA-Ausgabe primär mit this_start_words suchen (oben links)
    # Strategie 1: Suche mit ersten Wörtern vom Seitenanfang (PRIORITÄT für neue GA-Ausgabe)
    if this_start_words:
        words_clean = this_start_words.replace("-\n", "").replace("\n", " ")
        words_norm = normalize_for_comparison(words_clean)
        
        # Reduziertes Minimum: Mindestens 15 Zeichen für bessere Erkennung
        if len(words_norm) >= 15:
            # Versuche verschiedene Längen der ersten Wörter
            # Erweitert um kürzere Längen für bessere Trefferquote
            for length in [120, 100, 80, 60, 50, 40, 30, 25, 20, 15]:
                if len(words_norm) < length:
                    continue
                snippet = words_norm[:length]
                
                # Finde ALLE Vorkommen, nicht nur das erste
                candidates = []
                pos = norm_min
                while True:
                    pos = lecture_norm.find(snippet, pos)
                    if pos == -1:
                        break
                    orig_pos = map_norm_to_original(lecture_clean, pos)
                    if orig_pos >= min_position:
                        # NUR oben links suchen - keine Bewertung mit prev_end mehr!
                        # Bevorzuge Positionen die näher zu min_position sind (Monotonie)
                        distance = abs(orig_pos - min_position)
                        candidates.append((orig_pos, distance, pos))
                    pos += 1
                
                if candidates:
                    # Sortiere nach Nähe zu min_position (näher = besser)
                    candidates.sort(key=lambda x: x[1])  # x[1] ist distance
                    return candidates[0][0]
        
        # Fallback: Auch wenn weniger als 15 Zeichen, versuche es trotzdem mit kürzeren Snippets
        elif len(words_norm) >= 10:
            for length in [len(words_norm), len(words_norm) - 2, len(words_norm) - 5]:
                if length < 10:
                    break
                snippet = words_norm[:length]
                pos = lecture_norm.find(snippet, norm_min)
                if pos != -1:
                    orig_pos = map_norm_to_original(lecture_clean, pos)
                    if orig_pos >= min_position:
                        return orig_pos
    
    # Strategie 2: Suche nur nach this_start (oben links, ohne prev_end)
    for length in [60, 50, 40, 30, 20]:
        if len(this_norm) < length:
            continue
        
        snippet = this_norm[:length]
        
        # Finde ALLE Vorkommen
        candidates = []
        pos = norm_min
        while True:
            pos = lecture_norm.find(snippet, pos)
            if pos == -1:
                break
            orig_pos = map_norm_to_original(lecture_clean, pos)
            if orig_pos >= min_position:
                # NUR oben links suchen - keine Bewertung mit prev_end mehr!
                distance = abs(orig_pos - min_position)
                candidates.append((orig_pos, distance, pos))
            pos += 1
        
        if candidates:
            # Sortiere nach Nähe zu min_position (näher = besser)
            candidates.sort(key=lambda x: x[1])  # x[1] ist distance
            return candidates[0][0]
    
    # Strategie 3: Ab erstem vollständigen Wort (überspringe Silbentrennungs-Fragment)
    words = this_clean.split()
    if len(words) > 1:
        # Überspringe erstes Wort (könnte Fragment sein)
        rest = " ".join(words[1:])
        rest_norm = normalize_for_comparison(rest)
        
        # Finde ALLE Vorkommen
        candidates = []
        pos = norm_min
        while True:
            pos = lecture_norm.find(rest_norm[:min(50, len(rest_norm))], pos)
            if pos == -1:
                break
            orig_pos = map_norm_to_original(lecture_clean, pos)
            if orig_pos >= min_position:
                # NUR oben links suchen - keine Bewertung mit prev_end mehr!
                distance = abs(orig_pos - min_position)
                candidates.append((orig_pos, distance, pos))
            pos += 1
        
        if candidates:
            # Sortiere nach Nähe zu min_position (näher = besser)
            candidates.sort(key=lambda x: x[1])  # x[1] ist distance
            return candidates[0][0]
    
    # KEIN Fallback mit prev_end mehr - nur oben links suchen!
    # Wenn nichts gefunden wurde, gibt None zurück (keine Fehlermeldung)
    return None


def map_norm_to_original(text: str, norm_pos: int) -> int:
    """Mappt eine Position im normalisierten Text zurück zum Original."""
    if norm_pos <= 0:
        return 0
    if not text:
        return 0
    
    # Schnelle Approximation
    text_norm = normalize_for_comparison(text)
    if not text_norm:
        return 0
    
    ratio = len(text) / len(text_norm)
    estimated = int(norm_pos * ratio)
    
    return max(0, min(estimated, len(text)))


def process_lecture(
    lecture: Dict,
    pdf_pages: List[Tuple[int, int, str, str, str]],  # (pdf_idx, page_num, prev_end, this_start, this_start_words)
    start_page: int = None,
    end_page: Optional[int] = None,
    start_pdf_index: int = 0
) -> Tuple[int, int]:
    """
    Fügt Seitenmarker in einen Vortrag ein.
    
    OHNE MAPPING: Durchsucht ALLE PDF-Seiten und findet automatisch,
    welche Seiten zu diesem Vortrag gehören (durch Text-Matching).
    
    start_page/end_page sind optional - wenn nicht angegeben, werden
    alle PDF-Seiten durchsucht und nur die Matches eingefügt.
    """
    paragraphs = lecture.get("paragraphs", [])
    if not paragraphs:
        return 0, start_pdf_index
    
    # Schritt 1: Entferne ALLE existierenden Marker aus allen Absätzen
    for para in paragraphs:
        content = para.get("content") or para.get("text") or ""
        content = remove_existing_markers(content)
        if "content" in para:
            para["content"] = content
        else:
            para["text"] = content
    
    # Schritt 2: Baue Gesamt-Text (jetzt ohne Marker)
    full_text = ""
    para_boundaries = []  # (start, end, para_index)
    
    for i, para in enumerate(paragraphs):
        content = para.get("content") or para.get("text") or ""
        start = len(full_text)
        full_text += content + "\n"
        end = len(full_text)
        para_boundaries.append((start, end, i))
    
    # Schritt 3: Sammle Marker-Positionen durch Text-Matching
    markers = []  # (position, page_num)
    search_start = 0
    last_pdf_index = start_pdf_index
    first_page_found = None
    
    # Finde erste Inhalts-Position (überspringe kurze Titel-Absätze)
    first_content_pos = 0
    for start, end, idx in para_boundaries:
        content = paragraphs[idx].get("content") or paragraphs[idx].get("text") or ""
        # Titel sind meist kurz (<100 Zeichen) und ohne Satzzeichen
        if len(content) > 100 or any(p in content for p in '.!?'):
            first_content_pos = start
            break
        first_content_pos = end  # Nach dem Titel
    
    # Wenn start_page angegeben, füge Start-Marker am ANFANG des ersten Absatzes ein
    # (nicht erst nach Titel-Absätzen)
    if start_page is not None:
        markers.append((0, start_page))  # Position 0 = Anfang des ersten Absatzes
        first_page_found = start_page
        search_start = 1
    
    # Durchsuche alle PDF-Seiten ab start_pdf_index
    # WICHTIG: Sortiere nach Seitenzahl, damit frühere Seiten nicht übersprungen werden
    pages_to_process = pdf_pages[start_pdf_index:]
    pages_to_process = sorted(pages_to_process, key=lambda x: x[1])  # Sortiere nach Seitenzahl (Index 1)
    
    matched_pages = 0
    expected_pages = (end_page - start_page + 1) if (start_page and end_page) else 0
    
    for rel_idx, page_tuple in enumerate(pages_to_process):
        # Unterstütze sowohl alte (4-Tupel) als auch neue (5-Tupel) Format
        if len(page_tuple) == 5:
            pdf_idx, page_num, prev_end, this_start, this_start_words = page_tuple
        else:
            pdf_idx, page_num, prev_end, this_start = page_tuple
            this_start_words = ""
        # Wenn start_page/end_page gegeben, filtere
        if start_page is not None and page_num <= start_page:
            continue  # Start-Seite wurde bereits eingefügt
        if end_page is not None and page_num > end_page:
            break
        
        # Finde Position für diese Seite durch Text-Matching
        pos = find_pagebreak_position(prev_end, this_start, full_text, search_start, this_start_words)
        
        if pos is not None and pos > search_start:
            # Ohne start_page: Erste gefundene Seite = Marker am Anfang
            if first_page_found is None:
                first_page_found = page_num
                markers.append((first_content_pos, page_num))
                search_start = first_content_pos + 1
            
            # Weitere Seiten: Marker an der Match-Position
            # WICHTIG: Prüfe ob Position nach search_start liegt (Monotonie),
            # nicht ob Seitenzahl größer ist (könnte falsch sein wenn Seiten nicht in Reihenfolge gefunden werden)
            if pos >= search_start:
                # Prüfe ob diese Seitenzahl bereits eingefügt wurde (verhindere Duplikate)
                if not any(p == page_num for _, p in markers):
                    markers.append((pos, page_num))
                    search_start = pos + 1
                    matched_pages += 1
            
            last_pdf_index = start_pdf_index + rel_idx
    
    # FALLBACK: Wenn Text-Matching für weniger als 50% der Seiten funktioniert hat,
    # füge Marker basierend auf geschätzter Position ein
    if start_page and end_page and expected_pages > 2:
        if matched_pages < expected_pages * 0.3:  # Weniger als 30% gematcht
            # Berechne durchschnittliche Zeichen pro Seite
            text_length = len(full_text)
            chars_per_page = text_length / expected_pages if expected_pages > 0 else 2000
            
            # Füge geschätzte Marker ein
            for page_num in range(start_page + 1, end_page + 1):
                # Prüfe ob diese Seite bereits einen Marker hat
                if any(p == page_num for _, p in markers):
                    continue
                
                # Geschätzte Position
                pages_from_start = page_num - start_page
                estimated_pos = int(pages_from_start * chars_per_page)
                
                # Nur einfügen wenn Position im gültigen Bereich
                if 0 < estimated_pos < text_length:
                    markers.append((estimated_pos, page_num))
    
    if not markers:
        return 0, start_pdf_index
    
    # Schritt 4: Finale Validierung - streng aufsteigend nach Position UND Seitenzahl
    valid_markers = []
    last_pos = -1
    last_page = -1
    
    for pos, page_num in sorted(markers, key=lambda x: x[0]):
        if pos > last_pos and page_num > last_page:
            valid_markers.append((pos, page_num))
            last_pos = pos
            last_page = page_num
    
    # Schritt 5: Füge Marker ein (von hinten nach vorne, um Positionen nicht zu verschieben)
    valid_markers.sort(key=lambda x: x[0], reverse=True)
    
    inserted = 0
    for pos, page_num in valid_markers:
        for para_start, para_end, para_idx in para_boundaries:
            if para_start <= pos < para_end:
                para = paragraphs[para_idx]
                content = para.get("content") or para.get("text") or ""
                
                rel_pos = pos - para_start
                rel_pos = max(0, min(rel_pos, len(content)))
                
                # Position nach Satzzeichen verschieben
                rel_pos = adjust_position_after_punctuation(content, rel_pos)
                
                marker = f"|{page_num}|"
                new_content = content[:rel_pos] + marker + content[rel_pos:]
                
                if "content" in para:
                    para["content"] = new_content
                else:
                    para["text"] = new_content
                
                inserted += 1
                break
    
    return inserted, last_pdf_index + 1


def archive_old_pagebreaks(ga_number: str) -> None:
    """
    Verschiebt alte pagebreaks/*.json Dateien ins Archiv.
    Wird aufgerufen nachdem Marker erfolgreich eingefügt wurden.
    """
    import shutil
    import glob
    
    pagebreaks_dir = Path(__file__).parent.parent / "pagebreaks"
    archive_dir = pagebreaks_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return
    
    # Finde alle Dateien die zu dieser GA gehören
    # Patterns: GA072.json, GA072.json.old*, GA072-with-markers.json, GA072-report.json
    patterns_to_archive = [
        f"{ga_norm}.json",
        f"{ga_norm}.json.old*",
        f"{ga_norm}-with-markers.json",
    ]
    
    archived = []
    for pattern in patterns_to_archive:
        for old_file in pagebreaks_dir.glob(pattern):
            if old_file.is_file():
                dest = archive_dir / old_file.name
                # Falls bereits im Archiv, mit Timestamp versehen
                if dest.exists():
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest = archive_dir / f"{old_file.stem}_{timestamp}{old_file.suffix}"
                shutil.move(str(old_file), str(dest))
                archived.append(old_file.name)
    
    if archived:
        for name in archived:
            print(f"  Archiviert: {name}")


def process_ga(ga_number: str, update_source: bool = False) -> Dict:
    """
    Verarbeitet eine GA-Nummer.
    Rückgabe: Statistik-Dict
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return {"error": f"Ungültige GA-Nummer: {ga_number}"}
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_norm}")
    print(f"{'='*60}")
    
    # PDF finden
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print(f"  FEHLER: Keine PDF gefunden")
        return {"error": "Keine PDF"}
    
    print(f"  PDF: {pdf_path.name}")
    
    # PDF-Seiten extrahieren
    print(f"  Extrahiere PDF-Seiten...")
    pdf_pages = extract_pdf_pages(pdf_path)
    print(f"  {len(pdf_pages)} Seiten mit Seitenzahlen")
    
    if not pdf_pages:
        return {"error": "Keine Seiten mit Seitenzahlen"}
    
    # Vorträge laden
    files_map, lectures = load_lectures_for_ga(ga_norm)
    is_book = False
    book_source_file = None
    
    all_book_files = []  # Alle Dateien die dieses Buch enthalten
    
    if not lectures:
        # Versuche Bücher
        book_source_file, book, all_book_files = load_books_for_ga(ga_norm)
        if book:
            # Teile Buch in Kapitel auf (jedes Kapitel wie ein Vortrag)
            chapters = split_book_into_chapters(book, ga_norm)
            lectures = chapters
            is_book = True
            print(f"  Buch geladen: {book.get('title', '')[:50]}")
            if len(chapters) > 1:
                print(f"  → In {len(chapters)} Kapitel aufgeteilt")
            if len(all_book_files) > 1:
                print(f"  → In {len(all_book_files)} Dateien vorhanden")
        else:
            return {"error": "Keine Vorträge/Bücher gefunden"}
    else:
        print(f"  {len(lectures)} Vorträge geladen")
        if len(files_map) > 1:
            print(f"  (verteilt auf {len(files_map)} Dateien: {', '.join(f.name for f in files_map.keys())})")
    
    # Page-Mapping laden
    mapping = load_page_mapping()
    ga_mapping = mapping.get(ga_norm, {})
    
    # Automatisch Mapping generieren für "neue" PDFs ohne Copyright-Footer
    if not ga_mapping and not is_book and len(lectures) > 1:
        # Prüfe ob PDF altes oder neues Format hat
        if not is_old_pdf_format(pdf_path):
            print(f"  Neues PDF-Format erkannt (ohne Copyright-Footer)")
            print(f"  Versuche Mapping aus Inhaltsverzeichnis zu extrahieren...")
            ga_mapping = auto_generate_mapping(ga_norm, pdf_path, len(lectures))
        else:
            print(f"  Altes PDF-Format (Copyright-Footer)")
    
    # Verarbeite jeden Vortrag
    total_inserted = 0
    current_pdf_index = 0  # Für PDFs mit doppelten Seitenzahlen
    
    # Für Bücher: Prüfe ob Mapping vollständig ist
    # Wenn nicht, behandle das ganze Buch als eine Einheit
    if is_book and len(lectures) > 1:
        # Prüfe wie viele Kapitel ein Mapping haben
        mapped_count = sum(1 for i, lec in enumerate(lectures) 
                          if ga_mapping.get(lec.get("ID") or f"{ga_norm}/{i+1}"))
        
        if mapped_count < len(lectures) * 0.5:  # Weniger als 50% gemappt
            # Behandle Buch als eine Einheit, keine Kapitelaufteilung
            print(f"  ⚠️  Nur {mapped_count}/{len(lectures)} Kapitel haben Mapping")
            print(f"  → Verarbeite Buch als Ganzes (fortlaufende Seitenzahlen)")
            
            # Erste Inhaltsseite ermitteln - NUR aus Mapping oder page-break-markers.json
            first_page = ga_mapping.get(f"{ga_norm}/1")
            if not first_page:
                # Versuche aus page-break-markers.json (isFirstPage Marker)
                first_content = load_first_content_page(ga_norm)
                if first_content:
                    first_page = first_content
                else:
                    # KEIN Fallback auf Seite 7! Wir brauchen die echte Startseite.
                    print(f"  ⚠️  FEHLER: Keine Startseite gefunden für {ga_norm}!")
                    print(f"      Bitte in lecture-page-mapping.json eintragen: \"{ga_norm}/1\": <startseite>")
                    return {"error": f"Keine Startseite für {ga_norm} - bitte Mapping erstellen"}
            
            # Alle Absätze aus allen Kapiteln zusammenführen
            all_paragraphs = []
            for chapter in lectures:
                all_paragraphs.extend(chapter.get("paragraphs", []))
            
            # Ein "Gesamtbuch-Vortrag" erstellen
            unified_book = {
                "ID": f"{ga_norm}/1",
                "gaNumber": ga_norm,
                "title": book.get("title", ""),
                "lectureNumber": 1,
                "paragraphs": all_paragraphs,
            }
            
            end_page = pdf_pages[-1][1] if pdf_pages else None
            inserted, _ = process_lecture(unified_book, pdf_pages, first_page, end_page, 0)
            total_inserted = inserted
            
            # Schreibe Absätze zurück in die Kapitel
            para_idx = 0
            for chapter in lectures:
                chapter_len = len(chapter.get("paragraphs", []))
                chapter["paragraphs"] = unified_book["paragraphs"][para_idx:para_idx + chapter_len]
                para_idx += chapter_len
            
            print(f"    {ga_norm}: {inserted} Marker (S.{first_page}-{end_page})")
        else:
            # Vollständiges Mapping vorhanden - kapitelweise verarbeiten
            for i, lecture in enumerate(lectures):
                lec_id = lecture.get("ID") or f"{ga_norm}/{i+1}"
                lec_num = int(lecture.get("lectureNumber") or i + 1)
                
                start_page = ga_mapping.get(lec_id)
                if not start_page:
                    # Fallback: Vorheriges Kapitel + Schätzung
                    if i > 0:
                        prev_id = lectures[i-1].get("ID") or f"{ga_norm}/{i}"
                        prev_start = ga_mapping.get(prev_id)
                        if prev_start:
                            # Schätze basierend auf Absatzanzahl
                            prev_paras = len(lectures[i-1].get("paragraphs", []))
                            start_page = prev_start + max(1, prev_paras // 10)
                    
                    if not start_page:
                        first_content = load_first_content_page(ga_norm)
                        if first_content:
                            start_page = first_content
                        elif pdf_pages:
                            start_page = pdf_pages[0][1]
                
                end_page = None
                if i + 1 < len(lectures):
                    next_id = lectures[i + 1].get("ID") or f"{ga_norm}/{i+2}"
                    end_page = ga_mapping.get(next_id)
                    if end_page:
                        end_page -= 1
                
                if not end_page and pdf_pages:
                    end_page = pdf_pages[-1][1]
                
                inserted, current_pdf_index = process_lecture(
                    lecture, pdf_pages, start_page or 1, end_page, current_pdf_index
                )
                total_inserted += inserted
                
                title = (lecture.get("title") or "")[:40]
                print(f"    {lec_id}: {inserted} Marker (S.{start_page}-{end_page}) - {title}")
    else:
        # Vorträge (nicht Bücher)
        # 
        # Strategie:
        # 1. Wenn lecture-page-mapping vorhanden: Jeden Vortrag einzeln mit seinem Seitenbereich verarbeiten
        # 2. Ohne Mapping: Alle Vorträge als Gesamttext verarbeiten
        
        has_mapping = bool(ga_mapping)
        
        if has_mapping:
            # MIT MAPPING: Jeden Vortrag einzeln verarbeiten
            print(f"  Verarbeite {len(lectures)} Vorträge mit Mapping...")
            
            for i, lecture in enumerate(lectures):
                lec_id = lecture.get("ID") or f"{ga_norm}/{i+1}"
                
                # Start-Seite aus Mapping
                start_page = ga_mapping.get(lec_id)
                if not start_page:
                    # Versuche mit normalisierter ID
                    for key, val in ga_mapping.items():
                        if key.lower() == lec_id.lower():
                            start_page = val
                            break
                
                if not start_page:
                    title = (lecture.get("title") or "")[:40]
                    print(f"    {lec_id}: kein Mapping - {title}")
                    continue
                
                # End-Seite: nächster Vortrag oder letzte PDF-Seite
                end_page = None
                if i + 1 < len(lectures):
                    next_id = lectures[i + 1].get("ID") or f"{ga_norm}/{i+2}"
                    end_page = ga_mapping.get(next_id)
                    if not end_page:
                        for key, val in ga_mapping.items():
                            if key.lower() == next_id.lower():
                                end_page = val
                                break
                    if end_page:
                        end_page -= 1
                
                if not end_page and pdf_pages:
                    end_page = pdf_pages[-1][1]
                
                inserted, current_pdf_index = process_lecture(
                    lecture, pdf_pages, start_page, end_page, current_pdf_index
                )
                total_inserted += inserted
                
                title = (lecture.get("title") or "")[:40]
                print(f"    {lec_id}: {inserted} Marker (S.{start_page}-{end_page}) - {title}")
        else:
            # OHNE MAPPING: Alle Vorträge als Gesamttext verarbeiten
            print(f"  Verarbeite {len(lectures)} Vorträge als Gesamttext (kein Mapping)...")
            
            # Alle Vorträge zu einem "Gesamt-Vortrag" zusammenfügen
            all_paragraphs = []
            lecture_boundaries = []
            
            for lecture in lectures:
                start_idx = len(all_paragraphs)
                paras = lecture.get("paragraphs", [])
                all_paragraphs.extend(paras)
                end_idx = len(all_paragraphs)
                lecture_boundaries.append((start_idx, end_idx, lecture))
            
            unified_lecture = {
                "ID": f"{ga_norm}/unified",
                "paragraphs": all_paragraphs
            }
            
            total_inserted, _ = process_lecture(
                unified_lecture, pdf_pages,
                start_page=None,
                end_page=None,
                start_pdf_index=0
            )
            
            # Absätze zurück in die Original-Vorträge kopieren
            for start_idx, end_idx, lecture in lecture_boundaries:
                lecture["paragraphs"] = all_paragraphs[start_idx:end_idx]
                
                markers_in_lecture = 0
                for para in lecture["paragraphs"]:
                    content = para.get("content") or para.get("text") or ""
                    markers_in_lecture += len(re.findall(r'\|\d+\|', content))
                
                lec_id = lecture.get("ID") or "?"
                title = (lecture.get("title") or "")[:40]
                if markers_in_lecture > 0:
                    print(f"    {lec_id}: {markers_in_lecture} Marker - {title}")
                else:
                    print(f"    {lec_id}: keine Marker - {title}")
    
    print(f"\n  Gesamt: {total_inserted} Marker eingefügt")
    
    # Speichern
    if update_source and (files_map or book_source_file):
        if is_book and book_source_file:
            # Buch speichern - Kapitel-Absätze zurück zusammenführen
            # Sammle alle Absätze aus den Kapiteln
            all_paragraphs = []
            for chapter in lectures:
                all_paragraphs.extend(chapter.get("paragraphs", []))
            
            # Speichere in ALLE Dateien, die dieses Buch enthalten
            saved_files = []
            files_to_update = all_book_files if all_book_files else [book_source_file]
            
            for book_file in files_to_update:
                try:
                    with open(book_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    for orig_book in data.get("books", []):
                        if (orig_book.get("gaNumber") or "").upper() == ga_norm:
                            orig_book["paragraphs"] = all_paragraphs
                            break
                    
                    with open(book_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    saved_files.append(book_file.name)
                except Exception as e:
                    print(f"    ⚠️  Fehler beim Speichern in {book_file.name}: {e}")
            
            print(f"  Gespeichert in: {', '.join(saved_files)}")
        else:
            # Alle betroffenen Dateien aktualisieren
            saved_files = []
            for source_file in files_map.keys():
                with open(source_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Aktualisiere Vorträge im Original
                for orig_lec in data.get("lectures", []):
                    if (orig_lec.get("gaNumber") or "").upper() == ga_norm:
                        # Finde entsprechenden verarbeiteten Vortrag
                        for proc_lec in lectures:
                            if orig_lec.get("ID") == proc_lec.get("ID"):
                                orig_lec["paragraphs"] = proc_lec["paragraphs"]
                                break
                
                with open(source_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                saved_files.append(source_file.name)
            
            print(f"  Gespeichert in: {', '.join(saved_files)}")
    else:
        # In pagebreaks/ speichern
        PAGEBREAKS_DIR.mkdir(exist_ok=True)
        out_file = PAGEBREAKS_DIR / f"{ga_norm}.json"
        
        out_data = {"lectures": lectures}
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
        
        print(f"  Gespeichert in: {out_file.name}")
    
    # Archiviere alte pagebreaks/*.json Dateien (nicht mehr benötigt)
    if total_inserted > 0:
        archive_old_pagebreaks(ga_norm)
    
    return {
        "ga": ga_norm,
        "lectures": len(lectures),
        "markers_inserted": total_inserted,
        "pages": len(pdf_pages)
    }


def main():
    parser = argparse.ArgumentParser(description="Fügt Seitenmarker aus PDFs in Vorträge ein")
    parser.add_argument("ga", nargs="+", help="GA-Nummer(n) oder Bereich (z.B. 61 67)")
    parser.add_argument("--update-source", action="store_true", 
                        help="Originaldatei aktualisieren statt pagebreaks/ Kopie")
    
    args = parser.parse_args()
    
    # Bestimme GA-Nummern
    ga_numbers = []
    
    if len(args.ga) == 2 and args.ga[0].isdigit() and args.ga[1].isdigit():
        # Bereich
        start = int(args.ga[0])
        end = int(args.ga[1])
        ga_numbers = [f"GA{i:03d}" for i in range(start, end + 1)]
    else:
        # Einzelne GAs
        for ga in args.ga:
            ga_norm = normalize_ga(ga)
            if ga_norm:
                ga_numbers.append(ga_norm)
    
    if not ga_numbers:
        print("Keine gültigen GA-Nummern angegeben")
        sys.exit(1)
    
    # Verarbeite
    results = []
    for ga in ga_numbers:
        result = process_ga(ga, update_source=args.update_source)
        results.append(result)
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    success = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    
    print(f"  Erfolgreich: {len(success)}")
    print(f"  Fehler: {len(errors)}")
    
    if errors:
        print("\n  Fehler:")
        for r in errors:
            print(f"    - {r.get('ga', '?')}: {r.get('error')}")
    
    total_markers = sum(r.get("markers_inserted", 0) for r in success)
    print(f"\n  Gesamt Marker: {total_markers}")


if __name__ == "__main__":
    main()

