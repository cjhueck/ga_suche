#!/usr/bin/env python3
"""
Teilt MsN_converted in einzelne Vorträge auf basierend auf Seitenzahlen.

1. Liest MsN_converted (mit Markern)
2. Verwendet lecture-page-mapping.json für Seitenbereiche
3. Teilt in einzelne Dateien auf
4. Überträgt Block-IDs aus alten MsA-Dateien

Verwendung:
    python tools/split_msn_to_lectures.py GA019
"""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    """Normalisiere Text für Vergleich."""
    text = text.lower()
    text = text.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text


def count_words(text: str, exclude_headings: bool = True) -> int:
    """Zähle Wörter im Text (ohne Überschriften, Block-IDs und Marker)."""
    # Entferne Block-IDs
    text = re.sub(r'\^[a-z0-9]+', '', text)
    # Entferne Seitenmarker
    text = re.sub(r'\|\d+\|', '', text)
    
    if exclude_headings:
        # Entferne Überschriften (Zeilen die mit # beginnen)
        text = re.sub(r'^#+\s.*$', '', text, flags=re.MULTILINE)
        # Entferne GROSSBUCHSTABEN-Überschriften
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Überspringe reine Großbuchstaben-Zeilen
            if stripped and stripped.isupper() and len(stripped.split()) >= 2:
                continue
            clean_lines.append(line)
        text = '\n'.join(clean_lines)
    
    # Zähle Wörter
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def validate_word_count(msa_content: str, msan_content: str, lec_id: str, tolerance: float = 0.15) -> tuple:
    """
    Validiere Wortanzahl zwischen MsA und MsAN.
    
    Args:
        msa_content: Original MsA Inhalt
        msan_content: Neuer MsAN Inhalt
        lec_id: Vortragskennnung (z.B. GA019/1)
        tolerance: Erlaubte Abweichung (15% = 0.15)
    
    Returns:
        (is_valid, message, msa_words, msan_words)
    """
    msa_words = count_words(msa_content, exclude_headings=True)
    msan_words = count_words(msan_content, exclude_headings=True)
    
    if msa_words == 0:
        return (True, "MsA leer", msa_words, msan_words)
    
    diff_ratio = abs(msan_words - msa_words) / msa_words
    
    if diff_ratio <= tolerance:
        return (True, "OK", msa_words, msan_words)
    else:
        diff_pct = int(diff_ratio * 100)
        if msan_words > msa_words:
            return (False, f"MsAN hat {diff_pct}% MEHR Wörter ({msan_words} vs {msa_words})", msa_words, msan_words)
        else:
            return (False, f"MsAN hat {diff_pct}% WENIGER Wörter ({msan_words} vs {msa_words})", msa_words, msan_words)


def find_page_position(content: str, page_num: int) -> int:
    """Finde Position des Seitenmarkers |page_num| im Text."""
    pattern = rf'\|{page_num}\|'
    match = re.search(pattern, content)
    if match:
        return match.start()
    return -1


def extract_lecture_content(content: str, start_page: int, end_page: int, max_length: int = None) -> str:
    """Extrahiere Text zwischen zwei Seitenzahlen.
    
    Args:
        content: MsN_converted Inhalt
        start_page: Startseite
        end_page: Endseite (oder None für letzten Vortrag)
        max_length: Maximale Textlänge (aus MsA), um Herausgeber-Anhänge auszuschließen
    """
    start_pos = find_page_position(content, start_page)
    
    if start_pos < 0:
        # Suche nach nächster verfügbarer Seite
        for p in range(start_page, start_page + 10):
            start_pos = find_page_position(content, p)
            if start_pos >= 0:
                break
    
    if start_pos < 0:
        return None
    
    # Finde Ende basierend auf Seitenzahl
    end_pos = len(content)
    
    if end_page:
        found_end = find_page_position(content, end_page)
        if found_end < 0:
            # Suche nach nächster verfügbarer Seite (nur +/- 2)
            for p in range(end_page, end_page + 3):
                found_end = find_page_position(content, p)
                if found_end >= 0:
                    break
        
        if found_end > start_pos:
            end_pos = found_end
    
    # Begrenze auf max_length (aus MsA) - wichtig für letzten Vortrag ohne Herausgeber-Anhänge
    if max_length and max_length > 0:
        # Erlaube 20% mehr für Marker und Formatierungsunterschiede
        allowed_length = int(max_length * 1.3)
        if end_pos - start_pos > allowed_length:
            end_pos = start_pos + allowed_length
            # Finde nächsten Absatzumbruch
            next_break = content.find('\n\n', end_pos)
            if next_break > 0 and next_break < start_pos + allowed_length + 500:
                end_pos = next_break
    
    return content[start_pos:end_pos].strip()


