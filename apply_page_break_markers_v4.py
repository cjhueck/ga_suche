#!/usr/bin/env python3
"""
Apply Page-Break Anchors (V4) to Book/Lecture Paragraphs

GA-BAND-KATEGORIEN:
  BÜCHER:    GA001-GA028, GA045  -> steiner-books-*.json
  AUFSÄTZE:  GA029-GA036, GA046  -> steiner-full-lectures-*.json (wie Vorträge)
  VORTRÄGE:  GA051 ff            -> steiner-full-lectures-*.json

Nimmt (left/right)-Umbruchanker aus `page-break-markers.json` und findet im
JSON-Buchtext die exakte Einfügeposition pro Seitenumbruch.

Ergebnis (Test-Workflow):
  - schreibt standardmäßig KEINE bestehenden steiner-books-*.json um
  - erzeugt stattdessen ein GA-spezifisches Test-Output mit eingefügten Markern
  - Output wird in pagebreaks/ gespeichert (Override für Backend)

Marker-Syntax (intern):
  |<page>|
Beispiel:
  Philo|25|sophie

Aufruf:
  python apply_page_break_markers_v4.py GA004
  python apply_page_break_markers_v4.py GA004 --out pagebreaks/GA004.json
  python apply_page_break_markers_v4.py GA051 --out pagebreaks/GA051.json
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from array import array
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


SCRIPT_DIR = Path(__file__).parent
ANCHORS_FILE = SCRIPT_DIR / "page-break-markers.json"
DEFAULT_REPORT = SCRIPT_DIR / "page-break-apply-report.json"


LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}

STOPWORDS = {
    "der", "die", "das", "und", "oder", "aber", "dass", "daß", "den", "dem", "des",
    "ein", "eine", "einen", "einem", "einer", "eines", "ist", "sind", "war", "waren",
    "nicht", "nur", "auch", "noch", "schon", "mit", "von", "zu", "für", "auf", "in",
    "im", "am", "an", "als", "wie", "so", "sich", "ich", "wir", "ihr", "er", "sie", "es",
    "man", "bei", "durch", "wenn", "weil", "wird", "werden", "kann", "können",
}


def normalize_ga(ga_arg: str) -> Optional[str]:
    m = re.search(r"(\d+[a-z]?)", ga_arg, re.IGNORECASE)
    if not m:
        return None
    return f"GA{m.group(1).zfill(3).upper()}"


def iter_steiner_books_files() -> List[Path]:
    """
    Gibt alle steiner-books-*.json Dateien zurück, sortiert nach Änderungsdatum (neueste zuletzt).
    Damit wird bei der Suche die neueste Datei bevorzugt (überschreibt frühere Funde).
    """
    books_dir = SCRIPT_DIR / "steiner-books"
    if books_dir.exists():
        files = list(books_dir.glob("steiner-books-*.json"))
    else:
        files = list(SCRIPT_DIR.glob("steiner-books-*.json"))
    # Sortiere nach Änderungsdatum (älteste zuerst, neueste zuletzt)
    return sorted(files, key=lambda f: f.stat().st_mtime)


def load_json(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_alpha(ch: str) -> bool:
    return ch.isalpha()  # ok für DE


def is_lower_alpha(ch: str) -> bool:
    return ch.isalpha() and ch == ch.lower()


def normalize_simple(text: str) -> str:
    """
    Normalisierung für Matching (ohne Mapping):
    - lowercase
    - whitespace -> single space
    - soft hyphen entfernen
    - Ligaturen expandieren
    - ß -> ss
    - Hyphenation-Muster "x- <spaces>y" (y klein) -> "xy"
    """
    if not text:
        return ""

    s = text.replace("\u00ad", "").replace("\u00a0", " ")
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    s = s.lower()

    out = []
    i = 0
    last_space = False
    while i < len(s):
        ch = s[i]

        # Alte Orthographie: "th" -> "t" (z.B. "Thatsachen" ~ "Tatsachen")
        if ch == "t" and i + 1 < len(s) and s[i + 1] == "h":
            out.append("t")
            last_space = False
            i += 2
            continue

        # ß -> ss
        if ch == "ß":
            out.append("s")
            out.append("s")
            last_space = False
            i += 1
            continue

        # Hyphenation: Buchstabe + ('-' oder '¬') + whitespace + kleinbuchstabe => zusammenziehen
        if ch in {"-", "¬"} and i > 0 and is_alpha(s[i - 1]):
            j = i + 1
            while j < len(s) and s[j].isspace():
                j += 1
            if j < len(s) and is_lower_alpha(s[j]):
                # überspringe '-' und whitespace; der nächste Buchstabe kommt direkt
                i = j
                continue

        # whitespace
        if ch.isspace():
            if not last_space:
                out.append(" ")
                last_space = True
            i += 1
            continue

        out.append(ch)
        last_space = False
        i += 1

    return "".join(out).strip()


def normalize_paragraphs_with_map(paragraphs: List[Dict]) -> Tuple[str, array, array]:
    """
    Baut einen normalisierten Gesamttext aus allen Paragraphen und eine Mapping-Tabelle:
      norm_index -> (para_idx, char_idx)
    Rückgabe:
      norm_text, norm_para_idx[], norm_char_idx[]
    """
    norm_chars: List[str] = []
    norm_para = array("I")
    norm_char = array("I")

    last_space = False

    def emit(ch: str, p_i: int, c_i: int) -> None:
        nonlocal last_space
        norm_chars.append(ch)
        norm_para.append(p_i)
        norm_char.append(c_i)
        last_space = (ch == " ")

    for p_i, p in enumerate(paragraphs):
        s0 = (p.get("content") or "").replace("\u00a0", " ")
        
        # WICHTIG: Fußnoten überspringen (beginnen mit "[^")
        # Diese stehen im JSON am Ende, aber im PDF mitten im Text.
        # Wenn wir sie bei der Normalisierung einschließen, werden OCR-Anker
        # fälschlicherweise in den Fußnoten gefunden.
        if s0.startswith("[^"):
            continue
        
        # Separator zwischen Paragraphen: ein Space, der auf das Paragraph-Ende gemappt wird
        if p_i > 0:
            if not last_space:
                emit(" ", p_i - 1, len((paragraphs[p_i - 1].get("content") or "")))

        # Ligaturen im ORIGINAL expandieren (Mapping bleibt auf Original-Index)
        # -> wir expandieren während des Scans, indem wir pro Original-Char evtl. mehrere Normal-Chars emittieren.
        i = 0
        while i < len(s0):
            ch0 = s0[i]

            # soft hyphen raus
            if ch0 == "\u00ad":
                i += 1
                continue

            # Ligaturen
            if ch0 in LIGATURES:
                exp = LIGATURES[ch0].lower()
                for c in exp:
                    emit(c, p_i, i)
                i += 1
                continue

            # lowercase fürs Matching
            ch = ch0.lower()

            # Alte Orthographie: "th" -> "t" (Mapping: auf das 't' zeigen)
            if ch == "t" and i + 1 < len(s0) and s0[i + 1].lower() == "h":
                emit("t", p_i, i)
                i += 2
                continue

            # ß -> ss
            if ch == "ß":
                emit("s", p_i, i)
                emit("s", p_i, i)
                i += 1
                continue

            # Hyphenation in SOURCE: x-<ws>y (y klein) -> xy
            if ch in {"-", "¬"} and i > 0 and is_alpha(s0[i - 1]):
                j = i + 1
                while j < len(s0) and s0[j].isspace():
                    j += 1
                if j < len(s0) and is_lower_alpha(s0[j].lower()):
                    i = j
                    continue

            # whitespace -> single space
            if ch.isspace():
                if not last_space:
                    emit(" ", p_i, i)
                i += 1
                continue

            emit(ch, p_i, i)
            i += 1

    norm_text = "".join(norm_chars).strip()
    # strip() oben entfernt evtl. führende/trailing spaces ohne Mapping; wir korrigieren das,
    # indem wir Leading/Trailing Spaces gar nicht emittieren (über last_space) und norm_text ohnehin trimmen.
    # Mapping-Arrays bleiben dennoch passend, weil wir hier nur für Testzwecke verwenden und Insert-Posen
    # in der Regel nicht auf führende Spaces fallen.
    return norm_text, norm_para, norm_char


def find_best_insertion(
    norm_content: str,
    norm_para: array,
    norm_char: array,
    left: str,
    right: str,
    hyphenated: bool,
    min_norm_pos: int = 0,
) -> Optional[Tuple[int, int, int]]:
    """
    Findet die Insert-Position als (para_idx, char_idx) = Startposition von RIGHT im JSON.
    Verwendet LEFT als Disambiguierung.
    """
    r_norm_full = normalize_simple(right)
    l_norm_full = normalize_simple(left)

    def left_only() -> Optional[Tuple[int, int, int]]:
        """
        Fallback: Wenn RIGHT leer/zu kurz/zu kaputt ist, verankere am Ende von LEFT.
        Das ist nicht perfekt, aber deutlich besser als fehlende Marker.
        """
        if not l_norm_full or len(l_norm_full) < 25:
            return None
        for l_len in [180, 160, 140, 120, 100, 80, 60]:
            l_key = l_norm_full[-min(l_len, len(l_norm_full)) :].strip()
            if hyphenated and l_key.endswith("-"):
                l_key = l_key[:-1]
            if len(l_key) < 25:
                continue
            pos = norm_content.find(l_key, max(0, min_norm_pos))
            if pos >= 0:
                ins = pos + len(l_key)
                if ins >= len(norm_content):
                    ins = len(norm_content) - 1
                try:
                    return int(norm_para[ins]), int(norm_char[ins]), int(ins)
                except Exception:
                    return None
        return None

    # Wenn RIGHT zu kurz ist, direkt Left-only versuchen
    if not r_norm_full or len(r_norm_full) < 30:
        return left_only()

    def left_bonus(pos_start: int) -> float:
        """Bewertet ob LEFT kurz vor pos_start vorkommt."""
        if not l_norm_full:
            return 0.0
        window_start = max(0, pos_start - 900)
        for l_len in [140, 120, 100, 80, 60, 45]:
            l_key = l_norm_full[-min(l_len, len(l_norm_full)) :].strip()
            if hyphenated and l_key.endswith("-"):
                l_key = l_key[:-1]
            if len(l_key) < 25:
                continue
            l_pos = norm_content.rfind(l_key, window_start, pos_start)
            if l_pos >= 0:
                dist = pos_start - (l_pos + len(l_key))
                if dist < 0:
                    dist = abs(dist)
                if dist <= 10:
                    return 10.0 + (len(l_key) / 200.0)
                if dist <= 30:
                    return 7.0 + (len(l_key) / 200.0)
                if dist <= 80:
                    return 4.0 + (len(l_key) / 200.0)
                if dist <= 200:
                    return 2.0 + (len(l_key) / 200.0)
                return 0.2
        return -0.5

    def token_candidates() -> List[int]:
        """
        Fuzzy-Kandidatenstarts über Token-Alignment:
        - wähle 2-3 längere Wörter aus RIGHT
        - suche deren Vorkommen im Content
        - rechne Kandidatenstart = foundPos - tokenOffsetInRight
        """
        # nur ersten Teil verwenden (zu weit hinten wird ungenauer)
        region = r_norm_full[:400]
        tokens = re.findall(r"[a-zäöüß]{6,}", region)
        tokens = [t for t in tokens if t not in STOPWORDS]
        # längste zuerst, Duplikate raus
        uniq = []
        seen = set()
        for t in sorted(tokens, key=len, reverse=True):
            if t in seen:
                continue
            seen.add(t)
            uniq.append(t)
            if len(uniq) >= 6:
                break

        # sammle Kandidaten in Buckets (5er Raster)
        buckets: Dict[int, int] = {}
        for t in uniq:
            off = r_norm_full.find(t)
            if off < 0:
                continue
            # occurrences begrenzen
            occ = 0
            start = 0
            while True:
                p = norm_content.find(t, start)
                if p < 0:
                    break
                occ += 1
                if occ > 2000:
                    # zu häufig -> Token zu unspezifisch
                    buckets = {}
                    break
                cand = p - off
                if cand >= 0:
                    buckets[cand // 5] = buckets.get(cand // 5, 0) + 1
                start = p + 1
            if buckets:
                # wenn dieses Token brauchbar war, nimm zusätzlich noch 1-2 weitere Tokens
                continue

        if not buckets:
            return []

        # Top Buckets
        top = sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)[:40]
        # expand buckets back to candidate starts (center of bucket)
        return [k * 5 for k, _ in top]

    # Kandidatenlängen (erst lang, dann kürzer)
    r_lens = [140, 120, 100, 80, 60]

    best_score = -1.0
    best_pos: Optional[int] = None

    # 1) Schnellpfad: exakter RIGHT-Fund (nur ab min_norm_pos)
    for r_len in r_lens:
        r_key = r_norm_full[: min(r_len, len(r_norm_full))].strip()
        if len(r_key) < 30:
            continue

        start = max(0, min_norm_pos)
        while True:
            pos = norm_content.find(r_key, start)
            if pos < 0:
                break

            score = 1.0 + left_bonus(pos)

            if score > best_score:
                best_score = score
                best_pos = pos

            start = pos + 1

        if best_pos is not None and best_score >= 8.0:
            break  # gut genug, nicht weiter verkürzen

    # 2) Fuzzy-Pfad: wenn RIGHT nicht exakt gefunden wurde (OCR/Schriftartefakte)
    if best_pos is None:
        # Kandidatenstartpositionen über Token-Alignment
        cands = token_candidates()
        if not cands:
            return None

        # Vergleichsfenster: rechter Prefix
        r_cmp = r_norm_full[:160]
        for cand_start in cands:
            if cand_start < min_norm_pos:
                continue
            if cand_start < 0 or cand_start >= len(norm_content):
                continue
            seg = norm_content[cand_start : cand_start + len(r_cmp)]
            if len(seg) < 50:
                continue
            ratio = SequenceMatcher(None, r_cmp, seg).ratio()
            score = ratio * 10.0 + left_bonus(cand_start)
            if score > best_score:
                best_score = score
                best_pos = cand_start

    # Map norm index -> (para_idx, char_idx)
    if best_pos is None:
        return left_only()
    try:
        p_i = int(norm_para[best_pos])
        c_i = int(norm_char[best_pos])
        return p_i, c_i, int(best_pos)
    except Exception:
        return None


def find_safe_insertion_position(text: str, pos: int) -> int:
    """
    Prüft ob die Position innerhalb einer geschützten Markdown-Struktur liegt
    und verschiebt sie ggf. an eine sichere Stelle.
    
    Geschützte Strukturen:
    - Markdown-Bilder: ![alt](pfad)
    - Markdown-Links: [text](url)
    - HTML-Tags: <tag ...>
    
    Returns: Sichere Einfügeposition (vor der geschützten Struktur)
    """
    if pos < 0:
        return 0
    if pos > len(text):
        return len(text)
    
    # Finde alle geschützten Bereiche im Text
    protected_ranges: List[Tuple[int, int]] = []
    
    # Markdown-Bilder: ![...](...)
    for m in re.finditer(r'!\[[^\]]*\]\([^)]+\)', text):
        protected_ranges.append((m.start(), m.end()))
    
    # Markdown-Links: [...](...) - aber nicht Bilder (die beginnen mit !)
    for m in re.finditer(r'(?<!!)\[[^\]]*\]\([^)]+\)', text):
        protected_ranges.append((m.start(), m.end()))
    
    # HTML-Tags: <...>
    for m in re.finditer(r'<[^>]+>', text):
        protected_ranges.append((m.start(), m.end()))
    
    # Prüfe ob Position in einem geschützten Bereich liegt
    for start, end in protected_ranges:
        if start < pos < end:
            # Position liegt innerhalb -> verschiebe VOR die Struktur
            return start
    
    return pos


def find_word_boundary(text: str, pos: int) -> int:
    """
    Findet die beste Wortgrenze für eine Seitenmarker-Position.
    
    Der Marker markiert den BEGINN einer neuen Seite, also sollte er
    VOR dem ersten Wort der neuen Seite stehen, nicht nach dem letzten
    Wort der alten Seite.
    
    Strategie:
    1. Wenn Position nicht mitten im Wort liegt -> ok
    2. Wenn mitten im Wort: Verschiebe nach RECHTS zum Wortende,
       dann suche nach vorne bis zum nächsten Wortanfang
       (so steht der Marker vor dem neuen Wort, nicht nach dem alten)
    """
    if pos <= 0:
        return 0
    if pos >= len(text):
        return len(text)
    
    # Prüfe ob wir mitten in einem Wort sind
    left_char = text[pos - 1] if pos > 0 else ' '
    right_char = text[pos] if pos < len(text) else ' '
    
    # Wenn nicht mitten im Wort, Position ist ok
    if not (left_char.isalpha() and right_char.isalpha()):
        # Aber: Wenn wir direkt nach einem Wort stehen und Leerzeichen folgt,
        # verschiebe zum Leerzeichen (damit Marker vor dem nächsten Wort steht)
        if left_char.isalpha() and right_char.isspace():
            # Suche das nächste Nicht-Leerzeichen (Wortanfang)
            next_word = pos
            while next_word < len(text) and text[next_word].isspace():
                next_word += 1
            # Nur verschieben wenn wir ein Wort finden (nicht am Absatzende)
            if next_word < len(text):
                return next_word
        return pos
    
    # Wir sind mitten im Wort - gehe zum Ende des Wortes
    word_end = pos
    while word_end < len(text) and text[word_end].isalpha():
        word_end += 1
    
    # Jetzt überspringe Leerzeichen/Satzzeichen zum nächsten Wortanfang
    next_word = word_end
    while next_word < len(text) and not text[next_word].isalpha():
        next_word += 1
    
    # Wenn wir ein nächstes Wort gefunden haben, stelle Marker davor
    if next_word < len(text):
        return next_word
    
    # Sonst: Ende des Wortes (Absatzende)
    return word_end


def apply_insertions_to_paragraphs(
    paragraphs: List[Dict], 
    insertions: List[Tuple[int, int, int]],
    expected_min: Optional[int] = None,
    expected_max: Optional[int] = None
) -> int:
    """
    insertions: List[(para_idx, char_idx, page)] - muss pro Absatz absteigend sortiert angewendet werden.
    expected_min/max: Optionaler erwarteter Seitenbereich für den Vortrag.
    
    Intelligente Version mit eingebauter Korrekturlogik:
    - Verschiebt Marker auf Wortgrenzen (nicht mitten ins Wort)
    - Verhindert doppelte Marker an derselben Stelle
    - Verhindert globale Duplikate (dieselbe Seitenzahl mehrfach im Text)
    - Filtert Seitenzahlen außerhalb des erwarteten Bereichs (mit Toleranz)
    - Entfernt doppelte aufeinanderfolgende Seitenzahlen
    
    Returns: Anzahl der tatsächlich eingefügten Seitenzahlen
    """
    # Sammle bereits im Text vorhandene Seitenzahlen (vor dem Einfügen)
    existing_pages: set = set()
    for para in paragraphs:
        content = para.get("content") or ""
        for m in re.finditer(r'\|<?(\d+)>?\|', content):
            existing_pages.add(int(m.group(1)))
    
    # Filtere Insertions VOR dem Einfügen
    filtered_insertions = []
    tolerance = 1  # Erlaube 1 Seite Toleranz am Rand des Bereichs
    
    for p_i, c_i, page in insertions:
        # Bereichsprüfung (wenn angegeben)
        if expected_min is not None and expected_max is not None:
            if page < expected_min - tolerance or page > expected_max + tolerance:
                continue  # Überspringe Seitenzahlen außerhalb des Bereichs
        
        # Globale Duplikat-Prüfung
        if page in existing_pages:
            continue  # Diese Seitenzahl existiert bereits
        
        filtered_insertions.append((p_i, c_i, page))
        existing_pages.add(page)  # Merke, dass diese Seite jetzt verwendet wird
    
    by_para: Dict[int, List[Tuple[int, int]]] = {}
    for p_i, c_i, page in filtered_insertions:
        by_para.setdefault(p_i, []).append((c_i, page))

    inserted_count = 0
    for p_i, items in by_para.items():
        # absteigend nach char_idx
        items.sort(key=lambda t: t[0], reverse=True)
        s = paragraphs[p_i].get("content") or ""
        
        # Verfolge bereits eingefügte Positionen um Duplikate zu vermeiden
        inserted_positions: set = set()
        
        for c_i, page in items:
            marker = f"|{page}|"
            if c_i < 0:
                c_i = 0
            if c_i > len(s):
                c_i = len(s)
            
            # Prüfe ob Position in geschützter Struktur liegt und verschiebe ggf.
            c_i = find_safe_insertion_position(s, c_i)
            
            # Verschiebe auf Wortgrenze (nicht mitten ins Wort!)
            c_i = find_word_boundary(s, c_i)
            
            # Verhindere doppelte Einfügung an derselben Stelle
            if c_i in inserted_positions:
                continue
            inserted_positions.add(c_i)
            
            s = s[:c_i] + marker + s[c_i:]
            inserted_count += 1
            
            # Aktualisiere alle nachfolgenden Positionen (wir gehen absteigend, also nicht nötig)
        
        # Entferne doppelte aufeinanderfolgende Marker wie |116||116|
        s = re.sub(r'\|(\d+)\|\|(\d+)\|', lambda m: f"|{m.group(2)}|", s)
        
        paragraphs[p_i]["content"] = s
    
    # NACHBEREINIGUNG: Entferne nicht-sequentielle Seitenzahlen
    # (Seiten, die große Sprünge machen und wahrscheinlich falsch zugeordnet sind)
    cleanup_count = cleanup_non_sequential_pages(paragraphs, expected_min, expected_max)
    
    return inserted_count - cleanup_count


def cleanup_non_sequential_pages(
    paragraphs: List[Dict], 
    expected_min: Optional[int] = None, 
    expected_max: Optional[int] = None
) -> int:
    """
    Entfernt Seitenzahlen, die nicht sequentiell sind (große Sprünge nach vorne/hinten).
    Diese entstehen, wenn Anker an falschen Stellen im Text passen.
    """
    # Sammle alle Seitenzahlen mit Position
    all_pages = []
    for para_idx, para in enumerate(paragraphs):
        content = para.get("content") or ""
        for m in re.finditer(r'\|<?(\d+)>?\|', content):
            all_pages.append({
                "page": int(m.group(1)),
                "para_idx": para_idx,
                "match_idx": m.start(),
                "match_len": len(m.group(0))
            })
    
    if len(all_pages) < 3:
        return 0
    
    # Identifiziere Seiten, die nicht-sequentiell sind
    to_remove = []
    last_valid_page = all_pages[0]["page"]
    
    for i in range(1, len(all_pages)):
        current = all_pages[i]
        diff = current["page"] - last_valid_page
        
        # Großer Vorwärtssprung (> 3 Seiten) - wahrscheinlich falsche Zuordnung
        if diff > 3:
            to_remove.append(i)
            continue
        
        # JEDER Rückwärtssprung ist ein Fehler (Seiten müssen monoton steigen)
        if diff < 0:
            to_remove.append(i)
            continue
        
        last_valid_page = current["page"]
    
    # ZUSÄTZLICH: Prüfe die letzte Seitenzahl
    # Wenn sie einen großen Sprung von der vorletzten macht, gehört sie zum nächsten Vortrag
    remaining_pages = [p for i, p in enumerate(all_pages) if i not in to_remove]
    if len(remaining_pages) >= 2:
        last = remaining_pages[-1]
        second_last = remaining_pages[-2]
        if last["page"] - second_last["page"] > 2:
            # Die letzte Seite macht einen Sprung - entfernen
            to_remove.append(all_pages.index(last))
    
    if not to_remove:
        return 0
    
    # Entferne von hinten nach vorne
    for i in sorted(set(to_remove), reverse=True):
        info = all_pages[i]
        para = paragraphs[info["para_idx"]]
        content = para.get("content") or ""
        para["content"] = content[:info["match_idx"]] + content[info["match_idx"] + info["match_len"]:]
    
    return len(to_remove)


def iter_steiner_lectures_files() -> List[Path]:
    """
    Sucht in beiden Verzeichnissen: Unterordner und Hauptverzeichnis.
    Sortiert nach Änderungsdatum (neueste zuletzt), damit neuere Dateien bevorzugt werden.
    """
    lectures_dir = SCRIPT_DIR / "steiner-full-lectures"
    files = []
    # Suche zuerst im Unterordner
    if lectures_dir.exists():
        files.extend(lectures_dir.glob("steiner-full-lectures-*.json"))
    # Suche auch im Hauptverzeichnis
    files.extend(SCRIPT_DIR.glob("steiner-full-lectures-*.json"))
    # Entferne Duplikate und sortiere nach Änderungsdatum (älteste zuerst, neueste zuletzt)
    unique_files = list(set(files))
    return sorted(unique_files, key=lambda f: f.stat().st_mtime)


def load_book_by_ga(ga_number: str) -> Tuple[Path, Dict]:
    """
    Findet den Book-Eintrag für GAxxx in steiner-books-*.json und gibt (file_path, book_obj) zurück.
    WICHTIG: Verwendet die neueste Datei (nach Änderungsdatum), falls GA in mehreren Dateien vorkommt.
    """
    found_path = None
    found_book = None
    
    # Dateien sind nach Datum sortiert (älteste zuerst), also überschreibt neuere die ältere
    for path in iter_steiner_books_files():
        data = load_json(path)
        books = data.get("books") or []
        for b in books:
            if (b.get("ID") or "").upper() == ga_number.upper():
                found_path = path
                found_book = b
                # Nicht abbrechen - weitermachen, um neuere Dateien zu finden
    
    if found_book is not None:
        return found_path, found_book
    raise FileNotFoundError(f"{ga_number} nicht in steiner-books-*.json gefunden")


def load_lectures_by_ga(ga_number: str) -> Tuple[Path, Dict]:
    """
    Findet alle Lectures für GAxxx in steiner-full-lectures-*.json und 
    gibt (file_path, pseudo_book_obj) zurück.
    
    Das pseudo_book_obj hat die gleiche Struktur wie ein Book:
    - ID, title, paragraphs
    - _lectures: Liste der Original-Lecture-Objekte (für spätere Zuordnung)
    """
    ga_upper = ga_number.upper()
    all_lectures: List[Dict] = []
    source_path: Optional[Path] = None
    
    for path in iter_steiner_lectures_files():
        data = load_json(path)
        lectures = data.get("lectures") or []
        matching = [lec for lec in lectures if (lec.get("gaNumber") or "").upper() == ga_upper]
        if matching:
            all_lectures.extend(matching)
            if source_path is None:
                source_path = path
    
    if not all_lectures:
        raise FileNotFoundError(f"{ga_number} nicht in steiner-full-lectures-*.json gefunden")
    
    # Entferne Duplikate (basierend auf ID)
    seen_ids: set = set()
    unique_lectures: List[Dict] = []
    for lec in all_lectures:
        lec_id = lec.get("ID") or lec.get("title") or ""
        if lec_id not in seen_ids:
            seen_ids.add(lec_id)
            unique_lectures.append(lec)
    all_lectures = unique_lectures
    
    # Sortiere nach lectureNumber falls vorhanden
    all_lectures.sort(key=lambda x: int(x.get("lectureNumber") or 0))
    
    # Sammle alle Paragraphen mit Referenz zur Lecture
    all_paragraphs: List[Dict] = []
    for lec_idx, lec in enumerate(all_lectures):
        for para in (lec.get("paragraphs") or []):
            # Kopiere Paragraph und füge Lecture-Referenz hinzu
            para_copy = dict(para)
            para_copy["_lecture_idx"] = lec_idx
            para_copy["_lecture_id"] = lec.get("ID")
            all_paragraphs.append(para_copy)
    
    # Erstelle pseudo_book
    pseudo_book = {
        "ID": ga_upper,
        "title": all_lectures[0].get("gaTitle") or f"{ga_upper} Vorträge",
        "paragraphs": all_paragraphs,
        "_lectures": all_lectures,
        "_is_lectures": True,
    }
    
    return source_path, pseudo_book


def load_content_by_ga(ga_number: str) -> Tuple[Path, Dict, bool]:
    """
    Lädt entweder Buch oder Vorträge für eine GA-Nummer.
    Rückgabe: (source_path, content_obj, is_lectures)
    
    AUFSATZBÄNDE: Diese GA-Nummern existieren sowohl als Buch als auch als Vorträge,
    werden aber im Frontend als Aufsätze (wie Vorträge) angezeigt.
    Daher müssen sie hier auch als Vorträge verarbeitet werden!
    """
    # Aufsatzbände: Als Vorträge behandeln, auch wenn Buch existiert
    ga_upper = ga_number.upper()
    aufsatzbaende = ['GA019', 'GA024', 'GA026', 'GA042', 'GA043', 'GA044']
    
    # Für Aufsatzbände: Vorträge zuerst versuchen
    if ga_upper in aufsatzbaende:
        try:
            path, pseudo_book = load_lectures_by_ga(ga_number)
            return path, pseudo_book, True
        except FileNotFoundError:
            pass
        # Fallback auf Buch
        try:
            path, book = load_book_by_ga(ga_number)
            return path, book, False
        except FileNotFoundError:
            pass
    else:
        # Normale Reihenfolge: Buch zuerst
        try:
            path, book = load_book_by_ga(ga_number)
            return path, book, False
        except FileNotFoundError:
            pass
        
        # Versuche Vorträge
        try:
            path, pseudo_book = load_lectures_by_ga(ga_number)
            return path, pseudo_book, True
        except FileNotFoundError:
            pass
    
    raise FileNotFoundError(f"{ga_number} weder in steiner-books-*.json noch in steiner-full-lectures-*.json gefunden")


def find_lecture_start_page(lecture: Dict, breaks: List[Dict], min_page: int = 5) -> Optional[int]:
    """
    Findet die Start-Seitenzahl eines Vortrags im PDF.
    Sucht den ersten Absatz des Vortrags in den Break-right-Snippets.
    
    Verwendet robustes Fuzzy-Matching mit normalisierten Texten.
    """
    paragraphs = lecture.get("paragraphs") or []
    if not paragraphs:
        return None
    
    # Nimm den ersten Absatz (ohne HTML-Tags)
    first_para = (paragraphs[0].get("content") or "")
    first_para = re.sub(r"<[^>]+>", " ", first_para)  # HTML-Tags entfernen
    
    # Normalisiere mit der gleichen Funktion wie für Breaks
    first_para_norm = normalize_simple(first_para)
    
    if len(first_para_norm) < 30:
        return None
    
    # Verwende die ersten 200 Zeichen für die Suche
    search_text = first_para_norm[:200]
    
    # Sortiere Breaks nach Seite
    sorted_breaks = sorted(breaks, key=lambda x: x.get("page", 0))
    
    best_match: Optional[Tuple[float, int]] = None  # (ratio, page)
    
    for b in sorted_breaks:
        page = b.get("page", 0)
        if page < min_page:
            continue
        
        right = b.get("right") or ""
        if not right:
            continue
            
        right_norm = normalize_simple(right)
        if not right_norm:
            continue
        
        # Methode 1: Exakte Teilstring-Suche mit verschiedenen Längen
        for search_len in [150, 120, 100, 80, 60, 40]:
            if search_len > len(search_text):
                continue
            search_key = search_text[:search_len]
            if search_key in right_norm:
                return page
        
        # Methode 2: Fuzzy-Matching mit SequenceMatcher
        # Vergleiche die ersten N Zeichen des Absatzes mit dem right-Snippet
        compare_len = min(120, len(search_text), len(right_norm))
        if compare_len >= 40:
            ratio = SequenceMatcher(None, search_text[:compare_len], right_norm[:compare_len]).ratio()
            if ratio > 0.75:  # Mindestens 75% Übereinstimmung
                if best_match is None or ratio > best_match[0]:
                    best_match = (ratio, page)
    
    # Rückgabe des besten Fuzzy-Matches, falls kein exakter Match gefunden
    if best_match and best_match[0] > 0.75:
        return best_match[1]
    
    return None


def load_lecture_page_mapping(ga_number: str) -> Dict[str, int]:
    """Lädt das Lecture-Page-Mapping für eine GA-Nummer."""
    mapping_file = SCRIPT_DIR / "lecture-page-mapping.json"
    if not mapping_file.exists():
        return {}
    
    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(ga_number.upper(), {})
    except Exception:
        return {}


def process_lectures_individually(
    lectures: List[Dict],
    breaks: List[Dict],
    ga_number: str,
    min_page: int = 5
) -> Tuple[int, int, List[Dict]]:
    """
    Verarbeitet jeden Vortrag einzeln:
    1. Liest die Start-Seitenzahl aus dem Mapping (lecture-page-mapping.json)
    2. Ordnet die Breaks diesem Vortrag zu
    3. Fügt die Marker ein
    
    Rückgabe: (inserted_count, total_count, failures)
    """
    # Sortiere Breaks nach Seitenzahl
    sorted_breaks = sorted(breaks, key=lambda x: x.get("page", 0))
    
    # Lade das Mapping
    mapping = load_lecture_page_mapping(ga_number)
    
    # Finde Start-Seiten für alle Vorträge aus dem Mapping
    lecture_starts: List[Tuple[int, int, Dict]] = []  # (lecture_idx, start_page, lecture)
    mapped_count = 0
    fallback_count = 0
    
    # Sammle zunächst alle Vorträge mit bekannter Startseite
    lectures_with_page = []
    lectures_without_page = []
    
    for idx, lec in enumerate(lectures):
        lec_id = lec.get("ID") or ""
        
        # Versuche zuerst das Mapping
        if lec_id in mapping:
            start_page = mapping[lec_id]
            mapped_count += 1
            lectures_with_page.append((idx, start_page, lec))
        else:
            # Fallback: Alte Methode (Suche in breaks)
            start_page = find_lecture_start_page(lec, breaks, min_page)
            if start_page:
                fallback_count += 1
                lectures_with_page.append((idx, start_page, lec))
            else:
                lectures_without_page.append((idx, lec))
    
    # Sortiere bekannte Vorträge nach Start-Seite
    lectures_with_page.sort(key=lambda x: x[1])
    lecture_starts = list(lectures_with_page)
    
    # NEUE FALLBACK-LOGIK: Schätze Startseiten für unbekannte Vorträge
    if lectures_without_page and lectures_with_page:
        print(f"  Schätze Startseiten für {len(lectures_without_page)} Vorträge...")
        
        # Finde den letzten bekannten Vortrag und seine Endseite
        last_known_page = lectures_with_page[-1][1]
        
        # Berechne durchschnittliche Seitenzahl pro Vortrag
        if len(lectures_with_page) >= 2:
            total_pages = lectures_with_page[-1][1] - lectures_with_page[0][1]
            avg_pages_per_lecture = max(5, total_pages // len(lectures_with_page))
        else:
            avg_pages_per_lecture = 15  # Standardwert
        
        # Schätze Startseiten für unbekannte Vorträge
        estimated_count = 0
        for i, (idx, lec) in enumerate(lectures_without_page):
            # Schätze basierend auf Position nach dem letzten bekannten Vortrag
            estimated_page = last_known_page + (i + 1) * avg_pages_per_lecture
            
            # Prüfe ob diese Schätzung Sinn macht (nicht über max_page)
            max_break_page = max(b.get("page", 0) for b in sorted_breaks) if sorted_breaks else estimated_page
            if estimated_page <= max_break_page:
                lecture_starts.append((idx, estimated_page, lec))
                estimated_count += 1
        
        if estimated_count > 0:
            fallback_count += estimated_count
            print(f"    → {estimated_count} Vorträge mit geschätzter Startseite")
    
    # Sortiere nach Start-Seite
    lecture_starts.sort(key=lambda x: x[1])
    
    print(f"  Vorträge mit Start-Seite: {len(lecture_starts)} von {len(lectures)} (Mapping: {mapped_count}, Fallback: {fallback_count})")
    
    inserted_total = 0
    failures: List[Dict] = []
    
    # Verarbeite jeden Vortrag
    for i, (lec_idx, start_page, lecture) in enumerate(lecture_starts):
        # Ende ist die nächste Start-Seite oder eine sinnvolle Obergrenze
        if i + 1 < len(lecture_starts):
            end_page = lecture_starts[i + 1][1]
        else:
            # Letzter Vortrag: Verwende die letzte verfügbare Seite aus den Breaks
            # (nicht künstlich begrenzen, da der letzte Vortrag oft länger ist)
            max_break_page = max(b.get("page", 0) for b in sorted_breaks) if sorted_breaks else start_page
            end_page = max_break_page + 1  # +1, da end_page exklusiv ist
        
        # Finde Breaks für diesen Vortrag
        lec_breaks = [b for b in sorted_breaks if start_page <= b.get("page", 0) < end_page]
        
        paragraphs = lecture.get("paragraphs") or []
        if not paragraphs:
            continue
        
        insertions: List[Tuple[int, int, int]] = []
        
        # Normalisiere Paragraphen für diesen Vortrag
        norm_content, norm_para, norm_char = normalize_paragraphs_with_map(paragraphs)
        
        last_norm_pos = 0
        
        # Start-Seite: Immer am Anfang des ersten FLIESSTEXT einfügen (nach Überschriften)
        # Die V4-Methode funktioniert nicht gut für Start-Seiten, da der Text
        # oft Teil einer Überschrift ist
        for p_idx, para in enumerate(paragraphs):
            content = para.get("content") or ""
            # Entferne HTML-Tags und prüfe ob noch Fließtext übrig ist
            text_only = re.sub(r"<[^>]+>", "", content).strip()
            if len(text_only) > 20:  # Mindestens 20 Zeichen Fließtext
                # Finde Position nach eventuellen Überschriften
                # Suche nach dem Ende des letzten </h*> Tags (inkl. Whitespace danach)
                last_heading_end = 0
                for m in re.finditer(r"</h[1-6]>\s*", content):
                    last_heading_end = m.end()
                insertions.append((p_idx, last_heading_end, start_page))
                break
        else:
            # Absoluter Fallback: Anfang des ersten Absatzes
            insertions.append((0, 0, start_page))
        
        # Alle weiteren Breaks verarbeiten
        # RESYNC-Mechanismus auch für Vorträge
        need_resync = False
        
        for b in lec_breaks:
            page = int(b.get("page", 0))
            
            # Überspringe die Start-Seite (bereits verarbeitet)
            if page == start_page:
                continue
            
            left = b.get("left") or ""
            right = b.get("right") or ""
            hyph = bool(b.get("hyphenated"))
            
            # Normale Suche mit min_norm_pos
            search_min = last_norm_pos if not need_resync else 0
            found = find_best_insertion(
                norm_content, norm_para, norm_char, left, right, hyph, 
                min_norm_pos=search_min
            )
            
            # Bei Fehlschlag: Resync versuchen
            if not found and not need_resync:
                found = find_best_insertion(
                    norm_content, norm_para, norm_char, left, right, hyph, 
                    min_norm_pos=0
            )
            
            if found:
                p_i, c_i, norm_pos = found
                insertions.append((p_i, c_i, page))
                last_norm_pos = norm_pos + 1
                need_resync = False
            else:
                failures.append({"page": page, "reason": "no-match", "lecture": lec_idx})
                need_resync = True
        
        # Wende Insertions an (mit Bereichsprüfung)
        actual_inserted = apply_insertions_to_paragraphs(
            paragraphs, insertions, 
            expected_min=start_page, expected_max=end_page
        )
        # DEBUG: Zeige erste erfolgreiche Einfügung
        if i < 3:
            print(f"    Vortrag {lec_idx}: {actual_inserted} Seiten eingefügt (S.{start_page}-{end_page})")
        inserted_total += actual_inserted
    
    return inserted_total, len(sorted_breaks), failures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ga", help="z.B. GA004")
    ap.add_argument("--anchors", default=str(ANCHORS_FILE), help="Pfad zu page-break-markers.json")
    ap.add_argument("--out", default="", help="Output JSON (nur GA-Objekt) mit eingefügten Markern")
    ap.add_argument("--report", default=str(DEFAULT_REPORT), help="Report JSON")
    args = ap.parse_args()

    ga = normalize_ga(args.ga)
    if not ga:
        print("FEHLER: Ungültige GA-Nummer")
        sys.exit(1)

    anchors_path = Path(args.anchors)
    anchors = load_json(anchors_path)
    if ga not in anchors:
        print(f"FEHLER: {ga} nicht in {anchors_path.name} vorhanden")
        sys.exit(1)

    ga_anchors = anchors[ga]
    breaks = ga_anchors.get("breaks") or []
    print(f"[V4] {ga}: Break-Anker: {len(breaks)}")

    src_path, content, is_lectures = load_content_by_ga(ga)
    paragraphs = content.get("paragraphs") or []
    if not paragraphs:
        print(f"FEHLER: {ga} hat keine paragraphs-Struktur in {src_path.name}")
        sys.exit(1)

    content_type = "Vorträge" if is_lectures else "Buch"
    lecture_count = len(content.get("_lectures", [])) if is_lectures else 0
    extra_info = f", {lecture_count} Vorträge" if is_lectures else ""
    print(f"[V4] {ga}: Quelle: {src_path.name} ({content_type}), Paragraphen: {len(paragraphs)}{extra_info}")

    # Unterschiedliche Verarbeitung für Bücher und Vorträge
    if is_lectures:
        # VORTRÄGE: Jeden Vortrag einzeln verarbeiten
        lectures = content.get("_lectures", [])
        ok, total, failures = process_lectures_individually(lectures, breaks, ga, min_page=5)
    else:
        # BÜCHER: Wie bisher - als zusammenhängender Text
        # Norm + Mapping bauen
        norm_content, norm_para, norm_char = normalize_paragraphs_with_map(paragraphs)
        print(f"[V4] {ga}: norm length: {len(norm_content):,}")

        insertions: List[Tuple[int, int, int]] = []
        failures: List[Dict] = []
        last_norm_pos = 0

        # Auto-Startseite: verhindert, dass Frontmatter-Seiten (TOC/Impressum etc.)
        # fälschlich tief im Text gematcht werden (z.B. |5| mitten im Buch).
        start_page: Optional[int] = None
        start_pos_limit = int(len(norm_content) * 0.25)  # erster echter Match muss im ersten Viertel liegen
        last_inserted_page: Optional[int] = None

        # Filtere doppelte Seitenzahlen: Nur den ersten Eintrag pro Seite verwenden
        # (Doppelte entstehen durch OCR-Fehler oder mehrfache Seitenzahl-Erwähnungen im PDF)
        sorted_breaks = sorted(breaks, key=lambda x: int(x.get("page") or 0))
        seen_pages: set = set()
        unique_breaks = []
        for b in sorted_breaks:
            page = int(b.get("page") or 0)
            if page not in seen_pages:
                unique_breaks.append(b)
                seen_pages.add(page)
        
        if len(unique_breaks) < len(sorted_breaks):
            print(f"[V4] {ga}: {len(sorted_breaks) - len(unique_breaks)} doppelte Seitenzahlen entfernt")

        # Wir setzen Marker am START der nächsten Seite => direkt vor right
        for b in unique_breaks:
            page = int(b.get("page") or 0)
            left = b.get("left") or ""
            right = b.get("right") or ""
            hyph = bool(b.get("hyphenated"))

            if page <= 0:
                continue

            found = find_best_insertion(
                norm_content, norm_para, norm_char, left, right, hyph, min_norm_pos=last_norm_pos
            )
            
            # Bei Fehlschlag: Zweiter Versuch NUR mit RIGHT (ignoriere LEFT)
            # Grund: LEFT kann Fußnoten-Text enthalten, der im JSON am Ende steht
            if not found and right:
                found = find_best_insertion(
                    norm_content, norm_para, norm_char, "", right, hyph, min_norm_pos=last_norm_pos
                )
                if found:
                    print(f"  [RIGHT-ONLY] Seite {page}: Gefunden ohne LEFT")
            
            if not found:
                failures.append({"page": page, "reason": "no-match", "left": left[-80:], "right": right[:80]})
                continue

            p_i, c_i, norm_pos = found

            # Startseite finden (einmalig): der erste plausible Treffer muss früh im Text liegen.
            if start_page is None:
                if norm_pos > start_pos_limit and page <= 50:
                    # sehr wahrscheinlich Frontmatter-False-Positive
                    failures.append({"page": page, "reason": "start-too-late", "left": left[-80:], "right": right[:80]})
                    continue
                start_page = page
                # setze last_norm_pos auf diesen Treffer, damit die Sequenz stimmt
                last_norm_pos = norm_pos
                last_inserted_page = page
            else:
                # Seiten vor start_page werden ignoriert
                if page < start_page:
                    continue

                # Schutz gegen Ausreißer: ein einzelner falscher Treffer darf die Monotonie nicht "nach vorne reißen"
                # und dadurch alle folgenden Seiten unmöglich machen.
                if last_inserted_page is not None:
                    page_diff = max(1, page - last_inserted_page)
                else:
                    page_diff = 1
                delta = norm_pos - last_norm_pos
                max_jump = max(40000, page_diff * 15000)
                if delta > max_jump:
                    failures.append({"page": page, "reason": "jump-too-large", "left": left[-80:], "right": right[:80]})
                    continue

            insertions.append((p_i, c_i, page))
            # Update monotonic bound: exakt auf den gefundenen Norm-Index setzen.
            # (Das erneute Suchen nach right-prefix kann auf eine spätere, falsche Occurrence springen.)
            last_norm_pos = norm_pos + 1
            last_inserted_page = page

        # Insertions anwenden (absteigend pro Absatz)
        apply_insertions_to_paragraphs(paragraphs, insertions)

        ok = len(insertions)
        total = len([b for b in breaks if int(b.get("page") or 0) > 0])
    if total > 0:
        print(f"[V4] {ga}: eingefügt {ok}/{total} ({(ok/total*100.0):.1f}%)")
    else:
        print(f"[V4] {ga}: keine gültigen Breaks mit Seitenzahl (0) – nichts einzufügen")

    report = {
        "ga": ga,
        "sourceFile": str(src_path.name),
        "anchorsFile": str(anchors_path.name),
        "breaksTotal": len(breaks),
        "breaksWithPage": total,
        "inserted": ok,
        "insertedRatio": (ok / total) if total else 0.0,
        "failed": len(failures),
        "failuresSample": failures[:20],
    }
    save_json(Path(args.report), report)
    print(f"[V4] Report: {args.report}")

    # Output schreiben
    out_path = Path(args.out) if args.out else SCRIPT_DIR / f"{ga}-with-pagebreaks.json"
    
    if is_lectures:
        # Für Vorträge: Die Lectures wurden in process_lectures_individually
        # direkt (in-place) modifiziert, daher einfach ausgeben
        lectures = content.get("_lectures", [])
        
        out_obj = {
            "_info": "Output: Vorträge mit eingefügten |page|-Markern (aus V4 Break Anchors).",
            "ga": ga,
            "sourceFile": str(src_path.name),
            "lectureCount": len(lectures),
            "lectures": lectures,
        }
    else:
        out_obj = {
            "_info": "Output: Buch mit eingefügten |page|-Markern (aus V4 Break Anchors).",
            "ga": ga,
            "sourceFile": str(src_path.name),
            "book": content,
        }
    
    save_json(out_path, out_obj)
    print(f"[V4] Output: {out_path}")


if __name__ == "__main__":
    main()


