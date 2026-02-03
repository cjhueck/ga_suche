# -*- coding: utf-8 -*-
import json

# Check tableOfContents IDs in summary-database
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

print("=== summary-database.json: GA212/1 tableOfContents IDs ===")
toc = summary_db.get('GA212/1', {}).get('tableOfContents', [])
for h in toc[:8]:
    idx = h.get('index', '-')
    heading = h.get('heading', '')[:60]
    print(f"  {idx} : {heading}")

print("\n=== steiner-full-lectures-212-212.json: GA212/1 neue IDs ===")
with open('steiner-full-lectures/steiner-full-lectures-212-212.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lectures = data.get('lectures', [])
lec = [l for l in lectures if l.get('ID') == 'GA212/1'][0]
paras = lec.get('paragraphs', [])
print("Erste 15 Absatz-IDs:")
for p in paras[:15]:
    idx = p.get('index', '-')
    text = p.get('content', '')[:50]
    print(f"  {idx} : {text}...")

# Prüfe ob die TOC-IDs in den neuen Absätzen vorkommen
print("\n=== Prüfung: Kommen TOC-IDs in neuen Absätzen vor? ===")
new_ids = set(p.get('index', '') for p in paras)
for h in toc[:5]:
    idx = h.get('index', '-')
    found = "JA" if idx in new_ids else "NEIN"
    print(f"  {idx} -> {found}")

print(f"\nAnzahl TOC-Eintraege: {len(toc)}")
print(f"Anzahl neue Absatz-IDs: {len(new_ids)}")

# Zaehle Treffer
matches = sum(1 for h in toc if h.get('index', '') in new_ids)
print(f"Treffer: {matches} von {len(toc)}")
