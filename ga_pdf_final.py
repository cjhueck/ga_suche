# -*- coding: utf-8 -*-
"""
GA PDF Final - Finale perfekte Version
"""
import sys, io, os, re
from pathlib import Path
import fitz
import random
import string
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF_FOLDER = r'C:\Users\chuec\OneDrive\Anthroposophie\GA\GA Neu und Alt\GA'
OUTPUT_BASE = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'


def process_ga_pdf(ga_number, indizes_hinzufuegen=False):
    """Kompletter Workflow"""
    
    print("="*80)
    print(f"GA {ga_number} - PDF Extraktion")
    if indizes_hinzufuegen:
        print("  (mit Obsidian-Indizes)")
    print("="*80)
    
    # Finde PDF
    import glob
    # Versuche zuerst exakten Match (z.B. GA185a*.pdf), dann allgemeiner
    matches = []
    for pattern in [f"GA{ga_number}*.pdf", f"GA{ga_number.upper()}*.pdf"]:
        matches = glob.glob(os.path.join(PDF_FOLDER, pattern))
        if matches:
            break
    
    # Falls nicht gefunden und es eine reine Zahl ist, versuche mit führenden Nullen
    if not matches and ga_number.isdigit():
        ga_int = int(ga_number)
        for pattern in [f"GA{ga_int:03d}*.pdf"]:
            matches = glob.glob(os.path.join(PDF_FOLDER, pattern))
            if matches:
                break
    
    if not matches:
        print("PDF nicht gefunden")
        return
    
    pdf_path = matches[0]
    print(f"PDF: {os.path.basename(pdf_path)}\n")
    
    # Öffne PDF
    doc = fitz.open(pdf_path)
    print(f"Seiten: {len(doc)}")
    
    # Setup Ordner
    # Formatiere GA-Nummer: wenn nur Ziffern, dann mit führenden Nullen, sonst wie ist
    if ga_number.isdigit():
        ga_formatted = ga_number.zfill(3)
    else:
        ga_formatted = ga_number
    output_dir = os.path.join(OUTPUT_BASE, f"GA{ga_formatted}-Final")
    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Extrahiere seitenweise
    print("Extrahiere PDF...")
    pages = []
    image_count = 0
    
    for pnum in range(len(doc)):
        page = doc[pnum]
        text = page.get_text()
        
        # Bilder
        imgs = []
        for idx, img in enumerate(page.get_images()):
            xref = img[0]
            base = doc.extract_image(xref)
            fname = f"page_{pnum+1}_img_{idx+1}.{base['ext']}"
            fpath = os.path.join(assets_dir, fname)
            with open(fpath, "wb") as f:
                f.write(base["image"])
            imgs.append(f"assets/{fname}")
            image_count += 1
        
        pages.append({'num': pnum+1, 'text': text, 'images': imgs})
    
    doc.close()
    print(f"  Bilder: {image_count}\n")
    
    # Finde ersten echten Vortrag (nicht TOC)
    print("Finde Vortragsbeginn...")
    start_page = 0
    # Suche nach jedem möglichen Vortragstitel MIT Ortsangabe (echter Vortrag, nicht TOC)
    # Pattern: [TITEL], [irgendetwas], Datum
    # Format: "[TITEL], [Öffentlicher Vortrag, ] Ort, Tag. Monat Jahr"
    # Einfaches Pattern das alles matched: TITEL, REST, DATUM
    vortrag_pattern = r'[A-ZÄÖÜ].{4,},\s+.+?,\s+\d{1,2}\.\s+\w+\s+\d{4}'
    for i, p in enumerate(pages):
        # Entferne Zeilenumbrüche und Bindestriche am Zeilenende aus dem Text für die Suche
        text_single_line = p['text'].replace('-\n', '').replace('\n', ' ').replace('  ', ' ')
        # Suche nach jedem Vortragstitel MIT Ortsangabe und Datum
        match = re.search(vortrag_pattern, text_single_line)
        if match:
            # Prüfe ob danach >1000 Zeichen Text kommt (echter Vortrag, nicht TOC)
            remaining = text_single_line[match.end():]
            if len(remaining) > 1000:
                start_page = i
                print(f"  Start: Seite {p['num']} ({match.group(0)[:60]}...)\n")
                break
    
    # Finde Anhang (für Split, nicht für vollständige Datei)
    end_page = len(pages) - 5
    for i in range(start_page + 20, len(pages)):
        if re.search(r'^(ANHANG|HINWEISE|ANMERKUNGEN)\s*$', pages[i]['text'], re.M):
            end_page = i
            break
    
    # Baue Text für Split (nur Vorträge, ohne TOC/Anhang)
    full_text = []
    for i in range(start_page, end_page):
        full_text.append(pages[i]['text'])
        for img in pages[i]['images']:
            full_text.append(f"\n![Abbildung]({img})\n")
    
    text = '\n'.join(full_text)
    
    # Bereinige Text für Split
    print("Bereinige Text...")
    text = bereinige_text(text)
    
    # Markiere Vorträge (für Split)
    print("Markiere Vortraege...")
    text, vcount = markiere_vortraege(text)
    print(f"  Gefunden: {vcount} Vortraege\n")
    
    # Erstelle vollständige Datei (alle Seiten: bibliographische Angaben, TOC, Vorträge, Anhang)
    print("Erstelle vollständige GA-Datei...")
    full_text_complete = []
    for i in range(len(pages)):  # Alle Seiten
        full_text_complete.append(pages[i]['text'])
        for img in pages[i]['images']:
            full_text_complete.append(f"\n![Abbildung]({img})\n")
    
    text_complete = '\n'.join(full_text_complete)
    
    # Bereinige vollständigen Text
    text_complete = bereinige_text(text_complete)
    
    # Formatiere vollständige Datei (bibliographische Angaben, Vortragstitel, Hinweise)
    text_complete = formatiere_vollstaendige_datei(text_complete, ga_number)
    
    # Korrigiere Rechtschreibung
    text_complete = korrigiere_rechtschreibung(text_complete)
    
    # Füge Indizes hinzu (wenn gewünscht)
    if indizes_hinzufuegen:
        print("Füge Indizes zur vollständigen Datei hinzu...")
        bestehende_indizes = sammle_bestehende_indizes(output_dir)
        text_complete = fuege_indizes_hinzu(text_complete, bestehende_indizes)
    
    # Entferne nur Vortragsmarker (falls welche drin sind)
    text_complete = re.sub(r'<!-- VORTRAG_START:.*?-->', '', text_complete)
    text_complete = re.sub(r'\n\s*\n\s*\n+', '\n\n', text_complete)  # Mehrfache Leerzeilen reduzieren
    
    # Speichere vollständige Datei
    full_md_path = os.path.join(output_dir, f"GA{ga_formatted}-Vollständig.md")
    with open(full_md_path, 'w', encoding='utf-8') as f:
        f.write(text_complete)
    print(f"  Gespeichert: {Path(full_md_path).name}\n")
    
    # Splitte
    print("Erstelle Einzeldateien...")
    files = splitte_vortraege(text, output_dir, ga_number, indizes_hinzufuegen=indizes_hinzufuegen)
    
    print(f"\n{'='*80}")
    print(f"FERTIG: {len(files)} Vortraege in {output_dir}")
    print("="*80)
    
    return files


