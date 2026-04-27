"""
Entfernt den redundanten Schlegel-Absatz aus Zeile 16 (DE-Spalte)
und speichert als 0 Einleitung_fertig_DN_CH_2026.docx.
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'

shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    other = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

# Suche den zu löschenden Absatz
TARGET = 'Der romantische Imperativ fordert die Mischung aller Dichtarten'

para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def para_text(p):
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    return ''.join(runs)

matches = list(para_re.finditer(xml))
found = [m for m in matches if TARGET in para_text(m.group())]

print(f'Absätze mit Zieltext gefunden: {len(found)}')
for m in found:
    print(f'  → {para_text(m.group())[:120]}')

if len(found) != 1:
    print('FEHLER: Genau 1 Treffer erwartet.')
    sys.exit(1)

# Absatz aus XML entfernen
new_xml = xml[:found[0].start()] + xml[found[0].end():]

# Prüfen: ist er weg?
remaining = [m for m in para_re.finditer(new_xml) if TARGET in para_text(m.group())]
print(f'Nach Entfernung noch vorhanden: {len(remaining)}')

# Speichern
with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other.items():
        zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')

# Abschlusskontrolle: Zeile 16 anzeigen
with zipfile.ZipFile(DEST, 'r') as z:
    xml2 = z.read('word/document.xml').decode('utf-8')

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml2, re.DOTALL)
rows = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)
cells = re.findall(r'<w:tc>.*?</w:tc>', rows[16], re.DOTALL)

def cell_paras(cell_xml):
    paras = re.findall(r'<w:p[ >].*?</w:p>', cell_xml, re.DOTALL)
    return [''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip() for p in paras if ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip()]

print('\n=== Zeile 16 nach Bereinigung ===')
print(f'EN ({len(cell_paras(cells[0]))} Abs.):')
for p in cell_paras(cells[0]):
    print(f'  EN| {p[:100]}')
print(f'DE ({len(cell_paras(cells[1]))} Abs.):')
for p in cell_paras(cells[1]):
    print(f'  DE| {p[:100]}')
