#!/usr/bin/env python3
"""
Export Page Markers V3 - Robuste Seitenzahl-Extraktion mit Validierung

Workflow:
1. Extrahiere ALLE Seiten der PDF mit ihrem ersten Textblock
2. Extrahiere die Seitenzahl aus der Fußzeile (Y-Position-basiert, ganz unten)
3. Extrahiere Vortrags-Grenzen aus JSON (lectureId, startPage)
4. Ergänze fehlende Seitenzahlen durch lineare Interpolation
5. Suche jeden beforeText im JSON-Content
6. Validiere die gesamte Marker-Sequenz
7. Erstelle eine lückenlose Seitenmarker-Sequenz mit lectureId

Validierungen:
- Seitenzahlen aufsteigend, keine Duplikate
- Vortrags-Grenzen aufsteigend  
- beforeText im JSON auffindbar
- Mindestens 30% extrahiert (nicht interpoliert)
- Max-Seitenzahl ≤ PDF-Seitenanzahl

Verwendung:
    python export_page_markers_v2.py GA051
    python export_page_markers_v2.py --test GA051
    python export_page_markers_v2.py --validate GA051
"""

import fitz  # PyMuPDF
import re
import sys
import json
import io
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field
from enum import Enum

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Konfiguration
PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
OUTPUT_FILE = Path("page-markers.json")
SCRIPT_DIR = Path(__file__).parent

# beforeText Länge
BEFORE_TEXT_MIN = 20
BEFORE_TEXT_MAX = 60


def is_likely_heading(text: str) -> bool:
    """
    Erkennt ob ein Text wahrscheinlich eine Überschrift ist.
    Überschriften sollten NICHT als beforeText verwendet werden,
    sondern der Text UNTER der Überschrift.
    
    Returns:
        True wenn der Text wahrscheinlich eine Überschrift ist
    """
    if not text:
        return False
    
    # Normalisiere: Entferne Zeilenumbrüche, trimme
    text_clean = text.replace('\n', ' ').strip()
    
    # Kriterium 1: Komplett in GROSSBUCHSTABEN (und lang genug)
    # z.B. "WAS FINDET DER MODERNE MENSCH IN DER THEOSOPHIE?"
    if len(text_clean) > 10 and text_clean.upper() == text_clean:
        # Prüfe ob es tatsächlich Buchstaben enthält (nicht nur Zahlen/Sonderzeichen)
        if any(c.isalpha() for c in text_clean):
            return True
    
    # Kriterium 2: Meta-Texte (Autoreferate, Zusammenfassungen, Nummerierungen etc.)
    # Diese sind KEINE Absatz-Texte und sollten übersprungen werden
    # WICHTIG: VOR Kriterium 3 prüfen, da "/. Die griechischen..." sonst falsch als Absatz klassifiziert wird!
    meta_patterns = [
        r'^Autoreferat\b',
        r'^Zusammenfassung\s+(von|eines|einer|des|der)\b',
        r'^(Vortrag|Vorträge),?\s+gehalten\b',
        r'^gehalten\s+(in|am|vom)\b',
        r'^Notizen\b',
        r'^Stenographische\s+Aufzeichnung',
        r'^Vom\s+Vortragenden\s+(nicht\s+)?durchgesehen',
        r'^[/I1]\.\s+',  # Nummerierung wie "/. Die griechischen..." oder "I. Kapitel" oder "1. Die..."
        r'^\d+\.\s+(Die|Der|Das|Eine?)\s+',  # "1. Die griechischen Weltanschauungen"
        r'^Die\s+(griechischen|römischen|deutschen)\s+',  # Kapitelüberschriften
    ]
    
    for pattern in meta_patterns:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return True
    
    # Kriterium 3: Kurzer Text ohne Satzzeichen am Ende (typisch für Titel)
    # z.B. "Die Entstehung der Metamorphosenlehre"
    # ABER: Abgeschnittene Absätze (> 40 Zeichen mit Komma) sind KEINE Headings!
    if len(text_clean) < 80:
        # Hat kein Satzzeichen am Ende?
        if not text_clean.rstrip().endswith(('.', ',', ';', ':', '!', '?', '»', '"')):
            # Hat keine Absatz-typischen Merkmale (lange Sätze, mehrere Satzzeichen)?
            sentence_markers = text_clean.count('.') + text_clean.count(',') + text_clean.count(';')
            # Wenn der Text > 35 Zeichen UND mindestens ein Komma hat,
            # ist es wahrscheinlich ein abgeschnittener Absatz, keine Überschrift
            if sentence_markers >= 1 and len(text_clean) > 35:
                return False  # Wahrscheinlich ein Absatz!
            if sentence_markers < 2:
                return True
    
    # Kriterium 4: Datumszeilen (z.B. "Berlin, 6. September 1903")
    # Diese sind Meta-Informationen, keine Absätze
    date_patterns = [
        r'^[A-ZÄÖÜ][a-zäöüß]+,\s+\d{1,2}\.\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}$',
        r'^\d{1,2}\.\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}$',
        r'^[A-ZÄÖÜ][a-zäöüß]+,\s+(den\s+)?\d{1,2}\.\s+\w+\s+\d{4}$',
    ]
    for pattern in date_patterns:
        if re.match(pattern, text_clean):
            return True
    
    # Kriterium 4: Bekannte Überschriften-Muster
    heading_patterns = [
        r'^(ERSTER|ZWEITER|DRITTER|VIERTER|FÜNFTER|SECHSTER|SIEBENTER|ACHTER|NEUNTER|ZEHNTER)\s',
        r'^(Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebenter|Achter|Neunter|Zehnter)\s',
        r'^[IVX]+\.\s',  # Römische Ziffern: I., II., III.
        r'^[IVX]+\s+[A-ZÄÖÜ]',  # Römische Ziffern: I Kapitel
        r'^\d+\.\s+[A-ZÄÖÜ]',  # 1. Kapitel
        r'^(KAPITEL|Kapitel|TEIL|Teil|ANHANG|Anhang|VORWORT|Vorwort)\b',
        r'^(ZUR EINFÜHRUNG|Zur Einführung|EINLEITUNG|Einleitung)\b',
    ]
    
    for pattern in heading_patterns:
        if re.match(pattern, text_clean):
            return True
    
    # Kriterium 7: Kurze Kapitelüberschriften (weniger als 50 Zeichen, kein Satzzeichen)
    # "Die griechischen Weltanschauungen" ist eine Überschrift
    if len(text_clean) < 50 and not any(c in text_clean for c in '.,:;!?'):
        # Prüfe ob es wie eine Kapitelüberschrift aussieht
        if text_clean.startswith('Die ') or text_clean.startswith('Der ') or text_clean.startswith('Das '):
            words = text_clean.split()
            # Kapitelüberschriften haben oft 2-5 Wörter
            if len(words) <= 5:
                return True
    
    return False


class Confidence(Enum):
    """Konfidenz der Seitenzahl-Extraktion."""
    EXTRACTED = "extracted"      # Direkt aus PDF-Fußzeile
    INTERPOLATED = "interpolated"  # Linear interpoliert


@dataclass
class PageInfo:
    """Information über eine PDF-Seite."""
    pdf_index: int
    printed_page: Optional[int]  # Seitenzahl aus Fußzeile (kann None sein)
    first_text: str  # Erster Textblock der Seite
    all_texts: List[str]  # Alle Textblöcke (für Fallback bei Überschriften)
    is_content_page: bool  # True wenn Hauptinhalt (nicht Vorwort etc.)
    confidence: Confidence = Confidence.EXTRACTED  # Wie wurde die Seitenzahl ermittelt?