def bereinige_text(text):
    """Text-Bereinigung - wie in GA145_raw.md Beispiel"""
    # Korrigiere Datumsformat: entferne Komma vor Jahreszahl (z.B. "20. Februar, 1917" -> "20. Februar 1917")
    text = re.sub(r'(\d{1,2}\.\s+\w+),\s+(\d{4})', r'\1 \2', text)
    
    # Füge fehlendes Komma vor Datum ein: "Hamburg 30. Juni 1918" -> "Hamburg, 30. Juni 1918"
    # Aber nur wenn vorher auch ein Komma war (Vortragstitel)
    text = re.sub(r'([A-ZÄÖÜ].{10,}),\s+([A-Za-zäöüÄÖÜß][a-zäöüß\.\s]+)\s+(\d{1,2}\.\s+\w+\s+\d{4})', r'\1, \2, \3', text)
    
    # Korrigiere Jahrhundert-Angaben: "19.\nJahrhundert" -> "19. Jahrhundert"
    text = re.sub(r'(\d{1,2}\.)\s*\n\s*(Jahrhundert)', r'\1 \2', text)
    
    lines = text.split('\n')
    out = []
    
    # Entferne Seitenumbrüche UND korrigiere Worttrennungen über Seitenumbrüche hinweg
    cleaned_lines = []
    i = 0
    while i < len(lines):
        # Prüfe ob Seitenumbruch
        if re.match(r'^-{3,}$', lines[i].strip()):
            # Wenn vorherige Zeile mit Bindestrich endet, markiere für Zusammenfügung
            if cleaned_lines and cleaned_lines[-1].rstrip()[-1] in '-–—':
                # Überspringe Seitenumbruch
                i += 1
                while i < len(lines) and (re.match(r'^Seite \d+$', lines[i].strip()) or re.match(r'^-{3,}$', lines[i].strip())):
                    i += 1
                # Wenn nach Seitenumbruch Text kommt, füge direkt an vorherige Zeile an
                if i < len(lines) and lines[i].strip():
                    # Entferne Bindestrich von vorheriger Zeile und füge Text an
                    prev_line = cleaned_lines[-1].rstrip()
                    cleaned_lines[-1] = prev_line[:-1] + lines[i].strip()
                    i += 1
                    continue
            else:
                # Normale Seitenumbruch-Entfernung
                i += 1
                while i < len(lines) and (re.match(r'^Seite \d+$', lines[i].strip()) or re.match(r'^-{3,}$', lines[i].strip())):
                    i += 1
                continue
        cleaned_lines.append(lines[i])
        i += 1
    
    lines = cleaned_lines
    
    # Zusammenfügen
    for i, curr in enumerate(lines):
        prev = out[-1] if out else None
        
        if not prev or not curr.strip():
            out.append(curr)
            continue
        
        # Überschrift/Bild bleibt getrennt
        if re.match(r'^(#{1,6}\s+|!\[)', curr):
            out.append(curr)
            continue
        
        prev_trim = prev.rstrip()
        if not prev_trim:
            out.append(curr)
            continue
        
        last = prev_trim[-1]
        curr_stripped = curr.strip()
        
        # Absätze mit Punkt: Prüfe ob nächste Zeile ein neuer Satz ist oder Fortsetzung
        if last == '.':
            # Wenn nächste Zeile mit Großbuchstabe beginnt UND vorherige Zeile relativ kurz ist
            # → wahrscheinlich neuer Absatz
            # Wenn nächste Zeile mit Kleinbuchstabe beginnt → Fortsetzung (zusammenfügen)
            if curr_stripped and curr_stripped[0].islower():
                # Fortsetzung → zusammenfügen
                out[-1] = prev_trim + ' ' + curr_stripped
            else:
                # Neuer Satz → getrennt lassen
                out.append(curr)
        # Silbentrennung mit Bindestrich → OHNE Leerzeichen zusammenfügen
        elif last in '-–—':
            # Entferne Bindestrich und füge OHNE Leerzeichen zusammen
            out[-1] = prev_trim[:-1] + curr_stripped
        # Prüfe ob Leerzeile dazwischen war (Seitenumbruch wurde entfernt, aber Leerzeile bleibt)
        # Wenn vorherige Zeile mit Kleinbuchstabe endet und aktuelle mit Kleinbuchstabe beginnt
        # UND dazwischen war eine Leerzeile → wahrscheinlich Wortbruch über Seitenumbruch
        elif (prev_trim[-1].islower() and 
              curr_stripped and 
              curr_stripped[0].islower() and
              len(out) > 0 and 
              out[-1].strip() == prev_trim and
              i > 0 and lines[i-1].strip() == ''):
            # Wortbruch über Seitenumbruch → OHNE Leerzeichen zusammenfügen
            out[-1] = prev_trim + curr_stripped
        # Alles andere → MIT Leerzeichen zusammenfügen
        else:
            out[-1] = prev_trim + ' ' + curr_stripped
    
    # Leerzeilen zwischen Absätzen (nur nach Punkt, wenn nächster Satz mit Großbuchstabe beginnt)
    text2 = '\n'.join(out)
    lines2 = text2.split('\n')
    final = []
    for i, line in enumerate(lines2):
        final.append(line)
        # Nur wenn Zeile mit Punkt endet UND nächste Zeile mit Großbuchstabe beginnt → Leerzeile einfügen
        if line.strip() and line.strip()[-1] == '.':
            next_line = lines2[i+1] if i+1 < len(lines2) else ''
            if (next_line.strip() and 
                not next_line.startswith(('#', '!')) and
                next_line.strip()[0].isupper()):  # Nur wenn mit Großbuchstabe beginnt
                final.append('')
    
    # Finale Korrektur: Wortbrüche und falsche Umbrüche über Leerzeilen hinweg
    text3 = '\n'.join(final)
    lines3 = text3.split('\n')
    final2 = []
    i = 0
    while i < len(lines3):
        line = lines3[i]
        
        # Prüfe ob Zeile mit Bindestrich endet
        if line.strip() and line.strip()[-1] in '-–—':
            # Suche nächste nicht-leere Zeile (überspringe Leerzeilen)
            j = i + 1
            while j < len(lines3) and not lines3[j].strip():
                j += 1
            
            if j < len(lines3):
                next_line = lines3[j].strip()
                # Wenn nächste Zeile mit Kleinbuchstabe beginnt → Wortbruch
                if next_line and next_line[0].islower():
                    # Entferne Bindestrich von aktueller Zeile und füge zusammen
                    line_without_hyphen = line.rstrip()[:-1]
                    # Füge nächste Zeile direkt an (ohne Leerzeichen)
                    final2.append(line_without_hyphen + next_line)
                    i = j + 1
                    continue
        
        # Prüfe ob Zeile OHNE Punkt endet und nächste Zeile mit Kleinbuchstabe beginnt
        # → falscher Umbruch, zusammenfügen
        if line.strip() and line.strip()[-1] not in '.!?:;':
            # Suche nächste nicht-leere Zeile
            j = i + 1
            while j < len(lines3) and not lines3[j].strip():
                j += 1
            
            if j < len(lines3):
                next_line = lines3[j].strip()
                # Wenn nächste Zeile mit Kleinbuchstabe beginnt → falscher Umbruch
                if next_line and next_line[0].islower():
                    # Zusammenfügen mit Leerzeichen
                    final2.append(line.rstrip() + ' ' + next_line)
                    i = j + 1
                    continue
        
        final2.append(line)
        i += 1
    
    return '\n'.join(final2)


