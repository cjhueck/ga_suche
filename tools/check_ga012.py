import json
import re
import unicodedata

def normalize(text):
    """Normalisiere Text für Vergleich"""
    if not text:
        return ''
    # Normalisiere Unicode
    text = unicodedata.normalize('NFC', text)
    # Entferne Bindestriche am Zeilenende
    text = re.sub(r'-\s+', '', text)
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

# Lade die Breaks - explizit neu laden
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    markers = json.load(f)
ga012 = markers.get('GA012', {})
breaks = ga012.get('breaks', [])

# Lade den Buchtext
with open('steiner-books/steiner-books-001-012-part01.json', 'r', encoding='utf-8') as f:
    books = json.load(f)
book = next((b for b in books['books'] if b.get('ID') == 'GA012'), None)

if book:
    content = ' '.join(p.get('content','') for p in book.get('paragraphs', []))
    content_norm = normalize(content)
    
    print(f'Buchlänge: {len(content)} Zeichen')
    print()
    
    # Zähle Matches
    found_count = 0
    not_found = []
    
    for b in breaks:
        right = b.get('right', '')
        if right:
            # Versuche verschiedene Matching-Strategien
            right_norm = normalize(right[:50])
            if right_norm in content_norm:
                found_count += 1
            else:
                not_found.append(b['page'])
    
    print(f'Gefunden: {found_count} von {len(breaks)}')
    print(f'Nicht gefunden (erste 20): {not_found[:20]}')
    
    # Zeige ein Beispiel
    if breaks:
        b = breaks[0]
        right = b.get('right', '')[:100]
        print()
        print(f'Beispiel Seite {b["page"]}:')
        print(f'  Break-Text: "{right}"')
        print(f'  Break-Norm: "{normalize(right)[:80]}"')
        
        # Suche im Buch nach ähnlichem Text
        search = 'geisteswissenschaft'
        if search in content_norm:
            idx = content_norm.index(search)
            print(f'  Gefunden "{search}" bei Position {idx}')
            print(f'  Kontext: "...{content[max(0,idx-20):idx+80]}..."')
    # Finde die erste Seite, die im Text gefunden wird
    print()
    print('Suche erste gefundene Seite...')
    for b in breaks:
        right = b.get('right', '')
        if right:
            right_norm = normalize(right[:60])
            if right_norm and right_norm in content_norm:
                print(f'Erste gefundene Seite: {b["page"]}')
                print(f'Text: "{right[:80]}..."')
                break
else:
    print('Buch nicht gefunden')

