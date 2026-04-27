"""
Extrahiert alle direkten Zitate aus Kap. 1 (DE + EN nebeneinander)
mit Quellenangaben, sortiert nach Autor.
"""
import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\1 Die Bühne bereiten_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

tables = re.findall(r'<w:tbl>.*?</w:tbl>', xml, re.DOTALL)
rows   = re.findall(r'<w:tr[ >].*?</w:tr>', tables[0], re.DOTALL)

def cell_paras(cell_xml):
    paras = re.findall(r'<w:p[ >].*?</w:p>', cell_xml, re.DOTALL)
    out = []
    for p in paras:
        t = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)).strip()
        if t:
            out.append(t)
    return out

# Alle Anführungszeichen-Varianten (direkte Zitate)
QUOTE_RE = re.compile(
    r'(?:'
    r'[„\u201e](.*?)["\u201c\u201d]'   # „..." oder „..."
    r'|[»\xbb](.*?)[«\xab]'            # »...«
    r'|[›\u203a](.*?)[‹\u2039]'        # ›...‹
    r'|["\u2018\u2019](.*?)["\u2018\u2019]'  # '...' oder "..."
    r')',
    re.DOTALL
)

def find_quotes(text):
    results = []
    for m in QUOTE_RE.finditer(text):
        q = next((g for g in m.groups() if g is not None), '')
        if len(q.strip()) > 8:
            results.append(q.strip())
    return results

# Quellreferenzen erkennen
REF_RE = re.compile(
    r'(?:'
    r'AA\s+\d+[,\s]+\d+'               # Kant AA
    r'|KU\s+[§\d]+'                    # Kritik der Urteilskraft
    r'|KrV\s+[AB]\s*\d+'              # Kritik der reinen Vernunft
    r'|KFSA\s+\d+'                     # Schlegel
    r'|Buffon[^.;,)]{0,60}'           # Buffon
    r'|Histoire naturelle[^.;,)]{0,40}'
    r'|Herder[^.;,)]{0,40}'
    r'|Ideen[^.;,)]{0,40}'
    r'|Wolff[^.;,)]{0,30}'
    r'|Diderot[^.;,)]{0,30}'
    r'|Kant[^.;,)]{0,40}'
    r')',
    re.I
)

# Sammle alle Zeilen mit Zitaten
print('=== ALLE DIREKTZITATE IN KAP. 1 ===\n')
print(f'{"Nr":>3}  {"Quelle":<12}  {"EN-Zitat":<55}  {"DE-Zitat":<55}')
print('-' * 130)

nr = 0
for i, row in enumerate(rows):
    cells = re.findall(r'<w:tc>.*?</w:tc>', row, re.DOTALL)
    en_p = cell_paras(cells[0]) if cells else []
    de_p = cell_paras(cells[1]) if len(cells) > 1 else []
    en = ' '.join(en_p)
    de = ' '.join(de_p)

    en_quotes = find_quotes(en)
    de_quotes = find_quotes(de)

    if not en_quotes and not de_quotes:
        continue

    # Quelle bestimmen
    refs = REF_RE.findall(en + ' ' + de)
    quelle = refs[0][:12] if refs else '?'

    # Paare zusammenstellen (EN + DE)
    max_len = max(len(en_quotes), len(de_quotes))
    for j in range(max_len):
        enq = en_quotes[j] if j < len(en_quotes) else ''
        deq = de_quotes[j] if j < len(de_quotes) else ''
        if len(enq) < 5 and len(deq) < 5:
            continue
        nr += 1
        print(f'[{nr:>3}] Z{i:02d} {quelle:<12}')
        print(f'       EN: {enq[:120]}')
        print(f'       DE: {deq[:120]}')
        print()

print(f'\nGesamt: {nr} Direktzitate')
