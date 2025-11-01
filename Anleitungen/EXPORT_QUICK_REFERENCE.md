# Export Quick Reference

## Schnellübersicht

```bash
# Ein Befehl für alles:
python export_master.py [GA-BÄNDE] [OPTIONEN]
```

---

## Häufigste Kommandos

### 🔄 Einzelnen GA-Band aktualisieren
```bash
python export_master.py GA089 --skip-path-fix --skip-conversion
```
⏱️ ~3 Sekunden | Verwendung: Nach Textänderungen

---

### 🆕 Neuen GA-Band exportieren
```bash
python export_master.py GA112-GA117a --restart-server
```
⏱️ ~20 Sekunden | Verwendung: Erste Einrichtung neuer Bände

---

### 🖼️ Neue Bilder hinzugefügt
```bash
python export_master.py GA115
```
⏱️ ~15 Sekunden | Verwendung: Nach Hinzufügen neuer JPEGs

---

### 🔄 Kompletter Export (alle GA-Bände)
```bash
python export_master.py --restart-server
```
⏱️ ~2-5 Minuten | Verwendung: Nach vielen Änderungen

---

## Optionen

| Option | Was macht es? | Wann verwenden? |
|--------|--------------|-----------------|
| `--skip-path-fix` | Überspringt Bildpfad-Korrektur | Wenn Pfade bereits korrekt |
| `--skip-conversion` | Überspringt JPEG→PNG | Wenn keine neuen Bilder |
| `--restart-server` | Startet Server automatisch | Für sofortige Verfügbarkeit |

---

## Was passiert?

### Schritt 1: Bildpfad-Korrektur ✏️
- Korrigiert `.jpeg` → `.png` in Markdown
- Entfernt doppelte Ordnernamen
- Erstellt Backups (`.backup`)

### Schritt 2: JPEG → PNG 🖼️
- Konvertiert JPEGs zu transparenten PNGs
- Überspringt bereits existierende
- Weiße Bereiche werden transparent

### Schritt 3: Lectures exportieren 📚
- Liest Markdown aus Obsidian
- Extrahiert Metadaten & Absätze
- Speichert in `steiner-full-lectures*.json`

### Schritt 4: Bilder exportieren 🎨
- Findet Bildreferenzen in Lectures
- Encodiert Bilder als Base64
- Speichert in `steiner-images.json`

### Schritt 5: Server neu starten 🚀
- Stoppt alten Server
- Startet neuen Server
- Lädt aktualisierte Daten

---

## Typischer Workflow

```
1. In Obsidian arbeiten
   └─ Vorträge bearbeiten, Bilder einfügen

2. Export ausführen
   └─ python export_master.py GA089 --restart-server

3. Browser testen
   └─ http://localhost:3000 → F5

4. Fertig! ✅
```

---

## Troubleshooting

### Problem: Bilder werden nicht angezeigt
```bash
# Lösung 1: Server neu starten
python export_master.py --skip-path-fix --skip-conversion --restart-server

# Lösung 2: Browser-Cache leeren
# Strg+F5 im Browser
```

### Problem: "Pillow nicht installiert"
```bash
pip install Pillow
```

### Problem: Lectures nicht gefunden
```bash
# Vollständigen Export ausführen:
python export_master.py
```

---

## Dateien & Größen

| Datei | Größe | Inhalt |
|-------|-------|--------|
| `steiner-full-lectures*.json` (7 Teile) | ~75 MB | 1941 Vorträge |
| `steiner-images.json` | ~107 MB | 661 Bilder |
| **Gesamt** | **~182 MB** | Komplette Datenbank |

---

## Hilfe

```bash
python export_master.py --help
```

**Weitere Dokumentation:** `EXPORT_ANLEITUNG.md`

---

**Zuletzt aktualisiert:** November 2025

