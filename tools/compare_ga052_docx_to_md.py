#!/usr/bin/env python3
"""
Vergleicht DOCX-Vorlage mit MD-Dateien für GA052

Prüft, ob Textbereiche aus der DOCX-Datei in den einzelnen MD-Dateien fehlen.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

# Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from docx import Document
except ImportError:
    print("python-docx nicht installiert. Installieren mit: pip install python-docx")
    sys.exit(1)


def extract_text_from_docx(docx_path: Path) -> str:
    """Extrahiere Text aus DOCX-Datei."""
    doc = Document(docx_path)
    text_parts = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            text_parts.append(text)
    
    return '\n\n'.join(text_parts)


def normalize_text(text: str) -> str:
    """
    Normalisiere Text für Vergleich:
    - Entferne Seitenmarker |XX|
    - Entferne Block-IDs ^xyz
    - Entferne Markdown-Formatierung
    - Normalisiere Whitespace
    """
    # Entferne Seitenmarker
    text = re.sub(r'\|(\d+)\|', '', text)
    
    # Entferne Block-IDs
    text = re.sub(r'\s*\^[a-z0-9]+\s*', ' ', text)
    
    # Entferne Markdown-Formatierung
    text = re.sub(r'#{1,6}\s+', '', text)  # Überschriften
    text = re.sub(r'\[\[([^\]]+)\|([^\]]+)\]\]', r'\2', text)  # Links
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)  # Einfache Links
    
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def extract_lectures_from_reference_md(reference_md_path: Path) -> Dict[int, str]:
    """
    Extrahiere alle Vorträge aus der MD-Referenzdatei.
    
    Die Referenzdatei hat Struktur:
    - Inhaltsverzeichnis am Anfang
    - Vorträge mit "# TITEL" Überschriften
    - Einige Vorträge haben auch "## UNTERTITEL" (z.B. Vortrag 9, 10)
    - Vorträge sind durch "# TITEL" getrennt
    
    Rückgabe: Dict {index: text} für jeden Vortrag
    """
    content = reference_md_path.read_text(encoding='utf-8')
    lectures = {}
    
    # Suche nach Vortragsgrenzen: "# TITEL" (in Großbuchstaben)
    # Pattern: # TITEL IN GROSSBUCHSTABEN (möglicherweise mit Fragezeichen)
    lecture_pattern = r'^#\s+([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+?)(?:\?)?$'
    
    matches = list(re.finditer(lecture_pattern, content, re.MULTILINE))
    
    # Mappe Titel zu Indizes basierend auf bekannten Mustern
    title_to_index = {
        'DAS EWIGE UND DAS VERGÄNGLICHE DES MENSCHEN': 1,
        'DER URSPRUNG DER SEELE': 2,
        'DAS WESEN DER GOTTHEIT VOM THEOSOPHISCHEN STANDPUNKT': 3,
        'THEOSOPHIE UND CHRISTENTUM': 4,
        'DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE I': 5,
        'DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE II': 6,
        'DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE III': 7,
        'THEOSOPHISCHE SEELENLEHRE I KÖRPER UND SEELE': 8,
        'THEOSOPHISCHE SEELENLEHRE II': 9,
        'THEOSOPHISCHE SEELENLEHRE III': 10,
        'THEOSOPHIE UND SPIRITISMUS': 11,
        'THEOSOPHIE UND SOMNAMBULISMUS': 12,
        'DIE GESCHICHTE DES SPIRITISMUS': 13,
        'DIE GESCHICHTE DES HYPNOTISMUS UND DES SOMNAMBULISMUS': 14,
        'WAS FINDET DER HEUTIGE MENSCH IN DER THEOSOPHIE': 15,
        'WAS WISSEN UNSERE GELEHRTEN VON THEOSOPHIE': 16,
        'IST DIE THEOSOPHIE UNWISSENSCHAFTLICH': 17,
        'IST DIE THEOSOPHIE BUDDHISTISCHE PROPAGANDA': 18,
    }
    
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        title_normalized = re.sub(r'\s+', ' ', title.upper())
        
        # Finde Index durch Titel-Matching
        index = None
        for ref_title, idx in title_to_index.items():
            # Prüfe ob Titel übereinstimmt (erste 30 Zeichen oder vollständig)
            if title_normalized[:30] in ref_title or ref_title[:30] in title_normalized:
                index = idx
                break
        
        # Fallback: sequenziell basierend auf Position
        if index is None:
            index = i + 1
        
        # Finde Text bis zum nächsten Vortrag
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            # Suche nach "# HINWEISE" oder "# PERSONENREGISTER" als Ende
            hinweise_match = re.search(r'^#\s+HINWEISE', content[start_pos:], re.MULTILINE)
            if hinweise_match:
                end_pos = start_pos + hinweise_match.start()
            else:
                end_pos = len(content)
        
        lecture_text = content[start_pos:end_pos].strip()
        
        # Entferne Metadaten am Anfang (Copyright, etc.)
        lines = lecture_text.split('\n')
        content_start = 0
        for j, line in enumerate(lines):
            line_stripped = line.strip()
            # Überspringe leere Zeilen, Copyright-Zeilen
            if not line_stripped:
                continue
            if 'Copyright' in line_stripped or 'Seite:' in line_stripped:
                continue
            if line_stripped.startswith('---'):
                continue
            # Überspringe Datumszeilen (z.B. "Berlin, 6. September 1903")
            if re.match(r'^[A-Z][a-z]+,\s*\d+\.\s+[A-Z][a-z]+\s+\d{4}$', line_stripped):
                continue
            # Erster echter Text-Absatz
            if len(line_stripped) > 20 and not line_stripped.startswith('#'):
                content_start = j
                break
        
        lecture_text = '\n'.join(lines[content_start:]).strip()
        
        # Entferne Copyright-Zeilen und Trennlinien auch aus dem Text
        cleaned_lines = []
        for line in lecture_text.split('\n'):
            line_stripped = line.strip()
            if 'Copyright' in line_stripped or line_stripped == '---':
                continue
            cleaned_lines.append(line)
        
        lecture_text = '\n'.join(cleaned_lines).strip()
        lectures[index] = lecture_text
    
    return lectures


def extract_lectures_from_master_md(master_md_path: Path) -> Dict[int, str]:
    """
    Extrahiere alle Vorträge aus der großen MD-Datei.
    
    Rückgabe: Dict {index: text} für jeden Vortrag
    """
    content = master_md_path.read_text(encoding='utf-8')
    lectures = {}
    
    # Suche nach Vortragsgrenzen: "# TITEL, Ort, Datum"
    # Pattern: # TITEL IN GROSSBUCHSTABEN, Ort, Datum
    # Oder auch: # TITEL (ohne Komma nach Titel)
    lecture_pattern = r'^#\s+([A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+?)(?:,\s*([^,\n]+),\s*([^\n]+))?$'
    
    matches = list(re.finditer(lecture_pattern, content, re.MULTILINE))
    
    # Zuerst: Sammle alle Links im Inhaltsverzeichnis für Index-Mapping
    toc_links = {}
    toc_pattern = r'\[\[GA052\s*\((\d+)\.\)\s*([^\]]+)\]\]'
    for match in re.finditer(toc_pattern, content):
        index = int(match.group(1))
        title_part = match.group(2).strip()
        # Normalisiere Titel für Vergleich
        title_normalized = re.sub(r'\s+', ' ', title_part.upper())
        toc_links[index] = title_normalized
    
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        location = match.group(2).strip() if match.group(2) else ""
        date = match.group(3).strip() if match.group(3) else ""
        
        # Finde Index durch Vergleich mit TOC-Links
        title_normalized = re.sub(r'\s+', ' ', title.upper())
        index = None
        
        # Suche passenden Index im TOC
        for idx, toc_title in toc_links.items():
            # Prüfe ob Titel übereinstimmt (erste 30 Zeichen)
            if title_normalized[:30] in toc_title or toc_title[:30] in title_normalized:
                index = idx
                break
        
        # Fallback: Versuche Index aus vorherigem Link zu extrahieren
        if index is None:
            before_text = content[:match.start()]
            index_match = re.search(r'\[\[GA052\s*\((\d+)\.\)', before_text)
            if index_match:
                index = int(index_match.group(1))
            else:
                # Versuche sequenziell basierend auf Position
                index = i + 1
        
        # Finde Text bis zum nächsten Vortrag
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        lecture_text = content[start_pos:end_pos].strip()
        
        # Entferne Metadaten am Anfang (Quelle-Links, etc.)
        # Entferne alles bis zum ersten echten Absatz
        lines = lecture_text.split('\n')
        content_start = 0
        for j, line in enumerate(lines):
            line_stripped = line.strip()
            # Überspringe leere Zeilen, Links, Block-IDs
            if not line_stripped:
                continue
            if line_stripped.startswith('[[') or line_stripped.startswith('Quelle:'):
                continue
            if re.match(r'^\^[a-z0-9]+$', line_stripped):
                continue
            # Erster echter Text-Absatz
            if len(line_stripped) > 20 and not line_stripped.startswith('#'):
                content_start = j
                break
        
        lecture_text = '\n'.join(lines[content_start:]).strip()
        lectures[index] = lecture_text
    
    return lectures


def find_lecture_in_docx(docx_text: str, lecture_title: str, lecture_date: str) -> Optional[str]:
    """
    Finde den Text eines Vortrags in der DOCX-Datei.
    
    Sucht nach dem Titel und Datum und extrahiert den Text bis zum nächsten Vortrag.
    """
    # Normalisiere Titel und Datum für Suche
    title_pattern = re.escape(lecture_title)
    date_pattern = re.escape(lecture_date)
    
    # Suche nach Titel + Datum
    pattern = rf'{title_pattern}.*?{date_pattern}'
    match = re.search(pattern, docx_text, re.IGNORECASE | re.DOTALL)
    
    if not match:
        # Versuche nur mit Titel
        pattern = re.escape(lecture_title[:50])  # Erste 50 Zeichen
        match = re.search(pattern, docx_text, re.IGNORECASE)
    
    if not match:
        return None
    
    start_pos = match.start()
    
    # Finde das Ende: nächster Vortragstitel oder Ende des Dokuments
    # Suche nach Mustern wie "(1.)", "(2.)", etc. oder großen Überschriften
    next_lecture_pattern = r'\((\d+)\.\)\s+[A-ZÄÖÜ][A-ZÄÖÜ\s\-\?!«»]+'
    next_match = re.search(next_lecture_pattern, docx_text[start_pos + 100:], re.MULTILINE)
    
    if next_match:
        end_pos = start_pos + 100 + next_match.start()
    else:
        end_pos = len(docx_text)
    
    return docx_text[start_pos:end_pos].strip()


def extract_lecture_metadata_from_md(md_path: Path) -> Optional[Dict]:
    """Extrahiere Titel und Datum aus MD-Dateinamen oder Inhalt."""
    filename = md_path.name
    
    # Versuche aus Dateinamen zu extrahieren: "GA052 (1.) TITEL, Ort, Datum.md"
    match = re.match(r'GA052\s*\((\d+)\.\)\s*(.+?),\s*([^,]+),\s*(.+?)\.md', filename)
    if match:
        index = int(match.group(1))
        title = match.group(2).strip()
        location = match.group(3).strip()
        date = match.group(4).strip()
        return {
            'index': index,
            'title': title,
            'location': location,
            'date': f"{location}, {date}"
        }
    
    return None


def compare_texts(docx_text: str, md_text: str, lecture_title: str) -> Dict:
    """
    Vergleiche DOCX-Text mit MD-Text und finde fehlende Bereiche.
    
    Rückgabe: Dict mit Statistiken und fehlenden Textbereichen
    """
    docx_normalized = normalize_text(docx_text)
    md_normalized = normalize_text(md_text)
    
    # Verwende SequenceMatcher für Vergleich
    matcher = SequenceMatcher(None, docx_normalized, md_normalized)
    similarity = matcher.ratio()
    
    # Finde fehlende Bereiche
    missing_segments = []
    
    # Teile DOCX-Text in Absätze
    docx_paragraphs = [p.strip() for p in docx_normalized.split('\n\n') if p.strip()]
    
    for para in docx_paragraphs:
        if len(para) < 20:  # Zu kurz, ignoriere
            continue
        
        # Suche diesen Absatz im MD-Text
        para_normalized = normalize_text(para)
        
        # Prüfe, ob Absatz im MD-Text vorkommt
        if para_normalized not in md_normalized:
            # Versuche Teilübereinstimmung (erste 50 Zeichen)
            para_start = para_normalized[:100]
            if para_start not in md_normalized:
                missing_segments.append({
                    'text': para[:200] + '...' if len(para) > 200 else para,
                    'length': len(para)
                })
    
    return {
        'similarity': similarity,
        'docx_length': len(docx_normalized),
        'md_length': len(md_normalized),
        'length_diff': len(docx_normalized) - len(md_normalized),
        'missing_segments': missing_segments,
        'missing_segments_count': len(missing_segments)
    }


def process_ga052_comparison(docx_path: Path, md_dir: Path, master_md_path: Path = None, reference_md_path: Path = None) -> Dict:
    """
    Hauptfunktion: Vergleiche alle MD-Dateien mit Referenz.
    
    Priorität:
    1. reference_md_path (MD-Referenzdatei)
    2. master_md_path (Master-MD)
    3. docx_path (DOCX)
    """
    print(f"\n{'='*70}")
    print(f"GA052 Vergleich: Referenz vs. MD-Dateien")
    print(f"{'='*70}")
    
    # Verwende Referenz-MD als erste Priorität
    if reference_md_path and reference_md_path.exists():
        print(f"Referenz: MD-Referenzdatei ({reference_md_path.name})")
        print("1. Lade MD-Referenzdatei und extrahiere Vorträge...")
        reference_lectures = extract_lectures_from_reference_md(reference_md_path)
        print(f"   {len(reference_lectures)} Vorträge in Referenz-MD gefunden")
        use_docx = False
        use_master = False
    elif master_md_path and master_md_path.exists():
        print(f"Referenz: Master-MD ({master_md_path.name})")
        print("1. Lade Master-MD und extrahiere Vorträge...")
        reference_lectures = extract_lectures_from_master_md(master_md_path)
        print(f"   {len(reference_lectures)} Vorträge in Master-MD gefunden")
        use_docx = False
        use_master = True
    else:
        print(f"Referenz: DOCX ({docx_path.name})")
        print("1. Lade DOCX-Datei...")
        docx_text = extract_text_from_docx(docx_path)
        print(f"   DOCX-Text: {len(docx_text):,} Zeichen")
        use_docx = True
        use_master = False
    
    # Finde alle MD-Dateien
    print("\n2. Finde MD-Dateien...")
    md_files = sorted(md_dir.glob("GA052 (*.md"))
    md_files = [f for f in md_files if not f.name.endswith('_backup.md')]
    print(f"   {len(md_files)} MD-Dateien gefunden")
    
    results = []
    
    # Verarbeite jede MD-Datei
    print("\n3. Vergleiche Dateien...")
    print()
    
    for md_file in md_files:
        metadata = extract_lecture_metadata_from_md(md_file)
        if not metadata:
            print(f"   ⚠️  {md_file.name}: Metadaten nicht extrahiert")
            continue
        
        print(f"   [{metadata['index']}] {metadata['title'][:50]}...")
        
        # Lade MD-Text
        md_content = md_file.read_text(encoding='utf-8')
        
        # Finde Vortrag in Referenz
        if use_docx:
            reference_text = find_lecture_in_docx(
                docx_text, 
                metadata['title'], 
                metadata['date']
            )
        else:
            reference_text = reference_lectures.get(metadata['index'])
        
        if not reference_text:
            print(f"      ⚠️  Vortrag nicht in Referenz gefunden!")
            results.append({
                'file': md_file.name,
                'metadata': metadata,
                'status': 'not_found_in_reference',
                'comparison': None
            })
            continue
        
        # Vergleiche
        comparison = compare_texts(reference_text, md_content, metadata['title'])
        
        status = 'ok'
        if comparison['similarity'] < 0.95:
            status = 'low_similarity'
        if comparison['missing_segments_count'] > 0:
            status = 'missing_segments'
        
        print(f"      Ähnlichkeit: {comparison['similarity']:.1%}")
        print(f"      DOCX: {comparison['docx_length']:,} Zeichen")
        print(f"      MD: {comparison['md_length']:,} Zeichen")
        print(f"      Differenz: {comparison['length_diff']:+,} Zeichen")
        
        if comparison['missing_segments_count'] > 0:
            print(f"      ⚠️  {comparison['missing_segments_count']} mögliche fehlende Absätze")
            for i, seg in enumerate(comparison['missing_segments'][:3], 1):
                print(f"         {i}. {seg['text'][:80]}...")
        
        results.append({
            'file': md_file.name,
            'metadata': metadata,
            'status': status,
            'comparison': comparison
        })
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print("Zusammenfassung:")
    print(f"{'='*70}")
    
    ok_count = sum(1 for r in results if r['status'] == 'ok')
    low_sim_count = sum(1 for r in results if r['status'] == 'low_similarity')
    missing_count = sum(1 for r in results if r['status'] == 'missing_segments')
    not_found_count = sum(1 for r in results if r['status'] == 'not_found_in_reference')
    
    print(f"  OK: {ok_count}")
    print(f"  Niedrige Ähnlichkeit: {low_sim_count}")
    print(f"  Fehlende Absätze: {missing_count}")
    print(f"  Nicht in DOCX gefunden: {not_found_count}")
    
    # Detaillierte Liste der Probleme
    if missing_count > 0 or low_sim_count > 0:
        print(f"\n  Detaillierte Probleme:")
        for r in results:
            if r['status'] in ['missing_segments', 'low_similarity']:
                comp = r['comparison']
                print(f"    - {r['file']}")
                print(f"      Ähnlichkeit: {comp['similarity']:.1%}")
                if comp['missing_segments_count'] > 0:
                    print(f"      Fehlende Absätze: {comp['missing_segments_count']}")
    
    return {
        'results': results,
        'summary': {
            'total': len(results),
            'ok': ok_count,
            'low_similarity': low_sim_count,
            'missing_segments': missing_count,
            'not_found': not_found_count
        }
    }


def main():
    md_dir = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA052-Spirituelle Seelenlehre und Weltbetrachtung")
    docx_path = md_dir / "Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung.docx"
    master_md_path = md_dir / "GA052 - Spirituelle Seelenlehre und Weltbetrachtung (1903-1904).md"
    reference_md_path = md_dir / "Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung.md"
    
    if not md_dir.exists():
        print(f"FEHLER: MD-Verzeichnis nicht gefunden: {md_dir}")
        sys.exit(1)
    
    # Priorität: reference_md_path > master_md_path > docx_path
    if not reference_md_path.exists() and not master_md_path.exists() and not docx_path.exists():
        print(f"FEHLER: Keine Referenzdatei gefunden!")
        sys.exit(1)
    
    result = process_ga052_comparison(docx_path, md_dir, master_md_path, reference_md_path)
    
    # Speichere Ergebnis als JSON
    output_json = md_dir / "ga052_comparison_results.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nErgebnis gespeichert: {output_json}")


if __name__ == '__main__':
    main()
