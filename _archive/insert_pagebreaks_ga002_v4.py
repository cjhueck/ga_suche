#!/usr/bin/env python3
"""
V4-Verfahren: 200 Zeichen vor und nach dem Seitenumbruch in MsN,
dann anhand dieser Blöcke in MsA einfügen.

Seitenumbruch in MsN:
    ...Text vor...
    RUDOLF STEINER
    VERLAG
    Seite X
    ---
    ...Text nach...
"""

import re
from pathlib import Path
from difflib import SequenceMatcher

folder = Path('Steiner_GA/GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung')

msa_path = folder / 'GA002_msa.md'
msn_path = folder / 'GA 2 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung.md'

print(f"MsA: {msa_path.name}")
print(f"MsN: {msn_path.name}")

msa = msa_path.read_text(encoding='utf-8')
msn = msn_path.read_text(encoding='utf-8')

print(f"MsA: {len(msa)} Zeichen")
print(f"MsN: {len(msn)} Zeichen")


def normalize(text):
    """Normalisiere Text für Vergleich."""
    # Entferne Zeilenumbrüche, mehrfache Leerzeichen
    text = re.sub(r'\s+', ' ', text)
    # Entferne Sonderzeichen für besseres Matching
    text = text.lower()
    return text.strip()


def find_position_in_msa(msa_text, left_context, right_context):
    """
    Finde die Position in MsA wo left_context aufhört und right_context beginnt.
    Verwendet fuzzy matching.
    """
    left_norm = normalize(left_context)
    right_norm = normalize(right_context)
    msa_norm = normalize(msa_text)
    
    best_pos = -1
    best_score = 0
    
    # Schiebe ein Fenster über MsA
    window = 100  # Vergleichsfenster
    step = 20
    
    for i in range(0, len(msa_norm) - window, step):
        # Vergleiche linken Kontext (endet bei Position i)
        msa_left = msa_norm[max(0, i-200):i]
        # Vergleiche rechten Kontext (beginnt bei Position i)
        msa_right = msa_norm[i:i+200]
        
        # Score berechnen
        left_score = SequenceMatcher(None, left_norm[-100:], msa_left[-100:]).ratio()
        right_score = SequenceMatcher(None, right_norm[:100], msa_right[:100]).ratio()
        
        combined_score = (left_score + right_score) / 2
        
        if combined_score > best_score:
            best_score = combined_score
            best_pos = i
    
    return best_pos, best_score


def map_normalized_to_original(msa_original, norm_pos):
    """Mappe Position im normalisierten Text auf Original."""
    # Zähle Zeichen im Original bis wir norm_pos erreichen
    orig_pos = 0
    norm_count = 0
    
    msa_norm = normalize(msa_original)
    
    # Einfachere Methode: Finde einen markanten Text um norm_pos herum
    # und suche ihn im Original
    context = msa_norm[max(0, norm_pos-20):norm_pos+20]
    
    # Suche ähnlichen Text im Original
    for i in range(len(msa_original) - 40):
        orig_context = normalize(msa_original[i:i+40])
        if SequenceMatcher(None, context, orig_context).ratio() > 0.9:
            return i + 20  # Mitte des Kontexts
    
    return -1


# Extrahiere Seitenumbrüche aus MsN
# Pattern: alles vor "RUDOLF STEINER\nVERLAG\nSeite X\n---" und alles danach
pagebreak_pattern = re.compile(
    r'RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+(\d+)\s*\n\s*---',
    re.IGNORECASE
)

pagebreaks = []
for match in pagebreak_pattern.finditer(msn):
    page_num = int(match.group(1))
    start = match.start()
    end = match.end()
    
    # 200 Zeichen VOR dem Seitenumbruch
    left_start = max(0, start - 200)
    left_context = msn[left_start:start]
    
    # 200 Zeichen NACH dem Seitenumbruch
    right_context = msn[end:end + 200]
    
    # Bereinige: Entferne vorherige RUDOLF STEINER VERLAG Blöcke aus dem Kontext
    left_context = re.sub(r'RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+\d+\s*\n\s*---', '', left_context, flags=re.IGNORECASE)
    right_context = re.sub(r'RUDOLF\s+STEINER\s*\n\s*VERLAG\s*\n\s*Seite\s+\d+\s*\n\s*---', '', right_context, flags=re.IGNORECASE)
    
    pagebreaks.append({
        'page': page_num,
        'next_page': page_num + 1,
        'left': left_context.strip(),
        'right': right_context.strip()
    })

