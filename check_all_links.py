import urllib.request
import urllib.error
import re
import time

links_file = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\all_links.txt'

with open(links_file, encoding='utf-8') as f:
    links = [l.strip() for l in f if l.strip()]

print(f"Pruefe {len(links)} Links...\n")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; link-checker/1.0)',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}

results = []

for i, url in enumerate(links, 1):
    status = None
    note = ''
    final_url = url

    # Vorab-Prüfung auf offensichtlich defekte Links
    if re.search(r'\(\d{4}$', url) or url.endswith('-') or url.endswith('_'):
        status = 'TRUNCATED'
        note = 'URL abgeschnitten'
        results.append((url, status, note))
        print(f"{i:3}. TRUNCATED  {url[:80]}")
        continue

    if 'doi:10.' in url and url.startswith('https://doi.org/doi:'):
        status = 'DOUBLE_PREFIX'
        note = 'Doppeltes doi: Prefix'
        results.append((url, status, note))
        print(f"{i:3}. DOUBLE_DOI {url[:80]}")
        continue

    try:
        req = urllib.request.Request(url, headers=HEADERS, method='HEAD')
        req.add_header('Accept-Encoding', 'identity')
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            final_url = resp.url
        if status == 200:
            tag = 'OK '
        else:
            tag = f'HTTP {status}'
        results.append((url, str(status), note))
        print(f"{i:3}. {tag:<10} {url[:80]}")
    except urllib.error.HTTPError as e:
        status = e.code
        if status == 405:
            # HEAD nicht erlaubt -> GET versuchen
            try:
                req2 = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    status = resp2.status
                    final_url = resp2.url
                results.append((url, str(status), 'GET fallback'))
                print(f"{i:3}. OK (GET)   {url[:80]}")
            except Exception as e2:
                results.append((url, f'ERR:{e2}', ''))
                print(f"{i:3}. ERROR      {url[:80]}  -> {e2}")
        else:
            results.append((url, str(status), str(e.reason)))
            print(f"{i:3}. HTTP {status:<5} {url[:80]}")
    except Exception as e:
        results.append((url, f'ERR', str(e)[:60]))
        print(f"{i:3}. ERROR      {url[:80]}  -> {str(e)[:50]}")

    time.sleep(0.3)

print()
print("=" * 80)
print("ZUSAMMENFASSUNG - PROBLEMATISCHE LINKS:")
print("=" * 80)
problems = [(u, s, n) for u, s, n in results if not (s in ('200', 'OK') or s.startswith('OK') or s == '200')]
for u, s, n in sorted(problems, key=lambda x: x[1]):
    print(f"  [{s}] {u}")
    if n:
        print(f"         -> {n}")

print(f"\nGesamt: {len(links)}  |  OK: {len(links)-len(problems)}  |  Probleme: {len(problems)}")

# Speichere Ergebnisse
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\link_results.txt', 'w', encoding='utf-8') as f:
    for u, s, n in results:
        f.write(f"{s}\t{u}\t{n}\n")
