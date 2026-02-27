import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ga_dir = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

# GA307 Datei vom 9. August 1923 finden
pattern = os.path.join(ga_dir, '*307*', '*.md')
matches = glob.glob(pattern)
for fn in sorted(matches):
    if 'August' in fn or '9.' in fn or 'FÜNF' in fn.upper() or '5.' in fn:
        print(fn)
        with open(fn, 'r', encoding='utf-8') as f:
            content = f.read()
        # Zeige Zeilen mit Block-IDs
        lines = content.split('\n')
        for i, l in enumerate(lines[:50]):
            if l.strip():
                print(f'{i+1}: {l[:120]}')
        print('...')
        # Suche nach Block-IDs (^xxxxx)
        has_ids = any('^' in l for l in lines)
        print(f'Hat Block-IDs: {has_ids}')
        if has_ids:
            for i, l in enumerate(lines):
                if '^' in l:
                    print(f'  ID-Zeile {i+1}: {l[:100]}')
        break
