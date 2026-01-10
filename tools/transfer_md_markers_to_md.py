#!/usr/bin/env python3
"""
Überträgt Seitenmarker aus Mistral OCR Gesamt-MD in die einzelnen MD-Dateien.

Die Gesamt-MD enthält den kompletten Band mit Markern.
Die einzelnen MD-Dateien (GA019 (1.)...md, GA019 (2.)...md) werden
vom Export-System verwendet.

Verwendung:
    python tools/transfer_md_markers_to_md.py GA019
"""

import re
import sys
from pathlib import Path


def normalize(text):
    """Entferne alles außer Buchstaben für Vergleich."""
    return re.sub(r'[^a-zA-ZäöüÄÖÜßéèêëàâáíìîïóòôúùûñç]', '', text.lower())


def find_mistral_md(ga_folder: Path) -> Path:
    """Finde die Mistral OCR Gesamt-MD Datei."""
    # Suche in Unterordnern nach "Steiner, Rudolf GA XXX"
    for sub in ga_folder.iterdir():
        if sub.is_dir() and 'Steiner, Rudolf' in sub.name:
            for f in sub.iterdir():
                if f.suffix == '.md' and '_converted' not in f.name:
                    return f
    return None


def extract_markers_from_mistral(content: str) -> list:
    """
    Extrahiere Marker-Positionen aus Mistral OCR Format.
    
    Format: RUDOLF STEINER\nVERLAG\nSeite X\n---
    "Seite X" steht am ENDE von Seite X, also beginnt Text danach mit X+1.
    """
    markers = []
    
    # Pattern für Mistral-Seitenmarker
    pattern = r'RUDOLF STEINER\s*\n\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---'
    
    for m in re.finditer(pattern, content, re.IGNORECASE):
        page_num = int(m.group(1)) + 1  # Text DANACH ist Seite X+1
        
        # Text nach dem Marker (das ist der Beginn der nächsten Seite)
        after_start = m.end()
        after_text = content[after_start:after_start + 200]
        after_norm = normalize(after_text)
        
        # Text vor dem Marker (Ende der vorherigen Seite)
        before_end = m.start()
        before_text = content[max(0, before_end - 200):before_end]
        before_norm = normalize(before_text)
        
        markers.append({
            'page': page_num,
            'after_norm': after_norm[:100],
            'before_norm': before_norm[-100:],
            'after_raw': after_text[:80].replace('\n', ' ')
        })
    
    return markers


def insert_markers_into_md(md_path: Path, markers: list) -> int:
    """Füge Marker in eine einzelne MD-Datei ein."""
    
    content = md_path.read_text(encoding='utf-8')
    
    # Entferne alte Marker
    content = re.sub(r'\|\d+\|', '', content)
    
    norm_content = normalize(content)
    
    inserted = 0
    insertions = []  # (position, page_num)
    
    for marker in markers:
        if marker['page'] < 7:  # Skip Titelseiten
            continue
        
        # Suche nach der Position wo der Marker eingefügt werden soll
        search = marker['before_norm'][-60:] + marker['after_norm'][:60]
        
        pos = norm_content.find(search)
        if pos < 0:
            # Kürzere Suche
            search = marker['before_norm'][-30:] + marker['after_norm'][:30]
            pos = norm_content.find(search)
        
        if pos >= 0:
            # Position gefunden - berechne reale Position
            target_pos = pos + len(marker['before_norm'][-60:]) if len(marker['before_norm']) >= 60 else pos + len(marker['before_norm'])
            
            # Konvertiere normalisierte Position zu echter Position
            real_pos = 0
            norm_count = 0
            for i, c in enumerate(content):
                if norm_count >= target_pos:
                    real_pos = i
                    break
                if normalize(c):
                    norm_count += 1
            else:
                real_pos = len(content)
            
            insertions.append((real_pos, marker['page']))
            inserted += 1
    
    # Sortiere nach Position (absteigend) und füge ein
    insertions.sort(key=lambda x: x[0], reverse=True)
    
    for pos, page in insertions:
        marker_str = f'|{page}|'
        content = content[:pos] + marker_str + content[pos:]
    
    # Speichere
    md_path.write_text(content, encoding='utf-8')
    
    return inserted


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python transfer_md_markers_to_md.py GA019")
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
    
    # Finde Mistral OCR Datei
    mistral_md = find_mistral_md(ga_folder)
    if not mistral_md:
        print("Mistral OCR MD-Datei nicht gefunden!")
        sys.exit(1)
    
    print(f"Mistral MD: {mistral_md.name}")
    
    # Lade und extrahiere Marker
    mistral_content = mistral_md.read_text(encoding='utf-8')
    markers = extract_markers_from_mistral(mistral_content)
    print(f"Marker extrahiert: {len(markers)}")
    
    if markers:
        pages = [m['page'] for m in markers]
        print(f"  Seiten: {min(pages)} - {max(pages)}")
    
    # Finde einzelne MD-Dateien
    single_mds = []
    for f in ga_folder.iterdir():
        if f.suffix == '.md' and f.name.startswith(ga_num) and '(' in f.name:
            single_mds.append(f)
    
    single_mds.sort(key=lambda x: x.name)
    print(f"\nEinzelne MD-Dateien: {len(single_mds)}")
    
    # Füge Marker in jede Datei ein
    total_inserted = 0
    for md_file in single_mds:
        inserted = insert_markers_into_md(md_file, markers)
        if inserted > 0:
            print(f"  {md_file.name[:50]}...: {inserted} Marker")
            total_inserted += inserted
    
    print(f"\nGesamt eingefügt: {total_inserted}")
    print(f"\nJetzt: python export_master.py {ga_num} --skip-path-fix")


if __name__ == '__main__':
    main()

