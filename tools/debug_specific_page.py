#!/usr/bin/env python3
"""
Debug-Script für eine spezifische Seite
Zeigt warum eine Seite an der falschen Position gefunden wird
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
target_page = int(sys.argv[2]) if len(sys.argv) > 2 else 28

print(f"=== Debug: Seite {target_page} für {ga_number} ===\n")

# PDF finden
pdf_path = find_pdf_for_ga(ga_number)
if not pdf_path:
    print(f"FEHLER: Keine PDF gefunden für {ga_number}")
    sys.exit(1)

print(f"PDF: {pdf_path.name}\n")

# PDF-Seiten extrahieren
print("Extrahiere PDF-Seiten...")
pdf_pages = extract_pdf_pages(pdf_path)

# Finde Ziel-Seite
page_info = None
for pdf_idx, page_num, prev_end, this_start, this_start_words in pdf_pages:
    if page_num == target_page:
        page_info = (pdf_idx, page_num, prev_end, this_start, this_start_words)
        break

if not page_info:
    print(f"✗ Seite {target_page} nicht in PDF gefunden!")
    sys.exit(1)

pdf_idx, page_num, prev_end, this_start, this_start_words = page_info

print(f"Seite {target_page} gefunden (PDF-Index: {pdf_idx})\n")
print(f"prev_end (letzte 200 Zeichen):")
print(f"  {prev_end[-200:] if len(prev_end) > 200 else prev_end}\n")
print(f"this_start (erste 200 Zeichen):")
print(f"  {this_start[:200] if len(this_start) > 200 else this_start}\n")
print(f"this_start_words:")
print(f"  {this_start_words}\n")

# Buch laden
book_source_file, book, _ = load_books_for_ga(ga_number)
if not book:
    print(f"FEHLER: Kein Buch gefunden für {ga_number}")
    sys.exit(1)

# Baue Gesamttext
paragraphs = book.get("paragraphs", [])
full_text = ""
for para in paragraphs:
    content = para.get("content") or para.get("text") or ""
    full_text += content + "\n"

full_text_clean = remove_existing_markers(full_text)
print(f"Gesamttext: {len(full_text_clean)} Zeichen\n")

# Normalisiere
this_start_norm = normalize_for_comparison(this_start)
this_start_words_norm = normalize_for_comparison(this_start_words) if this_start_words else ""
full_text_norm = normalize_for_comparison(full_text_clean)

print(f"Normalisierte Längen:")
print(f"  this_start: {len(this_start_norm)} Zeichen")
print(f"  this_start_words: {len(this_start_words_norm)} Zeichen")
print(f"  full_text: {len(full_text_norm)} Zeichen\n")

# Suche alle Vorkommen
print(f"Suche nach Vorkommen von this_start im Text...\n")

# Suche mit this_start_words
if this_start_words_norm:
    print(f"1. Suche mit this_start_words:")
    for length in [120, 100, 80, 60, 50, 40, 30, 25, 20, 15]:
        if len(this_start_words_norm) < length:
            continue
        snippet = this_start_words_norm[:length]
        pos = 0
        matches = []
        while True:
            pos = full_text_norm.find(snippet, pos)
            if pos == -1:
                break
            matches.append(pos)
            pos += 1
        
        if matches:
            print(f"   Länge {length}: {len(matches)} Vorkommen bei Positionen: {matches[:5]}")
            for match_pos in matches[:3]:
                start = max(0, match_pos - 50)
                end = min(len(full_text_clean), match_pos + 150)
                context = full_text_clean[start:end]
                print(f"      Position {match_pos}: ...{context}...")
            if len(matches) > 3:
                print(f"      ... und {len(matches) - 3} weitere")
            print()

# Suche mit this_start
print(f"2. Suche mit this_start:")
for length in [60, 50, 40, 30, 20]:
    if len(this_start_norm) < length:
        continue
    snippet = this_start_norm[:length]
    pos = 0
    matches = []
    while True:
        pos = full_text_norm.find(snippet, pos)
        if pos == -1:
            break
        matches.append(pos)
        pos += 1
    
    if matches:
        print(f"   Länge {length}: {len(matches)} Vorkommen bei Positionen: {matches[:5]}")
        for match_pos in matches[:3]:
            start = max(0, match_pos - 50)
            end = min(len(full_text_clean), match_pos + 150)
            context = full_text_clean[start:end]
            print(f"      Position {match_pos}: ...{context}...")
        if len(matches) > 3:
            print(f"      ... und {len(matches) - 3} weitere")
        print()

# Zeige was bei Position 20541 wirklich steht
print(f"3. Was steht bei Position 20541 (gefundenes Match)?")
start = max(0, 20541 - 100)
end = min(len(full_text_clean), 20541 + 200)
context = full_text_clean[start:end]
print(f"   ...{context}...\n")

# Suche nach dem spezifischen Text aus dem PDF (wie er wirklich im PDF steht)
search_text_pdf = "alter krankten, einzig und allein darauf zurückzuführen"
search_norm_pdf = normalize_for_comparison(search_text_pdf)
print(f"4. Suche nach PDF-Text: '{search_text_pdf}'")
matches_pdf = []
pos = 0
while True:
    pos = full_text_norm.find(search_norm_pdf, pos)
    if pos == -1:
        break
    matches_pdf.append(pos)
    pos += 1

if matches_pdf:
    print(f"   Gefunden bei Positionen: {matches_pdf}")
    for match_pos in matches_pdf:
        start = max(0, match_pos - 100)
        end = min(len(full_text_clean), match_pos + len(search_text_pdf) + 100)
        context = full_text_clean[start:end]
        print(f"      Position {match_pos}: ...{context}...")
else:
    print(f"   ✗ Nicht gefunden!")
    print(f"   Gesucht (normalisiert): {search_norm_pdf[:100]}")

# Suche nach dem Text wie der Benutzer ihn sucht
search_text_user = "alter kranken, einzig und allein darauf zurückzuführen"
search_norm_user = normalize_for_comparison(search_text_user)
print(f"\n5. Suche nach Benutzer-Text: '{search_text_user}'")
matches_user = []
pos = 0
while True:
    pos = full_text_norm.find(search_norm_user, pos)
    if pos == -1:
        break
    matches_user.append(pos)
    pos += 1

if matches_user:
    print(f"   Gefunden bei Positionen: {matches_user}")
    for match_pos in matches_user:
        start = max(0, match_pos - 100)
        end = min(len(full_text_clean), match_pos + len(search_text_user) + 100)
        context = full_text_clean[start:end]
        print(f"      Position {match_pos}: ...{context}...")
else:
    print(f"   ✗ Nicht gefunden!")

print()

