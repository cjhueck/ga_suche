"""
remove-ga-citation-links.py
---------------------------
Entfernt GA-Quellenangaben als Markdown-Links aus Obsidian-Dateien:

  [GA 170, S. 222; 28.08.1916](http://localhost:3003/goto.html#...)
  [GA 109, S. 207; 07.06.1919](http://localhost:3003/goto.html#...)
  [GA 045, S. 129–131](https://akanthosakademie.files.wordpress.com/...)

- Am Ende von Absätzen (mit vorangehendem Leerzeichen, Komma oder Semikolon)
- Ganze Zeilen, die nur aus dem Link bestehen

Verwendung:
    python tools/remove-ga-citation-links.py --dry-run
    python tools/remove-ga-citation-links.py
"""

import re
import argparse
from pathlib import Path

VAULT = Path(r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Entwicklungsanthropologie")

# GA-Link: [GA NNN, S. XXX; DD.MM.YYYY](url) oder [GA NNN, S. XXX–YYY](url)
GA_LINK = r'\[GA\s+\d+[^\]]*\]\([^)]+\)'

# Am Ende von Absätzen: vorangehend , ; oder Leerzeichen
PATTERN_INLINE = re.compile(
    r'([,;]\s*| )' + GA_LINK,
    re.UNICODE
)

# Fallback: alle verbleibenden GA-Links (z.B. nach Gedankenstrich, Klammer)
PATTERN_ANY = re.compile(GA_LINK, re.UNICODE)

# Ganze Zeile nur mit Link
PATTERN_LINE = re.compile(
    r'^\s*' + GA_LINK + r'\s*$',
    re.MULTILINE | re.UNICODE
)

def process_file(fp: Path, dry_run: bool) -> bool:
    """Gibt True zurück wenn Änderungen vorgenommen wurden."""
    content = fp.read_text(encoding='utf-8')
    original = content

    # 1. Inline-Links entfernen (mit vorangehendem , ; oder Leerzeichen)
    content = PATTERN_INLINE.sub('', content)

    # 2. Standalone-Zeilen entfernen
    content = PATTERN_LINE.sub('', content)

    # 3. Verbleibende GA-Links (z.B. nach Klammer, Gedankenstrich)
    content = PATTERN_ANY.sub('', content)

    # 4. Mehrfache Leerzeilen auf max. 2 reduzieren (optional)
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    if content != original:
        if dry_run:
            print(f"  [DRY-RUN] {fp.relative_to(VAULT)}")
        else:
            fp.write_text(content, encoding='utf-8')
            print(f"  [GEÄNDERT] {fp.relative_to(VAULT)}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Entfernt GA-Citation-Links aus Obsidian")
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
