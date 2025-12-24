#!/usr/bin/env python3
"""
Extrahiert Seitenzahlen aus PDFs und erstellt page-markers.json für die App.

Die Seitenmarker werden am ENDE jeder Seite positioniert (nicht am Anfang der nächsten),
damit sie anzeigen "bis hier war Seite X".

Verwendung:
    python add_page_markers.py GA009           # Extrahiere für eine GA
    python add_page_markers.py --all           # Extrahiere für alle GAs
    python add_page_markers.py --update GA009  # Aktualisiere nur eine GA
    
Benötigt: pip install pymupdf
"""

import fitz  # PyMuPDF
import re
import sys
import json
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Tuple, Optional, Dict

# Konfiguration
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
MD_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
OUTPUT_FILE = Path("page-markers.json")

# Mindest-Übereinstimmung für Fuzzy-Matching (0.0 - 1.0)
MIN_MATCH_RATIO = 0.5

# Minimale Textlänge pro Seite, um sie zu berücksichtigen
MIN_PAGE_TEXT_LENGTH = 100

# Anzahl Zeichen am Ende einer Seite für den Marker
END_TEXT_LENGTH = 50


def normalize_text(text: str) -> str:
    """Normalisiert Text für besseren Vergleich."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.strip()


def extract_pages_from_pdf(pdf_path: Path) -> List[Tuple[int, str, str]]:
    """
    Extrahiert Text pro Seite aus einer PDF.
    Gibt Liste von (Seitenzahl, vollständiger Text, letzter Absatz) zurück.
    """
    pages = []
    
    try:
        doc = fitz.open(pdf_path)
        print(f"  PDF hat {len(doc)} Seiten")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Versuche die gedruckte Seitenzahl zu finden
            printed_page = page_num + 1  # Fallback: PDF-Seitenzahl
            
            lines = text.strip().split('\n')
            
            # Prüfe erste und letzte Zeilen auf Seitenzahlen
            for check_line in [lines[0] if lines else '', lines[-1] if lines else '']:
                check_line = check_line.strip()
                if check_line.isdigit() and len(check_line) <= 4:
                    printed_page = int(check_line)
                    break
            
            if len(text.strip()) >= MIN_PAGE_TEXT_LENGTH:
                # Extrahiere die letzten ~50 Zeichen (ohne Seitenzahl und Whitespace)
                # Das ist der Text, nach dem der Marker eingefügt wird
                clean_text = text.strip()
                
                # Entferne Seitenzahl am Ende falls vorhanden
                clean_lines = [l for l in clean_text.split('\n') if l.strip() and not l.strip().isdigit()]
                if clean_lines:
                    last_text = clean_lines[-1].strip()
                    # Nehme die letzten Wörter (ca. 50 Zeichen)
                    if len(last_text) > END_TEXT_LENGTH:
                        # Finde Wortgrenze
                        end_text = last_text[-END_TEXT_LENGTH:]
                        space_idx = end_text.find(' ')
                        if space_idx > 0:
                            end_text = end_text[space_idx+1:]
                        last_text = end_text
                else:
                    last_text = ""
                
                pages.append((printed_page, text, last_text))
        
        doc.close()
        
    except Exception as e:
        print(f"  FEHLER beim Lesen der PDF: {e}")
        return []
    
    return pages


def find_end_text_in_md(md_text: str, end_text: str, start_pos: int = 0) -> Optional[str]:
    """
    Sucht den End-Text einer PDF-Seite in der MD-Datei.
    Gibt den gefundenen Text zurück (für afterText im JSON) oder None.
    """
    if not end_text or len(end_text) < 10:
        return None
    
    md_normalized = normalize_text(md_text[start_pos:])
    search_normalized = normalize_text(end_text)
    
    if len(search_normalized) < 10:
        return None
    
    # Suche mit Fuzzy-Matching
    best_match = None
    best_ratio = 0
    best_pos = -1
    
    # Sliding window
    window_size = len(search_normalized) + 20
    for i in range(0, min(len(md_normalized) - window_size, 100000), 10):
        window = md_normalized[i:i + window_size]
        ratio = SequenceMatcher(None, search_normalized, window[:len(search_normalized)]).ratio()
        
        if ratio > best_ratio and ratio >= MIN_MATCH_RATIO:
            best_ratio = ratio
            best_pos = i
    
    if best_pos >= 0:
        # Finde den Original-Text an dieser Position
        # Suche nach einem Satzende oder natürlichen Bruchpunkt
        original_pos = start_pos + best_pos
        
        # Suche das Ende des Satzes/Absatzes
        search_end = min(original_pos + len(end_text) + 50, len(md_text))
        
        # Finde einen guten Endpunkt (Satzende, Absatzende)
        for end_marker in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
            end_idx = md_text.find(end_marker, original_pos, search_end)
            if end_idx > 0:
                # Extrahiere die letzten 40-60 Zeichen vor dem Endpunkt
                end_pos = end_idx + 1  # Nach dem Punkt
                start_extract = max(original_pos - 20, 0)
                extracted = md_text[start_extract:end_pos].strip()
                
                # Bereinige den extrahierten Text
                # Entferne Obsidian-Indizes (^abc123)
                extracted = re.sub(r'\s*\^[a-z0-9]+\s*', '', extracted)
                
                # Nehme nur die letzten 40-50 Zeichen
                if len(extracted) > 50:
                    # Finde Wortgrenze
                    extracted = extracted[-50:]
                    space_idx = extracted.find(' ')
                    if space_idx > 0:
                        extracted = extracted[space_idx+1:]
                
                if len(extracted) >= 15:
                    return extracted.strip()
        
        # Fallback: Nimm einfach den Text an der Position
        extracted = md_text[original_pos:original_pos + 50].strip()
        extracted = re.sub(r'\s*\^[a-z0-9]+\s*', '', extracted)
        if len(extracted) >= 15:
            words = extracted.split()
            if len(words) >= 3:
                return ' '.join(words[:6])
    
    return None


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die PDF-Datei für eine GA-Nummer."""
    num_match = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not num_match:
        return None
    
    ga_num = num_match.group(1).zfill(3)
    
    for pdf_file in PDF_DIR.glob("*.pdf"):
        if f"GA {ga_num}" in pdf_file.name or f"GA{ga_num}" in pdf_file.name:
            return pdf_file
    
    ga_num_short = ga_num.lstrip('0') or '0'
    for pdf_file in PDF_DIR.glob("*.pdf"):
        if f"GA {ga_num_short}," in pdf_file.name:
            return pdf_file
    
    return None


