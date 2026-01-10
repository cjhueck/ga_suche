#!/usr/bin/env python3
"""
Aktualisiert JSON-Texte mit MsN_converted (inkl. Seitenmarker).

Behält:
- Struktur (Aufteilung in Vorträge/Aufsätze)
- Überschriften, Zwischenüberschriften, Summaries, Keywords
- Absatz-IDs (^xxxxx)

Übernimmt aus MsN_converted:
- Text-Inhalt
- Seitenmarker (|XX|)

Verwendung:
    python tools/update_json_from_msn.py GA019
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


def extract_block_id(text: str) -> tuple:
    """Extrahiere Block-ID (^xxxxx) vom Ende des Textes."""
    match = re.search(r'\s*(\^[a-z0-9]+)\s*$', text)
    if match:
        block_id = match.group(1)
        text_without_id = text[:match.start()]
        return text_without_id.strip(), block_id
    return text.strip(), None


def find_text_in_msn(para_text: str, msn_content: str, msn_norm: str) -> str:
    """Finde entsprechenden Text in MsN_converted."""
    # Entferne alte Marker und Block-ID
    clean_text = re.sub(r'\|\d+\|', '', para_text)
    clean_text, block_id = extract_block_id(clean_text)
    
    if len(clean_text) < 20:
        return None
    
    # Normalisiere für Suche
    para_norm = normalize(clean_text)
    
    if len(para_norm) < 15:
        return None
    
    # Suche nach Anfang des Absatzes
    search_start = para_norm[:50]
    start_pos = msn_norm.find(search_start)
    
    if start_pos < 0:
        # Kürzere Suche
        search_start = para_norm[:30]
        start_pos = msn_norm.find(search_start)
    
    if start_pos < 0:
        return None
    
    # Suche nach Ende des Absatzes
    search_end = para_norm[-50:]
    end_search_start = start_pos + len(para_norm) - 100
    end_pos = msn_norm.find(search_end, max(0, end_search_start))
    
    if end_pos < 0:
        search_end = para_norm[-30:]
        end_pos = msn_norm.find(search_end, max(0, end_search_start))
    
    if end_pos < 0:
        # Schätze Ende basierend auf Länge
        end_pos = start_pos + len(para_norm)
    else:
        end_pos += len(search_end)
    
    # Konvertiere normalisierte Position zu echter Position
    def norm_pos_to_real(content: str, norm_pos: int) -> int:
        real_pos = 0
        norm_count = 0
        for i, c in enumerate(content):
            if norm_count >= norm_pos:
                return i
            if normalize(c):
                norm_count += 1
        return len(content)
    
    real_start = norm_pos_to_real(msn_content, start_pos)
    real_end = norm_pos_to_real(msn_content, end_pos)
    
    # Erweitere auf Absatzgrenzen
    while real_start > 0 and msn_content[real_start - 1] not in '\n':
        real_start -= 1
    while real_end < len(msn_content) and msn_content[real_end] not in '\n':
        real_end += 1
    
    extracted = msn_content[real_start:real_end].strip()
    
    # Prüfe Ähnlichkeit
    extracted_norm = normalize(extracted)
    similarity = SequenceMatcher(None, para_norm, extracted_norm).ratio()
    
    if similarity > 0.7:
        return extracted
    
    return None


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python update_json_from_msn.py GA019")
        sys.exit(1)
    
    ga_num = sys.argv[1].upper()
    if not ga_num.startswith('GA'):
        ga_num = f'GA{ga_num}'
    
    # Finde MsN_converted
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    msn_path = None
    
    for d in base.iterdir():
        if ga_num in d.name:
            for f in d.iterdir():
                if f.suffix == '.md' and '_converted' in f.name:
                    msn_path = f
                    break
    
    if not msn_path:
        print(f"MsN_converted nicht gefunden für {ga_num}")
        print("Führe zuerst aus: python tools/convert_msn_to_msa.py " + ga_num)
        sys.exit(1)
    
    print(f"MsN_converted: {msn_path.name}")
    
    # Lade MsN_converted
    msn_content = msn_path.read_text(encoding='utf-8')
    msn_norm = normalize(msn_content)
    print(f"  {len(msn_content)} Zeichen, {len(re.findall(r'\|\d+\|', msn_content))} Marker")
    
    # Finde JSON-Datei
    json_dir = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\steiner-full-lectures')
    json_path = None
    
    for f in json_dir.glob('*.json'):
        with open(f, 'r', encoding='utf-8') as jf:
            try:
                data = json.load(jf)
                for lec in data.get('lectures', []):
                    if lec.get('ID', '').startswith(ga_num):
                        json_path = f
                        break
                if json_path:
                    break
            except:
                pass
    
    if not json_path:
        print(f"JSON-Datei nicht gefunden für {ga_num}")
        sys.exit(1)
    
    print(f"JSON: {json_path.name}")
    
    # Lade JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Verarbeite jeden Vortrag
    total_updated = 0
    total_paragraphs = 0
    
    for lec in data.get('lectures', []):
        if not lec.get('ID', '').startswith(ga_num):
            continue
        
        lec_id = lec.get('ID')
        lec_updated = 0
        
        for para in lec.get('paragraphs', []):
            total_paragraphs += 1
            old_content = para.get('content', '')
            
            # Extrahiere Block-ID
            text_without_id, block_id = extract_block_id(old_content)
            
            # Finde entsprechenden Text in MsN
            new_text = find_text_in_msn(old_content, msn_content, msn_norm)
            
            if new_text:
                # Füge Block-ID wieder hinzu
                if block_id:
                    new_content = new_text + ' ' + block_id
                else:
                    new_content = new_text
                
                # Prüfe ob sich etwas geändert hat
                if normalize(new_content) != normalize(old_content):
                    para['content'] = new_content
                    lec_updated += 1
        
        if lec_updated > 0:
            print(f"  {lec_id}: {lec_updated} Absätze aktualisiert")
            total_updated += lec_updated
    
    print(f"\nGesamt: {total_updated}/{total_paragraphs} Absätze aktualisiert")
    
    # Speichere JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON gespeichert: {json_path}")


if __name__ == '__main__':
    main()

