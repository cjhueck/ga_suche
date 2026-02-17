# GA Link Converter - Obsidian Plugin

Konvertiert GA-Quellenangaben automatisch in klickbare Links zur GA-Suche.

## Funktionen

Wandelt Zitate wie:
```
(GA 110, S. 30; 12.04.1909)
```

automatisch um in:
```
([GA 110, S. 30; 12.04.1909](http://localhost:3003/goto.html#ga=110&date=1909-04-12&page=30))
```

Unterstützt auch Seitenbereiche:
```
(GA 110, S. 105–106; 15.04.1909)
```

wird zu:
```
([GA 110, S. 105–106; 15.04.1909](http://localhost:3003/goto.html#ga=110&date=1909-04-15&page=105))
```

## Installation

### Manuell installieren (Entwicklermodus)

1. Öffnen Sie Ihren Obsidian Vault-Ordner
2. Navigieren Sie zu `.obsidian/plugins/`
3. Erstellen Sie einen neuen Ordner `ga-link-converter`
4. Kopieren Sie die Dateien `manifest.json` und `main.js` in diesen Ordner
5. Starten Sie Obsidian neu oder laden Sie die Plugins neu
6. Aktivieren Sie das Plugin unter `Einstellungen → Community Plugins`

### Verzeichnisstruktur

```
YourVault/
└── .obsidian/
    └── plugins/
        └── ga-link-converter/
            ├── manifest.json
            └── main.js
```

## Verwendung

### Ganzes Dokument konvertieren

1. Öffnen Sie die Command Palette (Strg/Cmd + P)
2. Suchen Sie nach "Konvertiere GA-Zitate zu Links"
3. Führen Sie den Befehl aus

### Nur Auswahl konvertieren

1. Markieren Sie den Text, der GA-Zitate enthält
2. Öffnen Sie die Command Palette (Strg/Cmd + P)
3. Suchen Sie nach "Konvertiere GA-Zitate in Auswahl zu Links"
4. Führen Sie den Befehl aus

## Unterstützte Formate

Das Plugin erkennt GA-Quellenangaben in diesem Format:
- `(GA [Nummer], S. [Seite]; [Tag].[Monat].[Jahr])`
- `(GA [Nummer], S. [Seite1]–[Seite2]; [Tag].[Monat].[Jahr])`

Beispiele:
- `(GA 110, S. 30; 12.04.1909)`
- `(GA 110, S. 105–106; 15.04.1909)`
- `(GA 1, S. 1; 01.01.1900)`

## Hinweise

- Das Plugin konvertiert nur noch nicht verlinkte GA-Zitate
- Bei Seitenbereichen (z.B. S. 105–106) wird nur die erste Seite im Link verwendet
- Das Plugin unterstützt sowohl Bindestrich (-) als auch Gedankenstrich (–) für Seitenbereiche

## Konfiguration

Wenn Sie eine andere URL verwenden möchten (z.B. produktiver Server statt localhost), 
bearbeiten Sie die Zeile in `main.js`:

```javascript
const url = `http://localhost:3003/goto.html#ga=${ga}&date=${formattedDate}&page=${page}`;
```

Ändern Sie `http://localhost:3003` zu Ihrer gewünschten URL, z.B.:
```javascript
const url = `https://rudolf-steiner-online.de/goto.html#ga=${ga}&date=${formattedDate}&page=${page}`;
```

## Support

Bei Problemen oder Fragen erstellen Sie bitte ein Issue im Repository.
