#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA Text Vergleichs-Tool
=======================
Vergleicht lokale GA-Texte mit den Online-Versionen auf steiner.wiki

Nutzung:
    python compare_ga_texts.py              # Interaktiver Modus
    python compare_ga_texts.py 102          # Einzelne GA-Nummer
    python compare_ga_texts.py 100-105      # Bereich
    python compare_ga_texts.py 100,102,105  # Mehrere GA-Nummern
"""

import os
import re
import sys
import difflib
import requests
import io
import argparse
import json
from datetime import datetime

# UTF-8 Ausgabe für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from tabulate import tabulate

# Konfiguration
BASE_PATH = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA")
STEINER_WIKI_BASE = "https://steiner.wiki/GA_{}"
HISTORY_FILE = BASE_PATH / "_vergleich_historie.json"

# Rechtschreib-Mapping (alte -> neue Rechtschreibung)
RECHTSCHREIB_MAPPING = {
    'daß': 'dass',
    'muß': 'muss',
    'läßt': 'lässt',
    'faßt': 'fasst',
    'gefaßt': 'gefasst',
    'paßt': 'passt',
    'haßt': 'hasst',
    'Haß': 'Hass',
    'Fluß': 'Fluss',
    'Schluß': 'Schluss',
    'Bewußtsein': 'Bewusstsein',
    'bewußt': 'bewusst',
    'unbewußt': 'unbewusst',
    'Bewußtheit': 'Bewusstheit',
    'gewußt': 'gewusst',
    'wußte': 'wusste',
    'mußte': 'musste',
    'Kuß': 'Kuss',
    'Nuß': 'Nuss',
    'Genuß': 'Genuss',
    'Überfluß': 'Überfluss',
    'Einfluß': 'Einfluss',
    'Entschluß': 'Entschluss',
    'Ausfluß': 'Ausfluss',
    'Zufluß': 'Zufluss',
    'Abfluß': 'Abfluss',
    'Rückfluß': 'Rückfluss',
    'Kreislauf': 'Kreislauf',
    'Proceß': 'Prozess',
    'Prozeß': 'Prozess',
}

# Monats-Mapping für Datum-Vergleich
MONAT_MAPPING = {
    'januar': 1, 'jan': 1,
    'februar': 2, 'feb': 2,
    'märz': 3, 'maerz': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'mai': 5,
    'juni': 6, 'jun': 6,
    'juli': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9, 'sept': 9,
    'oktober': 10, 'okt': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'dezember': 12, 'dez': 12, 'dec': 12,
}

# Vortragsnummern-Mapping (Wort -> Zahl)
VORTRAG_NUMMER_MAPPING = {
    'erster': 1, 'erste': 1, 'i': 1,
    'zweiter': 2, 'zweite': 2, 'ii': 2,
    'dritter': 3, 'dritte': 3, 'iii': 3,
    'vierter': 4, 'vierte': 4, 'iv': 4,
    'fünfter': 5, 'fünfte': 5, 'fuenfter': 5, 'v': 5,
    'sechster': 6, 'sechste': 6, 'vi': 6,
    'siebter': 7, 'siebenter': 7, 'siebte': 7, 'vii': 7,
    'achter': 8, 'achte': 8, 'viii': 8,
    'neunter': 9, 'neunte': 9, 'ix': 9,
    'zehnter': 10, 'zehnte': 10, 'x': 10,
    'elfter': 11, 'elfte': 11, 'xi': 11,
    'zwölfter': 12, 'zwölfte': 12, 'zwoelfter': 12, 'xii': 12,
    'dreizehnter': 13, 'dreizehnte': 13, 'xiii': 13,
    'vierzehnter': 14, 'vierzehnte': 14, 'xiv': 14,
    'fünfzehnter': 15, 'fünfzehnte': 15, 'xv': 15,
    'sechzehnter': 16, 'sechzehnte': 16, 'xvi': 16,
    'siebzehnter': 17, 'siebzehnte': 17, 'xvii': 17,
    'achtzehnter': 18, 'achtzehnte': 18, 'xviii': 18,
    'neunzehnter': 19, 'neunzehnte': 19, 'xix': 19,
    'zwanzigster': 20, 'zwanzigste': 20, 'xx': 20,
}


@dataclass
class VortragVergleich:
    """Ergebnis eines Vortrag-Vergleichs"""
    vortrag_name: str
    lokal_vorhanden: bool
    online_vorhanden: bool
    textlaenge_lokal: int
    textlaenge_online: int
    abweichungen_count: int
    inhaltliche_abweichungen: int
    stilistische_abweichungen: int
    abweichungen: List[Tuple[str, str, str]]  # (lokal, online, typ)
    status: str


@dataclass
class GABandVergleich:
    """Ergebnis eines GA-Band-Vergleichs"""
    ga_nummer: int
    band_titel: str
    vortraege: List[VortragVergleich]
    gesamt_status: str
    fehler_meldung: Optional[str] = None


def normalize_rechtschreibung(text: str) -> str:
    """Normalisiert alte Rechtschreibung zu neuer"""
    for alt, neu in RECHTSCHREIB_MAPPING.items():
        text = re.sub(rf'\b{re.escape(alt)}\b', neu, text, flags=re.IGNORECASE)
    return text


def normalize_text(text: str, remove_page_markers: bool = True, 
                   normalize_spelling: bool = True) -> str:
    """
    Normalisiert Text für den Vergleich:
    - Entfernt Seitenzahlen-Marker
    - Entfernt Block-IDs (^xxxxx)
    - Entfernt Bild-Referenzen
    - Normalisiert Whitespace
    - Entfernt Markdown-Formatierung
    - Optional: Normalisiert Rechtschreibung
    """
    if not text:
        return ""
    
    # Entferne Block-IDs (z.B. ^y4wil9)
    text = re.sub(r'\^[a-z0-9]+\s*', '', text)
    
    # Entferne Bild-Referenzen (![...](assets/...))
    text = re.sub(r'!\[.*?\]\(.*?\)\s*', '', text)
    
    # Entferne Seitenzahlen-Marker (|123| oder **123**)
    if remove_page_markers:
        text = re.sub(r'\s*\|(\d+)\|\s*', ' ', text)
        text = re.sub(r'\s*\*\*(\d+)\*\*\s*', ' ', text)
    
    # Entferne Markdown-Formatierung
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Fett
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Kursiv
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Überschriften
    
    # Entferne Markdown-Tabellen
    text = re.sub(r'\|[^\n]+\|', '', text)
    
    # Normalisiere Rechtschreibung
    if normalize_spelling:
        text = normalize_rechtschreibung(text)
    
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_sentences(text: str) -> List[str]:
    """Extrahiert Sätze aus dem Text für den Vergleich"""
    normalized = normalize_text(text)
    # Teile in Sätze auf
    sentences = re.split(r'(?<=[.!?])\s+', normalized)
    return [s.strip() for s in sentences if s.strip()]


def find_ga_folder(ga_nummer) -> Optional[Path]:
    """Findet den Ordner für eine GA-Nummer (z.B. 102, '104a')"""
    ga_str = str(ga_nummer).lower()
    
    for folder in BASE_PATH.iterdir():
        if folder.is_dir():
            name = folder.name.lower()
            # Verschiedene Formatierungen: GA102-, GA102 -, GA0102-, GA104a-
            if (name.startswith(f"ga{ga_str}-") or 
                name.startswith(f"ga{ga_str} -")):
                return folder
            # Für rein numerische GA-Nummern auch mit führender Null
            if ga_str.isdigit():
                padded = ga_str.zfill(3)
                if name.startswith(f"ga{padded}-") or name.startswith(f"ga{padded} -"):
                    return folder
    return None


def find_vortrag_files(ga_folder: Path) -> List[Path]:
    """Findet alle Vortrag-Dateien in einem GA-Ordner"""
    vortrag_files = []
    
    for file in ga_folder.iterdir():
        if file.is_file() and file.suffix == '.md':
            name = file.name.upper()
            if 'VORTRAG' in name or 'REDE' in name:
                vortrag_files.append(file)
    
    # Sortiere nach Vortragsnummer
    def sort_key(f):
        match = re.search(r'\((\d+)\.\)', f.name)
        if match:
            return int(match.group(1))
        return 999
    
    return sorted(vortrag_files, key=sort_key)


def fetch_online_content(ga_nummer) -> Optional[str]:
    """Lädt den Inhalt einer GA-Seite von steiner.wiki"""
    url = STEINER_WIKI_BASE.format(ga_nummer)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  Fehler beim Abrufen von {url}: {e}")
        return None


def parse_online_vortraege(html_content: str, ga_nummer: int) -> Dict[str, str]:
    """
    Parst die Online-Vorträge aus dem HTML.
    Gibt Dictionary zurück: Key = Vortrag-Name, Value = Vortrag-Text
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    vortraege = {}
    
    content = soup.find('div', {'class': 'mw-parser-output'})
    if not content:
        content = soup
    
    current_vortrag = None
    current_text = []
    
    # Suche nach Vortrag-Überschriften in h2/h3 oder span mit ID
    for element in content.find_all(['h2', 'h3', 'p', 'span']):
        text = element.get_text().strip()
        
        # Prüfe ob es eine Vortrag-Überschrift ist
        is_heading = element.name in ['h2', 'h3']
        is_span_with_id = element.name == 'span' and element.get('id')
        
        if is_heading or is_span_with_id:
            text_upper = text.upper()
            if 'VORTRAG' in text_upper or 'REDE' in text_upper:
                # Speichere vorherigen Vortrag
                if current_vortrag and current_text:
                    vortraege[current_vortrag] = ' '.join(current_text)
                
                current_vortrag = text
                current_text = []
                continue
        
        # Sammle Paragraphen
        if element.name == 'p' and current_vortrag:
            para_text = element.get_text().strip()
            if para_text:
                current_text.append(para_text)
    
    # Letzten Vortrag speichern
    if current_vortrag and current_text:
        vortraege[current_vortrag] = ' '.join(current_text)
    
    return vortraege


