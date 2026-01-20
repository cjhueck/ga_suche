#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA Text Comparison Server
=========================
Flask-Backend für den Vergleich lokaler GA-Texte mit steiner.wiki
"""

import os
import re
import sys
import json
import difflib
import requests
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.')
CORS(app)

# Konfiguration
BASE_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"

# Monats-Mapping
MONAT_MAPPING = {
    'januar': 1, 'jan': 1, 'february': 2, 'februar': 2, 'feb': 2,
    'märz': 3, 'maerz': 3, 'mar': 3, 'march': 3,
    'april': 4, 'apr': 4, 'mai': 5, 'may': 5,
    'juni': 6, 'jun': 6, 'june': 6, 'juli': 7, 'jul': 7, 'july': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
    'oktober': 10, 'okt': 10, 'oct': 10, 'october': 10,
    'november': 11, 'nov': 11, 'dezember': 12, 'dez': 12, 'dec': 12, 'december': 12,
}

# Vortragsnummern-Mapping
VORTRAG_NUMMER_MAPPING = {
    'erster': 1, 'erste': 1, 'i': 1, 'zweiter': 2, 'zweite': 2, 'ii': 2,
    'dritter': 3, 'dritte': 3, 'iii': 3, 'vierter': 4, 'vierte': 4, 'iv': 4,
    'fünfter': 5, 'fünfte': 5, 'fuenfter': 5, 'v': 5,
    'sechster': 6, 'sechste': 6, 'vi': 6,
    'siebter': 7, 'siebenter': 7, 'siebte': 7, 'vii': 7,
    'achter': 8, 'achte': 8, 'viii': 8, 'neunter': 9, 'neunte': 9, 'ix': 9,
    'zehnter': 10, 'zehnte': 10, 'x': 10, 'elfter': 11, 'elfte': 11, 'xi': 11,
    'zwölfter': 12, 'zwölfte': 12, 'zwoelfter': 12, 'xii': 12,
    'dreizehnter': 13, 'vierzehnter': 14, 'fünfzehnter': 15,
    'sechzehnter': 16, 'siebzehnter': 17, 'achtzehnter': 18,
    'neunzehnter': 19, 'zwanzigster': 20,
}


def find_ga_folder(ga_nummer):
    """Findet den Ordner für eine GA-Nummer"""
    ga_str = str(ga_nummer).lower()
    for folder in BASE_PATH.iterdir():
        if folder.is_dir():
            name = folder.name.lower()
            if name.startswith(f"ga{ga_str}-") or name.startswith(f"ga{ga_str} -"):
                return folder
            if ga_str.isdigit():
                padded = ga_str.zfill(3)
                if name.startswith(f"ga{padded}-") or name.startswith(f"ga{padded} -"):
                    return folder
    return None


def find_vortrag_files(ga_folder):
    """Findet alle Vortrag-Dateien in einem GA-Ordner"""
    vortrag_files = []
    for file in ga_folder.iterdir():
        if file.is_file() and file.suffix == '.md':
            name = file.name.upper()
            # Dateien mit Vortragsnummer (z.B. "GA108 (1.) ...")
            has_number = re.search(r'GA\d+[A-Z]?\s*\(\d+\.\)', name)
            # Oder explizit "VORTRAG" oder "REDE" im Namen
            has_keyword = 'VORTRAG' in name or 'REDE' in name
            # Übersichts-Dateien ausschließen (keine Vortragsnummer)
            is_overview = file.stem.endswith(')') and not has_number
            
            if (has_number or has_keyword) and not is_overview:
                vortrag_files.append(file)
    
    def sort_key(f):
        match = re.search(r'\((\d+)\.\)', f.name)
        return int(match.group(1)) if match else 999
    
    return sorted(vortrag_files, key=sort_key)


def parse_date(text):
    """Extrahiert Datum aus Text"""
    match = re.search(r'(\d{1,2})\.?\s*(\w+)\s*(\d{3,4})', text)
    if match:
        tag = int(match.group(1))
        monat_str = match.group(2).lower()
        jahr = int(match.group(3))
        if jahr < 1000:
            jahr += 1000
        monat = MONAT_MAPPING.get(monat_str)
        if monat:
            return (tag, monat, jahr)
    return None


def extract_vortrag_nummer(text):
    """Extrahiert die Vortragsnummer aus dem Text"""
    match = re.search(r'\((\d+)\.\)', text)
    if match:
        return int(match.group(1))
    for wort, nummer in VORTRAG_NUMMER_MAPPING.items():
        if re.search(rf'\b{wort}\b', text.lower()):
            return nummer
    return None


def fetch_online_content(ga_nummer):
    """Lädt den Inhalt einer GA-Seite von steiner.wiki"""
    url = STEINER_WIKI_BASE.format(ga_nummer)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return None


def is_vortrag_heading(text):
    """Prüft ob ein Text eine Vortragsüberschrift ist"""
    text_upper = text.upper()
    
    # Explizit "VORTRAG" oder "REDE"
    if 'VORTRAG' in text_upper or 'REDE' in text_upper:
        return True
    
    # Überschrift mit Ort und Datum (z.B. "TITEL, Heidelberg, 21. Januar 1909")
    # Muster: Text, Ort, Tag. Monat Jahr
    if re.search(r'[A-ZÄÖÜ].*,\s*[A-ZÄÖÜ][a-zäöüß]+,?\s+\d{1,2}\.?\s*\w+\s*\d{4}', text):
        return True
    
    return False


def parse_online_vortraege(html_content):
    """Parst die Online-Vorträge aus dem HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    vortraege = {}
    
    content = soup.find('div', {'class': 'mw-parser-output'})
    if not content:
        content = soup
    
    current_vortrag = None
    current_text = []
    
    for element in content.find_all(['h1', 'h2', 'h3', 'p', 'span']):
        text = element.get_text().strip()
        is_heading = element.name in ['h1', 'h2', 'h3']
        is_span_with_id = element.name == 'span' and element.get('id')
        
        if is_heading or is_span_with_id:
            if is_vortrag_heading(text):
                if current_vortrag and current_text:
                    vortraege[current_vortrag] = '\n\n'.join(current_text)
                current_vortrag = text
                current_text = []
                continue
        
        if element.name == 'p' and current_vortrag:
            para_text = element.get_text().strip()
            # Entferne Soft-Hyphens
            para_text = para_text.replace('\u00ad', '')
            if para_text:
                current_text.append(para_text)
    
    if current_vortrag and current_text:
        vortraege[current_vortrag] = '\n\n'.join(current_text)
    
    return vortraege


