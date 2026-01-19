#!/usr/bin/env python3
"""
Bereitet MD-Referenzdateien für GA-Bände für die Verwendung vor.

Transformationen:
1. Entfernt Copyright-Zeilen
2. Entfernt bibliographische Angaben am Anfang, Inhaltsverzeichnis und Hinweise am Ende
3. Behält nur die Vorträge
4. Wandelt "# Fragebeantwortung" in "## Fragebeantwortung" um
5. Formatiert Vortragstitel (einzeilig und zweizeilig)
6. Verarbeitet Seitenumbrüche (---)
7. Fügt automatisch Seitenzahlen aus PDF hinzu

Verwendung:
    python tools/final_from_mistral_md.py <MD-Datei> --pdf <PDF-Datei> [--output <Ausgabedatei>]
"""

import os
import sys
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Optional: PIL für Bildkonvertierung
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def convert_jpeg_to_png_in_folder(folder_path: Path) -> int:
    """
    Konvertiert alle JPEG-Dateien in einem Ordner zu PNG und vereinfacht Dateinamen.
    
    Beispiel: 'Steiner, Rudolf GA 089..._img-0.jpeg' → 'img-0.png'
    
    Args:
        folder_path: Pfad zum Ordner (z.B. assets/)
        
    Returns:
        Anzahl konvertierter/umbenannter Dateien
    """
    if not HAS_PIL:
        print("  WARNUNG: PIL nicht installiert, Bildkonvertierung übersprungen")
        return 0
    
    if not folder_path.exists():
        return 0
    
    converted = 0
    
    # Finde alle Bilddateien (JPEG und PNG)
    image_files = list(folder_path.glob('*.jpeg')) + list(folder_path.glob('*.jpg')) + \
                  list(folder_path.glob('*.JPEG')) + list(folder_path.glob('*.JPG')) + \
                  list(folder_path.glob('*.png')) + list(folder_path.glob('*.PNG'))
    
    for image_file in image_files:
        try:
            # Extrahiere die Bildnummer aus dem Dateinamen (z.B. img-0, img-1, ...)
            img_match = re.search(r'(img-\d+)', image_file.stem, re.IGNORECASE)
            
            if img_match:
                simple_name = img_match.group(1).lower()  # z.B. "img-0"
                target_file = folder_path / f"{simple_name}.png"
                
                # Wenn Quelldatei = Zieldatei, nichts tun
                if image_file == target_file:
                    continue
                
                # Wenn es eine JPEG-Datei ist, konvertiere zu PNG
                if image_file.suffix.lower() in ('.jpeg', '.jpg'):
                    with Image.open(image_file) as img:
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img.save(target_file, 'PNG', optimize=True)
                        else:
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            rgb_img.paste(img)
                            rgb_img.save(target_file, 'PNG', optimize=True)
                    # Lösche Original
                    image_file.unlink()
                else:
                    # PNG-Datei: nur umbenennen wenn nötig
                    if image_file != target_file:
                        # Wenn Zieldatei bereits existiert, lösche Original
                        if target_file.exists():
                            image_file.unlink()
                        else:
                            image_file.rename(target_file)
                
                converted += 1
            else:
                # Kein img-X Pattern gefunden, nur JPEG zu PNG konvertieren
                if image_file.suffix.lower() in ('.jpeg', '.jpg'):
                    png_file = image_file.with_suffix('.png')
                    with Image.open(image_file) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img.save(png_file, 'PNG', optimize=True)
                else:
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img)
                    rgb_img.save(png_file, 'PNG', optimize=True)
                    image_file.unlink()
            converted += 1
            
        except Exception as e:
            print(f"    FEHLER bei {image_file.name}: {e}")
    
    return converted


def fix_image_placeholders_in_content(content: str) -> str:
    """
    Korrigiert Bildplatzhalter im Markdown-Text.
    1. Konvertiert .jpeg/.jpg Referenzen zu .png
    2. Vereinfacht Bildpfade zu Format: ![img-X.png](assets/img-X.png)
    
    Args:
        content: Markdown-Text
        
    Returns:
        Korrigierter Text
    """
    # Pattern 1: Pfad mit .jpeg/.jpg → .png
    jpeg_pattern = r'!\[([^\]]*)\]\(([^)]*\.jpe?g)([^)]*)\)'
    
    def convert_jpeg_to_png(match):
        alt_text = match.group(1)
        path_before_ext = match.group(2)
        path_after_ext = match.group(3)
        
        # Konvertiere auch Alt-Text von .jpeg/.jpg zu .png
        alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
        
        # Entferne .jpeg oder .jpg und füge .png hinzu
        path_without_ext = re.sub(r'\.jpe?g$', '', path_before_ext, flags=re.IGNORECASE)
        png_path_full = path_without_ext + '.png' + path_after_ext
        
        return f'![{alt_text_converted}]({png_path_full})'
    
    content = re.sub(jpeg_pattern, convert_jpeg_to_png, content)
    
    # Pattern 2: Alt-Text mit .jpeg/.jpg, aber Pfad bereits .png
    alt_jpeg_pattern = r'!\[([^\]]*\.jpe?g)\](\([^)]*\.png[^)]*\))'
    
    def convert_alt_jpeg_to_png(match):
        alt_text = match.group(1)
        path_part = match.group(2)
        alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
        return f'![{alt_text_converted}]{path_part}'
    
    content = re.sub(alt_jpeg_pattern, convert_alt_jpeg_to_png, content)
    
    # Pattern 3: Vereinfache Bildpfade zu Format ![img-X.png](assets/img-X.png)
    # Konvertiert z.B. ![Steiner, Rudolf GA 089..._img-0.png](assets/Steiner, Rudolf GA 089..._img-0.png)
    # zu ![img-0.png](assets/img-0.png)
    def simplify_image_path(match):
        full_match = match.group(0)
        # Extrahiere die Bildnummer (img-X)
        img_num_match = re.search(r'(img-\d+)\.(png|jpe?g)', full_match, re.IGNORECASE)
        if img_num_match:
            img_name = img_num_match.group(1)
            ext = img_num_match.group(2).lower()
            if ext in ('jpeg', 'jpg'):
                ext = 'png'
            return f'![{img_name}.{ext}](assets/{img_name}.{ext})'
        return full_match
    
    # Pattern für Bilder mit langem Präfix vor img-X
    long_prefix_pattern = r'!\[[^\]]*_?(img-\d+)\.[^\]]+\]\(assets/[^)]*_?(img-\d+)\.[^)]+\)'
    content = re.sub(long_prefix_pattern, simplify_image_path, content, flags=re.IGNORECASE)
    
    # Auch einfachere Muster abfangen
    simple_prefix_pattern = r'!\[[^\]]+\]\(assets/[^)]*?(img-\d+)\.(png|jpe?g)[^)]*\)'
    content = re.sub(simple_prefix_pattern, simplify_image_path, content, flags=re.IGNORECASE)
    
    return content


