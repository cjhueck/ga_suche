#!/usr/bin/env python3
"""
Export Page Markers V4 (Page-Break Anchors)

Ziel:
  Seitenumbruch-Marker robust aus PDF -> JSON zuordnen, indem pro Umbruch zwei
  Kontexte gespeichert werden:
    - left:  letzte N Zeichen des Fließtexts auf Seite X (VOR dem Umbruch)
    - right: erste N Zeichen des Fließtexts auf Seite X+1 (NACH dem Umbruch)

Warum:
  Die Umbruchstelle existiert nur im PDF. Mit (left,right) lässt sich die Nahtstelle
  im JSON-Text deutlich robuster (fuzzy/normalisiert) finden und der Marker genau
  an die Umbruchstelle setzen (ggf. mitten im Wort).

Output:
  Standardmäßig in: page-break-markers.json

Format (Beispiel):
{
  "_info": "...",
  "GA004": {
    "title": "...",
    "pdfSource": "...pdf",
    "pdfPageCount": 288,
    "breaks": [
      {
        "page": 9,
        "pdfFrom": 7,
        "pdfTo": 8,
        "left": "....",
        "right": "....",
        "hyphenated": true,
        "printedPageConfidence": "extracted"
      }
    ]
  }
}

Hinweis:
  V4 schreibt NUR die Break-Anker. Das eigentliche "Fuzzy-Finden und Marker setzen"
  passiert anschließend (z.B. in einem separaten Schritt/Script oder im Frontend).
"""

from __future__ import annotations

import io
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

import fitz  # PyMuPDF

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = SCRIPT_DIR / "page-break-markers.json"

# Kontexte je Umbruch
LEFT_CHARS = 200
RIGHT_CHARS = 200

# WICHTIG:
# Wir filtern NICHT pauschal oben/unten per Prozent, weil das echten Fließtext
# am Seitenanfang/-ende abschneiden kann (Marker driftet).
# Stattdessen:
# - Footer (Seitenzahl/Seite:) wird über Y-Position + Muster entfernt
# - Running Headers werden über Wiederholungs-Erkennung entfernt
# - "Überschriften"-Zeilen (ALL CAPS etc.) werden übersprungen, damit left/right
#   in den Fließtext greifen (Book-Headings sind im Paragraph-JSON oft NICHT enthalten)
FOOTER_Y_RATIO = 0.85          # untere 15%: dort sitzt die Seitenzahl zuverlässig
HEADER_SCAN_Y_RATIO = 0.18     # obere 18%: Kandidaten für Running Header

#
# Optional: Seitenbereiche für den Hauptinhalt (ohne Vorspann/Anhang).
# WICHTIG: Jetzt ab Seite 7 starten, um Vorworte zu erfassen!
# Das Vorwort ist im JSON meist enthalten und sollte Seitenzahlen bekommen.
#
GA_PAGE_RANGES: Dict[str, Tuple[int, int]] = {
    "GA001": (7, 300),
    "GA002": (7, 180),
    "GA003": (7, 120),
    # GA004: Vorrede ist im JSON enthalten (S.7ff). Frontmatter (S.1-6) ist NICHT im JSON -> skippen
    "GA004": (7, 280),
    "GA005": (7, 200),
    "GA006": (7, 220),
    "GA007": (7, 160),
    "GA008": (7, 190),
    "GA009": (7, 200),
    "GA010": (7, 230),
    "GA011": (7, 260),
    "GA012": (7, 110),
    "GA013": (7, 460),
    "GA015": (7, 100),
    "GA016": (7, 120),
    "GA017": (7, 110),
    "GA018": (7, 700),
    "GA020": (7, 220),
    "GA021": (7, 200),
    "GA022": (7, 100),
    "GA023": (7, 180),
    "GA024": (7, 500),
    "GA025": (7, 110),
    "GA026": (7, 280),
    "GA027": (7, 160),
    "GA028": (7, 570),
    # GA045: Nach S.104 beginnt "Varianten ..." (nicht im JSON-Paragraph-Text) -> abschneiden
    "GA045": (7, 104),
}


