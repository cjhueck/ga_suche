"""Extrahiert alle Buffon-Zitate (mit direkter Rede) aus Kap. 0 und 1."""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS = {
    '0': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx',
    '1': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx',
}

# Alle Anführungszeichen-Varianten
QUOTE_RE = re.compile(r'[„»›«‹"\'](.*?)[""«‹›\'"]', re.DOTALL)

def get_rows(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)
    result = []
    for row in rows:
        cells = re.findall(r'<w:tc>.*?</w:tc>', row, re.DOTALL)
        en_paras, de_paras = [], []
        for j, cell in enumerate(cells[:2]):
            paras = re.findall(r'<w:p[ >].*?</w:p>', cell, re.DOTALL)
            for p in paras:
                t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip()
                if t:
                    (en_paras if j == 0 else de_paras).append(t)
        result.append((en_paras, de_paras))
    return result

for kap, path in CHAPTERS.items():
    rows = get_rows(path)
    print(f'\n{"="*65}')
    print(f'KAPITEL {kap} – Buffon-Zitate (direkte Rede)')
    print(f'{"="*65}')
    for i, (en_p, de_p) in enumerate(rows):
        en = ' '.join(en_p)
        de = ' '.join(de_p)
        if 'Buffon' not in en and 'Buffon' not in de and 'Histoire naturelle' not in en:
            continue
        # Zitate in EN
        en_quotes = [q for q in QUOTE_RE.findall(en) if len(q) > 15]
        de_quotes = [q for q in QUOTE_RE.findall(de) if len(q) > 15]
        # Referenzen
        refs = re.findall(r'(?:vol\.|Bd\.|S\.|p\.)\s*\d+[^,;)]{0,30}', en + de, re.I)

        if en_quotes or de_quotes:
            print(f'\n[Zeile {i:02d}]')
            for q in en_quotes:
                print(f'  EN-Zitat: „{q[:150]}"')
            for q in de_quotes:
                print(f'  DE-Zitat: „{q[:150]}"')
            if refs:
                print(f'  Refs: {refs[:5]}')
            print(f'  EN-Kontext: {en[:200]}')
            print(f'  DE-Kontext: {de[:200]}')