def parse_date(text: str) -> Optional[Tuple[int, int, int]]:
    """
    Extrahiert Datum aus Text.
    Gibt zurück: (Tag, Monat, Jahr) oder None
    """
    # Muster: "27. Januar 1908" oder "27.Januar 1908" oder "27. Mai 908" (Tippfehler online)
    match = re.search(r'(\d{1,2})\.?\s*(\w+)\s*(\d{3,4})', text)
    if match:
        tag = int(match.group(1))
        monat_str = match.group(2).lower()
        jahr = int(match.group(3))
        
        # Korrigiere 3-stellige Jahreszahlen (z.B. "908" -> "1908")
        if jahr < 1000:
            jahr += 1000
        
        monat = MONAT_MAPPING.get(monat_str)
        if monat:
            return (tag, monat, jahr)
    
    return None


def extract_vortrag_nummer(text: str) -> Optional[int]:
    """
    Extrahiert die Vortragsnummer aus dem Text.
    Unterstützt:
    - "(1.)" Format aus Dateinamen
    - "ERSTER VORTRAG", "ZWEITER VORTRAG" etc.
    - Römische Zahlen
    """
    text_upper = text.upper()
    
    # Muster 1: "(X.)" Format in Dateinamen
    match = re.search(r'\((\d+)\.\)', text)
    if match:
        return int(match.group(1))
    
    # Muster 2: "ERSTER VORTRAG", "ZWEITER VORTRAG" etc.
    for wort, nummer in VORTRAG_NUMMER_MAPPING.items():
        pattern = rf'\b{wort}\b'
        if re.search(pattern, text.lower()):
            return nummer
    
    return None


