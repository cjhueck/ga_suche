/**
 * Konvertiert Quellen-Links in Obsidian-Zitatnotizen zu ga_online (Tab Texte).
 *
 * URL-Schema (sprachunabhängig für Navigation):
 *   https://rudolf-steiner-online.de/goto.html#ga=030&page=325&text=...
 * Optional: &date=YYYY-MM-DD nur bei vollständigem Vortragsdatum.
 *
 * `text=` enthält den deutschen Zitat-Anfang (zum Zeitpunkt der Konvertierung).
 * Dadurch bleibt die Treffer-Markierung auch nach einer späteren englischen
 * Übersetzung der Notizen erhalten, solange die URLs nicht mitübersetzt werden.
 *
 * Nutzung:
 *   node tools/convert-goetheanismus-obsidian-links.js --dry-run --files "Abweichung vom Normalen.md" "Aktiver Nachvollzug der Bildung.md"
 *   node tools/convert-goetheanismus-obsidian-links.js --files "Abweichung vom Normalen.md" "Aktiver Nachvollzug der Bildung.md"
 *   node tools/convert-goetheanismus-obsidian-links.js --all
 */
const fs = require('fs');
const path = require('path');

const VAULT = 'C:\\Obsidian\\Steiner Goetheanismus';
const QUOTES_DIR = path.join(VAULT, 'Zitate Steiner');
const BASE = 'https://rudolf-steiner-online.de/goto.html';
const MAX_QUOTE_WORDS = 40;

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const convertAll = args.includes('--all');
const filesArgIndex = args.indexOf('--files');
const namedFiles = filesArgIndex >= 0
  ? args.slice(filesArgIndex + 1).filter(a => !a.startsWith('--'))
  : [];

function padGa(ga) {
  const m = String(ga).match(/^(\d+)([a-zA-Z]?)$/);
  if (!m) return String(ga).padStart(3, '0');
  return m[1].padStart(3, '0') + m[2].toLowerCase();
}