def formatiere_vollstaendige_datei(text, ga_number):
    """Formatiere vollständige GA-Datei mit bibliographischen Angaben, Vortragstiteln und Hinweisen"""
    lines = text.split('\n')
    out = []
    i = 0
    first_lecture_found = False
    
    # Vortragstitel-Pattern
    vortrag_pattern = r'^((?:ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER|Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Siebenter|Achter|Neunter|Zehnter|Elfter|Zwölfter|Dreizehnter|Vierzehnter|Fünfzehnter|Sechzehnter|Siebzehnter|Achtzehnter|Neunzehnter|Zwanzigster|Einundzwanzigster|Zweiundzwanzigster|Dreiundzwanzigster|Vierundzwanzigster|Fünfundzwanzigster)\s+(?:VORTRAG|Vortrag))'
    
    # Suche nach erster Zeile mit bibliographischen Angaben
    bib_line_idx = None
    for j, line in enumerate(lines[:20]):  # Suche in ersten 20 Zeilen
        if re.search(rf'GA\s*{ga_number}', line, re.IGNORECASE) and 'KOSMISCHE' in line.upper():
            bib_line_idx = j
            break
    
    # Formatiere bibliographische Angaben
    if bib_line_idx is not None:
        bib_line = lines[bib_line_idx].strip()
        # Versuche, die Zeile zu zerlegen
        # Pattern: GA 174 KOSMISCHE UND MENSCHLICHE GESCHICHTE ... RUDOLF STEINER ... Zeitgeschichtliche Betrachtungen ...
        parts = []
        
        # GA-Nummer
        ga_match = re.search(rf'GA\s*{ga_number}', bib_line, re.IGNORECASE)
        if ga_match:
            out.append(f"# GA {ga_number}")
            out.append("")
        
        # KOSMISCHE UND MENSCHLICHE GESCHICHTE
        if 'KOSMISCHE UND MENSCHLICHE GESCHICHTE' in bib_line.upper():
            kosm_match = re.search(r'KOSMISCHE\s+UND\s+MENSCHLICHE\s+GESCHICHTE', bib_line, re.IGNORECASE)
            if kosm_match:
                out.append("## KOSMISCHE UND MENSCHLICHE GESCHICHTE")
                out.append("")
        
        # Band-Nummer (z.B. "Fünfter Band")
        band_match = re.search(r'(\w+er\s+Band)', bib_line, re.IGNORECASE)
        if band_match:
            out.append(band_match.group(1))
            out.append("")
        
        # RUDOLF STEINER
        if 'RUDOLF STEINER' in bib_line.upper():
            out.append("RUDOLF STEINER")
            out.append("")
        
        # Zeitgeschichtliche Betrachtungen
        zeit_match = re.search(r'(Zeitgeschichtliche\s+Betrachtungen)', bib_line, re.IGNORECASE)
        if zeit_match:
            out.append(f"## {zeit_match.group(1)}")
            out.append("")
        
        # Zweiter Teil / Erster Teil etc.
        teil_match = re.search(r'(\w+er\s+Teil)', bib_line, re.IGNORECASE)
        if teil_match:
            out.append(teil_match.group(1))
            out.append("")
        
        # Vorträge-Info (z.B. "Zwölf Vorträge, gehalten in...")
        vortraege_match = re.search(r'(\d+\s+Vorträge[^.]*\.)', bib_line)
        if vortraege_match:
            out.append(vortraege_match.group(1))
            out.append("")
        
        # Überspringe die ursprüngliche Bib-Zeile
        i = bib_line_idx + 1
    
    # TOC erkennen und behalten
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # TOC erkennen (INHALT alleine oder mit Text)
        if not first_lecture_found and (re.match(r'^\s*I\s*N\s*H\s*A\s*L\s*T\s*$', stripped.upper()) or re.match(r'^\s*INHALT\s+', stripped.upper())):
            if re.match(r'^\s*INHALT\s+', stripped.upper()):
                # "INHALT" am Anfang - entferne nur "INHALT", behalte Rest
                cleaned = re.sub(r'^\s*INHALT\s+', '', line, flags=re.IGNORECASE)
                out.append(cleaned)
            else:
                out.append(line)
            i += 1
            continue
        
        # Prüfe ob es ein Vortragstitel ist (mit oder ohne Ortsangabe)
        # Pattern: VORTRAG(, Ort)?, Datum (Komma vor Jahr wurde bereits in bereinige_text entfernt)
        vortrag_match = re.match(vortrag_pattern + r'(?:,\s+[^,]+)?,\s+\d{1,2}\.\s+\w+\s+\d{4}', stripped)
        
        if vortrag_match:
            # Prüfe ob nach diesem Titel viel Text kommt, bevor der nächste Vortragstitel erscheint
            # Zuerst: Prüfe ob auf der gleichen Zeile nach dem Datum noch Text steht
            title_check_match = re.match(r'^(.+?,\s+\d{1,2}\.\s+\w+\s+\d{4})(.*)$', stripped)
            text_on_same_line = ''
            if title_check_match and title_check_match.group(2).strip():
                text_on_same_line = title_check_match.group(2).strip()
            
            # Suche nach dem nächsten Vortragstitel in den nächsten 50 Zeilen
            text_after = []
            if text_on_same_line:
                text_after.append(text_on_same_line)
                
            next_vortrag_idx = None
            for j in range(i+1, min(i+50, len(lines))):
                next_line = lines[j].strip()
                # Prüfe ob nächste Zeile auch ein Vortragstitel ist
                if re.match(vortrag_pattern + r'(?:,\s+[^,]+)?,\s+\d{1,2}\.\s+\w+\s+\d{4}', next_line):
                    next_vortrag_idx = j
                    break
                text_after.append(next_line)
            
            # Wenn kein nächster Vortragstitel gefunden, nimm die nächsten 50 Zeilen
            if next_vortrag_idx is None and not text_on_same_line:
                text_after = [lines[j].strip() for j in range(i+1, min(i+50, len(lines)))]
            
            text_after_str = ' '.join(text_after)
            
            # Echter Vortrag: >1000 Zeichen Text vor dem nächsten Vortragstitel
            # TOC-Eintrag: <1000 Zeichen Text vor dem nächsten Vortragstitel
            # Erhöhe Grenze von 500 auf 1000, um TOC-Einträge besser zu filtern
            if len(text_after_str) > 1000:
                # Echter Vortrag - markiere als H1
                if not first_lecture_found:
                    first_lecture_found = True
                out.append(f"# {stripped}")
                i += 1
                continue
            else:
                # TOC-Eintrag - behalte als normalen Text
                out.append(line)
                i += 1
                continue
        
        # Hinweise/Anmerkungen/Anhang als H1
        if re.match(r'^(HINWEISE|ANMERKUNGEN|ANHANG)\s*\.?\s*$', stripped, re.IGNORECASE):
            out.append(f"# {stripped.upper()}")
            i += 1
            continue
        
        # Normale Zeile
        out.append(line)
        i += 1
    
    return '\n'.join(out)


