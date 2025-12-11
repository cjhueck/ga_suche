# -*- coding: utf-8 -*-
"""
PDF zu Markdown Konverter für GA-Bände
Konvertiert PDFs zu Markdown mit:
- H3 für Kapitelüberschriften
- H4 für Zwischenüberschriften
- Verlinkte Fußnoten mit Backlinks
- Bereinigte Absätze
- Rechtschreibkorrektur
"""
import sys
import io
import os
import re
from pathlib import Path
import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def korrigiere_rechtschreibung(text):
    """Korrigiere alte Rechtschreibung zu neuer (aus ga_pdf_final.py und export_master.py)"""
    # Ersetze lange Gedankenstriche durch kurze
    text = text.replace('—', '-')
    text = text.replace('–', '-')
    
    # Ersetze kk durch ck in deutschen Wörtern (Entwikklung → Entwicklung)
    def replace_kk(match):
        before = match.group(1)
        after = match.group(2)
        word = before + 'kk' + after
        
        # Ausnahmen: okkult*, *kehr (Rückkehr, zurückkehren), Akkord, Akkumulator, 
        #            Akkusativ, Mokka, Sakko, Stakkato, okkupier*, Brokkoli, sukkulen*
        word_lower = word.lower()
        kk_exceptions = ['okkult', 'kehr', 'akkord', 'akkum', 'akkus', 'mokka', 
                        'sakko', 'stakka', 'okkup', 'brokko', 'sukkul', 'makka']
        has_exception = any(exc in word_lower for exc in kk_exceptions)
        
        if (len(word) < 5 or not before or 
            any(c in word for c in ['/', ':', '.', '@', '_']) or
            has_exception):
            return match.group(0)
        
        return before + 'ck' + after
    
    kk_pattern = r'\b(\w+?)kk(\w+?)\b'
    text = re.sub(kk_pattern, replace_kk, text)
    
    # Wörterliste aus ga_pdf_final.py
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
        'biß': 'biss',
        'riß': 'riss',
        'floß': 'floss',
        'schoß': 'schoss',
        'Entschluß': 'Entschluss',
        'entschluß': 'entschluss',
        'müßte': 'müsste',
        'müßtest': 'müsstest',
        'müßtet': 'müsstet',
        'müßten': 'müssten',
        'reisst': 'reißt',
        'Eiweiss': 'Eiweiß',
        'eiweiss': 'eiweiß',
        'läßt': 'lässt',
        'heisst': 'heißt',
        'weiss': 'weiß',
        'ChristusWesenheit': 'Christus-Wesenheit',
        'Johannes-Evangelium': 'Johannes-Evangelium',
        'SeelischGeistiges': 'Seelisch-Geistiges',
        'Geistig-Seelisches': 'Geistig-Seelisches',
        'geistigseelisch': 'geistig-seelisch',
        'seelischgeistig': 'seelisch-geistig',
        'westund mitteleuropäisch': 'west- und mitteleuropäisch',
        'von daoder von dorther': 'von da- oder von dorther',
        'EntwederOder': 'Entweder-Oder',
        'Prozeß': 'Prozess',
        '..prozeß': '..prozess',
        'dreissig': 'dreißig',
        'dreiunddreissig': 'dreiunddreißig',
        # Aus export_master.py
        'Fleiss': 'Fleiß',
        'fleiss': 'fleiß',
        'vergeßlich': 'vergesslich',
        'heiss': 'heiß',
        'zurücckommen': 'zurückkommen',
        'ackurat': 'akkurat',
        'paßt': 'passt',
        'römischkatholisch': 'römisch-katholisch',
        'seelischgeistig': 'seelisch-geistig',
        'DeutschÖsterreicher': 'Deutsch-Österreicher',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def bereinige_text(text):
    """Bereinige Text: entferne falsche Umbrüche, füge richtige Absätze ein"""
    lines = text.split('\n')
    cleaned_lines = []
    
    # Entferne Seitenumbrüche und Seitenzahlen
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Seitenumbruch-Marker überspringen
        if re.match(r'^-{3,}$', line) or re.match(r'^Seite\s+\d+$', line, re.IGNORECASE):
            i += 1
            continue
        
        cleaned_lines.append(lines[i])
        i += 1
    
    lines = cleaned_lines
    
    # Zusammenfügen von Zeilen
    out = []
    for i, curr in enumerate(lines):
        prev = out[-1] if out else None
        
        if not prev or not curr.strip():
            out.append(curr)
            continue
        
        # Überschriften bleiben getrennt
        if re.match(r'^(#{1,6}\s+|!\[)', curr):
            out.append(curr)
            continue
        
        prev_trim = prev.rstrip()
        if not prev_trim:
            out.append(curr)
            continue
        
        # Wenn vorherige Zeile eine Überschrift ist, nicht zusammenfügen
        if prev_trim and re.match(r'^#{1,6}\s+', prev_trim):
            out.append(curr)
            continue
        
        last = prev_trim[-1]
        curr_stripped = curr.strip()
        
        # Silbentrennung mit Bindestrich → OHNE Leerzeichen zusammenfügen
        if last in '-–—':
            out[-1] = prev_trim[:-1] + curr_stripped
        # Wenn vorherige Zeile mit Punkt endet und nächste mit Großbuchstabe beginnt → neuer Absatz
        elif last == '.' and curr_stripped and curr_stripped[0].isupper():
            out.append(curr)
        # Wenn vorherige Zeile mit Kleinbuchstabe endet und nächste mit Kleinbuchstabe beginnt → zusammenfügen
        elif prev_trim[-1].islower() and curr_stripped and curr_stripped[0].islower():
            out[-1] = prev_trim + ' ' + curr_stripped
        # Alles andere → MIT Leerzeichen zusammenfügen
        else:
            out[-1] = prev_trim + ' ' + curr_stripped
    
    # Füge Leerzeilen zwischen Absätzen ein
    text2 = '\n'.join(out)
    lines2 = text2.split('\n')
    final = []
    for i, line in enumerate(lines2):
        final.append(line)
        # Wenn Zeile mit Punkt endet UND nächste Zeile mit Großbuchstabe beginnt → Leerzeile einfügen
        if line.strip() and line.strip()[-1] == '.':
            next_line = lines2[i+1] if i+1 < len(lines2) else ''
            if (next_line.strip() and 
                not next_line.startswith(('#', '!', '[')) and
                next_line.strip()[0].isupper()):
                final.append('')
    
    return '\n'.join(final)


