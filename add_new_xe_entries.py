import zipfile
import re
from lxml import etree
from collections import defaultdict

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_NEWXE.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

def get_para_text(p):
    return ''.join(t.text for r in p.iter(w('r')) for t in r.findall(w('t')) if t.text)

def get_para_style(p):
    pPr = p.find(w('pPr'))
    if pPr is not None:
        ps = pPr.find(w('pStyle'))
        if ps is not None:
            return ps.get(w('val'), '')
    return ''

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
    insert_pos = len(list(p))
    for j, r in enumerate(xe_runs):
        p.insert(insert_pos + j, r)

# Referenzparagraphen-Erkennung: typische Muster in Bibliographien
BIBLIO_PATTERNS = [
    r'^\s*[A-Z][a-z]+,\s+[A-Z]',        # "Author, A."
    r'^\s*[A-Z][a-z]+,\s+[A-Z][a-z]',  # "Albert, H."
    r'https?://',
    r'doi:',
    r'^\s*\(\d{4}\)',
    r'University Press',
    r'^\s*In\s+[A-Z]',
    r'^\s*Ed\.',
    r'^\s*\d+\s*\(',                      # "1. (Author"
]

def is_biblio_para(text):
    if len(text.strip()) < 30:
        return True
    for pat in BIBLIO_PATTERNS:
        if re.search(pat, text):
            return True
    # Typisches Muster: "Lastname, F. (year). Title. Journal/Publisher"
    if re.search(r'[A-Z][a-z]+,\s+[A-Z]\.\s*\(\d{4}\)', text):
        return True
    if re.search(r'\(\d{4}\)\.\s+[A-Z]', text):
        return True
    return False

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/document.xml') as f:
        doc_raw = f.read()

doc_tree = etree.fromstring(doc_raw)
paragraphs = doc_tree.findall('.//' + w('p'))

print(f"Gesamt Paragraphen: {len(paragraphs)}")
print()

# ============================================================
# PHASE 1: Physiology, Generation, Preformation
# ============================================================

todo_1 = {
    # pattern -> (xe_label, auch_untereintraege)
    r'\bphysiolog': [
        'Physiology',
    ],
    r'\bgeneration\b': [
        'Generation',
    ],
    r'\bpreformat': [
        'Preformation',
        'Embryology:preformation',
    ],
}

# ============================================================
# PHASE 2: Einzelpersonen
# ============================================================

todo_2 = {
    r'\bDescartes\b': ['Descartes'],
    r'\bHegel\b': ['Hegel'],
    r'\bHerder\b': ['Herder'],
    r'\bBuffon\b': ['Buffon'],
    r'\bOken\b': ['Oken'],
}

# ============================================================
# PHASE 3: Fichte (hat nur 1x XE, braucht mehr)
# ============================================================

todo_3 = {
    r'\bFichte\b': ['Fichte:Wissenschaftslehre'],
}

all_todo = {**todo_1, **todo_2}

# Zähler
added_counts = defaultdict(int)
skipped_biblio = defaultdict(int)
skipped_already = defaultdict(int)

for i, p in enumerate(paragraphs):
    text = get_para_text(p)
    style = get_para_style(p)
    existing_xe = get_existing_xe(p)

    if is_biblio_para(text):
        for pat in all_todo:
            if re.search(pat, text, re.IGNORECASE):
                skipped_biblio[pat] += 1
        continue

    for pattern, xe_labels in all_todo.items():
        if re.search(pattern, text, re.IGNORECASE):
            for xe_label in xe_labels:
                if xe_label not in existing_xe:
                    append_xe_to_para(p, xe_label)
                    added_counts[xe_label] += 1
                else:
                    skipped_already[xe_label] += 1

print("=== EINGEFÜGTE XE-EINTRÄGE ===")
for label, count in sorted(added_counts.items()):
    print(f"  XE \"{label}\": {count}x neu eingefügt")

print()
print("=== ÜBERSPRUNGEN (Bibliographie) ===")
for pat, count in sorted(skipped_biblio.items()):
    print(f"  Pattern '{pat}': {count}x in Bibliographie")

print()
print("=== ÜBERSPRUNGEN (bereits vorhanden) ===")
for label, count in sorted(skipped_already.items()):
    print(f"  XE \"{label}\": {count}x bereits vorhanden")

# Speichern
new_xml = etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, new_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: ...NEWXE.docx")
