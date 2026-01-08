#!/usr/bin/env python3
"""Prüft Seitenzahlen in Büchern GA001-GA007"""

import json
import re
import os

def check_book(ga_num):
    """Prüft Seitenzahlen in einem Buch"""
    
    # Finde die richtige JSON-Datei
    books_dir = "steiner-books"
    matching_files = []
    for f in os.listdir(books_dir):
        if f.startswith(f"steiner-books-{ga_num:03d}"):
            matching_files.append(f)
    
    if not matching_files:
        print(f"GA{ga_num:03d}: Keine Datei gefunden")
        return
    
    for filename in matching_files:
        filepath = os.path.join(books_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for book in data.get('books', []):
            ga_number = book.get('gaNumber', '?')
            if ga_number.upper() != f"GA{ga_num:03d}":
                continue
                
            found_pages = []
            first_page_para = None
            
            for para in book.get('paragraphs', []):
                content = para.get('content', '')
                matches = re.findall(r'\|(\d+)\|', content)
                if matches:
                    found_pages.extend(matches)
                    if first_page_para is None:
                        first_page_para = para.get('index', '?')
                        first_content = content[:150]
            
            if found_pages:
                print(f"GA{ga_num:03d}: Erste Seite = |{found_pages[0]}| (Para: {first_page_para})")
                print(f"  Text: {first_content}...")
                print(f"  Alle Seiten: {found_pages[:10]}{'...' if len(found_pages) > 10 else ''}")
            else:
                print(f"GA{ga_num:03d}: KEINE Seitenzahlen gefunden!")

# Prüfe GA001-007
for ga in range(1, 8):
    check_book(ga)
    print()

