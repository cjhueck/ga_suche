"""
Hole ALLE GA130 Vorträge mit ihren Nummern von rsarchive.org
"""

import requests
from bs4 import BeautifulSoup
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

r = requests.get('https://rsarchive.org/Lectures/GA130/', timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

# Finde alle Vortragslinks
links = soup.find_all('a', href=True)

lectures_with_numbers = []

for link in links:
    href = link['href']
    filename = href.split('/')[-1]
    
    # Nur Vortragsdateien
    if not re.match(r'\d{8}[aped]\d{2}\.html', filename):
        continue
    
    # Hole die Seite und extrahiere Nummer aus Titel
    full_url = f"https://rsarchive.org{href}" if href.startswith('/') else href
    
    try:
        lr = requests.get(full_url, timeout=10)
        lr.encoding = 'utf-8'
        lsoup = BeautifulSoup(lr.text, 'html.parser')
        
        # Deutscher Titel
        gdiv = lsoup.find('div', id='original')
        if not gdiv:
            gdiv = lsoup.find('div', class_='German')
        
        if gdiv:
            h3 = gdiv.find('h3')
            if h3:
                title = h3.get_text().strip()
                
                # Extrahiere Nummer
                num_match = re.match(r'^([IVXLCDM]+|[\d]+)\.', title)
                if num_match:
                    num_str = num_match.group(1)
                    
                    # Konvertiere römisch zu arabisch
                    if num_str.isdigit():
                        lecture_num = int(num_str)
                    else:
                        # Römische Zahlkonversion
                        roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                        result = 0
                        prev_value = 0
                        for char in reversed(num_str):
                            value = roman_values.get(char, 0)
                            if value < prev_value:
                                result -= value
                            else:
                                result += value
                            prev_value = value
                        lecture_num = result
                    
                    lectures_with_numbers.append((lecture_num, filename, title, full_url))
    except:
        pass

# Sortiere nach Vortragsnummer
lectures_with_numbers.sort(key=lambda x: x[0])

print(f"GA130 - Vorträge nach Nummerierung auf rsarchive.org:\n")
print("="*70)
print(f"Gesamt: {len(lectures_with_numbers)} Vorträge mit Nummern\n")

for num, filename, title, url in lectures_with_numbers:
    print(f"{num:2d}. {filename:25s} | {title[:70]}")

print(f"\n→ Erwartete Anzahl ohne Vorwort: 23")
print(f"→ Gefunden mit Nummern: {len(lectures_with_numbers)}")

# Prüfe ob Lücken
nums = [n[0] for n in lectures_with_numbers]
expected = set(range(1, max(nums)+1))
actual = set(nums)
missing = expected - actual

if missing:
    print(f"\n⚠️ Fehlende Nummern: {sorted(missing)}")


