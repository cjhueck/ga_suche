#!/usr/bin/env python3
"""Stellt Seitenmarker aus JSON wieder in MD-Datei her"""
import json
import re
import sys
from pathlib import Path

def normalize(text: str) -> str:
    """Normalisiert Text für Vergleich (nur Buchstaben, lowercase)"""
    return re.sub(r'[^a-zA-ZäöüÄÖÜßéèêëàâáíìîïóòôúùûñç]', '', text.lower())

def extract_markers_from_json(json_path: Path) -> list:
    """Extrahiert Seitenmarker aus JSON-Datei"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    markers = []
    
    # Prüfe ob es ein Buch oder Lectures sind
    if 'book' in data:
        # Buch-Struktur
        paragraphs = data['book'].get('paragraphs', [])
    elif 'lectures' in data:
        # Lectures-Struktur
        paragraphs = []
        for lecture in data.get('lectures', []):
            paragraphs.extend(lecture.get('paragraphs', []))
    else:
        print("  Warnung: Unbekannte JSON-Struktur")
        return []
    
    for para in paragraphs:
        content = para.get('content', '')
        
        # Finde alle Marker im Absatz
        for match in re.finditer(r'\|(\d+)\|', content):
            page_num = int(match.group(1))
            pos = match.start()
            
            # Extrahiere Kontext vor und nach dem Marker
            before = content[max(0, pos-150):pos]
            after = content[match.end():match.end()+150]
            
            markers.append({
                'page': page_num,
                'before': before,
                'after': after,
                'before_norm': normalize(before),
                'after_norm': normalize(after)
            })
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda x: x['page'])
    
    return markers

def insert_markers_into_md(md_path: Path, markers: list) -> int:
    """Fügt Marker in MD-Datei ein"""
    
    # Lade MD-Datei
    content = md_path.read_text(encoding='utf-8')
    
    # Entferne alte Marker
    content_clean = re.sub(r'\|\d+\|', '', content)
    
    # Normalisiere für Suche
    norm_content = normalize(content_clean)
    
    inserted = 0
    insertions = []  # (position, page_num)
    last_pos = 0  # Für sequentielle Suche
    
    for marker in markers:
        # Suche nach Position im normalisierten Text
        # Verwende "after" Text (steht nach dem Marker)
        best_pos = -1
        
        # Strategie 1: Suche nach "after" Text
        for search_len in [50, 40, 30, 25, 20, 15]:
            if len(marker['after_norm']) >= search_len:
                search = marker['after_norm'][:search_len]
                pos = norm_content.find(search, last_pos)
                if pos >= 0:
                    best_pos = pos
                    break
        
        # Strategie 2: Suche nach Kombination vor+nach
        if best_pos < 0:
            search = marker['before_norm'][-30:] + marker['after_norm'][:30]
            pos = norm_content.find(search, last_pos)
            if pos >= 0:
                best_pos = pos + len(marker['before_norm'][-30:])
        
        if best_pos >= 0:
            # Konvertiere normalisierte Position zu echter Position
            real_pos = 0
            norm_count = 0
            
            for i, c in enumerate(content_clean):
                if norm_count >= best_pos:
                    real_pos = i
                    break
                if normalize(c):
                    norm_count += 1
            else:
                real_pos = len(content_clean)
            
            insertions.append((real_pos, marker['page']))
            last_pos = best_pos
            inserted += 1
        else:
            print(f"  Warnung: Marker |{marker['page']}| nicht gefunden")
            print(f"    Suche nach: '{marker['after'][:50]}...'")
    
    # Sortiere nach Position (absteigend) und füge ein
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    for pos, page in insertions:
        marker_str = f'|{page}|'
        content_clean = content_clean[:pos] + marker_str + content_clean[pos:]
    
    # Speichere
    md_path.write_text(content_clean, encoding='utf-8')
    
    return inserted

def main():
    # Pfade
    json_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\pagebreaks\archive\GA011.json')
    md_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA011-Aus der Akasha-Chronik\GA011 - Aus der Akasha-Chronik (1904).md')
    
    if not json_path.exists():
        print(f"Fehler: JSON-Datei nicht gefunden: {json_path}")
        sys.exit(1)
    
    if not md_path.exists():
        print(f"Fehler: MD-Datei nicht gefunden: {md_path}")
        sys.exit(1)
    
    print(f"Lade Marker aus: {json_path.name}")
    markers = extract_markers_from_json(json_path)
    print(f"  Gefunden: {len(markers)} Marker")
    if markers:
        print(f"  Erste: |{markers[0]['page']}|, Letzte: |{markers[-1]['page']}|")
    
    print(f"\nFüge Marker ein in: {md_path.name}")
    inserted = insert_markers_into_md(md_path, markers)
    print(f"\nGesamt eingefügt: {inserted} von {len(markers)}")
    print(f"Datei gespeichert!")

if __name__ == '__main__':
    main()

