# -*- coding: utf-8 -*-
"""Fetch GA lectures and write cleaned markdown bodies for vault import."""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://localhost:3003"
OUT = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\_tmp_ga_export")
OUT.mkdir(exist_ok=True)

IDS = [
    "GA030/8", "GA030/42", "GA030/43",
    "GA035/2",
    "GA036/31", "GA036/35",
    "GA068c/6", "GA068c/11", "GA068c/17",
    "GA067/3",
    "GA061/4",
    "GA064/1",
    "GA065/1",
    "GA277/13", "GA277/16", "GA277/20", "GA277/30",
    "GA075/3",
]

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def html_to_text(s):
    s = s or ""
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def paras_to_md(lecture):
    paras = lecture.get("paragraphs") or []
    lines = []
    for p in paras:
        content = p.get("content") or p.get("text") or ""
        txt = html_to_text(content)
        if not txt:
            continue
        # skip page-only markers
        if re.fullmatch(r"\|<?\d+>?\|", txt):
            continue
        lines.append(txt)
    return "\n\n".join(lines)

bib = json.load(open(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\ga-bibliography.json", encoding="utf-8"))

index = []
for lid in IDS:
    ga, num = lid.split("/", 1)
    url = f"{BASE}/api/full-lecture/{urllib.parse.quote(ga)}/{urllib.parse.quote(num)}"
    try:
        data = get(url)
    except Exception as e:
        print("FAIL", lid, e)
        continue
    lec = data.get("lecture") or data
    md = paras_to_md(lec)
    title = lec.get("title") or ""
    date = lec.get("date") or ""
    loc = lec.get("location") or ""
    fn = OUT / (lid.replace("/", "_") + ".md")
    fn.write_text(md, encoding="utf-8")
    vol = bib.get(ga) or bib.get(ga.replace("GA0", "GA")) or {}
    rec = {
        "id": lid,
        "title": title,
        "date": date,
        "location": loc,
        "chars": len(md),
        "paras": md.count("\n\n") + (1 if md else 0),
        "file": str(fn),
        "bandTitle": vol.get("title") or lec.get("bandTitle") or lec.get("gaTitle") or "",
        "subtitle": vol.get("subtitle") or vol.get("titleSupplement") or "",
        "year": vol.get("year") or "",
        "edition": vol.get("edition") or "",
        "place": vol.get("place") or "",
        "publisher": vol.get("publisher") or "",
        "originalPublication": vol.get("originalPublication") or "",
    }
    index.append(rec)
    print(f"{lid}\t{date}\t{len(md):6d}c\t{rec['paras']:3d}p\t{title[:70]}")

(OUT / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", len(index), "files to", OUT)
