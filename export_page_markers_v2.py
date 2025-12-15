#!/usr/bin/env python3
"""
Export Page Markers V2 - Robuste Seitenzahl-Extraktion

Neuer Ansatz:
1. Extrahiere ALLE Seiten der PDF mit ihrem ersten Textblock
2. Extrahiere die Seitenzahl aus der Fußzeile (wo möglich)
3. Ergänze fehlende Seitenzahlen durch lineare Interpolation
4. Suche jeden beforeText im JSON-Content
5. Erstelle eine lückenlose Seitenmarker-Sequenz

Vorteile:
- Seitenumbrüche sind 100% zuverlässig (PDF-Seiten)
- Fehlende Fußzeilen-Seitenzahlen werden interpoliert
- Lückenlose Nummerierung garantiert

Verwendung:
    python export_page_markers_v2.py GA051
    python export_page_markers_v2.py --test GA051
"""

import fitz  # PyMuPDF
import re
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# Konfiguration
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = Path("page-markers.json")
SCRIPT_DIR = Path(__file__).parent

# beforeText Länge
BEFORE_TEXT_MIN = 20
BEFORE_TEXT_MAX = 60


@dataclass
class PageInfo:
    """Information über eine PDF-Seite."""
    pdf_index: int
    printed_page: Optional[int]  # Seitenzahl aus Fußzeile (kann None sein)
    first_text: str  # Erster Textblock der Seite
    all_texts: List[str]  # Alle Textblöcke (für Fallback bei Überschriften)
    is_content_page: bool  # True wenn Hauptinhalt (nicht Vorwort etc.)


def extract_page_number_from_footer(page_text: str) -> Optional[int]:
    """
    Extrahiert die gedruckte Seitenzahl aus der Fußzeile.
    Berücksichtigt auch Seitenzahlen mit Leerzeichen (z.B. "1 2 3" -> 123).
    """
    lines = page_text.strip().split('\n')
    
    # Prüfe die letzten Zeilen
    for line in reversed(lines[-5:]):
        line = line.strip()
        
        # Muster 1: "Seite: X" oder "Seite: 1 2 3"
        match = re.search(r'Seite:\s*([\d\s]+)', line)
        if match:
            num_str = match.group(1).replace(' ', '').strip()
            if num_str.isdigit():
                return int(num_str)
        
        # Muster 2: Nur Ziffern (evtl. mit Leerzeichen)
        clean_line = line.replace(' ', '')
        if clean_line.isdigit() and 1 <= len(clean_line) <= 4:
            return int(clean_line)
    
    return None


def get_text_blocks_of_page(page) -> List[str]:
    """
    Holt alle Textblöcke einer Seite (von oben nach unten sortiert).
    Ignoriert Kopfzeilen, Seitenzahlen, Copyright etc.
    
    Returns:
        Liste von Textblöcken, sortiert nach Y-Position
    """
    blocks = page.get_text("blocks")
    
    # Filtere Textblöcke (type 0 = Text)
    text_blocks = []
    for block in blocks:
        if len(block) >= 6 and block[6] == 0:  # block_type == 0 (Text)
            text = block[4].strip()
            
            # Ignoriere sehr kurze Blöcke
            if len(text) < 5:
                continue
            # Ignoriere reine Seitenzahlen
            if text.replace(' ', '').isdigit():
                continue
            # Ignoriere Copyright-Zeilen
            if 'Copyright' in text or 'Buch:' in text:
                continue
            if re.match(r'^Seite:\s*\d', text):
                continue
            
            text_blocks.append({
                'y': block[1],  # y0 Position
                'text': text
            })
    
    if not text_blocks:
        return []
    
    # Sortiere nach Y-Position (von oben nach unten)
    text_blocks.sort(key=lambda b: b['y'])
    
    return [b['text'] for b in text_blocks]


def get_first_text_of_page(page) -> Optional[str]:
    """
    Holt den ersten Textblock einer Seite (Text am OBEREN Rand).
    Wrapper für Kompatibilität.
    """
    blocks = get_text_blocks_of_page(page)
    return blocks[0] if blocks else None


