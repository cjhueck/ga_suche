import zipfile
import re
from collections import Counter, defaultdict

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        content = f.read().decode('utf-8')

# Alle XE-Felder extrahieren
instr_pattern = re.compile(r'<w:instrText[^>]*>(.*?)</w:instrText>', re.DOTALL)
all_instr = instr_pattern.findall(content)
xe_entries = [m.strip() for m in all_instr if 'XE' in m]

# Einzigartige Eintraege zaehlen
xe_clean = []
for xe in xe_entries:
    match = re.search(r'XE\s+"([^"]+)"', xe)
    if match:
        xe_clean.append(match.group(1))

counter = Counter(xe_clean)
unique_entries = sorted(counter.keys())

print(f"=== INDEXANALYSE ===")
print(f"Gesamt XE-Eintraege: {len(xe_clean)}")
print(f"Einzigartige Eintraege: {len(unique_entries)}")
print()

# Gruppiere nach Haupteintrag (vor dem Doppelpunkt)
by_main = defaultdict(list)
for entry in unique_entries:
    if ':' in entry:
        main, sub = entry.split(':', 1)
        by_main[main.strip()].append(sub.strip())
    else:
        by_main[entry].append('')

print("=== ALLE EINTRAEGE (alphabetisch nach Hauptstichwort) ===")
for main in sorted(by_main.keys(), key=lambda x: x.lower()):
    subs = by_main[main]
    if subs == ['']:
        print(f"  {main} ({counter[main]}x)")
    else:
        print(f"  {main}:")
        for sub in sorted(subs):
            key = f"{main}:{sub}"
            print(f"    - {sub} ({counter[key]}x)")

# Suche nach 'epigenesis' im Text (nicht als XE, sondern im Fliesstext)
print()
print("=== EPIGENESIS IM TEXT ===")
# Paragraphen-Text extrahieren
text_content = re.sub(r'<[^>]+>', ' ', content)
text_content = re.sub(r'\s+', ' ', text_content)
# Finde Epigenesis-Vorkommen
epi_positions = [m.start() for m in re.finditer(r'[Ee]pigenesis|[Ee]pigenese', text_content)]
print(f"'Epigenesis/Epigenese' im Fliesstext: {len(epi_positions)}x")
for pos in epi_positions[:10]:
    snippet = text_content[max(0,pos-80):pos+80].strip()
    print(f"  ...{snippet}...")
    print()

# Gibt es bereits XE-Eintraege fuer Epigenesis?
epi_xe = [e for e in xe_clean if 'epigenesis' in e.lower() or 'epigenese' in e.lower()]
print(f"Epigenesis als XE-Eintrag: {len(epi_xe)}x")
for e in epi_xe:
    print(f"  {e}")