def get_text_fingerprint(text: str, length: int = 200) -> str:
    """
    Erstellt einen normalisierten Fingerprint der ersten Textzeichen
    für Textvergleich beim Matching.
    """
    normalized = normalize_text(text, remove_page_markers=True, normalize_spelling=True)
    # Entferne GA-Titel und Überschriften vom Anfang
    normalized = re.sub(r'^GA\s*\d+[^\n]*', '', normalized)
    normalized = re.sub(r'^Das\s+\w+-Evangelium[^\n]*', '', normalized, flags=re.IGNORECASE)
    normalized = normalized.strip()
    # Nimm nur Buchstaben und Zahlen für stabilen Vergleich
    fingerprint = re.sub(r'[^\w]', '', normalized.lower())
    return fingerprint[:length]


def match_vortrag_names(local_name: str, online_names: List[str], 
                        local_text: str = None, 
                        online_texts: Dict[str, str] = None) -> Optional[str]:
    """
    Findet den passenden Online-Vortrag zu einem lokalen Vortrag.
    
    Matching-Strategie:
    1. Datum matchen
    2. Bei mehreren Treffern: Vortragsnummer verwenden
    3. Falls nötig: Textanfang vergleichen
    """
    local_date = parse_date(local_name)
    
    if not local_date:
        return None
    
    # Finde alle Online-Vorträge mit gleichem Datum
    matches = []
    for online_name in online_names:
        online_date = parse_date(online_name)
        if online_date and local_date == online_date:
            matches.append(online_name)
    
    if not matches:
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    # Mehrere Vorträge am gleichen Datum - nutze Vortragsnummer
    local_nummer = extract_vortrag_nummer(local_name)
    
    if local_nummer:
        for online_name in matches:
            online_nummer = extract_vortrag_nummer(online_name)
            if online_nummer and local_nummer == online_nummer:
                return online_name
    
    # Falls Vortragsnummern nicht helfen, vergleiche Textanfänge
    if local_text and online_texts:
        local_fp = get_text_fingerprint(local_text)
        
        best_match = None
        best_similarity = 0
        
        for online_name in matches:
            if online_name in online_texts:
                online_fp = get_text_fingerprint(online_texts[online_name])
                # Berechne Ähnlichkeit der Fingerprints
                similarity = difflib.SequenceMatcher(None, local_fp, online_fp).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = online_name
        
        if best_match and best_similarity > 0.5:
            return best_match
    
    # Fallback: Ersten Treffer zurückgeben (mit Warnung)
    return matches[0]


