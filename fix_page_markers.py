#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seitenzahlen-Marker Korrektur
=============================
Korrigiert die Positionen der Seitenzahlen-Marker in GA-Texten
basierend auf der Online-Version von steiner.wiki
"""

import re
import sys
import io
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional

# UTF-8 Ausgabe für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"

# Monats-Mapping
MONAT_MAPPING = {
    'januar': 1, 'jan': 1,
    'februar': 2, 'feb': 2,
    'märz': 3, 'maerz': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'mai': 5,
    'juni': 6, 'jun': 6,
    'juli': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9, 'sept': 9,
    'oktober': 10, 'okt': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'dezember': 12, 'dez': 12, 'dec': 12,
}


def fetch_online_content(ga_nummer: str) -> Optional[str]:
    """Lädt den Inhalt einer GA-Seite von steiner.wiki"""
    url = STEINER_WIKI_BASE.format(ga_nummer)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return None


def extract_page_contexts(html_content: str) -> Dict[int, Tuple[str, str, bool]]:
    """
    Extrahiert den Kontext um jede Seitenzahl aus der Online-Version.
    Gibt zurück: {seitenzahl: (wort_davor, wort_danach, ist_silbentrennung)}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Hole den gesamten Text mit Platzhaltern für Seitenzahlen
    # Ersetze <b>XX</b> durch spezielle Marker
    for b_tag in soup.find_all('b'):
        txt = b_tag.get_text().strip()
        if txt.isdigit() and 10 <= int(txt) <= 500:
            b_tag.replace_with(f'###PAGE_{txt}###')
    
    # Hole den bereinigten Text
    full_text = soup.get_text()
    
    page_contexts = {}
    
    # Finde alle Seitenzahlen-Marker mit Kontext
    pattern = r'(\S*)\s*###PAGE_(\d+)###\s*(\S*)'
    
    for match in re.finditer(pattern, full_text):
        wort_davor = match.group(1)
        page_num = int(match.group(2))
        wort_danach = match.group(3)
        
        # Bereinige die Wörter
        wort_davor = wort_davor.strip() if wort_davor else ''
        wort_danach = wort_danach.strip() if wort_danach else ''
        
        # Prüfe auf Silbentrennung
        ist_silbentrennung = False
        
        # Wenn das Wort davor mit Bindestrich endet -> Silbentrennung
        if wort_davor and wort_davor.endswith('-'):
            ist_silbentrennung = True
            wort_davor = wort_davor[:-1]
        
        # Wenn das nächste Wort mit Kleinbuchstabe beginnt
        # und es kein häufiges Wort am Satzanfang ist -> wahrscheinlich Silbentrennung
        common_start_words = ('und', 'oder', 'aber', 'denn', 'weil', 'wenn', 'wie', 'so', 
                               'da', 'als', 'auch', 'noch', 'nun', 'nur', 'schon', 'sehr',
                               'was', 'wer', 'wo', 'sie', 'er', 'es', 'wir', 'die', 'der',
                               'das', 'dem', 'den', 'des', 'ein', 'eine', 'einem', 'einen')
        
        if wort_danach and len(wort_danach) > 0 and wort_danach[0].islower():
            # Prüfe ob es ein häufiges Wort ist
            first_word_lower = wort_danach.lower().rstrip('.,;:!?')
            if first_word_lower not in common_start_words:
                # Und das vorherige Wort endet nicht mit Satzzeichen
                if wort_davor and wort_davor[-1] not in '.!?':
                    ist_silbentrennung = True
        
        page_contexts[page_num] = (wort_davor, wort_danach, ist_silbentrennung)
    
    return page_contexts


