#!/usr/bin/env python3
"""
Überträgt Absatz-IDs von einer alten Markdown-Datei auf eine neue.
Die Zuordnung erfolgt über normalisierte Textvergleiche,
wobei Rechtschreibvarianten (ß/ss, daß/dass etc.) und Seitenmarker ignoriert werden.
"""

import re
import os
import shutil
from difflib import SequenceMatcher

OLD_FILE = r"Steiner_GA\GA259-Das Schicksalsjahr 1923 in der AG\GA259 - Das Schicksalsjahr 1923 in der AG (1923)_alt.md"
NEW_FILE = r"Steiner_GA\GA259-Das Schicksalsjahr 1923 in der AG\GA259 - Das Schicksalsjahr 1923 in der Geschichte der Anthroposophischen Gesellschaft (1923).md"
BACKUP_FILE = NEW_FILE + '.bak'

def normalize(text):
    """Normalisiert Text für Vergleiche."""
    t = text.strip()
    # Seitenmarker |123| entfernen
    t = re.sub(r'\|(\d+)\|', '', t)
    # Absatz-ID am Ende entfernen
    t = re.sub(r'\s+\^[a-z0-9]+$', '', t)
    # Heading-Marker entfernen
    t = re.sub(r'^#{1,6}\s+', '', t)
    # ß -> ss (alte -> neue Rechtschreibung)
    t = t.replace('\u00df', 'ss')
    # ſ -> s
    t = t.replace('\u017f', 's')
    # Anführungszeichen vereinheitlichen
    for c in '\u00ab\u00bb\u201e\u201c\u201d\u201a\u2018\u2019':
        t = t.replace(c, '"')
    # Gedankenstriche vereinheitlichen
    for c in '\u2013\u2014\u2010\u2011\u2012\u2212':
        t = t.replace(c, '-')
    # Mehrfache Leerzeichen
    t = re.sub(r'\s+', ' ', t)
    t = t.strip().lower()
    return t


def extract_paragraphs_with_ids(filepath):
    """Extrahiert Absätze mit IDs aus der alten Datei."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    paragraphs = []
    current_para = []

    for line in lines:
        if line.strip() == '':
            if current_para:
                full_para = '\n'.join(current_para)
                id_match = re.search(r'\s+\^([a-z0-9]+)$', full_para.rstrip())
                if id_match:
                    para_id = id_match.group(1)
                    text = full_para[:id_match.start()].strip()
                    if not text:
                        text = re.sub(r'\s+\^[a-z0-9]+$', '', full_para.rstrip()).strip()
                    paragraphs.append((text, para_id))
                current_para = []
        else:
            current_para.append(line)

    if current_para:
        full_para = '\n'.join(current_para)
        id_match = re.search(r'\s+\^([a-z0-9]+)$', full_para.rstrip())
        if id_match:
            para_id = id_match.group(1)
            text = full_para[:id_match.start()].strip()
            if not text:
                text = re.sub(r'\s+\^[a-z0-9]+$', '', full_para.rstrip()).strip()
            paragraphs.append((text, para_id))

    return paragraphs


def extract_new_paragraphs(filepath):
    """Extrahiert Absätze aus der neuen Datei.
    Gibt Liste von (last_line_idx, text) Tupeln und die Zeilen zurück."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    paragraphs = []
    current_para_lines = []

    for i, line in enumerate(lines):
        if line.strip() == '':
            if current_para_lines:
                text = ''.join(current_para_lines).strip()
                last_line_idx = i - 1
                paragraphs.append((last_line_idx, text))
                current_para_lines = []
        else:
            current_para_lines.append(line)

    if current_para_lines:
        text = ''.join(current_para_lines).strip()
        last_line_idx = len(lines) - 1
        paragraphs.append((last_line_idx, text))

    return paragraphs, lines


def get_signature(norm_text, n_words=6):
    """Gibt die ersten n Wörter als Signatur zurück."""
    words = norm_text.split()
    return ' '.join(words[:n_words])


