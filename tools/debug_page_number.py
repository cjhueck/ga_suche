#!/usr/bin/env python3
"""Debuggt die Seitenzahl-Extraktion für eine PDF-Seite"""
import sys
import io
import re
import fitz
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")

# Finde PDF für GA068B
pdf_path = None
for p in PDF_DIR.glob("*.pdf"):
    if "068b" in p.name.lower():
        pdf_path = p
        break

doc = fitz.open(pdf_path)

# Finde die Seite mit "Verehrte Anwesende! Unter denjenigen"
target_idx = None
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text").lower()
    if "verehrte anwesende! unter denjenigen anschauungen" in text:
        target_idx = i
        break

if target_idx is None:
    print("Seite nicht gefunden")
    sys.exit(1)

page = doc[target_idx]
print(f"PDF-Index: {target_idx}")
print(f"Seitenhöhe: {page.rect.height}")
print()

# Zeige alle Blöcke und ihre Position
print("=== Alle Textblöcke ===\n")
blocks = page.get_text("blocks")
footer_threshold = page.rect.height * 0.85
print(f"Footer-Schwelle: {footer_threshold:.1f}")
print()

for i, block in enumerate(blocks):
    if len(block) < 7 or block[6] != 0:
        continue
    x0, y0, x1, y1 = block[:4]
    text = (block[4] or "").strip().replace('\n', ' ')[:60]
    in_footer = "FOOTER" if y1 > footer_threshold else ""
    print(f"Block {i:2d}: y={y1:6.1f} {in_footer:8s} '{text}'")

# Zeige was als Seitenzahl extrahiert würde
print("\n=== Kandidaten für Seitenzahl ===\n")
max_page = 1200
candidates = []

for block in blocks:
    if len(block) < 7 or block[6] != 0:
        continue
    y_bottom = float(block[3])
    text = (block[4] or "").strip()
    if not text or y_bottom < footer_threshold:
        continue
    
    m = re.search(r"Seite:\s*([\d\s]+)", text)
    if m:
        num_str = m.group(1).replace(" ", "").strip()
        if num_str.isdigit():
            num = int(num_str)
            if 1 <= num <= max_page:
                candidates.append((num, 10, y_bottom, "Seite: X", text[:40]))
                continue
    
    m = re.search(r"[-–—]\s*(\d+)\s*[-–—]", text)
    if m:
        num = int(m.group(1))
        if 1 <= num <= max_page:
            candidates.append((num, 8, y_bottom, "- X -", text[:40]))
            continue
    
    compact = text.replace(" ", "")
    if re.fullmatch(r"[\(\[\{<]*\d{1,4}[\)\]\}>]*[.\-–—,:;!]*", compact):
        num = int(re.search(r"\d{1,4}", compact).group(0))
        if 1 <= num <= max_page and num < 1000:
            candidates.append((num, 5, y_bottom, "standalone", text[:40]))

for c in candidates:
    print(f"  Kandidat: {c[0]:4d}, Priorität: {c[1]}, y={c[2]:.1f}, Typ: {c[3]}, Text: '{c[4]}'")

if candidates:
    candidates.sort(key=lambda c: (-c[1], -c[2]))
    print(f"\n  GEWÄHLT: Seite {candidates[0][0]}")

doc.close()












