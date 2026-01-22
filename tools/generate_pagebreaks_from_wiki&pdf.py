#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_pagebreaks_from_wiki&pdf.py
====================================
Kombiniertes Skript für Seitenmarker-Generierung:

1. SCHRITT 1 (Wiki): Holt Seitenmarker von steiner.wiki (Anthrowiki) und fügt sie ein
2. SCHRITT 2 (PDF): Korrigiert Silbentrennungen anhand des Original-PDFs

Bei Silbentrennungen wird nur der Text NACH dem Marker geprüft,
da vor dem Marker Fußnoten stehen können.
"""

import re
import sys
import requests
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup

# Konfiguration
PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
PDF_DIR = PROJECT_DIR / "Steiner_GA_pdf"
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"


# =============================================================================
# SCHRITT 1: Wiki-basierte Marker-Einfügung
# =============================================================================

def fetch_online_html(ga_nummer):
    """Lädt den HTML-Inhalt von steiner.wiki"""
    # Extrahiere nur die Zahl aus ga_nummer (z.B. "GA004" -> "4")
    import re
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


def extract_page_markers_from_html(html_content):
    """Extrahiert Seitenzahlen und deren Kontext aus der Online-Version."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    content = soup.find('div', {'class': 'mw-parser-output'})
    if not content:
        content = soup
    
    markers = []
    elements = content.find_all(['p', 'div', 'span'])
    full_text_parts = []
    
    for elem in elements:
        text = elem.get_text()
        if text.strip():
            full_text_parts.append(text)
    
    full_text = '\n'.join(full_text_parts)
    full_text = full_text.replace('\u00ad', '')
    
    pattern = r'([^\n]{0,150})\n\s*(\d{1,4})\s*\n([^\n]{0,150})'
    
    for match in re.finditer(pattern, full_text):
        context_before = match.group(1).strip()
        page_num = int(match.group(2))
        context_after = match.group(3).strip()
        
        if 1 <= page_num <= 999:
            if len(context_before) > 10 or len(context_after) > 10:
                markers.append({
                    'page': page_num,
                    'context_before': context_before[-100:] if len(context_before) > 100 else context_before,
                    'context_after': context_after[:100] if len(context_after) > 100 else context_after
                })
    
    markers.sort(key=lambda x: x['page'])
    
    seen = set()
    unique_markers = []
    for m in markers:
        if m['page'] not in seen:
            seen.add(m['page'])
            unique_markers.append(m)
    
    return unique_markers


def normalize_text(text):
    """Normalisiert Text für Vergleich"""
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'\*\*\d+\*\*', '', text)
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'#.*?\n', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\u00ad', '')
    text = text.replace('-\n', '')
    return text.strip()


def is_word_char(char):
    """Prüft ob ein Zeichen ein Wort-Zeichen ist"""
    return char.isalpha()


def format_marker_with_spacing(text, pos, marker):
    """Fügt einen Marker an Position pos ein, mit korrekter Formatierung."""
    char_before = text[pos-1] if pos > 0 else ' '
    char_after = text[pos] if pos < len(text) else ' '
    
    inside_word = is_word_char(char_before) and is_word_char(char_after)
    
    if inside_word:
        return text[:pos] + marker + text[pos:]
    else:
        needs_space_before = is_word_char(char_before)
        needs_space_after = is_word_char(char_after)
        
        prefix = ' ' if needs_space_before else ''
        suffix = ' ' if needs_space_after else ''
        
        return text[:pos] + prefix + marker + suffix + text[pos:]


def find_marker_position_after(text, start_pos, context_before, context_after):
    """Findet die Position für einen Marker, aber NUR NACH start_pos."""
    search_text = text[start_pos:]
    
    before_norm = normalize_text(context_before) if context_before else ''
    after_norm = normalize_text(context_after) if context_after else ''
    before_words = before_norm.split()[-4:] if before_norm else []
    after_words = after_norm.split()[:4] if after_norm else []
    
    # Methode 1: Wort-Trennung
    last_before = context_before.rstrip() if context_before else ''
    first_after = context_after.lstrip() if context_after else ''
    
    if last_before and first_after and last_before.endswith('-'):
        word_start = last_before.rstrip('-').split()[-1] if last_before.rstrip('-').split() else ''
        word_end = first_after.split()[0] if first_after.split() else ''
        combined_word = word_start + word_end
        
        if combined_word and len(combined_word) > 4:
            match = re.search(re.escape(combined_word), search_text, re.IGNORECASE)
            if match:
                return start_pos + match.start() + len(word_start), "Wort-Trennung"
    
    # Methode 2: Letztes Wort von before + erstes Wort von after
    if before_words and after_words and len(before_words[-1]) > 3 and len(after_words[0]) > 2:
        last_word = before_words[-1]
        first_after_word = after_words[0]
        
        for match in re.finditer(re.escape(last_word), search_text, re.IGNORECASE):
            pos = match.end()
            text_after = search_text[pos:pos+150]
            
            after_match = re.search(re.escape(first_after_word), text_after, re.IGNORECASE)
            if after_match:
                return start_pos + pos + after_match.start(), "Wort-Match"
    
    # Methode 3: Mehrwort-Sequenz
    if before_words and len(before_words) >= 2:
        for num_words in range(min(3, len(before_words)), 1, -1):
            search_phrase = ' '.join(before_words[-num_words:])
            if len(search_phrase) < 8:
                continue
            
            match = re.search(re.escape(search_phrase), search_text, re.IGNORECASE)
            if match:
                pos = match.end()
                if after_words:
                    text_after = search_text[pos:pos+200]
                    first_after = after_words[0]
                    after_match = re.search(re.escape(first_after), text_after, re.IGNORECASE)
                    if after_match:
                        return start_pos + pos + after_match.start(), "Mehrwort"
    
    return None, None


