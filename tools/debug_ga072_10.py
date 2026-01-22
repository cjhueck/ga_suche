#!/usr/bin/env python3
import sys
sys.path.insert(0, 'tools')
from generate_pagebreaks_with_pdf import extract_pdf_pages, find_pagebreak_position, remove_existing_markers
import json

pdf_pages = extract_pdf_pages('Steiner_GA_pdf/Steiner, Rudolf GA 072, 1990 - Freiheit, Unsterblichkeit, soziales Leben.pdf')

# Zeige Seitenzahlen um 388-390
print("PDF-Seiten 385-395:")
for pdf_idx, page_num, prev_end, this_start in pdf_pages:
    if 385 <= page_num <= 395:
        print(f"  S.{page_num}")

print()

# Prüfe auf fehlende fortlaufende Seitenzahlen
all_pages = sorted([p[1] for p in pdf_pages if 376 <= p[1] <= 438])
print(f"Seiten in GA072/10 Bereich: {all_pages}")

expected = list(range(376, 439))
missing = set(expected) - set(all_pages)
print(f"Fehlende Seiten: {sorted(missing)}")

extra = set(all_pages) - set(expected)
print(f"Unerwartete Seiten: {sorted(extra)}")

