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

Nicht als parallele Themenbereiche stehen lassen (Beispiel Kant):

- „Kants Erkenntnistheorie: Grundzüge und Kernbegriffe“
- „Kants Erkenntnistheorie: Ding an sich, Erscheinung und Erkenntnisgrenze“ (darin Hume, Verstand/Naturgesetze, Moralphilosophie)
- „Kants Erkenntnistheorie: Grundstruktur und Voraussetzungen“
- mehrere Goethe-Blöcke („Goethe und Kant“, „Kant und Goethe“, „… im Verhältnis zu Goethe“)
- mehrere Steiner-Kritik/Gegenposition/Denklehre-Blöcke

Stattdessen **ein** Bereich **Kants Erkenntnistheorie** mit den Zwischenüberschriften zu Ding an sich, Hume/Kausalität, Verstand/Naturgesetze, Moralphilosophie; **ein** Bereich **Steiners Kritik und Gegenposition**; **ein** Goethe-Bereich.

Die Inhaltsübersicht nummeriert nur die Zwischenüberschriften, nicht die Themenbereichstitel.

## Breite sitzt in den Zeilen

Viele **Aussagen/Zitate** unter wenigen Überschriften. Lieber 6–14 substanzielle Zwischenüberschriften als 25 Varianten desselben Themas.

## JSON

Wenn die Recherche als JSON gebaut wird: `themeGroups[].title` plus `subThemes[].title` und `subThemes[].group` (gleicher Text wie der Themenbereich).
