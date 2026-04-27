import zipfile, shutil, re

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_bich.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
import os; os.remove(tmp)

combined = doc + fn + rels
text = re.sub(r'<[^>]+>', ' ', combined)
text = re.sub(r'\s+', ' ', text)

# 1. Suche nach s11229-011-9878-7 (falsche DOI)
print("=== SUCHE: s11229-011-9878-7 (FALSCHE DOI) ===")
found = []
for m in re.finditer(r's11229-011-9878', combined):
    ctx = combined[max(0,m.start()-300):m.end()+100]
    ctx_clean = re.sub(r'<[^>]+>', '', ctx).strip()
    found.append(ctx_clean)
    print(ctx_clean[:400])
    print()
print(f"Gefunden: {len(found)}x\n")

# 2. Suche nach s11229-010-9722-6 (korrekte DOI)
print("=== SUCHE: s11229-010-9722-6 (RICHTIGE DOI) ===")
found2 = list(re.finditer(r's11229-010-9722', combined))
print(f"Richtige DOI bereits vorhanden: {len(found2)}x\n")

# 3. Suche nach Bich im Text
print("=== ALLE BICH-EINTRAEGE ===")
for m in re.finditer(r'Bich', text):
    snippet = text[max(0,m.start()-100):m.end()+200]
    print(snippet.strip()[:300])
    print()
