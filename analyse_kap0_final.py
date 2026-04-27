import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.DOTALL)
texts = []
for p in paras:
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    t = ''.join(runs).strip()
    if t:
        texts.append(t)

EN_WORDS = {'the','of','in','and','to','a','is','that','it','for','this','with','as','was','are','by',
            'from','at','be','an','or','but','not','we','i','which','have','has','on','its','their',
            'they','our','what','can','more','also','than','when','if','would','such','rather','thus',
            'however','these','those','were','been','him','her','who','will','do','did','may','might',
            'should','could','he','she','his','one','while','since','although','between','through'}
DE_WORDS = {'die','der','das','ist','ein','eine','und','zu','des','dem','den','sich','nicht','er','sie',
            'es','wir','auf','mit','als','von','an','im','dass','auch','aber','bei','nach','zum','zur',
            'wie','oder','so','durch','wird','hat','werden','sind','kann','diese','dieser','dieses',
            'jedoch','daher','dabei','sondern','wenn','nur','noch','schon','dann','hier','wobei',
            'indem','doch','wurde','waren','welche','welcher','welches','ihren','ihrem','ihrer'}

def is_english(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 5: return None
    en = sum(1 for w in words if w in EN_WORDS)
    de = sum(1 for w in words if w in DE_WORDS)
    de += len(re.findall(r'[äöüßÄÖÜ]', text)) * 1.5
    if en + de == 0: return None
    return en > de

print('=' * 70)
print('ANALYSE: 0 Einleitung_fertig_DN_CH.docx (FINALE VERSION)')
print('=' * 70)
print(f'Absätze: {len(texts)} | Zeichen: {sum(len(t) for t in texts):,}')
print()

# --- 1. Redaktionelle Notizen ---
print('=== 1. REDAKTIONELLE NOTIZEN ===')
found = False
for i, t in enumerate(texts):
    if any(kw in t for kw in ['Add the following','CHANGE TO','INSERT','TODO','add endnote','NOTE:','DELETE','[CH:','[DN:']):
        print(f'  [{i:3d}]: {t[:250]}')
        found = True
if not found:
    print('  Keine gefunden.')
print()

# --- 2. EN-Absätze ohne DE-Nachfolger ---
print('=== 2. ENGLISCHE ABSÄTZE OHNE DEUTSCHEN NACHFOLGER ===')
found = False
for i, t in enumerate(texts):
    if is_english(t) is True:
        next_lang = is_english(texts[i+1]) if i+1 < len(texts) else None
        redakt = any(kw in t for kw in ['Add the following','CHANGE TO','INSERT','add endnote'])
        if next_lang is True and not redakt:
            print(f'  [{i:3d}] → [{i+1:3d}] beide EN: {t[:100]}')
            print(f'         folgt:         {texts[i+1][:100]}')
            found = True
if not found:
    print('  Keine gefunden.')
print()

# --- 3. Vollständige Paarungsübersicht ---
print('=== 3. PAARUNGSÜBERSICHT ===')
for i, t in enumerate(texts):
    lang = is_english(t)
    flag = 'EN' if lang is True else ('DE' if lang is False else '--')
    if any(kw in t for kw in ['Add the following','CHANGE TO','INSERT','add endnote','DELETE']):
        flag = '!!'
    print(f'  [{i:3d}] {flag}  {t[:115]}')

# --- 4. Zitate in DE-Absätzen ---
print()
print('=== 4. ZITATE IN DEUTSCHEN ABSÄTZEN ===')
quote_re = re.compile(r'[„\u201e\u00bb](.*?)[\u201c\u201d\u00ab"]', re.DOTALL)
for i, t in enumerate(texts):
    if is_english(t) is not True:
        for m in quote_re.finditer(t):
            q = m.group(1).strip()
            if len(q) > 25:
                ql = is_english(q)
                flag = ' ⚠ ENGLISCH?' if ql is True else ''
                print(f'  [{i:3d}]{flag} «{q[:170]}»')

# --- 5. Schlegel-Zitat Volltext ---
print()
print('=== 5. SCHLEGEL-PASSAGE (Volltext) ===')
for i, t in enumerate(texts):
    if 'Schlegel' in t or 'Athenäum' in t or 'romantischen Imperativ' in t.lower():
        print(f'  [{i:3d}]: {t}')
        print()
