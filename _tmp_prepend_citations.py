# -*- coding: utf-8 -*-
from pathlib import Path

DE = Path(r"C:\Obsidian\Steiner Goetheanismus\Texte neu")
EN = Path(r"C:\Obsidian\Steiner Goetheanism\Texts neu")

LINK_NBSP = (
    'target="ga-suche" rel="opener" title="Textanfang in der GA-Suche" '
    'class="external-link"'
)


def href(ga, lecture, date=None):
    lec = lecture.replace("/", "%2F")
    if date:
        return (
            f"https://rudolf-steiner-online.de/goto.html#ga={ga}"
            f"&amp;date={date}&amp;lecture={lec}"
        )
    return (
        f"https://rudolf-steiner-online.de/goto.html#ga={ga}"
        f"&amp;lecture={lec}"
    )


def cite(ga_label, ga, lecture, date, text):
    a = (
        f'<a href="{href(ga, lecture, date)}" {LINK_NBSP}>&nbsp;</a>'
    )
    return f"**{text} ([[{ga_label}]];{a})**"


ITEMS = [
    {
        "de": "GA 018 - Die Rätsel der Philosophie in ihrer Geschichte als Umriss dargestellt (1914). Ausschnitt über Goethe im Verhältnis zu Kant.md",
        "en": "GA 018 - The Riddles of Philosophy Presented in Outline in Their History (1914). Excerpt on Goethe in Relation to Kant.md",
        "header": cite(
            "GA 018", "018", "GA018/2", None,
            "Steiner, Rudolf (1914): Die Rätsel der Philosophie in ihrer Geschichte als Umriss dargestellt. Ausschnitt über Goethe im Verhältnis zu Kant. In: *Die Rätsel der Philosophie. In ihrer Geschichte als Umriss dargestellt*. Rudolf Steiner Verlag, 9. Aufl., Dornach 1985, S. 162-173.",
        ),
    },
    {
        "de": "GA 046 - Die Bedeutung von Goethes Denken für die Naturanschauung (um 1884).md",
        "en": "GA 046 - The Significance of Goethe's Thinking for the View of Nature (around 1884).md",
        "header": cite(
            "GA 046", "046", "GA046/9", None,
            "Steiner, Rudolf (1884): Die Bedeutung von Goethes Denken für die Naturanschauung. Aus Notizbuch 322, undatiert, um 1884. In: *Nachgelassene Abhandlungen und Fragmente 1879-1924*. Rudolf Steiner Verlag, 1. Aufl., Basel 2020, S. 91-104.",
        ),
    },
    {
        "de": "GA 046 - Einzig mögliche Kritik der atomistischen Begriffe (1882).md",
        "en": "GA 046 - The Only Possible Critique of Atomistic Concepts (1882).md",
        "header": cite(
            "GA 046", "046", "GA046/7", None,
            "Steiner, Rudolf (1882): Einzig mögliche Kritik der atomistischen Begriffe. Manuskript, undatiert, 1882. In: *Nachgelassene Abhandlungen und Fragmente 1879-1924*. Rudolf Steiner Verlag, 1. Aufl., Basel 2020, S. 64-74.",
        ),
    },
    {
        "de": "GA 046 - Goethes Erkenntnisart (1889).md",
        "en": "GA 046 - Goethe's Mode of Cognition (1889).md",
        "header": cite(
            "GA 046", "046", "GA046/16", None,
            "Steiner, Rudolf (1889): Goethes Erkenntnisart. Aus Notizbuch 397, undatiert, 1889. In: *Nachgelassene Abhandlungen und Fragmente 1879-1924*. Rudolf Steiner Verlag, 1. Aufl., Basel 2020, S. 147-153.",
        ),
    },
    {
        "de": "GA 061 - VON PARACELSUS ZU GOETHE, Berlin, 16. November 1911.md",
        "en": "GA 061 - FROM PARACELSUS TO GOETHE, Berlin, 16 November 1911.md",
        "header": cite(
            "GA 061", "061", "GA061/4", "1911-11-16",
            "Steiner, Rudolf (1911): Von Paracelsus zu Goethe. Öffentlicher Vortrag, Berlin, 16. November 1911. In: *Menschengeschichte im Lichte der Geistesforschung*. Rudolf Steiner Verlag, 2. Aufl., Dornach 1983, S. 99-125.",
        ),
    },
    {
        "de": "GA 067 - GOETHE ALS VATER DER GEISTESFORSCHUNG, Berlin, 21. Februar 1918.md",
        "en": "GA 067 - GOETHE AS FATHER OF SPIRITUAL RESEARCH, Berlin, 21 February 1918.md",
        "header": cite(
            "GA 067", "067", "GA067/3", "1918-02-21",
            "Steiner, Rudolf (1918): Goethe als Vater der Geistesforschung. Öffentlicher Vortrag, Berlin, 21. Februar 1918. In: *Das Ewige in der Menschenseele. Unsterblichkeit und Freiheit*. Rudolf Steiner Verlag, 2. Aufl., Dornach 1992, S. 68-102.",
        ),
    },
    {
        "de": "GA 078 - VIERTER VORTRAG, Stuttgart, 1. September 1921.md",
        "en": "GA 078 - FOURTH LECTURE, Stuttgart, 1 September 1921.md",
        "header": cite(
            "GA 078", "078", "GA078/4", "1921-09-01",
            "Steiner, Rudolf (1921): Vierter Vortrag. Stuttgart, 1. September 1921. In: *Anthroposophie, ihre Erkenntniswurzeln und Lebensfrüchte*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1986, S. 67-86.",
        ),
    },
    {
        "de": "GA 078 - ZWEITER VORTRAG, Stuttgart, 30. August 1921.md",
        "en": "GA 078 - SECOND LECTURE, Stuttgart, 30 August 1921.md",
        "header": cite(
            "GA 078", "078", "GA078/2", "1921-08-30",
            "Steiner, Rudolf (1921): Zweiter Vortrag. Stuttgart, 30. August 1921. In: *Anthroposophie, ihre Erkenntniswurzeln und Lebensfrüchte*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1986, S. 25-45.",
        ),
    },
    {
        "de": "GA 081 - ERSTER VORTRAG - ANTHROPOSOPHIE UND NATURWISSENSCHAFT, Berlin, 6. März 1922.md",
        "en": "GA 081 - FIRST LECTURE - ANTHROPOSOPHY AND NATURAL SCIENCE, Berlin, 6 March 1922.md",
        "header": cite(
            "GA 081", "081", "GA081/1", "1922-03-06",
            "Steiner, Rudolf (1922): Anthroposophie und Naturwissenschaft. Erster Vortrag, Berlin, 6. März 1922. In: *Erneuerungs-Impulse für Kultur und Wissenschaft. Berliner Hochschulkurs*. Rudolf Steiner Verlag, 1. Aufl., Dornach 1994, S. 13-35.",
        ),
    },
    {
        "de": "GA 320 - ERSTER VORTRAG, Stuttgart, 23. Dezember 1919.md",
        "en": "GA 320 - FIRST LECTURE, Stuttgart, 23 December 1919.md",
        "header": cite(
            "GA 320", "320", "GA320/1", "1919-12-23",
            "Steiner, Rudolf (1919): Erster Vortrag. Stuttgart, 23. Dezember 1919. In: *Geisteswissenschaftliche Impulse zur Entwickelung der Physik. Erster naturwissenschaftlicher Kurs: Licht, Farbe, Ton - Masse, Elektrizität, Magnetismus*. Rudolf Steiner Verlag, 4. Aufl., Dornach 2000, S. 25-42.",
        ),
    },
    {
        "de": "GA 322 - ERSTER VORTRAG, Dornach, 27. September 1920.md",
        "en": "GA 322 - FIRST LECTURE, Dornach, 27 September 1920.md",
        "header": cite(
            "GA 322", "322", "GA322/1", "1920-09-27",
            "Steiner, Rudolf (1920): Erster Vortrag. Dornach, 27. September 1920. In: *Grenzen der Naturerkenntnis*. Rudolf Steiner Verlag, Dornach 1981, S. 7-19.",
        ),
    },
    {
        "de": "GA 326 - FÜNFTER VORTRAG, Dornach, 28. Dezember 1922.md",
        "en": "GA 326 - FIFTH LECTURE, Dornach, 28 December 1922.md",
        "header": cite(
            "GA 326", "326", "GA326/5", "1922-12-28",
            "Steiner, Rudolf (1922): Fünfter Vortrag. Dornach, 28. Dezember 1922. In: *Der Entstehungsmoment der Naturwissenschaft in der Weltgeschichte und ihre seitherige Entwickelung*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1977, S. 71-84.",
        ),
    },
    {
        "de": "GA 326 - SECHSTER VORTRAG, Dornach, 1. Januar 1923.md",
        "en": "GA 326 - SIXTH LECTURE, Dornach, 1 January 1923.md",
        "header": cite(
            "GA 326", "326", "GA326/6", "1923-01-01",
            "Steiner, Rudolf (1923): Sechster Vortrag. Dornach, 1. Januar 1923. In: *Der Entstehungsmoment der Naturwissenschaft in der Weltgeschichte und ihre seitherige Entwickelung*. Rudolf Steiner Verlag, 3. Aufl., Dornach 1977, S. 85-98.",
        ),
    },
]


def prepend(path: Path, header: str):
    body = path.read_text(encoding="utf-8")
    if body.lstrip().startswith("**Steiner, Rudolf"):
        print(f"skip (already cited): {path.name}")
        return
    body = body.lstrip("\n")
    if body and not body.endswith("\n"):
        body += "\n"
    path.write_text(header + "\n\n" + body, encoding="utf-8")
    print(f"ok {path.name}")


def main():
    for item in ITEMS:
        prepend(DE / item["de"], item["header"])
        prepend(EN / item["en"], item["header"])


if __name__ == "__main__":
    main()