def classify_difference(local_sent: str, online_sent: str) -> str:
    """
    Klassifiziert eine Abweichung.
    Gibt zurück: "inhaltlich" oder "stilistisch"
    """
    # Normalisiere beide mit Rechtschreibnormalisierung
    local_norm = normalize_text(local_sent, normalize_spelling=True)
    online_norm = normalize_text(online_sent, normalize_spelling=True)
    
    if local_norm == online_norm:
        return "stilistisch"
    
    # Prüfe auf kleine Unterschiede (Interpunktion, Leerzeichen)
    local_clean = re.sub(r'[^\w]', '', local_norm.lower())
    online_clean = re.sub(r'[^\w]', '', online_norm.lower())
    
    if local_clean == online_clean:
        return "stilistisch"
    
    # Berechne Ähnlichkeit
    similarity = difflib.SequenceMatcher(None, local_clean, online_clean).ratio()
    
    if similarity > 0.95:
        return "stilistisch"
    
    return "inhaltlich"


def compare_texts(local_text: str, online_text: str) -> Tuple[int, int, int, List[Tuple[str, str, str]]]:
    """
    Vergleicht zwei Texte und findet Abweichungen.
    Gibt zurück: (Gesamt-Abweichungen, inhaltliche, stilistische, Liste von Abweichungen)
    """
    local_sentences = extract_sentences(local_text)
    online_sentences = extract_sentences(online_text)
    
    matcher = difflib.SequenceMatcher(None, local_sentences, online_sentences)
    
    abweichungen = []
    inhaltlich = 0
    stilistisch = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                local_sent = local_sentences[i] if i < len(local_sentences) else ""
                online_sent = online_sentences[j] if j < len(online_sentences) else ""
                if local_sent != online_sent:
                    typ = classify_difference(local_sent, online_sent)
                    if typ == "inhaltlich":
                        inhaltlich += 1
                        abweichungen.append((local_sent[:100], online_sent[:100], typ))
                    else:
                        stilistisch += 1
        elif tag == 'delete':
            for i in range(i1, i2):
                inhaltlich += 1
                abweichungen.append((local_sentences[i][:100], "[FEHLT ONLINE]", "inhaltlich"))
        elif tag == 'insert':
            for j in range(j1, j2):
                inhaltlich += 1
                abweichungen.append(("[FEHLT LOKAL]", online_sentences[j][:100], "inhaltlich"))
    
    total = inhaltlich + stilistisch
    # Alle inhaltlichen Abweichungen speichern
    inhaltliche_abw = [a for a in abweichungen if a[2] == "inhaltlich"]
    return total, inhaltlich, stilistisch, inhaltliche_abw


