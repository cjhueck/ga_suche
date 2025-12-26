#!/usr/bin/env python3
"""Debug-Skript für GA012 Matching-Problem - V2"""
import json
import re
import sys
sys.path.insert(0, '.')
from apply_page_break_markers_v4 import normalize_simple, normalize_paragraphs_with_map

# Lade Pagebreak-Marker
markers = json.load(open('page-break-markers.json', encoding='utf-8'))
ga012_markers = markers.get('GA012', {}).get('breaks', [])

# Lade Buch
books_data = json.load(open('steiner-books/steiner-books-001-012-part01.json', encoding='utf-8'))
ga012_book = [b for b in books_data.get('books', []) if b.get('ID') == 'GA012'][0]
paras = ga012_book.get('paragraphs', [])

print(f"=== GA012 Debug ===")
print(f"Pagebreak-Marker: {len(ga012_markers)}")
print(f"Paragraphen: {len(paras)}")

# Normalisiere wie im Algorithmus
norm_content, norm_para, norm_char = normalize_paragraphs_with_map(paras)
print(f"Normalisierter Text: {len(norm_content)} Zeichen")

# Prüfe jeden Marker
print(f"\n=== Teste alle Marker ===")
successful = 0
failed = 0

for b in ga012_markers:
    page = b.get('page', 0)
    right = b.get('right', '')
    
    if not right or len(right) < 20:
        continue
    
    # Normalisiere RIGHT
    right_norm = normalize_simple(right)
    
    # Suche mit verschiedenen Längen
    found = False
    found_at = -1
    found_len = 0
    
    for search_len in [100, 80, 60, 40, 30, 20]:
        if search_len > len(right_norm):
            continue
        search_key = right_norm[:search_len]
        pos = norm_content.find(search_key)
        if pos >= 0:
            found = True
            found_at = pos
            found_len = search_len
            break
    
    if found:
        successful += 1
    else:
        failed += 1
        print(f"S.{page}: NICHT GEFUNDEN")
        print(f"  RIGHT: {right[:60]}...")
        print(f"  Normalisiert: {right_norm[:40]}")
        print()

print(f"\n=== Zusammenfassung ===")
print(f"Erfolgreich: {successful}")
print(f"Fehlgeschlagen: {failed}")

# Zeige die ersten 5 erfolgreichen und ersten 5 fehlgeschlagenen Seiten
print(f"\n=== Erste 10 Marker-Tests (detailliert) ===")
for i, b in enumerate(ga012_markers[:10]):
    page = b.get('page', 0)
    right = b.get('right', '')[:80]
    right_norm = normalize_simple(right)[:40]
    
    pos = norm_content.find(right_norm)
    status = f"gefunden@{pos}" if pos >= 0 else "NICHT GEFUNDEN"
    print(f"S.{page}: {status}")
    print(f"  → {right_norm}")

# Simuliere den sequentiellen Algorithmus
print(f"\n=== Simulation des sequentiellen Algorithmus ===")
last_norm_pos = 0
inserted = 0
start_page = None
start_pos_limit = int(len(norm_content) * 0.25)

for b in ga012_markers:
    page = b.get('page', 0)
    right = b.get('right', '')
    
    if not right or len(right) < 20 or page <= 0:
        continue
    
    right_norm = normalize_simple(right)
    
    # Suche ab last_norm_pos
    found_pos = -1
    for search_len in [100, 80, 60, 40, 30]:
        if search_len > len(right_norm):
            continue
        search_key = right_norm[:search_len]
        pos = norm_content.find(search_key, last_norm_pos)
        if pos >= 0:
            found_pos = pos
            break
    
    if found_pos < 0:
        print(f"S.{page}: nicht gefunden ab Position {last_norm_pos}")
        continue
    
    # Startseiten-Prüfung
    if start_page is None:
        if found_pos > start_pos_limit and page <= 50:
            print(f"S.{page}: start-too-late (pos={found_pos}, limit={start_pos_limit})")
            continue
        start_page = page
        last_norm_pos = found_pos
        inserted += 1
        print(f"S.{page}: STARTSEITE @ {found_pos}")
        continue
    
    # Jump-Prüfung
    delta = found_pos - last_norm_pos
    max_jump = max(40000, 15000)  # page_diff=1
    if delta > max_jump:
        print(f"S.{page}: jump-too-large (delta={delta}, max={max_jump})")
        continue
    
    # Erfolg
    inserted += 1
    last_norm_pos = found_pos + 1
    if inserted <= 20 or page >= 80:
        print(f"S.{page}: eingefügt @ {found_pos}")

print(f"\nGesamt eingefügt: {inserted}")

