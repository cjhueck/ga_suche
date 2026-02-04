import json
import glob
import os
import re

files = glob.glob('steiner-full-lectures/steiner-full-lectures-*.json')
print(f'JSON-Dateien gefunden: {len(files)}')
for f in files[:3]:
    print(f'  {os.path.basename(f)}')

gas = set()
total_lectures = 0

for jfile in files:
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lectures = data.get('lectures', [])
    total_lectures += len(lectures)
    
    for lecture in lectures:
        lid = lecture.get('ID', '') or lecture.get('id', '')
        if lid:
            match = re.match(r'GA(\d+)', lid)
            if match:
                gas.add(int(match.group(1)))

print(f'\nTotal Lectures: {total_lectures}')
print(f'Exportierte GAs ({len(gas)} total):')
sorted_gas = sorted(gas)
print(sorted_gas[:50])
if len(sorted_gas) > 50:
    print(f'... und {len(sorted_gas) - 50} weitere')

# Prüfe ob GA200/204 dabei
print(f'\nGA200 exportiert: {200 in gas}')
print(f'GA204 exportiert: {204 in gas}')

# Zeige Beispiel-IDs
print('\nBeispiel Lecture-IDs:')
with open(files[0], 'r', encoding='utf-8') as f:
    data = json.load(f)
for lec in data.get('lectures', [])[:5]:
    print(f'  {lec.get("ID", lec.get("id", "KEINE"))}')
