import re
import sys

PATH = r"c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA004-Die Philosophie der Freiheit\GA004 - Die Philosophie der Freiheit (1894).md"
t = open(PATH, encoding="utf-8", errors="replace").read()
heads = [(m.start(), m.group(0)) for m in re.finditer(r"^##+ .*$", t, re.M)]


def chapter(name):
    for i, (s, h) in enumerate(heads):
        if name in h:
            e = heads[i + 1][0] if i + 1 < len(heads) else len(t)
            return t[s:e]
    return ""


def dump(chapname, pattern, maxlen=1400):
    seg = chapter(chapname)
    print("=" * 20, chapname, len(seg))
    page = "?"
    for p in [x.strip() for x in seg.split("\n\n") if x.strip()]:
        pgs = re.findall(r"\|(\d{1,3})\|", p)
        if pgs:
            page = pgs[0]
        if re.search(pattern, p):
            txt = re.sub(r"\^[a-z0-9]{6}", "", p)
            txt = " ".join(txt.split())
            print(f"[S. {page}] {txt[:maxlen]}")
            print()


if __name__ == "__main__":
    which = sys.argv[1]
    pat = sys.argv[2] if len(sys.argv) > 2 else "Subjekt|Objekt"
    dump(which, pat)
