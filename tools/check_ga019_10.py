"""Prüft GA019/10 in MD und JSON."""
import json
import re
from pathlib import Path

# Prüfe Overrides
print("=== Overrides ===")
override_dir = Path('pagebreaks')
if override_dir.exists():
    for f in override_dir.iterdir():
        if '019' in f.name and f.suffix == '.json':
            print(f"  {f.name}")
            # Prüfe Inhalt
            data = json.load(open(f, encoding='utf-8'))
            if isinstance(data, dict):
                for key in data.keys():
                    if '10' in key or key.endswith('/10'):
                        print(f"    -> Enthaelt {key}")

# Prüfe JSON
print("\n=== JSON (steiner-books-019-019.json) ===")
json_path = Path('steiner-books/steiner-books-019-019.json')
if json_path.exists():
    data = json.load(open(json_path, encoding='utf-8'))
    print(f"Top-Level Keys: {list(data.keys())}")
    
    books = data.get('books', [])
    print(f"Anzahl books: {len(books)}")
    
    if books:
        book = books[0]
        print(f"Book Keys: {list(book.keys())}")
        
        # Chapters?
        chapters = book.get('chapters', [])
        print(f"Chapters: {len(chapters)}")
        
        # Paragraphs direkt?
        paras = book.get('paragraphs', [])
        print(f"Paragraphs: {len(paras)}")
        
        # Zeige Kapitel-Struktur
        print("\nKapitel-Struktur:")
        for i, ch in enumerate(chapters):
            print(f"  {i+1}. Keys: {list(ch.keys())}")
            title = ch.get('title', '')[:60]
            print(f"     title: {title}")
            for key in ch.keys():
                val = ch[key]
                if key != 'title':
                    print(f"     {key}: {type(val).__name__} = {str(val)[:50]}")
            if i >= 2:  # Nur erste 3 zeigen
                print("  ...")
                break
        
        # Berechne Start-Index fuer jedes Kapitel
        print("\n=== Kapitel 10 Inhalt ===")
        start_idx = 0
        for ch in chapters:
            num = ch['number']
            count = ch['paragraphs']
            end_idx = start_idx + count - 1
            
            if num == 10:
                print(f"Kapitel 10: Absaetze {start_idx}-{end_idx} ({count} Stueck)")
                print(f"\nErste 3 Absaetze von Kapitel 10:")
                for i in range(start_idx, min(start_idx + 3, len(paras))):
                    p = paras[i]
                    idx = p.get('index', '?')
                    content = p.get('content', '')[:100]
                    print(f"  [{i}] ^{idx}: {content}...")
            
            start_idx += count
else:
    print("JSON nicht gefunden!")
    
# Prüfe auch steiner-full-lectures
print("\n=== steiner-full-lectures ===")
for f in Path('steiner-full-lectures').glob('*part*.json'):
    data = json.load(open(f, encoding='utf-8'))
    lectures = data.get('lectures', [])
    for lec in lectures:
        ga = lec.get('ga_number', '')
        if str(ga) == '19' or str(ga) == '019':
            lec_num = lec.get('lecture_number', '?')
            title = lec.get('title', '')[:50]
            paras = lec.get('paragraphs', [])
            print(f"GA{ga}/{lec_num}: {title}... ({len(paras)} Absaetze)")

# Prüfe MD-Datei
print("\n=== MD-Datei ===")
ga_folder = None
for d in Path('Steiner_GA').iterdir():
    if 'GA019' in d.name:
        ga_folder = d
        break

if ga_folder:
    for f in ga_folder.iterdir():
        if '(10.)' in f.name and f.suffix == '.md' and '_backup' not in f.name:
            print(f"Datei: {f.name}")
            content = f.read_text(encoding='utf-8')
            print(f"Länge: {len(content)} Zeichen")
            
            # Marker
            markers = re.findall(r'\|(\d+)\|', content)
            if markers:
                print(f"Marker: {markers}")
            
            # Erster Absatz
            paras = content.split('\n\n')
            for p in paras[:3]:
                if p.strip() and len(p.strip()) > 20:
                    print(f"Anfang: {p.strip()[:150]}...")
                    break

