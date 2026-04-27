import zipfile, re, shutil

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_ctx.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')
import os; os.remove(tmp)

combined = doc + fn
# Sauberer Text
text = re.sub(r'<[^>]+>', ' ', combined)
text = re.sub(r'\s+', ' ', text)
text = re.sub(r'[\u200b\u200c\u200d]', '', text)

searches = [
    ('s10441-005-5350', 400),
    ('1097-0177', 300),
    ('jfg.2021.113', 300),
    ('9780226520827', 300),
    ('doi:10.1007/s40656-025-00681-7', 200),
]

for term, ctx_len in searches:
    for m in re.finditer(re.escape(term), text, re.IGNORECASE):
        snippet = text[max(0, m.start()-ctx_len):m.end()+ctx_len]
        print(f"\n=== '{term}' ===")
        print(snippet.strip())
        break  # nur erstes Vorkommen