class Confidence(Enum):
    EXTRACTED = "extracted"
    INTERPOLATED = "interpolated"


@dataclass
class PageMeta:
    pdf_index: int
    printed_page: Optional[int]
    printed_confidence: Confidence
    body_text: str


def normalize_ga(ga_arg: str) -> Optional[str]:
    m = re.search(r"(\d+[a-z]?)", ga_arg, re.IGNORECASE)
    if not m:
        return None
    return f"GA{m.group(1).zfill(3).upper()}"


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die PDF-Datei für eine GA-Nummer."""
    m = re.search(r"(\d+[a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    ga_num_str = m.group(1).zfill(3)
    ga_num_str_lower = ga_num_str.lower()

    for pdf_file in PDF_DIR.glob("*.pdf"):
        name_lower = pdf_file.name.lower()
        if f"ga {ga_num_str_lower}" in name_lower or f"ga{ga_num_str_lower}" in name_lower:
            return pdf_file
        ga_num_short = ga_num_str.lstrip("0") or "0"
        ga_num_short_lower = ga_num_short.lower()
        if f"ga {ga_num_short_lower}," in name_lower or f"ga {ga_num_short_lower} " in name_lower:
            return pdf_file
    return None


def extract_printed_page_from_footer(page: fitz.Page, max_page: int) -> Optional[int]:
    """Extrahiert gedruckte Seitenzahl aus dem unteren Bereich (sehr robust für GA-PDFs)."""
    page_height = page.rect.height
    blocks = page.get_text("blocks")

    def scan(threshold_ratio: float) -> List[Tuple[int, int, float]]:
        footer_threshold = page_height * threshold_ratio
        candidates: List[Tuple[int, int, float]] = []  # (num, priority, y_bottom)

        for block in blocks:
            if len(block) < 7 or block[6] != 0:
                continue
            y_bottom = float(block[3])
            text = (block[4] or "").strip()
            if not text:
                continue
            if y_bottom < footer_threshold:
                continue

            # Muster 1a: "Seite: X" (mit Doppelpunkt)
            m = re.search(r"Seite:\s*([\d\s]+)", text)
            if m:
                num_str = m.group(1).replace(" ", "").strip()
                if num_str.isdigit():
                    num = int(num_str)
                    if 1 <= num <= max_page:
                        candidates.append((num, 10, y_bottom))
                        continue
            
            # Muster 1b: "Seite X" (ohne Doppelpunkt) - für neuere GA-PDFs
            m = re.search(r"Seite\s+(\d+)", text)
            if m:
                num = int(m.group(1))
                if 1 <= num <= max_page:
                    candidates.append((num, 10, y_bottom))
                    continue

            # Muster 2: "- 123 -"
            m = re.search(r"[-–—]\s*(\d+)\s*[-–—]", text)
            if m:
                num = int(m.group(1))
                if 1 <= num <= max_page:
                    candidates.append((num, 8, y_bottom))
                    continue

            # Muster 3: Standalone-Zahl mit optionalen Klammern/Strichen/Punkt
            # WICHTIG: NICHT zu permissiv, sonst matcht es "1. Auflage" etc.
            compact = text.replace(" ", "")
            if re.fullmatch(r"[\(\[\{<]*\d{1,4}[\)\]\}>]*[.\-–—,:;!]*", compact):
                num = int(re.search(r"\d{1,4}", compact).group(0))
                # Jahreszahlen vermeiden
                if 1 <= num <= max_page and num < 1000:
                    candidates.append((num, 5, y_bottom))

        return candidates

    # Versuch 1: sehr unten (untere 15%)
    candidates = scan(0.85)
    # Versuch 2 (Fallback): etwas höher (untere 25%) für PDFs mit höher gesetzter Fußzeile
    if not candidates:
        candidates = scan(0.75)

    if not candidates:
        # Fallback 3: Plain-Text tail (manche PDFs liefern Footer-Zahlen nicht als Block)
        try:
            txt = page.get_text("text") or ""
        except Exception:
            txt = ""
        if txt:
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            tail = lines[-10:]
            for ln in reversed(tail):
                # "Seite: 12" oder "Seite 12"
                m = re.search(r"Seite:?\s*(\d{1,4})\s*$", ln)
                if m:
                    num = int(m.group(1))
                    if 1 <= num <= max_page:
                        return num
                # "- 123 -" / "123" / "123."
                m = re.fullmatch(r"[-–—]?\s*(\d{1,4})\s*[-–—]?\s*\.?\s*", ln)
                if m:
                    num = int(m.group(1))
                    if 1 <= num <= max_page and num < 1000:
                        return num
        return None

    candidates.sort(key=lambda c: (-c[1], -c[2]))
    return candidates[0][0]


def _normalize_header_candidate(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\d+", "", s)  # Zahlen raus
    return s.strip().lower()


def _is_likely_heading_line(line: str) -> bool:
    """
    Heuristik: Kopf-/Kapitelzeilen in ALL CAPS, kurze Titelzeilen etc.
    Diese sind im Paragraph-JSON oft NICHT enthalten -> überspringen.
    """
    if not line:
        return False
    t = line.strip()
    if len(t) < 4:
        return True
    upper = t.upper()
    if upper.startswith(("INHALT", "INHALTSVERZEICHNIS", "HINWEISE", "ANHANG")):
        return True
    if len(t) <= 90 and t == upper and any(c.isalpha() for c in t):
        if not t.endswith((".", ",", ";", ":", "!", "?")):
            return True
    return False


def build_header_skip_set(doc: fitz.Document) -> Set[str]:
    """
    Erkennt Running Headers über Wiederholung in den oberen ~18% der Seite.
    Gibt Set normalisierter Zeilen zurück, die übersprungen werden sollen.
    """
    counts: Dict[str, int] = {}
    total = len(doc)

    for i in range(total):
        page = doc[i]
        h = float(page.rect.height)
        header_y = h * HEADER_SCAN_Y_RATIO
        blocks = page.get_text("blocks")

        candidates: List[str] = []
        for b in blocks:
            if len(b) < 7 or b[6] != 0:
                continue
            y_top = float(b[1])
            if y_top > header_y:
                continue
            txt = (b[4] or "").strip()
            if not txt:
                continue
            first_line = txt.splitlines()[0].strip()
            if not first_line:
                continue
            if first_line.replace(" ", "").isdigit():
                continue
            if re.match(r"^Seite:\s*\d+", first_line):
                continue
            cand = _normalize_header_candidate(first_line)
            if 6 <= len(cand) <= 70:
                candidates.append(cand)

        for c in set(candidates[:2]):
            counts[c] = counts.get(c, 0) + 1

    skip: Set[str] = set()
    for k, v in counts.items():
        # häufig wiederkehrend -> Running Header
        if v >= 12 and v / max(total, 1) >= 0.08:
            skip.add(k)
    return skip


def extract_body_text(page: fitz.Page, header_skip: Optional[Set[str]] = None) -> str:
    """
    Extrahiert Fließtext in Reading-Order, entfernt Footer (Seitenzahlen) und
    Running Headers (via header_skip) sowie "Überschriften"-Zeilen.
    """
    header_skip = header_skip or set()
    h = float(page.rect.height)
    footer_y = h * FOOTER_Y_RATIO

    blocks = page.get_text("blocks")
    kept: List[Tuple[float, float, str]] = []  # (y_top, x_left, line)

    for b in blocks:
        if len(b) < 7 or b[6] != 0:
            continue
        x0 = float(b[0])
        y0 = float(b[1])
        y1 = float(b[3])
        txt = (b[4] or "").strip()
        if not txt:
            continue

        # Footer-Bereich: nur dann skippen, wenn es wie Seitenzahl aussieht
        if y0 >= footer_y:
            if txt.replace(" ", "").isdigit() or re.match(r"^Seite:\s*\d+", txt):
                continue
            if len(txt) <= 12 and re.search(r"\b\d{1,4}\b", txt):
                continue

        # Copyright etc.
        if "Copyright" in txt or "Buch:" in txt:
            continue

        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.replace(" ", "").isdigit():
                continue
            if re.match(r"^Seite:\s*\d+", line):
                continue

            norm_line = _normalize_header_candidate(line)
            if norm_line in header_skip:
                continue
            if _is_likely_heading_line(line):
                continue

            kept.append((y0, x0, line))

    kept.sort(key=lambda t: (t[0], t[1]))
    joined = " ".join(x[2] for x in kept)
    joined = re.sub(r"\s+", " ", joined).strip()

    # Entferne häufige PDF-/Editor-Artefakte wie "[34]" (Querverweise),
    # die im JSON-Text meist nicht enthalten sind und das Matching stören.
    joined = re.sub(r"\s*\[\d{1,3}\]\s*", " ", joined)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined


def interpolate_printed_pages(pages: List[PageMeta]) -> List[PageMeta]:
    """
    Füllt fehlende printed_page linear zwischen erkannten Ankerpunkten.
    """
    anchors: List[Tuple[int, int]] = [(i, p.printed_page) for i, p in enumerate(pages) if p.printed_page is not None]
    if not anchors:
        return pages

    # Vorwärts/zwischen Ankern auffüllen
    for i, p in enumerate(pages):
        if p.printed_page is not None:
            continue

        prev = None
        nxt = None
        for ai, ap in anchors:
            if ai < i:
                prev = (ai, ap)
            elif ai > i and nxt is None:
                nxt = (ai, ap)
                break

        if prev and nxt:
            pi, pp = prev
            ni, np = nxt
            offset = i - pi
            guess = pp + offset
        elif prev:
            pi, pp = prev
            guess = pp + (i - pi)
        elif nxt:
            ni, np = nxt
            guess = np - (ni - i)
        else:
            guess = i + 1

        pages[i] = PageMeta(
            pdf_index=p.pdf_index,
            printed_page=guess,
            printed_confidence=Confidence.INTERPOLATED,
            body_text=p.body_text,
        )

    return pages


def load_json_content_for_ga(ga_number: str) -> Optional[str]:
    """
    Lädt den gesamten Text-Content (Buch oder Vorträge) für eine GA aus steiner-*.json.
    (wie im v2-Skript, aber minimal, nur für optionale Validierung/Debug).
    """
    m = re.search(r"(\d+[a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    ga_pattern = f"GA{m.group(1).zfill(3).upper()}"

    parts: List[str] = []
    for jf in SCRIPT_DIR.glob("steiner-*.json"):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "lectures" in data:
                for lec in data["lectures"]:
                    if (lec.get("gaNumber") or "").upper() == ga_pattern:
                        title = lec.get("title") or ""
                        if title:
                            parts.append(title)
                        for para in lec.get("paragraphs", []):
                            parts.append(para.get("content", "") or "")

            if "books" in data:
                for book in data["books"]:
                    if (book.get("ID") or "").upper() == ga_pattern:
                        title = book.get("title") or ""
                        if title:
                            parts.append(title)
                        parts.append(book.get("content", "") or "")
        except Exception:
            continue

    return "\n\n".join(parts).strip() if parts else None


def normalize_text_for_search(s: str) -> str:
    """
    Minimale Normalisierung für Validierung:
    - Whitespace vereinheitlichen
    - typografische Anführungszeichen/Ligaturen nicht anfassen (nur Basis)
    - alte Rechtschreibung (daß->dass) optional
    """
    s = s.replace("daß", "dass").replace("Daß", "Dass")
    s = s.replace("\u00ad", "")  # soft hyphen
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def load_existing_output() -> Dict:
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "_info": (
            "Page-Break Anchors V4: Pro Umbruch wird (left,right) gespeichert. "
            "page = gedruckte Seitenzahl der NÄCHSTEN Seite (Beginn nach dem Umbruch). "
            "Diese Datei ersetzt NICHT page-markers.json; sie ist ein separates, robusteres Format."
        )
    }


def save_output(data: Dict) -> None:
    sorted_data: Dict = {"_info": data.get("_info", "")}
    ga_keys = sorted(k for k in data.keys() if k.startswith("GA"))
    for k in ga_keys:
        sorted_data[k] = data[k]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Gespeichert in: {OUTPUT_FILE}")


def build_breaks_for_ga(ga_number: str, validate: bool = False) -> Optional[Dict]:
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        print("FEHLER: Ungültige GA-Nummer")
        return None

    pdf_path = find_pdf_for_ga(ga_number)
    if not pdf_path:
        print(f"FEHLER: Keine PDF gefunden für {ga_norm}")
        return None

    print(f"\n{'='*60}\nVerarbeite: {ga_norm}\n{'='*60}")
    print(f"  PDF: {pdf_path.name}")

    doc = fitz.open(pdf_path)
    pdf_page_count = len(doc)
    max_page = min(pdf_page_count + 100, 1200)

    # Running Header erkennen (global über Dokument)
    header_skip = build_header_skip_set(doc)

    # Content-Range (falls bekannt)
    content_start, content_end = GA_PAGE_RANGES.get(ga_norm, (1, 10_000))
    if ga_norm in GA_PAGE_RANGES:
        print(f"  Hauptinhalt: Seite {content_start}–{content_end} (Range-Filter aktiv)")

    pages: List[PageMeta] = []
    extracted = 0
    for i in range(pdf_page_count):
        page = doc[i]
        printed = extract_printed_page_from_footer(page, max_page=max_page)
        conf = Confidence.EXTRACTED if printed is not None else Confidence.INTERPOLATED
        if printed is not None:
            extracted += 1

        body = extract_body_text(page, header_skip=header_skip)
        pages.append(PageMeta(pdf_index=i, printed_page=printed, printed_confidence=conf, body_text=body))

    doc.close()

    rate = (extracted / pdf_page_count * 100.0) if pdf_page_count else 0.0
    print(f"  PDF-Seiten: {pdf_page_count}, erkannte gedruckte Seiten: {extracted} ({rate:.1f}%)")

    # Fallback: Wenn überhaupt keine Seitenzahlen extrahiert werden konnten,
    # nutze PDF-Seitenindex als Seitenzahl (1-basiert). Das ist nicht perfekt,
    # aber ermöglicht ein reproduzierbares Ergebnis für PDFs ohne text-extrahierbare Footer.
    if extracted == 0 and pdf_page_count > 0:
        print("  ⚠️  Keine Seitenzahlen im Footer erkannt – verwende PDF-Seitennummern als Fallback")
        pages = [
            PageMeta(
                pdf_index=p.pdf_index,
                printed_page=p.pdf_index + 1,
                printed_confidence=Confidence.INTERPOLATED,
                body_text=p.body_text,
            )
            for p in pages
        ]

    pages = interpolate_printed_pages(pages)

    # Umbruchliste erstellen: Break zwischen i und i+1 => page = printed_page von i+1
    breaks = []
    
    # NEUER CODE: Allererster Textbeginn (firstPage) - nur "right", kein "left"
    # Finde die erste Seite im Content-Range mit Text
    first_page_entry = None
    for p in pages:
        if p.printed_page is not None and content_start <= p.printed_page <= content_end:
            if p.body_text and len(p.body_text.strip()) > 50:
                right = p.body_text[:RIGHT_CHARS] if len(p.body_text) > RIGHT_CHARS else p.body_text
                first_page_entry = {
                    "page": int(p.printed_page),
                    "pdfFrom": None,  # Keine vorherige Seite
                    "pdfTo": int(p.pdf_index),
                    "left": None,  # Kein Text davor
                    "right": right,
                    "hyphenated": False,
                    "printedPageConfidence": p.printed_confidence.value,
                    "isFirstPage": True,  # Markierung für allerersten Textbeginn
                }
                print(f"  Erste Textseite erkannt: Seite {p.printed_page} (PDF-Index {p.pdf_index})")
                break
    
    if first_page_entry:
        breaks.append(first_page_entry)
    
    # Reguläre Breaks zwischen Seiten
    for i in range(pdf_page_count - 1):
        left_src = pages[i].body_text or ""
        right_src = pages[i + 1].body_text or ""
        if not left_src and not right_src:
            continue

        left = left_src[-LEFT_CHARS:] if len(left_src) > LEFT_CHARS else left_src
        right = right_src[:RIGHT_CHARS] if len(right_src) > RIGHT_CHARS else right_src

        # Hyphenation am Seitenende erkennen (häufig: '-' oder '¬')
        left_trim = left.rstrip()
        hyphenated = bool(left_trim) and left_trim[-1] in {"-", "¬", "–"}

        next_page = pages[i + 1].printed_page
        if next_page is None:
            continue

        # Filter auf Hauptinhalt (falls Range bekannt)
        if not (content_start <= int(next_page) <= content_end):
            continue
        
        # Überspringe, wenn dies dieselbe Seite wie firstPage ist (vermeidet Duplikat)
        if first_page_entry and int(next_page) == first_page_entry["page"]:
            continue

        breaks.append(
            {
                "page": int(next_page),
                "pdfFrom": int(i),       # 0-based
                "pdfTo": int(i + 1),     # 0-based
                "left": left,
                "right": right,
                "hyphenated": hyphenated,
                "printedPageConfidence": pages[i + 1].printed_confidence.value,
            }
        )

    # Optional: grobe Validierung (nur als Report, kein hartes Abbrechen)
    if validate:
        content = load_json_content_for_ga(ga_norm)
        if not content:
            print("  VALIDIERUNG: Kein JSON-Content gefunden (steiner-*.json) – übersprungen")
        else:
            norm_content = normalize_text_for_search(content)
            ok = 0
            checked = 0
            for b in breaks:
                l = normalize_text_for_search(b["left"])
                r = normalize_text_for_search(b["right"])
                # Nimm robuste Teilstücke (Ende von left, Anfang von right)
                l_tail = l[-70:] if len(l) > 70 else l
                r_head = r[:70] if len(r) > 70 else r
                if len(l_tail) < 25 or len(r_head) < 25:
                    continue
                checked += 1

                # Robustere Prüfung als exakte Naht: finde left im JSON, dann right in Nähe
                l_pos = norm_content.find(l_tail)
                if l_pos >= 0:
                    window_start = max(0, l_pos - 50)
                    window_end = min(len(norm_content), l_pos + len(l_tail) + 800)
                    window = norm_content[window_start:window_end]
                    if r_head in window:
                        ok += 1
                        continue

                # Hyphenation-Fallback: trailing '-' entfernen (wenn das Ende im PDF getrennt war)
                if l_tail.endswith("-"):
                    l2 = l_tail[:-1]
                    l_pos2 = norm_content.find(l2)
                    if l_pos2 >= 0:
                        window_start = max(0, l_pos2 - 50)
                        window_end = min(len(norm_content), l_pos2 + len(l2) + 800)
                        window = norm_content[window_start:window_end]
                        if r_head in window:
                            ok += 1

            if checked:
                print(f"  VALIDIERUNG: {ok}/{checked} Nahtstellen direkt gefunden ({(ok/checked*100):.1f}%)")
            else:
                print("  VALIDIERUNG: Keine ausreichend langen Nahtstellen zum Prüfen")

    title_match = re.search(r" - (.+)\.pdf$", pdf_path.name)
    title = title_match.group(1) if title_match else ga_norm

    print(f"  Breaks erzeugt: {len(breaks)}")
    if breaks:
        print(f"  Beispiel: page={breaks[0]['page']} (pdf {breaks[0]['pdfFrom']}→{breaks[0]['pdfTo']})")

    return {
        "title": title,
        "pdfSource": pdf_path.name,
        "pdfPageCount": pdf_page_count,
        "contentRange": [int(content_start), int(content_end)],
        "breaks": breaks,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Export Page Markers V4 (Page-Break Anchors)")
        print("Verwendung:")
        print("  python export_page_markers_v4.py GA004")
        print("  python export_page_markers_v4.py --validate GA004")
        sys.exit(1)

    validate = "--validate" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("FEHLER: Keine GA-Nummer angegeben")
        sys.exit(1)

    out = load_existing_output()
    for ga_arg in args:
        ga_norm = normalize_ga(ga_arg)
        if not ga_norm:
            print(f"Ungültige GA-Nummer: {ga_arg}")
            continue
        result = build_breaks_for_ga(ga_norm, validate=validate)
        if result:
            out[ga_norm] = result

    save_output(out)


if __name__ == "__main__":
    main()


