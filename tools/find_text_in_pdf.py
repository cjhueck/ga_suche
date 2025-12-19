#!/usr/bin/env python3
"""Sucht einen Text im PDF und zeigt alle Vorkommen"""
import sys
import io
import re
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

pdf_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
ga = sys.argv[1].upper() if len(sys.argv) > 1 else 'GA068B'
search = sys.argv[2] if len(sys.argv) > 2 else 'verehrte anwesende'

# Finde PDF
ga_num = ga.replace('GA', '').lower()
pdfs = [p for p in pdf_dir.glob("*.pdf") if ga_num in p.name.lower()]
if not pdfs:
    print(f"Kein PDF für {ga}")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"PDF: {pdf_path.name}")
print(f"Suche: '{search}'\n")

doc = fitz.open(pdf_path)

def normalize(text):
    s = text.lower()
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('ß', 'ss')
    return s

search_norm = normalize(search)
print(f"Normalisiert: '{search_norm}'")

print(f"=== Vorkommen von '{search}' ===\n")

for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text")
    text_norm = normalize(text)
    
    if search_norm in text_norm:
        # Extrahiere gedruckte Seitenzahl
        lines = text.strip().split('\n')
        page_num = '?'
        for line in lines[-3:]:
            if line.strip().isdigit():
                page_num = line.strip()
                break
        
        # Zeige Kontext
        pos = text_norm.find(search_norm)
        start = max(0, pos - 30)
        end = min(len(text_norm), pos + len(search_norm) + 50)
        context = text_norm[start:end].replace('\n', ' ')
        
        print(f"PDF-Index {i:3d}, Seite {page_num}: ...{context}...")

doc.close()


