# -*- coding: utf-8 -*-
import json, re, urllib.parse, urllib.request
from pathlib import Path

BASE = "http://localhost:3003"
OUT = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\_tmp_ga_export")
bib = json.load(open(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\ga-bibliography.json", encoding="utf-8"))

IDS = [
    "GA030/8","GA030/42","GA030/43","GA035/2","GA036/31","GA036/35",
    "GA068c/6","GA068c/11","GA067/3","GA277/13","GA277/16","GA277/20","GA277/30",
]

def get(url):
    req = urllib.request.Request(url, headers={"Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def html_to_text(s):
    s = s or ""
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&nbsp;"," ").replace("&amp;","&").replace("&lt;","<")
           .replace("&gt;",">").replace("&quot;",'"'))
    return re.sub(r"\s+", " ", s).strip()

meta = []
for lid in IDS:
    ga, num = lid.split("/", 1)
    data = get(f"{BASE}/api/full-lecture/{urllib.parse.quote(ga)}/{urllib.parse.quote(num)}")
    lec = data.get("lecture") or data
    pages = []
    paras = []
    for p in lec.get("paragraphs") or []:
        raw = p.get("content") or ""
        pages += [int(x) for x in re.findall(r"\|<?(\d+)>?\|", raw)]
        t = html_to_text(raw)
        t = re.sub(r"\|<?\d+>?\|", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            paras.append(t)
    vol = bib.get(ga) or {}
    rec = {
        "id": lid,
        "title": lec.get("title"),
        "date": lec.get("date"),
        "location": lec.get("location"),
        "fileName": lec.get("fileName"),
        "bandTitle": lec.get("bandTitle") or lec.get("gaTitle") or vol.get("title"),
        "pages": (min(pages), max(pages)) if pages else None,
        "nparas": len(paras),
        "preview": paras[0][:280] if paras else "",
        "keys": sorted(lec.keys()),
    }
    meta.append(rec)
    print("="*60)
    print(json.dumps({k: rec[k] for k in rec if k != "keys"}, ensure_ascii=False, indent=2)[:1200])

(OUT/"_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
