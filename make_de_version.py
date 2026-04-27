"""
Erstellt eine rein deutsche Version der Einleitung.
Behält: deutsche Absätze + deutsche Überschriften.
Entfernt: alle englischen Absätze.
Speichert als: 0 Einleitung_DE_2026.docx
"""
import zipfile, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')

SRC  = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'
DEST = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_DE_2026.docx'

# -----------------------------------------------------------------------
# Spracherkennung
# -----------------------------------------------------------------------
EN_WORDS = {'the','of','in','and','to','a','is','that','it','for','this','with','as','was','are',
            'by','from','at','be','an','or','but','not','we','i','which','have','has','on','its',
            'their','they','our','what','can','more','also','than','when','if','would','such',
            'rather','thus','however','these','those','were','been','him','her','who','will','do',
            'did','may','might','should','could','he','she','his','one','while','since','although',
            'between','through','both','each','only','just','still','already','often','here'}
DE_WORDS = {'die','der','das','ist','ein','eine','und','zu','des','dem','den','sich','nicht','er',
            'sie','es','wir','auf','mit','als','von','an','im','dass','auch','aber','bei','nach',
            'zum','zur','wie','oder','so','durch','wird','hat','werden','sind','kann','diese',
            'dieser','dieses','jedoch','daher','dabei','sondern','wenn','nur','noch','schon',
            'dann','hier','wobei','indem','doch','wurde','waren','welche','welcher','welches',
            'ihren','ihrem','ihrer','jene','jener','solche','solcher','vielmehr','insofern'}

def lang(text):
    """Gibt 'en', 'de' oder None zurück."""
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 4:
        # Kurze Titel: Deutsch-Indiz = Umlaute oder deutsche Wörter
        has_umlaut = bool(re.search(r'[äöüßÄÖÜ]', text))
        has_de_word = any(w in DE_WORDS for w in words)
        has_en_word = any(w in EN_WORDS for w in words)
        if has_umlaut or has_de_word:
            return 'de'
        if has_en_word:
            return 'en'
        # Wortlisten für bekannte Überschriften
        if text.strip() in ('Introduction', 'Finding Romantic Empiricism'):
            return 'en'
        if text.strip() in ('Einleitung', 'Den romantischen Empirismus entdecken'):
            return 'de'
        return None
    en = sum(1 for w in words if w in EN_WORDS)
    de = sum(1 for w in words if w in DE_WORDS)
    de += len(re.findall(r'[äöüßÄÖÜ]', text)) * 1.5
    if en + de == 0:
        return None
    return 'en' if en > de else 'de'

# -----------------------------------------------------------------------
# XML laden
# -----------------------------------------------------------------------
shutil.copy2(SRC, DEST)

with zipfile.ZipFile(DEST, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    other_files = {n: z.read(n) for n in z.namelist() if n != 'word/document.xml'}

para_re = re.compile(r'<w:p[ >].*?</w:p>', re.DOTALL)
paras = list(para_re.finditer(xml))

def para_text(p):
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    return ''.join(runs)

# -----------------------------------------------------------------------
# Absätze filtern: nur DE behalten
# -----------------------------------------------------------------------
keep = []
removed = []
for m in paras:
    t = para_text(m.group()).strip()
    l = lang(t)
    if l == 'en':
        removed.append(t[:80])
    else:
        keep.append(m)

print(f'Gesamt:   {len(paras)} Absätze')
print(f'Behalten: {len(keep)}')
print(f'Entfernt: {len(removed)} (englisch)')
print()
print('=== Entfernte Absätze ===')
for r in removed:
    print(f'  – {r}')

# -----------------------------------------------------------------------
# Neues XML bauen
# -----------------------------------------------------------------------
new_parts = []
prev_end = 0
for m in paras:
    new_parts.append(xml[prev_end:m.start()])
    if m in keep:
        new_parts.append(m.group())
    prev_end = m.end()
new_parts.append(xml[prev_end:])
new_xml = ''.join(new_parts)

# -----------------------------------------------------------------------
# Ergebnis: Deutsche Absätze auflisten
# -----------------------------------------------------------------------
print()
print('=== DEUTSCHE VERSION – Absätze ===')
kept_texts = [para_text(m.group()).strip() for m in keep if para_text(m.group()).strip()]
for i, t in enumerate(kept_texts):
    print(f'[{i:3d}] {t[:110]}')

# -----------------------------------------------------------------------
# Speichern
# -----------------------------------------------------------------------
with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('word/document.xml', new_xml.encode('utf-8'))
    for name, data in other_files.items():
        zout.writestr(name, data)

print(f'\n✓ Gespeichert: {DEST}')
