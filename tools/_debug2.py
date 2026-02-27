import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fp = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie\I. Themen\Denken - Fühlen - Wollen\Seelische Entwicklung.md'
with open(fp, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeige Zeile 33 vollständig
line33 = lines[32]
print(f'Länge Zeile 33: {len(line33)} Zeichen')
print(f'Letzte 200 Zeichen: {repr(line33[-200:])}')
print()

# Teste CITE_RE auf diese Zeile
CITE_RE = re.compile(
    r'^(?P<para>.+?)\s+'
    r'(?P<cite>\[GA\s+(?P<ga>\d+),\s*S\.\s*[\d–\-]+;\s*'
    r'\d{2}\.\d{2}\.\d{4}\]'
    r'\(http[^\)]+ga=\d+&date=(?P<isodate>\d{4}-\d{2}-\d{2})[^\)]*\))'
    r'(?P<rest>.*)$',
    re.DOTALL
)
stripped = line33.rstrip('\n\r')
m = CITE_RE.match(stripped)
if m:
    print('MATCH gefunden!')
    print(f'  para (letzte 80): ...{m.group("para")[-80:]!r}')
    print(f'  ga: {m.group("ga")}')
    print(f'  isodate: {m.group("isodate")}')
    print(f'  rest: {m.group("rest")[:80]!r}')
else:
    print('KEIN MATCH')
    # Suche das [GA im Text
    idx = stripped.find('[GA ')
    if idx >= 0:
        print(f'  [GA gefunden bei Position {idx}')
        print(f'  Kontext: {repr(stripped[idx:idx+80])}')
    # Prüfe ob URL ) enthält
    url_start = stripped.find('(http')
    url_end = stripped.find(')', url_start)
    if url_start >= 0:
        url = stripped[url_start:url_end+1]
        print(f'  URL-Länge: {len(url)}')
        inner_paren = url[1:-1].count(')')
        print(f'  Klammern im URL: {inner_paren}')
        if inner_paren > 0:
            print(f'  Problem: ) im URL-Inhalt!')
