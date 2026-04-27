"""
Extrahiert alle Zitate mit Quellenangaben aus Kap. 0 und Kap. 1 (DE-Spalte).
Identifiziert Buffon, Kant (AA), Schlegel (KFSA), Goethe, Herder, Humboldt.
"""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

CHAPTERS = {
    '0': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx',
    '1': r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx',
}

def get_de_texts(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
    if not tables:
        return []
    rows = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)
    texts = []
    for row in rows:
        cells = re.findall(r'<w:tc>.*?</w:tc>', row, re.DOTALL)
        if len(cells) < 2:
            continue
        paras = re.findall(r'<w:p[ >].*?</w:p>', cells[1], re.DOTALL)
        for p in paras:
            runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
            t = ''.join(runs).strip()
            if t:
                texts.append(t)
    return texts

# Zitatmuster: Text in „..." oder »...« oder "..."
QUOTE_RE = re.compile(r'[„»"\'](.*?)[""«\'"]', re.DOTALL)

# Quellenreferenzen: (Buffon ...), (AA 5, ...), (KFSA ...), etc.
REF_RE = re.compile(r'\([^)]{3,80}(?:Bd\.|vol\.|S\.|p\.|AA|KFSA|FA|HA|LA|WA)[^)]{0,60}\)', re.I)

# Buffon-spezifisch
BUFFON_RE = re.compile(r'(?:Buffon|Histoire naturelle)[^.;]{0,200}[.;]', re.I)

all_quotes = {}

for kap, path in CHAPTERS.items():
    texts = get_de_texts(path)
    full_text = ' '.join(texts)

    print(f'\n{"="*60}')
    print(f'KAPITEL {kap}')
    print(f'{"="*60}')

    # Alle Zitate (in Anführungszeichen) mit Kontext
    print('\n--- ZITATE IN ANFÜHRUNGSZEICHEN ---')
    for t in texts:
        quotes = QUOTE_RE.findall(t)
        refs   = REF_RE.findall(t)
        if quotes or refs:
            for q in quotes:
                if len(q) > 10:
                    # Buffon?
                    marker = ''
                    if any(kw in t for kw in ['Buffon', 'Histoire naturelle']):
                        marker = ' [BUFFON]'
                    elif 'AA ' in t:
                        marker = ' [KANT-AA]'
                    elif 'KFSA' in t:
                        marker = ' [SCHLEGEL]'
                    elif any(kw in t for kw in ['Goethe', 'FA ', 'WA ', 'HA ']):
                        marker = ' [GOETHE]'
                    elif 'Herder' in t:
                        marker = ' [HERDER]'
                    elif 'Humboldt' in t:
                        marker = ' [HUMBOLDT]'
                    print(f'{marker} „{q[:120]}"')
                    # Quellenangabe
                    for r in refs:
                        print(f'       Quelle: {r}')
                    # Kontext
                    print(f'       Kontext: ...{t[max(0,t.find(q)-30):t.find(q)+len(q)+30]}...')
                    print()

    # Alle Buffon-Stellen
    print('\n--- ALLE BUFFON-STELLEN ---')
    for t in texts:
        if 'Buffon' in t or 'Histoire naturelle' in t:
            print(f'  > {t[:200]}')
            print()
