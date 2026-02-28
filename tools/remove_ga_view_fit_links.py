#!/usr/bin/env python3
"""
remove_ga_view_fit_links.py
---------------------------
Entfernt GA-Links mit view=Fit-URL (akanthosakademie PDF-Links) komplett.
Link und Zitation werden gelöscht.

Beispiel:
  Vorher: ...Urteilskraft. [GA 097, S. 168–169, 04.04.1906](https://akanthosakademie...view=Fit)
  Nachher: ...Urteilskraft.

Verwendung:
    python tools/remove_ga_view_fit_links.py              # Dry-Run
    python tools/remove_ga_view_fit_links.py --apply     # Änderungen schreiben
"""

import re
import argparse
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# [GA NNN, S. X-Y, DD.MM.YYYY](...view=Fit) – komplett entfernen
PATTERN = re.compile(
    r'[\s,]*\[[\s]*GA\s+\d+[a-z]?[^\]]*\]\([^)]*view=Fit\)',
    re.UNICODE
)

# GA [266b, ...](...view=Fit) – GA steht außerhalb
PATTERN_GA_AUSSEN = re.compile(
    r'\s+GA\s+\[\d+[a-z]?[^\]]*\]\([^)]*view=Fit\)',
    re.UNICODE
)

# Bereinigung: versehentlich als Text hinterlassene GA-Zitationen entfernen
# Format: " GA 097, S. 168–169, 04.04.1906" oder " GA 266b, S. 77–78, 04.11.1910"
PATTERN_CLEANUP = re.compile(
    r'\s+GA\s+\d+[a-z]?,\s*S\.\s*\d+(?:[–\-]\d+)?,\s*\d{2}\.\d{2}\.\d{4}',
    re.UNICODE
)


def process_file(fp: Path, apply: bool, file_filter: str | None) -> tuple[int, bool]:
    if file_filter and file_filter.lower() not in fp.name.lower():
        return 0, False

    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(OBSIDIAN_VAULT)}: {e}")
        return 0, False

    new_content = PATTERN.sub("", content)
    new_content = PATTERN_GA_AUSSEN.sub("", new_content)
    new_content = PATTERN_CLEANUP.sub("", new_content)
    new_content = re.sub(r'  +', ' ', new_content)

    if new_content != content:
        count = (
            len(PATTERN.findall(content))
            + len(PATTERN_GA_AUSSEN.findall(content))
            + len(PATTERN_CLEANUP.findall(content))
        )
        if apply:
            fp.write_text(new_content, encoding="utf-8")
        return count, True
    return 0, False


def main():
    parser = argparse.ArgumentParser(description="Entfernt GA view=Fit-Links, behält Zitation als Text")
    parser.add_argument("--apply", action="store_true", help="Änderungen speichern")
    parser.add_argument("--file", type=str, default=None, help="Nur Dateien mit diesem Namensteil")
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
