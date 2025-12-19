#!/usr/bin/env python3
"""Listet alle Vortragstitel im PDF auf"""
import sys
import io
import re
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068C'

ga_num = ga.replace('GA', '').lower()
pdf_path = None
for p in PDF_DIR.glob("*.pdf"):
    if ga_num in p.name.lower():
        pdf_path = p
        break

if not pdf_path:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

print(f"PDF: {pdf_path.name}\n")
print("=== Vortragstitel im PDF ===\n")

doc = fitz.open(pdf_path)

# Suche nach typischen Vortragsanfängen
# Format: TITEL (in Großbuchstaben) + Ort, Datum
lecture_pattern = re.compile(
    r"([A-ZÄÖÜ][A-ZÄÖÜ\s\-\«\»\'\"]+(?:\n[A-ZÄÖÜ][A-ZÄÖÜ\s\-\«\»\'\"]+)*)\s*\n\s*"
    r"(?:öffentlicher\s+Vortrag\s+)?([A-Za-zäöüß]+),?\s*(\d{1,2})\.?\s*([A-Za-zäöü]+)\s*(\d{4})",
    re.MULTILINE
)

lectures_found = []

for i in range(20, min(len(doc), 360)):  # Skip TOC, stop before Anhang
    page = doc[i]
    text = page.get_text("text")
    
    # Suche nach Vortragsanfängen
    for m in lecture_pattern.finditer(text):
        title = m.group(1).strip().replace('\n', ' ')
        ort = m.group(2)
        tag = m.group(3)
        monat = m.group(4)
        jahr = m.group(5)
        
        if len(title) > 10 and len(title) < 200:
            lectures_found.append({
                'page': i,
                'title': title[:60],
                'date': f"{ort}, {tag}. {monat} {jahr}"
            })

doc.close()

# Dedupliziere
seen = set()
for lec in lectures_found:
    key = lec['title'][:30]
    if key not in seen:
        seen.add(key)
        print(f"  Seite {lec['page']:3d}: {lec['title']}")
        print(f"            {lec['date']}")

print(f"\n=== Gesamt: {len(seen)} Vorträge gefunden ===")






