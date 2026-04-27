import zipfile
import copy
from lxml import etree

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_EPIGENESIS.docx'

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/document.xml') as f:
        raw = f.read()

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

def make_xe_field(xe_entry, rpr_font='Times New Roman'):
    """Erstellt drei w:r Elemente fuer ein XE-Feld."""
    runs = []

    def make_rpr():
        rPr = etree.Element(w('rPr'))
        rFonts = etree.SubElement(rPr, w('rFonts'))
        rFonts.set(w('ascii'), rpr_font)
        rFonts.set(w('hAnsi'), rpr_font)
        rFonts.set(w('cs'), rpr_font)
        return rPr

    # begin
    r_begin = etree.Element(w('r'))
    r_begin.set(w('rsidRPr'), '00205EA3')
    r_begin.append(make_rpr())
    fc_begin = etree.SubElement(r_begin, w('fldChar'))
    fc_begin.set(w('fldCharType'), 'begin')
    runs.append(r_begin)

    # instrText
    r_instr = etree.Element(w('r'))
    r_instr.set(w('rsidRPr'), '00205EA3')
    r_instr.append(make_rpr())
    instr = etree.SubElement(r_instr, w('instrText'))
    instr.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    instr.text = f' XE "{xe_entry}" '
    runs.append(r_instr)

    # end
    r_end = etree.Element(w('r'))
    r_end.set(w('rsidRPr'), '00205EA3')
    r_end.append(make_rpr())
    fc_end = etree.SubElement(r_end, w('fldChar'))
    fc_end.set(w('fldCharType'), 'end')
    runs.append(r_end)

    return runs

tree = etree.fromstring(raw)
paragraphs = tree.findall('.//' + w('p'))

# Paragraphen in Haeck et al. ohne XE "Epigenesis":
# Para 1404: Keyword-Liste
# Para 1415: Fliesstext (Kant, epigenesis)
# Para 1445: Abschnittstitel "From Epigenesis to Concrescence"
# Para 1453: Fliesstext ("epigenesis of pure reason")

# Zuzaetzlich: fuer para 1415 auch "Embryology:epigenesis" hinzufuegen,
# da es sich um biologischen Epigenesis-Begriff handelt

additions = {
    1404: ['Epigenesis'],
    1415: ['Epigenesis', 'Embryology:epigenesis'],
    1445: ['Epigenesis'],
    1453: ['Epigenesis'],
}

for para_idx, entries in additions.items():
    p = paragraphs[para_idx]
    # Fuege XE-Felder am Ende des Paragraphen ein (vor dem naechsten Element nach dem letzten w:r)
    # Finde letztes w:r oder w:bookmarkEnd Element
    children = list(p)
    insert_pos = len(children)  # ans Ende
    # Aber vor pPrChange oder anderen Meta-Elementen
    for i, child in enumerate(children):
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag in ('sectPr',):
            insert_pos = i
            break

    for entry in entries:
        xe_runs = make_xe_field(entry)
        for j, r in enumerate(xe_runs):
            p.insert(insert_pos + j, r)
        insert_pos += len(xe_runs)

    # Verifiziere
    instrs = [el.text for el in p.iter(w('instrText')) if el.text]
    print(f"Para {para_idx}: XE-Eintraege nach Einfuegen: {instrs}")

# Speichere als neue Datei
new_xml = etree.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, new_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nGespeichert: {out}")
