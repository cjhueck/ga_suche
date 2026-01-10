from export_books_master import BooksExporter
from pathlib import Path
import json

exporter = BooksExporter(parallel_workers=1, skip_spelling=True)
folder = Path(r'Steiner_GA\GA019-Gedanken während der Zeit des Krieges')

print(f'Processing: {folder.name}')
book = exporter.process_book(folder)
print(f'Book returned: {book is not None}')
if book:
    paras = book.get('paragraphs', [])
    print(f'Paragraphs: {len(paras)}')
    if paras:
        print(f'First: {paras[0].get("content", "")[:80]}...')
    
    # Direkt speichern
    output_data = {
        'metadata': {
            'exportDate': '2026-01-09',
            'totalBooks': 1,
            'gaRange': 'GA019-GA019'
        },
        'books': [book]
    }
    
    with open('steiner-books/steiner-books-019-019.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f'\nJSON gespeichert!')

