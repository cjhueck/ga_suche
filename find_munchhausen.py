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

def get_para_text(p):
    texts = []
    for r in p.iter(w('r')):
        for t in r.findall(w('t')):
            if t.text:
                texts.append(t.text)
    return ''.join(texts)

def get_instr_text(p):
    texts = []
    for instr in p.iter(w('instrText')):
        if instr.text:
            texts.append(instr.text)
    return ''.join(texts)

print("=== Suche nach Münchhausen ===")
for i, p in enumerate(paragraphs):
    text = get_para_text(p)
    if re.search(r'[Mm]\u00fcnch|[Mm]unchhausen|[Mm]\u00fcnchhausen|Trilemma', text, re.IGNORECASE):
        instr = get_instr_text(p)
        has_xe = 'XE' in instr
        print(f"Para {i}: {'MIT XE' if has_xe else 'OHNE XE'}")
        print(f"  Text: {text[:200]}")
        if instr:
            print(f"  XE:   {instr[:200]}")
        print()
