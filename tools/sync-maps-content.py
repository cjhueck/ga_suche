"""
sync-maps-content.py
--------------------
Kopiert Obsidian-Markdown-Dateien nach maps-content/ im ga_suche-Repo.
Ausführen nach Änderungen in Obsidian, dann git add + push.

Verwendung:
    python tools/sync-maps-content.py
    python tools/sync-maps-content.py --dry-run   (nur anzeigen, nicht kopieren)
"""

import os
import shutil
import argparse
from pathlib import Path

# Basis-Pfad des Obsidian-Vaults
OBSIDIAN_BASE = Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Obsidian" / "Obsidian Entwicklungsanthropologie"

# Ausgabe-Ordner (relativ zum Skript → maps-content/ im Repo-Root)
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "maps-content"

# Mapping: PDF-Name (ohne .pdf) → Obsidian-Pfad (relativ zu OBSIDIAN_BASE)
MAPPING = {
    "Rhythmisches_System":
        "I. Themen/Dreigliederung/Rhythmisches System.md",
    "Nerven-Sinnessystem":
        "I. Themen/Dreigliederung/Nerven-Sinnessystem.md",
    "Stoffwechsel-Gliedmaensystem":
        "I. Themen/Dreigliederung/Stoffwechsel-Gliedmaßensystem.md",
    "Seelische_Entwicklung_des_Kindes":
        "I. Themen/Denken - Fühlen - Wollen/Seelische Entwicklung.md",
    "Gedächtnisentwicklung_des_Kindes":
        "I. Themen/Gedächtnisentwicklung/Gedächtnis Zitate.md",
    "Gehen_Sprechen_Denken":
        "I. Themen/Gehen - Sprechen - Denken/Gehen - Sprechen - Denken Zitate.md",
    "Modellleib":
        "I. Themen/Modellleib/Modellleib Zitate.md",
    "Modellleib_chronologisch":
        "I. Themen/Modellleib/Modellleib Zitate.md",
    "Nachahmung":
        "I. Themen/Nachahmung/Nachahmung Zitate.md",
    "Nachahmung_-_Nachfolge_-_Freiheit":
        "I. Themen/Nachahmung - Nachfolge - Freiheit/Nachahmung - Nachfolge - Freiheit.md",
    "Phantasie":
        "I. Themen/Phantasie/Phantasie Zitate.md",
    "Pubertät":
        "I. Themen/Pubertät/Pubertät Zitate.md",
    "Pubertät_-_Entwicklung":
        "I. Themen/Pubertät - Entwicklung/Pubertät - Entwicklung Zitate.md",
    "Reinkarnations-Metamorphose":
        "I. Themen/Reinkarnation/Reinkarnationsmetamorphose.md",
    "Rubikon":
        "I. Themen/Rubikon/Rubikon Zitate.md",
    "Urteilskraft":
        "I. Themen/Urteilskraft/Urteilskraft Zitate.md",
    "Wirkungen_der_Erziehung_im_Lebenslauf":
        "I. Themen/Wirkungen im Lebenslauf/Wirkungen... Zitate.md",
    "Zahnwechsel":
        "I. Themen/Zahnwechsel/Zahnwechsel Zitate.md",
}


def sync(dry_run=False):
    OUTPUT_DIR.mkdir(exist_ok=True)
    ok = skipped = errors = 0

    for map_id, rel_path in MAPPING.items():
        src = OBSIDIAN_BASE / rel_path.replace("/", os.sep)
        dst = OUTPUT_DIR / (map_id + ".md")

        if not src.exists():
            print(f"  [FEHLT]   {map_id}  ({src})")
            errors += 1
            continue

        # Nur kopieren wenn Quell-Datei neuer oder Ziel fehlt
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            print(f"  [OK]      {map_id}  (unveraendert)")
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] {map_id}  {src.name} -> {dst.name}")
        else:
            shutil.copy2(src, dst)
            print(f"  [KOPIERT] {map_id}  {src.name} -> {dst.name}")
        ok += 1

    print()
    print(f"Ergebnis: {ok} kopiert, {skipped} unveraendert, {errors} fehlend")
    if errors:
        print("Tipp: Fehlende Dateien im MAPPING in diesem Skript pruefen.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obsidian -> maps-content/ Sync")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht kopieren")
    args = parser.parse_args()

    print(f"Obsidian-Vault: {OBSIDIAN_BASE}")
    print(f"Ausgabe:        {OUTPUT_DIR}")
    print()
    sync(dry_run=args.dry_run)