def entferne_toc(text):
    """Entferne Inhaltsverzeichnis aus dem Text"""
    lines = text.split('\n')
    out = []
    in_toc = False
    
    for i, line in enumerate(lines):
        # TOC erkennen (auch wenn "INHALT" am Anfang einer Zeile steht)
        if re.match(r'^\s*I\s*N\s*H\s*A\s*L\s*T\s*$', line.upper()) or re.match(r'^\s*INHALT\s+', line.upper()):
            in_toc = True
            # Wenn "INHALT" am Anfang steht, entferne es und den Rest der Zeile
            if re.match(r'^\s*INHALT\s+', line.upper()):
                # Entferne "INHALT" und alles danach bis zum ersten Vortragstitel
                cleaned = re.sub(r'^\s*INHALT\s+', '', line, flags=re.IGNORECASE)
                # Prüfe ob danach direkt ein Vortragstitel kommt
                if not re.match(r'^(ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER)\s+VORTRAG', cleaned):
                    continue  # Überspringe diese Zeile komplett
                else:
                    # Vortragstitel direkt nach INHALT - behalte nur den Vortragstitel
                    match = re.search(r'((?:ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER)\s+VORTRAG[^\n]*)', cleaned)
                    if match:
                        # Prüfe ob danach >500 Zeichen kommen
                        rest = '\n'.join(lines[i+1:i+10])
                        if len(rest) > 500:
                            in_toc = False
                            out.append(match.group(1))
                    continue
            continue
        
        # TOC endet bei erstem Vortrag mit viel Text danach
        if in_toc:
            # Prüfe ob es ein Vortragstitel ist
            if re.match(r'^(ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER)\s+VORTRAG', line):
                # Prüfe ob danach >500 Zeichen kommen
                rest = '\n'.join(lines[i+1:i+10])
                if len(rest) > 500:
                    in_toc = False
                    # Füge Vortragstitel hinzu
                    out.append(line)
                # Sonst weiter TOC überspringen
            continue
        
        out.append(line)
    
    return '\n'.join(out)


