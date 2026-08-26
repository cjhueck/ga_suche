import json
from pathlib import Path

p = Path("steiner-books/steiner-books-001-001.json")
data = json.loads(p.read_text(encoding="utf-8"))
book = data["books"][0]
print("file", book.get("fileName"))
print("n headings", len(book.get("headings") or []))
print("n paragraphs", len(book.get("paragraphs") or []))
print()
print("=== ALL HEADINGS ===")
for i, h in enumerate(book.get("headings") or [], 1):
    hid = h.get("id", "")
    text = h.get("text", "")
    print(f"{i:3d} L{h.get('level')} id={hid:12s}  {text!r}")

print()
print("=== Heading 6 and Band-related paragraphs nearby ===")
paras = book.get("paragraphs") or []
id_to_i = {para.get("index"): i for i, para in enumerate(paras)}
for h in book.get("headings") or []:
    t = h.get("text") or ""
    if "Band" in t or t.strip() in {"6.", "6"} or t.startswith("6."):
        idx = h.get("id")
        pi = id_to_i.get(idx)
        snippet = ""
        if pi is not None:
            snippet = (paras[pi].get("content") or "")[:120]
        print(f"HEAD {t!r} -> {idx} para#{pi} snippet={snippet!r}")
