#!/usr/bin/env python3
"""
restore_from_backup.py
=====================
Stellt MD-Dateien aus .backup wieder her (überschreibt die aktuelle Datei).

Verwendung:
    python tools/restore_from_backup.py              # Dry-Run (zeigt nur an)
    python tools/restore_from_backup.py --apply      # Wiederherstellung durchführen
"""

import shutil
import argparse
from pathlib import Path

OBSIDIAN_VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")
OBSIDIAN_TOPICS = OBSIDIAN_VAULT / "I. Themen"


def main():
    parser = argparse.ArgumentParser(description="Stellt Dateien aus .backup wieder her.")
    parser.add_argument("--apply", action="store_true", help="Wiederherstellung durchführen")
    args = parser.parse_args()

    if not OBSIDIAN_VAULT.exists():
        print(f"Vault nicht gefunden: {OBSIDIAN_VAULT}")
        return 1

    backups = list(OBSIDIAN_VAULT.rglob("*.md.backup"))
    if not backups:
        print("Keine .backup-Dateien gefunden.")
        return 0

    mode = "ANWENDEN" if args.apply else "DRY-RUN (--apply zum Wiederherstellen)"
    print(f"=== {mode} ===\n")
    print(f"Gefunden: {len(backups)} Backup-Dateien\n")

    for bp in sorted(backups):
        # file.md.backup -> file.md
        target = bp.parent / bp.stem  # stem = "file.md" für "file.md.backup"
        rel = bp.relative_to(OBSIDIAN_VAULT)
        if args.apply:
            shutil.copy2(bp, target)
            print(f"  [OK] {rel} -> {target.name}")
        else:
            print(f"  Würde: {target.name} aus Backup wiederherstellen")

    if not args.apply:
        print("\n  (Dry-Run – keine Änderungen; --apply zum Wiederherstellen)")

    return 0


if __name__ == "__main__":
    exit(main())
