#!/usr/bin/env python3
import sys
sys.path.insert(0, 'tools')
from generate_pagebreaks_with_pdf import extract_pdf_pages, find_pagebreak_position, normalize_for_comparison

pdf_path = 'Steiner_GA_pdf/Steiner, Rudolf GA 072, 1990 - Freiheit, Unsterblichkeit, soziales Leben.pdf'
pdf_pages = extract_pdf_pages(pdf_path)

# Lade MD-Datei
with open('Steiner_GA/GA072-Freiheit Unsterblichkeit Soziales Leben/GA072 (1.) DIE MENSCHENSEELE IM REICHE DES ÜBERSINNLICHEN UND IHR VERHÄLTNIS ZUM LEIB, Basel, 18. Oktober 1917 - Kopie.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Debug Seite 27
for pdf_idx, page_num, prev_end, this_start in pdf_pages:
    if page_num == 27:
        print('=== Seite 27 ===')
        print(f'prev_end (Ende S.26):')
        print(repr(prev_end[-100:]))
        print()
        print(f'this_start (Anfang S.27):')
        print(repr(this_start[:100]))
        print()
        
        # Teste Suche
        prev_clean = prev_end.replace("-\n", "").replace("\n", " ")
        this_clean = this_start.replace("-\n", "").replace("\n", " ")
        
        prev_norm = normalize_for_comparison(prev_clean[-50:])
        this_norm = normalize_for_comparison(this_clean[:50])
        content_norm = normalize_for_comparison(content)
        
        print(f'prev_norm: {prev_norm}')
        print(f'this_norm: {this_norm}')
        
        combined = prev_norm + this_norm
        print(f'Combined: {combined}')
        print(f'Combined in content: {combined in content_norm}')
        print(f'this_norm in content: {this_norm in content_norm}')
        
        if this_norm in content_norm:
            pos = content_norm.find(this_norm)
            print(f'this_norm gefunden bei: {pos}')
        
        # Suche manuell im MD
        print()
        print('Suche im MD nach "Hier muss":')
        if 'Hier muss' in content or 'Hier muß' in content:
            idx = content.find('Hier muss') if 'Hier muss' in content else content.find('Hier muß')
            print(f'Gefunden bei {idx}: {content[idx:idx+100]}')
        break

