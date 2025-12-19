#!/usr/bin/env python3
"""
Generate Lecture Page Mapping

Erstellt ein Mapping: Vortrag-ID → Start-Seitenzahl im PDF

Workflow:
1. Lädt Vorträge aus steiner-full-lectures-*.json
2. Öffnet das entsprechende PDF
3. Sucht die ersten 1000 Zeichen jedes Vortrags im PDF-Text (um False Positives bei langen Zitaten zu vermeiden)
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
    """
    Findet die PDF-Datei für eine GA-Nummer.
    Bevorzugt "_einzelseiten" PDFs (für aufgeteilte Doppelseiten-Scans).
    """
    m = re.search(r"(\d+[a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    ga_num_str = m.group(1).zfill(3)
    ga_num_str_lower = ga_num_str.lower()
    ga_num_short = ga_num_str.lstrip("0") or "0"
    ga_num_short_lower = ga_num_short.lower()

    candidates = []
    for pdf_file in PDF_DIR.glob("*.pdf"):
        name_lower = pdf_file.name.lower()
        if f"ga {ga_num_str_lower}" in name_lower or f"ga{ga_num_str_lower}" in name_lower:
            candidates.append(pdf_file)
        elif f"ga {ga_num_short_lower}," in name_lower or f"ga {ga_num_short_lower} " in name_lower:
            candidates.append(pdf_file)
    
    if not candidates:
        return None
    
    # Bevorzuge "_einzelseiten" PDFs (aufgeteilte Doppelseiten)
    for c in candidates:
        if "_einzelseiten" in c.name.lower():
            return c
    
    # Sonst: erstes gefundenes PDF (aber nicht "_DOPPELSEITEN" Backups)
    for c in candidates:
        if "_doppelseiten" not in c.name.lower():
            return c
    
    return candidates[0]


def iter_steiner_lectures_files() -> List[Path]:
    """Findet alle steiner-full-lectures-*.json Dateien."""
    lectures_dir = SCRIPT_DIR / "steiner-full-lectures"
    if lectures_dir.exists():
        return sorted(lectures_dir.glob("steiner-full-lectures-*.json"))
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


def load_page_breaks(ga_number: str) -> Dict[int, int]:
    """
    Lädt die Seitenzahlen aus page-break-markers.json.
    Rückgabe: Dict von PDF-Index → gedruckte Seitenzahl
    """
    markers_file = SCRIPT_DIR / "page-break-markers.json"
    if not markers_file.exists():
        return {}
    
    try:
        with open(markers_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        ga_data = data.get(ga_number.upper(), {})
        breaks = ga_data.get("breaks", [])
        
        # Baue Mapping: PDF-Index → Seitenzahl
        # WICHTIG: Verwende pdfTo als PDF-Index, nicht den Listenindex!
        result = {}
        for b in breaks:
            pdf_to = b.get("pdfTo")
            page = b.get("page", 0)
            if pdf_to is not None and page > 0:
                result[pdf_to] = page
        return result
    except Exception:
        return {}


def extract_page_texts(pdf_path: Path, ga_number: str = "") -> List[Tuple[int, int, str]]:
    """
    Extrahiert den Text jeder Seite aus dem PDF.
    Verwendet Seitenzahlen aus page-break-markers.json falls vorhanden.
    Rückgabe: Liste von (PDF-Index, Seitenzahl, Text)
    """
    # Versuche Seitenzahlen aus page-break-markers.json zu laden
    precomputed = load_page_breaks(ga_number) if ga_number else {}
    
    doc = fitz.open(pdf_path)
    page_texts: List[Tuple[int, int, str]] = []
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        # Verwende vorberechnete Seitenzahl falls vorhanden
        if i in precomputed:
            page_num = precomputed[i]
        else:
            # Fallback: Versuche Seitenzahl aus Footer zu extrahieren
            page_num = extract_page_number(page, i, len(doc))
        
        if page_num and text.strip():
            page_texts.append((i, page_num, text))
    
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
    page_texts: List[Tuple[int, int, str]],
    min_pdf_index: int = 0,
    max_pdf_index: Optional[int] = None
) -> Optional[Tuple[int, int]]:
    """
    Findet die Start-Seitenzahl eines Vortrags im PDF.
    
    min_pdf_index: Minimaler PDF-Index (für Monotonie-Erzwingung)
    max_pdf_index: Maximaler PDF-Index (optional)
    
    Rückgabe: (PDF-Index, Seitenzahl) oder None
    
    Strategie: Suche sequentiell durch das PDF (nach PDF-Index, nicht Seitenzahl!)
    """
    paragraphs = lecture.get("paragraphs") or []
    if not paragraphs:
        return None
    
    # Finde den ersten ECHTEN Fließtext-Absatz (nicht Metadaten, nicht Überschriften)
    # WICHTIG: Überschriften/Titel können auch im Inhaltsverzeichnis vorkommen!
    # Daher brauchen wir einen LÄNGEREN Text (>150 Zeichen) für zuverlässiges Matching.
    first_para_norm = ""
    collected_paras = []
    
    for i, para in enumerate(paragraphs[:15]):
        content = para.get("content") or para.get("text") or ""
        normalized = normalize_text(content)
        
        if len(normalized) < 30:
            continue
        if re.match(r"^(manuskript|fragment|undatiert|um\s*\d{4}|ca\s*\d{4}|\d{4})", normalized, re.IGNORECASE):
            continue
        if re.fullmatch(r"[ivxlcdm]+\.?|[a-z]\.?", normalized, re.IGNORECASE):
            continue
        
        # Sammle Absätze bis wir mindestens 200 Zeichen haben
        collected_paras.append(normalized)
        combined = " ".join(collected_paras)
        
        # Prüfe ob wir genug Text haben (mindestens 200 Zeichen)
        # UND ob es echter Fließtext ist (enthält Satzzeichen wie . , ; :)
        if len(combined) >= 200:
            # Prüfe auf Fließtext-Merkmale (Satzzeichen)
            has_punctuation = any(p in combined for p in ['. ', ', ', '; ', ': '])
            if has_punctuation:
                first_para_norm = combined
                break
    
    # Fallback: Wenn keine 200 Zeichen mit Satzzeichen, nimm was wir haben
    if not first_para_norm and collected_paras:
        first_para_norm = " ".join(collected_paras)
    
    if len(first_para_norm) < 80:
        return None
    
    search_text = first_para_norm[:1000]
    
    # Suche sequentiell durch das PDF (nach PDF-Index!)
    for pdf_idx, page_num, page_text in page_texts:
        if pdf_idx < min_pdf_index:
            continue
        if max_pdf_index and pdf_idx > max_pdf_index:
            continue
        
        page_norm = normalize_text(page_text)
        if not page_norm:
            continue
        
        # Exakte Teilstring-Suche
        # WICHTIG: Mindestens 150 Zeichen verwenden, um Inhaltsverzeichnis-Treffer zu vermeiden!
        for search_len in [800, 600, 400, 300, 250, 200, 150]:
            if search_len > len(search_text):
                continue
            search_key = search_text[:search_len]
            if search_key in page_norm:
                return (pdf_idx, page_num)
    
    # Fallback: Fuzzy-Matching
    best_match: Optional[Tuple[float, int, int]] = None
    for pdf_idx, page_num, page_text in page_texts:
        if pdf_idx < min_pdf_index:
            continue
        if max_pdf_index and pdf_idx > max_pdf_index:
            continue
        
        page_norm = normalize_text(page_text)
        if not page_norm:
            continue
        
        compare_len = min(150, len(search_text))
        if compare_len >= 40:
            step = 50
            for start in range(0, max(1, len(page_norm) - compare_len), step):
                window = page_norm[start:start + compare_len]
                ratio = SequenceMatcher(None, search_text[:compare_len], window).ratio()
                if ratio > 0.80:
                    if best_match is None or ratio > best_match[0]:
                        best_match = (ratio, pdf_idx, page_num)
    
    if best_match and best_match[0] > 0.80:
        return (best_match[1], best_match[2])
    
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
    
    # PDF-Seiten extrahieren (mit Seitenzahlen aus page-break-markers.json)
    print(f"  Extrahiere PDF-Texte...")
    page_texts = extract_page_texts(pdf_path, ga_norm)
    print(f"  Seiten mit Text: {len(page_texts)}")
    
    # Mapping erstellen - OHNE Monotonie-Erzwingung!
    # Jeder Vortrag wird unabhängig im gesamten PDF gesucht.
    # (Reihenfolge im JSON kann von Reihenfolge im PDF abweichen)
    mapping: Dict[str, int] = {}
    found = 0
    not_found = 0
    
    for i, lecture in enumerate(lectures):
        lec_id = lecture.get("ID") or f"{ga_norm}/{i+1}"
        lec_title = (lecture.get("title") or "")[:50]
        
        # Suche im gesamten PDF (ohne Monotonie-Einschränkung)
        result = find_lecture_in_pdf(lecture, page_texts, min_pdf_index=0)
        
        if result:
            pdf_idx, page_num = result
            mapping[lec_id] = page_num
            found += 1
            print(f"  ✓ {lec_id}: Seite {page_num} - {lec_title}")
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
