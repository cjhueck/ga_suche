#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
insert_and_correct_pagebreaks_ga116.py
======================================
Für GA116: Fügt Marker aus Wiki ein (#SE116-010 Format) und korrigiert mit PDF.
"""

import re
import requests
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
PDF_DIR = PROJECT_DIR / "Steiner_GA_pdf"
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"


def fetch_online_html(ga_nummer):
    """Lädt den HTML-Inhalt von steiner.wiki"""
    match = re.search(r'(\d+)', str(ga_nummer))
    ga_num = match.group(1).lstrip('0') or '0' if match else str(ga_nummer).lstrip('0') or '0'
    url = STEINER_WIKI_BASE.format(ga_num)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return None


def extract_se_markers_from_html(html_content, ga_num: int):
    """
    Extrahiert Marker im Format #SE116-010 aus dem HTML.
    Sucht auch nach normalen Seitenzahlen als Fallback.
    
    Returns: Liste von {page, context_before, context_after}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('div', {'class': 'mw-parser-output'}) or soup
    
    markers = []
    
    # Methode 1: Suche nach #SE116-010 Format im HTML-Text
    text = content.get_text()
    
    # Pattern: #SE116-010 oder SE116-010
    pattern = rf'#?SE{ga_num}-(\d{{3}})'
    
    for match in re.finditer(pattern, text):
        page_num = int(match.group(1))
        
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        context = text[start:end]
        
        marker_pos_in_context = match.start() - start
        context_before = context[:marker_pos_in_context].strip()
        context_after = context[marker_pos_in_context + len(match.group(0)):].strip()
        
        if len(context_before) > 10 or len(context_after) > 10:
            markers.append({
                'page': page_num,
                'context_before': context_before[-60:],
                'context_after': context_after[:60]
            })
    
    # Methode 2: Fallback - suche nach normalen Seitenzahlen (wie in anderen GAs)
    if not markers:
        pattern = r'([^\n]{0,150})\n\s*(\d{1,4})\s*\n([^\n]{0,150})'
        
        for match in re.finditer(pattern, text):
            context_before = match.group(1).strip()
            page_num = int(match.group(2))
            context_after = match.group(3).strip()
            
            if 1 <= page_num <= 999:
                if len(context_before) > 10 or len(context_after) > 10:
                    markers.append({
                        'page': page_num,
                        'context_before': context_before[-60:],
                        'context_after': context_after[:60]
                    })
    
    # Entferne Duplikate
    seen = set()
    unique_markers = []
    for m in markers:
        if m['page'] not in seen:
            seen.add(m['page'])
            unique_markers.append(m)
    
    unique_markers.sort(key=lambda x: x['page'])
    return unique_markers


def normalize_text(text: str) -> str:
    """Normalisiert Text für Vergleich"""
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'#SE\d+-\d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\u00ad', '')
    return text.strip()


def is_word_char(char: str) -> bool:
    return char.isalpha()


def find_marker_position(content: str, start_pos: int, context_before: str, context_after: str) -> Optional[int]:
    """Findet Position für Marker in MD-Text."""
    search_area = content[start_pos:]
    
    before_clean = normalize_text(context_before)
    after_clean = normalize_text(context_after)
    before_words = before_clean.split()[-3:] if before_clean else []
    after_words = after_clean.split()[:3] if after_clean else []
    
    if not before_words or not after_words:
        return None
    
    # Suche nach letztem Wort vor + erstem Wort nach
    last_word = before_words[-1]
    first_word = after_words[0]
    
    if last_word and first_word and len(last_word) > 2 and len(first_word) > 2:
        for match in re.finditer(re.escape(last_word), search_area, re.IGNORECASE):
            pos_after = match.end()
            text_after = search_area[pos_after:pos_after+100]
            
            first_match = re.search(r'^\s*' + re.escape(first_word), text_after, re.IGNORECASE)
            if first_match:
                ws_match = re.match(r'^\s*', text_after)
                ws_len = len(ws_match.group(0)) if ws_match else 0
                return start_pos + pos_after + ws_len
    
    return None


def insert_marker(content: str, pos: int, marker: str) -> str:
    """Fügt Marker mit korrektem Spacing ein."""
    if pos <= 0 or pos >= len(content):
        return content[:pos] + marker + content[pos:]
    
    char_before = content[pos-1] if pos > 0 else ' '
    char_after = content[pos] if pos < len(content) else ' '
    
    inside_word = is_word_char(char_before) and is_word_char(char_after)
    
    if inside_word:
        return content[:pos] + marker + content[pos:]
    else:
        prefix = ' ' if is_word_char(char_before) and char_before != ' ' else ''
        suffix = ' ' if is_word_char(char_after) and char_after != ' ' else ''
        return content[:pos] + prefix + marker + suffix + content[pos:]