def process_images(md_path: Path, content: str) -> str:
    """
    Verarbeitet Bilder in einer MD-Datei:
    1. Konvertiert JPEG zu PNG im assets-Ordner
    2. Aktualisiert Platzhalter im Text
    
    Args:
        md_path: Pfad zur MD-Datei
        content: Inhalt der MD-Datei
        
    Returns:
        Aktualisierter Inhalt
    """
    # Suche nach Bild-Platzhaltern
    image_pattern = r'!\[[^\]]*\]\([^)]*\.(jpe?g|png|webp|gif)[^)]*\)'
    matches = re.findall(image_pattern, content, re.IGNORECASE)
    
    if not matches:
        return content
    
    # Prüfe auf assets-Ordner
    assets_folder = md_path.parent / 'assets'
    
    converted = 0
    if assets_folder.exists():
        # Konvertiere JPEG zu PNG
        converted = convert_jpeg_to_png_in_folder(assets_folder)
        if converted > 0:
            print(f"  {converted} JPEG-Bilder zu PNG konvertiert")
    
    # Aktualisiere Platzhalter im Text
    original_content = content
    content = fix_image_placeholders_in_content(content)
    
    if content != original_content:
        placeholder_changes = len(re.findall(r'\.png', content)) - len(re.findall(r'\.png', original_content))
        if placeholder_changes > 0:
            print(f"  {placeholder_changes} Bild-Platzhalter aktualisiert")
    
    return content


def remove_copyright_lines(content: str) -> str:
    """Entferne Copyright-Zeilen und 'Seite: XX' Zeilen."""
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Entferne Copyright-Zeilen (case-insensitive, verschiedene Varianten)
        if 'copyright' in line_lower and 'rudolf steiner' in line_lower:
            continue
        if 'copyright' in line_lower and 'nachlass' in line_lower:
            continue
        if 'copyright' in line_lower and 'nachlaß' in line_lower:
            continue
        # Entferne Zeilen mit "Buch:" und "Seite:" (Copyright-Marker)
        if 'buch:' in line_lower and 'seite:' in line_lower:
            continue
        # Entferne einzelne "Seite: XX" Zeilen
        if line_stripped.startswith('Seite:') or line_lower.startswith('seite:'):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def extract_toc_entries(content: str) -> list:
    """
    Extrahiert Vortragstitel und Daten aus dem Inhaltsverzeichnis.
    Gibt eine Liste von Dictionaries zurück: [{'title': ..., 'date': ..., 'number': ...}, ...]
    """
    toc_entries = []
    lines = content.split('\n')
    
    # Finde Inhaltsverzeichnis (mit oder ohne #)
    toc_start = None
    toc_end = None
    toc_pattern = re.compile(r'^#?\s*(INHALT|Inhalt|INHALTSVERZEICHNIS|Inhaltsverzeichnis)\s*$', re.IGNORECASE)
    
    for i, line in enumerate(lines):
        if toc_pattern.match(line.strip()):
            toc_start = i + 1
            continue
        # TOC endet bei nächster echter Überschrift (nicht TOC-Eintrag)
        if toc_start is not None:
            stripped = line.strip()
            # Echte Überschrift = # gefolgt von Text, der kein TOC-Eintrag ist
            if stripped.startswith('#') and not re.match(r'^#?\s*(INHALT|Inhalt)', stripped):
                # Prüfe ob es eine echte Vortragsüberschrift ist (Großbuchstaben, kein römische Zahl)
                if re.match(r'^#\s+[A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»,\.]+$', stripped):
                    toc_end = i
                    break
            # Hinweise am Ende
            if re.match(r'^#?\s*(Hinweise|HINWEISE)\s*$', stripped, re.IGNORECASE):
                toc_end = i
                break
    
    if toc_start is None:
        return toc_entries
    
    if toc_end is None:
        toc_end = min(toc_start + 150, len(lines))  # Max 150 Zeilen im TOC
    
    # Pattern für TOC-Einträge
    # Format 1: "I. Titel\nOrt, Datum Seite"
    # Format 2: "Titel Ort, Datum Seite"
    roman_pattern = re.compile(r'^(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI{0,3}|XIV|XV?)[\.\s]+(.+)$')
    # Datum mit optionaler Seitenzahl am Ende: "Berlin, 15. Oktober 1908. 9" oder "Berlin, 15. Oktober 1908 9"
    date_with_page_pattern = re.compile(r'([A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*\d{4})[\.\s]*(\d+)?')
    date_pattern = re.compile(r'([A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*\d{4})')
    
    current_title = None
    current_number = None
    
    for i in range(toc_start, toc_end):
        line = lines[i].strip()
        if not line:
            continue
        
        # Ignoriere Copyright-Zeilen und Seitenzahlen
        if 'Copyright' in line or re.match(r'^\d+$', line):
            continue
        
        # Prüfe auf römische Zahl am Anfang
        roman_match = roman_pattern.match(line)
        if roman_match:
            current_number = roman_match.group(1)
            rest = roman_match.group(2).strip()
            
            # Prüfe ob Datum in derselben Zeile (mit optionaler Seitenzahl)
            date_match = date_with_page_pattern.search(rest)
            if date_match:
                title = rest[:date_match.start()].strip()
                date = date_match.group(1)
                page = int(date_match.group(2)) if date_match.group(2) else None
                toc_entries.append({
                    'number': current_number,
                    'title': title,
                    'date': date,
                    'page': page,
                    'title_normalized': re.sub(r'\s+', ' ', title.upper().strip())
                })
                current_title = None
            else:
                current_title = rest
            continue
        
        # Prüfe ob Datum in dieser Zeile (für mehrzeilige Einträge)
        date_match = date_with_page_pattern.search(line)
        if date_match and current_title:
            title_part = line[:date_match.start()].strip()
            if title_part:
                current_title = current_title + ' ' + title_part
            date = date_match.group(1)
            page = int(date_match.group(2)) if date_match.group(2) else None
            toc_entries.append({
                'number': current_number,
                'title': current_title.strip(),
                'date': date,
                'page': page,
                'title_normalized': re.sub(r'\s+', ' ', current_title.upper().strip())
            })
            current_title = None
            continue
        
        # Fortsetzung des Titels
        if current_title:
            current_title = current_title + ' ' + line
    
    return toc_entries