def find_md_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die MD-Datei für eine GA-Nummer."""
    num_match = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not num_match:
        return None
    
    ga_num = num_match.group(1).zfill(3)
    ga_dir_pattern = f"GA{ga_num}*"
    
    for ga_dir in MD_DIR.glob(ga_dir_pattern):
        if ga_dir.is_dir():
            for md_file in ga_dir.glob("*.md"):
                if "GA" in md_file.name and not md_file.name.endswith('.with_pages.md'):
                    return md_file
    
    return None


def process_ga(ga_number: str) -> Optional[Dict]:
    """
    Verarbeitet eine GA: Extrahiert Seitenzahlen aus PDF.
    Gibt ein Dictionary mit den Markern zurück.
    """
    print(f"\n{'='*60}")
    print(f"Verarbeite: {ga_number}")
    print(f"{'='*60}")
    
    pdf_path = find_pdf_for_ga(ga_number)
    md_path = find_md_for_ga(ga_number)
    
    if not pdf_path:
        print(f"  FEHLER: Keine PDF gefunden für {ga_number}")
        return None
    
    if not md_path:
        print(f"  FEHLER: Keine MD-Datei gefunden für {ga_number}")
        return None
    
    print(f"  PDF: {pdf_path.name}")
    print(f"  MD:  {md_path.name}")
    
    # Extrahiere Seiten aus PDF
    print("\n  Extrahiere Seiten aus PDF...")
    pdf_pages = extract_pages_from_pdf(pdf_path)
    
    if not pdf_pages:
        print("  FEHLER: Keine Seiten extrahiert")
        return None
    
    print(f"  {len(pdf_pages)} Seiten mit Text gefunden")
    
    # Lese MD-Datei
    md_text = md_path.read_text(encoding='utf-8')
    print(f"  MD-Datei hat {len(md_text)} Zeichen")
    
    # Finde Seitenenden
    print("\n  Suche Seitenenden...")
    markers = []
    last_pos = 0
    
    for page_num, full_text, end_text in pdf_pages:
        if not end_text:
            continue
        
        after_text = find_end_text_in_md(md_text, end_text, last_pos)
        
        if after_text:
            markers.append({
                "page": page_num,
                "afterText": after_text
            })
            
            # Update last_pos für nächste Suche
            found_idx = md_text.find(after_text, last_pos)
            if found_idx >= 0:
                last_pos = found_idx + len(after_text)
        
        if len(markers) % 20 == 0 and len(markers) > 0:
            print(f"    {len(markers)} Marker gefunden...")
    
    print(f"  {len(markers)} Seitenmarker gefunden")
    
    if not markers:
        print("  WARNUNG: Keine Marker gefunden!")
        return None
    
    # Zeige Beispiele
    print("\n  Beispiele:")
    for m in markers[:5]:
        print(f"    Seite {m['page']}: \"{m['afterText'][:40]}...\"")
    
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
        "_info": "Seitenmarker für GA-Bände. 'afterText' = Text nach dem der Marker |page| eingefügt wird"
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
        print("Verwendung:")
        print("  python add_page_markers.py GA009           # Eine GA extrahieren")
        print("  python add_page_markers.py GA009 GA010     # Mehrere GAs")
        print("  python add_page_markers.py --list          # Verfügbare PDFs anzeigen")
        print("")
        print("Die Ergebnisse werden in page-markers.json gespeichert.")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        print("Verfügbare PDFs:")
        for pdf in sorted(PDF_DIR.glob("*.pdf")):
            match = re.search(r'GA (\d+[a-z]?)', pdf.name)
            if match:
                print(f"  GA{match.group(1).zfill(3)}: {pdf.name}")
        sys.exit(0)
    
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
        
        result = process_ga(ga_number)
        if result:
            all_markers[ga_number] = result
    
    # Speichere aktualisierte Marker
    save_markers(all_markers)
    
    # Statistik
    ga_count = len([k for k in all_markers.keys() if k.startswith("GA")])
    total_markers = sum(len(v.get("markers", [])) for k, v in all_markers.items() if k.startswith("GA"))
    print(f"\nGesamt: {ga_count} GA-Bände mit {total_markers} Seitenmarkern")


if __name__ == "__main__":
    main()
