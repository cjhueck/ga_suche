import zipfile, re, os

folder = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final'

search_terms = [
    ('s11229-011-9878', 'Bich 2012 - FALSCHE DOI'),
    ('s10539-021-09818', '3. User-DOI - s10539'),
    ('9780198779063',    '1. User-DOI - 9780198779063'),
]

for fname in sorted(os.listdir(folder)):
    if not fname.endswith('.docx'):
        continue
    fpath = os.path.join(folder, fname)
    try:
        with zipfile.ZipFile(fpath, 'r') as z:
            xmlfiles = ['word/document.xml']
            if 'word/footnotes.xml' in z.namelist():
                xmlfiles.append('word/footnotes.xml')
            content = ''
            for xf in xmlfiles:
                content += z.read(xf).decode('utf-8', errors='replace')
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text)

        for term, label in search_terms:
            if term in content:
                # Kontext
                idx = content.find(term)
                ctx = content[max(0,idx-200):idx+200]
                ctx_clean = re.sub(r'<[^>]+>', '', ctx).strip()
                print(f"\n[{label}] in: {fname}")
                print(f"  {ctx_clean[:300]}")
    except Exception as e:
        pass

print("\nSuche abgeschlossen.")
