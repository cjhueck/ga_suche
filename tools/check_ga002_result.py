#!/usr/bin/env python3
import json
import re
from pathlib import Path

data = json.loads(Path('GA002-with-pagebreaks.json').read_text(encoding='utf-8'))
print('Keys:', list(data.keys()))

book = data.get('book', data.get('books', [{}])[0] if 'books' in data else {})
print(f'Book keys: {list(book.keys())}')

paras = book.get('paragraphs', [])
print(f'Paragraphs: {len(paras)}')

# Suche Marker
marker_8 = '|8|'
marker_7 = '|7|'

for i, p in enumerate(paras[:100]):
    c = p.get('content', '')
    if marker_8 in c:
        idx = c.find(marker_8)
        print(f'\nSeite 8 in Para {i}:')
        print(f'  ...{c[max(0,idx-40):idx+40]}...')
    if marker_7 in c:
        idx = c.find(marker_7)
        print(f'\nSeite 7 in Para {i}:')
        print(f'  ...{c[max(0,idx-40):min(len(c),idx+40)]}...')

# Zähle alle Marker
all_markers = []
for p in paras:
    markers = re.findall(r'\|(\d+)\|', p.get('content', ''))
    all_markers.extend(markers)

if all_markers:
    pages = sorted(set(int(m) for m in all_markers))
    print(f'\nGefundene Marker: {len(all_markers)}')
    print(f'Seiten: {min(pages)} - {max(pages)}')
else:
    print('\nKeine Marker gefunden!')
