#!/usr/bin/env python3
"""
Überträgt Seitenumbrüche von MsN (Mistral Neu) nach MsA (Mistral Alt).

MsN: Neue Mistral OCR MD-Datei mit exakten Seitenumbrüchen
     Format: "RUDOLF STEINER\nVERLAG\nSeite X\n---"
     
MsA: Existierende MD-Dateien in Obsidian (bereinigt, mit Absatz-IDs)

Strategie:
1. Extrahiere alle Seitenumbrüche aus MsN mit Kontext (Text vor/nach)
2. Normalisiere Text sehr aggressiv für Vergleich
3. Suche in MsA nach den Kontextstellen
4. Füge |X+1| Marker ein (Seite X am Ende → nächste Seite ist X+1)

Verwendung:
    python tools/transfer_pagebreaks_msn_to_msa.py GA019
"""

import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


def normalize_aggressive(text: str) -> str:
    """Sehr aggressive Normalisierung für Textvergleich."""
    # Lowercase
    text = text.lower()
    # Umlaute ersetzen
    text = text.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
    text = text.replace('ß', 'ss')
    text = text.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    text = text.replace('á', 'a').replace('à', 'a').replace('â', 'a')
    text = text.replace('í', 'i').replace('ì', 'i').replace('î', 'i')
    text = text.replace('ó', 'o').replace('ò', 'o').replace('ô', 'o')
    text = text.replace('ú', 'u').replace('ù', 'u').replace('û', 'u')
    # Nur Buchstaben behalten
    text = re.sub(r'[^a-z]', '', text)
    return text


def extract_pagebreaks_from_msn(content: str) -> list:
    """
    Extrahiere Seitenumbrüche aus MsN.
    
    Format: RUDOLF STEINER\nVERLAG\nSeite X\n---
    Der Text NACH dem --- gehört zu Seite X+1.
    """
    breaks = []
    
    # Pattern für Seitenmarker
    pattern = r'RUDOLF STEINER\s*\n\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---'
    
    for match in re.finditer(pattern, content, re.IGNORECASE):
        page_num = int(match.group(1))
        next_page = page_num + 1  # Text danach ist Seite X+1
        
        # Text VOR dem Marker (Ende der aktuellen Seite)
        before_end = match.start()
        before_text = content[max(0, before_end - 200):before_end]
        # Entferne vorherige RUDOLF STEINER VERLAG etc.
        before_text = re.sub(r'RUDOLF STEINER\s*\n\s*VERLAG\s*\n*Seite\s+\d+\s*\n*---\s*', '', before_text, flags=re.I)
        before_text = before_text.strip()
        
        # Text NACH dem Marker (Anfang der nächsten Seite)
        after_start = match.end()
        after_text = content[after_start:after_start + 500]
        # Entferne führende Leerzeilen und RUDOLF STEINER VERLAG Header
        after_text = re.sub(r'^[\s\n]*RUDOLF STEINER\s*\n\s*VERLAG\s*\n*', '', after_text, flags=re.I)
        after_text = re.sub(r'^Seite\s+\d+\s*\n*', '', after_text, flags=re.I)
        after_text = re.sub(r'^---\s*\n*', '', after_text)
        # Entferne Überschriften (# ..., [TITEL], etc.) - diese sind in MsA nicht vorhanden
        after_text = re.sub(r'^#[^\n]*\n+', '', after_text)
        after_text = re.sub(r'^\[[^\]]+\]\s*\n+', '', after_text)
        after_text = re.sub(r'^#{1,6}\s+[^\n]+\n+', '', after_text)
        # Entferne Metadaten wie "Manuskript" Zeilen
        after_text = re.sub(r'^Manuskript\s*\n+', '', after_text, flags=re.I)
        after_text = re.sub(r'^\[[^\]]*\d{4}[^\]]*\]\s*\n+', '', after_text)  # [Juli 1917] etc.
        after_text = after_text.strip()
        
        breaks.append({
            'page': next_page,
            'before_raw': before_text[-100:],
            'after_raw': after_text[:100],
            'before_norm': normalize_aggressive(before_text[-80:]),
            'after_norm': normalize_aggressive(after_text[:80]),
        })
    
    return breaks