def is_heading(line):
    """Prüft ob eine Zeile eine Markdown-Überschrift ist"""
    stripped = line.strip()
    return stripped.startswith('#') and len(stripped) > 1 and stripped[1] in '# '


def move_markers_around_headings(content):
    """Verschiebt Seitenmarker, die vor/in Überschriften stehen."""
    lines = content.split('\n')
    changes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if is_heading(line):
            match = re.match(r'^(\s*)(\|(\d+)\|)\s*(#+\s+.*)$', line)
            if match:
                indent = match.group(1)
                marker = match.group(2)
                heading = match.group(4)
                lines[i] = indent + heading
                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        if is_heading(line):
            match = re.match(r'^(\s*)(#+)\s*(\|(\d+)\|)\s*(.*)$', line)
            if match:
                indent = match.group(1)
                hashes = match.group(2)
                marker = match.group(3)
                title = match.group(5)
                lines[i] = indent + hashes + ' ' + title
                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not is_heading(next_line):
                        lines[j] = marker + ' ' + next_line.lstrip()
                        changes += 1
                        break
                    j += 1
        
        marker_at_end = re.search(r'\|(\d+)\|\s*$', line)
        if marker_at_end and not is_heading(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines) and is_heading(lines[j]):
                marker = marker_at_end.group(0).strip()
                lines[i] = re.sub(r'\s*\|(\d+)\|\s*$', '', line)
                
                k = j + 1
                while k < len(lines):
                    content_line = lines[k]
                    if content_line.strip() and not is_heading(content_line):
                        lines[k] = marker + ' ' + content_line.lstrip()
                        changes += 1
                        break
                    k += 1
        
        i += 1
    
    return '\n'.join(lines), changes


def insert_wiki_markers(md_path: Path, markers: List[Dict], start_page: int = 7) -> Tuple[int, int]:
    """Fügt Wiki-Marker in die MD-Datei ein."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    markers = [m for m in markers if m['page'] >= start_page]
    
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
        
        pos, method = find_marker_position_after(
            content, current_pos,
            marker_info['context_before'],
            marker_info['context_after']
        )
        
        if pos is not None:
            marker = f'|{page}|'
            content = format_marker_with_spacing(content, pos, marker)
            current_pos = pos + len(marker) + 2
            inserted += 1
        else:
            not_found += 1
    
    content, heading_changes = move_markers_around_headings(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return inserted, not_found


# =============================================================================
# SCHRITT 2: PDF-basierte Silbentrennungs-Korrektur
# =============================================================================

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
    """Extrahiert für jede Seite mit Silbentrennung das erste Wort/Fragment."""
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


# =============================================================================
# MAIN
# =============================================================================

def find_md_file(ga_norm: str) -> Optional[Path]:
    """Findet die MD-Datei für eine GA."""
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            for f in folder.glob("*.md"):
                if not re.search(r'\(\d+\.\)', f.stem) and 'kopie' not in f.name.lower():
                    return f
    return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generiert Pagebreaks von Wiki und korrigiert mit PDF'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 1, 102)')
    parser.add_argument('--start-page', '-s', type=int, default=7,
                        help='Startseite (Standard: 7)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Nur simulieren (keine Änderungen)')
    parser.add_argument('--wiki-only', action='store_true',
                        help='Nur Wiki-Schritt ausführen')
    parser.add_argument('--pdf-only', action='store_true',
                        help='Nur PDF-Korrektur ausführen')
    
    args = parser.parse_args()
    
    # Normalisiere GA
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = match.group(1).zfill(3)
    ga_norm = f"GA{ga_num}"
    
    print(f"\n{'='*60}")
    print(f"Pagebreak-Generierung für {ga_norm}")
    print(f"{'='*60}")
    
    # Finde MD-Datei
    md_path = find_md_file(ga_norm)
    if not md_path:
        print(f"FEHLER: Keine MD-Datei gefunden für {ga_norm}")
        return
    
    print(f"MD-Datei: {md_path.name}")
    
    if args.dry_run:
        print("\n*** DRY-RUN MODUS - Keine Änderungen ***\n")
        return
    
    # SCHRITT 1: Wiki
    if not args.pdf_only:
        print(f"\n--- SCHRITT 1: Wiki-Marker von steiner.wiki ---")
        
        html = fetch_online_html(args.ga)
        if not html:
            print("FEHLER: Wiki nicht erreichbar")
            return
        
        markers = extract_page_markers_from_html(html)
        markers = [m for m in markers if m['page'] >= args.start_page]
        print(f"Wiki-Marker gefunden: {len(markers)} (ab Seite {args.start_page})")
        
        if markers:
            inserted, not_found = insert_wiki_markers(md_path, markers, args.start_page)
            print(f"  Eingefügt: {inserted}")
            print(f"  Nicht gefunden: {not_found}")
    
    # SCHRITT 2: PDF-Korrektur
    if not args.wiki_only:
        print(f"\n--- SCHRITT 2: PDF-Silbentrennungs-Korrektur ---")
        
        pdf_path = find_pdf_for_ga(ga_norm)
        if not pdf_path:
            print("WARNUNG: Kein PDF gefunden - überspringe Korrektur")
        else:
            print(f"PDF: {pdf_path.name}")
            
            hyphenations = extract_hyphenations_from_pdf(pdf_path)
            print(f"Silbentrennungen im PDF: {len(hyphenations)}")
            
            if hyphenations:
                corrected, already_ok = correct_hyphenations_with_pdf(md_path, hyphenations)
                print(f"  Bereits korrekt: {already_ok}")
                print(f"  Korrigiert: {corrected}")
    
    print(f"\n{'='*60}")
    print("FERTIG!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