def extract_toc_dates(content: str) -> dict:
    """
    Extrahiert Vortragstitel und Daten aus dem Inhaltsverzeichnis.
    Gibt ein Dictionary zurück: {titel_normalisiert: vollständiges_datum}
    """
    entries = extract_toc_entries(content)
    return {e['title_normalized']: e['date'] for e in entries}


def add_missing_page_numbers_from_toc(content: str, toc_entries: list) -> str:
    """
    Ergänzt fehlende Seitenzahlen am Anfang von Vorträgen aus dem TOC.
    
    Prüft jeden Vortragstitel und fügt |XX| hinzu, wenn:
    - Der erste Absatz nach dem Titel keine Seitenzahl hat
    - Im TOC eine Seitenzahl für diesen Vortrag vorhanden ist
    """
    if not toc_entries:
        return content
    
    # Erstelle Mapping: normalisierter Titel -> Seitenzahl
    toc_pages = {}
    for entry in toc_entries:
        if entry.get('page'):
            toc_pages[entry['title_normalized']] = entry['page']
    
    if not toc_pages:
        return content
    
    lines = content.split('\n')
    result = []
    added_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf Vortragstitel
        title_match = re.match(r'^#\s+([^,]+)', line)
        if title_match:
            title = title_match.group(1).strip()
            # Entferne " - I", " - II" etc. für Matching
            title_base = re.sub(r'\s*-\s*(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI{0,3}|XIV|XV?)\s*$', '', title)
            title_normalized = re.sub(r'\s+', ' ', title_base.upper().strip())
            
            result.append(line)
            i += 1
            
            # Überspringe Leerzeilen
            while i < len(lines) and not lines[i].strip():
                result.append(lines[i])
                i += 1
            
            # Prüfe ob nächste Zeile bereits Seitenzahl hat
            if i < len(lines):
                next_line = lines[i]
                has_page = bool(re.match(r'^\|?\d+\|', next_line.strip()))
                
                if not has_page:
                    # Suche Seitenzahl im TOC
                    page = None
                    for toc_title, toc_page in toc_pages.items():
                        if toc_title in title_normalized or title_normalized in toc_title:
                            page = toc_page
                            break
                        # Vergleiche erste 30 Zeichen
                        if toc_title[:30] == title_normalized[:30]:
                            page = toc_page
                            break
                    
                    if page:
                        # Füge Seitenzahl am Anfang der Zeile ein
                        result.append(f"|{page}| {next_line.lstrip()}")
                        added_count += 1
                        i += 1
                        continue
                
                result.append(next_line)
                i += 1
            continue
        
        result.append(line)
        i += 1
    
    if added_count > 0:
        print(f"  {added_count} Seitenzahlen aus TOC ergänzt")
    
    return '\n'.join(result)


def validate_against_toc(final_content: str, toc_entries: list) -> None:
    """
    Vergleicht die formatierten Vortragstitel mit dem Inhaltsverzeichnis.
    Gibt Warnungen aus bei Abweichungen.
    """
    if not toc_entries:
        return
    
    # Extrahiere Titel aus final_content
    final_titles = []
    for line in final_content.split('\n'):
        match = re.match(r'^#\s+([^,]+)', line)
        if match:
            title = match.group(1).strip()
            # Entferne " - I", " - II" etc. am Ende für den Vergleich
            title_base = re.sub(r'\s*-\s*(I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XI{0,3}|XIV|XV?)\s*$', '', title)
            final_titles.append({
                'full': title,
                'base': title_base,
                'normalized': re.sub(r'\s+', ' ', title_base.upper().strip())
            })
    
    # Vergleiche
    toc_normalized = {e['title_normalized'] for e in toc_entries}
    final_normalized = {t['normalized'] for t in final_titles}
    
    # Fehlende Vorträge (im TOC aber nicht im Final)
    missing = []
    for entry in toc_entries:
        found = False
        for ft in final_titles:
            # Fuzzy-Vergleich: Prüfe ob Titel teilweise übereinstimmt
            if entry['title_normalized'] in ft['normalized'] or ft['normalized'] in entry['title_normalized']:
                found = True
                break
            # Oder erste 30 Zeichen
            if entry['title_normalized'][:30] == ft['normalized'][:30]:
                found = True
                break
        if not found:
            missing.append(entry)
    
    if missing:
        print(f"  WARNUNG: {len(missing)} Vorträge aus TOC nicht gefunden:")
        for m in missing[:5]:  # Max 5 anzeigen
            print(f"    - {m['number']}. {m['title'][:50]}...")
    
    # Anzahl-Vergleich
    if len(toc_entries) != len(final_titles):
        print(f"  INFO: TOC hat {len(toc_entries)} Einträge, Final hat {len(final_titles)} Vorträge")


