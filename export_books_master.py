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


class BooksExporter:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.steiner_ga_dir = os.path.join(self.project_root, "Steiner_GA")
        self.books = []
        self.spelling_settings = self.load_spelling_settings()
    
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
        
    def find_book_file(self, ga_folder):
        """Findet die Haupt-Markdown-Datei eines GA-Bandes"""
        # Suche nach Dateien im Format: "GAXXX - Titel (Jahr).md"
        md_files = list(ga_folder.glob("GA*.md"))
        
        # Filtere Backup-Dateien und Vortragsdateien aus
        main_files = []
        for md_file in md_files:
            name = md_file.name
            # Überspringe Backup-Dateien
            if name.endswith('.backup'):
                continue
            # Überspringe Vortragsdateien (Format: "GAXXX (N.) Titel, Ort, Datum.md")
            if re.match(r'GA\d{3}\s*\([0-9]+\.\)', name):
                continue
            # Hauptdatei sollte Format haben: "GAXXX - Titel (Jahr).md"
            if re.match(r'GA\d{3}\s*-\s*.+\(.+\)\.md', name):
                main_files.append(md_file)
        
        if main_files:
            # Wenn mehrere gefunden, nimm die erste (sollte nur eine sein)
            return main_files[0]
        return None
    
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
            result_lines = []
            for line in lines:
                # Prüfe auf Fußnoten-Definitionen [^n]: Text
                match = re.match(r'^(\[\^\d+\]:\s*)(.+)$', line)
                if match:
                    prefix = match.group(1)
                    fn_text = match.group(2).strip()
                    # Entferne trailing Backlinks
                    fn_text = re.sub(r'\s*[↩↩︎]\s*$', '', fn_text)
                    result_lines.append(prefix + fn_text)
                else:
                    result_lines.append(line)
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
        # Basis-Rechtschreibkorrekturen aus export_master.py
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
    
    def process_book(self, ga_folder):
        """Verarbeitet einen GA-Band"""
        ga_number = ga_folder.name.split('-')[0]  # z.B. "GA001"
        
        print(f"  {ga_number}...", end=' ', flush=True)
        
        # Finde Hauptdatei
        main_file = self.find_book_file(ga_folder)
        if not main_file:
            print("[X] Hauptdatei nicht gefunden")
            return None
        
        try:
            # Lese Datei
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Rechtschreibkorrekturen
            content = self.fix_spelling(content)
            
            # 2. Konvertiere Überschriften
            content = self.convert_headings(content)
            
            # 3. Extrahiere Überschriften
            headings = self.extract_headings(content)
            
            # 4. Korrigiere Links im Inhaltsverzeichnis
            content = self.fix_toc_links(content, headings)
            
            # 5. Konvertiere Fußnoten zu Markdown-Format
            content = self.convert_footnotes(content)
            
            # 6. Extrahiere Metadaten aus Dateinamen
            filename = main_file.stem
            # Format: "GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897)"
            title_match = re.search(r'GA\d{3}\s*-\s*(.+?)\s*\((.+?)\)', filename)
            if title_match:
                title_text = title_match.group(1).strip()
                year_range = title_match.group(2).strip()
                # Füge Jahr zum Titel hinzu, falls vorhanden
                title = f"{title_text} ({year_range})"
            else:
                # Fallback: Nimm alles nach "GAXXX - "
                title_match = re.search(r'GA\d{3}\s*-\s*(.+)', filename)
                if title_match:
                    title = title_match.group(1).strip()
                    year_range = ""
                else:
                    title = filename
                    year_range = ""
            
            # Erstelle Book-Objekt
            book = {
                'ID': ga_number,
                'gaNumber': ga_number,
                'fileName': filename,
                'title': title,
                'yearRange': year_range,
                'content': content,
                'headings': headings,
                'wordCount': len(content.split()),
                'charCount': len(content)
            }
            
            print(f"[OK] ({len(headings)} Überschriften, {book['wordCount']} Wörter)")
            return book
            
        except Exception as e:
            print(f"[X] Fehler: {e}")
            return None
    
    def export_books(self, ga_numbers=None):
        """Exportiert Schriften als JSON"""
        print("\n" + "=" * 70)
        print("  EXPORT STEINER GA-SCHRIFTEN (GA001-GA046)")
        print("=" * 70 + "\n")
        
        # Bestimme zu exportierende GA-Bände
        if ga_numbers:
            target_gas = ga_numbers
        else:
            # GA001 bis GA046
            target_gas = [f"GA{i:03d}" for i in range(1, 47)]
        
        print(f"Suche nach {len(target_gas)} GA-Bänden...\n")
        
        # Durchsuche Steiner_GA Ordner
        ga_folders = []
        for folder_name in sorted(os.listdir(self.steiner_ga_dir)):
            folder_path = Path(self.steiner_ga_dir) / folder_name
            
            if not folder_path.is_dir() or not folder_name.startswith('GA'):
                continue
            
            # Prüfe ob GA-Nummer in target_gas
            ga_match = re.match(r'GA(\d{3})[a-z]?', folder_name)
            if ga_match:
                ga_num = f"GA{ga_match.group(1)}"
                if ga_num in target_gas:
                    ga_folders.append((ga_num, folder_path))
        
        if not ga_folders:
            print("[X] Keine GA-Ordner gefunden!")
            return False
        
        print(f"Gefunden: {len(ga_folders)} Ordner\n")
        print("Verarbeite Schriften:\n")
        
        # Verarbeite jeden GA-Band
        for ga_num, folder_path in sorted(ga_folders):
            book = self.process_book(folder_path)
            if book:
                self.books.append(book)
        
        if not self.books:
            print("\n[X] Keine Bücher gefunden!")
            return False
        
        print(f"\n[OK] {len(self.books)} Bücher verarbeitet\n")
        
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
        """Speichert JSON, splittet wenn > 10 MB"""
        # Erstelle JSON-String
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        size_mb = len(json_str.encode('utf-8')) / (1024 * 1024)
        
        print(f"Gesamtgröße: {size_mb:.2f} MB\n")
        
        if size_mb <= 10:
            # Einzelne Datei
            ga_range = data['metadata']['gaRange'].replace('GA', '').replace('-', '-')
            filename = f"steiner-books-{ga_range}.json"
            filepath = Path(self.project_root) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            print(f"[OK] Gespeichert: {filename} ({size_mb:.2f} MB)")
        else:
            # Splitte in mehrere Dateien
            print(f"[!] Datei zu groß ({size_mb:.2f} MB), splitte in mehrere Dateien...\n")
            
            books = data['books']
            chunk_size = len(books) // ((size_mb // 10) + 1)
            
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
                filepath = Path(self.project_root) / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(chunk_json)
                
                print(f"  [{part_num}] {filename}: {len(chunk_books)} Bücher ({chunk_size_mb:.2f} MB)")
                part_num += 1
            
            print(f"\n[OK] {part_num - 1} Dateien erstellt")


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
            # GA-Nummer (mit oder ohne GA-Präfix)
            ga_num = arg.upper()
            if not ga_num.startswith('GA'):
                ga_num = f"GA{ga_num.zfill(3)}"
            ga_numbers.append(ga_num)
    
    return ga_numbers if ga_numbers else None


def main():
    """Hauptfunktion"""
    ga_numbers = parse_arguments()
    
    exporter = BooksExporter()
    
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

