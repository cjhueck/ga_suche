import zipfile, shutil, re

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_DOIFIX.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_doi.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')

import os; os.remove(tmp)

fixes = {
    'doc': [],
    'fn':  [],
}

# Fix 1: s10441-005-5350- 9 → s10441-005-5350-9 (Leerzeichen entfernen)
# Im XML: der DOI ist als Text gespeichert, das Leerzeichen ist zwischen zwei w:t Elementen
# Einfacher Fix direkt im XML-String
old1 = 's10441-005-5350-'
# Suche ob in doc oder fn
for name, content in [('doc', doc), ('fn', fn)]:
    if old1 in content:
        fixes[name].append(f'Acta Biotheoretica DOI (abgeschnitten) in {name}')

# Fix 2: doi:10.1007/s40656-025-00681-7 → 10.1007/s40656-025-00681-7
old2a = 'https://doi.org/doi:10.1007/s40656-025-00681-7'
old2b = 'doi:10.1007/s40656-025-00681-7'
for name, content in [('doc', doc), ('fn', fn)]:
    if old2a in content or old2b in content:
        fixes[name].append(f'Double DOI prefix in {name}')

print("Gefundene Fehler:")
for k, v in fixes.items():
    for msg in v:
        print(f"  {msg}")

# Tatsaechliche Fixes
# Fix 1: Im Dokument ist das 's10441-005-5350-' gefolgt von Whitespace und dann '9'
# Wir fixen direkt in der XML das Leerzeichen zwischen den Text-Tokens
# Da es als w:t gespeichert ist, koennte das Leerzeichen in einem separaten w:t sein
# Safer: ersetze alle Varianten
doc_new = doc
fn_new  = fn

# Fix Leerzeichen im DOI - verschiedene Moeglichkeiten wie es im XML erscheinen kann
# Variante 1: direkt im selben w:t
doc_new = doc_new.replace('s10441-005-5350- 9', 's10441-005-5350-9')
doc_new = doc_new.replace('s10441-005-5350-&#x2028;9', 's10441-005-5350-9')
fn_new  = fn_new.replace('s10441-005-5350- 9', 's10441-005-5350-9')

# Fix double doi: prefix
doc_new = doc_new.replace('https://doi.org/doi:10.1007/s40656-025-00681-7',
                           'https://doi.org/10.1007/s40656-025-00681-7')
doc_new = doc_new.replace('>doi:10.1007/s40656-025-00681-7<',
                           '>https://doi.org/10.1007/s40656-025-00681-7<')
fn_new  = fn_new.replace('https://doi.org/doi:10.1007/s40656-025-00681-7',
                           'https://doi.org/10.1007/s40656-025-00681-7')

# Auch den Hyperlink in den relationships fixen
with zipfile.ZipFile(src, 'r') as z:
    rels_raw = z.read('word/_rels/document.xml.rels').decode('utf-8')
    try:
        fn_rels_raw = z.read('word/_rels/footnotes.xml.rels').decode('utf-8')
    except:
        fn_rels_raw = None

rels_new = rels_raw.replace(
    'Target="https://doi.org/doi:10.1007/s40656-025-00681-7"',
    'Target="https://doi.org/10.1007/s40656-025-00681-7"'
)

# Verifikation
print()
print("Verifikation nach Fix:")
print(f"  s10441-005-5350-9 in doc: {doc_new.count('s10441-005-5350-9')}x")
print(f"  s10441-005-5350-  in doc: {doc_new.count('s10441-005-5350- ')}x (sollte 0 sein)")
print(f"  doi:10.1007/s40656 in doc: {doc_new.count('doi:10.1007/s40656')}x (sollte 0 sein)")
print(f"  doi:10.1007/s40656 in fn:  {fn_new.count('doi:10.1007/s40656')}x (sollte 0 sein)")
print(f"  doi:10.1007/s40656 in rels: {rels_new.count('doi:10.1007/s40656')}x (sollte 0 sein)")

# Speichern
with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, doc_new.encode('utf-8'))
            elif item.filename == 'word/footnotes.xml':
                zout.writestr(item, fn_new.encode('utf-8'))
            elif item.filename == 'word/_rels/document.xml.rels':
                zout.writestr(item, rels_new.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: ...DOIFIX.docx")
