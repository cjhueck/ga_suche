#!/usr/bin/env python3
"""
Rechtschreibregeln für Steiner GA-Suche
========================================

Diese Datei enthält alle Rechtschreibkorrekturen, die auf die Daten angewendet werden.
Die Regeln basieren auf der Umstellung von alter zu neuer deutscher Rechtschreibung.

Verwendung:
    from rechtschreibregeln import korrigiere_rechtschreibung
    
    text = "daß muß Bewußtsein"
    korrigiert = korrigiere_rechtschreibung(text)
    # Ergebnis: "dass muss Bewusstsein"
"""

import re


def korrigiere_rechtschreibung(text):
    """
    Korrigiere alte Rechtschreibung zu neuer deutscher Rechtschreibung.
    
    Args:
        text (str): Der zu korrigierende Text
        
    Returns:
        str: Der korrigierte Text
    """
    if not isinstance(text, str):
        return text
    
    # Ersetze lange Gedankenstriche durch kurze
    text = text.replace('—', '-')
    
    # Ersetze kk durch ck in deutschen Wörtern (Entwikklung → Entwicklung)
    def replace_kk(match):
        before = match.group(1)
        after = match.group(2)
        word = before + 'kk' + after
        
        # Überspringe wenn:
        # - Zu kurz (< 5 Zeichen)
        # - Enthält Sonderzeichen (URL, etc.)
        # - kk am Anfang des Wortes
        # - Wort enthält legitimes kk (Ausnahmen)
        # Ausnahmen: okkult*, *kehr (Rückkehr, zurückkehren), Akkord, Akkumulator, 
        #            Akkusativ, Mokka, Sakko, Stakkato, okkupier*, Brokkoli, sukkulen*
        word_lower = word.lower()
        kk_exceptions = ['okkult', 'kehr', 'akkord', 'akkum', 'akkus', 'mokka', 
                        'sakko', 'stakka', 'okkup', 'brokko', 'sukkul', 'makka']
        has_exception = any(exc in word_lower for exc in kk_exceptions)
        
        if (len(word) < 5 or not before or 
            any(c in word for c in ['/', ':', '.', '@', '_']) or
            has_exception):
            return match.group(0)
        
        # Ersetze kk durch ck
        return before + 'ck' + after
    
    kk_pattern = r'\b(\w+?)kk(\w+?)\b'
    text = re.sub(kk_pattern, replace_kk, text)
    
    # Wörterliste: Alte → Neue Rechtschreibung
    replacements = {
        # Häufigste: daß, muß, etc.
        'daß': 'dass',
        'Daß': 'Dass',
        'muß': 'muss',
        'mußt': 'musst',
        'mußte': 'musste',
        'mußtest': 'musstest',
        'mußtet': 'musstet',
        'mußten': 'mussten',
        'wußte': 'wusste',
        'gewußt': 'gewusst',
        
        # Bewusstsein und Varianten
        'Bewußtsein': 'Bewusstsein',
        'bewußt': 'bewusst',
        'Bewußtseins': 'Bewusstseins',
        'Bewußtseinszustand': 'Bewusstseinszustand',
        'Bewußtseinszustände': 'Bewusstseinszustände',
        'Unbewußtsein': 'Unbewusstsein',
        'unbewußt': 'unbewusst',
        'Selbstbewußtsein': 'Selbstbewusstsein',
        'selbstbewußt': 'selbstbewusst',
        
        # Weitere häufige: ißt, frißt, etc.
        'ißt': 'isst',
        'iß': 'iss',
        'frißt': 'frisst',
        
        # ß → ss (nach kurzem Vokal)
        'Kuß': 'Kuss',
        'Fluß': 'Fluss',
        'Schloß': 'Schloss',
        'Haß': 'Hass',
        'Nuß': 'Nuss',
        'Faß': 'Fass',
        'Preß': 'Press',
        'Miß': 'Miss',
        'miß': 'miss',
        'nuß': 'nuss',
        'fluß': 'fluss',
        'schloß': 'schloss',
        'kuß': 'kuss',
        'haß': 'hass',
        'faß': 'fass',
        'preß': 'press',
        'Anschluß': 'Anschluss',
        'schluß': 'schluss',
        'Schluß': 'Schluss',
        'biß': 'biss',
        'riß': 'riss',
        'floß': 'floss',
        'schoß': 'schoss',
        'Entschluß': 'Entschluss',
        'entschluß': 'entschluss',
        'häßlich': 'hässlich',
        'veranlaßt': 'veranlasst',
        'unermeßlich': 'unermesslich',
        'verläßt': 'verlässst',
        'verläßlich': 'verlässlich',
        
        # Konjunktiv: müßte, etc.
        'müßte': 'müsste',
        'müßtest': 'müsstest',
        'müßtet': 'müsstet',
        'müßten': 'müssten',
        
        # ss → ß (nach langem Vokal/Diphthong)
        'reisst': 'reißt',
        'Eiweiss': 'Eiweiß',
        'eiweiss': 'eiweiß',
        'läßt': 'lässt',
        'heisst': 'heißt',
        'weiss': 'weiß',
        
        # Zusammengesetzte Wörter mit Bindestrich
        'ChristusWesenheit': 'Christus-Wesenheit',
        'Johannes-Evangelium': 'Johannes-Evangelium',
        'SeelischGeistiges': 'Seelisch-Geistiges',
        'Geistig-Seelisches': 'Geistig-Seelisches',
        'geistigseelisch': 'geistig-seelisch',
        'seelischgeistig': 'seelisch-geistig',
        'westund mitteleuropäisch': 'west- und mitteleuropäisch',
        'von daoder von dorther': 'von da- oder von dorther',
        'EntwederOder': 'Entweder-Oder',
        
        # Prozeß → Prozess
        'Prozeß': 'Prozess',
        '..prozeß': '..prozess',
        
        # Zahlen: dreissig → dreißig
        'dreissig': 'dreißig',
        'dreiunddreissig': 'dreiunddreißig',
        
        # Zusätzliche aus export_master.py
        'Fleiss': 'Fleiß',
        'fleiss': 'fleiß',
        'vergeßlich': 'vergesslich',
        'heiss': 'heiß',
        'zurücckommen': 'zurückkommen',
        'ackurat': 'akkurat',
        'paßt': 'passt',
        'römischkatholisch': 'römisch-katholisch',
        'DeutschÖsterreicher': 'Deutsch-Österreicher',
        
        # Kongreß → Kongress
        'Kongreß': 'Kongress',
        'kongreß': 'kongress',
    }
    
    # Wende alle Ersetzungen an
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Regel: Zusammengesetzte Substantive mit großgeschriebenem zweiten Teil
    # müssen durch einen Bindestrich getrennt werden (z.B. GöttlichGeistiges => Göttlich-Geistiges)
    def add_hyphen_to_compound_nouns(match):
        """Fügt einen Bindestrich zwischen zwei Substantiven ein, wenn das zweite großgeschrieben ist."""
        word = match.group(0)
        # Finde die Stelle, wo ein Kleinbuchstabe auf einen Großbuchstaben folgt
        # Muster: [a-zäöüß][A-ZÄÖÜ] - funktioniert auch wenn das Wort mit Großbuchstabe beginnt
        pattern = r'([a-zäöüß])([A-ZÄÖÜ])'
        corrected = re.sub(pattern, r'\1-\2', word)
        return corrected
    
    # Finde Wörter, die aus zwei Teilen bestehen, wobei der zweite Teil mit Großbuchstabe beginnt
    # Muster: Mindestens ein Kleinbuchstabe (kann nach einem Großbuchstaben kommen), gefolgt von einem Großbuchstaben
    # Erfasst sowohl "göttlichGeistiges" als auch "GöttlichGeistiges"
    compound_pattern = r'\b[A-ZÄÖÜ]?[a-zäöüß]+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ]*\b'
    text = re.sub(compound_pattern, add_hyphen_to_compound_nouns, text)
    
    return text


