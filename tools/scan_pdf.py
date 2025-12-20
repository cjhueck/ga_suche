#!/usr/bin/env python3
"""Scannt ein PDF und zeigt die Struktur"""
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068C'
start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 300
end_page = int(sys.argv[3]) if len(sys.argv) > 3 else 350

ga_num = ga.replace('GA', '').lower()
pdf_path = None
for p in PDF_DIR.glob("*.pdf"):
    if ga_num in p.name.lower():
        pdf_path = p
        break

if not pdf_path:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

print(f"PDF: {pdf_path.name}")
print(f"Zeige Seiten {start_page}-{end_page}\n")

doc = fitz.open(pdf_path)
total = len(doc)
print(f"Gesamt: {total} Seiten\n")

for i in range(max(0, start_page), min(total, end_page)):
    page = doc[i]
    text = page.get_text("text").strip()
    # Erste Zeilen zeigen
    lines = text.split('\n')[:3]
    preview = ' | '.join(l.strip() for l in lines if l.strip())[:80]
    print(f"Seite {i:3d}: {preview}")

doc.close()