print(f"\nGefunden: {len(pagebreaks)} Seitenumbrüche in MsN")

# Zeige Beispiel
print("\nBeispiel (Seite 7):")
for pb in pagebreaks:
    if pb['page'] == 7:
        print(f"  LEFT (letzte 80): ...{pb['left'][-80:]}")
        print(f"  RIGHT (erste 80): {pb['right'][:80]}...")
        break

# Finde Positionen in MsA
print("\nSuche Positionen in MsA...")

msa_norm = normalize(msa)
insertions = []
not_found = []

for pb in pagebreaks:
    page = pb['page']
    next_page = pb['next_page']
    left = pb['left']
    right = pb['right']
    
    # Suche Position
    pos, score = find_position_in_msa(msa, left, right)
    
    if pos > 0 and score > 0.5:
        insertions.append({
            'norm_pos': pos,
            'page': next_page,
            'score': score,
            'left': left[-50:],
            'right': right[:50]
        })
    else:
        not_found.append(pb)

print(f"Gefunden: {len(insertions)}")
print(f"Nicht gefunden: {len(not_found)}")

# Zeige beste und schlechteste Matches
insertions.sort(key=lambda x: x['score'], reverse=True)
print(f"\nBeste Matches:")
for ins in insertions[:3]:
    print(f"  |{ins['page']}| Score={ins['score']:.2f}")

if insertions:
    print(f"\nSchlechteste Matches:")
    for ins in insertions[-3:]:
        print(f"  |{ins['page']}| Score={ins['score']:.2f}")

# Mappe auf Original-Positionen und füge Marker ein
print("\nMappe auf Original-Positionen...")

original_insertions = []
for ins in insertions:
    # Finde den Kontext im normalisierten MsA
    norm_pos = ins['norm_pos']
    context = msa_norm[max(0, norm_pos-30):norm_pos+30]
    
    # Suche diesen Kontext im Original
    for i in range(len(msa) - 60):
        orig_context = normalize(msa[i:i+60])
        if SequenceMatcher(None, context, orig_context).ratio() > 0.85:
            # Feinabstimmung: Finde die exakte Position
            orig_pos = i + 30
            original_insertions.append((orig_pos, ins['page']))
            break

print(f"Original-Positionen gefunden: {len(original_insertions)}")

# Sortiere nach Position (absteigend) und füge ein
original_insertions.sort(key=lambda x: x[0], reverse=True)

msa_result = msa
for pos, page in original_insertions:
    marker = f' |{page}| '
    # Prüfe ob bereits ein Marker in der Nähe ist
    nearby = msa_result[max(0, pos-10):pos+10]
    if f'|{page}|' not in nearby:
        msa_result = msa_result[:pos] + marker + msa_result[pos:]

# Bereinige doppelte Leerzeichen
msa_result = re.sub(r' {2,}', ' ', msa_result)

# Zähle Ergebnis
markers = re.findall(r'\|(\d+)\|', msa_result)
block_ids = len(re.findall(r'\^[a-z0-9]+', msa_result))
headings = len(re.findall(r'^#+\s', msa_result, re.MULTILINE))

print(f"\n=== Ergebnis ===")
print(f"Seitenmarker: {len(markers)}")
print(f"Block-IDs: {block_ids}")
print(f"Überschriften: {headings}")

if markers:
    pages = sorted(set(int(m) for m in markers))
    print(f"Seiten: {min(pages)} - {max(pages)}")

# Speichere
output_path = folder / 'GA002_msan.md'
output_path.write_text(msa_result, encoding='utf-8')
print(f"\nGespeichert: {output_path.name}")

# Verifikation
print("\n=== Verifikation ===")
# Seite 8: zwischen "Erfahrung" und "und Denken"
match = re.search(r'.{20}Erfahrung.{0,20}und Denken.{20}', msa_result)
if match:
    print(f"Seite 8: {match.group()}")

# Seite 9
match = re.search(r'\|9\|.{50}', msa_result)
if match:
    print(f"Seite 9: {match.group()}")