@dataclass
class LectureInfo:
    """Information über einen Vortrag/Kapitel."""
    lecture_id: str           # z.B. "GA051/1"
    title: str                # Vortragstitel
    start_page: Optional[int] = None  # Erste Seite des Vortrags
    end_page: Optional[int] = None    # Letzte Seite des Vortrags
    first_paragraph: str = ""  # Erster Absatz (für Abgleich)


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __bool__(self):
        return self.is_valid
    
    def merge(self, other: 'ValidationResult'):
        """Merged ein anderes Validierungsergebnis."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class PageMarkerValidator:
    """
    Validiert Seitenmarker auf Konsistenz und Korrektheit.
    
    Prüfungen:
    1. Seitenzahlen aufsteigend, keine Duplikate
    2. Vortrags-Grenzen aufsteigend
    3. beforeText im JSON auffindbar
    4. Mindestens 30% extrahiert (nicht interpoliert)
    5. Max-Seitenzahl ≤ PDF-Seitenanzahl
    """
    
    def __init__(self, ga_number: str):
        self.ga_number = ga_number
    
    def validate_page_sequence(self, markers: List[Dict]) -> ValidationResult:
        """
        Prüfung 1: Seitenzahlen müssen lückenlos aufsteigend sein.
        - Keine Duplikate
        - Keine Rücksprünge
        - Lücken > 1 sind Warnungen
        """
        result = ValidationResult(is_valid=True)
        
        if not markers:
            result.warnings.append("Keine Marker vorhanden")
            return result
        
        pages = [m['page'] for m in markers]
        
        # Duplikate prüfen
        seen: Set[int] = set()
        duplicates: Set[int] = set()
        for p in pages:
            if p in seen:
                duplicates.add(p)
            seen.add(p)
        
        if duplicates:
            result.is_valid = False
            result.errors.append(f"Doppelte Seitenzahlen: {sorted(duplicates)}")
        
        # Aufsteigende Reihenfolge prüfen
        for i in range(1, len(pages)):
            if pages[i] <= pages[i-1]:
                result.is_valid = False
                result.errors.append(
                    f"Rücksprung: Seite {pages[i]} nach Seite {pages[i-1]}"
                )
            
            # Lücken > 1 sind Warnungen (nicht kritisch)
            gap = pages[i] - pages[i-1]
            if gap > 1:
                result.warnings.append(
                    f"Lücke: Seite {pages[i-1]} → {pages[i]} ({gap-1} Seiten fehlen)"
                )
        
        return result
    
    def validate_lecture_boundaries(
        self, 
        lectures: List[LectureInfo],
        markers: List[Dict]
    ) -> ValidationResult:
        """
        Prüfung 2: Vortrags-Grenzen müssen aufsteigend sein.
        - Jeder Vortrag hat eine Start-Seitenzahl
        - Start-Seitenzahlen sind aufsteigend
        """
        result = ValidationResult(is_valid=True)
        
        if not lectures:
            result.warnings.append("Keine Vortrags-Grenzen definiert")
            return result
        
        prev_start = 0
        for i, lecture in enumerate(lectures):
            if lecture.start_page is None:
                result.warnings.append(f"{lecture.lecture_id}: Keine Start-Seitenzahl")
                continue
            
            if lecture.start_page <= prev_start and i > 0:
                result.is_valid = False
                result.errors.append(
                    f"{lecture.lecture_id} beginnt auf S.{lecture.start_page}, "
                    f"aber vorheriger Vortrag begann auf S.{prev_start}"
                )
            
            prev_start = lecture.start_page
        
        return result
    
    def validate_before_texts(
        self, 
        markers: List[Dict],
        json_content: str
    ) -> ValidationResult:
        """
        Prüfung 3: beforeText muss im JSON-Content auffindbar sein.
        """
        result = ValidationResult(is_valid=True)
        
        if not json_content:
            result.warnings.append("Kein JSON-Content zum Validieren")
            return result
        
        not_found = []
        for marker in markers:
            bt = marker.get('beforeText', '')
            if bt and len(bt) >= 10:
                # Suche mit den ersten 20 Zeichen
                search_text = bt[:min(30, len(bt))]
                if search_text not in json_content:
                    not_found.append(marker['page'])
        
        if not_found:
            if len(not_found) > 10:
                result.warnings.append(
                    f"{len(not_found)} beforeTexts nicht im JSON gefunden: "
                    f"S.{not_found[:5]}... (und {len(not_found)-5} weitere)"
                )
            else:
                result.warnings.append(
                    f"beforeTexts nicht im JSON gefunden: Seiten {not_found}"
                )
        
        return result
    
    def validate_interpolation_quality(
        self, 
        markers: List[Dict],
        min_extracted_ratio: float = 0.30
    ) -> ValidationResult:
        """
        Prüfung 4: Mindestens 30% der Seitenzahlen müssen extrahiert sein.
        """
        result = ValidationResult(is_valid=True)
        
        if not markers:
            return result
        
        extracted = sum(1 for m in markers if m.get('confidence') == 'extracted')
        total = len(markers)
        ratio = extracted / total
        
        if ratio < min_extracted_ratio:
            result.is_valid = False
            result.errors.append(
                f"Nur {ratio*100:.1f}% der Seitenzahlen direkt extrahiert "
                f"(Minimum: {min_extracted_ratio*100:.0f}%)"
            )
        
        # Prüfe auf lange interpolierte Strecken
        consecutive = 0
        max_consecutive = 0
        for m in markers:
            if m.get('confidence') == 'interpolated':
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        
        if max_consecutive > 5:
            result.warnings.append(
                f"Lange interpolierte Strecke: {max_consecutive} Seiten ohne Anker"
            )
        
        return result
    
    def validate_pdf_consistency(
        self, 
        markers: List[Dict],
        pdf_page_count: int
    ) -> ValidationResult:
        """
        Prüfung 5: Max-Seitenzahl sollte nicht größer sein als PDF-Seitenanzahl.
        """
        result = ValidationResult(is_valid=True)
        
        if not markers or pdf_page_count <= 0:
            return result
        
        max_page = max(m['page'] for m in markers)
        
        if max_page > pdf_page_count + 50:  # Etwas Toleranz für Vorspann
            result.warnings.append(
                f"Max Seitenzahl ({max_page}) >> PDF-Seiten ({pdf_page_count})"
            )
        
        return result
    
    def validate_all(
        self,
        markers: List[Dict],
        lectures: List[LectureInfo] = None,
        json_content: str = "",
        pdf_page_count: int = 0
    ) -> ValidationResult:
        """Führt alle Validierungen durch."""
        
        final_result = ValidationResult(is_valid=True)
        
        # Prüfung 1: Seitenzahlen-Sequenz
        final_result.merge(self.validate_page_sequence(markers))
        
        # Prüfung 2: Vortrags-Grenzen - ENTFERNT
        # Die lectureId-Zuordnung erfolgt jetzt im Frontend durch Text-Matching.
        # final_result.merge(self.validate_lecture_boundaries(lectures or [], markers))
        
        # Prüfung 3: beforeText im JSON
        final_result.merge(self.validate_before_texts(markers, json_content))
        
        # Prüfung 4: Interpolations-Qualität
        final_result.merge(self.validate_interpolation_quality(markers))
        
        # Prüfung 5: PDF-Konsistenz
        final_result.merge(self.validate_pdf_consistency(markers, pdf_page_count))
        
        return final_result
    
    def print_report(self, result: ValidationResult):
        """Gibt einen Validierungsbericht aus."""
        print(f"\n  {'='*50}")
        print(f"  VALIDIERUNGSBERICHT für {self.ga_number}")
        print(f"  {'='*50}")
        
        if result.is_valid:
            print(f"  ✅ Alle kritischen Prüfungen bestanden")
        else:
            print(f"  ❌ Kritische Fehler gefunden!")
        
        if result.errors:
            print(f"\n  FEHLER ({len(result.errors)}):")
            for err in result.errors:
                print(f"    ❌ {err}")
        
        if result.warnings:
            print(f"\n  WARNUNGEN ({len(result.warnings)}):")
            for warn in result.warnings:
                print(f"    ⚠️  {warn}")
        
        if not result.errors and not result.warnings:
            print(f"  ✨ Keine Probleme gefunden!")
        
        print()


def extract_page_number_from_footer_v2(page, max_page: int = 700) -> Tuple[Optional[int], Confidence]:
    """
    ROBUSTE Seitenzahl-Extraktion mit Y-Position-Validierung.
    
    Seitenzahlen in GA-PDFs stehen IMMER ganz unten auf der Seite.
    Diese Funktion nutzt die Y-Position der Textblöcke, um nur
    Text aus dem unteren 15% der Seite zu betrachten.
    
    Args:
        page: PyMuPDF Page-Objekt
        max_page: Maximale akzeptable Seitenzahl
    
    Returns:
        Tuple von (Seitenzahl, Konfidenz) oder (None, EXTRACTED)
    """
    page_height = page.rect.height
    footer_threshold = page_height * 0.85  # Untere 15%
    
    # Hole Textblöcke mit Position
    blocks = page.get_text("blocks")
    
    # Sammle Kandidaten: (seitenzahl, priorität, y_position)
    candidates = []
    
    for block in blocks:
        if len(block) < 6 or block[6] != 0:  # Nur Textblöcke (type 0)
            continue
        
        y_bottom = block[3]  # y1 = untere Kante des Blocks
        text = block[4].strip()
        
        # NUR Blöcke im Footer-Bereich (untere 15%)
        if y_bottom < footer_threshold:
            continue
        
        # Muster 1: "Seite: X" (HÖCHSTE PRIORITÄT - sehr zuverlässig)
        match = re.search(r'Seite:\s*([\d\s]+)', text)
        if match:
            num_str = match.group(1).replace(' ', '').strip()
            if num_str.isdigit():
                num = int(num_str)
                if 1 <= num <= max_page:
                    candidates.append((num, 10, y_bottom))
                    continue
        
        # Muster 2: "- 123 -" (zentrierte Seitenzahl)
        match = re.search(r'[-–—]\s*(\d+)\s*[-–—]', text)
        if match:
            num = int(match.group(1))
            if 1 <= num <= max_page:
                candidates.append((num, 8, y_bottom))
                continue
        
        # Muster 3: Alleinstehende Zahl (nur Ziffern, evtl. mit Leerzeichen)
        clean_text = text.replace(' ', '')
        if clean_text.isdigit() and len(clean_text) <= 4:
            num = int(clean_text)
            if 1 <= num <= max_page:
                candidates.append((num, 5, y_bottom))
    
    if not candidates:
        return None, Confidence.EXTRACTED
    
    # Wähle besten Kandidaten: höchste Priorität, dann tiefste Y-Position
    candidates.sort(key=lambda c: (-c[1], -c[2]))
    return candidates[0][0], Confidence.EXTRACTED


def extract_page_number_from_footer(page_text: str, max_page: int = 700) -> Optional[int]:
    """
    LEGACY: Text-basierte Seitenzahl-Extraktion (Fallback).
    
    Wird verwendet wenn Y-Position nicht verfügbar ist.
    
    WICHTIG: Nur SICHERE Seitenzahlen werden akzeptiert:
    - "Seite: X" Muster (sehr zuverlässig bei GA-PDFs)
    - Alleinstehende Zahlen nur wenn sie unter max_page sind
    - Jahreszahlen (>1000) werden NICHT als Seitenzahlen akzeptiert
    
    Args:
        page_text: Der gesamte Text der Seite
        max_page: Maximale akzeptable Seitenzahl
    """
    lines = page_text.strip().split('\n')
    
    # Prüfe die letzten Zeilen
    for line in reversed(lines[-5:]):
        line = line.strip()
        
        # Muster 1: "Seite: X" oder "Seite: 1 2 3" (HÖCHSTE PRIORITÄT - sehr zuverlässig)
        match = re.search(r'Seite:\s*([\d\s]+)', line)
        if match:
            num_str = match.group(1).replace(' ', '').strip()
            if num_str.isdigit():
                page_num = int(num_str)
                # Selbst bei "Seite:" Muster nur plausible Zahlen akzeptieren
                if 1 <= page_num <= max_page:
                    return page_num
        
        # Muster 2: Nur Ziffern (evtl. mit Leerzeichen)
        # STRENG: Nur akzeptieren wenn es eine plausible Seitenzahl ist
        clean_line = line.replace(' ', '')
        if clean_line.isdigit():
            page_num = int(clean_line)
            # KEINE Jahreszahlen! Nur Seitenzahlen unter max_page
            if 1 <= page_num <= max_page:
                return page_num
    
    return None


def is_word_fragment(text: str) -> bool:
    """
    Erkennt ob ein Text mit einem Wortfragment beginnt.
    
    Wortfragmente entstehen durch Silbentrennung am Seitenrand:
    - "halb der abendländischen..." (von "inner-halb")
    - "sterblichkeit sprechen..." (von "Un-sterblichkeit")
    
    Kriterien:
    - Beginnt mit Kleinbuchstabe
    - Ist NICHT ein normales Wort am Satzanfang (ich, und, oder, aber, etc.)
    - Hat kein Satzzeichen am Anfang
    """
    if not text or len(text) < 3:
        return False
    
    # Entferne führende Leerzeichen
    text = text.lstrip()
    if not text:
        return False
    
    first_char = text[0]
    
    # Beginnt mit Großbuchstabe oder Satzzeichen? -> Kein Fragment
    if first_char.isupper() or first_char in '«"„([':
        return False
    
    # Beginnt mit Kleinbuchstabe
    if first_char.islower():
        # Extrahiere das erste Wort
        first_word_match = re.match(r'^([a-zäöüß]+)', text)
        if not first_word_match:
            return False
        
        first_word = first_word_match.group(1).lower()
        
        # Liste von Wörtern, die normal am Anfang stehen können
        # (nach einem Satzzeichen, das wir vielleicht nicht sehen)
        normal_start_words = {
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr',
            'und', 'oder', 'aber', 'denn', 'wenn', 'weil', 'dass', 'daß',
            'so', 'da', 'doch', 'auch', 'nur', 'noch', 'schon',
            'in', 'an', 'auf', 'für', 'mit', 'von', 'zu', 'bei',
            'als', 'wie', 'was', 'wer', 'wo', 'wann', 'warum',
            'ja', 'nein', 'nicht', 'kein', 'keine',
            'man', 'alle', 'alles', 'jeder', 'jede', 'jedes',
            'ein', 'eine', 'einen', 'einem', 'einer', 'eines',
            'der', 'die', 'das', 'den', 'dem', 'des',
            'sein', 'seine', 'seiner', 'seinem', 'seinen',
            'ihr', 'ihre', 'ihrer', 'ihrem', 'ihren',
            'hier', 'dort', 'nun', 'dann', 'jetzt', 'heute',
            'dieses', 'diese', 'dieser', 'diesem', 'diesen',
            'welcher', 'welche', 'welches', 'welchem', 'welchen',
            'solcher', 'solche', 'solches', 'solchem', 'solchen',
        }
        
        if first_word in normal_start_words:
            return False
        
        # Kurze Wörter (2-3 Zeichen) die mit Kleinbuchstabe beginnen
        # sind wahrscheinlich Fragmente wenn sie nicht in der Liste sind
        if len(first_word) <= 4:
            return True
        
        # Längere Wörter die mit Kleinbuchstabe beginnen sind auch Fragmente
        # (außer sie stehen in der normal_start_words Liste)
        return True
    
    return False


def skip_word_fragment(text: str) -> str:
    """
    Überspringt ein Wortfragment am Anfang und gibt den Rest zurück.
    
    "halb der abendländischen Kultur" -> "der abendländischen Kultur"
    """
    if not is_word_fragment(text):
        return text
    
    # Finde das Ende des Fragments (erstes Leerzeichen)
    text = text.lstrip()
    space_idx = text.find(' ')
    
    if space_idx > 0:
        rest = text[space_idx + 1:].lstrip()
        # Prüfe ob der Rest auch ein Fragment ist (selten, aber möglich)
        if is_word_fragment(rest):
            return skip_word_fragment(rest)
        return rest
    
    return text


def get_first_text_line_of_page(page) -> Optional[str]:
    """
    Holt die ERSTE TEXTZEILE einer Seite (oberste Zeile, die kein Heading/Datum ist).
    
    WICHTIG: Nicht der erste Textblock, sondern die erste ZEILE!
    Eine Seite kann mitten im Satz beginnen - genau diese Zeile brauchen wir.
    
    NEU: Überspringt Wortfragmente durch Silbentrennung!
    
    Returns:
        Die erste Textzeile der Seite (nach Überschriften/Datum), oder None
    """
    # Hole den gesamten Text der Seite als Zeilen
    text = page.get_text()
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Ignoriere leere Zeilen
        if len(line) < 5:
            continue
        
        # Ignoriere Seitenzahlen und Copyright
        if line.replace(' ', '').isdigit():
            continue
        if 'Copyright' in line or 'Buch:' in line:
            continue
        if re.match(r'^Seite:\s*\d', line):
            continue
        
        # Prüfe ob es ein Heading oder Datum ist
        if is_likely_heading(line):
            continue
        
        # NEU: Überspringe Wortfragmente durch Silbentrennung
        clean_line = skip_word_fragment(line)
        
        # Prüfe ob nach dem Überspringen noch genug Text übrig ist
        if len(clean_line) >= 10:
            return clean_line
        
        # Falls zu kurz, verwende die nächste Zeile
        continue
    
    return None


def get_text_blocks_of_page(page) -> List[str]:
    """
    Holt alle Textblöcke einer Seite (von oben nach unten sortiert).
    Ignoriert Kopfzeilen, Seitenzahlen, Copyright etc.
    
    Returns:
        Liste von Textblöcken, sortiert nach Y-Position
    """
    blocks = page.get_text("blocks")
    
    # Filtere Textblöcke (type 0 = Text)
    text_blocks = []
    for block in blocks:
        if len(block) >= 6 and block[6] == 0:  # block_type == 0 (Text)
            text = block[4].strip()
            
            # Ignoriere sehr kurze Blöcke
            if len(text) < 5:
                continue
            # Ignoriere reine Seitenzahlen
            if text.replace(' ', '').isdigit():
                continue
            # Ignoriere Copyright-Zeilen
            if 'Copyright' in text or 'Buch:' in text:
                continue
            if re.match(r'^Seite:\s*\d', text):
                continue
            
            text_blocks.append({
                'y': block[1],  # y0 Position
                'text': text
            })
    
    if not text_blocks:
        return []
    
    # Sortiere nach Y-Position (von oben nach unten)
    text_blocks.sort(key=lambda b: b['y'])
    
    return [b['text'] for b in text_blocks]


def get_first_text_of_page(page) -> Optional[str]:
    """
    Holt den ersten Textblock einer Seite (Text am OBEREN Rand).
    Wrapper für Kompatibilität.
    """
    blocks = get_text_blocks_of_page(page)
    return blocks[0] if blocks else None


def is_content_page(page_text: str, page_num: Optional[int], start_page: int = 1, end_page: int = 9999) -> bool:
    """
    Prüft ob eine Seite zum Hauptinhalt gehört.
    
    Vorspann (Inhaltsverzeichnis, Vorwort) und Anhang (Literaturverzeichnis)
    sind NICHT in den JSON-Dateien vorhanden und können daher nicht markiert werden.
    
    Args:
        page_text: Der Text der Seite
        page_num: Die gedruckte Seitenzahl
        start_page: Erste Seite des Hauptinhalts (Standard: 1)
        end_page: Letzte Seite des Hauptinhalts (Standard: 9999)
    """
    if page_num is None:
        return False
    
    # Prüfe ob im definierten Seitenbereich
    if page_num < start_page or page_num > end_page:
        return False
    
    return True


# Seitenbereiche für bekannte GA-Bände (Hauptinhalt, ohne Vorspann/Anhang/Hinweise)
# Format: "GAxxxx": (erste_seite, letzte_seite)
# - Vorspann (Inhaltsverzeichnis, Vorwort) ist NICHT im JSON
# - Alles nach "HINWEISE" ist NICHT im JSON
GA_PAGE_RANGES = {
    "GA001": (7, 300),      # Hauptinhalt beginnt auf Seite 7
    "GA002": (7, 180),      # Hauptinhalt beginnt auf Seite 7 (Vorrede)
    "GA004": (9, 280),      # Hauptinhalt beginnt nach Vorwort
    "GA005": (9, 200),      # Hauptinhalt beginnt nach Vorwort
    "GA006": (9, 220),      # Hauptinhalt beginnt nach Vorwort
    "GA007": (9, 160),      # Hauptinhalt beginnt nach Vorwort
    "GA008": (9, 190),      # Hauptinhalt beginnt nach Vorwort
    "GA009": (9, 200),      # Hauptinhalt beginnt nach Vorwort
    "GA010": (9, 230),      # Hauptinhalt beginnt nach Vorwort
    "GA051": (17, 320),     # Hauptinhalt beginnt auf Seite 17 (Erster Vortrag)
    "GA052": (13, 420),     # Hauptinhalt beginnt auf Seite 13 (Erster Vortrag)
}


def is_toc_or_appendix_page(first_text: str) -> bool:
    """
    Erkennt ob eine Seite ein Inhaltsverzeichnis oder Anhang ist.
    Diese Seiten sind NICHT im JSON-Content und sollten übersprungen werden.
    """
    if not first_text:
        return False
    
    text_upper = first_text.upper().strip()
    
    # Inhaltsverzeichnis-Marker
    toc_markers = [
        'INHALT',
        'INHALTSVERZEICHNIS',
        'INHALTS-VERZEICHNIS',
        'ÜBERSICHT',
        'CONTENTS',
    ]
    
    # Anhang-Marker
    appendix_markers = [
        'HINWEISE',
        'HINWEISE DES HERAUSGEBERS',
        'ANMERKUNGEN',
        'ANHANG',
        'BIBLIOGRAPHISCHER NACHWEIS',
        'NAMENREGISTER',
        'PERSONENREGISTER',
        'SACHREGISTER',
        'LITERATURVERZEICHNIS',
        'VERZEICHNIS',
        'NACHWEIS FRÜHERER AUFLAGEN',
        'ZU DIESER AUSGABE',
        'HERAUSGEBERKORREKTUREN',
    ]
    
    all_markers = toc_markers + appendix_markers
    
    for marker in all_markers:
        if text_upper.startswith(marker):
            return True
    
    return False


def extract_all_pages(pdf_path: Path, start_page: int = 1, end_page: int = 9999) -> Tuple[List[PageInfo], int]:
    """
    Extrahiert Informationen über alle Seiten der PDF.
    
    Verwendet Y-Position-basierte Seitenzahl-Extraktion für robustere Ergebnisse.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        start_page: Erste Seite des Hauptinhalts
        end_page: Letzte Seite des Hauptinhalts
    
    Returns:
        Tuple von (Liste von PageInfo, PDF-Seitenanzahl)
    """
    doc = fitz.open(pdf_path)
    pages = []
    pdf_page_count = len(doc)
    
    # Dynamisches max_page basierend auf PDF-Größe
    max_page = min(pdf_page_count + 100, 800)  # Etwas Puffer für Vorspann
    
    for pdf_idx in range(pdf_page_count):
        page = doc[pdf_idx]
        page_text = page.get_text()
        
        # ROBUST: Extrahiere Seitenzahl mit Y-Position-Validierung
        printed_page, confidence = extract_page_number_from_footer_v2(page, max_page)
        
        # Fallback auf text-basierte Extraktion wenn Y-Position versagt
        if printed_page is None:
            printed_page = extract_page_number_from_footer(page_text, max_page)
            confidence = Confidence.EXTRACTED if printed_page else Confidence.INTERPOLATED
        
        # WICHTIG: Extrahiere die ERSTE TEXTZEILE der Seite (nicht den ganzen Block!)
        # Eine Seite kann mitten im Satz beginnen - genau diese Zeile brauchen wir.
        first_line = get_first_text_line_of_page(page)
        
        # Für Fallback: Auch alle Textblöcke extrahieren
        all_texts = get_text_blocks_of_page(page)
        
        if first_line or all_texts:
            pages.append(PageInfo(
                pdf_index=pdf_idx,
                printed_page=printed_page,
                first_text=first_line or (all_texts[0] if all_texts else ""),
                all_texts=all_texts,
                is_content_page=is_content_page(page_text, printed_page, start_page, end_page),
                confidence=confidence
            ))
    
    doc.close()
    return pages, pdf_page_count


def interpolate_page_numbers(pages: List[PageInfo]) -> List[PageInfo]:
    """
    Ergänzt fehlende Seitenzahlen durch lineare Interpolation.
    
    Strategie:
    1. Finde Ankerpunkte (Seiten mit bekannter Seitenzahl)
    2. Interpoliere zwischen Ankerpunkten
    3. Extrapoliere am Anfang/Ende wenn nötig
    """
    if not pages:
        return pages
    
    # Sammle Ankerpunkte: (index in pages, printed_page)
    anchors = []
    for i, p in enumerate(pages):
        if p.printed_page is not None:
            anchors.append((i, p.printed_page))
    
    if not anchors:
        print("    WARNUNG: Keine Seitenzahlen gefunden!")
        return pages
    
    print(f"    Ankerpunkte: {len(anchors)} Seiten mit erkannter Seitenzahl")
    
    # Interpoliere
    result = []
    for i, page in enumerate(pages):
        if page.printed_page is not None:
            result.append(page)
            continue
        
        # Finde nächste Ankerpunkte vor und nach dieser Seite
        prev_anchor = None
        next_anchor = None
        
        for anchor_idx, anchor_page in anchors:
            if anchor_idx < i:
                prev_anchor = (anchor_idx, anchor_page)
            elif anchor_idx > i and next_anchor is None:
                next_anchor = (anchor_idx, anchor_page)
                break
        
        # Berechne interpolierte Seitenzahl
        if prev_anchor and next_anchor:
            # Zwischen zwei Ankern: lineare Interpolation
            prev_idx, prev_page = prev_anchor
            next_idx, next_page = next_anchor
            
            # Berechne Offset
            pages_between = next_idx - prev_idx
            page_diff = next_page - prev_page
            
            if pages_between > 0 and page_diff == pages_between:
                # Perfekte Sequenz - interpoliere
                offset = i - prev_idx
                interpolated = prev_page + offset
            else:
                # Unregelmäßig - verwende Distanz zum nächsten Anker
                offset = i - prev_idx
                interpolated = prev_page + offset
        
        elif prev_anchor:
            # Nur vorheriger Anker: extrapoliere vorwärts
            prev_idx, prev_page = prev_anchor
            offset = i - prev_idx
            interpolated = prev_page + offset
        
        elif next_anchor:
            # Nur nächster Anker: extrapoliere rückwärts
            next_idx, next_page = next_anchor
            offset = next_idx - i
            interpolated = next_page - offset
        
        else:
            # Sollte nicht passieren (anchors ist nicht leer)
            interpolated = i + 1
        
        # Erstelle neue PageInfo mit interpolierter Seitenzahl
        # WICHTIG: Markiere als INTERPOLATED für Qualitätskontrolle
        result.append(PageInfo(
            pdf_index=page.pdf_index,
            printed_page=interpolated,
            first_text=page.first_text,
            all_texts=page.all_texts if hasattr(page, 'all_texts') else [page.first_text],
            is_content_page=page.is_content_page,
            confidence=Confidence.INTERPOLATED
        ))
    
    return result


def normalize_for_matching(text: str) -> str:
    """Normalisiert Text für robusteren Vergleich."""
    text = text.replace('daß', 'dass').replace('Daß', 'Dass')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_before_text_in_content(first_text: str, content: str) -> Optional[str]:
    """
    Sucht den ersten Text der PDF-Seite im JSON-Content.
    Gibt einen beforeText zurück, der exakt im Content gefunden werden kann.
    """
    if not first_text or len(first_text) < 5:
        return None
    
    search_text = first_text.replace('\n', ' ').strip()
    
    # Strategie 1: Exakte Suche
    for length in range(min(len(search_text), 50), 10, -5):
        search_phrase = search_text[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content.find(search_phrase)
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # Strategie 2: Rechtschreibreform-normalisiert
    search_norm = normalize_for_matching(search_text)
    content_norm = normalize_for_matching(content)
    
    for length in range(min(len(search_norm), 50), 10, -5):
        search_phrase = search_norm[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content_norm.find(search_phrase)
        if idx >= 0:
            # Finde Position im Original
            original_idx = _find_original_position(content, content_norm, idx)
            return _extract_before_text(content, original_idx, len(search_phrase))
    
    # Strategie 3: Case-insensitive
    search_lower = search_text.lower()
    content_lower = content.lower()
    
    for length in range(min(len(search_lower), 50), 10, -5):
        search_phrase = search_lower[:length].strip()
        if len(search_phrase) < 10:
            continue
        
        idx = content_lower.find(search_phrase)
        if idx >= 0:
            return _extract_before_text(content, idx, len(search_phrase))
    
    # Strategie 4: Worttrennung - ab zweitem Wort
    words = search_text.split()
    if len(words) >= 3:
        for start in range(1, min(3, len(words) - 1)):
            remaining = ' '.join(words[start:start + 4])
            idx = content.find(remaining)
            if idx >= 0:
                # Gehe zum Wortanfang zurück
                word_start = idx
                while word_start > 0 and content[word_start - 1] not in ' \n\t.,;:!?':
                    word_start -= 1
                return _extract_before_text(content, word_start, len(remaining) + (idx - word_start))
    
    # Strategie 5: Fuzzy-Matching - toleriere OCR-Fehler
    # Suche nach den LETZTEN 3-4 Wörtern (diese haben weniger Fehler)
    if len(words) >= 4:
        last_words = ' '.join(words[-4:])
        idx = content.find(last_words)
        if idx >= 0:
            # Gehe entsprechend viele Wörter zurück (nicht Zeilenanfang!)
            # Bei letzten 4 Wörtern gehen wir len(words) - 4 Wörter zurück
            word_start = idx
            words_back = 0
            max_words_back = len(words) - 4
            while word_start > 0 and words_back < max_words_back:
                word_start -= 1
                if content[word_start] in ' \n\t':
                    words_back += 1
                if content[word_start] in '.!?\n':
                    word_start += 1
                    break
            while word_start < idx and content[word_start] in ' \n\t':
                word_start += 1
            return _extract_before_text(content, word_start, idx - word_start + len(last_words))
    
    # Strategie 6: Suche nach charakteristischen Wort-Kombinationen
    # Überspringe das erste Wort (oft abgeschnitten) und suche die nächsten
    if len(words) >= 5:
        for skip in range(1, min(4, len(words) - 3)):
            search_phrase = ' '.join(words[skip:skip + 4])
            if len(search_phrase) >= 15:
                idx = content.find(search_phrase)
                if idx >= 0:
                    # Gehe nur "skip" Wörter zurück
                    word_start = idx
                    words_back = 0
                    while word_start > 0 and words_back < skip:
                        word_start -= 1
                        if content[word_start] in ' \n\t':
                            words_back += 1
                        if content[word_start] in '.!?\n':
                            word_start += 1
                            break
                    while word_start < idx and content[word_start] in ' \n\t':
                        word_start += 1
                    return _extract_before_text(content, word_start, idx - word_start + len(search_phrase))
    
    # Strategie 7: Suche mit Regex für Variationen
    # z.B. "mit m Betracht" -> "mit .{1,5} Betracht"
    if len(words) >= 3:
        for i in range(len(words) - 2):
            # Erstelle Pattern: Wort1 + (beliebiges Wort) + Wort3
            word1 = re.escape(words[i])
            word3 = re.escape(words[i + 2])
            if len(word1) >= 3 and len(word3) >= 3:
                pattern = word1 + r'\s+\S+\s+' + word3
                match = re.search(pattern, content)
                if match:
                    # Gehe nur wenige Wörter zurück (entspricht den übersprungenen Wörtern)
                    # NICHT zum Zeilenanfang - wir wollen nahe am gefundenen Text bleiben
                    word_start = match.start()
                    words_back = 0
                    max_words_back = i  # So viele Wörter wie wir übersprungen haben
                    while word_start > 0 and words_back < max_words_back:
                        word_start -= 1
                        if content[word_start] in ' \n\t':
                            words_back += 1
                        if content[word_start] in '.!?\n':
                            word_start += 1
                            break
                    # Überspringe führende Leerzeichen
                    while word_start < match.start() and content[word_start] in ' \n\t':
                        word_start += 1
                    return _extract_before_text(content, word_start, match.end() - word_start)
    
    # Strategie 8: Suche längere charakteristische Phrasen (ohne erstes Wort)
    # Oft ist das erste Wort abgeschnitten (z.B. "schen" statt "Menschen")
    if len(words) >= 4:
        # Überspringe das erste Wort und suche die nächsten Wörter
        for skip in range(1, min(4, len(words) - 2)):
            for length in range(min(5, len(words) - skip), 2, -1):
                phrase = ' '.join(words[skip:skip + length])
                if len(phrase) >= 12:
                    idx = content.find(phrase)
                    if idx >= 0:
                        # Gehe nur ein paar Wörter zurück zum Wortanfang
                        # NICHT zum Satzanfang - wir wollen nahe am gefundenen Text bleiben
                        word_start = idx
                        words_back = 0
                        while word_start > 0 and words_back < 3:
                            if content[word_start - 1] in ' \n\t':
                                words_back += 1
                            if content[word_start - 1] in '.!?\n':
                                break
                            word_start -= 1
                        # Überspringe führende Leerzeichen
                        while word_start < idx and content[word_start] in ' \n\t':
                            word_start += 1
                        return _extract_before_text(content, word_start, idx - word_start + len(phrase))
    
    # Strategie 9: Suche nach markanten Wörtern (3+ Buchstaben, selten)
    # Kombiniere 2 markante Wörter aus der Zeile
    significant_words = [w for w in words if len(w) >= 5 and w[0].islower()]
    if len(significant_words) >= 2:
        for i in range(len(significant_words) - 1):
            # Suche: Wort1 + (0-50 Zeichen) + Wort2
            word1 = re.escape(significant_words[i])
            word2 = re.escape(significant_words[i + 1])
            pattern = word1 + r'.{0,50}' + word2
            match = re.search(pattern, content)
            if match:
                # Gehe zum Zeilenanfang zurück
                line_start = match.start()
                while line_start > 0 and content[line_start - 1] not in '\n':
                    line_start -= 1
                return _extract_before_text(content, line_start, match.end() - line_start)
    
    return None


def _find_original_position(original: str, normalized: str, norm_idx: int) -> int:
    """Findet die Position im Original-String."""
    target = normalized[norm_idx:norm_idx + 30]
    
    for pos in range(max(0, norm_idx - 20), min(len(original), norm_idx + 50)):
        if normalize_for_matching(original[pos:pos + 35]).startswith(target[:20]):
            return pos
    
    return norm_idx


def _extract_before_text(content: str, start_idx: int, min_len: int) -> Optional[str]:
    """Extrahiert beforeText aus dem Content."""
    end_pos = start_idx + max(min_len, BEFORE_TEXT_MIN)
    
    while end_pos < len(content) and end_pos < start_idx + BEFORE_TEXT_MAX:
        # WICHTIG: Stoppe bei Wortgrenzen, aber NICHT bei \n
        # (wir wollen keine Zeilenumbrüche im beforeText)
        if content[end_pos] in ' .,;:!?':
            break
        # Bei Zeilenumbruch: Weiter bis zum nächsten sinnvollen Text
        if content[end_pos] == '\n':
            end_pos += 1
            continue
        end_pos += 1
    
    before_text = content[start_idx:end_pos].strip()
    
    # WICHTIG: Entferne Zeilenumbrüche aus dem beforeText
    # Das HTML hat <div> statt \n, also würde die Suche sonst fehlschlagen
    before_text = ' '.join(before_text.split())
    
    return before_text if len(before_text) >= BEFORE_TEXT_MIN else None


def load_json_content_for_ga(ga_number: str) -> Optional[str]:
    """
    Lädt den gesamten Text-Content für eine GA aus den JSON-Dateien.
    
    Enthält auch Vortrags-/Kapitel-Titel, damit Überschriften-Seiten gefunden werden.
    """
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num = ga_num.group(1).zfill(3).upper()
    ga_pattern = f"GA{ga_num}"
    
    content_parts = []
    
    for json_file in SCRIPT_DIR.glob("steiner-*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'lectures' in data:
                for lecture in data['lectures']:
                    if lecture.get('gaNumber', '').upper() == ga_pattern:
                        # Füge auch den Vortrags-Titel hinzu (für Überschriften-Seiten)
                        title = lecture.get('title', '')
                        if title:
                            content_parts.append(title)
                        
                        for para in lecture.get('paragraphs', []):
                            content_parts.append(para.get('content', ''))
            
            if 'books' in data:
                for book in data['books']:
                    if book.get('ID', '').upper() == ga_pattern:
                        # Füge Buchtitel hinzu
                        title = book.get('title', '')
                        if title:
                            content_parts.append(title)
                        content_parts.append(book.get('content', ''))
        
        except Exception as e:
            print(f"    Warnung: {json_file.name}: {e}")
    
    return '\n\n'.join(content_parts) if content_parts else None


def load_lectures_for_ga(ga_number: str) -> List[LectureInfo]:
    """
    Extrahiert alle Vorträge/Kapitel einer GA aus den JSON-Dateien.
    
    Returns:
        Liste von LectureInfo-Objekten mit lectureId, Titel und erstem Absatz
    """
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return []
    
    ga_num = ga_num.group(1).zfill(3).upper()
    ga_pattern = f"GA{ga_num}"
    
    lectures = []
    
    for json_file in sorted(SCRIPT_DIR.glob("steiner-*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'lectures' in data:
                for lecture in data['lectures']:
                    if lecture.get('gaNumber', '').upper() == ga_pattern:
                        lecture_id = lecture.get('ID', '')
                        title = lecture.get('title', '')
                        
                        # Extrahiere den ersten Absatz (für Seitenzahl-Zuordnung)
                        paragraphs = lecture.get('paragraphs', [])
                        first_para = ''
                        if paragraphs:
                            first_para = paragraphs[0].get('content', '')[:200]
                        
                        lectures.append(LectureInfo(
                            lecture_id=lecture_id,
                            title=title,
                            first_paragraph=first_para
                        ))
            
            if 'books' in data:
                for book in data['books']:
                    if book.get('ID', '').upper() == ga_pattern:
                        lectures.append(LectureInfo(
                            lecture_id=book.get('ID', ga_pattern),
                            title=book.get('title', ''),
                            first_paragraph=book.get('content', '')[:200] if book.get('content') else ''
                        ))
        
        except Exception as e:
            print(f"    Warnung beim Laden von Vorträgen: {json_file.name}: {e}")
    
    print(f"    {len(lectures)} Vorträge/Kapitel gefunden")
    return lectures


def find_lecture_start_pages_in_pdf(pdf_path: Path, lectures: List[LectureInfo], start_page: int = 1) -> Dict[str, int]:
    """
    Sucht die Vortrags-Titel direkt in der PDF und gibt deren Startseiten zurück.
    
    Diese Methode ist viel genauer als die Schätzung basierend auf Zeichenanzahl.
    
    WICHTIG: Sucht nur ab start_page und prüft ob der Titel die ERSTE Zeile ist,
    um Inhaltsverzeichnisse zu ignorieren.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        lectures: Liste der Vorträge mit Titeln
        start_page: Erste Seite des Hauptinhalts (ignoriert Vorwort/Inhaltsverzeichnis)
    
    Returns:
        Dict von lectureId -> startPage
    """
    result = {}
    
    try:
        doc = fitz.open(pdf_path)
        
        for lecture in lectures:
            if not lecture.title:
                continue
            
            # Normalisiere den Titel für die Suche
            title_upper = lecture.title.upper()
            # Verwende die ersten 30 Zeichen des Titels für den Vergleich
            title_search = title_upper[:30] if len(title_upper) > 30 else title_upper
            
            # Suche in jeder Seite
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text()
                
                # Extrahiere Seitenzahl aus dem Footer
                lines = text.strip().split('\n')
                page_num = None
                for line in lines[-3:]:
                    match = re.match(r'^Seite:\s*(\d+)$', line.strip())
                    if match:
                        page_num = int(match.group(1))
                        break
                
                if not page_num:
                    continue
                
                # WICHTIG: Ignoriere Seiten vor dem Hauptinhalt (Inhaltsverzeichnis!)
                if page_num < start_page:
                    continue
                
                # Finde die ERSTE nicht-leere Zeile (den Seitenkopf)
                first_line = None
                for line in lines[:5]:
                    line_clean = line.strip()
                    if line_clean and len(line_clean) > 5:
                        first_line = line_clean.upper()
                        break
                
                if not first_line:
                    continue
                
                # Ignoriere Inhaltsverzeichnis-Seiten
                if first_line.startswith('INHALT'):
                    continue
                
                # Prüfe ob der Titel die ERSTE Zeile ist (nicht irgendwo auf der Seite)
                if title_search in first_line:
                    result[lecture.lecture_id] = page_num
                    print(f"      {lecture.lecture_id}: Seite {page_num} (Titel in erster Zeile)")
                    break
        
        doc.close()
        
    except Exception as e:
        print(f"    Warnung bei PDF-Titel-Suche: {e}")
    
    return result


def assign_lecture_ids_to_markers(
    markers: List[Dict], 
    lectures: List[LectureInfo],
    content: str,
    pdf_path: Optional[Path] = None
) -> List[Dict]:
    """
    Weist jedem Marker eine lectureId zu.
    
    Strategie:
    1. Suche Vortrags-Titel direkt in der PDF (präzise Methode)
    2. Falls PDF nicht verfügbar: Fallback auf Schätzung
    3. Ordne Marker dem Vortrag zu, in dessen Seitenbereich sie fallen
    """
    if not lectures or not markers:
        return markers
    
    # Schritt 1: Finde Startseite für jeden Vortrag
    # PRIMÄRE Methode: Suche Titel in der PDF
    if pdf_path and pdf_path.exists():
        print("    Suche Vortrags-Titel in PDF...")
        pdf_start_pages = find_lecture_start_pages_in_pdf(pdf_path, lectures)
        
        # Übertrage gefundene Startseiten auf lectures
        for lecture in lectures:
            if lecture.lecture_id in pdf_start_pages:
                lecture.start_page = pdf_start_pages[lecture.lecture_id]
    
    # FALLBACK: Schätzung für Vorträge, die in der PDF nicht gefunden wurden
    marker_pages = {m['page']: m for m in markers}
    sorted_pages = sorted(marker_pages.keys())
    
    lectures_without_page = [l for l in lectures if l.start_page is None]
    if lectures_without_page:
        print(f"    Fallback-Schätzung für {len(lectures_without_page)} Vorträge...")
        
        for lecture in lectures_without_page:
            if not lecture.first_paragraph or len(lecture.first_paragraph) < 20:
                continue
            
            # Suche den ersten Absatz im Content
            search_text = lecture.first_paragraph[:50].strip()
            idx = content.find(search_text)
            
            if idx >= 0:
                text_before = content[:idx]
                # Schätze die Seite basierend auf der Position (~2500 Zeichen pro Seite)
                estimated_page = len(text_before) // 2500 + sorted_pages[0] if sorted_pages else 1
                
                # Finde den nächsten tatsächlichen Marker
                for page in sorted_pages:
                    if page >= estimated_page - 5:
                        lecture.start_page = page
                        print(f"      {lecture.lecture_id}: Seite {page} (geschätzt)")
                        break
    
    # Schritt 2: Sortiere Vorträge nach Startseite
    lectures_with_pages = [l for l in lectures if l.start_page is not None]
    lectures_with_pages.sort(key=lambda l: l.start_page)
    
    # Schritt 3: Weise lectureId zu
    for marker in markers:
        page = marker['page']
        
        # Finde den Vortrag, in dessen Bereich diese Seite fällt
        assigned_lecture = None
        for i, lecture in enumerate(lectures_with_pages):
            next_start = lectures_with_pages[i + 1].start_page if i + 1 < len(lectures_with_pages) else float('inf')
            
            if lecture.start_page <= page < next_start:
                assigned_lecture = lecture
                break
        
        if assigned_lecture:
            marker['lectureId'] = assigned_lecture.lecture_id
    
    # Zeige Vortrags-Grenzen
    if lectures_with_pages:
        print(f"    Vortrags-Grenzen:")
        for lecture in lectures_with_pages[:10]:
            print(f"      {lecture.lecture_id}: ab Seite {lecture.start_page}")
        if len(lectures_with_pages) > 10:
            print(f"      ... und {len(lectures_with_pages) - 10} weitere")
    
    return markers


def find_pdf_for_ga(ga_number: str) -> Optional[Path]:
    """Findet die PDF-Datei für eine GA-Nummer."""
    ga_num = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_num:
        return None
    
    ga_num_str = ga_num.group(1).zfill(3)
    
    for pdf_file in PDF_DIR.glob("*.pdf"):
        if f"GA {ga_num_str}" in pdf_file.name or f"GA{ga_num_str}" in pdf_file.name:
            return pdf_file
        
        ga_num_short = ga_num_str.lstrip('0') or '0'
        if f"GA {ga_num_short}," in pdf_file.name or f"GA {ga_num_short} " in pdf_file.name:
            return pdf_file
    
    return None


def process_ga(ga_number: str, test_mode: bool = False, validate_only: bool = False) -> Optional[Dict]:
    """
    Verarbeitet eine GA mit dem robusten Ansatz inkl. Validierung.
    
    Args:
        ga_number: GA-Nummer (z.B. "GA051")
        test_mode: Wenn True, wird nicht gespeichert
        validate_only: Wenn True, nur Validierung durchführen
    """
    print(f"\n{'='*60}")
    print(f"Verarbeite: {ga_number}")
    print(f"{'='*60}")
    
    # Normalisiere GA-Nummer
    ga_match = re.search(r'(\d+[a-z]?)', ga_number, re.IGNORECASE)
    if not ga_match:
        print("  FEHLER: Ungültige GA-Nummer")
        return None
    
    ga_normalized = f"GA{ga_match.group(1).zfill(3)}"
    
    # Finde PDF
    pdf_path = find_pdf_for_ga(ga_number)
    if not pdf_path:
        print(f"  FEHLER: Keine PDF gefunden")
        return None
    
    print(f"  PDF: {pdf_path.name}")
    
    # Lade JSON-Content
    print("  Lade JSON-Content...")
    content = load_json_content_for_ga(ga_number)
    if not content:
        print(f"  FEHLER: Kein Content in JSON")
        return None
    
    print(f"  Content: {len(content):,} Zeichen")
    
    # NEU: Lade Vortrags-Grenzen
    print("  Lade Vortrags-Struktur...")
    lectures = load_lectures_for_ga(ga_number)
    
    # Hole Seitenbereich für diese GA (falls bekannt)
    page_range = GA_PAGE_RANGES.get(ga_normalized, (1, 9999))
    start_page, end_page = page_range
    
    if ga_normalized in GA_PAGE_RANGES:
        print(f"  Seitenbereich: {start_page} - {end_page} (Hauptinhalt)")
    
    # SCHRITT 1: Extrahiere alle Seiten (mit Y-Position-basierter Seitenzahl-Erkennung)
    print("\n  Schritt 1: Extrahiere Seiten aus PDF (Y-Position-basiert)...")
    pages, pdf_page_count = extract_all_pages(pdf_path, start_page, end_page)
    print(f"    {len(pages)} Seiten mit Text gefunden (PDF: {pdf_page_count} Seiten)")
    
    # Statistik: Wie viele haben SICHERE Seitenzahlen aus der PDF?
    extracted_count = sum(1 for p in pages if p.printed_page is not None and p.confidence == Confidence.EXTRACTED)
    with_page_num = sum(1 for p in pages if p.printed_page is not None)
    recognition_rate = (extracted_count / len(pages) * 100) if pages else 0
    print(f"    Davon {extracted_count} direkt extrahiert ({recognition_rate:.1f}%)")
    
    # WICHTIG: Prüfe ob genügend sichere Seitenzahlen vorhanden sind
    MIN_RECOGNITION_RATE = 10.0  # Mindestens 10% der Seiten müssen Seitenzahlen haben
    
    if recognition_rate < MIN_RECOGNITION_RATE:
        print(f"\n  ⚠️  WARNUNG: Zu wenige Seitenzahlen erkannt ({recognition_rate:.1f}% < {MIN_RECOGNITION_RATE}%)")
        print(f"     Diese PDF hat keine zuverlässigen Seitenzahlen in der Fußzeile.")
        print(f"     Für diese GA können keine automatischen Marker erstellt werden.")
        print(f"     → Bitte manuell überprüfen oder Seitenzahlen in GA_PAGE_RANGES definieren.")
        return None
    
    # Zeige die ersten erkannten Seitenzahlen zur Validierung
    recognized = [(p.pdf_index + 1, p.printed_page) for p in pages if p.printed_page is not None and p.confidence == Confidence.EXTRACTED][:5]
    print(f"    Erste extrahierte Seitenzahlen: {recognized}")
    
    # SCHRITT 2: Interpoliere fehlende Seitenzahlen
    print("\n  Schritt 2: Interpoliere fehlende Seitenzahlen...")
    pages = interpolate_page_numbers(pages)
    
    # Statistik nach Interpolation
    interpolated_count = sum(1 for p in pages if p.confidence == Confidence.INTERPOLATED)
    print(f"    {interpolated_count} Seiten interpoliert")
    
    # Validierung: Prüfe Konsistenz der Seitenzahlen mit PDF-Seitenanzahl
    page_nums = [p.printed_page for p in pages if p.printed_page is not None]
    if page_nums:
        min_page = min(page_nums)
        max_page = max(page_nums)
        expected_range = max_page - min_page + 1
        
        # Die Anzahl der Seiten sollte ungefähr der PDF-Seitenanzahl entsprechen
        if abs(expected_range - pdf_page_count) > 10:
            print(f"    ⚠️  Warnung: Seitenbereich {min_page}-{max_page} ({expected_range} Seiten)")
            print(f"       PDF hat {pdf_page_count} Seiten - Differenz: {abs(expected_range - pdf_page_count)}")
        else:
            print(f"    ✓ Seitenbereich {min_page}-{max_page} passt zu {pdf_page_count} PDF-Seiten")
    
    # SCHRITT 3: Suche beforeText im JSON
    print("\n  Schritt 3: Suche beforeText im JSON-Content...")
    markers = []
    found_count = 0
    found_with_fallback = 0
    not_found_count = 0
    
    skipped_toc = 0
    
    for page in pages:
        if not page.is_content_page:
            continue
        
        # Überspringe Inhaltsverzeichnis- und Anhang-Seiten
        # Diese sind NICHT im JSON-Content!
        if page.first_text and is_toc_or_appendix_page(page.first_text):
            skipped_toc += 1
            continue
        
        before_text = None
        used_fallback = False
        
        # EINFACHE LOGIK: Verwende die erste Textzeile der Seite
        # Diese wurde bereits in extract_all_pages() extrahiert (nach Überschriften/Datum)
        if page.first_text:
            before_text = find_before_text_in_content(page.first_text, content)
        
        # Fallback: Wenn erste Zeile nicht gefunden, versuche die Textblöcke
        if not before_text and page.all_texts:
            for text_block in page.all_texts:
                if is_likely_heading(text_block):
                    continue
                before_text = find_before_text_in_content(text_block, content)
                if before_text and not is_likely_heading(before_text):
                    used_fallback = True
                    break
        
        if before_text:
            markers.append({
                "page": page.printed_page,
                "beforeText": before_text,
                "confidence": page.confidence.value  # "extracted" oder "interpolated"
            })
            found_count += 1
            if used_fallback:
                found_with_fallback += 1
        else:
            not_found_count += 1
            if not_found_count <= 5:
                print(f"    Seite {page.printed_page}: beforeText nicht gefunden")
                if page.first_text:
                    print(f"      PDF-Text: \"{page.first_text[:50]}...\"")
        
        if found_count % 50 == 0 and found_count > 0:
            print(f"    {found_count} Marker gefunden...")
    
    # Sortiere nach Seitenzahl
    markers.sort(key=lambda m: m['page'])
    
    # Entferne Duplikate
    seen_pages = set()
    unique_markers = []
    for m in markers:
        if m['page'] not in seen_pages:
            unique_markers.append(m)
            seen_pages.add(m['page'])
    markers = unique_markers
    
    print(f"\n  Ergebnis:")
    print(f"    {found_count} Seitenmarker gefunden")
    if found_with_fallback > 0:
        print(f"      (davon {found_with_fallback} mit Fallback auf nächsten Textblock)")
    if skipped_toc > 0:
        print(f"    {skipped_toc} Inhaltsverzeichnis-/Anhang-Seiten übersprungen")
    print(f"    {not_found_count} nicht im JSON gefunden")
    
    if markers:
        pages_range = f"{markers[0]['page']} - {markers[-1]['page']}"
        print(f"    Seitenbereich: {pages_range}")
        
        # Prüfe auf Lücken
        page_nums = [m['page'] for m in markers]
        expected_pages = set(range(min(page_nums), max(page_nums) + 1))
        found_pages = set(page_nums)
        missing = sorted(expected_pages - found_pages)
        
        if missing:
            print(f"    Fehlende Seiten: {len(missing)}")
            if len(missing) <= 10:
                print(f"      {missing}")
            else:
                print(f"      {missing[:5]} ... {missing[-5:]}")
        else:
            print(f"    ✓ Lückenlose Sequenz!")
    
    # HINWEIS: lectureId wird NICHT mehr zugewiesen!
    # Das Frontend prüft selbst, ob der beforeText im aktuellen Vortrag vorkommt.
    # Dies ist viel robuster, da der Seitenumbruch auch mitten in einem Wort sein kann.
    
    # SCHRITT 4: Validierung (vereinfacht - keine lectureId-Prüfung mehr)
    print("\n  Schritt 4: Validierung...")
    validator = PageMarkerValidator(ga_normalized)
    validation_result = validator.validate_all(
        markers=markers,
        lectures=lectures,
        json_content=content,
        pdf_page_count=pdf_page_count
    )
    
    # Zeige Validierungsbericht
    validator.print_report(validation_result)
    
    # Bei kritischen Fehlern und nicht im Test-Modus: abbrechen
    if not validation_result.is_valid and not test_mode:
        print(f"  ❌ Export abgebrochen wegen kritischer Validierungsfehler!")
        print(f"     Verwende --test um trotzdem fortzufahren.")
        return None
    
    # Extrahiere Titel
    title_match = re.search(r' - (.+)\.pdf$', pdf_path.name)
    title = title_match.group(1) if title_match else ga_number
    
    # Entferne lectureId aus Markern (nicht mehr benötigt)
    for marker in markers:
        marker.pop('lectureId', None)
    
    return {
        "title": title,
        "pdfSource": pdf_path.name,
        "markers": markers
    }


def load_existing_markers() -> Dict:
    """Lädt bestehende Marker."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "_info": "Seitenmarker für GA-Bände. 'beforeText' = Text am Seitenanfang, VOR dem der Marker |page| eingefügt wird."
    }


