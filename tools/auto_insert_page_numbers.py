#!/usr/bin/env python3
"""
Automatisches Einfügen von Seitenzahlen in Markdown-Dateien mit Hilfe von Claude API.

Dieses Skript:
1. Liest die OCR-MD-Datei und extrahiert Seitenzahlen aus Copyright-Zeilen
2. Extrapoliert fehlende Seitenzahlen
3. Verwendet Claude API, um die Positionen in der Ziel-MD-Datei zu finden
4. Fügt die Seitenzahlen an den richtigen Positionen ein
"""

import re
import os
import json
import sys
from typing import List, Tuple, Optional, Dict
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Fehler: anthropic-Bibliothek nicht gefunden.")
    print("Bitte installieren Sie sie mit: pip install anthropic")
    sys.exit(1)

# Versuche python-dotenv zu importieren (optional)
try:
    from dotenv import load_dotenv
    # Lade .env-Datei aus dem Projekt-Root (ein Verzeichnis höher)
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    env_path = project_root / '.env'
    
    # Versuche verschiedene Pfade
    if env_path.exists():
        load_dotenv(env_path, override=True)
    elif (script_dir / '.env').exists():
        load_dotenv(script_dir / '.env', override=True)
    else:
        load_dotenv()  # Versuche auch im aktuellen Verzeichnis
except ImportError:
    pass  # python-dotenv ist optional


