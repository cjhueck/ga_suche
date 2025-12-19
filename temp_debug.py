#!/usr/bin/env python3
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def normalize_text(text):
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", text)
    s = s.replace("\u00ad", "").replace("\u00a0", " ")
    s = s.lower().replace("ß", "ss")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Lade GA153 Vorträge
for path in SCRIPT_DIR.glob("steiner-full-lectures-*.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lectures = data.get("lectures") or []
    for lec in lectures:
        if (lec.get("gaNumber") or "").upper() == "GA153":
            lec_id = lec.get("ID") or ""
            if lec_id in ["GA153/1", "GA153/2"]:
                print(f"\n=== {lec_id}: {lec.get('title')} ===")
                paragraphs = lec.get("paragraphs") or []
                collected = []
                for i, para in enumerate(paragraphs[:10]):
                    content = para.get("content") or ""
                    normalized = normalize_text(content)
                    print(f"  Absatz {i}: {len(normalized)} Zeichen: {normalized[:80]}...")
                    if len(normalized) >= 30:
                        collected.append(normalized)
                        combined = " ".join(collected)
                        has_punct = any(p in combined for p in ['. ', ', ', '; ', ': '])
                        print(f"    -> Gesamt: {len(combined)} Zeichen, Satzzeichen: {has_punct}")
                        if len(combined) >= 200 and has_punct:
                            print(f"    -> VERWENDE DIESEN TEXT!")
                            break
