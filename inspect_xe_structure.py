import zipfile
import re
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

# Zeige XML eines Paragraphen MIT XE-Tag (para 979)
print("=== XML von Para 979 (MIT XE Epigenesis) ===")
p = paragraphs[979]
print(etree.tostring(p, pretty_print=True).decode('utf-8')[:3000])

print()
print("=== XML von Para 1404 (OHNE XE, Keyword-Liste Haeck) ===")
p = paragraphs[1404]
print(etree.tostring(p, pretty_print=True).decode('utf-8')[:3000])

print()
print("=== XML von Para 1445 (OHNE XE, Abschnittstitel Haeck) ===")
p = paragraphs[1445]
print(etree.tostring(p, pretty_print=True).decode('utf-8')[:3000])
