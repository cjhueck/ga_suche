/*
 * INHALTSGESTEUERTER Bild-Abgleich mit Cloudflare R2.
 *
 * Anders als tools/sync-images-to-r2.js (das den assets/-Ordner scannt) leitet
 * dieses Tool die benoetigten R2-Schluessel DIREKT aus den <img src="assets/...">
 * der Vortrags-/Buch-Inhalte ab. So entspricht der R2-Schluessel exakt der URL,
 * die der Browser anfragt (genau das, was backend.js -> absolutizeImageSrcInContent
 * erzeugt: images/<GA>/<dateiname-aus-content>).
 *
 * Hintergrund: Bei einigen Baenden (z.B. GA091) referenziert der Inhalt den LANGEN
 * Dateinamen (z.B. "Steiner, Rudolf GA 091, 2018 - ..._img-1.png"), waehrend im
 * direkten assets/-Ordner nur Kurznamen (img-1.png) liegen und die echte Datei im
 * Unterordner sogar eine andere Endung (.jpeg) hat. Der alte Scan-Uploader lud den
 * Kurznamen hoch -> online 404. Dieses Tool laedt die echte Datei unter dem vom
 * Inhalt referenzierten Namen hoch.
 *
 * Verwendung:
 *   node tools/sync-content-images-to-r2.js                # nur BERICHT (kein Upload)
 *   node tools/sync-content-images-to-r2.js --ga GA091     # nur diese Baende
 *   node tools/sync-content-images-to-r2.js --upload       # fehlende hochladen
 *   node tools/sync-content-images-to-r2.js --upload --ga GA091,GA092
 *
 * Liest R2-Zugangsdaten aus .env (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
 * R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME).
 */
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const { S3Client, ListObjectsV2Command, PutObjectCommand } = require('@aws-sdk/client-s3');

const ROOT = path.join(__dirname, '..');
const STEINER_GA_DIR = path.join(ROOT, 'Steiner_GA');
const CONTENT_DIRS = [
  path.join(ROOT, 'steiner-full-lectures'),
  path.join(ROOT, 'steiner-books')
];
const BUCKET = process.env.R2_BUCKET_NAME || 'ga-pdf';
const KEY_PREFIX = 'images/';

const CONTENT_TYPES = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml'
};
const ALT_EXTS = ['.jpeg', '.jpg', '.png', '.webp', '.gif', '.svg'];

// ---- CLI ----
const args = process.argv.slice(2);
const DO_UPLOAD = args.includes('--upload');
let gaFilter = null;
const gaIdx = args.indexOf('--ga');
if (gaIdx >= 0 && args[gaIdx + 1]) {
  gaFilter = new Set(args[gaIdx + 1].toUpperCase().split(',').map(s => s.trim()));
}

function makeClient() {
  const accountId = process.env.R2_ACCOUNT_ID;
  const accessKeyId = process.env.R2_ACCESS_KEY_ID;
  const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
  if (!accountId || !accessKeyId || !secretAccessKey) {
    throw new Error('R2-Zugangsdaten fehlen in .env (R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY)');
  }
  return new S3Client({
    region: 'auto',
    endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
    credentials: { accessKeyId, secretAccessKey }
  });
}

async function listExistingKeys(s3) {
  const keys = new Set();
  let token;
  let pages = 0;
  do {
    const resp = await s3.send(new ListObjectsV2Command({
      Bucket: BUCKET, Prefix: KEY_PREFIX, ContinuationToken: token, MaxKeys: 1000
    }));
    (resp.Contents || []).forEach(o => keys.add(o.Key));
    token = resp.IsTruncated ? resp.NextContinuationToken : undefined;
    pages++;
  } while (token);
  console.log(`[R2] ${keys.size} vorhandene Objekte unter "${KEY_PREFIX}" (in ${pages} Seite(n))`);
  return keys;
}

