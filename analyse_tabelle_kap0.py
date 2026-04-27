"""
Analysiert die zweispaltige Tabelle in Kap. 0:
Links = EN-Original, Rechts = DE-Übersetzung.
Zeigt alle Zeilen mit vollem Inhalt.
"""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
t = tables[0]
rows = re.findall(r'<w:tr[ >].*?</w:tr>', t, re.DOTALL)

def cell_paras(cell_xml):
    paras = re.findall(r'<w:p[ >].*?</w:p>', cell_xml, re.DOTALL)
    result = []
    for p in paras:
        runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
        text = ''.join(runs).strip()
        if text:
            result.append(text)
    return result

problems = []

for i, row in enumerate(rows):
    cells = re.findall(r'<w:tc>.*?</w:tc>', row, re.DOTALL)
    en_paras = cell_paras(cells[0]) if len(cells) > 0 else []
    de_paras = cell_paras(cells[1]) if len(cells) > 1 else []

    print(f'=== ZEILE {i:02d} ===')
    print(f'EN ({len(en_paras)} Absätze):')
    for p in en_paras:
        print(f'  EN| {p}')
    print(f'DE ({len(de_paras)} Absätze):')
    for p in de_paras:
        print(f'  DE| {p}')

    # Problem-Erkennung
    issues = []
    en_text = ' '.join(en_paras)
    de_text = ' '.join(de_paras)

    if not de_paras:
        issues.append('KEINE ÜBERSETZUNG')
    elif len(de_paras) < len(en_paras):
        issues.append(f'DE hat weniger Absätze ({len(de_paras)}) als EN ({len(en_paras)})')

    for kw in ['add endnote', 'ADD ENDNOTE', 'DELETE', 'CHANGE TO', 'Add the following', 'This endnote should']:
        if kw in en_text:
            issues.append(f'Redaktionelle Notiz in EN: "{kw}"')
        if kw in de_text:
            issues.append(f'Redaktionelle Notiz in DE: "{kw}"')

    # Englische Sätze in der DE-Spalte?
    en_words_in_de = re.findall(r'\b(the|of|and|that|which|however|therefore|although|because|while)\b', de_text, re.I)
    if len(en_words_in_de) > 5 and len(de_text) > 50:
        issues.append(f'Möglicher englischer Text in DE-Spalte ({len(en_words_in_de)} EN-Wörter gefunden)')

    if issues:
        for iss in issues:
            print(f'  *** PROBLEM: {iss}')
        problems.append((i, issues))

    print()

print('=' * 60)
print(f'ZUSAMMENFASSUNG: {len(problems)} Zeilen mit Problemen')
for row_i, issues in problems:
    print(f'  Zeile {row_i:02d}: {"; ".join(issues)}')