def erkenne_ueberschriften(text):
    """Erkenne und formatiere Überschriften: H3 für Kapitel, H4 für Zwischenüberschriften"""
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Leere Zeilen unverändert
        if not stripped:
            result.append(line)
            continue
        
        # Bereits vorhandene Markdown-Überschriften konvertieren
        # H1 (#) → H3 (###) - aber nur wenn es keine H2/H3/H4 ist
        if re.match(r'^#\s+', stripped) and not re.match(r'^##', stripped):
            # Entferne # und füge ### hinzu
            content = re.sub(r'^#\s+', '', stripped)
            result.append(f"### {content}")
            continue
        
        # H2 (##) → H4 (####)
        if re.match(r'^##\s+', stripped) and not re.match(r'^###', stripped):
            # Entferne ## und füge #### hinzu
            content = re.sub(r'^##\s+', '', stripped)
            result.append(f"#### {content}")
            continue
        
        # Kapitelüberschriften erkennen (z.B. "I. EINLEITUNG", "II. DIE ENTSTEHUNG...")
        # Pattern: Römische Zahl gefolgt von Punkt und Großbuchstaben (mindestens 3 Zeichen)
        kapitel_pattern = r'^([IVX]+\.)\s+([A-ZÄÖÜ][A-ZÄÖÜ\s]{2,})$'
        kapitel_match = re.match(kapitel_pattern, stripped)
        
        if kapitel_match:
            # H3 für Kapitelüberschriften mit ID für Verlinkung
            kapitel_num = kapitel_match.group(1).rstrip('.')
            kapitel_titel = kapitel_match.group(2).strip()
            # Erstelle ID für Link (normalisiere Titel)
            link_id = kapitel_titel.replace(' ', '-').replace('Ä', 'A').replace('Ö', 'O').replace('Ü', 'U').replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
            link_id = re.sub(r'[^a-zA-Z0-9\-]', '', link_id).lower()
            result.append(f"### {stripped}")
            # ID wird automatisch von Markdown generiert, aber wir können sie auch explizit setzen
            # Für bessere Kompatibilität verwenden wir den Titel direkt
            continue
        
        # Zwischenüberschriften erkennen (z.B. "1. Methodologie", "2. Dogmatische...")
        # Pattern: Nummer gefolgt von Punkt und Text (kann auch Großbuchstaben enthalten)
        zwischen_pattern = r'^(\d+\.)\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ\s]+)$'
        zwischen_match = re.match(zwischen_pattern, stripped)
        
        if zwischen_match:
            # Prüfe ob es wirklich eine Überschrift ist (nicht zu lang, nicht Teil eines Satzes)
            text_part = zwischen_match.group(2)
            if len(text_part) < 100 and not text_part.endswith(',') and len(stripped) < 150:
                # Prüfe ob nächste Zeile leer ist oder mit Großbuchstabe beginnt (typisch für Überschriften)
                next_line = lines[i+1].strip() if i+1 < len(lines) else ''
                if not next_line or next_line[0].isupper() if next_line else True:
                    # H4 für Zwischenüberschriften
                    result.append(f"#### {stripped}")
                    continue
        
        # Normale Zeile
        result.append(line)
    
    return '\n'.join(result)


