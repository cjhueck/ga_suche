import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\0 Einleitung - fertig neu - fertig.docx'

with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')

paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.DOTALL)
texts = []
for p in paras:
    runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.DOTALL)
    text = ''.join(runs).strip()
    if text:
        texts.append(text)

EN_WORDS = {'the','of','in','and','to','a','is','that','it','for','this','with','as','was','are','by',
            'from','at','be','an','or','but','not','we','i','which','have','has','on','its','their',
            'they','our','what','can','more','also','than','when','if','would','such','rather','thus',
            'however','these','those','were','been','him','her','who','will','do','did','may','might',
            'should','could','he','she','his','her','one','two','three','while','since','although'}
DE_WORDS = {'die','der','das','ist','ein','eine','und','zu','des','dem','den','sich','nicht','er','sie',
            'es','wir','auf','mit','als','von','an','im','dass','auch','aber','bei','nach','fuer','zum',
            'zur','wie','oder','so','durch','wird','hat','werden','sind','kann','diese','dieser','dieses',
            'jedoch','daher','dabei','vielmehr','sondern','wenn','nur','noch','schon','dann','hier',
            'wobei','indem','dabei','doch','wurde','waren','hatte','hatte','welche','welcher','welches'}

def is_english(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 5:
        return None
    en = sum(1 for w in words if w in EN_WORDS)
    de = sum(1 for w in words if w in DE_WORDS)
    de += len(re.findall(r'[äöüßÄÖÜ]', text)) * 1.5
    if en + de == 0:
        return None
    return en > de

print('=' * 70)
print('ANALYSE: 0 Einleitung – fertig neu – fertig.docx')
print('=' * 70)
print()

# -----------------------------------------------------------------------
# 1. REDAKTIONELLE NOTIZEN
# -----------------------------------------------------------------------
print('=== 1. REDAKTIONELLE NOTIZEN (müssen noch umgesetzt werden) ===')
print()
for i, t in enumerate(texts):
    if any(kw in t for kw in ['Add the following', 'CHANGE TO', 'INSERT', 'TODO', 'ADD:', 'NOTE:', 'add the']):
        print(f'  Abs. [{i:3d}]: {t}')
        # Zeige nächsten Absatz als Kontext
        if i+1 < len(texts):
            print(f'  → folgt: [{i+1:3d}]: {texts[i+1][:150]}')
        print()

# -----------------------------------------------------------------------
# 2. NICHT ÜBERSETZTE ENGLISCHE ABSÄTZE
# -----------------------------------------------------------------------
print()
print('=== 2. NICHT ÜBERSETZTE ENGLISCHE ABSÄTZE ===')
print()
i = 0
while i < len(texts):
    lang = is_english(texts[i])
    if lang is True:
        # Erwarte als nächstes einen DE-Absatz
        next_lang = is_english(texts[i+1]) if i+1 < len(texts) else None
        if next_lang is True or next_lang is None:
            # Redaktionelle Notizen überspringen
            if not any(kw in texts[i] for kw in ['Add the following', 'CHANGE TO', 'INSERT']):
                print(f'  Abs. [{i:3d}] (kein DE-Pendant): {texts[i][:160]}')
                print()
    i += 1

# -----------------------------------------------------------------------
# 3. STRUKTURÜBERSICHT: EN/DE-Paarung
# -----------------------------------------------------------------------
print()
print('=== 3. VOLLSTÄNDIGE PAARUNGSÜBERSICHT ===')
print()
for i, t in enumerate(texts):
    lang = is_english(t)
    flag = 'EN' if lang is True else ('DE' if lang is False else '--')
    # Redaktionelle Notizen markieren
    if any(kw in t for kw in ['Add the following', 'CHANGE TO', 'INSERT']):
        flag = '!!'
    print(f'  [{i:3d}] {flag}  {t[:110]}')

# -----------------------------------------------------------------------
# 4. DEUTSCHE ZITATE – POTENZIELLE RÜCKÜBERSETZUNGEN
# -----------------------------------------------------------------------
print()
print('=== 4. ZITATE IN DEUTSCHEN ABSÄTZEN (auf Rückübersetzungen prüfen) ===')
print()
quote_patterns = [
    re.compile(r'\u201e(.*?)\u201c', re.DOTALL),
    re.compile(r'\u201e(.*?)\u201d', re.DOTALL),
    re.compile(r'\u00bb(.*?)\u00ab', re.DOTALL),
    re.compile(r'"(.*?)"', re.DOTALL),
]
for i, t in enumerate(texts):
    if is_english(t) is False:  # nur DE-Absätze
        for pat in quote_patterns:
            for m in pat.finditer(t):
                q = m.group(1).strip()
                if len(q) > 25:
                    q_lang = is_english(q)
                    flag = ' ⚠ ENGLISCH – mögliche Rückübersetzung!' if q_lang is True else ''
                    print(f'  [{i:3d}]{flag}')
                    print(f'        «{q[:180]}»')
                    break

# -----------------------------------------------------------------------
# 5. SCHLEGEL-ZITAT PRÜFEN
# -----------------------------------------------------------------------
print()
print('=== 5. SCHLEGEL-ZITAT (Abs. 34-35) – VOLLTEXT ===')
for i in [33, 34, 35, 36]:
    if i < len(texts):
        print(f'  [{i:3d}]: {texts[i]}')
        print()
