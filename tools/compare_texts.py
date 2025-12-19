#!/usr/bin/env python3
"""Vergleicht PDF-Text mit JSON-Text für eine GA"""
import json
import sys
import io
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 50

# Finde PDF
pdf_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga_num = ga.replace('GA', '').zfill(3)
pdfs = list(pdf_dir.glob(f"*{ga_num}*")) + list(pdf_dir.glob(f"*GA {ga_num}*"))

if not pdfs:
    print(f"Kein PDF für {ga} gefunden")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"PDF: {pdf_path.name}")
print(f"Seite: {page_num}")

# Extrahiere PDF-Text
doc = fitz.open(pdf_path)
if page_num >= len(doc):
    print(f"Seite {page_num} existiert nicht (max: {len(doc)-1})")
    sys.exit(1)

page = doc[page_num]
pdf_text = page.get_text("text").strip()
doc.close()

print(f"\n=== PDF-Text (Seite {page_num}, erste 500 Zeichen) ===")
print(pdf_text[:500])

# Finde JSON-Text
print(f"\n=== JSON-Text (erster Vortrag, erste 500 Zeichen) ===")
for f in Path('.').glob('steiner-full-lectures-*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        lectures = data.get('lectures', [])
        matching = [l for l in lectures if (l.get('gaNumber', '') or '').upper() == ga]
        if matching:
            lec = matching[0]
            paras = lec.get('paragraphs', [])
            if paras:
                full_text = ' '.join(p.get('content', '') for p in paras[:5])
                print(full_text[:500])
            break
    except:
        pass


