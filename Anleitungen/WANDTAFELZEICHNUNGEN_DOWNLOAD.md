# Wandtafelzeichnungen von rsarchive.org

## Erfolgreich heruntergeladen (November 2025)

**Total: 151 Wandtafelzeichnungen von 12 GA-Bänden**

### GA-Bände mit Tafelzeichnungen auf rsarchive.org:

| GA-Band | Anzahl | Dateien | Größe |
|---------|--------|---------|-------|
| GA210 | 15 | 210-T01 bis T15 | 1.71 MB |
| GA211 | 11 | 211-T01 bis T11 | ~1.10 MB |
| GA212 | 14 | 212-T01 bis T14 | 1.95 MB |
| GA213 | 24 | 213-T01 bis T24 | 4.68 MB |
| GA214 | 10 | 214-T01 bis T10 | 2.01 MB |
| GA216 | 10 | 216-T01 bis T10 | 1.77 MB |
| GA218 | 5 | 218-T01 bis T05 | 0.89 MB |
| GA219 | 13 | 219-T01 bis T13 | 2.01 MB |
| GA220 | 13 | 220-T01 bis T13 | 2.10 MB |
| GA222 | 10 | 222-T01 bis T10 | 2.03 MB |
| GA223 | 9 | 223-T01 bis T09 | 1.91 MB |
| GA291 | 17 | 291-T01 bis T17 | 2.97 MB |
| **TOTAL** | **151** | | **~26 MB** |

---

## URL-Struktur auf rsarchive.org

```
https://rsarchive.org/Lectures/GA{NUM}/German/images/{NUM}-T{01-99}.webp

Beispiele:
- https://rsarchive.org/Lectures/GA211/German/images/211-T01.webp
- https://rsarchive.org/Lectures/GA213/German/images/213-T01.webp
- https://rsarchive.org/Lectures/GA291/German/images/291-T01.webp
```

---

## Download-Skript

### Verwendung:

**Einzelner GA-Band:**
```bash
python download_chalkboards_simple.py GA211
```

**Mehrere GA-Bände:**
```bash
python download_chalkboards_simple.py GA210 GA211 GA212
```

**Mit spezifischem Bereich:**
```bash
python download_chalkboards_simple.py GA211 --range 1-15
```

### Installation:
```bash
pip install requests
```

---

## Integration in Steiner GA-Suche

### Automatischer Workflow:

1. **Download von rsarchive.org:**
   ```bash
   python download_chalkboards_simple.py GA211
   ```

2. **Kopieren nach Steiner_GA:**
   ```powershell
   Copy-Item "downloads\chalkboards\GA211\*.webp" `
     "C:\Users\chuec\OneDrive\GitHub\Steiner_GA\GA211-...\assets\"
   ```

3. **In Obsidian referenzieren:**
   ```markdown
   ![211-T01](assets/211-T01.webp)
   ```

4. **Exportieren:**
   ```bash
   python export_master.py GA211
   ```

Die WebP-Dateien werden automatisch Base64-encodiert und in `steiner-images.json` eingefügt.

---

## Verfügbarkeit auf rsarchive.org

### ✅ Verfügbar (12 Bände):
GA210, GA211, GA212, GA213, GA214, GA216, GA218, GA219, GA220, GA222, GA223, GA291

### ❌ Nicht verfügbar / Noch nicht digitalisiert:
- GA089-GA098 (frühe Vorträge)
- GA100-GA119 (Evangelien-Vorträge)
- GA221 (Erdenwissen und Himmelserkenntnis)
- GA292-GA311 (außer GA291) (pädagogische Vorträge)

---

## Hinweise

### WebP vs. PNG/JPEG:
- rsarchive.org verwendet WebP-Format (modern, effizient)
- Ihre bestehenden Bilder sind PNG/JPEG
- WebP wird direkt unterstützt (keine Konvertierung nötig)
- Export-Skript erkennt `.webp` Endung automatisch

### Copyright & Nutzung:
- Quelle: https://rsarchive.org
- "Steiner Online Library, a public charity"
- Verwendung gemäß deren Nutzungsbedingungen
- Quellenangabe empfohlen

### Qualität:
- rsarchive.org Tafelzeichnungen sind farbig
- Hohe Auflösung (typisch 600-1000px Breite)
- Deutlich besser als schwarz-weiß Scans

---

## Zukünftige Updates

Falls rsarchive.org weitere GA-Bände digitalisiert:

```bash
# Teste einen GA-Band
python download_chalkboards_simple.py GA221 --range 1-20

# Batch-Update mehrerer Bände
python download_chalkboards_simple.py GA100 GA101 GA102
```

---

**Erstellt:** November 2025  
**Quelle:** https://rsarchive.org  
**Format:** WebP (XXX-T01.webp bis XXX-Tnn.webp)  
**Total Downloads:** 151 Tafelzeichnungen, 12 GA-Bände

