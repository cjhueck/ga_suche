#!/usr/bin/env python3
"""
Fügt Seitenmarker aus MsN EXAKT in MsA ein.
Findet das letzte Wort VOR dem Seitenumbruch und fügt Marker danach ein.
"""

import re
from pathlib import Path

folder = Path('Steiner_GA/GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung')

msa_path = folder / 'GA002_msa.md'
msn_path = folder / 'GA 2 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung.md'

print(f"MsA: {msa_path.name}")
print(f"MsN: {msn_path.name}")

msa = msa_path.read_text(encoding='utf-8')
msn = msn_path.read_text(encoding='utf-8')

print(f"MsA: {len(msa)} Zeichen")
print(f"MsN: {len(msn)} Zeichen")

# Extrahiere alle Seitenumbrüche aus MsN
# Format: Text...RUDOLF STEINER\nVERLAG\nSeite X\n---\n...Text
pattern = re.compile(
    r'(\S+)\s*\n\s*RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+(\d+)\s*\n\s*---\s*\n\s*(\S+)',
    re.IGNORECASE
)

pagebreaks = []
for match in pattern.finditer(msn):
    last_word_before = match.group(1)  # Letztes Wort vor dem Umbruch
    page_num = int(match.group(2))
    first_word_after = match.group(3)  # Erstes Wort nach dem Umbruch
    
    pagebreaks.append({
        'page': page_num,
        'next_page': page_num + 1,
        'before': last_word_before,
        'after': first_word_after
    })

print(f"\nGefunden: {len(pagebreaks)} Seitenumbrüche")

# Zeige Beispiele
print("\nBeispiele:")
for pb in pagebreaks[:5]:
    print(f"  Seite {pb['page']}: '{pb['before']}' | '{pb['after']}'")

# Füge Marker in MsA ein
# Strategie: Suche nach "before...after" und füge Marker dazwischen

msa_result = msa
insertions = []
not_found = []

for pb in pagebreaks:
    before = pb['before']
    after = pb['after']
    next_page = pb['next_page']
    
    # Escape für Regex
    before_esc = re.escape(before)
    after_esc = re.escape(after)
    
    # Suche nach before gefolgt von after (mit Whitespace dazwischen)
    # Ignoriere bereits eingefügte Marker
    pattern = before_esc + r'(\s+)' + after_esc
    match = re.search(pattern, msa_result, re.IGNORECASE)
    
    if match:
        # Berechne Position für Marker (nach "before", vor Whitespace)
        insert_pos = match.start() + len(before)
        insertions.append((insert_pos, next_page, before, after))
    else:
        not_found.append(pb)

print(f"\nGefunden in MsA: {len(insertions)}")
print(f"Nicht gefunden: {len(not_found)}")

if not_found:
    print("\nNicht gefunden (erste 10):")
    for pb in not_found[:10]:
        print(f"  Seite {pb['page']}: '{pb['before']}' | '{pb['after']}'")

# Sortiere nach Position (absteigend) um von hinten einzufügen
insertions.sort(key=lambda x: x[0], reverse=True)

# Füge Marker ein
for pos, page, before, after in insertions:
    marker = f' |{page}|'
    msa_result = msa_result[:pos] + marker + msa_result[pos:]

# Zähle Ergebnis
markers = re.findall(r'\|(\d+)\|', msa_result)
block_ids = len(re.findall(r'\^[a-z0-9]+', msa_result))
headings = len(re.findall(r'^#+\s', msa_result, re.MULTILINE))

print(f"\nErgebnis:")
print(f"  Seitenmarker: {len(markers)}")
print(f"  Block-IDs: {block_ids} (vorher: {len(re.findall(r'^[a-z0-9]+', msa))})")
print(f"  Überschriften: {headings}")

if markers:
    pages = sorted(set(int(m) for m in markers))
    print(f"  Seiten: {min(pages)} - {max(pages)}")

# Speichere
output_path = folder / 'GA002_msan.md'
output_path.write_text(msa_result, encoding='utf-8')
print(f"\nGespeichert: {output_path.name}")

# Verifiziere mit konkretem Beispiel
print("\n=== Verifikation: Seite 8 ===")
match = re.search(r'.{30}«Erfahrung.{0,30}und Denken.{30}', msa_result)
if match:
    print(match.group())

