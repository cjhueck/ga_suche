import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

GA_BASE = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

# GA307, 9. August 1923 -> finde Datei
pattern = os.path.join(GA_BASE, 'GA307*', '*.md')
for fn in sorted(glob.glob(pattern)):
    if '9. August' in fn:
        print(f'Gefundene Datei: {os.path.basename(fn)}')
        with open(fn, 'r', encoding='utf-8') as f:
            content = f.read()
        # Suche nach "Wille emanzipiert"
        idx = content.find('Wille emanzipiert')
        if idx >= 0:
            print(f'Gefunden bei Zeichen {idx}:')
            print(repr(content[max(0,idx-10):idx+200]))
            # Block-ID am Zeilenende
            line_start = content.rfind('\n', 0, idx)
            line_end   = content.find('\n', idx)
            line = content[line_start:line_end]
            print(f'\nGanze Zeile (Ende): ...{repr(line[-80:])}')
        else:
            print('NICHT GEFUNDEN in Datei')
            # Zeige erste 200 Zeichen der Datei
            print('Erste 300 Zeichen:', repr(content[:300]))
        break
