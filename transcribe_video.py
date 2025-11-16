#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video-Transkription mit Zeitstempeln
Verwendet OpenAI Whisper für lokale Transkription
"""

import whisper
import os
import sys
from datetime import timedelta

def format_timestamp(seconds):
    """Konvertiert Sekunden in MM:SS Format"""
    td = timedelta(seconds=seconds)
    minutes = int(td.total_seconds() // 60)
    secs = int(td.total_seconds() % 60)
    return f"{minutes:02d}:{secs:02d}"

def transcribe_video(video_path, output_path=None, model_size="base"):
    """
    Transkribiert Video mit Zeitstempeln
    
    Args:
        video_path: Pfad zur Video-Datei
        output_path: Pfad zur Ausgabe-TXT-Datei (optional)
        model_size: Whisper-Modell ('tiny', 'base', 'small', 'medium', 'large')
                   - tiny: schnellste, niedrigste Qualität
                   - base: gut für Deutsch, empfohlen
                   - small: bessere Qualität
                   - medium/large: beste Qualität, aber langsam
    """
    
    # Prüfe ob Datei existiert
    if not os.path.exists(video_path):
        print(f"[FEHLER] Video-Datei nicht gefunden: {video_path}")
        sys.exit(1)
    
    # Erstelle Ausgabepfad wenn nicht angegeben
    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_transkription.txt"
    
    print(f"[VIDEO] {video_path}")
    print(f"[AUSGABE] {output_path}")
    print(f"[INFO] Lade Whisper-Modell '{model_size}'...")
    print("[INFO] Dies kann beim ersten Mal etwas dauern (Modell wird heruntergeladen)...\n")
    
    # Lade Whisper-Modell
    model = whisper.load_model(model_size)
    
    print("[START] Transkribiere Video...")
    print("[INFO] Dies kann je nach Videolänge einige Minuten dauern...\n")
    
    # Transkribiere mit Zeitstempeln
    result = model.transcribe(
        video_path,
        language="de",  # Deutsch
        verbose=True,   # Zeige Fortschritt
        word_timestamps=False  # Segment-Timestamps reichen
    )
    
    # Schreibe Ergebnis in Datei
    print(f"\n[SPEICHERN] Schreibe Transkription nach {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("VIDEO-TRANSKRIPTION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Video: {os.path.basename(video_path)}\n")
        f.write(f"Dauer: {format_timestamp(result.get('duration', 0))}\n")
        f.write(f"Sprache: {result.get('language', 'unbekannt')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Transkription mit Zeitstempeln
        for segment in result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            # Format: [MM:SS - MM:SS] Text
            f.write(f"[{start_time} - {end_time}]\n")
            f.write(f"{text}\n\n")
        
        # Volltext ohne Zeitstempel (am Ende)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VOLLTEXT (ohne Zeitstempel)\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['text'].strip())
        f.write("\n")
    
    print(f"[FERTIG] Transkription gespeichert in: {output_path}")
    print(f"[INFO] {len(result['segments'])} Segmente transkribiert")
    
    return output_path

if __name__ == "__main__":
    # Standard-Videopfad (kann angepasst werden)
    default_video = r"c:\Users\chuec\Videos\Bildschirmaufzeichnungen\Bildschirmaufnahme 2025-11-16 112140.mp4"
    
    # Verwende Kommandozeilenargument oder Standard
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = default_video
    
    # Optional: Modellgröße als zweites Argument
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    print("\n" + "=" * 80)
    print("VIDEO-TRANSKRIPTION MIT WHISPER")
    print("=" * 80 + "\n")
    
    transcribe_video(video_path, model_size=model_size)
    
    print("\n[FERTIG] Sie können die Transkription jetzt öffnen.")

