# Datenverarbeitung – Skript-Dokumentation

Diese Dokumentation beschreibt die Python-Skripte zur Verarbeitung der GA-Daten, insbesondere zur Generierung von Seitenzahlen (Page Breaks).

---

## Übersicht der Skripte

| Skript | Funktion |
|--------|----------|
| `export_page_markers_v4.py` | Extrahiert Seitenumbruch-Marker aus PDF-Dateien |
| `apply_page_break_markers_v4.py` | Fügt die Marker in die JSON-Vortrags-/Buchdaten ein |
| `batch_generate_pagebreaks.py` | Batch-Verarbeitung: Führt beide Skripte für mehrere GA-Bände aus |
| `generate_lecture_page_mapping.py` | Erstellt Mapping: Vortrag-ID → Start-Seitenzahl |

---

## 1. export_page_markers_v4.py

### Zweck
Extrahiert Seitenumbruch-Informationen aus PDF-Dateien der Gesamtausgabe und speichert sie als "Break Anchors" für spätere Zuordnung zum JSON-Text.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` | Die gescannten/digitalisierten GA-Bände |
| Bestehende Marker | `page-break-markers.json` | Wird geladen und erweitert (falls vorhanden) |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: PDF laden
```
find_pdf_for_ga("GA198")
  → Sucht in Steiner_GA_pdf/ nach "ga 198" oder "ga198" im Dateinamen
  → Bevorzugt "_einzelseiten" PDFs (falls Doppelseiten aufgeteilt wurden)
  → Öffnet PDF mit PyMuPDF (fitz)
```

#### Schritt 2: Running Headers erkennen
```python
build_header_skip_set(doc):
    für jede Seite:
        # Scanne obere 18% der Seite
        für jeden Textblock mit y_top < page_height * 0.18:
            normalisiere Text (lowercase, ohne Zahlen)
            zähle Vorkommen über alle Seiten
    
    # Zeilen die auf ≥8% der Seiten vorkommen = Running Header
    return Set von zu überspringenden Zeilen
```
**Beispiel:** "ERSTER VORTRAG" erscheint auf 50 von 320 Seiten → wird als Running Header erkannt und übersprungen.

#### Schritt 3: Pro PDF-Seite verarbeiten

**3a. Seitenzahl aus Footer extrahieren:**
```python
extract_printed_page_from_footer(page):
    # Scanne untere 15% der Seite (y > page_height * 0.85)
    
    # Priorität der Muster:
    1. "Seite: 123" oder "Seite 123"  → Priorität 10
    2. "- 123 -" (mit Strichen)       → Priorität 8  
    3. Alleinstehende Zahl "123"      → Priorität 5
    
    # Wähle Kandidat mit höchster Priorität
    # Fallback: Plain-Text der letzten 10 Zeilen durchsuchen
```

**3b. Fließtext extrahieren:**
```python
extract_body_text(page, header_skip):
    für jeden Textblock:
        # Überspringe wenn:
        - Im Footer-Bereich UND sieht aus wie Seitenzahl
        - Enthält "Copyright" oder "Buch:"
        - Ist Running Header (in header_skip)
        - Ist ALL CAPS Überschrift (< 90 Zeichen, kein Satzzeichen am Ende)
    
    # Sortiere nach y-Position (Reading Order)
    # Verbinde zu einem String
    # Entferne PDF-Artefakte wie "[34]" (Querverweise)
```

**3c. Fehlende Seitenzahlen interpolieren:**
```python
interpolate_printed_pages(pages):
    # Beispiel: Seite 10, ?, ?, 13 erkannt
    # → Interpoliert zu: 10, 11, 12, 13
    
    für jede Seite ohne printed_page:
        finde vorherigen und nächsten Anker
        berechne lineare Interpolation