def markiere_vortraege(text):
    """Markiere Vorträge (ohne Titel im Text, nur Marker)"""
    lines = text.split('\n')
    out = []
    count = 0
    in_toc = False
    
    for i, line in enumerate(lines):
        # TOC erkennen und überspringen
        if re.match(r'^\s*I\s*N\s*H\s*A\s*L\s*T\s*$', line.upper()):
            in_toc = True
            continue
        
        # TOC endet bei erstem Vortrag mit viel Text danach
        # Unterstützt auch höhere Nummern
        if in_toc and re.match(r'^(ERSTER|I\.|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER)\s+VORTRAG', line):
            # Prüfe ob danach >500 Zeichen kommen
            rest = '\n'.join(lines[i+1:i+10])
            if len(rest) > 500:
                in_toc = False
        
        # Überspringe TOC-Zeilen
        if in_toc:
            continue
        
        # Markiere NUR Vorträge MIT Ortsangabe (echte Vorträge, nicht TOC)
        # Muster: 
        # 1. "DRITTER VORTRAG, Den Haag, 22. März 1913"
        # 2. "DIE ERKENNTNIS..., Öffentlicher Vortrag, St. Gallen, 15. November 1917"
        # 3. "DAS GEHEIMNIS..., St. Gallen, 16. November 1917"
        # Pattern: [TITEL], [irgendetwas], Datum
        
        # Pattern muss flexibel sein: Komma nach Titel ist Pflicht, Komma nach Ort ist optional
        # Format 1: "TITEL, Ort, Datum"
        # Format 2: "TITEL, Ort Datum" (ohne Komma nach Ort!)
        # Der Titel muss entweder "VORTRAG" enthalten ODER überwiegend GROSSBUCHSTABEN sein
        match = re.match(r'^([A-ZÄÖÜ].{4,}?),\s+(.+?)[,\s]+(\d{1,2}\.\s+\w+\s+\d{4})', line)
        
        if match:
            # Prüfe ob der Titel ein echter Vortragstitel ist:
            # 1. Enthält "VORTRAG" oder "Vortrag" ODER
            # 2. Mindestens 50% Großbuchstaben (ignoriere Leerzeichen und Satzzeichen)
            titel = match.group(1)
            if 'VORTRAG' not in titel.upper() and 'Vortrag' not in titel:
                # Zähle Großbuchstaben
                buchstaben = [c for c in titel if c.isalpha()]
                if buchstaben:
                    grossbuchstaben = [c for c in buchstaben if c.isupper()]
                    prozent_gross = len(grossbuchstaben) / len(buchstaben)
                    # Wenn weniger als 50% Großbuchstaben, ist es kein Vortragstitel
                    if prozent_gross < 0.5:
                        out.append(line)
                        i += 1
                        continue
        
        if match:
            # Extrahiere Ort aus dem "Rest"-Teil (kann "St. Gallen" oder "Erster Vortrag, Zürich" sein)
            rest_part = match.group(2).strip()
            # Wenn der Rest ein Komma enthält, ist der letzte Teil der Ort
            if ',' in rest_part:
                ort = rest_part.split(',')[-1].strip()
            else:
                ort = rest_part
            
            if len(ort) > 2:  # Echter Ort
                # TOC-Erkennung: Zähle wie viele Vortragstitel in den nächsten 10 Zeilen kommen
                # Wenn >2 Vortragstitel in den nächsten 10 Zeilen, dann ist es TOC
                vortrag_count_nearby = 0
                for j in range(i+1, min(i+10, len(lines))):
                    if re.match(r'^[A-ZÄÖÜ].{4,}?,\s+.+?,\s+\d{1,2}\.\s+\w+\s+\d{4}', lines[j]):
                        vortrag_count_nearby += 1
                
                # Wenn mehr als 2 Vortragstitel in den nächsten 10 Zeilen, ist es TOC -> überspringen
                if vortrag_count_nearby > 2:
                    continue
                
                # Prüfe ob nach diesem Titel viel Text kommt, bevor der nächste Vortragstitel erscheint
                # Zuerst: Prüfe ob auf der gleichen Zeile nach dem Datum noch Text steht
                title_check_match = re.match(r'^(.+?,\s+\d{1,2}\.\s+\w+\s+\d{4})(.*)$', line.strip())
                text_on_same_line = ''
                if title_check_match and title_check_match.group(2).strip():
                    text_on_same_line = title_check_match.group(2).strip()
                
                # Suche nach dem nächsten Vortragstitel in den nächsten 50 Zeilen
                text_after = []
                if text_on_same_line:
                    text_after.append(text_on_same_line)
                    
                next_vortrag_idx = None
                for j in range(i+1, min(i+50, len(lines))):
                    next_line = lines[j].strip()
                    # Prüfe ob nächste Zeile auch ein Vortragstitel ist (mit dem einfachen Pattern)
                    if re.match(r'^[A-ZÄÖÜ].{4,}?,\s+.+?,\s+\d{1,2}\.\s+\w+\s+\d{4}', next_line):
                        next_vortrag_idx = j
                        break
                    text_after.append(next_line)
                
                # Wenn kein nächster Vortragstitel gefunden, nimm die nächsten 50 Zeilen
                if next_vortrag_idx is None and not text_on_same_line:
                    text_after = [lines[j].strip() for j in range(i+1, min(i+50, len(lines)))]
                
                text_after_str = ' '.join(text_after)
                
                # Echter Vortrag: >1000 Zeichen Text vor dem nächsten Vortragstitel
                # TOC-Eintrag: <1000 Zeichen Text vor dem nächsten Vortragstitel
                # Erhöhe Grenze von 500 auf 1000, um TOC-Einträge besser zu filtern
                if len(text_after_str) > 1000:
                    # Trenne Titel vom Text (falls zusammenhängt)
                    title_line = line.strip()
                    # Wenn nach dem Datum noch Text kommt, trenne ihn ab
                    title_match = re.match(r'^(.+?,\s+\d{1,2}\.\s+\w+\s+\d{4})(.*)$', title_line)
                    if title_match:
                        remaining_text = title_match.group(2).strip()
                        # KEIN Titel mehr im Text, nur Marker mit Titel für Split
                        out.append('')
                        out.append(f'<!-- VORTRAG_START: {title_match.group(1)} -->')
                        out.append('')
                        if remaining_text:
                            out.append(remaining_text)
                    else:
                        out.append('')
                        out.append(f'<!-- VORTRAG_START: {title_line} -->')
                        out.append('')
                    count += 1
                    continue
        
        out.append(line)
    
    return '\n'.join(out), count


