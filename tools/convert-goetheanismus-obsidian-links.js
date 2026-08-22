/**
 * Konvertiert Quellen-Links in Obsidian-Zitatnotizen zu ga_online (Tab Texte).
 *
 * URL-Schema:
 *   Zitat:  goto.html#ga=030&lecture=GA030/21&p=k644x6&page=325&text=...
 *   Fußzeile (Textanfang, ohne Markierung): goto.html#ga=030&lecture=GA030/21
 * Optional: &date=YYYY-MM-DD nur bei vollständigem Vortragsdatum.
 *
 * `lecture` + `p` sind sprachstabile Ortung (gleiche Block-IDs in einer späteren englischen GA).
 * `text=` bleibt der deutsche Zitat-Anfang für die gepunktete Unterstreichung, solange der GA-Text deutsch ist.
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

function buildGotoUrl({ ga, page, pageEnd, date, text, lecture, p }) {
  const parts = [`ga=${padGa(ga)}`];
  if (date) parts.push(`date=${date}`);
  if (page) parts.push(`page=${page}`);
  if (pageEnd) parts.push(`pageEnd=${pageEnd}`);
  if (lecture) parts.push(`lecture=${encodeURIComponent(lecture)}`);
  if (p) parts.push(`p=${encodeURIComponent(String(p).replace(/^\^/, ''))}`);
  if (text) parts.push(`text=${encodeURIComponent(text)}`);
  return `${BASE}#${parts.join('&')}`;
}

const API_BASE = 'https://ga-suche.onrender.com';
const RESOLVE_API = `${API_BASE}/api/resolve-lecture`;
const lectureIdCache = new Map();

function normalizeForMatch(txt) {
  return String(txt || '').toLowerCase()
    .replace(/ß/g, 'ss')
    .replace(/[,;.:!?()"'„"‚'»«›‹—–-]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function matchParagraphIndex(paragraphs, searchText) {
  if (!Array.isArray(paragraphs) || !searchText) return null;
  const words = normalizeForMatch(searchText).split(/\s+/).filter(w => w.length >= 2);
  if (words.length < 3) return null;
  for (let len = Math.min(words.length, 40); len >= 3; len--) {
    const phrase = words.slice(0, len).join(' ');
    for (const para of paragraphs) {
      const content = para.content || para.text || '';
      if (!normalizeForMatch(content).includes(phrase)) continue;
      if (!para.index) continue;
      return String(para.index).replace(/^\^/, '');
    }
  }
  return null;
}

async function findParagraphIdByText(lectureId, text) {
  if (!lectureId || !text) return null;
  try {
    const pathId = String(lectureId).includes('/')
      ? String(lectureId).split('/').map(encodeURIComponent).join('/')
      : encodeURIComponent(lectureId);
    const resp = await fetch(`${API_BASE}/api/full-lecture/${pathId}`);
    if (!resp.ok) return null;
    const data = await resp.json();
    const paras = (data.lecture && data.lecture.paragraphs) || [];
    return matchParagraphIndex(paras, text);
  } catch (e) {
    return null;
  }
}

async function resolveLecture(ga, page, date, text) {
  const key = `${padGa(ga)}|${page || ''}|${date || ''}`;
  if (lectureIdCache.has(key)) {
    const cached = lectureIdCache.get(key);
    if (cached && text && !cached._textMatched) {
      const byText = await findParagraphIdByText(cached.lectureId, text);
      if (byText) {
        cached.paragraphIndex = byText;
        cached._textMatched = true;
      }
    }
    return cached;
  }
  const q = new URLSearchParams({ ga: padGa(ga) });
  if (date) q.set('date', date);
  if (page) q.set('page', page);
  if (text) q.set('text', text);
  try {
    const resp = await fetch(`${RESOLVE_API}?${q}`);
    if (!resp.ok) {
      lectureIdCache.set(key, null);
      return null;
    }
    const data = await resp.json();
    let paragraphIndex = data.paragraphIndex ? String(data.paragraphIndex).replace(/^\^/, '') : null;
    const lectureId = data.lectureId || null;
    if (text && lectureId) {
      const byText = await findParagraphIdByText(lectureId, text);
      if (byText) paragraphIndex = byText;
    }
    const resolved = {
      lectureId,
      paragraphIndex,
      _textMatched: !!(text && paragraphIndex)
    };
    lectureIdCache.set(key, resolved);
    return resolved;
  } catch (e) {
    lectureIdCache.set(key, null);
    return null;
  }
}

async function resolveLectureId(ga, page, date) {
  const resolved = await resolveLecture(ga, page, date);
  return resolved ? resolved.lectureId : null;
}

function parseLinkMeta(url) {
  const pdf = url.match(/ga(\d+[a-zA-Z]?)\.pdf#page=(\d+)/i);
  if (pdf) return { ga: pdf[1], page: pdf[2] };
  const hash = (url.split('#')[1] || '').replace(/\+/g, '%20');
  if (!hash) return null;
  const p = new URLSearchParams(hash);
  return {
    ga: p.get('ga'),
    date: p.get('date'),
    page: p.get('page'),
    pageEnd: p.get('pageEnd'),
    lecture: p.get('lecture'),
    p: p.get('p'),
    text: p.get('text')
  };
}

function findInlineMeta(text, gaHint) {
  const re = /https:\/\/rudolf-steiner-online\.de\/goto\.html#([^)\s]+)/g;
  let last = null;
  let m;
  while ((m = re.exec(text)) !== null) {
    const meta = parseLinkMeta('https://rudolf-steiner-online.de/goto.html#' + m[1]);
    if (!meta || !meta.ga) continue;
    if (gaHint && padGa(meta.ga) !== padGa(gaHint)) continue;
    last = meta;
  }
  return last;
}

async function buildStartUrl(meta) {
  const ga = meta.ga;
  const date = meta.date || null;
  let lecture = meta.lecture || null;
  if (!lecture) {
    lecture = await resolveLectureId(ga, meta.page, date);
  }
  return buildGotoUrl({ ga, date, lecture });
}

function wrapGaLink(url, label) {
  const href = String(url).replace(/&/g, '&amp;');
  const safeLabel = String(label)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return `<a href="${href}" target="ga-suche" rel="opener">${safeLabel}</a>`;
}

function pageDisplay(pageStart, pageEnd) {
  return pageEnd ? `${pageStart}–${pageEnd}` : pageStart;
}

async function convertContent(content) {
  let result = content;
  let count = 0;

  // 1) Wiki-Zitat: ([[GA 001]][[GA 001 - Titel#^id|, 1884, S. 12]])
  const wikiRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\]\[\[GA[^\]|#]+(?:#[^\]]+)?\|,\s*(?:(\d{4}),\s*)?S\.\s*(\d+)(?:[-–](\d+))?\]\]\)/g;
  result = result.replace(wikiRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = year ? `${year}, S. ${pageDisplay(page, pageEnd)}` : `S. ${pageDisplay(page, pageEnd)}`;
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 1b) Bereits vorhandene goto.html-Zitatlinks: Zitattext verlängern, vault/file entfernen
  const rsoRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[([^\]]+)\]\((https:\/\/rudolf-steiner-online\.de\/goto\.html#[^)]+)\)\)/g;
  result = result.replace(rsoRe, (match, ga, label, oldUrl, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const params = new URLSearchParams(oldUrl.split('#')[1] || '');
    const page = params.get('page');
    const pageEnd = params.get('pageEnd');
    const date = params.get('date');
    const url = buildGotoUrl({ ga, page, pageEnd, date, text: snippet });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 2) PDF-Link mit vollständigem Datum: ([[GA 078]], [01.09.1921, S. 80 f.](pdf))
  const pdfDatedRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[(\d{2})\.(\d{2})\.(\d{4}),\s*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)?/g;
  result = result.replace(pdfDatedRe, (match, ga, day, month, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = `${day}.${month}.${year}, S. ${pageDisplay(page, pageEnd)}`;
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3) PDF-Link ohne Datum: ([[GA 030]], [S. 325](pdf)) oder [S. 156-157]
  const pdfPageRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)?/g;
  result = result.replace(pdfPageRe, (match, ga, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, `S. ${pageDisplay(page, pageEnd)}`)})`;
  });

  // 4) Quellenzeile: leerer Link → Anfang des Textes, ohne page/text-Markierung
  const footerRe = /\[ ?\]\((https:\/\/(?:akanthosakademie\.files\.wordpress\.com\/[^)]+|rudolf-steiner-online\.de\/(?:goto|app)\.html#[^)]+))\)/gi;
  const footerMatches = [];
  let fm;
  while ((fm = footerRe.exec(result)) !== null) {
    footerMatches.push({ full: fm[0], url: fm[1], index: fm.index });
  }
  for (let i = footerMatches.length - 1; i >= 0; i--) {
    const { full, url, index } = footerMatches[i];
    const fromUrl = parseLinkMeta(url) || {};
    const fromInline = findInlineMeta(result.slice(0, index), fromUrl.ga) || {};
    const meta = {
      ga: fromUrl.ga || fromInline.ga,
      date: fromUrl.date || fromInline.date || null,
      page: fromUrl.page || fromInline.page || null,
      lecture: fromUrl.lecture || null
    };
    if (!meta.ga) continue;
    const startUrl = await buildStartUrl(meta);
    if (wrapGaLink(startUrl, ' ') === full) continue;
    result = result.slice(0, index) + wrapGaLink(startUrl, ' ') + result.slice(index + full.length);
    count++;
  }

  // 5) Markdown-goto-Links → HTML mit benanntem Fenster (Fokus bleibt auf ga-suche)
  result = result.replace(
    /\[([^\]]*)\]\((https:\/\/rudolf-steiner-online\.de\/goto\.html#[^)]+)\)/g,
    (match, label, url) => {
      count++;
      return wrapGaLink(url, label);
    }
  );

  // 6) Bestehende HTML-goto-Links: Zitat → lecture+p+text; Fußzeile → nur lecture
  const htmlRe = /<a href="(https:\/\/rudolf-steiner-online\.de\/goto\.html#[^"]+)"([^>]*)>([\s\S]*?)<\/a>/g;
  const htmlMatches = [];
  let hm;
  while ((hm = htmlRe.exec(result)) !== null) {
    htmlMatches.push({ full: hm[0], hrefRaw: hm[1], label: hm[3], index: hm.index });
  }
  for (let i = htmlMatches.length - 1; i >= 0; i--) {
    const { full, hrefRaw, label, index } = htmlMatches[i];
    const href = hrefRaw.replace(/&amp;/g, '&');
    const meta = parseLinkMeta(href);
    if (!meta || !meta.ga) continue;
    const isFooter = String(label).trim() === '';
    if (isFooter) {
      const startUrl = await buildStartUrl(meta);
      const replacement = wrapGaLink(startUrl, ' ');
      if (replacement === full) continue;
      result = result.slice(0, index) + replacement + result.slice(index + full.length);
      count++;
      continue;
    }
    const resolved = await resolveLecture(meta.ga, meta.page, meta.date, meta.text);
    const lecture = (resolved && resolved.lectureId) || meta.lecture;
    const p = (resolved && resolved.paragraphIndex) || meta.p;
    const url = buildGotoUrl({
      ga: meta.ga,
      page: meta.page,
      pageEnd: meta.pageEnd,
      date: meta.date,
      text: meta.text,
      lecture,
      p
    });
    const hrefEscaped = String(url).replace(/&/g, '&amp;');
    const replacement = `<a href="${hrefEscaped}" target="ga-suche" rel="opener">${label}</a>`;
    if (replacement === full) continue;
    result = result.slice(0, index) + replacement + result.slice(index + full.length);
    count++;
  }

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

async function main() {
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
    const { result, count } = await convertContent(original);
    if (count === 0 || result === original) {
      continue;
    }
    filesChanged++;
    linksChanged += count;
    console.log(`${path.basename(file)}: ${count} Link(s)`);
    if (dryRun) {
      const hrefRe = /goto\.html#([^"'\s)]+)/g;
      let m;
      while ((m = hrefRe.exec(result)) !== null) {
        const decoded = m[1].replace(/&amp;/g, '&');
        console.log('  URL:', decoded.length > 220 ? decoded.slice(0, 220) + '…' : decoded);
      }
    } else {
      fs.writeFileSync(file, result, 'utf8');
    }
  }

  console.log(`\n${filesChanged} Datei(en), ${linksChanged} Link(s) ${dryRun ? 'würden geändert' : 'geändert'}.`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
