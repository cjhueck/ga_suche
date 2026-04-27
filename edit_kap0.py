"""
Bereinigt 0 Einleitung_fertig_DN_CH.docx und speichert als _2026.docx.
Änderungen:
  1. Abs. [18]: " add endnote here. This endnote should read:" entfernen
  2. Abs. [19]: Sullivan-Endnotentext löschen
  3. Abs. [35]: Redundante Schlegel-Passage löschen
  4. Abs. [40]: "Add the following in a NEW PARAGRAPH." löschen
  5. Abs. [86]: Textteil ab " DELETE Thus although" entfernen
  6. Abs. [87]: "CHANGE TO: " Präfix entfernen → sauberer EN-Absatz
"""
import zipfile, re, sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'

# -----------------------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------------------

def para_text(p_xml):
    """Extrahiert den zusammengesetzten Text eines <w:p>-Elements."""
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p_xml, re.DOTALL)
    return ''.join(runs)

def set_para_text(p_xml, new_text):
    """
    Ersetzt den gesamten Textinhalt eines Paragraphen durch new_text,
    indem alle w:r-Elemente bis auf das erste gelöscht und das erste
    auf new_text gesetzt wird. Formatierung des ersten Runs bleibt erhalten.
    """
    # Ersten Run mit seinem rPr finden
    first_run_m = re.search(r'(<w:r[^>]*>)(.*?)(</w:r>)', p_xml, re.DOTALL)
    if not first_run_m:
        return p_xml  # Nichts zu tun

    # rPr (Formatierung) aus erstem Run extrahieren
    rpr_m = re.search(r'(<w:rPr>.*?</w:rPr>)', first_run_m.group(2), re.DOTALL)
    rpr = rpr_m.group(1) if rpr_m else ''

    # Neuen Run aufbauen
    new_run = f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(new_text)}</w:t></w:r>'

    # Alle alten w:r-Elemente entfernen
    p_body = re.sub(r'<w:r[ >].*?</w:r>', '', p_xml, flags=re.DOTALL)

    # Neuen Run vor </w:p> einfügen
    p_body = p_body.replace('</w:p>', new_run + '</w:p>')
    return p_body

