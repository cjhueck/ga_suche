#!/usr/bin/env python3
"""
remove_mindmap_links_only.py
----------------------------
Entfernt NUR den Mindmap-PDF-Link mit vorangehendem Komma oder Semikolon.
GA-Quellenlinks und Absatzmarken (^blockid) bleiben unverändert.

Zu entfernen: , [[...|Mindmap PDF]] oder ; [[...|Mindmap PDF]]

Verwendung:
    python tools/remove_mindmap_links_only.py              # Dry-Run
    python tools/remove_mindmap_links_only.py --apply      # Änderungen schreiben
"""

import re
import argparse
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# Nur Mindmap-Teil: Komma oder Semikolon + optionales Leerzeichen + [[...|Mindmap PDF]]
# Erhält davor: GA-Link, ^blockid (steht danach auf derselben Zeile)
PATTERN = re.compile(
    r'\s*[,;]\s*\[\[[^\]]*\|Mindmap PDF\]\]',
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

    matches = PATTERN.findall(content)
    count = len(matches)
    if count == 0:
        return 0, False

    new_content = PATTERN.sub("", content)
    if apply:
        fp.write_text(new_content, encoding="utf-8")
    return count, True


def main():
    parser = argparse.ArgumentParser(description="Entfernt nur Mindmap PDF-Links, behält GA-Links und Absatzmarken")
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
            print(f"  {rel}: {count} Mindmap-Links entfernt")

    print(f"\n=== GESAMT: {total_count} Mindmap-Links in {files_changed} Dateien ===")
    if not args.apply and total_count > 0:
        print("  (Dry-Run – keine Änderungen geschrieben)")

    return 0


if __name__ == "__main__":
    exit(main())
