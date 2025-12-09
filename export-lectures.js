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
    
    // Filter heading lines (H1-H6)
    if (/^\s*#{1,6}\s+/.test(l)) return null;
    
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
      if (gaNumber) {
        const gaNum = parseInt(gaNumber.match(/^\d+/)?.[0] || '999');
        if (gaNum >= 1 && gaNum <= 50) {
          continue; // Überspringe GA001-GA050 (werden als Bücher exportiert)
        }
      }
      
      if (selectedGAs.length > 0 && (!gaNumber || !selectedGAs.includes(`GA${gaNumber.toLowerCase()}`))) continue;

      const meta = this.extractMetadataFromFilename(filename);
      if (!meta) continue;

      // Skip lectures with "Bericht" in the title
      if (meta.title && meta.title.toLowerCase().includes('bericht')) {
        continue;
      }

      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split("\n");

      // NUR Absätze extrahieren (KEINE Summaries, TOC, Überschriften)
      const paragraphs = [];
      const lectureImages = []; // Bilder für diesen Vortrag
      
      for (let line of lines) {
        // Überspringe H3/H4 Überschriften (werden NICHT exportiert)
        if (/^#{3,4}\s+/.test(line)) {
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
            
            paragraphs.push({
              index: `^${blockId}`,
              content: convertedText
            });
          }
        }
      }

      if (paragraphs.length > 0) {
        const gaTitle = this.findGATitle(meta.gaNumber, allFiles);
        
        lectures.push({
          gaNumber: meta.gaNumber,
          gaTitle: gaTitle,
          lectureNumber: meta.lectureNumber,
          ID: meta.ID,
          title: meta.title,
          fileName: `${meta.ID} - ${meta.fullRest}`,
          location: meta.location,
          date: meta.date,
          paragraphs
        });
        
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

      const filePath = path.join(this.outputDir, fileName);
      fs.writeFileSync(filePath, jsonStr, 'utf8');

      const sizeMB = (Buffer.byteLength(jsonStr, 'utf8') / (1024 * 1024)).toFixed(2);
      
      exportedFiles.push(fileName);
    }

    
    // Exportiere Bilder in separate JSON-Datei
    if (Object.keys(allImages).length > 0) {
      
      await this.exportImages(allImages);
    }
    
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
  async exportImages(allImages) {
    const imagesWithData = {};
    let processedImages = 0;
    let failedImages = 0;
    
    for (const [lectureId, images] of Object.entries(allImages)) {
      imagesWithData[lectureId] = [];
      
      for (const img of images) {
        try {
          // Dekodiere URL-encoded Pfad
          const decodedPath = decodeURIComponent(img.path);
          
          // Der Pfad kann verschiedene Formate haben:
          // 1. "assets/GA089-Bewusstsein Leben Form_img-24.jpeg"
          // 2. "GA110-Geistige Hierarchien und ihre Widerspiegelung in der physischen Welt_img-0.jpeg"
          
          // Finde den GA-Ordner des Vortrags
          const gaNumber = lectureId.split('/')[0]; // z.B. "GA089"
          const gaDir = this.findGADirectory(gaNumber);
          
          if (!gaDir) {
            console.warn(`   ⚠ ${lectureId}: GA-Verzeichnis nicht gefunden für ${gaNumber}`);
            failedImages++;
            continue;
          }
          
          // Versuche verschiedene Pfad-Varianten
          let fullImagePath = null;
          
          // Variante 1: Pfad beginnt mit vollständigem GA-Ordnernamen (z.B. "GA101-Mythen.../assets/...")
          // Dies ist ein Pfad relativ zum Steiner_GA Root
          if (decodedPath.match(/^GA\d{3}[a-z]?[-\s]/i)) {
            // Pfad ist vom Root aus (this.sourceDir)
            fullImagePath = path.join(this.sourceDir, decodedPath);
          }
          // Variante 2: Pfad enthält nur "assets/" am Anfang (z.B. "assets/GA089-...")
          else if (decodedPath.startsWith('assets/') || decodedPath.startsWith('assets\\')) {
            fullImagePath = path.join(gaDir, decodedPath);
          } 
          // Variante 3: Pfad ist nur Dateiname (z.B. "GA110-...jpg")
          else if (decodedPath.match(/^GA\d{3}/i)) {
            fullImagePath = path.join(gaDir, 'assets', decodedPath);
          }
          // Variante 4: Relativer Pfad ohne GA-Präfix
          else {
            fullImagePath = path.join(gaDir, 'assets', decodedPath);
          }
          
          if (!fs.existsSync(fullImagePath)) {
            console.warn(`   ⚠ ${lectureId}: Bild nicht gefunden: ${decodedPath}`);
            console.warn(`      Geprüfter Pfad: ${fullImagePath}`);
            failedImages++;
            continue;
          }
          
          // Bestimme Dateiendung und prüfe ob Konvertierung nötig ist
          const ext = path.extname(fullImagePath).toLowerCase();
          const isJpeg = ext === '.jpg' || ext === '.jpeg';
          
          let imageBuffer;
          let mimeType = 'image/png'; // Standard: PNG nach Konvertierung
          let convertedPath = img.path; // Pfad für gespeichertes Bild
          
          try {
            if (isJpeg) {
              // Konvertiere JPEG zu PNG
              imageBuffer = await sharp(fullImagePath)
                .png()
                .toBuffer();
              
              // Aktualisiere Pfad: .jpeg/.jpg → .png
              convertedPath = img.path.replace(/\.jpe?g$/i, '.png');
            } else {
              // Andere Formate (PNG, GIF, WEBP) direkt lesen
              imageBuffer = fs.readFileSync(fullImagePath);
              
              // Bestimme MIME-Type für nicht-JPEG Dateien
              const mimeTypes = {
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
              };
              mimeType = mimeTypes[ext] || 'image/png';
            }
            
            // Konvertiere zu Base64
            const base64 = imageBuffer.toString('base64');
            
            // Aktualisiere auch Markdown-Referenz wenn JPEG konvertiert wurde
            let convertedMarkdownRef = img.markdownRef;
            if (isJpeg && img.markdownRef) {
              convertedMarkdownRef = img.markdownRef.replace(/\.jpe?g$/i, '.png');
            }
            
            imagesWithData[lectureId].push({
              index: img.index,
              altText: img.altText,
              path: convertedPath, // Verwende konvertierten Pfad (.png statt .jpeg)
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
    
    
    // Speichere chunks
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const filename = `steiner-images-part${String(i + 1).padStart(2, '0')}.json`;
      const filepath = path.join(this.outputDir, filename);
      
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
    
    // Lade fullLectures die gerade exportiert wurden
    const fullLectures = {};
    const files = fs.readdirSync(this.outputDir).filter(f => 
      f.startsWith('steiner-full-lectures-') && f.endsWith('.json')
    );
    
    
    for (const file of files) {
      try {
        const filePath = path.join(this.outputDir, file);
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