def extract_lectures_only(content: str) -> str:
    """
    Extrahiert nur die Vorträge aus dem Dokument.
    Entfernt:
    - Bibliographische Angaben am Anfang (vor dem ersten Vortrag)
    - Inhaltsverzeichnis (# INHALT oder ähnlich)
    - "Zu dieser Ausgabe" / "Xu dieser Ausgabe" Abschnitte
    - Hinweise am Ende (nach dem letzten Vortrag)
    """
    lines = content.split('\n')
    
    # Finde den ersten Vortrag (H1 mit Datum)
    first_lecture_idx = None
    last_lecture_end_idx = None
    
    # Pattern für Vortragstitel: H1 mit Ort und Datum
    lecture_pattern = re.compile(
        r'^#\s+[A-ZÄÖÜ].*,\s*\d{1,2}\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4}',
        re.IGNORECASE
    )
    
    # Alternative: H1 in Großbuchstaben gefolgt von Datum in nächsten Zeilen
    # Erlaubt auch Kommas im Titel (z.B. "HAECKEL, DIE WELTRÄTSEL UND DIE THEOSOPHIE")
    h1_caps_pattern = re.compile(r'^#\s+[A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»,\.]+$')
    # Titel OHNE # in Großbuchstaben (z.B. "BIBEL UND WEISHEIT")
    no_hash_caps_pattern = re.compile(r'^[A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»,\.]+$')
    # Römische Zahl (I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, XIII, XIV, XV)
    roman_numeral_pattern = re.compile(r'^(I{1,3}|IV|VI{0,3}|IX|XI{0,3}|XIV|XV?|V)$')
    # Datum mit Jahr: "Berlin, 10. Oktober 1907"
    date_pattern = re.compile(r'^[A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*\d{4}$')
    # Datum ohne Jahr: "Berlin, 10. Oktober"
    date_pattern_no_year = re.compile(r'^[A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*$')
    
    # Inhaltsverzeichnis-Pattern
    toc_pattern = re.compile(r'^#\s*(INHALT|Inhalt|INHALTSVERZEICHNIS|Inhaltsverzeichnis)\s*$', re.IGNORECASE)
    
    # Hinweise-Pattern (am Ende) - alles nach diesem Punkt wird gelöscht
    # Erkennt auch "# HINWEISE, Textunterlagen:" etc.
    notes_pattern = re.compile(r'^#\s*(HINWEISE|Hinweise|ANMERKUNGEN|Anmerkungen|PERSONENREGISTER|Personenregister|RUDOLF STEINER GESAMTAUSGABE)', re.IGNORECASE)
    
    # "Zu dieser Ausgabe" Pattern (oft als "Xu dieser Ausgabe" durch OCR-Fehler)
    zu_dieser_ausgabe_pattern = re.compile(r'^#?\s*[XZ]u dieser Ausgabe', re.IGNORECASE)
    
    i = 0
    in_toc = False
    in_skip_section = False  # Für "Zu dieser Ausgabe" etc.
    lecture_indices = []  # (start_idx, end_idx) für jeden Vortrag
    current_lecture_start = None
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Prüfe auf Inhaltsverzeichnis
        if toc_pattern.match(line):
            in_toc = True
            i += 1
            continue
        
        # Prüfe auf "Zu dieser Ausgabe" (auch "Xu dieser Ausgabe")
        if zu_dieser_ausgabe_pattern.match(line):
            in_skip_section = True
            i += 1
            continue
        
        # Prüfe auf Hinweise am Ende (alles danach wird ignoriert)
        if notes_pattern.match(line):
            # Speichere letzten Vortrag und beende
            if current_lecture_start is not None:
                lecture_indices.append((current_lecture_start, i - 1))
                current_lecture_start = None  # Verhindere doppeltes Hinzufügen
            break
        
        # Prüfe auf Vortragstitel (mit Datum in Zeile)
        if lecture_pattern.match(line):
            in_toc = False
            in_skip_section = False
            if current_lecture_start is not None:
                lecture_indices.append((current_lecture_start, i - 1))
            current_lecture_start = i
            i += 1
            continue
        
        # Prüfe auf H1 in Großbuchstaben (könnte Vortragstitel sein)
        if h1_caps_pattern.match(line) and not toc_pattern.match(line) and not notes_pattern.match(line):
            # Prüfe ob in den nächsten 5 Zeilen ein Datum kommt
            found_date = False
            for j in range(i + 1, min(i + 6, len(lines))):
                line_j = lines[j].strip()
                if date_pattern.match(line_j) or date_pattern_no_year.match(line_j):
                    found_date = True
                    break
            
            if found_date:
                in_toc = False
                in_skip_section = False
                if current_lecture_start is not None:
                    lecture_indices.append((current_lecture_start, i - 1))
                current_lecture_start = i
        
        # Prüfe auf Titel OHNE # in Großbuchstaben (z.B. "BIBEL UND WEISHEIT")
        # Gefolgt von römischer Zahl und/oder Datum
        elif no_hash_caps_pattern.match(line) and not in_toc:
            # Prüfe ob in den nächsten 6 Zeilen ein Datum kommt (evtl. mit römischer Zahl dazwischen)
            found_date = False
            for j in range(i + 1, min(i + 7, len(lines))):
                line_j = lines[j].strip()
                if not line_j:
                    continue
                if date_pattern.match(line_j) or date_pattern_no_year.match(line_j):
                    found_date = True
                    break
                # Wenn es eine römische Zahl ist, weitersuchen
                if roman_numeral_pattern.match(line_j):
                    continue
                # Wenn es kein Datum und keine römische Zahl ist, abbrechen
                break
            
            if found_date:
                in_toc = False
                in_skip_section = False
                if current_lecture_start is not None:
                    lecture_indices.append((current_lecture_start, i - 1))
                current_lecture_start = i
        
        i += 1
    
    # Letzten Vortrag hinzufügen
    if current_lecture_start is not None:
        lecture_indices.append((current_lecture_start, len(lines) - 1))
    
    if not lecture_indices:
        print("  WARNUNG: Keine Vorträge gefunden, behalte gesamten Inhalt")
        return content
    
    # Extrahiere nur die Vorträge
    result_lines = []
    for start_idx, end_idx in lecture_indices:
        # Entferne führende Leerzeilen
        while start_idx <= end_idx and not lines[start_idx].strip():
            start_idx += 1
        # Entferne nachfolgende Leerzeilen
        while end_idx >= start_idx and not lines[end_idx].strip():
            end_idx -= 1
        
        if start_idx <= end_idx:
            result_lines.extend(lines[start_idx:end_idx + 1])
            result_lines.append('')  # Leerzeile zwischen Vorträgen
    
    print(f"  {len(lecture_indices)} Vorträge extrahiert")
    return '\n'.join(result_lines)


