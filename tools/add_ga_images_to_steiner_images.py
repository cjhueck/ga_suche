#!/usr/bin/env python3
"""
Fügt Abbildungen aus Steiner_GA (GA295, GA306, etc.) in steiner-images ein.
Die Bilder werden als Base64 eingebettet, damit sie auch in der Online-Version funktionieren
(Steiner_GA ist nicht im Git/Deployment enthalten).

Verwendung:
    python tools/add_ga_images_to_steiner_images.py [--dry-run] [--ga GA295,GA306]
"""

import json
import base64
import re
import argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
STEINER_GA = BASE / "Steiner_GA"
LECTURES_DIR = BASE / "steiner-full-lectures"
IMAGES_DIR = BASE / "steiner-images"

# GAs die standardmäßig verarbeitet werden (Bände mit assets/ aber ohne steiner-images)
DEFAULT_GAS = ["GA295", "GA306"]


def find_ga_folder(ga_number: str) -> Path | None:
    """Findet den GA-Ordner in Steiner_GA."""
    if not STEINER_GA.exists():
        return None
    ga_upper = ga_number.upper().replace("GA", "GA")
    for d in STEINER_GA.iterdir():
        if d.is_dir() and d.name.upper().startswith(ga_upper):
            return d
    return None


def extract_img_refs_from_content(content: str) -> list[tuple[str, str]]:
    """Extrahiert (alt, filename) aus <img src="assets/img-N.png" alt="...">."""
    # Pattern: <img src="assets/img-N.png" alt="img-N.png" /> oder Varianten
    refs = []
    for m in re.finditer(r'<img\s+[^>]*src=["\']?([^"\'>\s]+)["\']?[^>]*alt=["\']?([^"\'<>]*)["\']?[^>]*>', content, re.I):
        src = m.group(1).strip()
        alt = (m.group(2) or "").strip()
        if "assets/" in src and re.search(r'img-\d+\.(png|jpg|jpeg|webp)', src, re.I):
            fn = src.split("assets/")[-1].split("/")[-1]
            refs.append((alt or fn, fn))
    # Auch: src="assets/img-0.png" einzeln
    for m in re.finditer(r'src=["\']?(?:[^"\'>\s]*/)?(assets/(img-\d+\.(?:png|jpg|jpeg|webp)))["\']?', content, re.I):
        fn = m.group(2).split("/")[-1] if "/" in m.group(2) else m.group(2)
        refs.append((fn, fn))
    return refs


def load_lectures_for_ga(ga_number: str) -> list[dict]:
    """Lädt alle Vorträge einer GA aus steiner-full-lectures."""
    lectures = []
    for f in LECTURES_DIR.glob("steiner-full-lectures-*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for lec in data.get("lectures", []):
                lid = lec.get("ID") or ""
                if lid.startswith(ga_number.upper() + "/") or lid == ga_number.upper():
                    lectures.append(lec)
        except Exception:
            pass
    return sorted(lectures, key=lambda l: (l.get("ID") or ""))


def collect_image_entries(ga_folder: Path, lectures: list[dict], ga_number: str, dry_run: bool) -> list[dict]:
    """Sammelt alle Bild-Einträge für die GA."""
    assets_path = ga_folder / "assets"
    if not assets_path.exists():
        print(f"  Kein assets/ Ordner: {assets_path}")
        return []

    entries = []
    seen = set()  # (lectureId, filename) um Duplikate zu vermeiden

    for lec in lectures:
        lecture_id = lec.get("ID") or ""
        if not lecture_id:
            continue

        for para in lec.get("paragraphs", []):
            content = para.get("content") or ""
            idx = para.get("index") or ""
            refs = extract_img_refs_from_content(content)
            if not refs:
                # Einzelnes img kann auch anders formatiert sein
                for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content):
                    src = m.group(1)
                    if "img-" in src and any(ext in src.lower() for ext in [".png", ".jpg", ".jpeg", ".webp"]):
                        fn = src.split("/")[-1].split("\\")[-1]
                        refs.append((fn, fn))

            for alt, filename in refs:
                key = (lecture_id, filename)
                if key in seen:
                    continue
                seen.add(key)

                img_path = assets_path / filename
                if not img_path.exists():
                    # Versuche .jpeg / .jpg wenn .png fehlt
                    base = re.sub(r"\.(png|jpg|jpeg|webp)$", "", filename, flags=re.I)
                    for ext in [".jpeg", ".jpg", ".png"]:
                        candidate = assets_path / (base + ext)
                        if candidate.exists():
                            img_path = candidate
                            filename = candidate.name
                            break

                if not img_path.exists():
                    print(f"  ⚠ Bild nicht gefunden: {img_path}")
                    continue

                if dry_run:
                    print(f"    Würde hinzufügen: {lecture_id} ^{idx} {filename}")
                    continue

                with open(img_path, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                ext = img_path.suffix.lower()
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")

                entries.append({
                    "lectureId": lecture_id,
                    "index": idx,
                    "altText": alt,
                    "path": f"assets/{filename}",
                    "markdownRef": f"![{alt}](assets/{filename})",
                    "base64": f"data:{mime};base64,{b64}",
                    "size": len(raw),
                })

    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts schreiben")
    ap.add_argument("--ga", type=str, default=",".join(DEFAULT_GAS), help="Komma-getrennte GA-Nummern, z.B. GA295,GA306")
    args = ap.parse_args()

    ga_list = [g.strip().upper() for g in args.ga.split(",") if g.strip()]

    print("=" * 60)
    print("GA-Bilder → steiner-images (für Online-Version)")
    print("=" * 60)

    if not STEINER_GA.exists():
        print(f"Fehler: Steiner_GA nicht gefunden: {STEINER_GA}")
        return 1

    all_entries = []

    for ga in ga_list:
        print(f"\n{ga}:")
        folder = find_ga_folder(ga)
        if not folder:
            print(f"  Ordner nicht gefunden")
            continue
        print(f"  Ordner: {folder.name}")

        lectures = load_lectures_for_ga(ga)
        if not lectures:
            print(f"  Keine Vorträge in full-lectures gefunden")
            continue
        print(f"  Vorträge: {len(lectures)}")

        entries = collect_image_entries(folder, lectures, ga, args.dry_run)
        all_entries.extend(entries)
        print(f"  Bilder: {len(entries)}")

    if not all_entries:
        print("\nKeine Bilder zum Hinzufügen.")
        return 0

    if args.dry_run:
        print(f"\n[DRY-RUN] Würde {len(all_entries)} Einträge hinzufügen.")
        return 0

    # Nächste Part-Nummer finden
    existing = list(IMAGES_DIR.glob("steiner-images-part*.json"))
    max_n = 0
    for p in existing:
        m = re.search(r"part(\d+)\.json$", p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    part_num = max_n + 1
    out_file = IMAGES_DIR / f"steiner-images-part{part_num:02d}.json"

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("FERTIG")
    print("=" * 60)
    print(f"Einträge: {len(all_entries)}")
    print(f"Datei: {out_file}")
    print(f"Größe: {out_file.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    exit(main())
