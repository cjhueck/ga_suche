#!/usr/bin/env python3
"""
Extrahiert bibliographische Angaben aus einer Citavi-Projektdatei (.ctv6)
und erstellt eine JSON-Datei mit den Daten für alle GA-Bände.

Citavi-Dateien sind SQLite-Datenbanken. Dieses Skript liest die relevanten
Tabellen und extrahiert die bibliographischen Informationen.
"""

import sqlite3
import json
import re
import sys
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

def extract_ga_number(title: str) -> Optional[str]:
    """Extrahiert die GA-Nummer aus einem Titel (z.B. 'GA100' oder 'GA 100')."""
    if not title:
        return None
    
    # Suche nach GA gefolgt von Zahlen und optionalem Buchstaben
    match = re.search(r'GA\s*(\d{1,3}[a-z]?)', title, re.IGNORECASE)
    if match:
        ga_num = match.group(1)
        # Normalisiere auf 3-stellige Zahl mit optionalem Buchstaben
        if ga_num[0].isdigit():
            num_part = ga_num.rstrip('abcdefghijklmnopqrstuvwxyz')
            letter_part = ga_num[len(num_part):].lower()
            normalized = f"GA{num_part.zfill(3)}{letter_part}"
            return normalized
    
    # Falls kein "GA" gefunden, suche nach reinen Zahlen+Buchstaben-Kombinationen
    # (z.B. "070a" im Volume-Feld)
    match = re.search(r'^(\d{1,3}[a-z]?)$', str(title).strip(), re.IGNORECASE)
    if match:
        ga_num = match.group(1)
        if ga_num[0].isdigit():
            num_part = ga_num.rstrip('abcdefghijklmnopqrstuvwxyz')
            letter_part = ga_num[len(num_part):].lower()
            normalized = f"GA{num_part.zfill(3)}{letter_part}"
            return normalized
    
    return None