def compare_ga_band(ga_nummer: int, verbose: bool = True) -> GABandVergleich:
    """Vergleicht einen kompletten GA-Band"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Vergleiche GA {ga_nummer}...")
        print('='*60)
    
    # Finde lokalen Ordner
    ga_folder = find_ga_folder(ga_nummer)
    if not ga_folder:
        return GABandVergleich(
            ga_nummer=ga_nummer,
            band_titel=f"GA {ga_nummer}",
            vortraege=[],
            gesamt_status="FEHLER",
            fehler_meldung=f"Lokaler Ordner fuer GA {ga_nummer} nicht gefunden"
        )
    
    band_titel = ga_folder.name
    if verbose:
        print(f"Lokaler Ordner: {band_titel}")
    
    # Finde lokale Vorträge
    local_files = find_vortrag_files(ga_folder)
    if verbose:
        print(f"Gefundene lokale Vortraege: {len(local_files)}")
    
    if not local_files:
        return GABandVergleich(
            ga_nummer=ga_nummer,
            band_titel=band_titel,
            vortraege=[],
            gesamt_status="WARNUNG",
            fehler_meldung="Keine Vortrag-Dateien im lokalen Ordner gefunden"
        )
    
    # Lade Online-Inhalt
    if verbose:
        print(f"Lade Online-Inhalt von steiner.wiki...")
    html_content = fetch_online_content(ga_nummer)
    
    if not html_content:
        return GABandVergleich(
            ga_nummer=ga_nummer,
            band_titel=band_titel,
            vortraege=[],
            gesamt_status="FEHLER",
            fehler_meldung=f"Online-Inhalt konnte nicht geladen werden"
        )
    
    # Parse Online-Vorträge
    online_vortraege = parse_online_vortraege(html_content, ga_nummer)
    if verbose:
        print(f"Gefundene Online-Vortraege: {len(online_vortraege)}")
    
    # Vergleiche jeden Vortrag
    vergleiche = []
    used_online_vortraege = set()  # Verhindere doppeltes Matching
    
    for local_file in local_files:
        vortrag_name = local_file.stem
        if verbose:
            print(f"\n  Vergleiche: {vortrag_name[:50]}...")
        
        # Lese lokalen Text
        try:
            local_text = local_file.read_text(encoding='utf-8')
            local_length = len(normalize_text(local_text))
        except Exception as e:
            vergleiche.append(VortragVergleich(
                vortrag_name=vortrag_name,
                lokal_vorhanden=False,
                online_vorhanden=False,
                textlaenge_lokal=0,
                textlaenge_online=0,
                abweichungen_count=-1,
                inhaltliche_abweichungen=0,
                stilistische_abweichungen=0,
                abweichungen=[],
                status=f"FEHLER: {e}"
            ))
            continue
        
        # Finde passenden Online-Vortrag (mit Textvergleich falls nötig)
        available_online = {k: v for k, v in online_vortraege.items() if k not in used_online_vortraege}
        matched_online = match_vortrag_names(
            vortrag_name, 
            list(available_online.keys()),
            local_text=local_text,
            online_texts=available_online
        )
        
        if not matched_online:
            vergleiche.append(VortragVergleich(
                vortrag_name=vortrag_name,
                lokal_vorhanden=True,
                online_vorhanden=False,
                textlaenge_lokal=local_length,
                textlaenge_online=0,
                abweichungen_count=-1,
                inhaltliche_abweichungen=0,
                stilistische_abweichungen=0,
                abweichungen=[],
                status="Nicht online gefunden"
            ))
            continue
        
        # Markiere als verwendet, um doppeltes Matching zu verhindern
        used_online_vortraege.add(matched_online)
        
        online_text = online_vortraege[matched_online]
        online_length = len(normalize_text(online_text))
        
        # Vergleiche Texte
        total, inhaltlich, stilistisch, abweichungen = compare_texts(local_text, online_text)
        
        if total == 0:
            status = "OK"
        elif inhaltlich == 0:
            status = f"OK (nur Rechtschreibung)"
        else:
            status = f"{inhaltlich} inhaltl."
        
        vergleiche.append(VortragVergleich(
            vortrag_name=vortrag_name,
            lokal_vorhanden=True,
            online_vorhanden=True,
            textlaenge_lokal=local_length,
            textlaenge_online=online_length,
            abweichungen_count=total,
            inhaltliche_abweichungen=inhaltlich,
            stilistische_abweichungen=stilistisch,
            abweichungen=abweichungen,
            status=status
        ))
    
    # Bestimme Gesamtstatus
    total_inhaltlich = sum(v.inhaltliche_abweichungen for v in vergleiche)
    total_stilistisch = sum(v.stilistische_abweichungen for v in vergleiche)
    missing = sum(1 for v in vergleiche if not v.online_vorhanden)
    
    if missing > 0:
        gesamt_status = f"WARNUNG: {missing} Vortraege nicht online"
    elif total_inhaltlich == 0:
        if total_stilistisch == 0:
            gesamt_status = "OK - Texte stimmen ueberein"
        else:
            gesamt_status = f"OK - nur Rechtschreibdifferenzen ({total_stilistisch})"
    else:
        gesamt_status = f"ABWEICHUNGEN: {total_inhaltlich} inhaltlich"
    
    return GABandVergleich(
        ga_nummer=ga_nummer,
        band_titel=band_titel,
        vortraege=vergleiche,
        gesamt_status=gesamt_status
    )


def print_ergebnis(ergebnis: GABandVergleich, show_details: bool = True):
    """Gibt das Vergleichsergebnis tabellarisch aus"""
    print(f"\n{'='*80}")
    print(f"ERGEBNIS: {ergebnis.band_titel}")
    print(f"{'='*80}")
    
    if ergebnis.fehler_meldung:
        print(f"\n[!] {ergebnis.fehler_meldung}")
        return
    
    # Tabelle erstellen
    headers = ["Nr.", "Vortrag (Datum)", "Lokal", "Online", "Inhaltl.", "Stil.", "Status"]
    rows = []
    
    for i, v in enumerate(ergebnis.vortraege, 1):
        # Extrahiere nur Datum
        date = parse_date(v.vortrag_name)
        if date:
            monat_namen = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            kurz_name = f"{date[0]:2d}. {monat_namen[date[1]]} {date[2]}"
        else:
            kurz_name = v.vortrag_name[:20]
        
        rows.append([
            i,
            kurz_name,
            f"{v.textlaenge_lokal:,}" if v.lokal_vorhanden else "-",
            f"{v.textlaenge_online:,}" if v.online_vorhanden else "-",
            v.inhaltliche_abweichungen if v.online_vorhanden else "-",
            v.stilistische_abweichungen if v.online_vorhanden else "-",
            v.status
        ])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    # Zeige inhaltliche Abweichungen pro Vortrag
    if show_details:
        for v in ergebnis.vortraege:
            if v.abweichungen and v.inhaltliche_abweichungen > 0:
                print(f"\n{'='*60}")
                print(f"VORTRAG: {v.vortrag_name}")
                print(f"Inhaltliche Abweichungen: {v.inhaltliche_abweichungen}")
                print('='*60)
                for i, (local, online, typ) in enumerate(v.abweichungen, 1):
                    print(f"\n  [{i}] LOKAL:  {local}")
                    print(f"      ONLINE: {online}")
    
    print(f"\n[GESAMTSTATUS] {ergebnis.gesamt_status}")


def parse_ga_range(eingabe: str) -> List:
    """
    Parst eine Eingabe zu einer Liste von GA-Nummern.
    Unterstützt: '102', '100-105', '104a', '104,104a'
    """
    ga_nummern = []
    
    for teil in eingabe.split(','):
        teil = teil.strip()
        # Prüfe ob es ein Bereich ist (nur für rein numerische Werte)
        if '-' in teil and teil.replace('-', '').isdigit():
            parts = teil.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                ga_nummern.extend(range(start, end + 1))
                continue
        
        # Einzelner Wert (kann Buchstaben enthalten wie "104a")
        if teil.isdigit():
            ga_nummern.append(int(teil))
        else:
            ga_nummern.append(teil)  # z.B. "104a"
    
    return ga_nummern


def load_history() -> Dict:
    """Lädt die Bearbeitungshistorie aus der JSON-Datei"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"bearbeitet": {}, "letzte_aktualisierung": None}
    return {"bearbeitet": {}, "letzte_aktualisierung": None}


