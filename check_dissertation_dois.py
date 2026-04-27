import re, os, urllib.request, urllib.error, time

folder = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\Dissertation\0. Text'

# Alle .md Dateien lesen
all_refs = []  # (datei, zeile_nr, zeile_text, doi)

md_files = [f for f in os.listdir(folder) if f.endswith('.md')]

for fname in sorted(md_files):
    fpath = os.path.join(folder, fname)
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        # Alle DOI-URLs finden
        for m in re.finditer(r'https?://doi\.org/([^\s\.\)]+)', line):
            doi_url = m.group(0).rstrip('.,;)')
            doi = m.group(1).rstrip('.,;)')
            all_refs.append((fname, i, line.strip()[:120], doi_url))

print(f"Gesamt DOIs in Dissertation: {len(all_refs)}\n")
for fname, lnr, txt, url in all_refs:
    print(f"  {fname}:{lnr}  {url}")

print()
print("=" * 80)
print("HTTP-CHECK ALLER DOIs")
print("=" * 80)

HEADERS = {'User-Agent': 'Mozilla/5.0'}

results = []
for fname, lnr, txt, url in all_refs:
    # Vorab-Prüfung
    if re.search(r'\(\d{4}$|\(\d{2}$', url) or url.endswith('-') or '/doi:' in url:
        status = 'FORMAT_FEHLER'
        results.append((fname, lnr, url, status, txt))
        print(f"FORMAT: [{fname}:{lnr}] {url}")
        continue

    for method in ('HEAD', 'GET'):
        try:
            req = urllib.request.Request(url, headers=HEADERS, method=method)
            with urllib.request.urlopen(req, timeout=12) as r:
                status = str(r.status)
            break
        except urllib.error.HTTPError as e:
            if e.code == 405 and method == 'HEAD':
                continue
            status = str(e.code)
            break
        except Exception as e:
            status = 'ERR'
            break

    tag = 'OK ' if status == '200' else f'HTTP {status}'
    print(f"{tag:<12} [{fname}:{lnr}] {url[:80]}")
    results.append((fname, lnr, url, status, txt))
    time.sleep(0.3)

# Zusammenfassung
print()
print("=" * 80)
print("PROBLEMATISCHE DOIs (nicht 200/403):")
print("=" * 80)
bad = [(f, l, u, s, t) for f, l, u, s, t in results
       if s not in ('200', '403', '301', '302', '303', 'FORMAT_FEHLER')]
format_err = [(f, l, u, s, t) for f, l, u, s, t in results if s == 'FORMAT_FEHLER']

for f, l, u, s, t in bad:
    print(f"\n  [{s}] {f}:{l}")
    print(f"  URL: {u}")
    print(f"  Zeile: {t}")

if format_err:
    print("\nFORMAT-FEHLER:")
    for f, l, u, s, t in format_err:
        print(f"  {f}:{l}  {u}")

print(f"\nGesamt: {len(all_refs)}  |  OK/403: {len([r for r in results if r[3] in ('200','403','301','302','303')])}  |  Probleme: {len(bad)+len(format_err)}")

# Speichere Ergebnisse
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\diss_doi_results.txt', 'w', encoding='utf-8') as f:
    for fname, lnr, txt, url, *_ in [(r[0],r[1],r[4],r[2]) for r in results]:
        status = [r[3] for r in results if r[0]==fname and r[1]==lnr][0]
        f.write(f"{status}\t{fname}:{lnr}\t{url}\t{txt}\n")
print("\nErgebnisse gespeichert in diss_doi_results.txt")
