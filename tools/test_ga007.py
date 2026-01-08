#!/usr/bin/env python3
"""Test GA007 Verarbeitung"""
import sys
import time
sys.path.insert(0, 'tools')
from apply_pagebreaks_from_pdf import (
    load_books_for_ga, extract_pdf_pages, find_pdf_for_ga,
    process_lecture, normalize_for_comparison
)

print('Test GA007...')
pdf_path = find_pdf_for_ga('GA007')
print(f'PDF: {pdf_path}')

pdf_pages = extract_pdf_pages(pdf_path)
print(f'Seiten: {len(pdf_pages)}')

source_file, book = load_books_for_ga('GA007')
if book:
    print(f'Buch geladen: {book.get("title", "")[:50]}')
    paras = book.get('paragraphs', [])
    print(f'Absätze: {len(paras)}')
    total_chars = sum(len(p.get('content', '') or p.get('text', '')) for p in paras)
    print(f'Gesamt Zeichen: {total_chars}')
    
    # Test normalize_for_comparison Performance
    print('\nTest normalize_for_comparison...')
    start = time.time()
    full_text = ''.join(p.get('content', '') or p.get('text', '') for p in paras)
    normalized = normalize_for_comparison(full_text)
    elapsed = time.time() - start
    print(f'  Normalisierung: {elapsed:.2f}s für {len(full_text)} Zeichen -> {len(normalized)} normalisiert')
    
    # Test process_lecture
    print('\nTest process_lecture...')
    start = time.time()
    inserted, last_idx = process_lecture(book, pdf_pages, 1, 174, 0)
    elapsed = time.time() - start
    print(f'  process_lecture: {elapsed:.2f}s, {inserted} Marker eingefügt')
else:
    print('Kein Buch gefunden!')

