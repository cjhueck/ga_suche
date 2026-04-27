import re, subprocess, sys

pdf = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical Epistemological Idealistic and Goethean Perspectives.pdf'

# Versuche pdfminer zu importieren
try:
    from pdfminer.high_level import extract_text
    text = extract_text(pdf)
    print(f"PDF-Text extrahiert: {len(text)} Zeichen")
    
    search_terms = [
        's11229-011-9878',
        's10539-021-09818', 
        '9780198779063',
        'Bich, Leonardo',
        'Complex Emergence',
    ]
    for term in search_terms:
        idx = text.find(term)
        if idx >= 0:
            snippet = text[max(0,idx-200):idx+200]
            print(f"\n[GEFUNDEN] '{term}':")
            print(snippet.strip()[:400])
        else:
            print(f"[NICHT GEFUNDEN] '{term}'")
except ImportError:
    print("pdfminer nicht installiert - installiere...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pdfminer.six', '-q'])
    from pdfminer.high_level import extract_text
    text = extract_text(pdf)
    print(f"PDF-Text extrahiert: {len(text)} Zeichen")
    
    search_terms = ['s11229-011-9878', 's10539-021-09818', '9780198779063', 'Bich, Leonardo']
    for term in search_terms:
        idx = text.find(term)
        if idx >= 0:
            print(f"\n[GEFUNDEN] '{term}':")
            print(text[max(0,idx-150):idx+200].strip()[:400])
        else:
            print(f"[NICHT GEFUNDEN] '{term}'")
