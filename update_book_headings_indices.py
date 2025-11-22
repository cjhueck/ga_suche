#!/usr/bin/env python3
"""
Aktualisiert die Überschriften-Indizes für Bücher GA001-GA013 in summary-database.json
Verknüpft jede Überschrift mit dem Index des ersten Paragraphs, der nach ihr kommt.
"""

import json
import re
from pathlib import Path

def convert_book_to_paragraphs(book_content):
    """Extrahiert Paragraphs aus Book-Content (wie in backend.js)"""
    paragraphs = []
    lines = book_content.split('\n')
    current_paragraph = ''
    current_index = None
    
    for line in lines:
        # Suche nach Index am Ende der Zeile (Format: ^abc123)
        index_match = re.search(r'\s+(\^[a-z0-9]+)\s*$', line)
        
        if index_match:
            index = index_match.group(1)
            line_without_index = re.sub(r'\s+\^[a-z0-9]+\s*$', '', line).strip()
            
            if current_paragraph or line_without_index:
                paragraphs.append({
                    'index': index,
                    'content': (current_paragraph + (' ' if current_paragraph else '') + line_without_index).strip(),
                    'text': (current_paragraph + (' ' if current_paragraph else '') + line_without_index).strip()
                })
            
            current_paragraph = ''
            current_index = index
        else:
            if line.strip():
                current_paragraph += (' ' if current_paragraph else '') + line.strip()
    
    if current_paragraph.strip():
        paragraphs.append({
            'index': current_index,
            'content': current_paragraph.strip(),
            'text': current_paragraph.strip()
        })
    
    return paragraphs

def find_paragraph_index_for_heading(heading_text, book_content, book_paragraphs):
    """Findet den Index des ersten Paragraphs nach einer Überschrift"""
    if not heading_text or not book_content:
        return None
    
    content_lower = book_content.lower()
    heading_text_lower = heading_text.lower()
    
    # Suche nach verschiedenen Varianten der Überschrift im Content
    heading_patterns = [
        re.compile(r'###+\s*' + re.escape(heading_text), re.IGNORECASE | re.MULTILINE),
        re.compile(r'##+\s*' + re.escape(heading_text), re.IGNORECASE | re.MULTILINE),
        re.compile(r'#+\s*' + re.escape(heading_text), re.IGNORECASE | re.MULTILINE),
        re.compile(r'^\s*' + re.escape(heading_text) + r'\s*$', re.IGNORECASE | re.MULTILINE)
    ]
    
    heading_position = -1
    for pattern in heading_patterns:
        match = pattern.search(content_lower)
        if match:
            heading_position = match.start()
            break
    
    # Wenn Überschrift gefunden, suche den ersten Paragraph danach
    if heading_position >= 0:
        for para in book_paragraphs:
            if para['index']:
                # Finde die Position dieses Paragraph-Index im Content
                index_pattern = re.compile(r'\s+' + re.escape(para['index']) + r'\s*$', re.MULTILINE)
                para_match = index_pattern.search(book_content)
                if para_match and para_match.start() > heading_position:
                    return para['index']
    
    # Fallback: Suche nach Paragraph, der mit der Überschrift beginnt
    for para in book_paragraphs:
        para_content_lower = (para.get('content') or para.get('text') or '').lower().strip()
        if para_content_lower.startswith(heading_text_lower):
            return para['index']
    
    return None

def update_book_headings(books_file, summary_db_file):
    """Aktualisiert die Überschriften-Indizes für alle Bücher"""
    
    # Lade Bücher
    print(f"Lade Bücher aus {books_file}...")
    with open(books_file, 'r', encoding='utf-8') as f:
        books_data = json.load(f)
    
    books = books_data.get('books', []) if isinstance(books_data, dict) else books_data
    
    # Lade summary-database.json
    print(f"Lade summary-database.json...")
    with open(summary_db_file, 'r', encoding='utf-8') as f:
        summary_db = json.load(f)
    
    updated_count = 0
    
    for book in books:
        book_id = book.get('ID') or book.get('gaNumber')
        if not book_id:
            continue
        
        # Nur GA001-GA013
        ga_match = re.match(r'GA0?([0-1][0-3])', book_id)
        if not ga_match:
            continue
        
        print(f"\nVerarbeite {book_id}...")
        
        # Prüfe ob Eintrag in summary-database existiert, erstelle neuen wenn nicht vorhanden
        if book_id not in summary_db:
            print(f"  [INFO] Erstelle neuen Eintrag in summary-database.json")
            summary_db[book_id] = {}
        
        # Verwende Überschriften aus dem Book-Export, falls vorhanden
        book_headings = book.get('headings', [])
        if book_headings:
            # Konvertiere Book-Headings zu summary-database Format
            headings_to_process = [
                {
                    'text': h.get('text', ''),
                    'level': f"h{h.get('level', 3)}"
                }
                for h in book_headings
            ]
        elif 'headings' in summary_db[book_id] and summary_db[book_id]['headings']:
            # Verwende vorhandene Überschriften aus summary-database
            headings_to_process = summary_db[book_id]['headings']
        else:
            print(f"  [WARN] Keine Überschriften vorhanden")
            continue
        
        # Extrahiere Paragraphs
        book_content = book.get('content', '')
        if not book_content:
            print(f"  [WARN] Kein Content vorhanden")
            continue
        
        book_paragraphs = convert_book_to_paragraphs(book_content)
        print(f"  {len(book_paragraphs)} Paragraphs extrahiert")
        
        # Aktualisiere Überschriften-Indizes
        updated_headings = []
        
        for heading in headings_to_process:
            heading_text = (heading.get('text') or heading.get('title') or '').strip()
            if not heading_text:
                continue
            
            # Finde Paragraph-Index für diese Überschrift
            paragraph_index = find_paragraph_index_for_heading(
                heading_text, book_content, book_paragraphs
            )
            
            if paragraph_index:
                updated_headings.append({
                    'index': paragraph_index,
                    'text': heading_text,
                    'level': heading.get('level', 'h3')
                })
                print(f"    [OK] \"{heading_text[:50]}...\" -> {paragraph_index}")
            else:
                # Fallback: Verwende alten Index
                old_index = heading.get('index', '')
                updated_headings.append({
                    'index': old_index,
                    'text': heading_text,
                    'level': heading.get('level', 'h3')
                })
                print(f"    [WARN] \"{heading_text[:50]}...\" -> Kein Paragraph gefunden (behalte: {old_index})")
        
        # Aktualisiere summary-database
        summary_db[book_id]['headings'] = updated_headings
        summary_db[book_id]['tableOfContents'] = [
            {
                'heading': h['text'],
                'description': '',
                'index': h['index']
            }
            for h in updated_headings
        ]
        
        updated_count += 1
        print(f"  [OK] {book_id}: {len(updated_headings)} Überschriften aktualisiert")
    
    # Speichere aktualisierte summary-database.json
    print(f"\nSpeichere aktualisierte summary-database.json...")
    with open(summary_db_file, 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Fertig! {updated_count} Bücher aktualisiert.")

if __name__ == '__main__':
    books_file = Path('steiner-books-001-013.json')
    summary_db_file = Path('summary-database.json')
    
    if not books_file.exists():
        print(f"Fehler: {books_file} nicht gefunden!")
        exit(1)
    
    if not summary_db_file.exists():
        print(f"Fehler: {summary_db_file} nicht gefunden!")
        exit(1)
    
    update_book_headings(books_file, summary_db_file)

