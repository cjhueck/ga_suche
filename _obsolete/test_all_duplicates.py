#!/usr/bin/env python3
"""Test: Duplikate in ALLEN GA-JSONs finden (Bücher + Vorträge)"""

import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche')

print("=" * 70)
print("DUPLIKAT-ANALYSE FÜR ALLE GA-BÄNDE")
print("=" * 70)

# === BÜCHER ===
print("\n### BÜCHER (steiner-books-*.json) ###\n")

books_by_id = defaultdict(list)  # ID -> [(Datei, Objekt), ...]

for jf in sorted(SCRIPT_DIR.glob('steiner-books-*.json')):
    try:
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for book in data.get('books', []):
            book_id = book.get('ID') or book.get('gaNumber') or 'UNKNOWN'
            books_by_id[book_id].append((jf.name, book.get('title', '')[:50]))
    except Exception as e:
        print(f"  Fehler bei {jf.name}: {e}")

book_duplicates = {k: v for k, v in books_by_id.items() if len(v) > 1}
print(f"Gesamt: {sum(len(v) for v in books_by_id.values())} Einträge")
print(f"Eindeutig: {len(books_by_id)} verschiedene IDs")
print(f"Duplikate: {len(book_duplicates)} IDs kommen mehrfach vor")

if book_duplicates:
    print("\nBeispiele:")
    for book_id, occurrences in list(book_duplicates.items())[:5]:
        files = [occ[0] for occ in occurrences]
        print(f"  {book_id}: {len(occurrences)}x in {files}")

# === VORTRÄGE ===
print("\n### VORTRÄGE (steiner-full-lectures-*.json) ###\n")

lectures_by_id = defaultdict(list)

for jf in sorted(SCRIPT_DIR.glob('steiner-full-lectures-*.json')):
    try:
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for lec in data.get('lectures', []):
            lec_id = lec.get('ID') or 'UNKNOWN'
            lectures_by_id[lec_id].append((jf.name, lec.get('title', '')[:50]))
    except Exception as e:
        print(f"  Fehler bei {jf.name}: {e}")

lecture_duplicates = {k: v for k, v in lectures_by_id.items() if len(v) > 1}
print(f"Gesamt: {sum(len(v) for v in lectures_by_id.values())} Einträge")
print(f"Eindeutig: {len(lectures_by_id)} verschiedene IDs")
print(f"Duplikate: {len(lecture_duplicates)} IDs kommen mehrfach vor")

if lecture_duplicates:
    print("\nBetroffene GA-Nummern:")
    affected_gas = set()
    for lec_id in lecture_duplicates.keys():
        ga = lec_id.split('/')[0] if '/' in lec_id else lec_id
        affected_gas.add(ga)
    print(f"  {sorted(affected_gas)}")

# === ZUSAMMENFASSUNG ===
print("\n" + "=" * 70)
print("ZUSAMMENFASSUNG")
print("=" * 70)
print(f"\nBücher mit Duplikaten: {len(book_duplicates)}")
print(f"Vorträge mit Duplikaten: {len(lecture_duplicates)}")

# === DATEI-ÜBERLAPPUNGEN ANALYSIEREN ===
print("\n### DATEI-ÜBERLAPPUNGEN ###\n")

# Welche Dateien enthalten welche GA-Nummern?
file_to_gas = defaultdict(set)

for jf in sorted(SCRIPT_DIR.glob('steiner-full-lectures-*.json')):
    try:
        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for lec in data.get('lectures', []):
            ga = lec.get('gaNumber', '').upper()
            if ga:
                file_to_gas[jf.name].add(ga)
    except:
        pass

# Finde Überlappungen
print("Dateien und ihre GA-Bereiche:")
for fname, gas in sorted(file_to_gas.items()):
    gas_sorted = sorted(gas, key=lambda x: int(x.replace('GA', '').replace('A', '').replace('B', '').replace('C', '') or 0))
    if len(gas_sorted) > 10:
        print(f"  {fname}: {gas_sorted[0]} - {gas_sorted[-1]} ({len(gas_sorted)} GAs)")
    else:
        print(f"  {fname}: {gas_sorted}")

