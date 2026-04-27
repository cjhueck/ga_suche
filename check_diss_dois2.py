import re, os, urllib.request, urllib.error, time

folder = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\Dissertation\0. Text'

# Alle DOIs aus allen .md Dateien sammeln
# Regex: stoppt NICHT bei Punkten, nur bei Leerzeichen und bestimmten Sonderzeichen
DOI_PAT = re.compile(r'https?://doi\.org/[^\s<>"\')\]\[]+')

all_refs = []  # (datei, zeile_nr, doi_url, zeilen_kontext)

md_files = [f for f in os.listdir(folder) if f.endswith('.md')
            and not f.startswith('X. Methodik')]  # Methodik auslassen

for fname in sorted(md_files):
    fpath = os.path.join(folder, fname)
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        for m in DOI_PAT.finditer(line):
            url = m.group(0).rstrip('.,;')
            # Bereinige trailing backtick, Punkt, Komma
            url = re.sub(r'[.,;`]+$', '', url)
            all_refs.append((fname, i, url, line.strip()[:120]))

print(f"Gesamt DOIs gefunden: {len(all_refs)}\n")

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def check_url(url):
    if re.search(r'\(\d{2,4}$', url) or url.endswith('-') or '/doi:' in url:
        return 'FORMAT_ERR', 'URL-Format fehlerhaft'
    for method in ('HEAD', 'GET'):
        try:
            req = urllib.request.Request(url, headers=HEADERS, method=method)
            with urllib.request.urlopen(req, timeout=12) as r:
                return str(r.status), ''
        except urllib.error.HTTPError as e:
            if e.code == 405 and method == 'HEAD':
                continue
            return str(e.code), str(e.reason)
        except Exception as e:
            return 'ERR', str(e)[:60]
    return 'ERR', 'HEAD+GET fehlgeschlagen'

results = []
for fname, lnr, url, ctx in all_refs:
    status, note = check_url(url)
    tag = 'OK ' if status in ('200','301','302') else f'{status}'
    line_out = f"{tag:<8} [{fname}:{lnr}] {url[:80]}"
    print(line_out.encode('ascii','replace').decode('ascii'))
    results.append((fname, lnr, url, status, note, ctx))
    time.sleep(0.25)

# Zusammenfassung
OK_STATUSES = {'200', '301', '302', '303', '403'}  # 403 = Publisher-block, DOI ok
print()
print('='*80)
print('PROBLEMATISCHE DOIs (404, ERR, FORMAT):')
print('='*80)

problems = [(f,l,u,s,n,c) for f,l,u,s,n,c in results if s not in OK_STATUSES]

for f,l,u,s,n,c in sorted(problems, key=lambda x: x[0]):
    print(f"\n  [{s}] {f}:{l}")
    print(f"  {u}")
    print(f"  -> {c[:110]}")

print(f"\nGesamt: {len(all_refs)}  |  OK/403: {len([r for r in results if r[3] in OK_STATUSES])}  |  Probleme: {len(problems)}")

# Speichere problematische für nächsten Schritt
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\diss_problems.txt', 'w', encoding='utf-8') as f:
    for fname,lnr,url,status,note,ctx in problems:
        f.write(f"{status}\t{fname}\t{lnr}\t{url}\t{ctx}\n")
print('\nProbleme gespeichert in diss_problems.txt')
