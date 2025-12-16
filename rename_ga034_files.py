#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript zum Umbenennen der GA034 Dateien mit Datumsangaben aus dem Inhaltsverzeichnis
"""

import os
import re

# Verzeichnis mit den Dateien
base_dir = r"c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA034-Lucifer-Gnosis 1903 bis 1908"

# Mapping: Dateinummer -> Datumsangabe
# Basierend auf dem Inhaltsverzeichnis des PDFs
date_mapping = {
    # AUFSÄTZE
    1: None,  # Zur Einführung - kein Datum
    2: "Juni 1903",  # Luzifer
    3: "Juli 1903",  # Meditation
    4: "Juli bis September 1903",  # Einweihung und Mysterien
    5: "September 1903",  # Meditation
    6: "Oktober-November 1903",  # Reinkarnation und Karma
    7: "Dezember 1903",  # Wie Karma wirkt
    8: None,  # Zur Einführung von «Lucifer-Gnosis» - hat schon Januar 1904 im Titel
    9: "Januar bis April 1904",  # Von der Aura des Menschen
    10: "Mai 1904",  # Die übersinnliche Welt und ihre Erkenntnis
    11: "September 1904",  # Aristoteles über das Mysteriendrama
    12: "März 1905",  # Vorrede zu Edouard Schurés Drama
    13: None,  # Zum Beginn des neuen Jahrganges - hat schon (Juni 1905) im Titel, Publikation Mai 1905
    14: "Juni 1905",  # Was bedeutet die Theosophie für den Menschen der Gegenwart
    15: "Juli 1905",  # Theosophie als Lebenspraxis
    16: "August 1905",  # Theosophie, Sittlichkeit und Gesundheit
    17: "September 1905",  # Theosophie und Wissenschaft
    18: "Oktober 1905 und 1906",  # Geisteswissenschaft und soziale Frage
    19: None,  # Haeckel - hat schon Datum im Titel (5. Oktober 1905), Publikation 1906
    20: "1906",  # Eduard von Hartmann. Nachruf
    21: "1906-1907",  # Lebensfragen der theosophischen Bewegung
    22: "Mai 1908",  # Theosophie und gegenwärtige Geistesströmungen
    23: "Mai 1908",  # Vorurteile aus vermeintlicher Wissenschaft
    24: "1907",  # Die Erziehung des Kindes
    25: "1907",  # Notiz über Friedrich August Wolf (WEGEN DER GROSSEN ZWISCHENZEIT...)
    26: "April 1908",  # An die Leser (FRAGEN UND ANTWORTEN)
    
    # DIE KULTUR DER GEGENWART IM SPIEGEL DER THEOSOPHIE
    27: "Juni 1903",  # Zum Buche von Théodule Ribot
    28: "Oktober-November 1903",  # Theosophie und Sozialismus
    29: "Dezember 1903",  # Die Theosophie und die Kulturaufgaben der Gegenwart
    30: "Januar 1904",  # Herder und die Theosophie
    31: "Februar 1904",  # Theosophie und moderne Naturwissenschaft
    32: "März 1904",  # Theosophie und modernes Leben
    33: "April 1904",  # Über das Vertreten der persönlichen Überzeugung
    34: "Mai 1904",  # Über den in der Wissenschaft scheinbar überwundenen Materialismus
    35: "September 1904",  # Über moderne naturwissenschaftliche Anschauungen
    36: "November 1904",  # Der englische Premierminister Balfour
    37: "Juni 1905",  # Zeitbilder (Zu Aufsätzen von Carnillo Schneider)
    
    # BEMERKUNGEN ZU AUFSÄTZEN
    38: "Januar-Mai 1904",  # Aus den nachgelassenen Papieren Paul Asmus'
    39: "Mai 1904",  # Zu einem Aufsatz von Lothar Brieger-Wasservogel
    40: "Juni-November 1904",  # Zum «Adeptenbuch» von A.M.O
    41: "Juli 1904",  # Zur Würdigung Schellings
    42: "Juli 1904",  # Zu Plotins Weltanschauung
    43: "1906",  # Einige Bemerkungen zu dem Aufsatz von Helene von Schewitsch
    
    # BESPRECHUNGEN THEOSOPHISCHER LITERATUR
    44: "August 1904",  # Besprechungen theosophischer Literatur (Die vier großen Religionen)
    
    # VON DER THEOSOPHISCHEN ARBEIT
    45: "Juni 1903",  # Von der theosophischen Arbeit (Theosophische Gesellschaft)
    46: "Oktober 1903",  # Theosophie und deutsche Kultur
    47: "November 1903",  # Okkulte Geschichtsforschung
    48: "April 1904",  # Hinweis auf den Kongress in Amsterdam
    49: "Juni 1904",  # Der theosophische Kongress in Amsterdam
    50: "August 1904",  # Mitteilung über Vorträge Annie Besants
    51: "August 1904",  # Weitere Mitteilungen
    52: "Oktober 1904",  # Notizen
    53: "Dezember 1904",  # Mitteilungen
    54: "Mai 1905",  # Hinweis (auf den Kongress in London)
    55: "Juni 1905",  # Mitteilungen (Von der Arbeit der Zweige)
    56: "September 1905",  # Die Arbeit in Stuttgart, Lugano, Weimar und Nürnberg
    57: "1906",  # Bildung neuer Zweige
    58: "Juli-August 1905",  # Der theosophische Kongress in London
    59: "1906",  # Hinweis (auf den Kongress in Paris)
    60: "1906",  # Der Kongress in Paris
    61: "1906",  # Nachruf auf die Gräfin Brockdorff
    62: "1906",  # Vorträge von Dr. Steiner
    63: "1907",  # Henry Steel Olcott (Nachruf)
    64: "1907",  # Mitteilungen
    65: "1907",  # Der Kongress der Föderation in München (Ankündigung)
    66: "1907",  # Der theosophische Kongress in München (Bericht)
    67: "1907",  # Zur bevorstehenden Präsidentenwahl
    68: "1907",  # Mitteilung (Annie Besant Wahl)
    69: None,  # HINWEISE - kein spezifisches Datum
}

def get_file_number(filename):
    """Extrahiert die Nummer aus dem Dateinamen"""
    match = re.search(r'GA034 \((\d+)\.\)', filename)
    if match:
        return int(match.group(1))
    return None

def has_date_in_filename(filename):
    """Prüft ob der Dateiname bereits ein Datum enthält"""
    # Prüft auf Muster wie (Juni 1905), (Januar 1904), etc.
    return bool(re.search(r'\([A-Za-z]+ \d{4}\)', filename)) or \
           bool(re.search(r'\(\d{4}\)', filename)) or \
           bool(re.search(r'Januar 1904', filename))

def rename_files(dry_run=True):
    """Benennt die Dateien um"""
    files = [f for f in os.listdir(base_dir) if f.endswith('.md') and f.startswith('GA034 (')]
    
    renamed_count = 0
    skipped_count = 0
    
    for filename in sorted(files, key=lambda x: get_file_number(x) or 0):
        file_num = get_file_number(filename)
        
        if file_num is None:
            print(f"[!] Konnte Nummer nicht extrahieren: {filename}")
            continue
        
        date = date_mapping.get(file_num)
        
        if date is None:
            print(f"[SKIP] Uebersprungen (kein Datum): {filename}")
            skipped_count += 1
            continue
        
        if has_date_in_filename(filename):
            print(f"[SKIP] Uebersprungen (hat bereits Datum): {filename}")
            skipped_count += 1
            continue
        
        # Neuen Dateinamen erstellen
        # Fuege das Datum vor .md ein
        new_filename = filename[:-3] + f" ({date}).md"
        
        old_path = os.path.join(base_dir, filename)
        new_path = os.path.join(base_dir, new_filename)
        
        if dry_run:
            print(f"[DRY] Wuerde umbenennen:\n   {filename}\n   -> {new_filename}\n")
            renamed_count += 1
        else:
            try:
                os.rename(old_path, new_path)
                print(f"[OK] Umbenannt:\n   {filename}\n   -> {new_filename}\n")
                renamed_count += 1
            except Exception as e:
                print(f"[ERROR] Fehler bei {filename}: {e}")
    
    print(f"\n{'='*60}")
    if dry_run:
        print(f"DRY RUN - Keine Dateien wurden geaendert!")
        print(f"Wuerde {renamed_count} Dateien umbenennen, {skipped_count} uebersprungen")
    else:
        print(f"Fertig! {renamed_count} Dateien umbenannt, {skipped_count} uebersprungen")

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("GA034 Dateien Umbenennung mit Datumsangaben")
    print("=" * 60)
    
    # Check for --execute flag
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        print("\nFuehre Umbenennung durch...\n")
        rename_files(dry_run=False)
    else:
        print("\nDRY RUN - Zeige was umbenannt werden wuerde:\n")
        rename_files(dry_run=True)
        print("\nUm die Umbenennung durchzufuehren, starten Sie mit: python rename_ga034_files.py --execute")
