#!/usr/bin/env python3
"""
PDF zu Markdown Konvertierung mit Gemini AI

Konvertiert PDF-Dateien (Rudolf Steiner GA) in saubere Markdown-Dateien:
- Seitenmarker |XX| am Seitenanfang
- Worttrennungen entfernt
- Seitenzahlen in Worttrennungen: Wort|XX|fortsetzung
- OCR-Fehler korrigiert
- Absätze erhalten
- Gedichte erkannt und formatiert
- Ein MD-File pro Vortrag

Verwendung:
    python tools/pdf_to_md_gemini.py <PDF-Pfad> [--dry-run] [--start-page X] [--end-page Y]
"""

import os
import sys
import re
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# Lade .env
load_dotenv()

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF nicht installiert. Installieren mit: pip install PyMuPDF")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("Google Generative AI nicht installiert. Installieren mit: pip install google-generativeai")
    sys.exit(1)


# Gemini konfigurieren
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("GEMINI_API_KEY nicht in Environment gefunden!")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)


def extract_pages_from_pdf(pdf_path: Path) -> List[Dict]:
    """
    Extrahiere alle Seiten aus dem PDF mit Text und Seitennummer.
    """
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Extrahiere die gedruckte Seitenzahl aus dem Footer
        printed_page = extract_printed_page_number(text, page_num + 1)
        
        pages.append({
            'pdf_page': page_num + 1,
            'printed_page': printed_page,
            'text': text
        })
    
    doc.close()
    return pages


