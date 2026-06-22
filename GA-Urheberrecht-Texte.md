# Urheberrecht: Per-Text-Bewertung der GA-Abschlussbände (2016–2025)

> **Handgepflegte Datei** – wird NICHT von `tools/extract_erstveroeffentlichung.py` überschrieben.
> Grundlage: die gedruckten Editionen in `Steiner_GA_pdf/` (mit editorischem Apparat).
> **Keine Rechtsberatung.** Bewertung anhand der editorischen „Textgrundlage/Erstveröffentlichung"-Angaben.

## Rechtlicher Rahmen
- **§ 64 UrhG:** Steiner † 1925 → Werktext seit **1.1.1996 gemeinfrei**.
- **§ 71 UrhG (editio princeps):** Text **erstmals nach 1995** veröffentlicht → 25 J. Schutz ab Erscheinen.
- **§ 70 UrhG (wiss. Ausgabe):** redaktioneller Apparat + konstituierte Textfassung → 25 J. ab Erscheinen.

## Ampel-Bedeutung
- 🟢 **frei** – nachweislich vor 1996 (zu Lebzeiten oder in früherer Ausgabe) veröffentlicht.
- 🔴 **§71** – Erstveröffentlichung (vermutlich) nach 1995 → bei Abmahnung entfernen / bis Schutzende sperren.
- 🟡 **prüfen** – Quelle unklar (nur Manuskript/Stenogramm genannt, kein Druckjahr) → Einzelfall.
- ⚪ **Apparat** – kein Steiner-Text, sondern Herausgeberleistung (§ 70).

## Vorgehen bei Abmahnung
Schutz gilt **pro Text**, nicht pro Band. → Geschützte Texte (🔴, ggf. 🟡) gezielt entfernen, **gemeinfreie (🟢) stehen lassen**. Für behaltene 🟢-Texte im Zweifel den **Vor-1996-Wortlaut** verwenden (nicht die edierte Neufassung), um § 70 an der Textgestalt zu vermeiden.

---

