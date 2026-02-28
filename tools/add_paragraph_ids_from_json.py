#!/usr/bin/env python3
"""
add_paragraph_ids_from_json.py
=============================
Fügt Absatz-IDs (^xyz) aus steiner-full-lectures und steiner-books JSON
zu den Obsidian-Textblöcken in "Obsidian Entwicklungsanthropologie" hinzu.

Liest die JSON-Dateien, sucht passende Absätze per Textvergleich und
fügt die block_id am Ende des Absatzes ein, falls noch nicht vorhanden.

Verwendung:
    python tools/add_paragraph_ids_from_json.py              # Dry-Run (nur anzeigen)
    python tools/add_paragraph_ids_from_json.py --apply     # Änderungen schreiben
    python tools/add_paragraph_ids_from_json.py --file "Wirkungen" --apply  # Nur bestimmte Dateien
"""

import json
import re
import argparse
from pathlib import Path
from difflib import SequenceMatcher

# Pfade
BASE = Path(__file__).parent.parent
LECTURES_DIR = BASE / "steiner-full-lectures"
BOOKS_DIR = BASE / "steiner-books"
OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")
OBSIDIAN_TOPICS = OBSIDIAN_VAULT / "I. Themen"
STEINER_GA_DIR = BASE / "Steiner_GA"

# Muster für GA-Zitation in ##### Kopfzeilen: "GA 301 10.05.1920" oder "GA 034 01.05.1907"
GA_CITE_RE = re.compile(
    r'GA\s+(\d+)([a-z]?)\s+(\d{2})\.(\d{2})\.(\d{4})',
    re.IGNORECASE
)

# GA + Seitenzahl aus Quellenangabe am Absatzende: [GA 095, S. 54–58, 27.08.1906]
# oder (GA 095, S. 54–58; 27.08.1906)
CITATION_RE = re.compile(
    r'[\[\(]\s*GA\s+(\d+)([a-z]?),\s*S\.\s*(\d+)(?:[–\-]\d+)?[^\]\)]*[\]\)]',
    re.IGNORECASE
)

# GA aus Steiner_GA Dateiname: "GA307 (1.) ..." oder "GA307 - ..."
STEINER_GA_GA_RE = re.compile(r'GA\s*(\d+)([a-z]?)\s*[\(\-]', re.IGNORECASE)
# Datum aus Dateiname: "5. August 1923" oder "16. Februar 1924"
STEINER_GA_DATE_RE = re.compile(r'(\d{1,2})\.\s*(\w+)\s+(\d{4})', re.IGNORECASE)
MONTH_DE = {
    "januar": "01", "februar": "02", "märz": "03", "maerz": "03", "april": "04", "mai": "05",
    "juni": "06", "juli": "07", "august": "08", "september": "09", "oktober": "10",
    "november": "11", "dezember": "12",
}


def normalize_text(text: str) -> str:
    """Normalisiert Text für Vergleich."""
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    # Seitenmarker |123|
    text = re.sub(r'\|\d+\|', '', text)
    # Block-IDs am Ende
    text = re.sub(r'\s*\^[a-z0-9]+\s*$', '', text)
    # GA-Zitation am Ende entfernen (in [] oder ())
    text = re.sub(
        r'\s*[\[\(]\s*GA\s+\d+[a-z]?,\s*S\.\s*[\d\s–\-]+(?:[,;]\s*\d{2}\.\d{2}\.\d{4})?[^\]\)]*[\]\)]\s*$',
        '',
        text,
        flags=re.IGNORECASE
    )
    # Alte Rechtschreibung
    for old, new in [
        ('daß', 'dass'), ('muß', 'muss'), ('läßt', 'lässt'),
        ('faßt', 'fasst'), ('bewußt', 'bewusst'), ('Unbewußt', 'Unbewusst'),
        ('gießt', 'giesst'), ('Einfluß', 'Einfluss'), ('Schluß', 'Schluss'),
        ('Fluß', 'Fluss'), ('paßt', 'passt'),
    ]:
        text = text.replace(old, new)
    return ' '.join(text.split()).strip()