def save_history(history: Dict):
    """Speichert die Bearbeitungshistorie in die JSON-Datei"""
    history["letzte_aktualisierung"] = datetime.now().isoformat()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def update_history(ergebnis: GABandVergleich, history: Dict):
    """Aktualisiert die Historie mit einem neuen Vergleichsergebnis"""
    ga_key = str(ergebnis.ga_nummer)
    
    total_inhaltlich = sum(v.inhaltliche_abweichungen for v in ergebnis.vortraege)
    total_stilistisch = sum(v.stilistische_abweichungen for v in ergebnis.vortraege)
    
    history["bearbeitet"][ga_key] = {
        "band_titel": ergebnis.band_titel,
        "datum": datetime.now().isoformat(),
        "anzahl_vortraege": len(ergebnis.vortraege),
        "inhaltliche_abweichungen": total_inhaltlich,
        "stilistische_abweichungen": total_stilistisch,
        "status": ergebnis.gesamt_status,
        "fehler": ergebnis.fehler_meldung
    }


def print_history_status(history: Dict):
    """Gibt eine Übersicht der bearbeiteten GA-Bände aus"""
    bearbeitet = history.get("bearbeitet", {})
    
    if not bearbeitet:
        print("\nNoch keine GA-Baende bearbeitet.")
        return
    
    print(f"\n{'='*80}")
    print(f"BEARBEITUNGSHISTORIE ({len(bearbeitet)} GA-Baende)")
    print('='*80)
    
    headers = ["GA", "Titel", "Datum", "Vortr.", "Inhaltl.", "Status"]
    rows = []
    
    for ga_num in sorted(bearbeitet.keys(), key=int):
        info = bearbeitet[ga_num]
        datum = info.get("datum", "")[:10]  # Nur Datum, ohne Zeit
        
        rows.append([
            ga_num,
            info.get("band_titel", "")[:30],
            datum,
            info.get("anzahl_vortraege", "-"),
            info.get("inhaltliche_abweichungen", "-"),
            info.get("status", "")[:20]
        ])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    if history.get("letzte_aktualisierung"):
        print(f"\nLetzte Aktualisierung: {history['letzte_aktualisierung'][:19]}")


