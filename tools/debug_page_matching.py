#!/usr/bin/env python3
"""
Debug-Script für Seitenmarker-Matching
Zeigt warum bestimmte Seiten nicht gefunden werden
"""
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Importiere die Funktionen aus apply_pagebreaks_from_pdf
sys.path.insert(0, str(Path(__file__).parent))
from apply_pagebreaks_from_pdf import (
    extract_pdf_pages,
    find_pdf_for_ga,
    load_books_for_ga,
    normalize_for_comparison,
    find_pagebreak_position,
    remove_existing_markers
)

ga_number = sys.argv[1] if len(sys.argv) > 1 else "GA003"
target_pages = [int(p) for p in sys.argv[2].split(",")] if len(sys.argv) > 2 else [10, 11, 12, 13, 14]

print(f"=== Debug: Seitenmarker-Matching für {ga_number} ===\n")
print(f"Ziel-Seiten: {target_pages}\n")

# PDF finden
pdf_path = find_pdf_for_ga(ga_number)
if not pdf_path:
    print(f"FEHLER: Keine PDF gefunden für {ga_number}")
    sys.exit(1)

print(f"PDF: {pdf_path.name}\n")

# PDF-Seiten extrahieren
print("Extrahiere PDF-Seiten...")
pdf_pages = extract_pdf_pages(pdf_path)
print(f"Gefunden: {len(pdf_pages)} Seiten mit Seitenzahlen\n")

# Buch/Vorträge laden
book_source_file, book, _ = load_books_for_ga(ga_number)
if not book:
    print(f"FEHLER: Kein Buch gefunden für {ga_number}")
    sys.exit(1)

print(f"Buch geladen: {book.get('title', '')[:50]}\n")

# Baue Gesamttext
paragraphs = book.get("paragraphs", [])
full_text = ""
for para in paragraphs:
    content = para.get("content") or para.get("text") or ""
    full_text += content + "\n"

full_text_clean = remove_existing_markers(full_text)
print(f"Gesamttext: {len(full_text_clean)} Zeichen\n")

# Prüfe jede Ziel-Seite
for target_page in target_pages:
    print(f"{'='*60}")
    print(f"Seite {target_page}")
    print(f"{'='*60}")
    
    # Finde diese Seite in pdf_pages
    page_info = None
    for pdf_idx, page_num, prev_end, this_start, this_start_words in pdf_pages:
        if page_num == target_page:
            page_info = (pdf_idx, page_num, prev_end, this_start, this_start_words)
            break
    
    if not page_info:
        print(f"  ✗ Seite {target_page} nicht in PDF gefunden!")
        continue
    
    pdf_idx, page_num, prev_end, this_start, this_start_words = page_info
    
    print(f"  PDF-Index: {pdf_idx}")
    print(f"  prev_end (letzte 100 Zeichen): {prev_end[-100:] if len(prev_end) > 100 else prev_end}")
    print(f"  this_start (erste 100 Zeichen): {this_start[:100] if len(this_start) > 100 else this_start}")
    print(f"  this_start_words: {this_start_words}")
    print()
    
    # Normalisiere für Vergleich
    this_start_norm = normalize_for_comparison(this_start)
    this_start_words_norm = normalize_for_comparison(this_start_words) if this_start_words else ""
    full_text_norm = normalize_for_comparison(full_text_clean)
    
    print(f"  Normalisierte Längen:")
    print(f"    this_start: {len(this_start_norm)} Zeichen")
    print(f"    this_start_words: {len(this_start_words_norm)} Zeichen")
    print()
    
    # Versuche verschiedene Suchstrategien
    print(f"  Suche im Text...")
    
    # Strategie 1: this_start_words
    if this_start_words_norm:
        found = False
        for length in [120, 100, 80, 60, 50, 40, 30, 25, 20, 15]:
            if len(this_start_words_norm) < length:
                continue
            snippet = this_start_words_norm[:length]
            pos = full_text_norm.find(snippet)
            if pos != -1:
                print(f"    ✓ Gefunden mit this_start_words (Länge {length}) bei Position {pos}")
                found = True
                break
        if not found:
            print(f"    ✗ this_start_words nicht gefunden")
            print(f"      Gesucht: {this_start_words_norm[:50]}...")
    
    # Strategie 2: this_start
    found = False
    for length in [60, 50, 40, 30, 20]:
        if len(this_start_norm) < length:
            continue
        snippet = this_start_norm[:length]
        pos = full_text_norm.find(snippet)
        if pos != -1:
            print(f"    ✓ Gefunden mit this_start (Länge {length}) bei Position {pos}")
            found = True
            break
    if not found:
        print(f"    ✗ this_start nicht gefunden")
        print(f"      Gesucht: {this_start_norm[:50]}...")
    
    # Zeige Kontext um die erwartete Position
    # Schätze Position basierend auf Seitenzahl
    if target_page > 10:
        estimated_pos = int((target_page - 10) * len(full_text_clean) / 10)
        print(f"\n  Erwartete Position (geschätzt): ~{estimated_pos}")
        print(f"  Kontext dort:")
        start = max(0, estimated_pos - 100)
        end = min(len(full_text_clean), estimated_pos + 100)
        context = full_text_clean[start:end]
        print(f"    ...{context}...")
    
    print()

