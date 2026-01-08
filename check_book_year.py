#!/usr/bin/env python3
import json

# Prüfe GA001 und GA002
files = [
    ('steiner-books/steiner-books-001-001.json', 'GA001'),
    ('steiner-books/steiner-books-002-002.json', 'GA002'),
]

for filepath, ga in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for book in data.get('books', []):
        if book.get('gaNumber', '').upper() == ga:
            print(f"\n{ga}:")
            print(f"  title: {book.get('title', '?')}")
            print(f"  year: {book.get('year', 'FEHLT!')}")
            print(f"  date: {book.get('date', '?')}")
            print(f"  dateString: {book.get('dateString', '?')}")
            # Zeige alle Keys
            print(f"  keys: {list(book.keys())}")