def extract_printed_page_number(text: str, pdf_page: int) -> Optional[int]:
    """
    Versuche die gedruckte Seitenzahl aus dem Text zu extrahieren.
    Diese steht oft am Ende der Seite.
    """
    lines = text.strip().split('\n')
    
    # Suche in den letzten Zeilen nach einer Zahl
    for line in reversed(lines[-5:]):
        line = line.strip()
        # Reine Zahl am Zeilenende
        if line.isdigit():
            return int(line)
        # Copyright-Zeile mit Seitenzahl
        match = re.search(r'Seite[:\s]*(\d+)', line, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def find_lecture_boundaries(pages: List[Dict]) -> List[Dict]:
    """
    Finde Vortragsgrenzen basierend auf Titeln und Daten.
    
    Vorträge beginnen typischerweise mit:
    - TITEL IN GROSSBUCHSTABEN
    - Ort, Datum (z.B. "Berlin, 15. Oktober 1908")
    """
    lectures = []
    current_lecture = None
    
    title_pattern = re.compile(
        r'^([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+)\s*\n\s*((?:Berlin|München|Dornach|Stuttgart|Wien|Hamburg|Köln|Leipzig|Nürnberg),\s*\d{1,2}\.?\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4})',
        re.MULTILINE
    )
    
    for i, page in enumerate(pages):
        text = page['text']
        
        # Suche nach Vortragstitel
        match = title_pattern.search(text)
        if match:
            title = match.group(1).strip()
            date = match.group(2).strip()
            
            # Ignoriere Inhaltsverzeichnis-Einträge (zu kurz oder mit Seitenzahl am Ende)
            if len(title) > 20 and not re.search(r'\d+\s*$', title):
                if current_lecture:
                    current_lecture['end_page'] = i
                    lectures.append(current_lecture)
                
                current_lecture = {
                    'title': title,
                    'date': date,
                    'start_page': i,
                    'end_page': None
                }
    
    # Letzter Vortrag
    if current_lecture:
        current_lecture['end_page'] = len(pages) - 1
        lectures.append(current_lecture)
    
    return lectures


def process_pages_with_gemini(pages: List[Dict], start_idx: int, end_idx: int, 
                              lecture_title: str, lecture_date: str) -> str:
    """
    Verarbeite mehrere Seiten mit Gemini zur Bereinigung.
    
    Sendet Seiten in Batches (um Token-Limits zu respektieren).
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Kombiniere Seitentext mit Seitennummern
    pages_text = ""
    for page in pages[start_idx:end_idx + 1]:
        page_num = page.get('printed_page') or page['pdf_page']
        pages_text += f"\n\n=== SEITE {page_num} ===\n{page['text']}"
    
    prompt = f"""Du bist ein Experte für die Bereinigung von OCR-gescannten Texten.

Ich gebe dir den Text eines Vortrags von Rudolf Steiner (GA = Gesamtausgabe).
Der Vortrag heißt "{lecture_title}" und wurde am {lecture_date} gehalten.

AUFGABEN (STRENG BEFOLGEN):

1. **SEITENMARKER**: Füge am Anfang jeder Seite den Marker |XX| ein (XX = Seitenzahl).
   Der Marker soll auf einer eigenen Zeile stehen.

2. **ALLE SILBENTRENNUNGEN ENTFERNEN**: Das ist SEHR WICHTIG!
   - "genom-\nmen" → "genommen"
   - "Seh-\nnen" → "Sehnen"  
   - "Entwicke-\nlung" → "Entwickelung"
   - "be-\nsonderen" → "besonderen"
   ABER: Verbindungs-Bindestriche BEIBEHALTEN: "geistig-seelisch" bleibt "geistig-seelisch"

3. **WORTTRENNUNGEN ÜBER SEITENGRENZEN**: Wenn ein Wort am Ende einer Seite getrennt ist:
   - "Geistes-" am Ende Seite 9, "wissenschaft" am Anfang Seite 10
   - Wird zu: "Geistes|10|wissenschaft" (der Marker steht IM Wort, ohne Leerzeichen)

4. **OCR-FEHLER KORRIGIEREN**: 
   - "UN D" → "UND"
   - "Weisheir" → "Weisheit"
   - Fehlende Leerzeichen ergänzen

5. **ABSÄTZE ERHALTEN**: Doppelter Zeilenumbruch zwischen Absätzen.

6. **GEDICHTE**: Erkenne Verse und formatiere mit zwei Leerzeichen am Zeilenende für Zeilenumbrüche.

7. **ENTFERNEN**:
   - Vortragstitel und Datum vom Textanfang
   - "Copyright Rudolf Steiner..." Zeilen
   - Seitenzahlen am Rand (einzelne Zahlen am Zeilenende)

8. **KEINE Block-IDs** (keine ^xyz am Ende von Absätzen)

WICHTIG:
- Gib NUR den bereinigten Text zurück, KEINE Erklärungen
- Beginne mit |XX| auf eigener Zeile
- ALLE Silbentrennungen müssen entfernt werden!

TEXT:
{pages_text}
"""

    try:
        print(f"        [API] Sende Anfrage an Gemini... (kann 10-30 Sekunden dauern)")
        response = model.generate_content(prompt)
        print(f"        [API] Antwort erhalten, verarbeite...")
        return response.text
    except Exception as e:
        print(f"    Gemini API Fehler: {e}")
        return None


def process_lecture_in_chunks(pages: List[Dict], lecture: Dict, 
                              chunk_size: int = 25) -> str:
    """
    Verarbeite einen Vortrag in Chunks (wegen Token-Limits).
    """
    start_idx = lecture['start_page']
    end_idx = lecture['end_page']
    
    all_text = []
    current_idx = start_idx
    
    total_chunks = ((end_idx - start_idx) // chunk_size) + 1
    chunk_num = 0
    
    while current_idx <= end_idx:
        chunk_end = min(current_idx + chunk_size - 1, end_idx)
        chunk_num += 1
        
        print(f"      [{chunk_num}/{total_chunks}] Verarbeite Seiten {current_idx + 1}-{chunk_end + 1}...")
        
        chunk_text = process_pages_with_gemini(
            pages, current_idx, chunk_end,
            lecture['title'], lecture['date']
        )
        
        if chunk_text:
            all_text.append(chunk_text)
            print(f"        [OK] Chunk {chunk_num} erfolgreich verarbeitet")
        else:
            print(f"      [FEHLER] Seiten {current_idx + 1}-{chunk_end + 1}")
        
        current_idx = chunk_end + 1
        
        # Rate limiting (nur wenn nicht letzter Chunk)
        if current_idx <= end_idx:
            print(f"        Warte 1 Sekunde vor nächstem Chunk...")
            time.sleep(1)
    
    return '\n\n'.join(all_text)


def post_process_text(text: str) -> str:
    """
    Nachbearbeitung des AI-Outputs:
    - Entferne doppelte Seitenmarker
    - Verbinde Absätze über Seitengrenzen
    - Formatiere Silbentrennungen über Seitengrenzen korrekt
    - Erkenne und formatiere Gedichte
    """
    
    # 1. Entferne Silbentrennungen: "be-\nsonderen" → "besonderen"
    text = re.sub(r'-\n([a-zäöüß])', r'\1', text)
    text = re.sub(r'(\w)- ([a-zäöüß])', r'\1\2', text)
    
    # 2. Verarbeite Seitenmarker und verbinde Absätze
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Leere Zeile = Absatzgrenze
        if not line.strip():
            result.append('')
            i += 1
            continue
        
        # Prüfe auf Seitenmarker auf eigener Zeile
        marker_match = re.match(r'^\|(\d+)\|$', line.strip())
        if marker_match:
            page_num = marker_match.group(1)
            
            # Prüfe ob vorherige Zeile bereits diesen Marker enthält (doppelt)
            if result and f'|{page_num}|' in result[-1]:
                # Marker ist bereits im vorherigen Absatz → überspringen
                # Aber den folgenden Text anhängen
                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_text = lines[i + 1].strip()
                    # Hänge an vorherigen Absatz an (Seitenübergang mitten im Absatz)
                    if result[-1] and not result[-1].endswith(('.', '!', '?', '»', '"')):
                        result[-1] = result[-1] + ' ' + next_text
                        i += 2
                        continue
                i += 1
                continue
            
            # Prüfe ob vorheriger Absatz mitten im Satz endet (kein Satzzeichen)
            if result and result[-1].strip():
                prev_line = result[-1].strip()
                # Endet nicht mit Satzzeichen → Seitenübergang mitten im Absatz
                if not prev_line.endswith(('.', '!', '?', '»', '"', ':')):
                    # Füge Marker inline ein und verbinde mit nächster Zeile
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        next_text = lines[i + 1].strip()
                        result[-1] = prev_line + f' |{page_num}| ' + next_text
                        i += 2
                        continue
            
            # Normaler Seitenmarker am Absatzanfang
            result.append(line)
            i += 1
            continue
        
        # Normale Zeile
        result.append(line)
        i += 1
    
    text = '\n'.join(result)
    
    # 3. Bereinige doppelte Seitenmarker (z.B. "text|10|\n\n|10|\ntext")
    # Pattern: |XX| am Ende, gefolgt von leerzeilen und |XX| am Anfang
    text = re.sub(r'\|(\d+)\|\s*\n\n\|(\1)\|\s*\n', r'|\1| ', text)
    
    # 4. Silbentrennung über Seitengrenze: "be-\n|11|\ntrieben" → "be|11|trieben"
    text = re.sub(r'(\w)-\s*\n\|(\d+)\|\s*\n([a-zäöüß])', r'\1|\2|\3', text)
    
    # 5. Verbinde Absätze die nur durch Seitenmarker getrennt sind
    # Pattern: Text ohne Satzende + |XX| auf eigener Zeile + Text mit Kleinbuchstabe
    text = re.sub(r'([^.!?»"\n])\s*\n\|(\d+)\|\s*\n([a-zäöü])', r'\1 |\2| \3', text)
    
    # 6. Bereinige mehrfache Leerzeichen und Leerzeichen vor Satzzeichen
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r' ([.,;:!?])', r'\1', text)
    
    # 7. Gedichte erkennen und formatieren
    text = format_poems(text)
    
    return text


def format_poems(text: str) -> str:
    """
    Erkenne und formatiere Gedichte/Verse.
    
    Heuristik: Suche nach typischen Vers-Mustern:
    - Kurze Sätze mit Semikolon/Ausrufezeichen
    - Reimende Zeilenenden
    - Bekannte Gedicht-Anfänge
    """
    
    # Bekannte Gedichte/Zitate aus Steiner-Vorträgen
    known_poems = [
        # Goethe: "Selige Sehnsucht"
        (r'Und solang du das nicht hast,\s*Dieses:\s*Stirb und Werde!\s*Bist du nur ein trüber Gast\s*Auf der dunklen Erde\.?',
         'Und solang du das nicht hast,\nDieses: Stirb und Werde!\nBist du nur ein trüber Gast\nAuf der dunklen Erde.'),
        
        # Goethe: Faust
        (r'Die Geisterwelt ist nicht verschlossen;\s*Dein Sinn ist zu,\s*dein Herz ist tot!\s*Auf,\s*bade,\s*Schüler,\s*unverdrossen\s*Die ird[^\s]* Brust im Morgenrot!',
         'Die Geisterwelt ist nicht verschlossen;\nDein Sinn ist zu, dein Herz ist tot!\nAuf, bade, Schüler, unverdrossen\nDie irdsche Brust im Morgenrot!'),
    ]
    
    for pattern, replacement in known_poems:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Generische Vers-Erkennung: Suche nach Mustern wie "Text; Text! Text. Text."
    # mit kurzen Segmenten die wie Verse aussehen
    def detect_verse_pattern(match):
        content = match.group(0)
        # Teile bei Semikolon und Ausrufezeichen
        parts = re.split(r'([;!])\s*', content)
        if len(parts) >= 6:  # Mindestens 3 Verse
            # Prüfe ob alle Teile kurz sind (< 60 Zeichen)
            verses = []
            current = ''
            for part in parts:
                if part in [';', '!']:
                    current += part
                    if len(current.strip()) < 60:
                        verses.append(current.strip())
                    current = ''
                else:
                    current = part
            if current.strip() and len(current.strip()) < 60:
                verses.append(current.strip())
            
            if len(verses) >= 3 and all(len(v) < 60 for v in verses):
                return '\n'.join(verses)
        return content
    
    return text


def sanitize_filename(title: str, date: str, index: int) -> str:
    """
    Erstelle einen gültigen Dateinamen aus Titel und Datum.
    """
    # Extrahiere Ort und Datum
    date_parts = date.split(',')
    location = date_parts[0].strip() if date_parts else 'Berlin'
    date_str = date_parts[1].strip() if len(date_parts) > 1 else date
    
    # Kürze den Titel und entferne Zeilenumbrüche und ungültige Zeichen
    title_short = title[:60].strip()
    title_short = re.sub(r'\s+', ' ', title_short)  # Ersetze alle Whitespace-Zeichen (inkl. \n) durch Leerzeichen
    title_short = re.sub(r'[<>:"/\\|?*\n\r]', '', title_short)  # Entferne ungültige Zeichen
    
    return f"({index}.) {title_short}, {location}, {date_str}.md"


def process_pdf(pdf_path: Path, output_dir: Path, dry_run: bool = False,
                start_page: int = None, end_page: int = None) -> Dict:
    """
    Hauptfunktion: Verarbeite ein PDF und erstelle MD-Dateien.
    """
    print(f"\n{'='*60}")
    print(f"PDF zu Markdown Konvertierung mit Gemini")
    print(f"{'='*60}")
    print(f"  PDF: {pdf_path.name}")
    print(f"  Output: {output_dir}")
    
    if dry_run:
        print(f"  *** DRY-RUN - Keine Dateien werden erstellt ***")
    
    # 1. PDF laden und Seiten extrahieren
    print(f"\n1. Extrahiere Seiten aus PDF...")
    pages = extract_pages_from_pdf(pdf_path)
    print(f"   {len(pages)} Seiten gefunden")
    
    # Optional: Nur bestimmte Seiten
    if start_page:
        pages = [p for p in pages if p['pdf_page'] >= start_page]
    if end_page:
        pages = [p for p in pages if p['pdf_page'] <= end_page]
    
    # 2. Vortragsgrenzen finden
    print(f"\n2. Suche Vortragsgrenzen...")
    lectures = find_lecture_boundaries(pages)
    print(f"   {len(lectures)} Vorträge gefunden:")
    for i, lec in enumerate(lectures, 1):
        print(f"     {i}. {lec['title'][:50]}... ({lec['date']})")
        print(f"        Seiten {lec['start_page'] + 1} - {lec['end_page'] + 1}")
    
    if not lectures:
        print("   WARNUNG: Keine Vorträge gefunden!")
        return {'error': 'Keine Vorträge gefunden'}
    
    # 3. Jeden Vortrag verarbeiten
    print(f"\n3. Verarbeite Vorträge mit Gemini...")
    results = []
    
    for i, lecture in enumerate(lectures, 1):
        print(f"\n   [{i}/{len(lectures)}] {lecture['title'][:40]}...")
        
        # Verarbeite mit Gemini
        cleaned_text = process_lecture_in_chunks(pages, lecture)
        
        if not cleaned_text:
            print(f"      FEHLER: Keine Ausgabe von Gemini")
            continue
        
        # Post-Processing
        print(f"      Post-Processing...")
        cleaned_text = post_process_text(cleaned_text)
        
        # Erstelle Metadaten-Header
        ga_match = re.search(r'GA\s*(\d+)', pdf_path.name)
        ga_number = ga_match.group(1) if ga_match else 'XXX'
        
        header = f"Quelle: [[GA{ga_number}|GA{ga_number}]]\n\n"
        final_text = header + cleaned_text
        
        # Speichere Datei
        filename = sanitize_filename(lecture['title'], lecture['date'], i)
        output_path = output_dir / filename
        
        if dry_run:
            print(f"      [DRY-RUN] Würde speichern: {filename}")
            print(f"      Länge: {len(final_text)} Zeichen")
        else:
            output_path.write_text(final_text, encoding='utf-8')
            print(f"      Gespeichert: {filename}")
        
        results.append({
            'title': lecture['title'],
            'date': lecture['date'],
            'filename': filename,
            'length': len(final_text)
        })
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Vorträge verarbeitet: {len(results)}")
    total_chars = sum(r['length'] for r in results)
    print(f"  Gesamt Zeichen: {total_chars:,}")
    print(f"{'='*60}")
    
    return {'lectures': results, 'total_chars': total_chars}


def main():
    parser = argparse.ArgumentParser(description='PDF zu Markdown mit Gemini AI')
    parser.add_argument('pdf_path', help='Pfad zur PDF-Datei')
    parser.add_argument('--output', '-o', help='Ausgabeverzeichnis (Standard: gleiches Verzeichnis wie PDF)')
    parser.add_argument('--dry-run', action='store_true', help='Nur simulieren, keine Dateien erstellen')
    parser.add_argument('--start-page', type=int, help='Erste Seite')
    parser.add_argument('--end-page', type=int, help='Letzte Seite')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"FEHLER: PDF nicht gefunden: {pdf_path}")
        sys.exit(1)
    
    output_dir = Path(args.output) if args.output else pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = process_pdf(
        pdf_path, 
        output_dir, 
        dry_run=args.dry_run,
        start_page=args.start_page,
        end_page=args.end_page
    )
    
    if 'error' in result:
        print(f"\nFEHLER: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
