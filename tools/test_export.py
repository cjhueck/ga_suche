from export_books_master import BooksExporter
from pathlib import Path

exporter = BooksExporter(parallel_workers=1, skip_spelling=True)

# Direkt process_book aufrufen
folder = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA019-Gedanken während der Zeit des Krieges')

print(f"Processing: {folder.name}")
book = exporter.process_book(folder)

print(f'\nBook returned: {book is not None}')
if book:
    print(f'Book ID: {book.get("ID")}')
    print(f'Paragraphs: {len(book.get("paragraphs", []))}')
    
    # Zeige ersten Absatz
    paras = book.get('paragraphs', [])
    if paras:
        content = paras[0].get('content', '')[:100]
        print(f'First para: {content}...')
else:
    print("Book is None - no export!")

