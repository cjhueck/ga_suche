import zipfile
import re
from lxml import etree
from collections import Counter, defaultdict

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

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        doc_raw = f.read()
    with z.open('word/footnotes.xml') as f:
        fn_raw = f.read()

doc_tree = etree.fromstring(doc_raw)
fn_tree = etree.fromstring(fn_raw)

doc_paras = doc_tree.findall('.//' + w('p'))
fn_paras = fn_tree.findall('.//' + w('p'))

# Volltext und XE-Eintraege
all_text_parts = []
all_xe = []
para_data = []  # (idx, text, xe_list)

for i, p in enumerate(doc_paras):
    text = get_para_text(p)
    instr = get_instr_text(p)
    all_text_parts.append(text)
    xes = re.findall(r'XE\s+"([^"]+)"', instr)
    all_xe.extend(xes)
    para_data.append((i, text, xes))

for i, p in enumerate(fn_paras):
    text = get_para_text(p)
    instr = get_instr_text(p)
    all_text_parts.append(text)
    xes = re.findall(r'XE\s+"([^"]+)"', instr)
    all_xe.extend(xes)

full_text = ' '.join(all_text_parts)

# --- 1. Beitragsstruktur identifizieren ---
# Anhand von Autornamen und Abschnittsmustern
print("=== BEITRAGSSTRUKTUR ===")

contributions = [
    ("Hueck", "Introduction"),
    ("Huneman", "Forms, functions and death"),
    ("Steigerwald", "Agency, Teleology and Normativity"),
    ("Chen", "Chronic vitalism"),
    ("Walsh", "Organisms as ecologically embedded systems"),
    ("Haeck et al.", "Knowing life a function of a function"),
    ("Hueck", "Dynamic Morphology as Explanatory Science"),
    ("Kerkmann", "From Idea to Experience"),
    ("Segall", "Revitalizing the Life Sciences"),
    ("Bembé", "Exploring Mammalian Morphology"),
    ("Holdrege", "Is the Earth Alive"),
    ("Kerkmann", "Epilogue"),
]

# Identifiziere Para-Ranges durch Autorennamen oder spezifische Texte
contrib_markers = {
    "Huneman": [50, 400],      # ca. Paragraphen-Bereich
    "Steigerwald": [400, 680],
    "Chen": [680, 950],
    "Steigerwald/Haeck": [950, 1060],
    "Haeck et al.": [1060, 1530],
    "Hueck_Dyn": [1530, 1750],
    "Kerkmann_Idea": [1750, 1950],
    "Segall": [1950, 2200],
    "Bembe": [2200, 2400],
    "Holdrege": [2400, 3200],
    "Kerkmann_Ep": [3200, 3400],
}

# --- 2. XE-Counter und eindeutige Eintraege ---
xe_counter = Counter(all_xe)
unique_entries = sorted(xe_counter.keys())

by_main = defaultdict(list)
for entry in unique_entries:
    if ':' in entry:
        main, sub = entry.split(':', 1)
        by_main[main.strip()].append(sub.strip())
    else:
        by_main[entry].append('')

print(f"Gesamt XE: {len(all_xe)}, Eindeutig: {len(unique_entries)}")
print()

# --- 3. LUECKENANALYSE: wichtige Begriffe ohne/mit wenig XE ---
print("=== LUECKENANALYSE ===")

# Erweiterte Begriffsliste
candidates = {
    # Schluesselpersonen
    "Aristotle": ("Aristoteles", 1),
    "Descartes": ("Descartes", 1),
    "Harvey": ("Harvey", 1),
    "Wolff, C.F.": ("Caspar Friedrich Wolff", 1),
    "Stahl": ("Stahl", 1),
    "Leibniz": ("Leibniz", 1),
    "Buffon": ("Buffon", 1),
    "Haller": ("Haller", 1),
    "Hegel": ("Hegel", 1),
    "Fichte": ("Fichte", 1),
    "Herder": ("Herder", 1),
    "Ritter": ("Ritter", 1),
    "Oken": ("Oken", 1),
    # Konzepte
    "physiology": ("physiology|Physiologie", 2),
    "generation": ("\\bgeneration\\b", 2),
    "preformation": ("preformation|Präformation", 2),
    "metabolism": ("metabolism|Stoffwechsel", 2),
    "autopoiesis": ("autopoiesis", 2),
    "form": ("\\bform\\b", 5),
    "normativity": ("normativity|Normativität", 2),
    "function": ("\\bfunction\\b", 5),
    "self-organization": ("self.organization", 3),
    "natural selection": ("natural selection", 2),
    "variation": ("\\bvariation\\b", 2),
    "adaptation": ("\\badaptation\\b", 2),
    "homeostasis": ("homeostasis", 1),
    "emergence": ("\\bemergence\\b", 2),
    "complexity": ("\\bcomplexity\\b", 2),
    "information": ("\\binformation\\b", 3),
    "causality": ("causality|causation", 2),
    "finality": ("finality|Finalität", 2),
    "Münchhausen": ("M.nchhausen", 1),
    "irritability": ("irritability", 1),
    "sensibility": ("sensibility", 1),
}

