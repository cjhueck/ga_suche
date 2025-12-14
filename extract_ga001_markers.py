#!/usr/bin/env python3
"""
Extrahiert Seitenmarker für GA001:
1. Liest die gedruckte Seitenzahl aus der PDF-Fußzeile
2. Findet den letzten Haupttext-Block jeder Seite (durch Abgleich mit MD-Datei)
3. Speichert die Marker in page-markers.json
"""

import fitz
import json
import re

# Pfade
pdf_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\Steiner, Rudolf GA 001, 1987 - Einleitungen zu Goethes naturwissenschaftlichen Schriften.pdf'
md_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA001-Goethes Naturwissenschaftliche Schriften\GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897).md'
json_path = r'steiner-books-001-008-part01.json'

# Lade MD-Datei als Referenz für Haupttext
print("Lade MD-Datei...")
with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Lade auch JSON für die finale Suche des afterText
print("Lade JSON-Datei...")
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Finde GA001 content
ga001_content = ''
for book in json_data.get('books', []):
    if book.get('ID') == 'GA001':
        ga001_content = book.get('content', '')
        break

print(f"MD: {len(md_content)} Zeichen")
print(f"JSON: {len(ga001_content)} Zeichen")

# Öffne PDF
doc = fitz.open(pdf_path)
print(f"PDF: {len(doc)} Seiten\n")

def get_printed_page_number(text):
    """Extrahiert die Seitenzahl aus 'Seite: X' (mit möglichen Leerzeichen)."""
    match = re.search(r'Seite:\s*([\d\s]+)', text)
    if match:
        page_str = match.group(1).replace(' ', '').strip()
        if page_str.isdigit():
            return int(page_str)
    return None

def normalize_text(text):
    """Normalisiert Text für Vergleich."""
    # Entferne Zeilenumbrüche, mehrfache Leerzeichen
    text = re.sub(r'\s+', ' ', text)
    # Entferne Trennstriche am Zeilenende (Wort-Trennung)
    text = re.sub(r'-\s*', '', text)
    # Ersetze typografische Zeichen
    text = text.replace('–', '-').replace('—', '-')
    text = text.replace('»', '"').replace('«', '"')
    return text.strip()

def find_text_in_content(text, content, min_words=4):
    """Findet einen Text im Content und gibt den gefundenen Abschnitt zurück."""
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Versuche verschiedene Wortanzahlen
    for word_count in [10, 8, 6, 5, 4]:
        if len(words) < word_count:
            continue
        
        # Suche von den letzten Wörtern
        search = ' '.join(words[-word_count:])
        if len(search) > 12 and search in content:
            return search
        
        # Suche auch vom Ende her mit weniger Wörtern am Ende (falls Trennstrich)
        if len(words) > word_count + 2:
            search = ' '.join(words[-(word_count+2):-2])
            if len(search) > 12 and search in content:
                return search
    
    return None

def is_in_md(block_text):
    """Prüft, ob ein Textblock im MD-Haupttext vorkommt."""
    # Normalisiere und nimm die ersten 30-50 Zeichen
    normalized = normalize_text(block_text)
    words = normalized.split()
    
    if len(words) < 4:
        return False
    
    # Suche nach den ersten 5-8 Wörtern
    for word_count in [8, 6, 5, 4]:
        if len(words) >= word_count:
            search = ' '.join(words[:word_count])
            if len(search) > 15 and search in md_content:
                return True
    
    return False

found_markers = []
missing_pages = []

print("Verarbeite Seiten...")
print(f"{'Seite':<8} {'Status':<12} {'Letzter Haupttext':<55}")
print("-" * 80)

for i in range(len(doc)):
    page = doc[i]
    full_text = page.get_text()
    
    # Extrahiere gedruckte Seitenzahl
    printed_page = get_printed_page_number(full_text)
    if printed_page is None:
        continue
    
    # Hole Textblöcke mit Position
    blocks = page.get_text("blocks")
    
    # Filtere und sortiere nach Y-Position
    text_blocks = []
    for block in blocks:
        x0, y0, x1, y1, text, block_no, block_type = block
        if block_type == 0:  # Nur Textblöcke
            text_clean = text.strip()
            # Ignoriere Copyright-Zeile
            if text_clean and not text_clean.startswith('Copyright') and not 'Buch:' in text_clean:
                text_blocks.append({
                    'y': y0,
                    'text': text_clean,
                    'is_main': is_in_md(text_clean)
                })
    
    # Sortiere nach Y-Position (von oben nach unten)
    text_blocks.sort(key=lambda b: b['y'])
    
    # Finde den letzten Haupttext-Block
    main_text_blocks = [b for b in text_blocks if b['is_main']]
    
    if not main_text_blocks:
        if printed_page >= 7:  # Text beginnt auf Seite 7
            missing_pages.append(printed_page)
        continue
    
    last_main_block = main_text_blocks[-1]
    last_text = last_main_block['text']  # Originaler Text (nicht normalisiert)
    
    # Finde passenden Text im JSON
    after_text = find_text_in_content(last_text, ga001_content)
    
    if after_text:
        found_markers.append({
            'page': printed_page,
            'afterText': after_text
        })
        status = "OK"
    else:
        # Versuche den vorletzten Block
        if len(main_text_blocks) >= 2:
            prev_block = main_text_blocks[-2]
            after_text = find_text_in_content(prev_block['text'], ga001_content)
            if after_text:
                found_markers.append({
                    'page': printed_page,
                    'afterText': after_text
                })
                status = "OK (prev)"
            else:
                missing_pages.append(printed_page)
                status = "NICHT GEFUNDEN"
        else:
            missing_pages.append(printed_page)
            status = "NICHT GEFUNDEN"
    
    if printed_page <= 25 or printed_page % 50 == 0:
        display_text = after_text[:50] if after_text else normalize_text(last_text)[:50]
        print(f"{printed_page:<8} {status:<12} {display_text}...")

doc.close()

# Sortiere Marker nach Seitenzahl
found_markers.sort(key=lambda m: m['page'])

print(f"\n{'='*80}")
print(f"ERGEBNIS: {len(found_markers)} Marker gefunden")
print(f"Fehlende Seiten: {len(missing_pages)}")
if missing_pages[:20]:
    print(f"  Erste fehlende: {missing_pages[:20]}")

# Speichere in page-markers.json
output = {
    "_info": "Seitenmarker für GA-Bände. 'afterText' = Text nach dem der Marker |page| eingefügt wird.",
    "GA001": {
        "title": "Einleitungen zu Goethes Naturwissenschaftlichen Schriften",
        "pdfSource": "Steiner, Rudolf GA 001, 1987 - Einleitungen zu Goethes naturwissenschaftlichen Schriften.pdf",
        "markers": found_markers
    },
    "GA009": {
        "title": "Theosophie",
        "pdfSource": "Steiner, Rudolf GA 009, 1987 - Theosophie.pdf",
        "markers": [
            {"page": 8, "afterText": "die den Zugang zu höheren Wirklichkeiten verschließen."}
        ]
    }
}

with open('page-markers.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nGespeichert in page-markers.json")