function extractQuoteSnippet(textBefore) {
  const blocks = textBefore.split(/\n(?:---+|____+)\n|\n\n+/);
  const lastBlock = (blocks.filter(b => b.trim()).pop() || textBefore);
  const lines = lastBlock.split('\n');
  const contentLines = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (/^#{1,6}\s/.test(trimmed)) continue;
    if (/^(\s*\[\[[^\]]+\]\]\s*[\|\s]*)+$/.test(trimmed)) continue;
    contentLines.push(trimmed);
  }
  const quoteText = contentLines.join(' ');
  const cleanText = quoteText
    .replace(/\[\[([^\]]*?\|)?([^\]]*?)\]\]/g, '$2')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\(\[\[GA[\s\S]*$/g, '')
    .trim();
  const words = cleanText
    .split(/\s+/)
    .map(w => w.replace(/^[„"‚'«»‹›(]+|[)"'«»‹›]+$/g, ''))
    .filter(w => w.length >= 1);
  return words.slice(0, MAX_QUOTE_WORDS).join(' ');
}

function buildGotoUrl({ ga, page, pageEnd, date, text }) {
  const parts = [`ga=${padGa(ga)}`];
  if (date) parts.push(`date=${date}`);
  if (page) parts.push(`page=${page}`);
  if (pageEnd) parts.push(`pageEnd=${pageEnd}`);
  if (text) parts.push(`text=${encodeURIComponent(text)}`);
  return `${BASE}#${parts.join('&')}`;
}

function pageDisplay(pageStart, pageEnd) {
  return pageEnd ? `${pageStart}–${pageEnd}` : pageStart;
}

function convertContent(content) {
  let result = content;
  let count = 0;

  // 1) Wiki-Zitat: ([[GA 001]][[GA 001 - Titel#^id|, 1884, S. 12]])
  const wikiRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\]\[\[GA[^\]|#]+(?:#[^\]]+)?\|,\s*(?:(\d{4}),\s*)?S\.\s*(\d+)(?:[-–](\d+))?\]\]\)/g;
  result = result.replace(wikiRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = year ? `${year}, S. ${pageDisplay(page, pageEnd)}` : `S. ${pageDisplay(page, pageEnd)}`;
    count++;
    return `([[GA ${ga}]], [${label}](${url}))`;
  });

  // 2) PDF-Link mit vollständigem Datum: ([[GA 078]], [01.09.1921, S. 80 f.](pdf))
  const pdfDatedRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[(\d{2})\.(\d{2})\.(\d{4}),\s*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)/g;
  result = result.replace(pdfDatedRe, (match, ga, day, month, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = `${day}.${month}.${year}, S. ${pageDisplay(page, pageEnd)}`;
    count++;
    return `([[GA ${ga}]], [${label}](${url}))`;
  });

  // 3) PDF-Link ohne Datum: ([[GA 030]], [S. 325](pdf)) oder [S. 156-157]
  const pdfPageRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)/g;
  result = result.replace(pdfPageRe, (match, ga, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    count++;
    return `([[GA ${ga}]], [S. ${pageDisplay(page, pageEnd)}](${url}))`;
  });

  // 4) Quellenzeile unten: leerer PDF-Link – denselben Zitat-Text wie der Inline-Link verwenden
  const footerRe = /\[ ?\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]*?ga(\d+[a-zA-Z]?)\.pdf#page=(\d+)[^)]*\)/gi;
  result = result.replace(footerRe, (match, ga, page) => {
    const gaPad = padGa(ga);
    const reuse = result.match(new RegExp(
      `https://rudolf-steiner-online\\.de/goto\\.html#ga=${gaPad}&(?:date=[^&]+&)?page=${page}[^)\\s]*`
    ));
    if (reuse) {
      count++;
      return `[ ](${reuse[0]})`;
    }
    const url = buildGotoUrl({ ga, page });
    count++;
    return `[ ](${url})`;
  });

  return { result, count };
}

function listMarkdownFiles() {
  if (namedFiles.length) {
    return namedFiles.map(name => {
      const direct = path.isAbsolute(name) ? name : path.join(QUOTES_DIR, name);
      return direct;
    });
  }
  if (!convertAll) {
    throw new Error('Bitte --files "Datei.md" ... oder --all angeben.');
  }
  return fs.readdirSync(QUOTES_DIR)
    .filter(f => f.endsWith('.md') && !f.includes(' - Kopie'))
    .map(f => path.join(QUOTES_DIR, f));
}

function main() {
  const files = listMarkdownFiles();
  let filesChanged = 0;
  let linksChanged = 0;

  console.log(dryRun ? '=== Dry-Run (keine Dateien schreiben) ===\n' : '=== Konvertierung ===\n');

  for (const file of files) {
    if (!fs.existsSync(file)) {
      console.error('Datei nicht gefunden:', file);
      continue;
    }
    const original = fs.readFileSync(file, 'utf8');
    const { result, count } = convertContent(original);
    if (count === 0 || result === original) {
      continue;
    }
    filesChanged++;
    linksChanged += count;
    console.log(`${path.basename(file)}: ${count} Link(s)`);
    if (dryRun) {
      const beforeLinks = original.match(/\[[^\]]*\]\([^)]+\)/g) || [];
      const afterLinks = result.match(/\[[^\]]*\]\([^)]+\)/g) || [];
      afterLinks.slice(0, 4).forEach((link, i) => {
        if (link !== beforeLinks[i]) {
          console.log('  NEU:', link.length > 180 ? link.slice(0, 180) + '…' : link);
        }
      });
    } else {
      fs.writeFileSync(file, result, 'utf8');
    }
  }

  console.log(`\n${filesChanged} Datei(en), ${linksChanged} Link(s) ${dryRun ? 'würden geändert' : 'geändert'}.`);
}

main();