def extract_ort(text):
    """Extrahiert den Ort aus dem Text (vor dem Datum)"""
    # Typische Muster: "Berlin, 5. Mai 1908" oder "in Berlin am 5. Mai"
    # Suche nach Wort vor Datum
    match = re.search(r'[,\s]([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)[,\s]+\d{1,2}\.?\s*\w+\s*\d{3,4}', text)
    if match:
        return match.group(1).strip().lower()
    # Alternative: Ort in Klammern oder nach Komma
    match = re.search(r'(?:in|zu)\s+([A-ZÄÖÜ][a-zäöüß]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return None


def get_text_fingerprint(text, num_words=20):
    """Erstellt einen Fingerprint aus den ersten N Wörtern des Textes"""
    # Entferne Markdown, Seitenmarker etc.
    clean = re.sub(r'#.*?\n', '', text)  # Überschriften
    clean = re.sub(r'\*\*\d+\*\*', '', clean)  # Seitenmarker
    clean = re.sub(r'\|\d+\|', '', clean)
    clean = re.sub(r'\^[a-z0-9]+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    words = clean.split()[:num_words]
    return ' '.join(words).lower()


def match_vortrag(local_name, online_vortraege, local_content=None):
    """Findet den passenden Online-Vortrag"""
    local_date = parse_date(local_name)
    local_nummer = extract_vortrag_nummer(local_name)
    local_ort = extract_ort(local_name)
    
    if not local_date:
        return None
    
    # Finde alle mit gleichem Datum
    matches = []
    for online_name in online_vortraege.keys():
        online_date = parse_date(online_name)
        if online_date and local_date == online_date:
            matches.append(online_name)
    
    if not matches:
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    # Bei mehreren: erst Ort vergleichen
    if local_ort:
        for online_name in matches:
            online_ort = extract_ort(online_name)
            if online_ort and local_ort == online_ort:
                return online_name
    
    # Dann Vortragsnummer verwenden
    if local_nummer:
        for online_name in matches:
            online_nummer = extract_vortrag_nummer(online_name)
            if online_nummer and local_nummer == online_nummer:
                return online_name
    
    # Zuletzt: Textanfang vergleichen (falls local_content vorhanden)
    if local_content and len(matches) > 1:
        local_fp = get_text_fingerprint(local_content)
        best_match = None
        best_score = 0
        
        for online_name in matches:
            online_content = online_vortraege.get(online_name, '')
            online_fp = get_text_fingerprint(online_content)
            
            # Vergleiche mit SequenceMatcher
            score = difflib.SequenceMatcher(None, local_fp, online_fp).ratio()
            if score > best_score:
                best_score = score
                best_match = online_name
        
        if best_match and best_score > 0.5:
            return best_match
    
    return matches[0]


def normalize_for_diff(text):
    """Normalisiert Text für den Diff-Vergleich"""
    # Entferne Soft-Hyphens
    text = text.replace('\u00ad', '')
    text = text.replace('\u200b', '')
    # Entferne Seitenzahlen-Marker
    text = re.sub(r'\s*\|(\d+)\|\s*', ' ', text)
    text = re.sub(r'\s*\*\*(\d+)\*\*\s*', ' ', text)
    # Entferne Block-IDs
    text = re.sub(r'\^[a-z0-9]+\s*', '', text)
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_spelling_variant(word1, word2):
    """Prüft ob zwei Wörter nur Rechtschreibvarianten sind (alt/neu)"""
    if not word1 or not word2:
        return False
    
    # Normalisiere beide Wörter: ß -> ss
    w1_norm = word1.lower().replace('ß', 'ss')
    w2_norm = word2.lower().replace('ß', 'ss')
    
    if w1_norm == w2_norm:
        return True
    
    # Prüfe auch Bindestrich-Varianten (Hin-deutung vs Hindeutung)
    w1_no_hyphen = w1_norm.replace('-', '')
    w2_no_hyphen = w2_norm.replace('-', '')
    
    if w1_no_hyphen == w2_no_hyphen:
        return True
    
    return False


def compute_diff(local_text, online_text):
    """Berechnet den Diff zwischen zwei Texten - auf Wort-Ebene"""
    local_norm = normalize_for_diff(local_text)
    online_norm = normalize_for_diff(online_text)
    
    # Teile in Wörter
    local_words = local_norm.split()
    online_words = online_norm.split()
    
    matcher = difflib.SequenceMatcher(None, local_words, online_words)
    
    differences = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            local_part = ' '.join(local_words[i1:i2]) if i1 < i2 else ''
            online_part = ' '.join(online_words[j1:j2]) if j1 < j2 else ''
            
            # Überspringe reine Whitespace-Unterschiede
            if local_part.strip() == online_part.strip():
                continue
            
            # Überspringe Rechtschreibvarianten (dass/daß, Bindestrich-Trennung)
            if is_spelling_variant(local_part, online_part):
                continue
            
            # Finde Kontext (3 Wörter vorher)
            context_start = max(0, i1 - 3)
            context = ' '.join(local_words[context_start:i1])
            
            differences.append({
                'type': tag,
                'local': local_part,
                'online': online_part,
                'context': context,
                'local_pos': i1,
                'online_pos': j1
            })
    
    return differences


# API Endpoints

@app.route('/')
def index():
    return send_from_directory('.', 'ga-text-comparison.html')


@app.route('/api/ga/<ga_nummer>/vortraege')
def get_vortraege(ga_nummer):
    """Gibt Liste der lokalen Vorträge für eine GA-Nummer zurück"""
    ga_folder = find_ga_folder(ga_nummer)
    if not ga_folder:
        return jsonify({'error': f'GA {ga_nummer} nicht gefunden'}), 404
    
    vortrag_files = find_vortrag_files(ga_folder)
    vortraege = []
    for f in vortrag_files:
        vortraege.append({
            'filename': f.name,
            'path': str(f),
            'name': f.stem
        })
    
    return jsonify({
        'ga_nummer': ga_nummer,
        'ga_folder': ga_folder.name,
        'vortraege': vortraege
    })


@app.route('/api/ga/<ga_nummer>/vortrag/<path:filename>')
def get_vortrag_content(ga_nummer, filename):
    """Gibt den Inhalt eines lokalen Vortrags zurück"""
    ga_folder = find_ga_folder(ga_nummer)
    if not ga_folder:
        return jsonify({'error': f'GA {ga_nummer} nicht gefunden'}), 404
    
    filepath = ga_folder / filename
    if not filepath.exists():
        return jsonify({'error': f'Datei nicht gefunden: {filename}'}), 404
    
    try:
        content = filepath.read_text(encoding='utf-8')
        return jsonify({
            'filename': filename,
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ga/<ga_nummer>/online')
def get_online_vortraege(ga_nummer):
    """Gibt Liste der Online-Vorträge für eine GA-Nummer zurück"""
    html_content = fetch_online_content(ga_nummer)
    if not html_content:
        return jsonify({'error': f'Online-Inhalt für GA {ga_nummer} nicht verfügbar'}), 404
    
    vortraege = parse_online_vortraege(html_content)
    return jsonify({
        'ga_nummer': ga_nummer,
        'vortraege': list(vortraege.keys())
    })


@app.route('/api/ga/<ga_nummer>/online/<path:vortrag_name>')
def get_online_vortrag_content(ga_nummer, vortrag_name):
    """Gibt den Inhalt eines Online-Vortrags zurück"""
    html_content = fetch_online_content(ga_nummer)
    if not html_content:
        return jsonify({'error': f'Online-Inhalt nicht verfügbar'}), 404
    
    vortraege = parse_online_vortraege(html_content)
    
    # Finde passenden Vortrag
    for name, content in vortraege.items():
        if vortrag_name in name or name in vortrag_name:
            return jsonify({
                'name': name,
                'content': content
            })
    
    return jsonify({'error': f'Vortrag nicht gefunden: {vortrag_name}'}), 404


@app.route('/api/ga/<ga_nummer>/match/<path:local_filename>')
def match_online_vortrag(ga_nummer, local_filename):
    """Findet den passenden Online-Vortrag zu einem lokalen Vortrag"""
    html_content = fetch_online_content(ga_nummer)
    if not html_content:
        return jsonify({'error': 'Online-Inhalt nicht verfügbar'}), 404
    
    online_vortraege = parse_online_vortraege(html_content)
    
    # Lade lokalen Inhalt für Textvergleich bei mehreren Matches
    local_content = None
    ga_folder = find_ga_folder(ga_nummer)
    if ga_folder:
        local_path = ga_folder / local_filename
        if local_path.exists():
            try:
                local_content = local_path.read_text(encoding='utf-8')
            except:
                pass
    
    matched = match_vortrag(local_filename, online_vortraege, local_content)
    
    if matched:
        return jsonify({
            'local': local_filename,
            'online': matched,
            'online_content': online_vortraege[matched]
        })
    
    return jsonify({'error': 'Kein passender Online-Vortrag gefunden'}), 404


@app.route('/api/diff', methods=['POST'])
def compute_text_diff():
    """Berechnet den Diff zwischen zwei Texten"""
    data = request.json
    local_text = data.get('local', '')
    online_text = data.get('online', '')
    
    differences = compute_diff(local_text, online_text)
    return jsonify({'differences': differences})


@app.route('/api/save', methods=['POST'])
def save_local_file():
    """Speichert Änderungen an einer lokalen Datei"""
    data = request.json
    filepath = data.get('filepath')
    content = data.get('content')
    
    if not filepath or content is None:
        return jsonify({'error': 'Fehlende Parameter'}), 400
    
    try:
        path = Path(filepath)
        if not path.exists():
            return jsonify({'error': 'Datei existiert nicht'}), 404
        
        path.write_text(content, encoding='utf-8')
        return jsonify({'success': True, 'message': 'Datei gespeichert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fix-markers/<ga_nummer>')
def fix_page_markers(ga_nummer):
    """Führt das Seitenmarker-Korrekturskript aus"""
    import subprocess
    
    script_path = Path(__file__).parent / 'fix_page_markers.py'
    if not script_path.exists():
        return jsonify({'error': 'Skript nicht gefunden'}), 404
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), str(ga_nummer), '--apply'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=120
        )
        return jsonify({
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout beim Ausführen des Skripts'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# PDF Konfiguration
PDF_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")


def find_pdf_file(ga_nummer):
    """Findet die PDF-Datei für eine GA-Nummer"""
    ga_str = str(ga_nummer).lower()
    ga_padded = ga_str.zfill(3)
    
    # Verschiedene Namensformate probieren
    patterns = [
        f"GA {ga_str},",      # "Steiner, Rudolf GA 102, 2001 - ..."
        f"GA {ga_str} -",     # "GA 102 - Titel.pdf"
        f"GA {ga_str}-",
        f"GA{ga_str} ",
        f"GA{ga_str}-",
        f"GA {ga_padded},",   # "Steiner, Rudolf GA 102, ..." mit führenden Nullen
        f"GA {ga_padded} ",
        f"GA{ga_padded}",
    ]
    
    for file in PDF_PATH.iterdir():
        if file.is_file() and file.suffix.lower() == '.pdf':
            name_lower = file.name.lower()
            for pattern in patterns:
                if pattern.lower() in name_lower:
                    return file
    
    # Auch in Teil-GAs suchen
    teil_path = PDF_PATH / "Teil-GAs"
    if teil_path.exists():
        for file in teil_path.iterdir():
            if file.is_file() and file.suffix.lower() == '.pdf':
                name_lower = file.name.lower()
                for pattern in patterns:
                    if pattern.lower() in name_lower:
                        return file
    
    return None


@app.route('/api/ga/<ga_nummer>/pdf')
def get_pdf_info(ga_nummer):
    """Gibt Informationen zur PDF-Datei für eine GA-Nummer zurück"""
    pdf_file = find_pdf_file(ga_nummer)
    if not pdf_file:
        return jsonify({'error': f'PDF für GA {ga_nummer} nicht gefunden'}), 404
    
    # URL-encode den Dateinamen für Sonderzeichen
    from urllib.parse import quote
    encoded_name = quote(pdf_file.name)
    
    return jsonify({
        'ga_nummer': ga_nummer,
        'filename': pdf_file.name,
        'path': str(pdf_file),
        'url': f'/pdf/{encoded_name}'
    })


@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    """Liefert PDF-Dateien aus"""
    # Suche in Hauptverzeichnis
    pdf_file = PDF_PATH / filename
    if pdf_file.exists():
        return send_from_directory(str(PDF_PATH), filename, mimetype='application/pdf')
    
    # Suche in Teil-GAs
    teil_file = PDF_PATH / "Teil-GAs" / filename
    if teil_file.exists():
        return send_from_directory(str(PDF_PATH / "Teil-GAs"), filename, mimetype='application/pdf')
    
    return jsonify({'error': 'PDF nicht gefunden'}), 404


if __name__ == '__main__':
    print("GA Text Comparison API Server")
    print("=============================")
    print(f"BASE_PATH: {BASE_PATH}")
    print(f"PDF_PATH: {PDF_PATH}")
    print("API läuft auf http://localhost:3004")
    print("Öffnen Sie http://localhost:3003/ga-text-comparison.html im Browser")
    app.run(host='0.0.0.0', port=3004, debug=True)
