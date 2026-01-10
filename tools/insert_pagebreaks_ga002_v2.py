#!/usr/bin/env python3
"""
Fügt Seitenmarker aus MsN EXAKT in MsA ein.
Verwendet den Text VOR und NACH dem Seitenumbruch für präzises Matching.
"""

import re
from pathlib import Path

folder = Path('Steiner_GA/GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung')

msa_path = folder / 'GA002_msa.md'
msn_path = folder / 'GA 2 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung.md'

print(f"MsA: {msa_path.name}")
print(f"MsN: {msn_path.name}")

# Lade Dateien
msa = msa_path.read_text(encoding='utf-8')
msn = msn_path.read_text(encoding='utf-8')

print(f"\nMsA: {len(msa)} Zeichen")
print(f"MsN: {len(msn)} Zeichen")


def normalize_for_search(text):
    """Normalisiere Text für Suche (behalte Wörter)."""
    # Entferne Zeilenumbrüche und mehrfache Leerzeichen
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_pagebreaks(msn_content):
    """
    Extrahiere Seitenumbrüche aus MsN.
    
    Format in MsN:
        ...Text vor Umbruch
        RUDOLF STEINER
        VERLAG
        Seite X
        ---
        Text nach Umbruch...
    
    "Seite X" = Ende von Seite X, danach kommt Seite X+1
    """
    pagebreaks = []
    
    # Pattern: Text vor RUDOLF STEINER VERLAG Seite X --- Text nach
    pattern = re.compile(
        r'(.{30,100}?)\s*\n\s*RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+(\d+)\s*\n\s*---\s*\n(.{30,100})',
        re.IGNORECASE | re.DOTALL
    )
    
    for match in pattern.finditer(msn_content):
        left_text = match.group(1)
        page_num = int(match.group(2))
        right_text = match.group(3)
        
        # Bereinige
        left_text = normalize_for_search(left_text)
        right_text = normalize_for_search(right_text)
        
        # Nimm nur die letzten/ersten Wörter
        left_words = left_text.split()[-5:]  # Letzte 5 Wörter
        right_words = right_text.split()[:5]  # Erste 5 Wörter
        
        pagebreaks.append({
            'page': page_num,
            'next_page': page_num + 1,
            'left': ' '.join(left_words),
            'right': ' '.join(right_words),
            'left_full': left_text,
            'right_full': right_text
        })
    
    return pagebreaks


def find_exact_position(msa_text, left_words, right_words):
    """
    Finde exakte Position für Marker basierend auf umgebenden Wörtern.
    """
    # Normalisiere MsA für Suche
    msa_norm = normalize_for_search(msa_text)
    
    # Suche nach: left_words + right_words (ohne Marker dazwischen)
    # Der Marker kommt zwischen left und right
    
    # Erstelle Suchpattern
    left_pattern = re.escape(left_words)
    right_pattern = re.escape(right_words)
    
    # Suche nach left...right mit beliebigem Zeichen dazwischen
    combined_pattern = left_pattern + r'\s*' + right_pattern
    
    match = re.search(combined_pattern, msa_norm, re.IGNORECASE)
    if match:
        # Position ist nach left_words
        left_end = match.start() + len(left_words)
        return left_end
    
    # Fallback: Suche nur nach left_words
    match = re.search(left_pattern, msa_norm, re.IGNORECASE)
    if match:
        return match.end()
    
    return -1


# Extrahiere Seitenumbrüche
pagebreaks = extract_pagebreaks(msn)
print(f"\nGefunden: {len(pagebreaks)} Seitenumbrüche")

if pagebreaks:
    print(f"\nBeispiel:")
    pb = pagebreaks[0]
    print(f"  Seite {pb['page']} -> {pb['next_page']}")
    print(f"  Links: '{pb['left']}'")
    print(f"  Rechts: '{pb['right']}'")

# Arbeite mit normalisiertem MsA
msa_norm = normalize_for_search(msa)

# Finde Positionen und füge Marker ein
insertions = []
not_found = []

for pb in pagebreaks:
    left = pb['left']
    right = pb['right']
    next_page = pb['next_page']
    
    # Suche nach der Kombination left + right
    # Der Marker kommt dazwischen
    pattern = re.escape(left) + r'(\s*)' + re.escape(right)
    match = re.search(pattern, msa_norm, re.IGNORECASE)
    
    if match:
        # Position ist am Ende von left
        pos = match.start() + len(left)
        insertions.append((pos, next_page, left, right))
    else:
        # Versuche mit weniger Wörtern
        left_short = ' '.join(left.split()[-3:])
        right_short = ' '.join(right.split()[:3])
        pattern = re.escape(left_short) + r'(\s*)' + re.escape(right_short)
        match = re.search(pattern, msa_norm, re.IGNORECASE)
        
        if match:
            pos = match.start() + len(left_short)
            insertions.append((pos, next_page, left_short, right_short))
        else:
            not_found.append(pb)

