import json
import sys

# Welche GAs aktualisieren?
target_gas = sys.argv[1:] if len(sys.argv) > 1 else ['GA003', 'GA009']

# Lade Bibliographie
with open('ga-bibliography.json', 'r', encoding='utf-8') as f:
    bib = json.load(f)

# Lade Bücher
with open('steiner-books-001-011-part01.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

books = data.get('books', [])
updated = []

for book in books:
    book_id = book.get('ID', '')
    if book_id in target_gas:
        bib_data = bib.get(book_id, {})
        
        # Aktualisiere bibliographische Felder
        if bib_data.get('title'):
            book['Titel'] = bib_data['title']
        if bib_data.get('subtitle'):
            book['Untertitel'] = bib_data['subtitle']
        if bib_data.get('author'):
            book['Autor'] = bib_data['author']
        if bib_data.get('year'):
            book['Jahr'] = bib_data['year']
        if bib_data.get('place'):
            book['Ort'] = bib_data['place']
        if bib_data.get('publisher'):
            book['Verlag'] = bib_data['publisher']
        if bib_data.get('edition'):
            book['Auflage'] = bib_data['edition']
        if bib_data.get('isbn'):
            book['ISBN'] = bib_data['isbn']
        if bib_data.get('originalPublication'):
            book['Originalausgabe'] = bib_data['originalPublication']
        
        updated.append(book_id)
        print(f'{book_id} aktualisiert:')
        print(f'  Titel: {book.get("Titel", "")}')
        print(f'  Untertitel: {book.get("Untertitel", "")}')
        print(f'  Jahr: {book.get("Jahr", "")}')
        print(f'  Verlag: {book.get("Verlag", "")}')
        print()

# Speichern
with open('steiner-books-001-011-part01.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Aktualisiert: {updated}')

