#!/usr/bin/env python3
"""
restore_heading_block_ids.py
============================
Fügt fehlende Obsidian-Block-IDs (^xyz) an Überschriften (H1–H5) wieder ein.

Betrifft:
- Markdown: #, ##, ###, ####, #####
- HTML: <H1>...</H1>, <H2>...</H2>, …, <H5>...</H5>

Verwendung:
    python tools/restore_heading_block_ids.py              # Dry-Run
    python tools/restore_heading_block_ids.py --apply     # Änderungen schreiben
"""

import re
import argparse
import secrets
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")
OBSIDIAN_TOPICS = OBSIDIAN_VAULT / "I. Themen"

# Markdown-Überschrift: # bis #####, optional Leerzeichen, Inhalt
MD_HEADING_RE = re.compile(r'^(#{1,5})\s+(.+)$')

# HTML-Überschrift: <H1>...</H1> etc.
HTML_HEADING_RE = re.compile(r'^(<H[1-5])>(.+?)</H[1-5]>(\s*)$', re.IGNORECASE)

# Bereits Block-ID am Ende?
BLOCK_ID_RE = re.compile(r'\^[a-z0-9]{6}\s*$')


def gen_block_id(seen: set) -> str:
    """Erzeugt eindeutige Obsidian-Block-ID (6 Zeichen a-z0-9)."""
    for _ in range(100):
        uid = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))
        if uid not in seen:
            seen.add(uid)
            return uid
    raise RuntimeError("Konnte keine eindeutige Block-ID erzeugen")


def process_file(fp: Path, apply: bool) -> tuple[int, bool]:
    """
    Verarbeitet eine MD-Datei. Gibt (Anzahl hinzugefügter IDs, ob geändert) zurück.
    """
    try:
        content = fp.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ {fp.relative_to(OBSIDIAN_VAULT)}: {e}")
        return 0, False

    lines = content.splitlines(keepends=True)
    seen_ids: set[str] = set()
    new_lines = []
    added = 0
    changed = False

    for line in lines:
        stripped = line.rstrip("\r\n")

        # Markdown-Überschrift?
        md_m = MD_HEADING_RE.match(stripped)
        if md_m:
            if BLOCK_ID_RE.search(stripped):
                new_lines.append(line)
                continue
            block_id = gen_block_id(seen_ids)
            new_lines.append(stripped.rstrip() + f" ^{block_id}\n")
            added += 1
            changed = True
            continue

        # HTML-Überschrift?
        html_m = HTML_HEADING_RE.match(stripped)
        if html_m:
            tag_open, inner, trailing = html_m.groups()
            if BLOCK_ID_RE.search(stripped):
                new_lines.append(line)
                continue
            tag_num = tag_open[-1].upper()
            block_id = gen_block_id(seen_ids)
            new_lines.append(f"{tag_open}>{inner}</H{tag_num}> ^{block_id}{trailing}\n")
            added += 1
            changed = True
            continue

        new_lines.append(line)

    if apply and changed:
        fp.write_text("".join(new_lines), encoding="utf-8")

    return added, changed


def main():
    parser = argparse.ArgumentParser(description="Fügt Block-IDs an Überschriften H1–H5 wieder ein.")
    parser.add_argument("--apply", action="store_true", help="Änderungen speichern")
    args = parser.parse_args()

    if not OBSIDIAN_VAULT.exists():
        print(f"Vault nicht gefunden: {OBSIDIAN_VAULT}")
        return 1

    if OBSIDIAN_TOPICS.exists():
        md_files = sorted(OBSIDIAN_TOPICS.rglob("*.md"))
    else:
        md_files = sorted(OBSIDIAN_VAULT.rglob("*.md"))

    mode = "ANWENDEN" if args.apply else "DRY-RUN (--apply zum Speichern)"
    print(f"=== {mode} ===\n")

    total_added = 0
    files_changed = 0

    for md in md_files:
        if ".backup" in str(md) or md.name.startswith("."):
            continue
        added, changed = process_file(md, args.apply)
        if added > 0:
            total_added += added
            files_changed += 1
            rel = md.relative_to(OBSIDIAN_VAULT)
            print(f"  {rel}: +{added} IDs")

    print(f"\n=== GESAMT: {total_added} IDs in {files_changed} Dateien ===")
    if not args.apply and total_added > 0:
        print("  (Dry-Run – keine Änderungen geschrieben)")

    return 0


if __name__ == "__main__":
    exit(main())
