#!/usr/bin/env python3
"""
Export Page Markers - Extrahiert Seitenzahlen aus GA-PDFs

Dieses Skript:
1. Liest die gedruckte Seitenzahl aus der PDF-Fußzeile (auch mit Leerzeichen wie "1 2 3")
2. Findet den ersten Text-Block jeder Seite (Text NACH dem Seitenumbruch) - beforeText
3. Sucht diesen Text in der entsprechenden JSON-Datei
4. Speichert die Marker in page-markers.json
5. Der Marker |page| wird VOR dem beforeText eingefügt (auch bei Worttrennungen)

Verwendung:
    python export_page_markers.py GA051         # Eine GA exportieren
    python export_page_markers.py GA051 GA052   # Mehrere GAs
    python export_page_markers.py --list        # Verfügbare PDFs anzeigen
    python export_page_markers.py --test GA051  # Nur testen, nicht speichern

Benötigt: pip install pymupdf
"""

import fitz  # PyMuPDF
import re
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Konfiguration
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = Path("page-markers.json")
SCRIPT_DIR = Path(__file__).parent

# Minimale Textlänge pro Seite
MIN_PAGE_TEXT_LENGTH = 50

# beforeText Länge (min/max)
BEFORE_TEXT_MIN = 20
BEFORE_TEXT_MAX = 60


def normalize_for_search(text: str) -> str:
    """Normalisiert Text für die Suche (entfernt Sonderzeichen, mehrfache Leerzeichen)."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


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
        # z.B. "123" oder "1 2 3"
        clean_line = line.replace(' ', '')
        if clean_line.isdigit() and 1 <= len(clean_line) <= 4:
            return int(clean_line)
    
    # Prüfe auch die ersten Zeilen (manche PDFs haben Seitenzahl oben)
    for line in lines[:3]:
        line = line.strip()
        clean_line = line.replace(' ', '')
        if clean_line.isdigit() and 1 <= len(clean_line) <= 4:
            return int(clean_line)
    
    return None


def get_first_text_of_page(page) -> Optional[str]:
    """
    Holt den ersten Textblock einer Seite (Text NACH dem Seitenumbruch).
    Dies ist der beforeText - der Text, VOR dem der Seitenmarker eingefügt wird.
    Ignoriert Kopfzeilen, Seitenzahlen, Copyright etc.
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
        return None
    
    # Sortiere nach Y-Position (von oben nach unten) und nimm den ERSTEN
    text_blocks.sort(key=lambda b: b['y'])
    
    # Nimm den ersten Block
    return text_blocks[0]['text']