// --- GA-Ordner-Cache (Steiner_GA/<GA...>) ---
let gaFolderCache = null;
function findGaFolder(ga) {
  if (!gaFolderCache) {
    gaFolderCache = new Map();
    if (fs.existsSync(STEINER_GA_DIR)) {
      for (const name of fs.readdirSync(STEINER_GA_DIR)) {
        let stat;
        try { stat = fs.statSync(path.join(STEINER_GA_DIR, name)); } catch { continue; }
        if (!stat.isDirectory()) continue;
        const m = name.match(/^(GA\d{1,3}[a-z]?)/i);
        if (m && !gaFolderCache.has(m[1].toUpperCase())) {
          gaFolderCache.set(m[1].toUpperCase(), path.join(STEINER_GA_DIR, name));
        }
      }
    }
  }
  return gaFolderCache.get(ga.toUpperCase()) || null;
}

// Loest einen vom Inhalt referenzierten Dateinamen auf eine echte lokale Datei auf.
// Repliziert backend.js -> findImageInGAFolder: assets/ direkt, dann Unterordner-assets,
// mit Endungs-Fallback und Whitespace-Fuzzy-Match.
function normalizeSpaces(s) { return s.replace(/\s+/g, ' '); }

function resolveInDir(dir, name) {
  const full = path.join(dir, name);
  if (fs.existsSync(full)) return full;
  const ext = path.extname(name).toLowerCase();
  const base = ext ? name.slice(0, -ext.length) : name;
  for (const alt of ALT_EXTS) {
    if (alt === ext) continue;
    const altPath = path.join(dir, base + alt);
    if (fs.existsSync(altPath)) return altPath;
  }
  // Fuzzy (Whitespace-normalisiert)
  let dirFiles;
  try { dirFiles = fs.readdirSync(dir); } catch { return null; }
  const normName = normalizeSpaces(name);
  let hit = dirFiles.find(f => normalizeSpaces(f) === normName);
  if (hit) return path.join(dir, hit);
  const normBase = normalizeSpaces(base);
  for (const alt of ALT_EXTS) {
    if (alt === ext) continue;
    hit = dirFiles.find(f => normalizeSpaces(f) === normBase + alt);
    if (hit) return path.join(dir, hit);
  }
  return null;
}

