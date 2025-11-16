# Video-Transkription mit Python

## Installation

1. **Python installieren** (falls noch nicht vorhanden)
   - Download: https://www.python.org/downloads/
   - Bei Installation: "Add Python to PATH" aktivieren

2. **Erforderliche Pakete installieren**

```bash
pip install openai-whisper
```

Falls Sie FFmpeg-Fehler bekommen:
```bash
pip install setuptools-rust
# Oder FFmpeg separat installieren: https://ffmpeg.org/download.html
```

## Verwendung

### Schnellstart (Standard-Video)
```bash
python transcribe_video.py
```

### Eigenes Video angeben
```bash
python transcribe_video.py "pfad\zur\video.mp4"
```

### Modellgröße wählen
```bash
# Schnell, niedrige Qualität
python transcribe_video.py "video.mp4" tiny

# Standard (empfohlen)
python transcribe_video.py "video.mp4" base

# Hohe Qualität (langsamer)
python transcribe_video.py "video.mp4" small

# Beste Qualität (sehr langsam)
python transcribe_video.py "video.mp4" medium
```

## Modelle

- **tiny**: ~1 GB RAM, sehr schnell, niedrige Qualität
- **base**: ~1 GB RAM, schnell, gute Qualität (empfohlen)
- **small**: ~2 GB RAM, mittel, sehr gute Qualität
- **medium**: ~5 GB RAM, langsam, exzellente Qualität
- **large**: ~10 GB RAM, sehr langsam, beste Qualität

## Ausgabe

Die Transkription wird als TXT-Datei mit folgendem Format gespeichert:

```
[00:00 - 00:15]
Dies ist der erste Satz im Video.

[00:15 - 00:30]
Hier kommt der zweite Teil...
```

Am Ende folgt der komplette Text ohne Zeitstempel.

## Dauer

- 10 Min Video: ~2-5 Minuten (base-Modell)
- 60 Min Video: ~10-30 Minuten (base-Modell)

Die erste Ausführung dauert länger, da das Modell heruntergeladen wird (~150 MB).

## Fehlerbehandlung

### "No module named 'whisper'"
```bash
pip install --upgrade openai-whisper
```

### FFmpeg-Fehler
```bash
# Windows (mit Chocolatey)
choco install ffmpeg

# Oder manuell: https://ffmpeg.org/download.html
```

### CUDA/GPU-Unterstützung (optional, für schnellere Verarbeitung)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```