def formatiere_titel(text):
    """Formatiere Titel: GA 001 RUDOLF STEINER GOETHES... → RUDOLF STEINER: GOETHES..."""
    lines = text.split('\n')
    result = []
    titel_formatiert = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Erkenne Titel-Zeile: "GA 001 RUDOLF STEINER GOETHES NATURWISSENSCHAFTLICHE SCHRIFTEN Ursprünglich..."
        if not titel_formatiert and re.search(r'GA\s+\d+\s+RUDOLF\s+STEINER\s+GOETHES', stripped, re.IGNORECASE):
            # Extrahiere Titel und Untertitel - flexibleres Pattern
            # Suche nach "RUDOLF STEINER" und "GOETHES NATURWISSENSCHAFTLICHE SCHRIFTEN"
            match = re.search(r'(RUDOLF\s+STEINER)\s+(GOETHES\s+NATURWISSENSCHAFTLICHE\s+SCHRIFTEN)\s+(Ursprünglich.*)', stripped, re.IGNORECASE)
            if match:
                autor = match.group(1)
                titel = match.group(2)
                untertitel = match.group(3)
                result.append(f"{autor}: {titel}")
                result.append("")
                result.append(untertitel)
                result.append("")
                titel_formatiert = True
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def formatiere_inhaltsverzeichnis(text):
    """Formatiere Inhaltsverzeichnis als H3 und verlinke Einträge"""
    lines = text.split('\n')
    result = []
    toc_processed = False
    
    # Sammle alle H3-Überschriften für das Inhaltsverzeichnis
    h3_ueberschriften = []
    for line in lines:
        stripped = line.strip()
        # Erkenne H3-Überschriften mit römischen Zahlen
        if re.match(r'^###\s+([IVX]+\.\s+.+)$', stripped):
            match = re.match(r'^###\s+([IVX]+\.\s+.+)$', stripped)
            if match:
                h3_ueberschriften.append(match.group(1))
        # Auch "ZUR EINFÜHRUNG" als H3
        elif re.match(r'^###\s+(ZUR\s+EINFÜHRUNG)$', stripped, re.IGNORECASE):
            h3_ueberschriften.insert(0, "ZUR EINFÜHRUNG")  # Am Anfang einfügen
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Erkenne Inhaltsverzeichnis-Beginn
        if not toc_processed and ('Inhalt' in stripped or stripped == '### Inhalt'):
            toc_processed = True
            # Überschreibe die vorhandene "Inhalt"-Zeile
            result.append("### Inhalt")
            result.append("")
            result.append("Zur Einführung")
            result.append('Aus „Mein Lebensgang", Kap. VI')
            result.append("")
            
            # Erstelle Links zu allen H3-Überschriften
            for ueberschrift in h3_ueberschriften:
                # Prüfe ob es "ZUR EINFÜHRUNG" ist
                if ueberschrift == "ZUR EINFÜHRUNG":
                    link_text = "zur-einführung".lower().replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
                    link_text = re.sub(r'[^a-z0-9\s-]', '', link_text)
                    link_text = re.sub(r'\s+', '-', link_text)
                    result.append(f"- [ZUR EINFÜHRUNG](#{link_text})")
                else:
                    # Extrahiere Nummer und Titel
                    match = re.match(r'^([IVX]+\.)\s+(.+)', ueberschrift)
                    if match:
                        kapitel_num = match.group(1)
                        kapitel_titel = match.group(2).strip()
                        
                        # Erstelle Link zu Überschrift (Markdown generiert IDs automatisch)
                        link_text = kapitel_titel.lower().replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
                        link_text = re.sub(r'[^a-z0-9\s-]', '', link_text)
                        link_text = re.sub(r'\s+', '-', link_text)
                        result.append(f"- [{kapitel_num} {kapitel_titel}](#{link_text})")
            
            result.append("")
            # Überspringe die ursprüngliche Inhalt-Zeile und die folgenden Zeilen bis zur nächsten Überschrift
            continue
        
        # Überspringe Zeilen, die Teil des alten Inhaltsverzeichnisses sind
        if toc_processed and i < 30:  # Erste 30 Zeilen nach "Inhalt"
            # Überspringe Zeilen mit Kapitelnummern ohne "###"
            if re.match(r'^(I{1,3}|IV|V|VI{0,3}|IX|X{0,3}|XVIII)\s+', stripped) and not stripped.startswith('###'):
                continue
        
        # Erkenne "ZUR EINFÜHRUNG" als separate Überschrift
        if 'ZUR EINFÜHRUNG' in stripped and not stripped.startswith('###'):
            # Wenn es eine lange Zeile ist, trenne sie auf
            if len(stripped) > 100:
                zur_einf_match = re.search(r'(ZUR\s+EINFÜHRUNG)\s+(.+)', stripped, re.IGNORECASE)
                if zur_einf_match:
                    result.append("### ZUR EINFÜHRUNG")
                    result.append("")
                    result.append(zur_einf_match.group(2))
                    continue
            else:
                result.append("### ZUR EINFÜHRUNG")
                result.append("")
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def extrahiere_abbildungen(text, pdf_path, output_path):
    """Extrahiere Abbildungen aus PDF und füge Platzhalter ein"""
    doc = fitz.open(pdf_path)
    output_dir = Path(output_path).parent
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    images_extracted = 0
    image_refs = []
    
    for pnum in range(len(doc)):
        page = doc[pnum]
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Erstelle Dateiname
            image_filename = f"GA001_page_{pnum+1}_img_{img_index+1}.{image_ext}"
            image_path = assets_dir / image_filename
            
            # Speichere Bild
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            
            images_extracted += 1
            image_refs.append({
                'page': pnum + 1,
                'index': img_index + 1,
                'filename': image_filename,
                'path': f"assets/{image_filename}"
            })
    
    doc.close()
    
    # Füge Bild-Platzhalter in Text ein (nach Seitenumbrüchen)
    if image_refs:
        lines = text.split('\n')
        new_lines = []
        current_page = 1
        
        for line in lines:
            new_lines.append(line)
            
            # Prüfe ob Seitenumbruch
            if re.match(r'^Seite\s+(\d+)$', line.strip(), re.IGNORECASE):
                page_match = re.match(r'^Seite\s+(\d+)$', line.strip(), re.IGNORECASE)
                if page_match:
                    current_page = int(page_match.group(1))
                    
                    # Füge Bilder für diese Seite ein
                    for img_ref in image_refs:
                        if img_ref['page'] == current_page:
                            new_lines.append(f"![Abbildung]({img_ref['path']})")
                            new_lines.append("")
        
        text = '\n'.join(new_lines)
    
    return text, images_extracted


