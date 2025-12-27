import json
import re
import unicodedata

def normalize(text):
    if not text:
        return ''
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'-\s+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

# Lade Breaks
markers = json.load(open('page-break-markers.json', encoding='utf-8'))
breaks = markers.get('GA026', {}).get('breaks', [])

# Lade Buchtext
books = json.load(open('steiner-books/steiner-books-025-045-part03.json', encoding='utf-8'))
book = next((b for b in books['books'] if b.get('ID') == 'GA026'), None)
content = ' '.join(p.get('content','') for p in book.get('paragraphs', []))
content_norm = normalize(content)

# Prüfe Seiten 175-200
print('Prüfe Seiten 175-200:')
for b in breaks:
    if 175 <= b['page'] <= 200:
        right = b.get('right', '')
        if right:
            right_norm = normalize(right[:60])
            found = right_norm in content_norm if right_norm else False
            status = 'OK' if found else 'NICHT GEFUNDEN'
            print(f"  Seite {b['page']}: {status}")
            if not found:
                print(f"    Anchor: {right[:80]}...")

