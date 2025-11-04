"""
Script zum Herunterladen deutscher Vortragstexte von rsarchive.org
Download German lecture texts from rsarchive.org as markdown files
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Zielverzeichnis für Downloads  
# WICHTIG: Downloads gehen direkt in lectures Verzeichnis
BASE_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\lectures")

def get_lecture_links(ga_identifier):
    """
    Hole alle Vortragslinks für einen GA-Band in EDITORISCHER Reihenfolge
    Liest IMMER zuerst die Tabelle auf rsarchive.org und verwendet die "No." Spalte
    für die Reihenfolge. Entfernt automatisch Duplikate (mehrere Buchtitel pro Vortrag).
    
    ga_identifier kann sein: "121", "332a", "266/I" etc.
    """
    # Konvertiere / zu nichts für URL (GA266/I -> GA266I)
    ga_url = str(ga_identifier).replace('/', '')
    base_url = f"https://rsarchive.org/Lectures/GA{ga_url}/"
    
    try:
        response = requests.get(base_url, timeout=15)
        if response.status_code != 200:
            print(f"✗ Fehler beim Abrufen der GA{ga_identifier} Indexseite")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NEUE METHODE: Parse die Tabelle, um editorische Reihenfolge zu erhalten
        lecture_data = []  # Liste von (nummer, url, ort_aus_tabelle) Tupeln
        
        # Finde die richtige Tabelle mit den Vorträgen
        # Suche nach Tabelle die "Lecture Title" oder "No." im Header hat
        table = None
        for tbl in soup.find_all('table'):
            header_text = tbl.get_text()
            if 'Lecture Title' in header_text or ('No.' in header_text and 'Date' in header_text):
                table = tbl
                break
        
        if table:
            # SPEZIAL: Diese Tabelle hat ungültiges HTML - <td> direkt im <table>, KEIN <tr>!
            # Parse alle <td> Elemente direkt
            all_tds = table.find_all('td')
            
            # Track welche Nummern wir schon gesehen haben (für Duplikate)
            seen_numbers = set()
            
            # Gruppiere in 5er-Gruppen (Nr., Title, Book, Date, City)
            for i in range(0, len(all_tds), 5):
                if i + 1 >= len(all_tds):  # Brauchen mindestens 2 Spalten
                    break
                
                # Spalte 0: Nummer
                number_td = all_tds[i]
                number_text = number_td.get_text(strip=True)
                try:
                    lecture_number = int(number_text.rstrip('.'))
                except ValueError:
                    continue
                
                # WICHTIG: Bei gleicher Nummer nur ersten Eintrag nehmen!
                # (Tabelle hat oft mehrere Buchtitel für denselben Vortrag)
                if lecture_number in seen_numbers:
                    continue  # Überspringe Duplikate
                seen_numbers.add(lecture_number)
                
                # Spalte 1: Lecture Title mit Link
                title_td = all_tds[i + 1]
                link = title_td.find('a', href=True)
                if link:
                    href = link['href']
                    # Konvertiere zu absoluter URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://rsarchive.org{href}"
                    else:
                        full_url = f"{base_url}{href}"
                    
                    # Filtere nur .html Dateien (nicht /index.php)
                    filename = href.split('/')[-1]
                    if filename.endswith('.html'):
                        lecture_data.append((lecture_number, full_url))
        
        # FALLBACK: Wenn keine Tabelle gefunden, verwende alte Methode (mit Warnung!)
        if not lecture_data:
            print(f"\n⚠️  WARNUNG: Keine Tabelle mit editorischer Reihenfolge gefunden!")
            print(f"   Verwende Fallback-Methode (sucht alle HTML-Links).")
            print(f"   Die Reihenfolge könnte falsch sein!\n")
            
            lecture_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                filename = href.split('/')[-1]
                
                is_lecture = re.match(r'\d{8}[aped]\d{2}\.html', filename)
                is_preface = 'preface' in filename.lower() and filename.endswith('.html')
                is_preliminary = 'preliminary' in filename.lower() or '0816' in filename
                
                if is_lecture or is_preface or is_preliminary:
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://rsarchive.org{href}"
                    else:
                        full_url = f"{base_url}{href}"
                    
                    lecture_links.append(full_url)
            
            lecture_links = sorted(list(set(lecture_links)))
            return lecture_links
        
        # Sortiere nach editorischer Nummer
        lecture_data.sort(key=lambda x: x[0])
        
        # Erfolgsmeldung
        print(f"\n✓ Tabelle erfolgreich gelesen: {len(lecture_data)} Vorträge in editorischer Reihenfolge")
        print(f"  (Duplikate wurden automatisch entfernt)\n")
        
        # Extrahiere nur die URLs
        lecture_links = [url for _, url in lecture_data]
        
        return lecture_links
        
    except Exception as e:
        print(f"✗ Fehler: {e}")
        return []

def extract_german_text_with_images(url, ga_identifier):
    """
    Extrahiere den deutschen Text von einer Vortragsseite MIT Bild-Referenzen
    ga_identifier: z.B. "121", "332a", "266/I"
    """
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return None, []
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Suche nach deutschem Text in verschiedenen Formaten
        # Format 1: <div id="original"> (älteres Format)
        german_div = soup.find('div', id='original')
        
        # Format 2: <div class="German"> (neueres Format, z.B. SOL2024)
        if not german_div:
            german_div = soup.find('div', class_='German')
        
        if german_div:
            # Entferne Fußnoten und andere störende Elemente (aber nicht img!)
            for unwanted in german_div.find_all(['script', 'style', 'sup']):
                unwanted.decompose()
            
            # Extrahiere Absätze UND Bilder in der richtigen Reihenfolge
            content_parts = []
            image_urls = []  # Liste der gefundenen Bild-URLs
            
            # ÜBERSPRINGE h3 Titel - fangen direkt mit Text an
            
            # Iteriere durch alle direkten Kinder (p, img, etc.)
            for element in german_div.children:
                if not element.name:  # Skip text nodes
                    continue
                
                # Überspringe h3 Überschriften
                if element.name == 'h3':
                    continue
                
                if element.name == 'p':
                    # Verwende get_text() mit separator='\n' für Listen
                    text = element.get_text(separator='\n', strip=False)
                    text = text.strip()
                    if text:
                        content_parts.append(text)
                
                elif element.name == 'img':
                    # Bild gefunden!
                    img_src = element.get('src', '')
                    if img_src:
                        # Extrahiere Dateinamen (z.B. "images/121-01.webp" -> "121-01.webp")
                        img_filename = img_src.split('/')[-1]
                        
                        # Füge Markdown-Bild-Referenz ein
                        img_alt = element.get('alt', f'Abbildung {img_filename}')
                        content_parts.append(f"\n![{img_alt}](assets/{img_filename})\n")
                        
                        # Merke Bild-URL für Download
                        # Konvertiere zu absoluter URL
                        if img_src.startswith('http'):
                            full_img_url = img_src
                        else:
                            # Relative URL - baue absolute
                            base_url = '/'.join(url.split('/')[:-1]) + '/'
                            full_img_url = base_url + img_src
                        
                        image_urls.append((img_filename, full_img_url))
            
            german_text = '\n\n'.join(content_parts)
            
            return german_text if german_text else None, image_urls
        
        # Methode 2: Fallback - suche nach id="german" oder class="german"
        german_div = soup.find(id=re.compile(r'german', re.I))
        if not german_div:
            german_div = soup.find(class_=re.compile(r'german', re.I))
        
        if german_div:
            paragraphs = []
            for p in german_div.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            return '\n\n'.join(paragraphs) if paragraphs else None, []
        
        return None, []
        
    except Exception as e:
        print(f"  ✗ Fehler beim Extrahieren: {e}")
        return None, []

def download_images(image_list, images_dir):
    """
    Lade Bilder herunter in das images Verzeichnis
    """
    if not image_list:
        return 0
    
    images_dir.mkdir(exist_ok=True)
    downloaded = 0
    
    for img_filename, img_url in image_list:
        img_path = images_dir / img_filename
        
        # Überspringe bereits existierende Bilder
        if img_path.exists():
            continue
        
        try:
            response = requests.get(img_url, timeout=15)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
        except:
            pass
    
    return downloaded

def normalize_german_title(title):
    """
    Konvertiere Titel zu GROSSBUCHSTABEN für Dateinamen
    """
    # Titel zu Großbuchstaben konvertieren
    return title.upper()

def translate_city_name(city_en):
    """
    Übersetze englische zu deutschen Städtenamen
    Deutsche Umlaute (ä, ö, ü, ß) bleiben erhalten
    Nur französische/andere Akzente (â, ê, etc.) werden entfernt
    """
    city_translations = {
        'zurich': 'Zürich',
        'munich': 'München',
        'cologne': 'Köln',
        'nuremberg': 'Nürnberg',
        'vienna': 'Wien',
        'basle': 'Basel',
        'basel': 'Basel',
        'berne': 'Bern',
        'bern': 'Bern',
        'geneva': 'Genf',
        'the hague': 'Den Haag',
        'hague': 'Den Haag',
        'copenhagen': 'Kopenhagen',
        'prague': 'Prag',
        'st. petersburg': 'St. Petersburg',
        'neuchâtel': 'Neuchatel',
        'neuchatel': 'Neuchatel',
        'christiania': 'Christiania',  # Alter Name für Oslo
        'oslo': 'Oslo',
        'milan': 'Mailand',
        'florence': 'Florenz',
        'rome': 'Rom',
        'venice': 'Venedig',
        'stuttgart': 'Stuttgart',
        'hamburg': 'Hamburg',
        'berlin': 'Berlin',
        'leipzig': 'Leipzig',
        'dresden': 'Dresden',
        'hannover': 'Hannover',
        'hanover': 'Hannover',
        'frankfurt': 'Frankfurt',
        'dusseldorf': 'Düsseldorf',
        'düsseldorf': 'Düsseldorf',
        'kassel': 'Kassel',
        'cassel': 'Kassel',  # Alte Schreibweise
        'bremen': 'Bremen',
        'elberfeld': 'Elberfeld',
        'linz': 'Linz',
        'strasbourg': 'Straßburg',
        'strassburg': 'Straßburg',
        'st. gallen': 'St. Gallen',
    }
    
    city_lower = city_en.lower().strip()
    translated = city_translations.get(city_lower, city_en)
    
    # Nur NICHT-deutsche Akzente entfernen (â, ê, î, ô, û, à, è, ù)
    # Deutsche Umlaute (ä, ö, ü, Ä, Ö, Ü, ß) behalten!
    result = translated
    # Ersetze nur spezifische französische Akzente
    replacements = {
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'à': 'a', 'è': 'e', 'ù': 'u',
        'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
        'À': 'A', 'È': 'E', 'Ù': 'U',
    }
    
    for accent, replacement in replacements.items():
        result = result.replace(accent, replacement)
    
    return result

def extract_lecture_metadata(url, soup=None):
    """
    Extrahiere Metadaten aus URL und Seite (Nummer, Titel, Ort, Datum)
    """
    try:
        if not soup:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return None
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extrahiere DEUTSCHEN Titel aus dem ersten h3 im div id="original" oder class="German"
        german_div = soup.find('div', id='original')
        if not german_div:
            german_div = soup.find('div', class_='German')
        
        title = "Vortrag"
        
        lecture_number_from_title = None
        
        if german_div:
            first_h3 = german_div.find('h3')
            if first_h3:
                title_raw = first_h3.get_text().strip()
                
                # Extrahiere Nummer aus Titel (römisch oder arabisch)
                # Muster: "I.", "II.", "VII.", "1.", "2.", etc.
                num_match = re.match(r'^([IVXLCDM]+|[\d]+)\.', title_raw)
                if num_match:
                    num_str = num_match.group(1)
                    
                    # Konvertiere römisch zu arabisch
                    if num_str.isdigit():
                        lecture_number_from_title = int(num_str)
                    else:
                        # Römische Zahlen konvertieren
                        roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                        result = 0
                        prev_value = 0
                        for char in reversed(num_str):
                            value = roman_values.get(char, 0)
                            if value < prev_value:
                                result -= value
                            else:
                                result += value
                            prev_value = value
                        lecture_number_from_title = result
                    
                    # Entferne Nummer aus Titel für Dateinamen
                    title_raw = re.sub(r'^[IVXLCDM]+\.\s*', '', title_raw)
                    title_raw = re.sub(r'^\d+\.\s*', '', title_raw)
                
                # Verwende den Titel direkt (in Großbuchstaben)
                if title_raw and title_raw.lower() not in ['vortrag', 'lecture']:
                    title = normalize_german_title(title_raw)
        
        # Extrahiere Datum und Ort aus dem gesamten Dokument
        # Format: "31 January 1915, Zurich"
        page_text = soup.get_text()
        
        # Suche nach Datum, Ort Muster
        # Erweitert um französische Sonderzeichen (à, â, è, é, ê, ë, ï, ô, ù, û, ç)
        date_location_match = re.search(
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}),?\s+([A-Z][a-zäöüßàâèéêëïôùûç\-\s]+?)(?:\n|$|<|\s{2,})',
            page_text
        )
        
        # Konvertiere englische Monatsnamen zu deutschen
        month_translation = {
            'january': 'Januar', 'february': 'Februar', 'march': 'März',
            'april': 'April', 'may': 'Mai', 'june': 'Juni',
            'july': 'Juli', 'august': 'August', 'september': 'September',
            'october': 'Oktober', 'november': 'November', 'december': 'Dezember'
        }
        
        date_str = ""
        location = "Unbekannter Ort"
        
        if date_location_match:
            day = date_location_match.group(1)
            month = date_location_match.group(2).lower()
            year = date_location_match.group(3)
            location_en = date_location_match.group(4).strip()
            
            month_de = month_translation.get(month, month.capitalize())
            date_str = f"{day}. {month_de} {year}"
            
            # Übersetze Städtenamen
            location = translate_city_name(location_en)
        
        # Extrahiere Vortragsnummer aus Titel oder URL
        lecture_num = "1"
        title_num_match = re.match(r'^(\d+)\.', title)
        if title_num_match:
            lecture_num = title_num_match.group(1)
            title = re.sub(r'^\d+\.\s*', '', title).strip()
        
        return {
            'number': str(lecture_number_from_title) if lecture_number_from_title else lecture_num,
            'title': title,
            'location': location,
            'date': date_str,
            'url': url,
            'number_from_title': lecture_number_from_title  # Für spätere Verwendung
        }
        
    except Exception as e:
        print(f"  ✗ Fehler bei Metadaten-Extraktion: {e}")
        return None

def create_markdown_file(ga_identifier, metadata, german_text, output_dir):
    """
    Erstelle eine Markdown-Datei mit dem gewünschten Format
    Format: GAXXX (N.) TITEL, Ort, Datum.md
    """
    if not metadata or not german_text:
        return False
    
    # Erstelle Dateinamen: GAXXX (N.) TITEL, Ort, Datum
    # Bereinige den Titel für Dateinamen (entferne ungültige Zeichen)
    # WICHTIG: Titel NICHT kürzen!
    title_clean = re.sub(r'[<>:"/\\|?*]', '', metadata['title'])
    
    # Bereinige Ort und Datum für Dateinamen (entferne französische Akzente)
    location_clean = metadata['location']
    # Ersetze französische Akzente (â, ê, î, ô, û, à, è, ù, é)
    accent_replacements = {
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'à': 'a', 'è': 'e', 'ù': 'u', 'é': 'e',
        'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
        'À': 'A', 'È': 'E', 'Ù': 'U', 'É': 'E',
    }
    for accent, replacement in accent_replacements.items():
        location_clean = location_clean.replace(accent, replacement)
    
    # Format: "Ort, Datum" z.B. "Zürich, 31. Januar 1915"
    location_date = f"{location_clean}, {metadata['date']}"
    
    # Verwende ga_identifier im Dateinamen (z.B. GA332a, GA266_I)
    ga_filename = str(ga_identifier).replace('/', '_')
    filename = f"GA{ga_filename} ({metadata['number']}.) {title_clean}, {location_date}.md"
    filepath = output_dir / filename
    
    # Erstelle Markdown-Inhalt - DIREKT mit Text beginnen (kein Header!)
    markdown_content = german_text
    
    try:
        # Wichtig: UTF-8 BOM für Windows-Kompatibilität
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(markdown_content)
        return True
    except Exception as e:
        print(f"  ✗ Fehler beim Speichern: {e}")
        return False

def download_ga_lectures(ga_identifier):
    """
    Lade alle Vorträge eines GA-Bandes herunter
    ga_identifier kann sein: "121", "332a", "266/I" etc.
    """
    print(f"\n{'='*70}")
    print(f"Download deutscher Vortragstexte für GA{ga_identifier}")
    print(f"{'='*70}\n")
    
    # WICHTIG: Für Obsidian brauchen wir Ordner im Format: GAXXX-Voller Titel
    # Prüfe ob Ordner bereits existiert
    ga_number = str(ga_identifier).replace('/', '')
    
    # Suche existierenden Ordner
    existing_folder = None
    for folder in BASE_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith(f"GA{ga_number}-"):
            existing_folder = folder
            break
    
    if existing_folder:
        output_dir = existing_folder
        print(f"✓ Verwende existierenden Ordner: {output_dir.name}\n")
    else:
        # Erstelle neuen Ordner - Titel wird später aus erstem Vortrag extrahiert
        ga_folder_name = str(ga_identifier).replace('/', '_')
        output_dir = BASE_DIR / f"GA{ga_folder_name}"
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠️ Neuer Ordner erstellt: {output_dir.name}")
        print(f"   Bitte später umbenennen zu: GA{ga_number}-Voller Titel\n")
    
    print(f"Zielverzeichnis: {output_dir}\n")
    
    # Hole alle Vortragslinks
    print("Suche nach Vorträgen...")
    lecture_links = get_lecture_links(ga_identifier)
    
    if not lecture_links:
        print(f"✗ Keine Vorträge gefunden für GA{ga_identifier}")
        return
    
    print(f"✓ {len(lecture_links)} Vorträge gefunden\n")
    
    # Verwende editorische Reihenfolge (wie auf rsarchive.org nummeriert)
    # KEINE chronologische Sortierung mehr!
    print("Verwende editorische Reihenfolge von rsarchive.org...")
    
    # Entferne nur Duplikate (gleiche URL mehrmals)
    # Behalte dabei die Reihenfolge
    seen_urls = set()
    unique_lectures = []
    for url in lecture_links:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_lectures.append(url)
    
    print(f"✓ {len(unique_lectures)} eindeutige Vorträge (editorische Reihenfolge)\n")
    print("-" * 70)
    
    successful = 0
    failed = 0
    total_images_downloaded = 0
    
    # Erstelle assets Unterverzeichnis für Bilder
    images_dir = output_dir / "assets"
    
    # Iteriere über Vorträge in editorischer Reihenfolge
    for lecture_num, url in enumerate(unique_lectures, 1):
        lecture_file = url.split('/')[-1]
        print(f"\n[{lecture_num}/{len(unique_lectures)}] {lecture_file}")
        
        try:
            # Extrahiere deutschen Text MIT Bildern
            print("  → Extrahiere Text und Bilder...", end=' ', flush=True)
            
            german_text, image_urls = extract_german_text_with_images(url, ga_identifier)
            
            if not german_text or len(german_text) < 100:
                print("✗ Nicht gefunden oder zu kurz")
                failed += 1
                continue
            
            print(f"✓ ({len(german_text)} Zeichen", end='')
            if image_urls:
                print(f", {len(image_urls)} Bild(er))", end='')
            else:
                print(")", end='')
            print()
            
            # Extrahiere Metadaten
            print("  → Extrahiere Metadaten...", end=' ', flush=True)
            metadata = extract_lecture_metadata(url, None)  # soup=None, wird in Funktion neu geholt
            
            if not metadata:
                print("✗ Fehler")
                failed += 1
                continue
            
            # DUPLIKAT-PRÜFUNG: Prüfe ob wir schon einen Vortrag mit gleichem Datum und ähnlicher Länge haben
            # (verschiedene Übersetzungen haben meist gleiche Länge)
            date_key = f"{metadata['location']}_{metadata['date']}"
            text_len = len(german_text)
            
            # Prüfe ob bereits ein Vortrag mit diesem Datum existiert
            is_duplicate = False
            for existing_file in output_dir.glob("*.md"):
                existing_name = existing_file.name
                # Prüfe ob gleiches Datum im Dateinamen
                if metadata['date'] in existing_name and metadata['location'] in existing_name:
                    # Prüfe Textlänge
                    try:
                        with open(existing_file, 'r', encoding='utf-8-sig') as f:
                            existing_text = f.read()
                        existing_len = len(existing_text)
                        # Nur wenn Länge EXAKT gleich ist, ist es ein Duplikat
                        # (+/- 10 Zeichen für minimale Formatunterschiede)
                        if abs(existing_len - text_len) < 10:
                            print(f"✓ Duplikat (gleiche Übersetzung wie bereits vorhanden)")
                            is_duplicate = True
                            break
                    except:
                        pass
            
            if is_duplicate:
                continue  # Überspringe Duplikat
            
            # NICHT überschreiben - verwende Nummer aus Titel wenn vorhanden
            # Sonst verwende chronologische Nummer
            if not metadata.get('number_from_title'):
                metadata['number'] = str(lecture_num)
            
            # Zeige Ort, Datum Format
            location_date_display = f"{metadata['location']}, {metadata['date']}"
            print(f"✓ Nr. {lecture_num}: {location_date_display}")
            
            # Lade Bilder herunter (falls vorhanden)
            if image_urls:
                print("  → Lade Bilder herunter...", end=' ', flush=True)
                imgs_downloaded = download_images(image_urls, images_dir)
                total_images_downloaded += imgs_downloaded
                if imgs_downloaded > 0:
                    print(f"✓ {imgs_downloaded} neu")
                else:
                    print("✓ (bereits vorhanden)")
            
            # Erstelle Markdown-Datei
            print("  → Speichere Datei...", end=' ', flush=True)
            if create_markdown_file(ga_identifier, metadata, german_text, output_dir):
                print("✓")
                successful += 1
            else:
                print("✗")
                failed += 1
        
        except Exception as e:
            print(f"  ✗ Fehler: {e}")
            failed += 1
        
        # Pause zwischen Requests
        time.sleep(0.5)
    
    print("\n" + "="*70)
    print("DOWNLOAD ABGESCHLOSSEN")
    print("="*70)
    print(f"\n✓ Erfolgreich: {successful} Vorträge")
    print(f"✗ Fehlgeschlagen: {failed}")
    if total_images_downloaded > 0:
        print(f"📷 Bilder heruntergeladen: {total_images_downloaded}")
        print(f"   Gespeichert in: {images_dir.absolute()}")
    print(f"\nVorträge gespeichert in: {output_dir.absolute()}")

def main():
    if len(sys.argv) > 1:
        # Kann sein: "121", "332a", "266/I" etc.
        ga_identifier = sys.argv[1]
    else:
        # Standard: GA121
        ga_identifier = "121"
        print(f"Keine GA-Nummer angegeben, verwende GA{ga_identifier}")
    
    download_ga_lectures(ga_identifier)

if __name__ == "__main__":
    main()

