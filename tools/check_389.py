import json
import re

with open('steiner-full-lectures/steiner-full-lectures-014-354-part04.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for lec in data['lectures']:
    if lec['ID'] == 'GA072/10':
        text = ' '.join([p.get('content', '') for p in lec['paragraphs']])
        count = len(re.findall(r'\|389\|', text))
        print(f'|389| Anzahl: {count}')
        
        if count > 0:
            m = re.search(r'.{30}\|389\|.{30}', text)
            if m:
                print(f'Kontext: {m.group()}')
        break