def normalize_for_matching(text: str) -> str:
    """
    Normalisiert Text für robusteren Vergleich:
    - daß -> dass (Rechtschreibreform)
    - Kleinbuchstaben
    - Mehrfache Leerzeichen entfernen
    """
    text = text.replace('daß', 'dass').replace('Daß', 'Dass')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_before_text_in_content(first_line_text: str, content: str) -> Optional[str]:
    """
    Sucht den ersten Zeilen-Text der PDF-Seite im JSON-Content.
    Gibt einen beforeText zurück, der exakt im Content gefunden werden kann.
    
    Der Marker wird VOR diesem Text eingefügt.
    
    Behandelt folgende Probleme:
    1. Worttrennung am Seitenanfang (z.B. "weit" von "Außen-weit")
    2. Rechtschreibreform (daß -> dass)
    3. Groß-/Kleinschreibung
    
    Args:
        first_line_text: Der erste Text der Seite aus dem PDF
        content: Der gesamte Text aus der JSON-Datei
    
    Returns:
        beforeText (20-60 Zeichen) der exakt im Content gesucht werden kann
    """
    if not first_line_text or len(first_line_text) < 5:
        return None
    
    # Bereinige den PDF-Text (Zeilenumbrüche zu Leerzeichen)
    search_text = first_line_text.replace('\n', ' ').strip()
    
    # === STRATEGIE 1: Exakte Suche mit verschiedenen Längen ===
    for length in range(min(len(search_text), 50), 10, -5):
        search_phrase = search_text[:length].strip()
        
        if len(search_phrase) < 10:
            continue
        
        idx = content.find(search_phrase)
        
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # === STRATEGIE 2: Rechtschreibreform-normalisiert ===
    search_normalized = normalize_for_matching(search_text)
    content_normalized = normalize_for_matching(content)
    
    for length in range(min(len(search_normalized), 50), 10, -5):
        search_phrase = search_normalized[:length].strip()
        
        if len(search_phrase) < 10:
            continue
        
        idx = content_normalized.find(search_phrase)
        
        if idx >= 0:
            # Finde die exakte Position im Original-Content
            # Durch Normalisierung kann die Position leicht abweichen
            original_idx = _find_original_position(content, content_normalized, idx)
            if original_idx >= 0:
                return _extract_before_text(content, original_idx, len(search_phrase))
    
    # === STRATEGIE 3: Case-insensitive Suche ===
    search_lower = search_text.lower()
    content_lower = content.lower()
    
    for length in range(min(len(search_lower), 50), 10, -5):
        search_phrase = search_lower[:length].strip()
        
        if len(search_phrase) < 10:
            continue
        
        idx = content_lower.find(search_phrase)
        
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # === STRATEGIE 4: Worttrennung - Suche ab dem ZWEITEN Wort ===
    # Wenn der erste Text ein Wortteil ist (z.B. "weit" von "Außenwelt"),
    # versuche ab dem zweiten Wort zu suchen
    words = search_text.split()
    if len(words) >= 3:
        # Starte ab dem zweiten Wort (überspringe potenziellen Wortteil)
        for start_word in range(1, min(3, len(words) - 1)):
            remaining_text = ' '.join(words[start_word:start_word + 4])
            
            idx = content.find(remaining_text)
            if idx >= 0:
                # Gefunden! Aber wir wollen den Text VOR diesem Punkt
                # Suche rückwärts nach dem Wortanfang
                word_start = idx
                while word_start > 0 and content[word_start - 1] not in ' \n\t.,;:!?':
                    word_start -= 1
                
                return _extract_before_text(content, word_start, len(remaining_text) + (idx - word_start))
    
    # === STRATEGIE 5: Fuzzy-Suche mit Wörtern (Original-Methode) ===
    search_normalized = normalize_for_search(search_text)
    content_normalized = normalize_for_search(content)
    
    words = search_normalized.split()
    if len(words) >= 2:
        for word_count in range(min(len(words), 5), 1, -1):
            search_phrase = ' '.join(words[:word_count])
            
            idx = content_normalized.find(search_phrase)
            if idx >= 0:
                for start_pos in range(max(0, idx - 50), min(len(content), idx + 100)):
                    if normalize_for_search(content[start_pos:start_pos + len(search_phrase) + 20]).startswith(search_phrase):
                        return _extract_before_text(content, start_pos, len(search_phrase))
    
    return None


def _find_original_position(original: str, normalized: str, normalized_idx: int) -> int:
    """
    Findet die ungefähre Position im Original-String basierend auf der Position im normalisierten String.
    """
    # Einfache Heuristik: Die Position im Original ist ähnlich
    # (Normalisierung verändert hauptsächlich Leerzeichen und daß->dass)
    
    # Suche in einem Fenster um die erwartete Position
    window_start = max(0, normalized_idx - 20)
    window_end = min(len(original), normalized_idx + 50)
    
    # Extrahiere den normalisierten Text an dieser Position
    target_text = normalized[normalized_idx:normalized_idx + 30]
    
    # Suche diesen Text im Original-Fenster
    for pos in range(window_start, window_end):
        if normalize_for_matching(original[pos:pos + 35]).startswith(target_text[:20]):
            return pos
    
    return normalized_idx  # Fallback: verwende die normalisierte Position


