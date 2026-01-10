import json
import re
import glob

# Prüfe page-break-markers.json für GA091/1
print("=== Prüfe page-break-markers.json ===")
data = json.load(open('page-break-markers.json', encoding='utf-8'))

# Prüfe GA091 Key
key = 'GA091'
if key in data:
    markers = data[key]
    print(f'\n{key}: Typ={type(markers).__name__}')
    
    # V4-Format mit breaks
    if isinstance(markers, dict) and 'breaks' in markers:
        breaks = markers['breaks']
        print(f'Anzahl breaks: {len(breaks)}')
        
        # Extrahiere Seitennummern aus breaks
        pages = []
        for b in breaks:
            if isinstance(b, dict):
                page = b.get('page') or b.get('page_num')
                if page:
                    pages.append(page)
        
        print(f'Seiten: {pages}')
        
        # Zeige Details der ersten 5 breaks
        print('\nErste 5 breaks:')
        for b in breaks[:5]:
            print(f'  {b}')
        
        # Zeige breaks um Seite 37-41
        print('\nBreaks um 37-41:')
        for b in breaks:
            page = b.get('page') or b.get('page_num')
            if page and 35 <= page <= 45:
                print(f'  |{page}|: {b}')
    else:
        print(f'Unbekanntes Format: {list(markers.keys()) if isinstance(markers, dict) else type(markers)}')

