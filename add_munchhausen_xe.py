import zipfile
import re
from lxml import etree

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_MUNCH.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

def get_para_text(p):
    texts = []
    for r in p.iter(w('r')):
        for t in r.findall(w('t')):
            if t.text:
                texts.append(t.text)
    return ''.join(texts)

def get_instr_text(p):
    texts = []
    for instr in p.iter(w('instrText')):
        if instr.text:
            texts.append(instr.text)
    return ''.join(texts)

def make_xe_field(xe_entry):
    runs = []

    def make_rpr():
        rPr = etree.Element(w('rPr'))
        rFonts = etree.SubElement(rPr, w('rFonts'))
        rFonts.set(w('ascii'), 'Times New Roman')
        rFonts.set(w('hAnsi'), 'Times New Roman')
        rFonts.set(w('cs'), 'Times New Roman')
        return rPr

    r_begin = etree.Element(w('r'))
    r_begin.set(w('rsidRPr'), '00205EA3')
    r_begin.append(make_rpr())
    fc_begin = etree.SubElement(r_begin, w('fldChar'))
    fc_begin.set(w('fldCharType'), 'begin')
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
    fc_end = etree.SubElement(r_end, w('fldChar'))
    fc_end.set(w('fldCharType'), 'end')
    runs.append(r_end)

    return runs

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/footnotes.xml') as f:
        fn_raw = f.read()
    with z.open('word/document.xml') as f:
        doc_raw = f.read()

fn_tree = etree.fromstring(fn_raw)
paragraphs = fn_tree.findall('.//' + w('p'))

print("=== Paragraphen mit Münchhausen in footnotes.xml ===")
target_paras = []
for i, p in enumerate(paragraphs):
    text = get_para_text(p)
    if re.search(r'nchhausen|Trilemma', text, re.IGNORECASE):
        instr = get_instr_text(p)
        has_xe = 'XE' in instr
        print(f"Para {i}: {'MIT XE' if has_xe else 'OHNE XE'}")
        print(f"  Text: {text[:250]}")
        if instr:
            print(f"  XE:   {instr[:200]}")
        print()
        if not has_xe or 'nchhausen' not in instr.lower():
            target_paras.append(i)

print(f"Einfügen in Paragraphen: {target_paras}")
print()

# XE-Feld einfügen
for para_idx in target_paras:
    p = paragraphs[para_idx]
    children = list(p)
    insert_pos = len(children)

    xe_runs = make_xe_field('Münchhausen-Trilemma')
    for j, r in enumerate(xe_runs):
        p.insert(insert_pos + j, r)

    instrs = [el.text for el in p.iter(w('instrText')) if el.text]
    print(f"Para {para_idx} nach Einfügen: {instrs}")

# Speichere
new_fn_xml = etree.tostring(fn_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/footnotes.xml':
                zout.writestr(item, new_fn_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: ...MUNCH.docx")
