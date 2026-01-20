#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seitenmarker-Korrektur basierend auf steiner.wiki
=================================================
Korrigiert die Position von Seitenmarkern (|123|) in lokalen GA-Dateien
anhand der Online-Version von steiner.wiki.

In der Online-Version stehen Seitenzahlen als eigenständige Zeilen oder
mit Absatzumbrüchen, was die korrekte Position anzeigt.
"""

import os
import re
import sys
import difflib
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Konfiguration
BASE_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"


def fetch_online_html(ga_nummer):
    """Lädt den HTML-Inhalt von steiner.wiki"""
    # GA-Nummer ohne führende Nullen
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
    """
    Extrahiert Seitenzahlen und deren Kontext aus der Online-Version.
    
    In steiner.wiki stehen Seitenzahlen oft als:
    - Eigenständige Zeilen/Absätze mit nur einer Zahl
    - Am Ende eines Absatzes vor dem Umbruch
    
    Verwendet 100 Zeichen Kontext vor und nach dem Seitenumbruch.
    
    Rückgabe: Liste von {page: int, context_before: str, context_after: str}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    content = soup.find('div', {'class': 'mw-parser-output'})
    if not content:
        content = soup
    
    markers = []
    
    # Sammle allen Text mit Struktur
    elements = content.find_all(['p', 'div', 'span'])
    full_text_parts = []
    
    for elem in elements:
        text = elem.get_text()
        if text.strip():
            full_text_parts.append(text)
    
    full_text = '\n'.join(full_text_parts)
    
    # Entferne Soft-Hyphens für besseres Matching
    full_text = full_text.replace('\u00ad', '')
    
    # Suche nach Seitenzahlen-Mustern
    # Regex: Zahl die von Zeilenumbrüchen umgeben ist (mit 150 Zeichen Kontext)
    pattern = r'([^\n]{0,150})\n\s*(\d{1,4})\s*\n([^\n]{0,150})'
    
    for match in re.finditer(pattern, full_text):
        context_before = match.group(1).strip()
        page_num = int(match.group(2))
        context_after = match.group(3).strip()
        
        # Filter: Nur plausible Seitenzahlen (1-999)
        if 1 <= page_num <= 999:
            # Ignoriere wenn Kontext zu kurz (wahrscheinlich keine echte Seitenzahl)
            if len(context_before) > 10 or len(context_after) > 10:
                markers.append({
                    'page': page_num,
                    # 100 Zeichen Kontext
                    'context_before': context_before[-100:] if len(context_before) > 100 else context_before,
                    'context_after': context_after[:100] if len(context_after) > 100 else context_after
                })
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda x: x['page'])
    
    # Entferne Duplikate (gleiche Seitenzahl)
    seen = set()
    unique_markers = []
    for m in markers:
        if m['page'] not in seen:
            seen.add(m['page'])
            unique_markers.append(m)
    
    return unique_markers