def get_citavi_tables(conn: sqlite3.Connection) -> List[str]:
    """Gibt eine Liste aller Tabellennamen in der Datenbank zurück."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def extract_bibliographic_data(citavi_path: str) -> Dict[str, Dict]:
    """
    Extrahiert bibliographische Daten aus einer Citavi-Datei.
    
    Returns:
        Dictionary mit GA-Nummern als Keys und bibliographischen Daten als Values
    """
    conn = sqlite3.connect(citavi_path)
    conn.row_factory = sqlite3.Row  # Ermöglicht Zugriff auf Spalten per Name
    
    bibliographic_data = {}
    
    try:
        # Zeige alle Tabellen
        tables = get_citavi_tables(conn)
        print(f"Gefundene Tabellen: {', '.join(tables)}")
        
        # Versuche verschiedene mögliche Tabellennamen
        possible_title_tables = ['Title', 'Titles', 'Reference', 'References', 'Item', 'Items']
        title_table = None
        
        for table_name in possible_title_tables:
            if table_name in tables:
                title_table = table_name
                break
        
        if not title_table:
            # Wenn keine Standard-Tabelle gefunden, verwende die erste Tabelle
            if tables:
                title_table = tables[0]
                print(f"Warnung: Verwende Tabelle '{title_table}' (keine Standard-Tabelle gefunden)")
            else:
                print("Fehler: Keine Tabellen in der Datenbank gefunden")
                return {}
        
        # Hole alle Spalten der Tabelle
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({title_table})")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\nSpalten in Tabelle '{title_table}': {', '.join(columns)}")
        
        # Versuche, relevante Spalten zu identifizieren
        title_col = None
        author_col = None
        year_col = None
        publisher_col = None
        place_col = None
        isbn_col = None
        pages_col = None
        
        for col in columns:
            col_lower = col.lower()
            if 'title' in col_lower or 'titel' in col_lower:
                title_col = col
            elif 'author' in col_lower or 'autor' in col_lower:
                author_col = col
            elif 'year' in col_lower or 'jahr' in col_lower or 'date' in col_lower:
                year_col = col
            elif 'publisher' in col_lower or 'verlag' in col_lower:
                publisher_col = col
            elif 'place' in col_lower or 'ort' in col_lower:
                place_col = col
            elif 'isbn' in col_lower:
                isbn_col = col
            elif 'page' in col_lower or 'seite' in col_lower:
                pages_col = col
        
        # SeriesTitles vorladen (für GA K-Reihen-Erkennung)
        series_lookup = {}
        if 'SeriesTitle' in tables:
            series_cursor = conn.cursor()
            series_cursor.execute("SELECT ID, Name FROM SeriesTitle")
            for sr in series_cursor.fetchall():
                series_lookup[sr['ID']] = sr['Name']
        
        # Lade alle Einträge
        cursor.execute(f"SELECT * FROM {title_table}")
        rows = cursor.fetchall()
        
        print(f"\nGefundene Einträge: {len(rows)}")
        
        # Verarbeite jeden Eintrag
        for row in rows:
            # Konvertiere Row zu Dictionary
            entry = dict(row)
            
            # Prüfe ob der Eintrag zu einer GA K-Reihe gehört
            series_id = entry.get('SeriesTitleID')
            series_name = series_lookup.get(series_id, '') if series_id else ''
            k_match = re.match(r'GA\s+K\s+(\d+)', series_name, re.IGNORECASE)
            
            ga_number = None
            title_value = None
            
            if k_match:
                # GA K-Reihe: z.B. SeriesTitle "GA K 58" + Volume "001" → "GAK58-001"
                k_number = k_match.group(1)
                volume = str(entry.get('Volume', '')).strip()
                if re.match(r'^\d{1,3}$', volume):
                    ga_number = f"GAK{k_number}-{volume.zfill(3)}"
                else:
                    ga_number = f"GAK{k_number}"
            else:
                # Reguläre GA-Nummer aus verschiedenen Feldern extrahieren
                fields_to_check = ['Title', 'ShortTitle', 'Number', 'Volume', 'TitleTagged', 'UniformTitle']
                
                for field in fields_to_check:
                    if field in entry and entry[field]:
                        field_value = str(entry[field])
                        extracted_ga = extract_ga_number(field_value)
                        if extracted_ga:
                            ga_number = extracted_ga
                            if field == 'Title' or not title_value:
                                title_value = field_value
                            break
                
                if not ga_number:
                    if 'Volume' in entry and entry['Volume']:
                        volume_value = str(entry['Volume']).strip()
                        extracted_ga = extract_ga_number(volume_value)
                        if extracted_ga:
                            ga_number = extracted_ga
                    
                    if not ga_number:
                        for col in columns:
                            if entry.get(col) and isinstance(entry[col], str):
                                field_value = str(entry[col])
                                if 'GA' in field_value.upper():
                                    extracted_ga = extract_ga_number(field_value)
                                    if extracted_ga:
                                        ga_number = extracted_ga
                                        title_value = field_value if not title_value else title_value
                                        break
            
            if not ga_number:
                continue
            
            # Bereinige Titel - verwende Title, ShortTitle oder UniformTitle
            clean_title = None
            if 'Title' in entry and entry['Title']:
                title_val = str(entry['Title'])
                if not (title_val.startswith('{') or title_val.startswith('[') or title_val.startswith('http')):
                    clean_title = title_val
            
            if not clean_title and 'ShortTitle' in entry and entry['ShortTitle']:
                short_title = str(entry['ShortTitle'])
                if not (short_title.startswith('{') or short_title.startswith('[') or short_title.startswith('http')):
                    clean_title = short_title
            
            if not clean_title and 'UniformTitle' in entry and entry['UniformTitle']:
                uniform_title = str(entry['UniformTitle'])
                if not (uniform_title.startswith('{') or uniform_title.startswith('[') or uniform_title.startswith('http')):
                    clean_title = uniform_title
            
            if not clean_title:
                clean_title = f"GA {ga_number.replace('GA', '')}"
            
            # Erstelle bibliographischen Eintrag
            bib_entry = {
                'gaNumber': ga_number,
                'title': clean_title,
            }
            
            # Hole Autoren aus ReferenceAuthor-Tabelle
            ref_id = entry.get('ID')
            if ref_id and 'ReferenceAuthor' in tables:
                try:
                    author_cursor = conn.cursor()
                    # Prüfe ob OrderNumber existiert
                    author_cursor.execute("PRAGMA table_info(ReferenceAuthor)")
                    author_cols = [col[1] for col in author_cursor.fetchall()]
                    order_by = "ORDER BY ra.OrderNumber" if "OrderNumber" in author_cols else ""
                    
                    author_cursor.execute(f"""
                        SELECT p.FirstName, p.LastName, p.MiddleName
                        FROM ReferenceAuthor ra
                        JOIN Person p ON ra.PersonID = p.ID
                        WHERE ra.ReferenceID = ?
                        {order_by}
                    """, (ref_id,))
                    authors = []
                    for author_row in author_cursor.fetchall():
                        author_parts = []
                        if author_row[0]:  # FirstName
                            author_parts.append(str(author_row[0]))
                        if author_row[2]:  # MiddleName
                            author_parts.append(str(author_row[2]))
                        if author_row[1]:  # LastName
                            author_parts.append(str(author_row[1]))
                        if author_parts:
                            authors.append(' '.join(author_parts))
                    if authors:
                        bib_entry['author'] = ', '.join(authors)
                except Exception as e:
                    print(f"Warnung: Konnte Autoren nicht laden für {ga_number}: {e}")
            
            # Hole Verlage aus ReferencePublisher-Tabelle
            if ref_id and 'ReferencePublisher' in tables:
                try:
                    publisher_cursor = conn.cursor()
                    # Prüfe ob OrderNumber existiert
                    publisher_cursor.execute("PRAGMA table_info(ReferencePublisher)")
                    publisher_cols = [col[1] for col in publisher_cursor.fetchall()]
                    order_by = "ORDER BY rp.OrderNumber" if "OrderNumber" in publisher_cols else ""
                    
                    publisher_cursor.execute(f"""
                        SELECT p.Name
                        FROM ReferencePublisher rp
                        JOIN Publisher p ON rp.PublisherID = p.ID
                        WHERE rp.ReferenceID = ?
                        {order_by}
                    """, (ref_id,))
                    publishers = [str(row[0]) for row in publisher_cursor.fetchall() if row[0]]
                    if publishers:
                        bib_entry['publisher'] = ', '.join(publishers)
                except Exception as e:
                    print(f"Warnung: Konnte Verlage nicht laden für {ga_number}: {e}")
            
            # Füge weitere Felder hinzu, falls vorhanden
            if 'Year' in entry and entry['Year']:
                bib_entry['year'] = str(entry['Year'])
            if 'PlaceOfPublication' in entry and entry['PlaceOfPublication']:
                bib_entry['place'] = str(entry['PlaceOfPublication'])
            if 'ISBN' in entry and entry['ISBN']:
                bib_entry['isbn'] = str(entry['ISBN'])
            if 'PageRange' in entry and entry['PageRange']:
                bib_entry['pages'] = str(entry['PageRange'])
            elif 'PageCount' in entry and entry['PageCount']:
                page_raw = str(entry['PageCount'])
                # Citavi speichert PageCount manchmal als XML: <c>238</c>\n<in>true</in>...
                pc_match = re.search(r'<c>(\d+)</c>', page_raw)
                if pc_match:
                    bib_entry['pages'] = pc_match.group(1)
                else:
                    bib_entry['pages'] = page_raw
            if 'Edition' in entry and entry['Edition']:
                bib_entry['edition'] = str(entry['Edition'])
            if 'Volume' in entry and entry['Volume']:
                bib_entry['volume'] = str(entry['Volume'])
            if 'Subtitle' in entry and entry['Subtitle']:
                bib_entry['subtitle'] = str(entry['Subtitle'])
            if 'TitleSupplement' in entry and entry['TitleSupplement']:
                bib_entry['titleSupplement'] = str(entry['TitleSupplement'])
            if 'OriginalPublication' in entry and entry['OriginalPublication']:
                bib_entry['originalPublication'] = str(entry['OriginalPublication'])
            
            # Hole Herausgeber aus ReferenceEditor-Tabelle
            if ref_id and 'ReferenceEditor' in tables:
                try:
                    editor_cursor = conn.cursor()
                    editor_cursor.execute("PRAGMA table_info(ReferenceEditor)")
                    editor_cols = [col[1] for col in editor_cursor.fetchall()]
                    order_by = "ORDER BY re.OrderNumber" if "OrderNumber" in editor_cols else ""
                    
                    editor_cursor.execute(f"""
                        SELECT p.FirstName, p.LastName, p.MiddleName
                        FROM ReferenceEditor re
                        JOIN Person p ON re.PersonID = p.ID
                        WHERE re.ReferenceID = ?
                        {order_by}
                    """, (ref_id,))
                    editors = []
                    for editor_row in editor_cursor.fetchall():
                        editor_parts = []
                        if editor_row[0]:  # FirstName
                            editor_parts.append(str(editor_row[0]))
                        if editor_row[2]:  # MiddleName
                            editor_parts.append(str(editor_row[2]))
                        if editor_row[1]:  # LastName
                            editor_parts.append(str(editor_row[1]))
                        if editor_parts:
                            editors.append(' '.join(editor_parts))
                    if editors:
                        bib_entry['editor'] = ', '.join(editors)
                except Exception as e:
                    print(f"Warnung: Konnte Herausgeber nicht laden für {ga_number}: {e}")
            
            # Speichere Eintrag (überschreibe bei Duplikaten)
            bibliographic_data[ga_number] = bib_entry
        
        print(f"\nExtrahiert: {len(bibliographic_data)} GA-Bände")
        
    except Exception as e:
        print(f"Fehler beim Lesen der Datenbank: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    return bibliographic_data

def find_ctv6_in_archive(archive_path: str) -> str:
    """
    Entpackt eine .ctv6archive-Datei (ZIP) in ein temp-Verzeichnis
    und gibt den Pfad zur enthaltenen .ctv6-Datei zurück.
    """
    tmp_dir = tempfile.mkdtemp(prefix="citavi_extract_")
    
    with zipfile.ZipFile(archive_path, 'r') as zf:
        ctv6_files = [n for n in zf.namelist() if n.endswith('.ctv6')]
        if not ctv6_files:
            raise FileNotFoundError(f"Keine .ctv6-Datei im Archiv gefunden. Inhalt: {zf.namelist()}")
        zf.extract(ctv6_files[0], tmp_dir)
        return str(Path(tmp_dir) / ctv6_files[0])


def main():
    citavi_archive = r"C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Backup\Rudolf Steiner Gesamtausgabe.ctv6archive"
    output_path = "ga-bibliography.json"
    
    if not Path(citavi_archive).exists():
        print(f"Fehler: Citavi-Archiv nicht gefunden: {citavi_archive}")
        sys.exit(1)
    
    print(f"Entpacke Archiv: {citavi_archive}")
    citavi_path = find_ctv6_in_archive(citavi_archive)
    print(f"Entpackt nach: {citavi_path}")
    
    try:
        print(f"Lese Citavi-Datei: {citavi_path}")
        bibliographic_data = extract_bibliographic_data(citavi_path)
    finally:
        import shutil
        tmp_dir = str(Path(citavi_path).parent)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"Temporäres Verzeichnis aufgeräumt: {tmp_dir}")
    
    if not bibliographic_data:
        print("Warnung: Keine bibliographischen Daten gefunden!")
        sys.exit(1)
    
    # Sortiere: reguläre GA zuerst (nach Nummer), dann GA K-Reihen
    def sort_key(item):
        key = item[0]
        is_k = key.startswith('GAK')
        nums = re.findall(r'\d+', key)
        primary = int(nums[0]) if nums else 999
        secondary = int(nums[1]) if len(nums) > 1 else 0
        return (is_k, primary, secondary, key)
    
    sorted_data = dict(sorted(bibliographic_data.items(), key=sort_key))
    
    # Speichere als JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nBibliographische Daten gespeichert in: {output_path}")
    print(f"Anzahl GA-Bände: {len(sorted_data)}")
    
    # Zeige erste paar Einträge als Beispiel
    print("\nBeispiel-Einträge:")
    for i, (ga_num, data) in enumerate(list(sorted_data.items())[:3]):
        print(f"\n{ga_num}:")
        for key, value in data.items():
            if key != 'additional':
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()

