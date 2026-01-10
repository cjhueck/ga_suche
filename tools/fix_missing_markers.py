#!/usr/bin/env python3
"""
Fügt fehlende Seitenmarker in GA019/1 ein.
"""

import json
import re
from pathlib import Path


def normalize(text):
    """Entferne alles außer Buchstaben."""
    return re.sub(r'[^a-zA-ZäöüÄÖÜßéèêëàâáíìîïóòôúùûñç]', '', text.lower())


def find_and_insert(paragraphs, search_text, page_num):
    """Finde Textposition und füge Marker ein."""
    search_norm = normalize(search_text)
    
    # Suche in allen Absätzen
    for para in paragraphs:
        content = para['content']
        norm_content = normalize(content)
        
        pos = norm_content.find(search_norm)
        if pos >= 0:
            # Finde echte Position
            real_pos = 0
            norm_count = 0
            for i, c in enumerate(content):
                if norm_count >= pos:
                    real_pos = i
                    break
                if normalize(c):
                    norm_count += 1
            
            # Prüfe ob Marker schon existiert
            marker = f'|{page_num}|'
            if marker not in content:
                para['content'] = content[:real_pos] + marker + content[real_pos:]
                return True
    return False


def main():
    # Marker und ihre Suchtexte (Textanfang nach dem Marker)
    missing_markers = {
        9: "Unsägliches Leiden, tiefe Trauer leben",  # Anfang
        11: "Verwirrend können die Empfindungen sein",
        17: "von außen her zu uns hineingetragene",
        40: "dafür, dass die Frage: Wer wird diesen Krieg wollen",
        51: "dass auch hier diejenigen, welche sich nicht äußern",
        57: "einen instinktiven Ausdruck findet",
        58: "Das erwähnte politische Ideal hat die Gewohnheit entwickelt",
        63: "von Halász in dem Hefte",
        64: "Augenblicke empfindet, der hebt auch sein Urteil",
    }
    
    # Lade JSON
    json_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\steiner-full-lectures\steiner-full-lectures-014-354-part01.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Finde GA019/1
    for lec in data.get('lectures', []):
        if lec.get('ID') == 'GA019/1':
            paragraphs = lec.get('paragraphs', [])
            
            print(f"GA019/1: {len(paragraphs)} Absätze")
            
            inserted = 0
            for page, search in missing_markers.items():
                if find_and_insert(paragraphs, search, page):
                    print(f"  |{page}| eingefügt bei '{search[:30]}...'")
                    inserted += 1
                else:
                    print(f"  |{page}| NICHT GEFUNDEN: '{search[:30]}...'")
            
            print(f"\nGesamt eingefügt: {inserted}")
            break
    
    # Speichere
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON gespeichert!")


if __name__ == '__main__':
    main()

