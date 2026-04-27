"""
Erstellt die deutsche Endversion von Kapitel 1:
- Nur deutsche Spalte (Tabelle aufgelöst)
- Alle Kommentare entfernt
- Einheitlich schwarze Schrift
- Keine Hervorhebungen
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DE_final.docx'

shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml   = z.read('word/document.xml').decode('utf-8')
    other = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

tbl_re  = re.compile(r'<w:tbl>.*?</w:tbl>', re.DOTALL)
row_re  = re.compile(r'<w:tr[ >].*?</w:tr>', re.DOTALL)
cell_re = re.compile(r'<w:tc>.*?</w:tc>', re.DOTALL)
para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def strip_cell_props(p):
    return re.sub(r'<w:tcPr>.*?</w:tcPr>', '', p, flags=re.DOTALL)

def para_text(p):
    return ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip()

# Redaktionelle EN-Notizen in DE-Spalte überspringen
EDIT_PREFIXES = ('Change to:', 'change to:', 'Add endnote:', 'add endnote:',
                 'DELETE ', 'CHANGE TO:', 'Add the following', 'INSERT ')

# ── 1. DE-Spalte extrahieren ──────────────────────────────────────────────────
tbl_match = tbl_re.search(xml)
rows = row_re.findall(tbl_match.group())
de_paras = []
skipped = 0
for row in rows:
    cells = cell_re.findall(row)
    if len(cells) < 2:
        continue
    for p in para_re.findall(cells[1]):
        t = para_text(p)
        if t and any(t.startswith(pref) for pref in EDIT_PREFIXES):
            skipped += 1
            continue
        de_paras.append(strip_cell_props(p))

new_xml = xml[:tbl_match.start()] + '\n'.join(de_paras) + xml[tbl_match.end():]
print(f'DE-Absätze extrahiert: {len(de_paras)} (übersprungen: {skipped})')

# ── 2. Kommentar-Markierungen entfernen ───────────────────────────────────────
for tag in ['w:commentRangeStart', 'w:commentRangeEnd', 'w:commentReference']:
    new_xml = re.sub(rf'<{tag}[^/]*/>', '', new_xml)
    new_xml = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', new_xml, flags=re.DOTALL)
print('Kommentar-Markierungen entfernt')

# ── 3. Farbformatierung entfernen ─────────────────────────────────────────────
new_xml = re.sub(r'<w:color\s+[^/]*/>', '', new_xml)
new_xml = re.sub(r'<w:highlight\s+[^/]*/>', '', new_xml)
new_xml = re.sub(r'(<w:rPr>(?:(?!<w:rPr>).)*?)<w:shd\s+[^/]*/>((?:(?!<w:rPr>).)*?</w:rPr>)',
                 r'\1\2', new_xml, flags=re.DOTALL)
print('Farbformatierung bereinigt')

# ── 4. Leere rPr aufräumen ────────────────────────────────────────────────────
new_xml = re.sub(r'<w:rPr>\s*</w:rPr>', '', new_xml)

# ── 5. Speichern ──────────────────────────────────────────────────────────────
EMPTY_COMMENTS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:comments>'

with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other.items():
        if name == 'word/comments.xml':
            zout.writestr(name, EMPTY_COMMENTS.encode('utf-8'))
        else:
            zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')

# ── Abschlusskontrolle ────────────────────────────────────────────────────────
with zipfile.ZipFile(DEST) as z:
    xml2 = z.read('word/document.xml').decode('utf-8')

filled = [p for p in para_re.findall(xml2) if re.search(r'<w:t[^>]*>[^<]+</w:t>', p)]
colors     = re.findall(r'<w:color[^>]+>', xml2)
highlights = re.findall(r'<w:highlight[^>]+>', xml2)
comments   = re.findall(r'<w:commentRange', xml2)
print(f'Nicht-leere Absätze: {len(filled)}')
print(f'Farbelemente: {len(colors)} | Highlights: {len(highlights)} | Kommentare: {len(comments)}')

texts = [''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip() for p in filled]
print('\nErste Absätze:')
for t in texts[:6]: print(f'  {t[:90]}')
print('...')
print('Letzte Absätze:')
for t in texts[-4:]: print(f'  {t[:90]}')
