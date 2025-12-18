import json

data = json.load(open('steiner-books-001-011-part01.json', 'r', encoding='utf-8'))
for i, b in enumerate(data.get('books', [])):
    if i in [2, 8]:  # Index 2 und 8 (GA003 und GA009)
        print(f'Index {i}:')
        print(f'  Keys: {list(b.keys())[:10]}')
        print(f'  ID: {b.get("ID", "NICHT VORHANDEN")}')
        print(f'  Titel: {b.get("Titel", "?")}')
        print()

