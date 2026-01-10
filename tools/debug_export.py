"""Debug-Skript für Export."""
import sys
sys.path.insert(0, '.')
from export_books_master import BooksExporter

print("=== Debug Export GA019 ===")
exporter = BooksExporter(parallel_workers=1)

# Monkey-patch save_json um zu sehen was gespeichert wird
original_save = exporter.save_json
def debug_save(data):
    books = data.get('books', [])
    print(f"\n[DEBUG] save_json aufgerufen mit {len(books)} Buechern")
    if books:
        for b in books:
            print(f"  - {b.get('gaNumber')}: {b.get('title', '')[:50]}")
    original_save(data)

exporter.save_json = debug_save

success = exporter.export_books(ga_numbers=['GA019'])

print(f"\n=== Ergebnis ===")
print(f"success: {success}")
print(f"len(self.books): {len(exporter.books)}")

