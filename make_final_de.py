"""
Erstellt die deutsche Endversion:
- Nur deutsche Spalte (Tabelle aufgelöst)
- Alle Kommentare entfernt
- Einheitlich schwarze Schrift (keine Farbmarkierungen)
- Keine Hervorhebungen (Highlight)
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_DE_final.docx'

shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml      = z.read('word/document.xml').decode('utf-8')
    other    = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

# ── 1. DE-Spalte aus Tabelle extrahieren ─────────────────────────────────────
tbl_re  = re.compile(r'<w:tbl>.*?</w:tbl>', re.DOTALL)
row_re  = re.compile(r'<w:tr[ >].*?</w:tr>', re.DOTALL)
cell_re = re.compile(r'<w:tc>.*?</w:tc>', re.DOTALL)
para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def strip_cell_props(p):
    return re.sub(r'<w:tcPr>.*?</w:tcPr>', '', p, flags=re.DOTALL)

tbl_match = tbl_re.search(xml)
rows = row_re.findall(tbl_match.group())
de_paras = []
for row in rows:
    cells = cell_re.findall(row)
    if len(cells) < 2:
        continue
    for p in para_re.findall(cells[1]):
        de_paras.append(strip_cell_props(p))

new_xml = xml[:tbl_match.start()] + '\n'.join(de_paras) + xml[tbl_match.end():]
print(f'DE-Absätze extrahiert: {len(de_paras)}')

# ── 2. Kommentar-Markierungen aus dem Body entfernen ─────────────────────────
for tag in ['w:commentRangeStart', 'w:commentRangeEnd', 'w:commentReference']:
    new_xml = re.sub(rf'<{tag}[^/]*/>', '', new_xml)
    new_xml = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', new_xml, flags=re.DOTALL)
print('Kommentar-Markierungen entfernt')

# ── 3. Farbformatierung entfernen (schwarz = Standard) ───────────────────────
# Entferne w:color-Elemente in Laufeigenschaften
new_xml = re.sub(r'<w:color\s+[^/]*/>', '', new_xml)
# Entferne w:highlight (farbige Hinterlegung)
new_xml = re.sub(r'<w:highlight\s+[^/]*/>', '', new_xml)
# Entferne w:shd (Schattierung / farbiger Hintergrund) in Laufeigenschaften
# (Vorsicht: nur innerhalb rPr, nicht tblPr/trPr/tcPr)
new_xml = re.sub(r'(<w:rPr>(?:(?!<w:rPr>).)*?)<w:shd\s+[^/]*/>((?:(?!<w:rPr>).)*?</w:rPr>)',
                 r'\1\2', new_xml, flags=re.DOTALL)
print('Farbformatierung bereinigt')

# ── 4. Leere rPr-Elemente aufräumen ──────────────────────────────────────────
new_xml = re.sub(r'<w:rPr>\s*</w:rPr>', '', new_xml)

# ── 5. Kommentardatei leeren ──────────────────────────────────────────────────
EMPTY_COMMENTS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:comments>'
EMPTY_FOOTNOTES_ENTRIES = None  # Fußnoten bleiben erhalten

# ── 6. Speichern ─────────────────────────────────────────────────────────────
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

paras = para_re.findall(xml2)
filled = [p for p in paras if re.search(r'<w:t[^>]*>[^<]+</w:t>', p)]
print(f'Nicht-leere Absätze im Ergebnis: {len(filled)}')

# Prüfe auf verbliebene Farbelemente
colors = re.findall(r'<w:color[^>]+>', xml2)
highlights = re.findall(r'<w:highlight[^>]+>', xml2)
comments_left = re.findall(r'<w:commentRange', xml2)
print(f'Verbliebene Farbelemente: {len(colors)}')
print(f'Verbliebene Highlights: {len(highlights)}')
print(f'Verbliebene Kommentar-Markierungen: {len(comments_left)}')

# Erste und letzte 5 Absätze anzeigen
def pt(p): return ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip()
texts = [pt(p) for p in filled]
print('\nErste Absätze:')
for t in texts[:5]: print(f'  {t[:90]}')
print('...')
print('Letzte Absätze:')
for t in texts[-5:]: print(f'  {t[:90]}')