def _extract_page_from_content(content: str) -> int | None:
    """Extrahiert erste Seitennummer aus |123| im Inhalt."""
    m = re.search(r'\|(\d+)\|', content)
    return int(m.group(1)) if m else None


def load_lectures_index() -> dict:
    """
    Lädt alle Vorträge aus steiner-full-lectures.
    Rückgabe: {(ga_num, date_iso): [(content, block_id, page), ...]}
    """
    index = {}
    if not LECTURES_DIR.exists():
        return index

    for fp in LECTURES_DIR.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠ {fp.name}: {e}")
            continue

        for lec in data.get("lectures", []):
            lid = lec.get("ID") or ""
            date_val = lec.get("date") or ""
            if date_val and len(date_val) == 10 and date_val[4] == "-":
                date_iso = date_val
            elif re.match(r'\d{2}\.\d{2}\.\d{4}', date_val or ""):
                d, m, y = date_val[:2], date_val[3:5], date_val[6:10]
                date_iso = f"{y}-{m}-{d}"
            else:
                date_iso = ""

            ga_match = re.match(r'GA(\d+)([a-z]?)', lid, re.IGNORECASE)
            ga_num = (ga_match.group(1) + (ga_match.group(2) or "")).upper() if ga_match else ""

            if not ga_num:
                continue

            key = (ga_num, date_iso) if date_iso else (ga_num,)
            if key not in index:
                index[key] = []

            for para in lec.get("paragraphs", []):
                content = para.get("content") or para.get("text") or ""
                block_id = (para.get("index") or "").lstrip("^").strip()
                page = _extract_page_from_content(content)
                if content and block_id:
                    # Normalisierten Inhalt vorab speichern (spart Wiederholung bei Suche)
                    index[key].append((normalize_text(content), block_id, page))

    return index


def load_books_index() -> dict:
    """
    Lädt alle Bücher aus steiner-books.
    Rückgabe: {ga_num: [(content, block_id, page), ...]}
    """
    index = {}
    if not BOOKS_DIR.exists():
        return index

    for fp in BOOKS_DIR.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠ {fp.name}: {e}")
            continue

        books = data.get("books", data) if isinstance(data, dict) else []
        if not isinstance(books, list):
            books = [data] if isinstance(data, dict) and data.get("ID") else []

        for book in books:
            bid = book.get("ID") or book.get("gaNumber") or ""
            ga_match = re.match(r'GA(\d+)([a-z]?)', str(bid), re.IGNORECASE)
            ga_num = (ga_match.group(1) + (ga_match.group(2) or "")).upper() if ga_match else ""

            if not ga_num:
                continue

            paras = book.get("paragraphs", [])
            if not paras and book.get("content"):
                content = book.get("content", "")
                for line in content.split("\n"):
                    m = re.match(r'^(\^[a-z0-9]+)\s+(.+)$', line.strip())
                    if m:
                        paras.append({"index": m.group(1).lstrip("^"), "content": m.group(2)})
                    elif line.strip():
                        paras.append({"index": "", "content": line.strip()})

            if ga_num not in index:
                index[ga_num] = []

            for para in paras:
                content = para.get("content") or para.get("text") or ""
                block_id = (para.get("index") or "").lstrip("^").strip()
                page = _extract_page_from_content(content)
                if content and block_id:
                    index[ga_num].append((normalize_text(content), block_id, page))

    return index


def extract_citation_page(obs_text: str) -> int | None:
    """Extrahiert Seitennummer aus [GA 095, S. 54–58, 27.08.1906] am Ende."""
    m = CITATION_RE.search(obs_text)
    return int(m.group(3)) if m else None


