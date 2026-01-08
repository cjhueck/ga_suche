#!/usr/bin/env python3
import json

# Suche in page-break-markers.json nach dem Kapitel-Start
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    markers = json.load(f)

breaks = markers.get('GA045', {}).get('breaks', [])
print("Suche nach 'CHARAKTER' oder 'ANTHROPOSOPHIE' in den Ankern:")
for b in breaks:
    right = b.get('right') or ''
    left = b.get('left') or ''
    if 'CHARAKTER' in right.upper() or 'ANTHROPOSOPHIE' in right.upper():
        print(f"  Seite {b.get('page')}: ...{left[-30:]} | {right[:60]}...")
    if 'CHARAKTER' in left.upper():
        print(f"  Seite {b.get('page')}: ...{left[-60:]} | {right[:30]}...")

# Suche auch im Buchtext
print("\nSuche im Buchtext:")
with open('steiner-books/steiner-books-023-045-part03.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

for book in books.get('books', []):
    if book.get('gaNumber', '').upper() == 'GA045':
        for i, para in enumerate(book.get('paragraphs', [])):
            content = para.get('content', '')
            if 'CHARAKTER DER ANTHROPOSOPHIE' in content.upper():
                print(f"  Absatz {i}: {content[:100]}...")
                break

