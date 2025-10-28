const fs = require('fs');
const path = require('path');

class ConceptsExporter {
  constructor(sourceDir, outputDir) {
    this.sourceDir = sourceDir;
    this.outputDir = outputDir;
    this.alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  }

  // Parse keyword entry from markdown
  parseKeywordEntry(text, letter) {
    // Match ## [[Keyword]]
    const headerMatch = text.match(/^##\s+\[\[(.+?)\]\]/);
    if (!headerMatch) return null;

    const keyword = headerMatch[1].trim();
    
    // Extract text content (everything after the header until next ## or end)
    const lines = text.split('\n');
    const contentLines = [];
    let inContent = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Skip the header line
      if (i === 0) {
        inContent = true;
        continue;
      }
      
      // Stop at next ## header
      if (line.match(/^##\s+\[\[.+?\]\]/)) {
        break;
      }
      
      // Skip empty lines at the start
      if (!inContent && line.trim() === '') continue;
      
      if (line.trim()) {
        inContent = true;
        contentLines.push(line);
      }
    }

    const content = contentLines.join('\n').trim();
    
    // Extract GA references from content
    const gaReferences = this.extractGAReferences(content);

    return {
      keyword: keyword,
      alphabetical: letter,
      text: content,
      gaReferences: gaReferences,
      source: 'obsidian-az'
    };
  }

  // Extract GA references from text
  extractGAReferences(text) {
    const references = new Set();
    
    // Match [[GA###/# ...]] or [[GA###/#]]
    const regex = /\[\[GA(\d{2,3}[a-z]?)\s*\((\d+)\.\)[^\]]*\|GA\d{2,3}[a-z]?\/\d+\]\]/gi;
    const matches = text.matchAll(regex);
    
    for (const match of matches) {
      const gaNum = match[1].toLowerCase();
      const lectureNum = match[2];
      references.add(`GA${gaNum}/${lectureNum}`);
    }

    // Also match simpler format [[GA###/#]]
    const simpleRegex = /\[\[GA(\d{2,3}[a-z]?)\/(\d+)\]\]/gi;
    const simpleMatches = text.matchAll(simpleRegex);
    
    for (const match of simpleMatches) {
      const gaNum = match[1].toLowerCase();
      const lectureNum = match[2];
      references.add(`GA${gaNum}/${lectureNum}`);
    }

    return Array.from(references).sort();
  }

  // Split markdown file into keyword entries
  splitIntoEntries(content) {
    const entries = [];
    const lines = content.split('\n');
    let currentEntry = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check if this is a keyword header
      if (line.match(/^##\s+\[\[.+?\]\]/)) {
        // Save previous entry if exists
        if (currentEntry.length > 0) {
          entries.push(currentEntry.join('\n'));
        }
        // Start new entry
        currentEntry = [line];
      } else {
        // Add line to current entry
        currentEntry.push(line);
      }
    }
    
    // Add last entry
    if (currentEntry.length > 0) {
      entries.push(currentEntry.join('\n'));
    }
    
    return entries;
  }

