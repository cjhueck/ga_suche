#!/usr/bin/env python3
"""
Automatisches Einfügen von Seitenzahlen in Markdown-Dateien basierend auf Text-Ähnlichkeit.

Dieses Skript verwendet Text-Ähnlichkeits-Algorithmen statt Claude API, um die Positionen zu finden.
"""

import re
import os
import sys
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from difflib import SequenceMatcher

try:
    from dotenv import load_dotenv
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass


def normalize_text(text: str) -> str:
    """Normalisiert Text für Vergleich (entfernt Sonderzeichen, normalisiert Leerzeichen)."""
    # Entferne Markdown-Marker
    text = re.sub(r'\^[a-z0-9]+', '', text)  # Entferne Marker wie ^k804ca
    text = re.sub(r'\[.*?\]', '', text)  # Entferne Markdown-Links
    text = re.sub(r'#+\s*', '', text)  # Entferne Überschriften-Marker
    # Normalisiere Leerzeichen
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text.lower()


def text_similarity(text1: str, text2: str) -> float:
    """Berechnet Ähnlichkeit zwischen zwei Texten (0-1)."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_best_match_position(
    target_text: List[str],
    search_text: str,
    start_pos: int = 0,
    window_size: int = 50
) -> Optional[int]:
    """
    Findet die beste Position in target_text, die zu search_text passt.
    
    Args:
        target_text: Liste von Textzeilen
        search_text: Text, der gefunden werden soll
        start_pos: Startposition für die Suche
        window_size: Größe des Suchfensters
        
    Returns:
        Beste Position oder None
    """
    search_normalized = normalize_text(search_text)
    best_match = None
    best_score = 0.0
    best_pos = None
    
    # Suche in einem Fenster um start_pos
    search_start = max(0, start_pos - window_size)
    search_end = min(len(target_text), start_pos + window_size)
    
    # Vergleiche verschiedene Fenstergrößen
    for window in [5, 10, 15, 20, 30]:
        for i in range(search_start, max(search_start, search_end - window)):
            window_text = ' '.join(target_text[i:i+window])
            window_normalized = normalize_text(window_text)
            
            # Berechne Ähnlichkeit - verwende sowohl vollständige als auch Teil-Übereinstimmungen
            full_similarity = SequenceMatcher(None, search_normalized, window_normalized).ratio()
            
            # Zusätzlich: Prüfe, ob wichtige Wörter übereinstimmen
            search_words = set(search_normalized.split())
            window_words = set(window_normalized.split())
            common_words = search_words & window_words
            word_overlap = len(common_words) / max(len(search_words), 1) if search_words else 0
            
            # Kombiniere beide Metriken
            combined_score = (full_similarity * 0.7) + (word_overlap * 0.3)
            
            if combined_score > best_score:
                best_score = combined_score
                best_pos = i + window - 1  # Ende des Fensters
                best_match = window_text[:100]  # Für Debugging
    
    # Nur zurückgeben, wenn Ähnlichkeit hoch genug ist
    # Niedrigere Schwelle, da OCR-Text und bereinigter Text unterschiedlich sein können
    if best_score > 0.25:  # Mindest-Ähnlichkeit von 25%
        return best_pos
    
    return None


class PageNumberInserterV2:
    def __init__(self):
        """Initialisiert den PageNumberInserter."""
        pass
        
    def extract_page_numbers_from_ocr(self, ocr_file_path: str) -> List[Tuple[int, int]]:
        """
        Extrahiert Seitenzahlen aus der OCR-MD-Datei.
        
        Returns:
            Liste von Tupeln (Zeilenindex, Seitenzahl)
        """
        with open(ocr_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        page_markers = []
        
        for i, line in enumerate(lines):
            # Suche nach Copyright-Zeilen mit Seitenzahlen
            match = re.search(r'Copyright Rudolf Steiner Nachlass-Verwaltung Buch: \d+ Seite: (\d+)', line, re.IGNORECASE)
            if match:
                page_num = int(match.group(1))
                page_markers.append((i, page_num))
        
        return page_markers
    
    def get_text_before_marker(self, lines: List[str], marker_line_idx: int, context_lines: int = 15) -> str:
        """Extrahiert Text vor einem Marker."""
        start = max(0, marker_line_idx - context_lines)
        end = marker_line_idx
        text_lines = lines[start:end]
        # Entferne leere Zeilen, Copyright-Zeilen und Markdown-Marker
        filtered = []
        for line in text_lines:
            line_stripped = line.strip()
            if (line_stripped and 
                not re.search(r'Copyright Rudolf Steiner', line_stripped, re.IGNORECASE) and
                not re.search(r'^---$', line_stripped) and
                not re.search(r'^#+\s*', line_stripped)):  # Keine Überschriften
                # Entferne Marker wie ^k804ca
                line_stripped = re.sub(r'\s*\^[a-z0-9]+\s*', ' ', line_stripped)
                filtered.append(line_stripped)
        # Verwende mehr Zeilen für besseren Kontext
        return ' '.join(filtered[-15:])  # Letzte 15 nicht-leere Zeilen
    
    def extrapolate_missing_pages(self, page_markers: List[Tuple[int, int]], total_lines: int) -> Dict[int, int]:
        """
        Extrapoliert fehlende Seitenzahlen zwischen vorhandenen Markern.
        """
        page_map = {}
        
        if not page_markers:
            return page_map
        
        sorted_markers = sorted(page_markers, key=lambda x: x[0])
        
        # Füge erste Seite hinzu
        first_line, first_page = sorted_markers[0]
        page_map[first_line] = first_page
        
        # Interpoliere zwischen vorhandenen Markern
        for i in range(len(sorted_markers) - 1):
            start_line, start_page = sorted_markers[i]
            end_line, end_page = sorted_markers[i + 1]
            
            line_diff = end_line - start_line
            page_diff = end_page - start_page
            
            if line_diff > 0 and page_diff > 0:
                # Lineare Interpolation
                for j in range(start_line + 1, end_line):
                    estimated_page = start_page + int((j - start_line) * page_diff / line_diff)
                    if estimated_page <= start_page + page_diff:
                        page_map[j] = estimated_page
            
            page_map[end_line] = end_page
        
        return page_map
    
    def find_page_position(
        self,
        target_md_lines: List[str],
        ocr_text_before_marker: str,
        page_number: int,
        approximate_position: Optional[int] = None
    ) -> Optional[int]:
        """
        Findet Position in Ziel-MD-Datei basierend auf Text-Ähnlichkeit.
        """
        if approximate_position is None:
            # Schätze Position basierend auf Seitenzahl
            # Annahme: ~50 Zeilen pro Seite
            approximate_position = page_number * 50
        
        # Finde beste Übereinstimmung
        position = find_best_match_position(
            target_md_lines,
            ocr_text_before_marker,
            approximate_position,
            window_size=100
        )
        
        return position
    
    def insert_page_number(self, lines: List[str], position: int, page_number: int) -> List[str]:
        """Fügt eine Seitenzahl an der angegebenen Position ein."""
        new_lines = lines.copy()
        
        # Prüfe, ob bereits eine Seitenzahl vorhanden ist
        if position < len(new_lines):
            current_line = new_lines[position].strip()
            next_line = new_lines[position + 1].strip() if position + 1 < len(new_lines) else ""
            
            if re.search(r'\[Seite:\s*\d+\]', current_line) or re.search(r'\[Seite:\s*\d+\]', next_line):
                return new_lines
        
        marker = f"[Seite: {page_number}]"
        new_lines.insert(position + 1, marker)
        new_lines.insert(position + 2, "")
        
        return new_lines
    
    def process_files(
        self,
        ocr_file_path: str,
        target_file_path: str,
        output_file_path: Optional[str] = None,
        max_pages: Optional[int] = None
    ):
        """Hauptfunktion: Verarbeitet die Dateien und fügt Seitenzahlen ein."""
        print(f"Lese OCR-Datei: {ocr_file_path}")
        with open(ocr_file_path, 'r', encoding='utf-8') as f:
            ocr_lines = [line.rstrip('\n\r') for line in f.readlines()]
        
        print(f"Lese Ziel-MD-Datei: {target_file_path}")
        with open(target_file_path, 'r', encoding='utf-8') as f:
            target_lines = [line.rstrip('\n\r') for line in f.readlines()]
        
        # Extrahiere Seitenzahlen
        print("Extrahiere Seitenzahlen aus OCR-Datei...")
        page_markers = self.extract_page_numbers_from_ocr(ocr_file_path)
        print(f"Gefunden: {len(page_markers)} Seitenmarker")
        
        if not page_markers:
            print("Keine Seitenmarker gefunden!")
            return
        
        # Extrapoliere fehlende Seitenzahlen
        print("Extrapoliere fehlende Seitenzahlen...")
        page_map = self.extrapolate_missing_pages(page_markers, len(ocr_lines))
        
        # Sortiere nach Seitenzahl
        sorted_pages = sorted(set(page_map.values()))
        if max_pages:
            sorted_pages = sorted_pages[:max_pages]
        
        print(f"Verarbeite {len(sorted_pages)} Seitenzahlen...")
        
        insertions = []
        
        for page_num in sorted_pages:
            # Finde OCR-Positionen mit dieser Seitenzahl
            ocr_positions = [line_idx for line_idx, p in page_map.items() if p == page_num]
            if not ocr_positions:
                continue
            
            ocr_line_idx = min(ocr_positions)
            
            # Hole Text vor dem Marker
            ocr_text = self.get_text_before_marker(ocr_lines, ocr_line_idx, context_lines=20)
            
            # Schätze Position
            estimated_pos = int((ocr_line_idx / len(ocr_lines)) * len(target_lines))
            
            # Finde Position
            print(f"Suche Position für Seite {page_num}...", end=" ")
            target_position = self.find_page_position(
                target_lines,
                ocr_text,
                page_num,
                estimated_pos
            )
            
            if target_position is not None:
                insertions.append((target_position, page_num))
                print(f"Position {target_position} gefunden")
            else:
                print("Position nicht gefunden (übersprungen)")
        
        # Sortiere Einfügungen rückwärts
        insertions.sort(key=lambda x: x[0], reverse=True)
        
        # Entferne Duplikate
        seen_positions = set()
        unique_insertions = []
        for pos, page_num in insertions:
            if pos not in seen_positions:
                seen_positions.add(pos)
                unique_insertions.append((pos, page_num))
        insertions = unique_insertions
        
        # Füge Seitenzahlen ein
        print(f"\nFüge {len(insertions)} Seitenzahlen ein...")
        result_lines = target_lines.copy()
        
        for position, page_num in insertions:
            result_lines = self.insert_page_number(result_lines, position, page_num)
        
        # Speichere Ergebnis
        output_path = output_file_path or target_file_path
        print(f"Speichere Ergebnis in: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result_lines))
            f.write('\n')
        
        print(f"\nFertig! {len(insertions)} Seitenzahlen eingefügt.")


def main():
    """Hauptfunktion für Kommandozeilen-Nutzung."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fügt automatisch Seitenzahlen in Markdown-Dateien ein (Text-Ähnlichkeits-basiert)"
    )
    parser.add_argument("ocr_file", help="Pfad zur OCR-MD-Datei")
    parser.add_argument("target_file", help="Pfad zur Ziel-MD-Datei")
    parser.add_argument("-o", "--output", help="Ausgabedatei (optional)")
    parser.add_argument("--max-pages", type=int, help="Maximale Anzahl von Seitenzahlen (für Tests)")
    
    args = parser.parse_args()
    
    try:
        inserter = PageNumberInserterV2()
        inserter.process_files(
            args.ocr_file,
            args.target_file,
            args.output,
            args.max_pages
        )
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

