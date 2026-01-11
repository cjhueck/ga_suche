#!/usr/bin/env python3
"""
GA002 Pagebreaks V4

MsA: GA002_msa.md (Block-IDs, Überschriften)
MsN: GA002_msn.md (Seitenmarker aus Mistral OCR)

Strategie:
1. Finde RUDOLF STEINER VERLAG Seite X --- in MsN
2. Nimm 200 Zeichen davor (left) 
3. Suche in MsA wo dieser Text endet
4. Füge Marker |X+1| dort ein
"""

import re
from pathlib import Path

FOLDER = Path('Steiner_GA/GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung')
MSA_PATH = FOLDER / 'GA002_msa.md'
MSN_PATH = FOLDER / 'GA002_msn.md'
OUTPUT_PATH = FOLDER / 'GA002_msan.md'


def normalize(text: str) -> str:
    """Nur Kleinbuchstaben und Zahlen."""
    text = text.lower()
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]', '', text)


def find_end_position(original: str, search_norm: str, start_from: int = 0) -> int:
    """
    Finde wo der normalisierte search_text in original endet.
    Gibt die ORIGINAL-Position zurück.
    """
    orig_norm = normalize(original)
    
    pos_norm = orig_norm.find(search_norm, start_from)
    if pos_norm < 0:
        return -1
    
    end_norm = pos_norm + len(search_norm)
    
    # Mappe zurück auf Original
    norm_count = 0
    for i, c in enumerate(original):
        if c.lower() in 'abcdefghijklmnopqrstuvwxyzäöüß0123456789':
            norm_count += 1
        if norm_count >= end_norm:
            return i + 1
    
    return len(original)


def main():
    print("=== GA002 Pagebreaks V4 ===\n")
    
    if not MSA_PATH.exists():
        print(f"FEHLER: {MSA_PATH} nicht gefunden!")
        return
    if not MSN_PATH.exists():
        print(f"FEHLER: {MSN_PATH} nicht gefunden!")
        return
    
    msa = MSA_PATH.read_text(encoding='utf-8')
    msn = MSN_PATH.read_text(encoding='utf-8')
    
    print(f"MsA: {MSA_PATH.name} ({len(msa):,} Zeichen)")
    print(f"MsN: {MSN_PATH.name} ({len(msn):,} Zeichen)")
    
    # Finde Seitenumbruch-Blöcke in MsN
    block_pattern = re.compile(
        r'RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+(\d+)\s*\n\s*---',
        re.IGNORECASE
    )
    
    pagebreaks = []
    for match in block_pattern.finditer(msn):
        page = int(match.group(1))
        start = match.start()
        
        # 200 Zeichen davor
        left_raw = msn[max(0, start-200):start]
        left = re.sub(r'\s+', ' ', left_raw).strip()
        
        # Worttrennung?
        hyphenated = bool(re.search(r'[-–—]\s*$', left))
        
        pagebreaks.append({
            'page': page,
            'next_page': page + 1,
            'left': left,
            'hyphenated': hyphenated
        })
    
    print(f"\nSeitenumbrüche in MsN: {len(pagebreaks)}")
    
    # Debug: Seite 7
    pb7 = next((p for p in pagebreaks if p['page'] == 7), None)
    if pb7:
        print(f"\nSeite 7 LEFT:")
        print(f"  ...{pb7['left'][-60:]}")
    
    # Finde Positionen in MsA
    insertions = []
    not_found = []
    last_norm_pos = 0
    
    msa_norm = normalize(msa)
    
    for pb in pagebreaks:
        left_norm = normalize(pb['left'])
        
        # Suche die letzten 40 Zeichen
        search = left_norm[-40:]
        
        pos = find_end_position(msa, search, last_norm_pos)
        
        if pos < 0:
            # Kürzere Suche
            search = left_norm[-25:]
            pos = find_end_position(msa, search, max(0, last_norm_pos - 1000))
        
        if pos >= 0:
            insertions.append({
                'pos': pos,
                'page': pb['next_page'],
                'hyphenated': pb['hyphenated']
            })
            # Update für nächste Suche
            search_in_norm = normalize(msa[:pos])
            last_norm_pos = len(search_in_norm) - 100
        else:
            not_found.append(pb['page'])
    
    print(f"\nGefunden: {len(insertions)}")
    print(f"Nicht gefunden: {len(not_found)}")
    if not_found:
        print(f"  Seiten: {not_found[:15]}...")
    
    # Debug: Position für Seite 8
    pb8 = next((i for i in insertions if i['page'] == 8), None)
    if pb8:
        pos = pb8['pos']
        print(f"\nSeite 8 Position {pos}:")
        print(f"  VOR:  '{msa[pos-20:pos]}'")
        print(f"  NACH: '{msa[pos:pos+20]}'")
    
    # Sortiere absteigend
    insertions.sort(key=lambda x: x['pos'], reverse=True)
    
    result = msa
    count = 0
    
    for ins in insertions:
        pos = ins['pos']
        page = ins['page']
        
        # Schon vorhanden?
        if f'|{page}|' in result[max(0, pos-10):pos+10]:
            continue
        
        if ins['hyphenated']:
            if pos > 0 and result[pos-1] in '-–—':
                result = result[:pos-1] + f'|{page}|' + result[pos:]
            else:
                result = result[:pos] + f'|{page}|' + result[pos:]
        else:
            result = result[:pos] + f' |{page}| ' + result[pos:]
        
        count += 1
    
    # Bereinige
    result = re.sub(r' {2,}', ' ', result)
    result = re.sub(r'\| ([.,;:!?»"])', r'|\1', result)
    
    markers = re.findall(r'\|(\d+)\|', result)
    print(f"\nMarker eingefügt: {count}")
    
    if markers:
        pages = sorted(set(int(m) for m in markers))
        print(f"Seiten: {min(pages)} - {max(pages)}")
    
    # Prüfe Seite 8
    m = re.search(r'.{30}\|8\|.{30}', result)
    if m:
        print(f"\nSeite 8: ...{m.group()}...")
    
    OUTPUT_PATH.write_text(result, encoding='utf-8')
    print(f"\nGespeichert: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
