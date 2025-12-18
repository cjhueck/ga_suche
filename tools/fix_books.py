import json

# Lade die aktualisierten Bücher (mit pagebreaks)
with open('GA003-with-pagebreaks.json', 'r', encoding='utf-8') as f:
    ga003_wrapper = json.load(f)
with open('GA009-with-pagebreaks.json', 'r', encoding='utf-8') as f:
    ga009_wrapper = json.load(f)

# Extrahiere das eigentliche Buch
ga003 = ga003_wrapper.get('book', ga003_wrapper)
ga009 = ga009_wrapper.get('book', ga009_wrapper)

# Lade Bibliographie
with open('ga-bibliography.json', 'r', encoding='utf-8') as f:
    bib = json.load(f)

# Aktualisiere bibliographische Daten
for book, ga_id in [(ga003, 'GA003'), (ga009, 'GA009')]:
    bib_data = bib.get(ga_id, {})
    
    book['ID'] = ga_id
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
    
    print(f'{ga_id}:')
    print(f'  Titel: {book.get("Titel", "")}')
    print(f'  Untertitel: {book.get("Untertitel", "")}')
    print(f'  Jahr: {book.get("Jahr", "")}')
    print()

# Lade Haupt-JSON
with open('steiner-books-001-011-part01.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Ersetze die Bücher
books = data.get('books', [])
for i, book in enumerate(books):
    book_id = book.get('ID', '')
    book_ga = book.get('ga', '')
    
    # Prüfe sowohl ID als auch ga-Feld
    if book_id == 'GA003' or book_ga == 'GA003':
        books[i] = ga003
        print(f'GA003 an Position {i} ersetzt')
    elif book_id == 'GA009' or book_ga == 'GA009':
        books[i] = ga009
        print(f'GA009 an Position {i} ersetzt')

# Speichern
with open('steiner-books-001-011-part01.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Fertig!')

