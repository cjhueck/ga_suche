#!/usr/bin/env python3
"""
Analysiert die Location-Daten in Citavi, um zu sehen, wohin die URLs verlinken.
"""

import sqlite3
import json
import re
from pathlib import Path
from collections import Counter

citavi_path = r"C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Rudolf Steiner Gesamtausgabe (Kopie)\Rudolf Steiner Gesamtausgabe (Kopie).ctv6"

conn = sqlite3.connect(citavi_path)
cursor = conn.cursor()

# Hole alle Locations mit ihren Addressen
print("=== Analysiere Location-Addressen ===\n")
cursor.execute("""
    SELECT l.Address, l.LocationType, r.Title, r.ShortTitle, r.ID as RefID
    FROM Location l
    LEFT JOIN Reference r ON l.ReferenceID = r.ID
    WHERE l.Address IS NOT NULL
""")
locations = cursor.fetchall()

print(f"Gesamtanzahl Locations mit Address: {len(locations)}\n")

# Analysiere CacheFilePath
cache_paths = []
file_names = []
urls = []

for address, loc_type, title, short_title, ref_id in locations:
    if not address:
        continue
    
    try:
        addr_data = json.loads(address)
        
        # Prüfe CacheFilePath
        cache_path = addr_data.get('CacheFilePath', '')
        if cache_path:
            cache_paths.append((cache_path, title or short_title))
        
        # Prüfe UriString (Dateiname)
        uri_string = addr_data.get('UriString', '')
        if uri_string and '.pdf' in uri_string.lower() and not uri_string.startswith('http'):
            file_names.append((uri_string, title or short_title))
        
        # Prüfe OriginalString (URL)
        original_string = addr_data.get('OriginalString', '')
        if original_string and (original_string.startswith('http://') or original_string.startswith('https://')):
            urls.append((original_string, title or short_title))
    except:
        pass

print(f"=== CacheFilePath-Analyse ===")
print(f"Locations mit CacheFilePath: {len(cache_paths)}")

if cache_paths:
    # Zeige Beispiel-Cache-Pfade
    print("\nBeispiel Cache-Pfade:")
    for cache_path, title in cache_paths[:5]:
        print(f"\n  {title}")
        print(f"    Cache: {cache_path}")
        exists = Path(cache_path).exists()
        print(f"    Existiert: {exists}")
        if exists:
            file_size = Path(cache_path).stat().st_size / (1024*1024)  # MB
            print(f"    Größe: {file_size:.2f} MB")

print(f"\n=== Dateinamen (ohne vollständigen Pfad) ===")
print(f"Anzahl: {len(file_names)}")
if file_names:
    print("\nBeispiel-Dateinamen:")
    for filename, title in file_names[:10]:
        print(f"  {title}")
        print(f"    Dateiname: {filename}")

print(f"\n=== URLs (Online-Ressourcen) ===")
print(f"Anzahl: {len(urls)}")
if urls:
    domain_counter = Counter()
    for url, title in urls:
        match = re.search(r'https?://([^/]+)', url)
        if match:
            domain_counter[match.group(1)] += 1
    
    print("\nTop Domains:")
    for domain, count in domain_counter.most_common(10):
        print(f"  {domain}: {count} Links")
    
    print("\nBeispiel-URLs:")
    for url, title in urls[:5]:
        print(f"  {title}")
        print(f"    URL: {url[:120]}...")

# Prüfe ob es einen gemeinsamen Basis-Ordner gibt
print(f"\n=== Prüfe gemeinsamen Basis-Ordner ===")
if cache_paths:
    base_paths = set()
    for cache_path, _ in cache_paths:
        path_obj = Path(cache_path)
        if path_obj.exists():
            # Versuche gemeinsamen Basis-Ordner zu finden
            base_paths.add(path_obj.parent)
    
    if base_paths:
        print(f"Verschiedene Basis-Ordner gefunden: {len(base_paths)}")
        for bp in list(base_paths)[:5]:
            print(f"  {bp}")
            # Zähle PDFs in diesem Ordner
            pdf_count = len(list(bp.glob('*.pdf')))
            print(f"    PDFs in diesem Ordner: {pdf_count}")

conn.close()

print("\n=== Zusammenfassung ===")
print("Die PDFs sind gespeichert:\n")
print(f"1. **Citavi Cache-Ordner** (wahrscheinlich):")
print(f"   - Pfad: C:\\Users\\chuec\\AppData\\Local\\Swiss Academic Software\\Citavi 7\\ProjectCache\\...")
print(f"   - Anzahl Cache-Pfade: {len(cache_paths)}")
print("   - Die PDFs sind wahrscheinlich lokal im Citavi-Cache gespeichert\n")

print(f"2. **Online-Ressourcen** (URLs):")
print(f"   - Anzahl URLs: {len(urls)}")
if urls:
    domains = []
    for url, _ in urls:
        match = re.search(r'https?://([^/]+)', url)
        if match:
            domains.append(match.group(1))
    domain_counter = Counter(domains)
    top_domains = ', '.join([d for d, _ in domain_counter.most_common(3)])
    print(f"   - Domains: {top_domains}")
else:
    print("   - Domains: Keine")

print(f"\n3. **Dateinamen** (ohne vollständigen Pfad):")
print(f"   - Anzahl: {len(file_names)}")
print("   - Diese sind wahrscheinlich im Citavi-Cache-Ordner gespeichert\n")

print("Um die PDF-Texte zu extrahieren, müsste man:")
print("- Die PDFs aus dem Citavi-Cache-Ordner lesen")
print("- Oder die PDFs von den URLs herunterladen")
print("- Dann den Text mit einer PDF-Bibliothek extrahieren")
