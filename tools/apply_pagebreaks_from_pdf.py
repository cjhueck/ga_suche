#!/usr/bin/env python3
"""
Apply Pagebreaks from PDF - Direktes Einfügen von Seitenumbrüchen aus PDFs

Verwendet die PDFs mit Seitenzahlen (Format: "Steiner, Rudolf GA XXX, YYYY - Titel")
aus Steiner_GA_pdf/ um |XX| Marker in die Vorträge einzufügen.

Verwendung:
  python tools/apply_pagebreaks_from_pdf.py GA061
  python tools/apply_pagebreaks_from_pdf.py GA061 --update-source
  python tools/apply_pagebreaks_from_pdf.py 61 67  # Bereich
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

# Ligaturen für Normalisierung
LIGATURES = {
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    "ﬅ": "st", "ﬆ": "st", "Ꜳ": "AA", "ꜳ": "aa", "Æ": "AE", "æ": "ae",
    "Œ": "OE", "œ": "oe",
}


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
    Sucht nach "Seite: XX" oder "Seite:XX" Muster.
    """
    for line in reversed(lines[-10:]):
        # Muster: "Seite: XX" oder "Seite:XX"
        match = re.search(r"Seite:\s*([\d\s]+)", line, re.IGNORECASE)
        if match:
            page_str = match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                return int(page_str)
    
    # Fallback: Einzelne Zahl am Ende
    for line in reversed(lines[-7:]):
        stripped = line.strip()
        if stripped and re.match(r"^[\d\s]+$", stripped):
            page_str = stripped.replace(" ", "")
            if page_str and 1 <= len(page_str) <= 4:
                try:
                    page_num = int(page_str)
                    if 1 <= page_num <= 999:
                        return page_num
                except ValueError:
                    continue
    
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