def extract_text_fragments(obs_text: str, words_per_frag: int = 10) -> list[str]:
    """
    Extrahiert 2–3 Textfragmente à ~10 Wörter für schnelle Substring-Suche.
    Kein Similarity-Check – nur: Fragment in Kandidat enthalten?
    """
    text = obs_text
    text = re.sub(r'\s*[\[\(]\s*GA\s+\d+[a-z]?,[^\]\)]+[\]\)]\s*$', '', text, flags=re.IGNORECASE)
    text = normalize_text(text)
    words = text.split()
    if len(words) < 8:
        return [text] if text else []

    frags = []
    # Anfang (evtl. "..." überspringen)
    start = 0
    if words and words[0] == "...":
        start = 1
    if start < len(words):
        f = " ".join(words[start : start + words_per_frag])
        if len(f) >= 15:
            frags.append(f)

    # Ende
    if len(words) > words_per_frag + 5:
        f = " ".join(words[-words_per_frag:])
        if f not in frags and len(f) >= 15:
            frags.append(f)

    # Mitte bei langem Text
    if len(words) > words_per_frag * 2 + 10:
        mid = len(words) // 2 - words_per_frag // 2
        f = " ".join(words[mid : mid + words_per_frag])
        if f not in frags and len(f) >= 15:
            frags.append(f)

    return frags[:3]


