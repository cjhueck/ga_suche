import json
from pathlib import Path

# Lade keywords-database
kw_db_path = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\keywords-database.json')
with open(kw_db_path, 'r', encoding='utf-8') as f:
    kw_db = json.load(f)

# Zeige ein paar GA210 Einträge mit ihren Headings
print('KEYWORD-STRUKTUR für GA210/3:')
print('=' * 60)

ga210_3 = kw_db.get('GA210/3', {})
keywords = ga210_3.get('keywords', [])[:5]

for kw in keywords:
    print(f"Term: {kw.get('term', '')}")
    print(f"Index: {kw.get('index', '')}")
    print(f"Heading: {kw.get('heading', '')[:80]}...")
    print(f"Source: {kw.get('source', '')}")
    print()

# Lade aktuellen JSON und zeige ersten Absatz von GA210/3
print('\nAKTUELLE PARAGRAPHEN in GA210/3:')
print('=' * 60)

# Suche in steiner-full-lectures
for json_file in Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche').glob('steiner-full-lectures-*.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for lecture in data.get('lectures', []):
        if lecture.get('ID') == 'GA210/3':
            paragraphs = lecture.get('paragraphs', [])[:5]
            for p in paragraphs:
                print(f"Index: {p.get('index', '')}")
                content = p.get('content', '')[:100]
                print(f"Content: {content}...")
                print()
            break