def main():
    print("=== ID-\u00dcbertragung GA259 ===\n")

    # Backup wiederherstellen (falls vorhanden) um sauber zu starten
    if os.path.exists(BACKUP_FILE):
        shutil.copy2(BACKUP_FILE, NEW_FILE)
        print(f"Backup wiederhergestellt: {BACKUP_FILE} -> {NEW_FILE}")
    else:
        shutil.copy2(NEW_FILE, BACKUP_FILE)
        print(f"Backup erstellt: {BACKUP_FILE}")

    # Alte Absätze mit IDs extrahieren
    old_paras = extract_paragraphs_with_ids(OLD_FILE)
    print(f"Alte Datei: {len(old_paras)} Abs\u00e4tze mit IDs gefunden")

    # Neue Absätze extrahieren
    new_paras, new_lines = extract_new_paragraphs(NEW_FILE)
    print(f"Neue Datei: {len(new_paras)} Abs\u00e4tze, {len(new_lines)} Zeilen\n")

    # Normalisierte Versionen
    old_norms = [normalize(text) for text, _ in old_paras]
    new_norms = [normalize(text) for _, text in new_paras]

    # === PASS 1: Exakte normalisierte Matches ===
    print("Pass 1: Exakte normalisierte Matches...")
    new_norm_to_idx = {}
    # Bei Duplikaten: alle Indizes merken
    new_norm_to_indices = {}
    for i, norm in enumerate(new_norms):
        if norm not in new_norm_to_indices:
            new_norm_to_indices[norm] = []
        new_norm_to_indices[norm].append(i)

    matches = {}  # old_idx -> (new_idx, score, method)
    used_new = set()

    for old_idx, old_norm in enumerate(old_norms):
        if old_norm and old_norm in new_norm_to_indices:
            candidates = [i for i in new_norm_to_indices[old_norm] if i not in used_new]
            if candidates:
                # Nimm den ersten verfügbaren
                new_idx = candidates[0]
                matches[old_idx] = (new_idx, 1.0, 'exact')
                used_new.add(new_idx)

    print(f"  -> {len(matches)} exakte Matches\n")

    # === PASS 2: Erste-Wörter-Signatur-Match ===
    print("Pass 2: Signatur-basiertes Matching (erste W\u00f6rter)...")
    # Signatur-Index aufbauen
    sig_to_new_indices = {}
    for i, norm in enumerate(new_norms):
        if i in used_new:
            continue
        for n in [8, 6]:
            sig = get_signature(norm, n)
            if len(sig) > 15:
                if sig not in sig_to_new_indices:
                    sig_to_new_indices[sig] = []
                sig_to_new_indices[sig].append((i, n))

    pass2_count = 0
    for old_idx in range(len(old_paras)):
        if old_idx in matches:
            continue
        old_norm = old_norms[old_idx]
        if len(old_norm) < 10:
            continue

        best_new_idx = -1
        best_score = 0

        for n in [8, 6]:
            sig = get_signature(old_norm, n)
            if len(sig) > 15 and sig in sig_to_new_indices:
                candidates = [(i, nn) for i, nn in sig_to_new_indices[sig] if i not in used_new]
                for new_idx, nn in candidates:
                    score = SequenceMatcher(None, old_norm, new_norms[new_idx]).ratio()
                    if score > best_score:
                        best_score = score
                        best_new_idx = new_idx

        if best_new_idx >= 0 and best_score >= 0.5:
            matches[old_idx] = (best_new_idx, best_score, 'signature')
            used_new.add(best_new_idx)
            pass2_count += 1

    print(f"  -> {pass2_count} Signatur-Matches\n")

    # === PASS 3: Substring-basiertes Matching ===
    print("Pass 3: Substring-basiertes Matching...")
    pass3_count = 0

    # Erstelle einen zusammenhängenden normalisierten Text der neuen Datei
    # mit Positionsreferenzen zu Absätzen
    for old_idx in range(len(old_paras)):
        if old_idx in matches:
            continue
        old_norm = old_norms[old_idx]
        old_words = old_norm.split()
        if len(old_words) < 4:
            continue

        # Suche nach einem längeren Substring
        search_lens = [15, 10, 7]
        for wcount in search_lens:
            if len(old_words) < wcount:
                continue
            search_phrase = ' '.join(old_words[:wcount])
            found = False
            for new_idx in range(len(new_norms)):
                if new_idx in used_new:
                    continue
                if search_phrase in new_norms[new_idx]:
                    score = SequenceMatcher(None, old_norm, new_norms[new_idx]).ratio()
                    if score >= 0.35:
                        matches[old_idx] = (new_idx, score, 'substring')
                        used_new.add(new_idx)
                        pass3_count += 1
                        found = True
                        break
            if found:
                break

    print(f"  -> {pass3_count} Substring-Matches\n")

    # === PASS 4: Kurze Absätze (Überschriften etc.) mit flexiblerem Match ===
    print("Pass 4: Flexible Matches f\u00fcr kurze Abs\u00e4tze...")
    pass4_count = 0
    for old_idx in range(len(old_paras)):
        if old_idx in matches:
            continue
        old_norm = old_norms[old_idx]
        old_words = old_norm.split()
        if len(old_norm) < 3:
            continue

        best_new_idx = -1
        best_score = 0

        # Für sehr kurze Absätze: Enthaltensein prüfen
        if len(old_words) <= 8:
            for new_idx in range(len(new_norms)):
                if new_idx in used_new:
                    continue
                new_words = new_norms[new_idx].split()
                if len(new_words) > 20:
                    continue  # Kurzen alten Absatz nicht mit langem matchen
                # Prüfe ob der alte Text im neuen enthalten ist oder umgekehrt
                if old_norm in new_norms[new_idx] or new_norms[new_idx] in old_norm:
                    score = SequenceMatcher(None, old_norm, new_norms[new_idx]).ratio()
                    if score > best_score:
                        best_score = score
                        best_new_idx = new_idx
                elif len(old_words) >= 2 and len(new_words) >= 2:
                    score = SequenceMatcher(None, old_norm, new_norms[new_idx]).ratio()
                    if score > best_score and score >= 0.6:
                        best_score = score
                        best_new_idx = new_idx

        if best_new_idx >= 0 and best_score >= 0.55:
            matches[old_idx] = (best_new_idx, best_score, 'short')
            used_new.add(best_new_idx)
            pass4_count += 1

    print(f"  -> {pass4_count} kurze Matches\n")

    # === PASS 5: Similarity-basiertes Matching mit Positionsheuristik ===
    print("Pass 5: Similarity mit Positionsheuristik...")
    pass5_count = 0

    # Berechne erwartete relative Position für ungematchte alte Absätze
    # basierend auf bereits gematchten
    matched_positions = sorted([(old_idx, new_idx) for old_idx, (new_idx, _, _) in matches.items()])

    for old_idx in range(len(old_paras)):
        if old_idx in matches:
            continue
        old_norm = old_norms[old_idx]
        if len(old_norm) < 10:
            continue

        # Schätze die erwartete Position im neuen Text
        expected_new_idx = -1
        # Finde die nächsten gematchten Nachbarn
        prev_match = None
        next_match = None
        for m_old, m_new in matched_positions:
            if m_old < old_idx:
                prev_match = (m_old, m_new)
            elif m_old > old_idx and next_match is None:
                next_match = (m_old, m_new)

        if prev_match and next_match:
            # Interpoliere
            frac = (old_idx - prev_match[0]) / max(1, next_match[0] - prev_match[0])
            expected_new_idx = int(prev_match[1] + frac * (next_match[1] - prev_match[1]))
        elif prev_match:
            expected_new_idx = prev_match[1] + (old_idx - prev_match[0])
        elif next_match:
            expected_new_idx = max(0, next_match[1] - (next_match[0] - old_idx))
        else:
            expected_new_idx = int(old_idx * len(new_paras) / max(1, len(old_paras)))

        # Suche in einem Fenster um die erwartete Position
        window = 80
        search_start = max(0, expected_new_idx - window)
        search_end = min(len(new_norms), expected_new_idx + window)

        best_new_idx = -1
        best_score = 0

        for new_idx in range(search_start, search_end):
            if new_idx in used_new:
                continue
            score = SequenceMatcher(None, old_norm, new_norms[new_idx]).ratio()
            if score > best_score:
                best_score = score
                best_new_idx = new_idx

        if best_new_idx >= 0 and best_score >= 0.60:
            matches[old_idx] = (best_new_idx, best_score, 'similarity')
            used_new.add(best_new_idx)
            pass5_count += 1
            # Update matched_positions for subsequent iterations
            matched_positions.append((old_idx, best_new_idx))
            matched_positions.sort()

    print(f"  -> {pass5_count} Similarity-Matches\n")

    # === Statistik ===
    total_matched = len(matches)
    total_unmatched = len(old_paras) - total_matched
    print(f"=== ERGEBNIS ===")
    print(f"Zugeordnet: {total_matched} von {len(old_paras)} IDs ({100*total_matched/len(old_paras):.1f}%)")
    print(f"Nicht zugeordnet: {total_unmatched}\n")

    # Score-Verteilung
    by_method = {}
    for old_idx, (new_idx, score, method) in matches.items():
        if method not in by_method:
            by_method[method] = []
        by_method[method].append(score)

    for method, scores in sorted(by_method.items()):
        avg = sum(scores) / len(scores)
        low = min(scores)
        print(f"  {method}: {len(scores)} Matches, avg Score {avg:.2f}, min {low:.2f}")

    # Niedrige Scores anzeigen
    low_matches = [(old_idx, new_idx, score, method)
                   for old_idx, (new_idx, score, method) in matches.items()
                   if score < 0.6]
    if low_matches:
        print(f"\nMatches mit niedrigem Score (<0.6): {len(low_matches)}")
        for old_idx, new_idx, score, method in sorted(low_matches, key=lambda x: x[2])[:15]:
            old_text = old_paras[old_idx][0][:70]
            new_text = new_paras[new_idx][1][:70]
            pid = old_paras[old_idx][1]
            print(f"  ^{pid} ({method}, {score:.2f}):")
            print(f"    ALT: {old_text}")
            print(f"    NEU: {new_text}")

    # Nicht zugeordnete anzeigen
    unmatched_ids = [(old_idx, old_paras[old_idx][1], old_paras[old_idx][0][:80])
                     for old_idx in range(len(old_paras)) if old_idx not in matches]
    if unmatched_ids:
        print(f"\nNicht zugeordnete IDs ({len(unmatched_ids)}):")
        for idx, pid, text in unmatched_ids:
            print(f"  [{idx}] ^{pid}: {text}")

    # === IDs in neue Datei schreiben ===
    line_id_map = {}
    for old_idx, (new_idx, score, method) in matches.items():
        line_num = new_paras[new_idx][0]
        para_id = old_paras[old_idx][1]
        line_id_map[line_num] = para_id

    output_lines = []
    for i, line in enumerate(new_lines):
        if i in line_id_map:
            stripped = line.rstrip('\n')
            if re.search(r'\s+\^[a-z0-9]+$', stripped):
                output_lines.append(line)
            else:
                output_lines.append(stripped + ' ^' + line_id_map[i] + '\n')
        else:
            output_lines.append(line)

    with open(NEW_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"\nDatei geschrieben mit {total_matched} IDs: {NEW_FILE}")
    print("Fertig!")


if __name__ == '__main__':
    main()
