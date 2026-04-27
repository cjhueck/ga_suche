import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')
    # Endnoten
    en_notes_xml = z.read('word/endnotes.xml').decode('utf-8') if 'word/endnotes.xml' in z.namelist() else ''
    fn_notes_xml = z.read('word/footnotes.xml').decode('utf-8') if 'word/footnotes.xml' in z.namelist() else ''

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
rows = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)

def cell_paras(cell_xml):
    paras = re.findall(r'<w:p[ >].*?</w:p>', cell_xml, re.DOTALL)
    result = []
    for p in paras:
        runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
        text = ''.join(runs).strip()
        if text:
            result.append(text)
    return result

for row_idx in [4, 18]:
    cells = re.findall(r'<w:tc>.*?</w:tc>', rows[row_idx], re.DOTALL)
    en_p = cell_paras(cells[0])
    de_p = cell_paras(cells[1])
    print(f'\n{"="*60}')
    print(f'ZEILE {row_idx}')
    print(f'EN ({len(en_p)} Abs.):')
    for p in en_p:
        print(f'  EN| {p}')
    print(f'DE ({len(de_p)} Abs.):')
    for p in de_p:
        print(f'  DE| {p}')

# Fußnoten anzeigen
def show_notes(notes_xml, tag):
    if not notes_xml:
        return
    pattern = r'<w:' + tag + r'\b[^>]*w:id="(\d+)"[^>]*>(.*?)</w:' + tag + r'>'
    for m in re.finditer(pattern, notes_xml, re.DOTALL):
        nid = m.group(1)
        runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', m.group(2), re.DOTALL)
        text = ''.join(runs).strip()
        if text:
            print(f'  {tag} {nid}: {text[:200]}')

print(f'\n{"="*60}')
print('ENDNOTEN:')
show_notes(en_notes_xml, 'endnote')
print('FUSSNOTEN:')
show_notes(fn_notes_xml, 'footnote')
