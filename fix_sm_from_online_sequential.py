#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sequentielle Seitenmarker-Einfügung basierend auf steiner.wiki
==============================================================
Die Marker werden SEQUENTIELL eingefügt - jeder neue Marker wird
NUR NACH dem vorherigen gesucht, um die korrekte Reihenfolge zu garantieren.
"""

import re
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Konfiguration
BASE_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"


def fetch_online_html(ga_nummer):
    """Lädt den HTML-Inhalt von steiner.wiki"""
    ga_num = str(ga_nummer).lstrip('0') or '0'
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
    
    # Regex: Zahl die von Zeilenumbrüchen umgeben ist
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
    
    # Entferne Duplikate
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
    """
    Findet die Position für einen Marker, aber NUR NACH start_pos.
    Dies garantiert die sequentielle Reihenfolge der Marker.
    
    Rückgabe: (position, method) oder (None, None)
    """
    # Nur im Text nach start_pos suchen
    search_text = text[start_pos:]
    
    before_norm = normalize_text(context_before) if context_before else ''
    after_norm = normalize_text(context_after) if context_after else ''
    before_words = before_norm.split()[-4:] if before_norm else []
    after_words = after_norm.split()[:4] if after_norm else []
    
    # Methode 1: Wort-Trennung (z.B. "dar-" + "stellt" → "darstellt")
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


def process_file_sequential(filepath, markers, start_page=None, dry_run=True, verbose=True):
    """
    Verarbeitet eine Datei mit SEQUENTIELLER Marker-Einfügung.
    Jeder Marker wird nur nach dem vorherigen gesucht.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0, [f"Fehler beim Lesen: {e}"]
    
    # Filtere Marker auf die gewünschte Startseite
    if start_page:
        markers = [m for m in markers if m['page'] >= start_page]
    
    inserted = 0
    not_found = 0
    details = []
    
    total = len(markers)
    current_pos = 0  # Startposition für sequentielle Suche
    
    for i, marker_info in enumerate(markers):
        page = marker_info['page']
        
        if verbose and (i % 20 == 0 or i == total - 1):
            print(f"  Fortschritt: {i+1}/{total} ({100*(i+1)//total}%) - Pos: {current_pos}", end='\r')
        
        # Prüfe ob Marker bereits existiert
        if f'|{page}|' in content:
            # Finde Position des existierenden Markers
            existing_pos = content.find(f'|{page}|')
            if existing_pos > current_pos:
                current_pos = existing_pos + len(f'|{page}|')
            details.append(f"Seite {page}: bereits vorhanden")
            continue
        
        # Suche Position NUR NACH current_pos
        pos, method = find_marker_position_after(
            content, 
            current_pos,
            marker_info['context_before'],
            marker_info['context_after']
        )
        
        if pos is not None:
            marker = f'|{page}|'
            content = format_marker_with_spacing(content, pos, marker)
            
            # Update current_pos für nächsten Marker
            current_pos = pos + len(marker) + 2  # +2 für mögliche Leerzeichen
            
            inserted += 1
            
            # Kontext für Info
            ctx_start = max(0, pos - 15)
            ctx_end = min(len(content), pos + len(marker) + 15)
            context = content[ctx_start:ctx_end].replace('\n', ' ')
            details.append(f"Seite {page}: [{method}] '...{context}...'")
        else:
            not_found += 1
            details.append(f"Seite {page}: nicht gefunden (nach Pos {current_pos})")
    
    if verbose:
        print()  # Neue Zeile nach Fortschritt
    
    # Zusammenfassung
    summary = f"Eingefuegt: {inserted}, Nicht gefunden: {not_found}"
    details.insert(0, summary)
    
    if inserted > 0 and not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            details.append("Aenderungen gespeichert.")
        except Exception as e:
            details.append(f"Fehler beim Speichern: {e}")
    
    return inserted, details


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sequentielle Seitenmarker-Einfuegung basierend auf steiner.wiki'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 1, 102)')
    parser.add_argument('--file', '-f', type=str, 
                        help='Einzelne Datei verarbeiten')
    parser.add_argument('--start-page', '-s', type=int, default=7,
                        help='Startseite (Standard: 7)')
    parser.add_argument('--apply', action='store_true', 
                        help='Aenderungen tatsaechlich speichern')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Weniger Ausgabe')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    verbose = not args.quiet
    
    print(f"\n{'='*60}")
    print(f"Sequentielle Seitenmarker-Einfuegung fuer GA {args.ga}")
    print(f"Startseite: {args.start_page}")
    print(f"Modus: {'SIMULATION' if dry_run else 'SPEICHERN'}")
    print(f"{'='*60}")
    
    # Lade Online-Inhalt
    print("\nLade Online-Version von steiner.wiki...")
    html = fetch_online_html(args.ga)
    
    if not html:
        print("FEHLER: Online-Inhalt nicht verfuegbar")
        return
    
    # Extrahiere Marker
    print("Extrahiere Seitenmarker...")
    markers = extract_page_markers_from_html(html)
    print(f"Gefunden: {len(markers)} Seitenmarker")
    
    # Filtere auf Startseite
    markers = [m for m in markers if m['page'] >= args.start_page]
    print(f"Nach Filter (>= Seite {args.start_page}): {len(markers)} Marker")
    
    if not markers:
        print("Keine Marker gefunden.")
        return
    
    # Zeige erste Marker
    print(f"\nErste 5 Marker:")
    for m in markers[:5]:
        print(f"  Seite {m['page']}: '...{m['context_before'][-30:]}' | '{m['context_after'][:30]}...'")
    
    # Verarbeite Datei
    if args.file:
        filepath = Path(args.file)
    else:
        # Suche GA-Ordner
        ga_padded = str(args.ga).zfill(3)
        filepath = None
        for folder in BASE_PATH.iterdir():
            if folder.is_dir() and folder.name.lower().startswith(f"ga{ga_padded}"):
                for md in folder.glob('*.md'):
                    if 'kopie' not in md.name.lower():
                        filepath = md
                        break
                break
        
        if filepath is None:
            print(f"FEHLER: GA-Ordner nicht gefunden")
            return
    
    if not filepath.exists():
        print(f"FEHLER: Datei nicht gefunden: {filepath}")
        return
    
    print(f"\nDatei: {filepath.name}")
    print(f"Verarbeite {len(markers)} Marker SEQUENTIELL...\n")
    
    inserted, details = process_file_sequential(
        filepath, markers, 
        start_page=args.start_page,
        dry_run=dry_run, 
        verbose=verbose
    )
    
    print(f"\n{'-'*60}")
    for detail in details[:50]:  # Erste 50 Details
        print(f"  {detail}")
    
    if len(details) > 50:
        print(f"  ... und {len(details) - 50} weitere")
    
    print(f"{'-'*60}")
    if dry_run:
        print("SIMULATION - keine Aenderungen gespeichert")
        print("Mit --apply ausfuehren, um Aenderungen zu speichern")
    else:
        print("Aenderungen wurden gespeichert!")


if __name__ == '__main__':
    main()
