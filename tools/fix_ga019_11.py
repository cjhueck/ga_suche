"""
Kürzt GA019/11_new.md auf die Länge von MsA.
"""
import re
from pathlib import Path

folder = Path('Steiner_GA')
ga_folder = [d for d in folder.iterdir() if 'GA019' in d.name][0]

# Finde beide Dateien
msa_file = None
msan_file = None
for f in ga_folder.iterdir():
    if '(11.)' in f.name and f.suffix == '.md':
        if '_new' in f.name:
            msan_file = f
        elif '_backup' not in f.name and '_converted' not in f.name:
            msa_file = f

print(f'MsA: {msa_file.name if msa_file else "nicht gefunden"}')
print(f'MsAN: {msan_file.name if msan_file else "nicht gefunden"}')

if not msa_file or not msan_file:
    print("Dateien nicht gefunden!")
    exit(1)

# Lade Texte
msa_text = msa_file.read_text(encoding='utf-8')
msan_text = msan_file.read_text(encoding='utf-8')

# Zähle Wörter in MsA (ohne IDs, Marker, Überschriften)
def count_content_words(text):
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\|\d+\|', '', text)
    text = re.sub(r'^#+\s.*$', '', text, flags=re.MULTILINE)
    words = re.findall(r'\b\w+\b', text)
    return len(words)

msa_words = count_content_words(msa_text)
msan_words = count_content_words(msan_text)

print(f'\nMsA: {msa_words} Wörter')
print(f'MsAN: {msan_words} Wörter')
print(f'Differenz: {msan_words - msa_words} Wörter')

# Finde Schnittpunkt - wo endet MsA?
# Zeige Ende von MsA
msa_clean = re.sub(r'\^[a-z0-9]+', '', msa_text)
print('\n=== Ende MsA (letzte 300 Zeichen) ===')
print(msa_clean[-300:])

# Finde diesen Text in MsAN
# Suche nach den letzten markanten Wörtern
last_words = re.findall(r'\b\w{5,}\b', msa_clean[-500:])[-10:]
print(f'\nLetzte Wörter in MsA: {last_words}')

# Suche in MsAN nach dem letzten gemeinsamen Absatz
msan_clean = re.sub(r'\^[a-z0-9]+', '', msan_text)
msan_clean = re.sub(r'\|\d+\|', ' ', msan_clean)

# Finde Position des letzten gemeinsamen Satzes
search_text = "darauf zu sehen"  # Typischer Satz am Ende
pos = msan_text.lower().rfind(search_text.lower())
if pos > 0:
    print(f'\nGefunden bei Position: {pos}')
    print(f'Kontext: ...{msan_text[pos-50:pos+100]}...')

# Kürze MsAN auf MsA-Länge
# Berechne Ziel-Zeichenlänge basierend auf MsA
target_chars = len(msa_text)
print(f'\nZiel-Länge: {target_chars} Zeichen')
print(f'Aktuelle Länge: {len(msan_text)} Zeichen')

# Finde einen guten Schnittpunkt (Ende eines Absatzes)
cut_pos = target_chars
# Suche nächsten Absatzumbruch
next_para = msan_text.find('\n\n', cut_pos)
if next_para > 0 and next_para < cut_pos + 500:
    cut_pos = next_para

# Zeige was abgeschnitten wird
print(f'\n=== Text der abgeschnitten wird (ab Position {cut_pos}) ===')
print(msan_text[cut_pos:cut_pos+500])

# Schneide ab
new_text = msan_text[:cut_pos].strip()

# Prüfe neue Wortanzahl
new_words = count_content_words(new_text)
print(f'\nNeue Wortanzahl: {new_words} (Ziel: {msa_words})')

# Speichere
if abs(new_words - msa_words) < msa_words * 0.05:  # Innerhalb 5%
    msan_file.write_text(new_text, encoding='utf-8')
    print(f'\nGespeichert! Differenz: {new_words - msa_words} Wörter')
else:
    print(f'\nWARNUNG: Immer noch zu große Differenz ({new_words - msa_words} Wörter)')
    print('Manuelle Anpassung erforderlich.')

