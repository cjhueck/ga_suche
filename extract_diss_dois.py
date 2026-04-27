import re, os, sys

# stdout auf UTF-8 setzen
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

folder = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\Dissertation\0. Text'

DOI_PAT = re.compile(r'https?://doi\.org/[^\s<>"\')\]\[`]+')

all_refs = []

files = sorted([f for f in os.listdir(folder) if f.endswith('.md')
                and 'Methodik' not in f and 'Sigla' not in f
                and 'Content' not in f and 'Word count' not in f
                and 'Forschungsstand' not in f and 'Wichtige' not in f
                and 'Common threads' not in f])

print(f"Dateien: {len(files)}")

for fname in files:
    fpath = os.path.join(folder, fname)
    try:
        with open(fpath, encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"FEHLER beim Lesen von {fname}: {e}")
        continue
    for i, line in enumerate(lines, 1):
        for m in DOI_PAT.finditer(line):
            url = re.sub(r'[.,;`\)]+$', '', m.group(0))
            all_refs.append((fname, i, url, line.strip()[:100]))

print(f"Gesamt DOIs: {len(all_refs)}\n")
for fname, lnr, url, ctx in all_refs:
    print(f"{fname}:{lnr}\t{url}")

# Speichern
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\diss_dois_list.txt', 'w', encoding='utf-8') as f:
    for fname, lnr, url, ctx in all_refs:
        f.write(f"{fname}\t{lnr}\t{url}\t{ctx}\n")
print(f"\nGespeichert.")