class PageNumberInserter:
    def __init__(self, api_key: Optional[str] = None):
        """Initialisiert den PageNumberInserter mit Claude API."""
        # Versuche .env-Datei zu laden falls noch nicht geschehen
        try:
            from dotenv import load_dotenv
            script_dir = Path(__file__).parent.absolute()
            project_root = script_dir.parent
            env_path = project_root / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=True)
        except ImportError:
            pass
        
        # Versuche verschiedene Variablennamen
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY") or os.getenv("CLAUDE_API_KEY_Jan26")
        
        if not self.api_key:
            # Debug-Info
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                print(f"Warnung: .env-Datei gefunden unter {env_path}, aber ANTHROPIC_API_KEY nicht gefunden.")
                print("Bitte überprüfen Sie, ob die Variable in der .env-Datei als ANTHROPIC_API_KEY=... gesetzt ist.")
            raise ValueError(
                "ANTHROPIC_API_KEY Umgebungsvariable nicht gesetzt oder kein API-Key übergeben.\n"
                "Bitte setzen Sie ANTHROPIC_API_KEY in der .env-Datei oder als Umgebungsvariable."
            )
        self.client = Anthropic(api_key=self.api_key)
        
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
    
    def extrapolate_missing_pages(self, page_markers: List[Tuple[int, int]], total_lines: int) -> Dict[int, int]:
        """
        Extrapoliert fehlende Seitenzahlen zwischen vorhandenen Markern.
        
        Args:
            page_markers: Liste von (Zeilenindex, Seitenzahl)
            total_lines: Gesamtanzahl der Zeilen in der OCR-Datei
            
        Returns:
            Dictionary: Zeilenindex -> Seitenzahl
        """
        page_map = {}
        
        if not page_markers:
            return page_map
        
        # Sortiere nach Zeilenindex
        sorted_markers = sorted(page_markers, key=lambda x: x[0])
        
        # Füge erste Seite hinzu
        first_line, first_page = sorted_markers[0]
        page_map[first_line] = first_page
        
        # Interpoliere zwischen vorhandenen Markern
        for i in range(len(sorted_markers) - 1):
            start_line, start_page = sorted_markers[i]
            end_line, end_page = sorted_markers[i + 1]
            
            # Berechne Seitenzahl für jede Zeile zwischen den Markern
            line_diff = end_line - start_line
            page_diff = end_page - start_page
            
            if line_diff > 0 and page_diff > 0:
                # Lineare Interpolation
                for j in range(start_line + 1, end_line):
                    # Schätze Seitenzahl basierend auf Position
                    estimated_page = start_page + int((j - start_line) * page_diff / line_diff)
                    # Nur wenn es sinnvoll ist (nicht zu viele Seiten pro Zeile)
                    if estimated_page <= start_page + page_diff:
                        page_map[j] = estimated_page
            
            page_map[end_line] = end_page
        
        # Extrapoliere nach dem letzten Marker
        if sorted_markers:
            last_line, last_page = sorted_markers[-1]
            # Schätze, dass jede ~50 Zeilen eine neue Seite ist (kann angepasst werden)
            lines_per_page = 50
            for j in range(last_line + 1, min(last_line + 100, total_lines)):
                estimated_page = last_page + ((j - last_line) // lines_per_page)
                if estimated_page > last_page:
                    page_map[j] = estimated_page
        
        return page_map
    
    def find_text_context(self, lines: List[str], line_idx: int, context_size: int = 5) -> str:
        """Extrahiert Kontext um eine Zeile herum."""
        start = max(0, line_idx - context_size)
        end = min(len(lines), line_idx + context_size + 1)
        context_lines = lines[start:end]
        return '\n'.join(context_lines)
    
    def _find_available_model(self) -> Optional[str]:
        """Findet ein verfügbares Claude-Modell durch Testaufruf."""
        models_to_try = [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229", 
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        
        for model_name in models_to_try:
            try:
                # Teste das Modell mit einem kurzen Aufruf
                self.client.messages.create(
                    model=model_name,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "test"}]
                )
                return model_name
            except Exception:
                continue
        
        return None
    
    def find_page_position_with_claude(
        self, 
        target_md_lines: List[str],
        ocr_context: str,
        page_number: int,
        approximate_position: Optional[int] = None
    ) -> Optional[int]:
        """
        Verwendet Claude API, um die Position in der Ziel-MD-Datei zu finden,
        wo die Seitenzahl eingefügt werden soll.
        
        Args:
            target_md_lines: Zeilen der Ziel-MD-Datei
            ocr_context: Text-Kontext aus der OCR-Datei um die Seitenzahl
            page_number: Die Seitenzahl, die eingefügt werden soll
            approximate_position: Ungefähre Position (Zeilenindex)
            
        Returns:
            Zeilenindex, wo die Seitenzahl eingefügt werden soll, oder None
        """
        # Bereite Kontext aus Ziel-MD vor
        if approximate_position is not None:
            target_start = max(0, approximate_position - 20)
            target_end = min(len(target_md_lines), approximate_position + 20)
            target_context = '\n'.join(target_md_lines[target_start:target_end])
        else:
            # Wenn keine ungefähre Position, verwende gesamten Text (kürzen wenn zu lang)
            max_lines = 100
            if len(target_md_lines) > max_lines:
                target_context = '\n'.join(target_md_lines[:max_lines]) + '\n...'
            else:
                target_context = '\n'.join(target_md_lines)
        
        prompt = f"""Du bist ein Experte für Text-Alignment zwischen OCR-Texten und bereinigten Markdown-Dateien.

Aufgabe: Finde die exakte Position in der Ziel-MD-Datei, wo die Seitenzahl {page_number} eingefügt werden soll.

OCR-Kontext (mit Seitenzahl {page_number}):
```
{ocr_context}
```

Ziel-MD-Kontext:
```
{target_context}
```

Die Seitenzahl sollte genau dort eingefügt werden, wo der entsprechende Text endet, der in der OCR-Datei vor der Copyright-Zeile mit Seite {page_number} steht.

Antworte NUR mit der Zeilennummer (0-basiert) in der Ziel-MD-Datei, wo die Seitenzahl eingefügt werden soll. Wenn du die Position nicht sicher finden kannst, antworte mit "UNKNOWN".

Antwort (nur Zahl oder "UNKNOWN"):"""

        try:
            # Finde verfügbares Modell (cache es für bessere Performance)
            if not hasattr(self, '_cached_model'):
                print("Suche verfügbares Claude-Modell...")
                self._cached_model = self._find_available_model()
                if self._cached_model:
                    print(f"Verwende Modell: {self._cached_model}")
                else:
                    print("Warnung: Kein verfügbares Claude-Modell gefunden!")
                    return None
            
            if not self._cached_model:
                return None
            
            message = self.client.messages.create(
                model=self._cached_model,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response = message.content[0].text.strip()
            
            # Versuche, die Zeilennummer zu extrahieren
            if response == "UNKNOWN":
                return None
            
            # Entferne eventuelle Erklärungen, behalte nur die Zahl
            match = re.search(r'\d+', response)
            if match:
                line_num = int(match.group(0))
                # Stelle sicher, dass die Zeilennummer im gültigen Bereich liegt
                if 0 <= line_num < len(target_md_lines):
                    return line_num
            
            return None
            
        except Exception as e:
            print(f"Fehler bei Claude API-Aufruf: {e}")
            return None
    
    def insert_page_number(self, lines: List[str], position: int, page_number: int) -> List[str]:
        """
        Fügt eine Seitenzahl an der angegebenen Position ein.
        
        Format: [Seite: {page_number}]
        Prüft, ob bereits eine Seitenzahl an dieser Position existiert.
        """
        new_lines = lines.copy()
        
        # Prüfe, ob bereits eine Seitenzahl an dieser Position existiert
        if position < len(new_lines):
            # Prüfe die aktuelle und nächste Zeile
            current_line = new_lines[position].strip()
            next_line = new_lines[position + 1].strip() if position + 1 < len(new_lines) else ""
            
            # Wenn bereits eine Seitenzahl vorhanden ist, überspringe
            if re.search(r'\[Seite:\s*\d+\]', current_line) or re.search(r'\[Seite:\s*\d+\]', next_line):
                return new_lines
        
        # Füge Seitenzahl-Marker ein
        marker = f"[Seite: {page_number}]"
        
        # Füge nach der angegebenen Zeile ein
        new_lines.insert(position + 1, marker)
        new_lines.insert(position + 2, "")  # Leerzeile danach
        
        return new_lines
    
    def process_files(
        self,
        ocr_file_path: str,
        target_file_path: str,
        output_file_path: Optional[str] = None,
        max_pages: Optional[int] = None
    ):
        """
        Hauptfunktion: Verarbeitet die Dateien und fügt Seitenzahlen ein.
        
        Args:
            ocr_file_path: Pfad zur OCR-MD-Datei
            target_file_path: Pfad zur Ziel-MD-Datei
            output_file_path: Pfad zur Ausgabedatei (optional, überschreibt target_file_path wenn None)
            max_pages: Maximale Anzahl von Seitenzahlen, die eingefügt werden sollen (für Tests)
        """
        print(f"Lese OCR-Datei: {ocr_file_path}")
        with open(ocr_file_path, 'r', encoding='utf-8') as f:
            ocr_lines = f.readlines()
        
        print(f"Lese Ziel-MD-Datei: {target_file_path}")
        with open(target_file_path, 'r', encoding='utf-8') as f:
            target_lines = f.readlines()
        
        # Entferne Zeilenumbrüche am Ende für bessere Verarbeitung
        ocr_lines = [line.rstrip('\n\r') for line in ocr_lines]
        target_lines = [line.rstrip('\n\r') for line in target_lines]
        
        # Extrahiere Seitenzahlen aus OCR
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
        
        # Sammle alle Positionen, die eingefügt werden sollen
        insertions = []  # Liste von (position, page_number)
        
        for page_num in sorted_pages:
            # Finde alle Zeilen in OCR mit dieser Seitenzahl
            ocr_positions = [line_idx for line_idx, p in page_map.items() if p == page_num]
            if not ocr_positions:
                continue
            
            # Verwende die erste Position (vor dem Copyright-Marker)
            ocr_line_idx = min(ocr_positions)
            
            # Hole Kontext aus OCR
            ocr_context = self.find_text_context(ocr_lines, ocr_line_idx, context_size=10)
            
            # Schätze ungefähre Position in Ziel-MD (basierend auf Zeilenverhältnis)
            estimated_pos = int((ocr_line_idx / len(ocr_lines)) * len(target_lines))
            
            # Verwende Claude, um exakte Position zu finden
            print(f"Suche Position für Seite {page_num}...")
            target_position = self.find_page_position_with_claude(
                target_lines,
                ocr_context,
                page_num,
                estimated_pos
            )
            
            if target_position is not None:
                insertions.append((target_position, page_num))
                print(f"  Seite {page_num}: Position {target_position} gefunden")
            else:
                print(f"  Seite {page_num}: Position nicht gefunden (übersprungen)")
        
        # Entferne Duplikate (gleiche Position)
        seen_positions = set()
        unique_insertions = []
        for pos, page_num in insertions:
            if pos not in seen_positions:
                seen_positions.add(pos)
                unique_insertions.append((pos, page_num))
        insertions = unique_insertions
        
        # Sortiere Einfügungen nach Position (rückwärts, damit Indizes nicht verschoben werden)
        insertions.sort(key=lambda x: x[0], reverse=True)
        
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
        description="Fügt automatisch Seitenzahlen in Markdown-Dateien ein mit Hilfe von Claude API"
    )
    parser.add_argument(
        "ocr_file",
        help="Pfad zur OCR-MD-Datei (mit Copyright-Zeilen und Seitenzahlen)"
    )
    parser.add_argument(
        "target_file",
        help="Pfad zur Ziel-MD-Datei (in die Seitenzahlen eingefügt werden sollen)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Ausgabedatei (optional, überschreibt target_file wenn nicht angegeben)"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API Key (optional, kann auch über ANTHROPIC_API_KEY Umgebungsvariable gesetzt werden)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximale Anzahl von Seitenzahlen zum Einfügen (für Tests)"
    )
    
    args = parser.parse_args()
    
    try:
        inserter = PageNumberInserter(api_key=args.api_key)
        inserter.process_files(
            args.ocr_file,
            args.target_file,
            args.output,
            args.max_pages
        )
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

