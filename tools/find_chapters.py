#!/usr/bin/env python3
"""Finde Kapitelstruktur in Büchern"""
import json
from pathlib import Path

def find_chapters_ga007():
    for f in Path('steiner-books').glob('steiner-books-001-012-part01.json'):
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for book in data.get('books', []):
            if book.get('gaNumber', '').upper() == 'GA007':
                paras = book.get('paragraphs', [])
                print(f"GA007: {len(paras)} Absätze")
                
                # Suche kurze Absätze, die Kapitelüberschriften sein könnten
                for i, p in enumerate(paras):
                    content = (p.get('content') or p.get('text') or '').strip()
                    # Kurze Absätze mit Großbuchstaben könnten Überschriften sein
                    if len(content) < 80 and content.isupper():
                        print(f"{i:3}: {content}")
                    elif len(content) < 60 and i < 30:
                        print(f"{i:3}: [{len(content):2}] {content[:50]}")

if __name__ == "__main__":
    find_chapters_ga007()


