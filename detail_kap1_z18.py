import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

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

cells = re.findall(r'<w:tc>.*?</w:tc>', rows[18], re.DOTALL)
en_p = cell_paras(cells[0])
de_p = cell_paras(cells[1])

print('=== ZEILE 18 – VOLLTEXT ===')
for j, p in enumerate(en_p):
    print(f'\nEN[{j}]: {p}')
print()
for j, p in enumerate(de_p):
    print(f'\nDE[{j}]: {p}')

# Auch Zeile 19 anzeigen (Kontext)
print('\n\n=== ZEILE 19 (Kontext) ===')
cells19 = re.findall(r'<w:tc>.*?</w:tc>', rows[19], re.DOTALL)
for j, p in enumerate(cell_paras(cells19[0])):
    print(f'EN[{j}]: {p[:150]}')
for j, p in enumerate(cell_paras(cells19[1])):
    print(f'DE[{j}]: {p[:150]}')
