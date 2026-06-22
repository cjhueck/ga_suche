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
import sys
import time

import requests

DB = "concepts-database.json"
API = "http://localhost:3003/api/concepts-batch-add"

block_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 5


def load_normal():
    with open(DB, encoding="utf-8") as f:
        data = json.load(f)
    normal = [c.get("keyword") for c in data
              if c.get("promptVersion") != "concept-v1" and c.get("keyword")]
    return len(data), normal


def main():
    total, normal = load_normal()
    print("DB gesamt: %d | normal (offen): %d" % (total, len(normal)))
    if not normal:
        print("Fertig - keine normalen Schlagwoerter mehr.")
        return
    block = normal[:block_size]
    print("Verarbeite Block: %d Schlagwoerter (concurrency=%d)" % (len(block), concurrency))
    print("  erste:", ", ".join(block[:5]), "..." if len(block) > 5 else "")
    t0 = time.time()
    try:
        r = requests.post(API, json={"keywords": block, "overwrite": True,
                                     "concurrency": concurrency}, timeout=3600)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print("FEHLER beim Request:", e)
        return
    res = j.get("results", {})
    ok = res.get("successful", [])
    fail = res.get("failed", [])
    skip = res.get("skipped", [])
    dur = time.time() - t0
    print("Server:", j.get("message"))
    print("  erfolgreich: %d | fehlgeschlagen: %d | uebersprungen: %d | %.0fs"
          % (len(ok), len(fail), len(skip), dur))
    for fobj in fail:
        print("  FAIL:", fobj.get("keyword"), "-", fobj.get("reason"))
    # Restbestand neu berechnen
    _, normal_after = load_normal()
    print("VERBLEIBEND normal:", len(normal_after))


if __name__ == "__main__":
    main()
