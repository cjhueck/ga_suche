const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

class SteinerLecturesExporter {
  constructor(sourceDir, outputDir) {
    this.sourceDir = sourceDir;
    this.outputDir = outputDir;
  }

  // Parse GA input (z.B. "GA051, GA058" oder "GA051-GA060")
  parseGAInput(input) {
    const result = new Set();
    (input || "")
      .split(",")
      .map(s => s.trim().toUpperCase())
      .forEach(token => {
        const rangeMatch = token.match(/^GA(\d{2,3})\s*[-—]\s*GA(\d{2,3})$/i);
        if (rangeMatch) {
          let start = parseInt(rangeMatch[1], 10);
          let end = parseInt(rangeMatch[2], 10);
          if (start > end) [start, end] = [end, start];
          for (let i = start; i <= end; i++) {
            result.add(`GA${String(i).padStart(3, '0')}`);
          }
        } else {
          const singleMatch = token.match(/^GA(\d{1,3}[A-Z]?)$/i);
          if (singleMatch) {
            const inner = singleMatch[1];
            const numMatch = inner.match(/^(\d{1,3})([A-Z]?)$/i);
            if (numMatch) {
              const padded = numMatch[1].padStart(3, '0') + numMatch[2].toLowerCase();
              result.add(`GA${padded}`);
            }
          }
        }
      });
    return [...result];
  }

  // Extract metadata from filename
  extractMetadataFromFilename(filename) {
    const match = filename.match(/^GA\s*(\d{2,3}[a-z]?)\s*\((\d+)\.\)\s+(.+)\.md$/i);
    if (!match) return null;
    const [, ga, lectureNumber, rest] = match;

    const parts = rest.split(',').map(p => p.trim());
    let titlePart = parts[0] || "";
    let location = null;
    let date = null;
    
    // VERBESSERTE LOGIK: Suche Datum in ALLEN Teilen
    // Datum-Pattern: "24. Juni 1904" mit optionalen Zusätzen wie "(abends)" oder "Ausarbeitung vom"
    const months = {
      "januar": "01", "februar": "02", "märz": "03", "maerz": "03", "marz": "03", "april": "04",
      "mai": "05", "juni": "06", "juli": "07", "august": "08", "september": "09",
      "oktober": "10", "november": "11", "dezember": "12"
    };
    
    let datePartIndex = -1;
    
    // Durchsuche alle parts nach Datumsmuster
    for (let i = 1; i < parts.length; i++) {
      const part = parts[i];
      
      // Suche Datum im Teil (kann irgendwo im String stehen)
      // Pattern: "24. Juni 1904" optional mit Text davor/danach
      const dateMatch = part.match(/(\d{1,2})\.\s*([a-zäöüß]+)\s*(\d{4})/i);
      
      if (dateMatch) {
        const day = dateMatch[1].padStart(2, "0");
        let monthName = dateMatch[2].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const month = months[monthName];
        const year = dateMatch[3];
        
        if (month) {
          date = `${year}-${month}-${day}`;
          datePartIndex = i;
          break;
        }
      }
    }
    
    // Ort ist normalerweise der Teil VOR dem Datum
    if (datePartIndex > 1) {
      location = parts[datePartIndex - 1];
    } else if (parts.length >= 2 && datePartIndex !== 1) {
      // Fallback: 2. Teil wenn kein Datum gefunden wurde
      location = parts[1];
    }

    return {
      gaNumber: `GA${ga.toLowerCase()}`,
      lectureNumber: lectureNumber,
      ID: `GA${ga.toLowerCase()}/${lectureNumber}`,
      title: titlePart,
      location: location,
      date: date,
      fullRest: rest
    };
  }

  // Parse German date format (vereinfacht, wird jetzt in extractMetadataFromFilename direkt gemacht)
  parseDate(dateStr) {
    const months = {
      "januar": "01", "februar": "02", "märz": "03", "maerz": "03", "marz": "03", "april": "04",
      "mai": "05", "juni": "06", "juli": "07", "august": "08", "september": "09",
      "oktober": "10", "november": "11", "dezember": "12"
    };
    
    // Suche Datum im String (kann überall stehen)
    const m = dateStr?.match(/(\d{1,2})\.\s*([a-zäöüß]+)\s*(\d{4})/i);
    if (!m) return null;
    
    const day = m[1].padStart(2, "0");
    let monthName = m[2].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const month = months[monthName] || null;
    const year = m[3];
    
    if (month) return `${year}-${month}-${day}`;
    return null;
  }

