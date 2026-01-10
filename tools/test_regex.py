import re
import os

folder = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for d in os.listdir(folder):
    if 'GA019' in d:
        ga_folder = os.path.join(folder, d)
        break

pattern = r'GA\d{2,3}[a-z]?\s*\((\d+)\.\)\s+([^,]+)\.md$'

print("Teste Regex-Pattern für Kapitel-Erkennung:\n")

for name in sorted(os.listdir(ga_folder)):
    if name.startswith('GA019') and name.endswith('.md') and '_backup' not in name and '_converted' not in name:
        match = re.match(pattern, name)
        if match:
            print(f"OK ({match.group(1):>2}): {name[:60]}")
        else:
            print(f"MISS    : {name[:60]}")
            # Debug: Zeige warum es nicht matcht
            m2 = re.match(r'GA\d{2,3}[a-z]?\s*\((\d+)\.\)', name)
            if m2:
                rest = name[m2.end():]
                print(f"         Kapitel {m2.group(1)} erkannt, aber Rest problematisch: '{rest[:40]}'")

