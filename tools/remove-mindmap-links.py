"""
remove-mindmap-links.py
----------------------
Entfernt aus Obsidian-Markdown-Dateien am Ende von Absätzen das Muster:
  ; [[X_mit_Links.pdf|Mindmap PDF]]
  , [[X_mit_Links.pdf|Mindmap PDF]]

Verwendung:
    python tools/remove-mindmap-links.py --dry-run   (nur anzeigen)
    python tools/remove-mindmap-links.py             (aendern)
"""

import re
import argparse
from pathlib import Path

VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# Entfernt: ; [[X_mit_Links.pdf|Mindmap PDF]] oder , [[X_mit_Links.pdf|Mindmap PDF]]
PATTERN = re.compile(
    r'[;,]\s*\[\[[^\]]*_mit_Links\.pdf\|Mindmap PDF\]\]',
    re.UNICODE
)

def process_file(fp: Path, dry_run: bool) -> bool:
    """Gibt True zurück wenn Änderungen vorgenommen wurden."""
    content = fp.read_text(encoding='utf-8')
    new_content = PATTERN.sub('', content)
    if new_content != content:
        if dry_run:
            print(f"  [DRY-RUN] {fp.relative_to(VAULT)}")
        else:
            fp.write_text(new_content, encoding='utf-8')
            print(f"  [GEÄNDERT] {fp.relative_to(VAULT)}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Entfernt Mindmap-PDF-Links aus Obsidian")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht ändern")
    args = parser.parse_args()

    if not VAULT.exists():
        print(f"Vault nicht gefunden: {VAULT}")
        return 1

    changed = 0
    for md in VAULT.rglob("*.md"):
        if md.suffix != ".md" or ".backup" in str(md):
            continue
        if process_file(md, args.dry_run):
            changed += 1

    print()
    print(f"Ergebnis: {changed} Dateien {'würden geändert' if args.dry_run else 'geändert'}")
    return 0

if __name__ == "__main__":
    exit(main())
