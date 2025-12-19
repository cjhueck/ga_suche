#!/usr/bin/env python3
"""Debuggt das Lecture-Page-Mapping für GA068B"""
import sys
import io
import re
import json
import fitz
from pathlib import Path
from difflib import SequenceMatcher

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")

def normalize_text(text):
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", text)
    s = s.replace("\u00ad", "").replace("\u00a0", " ")
    s = s.lower()
    s = s.replace("ß", "ss")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def extract_page_number(page, pdf_index, total_pages):
    page_height = page.rect.height
    blocks = page.get_text("blocks")
    max_page = min(total_pages + 100, 1200)
    footer_threshold = page_height * 0.85
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
                    candidates.append((num, 10, y_bottom))
                    continue
        
        m = re.search(r"[-–—]\s*(\d+)\s*[-–—]", text)
        if m:
            num = int(m.group(1))
            if 1 <= num <= max_page:
                candidates.append((num, 8, y_bottom))
                continue
        
        compact = text.replace(" ", "")
        if re.fullmatch(r"[\(\[\{<]*\d{1,4}[\)\]\}>]*[.\-–—,:;!]*", compact):
            num = int(re.search(r"\d{1,4}", compact).group(0))
            if 1 <= num <= max_page and num < 1000:
                candidates.append((num, 5, y_bottom))
    
    if candidates:
        candidates.sort(key=lambda c: (-c[1], -c[2]))
        return candidates[0][0]
    
    return pdf_index + 1

# Finde PDF für GA068B
pdf_path = None
for p in PDF_DIR.glob("*.pdf"):
    if "068b" in p.name.lower():
        pdf_path = p
        break

if not pdf_path:
    print("PDF nicht gefunden")
    sys.exit(1)

print(f"PDF: {pdf_path.name}\n")

# Extrahiere Seiten
doc = fitz.open(pdf_path)
page_texts = []
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text") or ""
    page_num = extract_page_number(page, i, len(doc))
    if text.strip():
        page_texts.append((page_num, text))

doc.close()

# Lade den Vortrag GA068b/5
search_text = ""
for f in Path('.').glob('steiner-full-lectures-*.json'):
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        for lec in data.get('lectures', []):
            if lec.get('ID') == 'GA068b/5':
                paras = lec.get('paragraphs', [])
                if paras:
                    first_para = paras[0].get('content', '')
                    search_text = normalize_text(first_para)[:1000]
                break
    except:
        pass
    if search_text:
        break

print(f"Suchtext (erste 200 Zeichen): {search_text[:200]}\n")

# Suche im PDF
print("=== Suche nach Vortrag GA068b/5 ===\n")

for page_num, page_text in page_texts:
    page_norm = normalize_text(page_text)
    
    # Teste verschiedene Suchlängen
    for search_len in [200, 150, 100, 80, 60, 40]:
        if search_len > len(search_text):
            continue
        search_key = search_text[:search_len]
        if search_key in page_norm:
            print(f"GEFUNDEN auf Seite {page_num} (Suchlänge {search_len})")
            pos = page_norm.find(search_key)
            print(f"  Kontext: ...{page_norm[max(0,pos-20):pos+100]}...")
            print()
            break
    else:
        continue
    break









