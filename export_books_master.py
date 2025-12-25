#!/usr/bin/env python3
"""
Master Export-Skript für Steiner GA-Schriften (GA001-GA046)
===========================================================
Exportiert Schriften als zusammenhängende Texte mit:
- Rechtschreibkorrekturen (wie bei Vorträgen)
- Überschriften-Umwandlung: H1→H3, H2→H4, H3→H4
- Inhaltsverzeichnis-Links zu Überschriften
- Fußnoten-Links
- Ausgabe als steiner_books_001-046.json (evtl. gesplittet)

Verwendung:
    python export_books_master.py                      # GA001-GA046
    python export_books_master.py GA001 GA002 GA003   # Nur bestimmte GA-Bände
"""

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool

# Importiere Rechtschreibkorrekturen
try:
    from rechtschreibregeln import korrigiere_rechtschreibung
except ImportError:
    print("Warnung: rechtschreibregeln.py nicht gefunden")
    def korrigiere_rechtschreibung(text):
        return text

# Importiere PIL für Bildkonvertierung
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warnung: PIL/Pillow nicht verfügbar. JPEG-zu-PNG Konvertierung wird übersprungen.")


def convert_jpeg_to_png_files(md_file_path):
    """
    Konvertiert alle JPEG-Bilder in PNG im assets-Ordner des GA-Bandes.
    Sucht alle .jpeg/.jpg Dateien im assets-Ordner und konvertiert sie zu .png.
    
    Args:
        md_file_path: Pfad zur Markdown-Datei
        
    Returns:
        Anzahl der konvertierten Dateien
    """
    if not PIL_AVAILABLE:
        return 0
    
    try:
        md_dir = os.path.dirname(md_file_path)
        
        # Finde assets-Ordner relativ zur Markdown-Datei
        assets_dir = os.path.join(md_dir, 'assets')
        
        if not os.path.exists(assets_dir):
            return 0
        
        converted_count = 0
        
        # Finde alle JPEG-Dateien im assets-Ordner
        for filename in os.listdir(assets_dir):
            if filename.lower().endswith('.jpeg') or filename.lower().endswith('.jpg'):
                jpeg_path = os.path.join(assets_dir, filename)
                
                # Erstelle PNG-Pfad
                png_filename = re.sub(r'\.jpe?g$', '.png', filename, flags=re.IGNORECASE)
                png_path = os.path.join(assets_dir, png_filename)
                
                # Überspringe wenn PNG bereits existiert
                if os.path.exists(png_path):
                    continue
                
                try:
                    # Konvertiere JPEG zu PNG
                    img = Image.open(jpeg_path)
                    img.save(png_path, 'PNG')
                    converted_count += 1
                except Exception as e:
                    print(f"    [WARN] Konvertierung fehlgeschlagen: {jpeg_path} -> {e}")
        
        return converted_count
        
    except Exception as e:
        print(f"    [WARN] Fehler beim Konvertieren der Bilder in {md_file_path}: {e}")
        return 0


