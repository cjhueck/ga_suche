---
name: recherche-gliederung
description: Gliedert Steiner-Recherchen zweistufig nach Themenbereichen und fasst redundante Zwischenüberschriften zusammen. Use when structuring Recherche results, Inhaltsübersicht, subThemes, thematic headings, or when the user asks about Zwischenüberschriften, Themenbereiche, or tabellarische Recherche.
---

# Recherche-Gliederung

Recherchen im Modus **Recherche** (GA-Suche, thematische Tabelle) nicht als flache Liste ähnlicher Zwischenüberschriften ausgeben.

## Zweistufige Ordnung

1. **Themenbereiche** (typisch 5–9): grobe Felder, z. B. Erkenntnistheorie, Kritik und Gegenposition, Philosophiegeschichte, Moralphilosophie, Goethe, Übersinnliches. Der Bereichstitel wiederholt nicht die Zwischenüberschrift.
2. **Zwischenüberschriften** darunter: nur so viele, wie wirklich verschiedene Aspekte sind. Inhaltlich gleiche oder stark überlappende Titel zu **einer** Überschrift zusammenfassen.

Die Inhaltsübersicht folgt derselben Tabelle: zuerst der Themenbereich, darunter die zusammengefassten Zwischenüberschriften.

## Redundanz

Nicht parallel stehen lassen (Beispiel Kant):

- „Kants Erkenntnistheorie: Ding an sich, Subjekt-Objekt-Trennung und Erscheinungswelt“
- „Kants Erkenntnistheorie: Ding an sich, Erscheinung und Erkenntnisgrenze“
- „Steiners Kritik an Kants Erkenntnistheorie und dem kritischen Idealismus“
- „Steiners grundlegende Kritik an Kant“

Stattdessen:

- Themenbereich **Kants Erkenntnistheorie** → eine Überschrift zu Ding an sich, Erscheinung, Subjekt-Objekt-Trennung und Erkenntnisgrenze
- Themenbereich **Steiners Kritik und Gegenposition** → eine Überschrift zu Kritik am kritischen Idealismus; Denken, Wahrnehmung, Wirklichkeit

## Breite sitzt in den Zeilen

Viele **Aussagen/Zitate** unter wenigen Überschriften. Lieber 6–14 substanzielle Zwischenüberschriften als 25 Varianten desselben Themas.

## JSON

Wenn die Recherche als JSON gebaut wird: `themeGroups[].title` plus `subThemes[].title` und `subThemes[].group` (gleicher Text wie der Themenbereich).
