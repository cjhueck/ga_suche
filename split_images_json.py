#!/usr/bin/env python3
"""
Teilt steiner-images.json in Chunks von max. 10 MB auf
======================================================
Ähnlich wie steiner-full-lectures-*-part*.json

Output:
  steiner-images-part01.json (max 10 MB)
  steiner-images-part02.json (max 10 MB)
  ...
"""

import json
import os
import sys

def get_size_mb(obj):
    """Berechnet Größe eines JSON-Objekts in MB"""
    json_str = json.dumps(obj, ensure_ascii=False)
    return len(json_str.encode('utf-8')) / (1024 * 1024)

def split_images_json(input_file, max_size_mb=10):
    """Teilt steiner-images.json in Chunks auf"""
    
    print("=" * 70)
    print("STEINER-IMAGES.JSON SPLITTER")
    print("=" * 70)
    print(f"Input: {input_file}")
    print(f"Max. Chunk-Größe: {max_size_mb} MB")
    print("=" * 70 + "\n")
    
    # Lade steiner-images.json
    with open(input_file, 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    total_size = get_size_mb(images_data)
    print(f"Gesamt-Größe: {total_size:.2f} MB")
    print(f"Anzahl Vorträge: {len(images_data)}")
    
    # Berechne Gesamtanzahl Bilder
    total_images = sum(len(imgs) for imgs in images_data.values())
    print(f"Anzahl Bilder: {total_images}\n")
    
    # Sortiere Vorträge nach GA-Nummer (für bessere Organisation)
    sorted_lectures = sorted(images_data.keys())
    
    # Teile in Chunks
    chunks = []
    current_chunk = {}
    current_size = 0
    
    for lecture_id in sorted_lectures:
        images = images_data[lecture_id]
        
        # Berechne Größe dieses Eintrags
        entry_size = get_size_mb({lecture_id: images})
        
        # Wenn dieser Eintrag alleine zu groß ist, warnen
        if entry_size > max_size_mb:
            print(f"WARNUNG {lecture_id}: {entry_size:.2f} MB (groesser als {max_size_mb} MB Limit!)")
            print(f"   Dieser Vortrag wird trotzdem in einen eigenen Chunk gepackt.")
            
            # Speichere aktuellen Chunk falls nicht leer
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = {}
                current_size = 0
            
            # Vortrag in eigenen Chunk
            chunks.append({lecture_id: images})
            continue
        
        # Prüfe ob hinzufügen noch passt
        test_chunk = {**current_chunk, lecture_id: images}
        test_size = get_size_mb(test_chunk)
        
        if test_size > max_size_mb and current_chunk:
            # Aktueller Chunk ist voll, starte neuen
            chunks.append(current_chunk)
            current_chunk = {lecture_id: images}
            current_size = entry_size
        else:
            # Füge zu aktuellem Chunk hinzu
            current_chunk[lecture_id] = images
            current_size = test_size
    
    # Letzten Chunk speichern
    if current_chunk:
        chunks.append(current_chunk)
    
    print(f"\nAufteilung in {len(chunks)} Chunks:\n")
    
    # Speichere Chunks
    output_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_num = i + 1
        filename = f"steiner-images-part{chunk_num:02d}.json"
        
        # Speichere Chunk
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        chunk_size = get_size_mb(chunk)
        chunk_lectures = len(chunk)
        chunk_images = sum(len(imgs) for imgs in chunk.values())
        
        print(f"  + {filename}")
        print(f"    Groesse: {chunk_size:.2f} MB")
        print(f"    Vortraege: {chunk_lectures}")
        print(f"    Bilder: {chunk_images}\n")
        
        output_files.append(filename)
    
    print("=" * 70)
    print("FERTIG!")
    print("=" * 70)
    print(f"  Chunks erstellt: {len(chunks)}")
    print(f"  Dateien: {', '.join(output_files)}")
    print("=" * 70 + "\n")
    
    print("Nächste Schritte:")
    print("  1. Alte steiner-images.json löschen oder umbenennen")
    print("  2. Backend anpassen zum Laden mehrerer Chunks")
    print("  3. Git commit & push\n")
    
    return output_files

if __name__ == "__main__":
    input_file = "steiner-images.json"
    
    if not os.path.exists(input_file):
        print(f"\nFehler: {input_file} nicht gefunden!")
        sys.exit(1)
    
    split_images_json(input_file, max_size_mb=10)

