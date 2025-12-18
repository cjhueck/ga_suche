import json
import sys

ga = sys.argv[1] if len(sys.argv) > 1 else 'GA009'

try:
    data = json.load(open(f'pagebreak-books/{ga}.json', 'r', encoding='utf-8'))
    book = data.get('book', data)
    p = book.get('paragraphs', [])
    print(f'pagebreak-books/{ga}.json:')
    print(f'  Paragraphen: {len(p)}')
    if p:
        content = p[0].get('content', '')
        print(f'  Erster: {content[:120]}')
        # Zähle Marker
        markers = sum(1 for para in p if '|' in para.get('content', '') and any(c.isdigit() for c in para.get('content', '')))
        print(f'  Mit Markern: {markers}')
except FileNotFoundError:
    print(f'Datei nicht gefunden: pagebreak-books/{ga}.json')
except Exception as e:
    print(f'Fehler: {e}')

