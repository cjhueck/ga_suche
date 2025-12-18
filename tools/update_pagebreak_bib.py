import json
import sys

# Welche GAs aktualisieren?
target_gas = sys.argv[1:] if len(sys.argv) > 1 else ['GA003', 'GA009']

# Lade Bibliographie
with open('ga-bibliography.json', 'r', encoding='utf-8') as f:
    bib = json.load(f)

for ga_id in target_gas:
    filepath = f'pagebreak-books/{ga_id}.json'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f'{ga_id}: Datei nicht gefunden')
        continue
    
    # Extrahiere das Buch (kann in 'book' verschachtelt sein)
    book = data.get('book', data)
    bib_data = bib.get(ga_id, {})
    
    if not bib_data:
        print(f'{ga_id}: Keine Bibliographie gefunden')
        continue
    
    # Aktualisiere bibliographische Felder
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
    
    # Speichern (Struktur beibehalten)
    if 'book' in data:
        data['book'] = book
    else:
        data = book
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'{ga_id} aktualisiert:')
    print(f'  Titel: {book.get("Titel", "")}')
    print(f'  Untertitel: {book.get("Untertitel", "")}')
    print(f'  Jahr: {book.get("Jahr", "")}')
    print(f'  Verlag: {book.get("Verlag", "")}')
    print()

print('Fertig!')

