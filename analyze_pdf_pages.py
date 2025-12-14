import fitz
import re

pdf_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf\Steiner, Rudolf GA 001, 1987 - Einleitungen zu Goethes naturwissenschaftlichen Schriften.pdf'
doc = fitz.open(pdf_path)

print(f'PDF hat {len(doc)} Seiten\n')
print('=== ANALYSE DER ERSTEN 20 SEITEN ===\n')
print(f'{"PDF-Seite":<12} {"Fußzeile Seite":<15} {"Letzte Textzeile (ohne Copyright)":<60}')
print('-' * 90)

for i in range(20):
    text = doc[i].get_text()
    
    # Extrahiere die Seitenzahl aus "Seite: X" (mit Leerzeichen zwischen Ziffern)
    seite_match = re.search(r'Seite:\s*([\d\s]+)', text)
    if seite_match:
        page_str = seite_match.group(1).replace(' ', '').strip()
        printed_page = page_str if page_str.isdigit() else '?'
    else:
        printed_page = '?'
    
    # Extrahiere die letzte Zeile des Inhalts (ohne Copyright)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    content_lines = [l for l in lines if not l.startswith('Copyright') and not l.startswith('Buch:') and not l.startswith('Seite:') and len(l) > 3]
    
    # Filtere Seitenzahlen am Ende
    while content_lines and content_lines[-1].replace(' ', '').isdigit():
        content_lines = content_lines[:-1]
    
    last_line = content_lines[-1][:55] if content_lines else '(leer)'
    
    print(f'{i+1:<12} {printed_page:<15} {last_line}...')

doc.close()