def export_results(ergebnisse: List[GABandVergleich], filepath: Path):
    """Exportiert die Ergebnisse in eine Markdown-Datei"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# GA Text-Vergleich Ergebnisse\n\n")
        f.write(f"Verglichen mit: steiner.wiki\n\n")
        
        for ergebnis in ergebnisse:
            f.write(f"## {ergebnis.band_titel}\n\n")
            
            if ergebnis.fehler_meldung:
                f.write(f"**Fehler:** {ergebnis.fehler_meldung}\n\n")
                continue
            
            # Tabelle
            f.write("| Nr. | Datum | Lokal | Online | Inhaltl. | Stil. | Status |\n")
            f.write("|-----|-------|-------|--------|----------|-------|--------|\n")
            
            for i, v in enumerate(ergebnis.vortraege, 1):
                date = parse_date(v.vortrag_name)
                if date:
                    monat_namen = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 
                                  'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
                    datum = f"{date[0]:2d}. {monat_namen[date[1]]} {date[2]}"
                else:
                    datum = v.vortrag_name[:15]
                
                f.write(f"| {i} | {datum} | {v.textlaenge_lokal:,} | ")
                f.write(f"{v.textlaenge_online:,} | {v.inhaltliche_abweichungen} | ")
                f.write(f"{v.stilistische_abweichungen} | {v.status} |\n")
            
            f.write(f"\n**Status:** {ergebnis.gesamt_status}\n\n")
            
            # Inhaltliche Abweichungen
            has_content_diff = any(v.inhaltliche_abweichungen > 0 for v in ergebnis.vortraege)
            if has_content_diff:
                f.write("### Inhaltliche Abweichungen\n\n")
                for v in ergebnis.vortraege:
                    inhaltliche = [(l, o, t) for l, o, t in v.abweichungen if t == "inhaltlich"]
                    if inhaltliche:
                        f.write(f"**{v.vortrag_name[:50]}**\n\n")
                        for local, online, _ in inhaltliche:
                            f.write(f"- Lokal: `{local[:80]}...`\n")
                            f.write(f"- Online: `{online[:80]}...`\n\n")
            
            f.write("---\n\n")
    
    print(f"\nErgebnisse exportiert nach: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Vergleicht lokale GA-Texte mit steiner.wiki'
    )
    parser.add_argument(
        'ga_range', 
        nargs='?', 
        help='GA-Nummer(n): 102, 100-105, oder 100,102,105'
    )
    parser.add_argument(
        '--details', '-d',
        action='store_true',
        default=True,
        help='Zeige detaillierte Abweichungen'
    )
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Exportiere Ergebnisse in Markdown-Datei'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Weniger Ausgaben'
    )
    parser.add_argument(
        '--history', '-H',
        action='store_true',
        help='Zeige Bearbeitungshistorie'
    )
    
    args = parser.parse_args()
    
    print("""