def insert_wiki_markers(md_path: Path, markers: List[Dict]) -> Tuple[int, int]:
    """Fügt Wiki-Marker in MD-Datei ein."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    inserted = 0
    not_found = 0
    current_pos = 0
    
    for marker_info in markers:
        page = marker_info['page']
        
        if f'|{page}|' in content:
            existing_pos = content.find(f'|{page}|')
            if existing_pos > current_pos:
                current_pos = existing_pos + len(f'|{page}|')
            continue
        
        pos = find_marker_position(
            content, current_pos,
            marker_info['context_before'],
            marker_info['context_after']
        )
        
        if pos is not None:
            marker = f'|{page}|'
            content = insert_marker(content, pos, marker)
            current_pos = pos + len(marker) + 2
            inserted += 1
        else:
            not_found += 1
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return inserted, not_found


def find_pdf_for_ga(ga_norm: str) -> Optional[Path]:
    """Findet das PDF für eine GA."""
    ga_num = ga_norm.replace("GA", "").lstrip("0")
    
    for pdf in PDF_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        if "steiner" in name_lower:
            if f"ga {ga_num}," in name_lower or f"ga {ga_num.zfill(3)}," in name_lower:
                return pdf
    return None


def extract_hyphenations_from_pdf(pdf_path: Path) -> Dict[int, str]:
    """Extrahiert Silbentrennungen aus PDF."""
    doc = fitz.open(pdf_path)
    hyphenations = {}
    prev_page_ends_hyphen = False
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        
        page_num = None
        match = re.search(r"Seite:\s*([\d\s]+)", text, re.IGNORECASE)
        if match:
            page_str = match.group(1).replace(" ", "").strip()
            if page_str.isdigit():
                page_num = int(page_str)
        
        body_text = text
        copyright_match = re.search(r"Copyright Rudolf Steiner", text)
        if copyright_match:
            body_text = text[:copyright_match.start()].strip()
        
        if page_num and prev_page_ends_hyphen:
            body_clean = body_text.strip()
            first_word_match = re.match(r'^([a-zA-ZäöüÄÖÜß]+)', body_clean)
            if first_word_match:
                this_start = first_word_match.group(1).lower()
                hyphenations[page_num] = this_start
        
        prev_page_ends_hyphen = body_text.rstrip().endswith('-')
    
    doc.close()
    return hyphenations


def correct_hyphenations_with_pdf(md_path: Path, hyphenations: Dict[int, str]) -> Tuple[int, int]:
    """Korrigiert Marker basierend auf PDF-Silbentrennungen."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_lower = content.lower()
    corrected = 0
    already_ok = 0
    
    for page_num, this_start in sorted(hyphenations.items()):
        marker = f"|{page_num}|"
        marker_pos = content.find(marker)
        
        if marker_pos == -1:
            continue
        
        after_marker = content_lower[marker_pos + len(marker):marker_pos + len(marker) + 30]
        
        if after_marker.lstrip().startswith(this_start):
            already_ok += 1
            continue
        
        pattern = re.compile(r'\b(\w*' + re.escape(this_start) + r')', re.IGNORECASE)
        search_area = content[max(0, marker_pos - 200):marker_pos + 500]
        search_offset = max(0, marker_pos - 200)
        
        best_match = None
        best_distance = float('inf')
        
        for match in pattern.finditer(search_area):
            word = match.group(1).lower()
            if word.endswith(this_start) or this_start in word:
                pos_in_original = search_offset + match.start()
                word_end = pos_in_original + len(match.group(0))
                
                if word.endswith(this_start):
                    fragment_start = word_end - len(this_start)
                    distance = abs(fragment_start - marker_pos)
                    if distance < best_distance and fragment_start != marker_pos:
                        best_match = fragment_start
                        best_distance = distance
        
        if best_match is not None and best_match != marker_pos:
            content_without_marker = content[:marker_pos] + content[marker_pos + len(marker):]
            new_pos = best_match if best_match < marker_pos else best_match - len(marker)
            content = content_without_marker[:new_pos] + marker + content_without_marker[new_pos:]
            corrected += 1
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return corrected, already_ok


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fügt Wiki-Marker ein und korrigiert mit PDF für GA116'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 116)')
    parser.add_argument('--dry-run', action='store_true', help='Nur simulieren')
    
    args = parser.parse_args()
    
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = int(match.group(1))
    ga_norm = f"GA{ga_num:03d}"
    
    print(f"\n{'='*60}")
    print(f"Wiki+PDF Pagebreaks für {ga_norm}")
    print(f"{'='*60}")
    
    # Finde Hauptdatei
    md_folder = None
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            md_folder = folder
            break
    
    if not md_folder:
        print(f"FEHLER: Kein MD-Ordner gefunden")
        return
    
    # Finde Hauptdatei (ohne Nummer im Namen)
    md_path = None
    for f in md_folder.glob("*.md"):
        if not re.search(r'\(\d+\.\)', f.stem):
            md_path = f
            break
    
    if not md_path:
        print(f"FEHLER: Keine Hauptdatei gefunden")
        return
    
    print(f"Hauptdatei: {md_path.name}")
    
    if args.dry_run:
        print("\n*** DRY-RUN MODUS ***\n")
        return
    
    # SCHRITT 1: Wiki-Marker
    print("\n--- SCHRITT 1: Wiki-Marker ---")
    html = fetch_online_html(ga_num)
    if not html:
        print("FEHLER: Wiki nicht erreichbar")
        return
    
    markers = extract_se_markers_from_html(html, ga_num)
    print(f"Wiki-Marker gefunden: {len(markers)}")
    
    if markers:
        inserted, not_found = insert_wiki_markers(md_path, markers)
        print(f"  Eingefügt: {inserted}")
        print(f"  Nicht gefunden: {not_found}")
    
    # SCHRITT 2: PDF-Korrektur
    print("\n--- SCHRITT 2: PDF-Korrektur ---")
    pdf_path = find_pdf_for_ga(ga_norm)
    if not pdf_path:
        print("WARNUNG: Kein PDF gefunden")
    else:
        print(f"PDF: {pdf_path.name}")
        hyphenations = extract_hyphenations_from_pdf(pdf_path)
        print(f"Silbentrennungen: {len(hyphenations)}")
        
        if hyphenations:
            corrected, already_ok = correct_hyphenations_with_pdf(md_path, hyphenations)
            print(f"  Bereits korrekt: {already_ok}")
            print(f"  Korrigiert: {corrected}")
    
    print(f"\n{'='*60}")
    print("FERTIG!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
