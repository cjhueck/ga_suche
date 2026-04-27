import zipfile, shutil, re

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_DOIFIX.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_doi2.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
    try:
        fn_rels = z.read('word/_rels/footnotes.xml.rels').decode('utf-8')
    except:
        fn_rels = None
import os; os.remove(tmp)

doc_new = doc
fn_new  = fn
rels_new = rels

# ── Fix 1: s10441-005-5350- in Run 1, 9 in Run 2 ──────────────────────────
# Ersetze in Run 1 den Text: fuege -9 ein und loesche die 9 aus Run 2
# Muster: <w:t>...s10441-005-5350-</w:t></w:r><w:r ...><w:rPr>...<w:spacing.../>...</w:rPr><w:t>9</w:t></w:r>

pattern1 = r'(<w:t>[^<]*s10441-005-5350-)(</w:t></w:r><w:r[^>]*><w:rPr>.*?</w:rPr><w:t>)(9)(</w:t></w:r>)'
def fix_s10441(m):
    # Haenge -9 an die URL in Run 1 an, leere den Text in Run 2
    return m.group(1) + '9' + m.group(2) + '' + m.group(4)

old_count_1 = len(re.findall(pattern1, doc_new, re.DOTALL))
doc_new = re.sub(pattern1, fix_s10441, doc_new, flags=re.DOTALL)
new_count_1 = doc_new.count('s10441-005-5350-9')
print(f"Fix 1 (s10441): {old_count_1} Treffer gefunden, jetzt {new_count_1}x s10441-005-5350-9 vorhanden")
print(f"  Kein haengender Bindestrich mehr: {'s10441-005-5350-</w:t>' not in doc_new}")

# ── Fix 2: Doppeltes doi: Prefix ──────────────────────────────────────────
old2 = 'https://doi.org/doi:10.1007/s40656-025-00681-7'
new2 = 'https://doi.org/10.1007/s40656-025-00681-7'
cnt_doc = doc_new.count(old2)
cnt_fn  = fn_new.count(old2)
cnt_rels = rels_new.count(f'Target="{old2}"')

doc_new  = doc_new.replace(old2, new2)
fn_new   = fn_new.replace(old2, new2)
rels_new = rels_new.replace(f'Target="{old2}"', f'Target="{new2}"')
print(f"\nFix 2 (double doi:): in doc={cnt_doc}x, fn={cnt_fn}x, rels={cnt_rels}x gefixt")
print(f"  Noch 'doi:10.1007/s40656' in doc: {doc_new.count('doi:10.1007/s40656')} (sollte 0)")
print(f"  Noch 'doi:10.1007/s40656' in rels: {rels_new.count('doi:10.1007/s40656')} (sollte 0)")

# ── Speichern ─────────────────────────────────────────────────────────────
with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, doc_new.encode('utf-8'))
            elif item.filename == 'word/footnotes.xml':
                zout.writestr(item, fn_new.encode('utf-8'))
            elif item.filename == 'word/_rels/document.xml.rels':
                zout.writestr(item, rels_new.encode('utf-8'))
            elif fn_rels is not None and item.filename == 'word/_rels/footnotes.xml.rels':
                # fn_rels braucht keinen Fix, aber trotzdem korrekt schreiben
                zout.writestr(item, fn_rels.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: {out}")
