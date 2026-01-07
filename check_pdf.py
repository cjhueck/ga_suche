#!/usr/bin/env python3
import fitz

pdf_path = "Steiner_GA_pdf/Steiner, Rudolf GA 093, 1991 - Die Tempellegende und die goldene Legende.pdf"
doc = fitz.open(pdf_path)

print(f"PDF hat {len(doc)} Seiten")
print()

# Prüfe verschiedene Seiten
for pdf_page in [6, 7, 8, 14, 15, 20, 21, 22, 23, 30]:
    if pdf_page < len(doc):
        text = doc[pdf_page].get_text()
        first_200 = text[:200].replace("\n", " | ")
        print(f"PDF-Seite {pdf_page+1} (Index {pdf_page}):")
        print(f"  Anfang: {first_200}")
        print()

doc.close()











