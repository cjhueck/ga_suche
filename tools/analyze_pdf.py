import fitz
from pathlib import Path
import sys

ga = sys.argv[1] if len(sys.argv) > 1 else 'GA003'

# Extrahiere Nummer aus GA
ga_num = ga.replace('GA', '').replace('ga', '').zfill(3)

pdf_dir = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')
pdf_files = list(pdf_dir.glob(f'*GA {ga_num}*.pdf')) + list(pdf_dir.glob(f'*GA{ga_num}*.pdf'))

if not pdf_files:
    print(f'Kein PDF für {ga} gefunden')
    sys.exit(1)

pdf_path = pdf_files[0]
print(f'PDF: {pdf_path.name}')

doc = fitz.open(pdf_path)

# Analysiere Seite 20 (sollte gedruckte Seitenzahl haben)
for page_idx in [10, 20, 30]:
    if page_idx >= len(doc):
        continue
    page = doc[page_idx]
    blocks = page.get_text('dict')['blocks']
    
    print(f'\nSeite {page_idx + 1} (PDF-Index {page_idx}):')
    
    # Zeige alle Textblöcke mit Y-Position
    all_texts = []
    for block in blocks:
        if 'lines' in block:
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        y = span['bbox'][1]
                        x = span['bbox'][0]
                        all_texts.append((y, x, text[:50]))
    
    # Sortiere nach Y-Position
    all_texts.sort()
    
    print('Erste 5 Texte (oben):')
    for y, x, text in all_texts[:5]:
        print(f'  Y={y:.0f}, X={x:.0f}: "{text}"')
    
    print('Letzte 5 Texte (unten):')
    for y, x, text in all_texts[-5:]:
        print(f'  Y={y:.0f}, X={x:.0f}: "{text}"')

doc.close()