def find_best_match(search_norm: str, target_norm: str, min_length: int = 20) -> int:
    """Finde beste Übereinstimmung mit Fuzzy-Matching."""
    if len(search_norm) < min_length:
        return -1
    
    # Exakter Match
    pos = target_norm.find(search_norm)
    if pos >= 0:
        return pos
    
    # Kürzerer exakter Match
    for length in [60, 40, 30, 20]:
        if len(search_norm) >= length:
            short_search = search_norm[:length]
            pos = target_norm.find(short_search)
            if pos >= 0:
                return pos
    
    # Fuzzy Match mit SequenceMatcher
    best_pos = -1
    best_ratio = 0.7  # Mindest-Ähnlichkeit
    
    window = len(search_norm)
    for i in range(len(target_norm) - window + 1):
        candidate = target_norm[i:i + window]
        ratio = SequenceMatcher(None, search_norm, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_pos = i
    
    return best_pos


def insert_markers_into_msa(msa_path: Path, breaks: list, start_page: int = None, end_page: int = None) -> int:
    """Füge Marker in eine MsA-Datei ein."""
    content = msa_path.read_text(encoding='utf-8')
    
    # Entferne alte Marker
    content = re.sub(r'\|\d+\|', '', content)
    
    norm_content = normalize_aggressive(content)
    
    inserted = 0
    insertions = []  # (real_pos, page_num)
    
    # Filtere Breaks nach Seitenbereich
    relevant_breaks = breaks
    if start_page is not None:
        relevant_breaks = [b for b in relevant_breaks if b['page'] >= start_page]
    if end_page is not None:
        relevant_breaks = [b for b in relevant_breaks if b['page'] <= end_page]
    
    last_pos = 0  # Für sequentielle Suche
    
    for brk in relevant_breaks:
        best_pos = -1
        
        # Strategie 1: Suche nur nach "after" Text (steht auf der neuen Seite)
        for search_len in [50, 40, 30, 25, 20]:
            if len(brk['after_norm']) >= search_len:
                search = brk['after_norm'][:search_len]
                pos = norm_content.find(search, last_pos)
                if pos >= 0:
                    best_pos = pos
                    break
        
        # Strategie 2: Suche nach Kombination vor+nach
        if best_pos < 0:
            search = brk['before_norm'][-30:] + brk['after_norm'][:30]
            pos = find_best_match(search, norm_content[last_pos:])
            if pos >= 0:
                best_pos = last_pos + pos + len(brk['before_norm'][-30:])
        
        # Strategie 3: Kürzere Suche
        if best_pos < 0:
            for search_len in [15, 12, 10]:
                if len(brk['after_norm']) >= search_len:
                    search = brk['after_norm'][:search_len]
                    pos = norm_content.find(search, last_pos)
                    if pos >= 0:
                        best_pos = pos
                        break
        
        if best_pos >= 0:
            # Konvertiere normalisierte Position zu echter Position
            real_pos = 0
            norm_count = 0
            for i, c in enumerate(content):
                if norm_count >= best_pos:
                    real_pos = i
                    break
                if normalize_aggressive(c):
                    norm_count += 1
            else:
                real_pos = len(content)
            
            insertions.append((real_pos, brk['page']))
            inserted += 1
            last_pos = best_pos + 10  # Etwas Puffer
    
    # Sortiere absteigend und füge ein
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    for pos, page in insertions:
        marker = f'|{page}|'
        content = content[:pos] + marker + content[pos:]
    
    # Speichere
    msa_path.write_text(content, encoding='utf-8')
    
    return inserted


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python transfer_pagebreaks_msn_to_msa.py GA019")
        sys.exit(1)
    
    ga_num = sys.argv[1].upper()
    if not ga_num.startswith('GA'):
        ga_num = f'GA{ga_num}'
    
    # Finde GA-Ordner
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    ga_folder = None
    
    for d in base.iterdir():
        if d.is_dir() and ga_num in d.name:
            ga_folder = d
            break
    
    if not ga_folder:
        print(f"GA-Ordner nicht gefunden: {ga_num}")
        sys.exit(1)
    
    print(f"GA-Ordner: {ga_folder.name}")
    
    # Finde MsN Datei (entweder direkt im Ordner oder in Unterordner)
    msn_path = None
    
    # Erst direkt im Ordner suchen
    for f in ga_folder.iterdir():
        if f.suffix == '.md' and 'Steiner, Rudolf' in f.name and '_converted' not in f.name:
            msn_path = f
            break
    
    # Falls nicht gefunden, in Unterordnern suchen
    if not msn_path:
        for sub in ga_folder.iterdir():
            if sub.is_dir() and 'Steiner, Rudolf' in sub.name:
                for f in sub.iterdir():
                    if f.suffix == '.md' and '_converted' not in f.name:
                        msn_path = f
                        break
    
    if not msn_path:
        print("MsN-Datei nicht gefunden!")
        sys.exit(1)
    
    print(f"MsN: {msn_path.name}")
    
    # Lade MsN und extrahiere Breaks
    msn_content = msn_path.read_text(encoding='utf-8')
    breaks = extract_pagebreaks_from_msn(msn_content)
    print(f"Seitenumbrüche extrahiert: {len(breaks)}")
    
    if breaks:
        pages = [b['page'] for b in breaks]
        print(f"  Seiten: {min(pages)} - {max(pages)}")
    
    # Finde MsA Dateien (einzelne Vorträge/Kapitel)
    msa_files = []
    for f in ga_folder.iterdir():
        if f.suffix == '.md' and f.name.startswith(ga_num) and '(' in f.name:
            msa_files.append(f)
    
    msa_files.sort(key=lambda x: x.name)
    print(f"\nMsA-Dateien: {len(msa_files)}")
    
    # Lade lecture-page-mapping für Seitenbereiche
    mapping_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\lecture-page-mapping.json')
    mapping = {}
    if mapping_path.exists():
        import json
        with open(mapping_path, 'r', encoding='utf-8') as f:
            all_mappings = json.load(f)
            mapping = all_mappings.get(ga_num, {})
    
    # Verarbeite jede MsA-Datei
    total_inserted = 0
    
    for msa_file in msa_files:
        # Extrahiere Vortragsnummer aus Dateiname
        match = re.search(r'\((\d+)\.\)', msa_file.name)
        if match:
            lec_num = int(match.group(1))
            lec_id = f'{ga_num}/{lec_num}'
            
            # Seitenbereich aus Mapping
            start_page = mapping.get(lec_id)
            
            # Ende ist Start des nächsten Vortrags
            next_lec_id = f'{ga_num}/{lec_num + 1}'
            end_page = mapping.get(next_lec_id)
            if end_page:
                end_page -= 1  # Exklusive
            
            inserted = insert_markers_into_msa(msa_file, breaks, start_page, end_page)
            
            if inserted > 0:
                range_str = f"S.{start_page}" if start_page else "?"
                if end_page:
                    range_str += f"-{end_page}"
                print(f"  {msa_file.name[:50]}...: {inserted} Marker ({range_str})")
                total_inserted += inserted
    
    print(f"\nGesamt eingefügt: {total_inserted}")
    print(f"\nNächster Schritt: python export_master.py {ga_num} --skip-path-fix")


if __name__ == '__main__':
    main()

