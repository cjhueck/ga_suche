#!/usr/bin/env python3
"""
remove_localhost_links.py
-------------------------
Entfernt nur die URL bei GA-Quellenangaben (localhost und akanthosakademie PDF).
Die Quellenangabe [GA 307, S. 87; 09.08.1923] bleibt stehen.

Beispiele:
  localhost: [GA 307, S. 87; 09.08.1923](http://localhost:3003/goto.html#ga=307&...)
  akanthosakademie: [GA 296, S. 71, 15.08.1919](https://akanthosakademie.../ga296.pdf#page=71&view=Fit)

Verwendung:
    python tools/remove_localhost_links.py              # Dry-Run
    python tools/remove_localhost_links.py --apply     # Änderungen schreiben
"""

import re
import argparse
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# (http://localhost:3003/...) – nur die URL-Klammer entfernen, Quellenangabe bleibt
PATTERN_LOCALHOST = re.compile(r'\(http://localhost:3003/[^)]+\)')

# (https://akanthosakademie.files.wordpress.com/...pdf#page=...&view=Fit) – nur die URL entfernen
PATTERN_AKANTHOS = re.compile(r'\(https://akanthosakademie\.files\.wordpress\.com/[^)]+\)')


def process_file(fp: Path, apply: bool, file_filter: str | None) -> tuple[int, bool]:
    if file_filter and file_filter.lower() not in fp.name.lower():
        return 0, False

    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(OBSIDIAN_VAULT)}: {e}")
        return 0, False

    new_content = content
    new_content = PATTERN_LOCALHOST.sub("", new_content)
    new_content = PATTERN_AKANTHOS.sub("", new_content)

    count = (
        len(PATTERN_LOCALHOST.findall(content))
        + len(PATTERN_AKANTHOS.findall(content))
    )
    if count == 0:
        return 0, False

    if apply:
        fp.write_text(new_content, encoding="utf-8")
    return count, True


def main():
    parser = argparse.ArgumentParser(
        description="Entfernt localhost-Links, behält Quellenangabe [GA ...]"
    )
    parser.add_argument("--apply", action="store_true", help="Änderungen speichern")
    parser.add_argument(
        "--file", type=str, default=None, help="Nur Dateien mit diesem Namensteil"
    )
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