## Aufbau dieser Auswertung
- **Diese Datei** = handgeprüfte Bände (verbindlich).
- **`GA-Urheberrecht-Gesamttabelle.md`** + **`.csv`** = konsolidierte Tabelle (GA | Nr | Vortrag/Text | Datum | Ampel | Begründung | Textgrundlage). Erzeugt mit `tools/build_gesamttabelle.py` (mit Publikations-Parser: Vor-/Erstdruck, „Bisherige Veröffentlichungen", Reihen-/Einzelvermerke). **1107 Texte**: 🟢 174 frei · 🟡 178 prüfen · 🔴 758 §71.
- **`GA-Urheberrecht-Texte-AUTO.md`** = älterer Per-Band-Entwurf (`tools/build_urheberrecht_table.py`).
- Noch ohne Tabelle (kein/nur Bild-PDF): GA 41b, 42, 70b, 71a, 71b, 251, 252, 277a, 288.

## Fortschritt
| Band | Status | Quelle |
|---|---|---|
| GA 19 | ✅ handgeprüft | PDF 2023 |
| GA 111 | ✅ handgeprüft (reihen-genau) | PDF 2018 |
| GA 46 | 🟠 Auto-Entwurf (84 × §71!) | PDF 2020 |
| GA 244 | 🟠 Auto-Entwurf (280 Einh.) | MD (kein PDF) |
| GA 68a–d, 69d/e, 70a/b, 71a, 80a–c, 87, 90a/b/c, 91, 117a, 250, 332b, 336, 37, 41a, 43, 289 | 🟠 Auto-Entwurf | PDF (inkl. Zusatzordner „Neue GAs") |
| GA 41b, 42, 71b, 251, 252, 277a, 288 | ❌ offen (kein/nur Bild-PDF) | – |

> **🟡 prüfen bei Vortragsbänden:** Der Apparat nennt die Textgrundlage (Stenogramm/Nachschrift), aber nicht immer Ort/Jahr der Erstveröffentlichung. Bei den **Abschlussbänden** (öffentliche Vorträge, erstmals gesammelt) sind viele dieser Transkripte **Erstdruck in der Neuausgabe → faktisch § 71**. Endgültige Klärung über den Anhang **„Nachweis der Veröffentlichungen aus dem Vortragswerk"** des jeweiligen Bandes.

---

<a id="ga019"></a>
## GA 19 — Gedanken während der Zeit des Krieges (Edition 2023)
PDF: `Steiner, Rudolf GA 019, 2023 - Gedanken während der Zeit des Krieges …`

| # | Text | Erstveröffentlichung lt. Apparat | Status |
|---|---|---|---|
| 1 | Gedanken während der Zeit des Krieges (Essay) | Berlin **1915** (3 Aufl.); Wiederabdr. Boos 1933 | 🟢 frei |
| 2 | Eine preisgekrönte wissenschaftliche Arbeit … (1917) | Neue Badische Landeszeitung, Mannheim, **17.4.1917**; Münchner Neueste Nachrichten 30.4.1917 | 🟢 frei |
| 3 | Erstes Memorandum (Juli 1917) | zu Lebzeiten nicht veröff.; Erstdruck **1929** (Polzer-Hoditz) / 1933 (Boos) | 🟢 frei¹ |
| 4 | Zweites Memorandum, erste Fassung (22.7.1917) | Erstdruck **1934** (Polzer, *Anthroposophie*) | 🟢 frei¹ |
| 5 | Zweites Memorandum, zweite Fassung (Juli 1917) | Erstdruck **1933** (Boos) | 🟢 frei¹ |
| 6 | Vorbemerkungen (Mai 1919) | Steiners Vorwort zur Moltke-Veröffentlichung **1919** | 🟢 frei |
| 7 | **An das deutsche Volk und an die deutsche Regierung!** (1919) | Inhaltsverz.: **„Unveröffentlichtes Flugblatt, Juni 1919"** | 🔴 §71 (Erstdruck vmtl. 2023) |
| 8 | Neue Tatsachen … (Matin-Interview, 12.10.1921) | *Dreigliederung* Nr.15 **1921**; *Das Goetheanum* Nr.9 1921 | 🟢 frei |
| 9 | Nachträgliche Bemerkungen (Okt. 1921) | ebd. **1921**; Boos 1933 | 🟢 frei |
| 10 | Über «Erwiderungen» … (26.10.1921) | *Dreigliederung* Nr.17 **1921**; Boos 1933 | 🟢 frei |
| 11 | Gegen Einwände … (10.11.1921) | *Dreigliederung* Nr.19 **1921**; Boos 1933 | 🟢 frei |

**Entfernen/sperren bei Abmahnung:** Text 7 (unveröff. Flugblatt → § 71, falls Erstdruck 2023; frei, falls schon Boos 1933).
**¹ Achtung:** in den Memoranden 3–5 sind einzelne **restituierte Manuskriptstellen**, die 1929/1933 fehlten (z. B. S. 76 f.), → diese Einzelstellen § 71-relevant, nicht der Grundtext.
**Apparat** (Einleitung, Hinweise, Lesarten) ⚪ § 70 © 2023.

---

<a id="ga111"></a>
## GA 111 — Einführung in die Grundlagen der Theosophie (Edition 2018)
PDF: `Steiner, Rudolf GA 111, 2018 …` — **kein Sammel-Anhang**; Publikationsangaben stehen **pro Reihe** am Beginn des jeweiligen Hinweise-Teils.
Aus „Zu dieser Ausgabe": drei Reihen; „Insofern ein Vortrag … bereits andernorts publiziert wurde, ist dies … in den Hinweisen nachgewiesen." → **kein Vermerk = Erstdruck 2018**.

| Reihe | Vorpublikation lt. Apparat | Status |
|---|---|---|
| **Weltenanfang und Weltenende** — 14 Vorträge, Hannover, 21.9.–4.10.1907 | „Die Vorträge wurden auf **steinerquellen.de bereits im Oktober 2008** … publiziert" | 🟢 frei¹ (Verlag ist nicht editio princeps) |
| **Niederlande 1908** | kein Vorpublikations-Vermerk (Ausnahme: 1 Vortrag „bereits publiziert in GA 68c" → der ist 🟢) | 🔴 §71 (Erstdruck 2018 → bis ~2043) |
| **Rom 1909** | kein Vorpublikations-Vermerk | 🔴 §71 (Erstdruck 2018 → bis ~2043) |

**Entfernen/sperren bei Abmahnung:** die Reihen **Niederlande 1908** und **Rom 1909** (Erstdruck 2018 durch den Verlag → § 71).
**¹ Hannover 1907:** schon 2008 von Dritten (steinerquellen.de) publiziert → der Rudolf Steiner Verlag ist **nicht** Erst­veröffentlicher; ein etwaiger § 71 läge bei steinerquellen (ab 2008). Geringes Risiko, sofern du den Text **nicht** 1:1 aus der edierten 2018er-Fassung (§ 70) übernimmst.
**Einzel-Ausnahme:** der in den Hinweisen als „bereits publiziert in GA 68c" vermerkte Vortrag = 🟢 frei.
**Apparat** ⚪ § 70 © 2018.

> ⚠️ Reihen-genau verifiziert; die exakte Zuordnung *welcher* Einzelvortrag zu Niederlande 1908 bzw. Rom 1909 gehört, ist noch tabellarisch nachzutragen.
