import json
d = json.load(open('page-break-markers.json', 'r', encoding='utf-8'))
breaks = d.get('GA153', {}).get('breaks', [])
for b in breaks:
    page = b.get('page', 0)
    if page and page <= 30:
        right = (b.get('right') or '')[:100]
        print(f"S.{page}: {right}...")
