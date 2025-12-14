"""Analysiert das Layout einer PDF-Seite: Haupttext vs. Fußnoten."""
import fitz

pdf_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\Steiner, Rudolf GA 001, 1987 - Einleitungen zu Goethes naturwissenschaftlichen Schriften.pdf'
doc = fitz.open(pdf_path)

# Analysiere Seite 9 (hat Fußnoten)
page = doc[8]  # 0-basiert
blocks = page.get_text("blocks")  # Gibt Textblöcke mit Position zurück

print(f"Seite 9 - {len(blocks)} Textblöcke:\n")
print(f"{'Y-Pos':<8} {'Text (gekürzt)':<70}")
print("-" * 80)

for block in sorted(blocks, key=lambda b: b[1]):  # Sortiert nach Y-Position
    x0, y0, x1, y1, text, block_no, block_type = block
    if block_type == 0:  # Nur Textblöcke
        text_clean = text.replace('\n', ' ').strip()[:65]
        if text_clean and not text_clean.startswith('Copyright'):
            print(f"{y0:<8.0f} {text_clean}...")

doc.close()