def convert_fragebeantwortung_to_h2(content: str) -> str:
    """
    Wandelt H1-Überschriften 'Fragebeantwortung' in H2 um.
    # Fragebeantwortung → ## Fragebeantwortung
    """
    # Pattern für verschiedene Schreibweisen
    patterns = [
        (r'^#\s+(Fragebeantwortung)\s*$', r'## \1'),
        (r'^#\s+(FRAGEBEANTWORTUNG)\s*$', r'## \1'),
        (r'^#\s+(Frage[-\s]?beantwortung)\s*$', r'## \1'),
        (r'^#\s+(Fragenbeantwortung)\s*$', r'## \1'),
        (r'^#\s+(FRAGENBEANTWORTUNG)\s*$', r'## \1'),
    ]
    
    lines = content.split('\n')
    result = []
    count = 0
    
    for line in lines:
        modified = False
        for pattern, replacement in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                count += 1
                modified = True
                break
        result.append(line)
    
    if count > 0:
        print(f"  {count} Fragebeantwortungen zu H2 konvertiert")
    
    return '\n'.join(result)


def format_lecture_titles(content: str, ga_number: str = "", toc_dates: dict = None) -> str:
    """
    Formatiere Vortragstitel:
    - Einzeilig: "# TITEL\n\nBerlin, Datum" → "# TITEL, Berlin, Datum"
    - Zweizeilig: "# TITEL\n## UNTERTITEL\n\nBerlin, Datum" → "# TITEL -  UNTERTITEL, Berlin, Datum"
    
    Wenn das Datum nicht korrekt erkennbar ist, wird es aus dem Inhaltsverzeichnis geholt.
    Falls auch das nicht möglich ist, wird die Zeile nach dem Titel dennoch angehängt.
    
    Args:
        content: Der MD-Inhalt
        ga_number: GA-Nummer (optional, für Debugging)
        toc_dates: Dictionary mit Titeln und Daten aus dem Inhaltsverzeichnis
    """
    if toc_dates is None:
        toc_dates = {}
    
    lines = content.split('\n')
    result = []
    i = 0
    formatted_count = 0
    toc_corrected_count = 0
    
    # Erweiterte Datumspatterns
    # Standard: "Berlin, 5. Oktober 1905"
    date_pattern_strict = re.compile(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+\s*\d{4})$')
    # Lockerer: auch mit OCR-Fehlern wie "Oktobcr" statt "Oktober"
    date_pattern_loose = re.compile(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-Za-zäöüß]+\s*\d{4})$')
    # Sehr locker: Ort, gefolgt von irgendwas mit Zahl und Jahr
    date_pattern_very_loose = re.compile(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*.+\d{4})$')
    # Ohne Jahr: "Berlin, 10. Oktober" (Jahr fehlt)
    date_pattern_no_year = re.compile(r'^([A-ZÄÖÜ][a-zäöüß]+,\s*\d{1,2}\.\s*[A-ZÄÖÜ][a-zäöüß]+)\s*$')
    
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf H1-Überschrift (Vortragstitel) - muss in Großbuchstaben sein
        h1_match = re.match(r'^#\s+([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»,]+)$', line)
        if h1_match:
            title1 = h1_match.group(1).strip()
            title1_normalized = re.sub(r'\s+', ' ', title1.upper().strip())
            
            # Prüfe ob nächste nicht-leere Zeile auch H1 ist (zweizeiliger Titel mit zwei H1)
            # z.B. "# SCHULFRAGEN\n\n# VOM STANDPUNKT DER GEISTESWISSENSCHAFT\n\nBerlin, 24. Januar 1907"
            # ODER: "# ERDENANFANG UND ERDENENDE\n\n# Berlin, 9. April 1908" (zweite H1 ist Datum)
            next_h1_idx = None
            next_h1_title = None
            for j in range(i + 1, min(i + 4, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                next_h1_match = re.match(r'^#\s+(.+)$', stripped)
                if next_h1_match:
                    next_h1_idx = j
                    next_h1_title = next_h1_match.group(1).strip()
                break  # Erste nicht-leere Zeile gefunden
            
            if next_h1_idx and next_h1_title:
                # Prüfe ob die zweite H1 ein Datum ist (z.B. "Berlin, 9. April 1908")
                is_date_h1 = False
                for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                    if pattern.match(next_h1_title):
                        is_date_h1 = True
                        break
                
                if is_date_h1:
                    # Zweite H1 ist das Datum - direkt anfügen ohne " - "
                    result.append(f"# {title1}, {next_h1_title}")
                    formatted_count += 1
                    i = next_h1_idx + 1
                    continue
                
                # Zweite H1 ist ein Untertitel - suche nach Datum danach
                # Suche nach Datum in den nächsten Zeilen nach der zweiten H1
                date = None
                date_idx = None
                for j in range(next_h1_idx + 1, min(next_h1_idx + 6, len(lines))):
                    stripped = lines[j].strip()
                    if not stripped:
                        continue
                    if stripped.startswith('#'):
                        break  # Nächste Überschrift erreicht
                    # Versuche verschiedene Patterns
                    for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                        date_match = pattern.match(stripped)
                        if date_match:
                            date = date_match.group(1)
                            date_idx = j
                            break
                    if date:
                        break
                    # Wenn keine leere Zeile und kein Datum, prüfe ob es eine Ort/Datum-Zeile ist
                    if stripped and ',' in stripped and any(c.isdigit() for c in stripped):
                        date = stripped
                        date_idx = j
                        break
                
                if date:
                    result.append(f"# {title1} - {next_h1_title}, {date}")
                    formatted_count += 1
                    i = date_idx + 1
                    continue
            
            # Prüfe ob nächste Zeile H2 ist (zweizeiliger Titel)
            if i + 1 < len(lines):
                h2_match = re.match(r'^##\s+(.+)$', lines[i + 1])
                if h2_match:
                    title2 = h2_match.group(1).strip()
                    
                    # Suche nach Datum in den nächsten 5 Zeilen
                    date = None
                    date_idx = None
                    for j in range(i + 2, min(i + 7, len(lines))):
                        stripped = lines[j].strip()
                        if not stripped:
                            continue
                        # Versuche verschiedene Patterns
                        for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                            date_match = pattern.match(stripped)
                            if date_match:
                                date = date_match.group(1)
                                date_idx = j
                                break
                        if date:
                            break
                        # Wenn keine leere Zeile und kein Datum, prüfe ob es eine Ort/Datum-Zeile ist
                        if stripped and not stripped.startswith('#') and ',' in stripped:
                            # Könnte Ort, Datum sein auch wenn Format nicht erkannt
                            date = stripped
                            date_idx = j
                            break
                    
                    # Versuche Datum aus TOC zu korrigieren
                    if date and toc_dates:
                        toc_date = toc_dates.get(title1_normalized)
                        if toc_date and toc_date != date:
                            date = toc_date
                            toc_corrected_count += 1
                    
                    if date:
                        result.append(f"# {title1} - {title2}, {date}")
                        formatted_count += 1
                        i = date_idx + 1
                        continue
            
            # Einzeiliger Titel: Suche nach Datum in den nächsten 5 Zeilen
            date = None
            date_idx = None
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                if stripped.startswith('Seite:'):
                    continue
                if stripped.startswith('#'):
                    break  # Nächste Überschrift erreicht
                
                # Versuche verschiedene Patterns
                for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                    date_match = pattern.match(stripped)
                    if date_match:
                        date = date_match.group(1)
                        date_idx = j
                        break
                if date:
                    break
                # Wenn keine leere Zeile und kein Datum, prüfe ob es eine Ort/Datum-Zeile ist
                if stripped and ',' in stripped and any(c.isdigit() for c in stripped):
                    # Könnte Ort, Datum sein auch wenn Format nicht erkannt
                    date = stripped
                    date_idx = j
                    break
            
            # Versuche Datum aus TOC zu korrigieren
            if date and toc_dates:
                toc_date = toc_dates.get(title1_normalized)
                if toc_date and toc_date != date:
                    date = toc_date
                    toc_corrected_count += 1
            elif not date and toc_dates:
                # Kein Datum gefunden, versuche aus TOC
                toc_date = toc_dates.get(title1_normalized)
                if toc_date:
                    date = toc_date
                    date_idx = i  # Kein extra Index zu überspringen
                    toc_corrected_count += 1
            
            if date:
                result.append(f"# {title1}, {date}")
                formatted_count += 1
                if date_idx and date_idx > i:
                    i = date_idx + 1
                else:
                    i += 1
                continue
        
        # Prüfe auf "## Erster/Zweiter/.../Zwölfter Vortrag" (H2 mit Zahlwort)
        # z.B. "## Zwölfter Vortrag\n\nBerlin, 10. November 1904" → "# Zwölfter Vortrag, Berlin, 10. November 1904"
        zahlwoerter = r'(?:[Ee]rster?|[Zz]weiter?|[Dd]ritter?|[Vv]ierter?|[Ff]ünfter?|[Ss]echster?|[Ss]iebter?|[Ss]iebenter?|[Aa]chter?|[Nn]eunter?|[Zz]ehnter?|[Ee]lfter?|[Zz]wölfter?|[Dd]reizehnter?|[Vv]ierzehnter?|[Ff]ünfzehnter?|[Ss]echzehnter?|[Ss]iebzehnter?|[Aa]chtzehnter?|[Nn]eunzehnter?|[Zz]wanzigster?)'
        h2_vortrag_match = re.match(rf'^##\s+({zahlwoerter}\s+Vortrag)\s*$', line.strip(), re.IGNORECASE)
        if h2_vortrag_match:
            vortrag_title = h2_vortrag_match.group(1).strip()
            
            # Suche nach Datum in den nächsten Zeilen
            date = None
            date_idx = None
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                if stripped.startswith('#'):
                    break
                for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                    date_match = pattern.match(stripped)
                    if date_match:
                        date = date_match.group(1)
                        date_idx = j
                        break
                if date:
                    break
                if stripped and ',' in stripped and any(c.isdigit() for c in stripped):
                    date = stripped
                    date_idx = j
                    break
            
            if date:
                result.append(f"# {vortrag_title}, {date}")
                formatted_count += 1
                i = date_idx + 1
                continue
        
        # Prüfe auf "Erster/Zweiter/.../Zwölfter Vortrag" OHNE # 
        # z.B. "Achter Vortrag\n\nBerlin, 2. November 1904" → "# Achter Vortrag, Berlin, 2. November 1904"
        plain_vortrag_match = re.match(rf'^({zahlwoerter}\s+Vortrag)\s*$', line.strip(), re.IGNORECASE)
        if plain_vortrag_match and not line.strip().startswith('#'):
            vortrag_title = plain_vortrag_match.group(1).strip()
            
            # Suche nach Datum in den nächsten Zeilen
            date = None
            date_idx = None
            for j in range(i + 1, min(i + 6, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                if stripped.startswith('#'):
                    break
                for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                    date_match = pattern.match(stripped)
                    if date_match:
                        date = date_match.group(1)
                        date_idx = j
                        break
                if date:
                    break
                if stripped and ',' in stripped and any(c.isdigit() for c in stripped):
                    date = stripped
                    date_idx = j
                    break
            
            if date:
                result.append(f"# {vortrag_title}, {date}")
                formatted_count += 1
                i = date_idx + 1
                continue
        
        # Prüfe auf Titel OHNE # in Großbuchstaben (z.B. "BIBEL UND WEISHEIT")
        # Gefolgt von römischer Zahl (I, II, III...) und Datum
        no_hash_match = re.match(r'^([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»,\.]+)$', line.strip())
        if no_hash_match and line.strip():
            title_no_hash = no_hash_match.group(1).strip()
            
            # Suche nach römischer Zahl und/oder Datum in den nächsten Zeilen
            roman_numeral = None
            date = None
            date_idx = None
            
            for j in range(i + 1, min(i + 7, len(lines))):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                
                # Prüfe auf römische Zahl
                roman_match = re.match(r'^(I{1,3}|IV|VI{0,3}|IX|XI{0,3}|XIV|XV?|V)$', stripped)
                if roman_match:
                    roman_numeral = roman_match.group(1)
                    continue
                
                # Prüfe auf Datum
                for pattern in [date_pattern_strict, date_pattern_loose, date_pattern_very_loose, date_pattern_no_year]:
                    date_match = pattern.match(stripped)
                    if date_match:
                        date = date_match.group(1)
                        date_idx = j
                        break
                if date:
                    break
                
                # Wenn keine leere Zeile und kein Datum und keine römische Zahl, abbrechen
                if stripped and ',' in stripped and any(c.isdigit() for c in stripped):
                    date = stripped
                    date_idx = j
                    break
                break
            
            if date:
                if roman_numeral:
                    result.append(f"# {title_no_hash} - {roman_numeral}, {date}")
                else:
                    result.append(f"# {title_no_hash}, {date}")
                formatted_count += 1
                if date_idx and date_idx > i:
                    i = date_idx + 1
                else:
                    i += 1
                continue
        
        # Normale Zeile
        result.append(line)
        i += 1
    
    if formatted_count > 0:
        print(f"  {formatted_count} Vortragstitel formatiert")
    if toc_corrected_count > 0:
        print(f"  {toc_corrected_count} Daten aus Inhaltsverzeichnis korrigiert")
    
    return '\n'.join(result)


def process_page_breaks(content: str) -> str:
    """
    Verarbeite Seitenumbrüche (---):
    - Entferne Seitenumbrüche innerhalb von Absätzen (in Fließtext verwandeln)
    - Behalte Seitenumbrüche zwischen Absätzen als Marker
    
    WICHTIG: Sei konservativ - entferne nur eindeutige Fälle innerhalb von Absätzen!
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Prüfe auf Seitenumbruchmarker (---)
        if line.strip() == '---':
            # Finde vorherige nicht-leere Zeile (ignoriere Überschriften und leere Zeilen)
            prev_idx = i - 1
            prev_text = None
            prev_line_idx = None
            while prev_idx >= 0:
                stripped = lines[prev_idx].strip()
                if stripped and not stripped.startswith('#'):
                    prev_text = stripped
                    prev_line_idx = prev_idx
                    break
                prev_idx -= 1
            
            # Finde nächste nicht-leere Zeile (ignoriere Überschriften und leere Zeilen)
            next_idx = i + 1
            next_text = None
            next_line_idx = None
            while next_idx < len(lines):
                stripped = lines[next_idx].strip()
                if stripped and not stripped.startswith('#'):
                    next_text = stripped
                    next_line_idx = next_idx
                    break
                next_idx += 1
            
            # Entscheide: Seitenumbruch zwischen Absätzen oder innerhalb?
            if prev_text and next_text:
                # Prüfe ob vorherige Zeile mit Satzzeichen endet (Absatzende)
                prev_ends_sentence = prev_text.endswith(('.', '!', '?', ':', ';', '»', '"'))
                
                # Prüfe ob nächste Zeile mit Großbuchstabe beginnt (neuer Satz/Absatz)
                next_starts_capital = next_text[0].isupper() if next_text else False
                
                # Prüfe ob vorherige Zeile bereits in result ist
                prev_in_result = result and result[-1].strip() == prev_text
                
                # NUR entfernen wenn:
                # 1. Vorherige Zeile endet NICHT mit Satzzeichen UND
                # 2. Nächste Zeile beginnt mit Kleinbuchstabe UND
                # 3. Vorherige Zeile ist bereits in result UND
                # 4. Es gibt keine leere Zeile zwischen prev und --- UND
                # 5. Es gibt keine leere Zeile zwischen --- und next
                # → eindeutiger Fall: Worttrennung innerhalb eines Absatzes
                
                # Prüfe ob leere Zeilen zwischen prev und --- oder --- und next
                has_empty_before = False
                has_empty_after = False
                if prev_line_idx is not None and i - prev_line_idx > 1:
                    # Prüfe Zeilen zwischen prev und ---
                    for k in range(prev_line_idx + 1, i):
                        if not lines[k].strip():
                            has_empty_before = True
                            break
                if next_line_idx is not None and next_line_idx - i > 1:
                    # Prüfe Zeilen zwischen --- und next
                    for k in range(i + 1, next_line_idx):
                        if not lines[k].strip():
                            has_empty_after = True
                            break
                
                if (not prev_ends_sentence and next_text[0].islower() and 
                    prev_in_result and not has_empty_before and not has_empty_after):
                    # Seitenumbruch innerhalb eines Absatzes → entfernen und verbinden
                    result.pop()  # Entferne letzte Zeile
                    
                    # Verbinde: Worttrennung ohne Leerzeichen
                    combined = prev_text + next_text
                    result.append(combined)
                    # Überspringe die nächste Zeile, da bereits verbunden
                    i = next_line_idx
                    continue
                else:
                    # Seitenumbruch zwischen Absätzen oder unsicher → Marker behalten
                    result.append('---')
            else:
                # Am Anfang oder Ende → Marker behalten
                result.append('---')
        else:
            result.append(line)
        
        i += 1
    
    return '\n'.join(result)


def extract_ga_number(filepath: Path) -> str:
    """Extrahiere GA-Nummer aus Dateinamen oder Pfad."""
    # Suche nach GA gefolgt von Zahlen
    match = re.search(r'GA\s*(\d+)', str(filepath), re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def find_pdf_file(input_path: Path) -> Optional[Path]:
    """Finde die passende PDF-Datei im selben Verzeichnis."""
    # Suche nach PDF mit gleichem Basisnamen
    pdf_candidates = [
        input_path.with_suffix('.pdf'),
        input_path.parent / f"{input_path.stem.replace('_prepared', '')}.pdf",
    ]
    
    # Suche auch nach PDFs mit ähnlichem Namen
    for pdf_file in input_path.parent.glob('*.pdf'):
        pdf_candidates.append(pdf_file)
    
    for pdf_path in pdf_candidates:
        if pdf_path.exists():
            return pdf_path
    
    return None


def run_add_page_numbers(md_path: Path, pdf_path: Path, output_path: Path) -> bool:
    """
    Führt add_page_numbers_from_pdf_v2.py aus.
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    script_path = Path(__file__).parent / 'add_page_numbers_from_pdf_v2.py'
    
    if not script_path.exists():
        print(f"  WARNUNG: Skript nicht gefunden: {script_path}")
        return False
    
    print(f"\n6. Füge Seitenzahlen aus PDF hinzu...")
    print(f"   PDF: {pdf_path.name}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(md_path), '--pdf', str(pdf_path), '-o', str(output_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Zeige relevante Ausgabe
            for line in result.stdout.split('\n'):
                if 'Marker' in line or 'Vortrag' in line or 'Gespeichert' in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"   FEHLER: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   FEHLER: {e}")
        return False


def prepare_reference_md(input_path: Path, pdf_path: Path = None, output_path: Path = None) -> str:
    """
    Hauptfunktion: Bereite MD-Referenzdatei vor.
    
    Args:
        input_path: Pfad zur Eingabe-MD-Datei
        pdf_path: Pfad zur PDF-Datei (optional, wird automatisch gesucht)
        output_path: Pfad zur Ausgabe-MD-Datei (optional)
    
    Returns:
        Der vorbereitete Inhalt als String
    """
    print(f"Lade Datei: {input_path.name}")
    content = input_path.read_text(encoding='utf-8')
    original_size = len(content)
    
    # Extrahiere GA-Nummer für Debugging
    ga_number = extract_ga_number(input_path)
    if ga_number:
        print(f"  GA-Nummer erkannt: GA{ga_number}")
    
    print("\n1. Extrahiere Daten aus Inhaltsverzeichnis...")
    toc_entries = extract_toc_entries(content)
    toc_dates = {e['title_normalized']: e['date'] for e in toc_entries}
    if toc_entries:
        print(f"  {len(toc_entries)} Einträge gefunden")
    else:
        print("  Kein Inhaltsverzeichnis gefunden")
    
    print("2. Entferne Copyright-Zeilen...")
    content = remove_copyright_lines(content)
    
    print("3. Extrahiere nur Vorträge (ohne Bibliographie, Inhalt, Hinweise)...")
    content = extract_lectures_only(content)
    
    print("4. Konvertiere Fragebeantwortungen zu H2...")
    content = convert_fragebeantwortung_to_h2(content)
    
    print("5. Formatiere Vortragstitel und verarbeite Seitenumbrüche...")
    content = format_lecture_titles(content, ga_number, toc_dates)
    content = process_page_breaks(content)

    # Verarbeite Bilder (JPEG zu PNG, Platzhalter aktualisieren)
    print("5b. Verarbeite Bilder...")
    content = process_images(input_path, content)

    # Speichere Zwischenergebnis (_prepared.md)
    prepared_path = input_path.parent / f"{input_path.stem}_prepared.md"
    prepared_path.write_text(content, encoding='utf-8')
    print(f"\n   Zwischenergebnis: {prepared_path.name}")
    print(f"   Original: {original_size:,} Zeichen → Bearbeitet: {len(content):,} Zeichen")
    
    # Finde PDF-Datei falls nicht angegeben
    if pdf_path is None:
        pdf_path = find_pdf_file(input_path)
    
    # Finale Ausgabe mit Seitenzahlen
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_final.md"
    
    if pdf_path and pdf_path.exists():
        # Führe add_page_numbers aus
        success = run_add_page_numbers(prepared_path, pdf_path, output_path)
        if success:
            final_content = output_path.read_text(encoding='utf-8')

            # Ergänze fehlende Seitenzahlen aus TOC
            if toc_entries:
                print("\n7. Ergänze fehlende Seitenzahlen aus TOC...")
                final_content = add_missing_page_numbers_from_toc(final_content, toc_entries)
                output_path.write_text(final_content, encoding='utf-8')
            
            # Validiere gegen Inhaltsverzeichnis
            if toc_entries:
                print("\n8. Validiere gegen Inhaltsverzeichnis...")
                validate_against_toc(final_content, toc_entries)

            print(f"\n✓ Finale Ausgabe: {output_path.name}")
            return final_content
        else:
            print(f"\n   Seitenzahlen konnten nicht hinzugefügt werden.")
            print(f"   Ausgabe ohne Seitenzahlen: {prepared_path.name}")
            return content
    else:
        print(f"\n   WARNUNG: Keine PDF-Datei gefunden.")
        print(f"   Ausgabe ohne Seitenzahlen: {prepared_path.name}")
        return content


def main():
    parser = argparse.ArgumentParser(
        description='Bereitet MD-Referenzdateien für GA-Bände vor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python tools/final_from_mistral_md.py "Steiner, Rudolf GA 052, 1986 - ...md" --pdf "GA052.pdf"
  python tools/final_from_mistral_md.py "GA052/Steiner, Rudolf GA 052.md"
  
Das Skript:
1. Entfernt Copyright-Zeilen
2. Extrahiert nur Vorträge (ohne Bibliographie, Inhaltsverzeichnis, Hinweise)
3. Konvertiert "# Fragebeantwortung" zu "## Fragebeantwortung"
4. Formatiert Vortragstitel und verarbeitet Seitenumbrüche
5. Fügt automatisch Seitenzahlen aus der PDF hinzu
        """
    )
    parser.add_argument('input_file', help='Pfad zur MD-Referenzdatei')
    parser.add_argument('--pdf', help='Pfad zur PDF-Datei (wird automatisch gesucht wenn nicht angegeben)')
    parser.add_argument('--output', '-o', help='Ausgabedatei (Standard: <input>_final.md)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"FEHLER: Datei nicht gefunden: {input_path}")
        sys.exit(1)
    
    pdf_path = Path(args.pdf) if args.pdf else None
    output_path = Path(args.output) if args.output else None
    
    prepare_reference_md(input_path, pdf_path, output_path)


if __name__ == '__main__':
    main()
