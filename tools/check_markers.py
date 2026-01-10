import json
import re

with open('steiner-books/steiner-books-019-019.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for book in data.get('books', []):
    all_text = ' '.join(p['content'] for p in book.get('paragraphs', []))
    markers = re.findall(r'\|(\d+)\|', all_text)
    
    print(f'Marker: {len(markers)}, Seiten: {min(int(m) for m in markers)}-{max(int(m) for m in markers)}')
    
    # Prüfe Formatierung
    good_spaces = len(re.findall(r' \|\d+\| ', all_text))
    word_splits = len(re.findall(r'\w\|\d+\|\w', all_text))
    punct_before = len(re.findall(r'[?!.,;:] \|\d+\|', all_text))
    
    print(f'  Mit Leerzeichen: {good_spaces}')
    print(f'  Worttrennungen: {word_splits}')
    print(f'  Satzzeichen vor Marker: {punct_before}')
    
    # Zeige Beispiele
    print('\nBeispiele:')
    count = 0
    for m in re.finditer(r'.{25}\|\d+\|.{25}', all_text):
        snippet = m.group(0).replace('\n', ' ')
        print(f'  {snippet}')
        count += 1
        if count >= 5:
            break