  // Export single letter or all
  async export(selectedLetters = []) {
    console.log('🔍 Searching for Schlagwörter A-Z files...\n');
    
    const keywords = [];
    const lettersToExport = selectedLetters.length > 0 
      ? selectedLetters.map(l => l.toUpperCase()) 
      : this.alphabet;

    console.log(`📚 Exporting letters: ${lettersToExport.join(', ')}\n`);

    for (const letter of lettersToExport) {
      const filePath = path.join(this.sourceDir, 'Schlagwörter A-Z', `${letter}.md`);
      
      if (!fs.existsSync(filePath)) {
        console.warn(`⚠️  File not found: ${letter}.md`);
        continue;
      }

      console.log(`📖 Processing ${letter}.md...`);
      
      const content = fs.readFileSync(filePath, 'utf8');
      const entries = this.splitIntoEntries(content);
      
      let count = 0;
      for (const entryText of entries) {
        const keyword = this.parseKeywordEntry(entryText, letter);
        if (keyword) {
          keywords.push(keyword);
          count++;
        }
      }
      
      console.log(`   ✓ Extracted ${count} keywords from ${letter}.md`);
    }

    if (keywords.length === 0) {
      console.log('\n❌ No keywords found.');
      return;
    }

    console.log(`\n✅ Total keywords extracted: ${keywords.length}`);

    // Sort alphabetically
    keywords.sort((a, b) => a.keyword.localeCompare(b.keyword));

    // Create filename based on selection
    let fileName;
    if (selectedLetters.length === 0) {
      fileName = 'schlagworte-az-all.json';
    } else if (selectedLetters.length === 1) {
      fileName = `schlagworte-az-${selectedLetters[0].toLowerCase()}.json`;
    } else {
      const range = `${selectedLetters[0].toLowerCase()}-${selectedLetters[selectedLetters.length - 1].toLowerCase()}`;
      fileName = `schlagworte-az-${range}.json`;
    }

    const filePath = path.join(this.outputDir, fileName);
    const data = {
      source: 'Schlagwörter A-Z (Obsidian)',
      exportDate: new Date().toISOString(),
      letters: lettersToExport,
      keywords: keywords
    };

    const jsonStr = JSON.stringify(data, null, 2);
    fs.writeFileSync(filePath, jsonStr, 'utf8');

    const sizeMB = (Buffer.byteLength(jsonStr, 'utf8') / (1024 * 1024)).toFixed(2);
    console.log(`\n💾 Exported to: ${fileName}`);
    console.log(`   Size: ${sizeMB} MB`);
    console.log(`   Keywords: ${keywords.length}`);
    console.log(`   GA References: ${keywords.reduce((sum, kw) => sum + kw.gaReferences.length, 0)}`);

    // Print statistics
    const letterStats = {};
    keywords.forEach(kw => {
      letterStats[kw.alphabetical] = (letterStats[kw.alphabetical] || 0) + 1;
    });

    console.log('\n📊 Keywords per letter:');
    Object.keys(letterStats).sort().forEach(letter => {
      console.log(`   ${letter}: ${letterStats[letter]}`);
    });

    console.log(`\n🎉 Export complete!`);
    console.log(`\n💡 To undo integration: Delete ${fileName} and restart the application.`);
  }
}

// CLI Interface
if (require.main === module) {
  const args = process.argv.slice(2);
  
  // Default paths
  const sourceDir = path.join(__dirname, '..', 'Steiner_GA');
  const outputDir = __dirname;

  const exporter = new ConceptsExporter(sourceDir, outputDir);

  let selectedLetters = [];
  
  if (args.length > 0) {
    const input = args.join(',').toUpperCase();
    
    // Parse input: "A", "A,B,C", "A-Z", etc.
    const tokens = input.split(',').map(s => s.trim());
    
    for (const token of tokens) {
      // Check for range (A-Z)
      if (token.includes('-')) {
        const [start, end] = token.split('-').map(s => s.trim());
        const startIdx = start.charCodeAt(0);
        const endIdx = end.charCodeAt(0);
        
        for (let i = startIdx; i <= endIdx; i++) {
          selectedLetters.push(String.fromCharCode(i));
        }
      } else if (token.match(/^[A-Z]$/)) {
        // Single letter
        selectedLetters.push(token);
      } else if (token === 'ALL') {
        // Export all
        selectedLetters = [];
        break;
      }
    }
    
    if (selectedLetters.length > 0) {
      // Remove duplicates and sort
      selectedLetters = [...new Set(selectedLetters)].sort();
      console.log(`🎯 Exporting selected letters: ${selectedLetters.join(', ')}\n`);
    } else {
      console.log('🎯 Exporting ALL letters (A-Z)\n');
    }
  } else {
    console.log('🎯 Exporting ALL letters (A-Z)\n');
  }

  exporter.export(selectedLetters)
    .then(() => {
      console.log('\n✨ Done!');
      process.exit(0);
    })
    .catch(err => {
      console.error('❌ Error:', err);
      process.exit(1);
    });
}

module.exports = ConceptsExporter;

