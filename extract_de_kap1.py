"""
Extrahiert die deutsche (rechte) Spalte aus Kapitel 1,
wandelt sie in normalen Fließtext um und speichert als _de.docx.
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH_de.docx'

shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    other = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

tbl_re  = re.compile(r'<w:tbl>.*?</w:tbl>', re.DOTALL)
row_re  = re.compile(r'<w:tr[ >].*?</w:tr>', re.DOTALL)
cell_re = re.compile(r'<w:tc>.*?</w:tc>', re.DOTALL)
para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def strip_cell_props(para_xml):
    return re.sub(r'<w:tcPr>.*?</w:tcPr>', '', para_xml, flags=re.DOTALL)

def para_text(p):
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    return ''.join(runs).strip()

# EN-Erkennungswörter zum Herausfiltern von redaktionellen EN-Notizen in DE-Spalte
EDIT_PREFIXES = ('Change to:', 'change to:', 'Add endnote:', 'add endnote:',
                 'DELETE ', 'CHANGE TO:', 'Add the following', 'INSERT ')

tbl_match = tbl_re.search(xml)
rows = row_re.findall(tbl_match.group())
print(f'Tabellenzeilen: {len(rows)}')

de_paragraphs = []
skipped = []

for i, row in enumerate(rows):
    cells = cell_re.findall(row)
    if len(cells) < 2:
        continue
    de_cell = cells[1]
    paras = para_re.findall(de_cell)
    for p in paras:
        text = para_text(p)
        if not text:
            de_paragraphs.append(strip_cell_props(p))  # Leerabsatz behalten
            continue
        # Redaktionelle EN-Notizen in DE-Spalte überspringen
        if any(text.startswith(pref) for pref in EDIT_PREFIXES):
            skipped.append(f'Zeile {i}: {text[:80]}')
            continue
        de_paragraphs.append(strip_cell_props(p))

print(f'Absätze extrahiert: {len(de_paragraphs)}')
if skipped:
    print(f'Übersprungen ({len(skipped)}):')
    for s in skipped:
        print(f'  – {s}')

# Tabelle durch DE-Absätze ersetzen
replacement = '\n'.join(de_paragraphs)
new_xml = xml[:tbl_match.start()] + replacement + xml[tbl_match.end():]

with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other.items():
        zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')

# Abschlusskontrolle
with zipfile.ZipFile(DEST, 'r') as z:
    xml2 = z.read('word/document.xml').decode('utf-8')
paras_final = [p for p in para_re.findall(xml2) if para_text(p)]
print(f'\n=== {len(paras_final)} nicht-leere Absätze im Ergebnisdokument ===')
for i, p in enumerate(paras_final[:10]):
    print(f'[{i:3d}] {para_text(p)[:100]}')
print('...')
for i, p in enumerate(paras_final[-5:], len(paras_final)-5):
    print(f'[{i:3d}] {para_text(p)[:100]}')
