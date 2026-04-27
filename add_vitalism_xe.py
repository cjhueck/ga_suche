import zipfile
import re
from lxml import etree
from collections import defaultdict

# Arbeitet auf der NEWXE-Datei weiter
src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_NEWXE.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_FINAL.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

def get_para_text(p):
    return ''.join(t.text for r in p.iter(w('r')) for t in r.findall(w('t')) if t.text)

def get_instr_text(p):
    return ''.join(el.text for el in p.iter(w('instrText')) if el.text)

def get_existing_xe(p):
    return re.findall(r'XE\s+"([^"]+)"', get_instr_text(p))

def make_xe_field(xe_entry):
    runs = []
    def make_rpr():
        rPr = etree.Element(w('rPr'))
        rf = etree.SubElement(rPr, w('rFonts'))
        rf.set(w('ascii'), 'Times New Roman')
        rf.set(w('hAnsi'), 'Times New Roman')
        rf.set(w('cs'), 'Times New Roman')
        return rPr
    r_begin = etree.Element(w('r'))
    r_begin.set(w('rsidRPr'), '00205EA3')
    r_begin.append(make_rpr())
    etree.SubElement(r_begin, w('fldChar')).set(w('fldCharType'), 'begin')
    runs.append(r_begin)
    r_instr = etree.Element(w('r'))
    r_instr.set(w('rsidRPr'), '00205EA3')
    r_instr.append(make_rpr())
    instr = etree.SubElement(r_instr, w('instrText'))
    instr.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    instr.text = f' XE "{xe_entry}" '
    runs.append(r_instr)
    r_end = etree.Element(w('r'))
    r_end.set(w('rsidRPr'), '00205EA3')
    r_end.append(make_rpr())
    etree.SubElement(r_end, w('fldChar')).set(w('fldCharType'), 'end')
    runs.append(r_end)
    return runs

def append_xe_to_para(p, xe_entry):
    xe_runs = make_xe_field(xe_entry)
    pos = len(list(p))
    for j, r in enumerate(xe_runs):
        p.insert(pos + j, r)

BIBLIO_PATTERNS = [
    r'[A-Z][a-z]+,\s+[A-Z]\.\s*\(\d{4}\)',
    r'\(\d{4}\)\.\s+[A-Z]',
    r'https?://',
    r'doi:',
    r'University Press',
    r'^\s*In\s+[A-Z]',
]

def is_biblio_para(text):
    if len(text.strip()) < 30:
        return True
    for pat in BIBLIO_PATTERNS:
        if re.search(pat, text):
            return True
    return False

# Themen mit wenig Abdeckung: Vitalism, Teleology (ergaenzen wo fehlend)
# Strategie: fuege standalone XE hinzu, wo der Begriff im Fliesstext steht
# aber KEIN XE eines verwandten Eintrags vorhanden ist

todo_consistency = {
    # pattern im text -> (XE-Label, check-ob-schon-verwandtes-XE)
    r'\bvitalis': ('Vitalism', lambda xes: any('italism' in x for x in xes)),
    r'\bteleolog': ('Teleology:return in biology', lambda xes: any('eleolog' in x for x in xes)),
    r'\bnormativity\b|\bnormative\b': ('Normativity', lambda xes: any('ormativ' in x for x in xes)),
    r'\badaptation\b|\badaptive\b': ('Adaptation', lambda xes: any('daptati' in x for x in xes)),
}

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/document.xml') as f:
        doc_raw = f.read()

doc_tree = etree.fromstring(doc_raw)
paragraphs = doc_tree.findall('.//' + w('p'))

added = defaultdict(int)
skipped_biblio = defaultdict(int)
skipped_covered = defaultdict(int)

for i, p in enumerate(paragraphs):
    text = get_para_text(p)
    if is_biblio_para(text):
        for pat in todo_consistency:
            if re.search(pat, text, re.IGNORECASE):
                skipped_biblio[pat] += 1
        continue

    existing_xe = get_existing_xe(p)

    for pattern, (xe_label, already_covered) in todo_consistency.items():
        if re.search(pattern, text, re.IGNORECASE):
            if already_covered(existing_xe):
                skipped_covered[xe_label] += 1
            elif xe_label not in existing_xe:
                append_xe_to_para(p, xe_label)
                added[xe_label] += 1

print("=== KONSISTENZ-XE EINGEFÜGT ===")
for label, count in sorted(added.items()):
    print(f"  XE \"{label}\": {count}x neu")

print()
print("=== BEREITS ABGEDECKT ===")
for label, count in sorted(skipped_covered.items()):
    print(f"  {label}: {count}x bereits mit verwandtem XE versehen")

print()
print("=== IN BIBLIOGRAPHIE ÜBERSPRUNGEN ===")
for pat, count in sorted(skipped_biblio.items()):
    print(f"  {pat}: {count}x")

new_xml = etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, new_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: ...FINAL.docx")
