#!/usr/bin/env python3
"""
Korrigiert falsche "oß"/"Oß" Schreibweisen zu "ob"/"Ob" in Steiner_GA Dateien
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Mapping von falschen zu korrekten Schreibweisen
CORRECTIONS = {
    # Häufigste Fehler
    'oßen': 'oben',
    'Oktoßer': 'Oktober',
    'beoßachten': 'beobachten',
    'Beoßachtung': 'Beobachtung',
    'beoßachtet': 'beobachtet',
    'Beoßachtungen': 'Beobachtungen',
    'Beoßachter': 'Beobachter',
    'Selbstbeoßachtung': 'Selbstbeobachtung',
    'oßerfläche': 'Oberfläche',
    'oßerflächlich': 'oberflächlich',
    'oßwohl': 'obwohl',
    'oßgleich': 'obgleich',
    'oßjektiv': 'objektiv',
    'oßjektive': 'objektive',
    'oßjektiven': 'objektiven',
    'oßjektiver': 'objektiver',
    'oßjektivität': 'Objektivität',
    'oßjekt': 'Objekt',
    'Proßlem': 'Problem',
    'Proßleme': 'Probleme',
    'Proßlematik': 'Problematik',
    'Proßlematisierung': 'Problematisierung',
    'Grundproßlem': 'Grundproblem',
    'Entwicklungsproßlem': 'Entwicklungsproblem',
    'Daseinsproßlem': 'Daseinsproblem',
    'Schlafproßlem': 'Schlafproblem',
    'Glücksproßlematik': 'Glücksproblematik',
    # Weitere Varianten mit "proß" → "prob"
    'auszuproßieren': 'auszuprobieren',
    'proßieren': 'probieren',
    'proßierten': 'probierten',
    'proßierenden': 'probierenden',
    'proßierende': 'probierende',
    'proßierend': 'probierend',
    'proßiert': 'probiert',
    'proßiast': 'probiast',
    'Proßeweise': 'Probeweise',
    'proßeweisen': 'probeweisen',
    'proßeweise': 'probeweise',
    'Proßen': 'Proben',
    'proßen': 'proben',
    'proßte': 'probte',
    'proßt': 'probt',
    'proßten': 'probten',
    'Proßst': 'Probst',
    'Proßekandidaten': 'Probekandidaten',
    'Proßekandidat': 'Probekandidat',
    'Proßiergläschen': 'Probiergläschen',
    'Proßiergläsern': 'Probiergläsern',
    'Proßearbeiten': 'Probearbeiten',
    'Proßenarbeit': 'Probenarbeit',
    'Proßenzeit': 'Probenzeit',
    'Proßenummer': 'Probenummer',
    'Proßeheft': 'Probeheft',
    'Proßevorlesungen': 'Probevorlesungen',
    'Proßerede': 'Proberede',
    'Proßepredigt': 'Proberedigt',
    'Proßepfad': 'Probepfad',
    'Proßebogen': 'Probebogen',
    'Proßelektion': 'Probelektion',
    'Proßeerwägungen': 'Probeerwägungen',
    'Proßemanöver': 'Probemanöver',
    'Proßabilität': 'Probabilität',
    'Proßabilismus': 'Probabilismus',
    'Proßation': 'Probation',
    'Approßation': 'Approbation',
    'approßierten': 'approbierten',
    'herumproßieren': 'herumprobieren',
    'herumproßiert': 'herumprobiert',
    'ausgeproßt': 'ausgeprobt',
    'erproßt': 'erprobt',
    'erproßte': 'erprobte',
    'erproßen': 'erproben',
    'Erproßen': 'Erproben',
    'herproßiert': 'herprobiert',
    'proßateren': 'probateren',
    'proßare': 'probare',
    'proßiern': 'probiern',
    'proßeweisemachen': 'probeweisemachen',
    'proßenlose': 'probenlose',
    # Weitere Varianten mit "proß" → "prob" in zusammengesetzten Wörtern
    'Erziehungsproßleme': 'Erziehungsprobleme',
    'Weltenproßlem': 'Weltenproblem',
    'Weltproßlemen': 'Weltproblemen',
    'Weltproßlem': 'Weltproblem',
    'Weltproßlem_': 'Weltproblem',
    'Zeitproßleme': 'Zeitprobleme',
    'Zeitproßlematik': 'Zeitproblematik',
    'Kampfproßleme': 'Kampfproßleme',
    'Seelenproßleme': 'Seelenprobleme',
    'Kulturproßleme': 'Kulturproßleme',
    'Kulturproßlematik': 'Kulturproblematik',
    'Culturproßlem': 'Culturproblem',
    'Herzensproßlem': 'Herzensproblem',
    'Mutterproßlem': 'Mutterproblem',
    'Madonnenproßlems': 'Madonnenproblems',
    'Todesproßlemes': 'Todesproblems',
    'Gedächtnisproßlem': 'Gedächtnisproblem',
    'Aufmerksamkeitsproßlem': 'Aufmerksamkeitsproblem',
    'Kardinalproßlem': 'Kardinalproblem',
    'Scholastikerproßlems': 'Scholastikerproblems',
    'Scholastikproßlems': 'Scholastikproblems',
    'Generalproßlemen': 'Generalproblemen',
    'Spezialistenproßleme': 'Spezialistenprobleme',
    'Spezialproßleme': 'Spezialprobleme',
    'Grenzproßlemen': 'Grenzproblemen',
    'Weltanschauungsproßleme': 'Weltanschauungsprobleme',
    'Triebproßlems': 'Triebproblems',
    'Machtproßlem': 'Machtproblem',
    'Machtproßlemen': 'Machtproblemen',
    'Nationalproßlem': 'Nationalproblem',
    'Qualitätsproßlem': 'Qualitätsproblem',
    'Logosproßlem': 'Logosproblem',
    'Ödipusproßlem': 'Ödipusproblem',
    'ÖdipusProßlem': 'ÖdipusProblem',
    'Farbenproßlem': 'Farbenproblem',
    'Farbenproßlemtik': 'Farbenproblemtik',
    'Denkproßlem': 'Denkproblem',
    'Bewußtseinsproßlem': 'Bewußtseinsproblem',
    'Sozialisierungsproßlem': 'Sozialisierungsproblem',
    'Völkerproßleme': 'Völkerprobleme',
    'Bagdadproßlem': 'Bagdadproblem',
    '224Bagdadproßlem': '224Bagdadproblem',
    'Bagdadbabnproßlem': 'Bagdadbabnproblem',
    'Raumproßlem': 'Raumproblem',
    'Schönheitsproßlemes': 'Schönheitsproblems',
    'Liebesproßlem': 'Liebesproblem',
    'Kunstproßlemen': 'Kunstproblemen',
    'Kunstproßlematik': 'Kunstproblematik',
    'Identitätsproßlem': 'Identitätsproblem',
    'Proßlemlösung': 'Problemlösung',
    'Proßlemlösungen': 'Problemlösungen',
    'Proßlemlösern': 'Problemlösern',
    'Proßlemlösungsfähigkeit': 'Problemlösungsfähigkeit',
    'Proßlemlösungsfähigkeit_': 'Problemlösungsfähigkeit',
    'Furchtproßlem': 'Furchtproblem',
    'Angstproßlem': 'Angstproblem',
    'Wahrscheinlichkeitsproßlem': 'Wahrscheinlichkeitsproblem',
    'Kategorienproßlem': 'Kategorienproblem',
    'Selbstproßlematik': 'Selbstproblematik',
    'Selbst-Proßlematik': 'Selbst-Problematik',
    'Selbst-Proßlematik_': 'Selbst-Problematik',
    'Proßlematik_': 'Problematik',
    '_Proßlematik': 'Problematik',
    '_Proßlematische': 'Problematische',
    'Grundproßlematik': 'Grundproblematik',
    'Gegenwartsproßlematik': 'Gegenwartsproblematik',
    'Lebensproßlematik': 'Lebensproblematik',
    'Erkenntnisproßlematik': 'Erkenntnisproblematik',
    'Gesellschaftsproßlematik': 'Gesellschaftsproblematik',
    'Impfproßlematik': 'Impfproblematik',
    'Vergänglichkeitsproßlem': 'Vergänglichkeitsproblem',
    'Überlieferungsproßleme': 'Überlieferungsprobleme',
    'Verständnisproßleme': 'Verständnisprobleme',
    'Erinnerungsproßlematik': 'Erinnerungsproblematik',
    'Hauptproßleme': 'Hauptprobleme',
    'Hauptproßleme_': 'Hauptprobleme',
    'Hauptproßlenie': 'Hauptproblenie',
    'Frauenproßlemromans': 'Frauenproblemromans',
    'Wärmetodproßlems': 'Wärmetodproblems',
    'Wärmetodproßlems_': 'Wärmetodproblems',
    'Daseinsproßlemen': 'Daseinsproblemen',
    'Daseinsproßleme': 'Daseinsprobleme',
    'Daseinsproßleme_': 'Daseinsprobleme',
    'Proßlem_': 'Problem',
    '_Proßlem': 'Problem',
    'Proßleme': 'Probleme',
    'Proßleme_': 'Probleme',
    '_Proßleme': 'Probleme',
    'Proßlemen': 'Problemen',
    'Proßlemen_': 'Problemen',
    'Proßlems': 'Problems',
    'Proßlems_': 'Problems',
    'Proßlemi': 'Problemi',
    'proßlema': 'problema',
    'proßlemas': 'problemas',
    'proßlème': 'problème',
    'proßlematic': 'problematic',
    'proßabably': 'probably',
    'Proßlemdramen': 'Problemdramen',
    'Proßlemcharakter': 'Problemcharakter',
    'Proßlembereiche': 'Problembereiche',
    'Erinnerungsproßlem': 'Erinnerungsproblem',
    'Erkenntnisproßlems': 'Erkenntnisproblems',
    'Erkenntnisproßlems_': 'Erkenntnisproblems',
    'Erkenntnisproßlern': 'Erkenntnisproblern',
    'Lebensproßlems': 'Lebensproblems',
    'Lebensproßlems_': 'Lebensproblems',
    'Lebensproßleme': 'Lebensprobleme',
    'Lebensproßleme_': 'Lebensprobleme',
    'Lebensproßlen': 'Lebensproblen',
    'Freiheitsproßleml': 'Freiheitsprobleml',
    'Wertproßlems': 'Wertproblems',
    'Gewissheitsproßlems': 'Gewissheitsproblems',
    'Individualitätsproßlems': 'Individualitätsproblems',
    'Individualitätsproßlem': 'Individualitätsproblem',
    'Schulproßleme': 'Schulprobleme',
    'Vortragsproßleme': 'Vortragsprobleme',
    'Kantproßlem': 'Kantproblem',
    'Architekturproßlem': 'Architekturproblem',
    'Dichterproßlem': 'Dichterproblem',
    'Mosesproßlem': 'Mosesproblem',
    'Christusproßlem': 'Christusproblem',
    'ChristusProßlem': 'ChristusProblem',
    'Christusproßlems': 'Christusproblems',
    'ChristusProßlems': 'ChristusProblems',
    'Todesproßlemes': 'Todesproblems',
    'Blutproße': 'Blutprobe',
    'Lebensproßen': 'Lebensproben',
    'Lebensproßlen': 'Lebensproblen',
    'Kraftproße': 'Kraftprobe',
    'Kraftproßen': 'Kraftproben',
    'Belastungsproße': 'Belastungsprobe',
    'Gegenproße': 'Gegenprobe',
    'Stichproßen': 'Stichproben',
    'Generalproßen': 'Generalproben',
    'Eurythmieproße': 'Eurythmieprobe',
    'Eurythmieproßen': 'Eurythmieproben',
    'Leseproßen': 'Leseproben',
    'Lehrproßen': 'Lehrproben',
    'Lichtproßen': 'Lichtproben',
    'Lichtproße': 'Lichtprobe',
    'Luftproße': 'Luftprobe',
    'Leidensproßen': 'Leidensproben',
    'Schriftproßen': 'Schriftproben',
    'Szenenproßen': 'Szenenproben',
    'Geduldsproße': 'Geduldsprobe',
    'Chorproße': 'Chorprobe',
    'Opernproße': 'Opernprobe',
    'Talentproße': 'Talentprobe',
    'Handschriftenproße': 'Handschriftenprobe',
    'Charakterproße': 'Charakterprobe',
    'Charakterproßen': 'Charakterproben',
    'rakterproßen': 'rakterproben',
    'Seelenproßen': 'Seelenproben',
    'Zeitenproßen': 'Zeitenproben',
    'Machtproße': 'Machtprobe',
    'Zerreißproße': 'Zerreißprobe',
    'Kulissenproßen': 'Kulissenproben',
    'Weihnachtsspielproßen': 'Weihnachtsspielproben',
    'Gesangproßen': 'Gesangproben',
    'Amtsproßezeit': 'Amtsprobezeit',
    'Stilproße': 'Stilprobe',
    'Proßenzeit': 'Probenzeit',
    'Vergänglichkeitsproßlem': 'Vergänglichkeitsproblem',
    'Willensproßlem': 'Willensproblem',
    'Realitätsproßlem': 'Realitätsproblem',
    'Grundlagenproßlem': 'Grundlagenproblem',
    'Materieproßlem': 'Materieproblem',
    'Empfindungsproßlem': 'Empfindungsproblem',
    'Berufsproßlem': 'Berufsproblem',
    'Glaubensproßlem': 'Glaubensproblem',
    'Wissensproßlem': 'Wissensproblem',
    'Kreditproßlem': 'Kreditproblem',
    'Preisproßlems': 'Preisproblems',
    'Lohnproßlems': 'Lohnproblems',
    'Kapitalproßlems': 'Kapitalproblems',
    'Kapitalproßleme': 'Kapitalprobleme',
    'Slawenproßlem': 'Slawenproblem',
    'Gegenwartsproßlem': 'Gegenwartsproblem',
    'Textproßleme': 'Textprobleme',
    'Kommunikationsproßlemen': 'Kommunikationsproblemen',
    'Übersetzungsproßleme': 'Übersetzungsprobleme',
    'Sexualproßleme': 'Sexualprobleme',
    'Sexualproßlem': 'Sexualproblem',
    'EinzelProßlemen': 'EinzelProblemen',
    'Zentralproßlemen': 'Zentralproblemen',
    'Eiszeitproßlem': 'Eiszeitproblem',
    'Faustproßlern': 'Faustproblern',
    'FaustProßlem': 'FaustProblem',
    'MusikantenProßlem': 'MusikantenProblem',
    'Langerproßte': 'Langerprobte',
    'Proßnitz': 'Probnitz',
    'Proßabilités': 'Probabilités',
    'proßlematisierten': 'problematisierten',
    'Jakoß': 'Jakob',
    'JAKoß': 'JAKob',
    'woßei': 'wobei',
    'soßald': 'sobald',
    'Soßald': 'Sobald',
    'oßeren': 'oberen',
    'oßere': 'obere',
    'erhoßen': 'erhoben',
    'erhoßene': 'erhobene',
    'eroßert': 'erobert',
    'eroßern': 'erobern',
    'Eroßerung': 'Eroberung',
    'Eroßerungen': 'Eroberungen',
    'Wiedereroßerung': 'Wiedereroberung',
    'hervorgehoßen': 'hervorgehoben',
    'herausgehoßen': 'herausgehoben',
    'Roßert': 'Robert',
    'oßsidian': 'obsidian',
    'oßsidianSteiner': 'obsidianSteiner',
    'oßerland': 'Oberland',
    'Goßineaus': 'Gobineaus',
}

# Wörter, die NICHT geändert werden sollen (korrekte deutsche Wörter mit "oß")
PROTECTED_WORDS = {
    'bloß', 'bloßen', 'bloße', 'bloßer', 'bloßes', 'bloßem',
    'groß', 'großen', 'große', 'großer', 'großes', 'großem', 'größte', 'größer', 'größten',
    'stoßen', 'Schoße', 'Anstoß', 'Großbritannien', 'Großgrundbesitzerin',
    'Großbritannien', 'großartig', 'Großes', 'Großen', 'Große',
}

def fix_oss_errors():
    """Korrigiere falsche 'oß'/'Oß' Schreibweisen"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
    # Sortiere Korrekturen nach Länge (längere zuerst), um Teilstring-Probleme zu vermeiden
    sorted_corrections = sorted(CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for md_file in steiner_ga_dir.rglob("*.md"):
        try:
            # Versuche verschiedene Kodierungen
            content = None
            encoding_used = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(md_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"Konnte {md_file} nicht lesen")
                continue
            
            original_content = content
            file_replacements = 0
            
            # Führe alle Korrekturen durch
            for wrong, correct in sorted_corrections:
                # Überspringe "sproß" Varianten - diese sind korrekt!
                if 'sproß' in wrong.lower() or wrong.lower().startswith('sproß'):
                    continue
                
                # Verwende Word-Boundaries, um Teilstring-Probleme zu vermeiden
                pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
                matches = pattern.findall(content)
                if matches:
                    count = len(matches)
                    content = pattern.sub(correct, content)
                    stats[wrong] += count
                    file_replacements += count
            
            # Speichere nur wenn Änderungen vorgenommen wurden
            if content != original_content:
                # Schreibe korrigierte Version
                with open(md_file, 'w', encoding=encoding_used or 'utf-8') as f:
                    f.write(content)
                
                files_modified.append(str(md_file.relative_to(steiner_ga_dir)))
                total_replacements += file_replacements
                print(f"[OK] {md_file.name}: {file_replacements} Korrekturen")
                
        except Exception as e:
            print(f"Fehler bei {md_file}: {e}")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("KORREKTUR ABGESCHLOSSEN")
    print("=" * 80)
    print(f"\nDateien geändert: {len(files_modified)}")
    print(f"Gesamt-Korrekturen: {total_replacements}")
    
    print("\nKorrekturen nach Wort:")
    for wrong, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        correct = CORRECTIONS[wrong]
        print(f"  '{wrong}' -> '{correct}': {count}x")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('oss_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'oss_corrections_log.txt'")

if __name__ == "__main__":
    print("Starte Korrektur der 'oß'/'Oß' Fehler...")
    print("=" * 80)
    fix_oss_errors()