def _extract_before_text(content: str, start_idx: int, min_length: int) -> Optional[str]:
    """
    Extrahiert beforeText aus dem Content ab einer bestimmten Position.
    """
    end_pos = start_idx + max(min_length, BEFORE_TEXT_MIN)
    
    # Erweitere bis zu einer guten Grenze (Wortende, max 60 Zeichen)
    while end_pos < len(content) and end_pos < start_idx + BEFORE_TEXT_MAX:
        if content[end_pos] in ' .,;:!?\n':
            break
        end_pos += 1
    
    before_text = content[start_idx:end_pos].strip()
    
    if len(before_text) >= BEFORE_TEXT_MIN:
        return before_text
    
    return None


def load_json_content_for_ga(ga_number: str) -> Optional[str]:
    """
    Lädt den gesamten Text-Content für eine GA aus den JSON-Dateien.
    Kombiniert alle Vorträge/Bücher zu einem String.
    """
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num = ga_num.group(1).zfill(3).upper()
    ga_pattern = f"GA{ga_num}"
    
    content_parts = []
    
    # Suche in allen JSON-Dateien
    for json_file in SCRIPT_DIR.glob("steiner-*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Für Vorträge (lectures)
            if 'lectures' in data:
                for lecture in data['lectures']:
                    if lecture.get('gaNumber', '').upper() == ga_pattern:
                        for para in lecture.get('paragraphs', []):
                            content_parts.append(para.get('content', ''))
            
            # Für Bücher (books)
            if 'books' in data:
                for book in data['books']:
                    if book.get('ID', '').upper() == ga_pattern:
                        content_parts.append(book.get('content', ''))
        
        except Exception as e:
            print(f"    Warnung: Fehler beim Lesen von {json_file.name}: {e}")
    
    if content_parts:
        return '\n\n'.join(content_parts)
    
    return None


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die PDF-Datei für eine GA-Nummer."""
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num_str = ga_num.group(1).zfill(3)
    
    # Suche mit verschiedenen Mustern
    for pdf_file in PDF_DIR.glob("*.pdf"):
        # Muster: "GA 051" oder "GA051"
        if f"GA {ga_num_str}" in pdf_file.name or f"GA{ga_num_str}" in pdf_file.name:
            return pdf_file
        
        # Auch ohne führende Nullen
        ga_num_short = ga_num_str.lstrip('0') or '0'
        if f"GA {ga_num_short}," in pdf_file.name or f"GA {ga_num_short} " in pdf_file.name:
            return pdf_file
    
    return None


def process_ga(ga_number: str, test_mode: bool = False) -> Optional[Dict]:
    """
    Verarbeitet eine GA: Extrahiert Seitenzahlen aus PDF und sucht sie im JSON-Content.
    
    Verwendet beforeText: Der erste Text einer Seite (nach dem Umbruch).
    Der Marker |page| wird VOR diesem Text eingefügt.
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
        print(f"  FEHLER: Keine PDF gefunden für {ga_number}")
        return None
    
    print(f"  PDF: {pdf_path.name}")
    
    # Lade JSON-Content
    print("  Lade JSON-Content...")
    content = load_json_content_for_ga(ga_number)
    if not content:
        print(f"  FEHLER: Kein Content in JSON-Dateien für {ga_number}")
        return None
    
    print(f"  Content: {len(content):,} Zeichen")
    
    # Öffne PDF und extrahiere Seiten
    print("\n  Extrahiere Seiten aus PDF...")
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  FEHLER: Kann PDF nicht öffnen: {e}")
        return None
    
    print(f"  PDF hat {len(doc)} Seiten")
    
    markers = []
    found_pages = set()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        
        # Extrahiere Seitenzahl aus Fußzeile
        printed_page = extract_page_number_from_footer(page_text)
        if printed_page is None:
            continue
        
        # Überspringe bereits gefundene Seiten (Duplikate)
        if printed_page in found_pages:
            continue
        
        # Hole den ersten Textblock (Text nach Seitenumbruch)
        first_text = get_first_text_of_page(page)
        if not first_text or len(first_text) < 10:
            continue
        
        # Suche diesen Text im JSON-Content
        before_text = find_before_text_in_content(first_text, content)
        
        if before_text:
            markers.append({
                "page": printed_page,
                "beforeText": before_text
            })
            found_pages.add(printed_page)
            
            if len(markers) % 50 == 0:
                print(f"    {len(markers)} Marker gefunden...")
    
    doc.close()
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda m: m['page'])
    
    print(f"\n  {len(markers)} Seitenmarker gefunden")
    
    if markers:
        print("\n  Beispiele:")
        for m in markers[:5]:
            before_preview = m['beforeText'][:50] + '...' if len(m['beforeText']) > 50 else m['beforeText']
            print(f"    Seite {m['page']:>3}: \"{before_preview}\"")
        
        if len(markers) > 5:
            print(f"    ... und {len(markers) - 5} weitere")
    
    # Extrahiere Titel aus PDF-Name
    title_match = re.search(r' - (.+)\.pdf$', pdf_path.name)
    title = title_match.group(1) if title_match else ga_number
    
    return {
        "title": title,
        "pdfSource": pdf_path.name,
        "markers": markers
    }


