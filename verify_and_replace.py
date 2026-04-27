import zipfile
import re
from lxml import etree
from collections import Counter

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_FINAL.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        content = f.read().decode('utf-8')

xe_all = re.findall(r'XE\s+"([^"]+)"', content)
xe_counter = Counter(xe_all)

print(f"=== VERIFIKATION FINALE DATEI ===")
print(f"Gesamt XE-Tags: {len(xe_all)}")
print(f"Eindeutige Eintraege: {len(xe_counter)}")
print()

# Prüfe neue Eintraege
new_expected = [
    'Physiology', 'Generation', 'Preformation', 'Embryology:preformation',
    'Descartes', 'Hegel', 'Herder', 'Buffon', 'Oken',
    'Vitalism', 'Adaptation', 'Normativity', 'Teleology:return in biology',
    'Münchhausen-Trilemma',  # in footnotes - wird separat gezaehlt
]

print("=== NEUE EINTRAEGE (Verifikation) ===")
for entry in new_expected:
    count = xe_counter.get(entry, 0)
    status = "OK" if count > 0 else "FEHLT (ggf. in footnotes.xml)"
    print(f"  {entry}: {count}x  [{status}]")

print()
print("=== TOP 20 HAEUFIGSTE EINTRAEGE ===")
for entry, count in xe_counter.most_common(20):
    print(f"  {count:4}x  {entry}")

print()
print("=== ALPHABETISCH (Auszug neue Eintraege) ===")
new_entries_found = sorted([k for k in xe_counter.keys() 
                             if any(n.lower() in k.lower() for n in 
                                    ['Physiology', 'Generation', 'Preformation', 'Descartes',
                                     'Hegel', 'Herder', 'Buffon', 'Oken', 'Vitalism', 
                                     'Adaptation', 'Normativity'])])
for e in new_entries_found:
    print(f"  {xe_counter[e]:4}x  {e}")
