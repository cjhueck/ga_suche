import zipfile, re, shutil

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_s.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc  = z.read('word/document.xml').decode('utf-8')
    fn   = z.read('word/footnotes.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
    try:
        fn_rels = z.read('word/_rels/footnotes.xml.rels').decode('utf-8')
    except:
        fn_rels = ''

import os; os.remove(tmp)

# Alle Hyperlinks aus den Relationships extrahieren
print("=== HYPERLINKS AUS RELATIONSHIPS ===")
all_rels_urls = re.findall(r'Target="([^"]*doi[^"]*)"', rels + fn_rels, re.IGNORECASE)
all_rels_urls += re.findall(r'Target="(https?://[^"]{10,})"', rels + fn_rels)
print(f"Hyperlinks in Rels: {len(all_rels_urls)}")
for url in sorted(set(all_rels_urls)):
    print(f"  {url}")

print()

# Suche nach den drei spezifischen DOIs
search_terms = [
    '9780198779063',
    's11229-011-9878',
    's10539-021-09818',
]
combined = doc + fn + rels + fn_rels
text_clean = re.sub(r'<[^>]+>', ' ', combined)
text_clean = re.sub(r'\s+', ' ', text_clean)

print("=== SUCHE NACH SPEZIFISCHEN DOI-FRAGMENTEN ===")
for term in search_terms:
    found = []
    for m in re.finditer(re.escape(term), combined, re.IGNORECASE):
        ctx = combined[max(0,m.start()-100):m.end()+100]
        ctx_clean = re.sub(r'<[^>]+>', '', ctx).strip()
        found.append(ctx_clean[:200])
    if found:
        print(f"\n  '{term}' GEFUNDEN ({len(found)}x):")
        for f in found:
            print(f"    {f}")
    else:
        print(f"\n  '{term}' -> NICHT GEFUNDEN im Dokument")

# Suche auch nach truncated DOIs - zeige Kontext
print()
print("=== KONTEXT DER TRUNCATED/DEFEKTEN LINKS ===")

truncated = [
    '1097-0177',   # Dev Dynamics
    's10441-005-5350',  # Acta Biotheoretica
    'S0367-1615',  # Elsevier
    'doi:10.1007/s40656-025-00681-7',  # double prefix
]

for term in truncated:
    for m in re.finditer(re.escape(term), doc + fn):
        content = doc + fn
        ctx = content[max(0,m.start()-150):m.end()+200]
        ctx_clean = re.sub(r'<[^>]+>', '', ctx).strip()
        print(f"\n  '{term}':")
        print(f"    {ctx_clean[:300]}")
        break

# Zeige auch 404-Links mit Kontext
print()
print("=== 404-LINKS MIT KONTEXT ===")
for doi_part in ['9780226520827', 'jfg.2021.113']:
    for m in re.finditer(re.escape(doi_part), doc + fn):
        content = doc + fn
        ctx = content[max(0,m.start()-200):m.end()+200]
        ctx_clean = re.sub(r'<[^>]+>', '', ctx).strip()
        print(f"\n  '{doi_part}':")
        print(f"    {ctx_clean[:400]}")
        break