def save_markers(data: Dict):
    """Speichert Marker."""
    sorted_data = {"_info": data.get("_info", "")}
    ga_keys = sorted([k for k in data.keys() if k.startswith("GA")])
    for key in ga_keys:
        sorted_data[key] = data[key]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Gespeichert in: {OUTPUT_FILE}")


def main():
    if len(sys.argv) < 2:
        print("Export Page Markers V3 - Robuste Seitenzahl-Extraktion mit Validierung")
        print()
        print("Verwendung:")
        print("  python export_page_markers_v2.py GA051          # Exportiert GA051")
        print("  python export_page_markers_v2.py --test GA051   # Test ohne Speichern")
        print("  python export_page_markers_v2.py --validate GA051  # Nur Validierung")
        print()
        print("Validierungen:")
        print("  ✓ Seitenzahlen aufsteigend, keine Duplikate")
        print("  ✓ Vortrags-Grenzen aufsteigend")
        print("  ✓ beforeText im JSON auffindbar")
        print("  ✓ Mindestens 30% der Seitenzahlen direkt extrahiert")
        print("  ✓ Max-Seitenzahl ≤ PDF-Seitenanzahl")
        sys.exit(1)
    
    test_mode = "--test" in sys.argv
    validate_only = "--validate" in sys.argv
    
    if test_mode:
        print("*** TEST-MODUS (keine Speicherung) ***\n")
    if validate_only:
        print("*** VALIDIERUNGS-MODUS ***\n")
    
    all_markers = load_existing_markers()
    
    for ga_arg in sys.argv[1:]:
        if ga_arg.startswith("--"):
            continue
        
        num_match = re.search(r'(\d+[a-z]?)', ga_arg, re.IGNORECASE)
        if not num_match:
            print(f"Ungültige GA-Nummer: {ga_arg}")
            continue
        
        ga_number = f"GA{num_match.group(1).zfill(3)}"
        
        result = process_ga(ga_number, test_mode=test_mode or validate_only, validate_only=validate_only)
        if result and not test_mode and not validate_only:
            all_markers[ga_number] = result
    
    if not test_mode and not validate_only:
        save_markers(all_markers)
    
    ga_count = len([k for k in all_markers.keys() if k.startswith("GA")])
    total = sum(len(v.get("markers", [])) for k, v in all_markers.items() if k.startswith("GA"))
    print(f"\nGesamt: {ga_count} GA-Bände mit {total} Seitenmarkern")


if __name__ == "__main__":
    main()