def extract_window_fragments(obs_text: str, words_per_frag: int = 7, max_windows: int = 24) -> list[str]:
    """
    Robuster Fallback: viele kurze 7-Wort-Fenster über den Absatz.
    So werden auch lange Absätze mit eingeschobenen Seitenmarkern besser getroffen.
    """
    text = re.sub(r'\s*[\[\(]\s*GA\s+\d+[a-z]?,[^\]\)]+[\]\)]\s*$', '', obs_text, flags=re.IGNORECASE)
    words = normalize_text(text).split()
    if len(words) < words_per_frag:
        return []

    last_start = len(words) - words_per_frag
    # Fenster gleichmäßig über den Absatz verteilen (statt jedes Wort zu nehmen)
    step = max(1, last_start // max(1, (max_windows - 1)))
    starts = list(range(0, last_start + 1, step))
    if starts[-1] != last_start:
        starts.append(last_start)

    frags = []
    for st in starts:
        frag = " ".join(words[st: st + words_per_frag]).strip()
        if len(frag) >= 12 and frag not in frags:
            frags.append(frag)
    return frags


def find_best_match(
    obs_text: str,
    candidates: list,
    page_from_citation: int | None = None,
) -> str | None:
    """
    Findet passenden Absatz per Fragment-Suche (2–3 Fragmente à 10 Wörter).
    Kein Similarity-Check – nur Substring: Fragment in content enthalten?
    candidates: [(content, block_id, page), ...]
    """
    fragments = extract_text_fragments(obs_text)
    if not fragments:
        return None

    norm_frags = [normalize_text(f) for f in fragments if f]

    # Optional: Nach Seite einschränken
    if page_from_citation is not None:
        page_cands = [x for x in candidates if len(x) >= 3 and x[2] == page_from_citation]
        if page_cands:
            candidates = page_cands

    best_id = None
    best_count = 0
    best_page_match = False

    for item in candidates:
        content_norm, block_id = item[0], item[1]  # content bereits normalisiert
        matches = sum(1 for nf in norm_frags if nf and nf in content_norm)
        if matches < 1:
            continue
        page_ok = len(item) >= 3 and item[2] == page_from_citation
        # Besser wenn mehr Fragmente UND (Seite passt oder bisher keine bessere)
        if matches > best_count or (matches == best_count and page_ok and not best_page_match):
            best_count = matches
            best_id = block_id
            best_page_match = page_ok

    if best_id:
        return best_id

    # Fallback für schwierige Fälle: viele 7-Wort-Fenster scorieren
    window_frags = extract_window_fragments(obs_text, words_per_frag=7, max_windows=24)
    if not window_frags:
        return None

    scored = []
    for item in candidates:
        content_norm, block_id = item[0], item[1]
        score = sum(1 for wf in window_frags if wf in content_norm)
        if score > 0:
            scored.append((score, block_id))

    if not scored:
        return None

    scored.sort(reverse=True)
    top_score, top_id = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else -1

    # Nur eindeutig genug übernehmen (sonst Risiko für falsche IDs)
    if top_score >= 2 and top_score > second_score:
        return top_id

    # Letzter Fallback: sehr konservativer Volltext-Ähnlichkeitsvergleich
    # (hilft bei kleinen OCR-/Orthographie-Differenzen trotz klar gleicher Passage)
    obs_norm = normalize_text(re.sub(r'\s*[\[\(]\s*GA\s+\d+[a-z]?,[^\]\)]+[\]\)]\s*$', '', obs_text, flags=re.IGNORECASE))
    if not obs_norm:
        return None

    sim_scored = []
    for item in candidates:
        content_norm, block_id = item[0], item[1]
        if not content_norm:
            continue
        ratio = SequenceMatcher(None, obs_norm, content_norm).ratio()
        page_ok = len(item) >= 3 and item[2] == page_from_citation if page_from_citation is not None else False
        # Seite leicht bevorzugen, aber nur minimal
        score = ratio + (0.005 if page_ok else 0.0)
        if score >= 0.94:
            sim_scored.append((score, ratio, block_id))

    if not sim_scored:
        return None

    sim_scored.sort(reverse=True)
    top_score, top_ratio, top_id = sim_scored[0]
    second_score = sim_scored[1][0] if len(sim_scored) > 1 else 0.0

    # Nur übernehmen, wenn deutlich/sauber führend
    if top_ratio >= 0.97 or (top_score >= 0.945 and (top_score - second_score) >= 0.01):
        return top_id

    return None


def extract_ga_from_header(line: str) -> tuple | None:
    """Extrahiert (ga_num, date_iso) aus ##### Zeile. None wenn kein GA."""
    m = GA_CITE_RE.search(line)
    if not m:
        return None
    ga_num = m.group(1) + (m.group(2) or "")
    dd, mm, yyyy = m.group(3), m.group(4), m.group(5)
    date_iso = f"{yyyy}-{mm}-{dd}"
    return (ga_num.upper(), date_iso)


def process_obsidian_file(fp: Path, lectures_idx: dict, books_idx: dict, apply: bool, file_filter: str | None) -> dict:
    """Verarbeitet eine Obsidian-MD-Datei."""
    stats = {"checked": 0, "added": 0, "already": 0, "no_match": 0, "no_ga": 0}

    if file_filter and file_filter.lower() not in fp.name.lower():
        return stats

    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(OBSIDIAN_VAULT)}: {e}")
        return stats

    # splitlines(keepends=True) erhält Zeilenumbrüche – wichtig, sonst werden alle Absätze zu einer Zeile
    lines = content.splitlines(keepends=True)
    current_ga = None  # (ga_num, date_iso) oder (ga_num,) für Bücher
    new_lines = []
    changed = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip("\r\n")

        # #### oder ##### Kopfzeile mit GA-Zitation?
        if stripped.startswith("####") and GA_CITE_RE.search(stripped):
            ga_info = extract_ga_from_header(stripped)
            if ga_info:
                ga_num, date_iso = ga_info
                # Vortrag (mit Datum) oder Buch (ohne Datum in Obsidian – prüfen wir beide)
                current_ga = (ga_num, date_iso)
            new_lines.append(line)
            i += 1
            continue

        # Leerzeile – Kontext zurücksetzen nicht (Absätze können über Leerzeilen gehen)
        if not stripped.strip():
            new_lines.append(line)
            i += 1
            continue

        # Normaler Textblock – potentieller Zitat-Absatz
        if current_ga and len(stripped) > 40:
            # Kein Headings-/Link-Only
            if stripped.startswith("#") or stripped.startswith("[[") and "]]" in stripped[:50]:
                new_lines.append(line)
                i += 1
                continue

            has_block_id = bool(re.search(r'\^[a-z0-9]+\s*$', stripped))
            if has_block_id:
                stats["already"] += 1
                new_lines.append(line)
                i += 1
                continue

            stats["checked"] += 1

            # Kandidaten: Vortrag (ga, date) oder Buch (ga ohne date)
            candidates = []
            if current_ga in lectures_idx:
                candidates = lectures_idx[current_ga]
            ga_num = current_ga[0] if current_ga else ""
            if ga_num in books_idx:
                candidates = candidates + books_idx[ga_num]

            if not candidates:
                stats["no_ga"] += 1
                new_lines.append(line)
                i += 1
                continue

            page_from_cit = extract_citation_page(stripped)
            block_id = find_best_match(stripped, candidates, page_from_citation=page_from_cit)
            if block_id:
                # ID nach Quellenangabe [GA ...], Leerzeichen davor, Zeilenumbruch danach
                new_line = stripped.rstrip() + f" ^{block_id}"
                if line.endswith("\n"):
                    new_line += "\n"
                elif line.endswith("\r"):
                    new_line += "\r"
                new_lines.append(new_line)
                stats["added"] += 1
                changed = True
            else:
                stats["no_match"] += 1
                new_lines.append(line)
        else:
            new_lines.append(line)

        i += 1

    if apply and changed:
        fp.write_text("".join(new_lines), encoding="utf-8")

    return stats