def is_content_page(page_text: str, page_num: Optional[int], start_page: int = 1, end_page: int = 9999) -> bool:
    """
    Prüft ob eine Seite zum Hauptinhalt gehört.
    
    Vorspann (Inhaltsverzeichnis, Vorwort) und Anhang (Literaturverzeichnis)
    sind NICHT in den JSON-Dateien vorhanden und können daher nicht markiert werden.
    
    Args:
        page_text: Der Text der Seite
        page_num: Die gedruckte Seitenzahl
        start_page: Erste Seite des Hauptinhalts (Standard: 1)
        end_page: Letzte Seite des Hauptinhalts (Standard: 9999)
    """
    if page_num is None:
        return False
    
    # Prüfe ob im definierten Seitenbereich
    if page_num < start_page or page_num > end_page:
        return False
    
    return True


# Seitenbereiche für bekannte GA-Bände (Hauptinhalt, ohne Vorspann/Anhang/Hinweise)
# Format: "GAxxxx": (erste_seite, letzte_seite)
# - Vorspann (Inhaltsverzeichnis, Vorwort) ist NICHT im JSON
# - Alles nach "HINWEISE" ist NICHT im JSON
GA_PAGE_RANGES = {
    "GA001": (7, 300),      # Hauptinhalt beginnt auf Seite 7 (nach Vorwort/Inhaltsverzeichnis)
    "GA051": (18, 320),     # Hauptinhalt: Seite 18-320, HINWEISE beginnt auf 321
}


def extract_all_pages(pdf_path: Path, start_page: int = 1, end_page: int = 9999) -> List[PageInfo]:
    """
    Extrahiert Informationen über alle Seiten der PDF.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        start_page: Erste Seite des Hauptinhalts
        end_page: Letzte Seite des Hauptinhalts
    """
    doc = fitz.open(pdf_path)
    pages = []
    
    for pdf_idx in range(len(doc)):
        page = doc[pdf_idx]
        page_text = page.get_text()
        
        # Extrahiere Seitenzahl aus Fußzeile
        printed_page = extract_page_number_from_footer(page_text)
        
        # Extrahiere ALLE Textblöcke (für Fallback bei Überschriften)
        all_texts = get_text_blocks_of_page(page)
        
        if all_texts:
            pages.append(PageInfo(
                pdf_index=pdf_idx,
                printed_page=printed_page,
                first_text=all_texts[0],
                all_texts=all_texts,
                is_content_page=is_content_page(page_text, printed_page, start_page, end_page)
            ))
    
    doc.close()
    return pages


def interpolate_page_numbers(pages: List[PageInfo]) -> List[PageInfo]:
    """
    Ergänzt fehlende Seitenzahlen durch lineare Interpolation.
    
    Strategie:
    1. Finde Ankerpunkte (Seiten mit bekannter Seitenzahl)
    2. Interpoliere zwischen Ankerpunkten
    3. Extrapoliere am Anfang/Ende wenn nötig
    """
    if not pages:
        return pages
    
    # Sammle Ankerpunkte: (index in pages, printed_page)
    anchors = []
    for i, p in enumerate(pages):
        if p.printed_page is not None:
            anchors.append((i, p.printed_page))
    
    if not anchors:
        print("    WARNUNG: Keine Seitenzahlen gefunden!")
        return pages
    
    print(f"    Ankerpunkte: {len(anchors)} Seiten mit erkannter Seitenzahl")
    
    # Interpoliere
    result = []
    for i, page in enumerate(pages):
        if page.printed_page is not None:
            result.append(page)
            continue
        
        # Finde nächste Ankerpunkte vor und nach dieser Seite
        prev_anchor = None
        next_anchor = None
        
        for anchor_idx, anchor_page in anchors:
            if anchor_idx < i:
                prev_anchor = (anchor_idx, anchor_page)
            elif anchor_idx > i and next_anchor is None:
                next_anchor = (anchor_idx, anchor_page)
                break
        
        # Berechne interpolierte Seitenzahl
        if prev_anchor and next_anchor:
            # Zwischen zwei Ankern: lineare Interpolation
            prev_idx, prev_page = prev_anchor
            next_idx, next_page = next_anchor
            
            # Berechne Offset
            pages_between = next_idx - prev_idx
            page_diff = next_page - prev_page
            
            if pages_between > 0 and page_diff == pages_between:
                # Perfekte Sequenz - interpoliere
                offset = i - prev_idx
                interpolated = prev_page + offset
            else:
                # Unregelmäßig - verwende Distanz zum nächsten Anker
                offset = i - prev_idx
                interpolated = prev_page + offset
        
        elif prev_anchor:
            # Nur vorheriger Anker: extrapoliere vorwärts
            prev_idx, prev_page = prev_anchor
            offset = i - prev_idx
            interpolated = prev_page + offset
        
        elif next_anchor:
            # Nur nächster Anker: extrapoliere rückwärts
            next_idx, next_page = next_anchor
            offset = next_idx - i
            interpolated = next_page - offset
        
        else:
            # Sollte nicht passieren (anchors ist nicht leer)
            interpolated = i + 1
        
        # Erstelle neue PageInfo mit interpolierter Seitenzahl
        result.append(PageInfo(
            pdf_index=page.pdf_index,
            printed_page=interpolated,
            first_text=page.first_text,
            is_content_page=page.is_content_page
        ))
    
    return result