  // Clean line for paragraph extraction
  cleanLine(line) {
    let l = line.trim();
    
    // Filter TOC entries (format: - [[#Heading]] - _Description_)
    if (/^-?\s*\[\[#.+?\]\]\s*-\s*_.*_/i.test(l)) return null;
    
    // Filter lines with multiple wiki links (Schlagwörter-Zeilen)
    if (/(\[\[.+?\]\])(\s*-\s*\[\[.+?\]\])+/i.test(l)) return null;
    
    // Filter "Inhaltsverzeichnis" headings
    if (/inhalts?verzeichnis/i.test(l)) return null;
    
    // Filter nur H1 (Dokumenttitel) - behalte H2, H3, H4 für Zwischenüberschriften
    if (/^\s*#\s+[^#]/.test(l)) return null;
    
    // Filter lines that are only italic/bold (oft Zusammenfassungen)
    if (/^[_*].+[_*]$/.test(l)) return null;
    
    // Filter "Quelle:" Zeilen
    if (/^Quelle:/i.test(l)) return null;
    
    // Filter Wiki-Link-Zeilen am Anfang (Schlagwörter)
    if (/^\[\[.+?\]\]/.test(l)) return null;
    
    // Filter Trennlinien
    if (/^[-=*]{3,}$/.test(l)) return null;
    
    // BEHALTE Bildmarkierungen (werden später verarbeitet)
    // ![img-name](path) wird nicht gefiltert
    
    return l;
  }

  // Konvertiere Wiki-Links zu Markdown-Format
  convertWikiLinksToMarkdown(text) {
    // Pattern: ![[dateiname.ext]] → ![](assets/dateiname.ext)
    return text.replace(/!\[\[([^\]]+)\]\]/g, (match, filename) => {
      // Extrahiere nur Dateinamen
      let cleanName = filename.split('/').pop();
      
      // Falls "assets/" im Namen: Extrahiere danach
      if (cleanName.includes('assets/')) {
        cleanName = cleanName.split('assets/').pop();
      }
      
      // Für img-N: Vereinfache
      // GA121_img-4.jpeg → img-4.jpeg
      const imgMatch = cleanName.match(/img-(\d+)\.(jpe?g|png|webp)/i);
      if (imgMatch) {
        cleanName = `img-${imgMatch[1]}.${imgMatch[2]}`;
      }
      
      // WICHTIG: URLs mit Leerzeichen in <> einschließen für Markdown
      return `![](<assets/${cleanName}>)`;
    });
  }
  
  // Prüft ob ein Text eine Listenzeile ist (nummeriert oder mit Aufzählungszeichen)
  isListItem(text) {
    if (!text) return false;
    // Nummerierte Liste: "1.", "2.", etc. am Anfang
    // Oder Aufzählungszeichen: "-", "*", "•" am Anfang
    return /^\d+\.\s/.test(text) || /^[-*•]\s/.test(text);
  }
  
  // Merged aufeinanderfolgende Listenabsätze mit dem vorhergehenden Absatz
  mergeListParagraphs(paragraphs) {
    if (!paragraphs || paragraphs.length === 0) return paragraphs;
    
    const merged = [];
    let i = 0;
    
    while (i < paragraphs.length) {
      const current = paragraphs[i];
      
      // Prüfe ob die NÄCHSTEN Absätze Listenelemente sind
      if (i + 1 < paragraphs.length && this.isListItem(paragraphs[i + 1].content)) {
        // Sammle alle aufeinanderfolgenden Listenelemente
        const listItems = [];
        let j = i + 1;
        
        while (j < paragraphs.length && this.isListItem(paragraphs[j].content)) {
          listItems.push(paragraphs[j]);
          j++;
        }
        
        if (listItems.length > 0) {
          // Kombiniere den aktuellen Absatz mit den Listenelementen
          // Füge die Listenelemente als Markdown-Liste zum Content hinzu
          let combinedContent = current.content;
          
          // Füge eine Leerzeile vor der Liste ein (wichtig für Markdown-Parsing)
          combinedContent += '\n\n';
          
          // Füge alle Listenelemente hinzu
          listItems.forEach(item => {
            combinedContent += item.content + '\n';
          });
          
          merged.push({
            index: current.index,
            content: combinedContent.trim()
          });
          
          i = j; // Überspringe die gemergten Listenelemente
          continue;
        }
      }
      
      // Wenn der aktuelle Absatz selbst eine Listenzeile ist (ohne vorhergehenden Einleitungsabsatz)
      // und weitere Listenzeilen folgen, fasse sie zusammen
      if (this.isListItem(current.content)) {
        const listItems = [current];
        let j = i + 1;
        
        while (j < paragraphs.length && this.isListItem(paragraphs[j].content)) {
          listItems.push(paragraphs[j]);
          j++;
        }
        
        if (listItems.length > 1) {
          // Kombiniere alle Listenelemente
          let combinedContent = listItems.map(item => item.content).join('\n');
          
          merged.push({
            index: current.index,
            content: combinedContent
          });
          
          i = j;
          continue;
        }
      }
      
      // Normaler Absatz ohne nachfolgende Liste
      merged.push(current);
      i++;
    }
    
    return merged;
  }
  
  // Formatiert Paragraph-Content:
  // 1. Gedichte: Reduziert doppelte Leerzeilen zwischen Zeilen auf einfache
  // 2. Durchgezogene Linien: Konvertiert * * * zu * * *
  formatParagraphContent(content) {
    if (!content) return content;
    
    // 1. Durchgezogene Linien: Konvertiere * * * zu * * * (beide sind identisch, aber sicherstellen)
    // Pattern: * * * oder * * * mit variablen Leerzeichen
    content = content.replace(/\*\s+\*\s+\*/g, '* * *');
    
    // 2. Gedichte: Reduziere doppelte Leerzeilen zwischen Zeilen auf einfache
    // Erkenne Gedichte: Mehrere kurze Zeilen (< 90 Zeichen) hintereinander
    const lines = content.split('\n');
    const resultLines = [];
    
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      const lineLength = line.trim().length;
      
      // Prüfe ob aktuelle Zeile kurz ist (potentielles Gedicht)
      if (lineLength > 0 && lineLength < 90) {
        // Prüfe ob nächste Zeile auch kurz ist (Gedicht erkannt)
        if (i + 1 < lines.length) {
          const nextLine = lines[i + 1];
          const nextLineLength = nextLine.trim().length;
          
          // Wenn nächste Zeile leer ist, prüfe die übernächste
          if (nextLineLength === 0 && i + 2 < lines.length) {
            const nextNextLine = lines[i + 2];
            const nextNextLength = nextNextLine.trim().length;
            
            // Wenn übernächste Zeile auch kurz ist, überspringe die leere Zeile
            if (nextNextLength > 0 && nextNextLength < 90) {
              resultLines.push(line);
              i += 1; // Überspringe leere Zeile
              continue;
            }
          }
          
          // Wenn nächste Zeile auch kurz ist, füge keine Leerzeile ein
          if (nextLineLength > 0 && nextLineLength < 90) {
            resultLines.push(line);
            i += 1;
            continue;
          }
        }
      }
      
      // Normale Zeile: Füge hinzu
      resultLines.push(line);
      i += 1;
    }
    
    return resultLines.join('\n');
  }
  
  // Extract image references from text
  // Hilfsfunktion: Bereinigt Bildpfade automatisch
  cleanImagePath(imagePath) {
    let cleaned = imagePath;
    
    // 0. Entferne < und > aus URLs (Markdown-Format für URLs mit Leerzeichen)
    cleaned = cleaned.replace(/^<(.+)>$/, '$1');
    
    // 0.5. Entferne Anführungszeichen am Anfang und Ende
    cleaned = cleaned.replace(/^['"](.+)['"]$/, '$1');
    
    // 1. Entferne URL-Encoding (%20 -> Leerzeichen, etc.)
    try {
      cleaned = decodeURIComponent(cleaned);
    } catch (e) {
      // Falls Decodierung fehlschlägt, verwende Original
    }
    
    // 2. Entferne GA-Ordnernamen aus dem Pfad
    // Pattern: GA###-Langer Ordnername/assets/file -> assets/file
    cleaned = cleaned.replace(/^GA\d+[a-z]?[- ][^/]+\//, '');
    
    // 3. Entferne GA###-Name_img-X.jpeg -> assets/img-X.jpeg
    cleaned = cleaned.replace(/^GA\d+[a-z]?[- ][^_]+_/, 'assets/');
    
    // 4. Entferne doppeltes "assets/" am Anfang
    cleaned = cleaned.replace(/^assets\/['"]?assets\//, 'assets/');
    
    // 5. Wenn kein assets/ am Anfang, füge es hinzu (für Dateien wie "img-0.jpeg")
    if (!cleaned.startsWith('assets/') && !cleaned.startsWith('../')) {
      cleaned = `assets/${cleaned}`;
    }
    
    // 6. NEU: Vereinfache komplexe Bildnamen zu img-X.ext
    // Pattern: assets/GA###-Langer Name_img-X.ext -> assets/img-X.ext
    // Auch: assets/GA###-Langer Name mit Umlauten_img-X.ext -> assets/img-X.ext
    const complexImgMatch = cleaned.match(/^assets\/.*[_-](img-\d+)\.(webp|png|jpe?g|gif)$/i);
    if (complexImgMatch) {
      cleaned = `assets/${complexImgMatch[1]}.${complexImgMatch[2]}`;
    }
    
    return cleaned;
  }
  
  extractImageReferences(text) {
    const images = [];
    
    // Pattern 1: Standard Markdown ![alt](path)
    const markdownRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
    let match;
    
    while ((match = markdownRegex.exec(text)) !== null) {
      const altText = match[1] || '';
      const imagePath = match[2] || '';
      
      // Automatische Bildpfad-Bereinigung
      const cleanedPath = this.cleanImagePath(imagePath);
      
      images.push({
        altText,
        path: cleanedPath,
        fullMatch: match[0]
      });
    }
    
    // Pattern 2: Obsidian Wiki-Links ![[filename]]
    const wikiRegex = /!\[\[([^\]]+)\]\]/g;
    
    while ((match = wikiRegex.exec(text)) !== null) {
      const filename = match[1] || '';
      
      // Konvertiere zu assets/filename Format
      const imagePath = filename.startsWith('assets/') ? filename : `assets/${filename}`;
      
      images.push({
        altText: filename.replace(/\.(webp|png|jpe?g)$/i, ''), // Dateiname ohne Endung
        path: imagePath,
        fullMatch: match[0]
      });
    }
    
    return images;
  }

  // Find GA title from master file
  findGATitle(gaNumber, allFiles) {
    const normalizedGA = gaNumber.toUpperCase();
    
    for (const file of allFiles) {
      // Skip files in Schlagwörter folder
      if (file.includes('Schlagwörter')) continue;
      
      const basename = path.basename(file, '.md');
      // Match only master files (NOT those with lecture number like "(1.)")
      const match = basename.match(/^(GA\d{2,3}[a-z]?)\s+-\s+(.+)$/i);
      if (match && !/\(\d+\.\)/.test(basename)) {
        const fileGA = match[1].toUpperCase();
        if (fileGA === normalizedGA) {
          return match[2].trim();
        }
      }
    }
    return null;
  }

  // Recursively find all markdown files
  findMarkdownFiles(dir, fileList = []) {
    const files = fs.readdirSync(dir);
    
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        this.findMarkdownFiles(filePath, fileList);
      } else if (file.endsWith('.md')) {
        fileList.push(filePath);
      }
    });
    
    return fileList;
  }

  // Calculate JSON size
  calculateSize(obj) {
    return Buffer.byteLength(JSON.stringify(obj), 'utf8');
  }

  // Split lectures into chunks
  splitLecturesIntoChunks(lectures, maxSizeBytes) {
    const chunks = [];
    let currentChunk = [];
    let currentSize = this.calculateSize({ lectures: [] });

    for (const lecture of lectures) {
      const lectureSize = this.calculateSize(lecture);
      const testSize = this.calculateSize({ lectures: [...currentChunk, lecture] });

      if (testSize > maxSizeBytes && currentChunk.length > 0) {
        chunks.push([...currentChunk]);
        currentChunk = [lecture];
        currentSize = this.calculateSize({ lectures: [lecture] });
      } else {
        currentChunk.push(lecture);
        currentSize = testSize;
      }
    }

    if (currentChunk.length > 0) {
      chunks.push(currentChunk);
    }

    return chunks;
  }

  // Entfernt GA-Bände aus bestehenden steiner-full-lectures-*.json Dateien
  // um Duplikate beim partiellen Export zu vermeiden
  removeGAsFromExistingFiles(gasToRemove) {
    if (!gasToRemove || gasToRemove.length === 0) return;

    const gasUpper = gasToRemove.map(g => g.toUpperCase());
    
    // Prüfe sowohl Hauptordner als auch steiner-full-lectures Unterordner
    const directoriesToCheck = [
      this.outputDir,
      path.join(this.outputDir, 'steiner-full-lectures')
    ];

    let totalRemoved = 0;

    for (const dir of directoriesToCheck) {
      if (!fs.existsSync(dir)) continue;
      
      // Finde alle bestehenden steiner-full-lectures-*.json Dateien
      const existingFiles = fs.readdirSync(dir)
        .filter(f => f.startsWith('steiner-full-lectures-') && f.endsWith('.json'));

      for (const fileName of existingFiles) {
        const filePath = path.join(dir, fileName);
        
        try {
          const content = fs.readFileSync(filePath, 'utf8');
          const data = JSON.parse(content);
          
          if (!data.lectures || !Array.isArray(data.lectures)) continue;
          
          const originalCount = data.lectures.length;
          
          // Filtere Vorträge der zu exportierenden GA-Bände heraus
          data.lectures = data.lectures.filter(l => {
            const gaNum = (l.gaNumber || '').toUpperCase();
            return !gasUpper.includes(gaNum);
          });
          
          const removedCount = originalCount - data.lectures.length;
          
          if (removedCount > 0) {
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
            const relativePath = path.relative(this.outputDir, filePath);
            console.log(`   🧹 ${relativePath}: ${removedCount} alte Einträge entfernt`);
            totalRemoved += removedCount;
          }
        } catch (e) {
          // Ignoriere Fehler beim Lesen/Schreiben
        }
      }
    }

    if (totalRemoved > 0) {
      console.log(`   ✓ Gesamt: ${totalRemoved} alte Einträge aus bestehenden Dateien entfernt\n`);
    }
  }

  // Main export function
  async export(selectedGAs = [], options = {}) {
    const { syncMetadata = true } = options;
    
    const allFiles = this.findMarkdownFiles(this.sourceDir);
    const lectures = [];
    const allImages = {}; // Sammelt alle Bildverweise: { lectureId: [ {index, altText, path, ...} ] }


    let processed = 0;
    for (const filePath of allFiles) {
      const filename = path.basename(filePath);
      
      // Check if it's a lecture file
      const gaMatch = filename.match(/^GA\s*\d{2,3}[a-z]?\s*\(\d+\.\)/);
      if (!gaMatch) continue;

      const gaNumber = filename.match(/^GA\s*(\d{2,3}[a-z]?)/i)?.[1]?.toUpperCase();
      
      // GA001-GA050 sind Bücher, nicht Vorträge - ausschließen
      // Ausnahmen: GA029-GA037, GA041b und GA046 sind Aufsatzbände (werden wie Vorträge exportiert)
      // Zusätzliche Ausnahmen: GA019, GA024, GA026, GA042, GA043, GA044 (auch als Aufsätze behandelbar)
      // BRIEFE: GA262, GA263a werden wie Vorträge exportiert (mit H2-Überschriften als Navigation)
      if (gaNumber) {
        const gaNum = parseInt(gaNumber.match(/^\d+/)?.[0] || '999');
        const gaLower = gaNumber.toLowerCase();
        const isGA041b = gaLower === '041b' || gaLower === '41b';
        // Standard Aufsatzbände + zusätzliche GAs die auch als Aufsätze exportiert werden können
        const additionalEssayBands = [14, 19, 24, 26, 42, 43, 44];
        const isEssayBand = (gaNum >= 29 && gaNum <= 37) || gaNum === 46 || isGA041b || additionalEssayBands.includes(gaNum);
        // BRIEFE: GA262 und GA263a werden wie Vorträge exportiert (NICHT als Bücher!)
        const isGA263a = gaLower === '263a' || gaLower === 'ga263a';
        const isLetterBand = gaNum === 262 || isGA263a;
        // Wenn selectedGAs angegeben sind UND diese GA dabei ist, dann exportieren (override)
        const isExplicitlySelected = selectedGAs.length > 0 && selectedGAs.map(g => g.toUpperCase()).includes(`GA${gaNumber.toUpperCase()}`);
        if (gaNum >= 1 && gaNum <= 50 && !isEssayBand && !isLetterBand && !isExplicitlySelected) {
          continue; // Überspringe GA001-GA050 (werden als Bücher exportiert)
        }
      }
      
      // Case-insensitive Vergleich für selectedGAs
      const selectedGAsUpper = selectedGAs.map(g => g.toUpperCase());
      if (selectedGAs.length > 0 && (!gaNumber || !selectedGAsUpper.includes(`GA${gaNumber.toUpperCase()}`))) continue;

      const meta = this.extractMetadataFromFilename(filename);
      if (!meta) continue;

      // Skip lectures with "Bericht" in the title
      if (meta.title && meta.title.toLowerCase().includes('bericht')) {
        continue;
      }

      const content = fs.readFileSync(filePath, 'utf8');
      // Unterstütze sowohl Unix (\n) als auch Windows (\r\n) Zeilenenden
      const lines = content.split(/\r?\n/);

      // NUR Absätze extrahieren (KEINE Summaries, TOC)
      // H2/H3/H4 Überschriften werden beibehalten und dem nächsten Absatz vorangestellt
      // AUSNAHME: Für GA051-GA084 werden H3/H4 NICHT exportiert (werden durch AI-generierte ersetzt)
      // BRIEFE (GA262, GA263a): H2-Überschriften werden mit Absatz-Indizes versehen
      const paragraphs = [];
      const lectureImages = []; // Bilder für diesen Vortrag
      let pendingHeadings = []; // Sammle Überschriften für den nächsten Absatz
      const letterHeadings = []; // Für Briefe: H2-Überschriften mit Absatz-Indizes
      let pendingLetterHeading = null; // Aktuelle H2-Überschrift die auf Index wartet
      
      // Prüfe ob dieser GA-Band manuelle Überschriften NICHT exportieren soll
      // GA051-GA084: Haben AI-generierte Headings, manuelle werden übersprungen
      const gaNumericMatch = meta.gaNumber.match(/^GA(\d+)/i);
      const gaNumeric = gaNumericMatch ? parseInt(gaNumericMatch[1], 10) : 0;
      const skipManualHeadings = gaNumeric >= 51 && gaNumeric <= 84;
      
      // BRIEFE: GA262 und GA263a - H2-Überschriften mit Absatz-Indizes versehen
      const gaLowerForCheck = meta.gaNumber.toLowerCase();
      const isLetterBand = gaNumeric === 262 || gaLowerForCheck === 'ga263a';
      
      if (skipManualHeadings) {
        console.log(`  [${meta.ID}] Manuelle H3/H4 werden übersprungen (AI-generierte verwenden)`);
      }
      
      if (isLetterBand) {
        console.log(`  [${meta.ID}] Briefe-Band: H2-Überschriften erhalten Absatz-Indizes`);
      }
      
      for (let line of lines) {
        // Erkenne H2/H3/H4 Überschriften und sammle sie
        // ABER: Für GA051-GA084 werden H3/H4 übersprungen (AI-generierte ersetzt)
        // BRIEFE: H2-Überschriften erhalten data-index Attribute für Navigation
        const headingMatch = line.match(/^(#{2,4})\s+(.+)$/);
        if (headingMatch) {
          const level = headingMatch[1].length; // 2, 3, oder 4
          const headingText = headingMatch[2].trim();
          
          // Für GA051-GA084: H3/H4 überspringen
          if (skipManualHeadings && level >= 3) {
            continue; // H3 und H4 nicht exportieren
          }
          
          // BRIEFE: H2-Überschriften werden als H4 gespeichert und warten auf Absatz-Index
          if (isLetterBand && level === 2) {
            // Speichere die Überschrift - der Index wird beim nächsten Absatz hinzugefügt
            // WICHTIG: level 4 verwenden (H2 wird zu H4 konvertiert)
            pendingLetterHeading = {
              text: headingText,
              level: 4  // H2 → H4 für konsistente Darstellung
            };
            // Die Überschrift wird NICHT zu pendingHeadings hinzugefügt,
            // sondern separat behandelt
            continue;
          }
          
          // Konvertiere zu HTML-Tag für spätere Darstellung
          pendingHeadings.push(`<h${level}>${headingText}</h${level}>`);
          continue;
        }
        
        const cleaned = this.cleanLine(line);
        if (!cleaned) continue;

        const blockMatch = cleaned.match(/^(.*)\s\^([a-z0-9]+)$/);
        if (blockMatch) {
          const text = blockMatch[1].trim();
          const blockId = blockMatch[2];
          if (text.length > 0) {
            // Prüfe ob dieser Absatz Bildmarkierungen enthält
            const imageRefs = this.extractImageReferences(text);
            if (imageRefs.length > 0) {
              imageRefs.forEach(img => {
                lectureImages.push({
                  index: `^${blockId}`,
                  altText: img.altText,
                  path: img.path,
                  markdownRef: img.fullMatch
                });
              });
            }
            
            // Konvertiere Wiki-Links zu Markdown-Format
            let convertedText = this.convertWikiLinksToMarkdown(text);
            
            // Formatiere Paragraph-Content (Gedichte und durchgezogene Linien)
            convertedText = this.formatParagraphContent(convertedText);
            
            // Konvertiere Markdown-Bilder zu HTML-img-Tags
            // damit das Frontend konsistentes HTML erhält
            convertedText = convertedText.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, 
              (match, alt, src) => {
                // Entferne <> Klammern um Pfade mit Leerzeichen (Markdown-Standard)
                let cleanSrc = src.trim().replace(/^<|>$/g, '');
                // Vereinfache Bildpfade (entferne GA###-Name_)
                cleanSrc = this.cleanImagePath(cleanSrc);
                return `<img src="${cleanSrc}" alt="${alt.trim()}" />`;
              });
            
            // BRIEFE: Brief-Überschrift (als H4) mit data-index Attribut hinzufügen
            if (pendingLetterHeading) {
              // Speichere in letterHeadings für summary-database (als h4)
              letterHeadings.push({
                index: `^${blockId}`,
                text: pendingLetterHeading.text,
                level: 'h4'  // Immer h4 für Briefe
              });
              // Füge H4 mit data-index zum Content hinzu (H2 aus MD wird zu H4 in HTML)
              const h4WithIndex = `<h4 data-index="^${blockId}">${pendingLetterHeading.text}</h4>`;
              convertedText = h4WithIndex + '\n' + convertedText;
              pendingLetterHeading = null; // Reset
            }
            
            // Füge gesammelte Überschriften vor dem Absatz ein
            if (pendingHeadings.length > 0) {
              convertedText = pendingHeadings.join('\n') + '\n' + convertedText;
              pendingHeadings = []; // Reset
            }
            
            paragraphs.push({
              index: `^${blockId}`,
              content: convertedText
            });
          }
        }
      }

      if (paragraphs.length > 0) {
        const gaTitle = this.findGATitle(meta.gaNumber, allFiles);
        
        // Merge aufeinanderfolgende Listenabsätze mit dem vorhergehenden Absatz
        const mergedParagraphs = this.mergeListParagraphs(paragraphs);
        
        const lectureData = {
          gaNumber: meta.gaNumber,
          gaTitle: gaTitle,
          lectureNumber: meta.lectureNumber,
          ID: meta.ID,
          title: meta.title,
          fileName: `${meta.ID} - ${meta.fullRest}`,
          location: meta.location,
          date: meta.date,
          paragraphs: mergedParagraphs
        };
        
        // BRIEFE: H2-Überschriften mit Absatz-Indizes hinzufügen
        if (isLetterBand && letterHeadings.length > 0) {
          lectureData.headings = letterHeadings;
          console.log(`    -> ${letterHeadings.length} Brief-Überschriften mit Indizes`);
        }
        
        
        lectures.push(lectureData);
        
        // Speichere Bilder für diesen Vortrag
        if (lectureImages.length > 0) {
          allImages[meta.ID] = lectureImages;
        }

        processed++;
        if (processed % 50 === 0) {
        }
      }
    }

    if (lectures.length === 0) {
      return;
    }


    // Sort lectures by GA number and lecture number
    lectures.sort((a, b) => {
      if (a.gaNumber !== b.gaNumber) {
        return a.gaNumber.localeCompare(b.gaNumber);
      }
      return parseInt(a.lectureNumber) - parseInt(b.lectureNumber);
    });

    const exportedGAs = [...new Set(lectures.map(l => l.gaNumber))].sort((a, b) => {
      const numA = parseInt(a.replace(/^GA/, ''));
      const numB = parseInt(b.replace(/^GA/, ''));
      return numA - numB;
    });

    const rangeStart = exportedGAs[0].replace(/^GA/, '').padStart(3, '0');
    const rangeEnd = exportedGAs[exportedGAs.length - 1].replace(/^GA/, '').padStart(3, '0');

    // WICHTIG: Entferne alte Einträge für die exportierten GA-Bände aus bestehenden Dateien
    // um Duplikate zu vermeiden
    this.removeGAsFromExistingFiles(exportedGAs);

    // Split into chunks of max 10 MB
    const maxSize = 10 * 1024 * 1024; // 10 MB
    const chunks = this.splitLecturesIntoChunks(lectures, maxSize);


    const exportedFiles = [];

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const data = { lectures: chunk };
      const jsonStr = JSON.stringify(data, null, 2);

      let fileName;
      if (chunks.length === 1) {
        fileName = `steiner-full-lectures-${rangeStart}-${rangeEnd}.json`;
      } else {
        const partNum = String(i + 1).padStart(2, '0');
        fileName = `steiner-full-lectures-${rangeStart}-${rangeEnd}-part${partNum}.json`;
      }

      // Speichere in steiner-full-lectures Unterordner
      const lecturesDir = path.join(this.outputDir, 'steiner-full-lectures');
      if (!fs.existsSync(lecturesDir)) {
        fs.mkdirSync(lecturesDir, { recursive: true });
      }
      const filePath = path.join(lecturesDir, fileName);
      fs.writeFileSync(filePath, jsonStr, 'utf8');

      const sizeMB = (Buffer.byteLength(jsonStr, 'utf8') / (1024 * 1024)).toFixed(2);
      
      exportedFiles.push(fileName);
    }

    
    // Exportiere Bilder in separate JSON-Datei
    if (Object.keys(allImages).length > 0) {
      
      await this.exportImages(allImages);
    }
    
    // BRIEFE: Speichere Brief-Überschriften in summary-database.json
    // Damit sie im TOC im rechten Summary-Panel angezeigt werden
    this.saveLetterHeadingsToSummaryDB(lectures);
    
    // Automatische Synchronisation der Metadaten (optional)
    if (syncMetadata) {
      
      try {
        await this.syncMetadataToExistingDatabases();
      } catch (syncError) {
        console.warn('⚠️  Metadaten-Synchronisation fehlgeschlagen:', syncError.message);
        console.warn('   Sie können manuell synchronisieren mit: node sync-metadata-from-fulllectures.js');
      }
    } else {
    }
  }
  
  // Exportiere Bilder in separate JSON-Datei
  // Hilfsfunktion: Suche Bild mit flexiblen Pfad-Varianten
  findImageFile(gaDir, imagePath) {
    const assetsDir = path.join(gaDir, 'assets');
    if (!fs.existsSync(assetsDir)) {
      return null;
    }
    
    // Normalisiere den gesuchten Pfad
    const normalizedPath = imagePath.replace(/^assets[\/\\]?/i, '').trim();
    
    // Extrahiere Bildnummer (z.B. "img-0", "img-22")
    const imgMatch = normalizedPath.match(/img-(\d+)/i);
    if (!imgMatch) {
      return null;
    }
    const imgNumber = imgMatch[1];
    
    // Extrahiere Dateiendung (falls vorhanden)
    const extMatch = normalizedPath.match(/\.(png|jpg|jpeg|webp)$/i);
    const requestedExt = extMatch ? extMatch[1].toLowerCase() : null;
    
    // Suche nach verschiedenen Varianten
    const searchPatterns = [];
    
    // 1. Exakter Pfad wie angegeben
    searchPatterns.push(normalizedPath);
    
    // 2. Mit verschiedenen Dateiendungen
    if (requestedExt) {
      const altExts = requestedExt === 'png' ? ['jpg', 'jpeg'] : ['png'];
      for (const altExt of altExts) {
        searchPatterns.push(normalizedPath.replace(/\.(png|jpg|jpeg|webp)$/i, `.${altExt}`));
      }
    }
    
    // 3. Mit GA-Ordnernamen-Präfix (verschiedene Varianten)
    const gaDirName = path.basename(gaDir);
    const imgPattern = `img-${imgNumber}`;
    
    // Variante: GA266a-Band I..._img-0.png
    searchPatterns.push(`${gaDirName}_${imgPattern}.png`);
    searchPatterns.push(`${gaDirName}_${imgPattern}.jpg`);
    searchPatterns.push(`${gaDirName}_${imgPattern}.jpeg`);
    
    // Variante: Nur img-0.png (einfacher Name)
    searchPatterns.push(`${imgPattern}.png`);
    searchPatterns.push(`${imgPattern}.jpg`);
    searchPatterns.push(`${imgPattern}.jpeg`);
    
    // Durchsuche alle Dateien im assets-Ordner
    const allFiles = fs.readdirSync(assetsDir);
    
    // Suche nach passenden Dateien
    for (const pattern of searchPatterns) {
      // Exaktes Match
      const exactMatch = allFiles.find(f => f.toLowerCase() === pattern.toLowerCase());
      if (exactMatch) {
        const fullPath = path.join(assetsDir, exactMatch);
        if (fs.existsSync(fullPath)) {
          return fullPath;
        }
      }
      
      // Pattern-Match (enthält img-X)
      const patternMatch = allFiles.find(f => {
        const fLower = f.toLowerCase();
        const patternLower = pattern.toLowerCase();
        // Prüfe ob Dateiname die Bildnummer enthält
        return fLower.includes(`img-${imgNumber}`) && 
               (patternLower.includes('.png') ? fLower.endsWith('.png') : 
                patternLower.includes('.jpg') ? (fLower.endsWith('.jpg') || fLower.endsWith('.jpeg')) : true);
      });
      
      if (patternMatch) {
        const fullPath = path.join(assetsDir, patternMatch);
        if (fs.existsSync(fullPath)) {
          return fullPath;
        }
      }
    }
    
    return null;
  }

  async exportImages(allImages) {
    const imagesWithData = {};
    let processedImages = 0;
    let failedImages = 0;
    
    // Cache für GA-Verzeichnisse und PDF-Extraktion
    const gaDirCache = {};
    const pdfExtractionCache = {};
    
    for (const [lectureId, images] of Object.entries(allImages)) {
      imagesWithData[lectureId] = [];
      
      // Finde den GA-Ordner des Vortrags
      const gaNumber = lectureId.split('/')[0]; // z.B. "GA266a"
      let gaDir = gaDirCache[gaNumber];
      
      if (!gaDir) {
        gaDir = this.findGADirectory(gaNumber);
        if (gaDir) {
          gaDirCache[gaNumber] = gaDir;
        }
      }
      
      if (!gaDir) {
        console.warn(`   ⚠ ${lectureId}: GA-Verzeichnis nicht gefunden für ${gaNumber}`);
        failedImages += images.length;
        continue;
      }
      
      // Prüfe ob PDF-Extraktion für diesen GA-Ordner bereits versucht wurde
      if (!pdfExtractionCache[gaNumber]) {
        pdfExtractionCache[gaNumber] = true;
        // Versuche Bilder aus PDF zu extrahieren, falls assets-Ordner leer oder unvollständig ist
        const assetsDir = path.join(gaDir, 'assets');
        const hasAssets = fs.existsSync(assetsDir) && fs.readdirSync(assetsDir).length > 0;
        
        if (!hasAssets) {
          console.log(`   📄 ${gaNumber}: Versuche Bilder aus PDF zu extrahieren...`);
          try {
            // Rufe Python-Skript für PDF-Extraktion auf
            const { execSync } = require('child_process');
            const pythonScript = path.join(__dirname, 'extract_images_from_pdf.py');
            const gaDirPath = gaDir.replace(/\\/g, '/'); // Normalisiere Pfad für Python
            
            if (fs.existsSync(pythonScript)) {
              execSync(`python "${pythonScript}" "${gaDirPath}"`, {
                encoding: 'utf8',
                stdio: 'inherit'
              });
              console.log(`   ✅ PDF-Extraktion für ${gaNumber} abgeschlossen`);
            } else {
              console.warn(`   ⚠ ${gaNumber}: extract_images_from_pdf.py nicht gefunden`);
            }
          } catch (error) {
            console.warn(`   ⚠ ${gaNumber}: PDF-Extraktion fehlgeschlagen: ${error.message}`);
          }
        }
      }
      
      for (const img of images) {
        try {
          // Dekodiere URL-encoded Pfad
          const decodedPath = decodeURIComponent(img.path);
          
          // Versuche Bild mit flexibler Suche zu finden
          let fullImagePath = this.findImageFile(gaDir, decodedPath);
          
          // Fallback: Alte Logik für vollständige Pfade
          if (!fullImagePath) {
            // Variante 1: Pfad beginnt mit vollständigem GA-Ordnernamen
            if (decodedPath.match(/^GA\d{3}[a-z]?[-\s]/i)) {
              fullImagePath = path.join(this.sourceDir, decodedPath);
            }
            // Variante 2: Pfad enthält nur "assets/" am Anfang
            else if (decodedPath.startsWith('assets/') || decodedPath.startsWith('assets\\')) {
              fullImagePath = path.join(gaDir, decodedPath);
            } 
            // Variante 3: Pfad ist nur Dateiname mit GA-Präfix
            else if (decodedPath.match(/^GA\d{3}/i)) {
              fullImagePath = path.join(gaDir, 'assets', decodedPath);
            }
            // Variante 4: Relativer Pfad ohne GA-Präfix
            else {
              fullImagePath = path.join(gaDir, 'assets', decodedPath);
            }
            
            // Prüfe ob Datei existiert
            if (!fs.existsSync(fullImagePath)) {
              fullImagePath = null;
            }
          }
          
          if (!fullImagePath) {
            // Letzter Versuch: Versuche PDF-Extraktion für dieses spezifische Bild
            const assetsDir = path.join(gaDir, 'assets');
            const pdfFiles = fs.readdirSync(gaDir).filter(f => f.endsWith('.pdf'));
            
            if (pdfFiles.length > 0 && !pdfExtractionCache[`${gaNumber}_extracted`]) {
              console.log(`   📄 ${lectureId}: Versuche Bilder aus PDF zu extrahieren...`);
              try {
                const { execSync } = require('child_process');
                const pythonScript = path.join(__dirname, 'extract_images_from_pdf.py');
                const gaDirPath = gaDir.replace(/\\/g, '/');
                
                if (fs.existsSync(pythonScript)) {
                  execSync(`python "${pythonScript}" "${gaDirPath}"`, {
                    encoding: 'utf8',
                    stdio: 'pipe'
                  });
                  pdfExtractionCache[`${gaNumber}_extracted`] = true;
                  
                  // Versuche erneut zu finden nach PDF-Extraktion
                  fullImagePath = this.findImageFile(gaDir, decodedPath);
                }
              } catch (error) {
                // PDF-Extraktion fehlgeschlagen, ignoriere
              }
            }
            
            if (!fullImagePath) {
              console.warn(`   ⚠ ${lectureId}: Bild nicht gefunden: ${decodedPath}`);
              failedImages++;
              continue;
            }
          }
          
          // Bestimme Dateiendung und prüfe ob Konvertierung nötig ist
          const ext = path.extname(fullImagePath).toLowerCase();
          const isJpeg = ext === '.jpg' || ext === '.jpeg';
          
          let imageBuffer;
          let mimeType = 'image/webp'; // Standard: WebP nach Konvertierung (kleinere Dateien)
          let convertedPath = img.path; // Pfad für gespeichertes Bild

          try {
            if (isJpeg) {
              // Konvertiere JPEG zu WebP (kleinere Dateien als PNG)
              imageBuffer = await sharp(fullImagePath)
                .webp({ quality: 85 })
                .toBuffer();

              // Aktualisiere Pfad: .jpeg/.jpg → .webp
              convertedPath = img.path.replace(/\.jpe?g$/i, '.webp');
            } else {
              // Andere Formate (PNG, GIF, WEBP) direkt lesen
              imageBuffer = fs.readFileSync(fullImagePath);
              
              // Bestimme MIME-Type für nicht-JPEG Dateien
              const mimeTypes = {
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
              };
              mimeType = mimeTypes[ext] || 'image/webp';
            }
            
            // Konvertiere zu Base64
            const base64 = imageBuffer.toString('base64');
            
            // Aktualisiere auch Markdown-Referenz und altText wenn JPEG konvertiert wurde
            let convertedMarkdownRef = img.markdownRef;
            let convertedAltText = img.altText;
            if (isJpeg) {
              if (img.markdownRef) {
                convertedMarkdownRef = img.markdownRef.replace(/\.jpe?g/gi, '.webp');
              }
              if (img.altText) {
                convertedAltText = img.altText.replace(/\.jpe?g$/i, '.webp');
              }
            }
            
            imagesWithData[lectureId].push({
              index: img.index,
              altText: convertedAltText, // Aktualisierter Alt-Text (.webp statt .jpeg)
              path: convertedPath, // Verwende konvertierten Pfad (.webp statt .jpeg)
              markdownRef: convertedMarkdownRef, // Aktualisierte Markdown-Referenz
              base64: `data:${mimeType};base64,${base64}`,
              size: imageBuffer.length
            });
            
          } catch (conversionError) {
            console.warn(`   ⚠ ${lectureId}: Fehler bei Konvertierung von ${img.path}: ${conversionError.message}`);
            // Fallback: Versuche Original zu lesen
            try {
              imageBuffer = fs.readFileSync(fullImagePath);
              const base64 = imageBuffer.toString('base64');
              const mimeTypes = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
              };
              mimeType = mimeTypes[ext] || 'image/jpeg';
              
              imagesWithData[lectureId].push({
                index: img.index,
                altText: img.altText,
                path: img.path,
                markdownRef: img.markdownRef,
                base64: `data:${mimeType};base64,${base64}`,
                size: imageBuffer.length
              });
            } catch (fallbackError) {
              console.warn(`   ⚠ ${lectureId}: Fallback fehlgeschlagen für ${img.path}: ${fallbackError.message}`);
              failedImages++;
              continue;
            }
          }
          
          processedImages++;
          
        } catch (error) {
          console.warn(`   ⚠ ${lectureId}: Fehler bei ${img.path}: ${error.message}`);
          failedImages++;
        }
      }
    }
    
    // HINWEIS: steiner-images.json wird nicht mehr erstellt - nur part-Dateien
    // Die Bilder werden direkt in gesplitteten part-Dateien gespeichert
    
    
    // Splitte Bilder in chunks und speichere als part-Dateien
    
    // Konvertiere imagesWithData zu Array
    const imagesList = [];
    for (const lectureId in imagesWithData) {
      for (const img of imagesWithData[lectureId]) {
        imagesList.push({
          lectureId: lectureId,
          ...img
        });
      }
    }
    
    // Dynamisches Splitting
    const MAX_SIZE_MB = 9.5;
    const maxSizeBytes = MAX_SIZE_MB * 1024 * 1024;
    const chunks = [];
    let currentChunk = [];
    
    for (let idx = 0; idx < imagesList.length; idx++) {
      const img = imagesList[idx];
      currentChunk.push(img);
      
      // Prüfe alle 5 Bilder die Größe
      if (currentChunk.length % 5 === 0 || idx === imagesList.length - 1) {
        const testJson = JSON.stringify(currentChunk, null, 2);
        const sizeBytes = Buffer.byteLength(testJson, 'utf8');
        
        // Wenn zu groß und mehr als 1 Bild, splitte
        if (sizeBytes > maxSizeBytes && currentChunk.length > 1) {
          const lastImg = currentChunk.pop();
          chunks.push([...currentChunk]);
          currentChunk = [lastImg];
        }
      }
    }
    
    // Letzten Chunk hinzufügen
    if (currentChunk.length > 0) {
      chunks.push(currentChunk);
    }
    
    
    // Speichere chunks in steiner-images Unterordner
    const imagesDir = path.join(this.outputDir, 'steiner-images');
    if (!fs.existsSync(imagesDir)) {
      fs.mkdirSync(imagesDir, { recursive: true });
    }
    
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const filename = `steiner-images-part${String(i + 1).padStart(2, '0')}.json`;
      const filepath = path.join(imagesDir, filename);
      
      fs.writeFileSync(filepath, JSON.stringify(chunk, null, 2), 'utf8');
      
      const sizeBytes = fs.statSync(filepath).size;
      const sizeMB = (sizeBytes / (1024 * 1024)).toFixed(2);
      
    }
    
  }
  
  // Finde GA-Verzeichnis für einen GA-Band
  findGADirectory(gaNumber) {
    const normalizedGA = gaNumber.toUpperCase();
    
    // Durchsuche das Source-Verzeichnis nach GA-Ordnern
    const files = fs.readdirSync(this.sourceDir);
    
    for (const file of files) {
      const filePath = path.join(this.sourceDir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        // Prüfe ob der Ordnername mit dem GA-Band übereinstimmt
        const match = file.match(/^(GA\d{2,3}[a-z]?)/i);
        if (match && match[1].toUpperCase() === normalizedGA) {
          return filePath;
        }
      }
    }
    
    return null;
  }
  
  // Synchronisiere Metadaten (date, year, location) in bestehende Datenbanken
  async syncMetadataToExistingDatabases() {
    const keywordsDBPath = path.join(this.outputDir, 'keywords-database.json');
    const summaryDBPath = path.join(this.outputDir, 'summary-database.json');
    
    // Prüfe ob Datenbanken existieren
    if (!fs.existsSync(keywordsDBPath)) {
      return;
    }
    
    // Lade fullLectures die gerade exportiert wurden (aus Unterordner)
    const fullLectures = {};
    const lecturesDir = path.join(this.outputDir, 'steiner-full-lectures');
    if (!fs.existsSync(lecturesDir)) return;
    
    const files = fs.readdirSync(lecturesDir).filter(f => 
      f.startsWith('steiner-full-lectures-') && f.endsWith('.json')
    );
    
    for (const file of files) {
      try {
        const filePath = path.join(lecturesDir, file);
        const content = fs.readFileSync(filePath, 'utf8');
        const data = JSON.parse(content);
        
        if (data.lectures && Array.isArray(data.lectures)) {
          data.lectures.forEach(lecture => {
            if (lecture.ID) {
              fullLectures[lecture.ID] = lecture;
            }
          });
        }
      } catch (error) {
        console.warn(`  ⚠ ${file}: ${error.message}`);
      }
    }
    
    
    // Lade keywords-database
    const keywordsDB = JSON.parse(fs.readFileSync(keywordsDBPath, 'utf8'));
    
    let kwUpdated = 0;
    let kwNoChange = 0;
    
    // Aktualisiere keywords-database
    for (const [lectureId, lectureData] of Object.entries(keywordsDB)) {
      const fullLecture = fullLectures[lectureId];
      if (!fullLecture) continue;
      
      let updated = false;
      
      // Hole Datum aus fullLecture (mit Fallback)
      let date = fullLecture.date || fullLecture.dateString || '';
      
      if (!date && (fullLecture.location || fullLecture.fileName)) {
        date = this.extractDateFromString(fullLecture.location || fullLecture.fileName);
      }
      
      const year = date ? parseInt(date.substring(0, 4)) : null;
      const location = fullLecture.location || null;
      
      // Aktualisiere nur wenn unterschiedlich
      if (lectureData.date !== date) {
        lectureData.date = date;
        updated = true;
      }
      
      if (lectureData.year !== year) {
        lectureData.year = year;
        updated = true;
      }
      
      if (location && lectureData.location !== location) {
        lectureData.location = location;
        updated = true;
      }
      
      if (updated) {
        kwUpdated++;
      } else {
        kwNoChange++;
      }
    }
    
    
    // Speichere nur wenn Änderungen vorgenommen wurden
    if (kwUpdated > 0) {
      fs.writeFileSync(keywordsDBPath, JSON.stringify(keywordsDB, null, 2), 'utf8');
    }
    
  }
  
  // Hilfsfunktion: Extrahiere Datum aus String
  extractDateFromString(str) {
    if (!str) return null;
    
    const months = {
      'januar': '01', 'februar': '02', 'märz': '03', 'maerz': '03', 'april': '04',
      'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
      'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
    };
    
    const match = str.match(/(\d{1,2})\.\s*([a-zäöüß]+)\s*(\d{4})/i);
    if (!match) return null;
    
    const day = match[1].padStart(2, '0');
    const monthName = match[2].toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const month = months[monthName];
    const year = match[3];
    
    if (month) return `${year}-${month}-${day}`;
    return null;
  }
  
  // BRIEFE: Speichere Brief-Überschriften in summary-database.json
  // Damit sie im TOC im rechten Summary-Panel angezeigt werden
  saveLetterHeadingsToSummaryDB(lectures) {
    const summaryDBPath = path.join(this.outputDir, 'summary-database.json');
    
    // Lade existierende summary-database.json
    let summaryDB = {};
    if (fs.existsSync(summaryDBPath)) {
      try {
        summaryDB = JSON.parse(fs.readFileSync(summaryDBPath, 'utf8'));
      } catch (e) {
        console.warn('  [WARN] Konnte summary-database.json nicht laden:', e.message);
      }
    }
    
    // Filtere Lectures mit Brief-Überschriften (headings vorhanden)
    const letterLectures = lectures.filter(l => l.headings && l.headings.length > 0);
    
    if (letterLectures.length === 0) {
      return 0;
    }
    
    let updatedCount = 0;
    
    for (const lecture of letterLectures) {
      const lectureId = lecture.ID;
      
      // Erstelle oder aktualisiere Eintrag
      if (!summaryDB[lectureId]) {
        summaryDB[lectureId] = {};
      }
      
      // Speichere headings (Brief-Überschriften mit Absatz-Indizes)
      summaryDB[lectureId].headings = lecture.headings;
      
      // Erstelle tableOfContents aus headings (für Kompatibilität)
      summaryDB[lectureId].tableOfContents = lecture.headings.map(h => ({
        heading: h.text,
        description: '',
        index: h.index
      }));
      
      summaryDB[lectureId].version = 'v2-letter';
      summaryDB[lectureId].timestamp = new Date().toISOString();
      
      updatedCount++;
    }
    
    // Speichere zurück
    fs.writeFileSync(summaryDBPath, JSON.stringify(summaryDB, null, 2), 'utf8');
    console.log(`  ✓ ${updatedCount} Brief-Lectures in summary-database.json gespeichert`);
    
    return updatedCount;
  }
}

// CLI Interface
if (require.main === module) {
  const args = process.argv.slice(2);
  
  // Parse Optionen
  const noSync = args.includes('--no-sync');
  const gaArgs = args.filter(a => !a.startsWith('--'));
  
  // Default paths (relativ zum Script)
  const sourceDir = path.join(__dirname, 'Steiner_GA');
  const outputDir = __dirname;

  const exporter = new SteinerLecturesExporter(sourceDir, outputDir);

  let selectedGAs = [];
  if (gaArgs.length > 0) {
    selectedGAs = exporter.parseGAInput(gaArgs.join(','));
  } else {
  }
  
  if (noSync) {
  } else {
  }

  exporter.export(selectedGAs, { syncMetadata: !noSync })
    .then(() => {
      process.exit(0);
    })
    .catch(err => {
      console.error('❌ Error:', err);
      process.exit(1);
    });
}

module.exports = SteinerLecturesExporter;