def korrigiere_rechtschreibung(text):
    """Korrigiere alte Rechtschreibung zu neuer"""
    # Ersetze lange Gedankenstriche durch kurze
    text = text.replace('—', '-')
    
    # Ersetze kk durch ck in deutschen Wörtern (Entwikklung → Entwicklung)
    # Pattern: kk innerhalb von Wörtern (mit Buchstaben davor und danach)
    def replace_kk(match):
        before = match.group(1)
        after = match.group(2)
        word = before + 'kk' + after
        
        # Überspringe wenn:
        # - Zu kurz (< 5 Zeichen)
        # - Enthält Sonderzeichen (URL, etc.)
        # - kk am Anfang des Wortes
        if len(word) < 5 or not before or any(c in word for c in ['/', ':', '.', '@', '_']):
            return match.group(0)
        
        # Ersetze kk durch ck
        return before + 'ck' + after
    
    kk_pattern = r'\b(\w+?)kk(\w+?)\b'
    text = re.sub(kk_pattern, replace_kk, text)
    
    # Wörterliste aus Obsidian-Plugin
    replacements = {
        # Häufigste
        'daß': 'dass',
        'Daß': 'Dass',
        'muß': 'muss',
        'mußt': 'musst',
        'mußte': 'musste',
        'mußtest': 'musstest',
        'mußtet': 'musstet',
        'mußten': 'mussten',
        'wußte': 'wusste',
        'gewußt': 'gewusst',
        'Bewußtsein': 'Bewusstsein',
        'bewußt': 'bewusst',
        'Bewußtseins': 'Bewusstseins',
        'Bewußtseinszustand': 'Bewusstseinszustand',
        'Bewußtseinszustände': 'Bewusstseinszustände',
        'Unbewußtsein': 'Unbewusstsein',
        'unbewußt': 'unbewusst',
        'Selbstbewußtsein': 'Selbstbewusstsein',
        'selbstbewußt': 'selbstbewusst',
        # Weitere häufige
        'ißt': 'isst',
        'iß': 'iss',
        'frißt': 'frisst',
        'Kuß': 'Kuss',
        'Fluß': 'Fluss',
        'Schloß': 'Schloss',
        'Haß': 'Hass',
        'Nuß': 'Nuss',
        'Faß': 'Fass',
        'Preß': 'Press',
        'Miß': 'Miss',
        'miß': 'miss',
        'nuß': 'nuss',
        'fluß': 'fluss',
        'schloß': 'schloss',
        'kuß': 'kuss',
        'haß': 'hass',
        'faß': 'fass',
        'preß': 'press',
        'Anschluß': 'Anschluss',
        'schluß': 'schluss',
        'Schluß': 'Schluss',
        # Weitere Formen
        'biß': 'biss',
        'riß': 'riss',
        'floß': 'floss',
        'schoß': 'schoss',
        # Weitere Korrekturen
        'Entschluß': 'Entschluss',
        'entschluß': 'entschluss',
        'Entschlüsse': 'Entschlüsse',  # Plural bleibt gleich
        'entschlüsse': 'entschlüsse',  # Plural bleibt gleich
        'müßte': 'müsste',
        'müßtest': 'müsstest',
        'müßtet': 'müsstet',
        'müßten': 'müssten',
        # ss zu ß (nach langem Vokal/Diphthong)
        'reisst': 'reißt',
        'Eiweiss': 'Eiweiß',
        'eiweiss': 'eiweiß',
        # Weitere häufige Korrekturen
        'läßt': 'lässt',
        'heisst': 'heißt',
        'weiss': 'weiß',
        # Zusammengesetzte Wörter mit Bindestrich
        'ChristusWesenheit': 'Christus-Wesenheit',
        'JohannesEvangelium': 'Johannes-Evangelium',
        'SeelischGeistiges': 'Seelisch-Geistiges',
        'GeistigSeelisches': 'Geistig-Seelisches',
        'geistigseelisch': 'geistig-seelisch',
        'seelischgeistig': 'seelisch-geistig',
        'westund mitteleuropäisch': 'west- und mitteleuropäisch',
        'von daoder von dorther': 'von da- oder von dorther',
        'EntwederOder': 'Entweder-Oder',
        # Weitere Prozeß-Varianten
        'Prozeß': 'Prozess',
        '..prozeß': '..prozess',
        # ss statt ss
        'dreissig': 'dreißig',
        'dreiunddreissig': 'dreiunddreißig',
    }
    
    # Ersetze alle Vorkommen
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def sammle_bestehende_indizes(folder):
    """Sammle alle bestehenden Obsidian-Indizes aus Markdown-Dateien"""
    indices = set()
    
    # Suche alle .md Dateien im Ordner
    md_files = glob.glob(os.path.join(folder, '**', '*.md'), recursive=True)
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Finde alle Indizes: ^[a-z0-9]{6}
                found = re.findall(r'\^([a-z0-9]{6})', content)
                indices.update(found)
        except Exception as e:
            print(f"  Warnung: Konnte {md_file} nicht lesen: {e}")
    
    return indices