def extract_ga_and_date_from_steiner_path(fp: Path) -> tuple[str, str] | None:
    """
    Extrahiert (ga_num, date_iso) aus Steiner_GA Dateipfad/Name.
    z.B. GA307 (1.) ERSTER VORTRAG, Ilkley, 5. August 1923.md -> (307, 1923-08-05)
    """
    name = fp.stem
    ga_num = None
    ga_m = STEINER_GA_GA_RE.search(name)
    if ga_m:
        ga_num = (ga_m.group(1) + (ga_m.group(2) or "")).upper()
    if not ga_num:
        for part in fp.parent.parts:
            ga_m = re.match(r'GA\s*(\d+)([a-z]?)(?:\s|$|-)', part, re.IGNORECASE)
            if ga_m:
                ga_num = (ga_m.group(1) + (ga_m.group(2) or "")).upper()
                break
    if not ga_num:
        return None

    date_m = STEINER_GA_DATE_RE.search(name)
    if date_m:
        day, month_name, year = date_m.group(1), date_m.group(2).lower(), date_m.group(3)
        month = MONTH_DE.get(month_name) or MONTH_DE.get(month_name[:3])
        if not month:
            for k, v in MONTH_DE.items():
                if month_name.startswith(k[:2]) or k.startswith(month_name[:2]):
                    month = v
                    break
        if month:
            return (ga_num, f"{year}-{month}-{int(day):02d}")
    return (ga_num, "")