function resolveLocalImage(ga, fileFromContent) {
  const gaFolder = findGaFolder(ga);
  if (!gaFolder) return null;
  // Nur den Dateinamen relativ zu assets/ betrachten
  let name = fileFromContent;
  const ai = name.lastIndexOf('/assets/');
  if (ai >= 0) name = name.substring(ai + 8);
  name = name.replace(/^assets\//i, '');

  const directAssets = path.join(gaFolder, 'assets');
  if (fs.existsSync(directAssets)) {
    const r = resolveInDir(directAssets, name);
    if (r) return r;
  }
  // Unterordner mit assets/
  try {
    for (const entry of fs.readdirSync(gaFolder, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.name === 'assets') continue;
      const subAssets = path.join(gaFolder, entry.name, 'assets');
      if (fs.existsSync(subAssets)) {
        const r = resolveInDir(subAssets, name);
        if (r) return r;
      }
    }
  } catch { /* ignore */ }
  return null;
}

// Sammelt alle vom Inhalt referenzierten (ga, file) Paare.
function collectReferencedImages() {
  const refs = new Map(); // key -> { ga, file, key }
  const IMG_RE = /<img\b[^>]*?\bsrc\s*=\s*(["'])\s*(?:\.?\/)?assets\/([^"']+?)\s*\1/gi;

  for (const dir of CONTENT_DIRS) {
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
    for (const fname of files) {
      let data;
      try {
        const raw = fs.readFileSync(path.join(dir, fname), 'utf8').replace(/^\uFEFF/, '');
        data = JSON.parse(raw);
      } catch (e) {
        console.warn(`  [WARN] ${fname} nicht lesbar/parsebar: ${e.message}`);
        continue;
      }
      // Moegliche Container: { lectures: [...] }, { books: [...] }, [...] oder Einzelobjekt
      const items = Array.isArray(data) ? data
        : Array.isArray(data.lectures) ? data.lectures
        : Array.isArray(data.books) ? data.books
        : [data];
      for (const item of items) {
        if (!item || typeof item !== 'object') continue;
        const ga = String(item.gaNumber || (item.ID ? String(item.ID).split('/')[0] : '') || '').toUpperCase();
        if (!/^GA\d{1,3}[a-z]?$/.test(ga)) continue;
        if (gaFilter && !gaFilter.has(ga)) continue;

        // Alle Textquellen des Items zusammensuchen
        const texts = [];
        if (typeof item.content === 'string') texts.push(item.content);
        if (typeof item.text === 'string') texts.push(item.text);
        if (Array.isArray(item.paragraphs)) {
          for (const p of item.paragraphs) {
            if (!p) continue;
            if (typeof p.content === 'string') texts.push(p.content);
            if (typeof p.text === 'string') texts.push(p.text);
          }
        }
        for (const t of texts) {
          if (t.indexOf('<img') === -1) continue;
          let m;
          IMG_RE.lastIndex = 0;
          while ((m = IMG_RE.exec(t)) !== null) {
            const file = m[2];
            if (file.includes('?')) continue;
            const key = `${KEY_PREFIX}${ga}/${file}`;
            if (!refs.has(key)) refs.set(key, { ga, file, key });
          }
        }
      }
    }
  }
  return [...refs.values()];
}

async function main() {
  console.log(`Modus: ${DO_UPLOAD ? 'UPLOAD (fehlende hochladen)' : 'BERICHT (kein Upload)'}`);
  if (gaFilter) console.log(`Filter: ${[...gaFilter].join(', ')}`);
  console.log(`Bucket: ${BUCKET}, Prefix: ${KEY_PREFIX}\n`);

  const s3 = makeClient();
  const existing = await listExistingKeys(s3);
  const referenced = collectReferencedImages();
  console.log(`[INHALT] ${referenced.length} eindeutige Bild-Referenzen in den Inhalten\n`);

  const missing = referenced.filter(it => !existing.has(it.key));

  // Aufloesung pruefen
  const resolvable = [];
  const unresolved = [];
  for (const it of missing) {
    const local = resolveLocalImage(it.ga, it.file);
    if (local) resolvable.push({ ...it, local });
    else unresolved.push(it);
  }

  // Bericht
  const byGa = new Map();
  for (const it of missing) {
    if (!byGa.has(it.ga)) byGa.set(it.ga, { total: 0, unresolved: 0 });
    byGa.get(it.ga).total++;
  }
  for (const it of unresolved) byGa.get(it.ga).unresolved++;

  const gasSorted = [...byGa.keys()].sort();
  console.log(`=== FEHLEN AUF R2 (vom Inhalt referenziert): ${missing.length} Bilder in ${gasSorted.length} GA-Baenden ===`);
  for (const ga of gasSorted) {
    const s = byGa.get(ga);
    const warn = s.unresolved ? `  ⚠ ${s.unresolved} lokal NICHT auffindbar` : '';
    console.log(`  ${ga}: ${s.total} fehlend${warn}`);
  }

  if (unresolved.length) {
    console.log(`\n⚠ ${unresolved.length} Referenzen ohne lokale Datei (Beispiele):`);
    unresolved.slice(0, 15).forEach(it => console.log(`   ${it.key}`));
  }

  if (missing.length === 0) {
    console.log('\nAlles vorhanden — nichts zu tun.');
    return;
  }

  if (!DO_UPLOAD) {
    console.log(`\n(Nur Bericht. Hochladbar: ${resolvable.length}. Zum Hochladen: node tools/sync-content-images-to-r2.js --upload` + (gaFilter ? ' --ga ' + [...gaFilter].join(',') : '') + ')');
    return;
  }

  console.log(`\n=== UPLOAD START: ${resolvable.length} Bilder ===`);
  let ok = 0, err = 0;
  for (let i = 0; i < resolvable.length; i++) {
    const it = resolvable[i];
    const realExt = path.extname(it.local).toLowerCase();
    const ct = CONTENT_TYPES[realExt] || 'application/octet-stream';
    try {
      const body = fs.readFileSync(it.local);
      await s3.send(new PutObjectCommand({ Bucket: BUCKET, Key: it.key, Body: body, ContentType: ct }));
      ok++;
      if (ok % 25 === 0 || i === resolvable.length - 1) {
        console.log(`  ${ok}/${resolvable.length} hochgeladen … (zuletzt ${it.key})`);
      }
    } catch (e) {
      err++;
      console.warn(`  FEHLER ${it.key}: ${e.message}`);
    }
  }
  console.log(`\n=== FERTIG: ${ok} hochgeladen, ${err} Fehler, ${unresolved.length} ohne lokale Datei ===`);
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