def generiere_eindeutigen_index(bestehende_indizes):
    """Generiere einen neuen eindeutigen 6-stelligen Index"""
    chars = string.ascii_lowercase + string.digits
    max_versuche = 10000
    
    for _ in range(max_versuche):
        # Generiere zufälligen 6-stelligen Index
        index = ''.join(random.choice(chars) for _ in range(6))
        if index not in bestehende_indizes:
            bestehende_indizes.add(index)
            return index
    
    # Fallback: Verwende Timestamp-basierte Methode
    import time
    timestamp = str(int(time.time() * 1000))[-6:]
    return timestamp


def fuege_indizes_hinzu(text, bestehende_indizes):
    """Füge Obsidian-Indizes zu Absätzen hinzu (nur an Zeilen, die mit Punkt enden)"""
    lines = text.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Leere Zeilen unverändert lassen
        if not stripped:
            result.append(line)
            continue
        
        # Prüfe ob Zeile bereits einen Index hat
        if re.search(r'\^[a-z0-9]{6}$', stripped):
            # Hat bereits Index, unverändert lassen
            result.append(line)
        elif stripped[-1] == '.':
            # Zeile endet mit Punkt → füge Index hinzu
            # Prüfe ob es eine Überschrift oder Bild ist
            if not stripped.startswith(('#', '![')):
                # Normaler Absatz → füge Index hinzu
                index = generiere_eindeutigen_index(bestehende_indizes)
                result.append(line.rstrip() + f' ^{index}')
            else:
                result.append(line)
        else:
            result.append(line)
    
    return '\n'.join(result)


