"""
Bereinigt doppelte Seitenmarker in GA091 (aus Inhaltsverzeichnis).
"""
import json

# Lade page-break-markers.json
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

if 'GA091' not in data:
    print("GA091 nicht gefunden!")
    exit(1)

ga091 = data['GA091']
breaks = ga091.get('breaks', [])
print(f"Ursprünglich: {len(breaks)} Breaks")

# Finde die TOC-Einträge (pdfFrom < 25, aber page > 10)
# Diese sind die falschen Kapitelstart-Marker
toc_pages = []
content_breaks = []

for b in breaks:
    page = b.get('page')
    pdf_from = b.get('pdfFrom')
    
    # TOC-Einträge: pdfFrom ist klein (< 25), aber page ist groß (> 10)
    # Das sind die Kapitelstarts aus dem Inhaltsverzeichnis
    if pdf_from is not None and pdf_from < 25 and page and page > 10:
        toc_pages.append(page)
        print(f"  Entferne TOC-Marker: |{page}| (pdfFrom={pdf_from})")
    else:
        content_breaks.append(b)

print(f"\nEntfernt: {len(toc_pages)} TOC-Marker")
print(f"TOC-Seiten: {sorted(toc_pages)}")
print(f"Verbleibend: {len(content_breaks)} Breaks")

# Prüfe auf doppelte Seitennummern
pages = [b.get('page') for b in content_breaks if b.get('page')]
duplicates = [p for p in set(pages) if pages.count(p) > 1]
if duplicates:
    print(f"\nWARNUNG: Noch doppelte Seiten: {duplicates}")

# Speichere
ga091['breaks'] = content_breaks
data['GA091'] = ga091

with open('page-break-markers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nGespeichert!")

