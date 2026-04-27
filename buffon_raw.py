"""Zeigt alle Buffon-Absätze mit rohem Text inkl. Sonderzeichen."""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS = {
    '0': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx',
    '1': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx',
}

for kap, path in CHAPTERS.items():
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)

    print(f'\n{"="*65}')
    print(f'KAPITEL {kap}')
    print(f'{"="*65}')

    for i, row in enumerate(rows):
        cells = re.findall(r'<w:tc>.*?</w:tc>', row, re.DOTALL)
        texts = []
        for cell in cells[:2]:
            paras = re.findall(r'<w:p[ >].*?</w:p>', cell, re.DOTALL)
            cell_text = ''
            for p in paras:
                t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL))
                cell_text += t + ' '
            texts.append(cell_text.strip())

        en, de = texts[0] if texts else '', texts[1] if len(texts) > 1 else ''

        if 'Buffon' in en or 'Buffon' in de:
            print(f'\n[Zeile {i:02d}]')
            # Zeige EN-Zitate (original)
            en_quotes = re.findall(r'["\u201c\u2018\xab\u203a\u2039](.*?)["\u201d\u2019\xbb\u203a\u2039]', en)
            de_quotes = re.findall(r'[„\u201e\u2018\xab\u203a\u2039\u00bb](.*?)["\u201c\u201d\u2019\xbb\u203a\u2039\u00ab]', de)
            print(f'  EN: {en[:300]}')
            print(f'  DE: {de[:300]}')
            # Sonderzeichen anzeigen
            special_en = [(j, c, hex(ord(c))) for j, c in enumerate(en) if ord(c) > 127 and ord(c) < 10000][:20]
            special_de = [(j, c, hex(ord(c))) for j, c in enumerate(de) if ord(c) > 127 and ord(c) < 10000][:20]
            if any(hex(ord(c)) in ['0x201e', '0x201c', '0x2039', '0x203a', '0xab', '0xbb', '0x2018', '0x2019']
                   for _, c, _ in special_de):
                print(f'  Anführungszeichen in DE: {[(c, h) for _, c, h in special_de if h in ["0x201e","0x201c","0x2039","0x203a","0xab","0xbb","0x2018","0x2019"]]}')
