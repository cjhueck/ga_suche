#!/usr/bin/env python3
"""Debug-Skript für GA012 - teste den echten Algorithmus"""
import json
import sys
sys.path.insert(0, '.')
from apply_page_break_markers_v4 import (
    normalize_simple, 
    normalize_paragraphs_with_map,
    find_best_insertion
)

# Lade Pagebreak-Marker
markers = json.load(open('page-break-markers.json', encoding='utf-8'))
ga012_markers = markers.get('GA012', {}).get('breaks', [])

# Lade Buch
books_data = json.load(open('steiner-books/steiner-books-001-012-part01.json', encoding='utf-8'))
ga012_book = [b for b in books_data.get('books', []) if b.get('ID') == 'GA012'][0]
paras = ga012_book.get('paragraphs', [])

print(f"=== GA012 Debug mit echtem Algorithmus ===")
print(f"Pagebreak-Marker: {len(ga012_markers)}")
print(f"Paragraphen: {len(paras)}")

# Normalisiere wie im Algorithmus
norm_content, norm_para, norm_char = normalize_paragraphs_with_map(paras)
print(f"Normalisierter Text: {len(norm_content)} Zeichen")

# Teste find_best_insertion für alle Marker
print(f"\n=== Test find_best_insertion ===")
last_norm_pos = 0
inserted = 0
start_page = None
start_pos_limit = int(len(norm_content) * 0.25)
last_inserted_page = None

for b in ga012_markers:
    page = b.get('page', 0)
    left = b.get('left', '') or ''
    right = b.get('right', '') or ''
    hyph = bool(b.get('hyphenated'))
    
    if page <= 0:
        continue
    
    # Echte find_best_insertion Funktion
    result = find_best_insertion(
        norm_content, norm_para, norm_char,
        left, right, hyph,
        min_norm_pos=last_norm_pos
    )
    
    if result is None:
        # Zweiter Versuch ohne LEFT
        result = find_best_insertion(
            norm_content, norm_para, norm_char,
            "", right, hyph,
            min_norm_pos=last_norm_pos
        )
    
    if result is None:
        print(f"S.{page}: NICHT GEFUNDEN (last_norm_pos={last_norm_pos})")
        continue
    
    p_i, c_i, norm_pos = result
    
    # Startseiten-Prüfung
    if start_page is None:
        if norm_pos > start_pos_limit and page <= 50:
            print(f"S.{page}: start-too-late (pos={norm_pos}, limit={start_pos_limit})")
            continue
        start_page = page
        last_norm_pos = norm_pos
        last_inserted_page = page
        inserted += 1
        print(f"S.{page}: STARTSEITE @ {norm_pos}")
        continue
    
    # Jump-Prüfung
    if last_inserted_page is not None:
        page_diff = max(1, page - last_inserted_page)
    else:
        page_diff = 1
    delta = norm_pos - last_norm_pos
    max_jump = max(40000, page_diff * 15000)
    if delta > max_jump:
        print(f"S.{page}: jump-too-large (delta={delta}, max={max_jump}, page_diff={page_diff})")
        continue
    
    # Erfolg
    inserted += 1
    last_norm_pos = norm_pos + 1
    last_inserted_page = page
    if inserted <= 25 or page >= 75:
        print(f"S.{page}: eingefügt @ {norm_pos}")

print(f"\nGesamt eingefügt: {inserted}")