gaps = []
for label, (pattern, min_text_count) in candidates.items():
    text_count = len(re.findall(pattern, full_text, re.IGNORECASE))
    xe_count = sum(v for k, v in xe_counter.items() if re.search(label.split(',')[0].split('/')[0].lower(), k.lower()))
    if text_count >= min_text_count * 5:
        gaps.append((label, text_count, xe_count))

gaps.sort(key=lambda x: x[1], reverse=True)
print(f"{'Begriff':<25} {'Text':>6} {'XE':>6} {'Status'}")
print("-" * 50)
for label, tc, xc in gaps:
    status = "OK" if xc > 3 else ("WENIG" if xc > 0 else "FEHLT")
    print(f"{label:<25} {tc:>6} {xc:>6}   {status}")

print()
# --- 4. CROSS-BEITRAGS-KONSISTENZ ---
print("=== KONSISTENZ-PRUEFUNG (Top-Eintraege) ===")

# Fuer die wichtigsten Eintraege: in welchen Parabereichen kommen sie vor?
key_terms = [
    ("Epigenesis", r"epigenesis"),
    ("Vitalism", r"vitalism"),
    ("Teleology", r"teleolog"),
    ("Organism", r"\borganism\b"),
    ("Kant:natural purposes", r"natural purpose"),
    ("Morphology", r"morpholog"),
]

for xe_label, text_pattern in key_terms:
    # Paragraphen mit XE-Eintrag
    xe_paras = [i for i, text, xes in para_data if any(xe_label.lower() in xe.lower() for xe in xes)]
    # Paragraphen mit Texterwähnung (ohne XE)
    text_paras_no_xe = [i for i, text, xes in para_data
                        if re.search(text_pattern, text, re.IGNORECASE)
                        and not any(xe_label.lower() in xe.lower() for xe in xes)]
    print(f"\n{xe_label}:")
    print(f"  Mit XE:     {len(xe_paras)} Paras {xe_paras[:8]}{'...' if len(xe_paras)>8 else ''}")
    print(f"  Ohne XE:    {len(text_paras_no_xe)} Paras {text_paras_no_xe[:8]}{'...' if len(text_paras_no_xe)>8 else ''}")

print()
# --- 5. UNTEREINTRAGS-HARMONISIERUNG ---
print("=== UNTEREINTRAEGE HARMONISIERUNG ===")

# Aehnliche Untereintraege die vereinheitlicht werden koennten
for main, subs in sorted(by_main.items()):
    if len(subs) > 2 and subs != ['']:
        # Zeige Haupteintraege mit vielen Untereintraegen
        non_empty = [s for s in subs if s]
        if len(non_empty) >= 3:
            print(f"\n{main}:")
            for sub in sorted(non_empty):
                key = f"{main}:{sub}"
                print(f"  - '{sub}' ({xe_counter[key]}x)")

print()
# --- 6. NEUE HAUPTEINTRAEGE Vorschlaege ---
print("=== VORSCHLAEGE NEUE HAUPTEINTRAEGE ===")
new_entries = [
    ("Physiology", "Physiologie/physiology kommt 40x im Text vor, kein Haupteintrag"),
    ("Generation", "'generation' 45x im Text, kein Eintrag"),
    ("Preformation", "Gegenbegriff zu Epigenesis, oft erwaehnt"),
    ("Münchhausen-Trilemma", "Jetzt in Fussnote markiert (neu hinzugefuegt)"),
    ("Normativity", "Zentrales Thema bei Steigerwald, Walsh"),
    ("Adaptation", "Wichtig fuer Evo-Devo Diskussion"),
    ("Homeostasis", "Taucht in mehreren Beitraegen auf"),
    ("Metabolism", "Grundbegriff der Biologie, fehlt im Index"),
]
for entry, reason in new_entries:
    print(f"  {entry}: {reason}")
