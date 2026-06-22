# -*- coding: utf-8 -*-
"""
Wandelt 'normale' Schlagwoerter (ohne promptVersion 'concept-v1') in die
ausfuehrliche/kursive Variante um, indem sie ueber den laufenden Server neu
generiert werden (/api/concepts-batch-add, overwrite=true).

Verarbeitet pro Aufruf einen Block (Standard 50). Idempotent: bereits
konvertierte (concept-v1) werden automatisch uebersprungen, einfach erneut
aufrufen, bis 0 verbleiben.

Aufruf:
    python tools/regen_concepts_block.py            # 50, concurrency 5
    python tools/regen_concepts_block.py 50 5
"""
import json
import os
import sys
import time

import requests

DB = "concepts-database.json"
API = "http://localhost:3003/api/concepts-batch-add"
SKIP_FILE = os.path.join(os.path.dirname(__file__), "concepts_skip.json")

# Aufruf: python regen_concepts_block.py [block_size] [concurrency] [loop]
args = [a for a in sys.argv[1:] if a.lower() != "loop"]
loop_mode = "loop" in [a.lower() for a in sys.argv[1:]]
block_size = int(args[0]) if len(args) > 0 else 50
concurrency = int(args[1]) if len(args) > 1 else 5

PERM_FAIL = "keine relevanten textstellen"  # diese sind nicht generierbar -> skip


def load_skip():
    try:
        with open(SKIP_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_skip(s):
    with open(SKIP_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(s), f, ensure_ascii=False, indent=2)


def load_normal(skip):
    with open(DB, encoding="utf-8") as f:
        data = json.load(f)
    normal = [c.get("keyword") for c in data
              if c.get("promptVersion") != "concept-v1" and c.get("keyword")
              and c.get("keyword") not in skip]
    return len(data), normal


def run_block(skip):
    total, normal = load_normal(skip)
    if not normal:
        print("Fertig - keine (generierbaren) normalen Schlagwoerter mehr.")
        return 0, skip
    block = normal[:block_size]
    print("Block: %d Woerter (concurrency=%d) | offen: %d | skip: %d"
          % (len(block), concurrency, len(normal), len(skip)))
    print("  erste:", ", ".join(block[:5]))
    t0 = time.time()
    try:
        r = requests.post(API, json={"keywords": block, "overwrite": True,
                                     "concurrency": concurrency}, timeout=3600)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print("FEHLER beim Request:", e)
        return -1, skip
    res = j.get("results", {})
    ok = res.get("successful", [])
    fail = res.get("failed", [])
    dur = time.time() - t0
    # Dauer-Fehlschlaege (keine Textstellen) auf Skip-Liste
    new_skips = 0
    for fobj in fail:
        kw = fobj.get("keyword")
        reason = (fobj.get("reason") or "").lower()
        if kw and PERM_FAIL in reason:
            skip.add(kw)
            new_skips += 1
    save_skip(skip)
    print("  OK: %d | FAIL: %d (davon %d auf Skip) | %.0fs"
          % (len(ok), len(fail), new_skips, dur))
    _, normal_after = load_normal(skip)
    print("  VERBLEIBEND (generierbar):", len(normal_after))
    return len(normal_after), skip


def main():
    skip = load_skip()
    if loop_mode:
        block_num = 0
        while True:
            block_num += 1
            print("==== Block #%d ====" % block_num)
            remaining, skip = run_block(skip)
            if remaining <= 0:
                break
            time.sleep(2)
        print("LOOP FERTIG nach %d Bloecken. Skip-Liste: %d" % (block_num, len(skip)))
    else:
        run_block(skip)


if __name__ == "__main__":
    main()
