#!/usr/bin/env node
/**
 * Upload a local GA PDF to R2 as ga_pdf/ga{NNN}.pdf
 * Usage: node scripts/upload-ga-pdf-r2.js 335
 */
require('dotenv').config({ path: require('path').join(__dirname, '..', '.env'), override: true });

const fs = require('fs');
const path = require('path');
const r2 = require('../r2-client');

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
  const gaNumPadded = numMatch[1].padStart(3, '0') + (numMatch[2] || '').toLowerCase();
  const localPath = path.join(__dirname, '..', 'Steiner_GA_pdf', `ga${gaNumPadded}.pdf`);

  if (!fs.existsSync(localPath)) {
    console.error('Datei nicht gefunden:', localPath);
    process.exit(1);
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
