#!/usr/bin/env python3
"""
Generate Lecture Page Mapping

Erstellt ein Mapping: Vortrag-ID → Start-Seitenzahl im PDF

Workflow:
1. Lädt Vorträge aus steiner-full-lectures-*.json
2. Öffnet das entsprechende PDF
3. Sucht die ersten 200 Zeichen jedes Vortrags im PDF-Text
4. Speichert das Mapping in lecture-page-mapping.json

Verwendung:
  python generate_lecture_page_mapping.py GA030
  python generate_lecture_page_mapping.py --all
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

import fitz  # PyMuPDF

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = SCRIPT_DIR / "lecture-page-mapping.json"

# Ligaturen für Normalisierung
LIGATURES = {
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    "ﬅ": "st", "ﬆ": "st", "Ꜳ": "AA", "ꜳ": "aa", "Æ": "AE", "æ": "ae",
    "Œ": "OE", "œ": "oe",
}


def normalize_text(text: str) -> str:
    """Normalisiert Text für Matching."""
    if not text:
        return ""
    
    # HTML-Tags entfernen
    s = re.sub(r"<[^>]+>", " ", text)
    
    # Soft hyphen und nbsp entfernen
    s = s.replace("\u00ad", "").replace("\u00a0", " ")
    
    # Ligaturen expandieren
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    
    # Lowercase
    s = s.lower()
    
    # ß -> ss
    s = s.replace("ß", "ss")
    
    # Whitespace normalisieren
    s = re.sub(r"\s+", " ", s)
    
    return s.strip()


def normalize_ga(ga_arg: str) -> Optional[str]:
    """Normalisiert GA-Nummer."""
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


def iter_steiner_lectures_files() -> List[Path]:
    """Findet alle steiner-full-lectures-*.json Dateien."""
    return sorted(SCRIPT_DIR.glob("steiner-full-lectures-*.json"))


def load_lectures_for_ga(ga_number: str) -> List[Dict]:
    """Lädt alle Vorträge für eine GA-Nummer."""
    ga_upper = ga_number.upper()
    all_lectures: List[Dict] = []
    seen_ids: set = set()
    
    for path in iter_steiner_lectures_files():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lectures = data.get("lectures") or []
            for lec in lectures:
                if (lec.get("gaNumber") or "").upper() == ga_upper:
                    lec_id = lec.get("ID") or lec.get("title") or ""
                    if lec_id not in seen_ids:
                        seen_ids.add(lec_id)
                        all_lectures.append(lec)
        except Exception:
            continue
    
    # Sortiere nach lectureNumber
    all_lectures.sort(key=lambda x: int(x.get("lectureNumber") or 0))
    return all_lectures


def extract_page_texts(pdf_path: Path) -> List[Tuple[int, str]]:
    """
    Extrahiert den Text jeder Seite aus dem PDF.
    Rückgabe: Liste von (Seitenzahl, Text)
    """
    doc = fitz.open(pdf_path)
    page_texts: List[Tuple[int, str]] = []
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        # Versuche Seitenzahl aus Footer zu extrahieren
        page_num = extract_page_number(page, i, len(doc))
        
        if page_num and text.strip():
            page_texts.append((page_num, text))
    
    doc.close()
    return page_texts


def extract_page_number(page: fitz.Page, pdf_index: int, total_pages: int) -> Optional[int]:
    """Extrahiert die gedruckte Seitenzahl aus dem Footer."""
    page_height = page.rect.height
    blocks = page.get_text("blocks")
    max_page = min(total_pages + 100, 1200)
    
    footer_threshold = page_height * 0.85
    candidates: List[Tuple[int, int, float]] = []
    
    for block in blocks:
        if len(block) < 7 or block[6] != 0:
            continue
        y_bottom = float(block[3])
        text = (block[4] or "").strip()
        if not text or y_bottom < footer_threshold:
            continue
        
        # Muster: "Seite: X"
        m = re.search(r"Seite:\s*([\d\s]+)", text)
        if m:
            num_str = m.group(1).replace(" ", "").strip()
            if num_str.isdigit():
                num = int(num_str)
                if 1 <= num <= max_page:
                    candidates.append((num, 10, y_bottom))
                    continue
        
        # Muster: "- 123 -"
        m = re.search(r"[-–—]\s*(\d+)\s*[-–—]", text)
        if m:
            num = int(m.group(1))
            if 1 <= num <= max_page:
                candidates.append((num, 8, y_bottom))
                continue
        
        # Muster: Standalone-Zahl
        compact = text.replace(" ", "")
        if re.fullmatch(r"[\(\[\{<]*\d{1,4}[\)\]\}>]*[.\-–—,:;!]*", compact):
            num = int(re.search(r"\d{1,4}", compact).group(0))
            if 1 <= num <= max_page and num < 1000:
                candidates.append((num, 5, y_bottom))
    
    if candidates:
        candidates.sort(key=lambda c: (-c[1], -c[2]))
        return candidates[0][0]
    
    # Fallback: PDF-Index + 1
    return pdf_index + 1


def find_lecture_in_pdf(
    lecture: Dict, 
    page_texts: List[Tuple[int, str]],
    min_page: int = 1
) -> Optional[int]:
    """
    Findet die Start-Seitenzahl eines Vortrags im PDF.
    
    Sucht die ersten 200 Zeichen des ersten Absatzes im PDF-Text.
    """
    paragraphs = lecture.get("paragraphs") or []
    if not paragraphs:
        return None
    
    # Nimm den ersten Absatz
    first_para = paragraphs[0].get("content") or ""
    first_para_norm = normalize_text(first_para)
    
    if len(first_para_norm) < 30:
        # Versuche nächsten Absatz
        if len(paragraphs) > 1:
            first_para = paragraphs[1].get("content") or ""
            first_para_norm = normalize_text(first_para)
    
    if len(first_para_norm) < 30:
        return None
    
    # Verwende die ersten 200 Zeichen für die Suche
    search_text = first_para_norm[:200]
    
    best_match: Optional[Tuple[float, int]] = None
    
    for page_num, page_text in page_texts:
        if page_num < min_page:
            continue
        
        page_norm = normalize_text(page_text)
        if not page_norm:
            continue
        
        # Methode 1: Exakte Teilstring-Suche mit verschiedenen Längen
        for search_len in [150, 120, 100, 80, 60, 40]:
            if search_len > len(search_text):
                continue
            search_key = search_text[:search_len]
            if search_key in page_norm:
                return page_num
        
        # Methode 2: Fuzzy-Matching
        # Suche das beste Match im Seitentext
        compare_len = min(100, len(search_text))
        if compare_len >= 40:
            # Sliding Window über den Seitentext
            step = 50
            for start in range(0, max(1, len(page_norm) - compare_len), step):
                window = page_norm[start:start + compare_len]
                ratio = SequenceMatcher(None, search_text[:compare_len], window).ratio()
                if ratio > 0.80:
                    if best_match is None or ratio > best_match[0]:
                        best_match = (ratio, page_num)
                    if ratio > 0.90:
                        return page_num
    
    # Rückgabe des besten Fuzzy-Matches
    if best_match and best_match[0] > 0.80:
        return best_match[1]
    
    return None


def generate_mapping_for_ga(ga_number: str) -> Dict[str, int]:
    """
    Generiert das Mapping für eine GA-Nummer.
    Rückgabe: Dict von Vortrag-ID → Seitenzahl
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        print(f"FEHLER: Ungültige GA-Nummer: {ga_number}")
        return {}
    
    # PDF finden
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print(f"FEHLER: Keine PDF gefunden für {ga_norm}")
        return {}
    
    # Vorträge laden
    lectures = load_lectures_for_ga(ga_norm)
    if not lectures:
        print(f"FEHLER: Keine Vorträge gefunden für {ga_norm}")
        return {}
    
    print(f"\n{'='*60}")
    print(f"Generiere Mapping für {ga_norm}")
    print(f"{'='*60}")
    print(f"  PDF: {pdf_path.name}")
    print(f"  Vorträge: {len(lectures)}")
    
    # PDF-Seiten extrahieren
    print(f"  Extrahiere PDF-Texte...")
    page_texts = extract_page_texts(pdf_path)
    print(f"  Seiten mit Text: {len(page_texts)}")
    
    # Mapping erstellen
    mapping: Dict[str, int] = {}
    found = 0
    not_found = 0
    
    for i, lecture in enumerate(lectures):
        lec_id = lecture.get("ID") or f"{ga_norm}/{i+1}"
        lec_title = (lecture.get("title") or "")[:50]
        
        page = find_lecture_in_pdf(lecture, page_texts)
        
        if page:
            mapping[lec_id] = page
            found += 1
            print(f"  ✓ {lec_id}: Seite {page} - {lec_title}")
        else:
            not_found += 1
            print(f"  ✗ {lec_id}: NICHT GEFUNDEN - {lec_title}")
    
    print(f"\n  Ergebnis: {found}/{len(lectures)} gefunden ({found/len(lectures)*100:.1f}%)")
    
    return mapping


