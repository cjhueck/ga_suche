#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_pagebreaks_from_json.py
============================
Synchronisiert Seitenmarker aus steiner-books JSON-Dateien in MD-Dateien.

Die JSON-Dateien enthalten die korrekten Marker-Positionen.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

PROJECT_DIR = Path(__file__).parent.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"
STEINER_BOOKS_DIR = PROJECT_DIR / "steiner-books"


def find_json_for_ga(ga_num: int) -> Optional[Path]:
    """Findet die JSON-Datei für eine GA."""
    pattern = f"*-{ga_num:03d}-*.json"
    matches = list(STEINER_BOOKS_DIR.glob(pattern))
    
    if not matches:
        # Versuche ohne führende Nullen
        pattern = f"*-{ga_num}-*.json"
        matches = list(STEINER_BOOKS_DIR.glob(pattern))
    
    return matches[0] if matches else None


def find_md_for_ga(ga_num: int) -> Optional[Path]:
    """Findet die MD-Datei für eine GA."""
    ga_norm = f"GA{ga_num:03d}"
    
    for folder in STEINER_GA_DIR.iterdir():
        if folder.is_dir() and folder.name.upper().startswith(ga_norm):
            for f in folder.glob("*.md"):
                if not re.search(r'\(\d+\.\)', f.stem) and 'kopie' not in f.name.lower():
                    return f
    return None


