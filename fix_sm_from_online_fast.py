#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schnelle Seitenmarker-Einfügung basierend auf steiner.wiki
==========================================================
Optimierte Version ohne langsames Fuzzy-Matching.
Verwendet nur exakte Wort-Suche und Wort-Trennung.
"""

import os
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


def insert_marker_fast(text, page_num, context_before, context_after):
    """
    Schnelle Marker-Einfügung ohne Fuzzy-Matching.
    Verwendet nur exakte Wort-Suche und Wort-Trennung.
    """
    marker = f'|{page_num}|'
    
    if f'|{page_num}|' in text:
        return text, False, "bereits vorhanden"
    
    if not context_before and not context_after:
        return text, False, "kein Kontext"
    
    best_pos = None
    method = ""
    
    # Methode 1: Wort-Trennung (z.B. "dar-" + "stellt" → "darstellt")
    last_before = context_before.rstrip() if context_before else ''
    first_after = context_after.lstrip() if context_after else ''
    
    if last_before and first_after and last_before.endswith('-'):
        word_start = last_before.rstrip('-').split()[-1] if last_before.rstrip('-').split() else ''
        word_end = first_after.split()[0] if first_after.split() else ''
        combined_word = word_start + word_end
        
        if combined_word and len(combined_word) > 4:
            for match in re.finditer(re.escape(combined_word), text, re.IGNORECASE):
                best_pos = match.start() + len(word_start)
                method = "Wort-Trennung"
                break
    
    # Methode 2: Exakte Wort-Sequenz-Suche
    if best_pos is None:
        before_norm = normalize_text(context_before)
        after_norm = normalize_text(context_after)
        before_words = before_norm.split()[-4:] if before_norm else []
        after_words = after_norm.split()[:4] if after_norm else []
        
        if before_words and len(before_words[-1]) > 3:
            last_word = before_words[-1]
            
            for match in re.finditer(re.escape(last_word), text, re.IGNORECASE):
                pos = match.end()
                text_after = text[pos:pos+150]
                
                if after_words and len(after_words[0]) > 2:
                    first_after_word = after_words[0]
                    after_match = re.search(re.escape(first_after_word), text_after, re.IGNORECASE)
                    if after_match:
                        best_pos = pos + after_match.start()
                        method = "Wort-Match"
                        break
    
    # Methode 3: Mehrwort-Sequenz (letzten 2-3 Wörter von before)
    if best_pos is None and before_words and len(before_words) >= 2:
        for num_words in range(min(3, len(before_words)), 1, -1):
            search_phrase = ' '.join(before_words[-num_words:])
            if len(search_phrase) < 8:
                continue
            
            for match in re.finditer(re.escape(search_phrase), text, re.IGNORECASE):
                pos = match.end()
                # Prüfe ob after-Kontext in der Nähe ist
                if after_words:
                    text_after = text[pos:pos+200]
                    first_after = after_words[0]
                    if re.search(re.escape(first_after), text_after, re.IGNORECASE):
                        # Finde genaue Position
                        after_match = re.search(re.escape(first_after), text_after, re.IGNORECASE)
                        if after_match:
                            best_pos = pos + after_match.start()
                            method = "Mehrwort"
                            break
            if best_pos:
                break
    
    if best_pos is None:
        return text, False, "nicht gefunden"
    
    new_text = format_marker_with_spacing(text, best_pos, marker)
    
    # Kurzer Kontext für Info
    ctx_start = max(0, best_pos - 20)
    ctx_end = min(len(new_text), best_pos + len(marker) + 20)
    context = new_text[ctx_start:ctx_end].replace('\n', ' ')
    
    return new_text, True, f"[{method}] '...{context}...'"


def process_file_fast(filepath, markers, dry_run=True, verbose=True):
    """Verarbeitet eine Datei mit schnellem Matching."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0, [f"Fehler beim Lesen: {e}"]
    
    original_content = content
    inserted = 0
    skipped_existing = 0
    not_found = 0
    details = []
    
    total = len(markers)
    
    for i, marker_info in enumerate(markers):
        page = marker_info['page']
        
        if verbose and (i % 50 == 0 or i == total - 1):
            print(f"  Fortschritt: {i+1}/{total} ({100*(i+1)//total}%)", end='\r')
        
        new_content, was_inserted, info = insert_marker_fast(
            content,
            page,
            marker_info['context_before'],
            marker_info['context_after']
        )
        
        if was_inserted:
            content = new_content
            inserted += 1
            details.append(f"Seite {page}: {info}")
        elif "bereits vorhanden" in info:
            skipped_existing += 1
        else:
            not_found += 1
            if verbose:
                details.append(f"Seite {page}: {info}")
    
    if verbose:
        print()  # Neue Zeile nach Fortschritt
    
    # Zusammenfassung
    summary = f"Eingefügt: {inserted}, Bereits vorhanden: {skipped_existing}, Nicht gefunden: {not_found}"
    details.insert(0, summary)
    
    if inserted > 0 and not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            details.append("Änderungen gespeichert.")
        except Exception as e:
            details.append(f"Fehler beim Speichern: {e}")
    
    return inserted, details


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Schnelle Seitenmarker-Einfügung basierend auf steiner.wiki'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 1, 102)')
    parser.add_argument('--file', '-f', type=str, 
                        help='Einzelne Datei verarbeiten')
    parser.add_argument('--apply', action='store_true', 
                        help='Änderungen tatsächlich speichern')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Weniger Ausgabe')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    verbose = not args.quiet
    
    print(f"\n{'='*60}")
    print(f"Schnelle Seitenmarker-Einfügung für GA {args.ga}")
    print(f"Modus: {'SIMULATION' if dry_run else 'SPEICHERN'}")
    print(f"{'='*60}")
    
    # Lade Online-Inhalt
    print("\nLade Online-Version von steiner.wiki...")
    html = fetch_online_html(args.ga)
    
    if not html:
        print("FEHLER: Online-Inhalt nicht verfügbar")
        return
    
    # Extrahiere Marker
    print("Extrahiere Seitenmarker...")
    markers = extract_page_markers_from_html(html)
    print(f"Gefunden: {len(markers)} Seitenmarker")
    
    if not markers:
        print("Keine Marker gefunden.")
        return
    
    # Verarbeite Datei
    if args.file:
        filepath = Path(args.file)
    else:
        # Suche GA-Ordner
        ga_padded = str(args.ga).zfill(3)
        for folder in BASE_PATH.iterdir():
            if folder.is_dir() and folder.name.lower().startswith(f"ga{ga_padded}"):
                # Suche Haupt-MD-Datei
                for md in folder.glob('*.md'):
                    if 'kopie' not in md.name.lower():
                        filepath = md
                        break
                break
        else:
            print(f"FEHLER: GA-Ordner nicht gefunden")
            return
    
    if not filepath.exists():
        print(f"FEHLER: Datei nicht gefunden: {filepath}")
        return
    
    print(f"\nDatei: {filepath.name}")
    print(f"Verarbeite {len(markers)} Marker...\n")
    
    inserted, details = process_file_fast(filepath, markers, dry_run=dry_run, verbose=verbose)
    
    print(f"\n{'-'*60}")
    for detail in details[:30]:  # Erste 30 Details
        print(f"  {detail}")
    
    if len(details) > 30:
        print(f"  ... und {len(details) - 30} weitere")
    
    print(f"{'-'*60}")
    if dry_run:
        print("SIMULATION - keine Änderungen gespeichert")
        print("Mit --apply ausführen, um Änderungen zu speichern")
    else:
        print("Änderungen wurden gespeichert!")


if __name__ == '__main__':
    main()
