#!/usr/bin/env python3
"""
Überträgt Seitenmarker aus Mistral OCR MD-Datei in JSON.

Mistral OCR Format:
    ...Text von Seite X...
    RUDOLF STEINER
    VERLAG
    Seite X
    ---
    ...Text von Seite X+1...

Der Marker "Seite X" steht am ENDE von Seite X.
Also beginnt der Text DANACH mit Seite X+1.
"""

import json
import re
from pathlib import Path


def main():
    # 1. Finde und lade konvertierte MD
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    md_path = None
    
    for d in base.iterdir():
        if 'GA019' in d.name:
            for sub in d.iterdir():
                if sub.is_dir() and 'Steiner, Rudolf' in sub.name:
                    for f in sub.iterdir():
                        if f.suffix == '.md' and '_converted' not in f.name:
                            md_path = f
                            break
    
    if not md_path:
        print("MD-Datei nicht gefunden!")
        return
    
    print(f"MD geladen: {md_path}")
    md_content = md_path.read_text(encoding='utf-8')
    print(f"  {len(md_content)} Zeichen")
    
    # 2. Konvertiere: "Seite X" -> |X+1| (weil Seite X am ENDE steht)
    pattern = r'\n*RUDOLF STEINER\s*\n\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---\n*'
    
    def replace_marker(match):
        page_num = int(match.group(1))
        next_page = page_num + 1  # Text DANACH ist Seite X+1
        return f'|{next_page}|'
    
    converted = re.sub(pattern, replace_marker, md_content, flags=re.IGNORECASE)
    
    # Entferne auch alleinstehende "Seite X"
    converted = re.sub(r'\nSeite\s+\d+\s*\n', '\n', converted)
    converted = re.sub(r'\n{3,}', '\n\n', converted)
    
    # Zähle Marker
    markers = re.findall(r'\|(\d+)\|', converted)
    print(f"Marker erstellt: {len(markers)}")
    if markers:
        print(f"  Erste: |{markers[0]}|, Letzte: |{markers[-1]}|")
    
    # 3. Lade JSON
    json_path = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\steiner-full-lectures\steiner-full-lectures-014-354-part01.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 4. Finde GA019 Lectures
    ga019_lectures = [l for l in data.get('lectures', []) if l.get('ID', '').startswith('GA019')]
    print(f"GA019 Vorträge: {len(ga019_lectures)}")
    
    # 5. Entferne alte Marker aus JSON
    for lec in ga019_lectures:
        for para in lec.get('paragraphs', []):
            para['content'] = re.sub(r'\|\d+\|', '', para['content'])
    
    # 6. Normalisiere Text für Vergleich
    def normalize(text):
        # Entferne alles außer Buchstaben
        return re.sub(r'[^a-zA-ZäöüÄÖÜßéèêëàâáíìîïóòôúùûñç]', '', text.lower())
    
    # 7. Extrahiere Marker-Positionen aus MD
    md_markers = []
    for m in re.finditer(r'\|(\d+)\|', converted):
        page = int(m.group(1))
        # Text vor und nach dem Marker
        before = converted[max(0, m.start()-150):m.start()]
        after = converted[m.end():m.end()+150]
        md_markers.append({
            'page': page,
            'before_norm': normalize(before),
            'after_norm': normalize(after),
            'before_raw': before[-50:],
            'after_raw': after[:50]
        })
    
    print(f"MD Marker extrahiert: {len(md_markers)}")
    
    # 8. Füge Marker in JSON ein
    inserted = 0
    not_found = 0
    
    for lec in ga019_lectures:
        lec_id = lec.get('ID', '')
        
        # Sammle gesamten Text des Vortrags
        paragraphs = lec.get('paragraphs', [])
        full_text = '\n'.join(p['content'] for p in paragraphs)
        norm_text = normalize(full_text)
        
        lec_inserted = 0
        
        for marker in md_markers:
            if marker['page'] < 9:  # Skip Titelseiten etc.
                continue
            
            # Suche nach der Marker-Position
            search_before = marker['before_norm'][-80:]
            search_after = marker['after_norm'][:80]
            search = search_before + search_after
            
            pos = norm_text.find(search)
            if pos < 0:
                # Kürzere Suche
                search = search_before[-40:] + search_after[:40]
                pos = norm_text.find(search)
            
            if pos >= 0:
                # Position gefunden - jetzt in Absatz einfügen
                target_pos = pos + len(search_before)
                
                # Finde den richtigen Absatz
                char_count = 0
                for para in paragraphs:
                    norm_para = normalize(para['content'])
                    para_end = char_count + len(norm_para)
                    
                    if target_pos <= para_end:
                        # Marker gehört in diesen Absatz
                        rel_pos = target_pos - char_count
                        
                        # Finde echte Position im Original-Text
                        real_pos = 0
                        norm_count = 0
                        content = para['content']
                        
                        for i, c in enumerate(content):
                            if norm_count >= rel_pos:
                                real_pos = i
                                break
                            if normalize(c):
                                norm_count += 1
                        else:
                            real_pos = len(content)
                        
                        # Prüfe ob Marker schon existiert
                        marker_str = f"|{marker['page']}|"
                        if marker_str not in para['content']:
                            para['content'] = content[:real_pos] + marker_str + content[real_pos:]
                            inserted += 1
                            lec_inserted += 1
                        break
                    
                    char_count = para_end
            else:
                not_found += 1
        
        if lec_inserted > 0:
            print(f"  {lec_id}: {lec_inserted} Marker")
    
    print(f"\nGesamt eingefügt: {inserted}")
    print(f"Nicht gefunden: {not_found}")
    
    # 9. Speichere
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON gespeichert: {json_path}")


if __name__ == '__main__':
    main()

