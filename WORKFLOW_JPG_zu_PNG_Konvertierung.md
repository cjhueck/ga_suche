# Workflow: JPEG zu PNG Konvertierung und Export

## Übersicht
Dieser Workflow beschreibt, wie Sie alle JPEG-Bilder aus den GA-Ordnern in transparente PNG-Dateien umwandeln und in die `steiner-images.json` exportieren.

---

## Voraussetzungen

### Software
- **Python 3.x** (bereits installiert)
- **Pillow (PIL)** für Bildkonvertierung
  ```powershell
  pip install Pillow
  ```

### Ordnerstruktur
```
C:\Users\chuec\OneDrive\GitHub\Steiner_GA\
├── GA089-Bewusstsein Leben Form\      ← Bereits PNG
│   └── assets\
│       ├── GA089-Bewusstsein Leben Form_img-0.png
│       ├── GA089-Bewusstsein Leben Form_img-1.png
│       └── ...
├── GA090a-Selbsterkenntnis und Gotteserkenntnis I\  ← Noch JPEG
│   └── assets\
│       ├── GA090a-..._img-0.jpeg
│       └── ...
└── ... (weitere GA-Bände)
```

---

## Schritt 1: JPEG zu PNG Konvertierung

### Option A: Python-Script für ALLE GA-Bände (Empfohlen)

Erstellen Sie ein Script `convert_all_jpegs_to_png.py`:

```python
#!/usr/bin/env python3
"""
Konvertiert alle JPEG-Bilder in den GA-Ordnern zu transparenten PNG-Dateien.
"""

import os
from PIL import Image
from pathlib import Path

def convert_jpeg_to_transparent_png(jpeg_path, png_path):
    """
    Konvertiert JPEG zu PNG mit transparentem Hintergrund.
    Weiße Bereiche werden transparent gemacht.
    """
    try:
        # Öffne JPEG
        img = Image.open(jpeg_path)
        
        # Konvertiere zu RGBA (für Transparenz)
        img = img.convert("RGBA")
        
        # Lade Pixel-Daten
        datas = img.getdata()
        new_data = []
        
        # Mache weiße/helle Bereiche transparent
        # Schwellenwert: RGB > 240 wird transparent
        for item in datas:
            # Wenn Pixel fast weiß ist (R, G, B alle > 240)
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                # Mache transparent (Alpha = 0)
                new_data.append((255, 255, 255, 0))
            else:
                # Behalte Pixel wie es ist
                new_data.append(item)
        
        # Setze neue Pixel-Daten
        img.putdata(new_data)
        
        # Speichere als PNG
        img.save(png_path, "PNG")
        print(f"  ✓ {os.path.basename(png_path)}")
        return True
        
    except Exception as e:
        print(f"  X Fehler bei {os.path.basename(jpeg_path)}: {e}")
        return False


def process_ga_folder(ga_folder_path):
    """
    Verarbeitet einen einzelnen GA-Ordner.
    """
    assets_path = os.path.join(ga_folder_path, 'assets')
    
    if not os.path.exists(assets_path):
        return 0, 0
    
    converted = 0
    errors = 0
    
    # Finde alle JPEG-Dateien
    for file_name in os.listdir(assets_path):
        if file_name.lower().endswith(('.jpg', '.jpeg')):
            jpeg_path = os.path.join(assets_path, file_name)
            
            # Erstelle PNG-Dateiname
            png_name = file_name.rsplit('.', 1)[0] + '.png'
            png_path = os.path.join(assets_path, png_name)
            
            # Überspringe, wenn PNG bereits existiert
            if os.path.exists(png_path):
                continue
            
            # Konvertiere
            if convert_jpeg_to_transparent_png(jpeg_path, png_path):
                converted += 1
            else:
                errors += 1
    
    return converted, errors


if __name__ == "__main__":
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    
    print("=" * 60)
    print("JPEG zu PNG Konverter - Alle GA-Bände")
    print("=" * 60)
    print(f"Basis-Ordner: {steiner_ga_dir}\n")
    
    total_converted = 0
    total_errors = 0
    total_folders = 0
    
    # Durchlaufe alle GA-Ordner
    for folder_name in sorted(os.listdir(steiner_ga_dir)):
        folder_path = os.path.join(steiner_ga_dir, folder_name)
        
        # Überspringe Dateien
        if not os.path.isdir(folder_path):
            continue
        
        # Überspringe Ordner, die nicht mit GA anfangen
        if not folder_name.startswith('GA'):
            continue
        
        print(f"\n{folder_name}:")
        converted, errors = process_ga_folder(folder_path)
        
        if converted > 0 or errors > 0:
            total_folders += 1
            total_converted += converted
            total_errors += errors
            print(f"  → {converted} konvertiert, {errors} Fehler")
    
    print(f"\n{'='*60}")
    print(f"✓ Fertig!")
    print(f"  Ordner verarbeitet: {total_folders}")
    print(f"  Bilder konvertiert: {total_converted}")
    print(f"  Fehler: {total_errors}")
    print(f"{'='*60}")
```