def fix_image_placeholders_in_content(content):
    """
    Konvertiert JPEG-Platzhalter zu PNG in Markdown-Text.
    
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
    
    return content


class BooksExporter:
    def __init__(self, parallel_workers=4, skip_spelling=False):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.steiner_ga_dir = os.path.join(self.project_root, "Steiner_GA")
        self.books = []
        self.spelling_settings = self.load_spelling_settings() if not skip_spelling else None
        # PERFORMANCE: Lade summary-database.json einmal und halte sie im Speicher
        self.summary_db = self.load_summary_db()
        self.summary_db_modified = False
        self.parallel_workers = parallel_workers  # Anzahl paralleler Prozesse (Standard: 4)
        self.skip_spelling = skip_spelling  # Überspringe Rechtschreibkorrekturen für Geschwindigkeit
    
    def load_spelling_settings(self):
        """Lädt Rechtschreibkorrekturen aus ss-targeted-settings.json"""
        settings_path = os.path.join(self.steiner_ga_dir, "ss-targeted-settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warnung: Konnte ss-targeted-settings.json nicht laden: {e}")
        return None
    
    def load_summary_db(self):
        """Lädt summary-database.json einmal beim Start"""
        summary_db_path = Path(self.project_root) / 'summary-database.json'
        if summary_db_path.exists():
            try:
                print(f"Lade summary-database.json ({summary_db_path.stat().st_size / (1024*1024):.1f} MB)...")
                with open(summary_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Konnte summary-database.json nicht laden: {e}")
        return {}
    
    def save_summary_db(self, force=False):
        """Speichert summary-database.json nur wenn geändert (oder bei force=True)
        
        WICHTIG: Lädt die aktuelle Datei neu und merged sie mit den neuen Daten,
        um sicherzustellen, dass bestehende Vortrags-Einträge nicht überschrieben werden.
        """
        if not self.summary_db_modified and not force:
            return
        
        summary_db_path = Path(self.project_root) / 'summary-database.json'
        try:
            print(f"Speichere summary-database.json...")
            
            # WICHTIG: Lade die aktuelle Datei neu, um bestehende Vortrags-Daten zu erhalten
            # (könnte zwischenzeitlich durch Backend oder andere Prozesse geändert worden sein)
            existing_db = {}
            if summary_db_path.exists():
                try:
                    print(f"    Lade bestehende summary-database.json zum Mergen...")
                    with open(summary_db_path, 'r', encoding='utf-8') as f:
                        existing_db = json.load(f)
                    print(f"    Gefunden: {len(existing_db)} Einträge in bestehender Datei")
                except Exception as e:
                    print(f"    [WARN] Konnte bestehende Datei nicht laden: {e}")
                    existing_db = {}
            
            # Merge: Bestehende Daten behalten, neue/geänderte Bücher-Daten überschreiben
            # (nur für Bücher, nicht für Vorträge!)
            merged_db = existing_db.copy()
            
            # Füge nur Bücher-Einträge hinzu/aktualisiere sie (GA001-GA046, inkl. Varianten mit Suffix)
            # HINWEIS: GA262 und GA263a werden jetzt als BRIEFE exportiert (in export-lectures.js)
            MULTI_FILE_BOOKS = set()  # Keine Multi-File-Bücher mehr - GA262/GA263a sind jetzt Briefe
            books_added = 0
            for book_id, book_data in self.summary_db.items():
                # Prüfe ob es ein Buch ist (GA001-GA046, inkl. GA040a, GA041a, etc. + Multi-File-Bücher)
                # Bücher haben IDs wie "GA001", "GA002", "GA040a", "GA262", etc. (kein "/" wie bei Vorträgen)
                # Pattern: GA gefolgt von 3 Ziffern, optional gefolgt von einem Buchstaben
                is_book = isinstance(book_id, str) and (
                    (re.match(r'^GA\d{3}[a-z]?$', book_id) is not None and '/' not in book_id) or
                    book_id in MULTI_FILE_BOOKS
                )
                
                if is_book:
                    # Bücher-ID: Überschreibe oder füge hinzu (überschreibt bestehende Einträge!)
                    merged_db[book_id] = book_data
                    books_added += 1
                else:
                    # Vortrags-ID: Nur hinzufügen wenn noch nicht vorhanden (nicht überschreiben!)
                    if book_id not in merged_db:
                        merged_db[book_id] = book_data
                    # Wenn vorhanden, behalte bestehende Vortrags-Daten (nicht überschreiben)
            
            print(f"    {books_added} Bücher-Einträge hinzugefügt/aktualisiert")
            print(f"    Gesamt: {len(merged_db)} Einträge (Bücher + Vorträge)")
            
            # Debug: Prüfe was gespeichert wird
            if 'GA001' in merged_db and merged_db['GA001'].get('headings'):
                first_heading = merged_db['GA001']['headings'][0]
                print(f"    [DEBUG-SAVE] GA001 erste Überschrift Index vor Speichern: {first_heading.get('index')}")
            
            # Speichere die gemergte Datenbank
            with open(summary_db_path, 'w', encoding='utf-8') as f:
                json.dump(merged_db, f, indent=2, ensure_ascii=False)
            
            # Debug: Prüfe was tatsächlich gespeichert wurde
            with open(summary_db_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                if 'GA001' in saved_data and saved_data['GA001'].get('headings'):
                    first_saved = saved_data['GA001']['headings'][0]
                    print(f"    [DEBUG-SAVE] GA001 erste Überschrift Index nach Speichern: {first_saved.get('index')}")
            
            # Aktualisiere self.summary_db mit den gemergten Daten für weitere Operationen
            self.summary_db = merged_db
            self.summary_db_modified = False
            print(f"[OK] summary-database.json gespeichert (gemergt mit bestehenden Daten)")
        except Exception as e:
            print(f"[WARN] Konnte summary-database.json nicht speichern: {e}")
            # Versuche es nochmal mit ensure_ascii=True für problematische Zeichen
            try:
                # Auch hier: Lade bestehende Datei und merge
                existing_db = {}
                if summary_db_path.exists():
                    try:
                        with open(summary_db_path, 'r', encoding='utf-8') as f:
                            existing_db = json.load(f)
                    except:
                        pass
                
                merged_db = existing_db.copy()
                # HINWEIS: GA262 und GA263a werden jetzt als BRIEFE exportiert (in export-lectures.js)
                MULTI_FILE_BOOKS = set()  # Keine Multi-File-Bücher mehr
                for book_id, book_data in self.summary_db.items():
                    # Prüfe ob es ein Buch ist (GA001-GA046)
                    is_book = isinstance(book_id, str) and (
                        (book_id.startswith('GA0') and len(book_id) <= 5 and '/' not in book_id) or
                        book_id in MULTI_FILE_BOOKS
                    )
                    
                    if is_book:
                        merged_db[book_id] = book_data
                    elif book_id not in merged_db:
                        merged_db[book_id] = book_data
                
                with open(summary_db_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_db, f, indent=2, ensure_ascii=True)
                self.summary_db = merged_db
                self.summary_db_modified = False
                print(f"[OK] summary-database.json gespeichert (mit ASCII-Escaping, gemergt)")
            except Exception as e2:
                print(f"[FEHLER] Konnte summary-database.json nicht speichern: {e2}")
        
    def find_book_files(self, ga_folder):
        """Findet die Markdown-Datei(en) eines GA-Bandes.
        
        Gibt ein Tuple zurück: (is_multi_file, files)
        - is_multi_file: True wenn Multi-File-Buch (z.B. GA001 mit Kapiteln)
        - files: Liste der Dateien (sortiert nach Kapitelnummer bei Multi-File)
        """
        md_files = list(ga_folder.glob("GA*.md"))
        
        # Filtere Backup-Dateien aus
        md_files = [f for f in md_files if not f.name.endswith('.backup')]
        
        # Suche nach Multi-File-Format: "GAXXX (N.) KAPITELNAME.md"
        # z.B. "GA001 (1.) ZUR EINFÜHRUNG.md", "GA001 (2.) ERSTER BAND.md"
        chapter_files = []
        for md_file in md_files:
            name = md_file.name
            # Multi-File-Kapitel: "GAXXX (N.) KAPITELNAME.md" (OHNE Komma/Datum = kein Vortrag)
            match = re.match(r'GA\d{2,3}[a-z]?\s*\((\d+)\.\)\s+([^,]+)\.md$', name)
            if match:
                chapter_num = int(match.group(1))
                chapter_files.append((chapter_num, md_file))
        
        # Wenn Multi-File-Kapitel gefunden, sortiere nach Kapitelnummer
        if len(chapter_files) >= 2:
            chapter_files.sort(key=lambda x: x[0])
            return (True, [f for _, f in chapter_files])
        
        # Sonst: Suche nach Einzeldatei (altes Verhalten)
        main_files_with_year = []
        main_files_without_year = []
        for md_file in md_files:
            name = md_file.name
            # Überspringe Vortragsdateien (Format: "GAXXX (N.) Titel, Ort, Datum.md" - MIT Komma)
            if re.match(r'GA\d{2,3}[a-z]?\s*\([0-9]+\.\)\s+.+,.+\.md', name):
                continue
            # Hauptdatei mit Jahr: "GAXXX - Titel (Jahr).md" oder "GAXXXa - Titel (Jahr).md"
            if re.match(r'GA\d{2,3}[a-z]?\s*-\s*.+\(.+\)\.md', name):
                main_files_with_year.append(md_file)
            # Hauptdatei ohne Jahr: "GAXXX - Titel.md" oder "GAXXXa - Titel.md"
            elif re.match(r'GA\d{2,3}[a-z]?\s*-\s*.+\.md', name):
                main_files_without_year.append(md_file)
        
        # Bevorzuge Dateien mit Jahr, falls vorhanden
        if main_files_with_year:
            return (False, [main_files_with_year[0]])
        elif main_files_without_year:
            return (False, [main_files_without_year[0]])
        return (False, [])
    
    def find_book_file(self, ga_folder):
        """Legacy-Wrapper für find_book_files() - gibt nur eine Datei zurück"""
        is_multi, files = self.find_book_files(ga_folder)
        return files[0] if files else None
    
    def convert_headings(self, text):
        """Wandelt Überschriften um: H1→H3, H2→H4, H3→H4"""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # H1 (# Überschrift) → H3 (### Überschrift)
            if re.match(r'^#\s+[^#]', line):
                line = re.sub(r'^#\s+', '### ', line)
            # H2 (## Überschrift) → H4 (#### Überschrift)
            elif re.match(r'^##\s+[^#]', line):
                line = re.sub(r'^##\s+', '#### ', line)
            # H3 (### Überschrift) → H4 (#### Überschrift)
            elif re.match(r'^###\s+[^#]', line):
                line = re.sub(r'^###\s+', '#### ', line)
            
            result.append(line)
        
        return '\n'.join(result)
    
    def extract_headings(self, text):
        """Extrahiert alle Überschriften mit ihren IDs"""
        headings = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Erkenne H3 und H4 Überschriften (nach Umwandlung)
            match = re.match(r'^(###|####)\s+(.+)$', line)
            if match:
                level = 3 if match.group(1) == '###' else 4
                heading_text = match.group(2).strip()
                
                # Erstelle ID aus Überschrift (wie Markdown es macht)
                heading_id = self.create_heading_id(heading_text)
                
                headings.append({
                    'id': heading_id,
                    'text': heading_text,
                    'level': level,
                    'line': i + 1
                })
        
        return headings
    
    def extract_paragraphs(self, text):
        """Extrahiert Absätze aus Text (ohne Überschriften), ähnlich wie bei Vorträgen"""
        paragraphs = []
        lines = text.split('\n')
        current_paragraph = ''
        current_index = None
        
        for line in lines:
            # Überspringe Überschriften (H3/H4)
            if re.match(r'^#{3,4}\s+', line):
                # Wenn wir einen Absatz gesammelt haben, speichere ihn
                if current_paragraph.strip() and current_index:
                    paragraphs.append({
                        'index': current_index,
                        'content': current_paragraph.strip()
                    })
                    current_paragraph = ''
                continue
            
            # Überspringe leere Zeilen (werden ignoriert)
            if not line.strip():
                # Wenn wir einen Absatz gesammelt haben und eine leere Zeile kommt,
                # könnte das das Ende eines Absatzes sein
                if current_paragraph.strip() and current_index:
                    paragraphs.append({
                        'index': current_index,
                        'content': current_paragraph.strip()
                    })
                    current_paragraph = ''
                continue
            
            # Suche nach Index am Ende der Zeile (Format: ^abc123)
            index_match = re.search(r'\s+(\^[a-z0-9]+)\s*$', line)
            
            if index_match:
                index = index_match.group(1)
                line_without_index = re.sub(r'\s+\^[a-z0-9]+\s*$', '', line).strip()
                
                # Wenn wir bereits einen Absatz gesammelt haben, speichere ihn
                if current_paragraph.strip() and current_index:
                    paragraphs.append({
                        'index': current_index,
                        'content': current_paragraph.strip()
                    })
                
                # Starte neuen Absatz
                if line_without_index:
                    current_paragraph = line_without_index
                else:
                    current_paragraph = ''
                current_index = index
            else:
                # Füge Zeile zum aktuellen Absatz hinzu
                if current_paragraph:
                    current_paragraph += ' ' + line.strip()
                else:
                    current_paragraph = line.strip()
        
        # Speichere letzten Absatz falls vorhanden
        if current_paragraph.strip() and current_index:
            paragraphs.append({
                'index': current_index,
                'content': current_paragraph.strip()
            })
        
        return paragraphs
    
    def link_headings_to_paragraphs(self, headings, paragraphs, content):
        """Verknüpft Überschriften mit Absatz-Indizes.
        
        WICHTIG: Die Suche erfolgt sequenziell - jede Überschrift wird nur ab der 
        Position der vorherigen Überschrift gesucht. Das verhindert, dass Überschriften
        wie "I", "II" aus verschiedenen Kapiteln auf denselben Absatz-Index gemappt werden.
        """
        linked_headings = []
        
        if not paragraphs:
            # Wenn keine Absätze vorhanden, verwende die ursprünglichen heading IDs als index
            for heading in headings:
                linked_headings.append({
                    'index': heading.get('id', ''),
                    'text': heading['text'],
                    'level': f'h{heading["level"]}'
                })
            return linked_headings
        
        # PERFORMANCE: Erstelle Mapping von Paragraph-Indizes zu Positionen EINMAL (nicht für jede Überschrift)
        para_positions = []
        for para in paragraphs:
            if para['index']:
                # Finde die Position dieses Paragraph-Index im Content
                # WICHTIG: Der Index steht am Ende einer Zeile, z.B. "Text ^abc123"
                index_pattern = re.compile(r'\s+' + re.escape(para['index']) + r'\s*$', re.MULTILINE)
                para_match = index_pattern.search(content)
                if para_match:
                    para_positions.append((para_match.start(), para['index']))
                else:
                    # Fallback: Suche nach Index irgendwo im Content (falls Format anders ist)
                    pos = content.find(para['index'])
                    if pos >= 0:
                        para_positions.append((pos, para['index']))
        
        # Sortiere nach Position (nur einmal)
        para_positions.sort(key=lambda x: x[0])
        
        # PERFORMANCE: Erstelle Liste von Absatz-Indizes für schnellen Zugriff
        para_indices_by_pos = [idx for pos, idx in para_positions]
        
        # SEQUENZIELLE SUCHE: Starte bei Position 0 und suche jede Überschrift nur ab der 
        # Position der vorherigen. Das verhindert, dass "I" aus Kapitel 2 auf den ersten
        # Absatz nach "I" aus Kapitel 1 gemappt wird.
        search_start_pos = 0
        
        for heading_idx, heading in enumerate(headings):
            heading_text = heading['text']
            heading_level = heading['level']
            
            # PERFORMANCE: Verwende einfache String-Suche statt mehrerer Regex-Patterns
            # Suche nach Überschrift im Content (mit Markdown-Syntax)
            # WICHTIG: Suche nur ab search_start_pos!
            heading_text_escaped = re.escape(heading_text.strip())
            
            # Versuche zuerst exakte Übereinstimmung mit Markdown-Syntax
            heading_position = -1
            for markdown_level in ['###', '####']:
                pattern_str = f'{markdown_level} {heading_text}'
                # Suche ab search_start_pos, nicht ab 0!
                pos = content.find(pattern_str, search_start_pos)
                if pos >= 0:
                    heading_position = pos
                    break
            
            # Wenn nicht gefunden, suche nur nach Text (schneller)
            if heading_position == -1:
                # Suche ab search_start_pos, nicht ab 0!
                heading_pos = content.find(heading_text, search_start_pos)
                if heading_pos >= 0:
                    # Prüfe ob es wirklich eine Überschrift ist (hat # davor)
                    before_text = content[max(0, heading_pos - 50):heading_pos]
                    if '###' in before_text or '####' in before_text:
                        heading_position = heading_pos
            
            # Finde den ersten Absatz nach dieser Überschrift
            paragraph_index = None
            if heading_position >= 0 and para_positions:
                # Verwende bereits sortierte Liste, aber nur Absätze nach heading_position
                for pos, para_idx in para_positions:
                    if pos > heading_position:
                        paragraph_index = para_idx
                        break
                
                # Aktualisiere search_start_pos für die nächste Überschrift
                # So wird die nächste Überschrift nur ab hier gesucht
                search_start_pos = heading_position + 1
            
            # Fallback 1: Suche nach Paragraph, der mit der Überschrift beginnt
            # WICHTIG: Auch hier nur Paragraphs ab der aktuellen Position berücksichtigen
            if not paragraph_index:
                heading_text_lower = heading_text.lower().strip()
                for para in paragraphs:
                    para_content = (para.get('content') or '').lower().strip()
                    if para_content.startswith(heading_text_lower) or heading_text_lower in para_content[:100]:
                        # Prüfe ob dieser Paragraph nach search_start_pos kommt
                        para_idx = para['index']
                        para_pos = next((pos for pos, idx in para_positions if idx == para_idx), -1)
                        if para_pos >= search_start_pos or search_start_pos == 0:
                            paragraph_index = para_idx
                            # Aktualisiere search_start_pos
                            if para_pos > 0:
                                search_start_pos = para_pos + 1
                            break
            
            # Fallback 2: Verwende sequenziell die nächsten Absätze für die Überschriften
            if not paragraph_index and paragraphs:
                # Finde den nächsten Absatz ab search_start_pos
                for pos, para_idx in para_positions:
                    if pos >= search_start_pos:
                        paragraph_index = para_idx
                        search_start_pos = pos + 1
                        break
                
                # Wenn kein Absatz mehr nach search_start_pos, verwende den letzten
                if not paragraph_index:
                    paragraph_index = paragraphs[-1]['index']
            
            # WICHTIG: Stelle sicher, dass immer ein Index gesetzt wird
            if not paragraph_index and paragraphs:
                paragraph_index = paragraphs[0]['index']
            
            linked_headings.append({
                'index': paragraph_index or '',
                'text': heading_text,
                'level': f'h{heading_level}'
            })
        
        return linked_headings
    
    def save_headings_to_summary_db(self, book_id, headings):
        """Speichert Überschriften in summary-database.json (im Speicher, wird am Ende gespeichert)"""
        # Erstelle oder aktualisiere Eintrag für dieses Buch im Speicher
        if book_id not in self.summary_db:
            self.summary_db[book_id] = {}
        
        # Debug: Prüfe ob Überschriften Absatz-Indizes haben
        if headings:
            first_heading_index = headings[0].get('index', '')
            if first_heading_index and first_heading_index.startswith('^'):
                print(f"    [DEBUG] Überschriften haben Absatz-Indizes: {first_heading_index}")
            else:
                print(f"    [WARN] Überschriften haben KEINE Absatz-Indizes! Erste Überschrift Index: {first_heading_index}")
        
        # Speichere nur Überschriften (keine Summary, keine Keywords)
        self.summary_db[book_id]['headings'] = headings
        self.summary_db[book_id]['tableOfContents'] = [
            {
                'heading': h['text'],
                'description': '',  # Bücher haben keine Beschreibungen
                'index': h['index']
            }
            for h in headings
        ]
        self.summary_db[book_id]['version'] = 'v2'
        
        # WICHTIG: Markiere als geändert (wird am Ende gespeichert)
        self.summary_db_modified = True
        print(f"    [OK] Überschriften für {book_id} vorbereitet ({len(headings)} Überschriften)")
    
    def create_heading_id(self, text):
        """Erstellt eine Markdown-kompatible ID aus Überschriftstext"""
        # Entferne Sonderzeichen, konvertiere zu Kleinbuchstaben
        # Ersetze Leerzeichen durch Bindestriche
        id_text = text.lower()
        # Ersetze Umlaute
        id_text = id_text.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
        # Entferne Sonderzeichen außer Bindestrichen und Leerzeichen
        id_text = re.sub(r'[^a-z0-9\s-]', '', id_text)
        # Ersetze Leerzeichen durch Bindestriche
        id_text = re.sub(r'\s+', '-', id_text)
        # Entferne mehrfache Bindestriche
        id_text = re.sub(r'-+', '-', id_text)
        # Entferne führende/abschließende Bindestriche
        id_text = id_text.strip('-')
        
        return id_text
    
    def fix_toc_links(self, text, headings):
        """Korrigiert Links im Inhaltsverzeichnis zu den neuen Überschriften"""
        lines = text.split('\n')
        result = []
        
        # Erstelle Mapping von altem Link-Text zu neuer ID
        heading_map = {}
        for heading in headings:
            # Original-Text als Key
            heading_map[heading['text']] = heading['id']
            # Auch ohne Sonderzeichen
            clean_text = re.sub(r'[^\w\s]', '', heading['text'])
            heading_map[clean_text] = heading['id']
        
        for line in lines:
            # Erkenne Links im Format: [[#Überschrift]] oder [[#Überschrift|Text]]
            # Pattern: [[#...]]
            def replace_link(match):
                link_content = match.group(1)
                
                # Entferne # am Anfang falls vorhanden
                if link_content.startswith('#'):
                    link_content = link_content[1:]
                
                # Prüfe ob Pipe vorhanden ([[#Text|Anzeige]])
                if '|' in link_content:
                    link_text, display_text = link_content.split('|', 1)
                    link_text = link_text.strip()
                    display_text = display_text.strip()
                else:
                    link_text = link_content.strip()
                    display_text = link_text
                
                # Finde passende Überschrift
                heading_id = None
                for heading in headings:
                    if heading['text'] == link_text or heading['text'].upper() == link_text.upper():
                        heading_id = heading['id']
                        break
                
                if heading_id:
                    return f'[[#{heading_id}|{display_text}]]'
                else:
                    # Falls nicht gefunden, versuche ID direkt zu erstellen
                    heading_id = self.create_heading_id(link_text)
                    return f'[[#{heading_id}|{display_text}]]'
            
            # Ersetze Links
            line = re.sub(r'\[\[#([^\]]+)\]\]', replace_link, line)
            result.append(line)
        
        return '\n'.join(result)
    
    def roman_to_arabic(self, roman):
        """Konvertiert römische Ziffern (i, ii, iii, etc.) zu arabischen Zahlen"""
        roman_map = {
            'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
            'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
            'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
            'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20,
            'xxi': 21, 'xxii': 22, 'xxiii': 23, 'xxiv': 24, 'xxv': 25,
            'xxvi': 26, 'xxvii': 27, 'xxviii': 28, 'xxix': 29, 'xxx': 30,
            'xl': 40, 'l': 50, 'lx': 60, 'lxx': 70, 'lxxx': 80, 'xc': 90, 'c': 100
        }
        # Erweitere für größere Zahlen
        for i in range(31, 200):
            if i <= 30:
                continue
            if i < 40:
                roman_map[f'xxx{"i" * (i - 30)}'] = i
            elif i < 50:
                roman_map[f'xl{"i" * (i - 40)}'] = i
            elif i < 60:
                roman_map[f'l{"i" * (i - 50)}'] = i
            elif i < 70:
                roman_map[f'lx{"i" * (i - 60)}'] = i
            elif i < 80:
                roman_map[f'lxx{"i" * (i - 70)}'] = i
            elif i < 90:
                roman_map[f'lxxx{"i" * (i - 80)}'] = i
            elif i < 100:
                roman_map[f'xc{"i" * (i - 90)}'] = i
        
        return roman_map.get(roman.lower(), None)
    
    def convert_footnotes(self, text):
        """Sichert Markdown-Fußnoten und konvertiert alte Formate falls vorhanden"""
        lines = text.split('\n')
        
        # Schritt 1: Prüfe ob bereits Markdown-Fußnoten vorhanden sind
        has_markdown_footnotes = False
        for line in lines:
            if re.match(r'^\[\^(\d+)\]:\s*(.+)$', line):
                has_markdown_footnotes = True
                break
        
        # Wenn bereits Markdown-Fußnoten vorhanden, nur bereinigen
        if has_markdown_footnotes:
            # Entferne Backlinks (↩) aus Fußnoten-Definitionen, falls vorhanden
            # Unterstützt mehrzeilige Fußnoten
            result_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Prüfe auf Fußnoten-Definitionen [^n]: Text
                match = re.match(r'^(\[\^\d+\]:\s*)(.+)$', line)
                if match:
                    prefix = match.group(1)
                    fn_text = match.group(2)
                    i += 1
                    
                    # Sammle alle nachfolgenden Zeilen, die Teil dieser Fußnote sind
                    # Eine Fußnote endet, wenn:
                    # 1. Eine neue Fußnote beginnt ([^n]:)
                    # 2. Eine Überschrift beginnt (#)
                    # 3. Normaler Text ohne Einrückung beginnt (aber das ist schwer zu erkennen)
                    # Strategie: Sammle Zeilen bis zur nächsten Fußnote, aber stoppe auch bei Überschriften
                    while i < len(lines):
                        next_line = lines[i]
                        # Prüfe ob nächste Zeile eine neue Fußnote ist
                        if re.match(r'^\[\^\d+\]:', next_line):
                            break
                        # Prüfe ob nächste Zeile eine Überschrift ist (Fußnoten stehen normalerweise vor dem normalen Text)
                        if re.match(r'^#+\s+', next_line):
                            break
                        # Prüfe ob nächste Zeile leer ist
                        if next_line.strip() == '':
                            # Prüfe ob nach der leeren Zeile eine neue Fußnote oder Überschrift kommt
                            if i + 1 < len(lines):
                                next_next = lines[i + 1]
                                if re.match(r'^\[\^\d+\]:', next_next) or re.match(r'^#+\s+', next_next):
                                    break
                            # Sonst ist es Teil der Fußnote (leere Zeile innerhalb)
                            fn_text += '\n' + next_line
                            i += 1
                            continue
                        # Alle anderen Zeilen sind Teil der Fußnote
                        fn_text += '\n' + next_line
                        i += 1
                    
                    # Bereinige den Fußnoten-Text
                    fn_text = fn_text.strip()
                    # Entferne trailing Backlinks
                    fn_text = re.sub(r'\s*[↩↩︎]\s*$', '', fn_text)
                    # Entferne mehrfache Leerzeilen am Ende
                    fn_text = re.sub(r'\n\n+$', '\n', fn_text)
                    result_lines.append(prefix + fn_text)
                else:
                    result_lines.append(line)
                    i += 1
            return '\n'.join(result_lines)
        
        # Schritt 2: Fallback: Konvertiere alte römische Ziffern-Format falls vorhanden
        footnote_definitions = {}
        footnote_section_start = None
        
        # Finde Fußnoten-Sektion (römische Ziffern: i[...], ii[...], etc.)
        for i in range(len(lines) - 1, max(0, len(lines) - 200), -1):
            line = lines[i].strip()
            if re.match(r'^([ivxlcdm]+)\s*[\[(](.+?)[\])]\s*$', line, re.IGNORECASE):
                footnote_section_start = i
                break
        
        # Extrahiere alte Fußnoten-Definitionen
        if footnote_section_start is not None:
            for i in range(footnote_section_start, len(lines)):
                line = lines[i].strip()
                match = re.match(r'^([ivxlcdm]+)\s*[\[(](.+?)[\])]\s*$', line, re.IGNORECASE)
                if match:
                    roman = match.group(1).lower()
                    fn_text = match.group(2).strip()
                    arabic = self.roman_to_arabic(roman)
                    if arabic:
                        footnote_definitions[arabic] = fn_text
                        lines[i] = ''  # Markiere zum Entfernen
        
        # Schritt 3: Ersetze alte Referenzen im Text (.i, .ii, etc.)
        def replace_footnote_ref(match):
            roman = match.group(1).lower()
            arabic = self.roman_to_arabic(roman)
            if arabic:
                return f'[^{arabic}]'
            return match.group(0)
        
        text = re.sub(r'\.([ivxlcdm]+)\b', replace_footnote_ref, text, flags=re.IGNORECASE)
        
        # Schritt 4: Füge konvertierte Fußnoten-Definitionen hinzu
        if footnote_definitions:
            lines = [line for line in lines if line.strip() or line == '']
            text = '\n'.join(lines)
            
            footnotes_section = '\n\n'
            for fn_num in sorted(footnote_definitions.keys()):
                fn_text = footnote_definitions[fn_num].strip()
                fn_text = re.sub(r'\s*[↩↩︎]\s*$', '', fn_text)
                footnotes_section += f'[^{fn_num}]: {fn_text}\n'
            
            text += footnotes_section
        
        return text
    
    def fix_spelling(self, text):
        """Korrigiert deutsche Rechtschreibung (wie in export_master.py und ss-targeted-settings.json)"""
        # Verwende zuerst die umfassende Rechtschreibkorrektur aus rechtschreibregeln.py
        text = korrigiere_rechtschreibung(text)
        
        # Zusätzliche spezifische Korrekturen
        spelling_replacements = [
            ('Fleiss', 'Fleiß'),
            ('fleiss', 'fleiß'),
            ('vergeßlich', 'vergesslich'),
            ('heiss', 'heiß'),
            ('zurücckommen', 'zurückkommen'),
            ('ackurat', 'akkurat'),
            ('paßt', 'passt'),
            ('römischkatholisch', 'römisch-katholisch'),
            ('seelischgeistig', 'seelisch-geistig'),
            ('DeutschÖsterreicher', 'Deutsch-Österreicher'),
            # Mißverständnis Varianten
            ('Mißverständnisse', 'Missverständnisse'),
            ('mißverständnisse', 'missverständnisse'),
            ('Mißverständnis', 'Missverständnis'),
            ('mißverständnis', 'missverständnis'),
            ('Mißverständnissen', 'Missverständnissen'),
            ('mißverständnissen', 'missverständnissen'),
            # angepaßt Varianten
            ('angepaßt', 'angepasst'),
            ('Angepaßt', 'Angepasst'),
            ('angepaßte', 'angepasste'),
            ('Angepaßte', 'Angepasste'),
            ('angepaßten', 'angepassten'),
            ('Angepaßten', 'Angepassten'),
            ('angepaßter', 'angepasster'),
            ('Angepaßter', 'Angepasster')
        ]
        
        # Lade zusätzliche Korrekturen aus ss-targeted-settings.json
        if self.spelling_settings:
            # Parse exactReplacements
            for replacement in self.spelling_settings.get('exactReplacements', []):
                if '=>' in replacement:
                    parts = replacement.split('=>', 1)
                    old_text = parts[0].strip()
                    new_text = parts[1].strip()
                    if old_text and new_text:
                        # Füge sowohl Original als auch Großschreibung-Variante hinzu
                        spelling_replacements.append((old_text, new_text))
                        if old_text[0].isupper():
                            spelling_replacements.append((old_text.lower(), new_text.lower()))
                        elif old_text[0].islower():
                            spelling_replacements.append((old_text.capitalize(), new_text.capitalize()))
        
        # Wende exact replacements an
        for old_spelling, new_spelling in spelling_replacements:
            text = text.replace(old_spelling, new_spelling)
        
        # Wende regex replacements an (aus ss-targeted-settings.json)
        if self.spelling_settings:
            for replacement in self.spelling_settings.get('regexReplacements', []):
                if '=>' in replacement:
                    parts = replacement.split('=>', 1)
                    pattern = parts[0].strip()
                    replacement_text = parts[1].strip()
                    if pattern and replacement_text:
                        try:
                            # Verwende re.sub mit Flags für case-insensitive und Unicode
                            text = re.sub(pattern, replacement_text, text, flags=re.IGNORECASE | re.UNICODE)
                        except re.error as e:
                            # Ignoriere ungültige Regex-Patterns
                            pass
        
        return text
    
    def format_paragraph_content(self, content):
        """
        Formatiert Paragraph-Content:
        1. Gedichte: Reduziert doppelte Leerzeilen zwischen Zeilen auf einfache
        2. Durchgezogene Linien: Konvertiert * * * zu * * *
        """
        if not content:
            return content
        
        # 1. Durchgezogene Linien: Konvertiere * * * zu * * * (beide sind identisch, aber sicherstellen)
        # Pattern: * * * oder * * * mit variablen Leerzeichen
        content = re.sub(r'\*\s+\*\s+\*', '* * *', content)
        
        # 2. Gedichte: Reduziere doppelte Leerzeilen zwischen Zeilen auf einfache
        # Erkenne Gedichte: Mehrere kurze Zeilen (< 90 Zeichen) hintereinander
        lines = content.split('\n')
        result_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_length = len(line.strip())
            
            # Prüfe ob aktuelle Zeile kurz ist (potentielles Gedicht)
            if line_length > 0 and line_length < 90:
                # Prüfe ob nächste Zeile auch kurz ist (Gedicht erkannt)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_line_length = len(next_line.strip())
                    
                    # Wenn nächste Zeile leer ist, prüfe die übernächste
                    if next_line_length == 0 and i + 2 < len(lines):
                        next_next_line = lines[i + 2]
                        next_next_length = len(next_next_line.strip())
                        
                        # Wenn übernächste Zeile auch kurz ist, überspringe die leere Zeile
                        if next_next_length > 0 and next_next_length < 90:
                            result_lines.append(line)
                            i += 1  # Überspringe leere Zeile
                            continue
                    
                    # Wenn nächste Zeile auch kurz ist, füge keine Leerzeile ein
                    if next_line_length > 0 and next_line_length < 90:
                        result_lines.append(line)
                        i += 1
                        continue
            
            # Normale Zeile: Füge hinzu
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def process_book(self, ga_folder):
        """Verarbeitet einen GA-Band (Single-File oder Multi-File)"""
        import time
        start_time = time.time()
        
        ga_number = ga_folder.name.split('-')[0]  # z.B. "GA001"
        
        print(f"  {ga_number}...", end=' ', flush=True)
        
        # Prüfe ob Multi-File oder Single-File
        is_multi_file, book_files = self.find_book_files(ga_folder)
        
        if not book_files:
            print("[X] Keine Dateien gefunden")
            return None
        
        if is_multi_file:
            print(f"[MULTI-FILE: {len(book_files)} Kapitel]")
            return self.process_multi_file_book(ga_folder, ga_number, book_files, start_time)
        
        # Single-File-Verarbeitung (ursprünglicher Code)
        main_file = book_files[0]
        
        try:
            # Lese Datei
            read_start = time.time()
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            read_time = time.time() - read_start
            
            # 0. Konvertiere JPEG-Bilder zu PNG (überspringen für Performance)
            # converted_images = convert_jpeg_to_png_files(main_file)
            
            # 1. Rechtschreibkorrekturen (OPTIONAL - kann deaktiviert werden für Geschwindigkeit)
            if not self.skip_spelling:
                spelling_start = time.time()
                # OPTIMIERUNG: Überspringe Rechtschreibkorrekturen wenn Text sehr groß (>500KB)
                if len(content) < 500000:  # Nur bei kleineren Dateien
                    content = self.fix_spelling(content)
                spelling_time = time.time() - spelling_start
            else:
                spelling_time = 0
            
            # 1.5. Konvertiere JPEG-Platzhalter zu PNG
            content = fix_image_placeholders_in_content(content)
            
            # 2. Konvertiere Überschriften
            content = self.convert_headings(content)
            
            # 3. Extrahiere Überschriften (für TOC und Verknüpfung)
            headings = self.extract_headings(content)
            
            # 4. Korrigiere Links im Inhaltsverzeichnis
            content = self.fix_toc_links(content, headings)
            
            # 5. Konvertiere Fußnoten zu Markdown-Format
            content = self.convert_footnotes(content)
            
            # 6. Extrahiere Absätze (ohne Überschriften) - wie bei Vorträgen
            paragraphs = self.extract_paragraphs(content)
            
            # 6.5. Formatiere Paragraph-Content (Gedichte und durchgezogene Linien)
            for para in paragraphs:
                if para.get('content'):
                    para['content'] = self.format_paragraph_content(para['content'])
            
            # Prüfe ob Absätze Indizes haben
            has_paragraph_indices = len(paragraphs) > 0 and all(p.get('index', '').startswith('^') for p in paragraphs)
            
            if not has_paragraph_indices:
                print(f"[ÜBERSPRUNGEN] Keine Absatz-Indizes gefunden ({len(paragraphs)} Absätze ohne Indizes)")
                return None
            
            # 7. Verknüpfe Überschriften mit Absatz-Indizes
            linked_headings = self.link_headings_to_paragraphs(headings, paragraphs, content)
            
            # Debug: Prüfe ob Verknüpfung funktioniert hat
            if linked_headings:
                first_linked = linked_headings[0]
                print(f"    [DEBUG] Erste verknüpfte Überschrift: Index={first_linked.get('index')}, Text={first_linked.get('text')[:40]}")
                # Prüfe ob Index ein Absatz-Index ist (beginnt mit ^)
                if first_linked.get('index') and not first_linked.get('index').startswith('^'):
                    print(f"    [WARN] Überschrift hat keinen Absatz-Index! Index={first_linked.get('index')}")
                    # Wenn keine Absatz-Indizes vorhanden, überspringe Export
                    print(f"[ÜBERSPRUNGEN] Überschriften haben keine Absatz-Indizes")
                    return None
            
            # 8. Speichere Überschriften in summary-database.json
            self.save_headings_to_summary_db(ga_number, linked_headings)
            
            # WICHTIG: Verwende linked_headings für Book-Export (haben index statt id)
            # Konvertiere linked_headings zu Book-Format (mit id für Kompatibilität)
            headings_for_export = []
            for h in linked_headings:
                headings_for_export.append({
                    'id': h.get('index', ''),  # Verwende index als id für Kompatibilität
                    'text': h['text'],
                    'level': int(h['level'].replace('h', '')) if 'level' in h else 3
                })
            headings = headings_for_export  # Ersetze headings mit linked_headings
            
            # 9. Erstelle Content ohne Überschriften (nur Absätze)
            # Für Kompatibilität: Content bleibt vorhanden, aber wird später durch Absätze ersetzt
            content_without_headings = content
            # Entferne Überschriften aus Content für spätere Verwendung
            lines = content.split('\n')
            content_lines = []
            for line in lines:
                if not re.match(r'^#{3,4}\s+', line):
                    content_lines.append(line)
            content_without_headings = '\n'.join(content_lines)
            
            # 10. Extrahiere Metadaten aus Dateinamen
            filename = main_file.stem
            # Format: "GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897)"
            # Oder: "GA040a - Wahrspruchworte" (ohne Jahr)
            # WICHTIG: GA-Nummer mit optionalem Suffix unterstützen
            title_match = re.search(r'GA\d{2,3}[a-z]?\s*-\s*(.+?)\s*\((.+?)\)', filename)
            if title_match:
                title_text = title_match.group(1).strip()
                year_range = title_match.group(2).strip()
                # Füge Jahr zum Titel hinzu, falls vorhanden
                title = f"{title_text} ({year_range})"
            else:
                # Fallback: Nimm alles nach "GAXXX - " oder "GAXXXa - "
                title_match = re.search(r'GA\d{2,3}[a-z]?\s*-\s*(.+)', filename)
                if title_match:
                    title = title_match.group(1).strip()
                    year_range = ""
                else:
                    # Wenn kein " - " gefunden, entferne GA-Nummer vom Anfang
                    title_match = re.match(r'GA\d{2,3}[a-z]?\s*-\s*(.+)', filename)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        # Letzter Fallback: Entferne GA-Nummer vom Anfang
                        title = re.sub(r'^GA\d{2,3}[a-z]?\s*-\s*', '', filename).strip()
                    year_range = ""
            
            # Erstelle Book-Objekt
            # WICHTIG: paragraphs wird für neues Format verwendet, content bleibt für Kompatibilität
            book = {
                'ID': ga_number,
                'gaNumber': ga_number,
                'fileName': filename,
                'title': title,
                'yearRange': year_range,
                'content': content,  # Behalte für Kompatibilität
                'paragraphs': paragraphs,  # Neues Format: Absätze ohne Überschriften
                'headings': headings,  # Behalte für Kompatibilität (TOC)
                'wordCount': sum(len(p['content'].split()) for p in paragraphs),
                'charCount': sum(len(p['content']) for p in paragraphs)
            }
            
            total_time = time.time() - start_time
            print(f"[OK] ({len(headings)} Überschriften, {len(paragraphs)} Absätze, {book['wordCount']} Wörter, {total_time:.1f}s)")
            return book
            
        except Exception as e:
            print(f"[X] Fehler: {e}")
            return None
    
    def process_multi_file_book(self, ga_folder, ga_number, chapter_files, start_time):
        """Verarbeitet ein Multi-File-Buch (mehrere Kapitel-Dateien)"""
        import time
        
        all_paragraphs = []
        all_headings = []
        all_content_parts = []
        chapter_info = []
        
        for chapter_idx, chapter_file in enumerate(chapter_files, 1):
            chapter_name = chapter_file.stem
            print(f"    Kapitel {chapter_idx}/{len(chapter_files)}: {chapter_name[:50]}...")
            
            try:
                # Lese Kapitel-Datei
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extrahiere Kapiteltitel aus Dateinamen
                # Format: "GA001 (1.) ZUR EINFÜHRUNG.md"
                title_match = re.match(r'GA\d{2,3}[a-z]?\s*\(\d+\.\)\s+(.+)$', chapter_name)
                chapter_title = title_match.group(1).strip() if title_match else chapter_name
                
                # 1. Rechtschreibkorrekturen (optional)
                if not self.skip_spelling and len(content) < 500000:
                    content = self.fix_spelling(content)
                
                # 1.5. Konvertiere JPEG-Platzhalter zu PNG
                content = fix_image_placeholders_in_content(content)
                
                # 2. Konvertiere Überschriften
                content = self.convert_headings(content)
                
                # 3. Extrahiere Überschriften
                chapter_headings = self.extract_headings(content)
                
                # 4. Korrigiere Links im Inhaltsverzeichnis
                content = self.fix_toc_links(content, chapter_headings)
                
                # 5. Konvertiere Fußnoten
                content = self.convert_footnotes(content)
                
                # 6. Extrahiere Absätze
                chapter_paragraphs = self.extract_paragraphs(content)
                
                # 6.5. Formatiere Paragraph-Content
                for para in chapter_paragraphs:
                    if para.get('content'):
                        para['content'] = self.format_paragraph_content(para['content'])
                
                # Prüfe ob Absätze Indizes haben
                has_indices = len(chapter_paragraphs) > 0 and all(
                    p.get('index', '').startswith('^') for p in chapter_paragraphs
                )
                
                if not has_indices:
                    print(f"      [WARN] Kapitel {chapter_idx} hat keine Absatz-Indizes - übersprungen")
                    continue
                
                # 7. Verknüpfe Überschriften mit Absatz-Indizes
                linked_headings = self.link_headings_to_paragraphs(
                    chapter_headings, chapter_paragraphs, content
                )
                
                # Füge Kapitelüberschrift als H3 hinzu (wenn nicht schon vorhanden)
                if chapter_paragraphs and chapter_title:
                    first_para_index = chapter_paragraphs[0].get('index', '')
                    # Prüfe ob Kapitelüberschrift bereits in linked_headings
                    has_chapter_heading = any(
                        h.get('text', '').upper() == chapter_title.upper() 
                        for h in linked_headings
                    )
                    if not has_chapter_heading:
                        # Füge Kapitelüberschrift am Anfang ein
                        linked_headings.insert(0, {
                            'index': first_para_index,
                            'text': chapter_title,
                            'level': 'h3'
                        })
                
                # Sammle alle Daten
                all_paragraphs.extend(chapter_paragraphs)
                all_headings.extend(linked_headings)
                all_content_parts.append(content)
                
                chapter_info.append({
                    'number': chapter_idx,
                    'title': chapter_title,
                    'paragraphs': len(chapter_paragraphs),
                    'headings': len(linked_headings)
                })
                
                print(f"      [OK] {len(chapter_paragraphs)} Absätze, {len(linked_headings)} Überschriften")
                
            except Exception as e:
                print(f"      [X] Fehler: {e}")
                continue
        
        # Prüfe ob genug Kapitel verarbeitet wurden
        if not all_paragraphs:
            print(f"  [X] Keine gültigen Kapitel gefunden")
            return None
        
        # 8. Speichere alle Überschriften in summary-database.json
        self.save_headings_to_summary_db(ga_number, all_headings)
        
        # Konvertiere Headings zu Book-Format
        headings_for_export = []
        for h in all_headings:
            headings_for_export.append({
                'id': h.get('index', ''),
                'text': h['text'],
                'level': int(h['level'].replace('h', '')) if 'level' in h else 3
            })
        
        # Extrahiere Titel und Jahr aus dem Ordnernamen
        # Format: "GA001-Goethes Naturwissenschaftliche Schriften"
        folder_name = ga_folder.name
        title_match = re.match(r'GA\d{2,3}[a-z]?-(.+)$', folder_name)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = folder_name
        
        # Suche Jahr in der ersten Hauptdatei (falls vorhanden)
        year_range = ""
        main_file = self.find_book_file(ga_folder)
        if main_file:
            year_match = re.search(r'\((\d{4}(?:-\d{4})?)\)', main_file.name)
            if year_match:
                year_range = year_match.group(1)
        
        # Kombiniere alle Contents
        combined_content = '\n\n---\n\n'.join(all_content_parts)
        
        # Erstelle Book-Objekt
        book = {
            'ID': ga_number,
            'gaNumber': ga_number,
            'fileName': folder_name,
            'title': title,
            'yearRange': year_range,
            'content': combined_content,
            'paragraphs': all_paragraphs,
            'headings': headings_for_export,
            'chapters': chapter_info,  # Zusätzliche Info über Kapitel
            'wordCount': sum(len(p['content'].split()) for p in all_paragraphs),
            'charCount': sum(len(p['content']) for p in all_paragraphs)
        }
        
        total_time = time.time() - start_time
        print(f"  [OK] Multi-File: {len(chapter_info)} Kapitel, {len(headings_for_export)} Überschriften, {len(all_paragraphs)} Absätze, {book['wordCount']} Wörter, {total_time:.1f}s")
        return book
    
    def export_books(self, ga_numbers=None):
        """Exportiert Schriften als JSON"""
        print("\n" + "=" * 70)
        print("  EXPORT STEINER GA-SCHRIFTEN (GA001-GA046 + Multi-File-Bücher)")
        print("=" * 70 + "\n")
        
        # Bestimme zu exportierende GA-Bände
        # Ausnahmen: GA029-GA037, GA041b und GA046 sind Aufsatzbände (werden wie Vorträge exportiert)
        essay_bands = set(range(29, 38)) | {46}  # GA029-GA037 und GA046
        
        def is_essay_band(ga):
            """Prüft ob eine GA-Nummer ein Aufsatzband ist"""
            match = re.match(r'GA(\d{2,3})([a-z])?', ga.upper())
            if match:
                ga_num = int(match.group(1))
                ga_suffix = (match.group(2) or '').lower()
                return ga_num in essay_bands or (ga_num == 41 and ga_suffix == 'b')
            return False
        
        if ga_numbers:
            # Filtere Aufsatzbände aus der übergebenen Liste
            target_gas = [ga for ga in ga_numbers if not is_essay_band(ga)]
        else:
            # GA001 bis GA046, inklusive Varianten mit Suffix (z.B. GA040a, GA041a)
            target_gas = [f"GA{i:03d}" for i in range(1, 47) if i not in essay_bands]
            # Füge bekannte Varianten mit Suffix hinzu (außer GA041b = Aufsatzband)
            target_gas.extend(['GA040a', 'GA041a'])
            # HINWEIS: GA262 und GA263a werden jetzt als BRIEFE exportiert (in export-lectures.js)
        
        print(f"Suche nach {len(target_gas)} GA-Bänden...\n")
        
        # Durchsuche Steiner_GA Ordner
        ga_folders = []
        skip_books = []  # Liste leer - Bücher ohne Absatz-Indizes werden automatisch übersprungen
        
        for folder_name in sorted(os.listdir(self.steiner_ga_dir)):
            folder_path = Path(self.steiner_ga_dir) / folder_name
            
            if not folder_path.is_dir() or not folder_name.startswith('GA'):
                continue
            
            # Extrahiere vollständige GA-Nummer (mit optionalem Suffix)
            ga_match = re.match(r'GA(\d{3})([a-z])?', folder_name)
            if ga_match:
                ga_base = f"GA{ga_match.group(1)}"
                ga_suffix = ga_match.group(2) or ''
                ga_full = ga_base + ga_suffix
                
                # Prüfe ob vollständige GA-Nummer ODER Basis-GA-Nummer in target_gas
                if ga_full in target_gas or ga_base in target_gas:
                    # Überspringe Bücher in skip_books Liste (nur Basis-Nummer prüfen)
                    if ga_base in skip_books:
                        print(f"  {ga_full}... [ÜBERSPRUNGEN]")
                        continue
                    # Speichere vollständige GA-Nummer (mit Suffix)
                    ga_folders.append((ga_full, folder_path))
        
        if not ga_folders:
            print("[X] Keine GA-Ordner gefunden!")
            return False
        
        print(f"Gefunden: {len(ga_folders)} Ordner\n")
        print("Verarbeite Schriften:\n")
        
        # PERFORMANCE: Parallele Verarbeitung mit multiprocessing
        # OPTIMIERUNG: Deaktiviere Parallelisierung für bessere Kompatibilität
        # (kann wieder aktiviert werden wenn nötig)
        use_parallel = False  # MULTIPROCESSING_AVAILABLE and hasattr(self, 'parallel_workers') and self.parallel_workers > 1 and len(ga_folders) > 1
        
        if use_parallel:
            print(f"\nVerarbeite {len(ga_folders)} Bücher parallel ({self.parallel_workers} Prozesse)...\n")
            
            # Worker-Funktion für parallele Verarbeitung (außerhalb der Klasse für Pickling)
            def process_book_worker(args):
                ga_num, folder_path_str, spelling_settings_dict, initial_summary_db_dict = args
                try:
                    folder_path = Path(folder_path_str)
                    # Erstelle temporären Exporter für diesen Worker
                    worker_exporter = BooksExporter(parallel_workers=1)
                    worker_exporter.summary_db = dict(initial_summary_db_dict)
                    worker_exporter.spelling_settings = spelling_settings_dict
                    
                    book = worker_exporter.process_book(folder_path)
                    
                    # Gib Buch und aktualisierte summary_db zurück
                    updated_db_entry = None
                    if book and ga_num in worker_exporter.summary_db:
                        updated_db_entry = (ga_num, worker_exporter.summary_db[ga_num])
                    
                    return (book, updated_db_entry)
                except Exception as e:
                    print(f"\n  [FEHLER] {ga_num}: {e}")
                    return (None, None)
            
            # Bereite Argumente für Worker vor
            worker_args = [
                (ga_num, str(folder_path), self.spelling_settings, self.summary_db)
                for ga_num, folder_path in sorted(ga_folders)
            ]
            
            # Verarbeite parallel
            with Pool(processes=self.parallel_workers) as pool:
                results = pool.map(process_book_worker, worker_args)
            
            # Sammle erfolgreiche Ergebnisse und aktualisiere summary_db
            self.books = []
            for book, db_entry in results:
                if book:
                    self.books.append(book)
                if db_entry:
                    ga_num, db_data = db_entry
                    self.summary_db[ga_num] = db_data
                    self.summary_db_modified = True
            
        else:
            # Sequenzielle Verarbeitung (Fallback oder wenn parallel_workers=1)
            print(f"\nVerarbeite {len(ga_folders)} Bücher sequenziell...\n")
            for ga_num, folder_path in sorted(ga_folders):
                book = self.process_book(folder_path)
                if book:
                    self.books.append(book)
        
        if not self.books:
            print("\n[X] Keine Bücher gefunden!")
            return False
        
        print(f"\n[OK] {len(self.books)} Bücher verarbeitet\n")
        
        # PERFORMANCE: Speichere summary-database.json einmal am Ende (statt bei jedem Buch)
        print("Speichere summary-database.json mit allen Überschriften...")
        self.save_summary_db(force=True)
        
        # Erstelle JSON-Struktur
        output_data = {
            'metadata': {
                'exportDate': datetime.now().isoformat(),
                'totalBooks': len(self.books),
                'gaRange': f"{min(b['gaNumber'] for b in self.books)}-{max(b['gaNumber'] for b in self.books)}"
            },
            'books': self.books
        }
        
        # Speichere JSON (evtl. gesplittet)
        self.save_json(output_data)
        
        return True
    
    def save_json(self, data):
        """Speichert JSON in steiner-books/ Unterverzeichnis, splittet wenn > 10 MB"""
        # Erstelle JSON-String
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        size_mb = len(json_str.encode('utf-8')) / (1024 * 1024)
        
        print(f"Gesamtgröße: {size_mb:.2f} MB\n")
        
        # Stelle sicher, dass das steiner-books/ Verzeichnis existiert
        books_dir = Path(self.project_root) / 'steiner-books'
        books_dir.mkdir(exist_ok=True)
        
        if size_mb <= 10:
            # Einzelne Datei
            ga_range = data['metadata']['gaRange'].replace('GA', '').replace('-', '-')
            filename = f"steiner-books-{ga_range}.json"
            filepath = books_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            print(f"[OK] Gespeichert: steiner-books/{filename} ({size_mb:.2f} MB)")
        else:
            # Splitte in mehrere Dateien
            print(f"[!] Datei zu groß ({size_mb:.2f} MB), splitte in mehrere Dateien...\n")
            
            books = data['books']
            chunk_size = int(len(books) // ((size_mb // 10) + 1))
            if chunk_size < 1:
                chunk_size = 1
            
            part_num = 1
            for i in range(0, len(books), chunk_size):
                chunk_books = books[i:i+chunk_size]
                
                chunk_data = {
                    'metadata': {
                        **data['metadata'],
                        'part': part_num,
                        'totalParts': (len(books) // chunk_size) + 1
                    },
                    'books': chunk_books
                }
                
                chunk_json = json.dumps(chunk_data, ensure_ascii=False, indent=2)
                chunk_size_mb = len(chunk_json.encode('utf-8')) / (1024 * 1024)
                
                ga_range = f"{chunk_books[0]['gaNumber'].replace('GA', '')}-{chunk_books[-1]['gaNumber'].replace('GA', '')}"
                filename = f"steiner-books-{ga_range}-part{part_num:02d}.json"
                filepath = books_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(chunk_json)
                
                print(f"  [{part_num}] steiner-books/{filename}: {len(chunk_books)} Bücher ({chunk_size_mb:.2f} MB)")
                part_num += 1
            
            print(f"\n[OK] {part_num - 1} Dateien erstellt in steiner-books/")


def parse_arguments():
    """Parse Kommandozeilenargumente"""
    args = sys.argv[1:]
    
    ga_numbers = []
    for arg in args:
        if arg.startswith('--'):
            if arg == '--help' or arg == '-h':
                print(__doc__)
                sys.exit(0)
        else:
            # GA-Nummer (mit oder ohne GA-Präfix, Suffixe bleiben klein)
            arg_upper = arg.upper()
            if not arg_upper.startswith('GA'):
                # Extrahiere Suffix falls vorhanden (z.B. "40a" -> "a")
                suffix_match = re.search(r'(\d+)([a-z])?', arg, re.IGNORECASE)
                if suffix_match:
                    num_part = suffix_match.group(1)
                    suffix_part = suffix_match.group(2) or ''
                    ga_num = f"GA{num_part.zfill(3)}{suffix_part.lower()}"
                else:
                    ga_num = f"GA{arg.zfill(3)}"
            else:
                # GA-Präfix vorhanden, behalte Suffix in Original-Größe
                ga_match = re.match(r'GA(\d+)([a-z])?', arg, re.IGNORECASE)
                if ga_match:
                    num_part = ga_match.group(1)
                    suffix_part = ga_match.group(2) or ''
                    ga_num = f"GA{num_part.zfill(3)}{suffix_part.lower()}"
                else:
                    ga_num = arg_upper
            ga_numbers.append(ga_num)
    
    return ga_numbers if ga_numbers else None


def main():
    """Hauptfunktion"""
    ga_numbers = parse_arguments()
    
    # PERFORMANCE: Überspringe Rechtschreibkorrekturen für schnellere Verarbeitung
    # (kann später mit --spelling aktiviert werden)
    skip_spelling = '--spelling' not in sys.argv
    
    exporter = BooksExporter(parallel_workers=1, skip_spelling=skip_spelling)  # Parallelisierung deaktiviert für Windows-Kompatibilität
    
    # Prüfe, ob Steiner_GA Ordner existiert
    if not os.path.exists(exporter.steiner_ga_dir):
        print("\n" + "=" * 70)
        print("FEHLER: Steiner_GA Ordner nicht gefunden!")
        print("=" * 70)
        print(f"Erwartet: {exporter.steiner_ga_dir}")
        print("=" * 70 + "\n")
        sys.exit(1)
    
    # Führe Export aus
    success = exporter.export_books(ga_numbers)
    
    if success:
        print("\n" + "=" * 70)
        print("  [OK] EXPORT ERFOLGREICH!")
        print("=" * 70 + "\n")
    else:
        print("\n" + "=" * 70)
        print("  [X] EXPORT FEHLGESCHLAGEN!")
        print("=" * 70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