```

#### Schritt 4: Breaks erstellen
```python
für i in range(pdf_page_count - 1):
    left_text = pages[i].body_text[-200:]    # Letzte 200 Zeichen
    right_text = pages[i+1].body_text[:200]  # Erste 200 Zeichen
    
    # Prüfe auf Silbentrennung am Seitenende
    hyphenated = left_text.rstrip()[-1] in {"-", "¬", "–"}
    
    breaks.append({
        "page": pages[i+1].printed_page,  # Seitenzahl der NÄCHSTEN Seite
        "pdfFrom": i,
        "pdfTo": i + 1,
        "left": left_text,
        "right": right_text,
        "hyphenated": hyphenated
    })
```

**Beispiel eines Breaks:**
```
PDF-Seite 12 (gedruckt S.13): "...ist ein Unding in der Menschheit"
PDF-Seite 13 (gedruckt S.14): "dieser Weise gleichgültig bleiben..."

→ Break: { page: 14, left: "...Menschheit", right: "dieser Weise..." }
```

### Output

| Datei | Pfad | Format |
|-------|------|--------|
| Page-Break-Markers | `page-break-markers.json` | JSON |

**Struktur:**
```json
{
  "_info": "Page-Break Anchors V4...",
  "GA198": {
    "title": "Heilfaktoren für den sozialen Organismus",
    "pdfSource": "Steiner, Rudolf GA 198 1984 - ....pdf",
    "pdfPageCount": 320,
    "contentRange": [7, 10000],
    "breaks": [
      {
        "page": 13,
        "pdfFrom": null,
        "pdfTo": 12,
        "left": null,
        "right": "Was heute den Menschen als eine fast...",
        "hyphenated": false,
        "isFirstPage": true
      },
      {
        "page": 14,
        "pdfFrom": 12,
        "pdfTo": 13,
        "left": "...ist ein Unding in der Menschheit",
        "right": "dieser Weise gleichgültig bleiben...",
        "hyphenated": false
      }
    ]
  }
}
```

### Aufruf

```powershell
# Einzelne GA verarbeiten
python export_page_markers_v4.py GA198

