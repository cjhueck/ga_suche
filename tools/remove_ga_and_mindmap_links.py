#!/usr/bin/env python3
"""
remove_ga_and_mindmap_links.py
------------------------------
Entfernt das Muster [GA ..., Mindmap PDF]] am Ende von Absätzen,
OHNE die Absatzmarken (^blockid) zu löschen.

Beispiel zu entfernen:
  [GA 226, S. 53-54, 18.05.1923](https://akanthosakademie...), [[Gehen_Sprechen_Denken_mit_Links.pdf|Mindmap PDF]]

Ergebnis: Der vorangehende Text und ggf. ^blockid bleiben erhalten.

Verwendung:
    python tools/remove_ga_and_mindmap_links.py              # Dry-Run
    python tools/remove_ga_and_mindmap_links.py --apply      # Änderungen schreiben
    python tools/remove_ga_and_mindmap_links.py --file "Gedächtnis" --apply  # Nur eine Datei
"""

import re
import argparse
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# Pattern 1: Leerzeichen/Komma, dann [GA ...](url), dann , oder ; dann [[...|Mindmap PDF]]
# Pattern 2: Punkt direkt vor [ (z.B. "vermögen.[ GA 303...]") – Punkt muss erhalten bleiben
# Pattern 3: " GA [266b, ...]" – GA steht außerhalb der Klammer (Gehen-Sprechen-Denken)
PATTERN_STANDARD = re.compile(
    r'[\s,]+\['  # vorangehend: Leerzeichen oder Komma
    r'[\s]*GA\s+\d+[a-z]?[^\]]*\]'  # [GA NNN oder [ GA NNN
    r'\([^)]+\)'
    r'\s*[,;]\s*'
    r'\[\[[^\]]*\|Mindmap PDF\]\]',
    re.UNICODE
)
PATTERN_PUNKT_VOR = re.compile(
    r'\.([\s]*\[[\s]*GA\s+\d+[a-z]?[^\]]*\]\([^)]+\)\s*[,;]\s*\[\[[^\]]*\|Mindmap PDF\]\])',
    re.UNICODE
)
PATTERN_GA_AUSSEN = re.compile(
    r'\s+GA\s+\[\d+[a-z]?[^\]]*\]\([^)]+\)\s*[,;]\s*\[\[[^\]]*\|Mindmap PDF\]\]',
    re.UNICODE
)


def process_file(fp: Path, apply: bool, file_filter: str | None) -> tuple[int, bool]:
    """Entfernt Links, behält ^blockid. Gibt (Anzahl Entfernungen, geändert) zurück."""
    if file_filter and file_filter.lower() not in fp.name.lower():
        return 0, False

    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(OBSIDIAN_VAULT)}: {e}")
        return 0, False

    def replacer_punkt(m):
        return "."

    new_content = PATTERN_STANDARD.sub("", content)
    new_content = PATTERN_PUNKT_VOR.sub(replacer_punkt, new_content)
    new_content = PATTERN_GA_AUSSEN.sub("", new_content)

    # Doppelte Leerzeichen bereinigen
    new_content = re.sub(r'  +', ' ', new_content)

    if new_content != content:
        count = (
            len(PATTERN_STANDARD.findall(content))
            + len(PATTERN_PUNKT_VOR.findall(content))
            + len(PATTERN_GA_AUSSEN.findall(content))
        )
        if apply:
            fp.write_text(new_content, encoding="utf-8")
        return count, True
    return 0, False


def main():
    parser = argparse.ArgumentParser(description="Entfernt [GA...], [[...|Mindmap PDF]] ohne ^blockid zu löschen")
    parser.add_argument("--apply", action="store_true", help="Änderungen speichern")
    parser.add_argument("--file", type=str, default=None, help="Nur Dateien mit diesem Namensteil (z.B. Gedächtnis)")
    args = parser.parse_args()

    if not OBSIDIAN_VAULT.exists():
        print(f"Vault nicht gefunden: {OBSIDIAN_VAULT}")
        return 1

    mode = "ANWENDEN" if args.apply else "DRY-RUN (--apply zum Speichern)"
    print(f"=== {mode} ===\n")

    md_files = sorted(OBSIDIAN_VAULT.rglob("*.md"))
    total_count = 0
    files_changed = 0

    for fp in md_files:
        if ".backup" in str(fp) or fp.name.startswith("."):
            continue
        count, changed = process_file(fp, args.apply, args.file)
        if count > 0:
            total_count += count
            files_changed += 1
            rel = fp.relative_to(OBSIDIAN_VAULT)
            print(f"  {rel}: {count} Links entfernt")

    print(f"\n=== GESAMT: {total_count} Links in {files_changed} Dateien ===")
    if not args.apply and total_count > 0:
        print("  (Dry-Run – keine Änderungen geschrieben)")

    return 0


if __name__ == "__main__":
    exit(main())
