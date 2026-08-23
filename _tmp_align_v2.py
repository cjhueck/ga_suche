# -*- coding: utf-8 -*-
"""Align EN blank-line / paragraph structure to the German originals.

Headings and table-of-contents groups are treated as hard structure.
Prose between those anchors is packed or split so the number of
paragraphs matches the German file. Footnotes are left untouched.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

DE_DIR = Path(r"c:\Obsidian\Steiner Goetheanismus\Texte")
EN_DIR = Path(r"c:\Obsidian\Steiner Goetheanism\Texts")
EN_COPY = Path(r"c:\Obsidian\Steiner Goetheanismus\en\Texts")

PAIR_HINTS = [
    ("Einleitungen", "Introductions"),
    ("Grundlinien", "Theory of Knowledge"),
    ("Goethes Weltanschauung (1897)", "World View (1897)"),
    ("handschriftlichen Nachlasse", "Nachlass"),
    ("Vater einer neuen", "Father of a New"),
    ("als Ästhetiker", "as Aesthetician"),
    ("Moral und Christentum", "Morality and Christianity"),
    ("die Medizin", "Medicine"),
    ("Versammlung", "Assembly"),
    ("geheime Offenbarung", "Secret Revelation"),
    ("Naturanschauung gemäß", "View of Nature"),
    ("Recht in der Naturwissenschaft", "Right in Natural Science"),
    ("Haeckel", "Haeckel"),
    ("Weimarer Goethe-Ausgabe", "Weimar Goethe Edition"),
    ("Fragment", "Fragment"),
    ("Gewinn der Goethe-Studien", "Gain to Goethe Studies"),
    ("Gewinn unserer Anschauungen", "Gain to Our Views"),
    ("Goetheanum", "Goetheanum"),
    ("Vortragsnachschrift", "Lecture Transcript"),
]


def pair_files() -> list[tuple[Path, Path]]:
    de_files = list(DE_DIR.glob("*.md"))
    en_files = list(EN_DIR.glob("*.md"))
    used_en: set[Path] = set()
    pairs: list[tuple[Path, Path]] = []
    for needle_de, needle_en in PAIR_HINTS:
        de = next((p for p in de_files if needle_de in p.name), None)
        en = next((p for p in en_files if needle_en in p.name and p not in used_en), None)
        if de and en:
            pairs.append((de, en))
            used_en.add(en)
        else:
            print("UNPAIRED", needle_de, "->", needle_en, "de", bool(de), "en", bool(en))
    leftover_de = [p for p in de_files if p not in {a for a, _ in pairs}]
    leftover_en = [p for p in en_files if p not in used_en]
    if leftover_de or leftover_en:
        print("leftover DE", [p.name for p in leftover_de])
        print("leftover EN", [p.name for p in leftover_en])
    return pairs


def cut_notes(text: str) -> tuple[str, str]:
    m = re.search(r"\n(\[\^[0-9]+\]:)", text)
    if not m:
        return text, ""
    return text[: m.start() + 1], text[m.start() + 1 :]


def coarse_blocks(text: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def is_toc_line(ln: str) -> bool:
    s = ln.strip()
    return s.startswith("[[#") or s.startswith("**[[#")


def is_heading_line(ln: str) -> bool:
    return bool(re.match(r"^#{1,6} ", ln.strip()))


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"[ \t\n]+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?»:\"'])\s+(?=[A-ZÄÖÜ\"«\[(])", text)
    return [p.strip() for p in parts if p.strip()] or [text]


def pack_to_n(units: list[str], n: int) -> list[str]:
    units = [u.strip() for u in units if u.strip()]
    if n <= 0:
        return []
    if not units:
        return [""] * n
    if n == 1:
        return [" ".join(re.sub(r"\s+", " ", u) for u in units)]
    if len(units) == n:
        return units
    if len(units) > n:
        items = list(units)
        while len(items) > n:
            candidates = []
            for i in range(len(items) - 1):
                if items[i].strip() == "*" or items[i + 1].strip() == "*":
                    continue
                candidates.append((len(items[i]) + len(items[i + 1]), i))
            if candidates:
                i = min(candidates)[1]
            else:
                lens = [len(items[i]) + len(items[i + 1]) for i in range(len(items) - 1)]
                i = min(range(len(lens)), key=lambda k: lens[k])
            items[i] = items[i].rstrip() + " " + items[i + 1].lstrip()
            del items[i + 1]
        return items
    items = list(units)
    guard = 0
    while len(items) < n and guard < 4000:
        guard += 1
        idx = max(
            range(len(items)),
            key=lambda i: -1
            if is_heading_line(items[i].split("\n")[0]) or items[i].strip() == "*"
            else len(items[i]),
        )
        sents = split_sentences(items[idx])
        if len(sents) < 2:
            words = items[idx].split()
            if len(words) < 4:
                break
            mid = max(1, len(words) // 2)
            items[idx : idx + 1] = [" ".join(words[:mid]), " ".join(words[mid:])]
            continue
        mid = max(1, len(sents) // 2)
        items[idx : idx + 1] = [" ".join(sents[:mid]), " ".join(sents[mid:])]
    if len(items) < n:
        items.extend([items[-1] if items else ""] * (n - len(items)))
    return items[:n]


def split_glued_heading_line(chunk: str) -> list[str]:
    """If a heading and the following sentence share one line, split them."""
    if "\n" in chunk or not is_heading_line(chunk):
        return [chunk]
    m = re.match(
        r"^(#{1,6} [^\[]{1,90}?)[ \t]+((?:\[\d+\]|[A-ZÄÖÜ«\"']).+)$",
        chunk,
    )
    if not m:
        return [chunk]
    head, rest = m.group(1).strip(), m.group(2).strip()
    if head.rstrip().endswith("."):
        return [chunk]
    if rest[0] in "[\"'«" or (rest[0].isupper() and len(rest) > 40):
        return [head, rest]
    return [chunk]


def explode_units(block: str) -> list[str]:
    text = block.strip()
    if not text:
        return []
    pieces = re.split(r"(?<=\S)[ \t]+(?=#{1,6} )", text)
    units: list[str] = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        first, *rest_lines = piece.split("\n")
        for part in split_glued_heading_line(first.strip()):
            units.append(part)
        rest = "\n".join(rest_lines).strip()
        if rest:
            if is_heading_line(rest.split("\n", 1)[0]):
                units.extend(explode_units(rest))
            else:
                lines = [ln.strip() for ln in rest.split("\n") if ln.strip()]
                if lines and all(is_toc_line(ln) or is_heading_line(ln) for ln in lines):
                    units.extend(lines)
                else:
                    units.append(rest)
    # explode pure TOC / stacked heading / page+heading blocks
    flat: list[str] = []
    for u in units:
        lines = [ln.strip() for ln in u.split("\n") if ln.strip()]
        if len(lines) > 1 and all(is_toc_line(ln) for ln in lines):
            flat.extend(lines)
        elif len(lines) > 1 and any(is_heading_line(ln) for ln in lines):
            flat.extend(lines)
        else:
            flat.append(u)
    peeled: list[str] = []
    for u in flat:
        s = u.strip()
        if s.startswith("* ") and not s.startswith("**"):
            peeled.append("*")
            rest = s[2:].strip()
            if rest:
                peeled.append(rest)
        else:
            peeled.append(u)
    return peeled


PAGE_ONLY = re.compile(r"^\[\d+\]\s*$")


def is_page_only(u: str) -> bool:
    return bool(PAGE_ONLY.match(u.strip()))


def unit_kind(u: str) -> str:
    line = u.split("\n")[0].strip()
    if is_heading_line(line) and u.strip().count("\n") == 0:
        return "heading"
    if is_toc_line(line):
        return "toc"
    return "para"


def de_kind(db: str) -> str:
    dlines = [ln.strip() for ln in db.split("\n") if ln.strip()]
    if dlines and all(is_toc_line(ln) for ln in dlines):
        return "toc"
    if any(is_heading_line(ln) for ln in dlines):
        return "heading"
    return "para"


def fit_internal_lines(text: str, nlines: int) -> str:
    text = text.strip()
    if nlines <= 1:
        if re.search(r"(?m)^#{1,6} ", text):
            return text
        return re.sub(r"\s+", " ", text)
    existing = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(existing) == nlines:
        return "\n".join(existing)
    bits = pack_to_n(existing if len(existing) > 1 else split_sentences(text), nlines)
    return "\n".join(bits)


def align_blocks(de_blocks: list[str], en_units: list[str]) -> list[str]:
    i = 0
    n = len(en_units)
    out: list[str] = []
    bi = 0
    while bi < len(de_blocks):
        db = de_blocks[bi]
        kind = de_kind(db)
        dlines = [ln.strip() for ln in db.split("\n") if ln.strip()]

        if kind == "heading":
            got: list[str] = []
            while i < n and is_page_only(en_units[i]):
                got.append(en_units[i].strip())
                i += 1
            if i < n and unit_kind(en_units[i]) == "heading":
                unit = en_units[i]
                lines = unit.split("\n")
                got.append(lines[0].strip())
                rest = "\n".join(lines[1:]).strip()
                i += 1
                if rest:
                    extra_units = explode_units(rest)
                    en_units[i:i] = extra_units
                    n = len(en_units)
            elif i < n:
                # unexpected: take next unit so we still emit something
                got.append(en_units[i].split("\n")[0].strip())
                i += 1
            # reproduce DE line grouping (page marker + heading without blank line)
            de_nonempty = dlines
            if len(got) == len(de_nonempty):
                out.append("\n".join(got))
            elif len(de_nonempty) == 1:
                out.append(got[-1] if got else "")
            else:
                out.append("\n".join(got))
            bi += 1

        elif kind == "toc":
            need = len(dlines)
            got: list[str] = []
            while i < n and len(got) < need:
                if unit_kind(en_units[i]) == "heading":
                    break
                progressed = False
                leftover_prose: list[str] = []
                for ln in en_units[i].split("\n"):
                    if is_toc_line(ln) and len(got) < need:
                        got.append(ln.strip())
                        progressed = True
                    elif ln.strip() and not is_toc_line(ln):
                        leftover_prose.append(ln.strip())
                i += 1
                if leftover_prose and len(got) >= need:
                    extra_units = leftover_prose
                    en_units[i:i] = extra_units
                    n = len(en_units)
                    break
                if not progressed:
                    break
            while len(got) < need:
                got.append("")
            out.append("\n".join(got[:need]))
            bi += 1

        else:
            n_paras = 0
            k = bi
            while k < len(de_blocks) and de_kind(de_blocks[k]) == "para":
                n_paras += 1
                k += 1
            chunk: list[str] = []
            while i < n and unit_kind(en_units[i]) == "para":
                if is_page_only(en_units[i]) and i + 1 < n and unit_kind(en_units[i + 1]) == "heading":
                    break
                chunk.append(en_units[i])
                i += 1
            # DE often has a lone "*" as its own paragraph; EN may glue it to the next sentence
            if any(b.strip() == "*" for b in de_blocks[bi:k]):
                peeled: list[str] = []
                for u in chunk:
                    s = u.strip()
                    if s == "*":
                        peeled.append("*")
                    elif s.startswith("* ") or s.startswith("*\n"):
                        peeled.append("*")
                        rest = s[1:].strip()
                        if rest:
                            peeled.append(rest)
                    else:
                        peeled.append(u)
                chunk = peeled
            de_slice = de_blocks[bi:k]
            page_units = [u for u in chunk if is_page_only(u)]
            prose_units = [u for u in chunk if not is_page_only(u)]
            page_i = 0
            n_prose = sum(
                1
                for dbp in de_slice
                if not is_page_only((dbp.strip().split("\n") or [""])[0])
            )
            packed_prose = pack_to_n(prose_units, n_prose) if n_prose else []
            prose_i = 0
            for dbp in de_slice:
                first = (dbp.strip().split("\n") or [""])[0]
                if is_page_only(first):
                    if page_i < len(page_units):
                        out.append(page_units[page_i])
                        page_i += 1
                    else:
                        out.append(first)
                    continue
                p = packed_prose[prose_i] if prose_i < len(packed_prose) else ""
                prose_i += 1
                nlines = len([ln for ln in dbp.split("\n") if ln.strip()])
                out.append(fit_internal_lines(p, nlines) if p.strip() else dbp.strip())
            # unused leftover page markers stay for a later heading/para
            unused = page_units[page_i:]
            if unused:
                en_units[i:i] = unused
                n = len(en_units)
            bi = k

    if i < n:
        extra = " ".join(re.sub(r"\s+", " ", u) for u in en_units[i:])
        if extra:
            if out:
                out[-1] = (out[-1] + " " + extra).strip()
            else:
                out.append(extra)
    return out


def align_file(de_text: str, en_text: str) -> str:
    de_body, _ = cut_notes(de_text)
    en_body, en_notes = cut_notes(en_text)
    de_blocks = coarse_blocks(de_body)
    en_units: list[str] = []
    for b in coarse_blocks(en_body):
        en_units.extend(explode_units(b))
    out_blocks = align_blocks(de_blocks, en_units)
    body = "\n\n".join(b for b in out_blocks if b is not None)
    body = re.sub(r"\n{3,}", "\n\n", body).rstrip() + "\n"
    if en_notes:
        return body.rstrip() + "\n\n" + en_notes.lstrip("\n")
    return body


def heading_count(blocks: list[str]) -> int:
    return sum(1 for b in blocks if any(is_heading_line(ln) for ln in b.split("\n")))


def main(dry_run: bool = True) -> None:
    pairs = pair_files()
    print("pairs", len(pairs), "dry" if dry_run else "WRITE")
    for de_path, en_path in pairs:
        de = de_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        de_blocks = coarse_blocks(cut_notes(de)[0])
        old_blocks = coarse_blocks(cut_notes(en)[0])
        new = align_file(de, en)
        new_blocks = coarse_blocks(cut_notes(new)[0])
        flag = "" if len(new_blocks) == len(de_blocks) else " COUNT"
        hflag = ""
        dh, nh = heading_count(de_blocks), heading_count(new_blocks)
        if dh != nh:
            hflag = f" HEAD {dh}->{nh}"
        print(
            f"{en_path.name[:56]:56} DE={len(de_blocks):4} old={len(old_blocks):4} "
            f"new={len(new_blocks):4}{flag}{hflag}"
        )
        if not dry_run:
            en_path.write_text(new, encoding="utf-8")
            dest = EN_COPY / en_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(en_path, dest)


if __name__ == "__main__":
    main(dry_run="--write" not in sys.argv)
