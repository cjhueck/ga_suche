import json
import re

with open('steiner-books/steiner-books-019-019.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

books = data.get('books', [])
print(f'Anzahl Bücher: {len(books)}')

if books:
    book = books[0]
    paras = book.get('paragraphs', [])
    print(f'Absätze: {len(paras)}')
    
    all_text = ' '.join(p['content'] for p in paras)
    markers = re.findall(r'\|\d+\|', all_text)
    print(f'Marker: {len(markers)}')
    
    # Finde Beispiele
    print('\nBeispiele aus JSON:')
    for m in re.finditer(r'.{25}\|\d+\|.{25}', all_text):
        print(f'  {m.group(0)}')
        if '|12|' in m.group(0):
            break

