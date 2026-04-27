import zipfile
import re
from lxml import etree

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

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

def search_in_file(z, filename, label):
    print(f"=== Suche in {label} ===")
    try:
        with z.open(filename) as f:
            raw = f.read()
        # Rohsuche
        raw_str = raw.decode('utf-8', errors='replace')
        if 'nchhausen' in raw_str or 'Trilemma' in raw_str:
            print(f"  -> Treffer in Rohtext!")
            # Finde Kontext
            for m in re.finditer(r'.{0,80}(nchhausen|Trilemma).{0,80}', raw_str):
                print(f"  Kontext: {m.group(0)[:200]}")
        else:
            print(f"  -> Kein Treffer")
    except Exception as e:
        print(f"  -> Datei nicht vorhanden: {e}")
    print()

with zipfile.ZipFile(path, 'r') as z:
    files = z.namelist()
    print("Dateien im DOCX:")
    for f in files:
        print(f"  {f}")
    print()
    
    search_in_file(z, 'word/document.xml', 'document.xml')
    search_in_file(z, 'word/footnotes.xml', 'footnotes.xml')
    search_in_file(z, 'word/endnotes.xml', 'endnotes.xml')
