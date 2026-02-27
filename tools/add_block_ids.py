"""
add_block_ids.py
================
Fügt Obsidian-Block-IDs (^pfr5w5 etc.) aus den Steiner_GA-Quelldateien
in die Zitat-Dateien unter I. Themen ein.

Format vorher:  Zitat-Text [GA 307, S. 85; 09.08.1923](url); ...
Format nachher: Zitat-Text ^pfr5w5 [GA 307, S. 85; 09.08.1923](url); ...

Aufruf:
    python add_block_ids.py              # Dry-Run (nur Vorschau)
    python add_block_ids.py --apply      # Alle Dateien schreiben
    python add_block_ids.py --file Seelische --apply
"""

import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

APPLY  = '--apply' in sys.argv
SINGLE = None
if '--file' in sys.argv:
    idx = sys.argv.index('--file')
    SINGLE = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

GA_BASE       = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
OBSIDIAN_BASE = (r'C:\Users\chuec\OneDrive\Obsidian'
                 r'\Obsidian Entwicklungsanthropologie\I. Themen')

MONTHS = {
    'januar':1,'februar':2,'märz':3,'maerz':3,'april':4,'mai':5,'juni':6,
    'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12,
}

def date_from_filename(fn):
    m = re.search(r'(\d{1,2})\.\s+(\w+)\s+(\d{4})', fn, re.IGNORECASE)
    if m:
        day, month, year = m.groups()
        mn = MONTHS.get(month.lower())
        if mn:
            return f'{year}-{int(mn):02d}-{int(day):02d}'
    return None

def find_ga_file(ga_num_str, iso_date):
    ga_num = int(ga_num_str)
    folders = (glob.glob(os.path.join(GA_BASE, f'GA{ga_num:03d}*')) +
               glob.glob(os.path.join(GA_BASE, f'GA{ga_num}*')))
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            if fn.endswith('.md') and date_from_filename(fn) == iso_date:
                return os.path.join(folder, fn)
    return None

def normalize(text):
    """
    Entfernt Seitenmarkierungen und normalisiert Leerzeichen.
    Behandelt:  |85|  |85   | (Zeilenbeginn-Pipe)  || 
    """
    # Alle | mit optionalen Ziffern davor/danach
    text = re.sub(r'\|[^|]*\|', '', text)   # |85|  |xxx|
    text = re.sub(r'\|\s*\d+', '', text)     # |85 ohne schliessendes |
    text = re.sub(r'\|(?=\s|$)', '', text)   # | am Zeilenende oder vor Leerzeichen
    text = re.sub(r'^\s*\|\s*', '', text)    # fuehrendes | am Anfang
    return re.sub(r'\s+', ' ', text).strip()

def build_search_keys(quote_text):
    """Mehrere Suchschlüssel – robust gegen Anfang-Variationen im Zitat."""
    norm = normalize(quote_text)
    # Auslassungs-Präfix entfernen ("... ", "…")
    clean = re.sub(r'^[.…\s]+', '', norm).strip()
    keys = []
    for base in (norm[:100], clean[:100]):
        if len(base) >= 25:
            keys.append(base)
    # Erstes/zweites Wort überspringen
    words = clean.split()
    for skip in (1, 2):
        chunk = ' '.join(words[skip:])[:80]
        if len(chunk) >= 25:
            keys.append(chunk)
    # Mittlere Segmente
    for start in (10, 20, 35):
        chunk = clean[start:start + 70]
        if len(chunk) >= 25:
            keys.append(chunk)
    # Deduplizieren
    seen, result = set(), []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result