def normalize_for_matching(text: str) -> str:
    """Normalisiert Text für robusteren Vergleich."""
    text = text.replace('daß', 'dass').replace('Daß', 'Dass')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_before_text_in_content(first_text: str, content: str) -> Optional[str]:
    """
    Sucht den ersten Text der PDF-Seite im JSON-Content.
    Gibt einen beforeText zurück, der exakt im Content gefunden werden kann.
    """
    if not first_text or len(first_text) < 5:
        return None
    
    search_text = first_text.replace('\n', ' ').strip()
    
    # Strategie 1: Exakte Suche
    for length in range(min(len(search_text), 50), 10, -5):
        search_phrase = search_text[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content.find(search_phrase)
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # Strategie 2: Rechtschreibreform-normalisiert
    search_norm = normalize_for_matching(search_text)
    content_norm = normalize_for_matching(content)
    
    for length in range(min(len(search_norm), 50), 10, -5):
        search_phrase = search_norm[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content_norm.find(search_phrase)
        if idx >= 0:
            # Finde Position im Original
            original_idx = _find_original_position(content, content_norm, idx)
            return _extract_before_text(content, original_idx, len(search_phrase))
    
    # Strategie 3: Case-insensitive
    search_lower = search_text.lower()
    content_lower = content.lower()
    
    for length in range(min(len(search_lower), 50), 10, -5):
        search_phrase = search_lower[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content_lower.find(search_phrase)
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # Strategie 4: Worttrennung - ab zweitem Wort
    words = search_text.split()
    if len(words) >= 3:
        for start in range(1, min(3, len(words) - 1)):
            remaining = ' '.join(words[start:start + 4])
            idx = content.find(remaining)
            if idx >= 0:
                # Gehe zum Wortanfang zurück
                word_start = idx
                while word_start > 0 and content[word_start - 1] not in ' \n\t.,;:!?':
                    word_start -= 1
                return _extract_before_text(content, word_start, len(remaining) + (idx - word_start))
    
    return None


def _find_original_position(original: str, normalized: str, norm_idx: int) -> int:
    """Findet die Position im Original-String."""
    target = normalized[norm_idx:norm_idx + 30]
    
    for pos in range(max(0, norm_idx - 20), min(len(original), norm_idx + 50)):
        if normalize_for_matching(original[pos:pos + 35]).startswith(target[:20]):
            return pos
    
    return norm_idx


def _extract_before_text(content: str, start_idx: int, min_len: int) -> Optional[str]:
    """Extrahiert beforeText aus dem Content."""
    end_pos = start_idx + max(min_len, BEFORE_TEXT_MIN)
    
    while end_pos < len(content) and end_pos < start_idx + BEFORE_TEXT_MAX:
        if content[end_pos] in ' .,;:!?\n':
            break
        end_pos += 1
    
    before_text = content[start_idx:end_pos].strip()
    return before_text if len(before_text) >= BEFORE_TEXT_MIN else None


def load_json_content_for_ga(ga_number: str) -> Optional[str]:
    """
    Lädt den gesamten Text-Content für eine GA aus den JSON-Dateien.
    
    Enthält auch Vortrags-/Kapitel-Titel, damit Überschriften-Seiten gefunden werden.
    """
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num = ga_num.group(1).zfill(3).upper()
    ga_pattern = f"GA{ga_num}"
    
    content_parts = []
    
    for json_file in SCRIPT_DIR.glob("steiner-*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'lectures' in data:
                for lecture in data['lectures']:
                    if lecture.get('gaNumber', '').upper() == ga_pattern:
                        # Füge auch den Vortrags-Titel hinzu (für Überschriften-Seiten)
                        title = lecture.get('title', '')
                        if title:
                            content_parts.append(title)
                        
                        for para in lecture.get('paragraphs', []):
                            content_parts.append(para.get('content', ''))
            
            if 'books' in data:
                for book in data['books']:
                    if book.get('ID', '').upper() == ga_pattern:
                        # Füge Buchtitel hinzu
                        title = book.get('title', '')
                        if title:
                            content_parts.append(title)
                        content_parts.append(book.get('content', ''))
        
        except Exception as e:
            print(f"    Warnung: {json_file.name}: {e}")
    
    return '\n\n'.join(content_parts) if content_parts else None


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die PDF-Datei für eine GA-Nummer."""
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num_str = ga_num.group(1).zfill(3)
    
    for pdf_file in PDF_DIR.glob("*.pdf"):
        if f"GA {ga_num_str}" in pdf_file.name or f"GA{ga_num_str}" in pdf_file.name:
            return pdf_file
        
        ga_num_short = ga_num_str.lstrip('0') or '0'
        if f"GA {ga_num_short}," in pdf_file.name or f"GA {ga_num_short} " in pdf_file.name:
            return pdf_file
    
    return None


def process_ga(ga_number: str, test_mode: bool = False) -> Optional[Dict]:
    """
    Verarbeitet eine GA mit dem neuen robusten Ansatz.
    """
    print(f"\n{'='*60}")
    print(f"Verarbeite: {ga_number}")
    print(f"{'='*60}")
    
    # Normalisiere GA-Nummer
    ga_match = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_match:
        print("  FEHLER: Ungültige GA-Nummer")
        return None
    
    ga_normalized = f"GA{ga_match.group(1).zfill(3)}"
    
    # Finde PDF
    pdf_path = find_pdf_for_ga(ga_number)
    if not pdf_path:
        print(f"  FEHLER: Keine PDF gefunden")
        return None
    
    print(f"  PDF: {pdf_path.name}")
    
    # Lade JSON-Content
    print("  Lade JSON-Content...")
    content = load_json_content_for_ga(ga_number)
    if not content:
        print(f"  FEHLER: Kein Content in JSON")
        return None
    
    print(f"  Content: {len(content):,} Zeichen")
    
    # Hole Seitenbereich für diese GA (falls bekannt)
    page_range = GA_PAGE_RANGES.get(ga_normalized, (1, 9999))
    start_page, end_page = page_range
    
    if ga_normalized in GA_PAGE_RANGES:
        print(f"  Seitenbereich: {start_page} - {end_page} (Hauptinhalt)")
    
    # SCHRITT 1: Extrahiere alle Seiten
    print("\n  Schritt 1: Extrahiere Seiten aus PDF...")
    pages = extract_all_pages(pdf_path, start_page, end_page)
    print(f"    {len(pages)} Seiten mit Text gefunden")
    
    # Statistik: Wie viele haben Seitenzahlen?
    with_page_num = sum(1 for p in pages if p.printed_page is not None)
    print(f"    Davon {with_page_num} mit erkannter Seitenzahl")
    
    # SCHRITT 2: Interpoliere fehlende Seitenzahlen
    print("\n  Schritt 2: Interpoliere fehlende Seitenzahlen...")
    pages = interpolate_page_numbers(pages)
    
    # SCHRITT 3: Suche beforeText im JSON
    print("\n  Schritt 3: Suche beforeText im JSON-Content...")
    markers = []
    found_count = 0
    found_with_fallback = 0
    not_found_count = 0
    
    for page in pages:
        if not page.is_content_page:
            continue
        
        before_text = None
        used_fallback = False
        
        # Versuche zuerst den ersten Textblock
        before_text = find_before_text_in_content(page.first_text, content)
        
        # Fallback: Wenn nicht gefunden, versuche die nächsten Textblöcke
        # (z.B. wenn der erste Block eine Überschrift ist, die nicht im JSON steht)
        if not before_text and len(page.all_texts) > 1:
            for text_block in page.all_texts[1:4]:  # Versuche bis zu 3 weitere Blöcke
                before_text = find_before_text_in_content(text_block, content)
                if before_text:
                    used_fallback = True
                    break
        
        if before_text:
            markers.append({
                "page": page.printed_page,
                "beforeText": before_text
            })
            found_count += 1
            if used_fallback:
                found_with_fallback += 1
        else:
            not_found_count += 1
            if not_found_count <= 5:
                print(f"    Seite {page.printed_page}: beforeText nicht gefunden")
                print(f"      PDF-Text: \"{page.first_text[:50]}...\"")
        
        if found_count % 50 == 0 and found_count > 0:
            print(f"    {found_count} Marker gefunden...")
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda m: m['page'])
    
    # Entferne Duplikate
    seen_pages = set()
    unique_markers = []
    for m in markers:
        if m['page'] not in seen_pages:
            unique_markers.append(m)
            seen_pages.add(m['page'])
    markers = unique_markers
    
    print(f"\n  Ergebnis:")
    print(f"    {found_count} Seitenmarker gefunden")
    if found_with_fallback > 0:
        print(f"      (davon {found_with_fallback} mit Fallback auf nächsten Textblock)")
    print(f"    {not_found_count} nicht im JSON gefunden")
    
    if markers:
        pages_range = f"{markers[0]['page']} - {markers[-1]['page']}"
        print(f"    Seitenbereich: {pages_range}")
        
        # Prüfe auf Lücken
        page_nums = [m['page'] for m in markers]
        expected_pages = set(range(min(page_nums), max(page_nums) + 1))
        found_pages = set(page_nums)
        missing = sorted(expected_pages - found_pages)
        
        if missing:
            print(f"    Fehlende Seiten: {len(missing)}")
            if len(missing) <= 10:
                print(f"      {missing}")
            else:
                print(f"      {missing[:5]} ... {missing[-5:]}")
        else:
            print(f"    ✓ Lückenlose Sequenz!")
    
    # Extrahiere Titel
    title_match = re.search(r' - (.+)\.pdf$', pdf_path.name)
    title = title_match.group(1) if title_match else ga_number
    
    return {
        "title": title,
        "pdfSource": pdf_path.name,
        "markers": markers
    }


def load_existing_markers() -> Dict:
    """Lädt bestehende Marker."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "_info": "Seitenmarker für GA-Bände. 'beforeText' = Text am Seitenanfang, VOR dem der Marker |page| eingefügt wird."
    }


def save_markers(data: Dict):
    """Speichert Marker."""
    sorted_data = {"_info": data.get("_info", "")}
    ga_keys = sorted([k for k in data.keys() if k.startswith("GA")])
    for key in ga_keys:
        sorted_data[key] = data[key]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Gespeichert in: {OUTPUT_FILE}")


def main():
    if len(sys.argv) < 2:
        print("Export Page Markers V2 - Robuste Seitenzahl-Extraktion")
        print()
        print("Verwendung:")
        print("  python export_page_markers_v2.py GA051")
        print("  python export_page_markers_v2.py --test GA051")
        sys.exit(1)
    
    test_mode = "--test" in sys.argv
    if test_mode:
        print("*** TEST-MODUS ***\n")
    
    all_markers = load_existing_markers()
    
    for ga_arg in sys.argv[1:]:
        if ga_arg.startswith("--"):
            continue
        
        num_match = re.search(r'(\d+[a-z]?)', ga_arg, re.IGNORECASE)
        if not num_match:
            print(f"Ungültige GA-Nummer: {ga_arg}")
            continue
        
        ga_number = f"GA{num_match.group(1).zfill(3)}"
        
        result = process_ga(ga_number, test_mode)
        if result and not test_mode:
            all_markers[ga_number] = result
    
    if not test_mode:
        save_markers(all_markers)
    
    ga_count = len([k for k in all_markers.keys() if k.startswith("GA")])
    total = sum(len(v.get("markers", [])) for k, v in all_markers.items() if k.startswith("GA"))
    print(f"\nGesamt: {ga_count} GA-Bände mit {total} Seitenmarkern")


if __name__ == "__main__":
    main()

