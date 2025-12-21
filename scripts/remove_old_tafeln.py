"""
Entfernt alte Tafel-Bilder aus den steiner-full-lectures JSON-Dateien.
Diese werden durch chalkboards.json ersetzt.
"""

import json
import re
from pathlib import Path

# Alle full-lectures Dateien durchgehen
lectures_dir = Path('steiner-full-lectures')
removed_count = 0
files_modified = 0

# Pattern für alte Tafel-Referenzen
TAFEL_PATTERNS = [
    # Format 1: <img src="assets/GA191-1919-10-03-T01.webp" alt="Tafel 1" />
    r'^(<h2>Wandtafelzeichnungen</h2>\n)?<img src=["\']assets/GA\d+[A-Za-z]?-\d{4}-\d{2}-\d{2}-T\d+[A-Za-z]?\.webp["\'] alt=["\']Tafel \d+[A-Za-z]?["\'] ?/>$',
    # Format 2: <h2>Wandtafelzeichnungen</h2>\n![Tafel 1](assets/GA073a-T01.webp)
    r'^(<h2>Wandtafelzeichnungen</h2>\n)?!\[Tafel \d+[A-Za-z]?\]\(assets/GA\d+[A-Za-z]?-T\d+[A-Za-z]?\.webp\)$',
    # Format 3: Nur Markdown-Bild mit Tafel
    r'^!\[Tafel \d+[A-Za-z]?\]\(assets/GA\d+[A-Za-z]?.*?\.webp\)$',
]

for json_file in lectures_dir.glob('*.json'):
    print(f'Prüfe: {json_file.name}')
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modified = False
    
    # Bestimme das Vortrags-Array (kann direkt oder unter "lectures" sein)
    if isinstance(data, list):
        lectures = data
    elif isinstance(data, dict) and 'lectures' in data:
        lectures = data['lectures']
    else:
        print(f'  Unbekanntes Format, überspringe')
        continue
    
    # Durchgehe alle Vorträge
    for lecture in lectures:
        if 'paragraphs' in lecture:
            # Filter: Entferne Paragraphen die NUR Tafel-Bilder enthalten
            new_paragraphs = []
            for para in lecture['paragraphs']:
                content = para.get('content', '')
                
                # Prüfe alle Patterns
                is_pure_tafel = False
                for pattern in TAFEL_PATTERNS:
                    if re.match(pattern, content):
                        is_pure_tafel = True
                        break
                
                if is_pure_tafel:
                    removed_count += 1
                    modified = True
                    print(f'  Entferne: {content[:80]}...')
                else:
                    new_paragraphs.append(para)
            
            lecture['paragraphs'] = new_paragraphs
    
    if modified:
        files_modified += 1
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f'  -> Datei aktualisiert')

print(f'\n=== Fertig ===')
print(f'Entfernte Tafel-Absätze: {removed_count}')
print(f'Geänderte Dateien: {files_modified}')