# Mit Validierung (prüft ob Breaks im JSON-Text gefunden werden)
python export_page_markers_v4.py --validate GA198
```

---

## 2. apply_page_break_markers_v4.py

### Zweck
Nimmt die Break-Anker aus `page-break-markers.json` und findet im JSON-Text die exakte Einfügeposition für jeden Seitenumbruch. Fügt Marker im Format `|<page>|` ein.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| Break-Anker | `page-break-markers.json` | Output von `export_page_markers_v4.py` |
| Vorträge | `steiner-full-lectures/*.json` | JSON-Dateien mit Vortrags-Paragraphen |
| Bücher | `steiner-books/*.json` | JSON-Dateien mit Buch-Paragraphen |
| Lecture-Mapping | `lecture-page-mapping.json` | Start-Seitenzahlen pro Vortrag |

### GA-Band-Kategorien

| Kategorie | GA-Nummern | Quelldateien |
|-----------|------------|--------------|
| Bücher | GA001-GA028, GA045 | `steiner-books-*.json` |
| Aufsätze | GA029-GA036, GA046 | `steiner-full-lectures-*.json` |
| Vorträge | GA051 ff | `steiner-full-lectures-*.json` |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Daten laden
```python
# Break-Anker laden
anchors = load_json("page-break-markers.json")
breaks = anchors["GA198"]["breaks"]  # z.B. 318 Breaks

# Vorträge oder Buch laden
if GA >= 51:
    lectures = load_lectures_by_ga("GA198")  # 17 Vorträge
else:
    book = load_book_by_ga("GA004")
```

#### Schritt 2: Text normalisieren (für Fuzzy-Matching)

Die Normalisierung ist entscheidend, weil PDF-Text und JSON-Text sich unterscheiden können:

```python
def normalize_simple(text):
    # 1. Soft Hyphen und Non-Breaking Space entfernen
    s = text.replace("\u00ad", "").replace("\u00a0", " ")
    
    # 2. Ligaturen expandieren
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")
    
    # 3. Lowercase
    s = s.lower()
    
    # 4. Alte Orthographie: "th" → "t"
    #    "Thatsachen" → "tatsachen" (PDF) vs "Tatsachen" → "tatsachen" (JSON)
    s = re.sub(r"th", "t", s)  # vereinfacht
    
    # 5. ß → ss
    s = s.replace("ß", "ss")
    
    # 6. Silbentrennung zusammenführen
    #    "Philo-\nsophie" → "philosophie"
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)
    
    # 7. Whitespace normalisieren
    s = re.sub(r"\s+", " ", s)
    
    return s.strip()
```

**Beispiel:**
```
PDF:  "Thatsächlich ist es so, daß die Philo-\nsophie..."
JSON: "Tatsächlich ist es so, dass die Philosophie..."

Nach Normalisierung (beide):
      "tatsachlich ist es so, dass die philosophie..."
```

#### Schritt 3a: Vorträge einzeln verarbeiten

```python
def process_lectures_individually(lectures, breaks):
    # Lade Start-Seitenzahlen aus lecture-page-mapping.json
    mapping = {
        "GA198/1": 13,   # Vortrag 1 beginnt auf Seite 13
        "GA198/2": 25,   # Vortrag 2 beginnt auf Seite 25
        ...
    }
    
    für jeden Vortrag:
        start_page = mapping[vortrag.ID]
        end_page = mapping[nächster_vortrag.ID] oder start_page + 10
        
        # Filtere Breaks für diesen Seitenbereich
        vortrag_breaks = [b for b in breaks if start_page <= b.page < end_page]
        
        # Normalisiere alle Paragraphen des Vortrags
        norm_text, para_map, char_map = normalize_paragraphs_with_map(vortrag.paragraphs)
        
        # Füge Start-Seite am Anfang des ersten Fließtext-Absatzes ein
        insertions.append((0, 0, start_page))
        
        # Finde Position für jeden weiteren Break
        für jeden break in vortrag_breaks:
            position = find_best_insertion(norm_text, break.left, break.right)
            if position:
                insertions.append(position)
```

#### Schritt 3b: Bücher als zusammenhängenden Text verarbeiten

```python
def process_book(book, breaks):
    # Alle Paragraphen zu einem normalisierten Text verbinden
    norm_text, para_map, char_map = normalize_paragraphs_with_map(book.paragraphs)
    
    last_norm_pos = 0  # Monotonie: jeder Break muss NACH dem vorherigen sein
    
    für jeden break in sortiert_nach_seitenzahl(breaks):
        position = find_best_insertion(norm_text, break.left, break.right, 
                                       min_norm_pos=last_norm_pos)
        
        # Schutz gegen Ausreißer: Sprung darf nicht zu groß sein
        if position - last_norm_pos > 40000:
            skip(break)  # Wahrscheinlich False Positive
            continue
        
        insertions.append(position)
        last_norm_pos = position + 1
```

#### Schritt 4: Insertion finden (Kern-Algorithmus)

```python
def find_best_insertion(norm_content, left, right, hyphenated, min_norm_pos=0):
    r_norm = normalize_simple(right)
    l_norm = normalize_simple(left)
    
    best_score = -1
    best_pos = None
    
    # === METHODE 1: Exakte Suche nach RIGHT ===
    für r_len in [140, 120, 100, 80, 60]:  # Verschiedene Längen probieren
        r_key = r_norm[:r_len]
        
        pos = norm_content.find(r_key, min_norm_pos)
        while pos >= 0:
            # Bewerte Fund: Ist LEFT kurz davor?
            score = 1.0 + left_bonus(pos, l_norm)
            
            if score > best_score:
                best_score = score
                best_pos = pos
            
            pos = norm_content.find(r_key, pos + 1)
        
        if best_score >= 8.0:  # Sehr guter Fund (LEFT direkt davor)
            break
    
    # === METHODE 2: Fuzzy-Matching (wenn exakt nicht gefunden) ===
    if best_pos is None:
        # Extrahiere lange Wörter aus RIGHT
        tokens = ["geisteswissenschaft", "menschheit", "entwicklung", ...]
        
        für jedes token:
            # Finde alle Vorkommen im Text
            # Berechne: position - token_offset_in_right = kandidat_start
            kandidaten.append(kandidat_start)
        
        für jeden kandidat:
            # Vergleiche mit SequenceMatcher
            segment = norm_content[kandidat:kandidat+160]
            ratio = SequenceMatcher(None, r_norm[:160], segment).ratio()
            
            if ratio > 0.7:  # Mindestens 70% Übereinstimmung
                score = ratio * 10 + left_bonus(kandidat)
                if score > best_score:
                    best_pos = kandidat
    
    # === METHODE 3: Fallback auf LEFT ===
    if best_pos is None:
        # Finde Ende von LEFT und setze Marker dort
        l_pos = norm_content.find(l_norm[-100:])
        if l_pos >= 0:
            best_pos = l_pos + len(l_norm[-100:])
    
    # Konvertiere norm_pos zurück zu (paragraph_idx, char_idx)
    return (para_map[best_pos], char_map[best_pos], best_pos)


def left_bonus(pos, l_norm):
    """Bonus wenn LEFT kurz vor POS gefunden wird"""
    window = norm_content[max(0, pos-900):pos]
    
    l_pos = window.rfind(l_norm[-100:])
    if l_pos >= 0:
        distance = pos - (window_start + l_pos + len(l_norm[-100:]))
        
        if distance <= 10:   return 10.0  # Perfekt: LEFT endet direkt vor RIGHT
        if distance <= 30:   return 7.0   # Sehr gut
        if distance <= 80:   return 4.0   # Gut
        if distance <= 200:  return 2.0   # Akzeptabel
    
    return -0.5  # LEFT nicht gefunden → Abzug
```

**Beispiel:**
```
Break: { page: 14, left: "...Unding in der Menschheit", right: "dieser Weise gleichgültig" }

1. Suche "dieser weise gleichgultig" (normalisiert) im JSON-Text
2. Gefunden an Position 4523
3. Prüfe: Ist "unding in der menschheit" kurz vor 4523?
   → Gefunden bei Position 4498, Distanz = 25 → Score = 7.0
4. → Einfügeposition: Position 4523 im normalisierten Text
   → Zurückrechnen: Paragraph 3, Zeichen 156
```

#### Schritt 5: Marker einfügen

```python
def apply_insertions_to_paragraphs(paragraphs, insertions):
    # Gruppiere nach Paragraph
    by_para = group_by(insertions, key=para_idx)
    
    für jeden paragraph:
        # WICHTIG: Von hinten nach vorne einfügen (damit Positionen stimmen)
        für (char_idx, page) in sorted(by_para[para_idx], reverse=True):
            
            # Prüfe ob Position in geschützter Struktur liegt
            char_idx = find_safe_insertion_position(content, char_idx)
            # z.B. nicht innerhalb von ![alt](bild.png) oder <img ...>
            
            # Marker einfügen
            content = content[:char_idx] + f"|{page}|" + content[char_idx:]
        
        paragraph["content"] = content
```

**Vorher:**
```
"dieser Weise gleichgültig bleiben. Da war alles..."
```

**Nachher:**
```
"|14|dieser Weise gleichgültig bleiben. Da war alles..."
```

### Output

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Vorträge/Buch mit Markern | `pagebreak-books/GA198.json` | JSON mit eingefügten `\|page\|` Markern |
| Report | `pagebreak-books/GA198-report.json` | Statistik und Fehler |

**Vortrags-Output Struktur:**
```json
{
  "_info": "Output: Vorträge mit eingefügten |page|-Markern...",
  "ga": "GA198",
  "sourceFile": "steiner-full-lectures-198-198.json",
  "lectureCount": 17,
  "lectures": [
    {
      "gaNumber": "GA198",
      "lectureNumber": "1",
      "ID": "GA198/1",
      "title": "ERSTER VORTRAG",
      "paragraphs": [
        {
          "index": "^4iv2sd",
          "content": "|13|Was heute den Menschen als eine fast unumstrittene..."
        }
      ]
    }
  ]
}
```

**Report Struktur:**
```json
{
  "ga": "GA198",
  "sourceFile": "steiner-full-lectures-198-198.json",
  "anchorsFile": "page-break-markers.json",
  "breaksTotal": 318,
  "breaksWithPage": 318,
  "inserted": 265,
  "insertedRatio": 0.833,
  "failed": 17,
  "failuresSample": [
    {"page": 24, "reason": "no-match", "lecture": 0}
  ]
}
```

### Aufruf

```powershell
# Standard: Output in pagebreak-books/
python apply_page_break_markers_v4.py GA198

# Mit explizitem Output-Pfad
python apply_page_break_markers_v4.py GA198 --out pagebreak-books/GA198.json

# Mit Report-Pfad
python apply_page_break_markers_v4.py GA198 --out pagebreak-books/GA198.json --report pagebreak-books/GA198-report.json
```

---

## 3. batch_generate_pagebreaks.py

### Zweck
Batch-Verarbeitung: Führt `export_page_markers_v4.py` und `apply_page_break_markers_v4.py` automatisch für einen Bereich von GA-Bänden aus.

### Input-Daten

| Quelle | Beschreibung |
|--------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` |
| Bestehende Pagebreaks | `pagebreak-books/GA*.json` (zum Überspringen bereits verarbeiteter) |

### Verarbeitungsschritte (detailliert)

```python
def main():
    # Parameter: python batch_generate_pagebreaks.py 198 200
    start_ga = 198
    end_ga = 200
    
    für ga_num in range(start_ga, end_ga + 1):
        ga_str = f"GA{ga_num:03d}"  # "GA198"
        
        # === SCHRITT 1: PDF prüfen ===
        pdf_path = find_pdf_for_ga(ga_num)
        if not pdf_path:
            print(f"⚠️ {ga_str}: Keine PDF")
            no_pdf += 1
            continue
        
        # === SCHRITT 2: Bereits verarbeitet? ===
        if (PAGEBREAK_DIR / f"{ga_str}.json").exists():
            print(f"✓ {ga_str}: Bereits verarbeitet (übersprungen)")
            skipped += 1
            continue
        
        # === SCHRITT 3: export_page_markers_v4.py aufrufen ===
        print(f"[1/2] Exportiere Page-Break-Marker für {ga_str}...")
        subprocess.run([
            "python", "export_page_markers_v4.py", ga_str
        ])
        # → Schreibt/erweitert page-break-markers.json
        
        # === SCHRITT 4: apply_page_break_markers_v4.py aufrufen ===
        print(f"[2/2] Wende Marker auf Vorträge an...")
        subprocess.run([
            "python", "apply_page_break_markers_v4.py", ga_str,
            "--out", f"pagebreak-books/{ga_str}.json",
            "--report", f"pagebreak-books/{ga_str}-report.json"
        ])
        # → Erzeugt pagebreak-books/GA198.json und GA198-report.json
        
        processed += 1
    
    # === SCHRITT 5: Zusammenfassung ===
    print(f"Verarbeitet: {processed}")
    print(f"Bereits fertig: {skipped}")
    print(f"Keine PDF: {no_pdf}")
    print(f"Fehlgeschlagen: {failed}")
```

**Beispiel-Ausgabe:**
```
============================================================
Batch-Generierung Seitenzahlen: GA198 bis GA200
============================================================

============================================================
Verarbeite GA198...
PDF: Steiner, Rudolf GA 198 1984 - Heilfaktoren für den sozialen Organismus.pdf
============================================================

[1/2] Exportiere Page-Break-Marker...
  PDF-Seiten: 320, erkannte gedruckte Seiten: 320 (100.0%)
  Breaks erzeugt: 318

[2/2] Wende Marker auf Vorträge an...
  Vorträge mit Start-Seite: 17 von 17
  eingefügt 265/318 (83.3%)
  ✓ GA198 erfolgreich verarbeitet!

  ✓ GA199: Bereits verarbeitet (übersprungen)
  ⚠️ GA200: Keine PDF

============================================================
ZUSAMMENFASSUNG
============================================================
  Verarbeitet:     1
  Bereits fertig:  1
  Keine PDF:       1
  Fehlgeschlagen:  0
============================================================
```

### Output

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Break-Marker | `page-break-markers.json` | Wird erweitert |
| Pagebreaks | `pagebreak-books/GA*.json` | Pro GA eine Datei |
| Reports | `pagebreak-books/GA*-report.json` | Pro GA ein Report |

### Aufruf

```powershell
# Standardbereich GA052-150
python batch_generate_pagebreaks.py

# Spezifischer Bereich
python batch_generate_pagebreaks.py 198 200

# Einzelne GA
python batch_generate_pagebreaks.py 198 198

# Nur prüfen welche PDFs existieren (ohne Verarbeitung)
python batch_generate_pagebreaks.py --check
```

---

## 4. generate_lecture_page_mapping.py

### Zweck
Erstellt ein Mapping von Vortrag-IDs zu ihren Start-Seitenzahlen im PDF. Dieses Mapping wird von `apply_page_break_markers_v4.py` verwendet, um zu wissen, wo im PDF jeder Vortrag beginnt.

### Warum ist dieses Skript nötig?
Bei Vortrags-Bänden (GA051+) enthält ein PDF mehrere Vorträge. Das `apply_page_break_markers_v4.py` muss wissen:
- Wo beginnt Vortrag 1? (z.B. Seite 13)
- Wo beginnt Vortrag 2? (z.B. Seite 25)
- usw.

Ohne dieses Mapping würde das Skript die Breaks falsch zuordnen.

### Input-Daten

| Quelle | Pfad | Beschreibung |
|--------|------|--------------|
| PDF-Dateien | `Steiner_GA_pdf/*.pdf` | GA-Band PDFs |
| Vorträge | `steiner-full-lectures/*.json` | JSON mit Vortrags-Text |
| Page-Breaks (optional) | `page-break-markers.json` | Für bessere Seitenzahl-Erkennung |

### Verarbeitungsschritte (detailliert)

#### Schritt 1: Vorträge laden
```python
lectures = load_lectures_for_ga("GA198")
# Lädt aus steiner-full-lectures/steiner-full-lectures-198-198.json
# Sortiert nach lectureNumber: [Vortrag 1, Vortrag 2, ..., Vortrag 17]
```

#### Schritt 2: PDF-Seiten extrahieren
```python
def extract_page_texts(pdf_path, ga_number):
    # Versuche vorberechnete Seitenzahlen zu laden
    precomputed = load_page_breaks(ga_number)  # aus page-break-markers.json
    
    page_texts = []
    für jede PDF-Seite i:
        text = page.get_text("text")
        
        if i in precomputed:
            page_num = precomputed[i]  # Seitenzahl aus page-break-markers.json
        else:
            page_num = extract_page_number(page)  # Aus Footer extrahieren
        
        page_texts.append((i, page_num, text))
    
    return page_texts  # [(0, 7, "Inhalt..."), (1, 8, "Vorwort..."), ...]
```

#### Schritt 3: Für jeden Vortrag die Start-Seite finden

```python
def find_lecture_in_pdf(lecture, page_texts):
    # === SCHRITT 3a: Ersten Fließtext-Absatz finden ===
    collected = []
    für jeden absatz in lecture.paragraphs[:15]:
        text = normalize_text(absatz.content)
        
        # Überspringe Metadaten und kurze Zeilen
        if len(text) < 30: continue
        if text.startswith(("manuskript", "fragment", "undatiert")): continue
        
        collected.append(text)
        
        # Brauchen mindestens 200 Zeichen MIT Satzzeichen (Fließtext)
        combined = " ".join(collected)
        if len(combined) >= 200 and any(p in combined for p in ['. ', ', ', '; ']):
            break
    
    search_text = combined[:1000]  # Maximal 1000 Zeichen für Suche
    
    # === SCHRITT 3b: Im PDF suchen (sequentiell) ===
    für (pdf_idx, page_num, page_text) in page_texts:
        page_norm = normalize_text(page_text)
        
        # Exakte Teilstring-Suche (verschiedene Längen)
        für search_len in [800, 600, 400, 300, 250, 200, 150]:
            search_key = search_text[:search_len]
            if search_key in page_norm:
                return (pdf_idx, page_num)  # GEFUNDEN!
    
    # === SCHRITT 3c: Fallback - Fuzzy Matching ===
    best_match = None
    für (pdf_idx, page_num, page_text) in page_texts:
        page_norm = normalize_text(page_text)
        
        # Sliding Window über die Seite
        für start in range(0, len(page_norm) - 150, 50):
            window = page_norm[start:start + 150]
            ratio = SequenceMatcher(None, search_text[:150], window).ratio()
            
            if ratio > 0.80 and (best_match is None or ratio > best_match[0]):
                best_match = (ratio, pdf_idx, page_num)
    
    if best_match and best_match[0] > 0.80:
        return (best_match[1], best_match[2])
    
    return None  # Nicht gefunden
```

**Beispiel:**
```
Vortrag GA198/1:
  Absatz 1: "ERSTER VORTRAG"                    → zu kurz, übersprungen
  Absatz 2: "Dornach, 20. März 1920"            → Metadaten, übersprungen  
  Absatz 3: "Was heute den Menschen als eine fast unumstrittene Autorität 
             gilt, das ist Wissenschaft..."     → 200+ Zeichen, Fließtext ✓

Suche im PDF:
  Seite 7 (Inhalt): enthält "Erster Vortrag...Seite 13" → Nein (falscher Text)
  Seite 12 (S.13): enthält "Was heute den Menschen als eine fast..." → JA!

Ergebnis: GA198/1 → Seite 13
```

#### Schritt 4: Mapping speichern
```python
mapping = {
    "GA198/1": 13,
    "GA198/2": 25,
    "GA198/3": 42,
    ...
}

# Lade bestehendes Mapping und erweitere
existing = load_json("lecture-page-mapping.json")
existing["GA198"] = mapping
save_json("lecture-page-mapping.json", existing)
```

### Output

| Datei | Pfad | Format |
|-------|------|--------|
| Lecture-Mapping | `lecture-page-mapping.json` | JSON |

**Struktur:**
```json
{
  "_info": "Lecture-ID → Start-Seitenzahl im PDF",
  "GA198": {
    "GA198/1": 13,
    "GA198/2": 25,
    "GA198/3": 42,
    "GA198/4": 57
  },
  "GA199": {
    "GA199/1": 11,
    "GA199/2": 28
  }
}
```

### Aufruf

```powershell
# Mapping für eine GA generieren
python generate_lecture_page_mapping.py GA198

# Nach dem Mapping: Pagebreaks neu generieren
python batch_generate_pagebreaks.py 198 198
```

### Wann dieses Skript verwenden?

- **Vor** dem ersten Pagebreak-Generieren für eine neue GA
- Wenn viele Vorträge mit "no-match" im Report sind
- Wenn die automatische Start-Seiten-Erkennung fehlschlägt

---

## Datenfluss-Diagramm

```
┌─────────────────────┐
│   PDF-Dateien       │
│ Steiner_GA_pdf/     │
└─────────┬───────────┘
          │
          ├─────────────────────────────────────────┐
          │                                         │
          ▼                                         ▼
┌─────────────────────────────┐     ┌────────────────────────────────┐
│ export_page_markers_v4.py   │     │ generate_lecture_page_mapping  │
│ - Seitenzahlen erkennen     │     │ - Vortrag-Text im PDF suchen   │
│ - Fließtext extrahieren     │     │ - Start-Seite pro Vortrag      │
│ - Break-Anker speichern     │     └─────────────┬──────────────────┘
└─────────┬───────────────────┘                   │
          │                                       ▼
          ▼                           ┌───────────────────────┐
┌─────────────────────┐               │ lecture-page-mapping  │
│ page-break-markers  │               │        .json          │
│      .json          │               └───────────┬───────────┘
└─────────┬───────────┘                           │
          │                                       │
          └───────────────────┬───────────────────┘
                              │
                              ▼
┌─────────────────────────────────┐     ┌──────────────────────┐
│ apply_page_break_markers_v4.py  │◄────│ steiner-full-lectures│
│ - Fuzzy-Matching im Text        │     │ steiner-books        │
│ - |page| Marker einfügen        │     │      .json           │
└─────────┬───────────────────────┘     └──────────────────────┘
          │
          ▼
┌─────────────────────┐
│   pagebreak-books/  │
│   GA*.json          │
│   GA*-report.json   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     backend.js      │
│ (lädt Overrides)    │
└─────────────────────┘
```

---

## Backend-Integration

Das Backend (`backend.js`) lädt beim Start automatisch die Pagebreak-Overrides aus `pagebreak-books/`:

```javascript
// Zeile 729-760 in backend.js
const overridesDir = path.join(__dirname, 'pagebreak-books');
const overrideFiles = files.filter(f => /^GA\d{3}[a-z]?\.json$/i.test(f));

// Für jeden Override: Ersetze die Vorträge/Bücher mit den Versionen
// die |page|-Marker enthalten
```

**Wichtig:** Nach dem Generieren neuer Pagebreaks muss der Server neu gestartet werden, damit die Änderungen geladen werden!

---

## Typische Workflow-Beispiele

### Neue GA-Seitenzahlen generieren (Standardfall)

```powershell
# 1. Server stoppen
Get-Process -Name "node" | Stop-Process -Force

# 2. Pagebreaks generieren
python batch_generate_pagebreaks.py 198 198

# 3. Server starten
node backend.js
```

### Neue GA mit Lecture-Mapping (für bessere Ergebnisse)

```powershell
# 1. Server stoppen
Get-Process -Name "node" | Stop-Process -Force

# 2. Erst das Lecture-Mapping erstellen (findet Start-Seite jedes Vortrags)
python generate_lecture_page_mapping.py GA198

# 3. Dann Pagebreaks generieren (nutzt das Mapping)
python batch_generate_pagebreaks.py 198 198

# 4. Server starten
node backend.js
```

### Mehrere GAs auf einmal verarbeiten

```powershell
python batch_generate_pagebreaks.py 190 200
```

### Prüfen welche GAs noch fehlen

```powershell
python batch_generate_pagebreaks.py --check
```

### Wenn viele "no-match" Fehler auftreten

```powershell
# 1. Erst Lecture-Mapping (neu) erstellen
python generate_lecture_page_mapping.py GA198

# 2. Dann Pagebreaks neu generieren
python batch_generate_pagebreaks.py 198 198
```

---

## Fehlerbehebung

### Problem: Seitenzahlen nicht sichtbar

1. **Prüfen ob Pagebreak-Datei existiert:**
   ```powershell
   Test-Path pagebreak-books/GA198.json
   ```

2. **Server neu starten** (lädt Overrides neu)

3. **Report prüfen** für Einfüge-Quote:
   ```powershell
   Get-Content pagebreak-books/GA198-report.json
   ```

### Problem: Viele "no-match" Fehler

- PDF-Qualität prüfen (OCR-Fehler?)
- `lecture-page-mapping.json` erweitern (manuelle Start-Seiten)
- `--validate` Flag bei Export verwenden

### Problem: Seitenzahlen an falscher Stelle

- Break-Anker in `page-break-markers.json` prüfen
- Eventuell manuell korrigieren oder PDF mit besserer Qualität verwenden

---

## Technische Details

### Normalisierung für Matching

| Original | Normalisiert | Grund |
|----------|--------------|-------|
| `Thatsachen` | `tatsachen` | Alte Orthographie |
| `daß` | `dass` | Alte Rechtschreibung |
| `ﬁnden` | `finden` | Ligatur |
| `Philo-<br>sophie` | `philosophie` | Silbentrennung |

### Marker-Format

```
Text vor Seitenumbruch|14|Text der nächsten Seite
```

Der Marker `|14|` bedeutet: "Hier beginnt Seite 14 des gedruckten Buches."

---

*Letzte Aktualisierung: Dezember 2024*

