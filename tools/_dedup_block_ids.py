# -*- coding: utf-8 -*-
"""
Entfernt 'doppelte' Absatz-IDs: Wenn direkt nach einer Zeile, die mit einer
Block-ID endet, eine Zeile folgt, die NUR aus einer Block-ID besteht, wird
diese reine ID-Zeile geloescht (die 'zweite' ID).

Aufruf:
    python tools/_dedup_block_ids.py "<pfad>"          # Trockenlauf
    python tools/_dedup_block_ids.py "<pfad>" --apply   # anwenden
"""
import re
import sys
import os

path = sys.argv[1]
apply = "--apply" in sys.argv

ID_ONLY = re.compile(r"^\s*\^[A-Za-z0-9_-]+\s*$")
ENDS_WITH_ID = re.compile(r"\^[A-Za-z0-9_-]+\s*$")

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
removed = []
kept_standalone = []
prev_nonblank = None  # zuletzt behaltene nicht-leere Zeile (ohne Zeilenumbruch)

for i, line in enumerate(lines):
    stripped = line.rstrip("\n")
    if ID_ONLY.match(stripped):
        # Vorherige nicht-leere (behaltene) Zeile endet mit ID?
        if prev_nonblank is not None and ENDS_WITH_ID.search(prev_nonblank):
            removed.append((i + 1, stripped.strip()))
            continue  # zweite ID -> loeschen
        else:
            kept_standalone.append((i + 1, stripped.strip()))
    out.append(line)
    if stripped.strip() != "":
        prev_nonblank = stripped

print("Datei:", os.path.basename(path))
print("Zeilen:", len(lines))
print("Zu entfernende doppelte ID-Zeilen:", len(removed))
for ln, t in removed[:20]:
    print("   - Zeile", ln, ":", t)
if len(removed) > 20:
    print("   ... und", len(removed) - 20, "weitere")
print("Behaltene Einzel-ID-Zeilen (KEINE vorangehende ID -> nicht geloescht):", len(kept_standalone))
for ln, t in kept_standalone[:10]:
    print("   ? Zeile", ln, ":", t)

if apply and removed:
    bak = path + ".bak"
    if not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f:
            f.writelines(lines)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(out)
    os.replace(tmp, path)
    print("ANGEWENDET. Backup:", os.path.basename(bak))
elif apply:
    print("Nichts zu tun.")
else:
    print("(Trockenlauf - nichts geaendert. Mit --apply anwenden.)")
