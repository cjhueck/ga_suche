# -*- coding: utf-8 -*-
from pathlib import Path
import re

DE = Path(r"c:\Obsidian\Steiner Goetheanismus\Texte")
EN = Path(r"c:\Obsidian\Steiner Goetheanism\Texts")

# Map by GA prefix
de_files = sorted(DE.glob("*.md"))
en_files = sorted(EN.glob("*.md"))

def ga_key(p: Path) -> str:
    m = re.match(r"(GA \d+|Lecture|Vortrags)", p.name)
    return m.group(1) if m else p.name[:20]

def blocks(text: str):
    # drop footnotes at end
    text = re.split(r"\n\[\^1\]:", text, maxsplit=1)[0]
    parts = re.split(r"\n\s*\n", text)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out

def is_heading(b: str) -> bool:
    return b.startswith("#") or b.startswith("**[[") or b.startswith("[[#")

def body_blocks(blocks_list):
    return [b for b in blocks_list if not is_heading(b) and not b.startswith("**Steiner") and not b.startswith("[ ]")]

print("=== file pair paragraph counts ===")
pairs = []
for df in de_files:
    key = df.name.split(" - ")[0]
    cands = [ef for ef in en_files if ef.name.startswith(key)]
    if key.startswith("Vortrags"):
        cands = [ef for ef in en_files if ef.name.startswith("Lecture")]
    if not cands:
        print("NO EN for", df.name)
        continue
    ef = cands[0]
    db = blocks(df.read_text(encoding="utf-8"))
    eb = blocks(ef.read_text(encoding="utf-8"))
    dbody = body_blocks(db)
    ebody = body_blocks(eb)
    pairs.append((df, ef, db, eb, dbody, ebody))
    print(f"{key:12} DE blocks={len(db):4} body={len(dbody):4} | EN blocks={len(eb):4} body={len(ebody):4}  dbody={len(ebody)-len(dbody):+d}  {ef.name[:50]}")

print("\n=== GA 001 section markers ===")
df = next(DE.glob("GA 001*.md"))
ef = next(EN.glob("GA 001*.md"))
dt = df.read_text(encoding="utf-8")
et = ef.read_text(encoding="utf-8")
dmarks = re.findall(r"\[([IVX]+/\d+)\]", dt)
emarks = re.findall(r"\[([IVX]+/\d+)\]", et)
print("DE marks", len(dmarks), "EN marks", len(emarks))
print("only DE", set(dmarks)-set(emarks))
print("only EN", set(emarks)-set(dmarks))

# Compare paragraph counts between consecutive markers in GA 001
def split_by_markers(text):
    parts = re.split(r"(?=^\[[IVX]+/\d+\])", text, flags=re.M)
    return parts

print("\n=== GA 001 paras per marker (first mismatches) ===")
dparts = split_by_markers(dt)
eparts = split_by_markers(et)
# skip preamble
print("dparts", len(dparts), "eparts", len(eparts))

def nparas(s):
    return len([p for p in re.split(r"\n\s*\n", s) if p.strip()])

mism = 0
for i, (dp, ep) in enumerate(zip(dparts[1:], eparts[1:])):
    nd, ne = nparas(dp), nparas(ep)
    dm = re.match(r"\[([IVX]+/\d+)\]", dp)
    em = re.match(r"\[([IVX]+/\d+)\]", ep)
    if nd != ne or (dm and em and dm.group(1) != em.group(1)):
        mism += 1
        if mism <= 25:
            print(f"  {dm.group(1) if dm else '?'} vs {em.group(1) if em else '?'}  DE={nd} EN={ne}")
print("total marker mismatches", mism, "of", min(len(dparts), len(eparts))-1)