def fix_page_markers_in_text(text: str, page_contexts: Dict[int, Tuple[str, str, bool]]) -> Tuple[str, int]:
    """
    Korrigiert die Seitenzahlen-Marker im Text.
    Gibt zurück: (korrigierter_text, anzahl_korrekturen)
    """
    corrections = 0
    
    # Finde alle Seitenzahlen-Marker im lokalen Text
    # Muster: |XX| mit beliebigem Kontext
    
    def replace_marker(match):
        nonlocal corrections
        
        before = match.group(1) or ""
        page_num = int(match.group(2))
        after = match.group(3) or ""
        
        if page_num not in page_contexts:
            # Keine Info aus Online-Version, Standard-Formatierung
            return f" |{page_num}| "
        
        wort_davor_online, wort_danach_online, ist_silbentrennung = page_contexts[page_num]
        
        # Aktuelle Formatierung prüfen
        has_space_before = before.endswith(' ') or before == ''
        has_space_after = after.startswith(' ') or after == ''
        
        if ist_silbentrennung:
            # Bei Silbentrennung: Marker ohne Leerzeichen im Wort
            # Entferne Leerzeichen wenn vorhanden
            new_before = before.rstrip()
            new_after = after.lstrip()
            new_text = f"{new_before}|{page_num}|{new_after}"
            
            if new_before != before or new_after != after:
                corrections += 1
                return new_text
        else:
            # Zwischen Wörtern: Leerzeichen vor und nach dem Marker
            new_before = before.rstrip() + ' ' if before.strip() else ''
            new_after = ' ' + after.lstrip() if after.strip() else ''
            new_text = f"{new_before}|{page_num}|{new_after}"
            
            # Prüfe ob Korrektur nötig
            if not has_space_before or not has_space_after:
                corrections += 1
                return new_text
        
        return match.group(0)
    
    # Ersetze alle Marker
    # Muster: optionaler Kontext + |XX| + optionaler Kontext
    pattern = r'(\S*)\|(\d+)\|(\S*)'
    result = re.sub(pattern, replace_marker, text)
    
    return result, corrections


def is_word_internal_marker(before: str, after: str) -> bool:
    """
    Prüft ob ein Marker innerhalb eines Wortes steht (Silbentrennung).
    Ein Marker ist wort-intern, wenn:
    - vor UND nach dem Marker Buchstaben stehen (keine Leerzeichen/Satzzeichen)
    """
    if not before or not after:
        return False
    
    # Prüfe ob das letzte Zeichen vor dem Marker ein Buchstabe ist
    last_char = before[-1] if before else ''
    first_char = after[0] if after else ''
    
    return last_char.isalpha() and first_char.isalpha()


def process_ga_file(filepath: Path, page_contexts: Dict[int, Tuple[str, str, bool]], 
                    dry_run: bool = True) -> Tuple[int, List[str]]:
    """
    Verarbeitet eine GA-Datei und korrigiert die Seitenzahlen-Marker.
    
    Regeln:
    1. Marker INNERHALB eines Wortes (Buchstaben davor UND danach) -> nicht ändern (Silbentrennung)
    2. Marker am Wortanfang (|XX|Wort) -> Leerzeichen vor Wort: |XX| Wort
    3. Marker am Wortende (Wort|XX|) -> Leerzeichen nach Wort: Wort |XX|
    4. Marker zwischen Wörtern -> Leerzeichen beidseitig: Wort |XX| Wort
    
    Gibt zurück: (anzahl_korrekturen, liste_der_aenderungen)
    """
    try:
        original_text = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return 0, [f"Fehler beim Lesen: {e}"]
    
    changes = []
    new_text = original_text
    total_corrections = 0
    
    # Finde alle Seitenzahlen-Marker mit Kontext
    # Muster: optionales Wort + |XX| + optionales Wort
    pattern = r'(\S*)\|(\d+)\|(\S*)'
    
    for match in re.finditer(pattern, original_text):
        before = match.group(1)
        page_num = int(match.group(2))
        after = match.group(3)
        
        old_pattern = match.group(0)
        
        # Prüfe ob Marker innerhalb eines Wortes steht (Silbentrennung)
        if is_word_internal_marker(before, after):
            # Silbentrennung: NICHT ändern
            continue
        
        # Marker ist NICHT innerhalb eines Wortes -> Leerzeichen hinzufügen
        new_before = before.rstrip() if before else ''
        new_after = after.lstrip() if after else ''
        
        # Füge Leerzeichen hinzu wo nötig
        if new_before and not new_before.endswith(' '):
            new_before = new_before + ' '
        if new_after and not new_after.startswith(' '):
            new_after = ' ' + new_after
        
        new_pattern = f"{new_before}|{page_num}|{new_after}"
        
        if old_pattern != new_pattern:
            # Ersetze im Text
            new_text = new_text.replace(old_pattern, new_pattern, 1)
            changes.append(f"  Seite {page_num}: '{old_pattern[:40]}' -> '{new_pattern[:40]}'")
            total_corrections += 1
    
    if not dry_run and total_corrections > 0:
        filepath.write_text(new_text, encoding='utf-8')
    
    return total_corrections, changes