def _esc(text):
    """XML-Sonderzeichen escapen."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

# -----------------------------------------------------------------------
# Dokument laden
# -----------------------------------------------------------------------
shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    other_files = {name: z.read(name) for name in z.namelist() if name != 'word/document.xml'}

# Alle <w:p>-Elemente extrahieren (mit Position)
para_pattern = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)
paras = list(para_pattern.finditer(xml))

print(f'Paragraphen gesamt: {len(paras)}')

# Index-Lookup: Index → Originaltext
para_texts = [para_text(m.group()) for m in paras]

# -----------------------------------------------------------------------
# Zielabsätze identifizieren
# -----------------------------------------------------------------------

def find_para(search_str, start=0):
    """Findet den Index des Paragraphen, der search_str enthält."""
    for i in range(start, len(para_texts)):
        if search_str in para_texts[i]:
            return i
    return -1

idx18 = find_para('add endnote here. This endnote should read:')
idx19 = find_para('as Heather Sullivan has done')
idx35 = find_para('Kunstwerden')
idx40 = find_para('Add the following in a NEW PARAGRAPH')
idx86 = find_para('DELETE Thus although')
idx87 = find_para('CHANGE TO: Thus, the parts of an oak tree')

print(f'\nGefundene Absatz-Indizes:')
print(f'  [18] Endnotenhinweis:    {idx18}')
print(f'  [19] Sullivan-Text:      {idx19}')
print(f'  [35] Kunstwerden:        {idx35}')
print(f'  [40] Add following:      {idx40}')
print(f'  [86] DELETE Thus:        {idx86}')
print(f'  [87] CHANGE TO oak tree: {idx87}')

all_found = all(i >= 0 for i in [idx18, idx19, idx35, idx40, idx86, idx87])
if not all_found:
    print('\nFEHLER: Nicht alle Absätze gefunden! Abbruch.')
    sys.exit(1)

# -----------------------------------------------------------------------
# Änderungen vorbereiten: XML-Strings der Paragraphen modifizieren
# -----------------------------------------------------------------------
changes = {}  # idx → ('delete'|'replace', new_xml_or_None)

# 1. Abs [18]: " add endnote here. This endnote should read:" entfernen
orig18 = paras[idx18].group()
text18 = para_texts[idx18]
clean18 = text18.replace(' add endnote here. This endnote should read:', '').rstrip()
# Text sauber neu setzen
new18 = set_para_text(orig18, clean18)
changes[idx18] = ('replace', new18)
print(f'\n[18] Bereinigt: ...{clean18[-80:]}')

# 2. Abs [19]: Sullivan-Endnotentext löschen
changes[idx19] = ('delete', None)
print(f'[19] Gelöscht: {para_texts[idx19][:80]}...')

# 3. Abs [35]: Kunstwerden-Absatz löschen
changes[idx35] = ('delete', None)
print(f'[35] Gelöscht: {para_texts[idx35][:80]}...')

# 4. Abs [40]: "Add the following in a NEW PARAGRAPH." löschen
changes[idx40] = ('delete', None)
print(f'[40] Gelöscht: {para_texts[idx40][:80]}...')

# 5. Abs [86]: Alles ab " DELETE Thus although" entfernen
orig86 = paras[idx86].group()
text86 = para_texts[idx86]
cut_pos = text86.find(' DELETE Thus although')
if cut_pos < 0:
    cut_pos = text86.find('DELETE Thus')
clean86 = text86[:cut_pos].rstrip()
new86 = set_para_text(orig86, clean86)
changes[idx86] = ('replace', new86)
print(f'\n[86] Bereinigt (Ende): ...{clean86[-80:]}')

# 6. Abs [87]: "CHANGE TO: " Präfix entfernen
orig87 = paras[idx87].group()
text87 = para_texts[idx87]
clean87 = re.sub(r'^CHANGE TO:\s*', '', text87).strip()
new87 = set_para_text(orig87, clean87)
changes[idx87] = ('replace', new87)
print(f'[87] Bereinigt (Anfang): {clean87[:80]}...')

# -----------------------------------------------------------------------
# XML neu zusammensetzen
# -----------------------------------------------------------------------
# Gehe durch alle Paragraphen und baue neues XML
new_xml_parts = []
prev_end = 0

for i, m in enumerate(paras):
    # Bereich vor diesem Paragraphen hinzufügen
    new_xml_parts.append(xml[prev_end:m.start()])

    if i in changes:
        action, new_content = changes[i]
        if action == 'delete':
            pass  # Nichts hinzufügen
        else:
            new_xml_parts.append(new_content)
    else:
        new_xml_parts.append(m.group())

    prev_end = m.end()

# Rest nach letztem Paragraphen
new_xml_parts.append(xml[prev_end:])

new_xml = ''.join(new_xml_parts)

# -----------------------------------------------------------------------
# Ergebnis validieren
# -----------------------------------------------------------------------
new_paras = list(para_pattern.finditer(new_xml))
print(f'\nErgebnis: {len(new_paras)} Absätze (vorher: {len(paras)}, Δ = {len(paras)-len(new_paras)} gelöscht)')

# Prüfe ob Editorial-Strings noch vorhanden
checks = [
    ('add endnote here', 'Endnotenhinweis'),
    ('Kunstwerden', 'Kunstwerden-Typo'),
    ('Add the following in a NEW PARAGRAPH', 'Add following'),
    ('DELETE Thus', 'DELETE-Marker'),
    ('CHANGE TO:', 'CHANGE TO'),
]
print('\nRestprüfung:')
for search, label in checks:
    found = search in new_xml
    status = '✗ NOCH VORHANDEN!' if found else '✓ entfernt'
    print(f'  {label}: {status}')

# Sullivan-Text-Prüfung
sullivan_found = 'as Heather Sullivan has done' in new_xml
print(f'  Sullivan-Text: {"✗ NOCH VORHANDEN!" if sullivan_found else "✓ entfernt"}')

# -----------------------------------------------------------------------
# Datei speichern
# -----------------------------------------------------------------------
with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other_files.items():
        zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')
