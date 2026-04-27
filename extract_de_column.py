"""
Extrahiert die deutsche (rechte) Spalte aus der Tabelle,
wandelt sie in normalen Fließtext um und speichert als _de.docx.
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026_de.docx'

shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    other = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

# Tabelleninhalt der rechten Spalte extrahieren
tbl_re  = re.compile(r'<w:tbl>.*?</w:tbl>', re.DOTALL)
row_re  = re.compile(r'<w:tr[ >].*?</w:tr>', re.DOTALL)
cell_re = re.compile(r'<w:tc>.*?</w:tc>', re.DOTALL)
para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def strip_cell_props(para_xml):
    """Entfernt tcPr aus Absätzen (Zelleigenschaften gehören nicht in Fließtext)."""
    return re.sub(r'<w:tcPr>.*?</w:tcPr>', '', para_xml, flags=re.DOTALL)

tbl_match = tbl_re.search(xml)
if not tbl_match:
    print('FEHLER: Keine Tabelle gefunden.')
    sys.exit(1)

tbl_xml = tbl_match.group()
rows = row_re.findall(tbl_xml)
print(f'Tabellenzeilen: {len(rows)}')

# Alle Absätze aus der rechten (DE) Zelle sammeln
de_paragraphs = []
for i, row in enumerate(rows):
    cells = cell_re.findall(row)
    if len(cells) < 2:
        continue
    de_cell = cells[1]
    paras = para_re.findall(de_cell)
    for p in paras:
        clean_p = strip_cell_props(p)
        de_paragraphs.append(clean_p)

print(f'Deutsche Absätze extrahiert: {len(de_paragraphs)}')

# Tabelle im XML durch die deutschen Absätze ersetzen
replacement = '\n'.join(de_paragraphs)
new_xml = xml[:tbl_match.start()] + replacement + xml[tbl_match.end():]

# Speichern
with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other.items():
        zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')

# Abschlusskontrolle: Absätze anzeigen
with zipfile.ZipFile(DEST, 'r') as z:
    xml2 = z.read('word/document.xml').decode('utf-8')

paras = para_re.findall(xml2)
print(f'\n=== {len(paras)} Absätze im Ergebnisdokument ===')
for i, p in enumerate(paras):
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    text = ''.join(runs).strip()
    if text:
        print(f'[{i:3d}] {text[:100]}')
