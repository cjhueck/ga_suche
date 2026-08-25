# -*- coding: utf-8 -*-
"""Write German vault files from exported GA texts."""
import re
from pathlib import Path

SRC = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\_tmp_ga_export")
DST = Path(r"C:\Obsidian\Steiner Goetheanismus\Texte")

GA_LINK = (
    'https://rudolf-steiner-online.de/goto.html#ga={ga}&amp;{date_part}'
    'lecture={lecture}'
)
LINK_ATTRS = (
    'target="ga-suche" rel="opener" title="Textanfang in der GA-Suche" '
    'class="external-link"'
)
LINK_ATTRS_DATE = 'target="ga-suche" rel="opener"'


def link(ga, lecture, date=None, label=None):
    date_part = f"date={date}&amp;" if date else ""
    href = (
        f"https://rudolf-steiner-online.de/goto.html#ga={ga}"
        f"{'&amp;date=' + date if date else ''}"
        f"&amp;lecture={lecture.replace('/', '%2F')}"
    )
    inner = label if label else "&nbsp;"
    attrs = LINK_ATTRS_DATE if label else LINK_ATTRS
    return f'<a href="{href}" {attrs}>{inner}</a>'


def clean_body(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # drop stray line-number leftovers like "    10|"
    text = re.sub(r"\n\s+\d+\|\s*$", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


ITEMS = [
    {
        "src": "GA030_42.md",
        "dst": "GA 030 - Über das Verhältnis Thomas Seebecks zu Goethes Farbenlehre (1886).md",
        "header": (
            "**Steiner, Rudolf (1886): Über das Verhältnis Thomas Seebecks zu Goethes Farbenlehre. "
            "[Chronik des Wiener Goethe-Vereins, 1. Jg., 1. Bd., Nr. 1; 17. Okt. 1886]. "
            "In: *Methodische Grundlagen der Anthroposophie 1884-1901*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1989, S. 477-478. "
            f"([[GA 030]];{link('030', 'GA030/42')})**"
        ),
    },
    {
        "src": "GA030_43.md",
        "dst": "GA 030 - Hundert Jahre zurück. Zur Farbenlehre (1887).md",
        "header": (
            "**Steiner, Rudolf (1887): Hundert Jahre zurück. Zur Farbenlehre. "
            "[Chronik des Wiener Goethe-Vereins, 2. Jg., 1. Bd., Nr. 7; 15. Apr. 1887]. "
            "In: *Methodische Grundlagen der Anthroposophie 1884-1901*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1989, S. 478-479. "
            f"([[GA 030]];{link('030', 'GA030/43')})**"
        ),
    },
    {
        "src": "GA030_8.md",
        "dst": "GA 030 - Goethe-Studien - Grund-Ideen (1900).md",
        "header": (
            "**Steiner, Rudolf (1900): Goethe-Studien - Grund-Ideen. "
            "[Magazin für Literatur, 69. Jg., Nr. 30; 28. Juli 1900]. "
            "In: *Methodische Grundlagen der Anthroposophie 1884-1901*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1989, S. 201-207. "
            f"([[GA 030]];{link('030', 'GA030/8')})**"
        ),
        "fixes": [
            ("ernporquillt", "emporquillt"),
            ("Vollkomrnene", "Vollkommene"),
            ("Sie suchen das suchen das Vollkommene", "Sie suchen das Vollkommene"),
        ],
    },
    {
        "src": "GA068c_6.md",
        "dst": "GA 068c - Goethes Naturanschauung in der Gegenwart, Berlin, 18. Juni 1901.md",
        "header": (
            "**Steiner, Rudolf (1901): Goethes Naturanschauung in der Gegenwart. Öffentlicher Vortrag, Berlin, 18. Juni 1901 (Zeitungsbericht). "
            "In: *Goethe und die Gegenwart*. Rudolf Steiner Verlag, Basel 2017, S. 56-58. "
            f"([[GA 068c]];{link('068c', 'GA068c/6', '1901-06-18')})**"
        ),
        "fixes": [
            ("sondern uni das Entdeckte", "sondern um das Entdeckte"),
            ("die große materialis-tisch-monistische", "die große materialistisch-monistische"),
        ],
    },
    {
        "src": "GA068c_11.md",
        "dst": "GA 068c - Goethe als Theosoph, München, 22. April 1904.md",
        "header": (
            "**Steiner, Rudolf (1904): Goethe als Theosoph. Öffentlicher Vortrag, München, 22. April 1904 (Zeitungsbericht). "
            "In: *Goethe und die Gegenwart*. Rudolf Steiner Verlag, Basel 2017, S. 121-123. "
            f"([[GA 068c]];{link('068c', 'GA068c/11', '1904-04-22')})**"
        ),
        "fixes": [
            ("Ludwig Dein- hard", "Ludwig Deinhard"),
            ("muss. ten.", "mussten."),
        ],
    },
    {
        "src": "GA035_2.md",
        "dst": "GA 035 - Die okkulte Grundlage in Goethes Schaffen (1905).md",
        "header": (
            "**Steiner, Rudolf (1905): Die okkulte Grundlage in Goethes Schaffen. Autoreferat eines Vortrags auf dem theosophischen Kongress in London, 10. Juli 1905. "
            "In: *Philosophie und Anthroposophie. Gesammelte Aufsätze 1904-1923*. Rudolf Steiner Verlag, 2. Aufl., Dornach 1984, S. 19-42. "
            f"([[GA 035]];{link('035', 'GA035/2')})**"
        ),
    },
    {
        "src": "GA067_3.md",
        "dst": "GA 067 - Goethe als Vater der Geistesforschung, Berlin, 21. Februar 1918.md",
        "header": (
            "**Steiner, Rudolf (1918): Goethe als Vater der Geistesforschung. Öffentlicher Vortrag, Berlin, 21. Februar 1918. "
            "In: *Das Ewige in der Menschenseele. Unsterblichkeit und Freiheit*. Rudolf Steiner Verlag, 2. Aufl., Dornach 1992, S. 68-102. "
            f"([[GA 067]];{link('067', 'GA067/3', '1918-02-21')})**"
        ),
    },
    {
        "src": "GA277_13.md",
        "dst": "GA 277 - Goethesche Weltanschauung und Goethes Kunstgesinnung, Dornach, 17. August 1919.md",
        "header": (
            "**Steiner, Rudolf (1919): Goethesche Weltanschauung und Goethes Kunstgesinnung. Ansprache, Dornach, 17. August 1919. "
            "In: *Eurythmie. Die Offenbarung der sprechenden Seele*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1999, S. 70-75. "
            f"([[GA 277]];{link('277', 'GA277/13', '1919-08-17')})**"
        ),
    },
    {
        "src": "GA277_16.md",
        "dst": "GA 277 - Goethes Anschauung von der Idee, Dornach, 19. Oktober 1919.md",
        "header": (
            "**Steiner, Rudolf (1919): Goethes Anschauung von der Idee. Ansprache, Dornach, 19. Oktober 1919. "
            "In: *Eurythmie. Die Offenbarung der sprechenden Seele*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1999, S. 86-88. "
            f"([[GA 277]];{link('277', 'GA277/16', '1919-10-19')})**"
        ),
    },
    {
        "src": "GA277_20.md",
        "dst": "GA 277 - Die Seelenkunde der Goetheschen Weltanschauung, Dornach, 22. November 1919.md",
        "header": (
            "**Steiner, Rudolf (1919): Die Seelenkunde der Goetheschen Weltanschauung. Ansprache, Dornach, 22. November 1919. "
            "In: *Eurythmie. Die Offenbarung der sprechenden Seele*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1999, S. 116-122. "
            f"([[GA 277]];{link('277', 'GA277/20', '1919-11-22')})**"
        ),
        "fixes": [
            ("zugrunde hegen der gesprochenen Sprache", "zugrunde liegen der gesprochenen Sprache"),
        ],
    },
    {
        "src": "GA277_30.md",
        "dst": "GA 277 - Über Goethes Prosahymnus Die Natur, Dornach, 17. April 1920.md",
        "header": (
            "**Steiner, Rudolf (1920): Über Goethes Prosahymnus «Die Natur». Ansprache, Dornach, 17. April 1920. "
            "In: *Eurythmie. Die Offenbarung der sprechenden Seele*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1999, S. 173-174. "
            f"([[GA 277]];{link('277', 'GA277/30', '1920-04-17')})**"
        ),
        "fixes": [
            ("In diesem Prosyhymnus", "In diesem Prosahymnus"),
        ],
    },
    {
        "src": "GA036_31.md",
        "dst": "GA 036 - Goethe, der Schauende und Schiller, der Sinnende (1923).md",
        "header": (
            "**Steiner, Rudolf (1923): Goethe, der Schauende und Schiller, der Sinnende. "
            "In: *Der Goetheanumgedanke inmitten der Kulturkrisis der Gegenwart. Gesammelte Aufsätze 1921-1925 aus der Wochenschrift \"Das Goetheanum\"*. Rudolf Steiner Verlag, 1. Aufl., Dornach 1961, S. 128-131. "
            f"([[GA 036]], {link('036', 'GA036/31', '1922-04-09', '09.04.1922')})**"
        ),
        "fixes": [
            ("kommen können.,", "kommen können."),
            ("Freundschaftsb- und", "Freundschaftsbund"),
        ],
    },
    {
        "src": "GA036_35.md",
        "dst": "GA 036 - Die Schaffenshöhe Goethes im Lichte Benedetto Croces (1923).md",
        "header": (
            "**Steiner, Rudolf (1923): Die Schaffenshöhe Goethes im Lichte Benedetto Croces. "
            "In: *Der Goetheanumgedanke inmitten der Kulturkrisis der Gegenwart. Gesammelte Aufsätze 1921-1925 aus der Wochenschrift \"Das Goetheanum\"*. Rudolf Steiner Verlag, 1. Aufl., Dornach 1961, S. 145-149. "
            f"([[GA 036]], {link('036', 'GA036/35', '1923-08-19', '19.08.1923')})**"
        ),
        "fixes": [
            ("dramatiscbe Gedankenverwirrung", "dramatische Gedankenverwirrung"),
        ],
    },
]


def main():
    for item in ITEMS:
        body = (SRC / item["src"]).read_text(encoding="utf-8")
        for old, new in item.get("fixes", []):
            body = body.replace(old, new)
        body = clean_body(body)
        out = item["header"] + "\n\n" + body
        path = DST / item["dst"]
        path.write_text(out, encoding="utf-8")
        print(f"wrote {path.name} ({len(out)} chars)")


if __name__ == "__main__":
    main()