def verarbeite_fussnoten(text):
    """Verarbeite Fußnoten: erhalte Links und erstelle Backlinks"""
    # Fußnoten im Format: ".i" oder ".ii" oder ".1" am Ende eines Satzes
    # Oder: ${ }^{i}$ oder ${ }^{\text {ii }}$ oder ${ }^{11}$
    
    # Zuerst: Einfache Fußnoten-Marker wie ".i", ".ii", ".1" am Satzende
    # Pattern: Punkt gefolgt von römischer Zahl oder Nummer am Ende einer Zeile oder vor Leerzeichen
    einfache_fussnoten_pattern = r'\.([ivxlcdmIVXLCDM]+|\d+)(?=\s|$)'
    
    fussnoten_map = {}
    fussnoten_counter = 1
    fussnoten_refs = {}  # Speichere Referenzen für Backlinks
    
    def process_einfache_fussnote(match, pos):
        nonlocal fussnoten_counter
        marker = match.group(1)
        
        # Erstelle eindeutige ID
        if marker not in fussnoten_map:
            fn_id = str(fussnoten_counter)
            fussnoten_map[marker] = fn_id
            fussnoten_refs[fn_id] = []
            fussnoten_counter += 1
        else:
            fn_id = fussnoten_map[marker]
        
        # Speichere Position für Backlink
        fussnoten_refs[fn_id].append(pos)
        
        # Ersetze durch klickbaren Link
        return f'. [^{fn_id}]'
    
    # Ersetze einfache Fußnoten-Marker
    text_lines = text.split('\n')
    new_lines = []
    for line_idx, line in enumerate(text_lines):
        # Suche nach einfachen Fußnoten-Markern
        pos = 0
        new_line = line
        for match in re.finditer(einfache_fussnoten_pattern, line):
            marker = match.group(1)
            if marker not in fussnoten_map:
                fn_id = str(fussnoten_counter)
                fussnoten_map[marker] = fn_id
                fussnoten_refs[fn_id] = []
                fussnoten_counter += 1
            else:
                fn_id = fussnoten_map[marker]
            
            # Ersetze Marker durch Link
            start, end = match.span()
            new_line = new_line[:start] + f'. [^{fn_id}]' + new_line[end:]
        
        new_lines.append(new_line)
    
    text = '\n'.join(new_lines)
    
    # Dann: Komplexe Fußnoten im Format ${ }^{...}
    fussnoten_pattern = r'\$\{\s*\}^{\s*\{([^}]+)\}\s*\$'
    
    def process_komplexe_fussnote(match):
        nonlocal fussnoten_counter
        marker = match.group(1)
        # Bereinige Marker (entferne \text { })
        marker_clean = re.sub(r'\\text\s*\{', '', marker)
        marker_clean = re.sub(r'\}', '', marker_clean)
        marker_clean = marker_clean.strip()
        
        # Erstelle eindeutige ID basierend auf Marker
        if marker_clean not in fussnoten_map:
            fn_id = str(fussnoten_counter)
            fussnoten_map[marker_clean] = fn_id
            fussnoten_refs[fn_id] = []
            fussnoten_counter += 1
        else:
            fn_id = fussnoten_map[marker_clean]
        
        # Ersetze durch klickbaren Link
        return f' [^{fn_id}]'
    
    # Ersetze komplexe Fußnoten-Marker
    text = re.sub(fussnoten_pattern, process_komplexe_fussnote, text)
    
    # Füge Fußnoten-Definitionen am Ende hinzu (mit Backlinks)
    if fussnoten_map:
        text += '\n\n---\n\n## Fußnoten\n\n'
        # Sortiere nach ID (numerisch)
        sorted_fns = sorted(fussnoten_map.items(), key=lambda x: (
            int(x[1]) if x[1].isdigit() else float('inf'),
            x[1] if not x[1].isdigit() else ''
        ))
        for marker, fn_id in sorted_fns:
            # Erstelle Backlink zu allen Referenzen
            backlinks = ' '.join([f'[↑](#fn-ref-{fn_id}-{i})' for i in range(len(fussnoten_refs.get(fn_id, [])))])
            text += f'[^{fn_id}]: {marker} {backlinks}\n'
    
    # Füge IDs zu Fußnoten-Referenzen hinzu für Backlinks (nur für Markdown, HTML wird später generiert)
    # Für jetzt: einfache Markdown-Fußnoten ohne HTML-Tags
    # Die HTML-Konvertierung wird später die IDs hinzufügen
    
    return text


