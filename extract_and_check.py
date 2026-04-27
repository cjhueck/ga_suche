import zipfile, re, urllib.request, urllib.error, time, sys
from collections import OrderedDict

# ── Extraktion ──────────────────────────────────────────────────────────────
src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_ec.docx'

import shutil
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
    fn  = z.read('word/footnotes.xml').decode('utf-8')

import os; os.remove(tmp)

combined = doc + fn
text = re.sub(r'<[^>]+>', ' ', combined)
text = re.sub(r'\s+', ' ', text)
# Zero-width spaces und andere unsichtbare Zeichen entfernen
text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

found = OrderedDict()

# DOI-Links
for m in re.finditer(r'https?://doi\.org/[^\s<>"\')\]]+', text, re.IGNORECASE):
    url = m.group(0).rstrip('.,;)')
    found[url] = True

# doi: Prefix
for m in re.finditer(r'doi:\s*(10\.\d{4,}/[^\s<>"\')\]]+)', text, re.IGNORECASE):
    url = 'https://doi.org/' + m.group(1).rstrip('.,;)')
    found[url] = True

# Sonstige URLs
for m in re.finditer(r'https?://(?!doi\.org)[^\s<>"\')\]]{15,}', text, re.IGNORECASE):
    url = m.group(0).rstrip('.,;)')
    url = re.sub(r'[\u200b\u200c\u200d]', '', url)
    if len(url) > 15:
        found[url] = True

links = list(found.keys())
print(f"Gefunden: {len(links)} Links\n", flush=True)

# ── HTTP-Check ───────────────────────────────────────────────────────────────
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; checker/1.0)'}

def check(url):
    # Offensichtlich defekt
    if re.search(r'\(\d{4}$|\(\d{2}$', url):
        return 'TRUNCATED', 'URL abgeschnitten (offene Klammer)'
    if url.endswith('-') or url.endswith('_'):
        return 'TRUNCATED', 'URL abgeschnitten'
    if '/doi:10.' in url:
        return 'DOUBLE_DOI', 'Doppeltes doi:-Prefix'

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
            return 'ERR', str(e)[:80]
    return 'ERR', 'HEAD und GET fehlgeschlagen'

results = []
for i, url in enumerate(links, 1):
    status, note = check(url)
    results.append((url, status, note))
    tag = status if status not in ('200',) else 'OK '
    line = f"{i:3}. {tag:<12} {url[:85]}"
    # ASCII-safe output fuer Windows-Terminal
    print(line.encode('ascii', 'replace').decode('ascii'), flush=True)
    time.sleep(0.25)

# ── Zusammenfassung ───────────────────────────────────────────────────────────
print('\n' + '='*80, flush=True)
print('PROBLEMATISCHE LINKS:', flush=True)
print('='*80, flush=True)

ok_statuses = {'200', '301', '302', '303'}
problems = [(u, s, n) for u, s, n in results
            if s not in ok_statuses and not s.startswith('OK')]

for u, s, n in sorted(problems, key=lambda x: x[1]):
    print(f"  [{s}] {u}".encode('ascii','replace').decode('ascii'), flush=True)
    if n:
        print(f"        -> {n}".encode('ascii','replace').decode('ascii'), flush=True)

print(f"\nGesamt: {len(links)}  OK: {len(links)-len(problems)}  Probleme: {len(problems)}", flush=True)

# Speichere
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\link_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"STATUS\tURL\tNOTE\n")
    for u, s, n in results:
        f.write(f"{s}\t{u}\t{n}\n")
print('\nErgebnisse gespeichert in link_results.txt', flush=True)