def splitte_vortraege(text, folder, ga_nr, indizes_hinzufuegen=False):
    """Split in Dateien"""
    # Sammle bestehende Indizes, wenn wir neue hinzufügen sollen
    bestehende_indizes = set()
    if indizes_hinzufuegen:
        print("  Sammle bestehende Indizes...")
        # Suche auch im übergeordneten Ordner
        parent_folder = os.path.dirname(folder)
        bestehende_indizes = sammle_bestehende_indizes(parent_folder)
        print(f"  {len(bestehende_indizes)} bestehende Indizes gefunden")
    
    sections = []
    curr_title = None
    curr_text = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Marker gefunden - neuer Vortrag beginnt
        if '<!-- VORTRAG_START:' in line:
            # Speichere vorherigen Vortrag
            if curr_title and curr_text:
                text_only = '\n'.join(curr_text)
                text_only = re.sub(r'<!-- VORTRAG_START:.*?-->', '', text_only)
                text_only = korrigiere_rechtschreibung(text_only)
                # Füge Indizes hinzu, wenn gewünscht
                if indizes_hinzufuegen:
                    text_only = fuege_indizes_hinzu(text_only, bestehende_indizes)
                sections.append({'title': curr_title, 'text': text_only})
            
            # Extrahiere Titel aus Marker
            match = re.search(r'<!-- VORTRAG_START:\s*(.+?)\s*-->', line)
            if match:
                curr_title = match.group(1).strip()
            curr_text = []
            i += 1
            continue
        
        # Text sammeln
        if curr_title is not None:
            # Überspringe leere Zeilen direkt nach Marker
            if not (line.strip() == '' and len(curr_text) == 0):
                curr_text.append(line)
        
        i += 1
    
    # Letzten speichern
    if curr_title and curr_text:
        text_only = '\n'.join(curr_text)
        text_only = re.sub(r'<!-- VORTRAG_START:.*?-->', '', text_only)
        text_only = korrigiere_rechtschreibung(text_only)
        # Füge Indizes hinzu, wenn gewünscht
        if indizes_hinzufuegen:
            text_only = fuege_indizes_hinzu(text_only, bestehende_indizes)
        sections.append({'title': curr_title, 'text': text_only})
    
    # Filtere TOC: Verschiedene Kriterien zum Erkennen von TOC-Einträgen
    filtered_sections = []
    vortrag_title_pattern = r'(?:ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER|Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Siebenter|Achter|Neunter|Zehnter|Elfter|Zwölfter|Dreizehnter|Vierzehnter|Fünfzehnter|Sechzehnter|Siebzehnter|Achtzehnter|Neunzehnter|Zwanzigster|Einundzwanzigster|Zweiundzwanzigster|Dreiundzwanzigster|Vierundzwanzigster|Fünfundzwanzigster)\s+(?:VORTRAG|Vortrag)'
    for sec in sections:
        # Zähle wie viele Vortragstitel im Text vorkommen
        vortrag_count = len(re.findall(vortrag_title_pattern, sec['text']))
        text_length = len(sec['text'])
        
        # TOC-Kriterien:
        # 1. Mehr als 5 Vortragstitel im Text -> definitiv TOC
        # 2. 2 oder mehr Vortragstitel UND Text kürzer als 2000 Zeichen -> wahrscheinlich TOC/Vorspann
        is_toc = False
        if vortrag_count > 5:
            is_toc = True
        elif vortrag_count >= 2 and text_length < 2000:
            is_toc = True
        
        if is_toc:
            print(f"  [TOC übersprungen] {sec['title'][:60]}...")
            continue
        filtered_sections.append(sec)
    
    # Erstelle Dateien
    files = []
    for i, sec in enumerate(filtered_sections, 1):
        title = sec['title']
        
        # Kürze Titel (unterstützt auch höhere Nummern)
        match = re.search(r'((?:ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER|ELFTER|ZWÖLFTER|DREIZEHNTER|VIERZEHNTER|FÜNFZEHNTER|SECHZEHNTER|SIEBZEHNTER|ACHTZEHNTER|NEUNZEHNTER|ZWANZIGSTER|EINUNDZWANZIGSTER|ZWEIUNDZWANZIGSTER|DREIUNDZWANZIGSTER|VIERUNDZWANZIGSTER|FÜNFUNDZWANZIGSTER)\s+VORTRAG.*?(?:\d{4}|$))', title)
        short = match.group(1)[:80] if match else title[:80]
        
        # Formatiere GA-Nummer: wenn nur Ziffern, dann mit führenden Nullen, sonst wie ist
        if ga_nr.isdigit():
            ga_formatted = ga_nr.zfill(3)
        else:
            ga_formatted = ga_nr
        fname = f"GA{ga_formatted} ({i}.) {short}.md"
        fname = re.sub(r'[<>:"/\\|?*]', '', fname)
        fname = re.sub(r'\s+', ' ', fname).strip()
        
        fpath = os.path.join(folder, fname)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(sec['text'])
        
        files.append(fpath)
        print(f"  [{i:2d}] {Path(fpath).name[:70]}")
    
    return files


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python ga_pdf_final.py <GA-Nummer> [--indizes]")
        print("  --indizes: Füge Obsidian-Indizes zu Absätzen hinzu")
        return
    
    ga_number = sys.argv[1]
    indizes_hinzufuegen = '--indizes' in sys.argv or '-i' in sys.argv
    
    process_ga_pdf(ga_number, indizes_hinzufuegen=indizes_hinzufuegen)


if __name__ == "__main__":
    main()