def konvertiere_pdf_zu_md(pdf_path, output_path):
    """Konvertiere PDF zu Markdown"""
    print(f"Konvertiere: {Path(pdf_path).name}")
    
    # Öffne PDF
    doc = fitz.open(pdf_path)
    print(f"  Seiten: {len(doc)}")
    
    # Extrahiere Text seitenweise
    pages_text = []
    for pnum in range(len(doc)):
        page = doc[pnum]
        text = page.get_text()
        pages_text.append(text)
    
    doc.close()
    
    # Verbinde alle Seiten
    text = '\n'.join(pages_text)
    
    # Erkenne und formatiere Überschriften ZUERST (bevor Textbereinigung sie zerstört)
    print("  Erkenne Überschriften...")
    text = erkenne_ueberschriften(text)
    # Debug: Zähle Überschriften
    h3_count = len(re.findall(r'^###\s+', text, re.MULTILINE))
    h4_count = len(re.findall(r'^####\s+', text, re.MULTILINE))
    print(f"    Gefunden: {h3_count} H3, {h4_count} H4")
    
    # Bereinige Text (nach Überschriften-Erkennung)
    print("  Bereinige Text...")
    text = bereinige_text(text)
    
    # Formatiere Titel und Metadaten (nach Textbereinigung)
    print("  Formatiere Titel...")
    text = formatiere_titel(text)
    
    # Formatiere Inhaltsverzeichnis und verlinke es (nach Textbereinigung)
    print("  Formatiere Inhaltsverzeichnis...")
    text = formatiere_inhaltsverzeichnis(text)
    
    # Extrahiere und füge Abbildungen ein
    print("  Extrahiere Abbildungen...")
    text, images_extracted = extrahiere_abbildungen(text, pdf_path, output_path)
    if images_extracted > 0:
        print(f"    {images_extracted} Abbildungen extrahiert")
    
    # Verarbeite Fußnoten
    print("  Verarbeite Fußnoten...")
    text = verarbeite_fussnoten(text)
    
    # Korrigiere Rechtschreibung
    print("  Korrigiere Rechtschreibung...")
    text = korrigiere_rechtschreibung(text)
    
    # Stelle sicher, dass Ausgabeordner existiert
    output_path_obj = Path(output_path)
    output_dir = output_path_obj.parent
    if output_dir and str(output_dir) != '.':
        os.makedirs(output_dir, exist_ok=True)
    
    # Speichere MD-Datei
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  Gespeichert: {Path(output_path).name}\n")
        print(f"  Vollständiger Pfad: {output_path}\n")
    except Exception as e:
        print(f"  FEHLER beim Speichern: {e}\n")
        raise
    
    return output_path