def transfer_block_ids(new_content: str, old_content: str) -> str:
    """Übertrage Block-IDs von altem zu neuem Content."""
    # Extrahiere alle Block-IDs aus altem Content
    old_ids = re.findall(r'\^[a-z0-9]+', old_content)
    
    if not old_ids:
        return new_content
    
    # Teile beide Texte in Absätze
    new_paragraphs = re.split(r'\n\n+', new_content)
    old_paragraphs = re.split(r'\n\n+', old_content)
    
    result_paragraphs = []
    used_ids = set()
    
    for new_para in new_paragraphs:
        new_para = new_para.strip()
        if not new_para:
            continue
        
        # Hat der Absatz schon eine ID?
        if re.search(r'\^[a-z0-9]+\s*$', new_para):
            result_paragraphs.append(new_para)
            continue
        
        new_norm = normalize(new_para)
        best_match = None
        best_ratio = 0.5
        
        # Finde besten Match im alten Content
        for old_para in old_paragraphs:
            old_para = old_para.strip()
            if not old_para:
                continue
            
            # Extrahiere ID
            id_match = re.search(r'(\^[a-z0-9]+)\s*$', old_para)
            if not id_match:
                continue
            
            block_id = id_match.group(1)
            if block_id in used_ids:
                continue
            
            old_text = old_para[:id_match.start()].strip()
            old_norm = normalize(old_text)
            
            # Vergleiche
            if len(new_norm) > 20 and len(old_norm) > 20:
                # Vergleiche Anfang
                ratio = SequenceMatcher(None, new_norm[:100], old_norm[:100]).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = block_id
        
        if best_match:
            new_para = new_para + ' ' + best_match
            used_ids.add(best_match)
        
        result_paragraphs.append(new_para)
    
    return '\n\n'.join(result_paragraphs)


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python split_msn_to_lectures.py GA019")
        sys.exit(1)
    
    ga_num = sys.argv[1].upper()
    if not ga_num.startswith('GA'):
        ga_num = f'GA{ga_num}'
    
    # Lade Mapping
    mapping_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\lecture-page-mapping.json')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        all_mappings = json.load(f)
    
    ga_mapping = all_mappings.get(ga_num, {})
    if not ga_mapping:
        print(f"Kein Mapping für {ga_num} gefunden!")
        sys.exit(1)
    
    print(f"Mapping für {ga_num}: {len(ga_mapping)} Vorträge")
    
    # Finde GA-Ordner und MsN_converted
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    ga_folder = None
    msn_path = None
    
    for d in base.iterdir():
        if ga_num in d.name:
            ga_folder = d
            for f in d.iterdir():
                if f.suffix == '.md' and '_converted' in f.name:
                    msn_path = f
                    break
            break
    
    if not msn_path:
        print("MsN_converted nicht gefunden!")
        print(f"Führe zuerst aus: python tools/convert_msn_to_msa.py {ga_num}")
        sys.exit(1)
    
    print(f"MsN_converted: {msn_path.name}")
    
    # Lade MsN_converted
    msn_content = msn_path.read_text(encoding='utf-8')
    marker_count = len(re.findall(r'\|\d+\|', msn_content))
    print(f"  {len(msn_content)} Zeichen, {marker_count} Marker")
    
    # Finde alte MsA-Dateien
    old_msa_files = {}
    for f in ga_folder.iterdir():
        if f.suffix == '.md' and f.name.startswith(ga_num) and '(' in f.name:
            match = re.search(r'\((\d+)\.\)', f.name)
            if match:
                lec_num = int(match.group(1))
                old_msa_files[lec_num] = f
    
    print(f"Alte MsA-Dateien: {len(old_msa_files)}")
    
    # Sortiere Mapping nach Vortragsnummer
    sorted_lectures = sorted(ga_mapping.items(), key=lambda x: int(re.search(r'/(\d+)$', x[0]).group(1)))
    
    # Verarbeite jeden Vortrag
    created_files = []
    validation_errors = []
    
    for i, (lec_id, start_page) in enumerate(sorted_lectures):
        lec_num = int(re.search(r'/(\d+)$', lec_id).group(1))
        
        # Ende ist Start des nächsten Vortrags
        if i + 1 < len(sorted_lectures):
            end_page = sorted_lectures[i + 1][1]
        else:
            end_page = None
        
        print(f"\n{lec_id}: Seiten {start_page}-{end_page if end_page else 'Ende'}")
        
        # Hole Textlänge aus alter MsA-Datei (um Herausgeber-Anhänge auszuschließen)
        max_length = None
        if lec_num in old_msa_files:
            old_text = old_msa_files[lec_num].read_text(encoding='utf-8')
            # Entferne Block-IDs und Marker für Längenberechnung
            clean_old = re.sub(r'\^[a-z0-9]+', '', old_text)
            clean_old = re.sub(r'\|\d+\|', '', clean_old)
            max_length = len(clean_old)
            print(f"  MsA-Länge: {max_length} Zeichen")
        
        # Extrahiere Content
        lecture_content = extract_lecture_content(msn_content, start_page, end_page, max_length)
        
        if not lecture_content:
            print(f"  WARNUNG: Kein Content gefunden!")
            continue
        
        # Bereinige Content
        # Entferne Überschriften und Header am Anfang (werden separat verwaltet)
        lines = lecture_content.split('\n')
        clean_lines = []
        skip_header = True
        
        for line in lines:
            stripped = line.strip()
            # Überspringe leere Zeilen und Überschriften am Anfang
            if skip_header:
                if not stripped:
                    continue
                # Markdown-Überschriften
                if stripped.startswith('#'):
                    continue
                # Eckige Klammern wie [Juli 1917]
                if stripped.startswith('[') and stripped.endswith(']'):
                    continue
                # RUDOLF STEINER VERLAG
                if stripped in ['Manuskript', 'RUDOLF STEINER', 'VERLAG', 'Rudolf Steiner', 'Verlag']:
                    continue
                # Datumszeilen wie [Juli 1917]
                if re.match(r'^\[.*\d{4}.*\]$', stripped):
                    continue
                # GROSSBUCHSTABEN-Zeilen (Überschriften aus MsN)
                # Mindestens 3 Wörter in Großbuchstaben = wahrscheinlich Überschrift
                if stripped.isupper() and len(stripped.split()) >= 2:
                    continue
                # Zeilen die nur aus Großbuchstaben und wenigen Sonderzeichen bestehen
                if re.match(r'^[A-ZÄÖÜ\s,.\-–—!?»«]+$', stripped) and len(stripped) > 10:
                    continue
                # Wenn wir hier ankommen und die Zeile beginnt mit « oder einem Kleinbuchstaben,
                # ist der Header vorbei
                if stripped.startswith('«') or (stripped and stripped[0].islower()):
                    skip_header = False
                # Sonstige kurze Zeilen am Anfang könnten noch Header sein
                elif len(stripped) < 50 and not re.search(r'[a-zäöüß]', stripped):
                    continue
                else:
                    skip_header = False
            clean_lines.append(line)
        
        lecture_content = '\n'.join(clean_lines).strip()
        
        # Marker-Statistik
        markers = re.findall(r'\|(\d+)\|', lecture_content)
        if markers:
            pages = sorted(set(int(m) for m in markers))
            print(f"  {len(markers)} Marker, Seiten: {min(pages)}-{max(pages)}")
        else:
            print(f"  0 Marker")
        
        # Übertrage Block-IDs aus alter Datei
        if lec_num in old_msa_files:
            old_content = old_msa_files[lec_num].read_text(encoding='utf-8')
            lecture_content = transfer_block_ids(lecture_content, old_content)
            
            # Zähle übertragene IDs
            ids = re.findall(r'\^[a-z0-9]+', lecture_content)
            print(f"  {len(ids)} Block-IDs übertragen")
        
        # Erstelle Dateiname aus alter Datei oder generiere neuen
        if lec_num in old_msa_files:
            new_filename = old_msa_files[lec_num].stem + '_new.md'
        else:
            new_filename = f"{ga_num} ({lec_num}.)_new.md"
        
        new_path = ga_folder / new_filename
        new_path.write_text(lecture_content, encoding='utf-8')
        created_files.append(new_path)
        print(f"  Gespeichert: {new_filename}")
        
        # Wortanzahl-Validierung
        if lec_num in old_msa_files:
            is_valid, msg, msa_w, msan_w = validate_word_count(old_content, lecture_content, lec_id)
            if is_valid:
                print(f"  [OK] Wortanzahl: {msa_w} -> {msan_w} ({msg})")
            else:
                print(f"  [!] WARNUNG: {msg}")
                validation_errors.append((lec_id, msg, msa_w, msan_w))
    
    print(f"\n{'='*60}")
    print(f"Erstellt: {len(created_files)} Dateien")
    
    # Zeige Validierungsfehler
    if validation_errors:
        print(f"\n[!] WORTANZAHL-DISKREPANZEN ({len(validation_errors)} Dateien):")
        print("-" * 60)
        for lec_id, msg, msa_w, msan_w in validation_errors:
            print(f"  {lec_id}: {msg}")
        print("-" * 60)
        print("Bitte pruefen Sie diese Dateien manuell!")
        print("Moegliche Ursachen:")
        print("  - MsN enthaelt Herausgeber-Anhaenge -> max_length anpassen")
        print("  - MsN fehlt Text -> Seitenmapping pruefen")
        print("  - Unterschiedliche Textversionen")
    else:
        print(f"\n[OK] Alle Wortanzahlen validiert (Toleranz: 15%)")
    
    print(f"\nNächste Schritte:")
    print(f"1. Prüfe die neuen Dateien (*_new.md)")
    print(f"2. Wenn OK: Ersetze die alten durch die neuen")
    print(f"3. Führe aus: python export_master.py {ga_num} --skip-path-fix")


if __name__ == '__main__':
    main()

