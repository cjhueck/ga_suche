# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import shutil
from pathlib import Path

DE_DIR = Path(r"c:\Obsidian\Steiner Goetheanismus\Texte")
EN_DIR = Path(r"c:\Obsidian\Steiner Goetheanism\Texts")
EN_COPY = Path(r"c:\Obsidian\Steiner Goetheanismus\en\Texts")

PAIR_HINTS = [
    ("Einleitungen", "Introductions"),
    ("Grundlinien", "Theory of Knowledge"),
    ("Goethes Weltanschauung (1897)", "World View (1897)"),
    ("handschriftlichen Nachlasse", "Manuscript Nachlass"),
    ("Vater einer neuen", "Father of a New Aesthetics"),
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
            print("UNPAIRED hint", needle_de, "->", needle_en, "de", bool(de), "en", bool(en))
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


def looks_complete_line(ln: str) -> bool:
    s = ln.strip()
    if not s:
        return False
    if s.startswith(("#", "[[#", "**[[#", ">", "|", "- ", "* ", "1.", "[", "«", '"')):
        return True
    if len(s) > 40 and (s[-1] in ".!?:;»\"')" or s.endswith("...") or s[-1].isdigit()):
        return True
    return False


def atomic_units(text: str) -> list[str]:
    units: list[str] = []
    for block in coarse_blocks(text):
        if block.startswith("#"):
            units.append(block)
            continue
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if len(lines) > 1 and all(looks_complete_line(ln) for ln in lines):
            units.extend(lines)
        else:
            units.append(" ".join(lines))
    return units


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?»:\"'])\s+(?=[A-ZÄÖÜ\"«\[(])", text)
    out = [p.strip() for p in parts if p.strip()]
    return out or [text]


def expand_units(units: list[str], needed: int) -> list[str]:
    """Split longest units by sentences until we have at least `needed` units."""
    units = list(units)
    guard = 0
    while len(units) < needed and guard < 5000:
        guard += 1
        idx = max(range(len(units)), key=lambda i: len(units[i]) if not units[i].startswith("#") else -1)
        sents = split_sentences(units[idx])
        if len(sents) < 2:
            break
        mid = max(1, len(sents) // 2)
        units[idx : idx + 1] = [" ".join(sents[:mid]), " ".join(sents[mid:])]
    return units


def align_units_to_blocks(de_blocks: list[str], en_units: list[str]) -> list[list[str]]:
    n, m = len(de_blocks), len(en_units)
    if n == 0:
        return []
    if m == 0:
        return [[] for _ in de_blocks]
    if m < n:
        en_units = expand_units(en_units, n)
        m = len(en_units)
        if m < n:
            # cannot split further; last DE blocks share leftover
            groups = [[u] for u in en_units]
            while len(groups) < n:
                groups.append([])
            return groups

    de_len = [max(1, len(b)) for b in de_blocks]
    en_len = [max(1, len(u)) for u in en_units]

    # dp[i][j]: min cost matching first i blocks with first j units
    INF = 10**18
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    prev = [[(0, 0)] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0

    def cost(i: int, take: int, j_end: int) -> float:
        sl = sum(en_len[j_end - take : j_end])
        dl = de_len[i - 1]
        # length mismatch
        c = abs(sl - dl) / max(dl, sl, 1)
        de_h = de_blocks[i - 1].startswith("#")
        # heading should consume exactly one heading unit
        units = en_units[j_end - take : j_end]
        if de_h:
            if take != 1 or not units[0].startswith("#"):
                c += 50
            else:
                c -= 0.5
        else:
            if any(u.startswith("#") for u in units):
                c += 50
        # prefer similar line counts
        de_lines = max(1, len([ln for ln in de_blocks[i - 1].split("\n") if ln.strip()]))
        if take != de_lines:
            c += 0.15 * abs(take - de_lines)
        return c

    max_take = 12
    for i in range(1, n + 1):
        jmin = i  # at least 1 unit per remaining? not strictly
        for j in range(i, m - (n - i) + 1):
            max_k = min(max_take, j - (i - 1))
            best = INF
            best_k = 1
            for k in range(1, max_k + 1):
                if dp[i - 1][j - k] >= INF:
                    continue
                c = dp[i - 1][j - k] + cost(i, k, j)
                if c < best:
                    best = c
                    best_k = k
            dp[i][j] = best
            prev[i][j] = (i - 1, j - best_k)

    # if last state not reached (constraints too tight), greedy fallback
    if dp[n][m] >= INF:
        groups: list[list[str]] = []
        j = 0
        for i, b in enumerate(de_blocks):
            remain_b = n - i
            remain_u = m - j
            take = max(1, round(remain_u / remain_b)) if remain_b else remain_u
            take = min(take, remain_u - (remain_b - 1))
            take = max(1, take)
            groups.append(en_units[j : j + take])
            j += take
        if j < m:
            groups[-1].extend(en_units[j:])
        return groups

    groups_rev: list[list[str]] = []
    i, j = n, m
    while i > 0:
        pi, pj = prev[i][j]
        groups_rev.append(en_units[pj:j])
        i, j = pi, pj
    groups_rev.reverse()
    return groups_rev


def format_group(de_block: str, en_parts: list[str]) -> str:
    if not en_parts:
        return ""
    de_lines = [ln for ln in de_block.split("\n") if ln.strip()]
    nlines = len(de_lines)
    if nlines <= 1 or len(en_parts) == 1:
        return " ".join(re.sub(r"\s+", " ", p).strip() for p in en_parts)
    # match internal newlines of the German block
    if len(en_parts) == nlines:
        return "\n".join(re.sub(r"\s+", " ", p).strip() for p in en_parts)
    # pack en_parts into nlines groups
    packed = pack_list(en_parts, nlines)
    return "\n".join(packed)


def pack_list(parts: list[str], n: int) -> list[str]:
    if n <= 1:
        return [" ".join(parts)]
    if len(parts) <= n:
        return parts
    weights = [max(1, len(p)) for p in parts]
    total = sum(weights)
    targets = [total * (i + 1) / n for i in range(n)]
    groups: list[list[str]] = [[] for _ in range(n)]
    acc = 0
    gi = 0
    for p, w in zip(parts, weights):
        while gi < n - 1 and acc >= targets[gi]:
            gi += 1
        groups[gi].append(p)
        acc += w
    return [" ".join(g) if g else "" for g in groups]


def align_file(de_text: str, en_text: str) -> str:
    de_body, _de_notes = cut_notes(de_text)
    en_body, en_notes = cut_notes(en_text)
    de_blocks = coarse_blocks(de_body)
    en_units = atomic_units(en_body)
    groups = align_units_to_blocks(de_blocks, en_units)
    out_blocks = []
    for db, grp in zip(de_blocks, groups):
        out_blocks.append(format_group(db, grp))
    body = "\n\n".join(b for b in out_blocks if b is not None)
    if en_notes:
        return body.rstrip() + "\n\n" + en_notes.lstrip("\n")
    return body.rstrip() + "\n"


def main() -> None:
    pairs = pair_files()
    print("pairs", len(pairs))
    for de_path, en_path in pairs:
        de = de_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        de_n = len(coarse_blocks(cut_notes(de)[0]))
        old_n = len(coarse_blocks(cut_notes(en)[0]))
        new = align_file(de, en)
        new_n = len(coarse_blocks(cut_notes(new)[0]))
        en_path.write_text(new, encoding="utf-8")
        dest = EN_COPY / en_path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(en_path, dest)
        print(f"{en_path.name[:58]:58} DE={de_n:4} old={old_n:4} new={new_n:4}")


if __name__ == "__main__":
    main()