================================================================
           GA TEXT VERGLEICHS-TOOL                            
   Vergleicht lokale GA-Texte mit steiner.wiki                
================================================================
    """)
    
    # Lade Historie
    history = load_history()
    
    # Nur Historie anzeigen
    if args.history:
        print_history_status(history)
        return
    
    # Wenn GA-Nummer als Argument übergeben wurde
    if args.ga_range:
        try:
            ga_nummern = parse_ga_range(args.ga_range)
            print(f"Vergleiche GA-Baende: {ga_nummern}")
            
            ergebnisse = []
            for ga_nummer in ga_nummern:
                # Prüfe ob bereits bearbeitet
                ga_key = str(ga_nummer)
                if ga_key in history.get("bearbeitet", {}):
                    prev = history["bearbeitet"][ga_key]
                    print(f"\n  [i] GA {ga_nummer} wurde bereits am {prev['datum'][:10]} bearbeitet")
                    print(f"      Status: {prev['status']}")
                
                ergebnis = compare_ga_band(ga_nummer, verbose=not args.quiet)
                ergebnisse.append(ergebnis)
                
                # Historie aktualisieren
                update_history(ergebnis, history)
                
                if not args.quiet:
                    print_ergebnis(ergebnis, show_details=args.details)
            
            # Historie speichern
            save_history(history)
            
            if len(ergebnisse) > 1:
                print_zusammenfassung(ergebnisse)
            
            # Export wenn gewuenscht
            if args.export:
                export_results(ergebnisse, Path(args.export))
                
        except ValueError as e:
            print(f"Fehler: Ungueltige GA-Nummer: {e}")
            sys.exit(1)
    else:
        # Interaktiver Modus
        interactive_mode(args.details, history)


def print_zusammenfassung(ergebnisse: List[GABandVergleich]):
    """Gibt eine Zusammenfassung für mehrere GA-Bände aus"""
    print(f"\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print('='*80)
    
    summary_headers = ["GA", "Titel", "Vortr.", "Inhaltl.", "Stil.", "Status"]
    summary_rows = []
    
    for e in ergebnisse:
        total_inhaltlich = sum(v.inhaltliche_abweichungen for v in e.vortraege)
        total_stilistisch = sum(v.stilistische_abweichungen for v in e.vortraege)
        
        summary_rows.append([
            e.ga_nummer,
            e.band_titel[:35] if e.band_titel else "-",
            len(e.vortraege),
            total_inhaltlich,
            total_stilistisch,
            e.gesamt_status[:25]
        ])
    
    print(tabulate(summary_rows, headers=summary_headers, tablefmt="grid"))


def interactive_mode(show_details: bool = True, history: Dict = None):
    """Interaktiver Modus"""
    if history is None:
        history = load_history()
    
    while True:
        print("\nBefehle: GA-Nummer(n), 'historie', 'q' zum Beenden")
        print("Beispiele: '102', '100-105', '100,102,105'")
        try:
            eingabe = input("> ").strip()
        except EOFError:
            break
        
        if eingabe.lower() in ['q', 'quit', 'exit', 'beenden']:
            print("Auf Wiedersehen!")
            break
        
        if eingabe.lower() in ['historie', 'history', 'h']:
            print_history_status(history)
            continue
        
        try:
            ga_nummern = parse_ga_range(eingabe)
        except ValueError:
            print("Ungueltige Eingabe. Bitte GA-Nummer(n) eingeben.")
            continue
        
        print(f"\nVergleiche GA-Baende: {ga_nummern}")
        
        ergebnisse = []
        for ga_nummer in ga_nummern:
            # Prüfe ob bereits bearbeitet
            ga_key = str(ga_nummer)
            if ga_key in history.get("bearbeitet", {}):
                prev = history["bearbeitet"][ga_key]
                print(f"\n  [i] GA {ga_nummer} wurde bereits am {prev['datum'][:10]} bearbeitet")
                print(f"      Status: {prev['status']}")
            
            ergebnis = compare_ga_band(ga_nummer)
            ergebnisse.append(ergebnis)
            
            # Historie aktualisieren
            update_history(ergebnis, history)
            
            print_ergebnis(ergebnis, show_details=show_details)
        
        # Historie speichern
        save_history(history)
        
        if len(ergebnisse) > 1:
            print_zusammenfassung(ergebnisse)


if __name__ == "__main__":
    main()