def process_steiner_ga_file(
    fp: Path,
    lectures_idx: dict,
    books_idx: dict,
    apply: bool,
    file_filter: str | None,
) -> dict:
    """Verarbeitet eine Steiner_GA MD-Datei (Vortrags-Volltext, Absätze durch Leerzeilen getrennt)."""
    stats = {"checked": 0, "added": 0, "already": 0, "no_match": 0, "no_ga": 0}

    if file_filter and file_filter.lower() not in fp.name.lower():
        return stats

    ga_date = extract_ga_and_date_from_steiner_path(fp)
    if not ga_date:
        return stats

    ga_num, date_iso = ga_date
    current_ga = (ga_num, date_iso) if date_iso else (ga_num,)

    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(STEINER_GA_DIR)}: {e}")
        return stats

    # Absätze: durch \n\n getrennt
    blocks = re.split(r'\n\s*\n', content)
    new_blocks = []
    changed = False

    # Nur präzise (ga, datum)-Treffer – kein Fallback auf alle Vorträge (zu viele Kandidaten)
    candidates = []
    if current_ga in lectures_idx:
        candidates = list(lectures_idx[current_ga])
    if ga_num in books_idx:
        candidates = candidates + list(books_idx[ga_num])

    if not candidates:
        stats["no_ga"] = len([b for b in blocks if len(b.strip()) > 40])
        return stats

    for block in blocks:
        block = block.rstrip()
        if len(block.strip()) < 40:
            new_blocks.append(block)
            continue

        if block.strip().startswith("#") or block.strip().startswith("<"):
            new_blocks.append(block)
            continue

        has_block_id = bool(re.search(r'\^[a-z0-9]+\s*$', block))
        if has_block_id:
            stats["already"] += 1
            new_blocks.append(block)
            continue

        stats["checked"] += 1
        page_from_cit = extract_citation_page(block)
        block_id = find_best_match(block, candidates, page_from_citation=page_from_cit)
        if block_id:
            new_blocks.append(block.rstrip() + f" ^{block_id}")
            stats["added"] += 1
            changed = True
        else:
            new_blocks.append(block)
            stats["no_match"] += 1

    if apply and changed:
        fp.write_text("\n\n".join(new_blocks), encoding="utf-8")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Fügt Absatz-IDs aus Steiner-GA-JSON ein.")
    parser.add_argument("--apply", action="store_true", help="Änderungen speichern")
    parser.add_argument("--file", type=str, default=None, help="Nur Dateien mit diesem Namen(s)-Teil verarbeiten")
    parser.add_argument("--steiner-ga", action="store_true", help="In Steiner_GA suchen statt Obsidian")
    args = parser.parse_args()

    use_steiner_ga = args.steiner_ga
    if use_steiner_ga and not STEINER_GA_DIR.exists():
        print(f"Steiner_GA nicht gefunden: {STEINER_GA_DIR}")
        return 1
    if not use_steiner_ga and not OBSIDIAN_VAULT.exists():
        print(f"Obsidian-Vault nicht gefunden: {OBSIDIAN_VAULT}")
        return 1

    print("Lade steiner-full-lectures...")
    lectures_idx = load_lectures_index()
    total_paras_lec = sum(len(v) for v in lectures_idx.values())
    print(f"  {len(lectures_idx)} GA+Datum-Keys, {total_paras_lec} Absätze")

    print("Lade steiner-books...")
    books_idx = load_books_index()
    total_paras_book = sum(len(v) for v in books_idx.values())
    print(f"  {len(books_idx)} Bücher, {total_paras_book} Absätze")

    mode = "ANWENDEN" if args.apply else "DRY-RUN (--apply zum Speichern)"
    print(f"\n=== {mode} {'[Steiner_GA]' if use_steiner_ga else ''} ===\n")

    total = {"checked": 0, "added": 0, "already": 0, "no_match": 0, "no_ga": 0}
    files_changed = 0
    base_dir = STEINER_GA_DIR if use_steiner_ga else OBSIDIAN_VAULT

    if use_steiner_ga:
        md_files = sorted(STEINER_GA_DIR.rglob("*.md"))
        process_fn = process_steiner_ga_file
    else:
        md_files = sorted(OBSIDIAN_TOPICS.rglob("*.md")) if OBSIDIAN_TOPICS.exists() else sorted(OBSIDIAN_VAULT.rglob("*.md"))
        process_fn = process_obsidian_file

    for md in md_files:
        if ".backup" in str(md) or md.name.startswith(".") or "chalkboards" in str(md):
            continue
        rel = md.relative_to(base_dir)
        stats = process_fn(md, lectures_idx, books_idx, args.apply, args.file)
        for k in total:
            total[k] += stats[k]
        if stats["added"] > 0:
            files_changed += 1
            print(f"  {rel}: +{stats['added']} IDs")

    print(f"\n=== GESAMT ===")
    print(f"  Geprüft: {total['checked']} | Neu: {total['added']} | Bereits: {total['already']} | Kein Match: {total['no_match']} | Kein GA: {total['no_ga']}")
    if args.apply:
        print(f"  Dateien geändert: {files_changed}")
    else:
        print("  (Dry-Run – keine Änderungen geschrieben)")

    return 0


if __name__ == "__main__":
    exit(main())