def load_existing_mapping() -> Dict:
    """Lädt bestehendes Mapping."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"_info": "Lecture-ID → Start-Seitenzahl im PDF"}


def save_mapping(data: Dict) -> None:
    """Speichert das Mapping."""
    sorted_data: Dict = {"_info": data.get("_info", "")}
    ga_keys = sorted(k for k in data.keys() if k.startswith("GA"))
    for k in ga_keys:
        sorted_data[k] = data[k]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Gespeichert in: {OUTPUT_FILE}")


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python generate_lecture_page_mapping.py GA030")
        print("            python generate_lecture_page_mapping.py --all")
        sys.exit(1)
    
    existing = load_existing_mapping()
    
    if sys.argv[1] == "--all":
        # Alle Vortrags-GAs verarbeiten
        # TODO: Liste der Vortrags-GAs
        print("--all noch nicht implementiert")
        sys.exit(1)
    else:
        ga = sys.argv[1]
        ga_norm = normalize_ga(ga)
        if not ga_norm:
            print(f"FEHLER: Ungültige GA-Nummer: {ga}")
            sys.exit(1)
        
        mapping = generate_mapping_for_ga(ga)
        if mapping:
            existing[ga_norm] = mapping
            save_mapping(existing)


if __name__ == "__main__":
    main()
