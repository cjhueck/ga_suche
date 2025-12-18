import json
import sys

ga = sys.argv[1] if len(sys.argv) > 1 else 'GA036'

with open('page-break-apply-report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

ga_report = report.get(ga, {})
print(f'{ga} Report:')
print(f'  Gesamt Breaks: {ga_report.get("totalBreaks", 0)}')
print(f'  Eingefügt: {ga_report.get("inserted", 0)}')
print(f'  Nicht gefunden: {ga_report.get("notFound", 0)}')

# Zeige einige nicht gefundene
not_found = ga_report.get('notFoundDetails', [])[:5]
if not_found:
    print(f'\nBeispiele nicht gefunden:')
    for nf in not_found:
        print(f'  Seite {nf.get("page", "?")}: {nf.get("reason", "?")}')
        left = (nf.get('left', '') or '')[:60]
        right = (nf.get('right', '') or '')[:60]
        print(f'    Left: {left}...')
        print(f'    Right: {right}...')
else:
    print('\nKeine Details zu nicht gefundenen Breaks.')
