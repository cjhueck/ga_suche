import zipfile
import re
from collections import Counter, defaultdict
from lxml import etree

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        raw = f.read()

tree = etree.fromstring(raw)

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def w(tag):
    return '{' + W + '}' + tag

# Alle Paragraphen extrahieren mit Text und XE-Info
paragraphs = tree.findall('.//' + w('p'))

# ---- Identifiziere Beitraege (Ueberschriften) ----
# Ueberschriften sind typischerweise in bestimmten Styles

def get_para_style(p):
    pPr = p.find(w('pPr'))
    if pPr is not None:
        pStyle = pPr.find(w('pStyle'))
        if pStyle is not None:
            return pStyle.get(w('val'), '')
    return ''

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

# Finde Ueberschriften-Styles
print("=== DOKUMENTSTRUKTUR: UEBERSCHRIFTEN ===")
heading_styles = set()
for p in paragraphs:
    style = get_para_style(p)
    if style and ('Heading' in style or 'heading' in style or 'berschrift' in style or 'Title' in style or 'title' in style):
        heading_styles.add(style)
        
print("Gefundene Heading-Styles:", heading_styles)
print()

# Zeige alle Heading-1 Paragraphen (Beitragstitel)
print("=== BEITRAGSTITEL (Heading-Styles) ===")
for p in paragraphs:
    style = get_para_style(p)
    if style in heading_styles:
        text = get_para_text(p)
        if text.strip():
            print(f"  [{style}] {text.strip()[:100]}")

print()

# ---- Epigenesis-Analyse: wo fehlen XE-Tags? ----
print("=== EPIGENESIS-ANALYSE ===")
print("Paragraphen mit 'epigenesis' im Text:")
print()

epi_count_with_xe = 0
epi_count_without_xe = 0
missing_xe_paras = []

for i, p in enumerate(paragraphs):
    text = get_para_text(p)
    instr = get_instr_text(p)
    
    has_epi_text = bool(re.search(r'[Ee]pigenesis|[Ee]pigenese', text))
    has_epi_xe = bool(re.search(r'[Ee]pigenesis|[Ee]pigenese', instr))
    
    if has_epi_text:
        if has_epi_xe:
            epi_count_with_xe += 1
            print(f"  [Para {i}] MIT XE: {text[:120].strip()}")
        else:
            epi_count_without_xe += 1
            print(f"  [Para {i}] OHNE XE: {text[:120].strip()}")
            missing_xe_paras.append(i)

print()
print(f"Mit XE-Tag: {epi_count_with_xe}")
print(f"Ohne XE-Tag: {epi_count_without_xe}")
print(f"Fehlende XE-Tags in Paragraphen: {missing_xe_paras}")

# ---- Index-Lueckenanalyse: haeufige Begriffe ohne XE ----
print()
print("=== HAEUFIGE SCHLUESSELWOERTER IM TEXT OHNE XE-EINTRAG ===")

# Schluesselbegriffe die relevant sein koennten
keywords = [
    'preformation', 'Präformation', 'Bildungstrieb', 'Naturphilosophie',
    'vitalism', 'teleology', 'morphology', 'physiology', 'organism',
    'epigenesis', 'autopoiesis', 'metabolism', 'Treviranus', 'Ritter',
    'Oken', 'Girtanner', 'Wolff', 'Harvey', 'generation', 'embryo',
    'irritability', 'sensibility', 'reproduction',
]

all_text = ' '.join([get_para_text(p) for p in paragraphs])
all_instr = ' '.join([get_instr_text(p) for p in paragraphs])

for kw in keywords:
    text_count = len(re.findall(kw, all_text, re.IGNORECASE))
    xe_count = len(re.findall(kw, all_instr, re.IGNORECASE))
    if text_count > 5 and xe_count == 0:
        print(f"  '{kw}': {text_count}x im Text, {xe_count}x im Index -> FEHLT")
    elif text_count > 5:
        print(f"  '{kw}': {text_count}x im Text, {xe_count}x im Index")
