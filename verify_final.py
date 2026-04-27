import zipfile, re
from collections import Counter

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

with zipfile.ZipFile(path, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')

xe = re.findall(r'XE "([^"]+)"', doc + fn)
c = Counter(xe)

checks = [
    ('Kant:organism and purposiveness',                   '== 110 (harmonisiert)'),
    ('Kant:natural purposes',                             '== 0 (entfernt)'),
    ('Vitalism:historical context',                       '== 11 (harmonisiert)'),
    ('Vitalism:historical tradition',                     '== 0 (entfernt)'),
    ('Physiology',                                        '== 38 (neu)'),
    ('Metabolism',                                        '== 4 (neu)'),
    ('Kielmeyer:reproduction, irritability, and sensibility', '== 12 (korrigiert)'),
    ('Excitability:Brown, Humboldt, and Treviranus',      '== 19 (korrigiert)'),
    ('Epigenesis',                                        '== 5 (neu)'),
    ('Munchhausen-Trilemma',                              'in footnotes'),
    ('Life:conditions of cognition',                      '== 0 (geloescht)'),
]

print(f'Datei: ...Cognizing Life...docx')
print(f'Gesamt XE-Tags: {len(xe)}  |  Eindeutige Eintraege: {len(c)}')
print()
print(f"{'Eintrag':<55} {'Ist':>5}  Erwartung")
print('-' * 80)
for entry, expected in checks:
    count = c.get(entry, c.get(entry.replace('ü','u'), 0))
    ok = 'OK' if count > 0 or '== 0' in expected else '?'
    if '== 0' in expected:
        ok = 'OK' if count == 0 else 'FEHLER'
    print(f"  {entry:<53} {count:>5}x  {expected}  [{ok}]")
