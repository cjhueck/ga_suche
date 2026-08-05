#!/usr/bin/env node
/**
 * Upload a local GA PDF to R2 as ga_pdf/ga{NNN}.pdf
 * Sucht zuerst Steiner_GA_pdf/ga{NNN}.pdf; fehlt die Kurzform, wird der Langname
 * (z.B. "Steiner, Rudolf GA 148 …pdf") genommen und als ga{NNN}.pdf abgelegt.
 * Usage: node scripts/upload-ga-pdf-r2.js 335
 */
require('dotenv').config({ path: require('path').join(__dirname, '..', '.env'), override: true });

const fs = require('fs');
const path = require('path');
const r2 = require('../r2-client');

function findLongNamePdf(pdfDir, numberPart, letterPart) {
  if (!fs.existsSync(pdfDir)) return null;
  const gaPattern = new RegExp(`GA\\s*0*${numberPart}${letterPart}[,\\s\\-]`, 'i');
  const files = fs.readdirSync(pdfDir).filter((f) => f.toLowerCase().endsWith('.pdf'));
  const match = files.find((f) => gaPattern.test(f) && !/-bilder\.pdf$/i.test(f));
  return match ? path.join(pdfDir, match) : null;
}

async function main() {
  const gaArg = process.argv[2];
  if (!gaArg || !/^\d{1,3}[a-z]?$/i.test(gaArg)) {
    console.error('Usage: node scripts/upload-ga-pdf-r2.js 335');
    process.exit(1);
  }

  if (!r2.isConfigured()) {
    console.error('R2 nicht konfiguriert (.env: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME)');
    process.exit(1);
  }

  const numMatch = gaArg.match(/^(\d+)([a-z]?)$/i);
  const numberPart = numMatch[1];
  const letterPart = (numMatch[2] || '').toLowerCase();
  const gaNumPadded = numberPart.padStart(3, '0') + letterPart;
  const pdfDir = path.join(__dirname, '..', 'Steiner_GA_pdf');
  const shortPath = path.join(pdfDir, `ga${gaNumPadded}.pdf`);

  let localPath = shortPath;
  if (!fs.existsSync(shortPath)) {
    const longPath = findLongNamePdf(pdfDir, numberPart, letterPart);
    if (!longPath) {
      console.error('Datei nicht gefunden:', shortPath);
      console.error('(auch kein Langname mit GA', numberPart + letterPart, 'in', pdfDir + ')');
      process.exit(1);
    }
    fs.copyFileSync(longPath, shortPath);
    console.log(`Kurzname angelegt: ${path.basename(longPath)} -> ga${gaNumPadded}.pdf`);
    localPath = shortPath;
  }

  const body = fs.readFileSync(localPath);
  const key = `ga_pdf/ga${gaNumPadded}.pdf`;
  await r2.putFile(key, body, 'application/pdf');
  console.log(`OK: ${localPath} (${body.length} bytes) -> R2 ${key}`);
}

main().catch((err) => {
  console.error('Fehler:', err.message);
  process.exit(1);
});
