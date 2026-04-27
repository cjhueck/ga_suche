import zipfile
from lxml import etree

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        raw = f.read()

tree = etree.fromstring(raw)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

paragraphs = tree.findall('.//' + w('p'))

# Para 164 hat XE "Embryology:epigenesis" - zeige vollstaendiges XML
print("=== Para 164 vollstaendiges XML ===")
p = paragraphs[164]
xml_str = etree.tostring(p, pretty_print=True).decode('utf-8')
# Nur die relevanten Teile zeigen - suche den XE-Teil
lines = xml_str.split('\n')
for i, line in enumerate(lines):
    if 'instrText' in line or 'fldChar' in line or 'vanish' in line:
        # Zeige Kontext
        start = max(0, i-3)
        end = min(len(lines), i+4)
        for j in range(start, end):
            print(f"  {j:3}: {lines[j]}")
        print("  ---")

print()
print("=== Para 983 vollstaendiges XML (Epigenesis standalone) ===")
p = paragraphs[983]
xml_str = etree.tostring(p, pretty_print=True).decode('utf-8')
lines = xml_str.split('\n')
for i, line in enumerate(lines):
    if 'instrText' in line or 'fldChar' in line or 'vanish' in line:
        start = max(0, i-3)
        end = min(len(lines), i+4)
        for j in range(start, end):
            print(f"  {j:3}: {lines[j]}")
        print("  ---")
