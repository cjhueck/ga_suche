import zipfile
import re
from lxml import etree
from collections import defaultdict

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_REV2.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

def get_para_text(p):
    return ''.join(t.text for r in p.iter(w('r')) for t in r.findall(w('t')) if t.text)

def get_existing_xe(p):
    return re.findall(r'XE\s+"([^"]+)"', ''.join(el.text for el in p.iter(w('instrText')) if el.text))

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
    r'https?://', r'doi:', r'University Press',
]

def is_biblio(text):
    if len(text.strip()) < 30:
        return True
    return any(re.search(p, text) for p in BIBLIO_PATTERNS)

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/document.xml') as f:
        doc_raw = f.read()

doc_tree = etree.fromstring(doc_raw)
paragraphs = doc_tree.findall('.//' + w('p'))

# ============================================================
# PHASE A: String-Ersetzungen direkt auf XML-Bytes
# ============================================================
doc_str = doc_raw.decode('utf-8')

replacements = [
    # Kant harmonisieren
    ('XE "Kant:natural purposes"',             'XE "Kant:organism and purposiveness"'),
    ('XE "Kant:organisms as natural purposes"', 'XE "Kant:organism and purposiveness"'),
    # Vitalism harmonisieren
    ('XE "Vitalism:historical tradition"',      'XE "Vitalism:historical context"'),
]

replace_counts = {}
for old, new in replacements:
    count = doc_str.count(old)
    doc_str = doc_str.replace(old, new)
    replace_counts[old] = count
    print(f'Ersetzt: "{old}" -> "{new}" ({count}x)')

print()

# Neu parsen nach String-Ersetzungen
doc_tree = etree.fromstring(doc_str.encode('utf-8'))
paragraphs = doc_tree.findall('.//' + w('p'))

# ============================================================
# PHASE B: XE-Felder entfernen (Life-Untereintraege)
# ============================================================
entries_to_delete = {
    'Life:self-organization and interdependence',
    'Life:conditions of cognition',
}

deleted_counts = defaultdict(int)

for p in paragraphs:
    children = list(p)
    to_remove = []
    i = 0
    while i < len(children):
        child = children[i]
        # Suche begin-fldChar
        fc = child.find('.//' + w('fldChar'))
        if fc is not None and fc.get(w('fldCharType')) == 'begin':
            # Naechstes Kind ist instrText-Run
            if i + 1 < len(children):
                instr_run = children[i + 1]
                instr_els = instr_run.findall('.//' + w('instrText'))
                if instr_els:
                    instr_text = ''.join(el.text for el in instr_els if el.text)
                    xe_match = re.search(r'XE\s+"([^"]+)"', instr_text)
                    if xe_match and xe_match.group(1) in entries_to_delete:
                        # Merke begin, instr und end (i, i+1, i+2) zum Loeschen
                        to_remove.extend([child, instr_run])
                        deleted_counts[xe_match.group(1)] += 1
                        # end-run suchen (i+2)
                        if i + 2 < len(children):
                            end_run = children[i + 2]
                            end_fc = end_run.find('.//' + w('fldChar'))
                            if end_fc is not None and end_fc.get(w('fldCharType')) == 'end':
                                to_remove.append(end_run)
                        i += 3
                        continue
        i += 1

    for el in to_remove:
        p.remove(el)

print("=== GELOESCHTE XE-EINTRAEGE ===")
for entry, count in deleted_counts.items():
    print(f'  Geloescht: XE "{entry}" ({count}x)')
print()

# ============================================================
# PHASE C: Neue XE-Eintraege hinzufuegen
# ============================================================
new_todo = {
    r'\bmetabolis':        ['Metabolism'],
    r'\bhomeostasis\b':    ['Homeostasis'],
    r'\binformation\b':    ['Information'],
    r'\bFichte\b':         ['Fichte:Wissenschaftslehre'],
}

added = defaultdict(int)
skipped_biblio = defaultdict(int)
skipped_covered = defaultdict(int)

for p in paragraphs:
    text = get_para_text(p)
    if is_biblio(text):
        continue
    existing = get_existing_xe(p)
    for pattern, xe_labels in new_todo.items():
        if re.search(pattern, text, re.IGNORECASE):
            for xe_label in xe_labels:
                # Prüfe ob schon ein verwandter Eintrag vorhanden
                key = xe_label.split(':')[0].lower()
                already = any(key in x.lower() for x in existing)
                if already:
                    skipped_covered[xe_label] += 1
                else:
                    append_xe_to_para(p, xe_label)
                    added[xe_label] += 1
                    existing.append(xe_label)

print("=== NEU HINZUGEFUEGTE XE-EINTRAEGE ===")
for label, count in sorted(added.items()):
    print(f'  XE "{label}": {count}x neu')
print()
print("=== UEBERSPRUNGEN (bereits abgedeckt) ===")
for label, count in sorted(skipped_covered.items()):
    print(f'  {label}: {count}x')
print()

# ============================================================
# PHASE D: Verifikation
# ============================================================
all_instr = ''.join(el.text for el in doc_tree.iter(w('instrText')) if el.text)
from collections import Counter
xe_all = re.findall(r'XE\s+"([^"]+)"', all_instr)
xe_counter = Counter(xe_all)

print("=== VERIFIKATION: RELEVANTE EINTRAEGE ===")
check = [
    'Kant:organism and purposiveness',
    'Kant:natural purposes',
    'Kant:organisms as natural purposes',
    'Vitalism:historical context',
    'Vitalism:historical tradition',
    'Life:self-organization and interdependence',
    'Life:conditions of cognition',
    'Metabolism',
    'Homeostasis',
    'Information',
    'Fichte:Wissenschaftslehre',
]
for entry in check:
    count = xe_counter.get(entry, 0)
    print(f'  {count:4}x  {entry}')

print(f'\nGesamt XE: {len(xe_all)}  |  Eindeutig: {len(xe_counter)}')

# Speichern
new_xml = etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, new_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print(f'\nGespeichert: ...REV2.docx')