def normalize_text(text):
    """Normalisiert Text für Vergleich"""
    # Entferne Seitenmarker
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'\*\*\d+\*\*', '', text)
    # Entferne Block-IDs
    text = re.sub(r'\^[a-z0-9]+', '', text)
    # Entferne Markdown
    text = re.sub(r'#.*?\n', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    # Entferne Soft-Hyphens
    text = text.replace('\u00ad', '')
    text = text.replace('-\n', '')
    return text.strip()


def find_position_in_local(local_text, context_before, context_after):
    """
    Findet die Position im lokalen Text basierend auf dem Online-Kontext.
    
    Rückgabe: Position (int) oder None
    """
    # Normalisiere
    local_norm = normalize_text(local_text)
    before_norm = normalize_text(context_before)
    after_norm = normalize_text(context_after)
    
    if not before_norm and not after_norm:
        return None
    
    # Suche nach der Kombination von Kontext
    search_pattern = before_norm[-40:] + '.*?' + after_norm[:40]
    
    try:
        # Escape spezielle Regex-Zeichen
        search_escaped = re.escape(before_norm[-40:]) + r'.{0,50}' + re.escape(after_norm[:40])
        match = re.search(search_escaped, local_norm, re.IGNORECASE)
        
        if match:
            # Finde Position zwischen before und after
            before_end = match.start() + len(before_norm[-40:])
            return before_end
    except:
        pass
    
    # Fallback: Suche nur nach before-Kontext
    if before_norm:
        try:
            search = re.escape(before_norm[-50:])
            match = re.search(search, local_norm, re.IGNORECASE)
            if match:
                return match.end()
        except:
            pass
    
    return None


def find_marker_in_local(local_text, page_num):
    """Findet die aktuelle Position eines Seitenmarkers im lokalen Text"""
    pattern = rf'\|{page_num}\|'
    match = re.search(pattern, local_text)
    if match:
        return match.start(), match.end()
    return None, None


def get_context_at_position(text, pos, chars=50):
    """Gibt den Kontext um eine Position zurück"""
    start = max(0, pos - chars)
    end = min(len(text), pos + chars)
    return text[start:end]


def is_word_char(char):
    """Prüft ob ein Zeichen ein Wort-Zeichen ist (Buchstabe)"""
    return char.isalpha()


def format_marker_with_spacing(text, pos, marker):
    """
    Fügt einen Marker an Position pos ein, mit korrekter Leerzeichen-Formatierung.
    
    - Wenn der Marker ein Wort trennt: ohne Leerzeichen (dar|10|stellt)
    - Wenn der Marker zwischen Wörtern steht: mit Leerzeichen ( |10| )
    
    Rückgabe: Text mit eingefügtem Marker
    """
    # Zeichen vor und nach der Position
    char_before = text[pos-1] if pos > 0 else ' '
    char_after = text[pos] if pos < len(text) else ' '
    
    # Prüfe ob wir innerhalb eines Wortes sind
    inside_word = is_word_char(char_before) and is_word_char(char_after)
    
    if inside_word:
        # Wort-Trennung: kein Leerzeichen
        return text[:pos] + marker + text[pos:]
    else:
        # Zwischen Wörtern: mit Leerzeichen
        # Prüfe ob bereits Leerzeichen vorhanden
        needs_space_before = is_word_char(char_before)
        needs_space_after = is_word_char(char_after)
        
        prefix = ' ' if needs_space_before else ''
        suffix = ' ' if needs_space_after else ''
        
        return text[:pos] + prefix + marker + suffix + text[pos:]


def correct_marker_position(local_text, page_num, correct_context_before, correct_context_after):
    """
    Korrigiert die Position eines Seitenmarkers im lokalen Text.
    Verwendet Fuzzy-Matching mit 100 Zeichen Kontext.
    
    Rückgabe: (korrigierter_text, wurde_korrigiert, info)
    """
    marker = f'|{page_num}|'
    
    # Finde aktuelle Position des Markers
    current_start, current_end = find_marker_in_local(local_text, page_num)
    
    if current_start is None:
        return local_text, False, f"Marker {marker} nicht im lokalen Text gefunden"
    
    # Entferne alten Marker inklusive umgebende Leerzeichen falls vorhanden
    text_without_marker = local_text[:current_start] + local_text[current_end:]
    
    # Entferne überschüssige Leerzeichen um die alte Marker-Position
    if current_start > 0 and current_start < len(text_without_marker):
        if text_without_marker[current_start-1:current_start+1] == '  ':
            text_without_marker = text_without_marker[:current_start] + text_without_marker[current_start+1:]
    
    best_pos = None
    method_used = ""
    
    # Methode 1: Prüfe ob Online-Kontext eine Wort-Trennung zeigt
    last_before = correct_context_before.rstrip() if correct_context_before else ''
    first_after = correct_context_after.lstrip() if correct_context_after else ''
    
    if last_before and first_after and last_before.endswith('-'):
        word_start = last_before.rstrip('-').split()[-1] if last_before.rstrip('-').split() else ''
        word_end = first_after.split()[0] if first_after.split() else ''
        combined_word = word_start + word_end
        
        if combined_word and len(combined_word) > 3:
            for match in re.finditer(re.escape(combined_word), text_without_marker, re.IGNORECASE):
                best_pos = match.start() + len(word_start)
                method_used = "Wort-Trennung"
                break
    
    # Methode 2: Fuzzy-Matching
    if best_pos is None:
        approx_pos, score = fuzzy_find_context(text_without_marker, correct_context_before, correct_context_after, min_score=0.5)
        
        if approx_pos is not None:
            best_pos = find_exact_break_position(text_without_marker, approx_pos, correct_context_before, correct_context_after)
            method_used = f"Fuzzy ({score:.0%})"
    
    # Methode 3: Wort-basierte Suche als Fallback
    if best_pos is None:
        before_norm = normalize_text(correct_context_before)
        after_norm = normalize_text(correct_context_after)
        before_words = before_norm.split()[-4:] if before_norm else []
        after_words = after_norm.split()[:4] if after_norm else []
        
        if before_words:
            last_word = before_words[-1]
            
            if len(last_word) > 3:
                for match in re.finditer(re.escape(last_word), text_without_marker, re.IGNORECASE):
                    pos = match.end()
                    text_after = text_without_marker[pos:pos+100]
                    
                    if after_words:
                        first_after_word = after_words[0]
                        after_match = re.search(re.escape(first_after_word), text_after, re.IGNORECASE)
                        if after_match:
                            best_pos = pos + after_match.start()
                            method_used = "Wort-Match"
                            break
    
    if best_pos is None:
        return local_text, False, "Korrekte Position nicht gefunden"
    
    # Ist die Position ähnlich? (Toleranz von 10 Zeichen)
    if abs(current_start - best_pos) <= 10:
        return local_text, False, "Position bereits korrekt"
    
    # Erstelle neuen Text mit korrigiertem Marker und korrekter Formatierung
    new_text = format_marker_with_spacing(text_without_marker, best_pos, marker)
    
    old_context = get_context_at_position(local_text, current_start, 30)
    new_context = get_context_at_position(new_text, best_pos, 30)
    
    info = f"[{method_used}] '...{old_context}...' -> '...{new_context}...'"
    
    return new_text, True, info


def fuzzy_find_context(text, context_before, context_after, min_score=0.6):
    """
    Findet die Position im Text mittels Fuzzy-Matching.
    Verwendet 100 Zeichen Kontext vor und nach dem Seitenumbruch.
    
    Rückgabe: (position, score) oder (None, 0)
    """
    text_norm = normalize_text(text)
    before_norm = normalize_text(context_before)
    after_norm = normalize_text(context_after)
    
    if not before_norm and not after_norm:
        return None, 0
    
    # Kombinierter Suchstring: Ende von before + Anfang von after
    # Nimm die letzten 50 Zeichen von before und ersten 50 von after
    search_before = before_norm[-50:] if len(before_norm) > 50 else before_norm
    search_after = after_norm[:50] if len(after_norm) > 50 else after_norm
    
    best_pos = None
    best_score = 0
    
    # Sliding Window Suche
    window_size = len(search_before) + len(search_after) + 20
    
    for i in range(0, len(text_norm) - window_size + 1, 5):  # Schrittweite 5 für Geschwindigkeit
        window = text_norm[i:i + window_size]
        
        # Teile das Fenster in zwei Hälften
        mid = len(window) // 2
        window_before = window[:mid + 10]
        window_after = window[mid - 10:]
        
        # Berechne Ähnlichkeit für beide Teile
        score_before = difflib.SequenceMatcher(None, search_before, window_before[-len(search_before)-10:]).ratio()
        score_after = difflib.SequenceMatcher(None, search_after, window_after[:len(search_after)+10]).ratio()
        
        # Kombinierter Score
        combined_score = (score_before + score_after) / 2
        
        if combined_score > best_score:
            best_score = combined_score
            # Position ist ungefähr in der Mitte des Fensters
            best_pos = i + mid
    
    if best_score >= min_score:
        return best_pos, best_score
    
    return None, best_score


def find_exact_break_position(text, approx_pos, context_before, context_after):
    """
    Findet die exakte Umbruch-Position basierend auf einer ungefähren Position.
    Sucht nach dem besten Übergang zwischen before- und after-Kontext.
    """
    before_norm = normalize_text(context_before)
    after_norm = normalize_text(context_after)
    
    # Nimm letzte Wörter von before und erste von after
    before_words = before_norm.split()[-3:] if before_norm else []
    after_words = after_norm.split()[:3] if after_norm else []
    
    if not before_words or not after_words:
        return approx_pos
    
    # Suche im Bereich um approx_pos
    search_start = max(0, approx_pos - 200)
    search_end = min(len(text), approx_pos + 200)
    search_area = text[search_start:search_end]
    
    # Suche nach dem letzten Wort von before
    last_before_word = before_words[-1]
    first_after_word = after_words[0]
    
    # Finde alle Vorkommen des letzten before-Wortes
    for match in re.finditer(re.escape(last_before_word), search_area, re.IGNORECASE):
        pos_after_word = search_start + match.end()
        
        # Prüfe ob das erste after-Wort danach kommt
        text_after = text[pos_after_word:pos_after_word + 100]
        
        if re.search(re.escape(first_after_word), text_after, re.IGNORECASE):
            # Finde genaue Position (zwischen den Wörtern)
            after_match = re.search(re.escape(first_after_word), text_after, re.IGNORECASE)
            if after_match:
                return pos_after_word + after_match.start()
    
    return approx_pos


def insert_new_marker(text, page_num, context_before, context_after):
    """
    Fügt einen neuen Seitenmarker in den Text ein, basierend auf dem Online-Kontext.
    Verwendet Fuzzy-Matching mit 100 Zeichen Kontext vor und nach dem Umbruch.
    
    Rückgabe: (neuer_text, wurde_eingefügt, info)
    """
    marker = f'|{page_num}|'
    
    # Prüfe ob Marker bereits existiert
    if f'|{page_num}|' in text:
        return text, False, f"Marker {marker} existiert bereits"
    
    if not context_before and not context_after:
        return text, False, "Nicht genug Kontext"
    
    best_pos = None
    method_used = ""
    
    # Methode 1: Prüfe ob Online-Kontext eine Wort-Trennung zeigt (z.B. "dar-" + "stellt")
    last_before = context_before.rstrip() if context_before else ''
    first_after = context_after.lstrip() if context_after else ''
    
    if last_before and first_after and last_before.endswith('-'):
        # Wort-Trennung erkannt
        word_start = last_before.rstrip('-').split()[-1] if last_before.rstrip('-').split() else ''
        word_end = first_after.split()[0] if first_after.split() else ''
        combined_word = word_start + word_end
        
        if combined_word and len(combined_word) > 4:
            # Suche das kombinierte Wort
            for match in re.finditer(re.escape(combined_word), text, re.IGNORECASE):
                best_pos = match.start() + len(word_start)
                method_used = "Wort-Trennung"
                break
    
    # Methode 2: Fuzzy-Matching mit kombiniertem Kontext
    if best_pos is None:
        approx_pos, score = fuzzy_find_context(text, context_before, context_after, min_score=0.5)
        
        if approx_pos is not None:
            # Verfeinere die Position
            best_pos = find_exact_break_position(text, approx_pos, context_before, context_after)
            method_used = f"Fuzzy ({score:.0%})"
    
    # Methode 3: Exakte Wort-Suche als Fallback
    if best_pos is None:
        before_norm = normalize_text(context_before)
        after_norm = normalize_text(context_after)
        before_words = before_norm.split()[-4:] if before_norm else []
        after_words = after_norm.split()[:4] if after_norm else []
        
        if before_words and after_words:
            # Suche nach Kombination der letzten/ersten Wörter
            for num_before in range(len(before_words), 0, -1):
                search_phrase = ' '.join(before_words[-num_before:])
                if len(search_phrase) < 8:
                    continue
                
                text_norm = normalize_text(text)
                for match in re.finditer(re.escape(search_phrase), text_norm, re.IGNORECASE):
                    # Prüfe ob after-Kontext folgt
                    pos = match.end()
                    remaining = text_norm[pos:pos + 150]
                    
                    first_after = after_words[0]
                    if first_after.lower() in remaining.lower()[:100]:
                        # Finde Position im Originaltext
                        # Mapping von normalisierter zu Original-Position
                        best_pos = find_original_position(text, pos, search_phrase, first_after)
                        if best_pos:
                            method_used = "Wort-Match"
                            break
                
                if best_pos is not None:
                    break
    
    if best_pos is None:
        return text, False, f"Position für Seite {page_num} nicht gefunden"
    
    # Füge Marker mit korrekter Formatierung ein
    new_text = format_marker_with_spacing(text, best_pos, marker)
    
    context = get_context_at_position(new_text, best_pos, 25)
    info = f"[{method_used}] '...{context}...'"
    
    return new_text, True, info


def find_original_position(text, norm_pos, before_phrase, after_word):
    """
    Findet die Position im Originaltext basierend auf normalisierten Phrasen.
    """
    # Suche die before_phrase im Originaltext
    before_words = before_phrase.split()
    if not before_words:
        return None
    
    last_word = before_words[-1]
    
    for match in re.finditer(re.escape(last_word), text, re.IGNORECASE):
        pos = match.end()
        # Prüfe ob after_word danach kommt
        remaining = text[pos:pos + 100]
        after_match = re.search(re.escape(after_word), remaining, re.IGNORECASE)
        if after_match:
            return pos + after_match.start()
    
    return None


def normalize_marker_spacing(text):
    """
    Normalisiert die Leerzeichen um alle Seitenmarker im Text.
    
    - Wort-Trennung: kein Leerzeichen (dar|10|stellt)
    - Zwischen Wörtern: mit Leerzeichen (Ende |10| Anfang)
    
    Rückgabe: (normalisierter_text, anzahl_änderungen)
    """
    changes = 0
    
    # Finde alle Marker
    pattern = r'(\s*)\|(\d+)\|(\s*)'
    
    def replace_marker(match):
        nonlocal changes
        space_before = match.group(1)
        page_num = match.group(2)
        space_after = match.group(3)
        marker = f'|{page_num}|'
        
        # Position im Originaltext
        start = match.start()
        end = match.end()
        
        # Zeichen vor dem Leerzeichen/Marker
        pos_before = start - 1 if start > 0 else -1
        char_before = text[pos_before] if pos_before >= 0 else ' '
        
        # Zeichen nach dem Leerzeichen/Marker
        pos_after = end
        char_after = text[pos_after] if pos_after < len(text) else ' '
        
        # Prüfe ob wir innerhalb eines Wortes sind (nach Entfernen der Leerzeichen)
        # Hole das echte Zeichen vor space_before
        real_pos_before = start - len(space_before) - 1 if start > len(space_before) else -1
        real_char_before = text[real_pos_before] if real_pos_before >= 0 else ' '
        
        inside_word = is_word_char(real_char_before) and is_word_char(char_after)
        
        if inside_word:
            # Wort-Trennung: kein Leerzeichen
            if space_before or space_after:
                changes += 1
            return marker
        else:
            # Zwischen Wörtern
            needs_before = is_word_char(real_char_before) and not space_before
            needs_after = is_word_char(char_after) and not space_after
            
            new_before = ' ' if is_word_char(real_char_before) else ''
            new_after = ' ' if is_word_char(char_after) else ''
            
            result = new_before + marker + new_after
            
            if space_before.strip() != new_before.strip() or space_after.strip() != new_after.strip():
                changes += 1
            
            return result
    
    # Ersetze alle Marker mit korrekter Formatierung
    new_text = re.sub(pattern, replace_marker, text)
    
    # Bereinige doppelte Leerzeichen
    new_text = re.sub(r'  +', ' ', new_text)
    
    return new_text, changes


def process_ga_file(filepath, online_markers, dry_run=True, insert_missing=True):
    """
    Verarbeitet eine GA-Datei und korrigiert/fügt Seitenmarker ein.
    
    Args:
        filepath: Pfad zur Markdown-Datei
        online_markers: Liste der Online-Marker mit Kontext
        dry_run: Wenn True, werden keine Änderungen gespeichert
        insert_missing: Wenn True, werden fehlende Marker eingefügt
    
    Rückgabe: (anzahl_korrekturen, details)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0, [f"Fehler beim Lesen: {e}"]
    
    original_content = content
    corrections = []
    inserted = 0
    corrected = 0
    
    for marker_info in online_markers:
        page = marker_info['page']
        
        # Prüfe ob dieser Marker in der Datei existiert
        if f'|{page}|' in content:
            # Marker existiert -> Position korrigieren
            new_content, was_corrected, info = correct_marker_position(
                content,
                page,
                marker_info['context_before'],
                marker_info['context_after']
            )
            
            if was_corrected:
                content = new_content
                corrections.append(f"Seite {page} korrigiert: {info}")
                corrected += 1
        
        elif insert_missing:
            # Marker fehlt -> Neu einfügen
            new_content, was_inserted, info = insert_new_marker(
                content,
                page,
                marker_info['context_before'],
                marker_info['context_after']
            )
            
            if was_inserted:
                content = new_content
                corrections.append(f"Seite {page} eingefügt: {info}")
                inserted += 1
    
    # Dann: Leerzeichen-Formatierung normalisieren
    content, spacing_changes = normalize_marker_spacing(content)
    if spacing_changes > 0:
        corrections.append(f"Leerzeichen bei {spacing_changes} Marker(n) korrigiert")
    
    # Zusammenfassung
    if inserted > 0 or corrected > 0:
        summary = []
        if inserted > 0:
            summary.append(f"{inserted} neu eingefügt")
        if corrected > 0:
            summary.append(f"{corrected} korrigiert")
        corrections.insert(0, f"Zusammenfassung: {', '.join(summary)}")
    
    if corrections and not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            return 0, [f"Fehler beim Speichern: {e}"]
    
    return len(corrections), corrections


def find_ga_folder(ga_nummer):
    """Findet den Ordner für eine GA-Nummer"""
    ga_str = str(ga_nummer).lower().lstrip('0') or '0'
    ga_padded = ga_str.zfill(3)
    
    for folder in BASE_PATH.iterdir():
        if folder.is_dir():
            name = folder.name.lower()
            # Verschiedene Namensformate
            if (name.startswith(f"ga{ga_str}-") or 
                name.startswith(f"ga{ga_str} -") or
                name.startswith(f"ga{ga_padded}-") or
                name.startswith(f"ga{ga_padded} -")):
                return folder
    return None


def process_ga(ga_nummer, dry_run=True, verbose=True):
    """
    Verarbeitet alle Dateien einer GA.
    
    Args:
        ga_nummer: GA-Nummer
        dry_run: Wenn True, nur Simulation
        verbose: Ausführliche Ausgabe
    """
    print(f"\n{'='*60}")
    print(f"Verarbeite GA {ga_nummer}" + (" (Simulation)" if dry_run else ""))
    print('='*60)
    
    # Lade Online-Inhalt
    print("Lade Online-Version von steiner.wiki...")
    html = fetch_online_html(ga_nummer)
    
    if not html:
        print("FEHLER: Online-Inhalt nicht verfügbar")
        return
    
    # Extrahiere Marker aus Online-Version
    online_markers = extract_page_markers_from_html(html)
    print(f"Gefunden: {len(online_markers)} Seitenmarker in Online-Version")
    
    if verbose and online_markers:
        print("\nBeispiel-Marker aus Online:")
        for m in online_markers[:3]:
            print(f"  Seite {m['page']}: '...{m['context_before'][-30:]}' | '{m['context_after'][:30]}...'")
    
    # Finde GA-Ordner
    ga_folder = find_ga_folder(ga_nummer)
    if not ga_folder:
        print(f"FEHLER: GA-Ordner nicht gefunden")
        return
    
    print(f"\nGA-Ordner: {ga_folder.name}")
    
    # Verarbeite alle Markdown-Dateien
    md_files = list(ga_folder.glob('*.md'))
    print(f"Gefunden: {len(md_files)} Markdown-Dateien")
    
    total_corrections = 0
    
    for filepath in md_files:
        num_corrections, details = process_ga_file(filepath, online_markers, dry_run, insert_missing=True)
        
        if num_corrections > 0:
            print(f"\n📄 {filepath.name}")
            print(f"   {num_corrections} Änderung(en):")
            for detail in details:
                print(f"   - {detail}")
            total_corrections += num_corrections
    
    print(f"\n{'─'*60}")
    print(f"Gesamt: {total_corrections} Korrektur(en)" + 
          (" (nicht gespeichert - Simulation)" if dry_run else " (gespeichert)"))


def process_single_file(filepath, ga_nummer, dry_run=True, verbose=True):
    """
    Verarbeitet eine einzelne Datei.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"FEHLER: Datei nicht gefunden: {filepath}")
        return
    
    print(f"\n{'='*60}")
    print(f"Verarbeite Datei: {filepath.name}")
    print(f"GA: {ga_nummer}" + (" (Simulation)" if dry_run else ""))
    print('='*60)
    
    # Lade Online-Inhalt
    print("Lade Online-Version von steiner.wiki...")
    html = fetch_online_html(ga_nummer)
    
    if not html:
        print("FEHLER: Online-Inhalt nicht verfügbar")
        return
    
    # Extrahiere Marker aus Online-Version
    online_markers = extract_page_markers_from_html(html)
    print(f"Gefunden: {len(online_markers)} Seitenmarker in Online-Version")
    
    if verbose and online_markers:
        print("\nBeispiel-Marker aus Online:")
        for m in online_markers[:5]:
            print(f"  Seite {m['page']}: '...{m['context_before'][-30:]}' | '{m['context_after'][:30]}...'")
    
    # Verarbeite Datei
    num_corrections, details = process_ga_file(filepath, online_markers, dry_run, insert_missing=True)
    
    if num_corrections > 0:
        print(f"\n{num_corrections} Änderung(en):")
        for detail in details:
            print(f"  - {detail}")
    else:
        print("\nKeine Änderungen notwendig.")
    
    print(f"\n{'─'*60}")
    if dry_run:
        print("(Simulation - keine Änderungen gespeichert)")
    else:
        print("Änderungen gespeichert.")


def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Korrigiert Seitenmarker in GA-Dateien basierend auf steiner.wiki'
    )
    parser.add_argument('ga', type=str, help='GA-Nummer (z.B. 1, 102)')
    parser.add_argument('--file', '-f', type=str, 
                        help='Einzelne Datei verarbeiten (statt gesamte GA)')
    parser.add_argument('--apply', action='store_true', 
                        help='Änderungen tatsächlich speichern (sonst nur Simulation)')
    parser.add_argument('--no-insert', action='store_true',
                        help='Keine neuen Marker einfügen, nur korrigieren')
    parser.add_argument('--quiet', action='store_true',
                        help='Weniger Ausgabe')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    verbose = not args.quiet
    
    if not dry_run:
        print("⚠️  ACHTUNG: Änderungen werden gespeichert!")
        response = input("Fortfahren? (j/n): ")
        if response.lower() != 'j':
            print("Abgebrochen.")
            return
    
    if args.file:
        process_single_file(args.file, args.ga, dry_run=dry_run, verbose=verbose)
    else:
        process_ga(args.ga, dry_run=dry_run, verbose=verbose)


if __name__ == '__main__':
    main()