def get_block_id(ga_file_path, quote_text):
    try:
        with open(ga_file_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
    except Exception as e:
        return None, f'Lesefehler: {e}'

    keys = build_search_keys(quote_text)
    for key in keys:
        for line in lines:
            # Ganzen Zeileninhalt normalisieren (max 800 Zeichen)
            norm_line = normalize(line[:800])
            if key in norm_line:
                m = re.search(r'\^([a-z0-9]+)\s*\r?$', line.rstrip())
                if m:
                    return '^' + m.group(1), None
                else:
                    return None, 'Absatz gefunden, aber keine Block-ID'
    short = normalize(quote_text)[:65]
    return None, f'Absatz nicht gefunden  »{short}«'

# ── Zitat-Zeilen-Muster ───────────────────────────────────────────────────────
# Unterstützt:
#   [GA NNN, S. PP; 09.08.1923](http://...&date=1923-08-09...)   (mit URL)
#   [GA NNN, S. PP; 09.08.1923]                                  (ohne URL)
CITE_RE = re.compile(
    r'^(?P<para>.+?)\s+'
    r'(?P<cite>'
        r'\[GA\s+(?P<ga>\d+),\s*S\.\s*[\d–\-]+;\s*'
        r'(?P<dd>\d{2})\.(?P<mm>\d{2})\.(?P<yyyy>\d{4})\]'
        r'(?:\(http[^\)]+ga=\d+&date=(?P<isodate>\d{4}-\d{2}-\d{2})[^\)]*\))?'
    r')'
    r'(?P<rest>.*)$',
    re.DOTALL
)

def process_file(filepath, dry_run=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    stats = {'total': 0, 'already': 0, 'added': 0, 'not_found': 0, 'no_ga_file': 0}

    for line in lines:
        stripped = line.rstrip('\n\r')
        # Bereits Block-ID vorhanden? (^xxx direkt vor [GA)
        if re.search(r'\^[a-z0-9]+\s+\[GA\s+\d+', stripped):
            stats['already'] += 1
            new_lines.append(line)
            continue
        m = CITE_RE.match(stripped)
        if not m:
            new_lines.append(line)
            continue

        stats['total'] += 1
        para    = m.group('para')
        cite    = m.group('cite')
        ga_num  = m.group('ga')
        rest    = m.group('rest')
        # ISO-Datum: aus URL-Parameter, sonst aus DD.MM.YYYY
        isodate = m.group('isodate') or f'{m.group("yyyy")}-{m.group("mm")}-{m.group("dd")}'

        ga_file = find_ga_file(ga_num, isodate)
        if not ga_file:
            stats['no_ga_file'] += 1
            print(f'  ⚠  GA{ga_num} {isodate} – Datei nicht gefunden')
            new_lines.append(line)
            continue

        block_id, err = get_block_id(ga_file, para)
        if block_id:
            stats['added'] += 1
            eol = '\n' if line.endswith('\n') else ''
            new_line = f'{para} {block_id} {cite}{rest}{eol}'
            if dry_run:
                print(f'  +{block_id}  »{para[:65]}«')
            new_lines.append(new_line)
        else:
            stats['not_found'] += 1
            if dry_run:
                print(f'  ?  {err}')
            new_lines.append(line)

    if not dry_run and stats['added'] > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'  ✓ Gespeichert – {stats["added"]} IDs eingefügt')

    return stats

def main():
    mode = 'SCHREIBEN' if APPLY else 'DRY-RUN  (--apply zum Speichern)'
    print(f'\n=== add_block_ids.py | {mode} ===\n')

    md_files = []
    for root, dirs, files in os.walk(OBSIDIAN_BASE):
        for fn in sorted(files):
            if not fn.endswith('.md') or '(download)' in fn:
                continue
            if SINGLE and SINGLE.lower() not in fn.lower():
                continue
            md_files.append(os.path.join(root, fn))

    total = {'total': 0, 'already': 0, 'added': 0, 'not_found': 0, 'no_ga_file': 0}
    for fp in md_files:
        rel = fp.replace(OBSIDIAN_BASE + os.sep, '')
        print(f'\n── {rel}')
        stats = process_file(fp, dry_run=not APPLY)
        for k in total:
            total[k] += stats[k]
        if stats['total'] == 0:
            print('  (keine Zitat-Zeilen)')
        else:
            print(f'  Zitate: {stats["total"]} | bereits: {stats["already"]} | '
                  f'+neu: {stats["added"]} | nicht gefunden: {stats["not_found"]} | '
                  f'GA fehlt: {stats["no_ga_file"]}')

    print(f'\n=== GESAMT ===')
    for k, v in total.items():
        print(f'  {k}: {v}')

if __name__ == '__main__':
    main()