def extract_pdf_pages(pdf_path: Path) -> List[Tuple[int, int, str, str]]:
    """
    Extrahiert alle Seiten basierend auf der Copyright-Zeile.
    
    Format im PDF:
        [Anfang Seite N] ... Text ... [Ende Seite N]
        Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 7 2
        Seite: N
    
    Für Marker |N| brauchen wir:
        - prev_end: Ende von Seite N-1
        - this_start: Anfang von Seite N
    
    Rückgabe: Liste von (PDF-Index, Seitenzahl N, Ende-Seite-N-1, Anfang-Seite-N)
    """
    doc = fitz.open(pdf_path)
    
    # Sammle alle Seiten mit Copyright-Footer
    page_data = []  # (pdf_index, page_num, text_start, text_end)
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        if not text.strip():
            continue
        
        # Suche nach Copyright-Zeile (auch mit OCR-Fehlern wie "Steinet" statt "Steiner")
        copyright_match = re.search(
            r'Copyright\s+Rudolf\s+Stein\w*.*?Seite:\s*([\d\s]+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not copyright_match:
            continue
        
        # Extrahiere Seitenzahl (mit Leerzeichen wie "2 2" -> 22)
        page_str = copyright_match.group(1).replace(" ", "").strip()
        if not page_str.isdigit():
            continue
        page_num = int(page_str)
        
        # Text VOR der Copyright-Zeile
        body_text = text[:copyright_match.start()].strip()
        
        # Anfang dieser Seite (erste 300 Zeichen)
        text_start = body_text[:300] if len(body_text) > 300 else body_text
        # Ende dieser Seite (letzte 300 Zeichen)
        text_end = body_text[-300:] if len(body_text) > 300 else body_text
        
        page_data.append((i, page_num, text_start, text_end))
    
    doc.close()
    
    # Korrigiere nicht-fortlaufende Seitenzahlen (OCR-Fehler)
    # z.B. wenn Seite 383 zweimal vorkommt und 388 fehlt
    page_data = fix_page_numbers(page_data)
    
    # Für jeden Marker |N|: prev_end (Ende S.N-1) + this_start (Anfang S.N)
    pages = []
    
    for idx, (pdf_idx, page_num, text_start, text_end) in enumerate(page_data):
        # prev_end = Ende der VORHERIGEN Seite (N-1)
        if idx > 0:
            prev_end = page_data[idx - 1][3]  # text_end der vorherigen Seite
        else:
            prev_end = ""
        
        # this_start = Anfang DIESER Seite (N)
        this_start = text_start
        
        # Marker |page_num| kommt zwischen prev_end und this_start
        pages.append((pdf_idx, page_num, prev_end, this_start))
    
    return pages


def fix_page_numbers(page_data: List[Tuple[int, int, str, str]]) -> List[Tuple[int, int, str, str]]:
    """
    Korrigiert nicht-fortlaufende Seitenzahlen.
    
    Wenn eine Seitenzahl nicht zur Sequenz passt (z.B. 383 statt 388),
    wird sie basierend auf der erwarteten Fortlaufung korrigiert.
    """
    if len(page_data) < 3:
        return page_data
    
    corrected = []
    
    for idx, (pdf_idx, page_num, text_start, text_end) in enumerate(page_data):
        expected_page = None
        
        if idx > 0:
            prev_page = corrected[-1][1]
            expected_page = prev_page + 1
            
            # Prüfe ob die aktuelle Seitenzahl zur Sequenz passt
            # Toleranz: max 2 Seiten Sprung (für fehlende Seiten)
            if abs(page_num - expected_page) > 2:
                # Seitenzahl passt nicht - korrigiere sie
                corrected.append((pdf_idx, expected_page, text_start, text_end))
                continue
        
        corrected.append((pdf_idx, page_num, text_start, text_end))
    
    return corrected


def load_lectures_for_ga(ga_number: str) -> Tuple[Optional[Path], List[Dict]]:
    """
    Lädt alle Vorträge/Aufsätze für eine GA-Nummer.
    Rückgabe: (Quell-Datei, Liste von Vorträgen)
    """
    ga_upper = ga_number.upper()
    source_file = None
    lectures = []
    
    # Suche in steiner-full-lectures
    for path in sorted(LECTURES_DIR.glob("steiner-full-lectures-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for lec in data.get("lectures", []):
                if (lec.get("gaNumber") or "").upper() == ga_upper:
                    if source_file is None:
                        source_file = path
                    lectures.append(lec)
        except Exception:
            continue
    
    # Sortiere nach lectureNumber
    lectures.sort(key=lambda x: int(x.get("lectureNumber") or 0))
    return source_file, lectures


def load_books_for_ga(ga_number: str) -> Tuple[Optional[Path], Optional[Dict]]:
    """
    Lädt ein Buch für eine GA-Nummer.
    Rückgabe: (Quell-Datei, Buch-Dict)
    """
    ga_upper = ga_number.upper()
    
    for path in sorted(BOOKS_DIR.glob("steiner-books-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for book in data.get("books", []):
                if (book.get("gaNumber") or "").upper() == ga_upper:
                    return path, book
        except Exception:
            continue
    
    return None, None


def load_page_mapping() -> Dict:
    """Lädt das Lecture-Page-Mapping."""
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


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


def insert_marker_at_position(text: str, pos: int, page_num: int) -> str:
    """Fügt einen Marker an der angegebenen Position ein."""
    marker = f"|{page_num}|"
    return text[:pos] + marker + text[pos:]


def find_pagebreak_position(
    prev_end: str,
    this_start: str,
    lecture_text: str,
    min_position: int = 0
) -> Optional[int]:
    """
    Findet die exakte Position eines Seitenumbruchs im Vortrag.
    
    Suche nach "Ende vorherige Seite" + "Anfang diese Seite" im JSON.
    Der Marker kommt genau dazwischen.
    """
    lecture_clean = remove_existing_markers(lecture_text)
    lecture_norm = normalize_for_comparison(lecture_clean)
    
    # Approximiere min_position im normalisierten Text
    norm_min = int(min_position * 0.6) if min_position > 0 else 0
    
    # Für erste Seite (kein prev_end): Position 0
    if not prev_end:
        return 0
    
    # Normalisiere und entferne Silbentrennungen
    prev_clean = prev_end.replace("-\n", "").replace("\n", " ")
    this_clean = this_start.replace("-\n", "").replace("\n", " ")
    
    prev_norm = normalize_for_comparison(prev_clean)
    this_norm = normalize_for_comparison(this_clean)
    
    # Strategie 1: Kombinierte Suche (prev_end + this_start)
    for prev_len in [50, 40, 30, 25, 20, 15]:
        for this_len in [50, 40, 30, 25, 20, 15]:
            if len(prev_norm) < prev_len or len(this_norm) < this_len:
                continue
            
            prev_snippet = prev_norm[-prev_len:]
            this_snippet = this_norm[:this_len]
            combined = prev_snippet + this_snippet
            
            pos = lecture_norm.find(combined, norm_min)
            if pos != -1:
                marker_norm_pos = pos + prev_len
                orig_pos = map_norm_to_original(lecture_clean, marker_norm_pos)
                if orig_pos >= min_position:
                    return orig_pos
    
    # Strategie 2: Suche nur nach this_start (für Fälle mit starker Abweichung am Ende)
    for length in [60, 50, 40, 30, 20]:
        if len(this_norm) < length:
            continue
        
        snippet = this_norm[:length]
        pos = lecture_norm.find(snippet, norm_min)
        if pos != -1:
            orig_pos = map_norm_to_original(lecture_clean, pos)
            if orig_pos >= min_position:
                return orig_pos
    
    # Strategie 3: Ab erstem vollständigen Wort (überspringe Silbentrennungs-Fragment)
    words = this_clean.split()
    if len(words) > 1:
        # Überspringe erstes Wort (könnte Fragment sein)
        rest = " ".join(words[1:])
        rest_norm = normalize_for_comparison(rest)
        for length in [50, 40, 30, 20]:
            if len(rest_norm) < length:
                continue
            pos = lecture_norm.find(rest_norm[:length], norm_min)
            if pos != -1:
                orig_pos = map_norm_to_original(lecture_clean, pos)
                if orig_pos >= min_position:
                    return orig_pos
    
    return None


def map_norm_to_original(text: str, norm_pos: int) -> int:
    """Mappt eine Position im normalisierten Text zurück zum Original."""
    norm_count = 0
    
    for i, char in enumerate(text):
        if norm_count >= norm_pos:
            return i
        
        char_norm = normalize_for_comparison(char)
        if char_norm:
            norm_count += len(char_norm)
    
    return len(text)


def process_lecture(
    lecture: Dict,
    pdf_pages: List[Tuple[int, int, str, str]],
    start_page: int,
    end_page: Optional[int] = None,
    start_pdf_index: int = 0
) -> Tuple[int, int]:
    """
    Fügt Seitenmarker in einen Vortrag ein.
    
    WICHTIG: Marker werden streng sequentiell gesucht und eingefügt.
    Jede Seitenzahl kommt nur einmal vor, in aufsteigender Reihenfolge.
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
    
    # Schritt 3: Sammle Marker-Positionen (streng sequentiell)
    markers = []  # (position, page_num)
    search_start = 0
    last_pdf_index = start_pdf_index
    current_page = start_page
    
    # Filtere PDF-Seiten für diesen Vortrag
    relevant_pages = [(idx, pn, pe, ts) for idx, pn, pe, ts in pdf_pages 
                      if start_page <= pn <= (end_page or 9999)]
    
    for pdf_idx, page_num, prev_end, this_start in relevant_pages:
        # Überspringe wenn Seitenzahl nicht die erwartete nächste ist
        # (verhindert Duplikate und Rückwärts-Sprünge)
        if page_num < current_page:
            continue
        
        # Erste Seite: Marker am Anfang
        if page_num == start_page:
            markers.append((0, page_num))
            current_page = page_num + 1
            last_pdf_index = pdf_idx
            continue
        
        # Finde Position für diese Seite
        pos = find_pagebreak_position(prev_end, this_start, full_text, search_start)
        
        if pos is not None and pos > search_start:
            markers.append((pos, page_num))
            search_start = pos + 1
            current_page = page_num + 1
            last_pdf_index = pdf_idx
    
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
    source_file, lectures = load_lectures_for_ga(ga_norm)
    
    if not lectures:
        # Versuche Bücher
        source_file, book = load_books_for_ga(ga_norm)
        if book:
            lectures = [book]
            print(f"  Buch geladen: {book.get('title', '')[:50]}")
        else:
            return {"error": "Keine Vorträge/Bücher gefunden"}
    else:
        print(f"  {len(lectures)} Vorträge geladen")
    
    # Page-Mapping laden
    mapping = load_page_mapping()
    ga_mapping = mapping.get(ga_norm, {})
    
    # Verarbeite jeden Vortrag
    total_inserted = 0
    current_pdf_index = 0  # Für PDFs mit doppelten Seitenzahlen
    
    for i, lecture in enumerate(lectures):
        lec_id = lecture.get("ID") or f"{ga_norm}/{i+1}"
        lec_num = int(lecture.get("lectureNumber") or i + 1)
        
        # Start-Seite aus Mapping oder Schätzung
        start_page = ga_mapping.get(lec_id)
        if not start_page:
            # Fallback: erste verfügbare Seite (Index 1 = Seitenzahl)
            if pdf_pages:
                start_page = pdf_pages[0][1]
        
        # End-Seite: nächster Vortrag oder letzte Seite
        end_page = None
        if i + 1 < len(lectures):
            next_id = lectures[i + 1].get("ID") or f"{ga_norm}/{i+2}"
            end_page = ga_mapping.get(next_id)
            if end_page:
                end_page -= 1
        
        if not end_page and pdf_pages:
            end_page = pdf_pages[-1][1]  # Index 1 = Seitenzahl
        
        inserted, current_pdf_index = process_lecture(
            lecture, pdf_pages, start_page or 1, end_page, current_pdf_index
        )
        total_inserted += inserted
        
        title = (lecture.get("title") or "")[:40]
        print(f"    {lec_id}: {inserted} Marker (S.{start_page}-{end_page}) - {title}")
    
    print(f"\n  Gesamt: {total_inserted} Marker eingefügt")
    
    # Speichern
    if source_file and update_source:
        # Originaldatei aktualisieren
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
        
        print(f"  Gespeichert in: {source_file.name}")
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

