/*
 * Abgleich der lokalen Vortragsbilder (Steiner_GA / GA-Ordner / assets) mit Cloudflare R2.
 *
 * Schema (wie tools/upload_images_to_r2.ps1):
 *   Bucket:  ga-pdf  (R2_BUCKET_NAME)
 *   Key:     images/<GA>/<dateiname>        z.B. images/GA293/img-11.png
 *   Pro Bildname nur EIN Format (Prioritaet: png > jpeg > jpg > webp > gif > svg)
 *
 * Verwendung:
 *   node tools/sync-images-to-r2.js                 # nur BERICHT (kein Upload)
 *   node tools/sync-images-to-r2.js --ga GA293,GA028  # nur diese Baende pruefen
 *   node tools/sync-images-to-r2.js --upload         # fehlende hochladen
 *   node tools/sync-images-to-r2.js --upload --ga GA293
 *
 * Liest R2-Zugangsdaten aus .env (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
 * R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME).
 */
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const {
  S3Client, ListObjectsV2Command, PutObjectCommand
} = require('@aws-sdk/client-s3');

const ROOT = path.join(__dirname, '..');
const SOURCE_DIR = path.join(ROOT, 'Steiner_GA');
const BUCKET = process.env.R2_BUCKET_NAME || 'ga-pdf';
const KEY_PREFIX = 'images/';

const CONTENT_TYPES = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml'
};
const EXT_PRIORITY = { '.png': 0, '.jpeg': 1, '.jpg': 2, '.webp': 3, '.gif': 4, '.svg': 5 };

// ---- CLI args ----
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
  let token = undefined;
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

function gaNumberFromFolder(name) {
  const m = name.match(/^(GA\d{1,3}[a-z]?)/i);
  return m ? m[1].toUpperCase() : null;
}

// Pro Bildname nur die beste Datei (Format-Prioritaet) — wie im ps1-Uploader.
function pickBestPerName(files) {
  const best = new Map();
  for (const f of files) {
    const ext = path.extname(f).toLowerCase();
    if (!(ext in CONTENT_TYPES)) continue;
    const base = path.basename(f, ext);
    const prio = ext in EXT_PRIORITY ? EXT_PRIORITY[ext] : 99;
    if (!best.has(base) || prio < best.get(base).prio) {
      best.set(base, { file: f, prio });
    }
  }
  return [...best.values()].map(v => v.file).sort();
}

function collectLocalImages() {
  const result = []; // { ga, absPath, fileName, key }
  if (!fs.existsSync(SOURCE_DIR)) {
    throw new Error(`Quellordner nicht gefunden: ${SOURCE_DIR}`);
  }
  const gaFolders = fs.readdirSync(SOURCE_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory() && /^GA\d{1,3}[a-z]?/i.test(d.name))
    .map(d => d.name).sort();

  for (const folder of gaFolders) {
    const ga = gaNumberFromFolder(folder);
    if (!ga) continue;
    if (gaFilter && !gaFilter.has(ga)) continue;
    const assetsDir = path.join(SOURCE_DIR, folder, 'assets');
    if (!fs.existsSync(assetsDir)) continue;
    let files;
    try { files = fs.readdirSync(assetsDir).filter(f => fs.statSync(path.join(assetsDir, f)).isFile()); }
    catch { continue; }
    const best = pickBestPerName(files);
    for (const fileName of best) {
      result.push({
        ga,
        absPath: path.join(assetsDir, fileName),
        fileName,
        key: `${KEY_PREFIX}${ga}/${fileName}`
      });
    }
  }
  return result;
}

async function main() {
  console.log(`Modus: ${DO_UPLOAD ? 'UPLOAD (fehlende hochladen)' : 'BERICHT (kein Upload)'}`);
  if (gaFilter) console.log(`Filter: ${[...gaFilter].join(', ')}`);
  console.log(`Bucket: ${BUCKET}, Prefix: ${KEY_PREFIX}\n`);

  const s3 = makeClient();
  const existing = await listExistingKeys(s3);
  const local = collectLocalImages();
  console.log(`[LOKAL] ${local.length} Bilddateien (nach Format-Dedup) in ${SOURCE_DIR}\n`);

  const missing = local.filter(it => !existing.has(it.key));

  // Bericht: fehlende pro GA
  const byGa = new Map();
  for (const it of missing) {
    if (!byGa.has(it.ga)) byGa.set(it.ga, []);
    byGa.get(it.ga).push(it.fileName);
  }
  const gasSorted = [...byGa.keys()].sort();
  console.log(`=== FEHLEN AUF R2: ${missing.length} Bilder in ${gasSorted.length} GA-Baenden ===`);
  for (const ga of gasSorted) {
    const list = byGa.get(ga);
    console.log(`  ${ga}: ${list.length} fehlend  (${list.slice(0, 5).join(', ')}${list.length > 5 ? ', …' : ''})`);
  }
  if (missing.length === 0) {
    console.log('\nAlles vorhanden — nichts zu tun.');
    return;
  }

  if (!DO_UPLOAD) {
    console.log('\n(Nur Bericht. Zum Hochladen: node tools/sync-images-to-r2.js --upload' + (gaFilter ? ' --ga ' + [...gaFilter].join(',') : '') + ')');
    return;
  }

  // Upload
  console.log(`\n=== UPLOAD START: ${missing.length} Bilder ===`);
  let ok = 0, err = 0;
  for (let i = 0; i < missing.length; i++) {
    const it = missing[i];
    const ext = path.extname(it.fileName).toLowerCase();
    const ct = CONTENT_TYPES[ext] || 'application/octet-stream';
    try {
      const body = fs.readFileSync(it.absPath);
      await s3.send(new PutObjectCommand({
        Bucket: BUCKET, Key: it.key, Body: body, ContentType: ct
      }));
      ok++;
      if (ok % 25 === 0 || i === missing.length - 1) {
        console.log(`  ${ok}/${missing.length} hochgeladen … (zuletzt ${it.key})`);
      }
    } catch (e) {
      err++;
      console.warn(`  FEHLER ${it.key}: ${e.message}`);
    }
  }
  console.log(`\n=== FERTIG: ${ok} hochgeladen, ${err} Fehler ===`);
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
