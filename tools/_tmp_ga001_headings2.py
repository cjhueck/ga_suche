import json
from pathlib import Path

book = json.loads(Path("steiner-books/steiner-books-001-001.json").read_text(encoding="utf-8"))["books"][0]
paras = book["paragraphs"]

print("=== paragraphs whose content looks like a heading ===")
for i, p in enumerate(paras):
    c = (p.get("content") or "").strip()
    if c.startswith("#") or c.startswith("DRITTER") or c.startswith("6.") or "Dritter Band" in c or c.startswith("###"):
        print(i, p.get("index"), repr(c[:160]))

print("\n=== paragraph around heading 6 (tgo9hb) ===")
for i, p in enumerate(paras):
    if p.get("index") == "^tgo9hb":
        for j in range(max(0, i - 2), min(len(paras), i + 3)):
            print(j, paras[j].get("index"), repr((paras[j].get("content") or "")[:140]))

print("\n=== summary-db headings around Dritter/6 ===")
# stream just GA001 from summary db via json
# file is huge; load and get key
print("loading summary db (may take a bit)...")
db = json.loads(Path("summary-database.json").read_text(encoding="utf-8"))
hs = db.get("GA001", {}).get("headings", [])
print("count", len(hs))
for i, h in enumerate(hs, 1):
    t = h.get("text") or ""
    if "Band" in t or t.strip().startswith("6") or "Newton" in t or t.strip() in {"6.", "5.", "1."}:
        print(f"{i:3d} {h}")
