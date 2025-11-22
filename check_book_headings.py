#!/usr/bin/env python3
import json

# Prüfe summary-database.json
print("=== Bücher in summary-database.json ===")
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

book_ids = []
for k in summary_db.keys():
    if k.startswith('GA0'):
        try:
            num = int(k.replace('GA', '').split('/')[0])  # Ignoriere "/11" etc.
            if 1 <= num <= 13:
                book_ids.append(k)
        except ValueError:
            pass
for book_id in sorted(book_ids):
    headings = summary_db[book_id].get('headings', [])
    print(f"{book_id}: {len(headings)} Überschriften")
    if headings:
        # Zeige ersten Index-Typ
        first_index = headings[0].get('index', '')
        index_type = 'Paragraph-Index' if first_index.startswith('^') else 'String-Index'
        print(f"  -> Index-Typ: {index_type} (Beispiel: {first_index})")

print("\n=== Bücher in steiner-books-001-013.json ===")
with open('steiner-books-001-013.json', 'r', encoding='utf-8') as f:
    books_data = json.load(f)

books = books_data.get('books', []) if isinstance(books_data, dict) else books_data
for book in books:
    book_id = book.get('ID') or book.get('gaNumber', '')
    headings = book.get('headings', [])
    print(f"{book_id}: {len(headings)} Überschriften im Export")

