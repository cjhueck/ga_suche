"""
Analysiert Kapitel 1: Tabellenstruktur, Vollständigkeit der DE-Übersetzung,
redaktionelle Notizen, Probleme.
"""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
print(f'Tabellen: {len(tables)}')

row_re  = re.compile(r'<w:tr[ >].*?</w:tr>', re.DOTALL)
cell_re = re.compile(r'<w:tc>.*?</w:tc>', re.DOTALL)
para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)

def cell_paras(cell_xml):
    paras = para_re.findall(cell_xml)
    result = []
    for p in paras:
        runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
        text = ''.join(runs).strip()
        if text:
            result.append(text)
    return result

EDIT_MARKERS = ['add endnote', 'ADD ENDNOTE', 'DELETE', 'CHANGE TO', 'CHANGE to',
                'Add the following', 'This endnote should', 'INSERT', 'REMOVE',
                'add footnote', 'ADD FOOTNOTE', 'NOTE TO', 'NOTE:']

problems = []
total_rows = 0

for tbl_idx, tbl in enumerate(tables):
    rows = row_re.findall(tbl)
    print(f'\n=== TABELLE {tbl_idx} ({len(rows)} Zeilen) ===')
    total_rows += len(rows)

    for i, row in enumerate(rows):
        cells = cell_re.findall(row)
        en_paras = cell_paras(cells[0]) if len(cells) > 0 else []
        de_paras = cell_paras(cells[1]) if len(cells) > 1 else []

        en_text = ' '.join(en_paras)
        de_text = ' '.join(de_paras)

        issues = []

        if not de_paras and en_paras:
            issues.append('KEINE ÜBERSETZUNG')
        elif len(de_paras) < len(en_paras) - 1:
            issues.append(f'DE ({len(de_paras)}) deutlich weniger Abs. als EN ({len(en_paras)})')

        for kw in EDIT_MARKERS:
            if kw in en_text:
                issues.append(f'Redakt. Notiz EN: "{kw}"')
            if kw in de_text:
                issues.append(f'Redakt. Notiz DE: "{kw}"')

        # Englische Wörter in DE-Spalte (möglicher nicht übersetzter Text)
        if de_text and len(de_text) > 100:
            en_words = re.findall(r'\b(the|of|and|that|which|however|therefore|although|because|while|thus|since|whether|between|through|within|without|during|before|after|beyond|both|each|only|still|already|often|here|there|where|when|what|how|this|these|those|their|them|they|will|would|could|should|might|have|has|been|were|are|was|not|but|for|with|from|into|onto|upon|over|under|about|above|below)\b',
                                   de_text, re.I)
            if len(en_words) > 8:
                issues.append(f'Mögl. EN-Text in DE ({len(en_words)} EN-Wörter)')

        if issues:
            print(f'\n  [Zeile {i:02d}] *** PROBLEME: {"; ".join(issues)}')
            print(f'    EN: {en_text[:150]}')
            print(f'    DE: {de_text[:150]}')
            problems.append((tbl_idx, i, issues, en_paras, de_paras))
        else:
            # Nur erste/letzte anzeigen zur Orientierung
            if i == 0 or (i < 3):
                print(f'  [Zeile {i:02d}] EN: {en_text[:80]} | DE: {de_text[:80]}')

print(f'\n{"="*60}')
print(f'ZUSAMMENFASSUNG: {len(tables)} Tabellen, {total_rows} Zeilen, {len(problems)} Probleme')
for tbl_i, row_i, issues, en_p, de_p in problems:
    print(f'\n  Tabelle {tbl_i}, Zeile {row_i:02d}: {"; ".join(issues)}')
    for p in en_p:
        print(f'    EN| {p[:120]}')
    for p in de_p:
        print(f'    DE| {p[:120]}')
