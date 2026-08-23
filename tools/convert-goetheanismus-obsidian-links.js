/**
 * Konvertiert Quellen-Links in Obsidian-Zitatnotizen zu ga_online (Tab Texte).
 *
 * URL-Schema:
 *   Zitat:  goto.html#ga=030&lecture=GA030/21&p=k644x6&page=325&text=...
 *   Fußzeile (Textanfang, ohne Markierung): goto.html#ga=030&lecture=GA030/21
 * Optional: &date=YYYY-MM-DD nur bei vollständigem Vortragsdatum.
 *
 * `lecture` + `p` sind sprachstabile Ortung (gleiche Block-IDs in einer späteren englischen GA).
 * `text=` bleibt der deutsche Zitat-Anfang für die Markierung, solange der GA-Text deutsch ist.
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

function isMetaLine(trimmed) {
  if (!trimmed) return true;
  if (/^#{1,6}\s/.test(trimmed)) return true;
  if (/^(\s*\[\[[^\]]+\]\]\s*[\|\s]*)+$/.test(trimmed)) return true;
  return false;
}

function snippetFromBlock(block) {
  const lines = String(block || '').split('\n');
  const contentLines = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (isMetaLine(trimmed)) continue;
    contentLines.push(trimmed);
  }
  if (!contentLines.length) return '';
  const cleanText = contentLines.join(' ')
    .replace(/\(\[\[GA[\s\S]*$/g, '')
    .replace(/\[\[([^\]]*?\|)?([^\]]*?)\]\]/g, '$2')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();
  const words = cleanText
    .split(/\s+/)
    .map(w => w.replace(/^[„"‚'«»‹›(]+|[)"'«»‹›]+$/g, ''))
    .filter(w => w.length >= 1);
  return words.slice(0, MAX_QUOTE_WORDS).join(' ');
}

function extractQuoteSnippet(textBefore) {
  const blocks = String(textBefore || '').split(/\n(?:---+|____+)\n|\n\n+/);
  for (const block of blocks) {
    const snippet = snippetFromBlock(block);
    if (snippet) return snippet;
  }
  return snippetFromBlock(textBefore);
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
      date: data.date || null,
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
    date: normalizeSteinerDate(p.get('date')),
    page: p.get('page'),
    pageEnd: p.get('pageEnd'),
    lecture: p.get('lecture'),
    p: p.get('p'),
    text: p.get('text')
  };
}

function normalizeSteinerDate(date) {
  if (!date) return null;
  const m = String(date).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return date;
  let year = Number(m[1]);
  if (year >= 2000 && year <= 2029) year -= 100;
  return `${year}-${m[2]}-${m[3]}`;
}

function isPlausibleSteinerDate(date) {
  const m = String(date || '').match(/^(\d{4})/);
  if (!m) return false;
  const year = Number(m[1]);
  return year >= 1883 && year <= 1925;
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

function findInlineMeta(text, gaHint) {
  const re = /goto\.html#([^"'\s)]+)/g;
  let first = null;
  let firstQuote = null;
  let m;
  while ((m = re.exec(text)) !== null) {
    const hash = m[1].replace(/&amp;/g, '&');
    const meta = parseLinkMeta('https://rudolf-steiner-online.de/goto.html#' + hash);
    if (!meta || !meta.ga) continue;
    if (gaHint && padGa(meta.ga) !== padGa(gaHint)) continue;
    if (!first) first = meta;
    if (!firstQuote && (meta.page || meta.text)) firstQuote = meta;
  }
  return firstQuote || first;
}

function citationLabel({ page, pageEnd, date, year }) {
  const pages = page ? `S. ${pageDisplay(page, pageEnd)}` : '';
  if (date) {
    const dm = String(date).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (dm && pages) return `${dm[3]}.${dm[2]}.${dm[1]}, ${pages}`;
    if (dm) return `${dm[3]}.${dm[2]}.${dm[1]}`;
  }
  if (year && pages) return `${year}, ${pages}`;
  return pages;
}

async function buildStartUrl(meta) {
  const ga = meta.ga;
  const date = normalizeSteinerDate(meta.date || null);
  let lecture = meta.lecture || null;
  if (!lecture) {
    lecture = await resolveLectureId(ga, meta.page, date);
  }
  return buildGotoUrl({ ga, date, lecture });
}

const FOOTER_ICON = '&nbsp;';

function isFooterLabel(label) {
  const t = String(label || '').replace(/&amp;/g, '&').replace(/&nbsp;/g, ' ').trim();
  return t === '' || t === '↗' || t === '🔗';
}

function wrapGaLink(url, label) {
  const href = String(url).replace(/&/g, '&amp;');
  const safeLabel = String(label)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return `<a href="${href}" target="ga-suche" rel="opener">${safeLabel}</a>`;
}

function wrapGaFooterLink(url) {
  const href = String(url).replace(/&/g, '&amp;');
  return `<a href="${href}" target="ga-suche" rel="opener" title="Textanfang in der GA-Suche" class="external-link">${FOOTER_ICON}</a>`;
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
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 1c) Wiki-Zitat mit Komma: ([[GA 001]], [[GA 001 - Titel#^id|1884, S. 37-38]])
  const wikiCommaRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[\[GA[^\]|#]+(?:#[^\]]+)?\|(?:(\d{4}),\s*)?S\.\s*(\d+)(?:[-–](\d+))?(?:\s*f+\.?)?\]\]\)/g;
  result = result.replace(wikiCommaRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 1b) Bereits vorhandene goto.html-Zitatlinks: Zitattext verlängern, vault/file entfernen
  const rsoRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[([^\]]+)\]\((https:\/\/rudolf-steiner-online\.de\/goto\.html#[^)]+)\)\)/g;
  result = result.replace(rsoRe, (match, ga, oldLabel, oldUrl, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const hash = (oldUrl.split('#')[1] || '').replace(/\+/g, '%20');
    const params = new URLSearchParams(hash);
    const page = params.get('page');
    const pageEnd = params.get('pageEnd');
    const date = normalizeSteinerDate(params.get('date'));
    const url = buildGotoUrl({ ga, page, pageEnd, date, text: snippet });
    const label = citationLabel({ page, pageEnd, date }) || oldLabel;
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

  // 3b) Drei Wiki-Links: ([[GA 030]], [[GA 030 - Titel|1894]], [[GA 030 - Titel#^id|S. 76 f.]])
  const wikiTripleRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[\[GA[^\]\n]+\|(\d{4})\]\],\s*\[\[GA[^\]|#\n]+(?:#[^\]]+)?\|S\.\s*(\d+)(?:[-–](\d+))?(?:\s*f+\.?)?\]\]\)?/g;
  result = result.replace(wikiTripleRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3c) PDF mit vollständigem Datum im Label: [20.10.1908. S. 201]
  const pdfDateThenPageRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[[^\]]*(\d{2})\.(\d{2})\.(\d{4})[^\]]*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)?/g;
  result = result.replace(pdfDateThenPageRe, (match, ga, day, month, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = citationLabel({ page, pageEnd, date: `${year}-${month}-${day}` });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3d) PDF mit Jahr: ([[GA 020]], [1916, S. 163](pdf)) / [V. 1925, S. 113]
  const pdfYearRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[[^\]]*(\d{4})[,.]\s*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)?/g;
  result = result.replace(pdfYearRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3e) PDF: [S. 166, 01.11.1918] mit oder ohne [[GA]]
  const pdfPageThenDateRe = /\((?:\[\[GA\s*(\d+[a-zA-Z]?)\]\]|GA\s*(\d+[a-zA-Z]?)),\s*\[S\.\s*(\d+)(?:[-–](\d+))?,\s*(\d{2})\.(\d{2})\.(\d{4})[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)?/g;
  result = result.replace(pdfPageThenDateRe, (match, gaWiki, gaBare, page, pageEnd, day, month, year, offset) => {
    const ga = gaWiki || gaBare;
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = citationLabel({ page, pageEnd, date: `${year}-${month}-${day}` });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3f) Unverklammertes PDF: [[GA 028]], [Kap. V. 1925, S. 112](pdf)
  const pdfUnwrappedYearRe = /\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[[^\]]*(\d{4})[,.]\s*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)/g;
  result = result.replace(pdfUnwrappedYearRe, (match, ga, year, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `[[GA ${ga}]], ${wrapGaLink(url, label)}`;
  });

  // 3g) Nur PDF-Markdown: ([GA 001, S. 35-36](pdf))
  const bareGaPdfRe = /\(\[GA\s*(\d+[a-zA-Z]?),\s*S\.\s*(\d+)(?:[-–](\d+))?[^\]]*\]\(https:\/\/akanthosakademie\.files\.wordpress\.com\/[^)]+\)\)/g;
  result = result.replace(bareGaPdfRe, (match, ga, page, pageEnd, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, text: snippet });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, `S. ${pageDisplay(page, pageEnd)}`)})`;
  });

  // 3h) Unverlinkte Zitation mit Datum: ([[GA 065]], S. 647–648, 15.04.1916)
  const plainDatedRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*S\.\s*(\d+)(?:[-–](\d+))?,\s*(\d{2})\.(\d{2})\.(\d{4})\)/g;
  result = result.replace(plainDatedRe, (match, ga, page, pageEnd, day, month, year, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = citationLabel({ page, pageEnd, date: `${year}-${month}-${day}` });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3i) Unverlinkte Zitation ohne Komma: ([[GA 061]], S. 492 28.03.1912)
  const plainDatedLooseRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*S\.\s*(\d+)(?:[-–](\d+))?\s+(\d{2})\.(\d{2})\.(\d{4})(?:<a[^>]*title="Textanfang in der GA-Suche"[^>]*>[\s\S]*?<\/a>)?\)?/g;
  result = result.replace(plainDatedLooseRe, (match, ga, page, pageEnd, day, month, year, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    const url = buildGotoUrl({ ga, page, pageEnd, date: `${year}-${month}-${day}`, text: snippet });
    const label = citationLabel({ page, pageEnd, date: `${year}-${month}-${day}` });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3j) «siehe auch» und ähnliche Wiki-Nachweise ohne öffnende Klammer am Match-Anfang
  const wikiAlsoRe = /\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*\[\[GA[^\]|#]+(?:#\^?([a-zA-Z0-9]+))?\|(?:(\d{4}),\s*)?S\.\s*(\d+)(?:[-–](\d+))?(?:\s*f+\.?)?\]\]/g;
  result = result.replace(wikiAlsoRe, (match, ga, blockId, year, page, pageEnd) => {
    const url = buildGotoUrl({ ga, page, pageEnd, p: blockId || undefined });
    const label = citationLabel({ page, pageEnd, year });
    count++;
    return `[[GA ${ga}]], ${wrapGaLink(url, label)}`;
  });

  // 3k) Unverlinkte Seitenzahl, optional mit Datum: ([[GA 030]], S. 274–276) / S. 104, 2.9.1921 / S. 49 6.1.1920 / S. 292-293, 03.1902
  const plainPageRe = /\(\[\[GA\s*(\d+[a-zA-Z]?)\]\],\s*S\.\s*(\d+)(?:[-–](\d+))?(?:\s*f+\.?)?(?:\s*,)?\s*(?:(\d{1,2})\.(\d{1,2})\.(\d{4})|(\d{1,2})\.(\d{4}))?\)/g;
  result = result.replace(plainPageRe, (match, ga, page, pageEnd, day, month, year, monthOnly, yearOnly, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    let date = null;
    let labelYear = yearOnly || null;
    if (day && month && year) {
      date = normalizeSteinerDate(`${year}-${pad2(month)}-${pad2(day)}`);
    }
    const url = buildGotoUrl({ ga, page, pageEnd, date, text: snippet });
    const label = citationLabel({ page, pageEnd, date, year: date ? null : (year || labelYear) });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
  });

  // 3l) Nachweis ohne Wiki-Klammern: (GA 177, S. 224–225, 26.10.1917) / (GA 001, S. 16)
  const bareGaCiteRe = /\(GA\s*(\d+[a-zA-Z]?),\s*S\.\s*(\d+)(?:[-–](\d+))?(?:\s*f+\.?)?(?:\s*,)?\s*(?:(\d{1,2})\.(\d{1,2})\.(\d{4}))?\)/g;
  result = result.replace(bareGaCiteRe, (match, ga, page, pageEnd, day, month, year, offset) => {
    const snippet = extractQuoteSnippet(result.slice(0, offset));
    let date = null;
    if (day && month && year) {
      date = normalizeSteinerDate(`${year}-${pad2(month)}-${pad2(day)}`);
    }
    const url = buildGotoUrl({ ga, page, pageEnd, date, text: snippet });
    const label = citationLabel({ page, pageEnd, date });
    count++;
    return `([[GA ${ga}]], ${wrapGaLink(url, label)})`;
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
    if (wrapGaFooterLink(startUrl) === full) continue;
    result = result.slice(0, index) + wrapGaFooterLink(startUrl) + result.slice(index + full.length);
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
    const originalDateParam = new URLSearchParams((href.split('#')[1] || '').replace(/\+/g, '%20')).get('date');
    const meta = parseLinkMeta(href);
    if (!meta || !meta.ga) continue;
    meta.date = normalizeSteinerDate(meta.date || originalDateParam);
    const isFooter = isFooterLabel(label);
    if (isFooter) {
      const startUrl = await buildStartUrl(meta);
      const replacement = wrapGaFooterLink(startUrl);
      if (replacement === full) continue;
      result = result.slice(0, index) + replacement + result.slice(index + full.length);
      count++;
      continue;
    }
    const inSieheAuch = /siehe auch[\s\S]{0,120}$/i.test(result.slice(Math.max(0, index - 120), index));
    const extractedSnippet = inSieheAuch ? '' : extractQuoteSnippet(result.slice(0, index));
    const quoteText = inSieheAuch ? null : (extractedSnippet || meta.text);
    const snippetChanged = Boolean(!inSieheAuch && extractedSnippet && extractedSnippet !== (meta.text || ''));
    const dateFixed = Boolean(originalDateParam && meta.date && originalDateParam !== meta.date);
    const implausibleDate = Boolean(meta.date && !isPlausibleSteinerDate(meta.date));
    const skipResolve = meta.lecture && meta.p && !dateFixed && !implausibleDate && !snippetChanged && !(inSieheAuch && meta.text);
    let lecture = meta.lecture;
    let p = meta.p;
    if (!skipResolve) {
      let resolved = await resolveLecture(meta.ga, meta.page, implausibleDate ? null : meta.date, quoteText);
      if (quoteText && meta.date && !implausibleDate && (!resolved || !resolved.paragraphIndex)) {
        const withoutDate = await resolveLecture(meta.ga, meta.page, null, quoteText);
        if (withoutDate && withoutDate.paragraphIndex) resolved = withoutDate;
      }
      lecture = (resolved && resolved.lectureId) || meta.lecture;
      p = (resolved && resolved.paragraphIndex) || meta.p;
      if (resolved && resolved.date && (!meta.date || implausibleDate || dateFixed)) {
        meta.date = resolved.date;
      }
    }
    let newLabel = label;
    if (meta.date && (dateFixed || implausibleDate)) {
      const rebuilt = citationLabel({ page: meta.page, pageEnd: meta.pageEnd, date: meta.date });
      if (rebuilt) newLabel = rebuilt;
    }
    const url = buildGotoUrl({
      ga: meta.ga,
      page: meta.page,
      pageEnd: meta.pageEnd,
      date: meta.date,
      text: quoteText,
      lecture,
      p
    });
    const hrefEscaped = String(url).replace(/&/g, '&amp;');
    const replacement = `<a href="${hrefEscaped}" target="ga-suche" rel="opener">${newLabel}</a>`;
    if (replacement === full) continue;
    result = result.slice(0, index) + replacement + result.slice(index + full.length);
    count++;
  }

  // 7) Fußzeilen-Link (Textanfang): ergänzen oder aus Zitat-Metadaten aktualisieren
  const footerMeta = findInlineMeta(result, null);
  if (footerMeta && footerMeta.ga) {
    const startUrl = await buildStartUrl(footerMeta);
    const footer = wrapGaFooterLink(startUrl);
    if (/title="Textanfang in der GA-Suche"/.test(result)) {
      const next = result.replace(/<a href="https:\/\/rudolf-steiner-online\.de\/goto\.html#[^"]+"[^>]*title="Textanfang in der GA-Suche"[^>]*>[\s\S]*?<\/a>/, footer);
      if (next !== result) {
        result = next;
        count++;
      }
    } else {
      const lines = result.replace(/\s+$/, '').split('\n');
      let lastIdx = lines.length - 1;
      while (lastIdx >= 0 && !lines[lastIdx].trim()) lastIdx--;
      if (lastIdx >= 0) {
        const hasSep = /\n(?:---+|____+)\s*\n/.test(result);
        if (hasSep) {
          if (/\.\s*$/.test(lines[lastIdx])) {
            lines[lastIdx] = lines[lastIdx].replace(/\.\s*$/, footer + '.');
          } else {
            lines[lastIdx] = lines[lastIdx] + footer;
          }
        } else {
          lines.push('', footer);
        }
        result = lines.join('\n') + '\n';
        count++;
      }
    }
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

  if (!dryRun) {
    const leftover = [];
    for (const file of files) {
      if (!fs.existsSync(file)) continue;
      const text = fs.readFileSync(file, 'utf8');
      const hasQuote = /\(\[\[GA\s*\d/.test(text);
      const hasHtmlQuote = /goto\.html#[^"]*text=/.test(text) || /goto\.html#[^"]*lecture=/.test(text);
      const oldPdf = /akanthosakademie\.files\.wordpress\.com/.test(text);
      const oldMdGoto = /\[[^\]]*\]\(https:\/\/rudolf-steiner-online\.de\/goto\.html/.test(text);
      const oldWiki = /\(\[\[GA\s*\d+[a-zA-Z]?\]\],\s*\[\[GA/.test(text);
      const plainCite = /\(\[\[GA\s*\d+[a-zA-Z]?\]\],\s*S\./.test(text);
      if (oldPdf || oldMdGoto || oldWiki || plainCite || (hasQuote && !hasHtmlQuote)) {
        leftover.push(path.basename(file));
      }
    }
    if (leftover.length) {
      console.log(`\nNoch nicht vollständig: ${leftover.length}`);
      leftover.slice(0, 40).forEach(n => console.log('  -', n));
      if (leftover.length > 40) console.log(`  … und ${leftover.length - 40} weitere`);
    }
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