**Ausführen:**
```powershell
cd C:\Users\chuec\OneDrive\GitHub\ga_suche
python convert_all_jpegs_to_png.py
```

**Hinweis**: Dieser Ansatz macht **alle weißen Bereiche transparent**. Je nach Ihren Zeichnungen müssen Sie eventuell den Schwellenwert anpassen (Zeile mit `if item[0] > 240`).

---

### Option B: Einzelner GA-Band (für Tests)

Falls Sie zuerst nur einen GA-Band testen möchten:

```python
# Im Script oben, ersetzen Sie die Hauptschleife durch:
folder_name = "GA090a-Selbsterkenntnis und Gotteserkenntnis I"
folder_path = os.path.join(steiner_ga_dir, folder_name)
converted, errors = process_ga_folder(folder_path)
print(f"{folder_name}: {converted} konvertiert, {errors} Fehler")
```

---

## Schritt 2: Export in steiner-images.json

Nach der Konvertierung:

```powershell
cd C:\Users\chuec\OneDrive\GitHub\ga_suche
python export_images_from_lectures.py
```

**Das Script:**
- Durchsucht alle `steiner-full-lectures-*.json` Dateien
- Findet alle Bildreferenzen (`.jpeg` im Text)
- Sucht die entsprechenden PNG-Dateien in `Steiner_GA/GAxxx-.../assets/`
- Encodiert die PNG-Dateien als Base64
- Speichert in `steiner-images.json` mit Original-Referenz (`.jpeg`)

**Ergebnis:**
```
============================================================
OK Fertig!
  Bildreferenzen gefunden: 632
  Erfolgreich encodiert: XXX  ← Anzahl gefundener PNGs
  Nicht gefunden: YYY        ← Noch nicht konvertiert
  Vorträge mit Bildern: ZZZ
============================================================
```

---

## Schritt 3: Server neu starten

```powershell
# Stoppe laufenden Server (falls aktiv)
# Drücken Sie Strg+C im Server-Terminal

# Starte Server neu
cd C:\Users\chuec\OneDrive\GitHub\ga_suche
node backend.js
```

**Warten Sie auf:**
```
Lade steiner-images.json...
✓ steiner-images.json geladen: X Vorträge, Y Bilder
```

---

## Schritt 4: Browser neu laden

```
http://localhost:3000
```

Drücken Sie **F5** oder **Strg+F5** (Hard Refresh)

---

## Empfohlene Reihenfolge

### Phase 1: Test mit einem GA-Band
1. Wählen Sie einen kleineren GA-Band (z.B. GA090a)
2. Konvertieren Sie nur diesen einen
3. Exportieren Sie mit `export_images_from_lectures.py`
4. Testen Sie im Browser

### Phase 2: Alle verbleibenden GA-Bände
1. Führen Sie `convert_all_jpegs_to_png.py` aus (kann einige Minuten dauern!)
2. Exportieren Sie mit `export_images_from_lectures.py`
3. Server neu starten
4. Browser neu laden

---

## Troubleshooting

### PNG-Dateien werden nicht gefunden
- Prüfen Sie, ob die PNG-Dateien wirklich erstellt wurden:
  ```powershell
  Get-ChildItem "C:\Users\chuec\OneDrive\GitHub\Steiner_GA\GA090a*\assets\*.png" -Recurse
  ```

### Bilder werden nicht angezeigt
1. Prüfen Sie Browser-Konsole (F12) auf Fehler
2. Prüfen Sie, ob Server `steiner-images.json` geladen hat
3. Prüfen Sie, ob Lecture-ID in JSON vorhanden ist

### Transparenz funktioniert nicht richtig
- Passen Sie Schwellenwert im Konvertierungs-Script an:
  - Höher (z.B. 250): Mehr wird transparent
  - Niedriger (z.B. 230): Weniger wird transparent

---

## Aktueller Status

✅ **Bereits konvertiert:**
- GA089-Bewusstsein Leben Form: 40 Bilder

❌ **Noch zu konvertieren:** (~592 Bilder)
- GA090a, GA090b, GA091, GA093, GA094, GA095, GA096, GA097, GA098, GA100, GA101, GA102, GA103, GA104, GA104a, GA105, GA108, GA110, GA111, GA210, GA211, GA212, GA213, GA214, GA215, GA216, GA218, GA219, GA220, GA221, GA222, GA223, GA293, GA294, GA295, GA296, GA299, GA300a, GA300b, GA300c, GA301, GA302, GA303, GA304, GA304a, GA305, GA306, GA307, GA309, GA310, GA311

---

## Geschätzte Zeiten

- **Konvertierung** (alle ~592 Bilder): ~5-10 Minuten
- **Export** (alle Bilder): ~2-5 Minuten
- **Server-Neustart**: ~5 Sekunden

**Gesamtzeit**: ~10-20 Minuten für komplette Migration

