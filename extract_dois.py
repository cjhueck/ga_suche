import zipfile, re

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

with zipfile.ZipFile(path, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')

combined = doc + fn

# Bereinige XML-Tags fuer Textextraktion
text = re.sub(r'<[^>]+>', ' ', combined)
text = re.sub(r'\s+', ' ', text)

# Extrahiere alle DOIs (verschiedene Formate)
patterns = [
    r'https?://doi\.org/[^\s<>"\')\]]+',
    r'doi:\s*10\.\d{4,}/[^\s<>"\')\]]+',
    r'DOI:\s*10\.\d{4,}/[^\s<>"\')\]]+',
    r'\b10\.\d{4,}/[^\s<>"\')\]]{5,}',
]

found = set()
for pat in patterns:
    for m in re.finditer(pat, text, re.IGNORECASE):
        url = m.group(0).strip().rstrip('.,;')
        # Normalisiere zu https://doi.org/
        if url.lower().startswith('doi:'):
            url = 'https://doi.org/' + url[4:].strip()
        elif url.startswith('10.'):
            url = 'https://doi.org/' + url
        found.add(url)

# Auch reine URLs (non-DOI) extrahieren
url_pat = r'https?://(?!doi\.org)[^\s<>"\')\]]{10,}'
for m in re.finditer(url_pat, text, re.IGNORECASE):
    url = m.group(0).strip().rstrip('.,;)')
    found.add(url)

dois = sorted(found)
print(f"Gefundene Links: {len(dois)}")
print()
for i, d in enumerate(dois, 1):
    print(f"{i:3}. {d}")

# Speichere Liste fuer naechsten Schritt
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\all_links.txt', 'w', encoding='utf-8') as f:
    for d in dois:
        f.write(d + '\n')

print(f"\nGespeichert in all_links.txt")