def find_ga_folder(ga_nummer: str) -> Optional[Path]:
    """Findet den Ordner für eine GA-Nummer (z.B. '104' oder '104a')"""
    ga_nummer = str(ga_nummer).lower()
    
    for folder in BASE_PATH.iterdir():
        if folder.is_dir():
            name = folder.name.lower()
            # Versuche verschiedene Formate: GA104a-, GA0104a-, GA104a -
            if (name.startswith(f"ga{ga_nummer}-") or 
                name.startswith(f"ga0{ga_nummer}-") or
                name.startswith(f"ga{ga_nummer} -")):
                return folder
            # Für rein numerische GA-Nummern auch mit führender Null
            if ga_nummer.isdigit():
                padded = ga_nummer.zfill(3)
                if name.startswith(f"ga{padded}-") or name.startswith(f"ga{padded} -"):
                    return folder
    return None


def find_vortrag_files(ga_folder: Path) -> List[Path]:
    """Findet alle Vortrag-Dateien in einem GA-Ordner"""
    vortrag_files = []
    for file in ga_folder.iterdir():
        if file.is_file() and file.suffix == '.md':
            name = file.name.upper()
            if 'VORTRAG' in name or 'REDE' in name:
                vortrag_files.append(file)
    
    def sort_key(f):
        match = re.search(r'\((\d+)\.\)', f.name)
        return int(match.group(1)) if match else 999
    
    return sorted(vortrag_files, key=sort_key)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Korrigiert Seitenzahlen-Marker in GA-Texten')
    parser.add_argument('ga_nummer', type=str, help='GA-Nummer (z.B. 102, 104a)')
    parser.add_argument('--apply', '-a', action='store_true', 
                        help='Änderungen wirklich durchführen (ohne: nur Vorschau)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Seitenzahlen-Marker Korrektur für GA {args.ga_nummer}")
    print('='*60)
    
    # Finde GA-Ordner
    ga_folder = find_ga_folder(args.ga_nummer)
    if not ga_folder:
        print(f"Fehler: Ordner für GA {args.ga_nummer} nicht gefunden")
        return
    
    print(f"Ordner: {ga_folder.name}")
    
    # Lade Online-Inhalt
    print("Lade Online-Inhalt...")
    html_content = fetch_online_content(args.ga_nummer)
    if not html_content:
        print("Fehler: Konnte Online-Inhalt nicht laden")
        return
    
    # Extrahiere Seitenzahlen-Kontexte
    print("Analysiere Seitenzahlen-Positionen...")
    page_contexts = extract_page_contexts(html_content)
    print(f"Gefundene Seitenzahlen: {len(page_contexts)}")
    
    # Zeige einige Beispiele
    print("\nBeispiele aus Online-Version:")
    for i, (page, (vor, nach, silben)) in enumerate(sorted(page_contexts.items())[:5]):
        typ = "Silbentrennung" if silben else "Zwischen Woertern"
        print(f"  Seite {page}: '{vor}' ... '{nach}' ({typ})")
    
    # Finde Vortrag-Dateien
    vortrag_files = find_vortrag_files(ga_folder)
    print(f"\nGefundene Vortraege: {len(vortrag_files)}")
    
    if not args.apply:
        print("\n[VORSCHAU-MODUS - keine Änderungen werden durchgeführt]")
        print("Verwende --apply um Änderungen anzuwenden\n")
    
    # Verarbeite jede Datei
    total_corrections = 0
    
    for filepath in vortrag_files:
        print(f"\n--- {filepath.name[:50]} ---")
        
        corrections, changes = process_ga_file(filepath, page_contexts, dry_run=not args.apply)
        
        if corrections > 0:
            print(f"Korrekturen: {corrections}")
            for change in changes[:10]:
                print(change)
            if len(changes) > 10:
                print(f"  ... und {len(changes) - 10} weitere")
            total_corrections += corrections
        else:
            print("Keine Korrekturen noetig")
    
    print(f"\n{'='*60}")
    print(f"GESAMT: {total_corrections} Korrekturen")
    if args.apply:
        print("Änderungen wurden gespeichert!")
    else:
        print("Führe mit --apply aus, um Änderungen zu speichern")
    print('='*60)


if __name__ == "__main__":
    main()