def finde_pdf_und_output(pdf_path_or_dir, ga_nummer=None, output_filename=None):
    """Finde PDF-Datei und bestimme Ausgabepfad"""
    pdf_path = Path(pdf_path_or_dir)
    
    if pdf_path.is_file() and pdf_path.suffix.lower() == '.pdf':
        # Direkte PDF-Datei
        pdf_file = pdf_path
        # Bestimme Ausgabepfad basierend auf PDF-Pfad
        output_dir = pdf_file.parent
        
        # Verwende angegebenen Dateinamen oder erstelle Standard-Namen
        if output_filename:
            output_path = output_dir / output_filename
        else:
            base_name = pdf_file.stem
            md_name = f"{base_name}.md"
            output_path = output_dir / md_name
        
        return pdf_file, output_path
    
    elif pdf_path.is_dir():
        # Ordner: suche PDF-Dateien
        pdf_files = list(pdf_path.glob('*.pdf'))
        if not pdf_files:
            return None, None
        if len(pdf_files) == 1:
            pdf_file = pdf_files[0]
            output_dir = pdf_path
            
            # Verwende angegebenen Dateinamen oder erstelle Standard-Namen
            if output_filename:
                output_path = output_dir / output_filename
            else:
                base_name = pdf_file.stem
                md_name = f"{base_name}.md"
                output_path = output_dir / md_name
            
            return pdf_file, output_path
        else:
            # Mehrere PDFs im Ordner
            return pdf_files, None
    
    return None, None


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python pdf_to_md_converter.py <PDF-Pfad> [Ausgabe-Dateiname]")
        print("  python pdf_to_md_converter.py <Ordner-Pfad>")
        print("  python pdf_to_md_converter.py --batch <GA-Nummer-Liste>")
        print("\nBeispiele:")
        print('  python pdf_to_md_converter.py "C:\\Users\\...\\GA001-Goethes Naturwissenschaftliche Schriften.pdf"')
        print('  python pdf_to_md_converter.py "C:\\Users\\...\\GA001-Goethes Naturwissenschaftliche Schriften.pdf" "GA001 - Goethes Naturwissenschaftliche Schriften (1883-1897).md"')
        print('  python pdf_to_md_converter.py "C:\\Users\\...\\GA001-Goethes Naturwissenschaftliche Schriften"')
        print('  python pdf_to_md_converter.py --batch "001,002,003"')
        return
    
    if sys.argv[1] == '--batch':
        # Batch-Verarbeitung
        if len(sys.argv) < 3:
            print("Fehler: Bitte GA-Nummern angeben (z.B. --batch 001,002,003)")
            return
        
        ga_nummern = sys.argv[2].split(',')
        base_dir = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
        
        for ga_num in ga_nummern:
            ga_num = ga_num.strip()
            print(f"\n{'='*80}")
            print(f"Verarbeite GA {ga_num}")
            print('='*80)
            
            # Suche Ordner für diesen GA-Band
            ga_ordner = None
            for item in base_dir.iterdir():
                if item.is_dir() and item.name.startswith(f'GA{ga_num.zfill(3)}'):
                    ga_ordner = item
                    break
            
            if not ga_ordner:
                print(f"Warnung: Ordner für GA {ga_num} nicht gefunden")
                continue
            
            # Suche PDF im Ordner
            pdf_files = list(ga_ordner.glob('*.pdf'))
            if not pdf_files:
                print(f"Warnung: Keine PDF für GA {ga_num} gefunden")
                continue
            
            pdf_file = pdf_files[0]
            # Bestimme Ausgabepfad (basierend auf vorhandener MD-Datei oder neu erstellen)
            md_files = list(ga_ordner.glob('*.md'))
            if md_files:
                # Verwende vorhandenen MD-Dateinamen
                output_path = md_files[0]
            else:
                # Erstelle neuen Namen basierend auf PDF-Namen
                base_name = pdf_file.stem
                output_path = ga_ordner / f"{base_name}.md"
            
            konvertiere_pdf_zu_md(str(pdf_file), str(output_path))
    
    else:
        # Einzelne Datei oder Ordner
        input_path = sys.argv[1]
        output_filename = sys.argv[2] if len(sys.argv) > 2 else None
        
        pdf_file, auto_output_path = finde_pdf_und_output(input_path, output_filename=output_filename)
        
        if pdf_file is None:
            print(f"Fehler: PDF-Datei nicht gefunden: {input_path}")
            return
        
        if isinstance(pdf_file, list):
            # Mehrere PDFs im Ordner
            for pdf in pdf_file:
                output = pdf.parent / f"{pdf.stem}.md"
                konvertiere_pdf_zu_md(str(pdf), str(output))
        else:
            # Einzelne PDF
            if output_filename:
                # Wenn nur Dateiname angegeben, verwende PDF-Ordner als Basis
                if os.path.dirname(output_filename) == '':
                    final_output = pdf_file.parent / output_filename
                else:
                    final_output = Path(output_filename)
            else:
                final_output = auto_output_path
            konvertiere_pdf_zu_md(str(pdf_file), str(final_output))


if __name__ == "__main__":
    main()

