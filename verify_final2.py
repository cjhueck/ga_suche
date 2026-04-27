import zipfile, re
from collections import Counter

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_verify.docx'

with zipfile.ZipFile(path, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')

xe = re.findall(r'XE "([^"]+)"', doc + fn)
c = Counter(xe)

checks = [
    ('Kant:organism and purposiveness',                       '== 110 (harmonisiert)'),
    ('Kant:natural purposes',                                 '== 0 (entfernt)'),
    ('Vitalism:historical context',                           '== 11 (harmonisiert)'),
    ('Vitalism:historical tradition',                         '== 0 (entfernt)'),
    ('Physiology',                                            '== 38 (neu)'),
    ('Metabolism',                                            '== 4 (neu)'),
    ('Kielmeyer:reproduction, irritability, and sensibility', '== 12 (korrigiert)'),
    ('Excitability:Brown, Humboldt, and Treviranus',          '== 19 (korrigiert)'),
    ('Epigenesis',                                            '== 5 (neu)'),
    ('Life:conditions of cognition',                          '== 0 (geloescht)'),
]

print(f'Gesamt XE-Tags: {len(xe)}  |  Eindeutige Eintraege: {len(c)}')
print()
print(f"{'Eintrag':<55} {'Ist':>5}  Soll")
print('-' * 85)
for entry, expected in checks:
    count = c.get(entry, 0)
    if '== 0' in expected:
        ok = 'OK' if count == 0 else 'FEHLER'
    else:
        ok = 'OK' if count > 0 else 'FEHLER'
    print(f"  {entry:<53} {count:>5}x  {expected}  [{ok}]")

# Munchhausen separat (Sonderzeichen)
m_count = sum(v for k, v in c.items() if 'nchhausen' in k.lower())
print(f"  {'Munchhausen-Trilemma (Fussnote)':<53} {m_count:>5}x  == 1 (neu)  [{'OK' if m_count > 0 else 'FEHLER'}]")
