#!/usr/bin/env python3
"""
Fügt Seitenmarker aus MsN in MsA ein.
MsA behält Überschriften und Block-IDs.
Nur Seitenmarker werden aus MsN übernommen.
"""

import re
from pathlib import Path
from difflib import SequenceMatcher

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

# Extrahiere Seitenmarker-Positionen aus MsN
# Format: "RUDOLF STEINER VERLAG Seite X ---" oder "Seite X"
# "Seite X" markiert das ENDE von Seite X, danach kommt Seite X+1

def normalize(text):
    """Normalisiere für Vergleich."""
    text = text.lower()
    text = re.sub(r'[^a-zäöüß0-9]', '', text)
    return text

# Finde alle Seitenumbrüche in MsN
pagebreaks = []

# Pattern 1: RUDOLF STEINER VERLAG ... Seite X ---
pattern1 = re.compile(
    r'RUDOLF\s+STEINER\s*\n?\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---',
    re.IGNORECASE
)

# Pattern 2: Nur "Seite X" am Zeilenende
pattern2 = re.compile(r'\nSeite\s+(\d+)\s*\n', re.IGNORECASE)

for match in pattern1.finditer(msn):
    page_num = int(match.group(1))
    pos = match.start()
    # Text vor dem Marker (für Matching)
    left_text = msn[max(0, pos-100):pos]
    # Text nach dem Marker
    right_text = msn[match.end():match.end()+100]
    pagebreaks.append({
        'page': page_num,
        'left': normalize(left_text),
        'right': normalize(right_text),
        'left_raw': left_text[-50:],
        'right_raw': right_text[:50]
    })

print(f"\nGefunden: {len(pagebreaks)} Seitenumbrüche")
if pagebreaks:
    pages = sorted(set(pb['page'] for pb in pagebreaks))
    print(f"Seiten: {min(pages)} - {max(pages)}")

# Füge Marker in MsA ein
def find_best_position(msa_text, left_norm, right_norm, start_search=0):
    """Finde beste Position für Marker basierend auf Kontext."""
    best_pos = -1
    best_score = 0
    
    # Suche in Fenstern
    window_size = 200
    for i in range(start_search, len(msa_text) - 50, 50):
        msa_left = normalize(msa_text[max(0, i-100):i])
        msa_right = normalize(msa_text[i:i+100])
        
        # Vergleiche
        left_score = SequenceMatcher(None, left_norm[-50:], msa_left[-50:]).ratio()
        right_score = SequenceMatcher(None, right_norm[:50], msa_right[:50]).ratio()
        
        score = (left_score + right_score) / 2
        if score > best_score and score > 0.5:
            best_score = score
            best_pos = i
    
    return best_pos, best_score

# Sortiere nach Seitenzahl
pagebreaks_sorted = sorted(pagebreaks, key=lambda x: x['page'])

# Füge Marker ein (von hinten nach vorne um Positionen nicht zu verschieben)
msa_with_markers = msa
insertions = []
last_pos = 0

print("\nSuche Positionen...")
for pb in pagebreaks_sorted:
    page = pb['page']
    next_page = page + 1  # Marker zeigt nächste Seite an
    
    pos, score = find_best_position(msa_with_markers, pb['left'], pb['right'], last_pos)
    
    if pos > 0:
        insertions.append((pos, next_page, score))
        last_pos = pos
        if len(insertions) <= 5 or len(insertions) % 20 == 0:
            print(f"  |{next_page}| bei Position {pos} (Score: {score:.2f})")

print(f"\n{len(insertions)} Positionen gefunden")

# Füge Marker ein (von hinten nach vorne)
for pos, page, score in sorted(insertions, reverse=True):
    marker = f'|{page}|'
    # Prüfe ob Marker schon existiert
    if marker not in msa_with_markers[pos-20:pos+20]:
        # Füge Marker mit Leerzeichen ein
        msa_with_markers = msa_with_markers[:pos] + f' {marker} ' + msa_with_markers[pos:]

# Bereinige doppelte Leerzeichen
msa_with_markers = re.sub(r' {2,}', ' ', msa_with_markers)

# Zähle Marker
markers = re.findall(r'\|(\d+)\|', msa_with_markers)
print(f"\nMarker in MsAN: {len(markers)}")

# Prüfe Block-IDs
msa_ids = len(re.findall(r'\^[a-z0-9]+', msa))
msan_ids = len(re.findall(r'\^[a-z0-9]+', msa_with_markers))
print(f"Block-IDs: MsA={msa_ids}, MsAN={msan_ids}")

# Prüfe Überschriften
msa_headings = len(re.findall(r'^#+\s', msa, re.MULTILINE))
msan_headings = len(re.findall(r'^#+\s', msa_with_markers, re.MULTILINE))
print(f"Überschriften: MsA={msa_headings}, MsAN={msan_headings}")

# Speichere
output_path = folder / 'GA002_msan.md'
output_path.write_text(msa_with_markers, encoding='utf-8')
print(f"\nGespeichert: {output_path.name}")

# Zeige Beispiele
print("\nBeispiele:")
for m in markers[:3]:
    pattern = rf'.{{30}}\|{m}\|.{{30}}'
    match = re.search(pattern, msa_with_markers)
    if match:
        print(f"  |{m}|: ...{match.group()}...")

