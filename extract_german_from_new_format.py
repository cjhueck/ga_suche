"""
Teste Extraktion von neuem Seitenformat
"""

import requests
from bs4 import BeautifulSoup
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

url = "https://rsarchive.org/Lectures/GA174b/English/SOL2024/19140930p01.html"

response = requests.get(url, timeout=15)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

# Methode 1: Suche div id="original" (altes Format)
german_div = soup.find('div', id='original')

if german_div:
    print("ALTES FORMAT")
else:
    print("NEUES FORMAT - suche in articleBox")
    
    # Neues Format: Der Text ist in divs innerhalb von centerPanel/articleBox
    center = soup.find('div', id='centerPanel')
    if center:
        # Suche nach divs mit class="English" und class="German" oder ähnlich
        all_divs = center.find_all('div', class_=True)
        
        print(f"\nDivs mit Klassen in centerPanel: {len(all_divs)}")
        
        for div in all_divs[:20]:
            classes = ' '.join(div.get('class', []))
            text = div.get_text(strip=True)
            
            if text and len(text) > 500:
                print(f"\n<div class='{classes}'>:")
                print(f"  Länge: {len(text)} Zeichen")
                print(f"  Erste 200: {text[:200]}")
                
                # Prüfe ob deutsch
                if any(word in text for word in ['werden', 'worden', 'müssen', 'können', 'heute']):
                    print("  → DEUTSCH!")
                else:
                    print("  → Englisch")