def extract_markers_from_json(json_path: Path) -> List[Dict]:
    """
    Extrahiert Marker und Kontext aus der JSON-Datei.
    
    Returns: Liste von {page, context_before, context_after}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Hole den gesamten Content
    content = ""
    if 'books' in data and data['books']:
        content = data['books'][0].get('content', '')
    elif 'content' in data:
        content = data['content']
    
    if not content:
        return []
    
    markers = []
    
    # Finde alle Marker mit Kontext
    for match in re.finditer(r'(.{0,60})\|(\d+)\|(.{0,60})', content, re.DOTALL):
        context_before = match.group(1)
        page_num = int(match.group(2))
        context_after = match.group(3)
        
        # Bereinige Kontext (entferne andere Marker)
        context_before = re.sub(r'\|\d+\|', '', context_before)
        context_after = re.sub(r'\|\d+\|', '', context_after)
        
        # Letzte 40 Zeichen vor, erste 40 nach
        context_before = context_before[-40:].strip()
        context_after = context_after[:40].strip()
        
        markers.append({
            'page': page_num,
            'context_before': context_before,
            'context_after': context_after
        })
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda x: x['page'])
    
    return markers


def normalize_for_search(text: str) -> str:
    """Normalisiert Text für Suche."""
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\u00ad', '')
    return text.strip()


def is_word_char(char: str) -> bool:
    """Prüft ob ein Zeichen ein Buchstabe ist."""
    return char.isalpha()


def find_position_in_md(md_content: str, start_pos: int, 
                        context_before: str, context_after: str) -> Optional[int]:
    """
    Findet die Position für einen Marker in der MD-Datei.
    Sucht nur nach start_pos.
    """
    search_area = md_content[start_pos:]
    
    # Normalisiere Kontexte
    before_clean = normalize_for_search(context_before)
    after_clean = normalize_for_search(context_after)
    
    # Extrahiere letzte Wörter vor und erste Wörter nach
    before_words = before_clean.split()[-3:] if before_clean else []
    after_words = after_clean.split()[:3] if after_clean else []
    
    if not before_words or not after_words:
        return None
    
    # Methode 1: Suche nach letztem Wort vor + erstem Wort nach
    last_word = before_words[-1] if before_words else ''
    first_word = after_words[0] if after_words else ''
    
    if last_word and first_word and len(last_word) > 2 and len(first_word) > 2:
        for match in re.finditer(re.escape(last_word), search_area, re.IGNORECASE):
            pos_after_word = match.end()
            text_after = search_area[pos_after_word:pos_after_word+100]
            
            # Prüfe ob first_word bald kommt
            first_match = re.search(r'^\s*' + re.escape(first_word), text_after, re.IGNORECASE)
            if first_match:
                # Position ist nach last_word + Whitespace
                ws_match = re.match(r'^\s*', text_after)
                ws_len = len(ws_match.group(0)) if ws_match else 0
                return start_pos + pos_after_word + ws_len
    
    # Methode 2: Mehrwort-Sequenz
    if len(before_words) >= 2:
        search_phrase = ' '.join(before_words[-2:])
        match = re.search(re.escape(search_phrase), search_area, re.IGNORECASE)
        if match:
            pos = match.end()
            text_after = search_area[pos:pos+100]
            
            if after_words:
                first_match = re.search(r'^\s*' + re.escape(after_words[0]), text_after, re.IGNORECASE)
                if first_match:
                    ws_match = re.match(r'^\s*', text_after)
                    ws_len = len(ws_match.group(0)) if ws_match else 0
                    return start_pos + pos + ws_len
    
    return None


def insert_marker(content: str, pos: int, marker: str) -> str:
    """Fügt Marker an Position ein mit korrektem Spacing."""
    if pos <= 0 or pos >= len(content):
        return content[:pos] + marker + content[pos:]
    
    char_before = content[pos-1]
    char_after = content[pos] if pos < len(content) else ' '
    
    inside_word = is_word_char(char_before) and is_word_char(char_after)
    
    if inside_word:
        # Marker innerhalb eines Wortes (Silbentrennung) - ohne Leerzeichen
        return content[:pos] + marker + content[pos:]
    else:
        # Marker zwischen Wörtern - mit Leerzeichen
        prefix = ' ' if is_word_char(char_before) and char_before != ' ' else ''
        suffix = ' ' if is_word_char(char_after) and char_after != ' ' else ''
        return content[:pos] + prefix + marker + suffix + content[pos:]


def sync_markers_to_md(md_path: Path, markers: List[Dict]) -> Tuple[int, int, List[str]]:
    """
    Fügt Marker aus JSON in die MD-Datei ein.
    
    Returns: (inserted, not_found, messages)
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Entferne existierende Marker (aber behalte Newlines!)
    content = re.sub(r' *\|\d+\| *', ' ', content)
    
    inserted = 0
    not_found = 0
    messages = []
    current_pos = 0
    
    for marker_info in markers:
        page = marker_info['page']
        
        pos = find_position_in_md(
            content, current_pos,
            marker_info['context_before'],
            marker_info['context_after']
        )
        
        if pos is not None:
            marker = f'|{page}|'
            content = insert_marker(content, pos, marker)
            
            # Update current_pos (Marker + mögliche Leerzeichen hinzugefügt)
            current_pos = pos + len(marker) + 2
            inserted += 1
            
            # Context für Debug
            ctx = content[max(0, pos-20):pos+len(marker)+20].replace('\n', ' ')
            messages.append(f"Seite {page}: ...{ctx}...")
        else:
            not_found += 1
            messages.append(f"Seite {page}: nicht gefunden")
    
    # Speichere
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return inserted, not_found, messages


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Synchronisiert Seitenmarker aus JSON in MD-Datei'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 4, GA004)')
    parser.add_argument('--dry-run', action='store_true', help='Nur simulieren')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mehr Ausgabe')
    
    args = parser.parse_args()
    
    # Normalisiere GA
    match = re.search(r'(\d+)', args.ga)
    if not match:
        print("Ungültige GA-Nummer")
        return
    
    ga_num = int(match.group(1))
    
    print(f"\n{'='*60}")
    print(f"Synchronisiere Seitenmarker für GA{ga_num:03d}")
    print(f"{'='*60}")
    
    # Finde JSON
    json_path = find_json_for_ga(ga_num)
    if not json_path:
        print(f"FEHLER: Keine JSON-Datei gefunden für GA{ga_num:03d}")
        return
    
    print(f"JSON: {json_path.name}")
    
    # Finde MD
    md_path = find_md_for_ga(ga_num)
    if not md_path:
        print(f"FEHLER: Keine MD-Datei gefunden für GA{ga_num:03d}")
        return
    
    print(f"MD: {md_path.name}")
    
    # Extrahiere Marker aus JSON
    print("\nExtrahiere Marker aus JSON...")
    markers = extract_markers_from_json(json_path)
    print(f"Gefunden: {len(markers)} Marker")
    
    if args.verbose and markers:
        print("\nErste 5 Marker:")
        for m in markers[:5]:
            print(f"  |{m['page']}|: '{m['context_before'][-20:]}' | '{m['context_after'][:20]}'")
    
    if args.dry_run:
        print("\n*** DRY-RUN - keine Änderungen ***")
        return
    
    # Synchronisiere
    print("\nFüge Marker ein...")
    inserted, not_found, messages = sync_markers_to_md(md_path, markers)
    
    print(f"\nErgebnis:")
    print(f"  Eingefügt: {inserted}")
    print(f"  Nicht gefunden: {not_found}")
    
    if args.verbose:
        print("\nDetails:")
        for msg in messages[:30]:
            print(f"  {msg}")
        if len(messages) > 30:
            print(f"  ... und {len(messages) - 30} weitere")
    
    print(f"\n{'='*60}")
    print("FERTIG!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