def korrigiere_json_obj(obj):
    """
    Rekursiv durch JSON-Objekt gehen und Rechtschreibung korrigieren.
    
    Args:
        obj: JSON-Objekt (dict, list, str, oder andere Typen)
        
    Returns:
        Korrigiertes JSON-Objekt
    """
    if isinstance(obj, dict):
        return {key: korrigiere_json_obj(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [korrigiere_json_obj(item) for item in obj]
    elif isinstance(obj, str):
        return korrigiere_rechtschreibung(obj)
    else:
        return obj


# Liste aller Ersetzungen für Dokumentation/Export
def get_replacements_dict():
    """
    Gibt das Dictionary aller Ersetzungen zurück.
    Nützlich für Dokumentation oder Export der Regeln.
    
    Returns:
        dict: Dictionary mit alten → neuen Schreibweisen
    """
    return {
        'daß': 'dass',
        'Daß': 'Dass',
        'muß': 'muss',
        'mußt': 'musst',
        'mußte': 'musste',
        'mußtest': 'musstest',
        'mußtet': 'musstet',
        'mußten': 'mussten',
        'wußte': 'wusste',
        'gewußt': 'gewusst',
        'Bewußtsein': 'Bewusstsein',
        'bewußt': 'bewusst',
        'Bewußtseins': 'Bewusstseins',
        'Bewußtseinszustand': 'Bewusstseinszustand',
        'Bewußtseinszustände': 'Bewusstseinszustände',
        'Unbewußtsein': 'Unbewusstsein',
        'unbewußt': 'unbewusst',
        'Selbstbewußtsein': 'Selbstbewusstsein',
        'selbstbewußt': 'selbstbewusst',
        'ißt': 'isst',
        'iß': 'iss',
        'frißt': 'frisst',
        'Kuß': 'Kuss',
        'Fluß': 'Fluss',
        'Schloß': 'Schloss',
        'Haß': 'Hass',
        'Nuß': 'Nuss',
        'Faß': 'Fass',
        'Preß': 'Press',
        'Miß': 'Miss',
        'miß': 'miss',
        'nuß': 'nuss',
        'fluß': 'fluss',
        'schloß': 'schloss',
        'kuß': 'kuss',
        'haß': 'hass',
        'faß': 'fass',
        'preß': 'press',
        'Anschluß': 'Anschluss',
        'schluß': 'schluss',
        'Schluß': 'Schluss',
        'biß': 'biss',
        'riß': 'riss',
        'floß': 'floss',
        'schoß': 'schoss',
        'Entschluß': 'Entschluss',
        'entschluß': 'entschluss',
        'müßte': 'müsste',
        'müßtest': 'müsstest',
        'müßtet': 'müsstet',
        'müßten': 'müssten',
        'reisst': 'reißt',
        'Eiweiss': 'Eiweiß',
        'eiweiss': 'eiweiß',
        'läßt': 'lässt',
        'heisst': 'heißt',
        'weiss': 'weiß',
        'ChristusWesenheit': 'Christus-Wesenheit',
        'Johannes-Evangelium': 'Johannes-Evangelium',
        'SeelischGeistiges': 'Seelisch-Geistiges',
        'Geistig-Seelisches': 'Geistig-Seelisches',
        'geistigseelisch': 'geistig-seelisch',
        'seelischgeistig': 'seelisch-geistig',
        'westund mitteleuropäisch': 'west- und mitteleuropäisch',
        'von daoder von dorther': 'von da- oder von dorther',
        'EntwederOder': 'Entweder-Oder',
        'Prozeß': 'Prozess',
        '..prozeß': '..prozess',
        'dreissig': 'dreißig',
        'dreiunddreissig': 'dreiunddreißig',
        'Fleiss': 'Fleiß',
        'fleiss': 'fleiß',
        'vergeßlich': 'vergesslich',
        'heiss': 'heiß',
        'zurücckommen': 'zurückkommen',
        'ackurat': 'akkurat',
        'paßt': 'passt',
        'römischkatholisch': 'römisch-katholisch',
        'DeutschÖsterreicher': 'Deutsch-Österreicher',
        
        # Kongreß → Kongress
        'Kongreß': 'Kongress',
        'kongreß': 'kongress',
    }


if __name__ == '__main__':
    # Test-Beispiele
    test_cases = [
        "daß muß Bewußtsein",
        "Haß Fluß Schloß",
        "mußte wußte gewußt",
        "heisst weiss läßt",
        "ChristusWesenheit Johannes-Evangelium",
        "Prozeß Entschluß",
        "Kongreß und Kongresse",
        "GöttlichGeistiges und SeelischGeistiges",
    ]
    
    print("Test der Rechtschreibkorrekturen:")
    print("=" * 60)
    for test in test_cases:
        korrigiert = korrigiere_rechtschreibung(test)
        print(f"Vorher: {test}")
        print(f"Nachher: {korrigiert}")
        print()