def load_existing_markers() -> Dict:
    """Lädt bestehende Marker aus page-markers.json."""
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
    """Speichert Marker in page-markers.json."""
    # Sortiere GA-Nummern
    sorted_data = {"_info": data.get("_info", "")}
    ga_keys = sorted([k for k in data.keys() if k.startswith("GA")])
    for key in ga_keys:
        sorted_data[key] = data[key]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Gespeichert in: {OUTPUT_FILE}")


def main():
    if len(sys.argv) < 2:
        print("Export Page Markers - Seitenzahlen aus GA-PDFs extrahieren")
        print()
        print("Verwendung:")
        print("  python export_page_markers.py GA051         # Eine GA exportieren")
        print("  python export_page_markers.py GA051 GA052   # Mehrere GAs")
        print("  python export_page_markers.py --list        # Verfügbare PDFs anzeigen")
        print("  python export_page_markers.py --test GA051  # Nur testen, nicht speichern")
        print()
        print("Der Marker wird VOR dem beforeText eingefügt (auch bei Worttrennungen).")
        print("Die Ergebnisse werden in page-markers.json gespeichert.")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        print("Verfügbare PDFs:")
        for pdf in sorted(PDF_DIR.glob("*.pdf")):
            match = re.search(r'GA (\d+[a-z]?)', pdf.name)
            if match:
                ga_num = match.group(1).zfill(3)
                print(f"  GA{ga_num}: {pdf.name}")
        sys.exit(0)
    
    test_mode = "--test" in sys.argv
    if test_mode:
        print("*** TEST-MODUS - Änderungen werden NICHT gespeichert ***\n")
    
    # Lade bestehende Marker
    all_markers = load_existing_markers()
    
    # Verarbeite angegebene GAs
    for ga_arg in sys.argv[1:]:
        if ga_arg.startswith("--"):
            continue
        
        # Normalisiere GA-Nummer
        num_match = re.search(r'(\d+[a-z]?)', ga_arg, re.IGNORECASE)
        if not num_match:
            print(f"Ungültige GA-Nummer: {ga_arg}")
            continue
        
        ga_number = f"GA{num_match.group(1).zfill(3)}"
        
        result = process_ga(ga_number, test_mode)
        if result and not test_mode:
            all_markers[ga_number] = result
    
    # Speichere aktualisierte Marker
    if not test_mode:
        save_markers(all_markers)
    
    # Statistik
    ga_count = len([k for k in all_markers.keys() if k.startswith("GA")])
    total_markers = sum(len(v.get("markers", [])) for k, v in all_markers.items() if k.startswith("GA"))
    print(f"\nGesamt: {ga_count} GA-Bände mit {total_markers} Seitenmarkern")


if __name__ == "__main__":
    main()