print(f"\nGefunden: {len(insertions)} Positionen")
print(f"Nicht gefunden: {len(not_found)}")

if not_found and len(not_found) <= 10:
    print("\nNicht gefunden:")
    for pb in not_found[:5]:
        print(f"  Seite {pb['page']}: '{pb['left']}' | '{pb['right']}'")

# Sortiere nach Position (absteigend) für Einfügung
insertions.sort(key=lambda x: x[0], reverse=True)

# Füge Marker in normalisiertes MsA ein
msa_with_markers = msa_norm
for pos, page, left, right in insertions:
    marker = f' |{page}| '
    msa_with_markers = msa_with_markers[:pos] + marker + msa_with_markers[pos:]

# Bereinige doppelte Leerzeichen
msa_with_markers = re.sub(r' {2,}', ' ', msa_with_markers)

# Problem: Wir haben die Formatierung von MsA verloren (Überschriften, Absätze)
# Wir müssen die Marker stattdessen in das Original-MsA einfügen

print("\n--- Neuansatz: Marker in Original-MsA einfügen ---")

# Finde Positionen im Original-MsA
def find_in_original(msa_original, left_words, right_words):
    """Finde Position im Original-MsA (mit Formatierung)."""
    # Suche nach left_words am Ende einer Zeile/Absatzes und right_words am Anfang
    # Oder beide hintereinander
    
    # Normalisiere left/right für flexiblere Suche
    left_norm = re.sub(r'\s+', r'\\s+', re.escape(left_words))
    right_norm = re.sub(r'\s+', r'\\s+', re.escape(right_words))
    
    # Pattern: left...right mit beliebigem Whitespace dazwischen
    pattern = left_norm + r'\s*' + right_norm
    match = re.search(pattern, msa_original, re.IGNORECASE)
    
    if match:
        # Finde Ende von left_words im Match
        left_match = re.search(left_norm, match.group(), re.IGNORECASE)
        if left_match:
            return match.start() + left_match.end()
    
    return -1


# Finde alle Positionen im Original
original_insertions = []

for pb in pagebreaks:
    left = pb['left']
    right = pb['right']
    next_page = pb['next_page']
    
    pos = find_in_original(msa, left, right)
    if pos > 0:
        original_insertions.append((pos, next_page))
    else:
        # Versuche mit kürzeren Wörtern
        left_short = ' '.join(left.split()[-2:])
        right_short = ' '.join(right.split()[:2])
        pos = find_in_original(msa, left_short, right_short)
        if pos > 0:
            original_insertions.append((pos, next_page))

print(f"Positionen im Original gefunden: {len(original_insertions)}")

# Sortiere und füge ein (von hinten nach vorne)
original_insertions.sort(key=lambda x: x[0], reverse=True)

msa_final = msa
for pos, page in original_insertions:
    marker = f' |{page}| '
    msa_final = msa_final[:pos] + marker + msa_final[pos:]

# Bereinige
msa_final = re.sub(r' {2,}', ' ', msa_final)
msa_final = re.sub(r'\n ', '\n', msa_final)

# Zähle
markers = re.findall(r'\|(\d+)\|', msa_final)
block_ids = re.findall(r'\^[a-z0-9]+', msa_final)
headings = re.findall(r'^#+\s', msa_final, re.MULTILINE)

print(f"\nErgebnis:")
print(f"  Seitenmarker: {len(markers)}")
print(f"  Block-IDs: {len(block_ids)} (vorher: {len(re.findall(r'^[a-z0-9]+', msa))})")
print(f"  Überschriften: {len(headings)}")

# Speichere
output_path = folder / 'GA002_msan.md'
output_path.write_text(msa_final, encoding='utf-8')
print(f"\nGespeichert: {output_path.name}")

# Zeige Beispiele
print("\nBeispiele:")
for i, (pos, page) in enumerate(sorted(original_insertions)[:3]):
    # Zeige Kontext aus dem finalen Text
    start = max(0, pos - 30)
    end = min(len(msa_final), pos + 50)
    context = msa_final[start:end].replace('\n', ' ')
    print(f"  |{page}|: ...{context}...")

