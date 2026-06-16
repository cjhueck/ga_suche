// Vectorize-Client für Cloudflare Vectorize V2 (REST API).
// Wird von Node.js (Render-Backend, lokales Backend, Setup-Skripte) verwendet.
// Voraussetzungen in .env:
//   CLOUDFLARE_ACCOUNT_ID    (gleiche ID wie R2_ACCOUNT_ID)
//   CLOUDFLARE_API_TOKEN     (Token mit Vectorize:Edit-Berechtigung)
//   VECTORIZE_INDEX_NAME     (Name des Index, z.B. "ga-paragraph-embeddings")

const API_BASE = 'https://api.cloudflare.com/client/v4';

function getConfig() {
  const accountId = process.env.CLOUDFLARE_ACCOUNT_ID || process.env.R2_ACCOUNT_ID;
  const apiToken = process.env.CLOUDFLARE_API_TOKEN;
  const indexName = process.env.VECTORIZE_INDEX_NAME || 'ga-paragraph-embeddings';
  return { accountId, apiToken, indexName };
}

function isConfigured() {
  const { accountId, apiToken } = getConfig();
  return !!(accountId && apiToken);
}

function getIndexName() {
  return getConfig().indexName;
}

function authHeaders(extra = {}) {
  const { apiToken } = getConfig();
  return {
    'Authorization': `Bearer ${apiToken}`,
    ...extra
  };
}

function indexesBaseUrl() {
  const { accountId } = getConfig();
  return `${API_BASE}/accounts/${accountId}/vectorize/v2/indexes`;
}

function indexUrl(subPath = '') {
  const { indexName } = getConfig();
  const sub = subPath ? (subPath.startsWith('/') ? subPath : '/' + subPath) : '';
  return `${indexesBaseUrl()}/${indexName}${sub}`;
}

async function readJsonOrThrow(response, context) {
  const text = await response.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { raw: text }; }
  if (!response.ok || body?.success === false) {
    const errMsgs = (body?.errors || []).map(e => `[${e.code}] ${e.message}`).join('; ') || text;
    const err = new Error(`Vectorize ${context} failed (HTTP ${response.status}): ${errMsgs}`);
    err.status = response.status;
    err.body = body;
    throw err;
  }
  return body;
}

// ==========================================================================
// INDEX-Verwaltung
// ==========================================================================

async function createIndex({ dimensions = 768, metric = 'cosine', description = '' } = {}) {
  if (!isConfigured()) throw new Error('Vectorize nicht konfiguriert (CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN fehlen)');
  const { indexName } = getConfig();
  const r = await fetch(indexesBaseUrl(), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      name: indexName,
      description,
      config: { dimensions, metric }
    })
  });
  return readJsonOrThrow(r, 'createIndex');
}

async function describeIndex() {
  const r = await fetch(indexUrl(), { headers: authHeaders() });
  return readJsonOrThrow(r, 'describeIndex');
}

async function getIndexInfo() {
  const r = await fetch(indexUrl('/info'), { headers: authHeaders() });
  return readJsonOrThrow(r, 'getIndexInfo');
}

// ==========================================================================
// METADATA-INDEX (für effiziente Filter wie gaBand=GA001)
// Limit: 10 Metadata-Indexe pro Vectorize-Index.
// ==========================================================================

async function createMetadataIndex(propertyName, indexType = 'string') {
  const r = await fetch(indexUrl('/metadata_index/create'), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ propertyName, indexType })
  });
  return readJsonOrThrow(r, `createMetadataIndex(${propertyName})`);
}

async function listMetadataIndexes() {
  const r = await fetch(indexUrl('/metadata_index/list'), { headers: authHeaders() });
  return readJsonOrThrow(r, 'listMetadataIndexes');
}

// ==========================================================================
// VECTOR-OPERATIONEN
// ==========================================================================

/**
 * Upsert via NDJSON. vectors = [{ id, values, metadata? }]
 * Cloudflare-Limits (V2): max 5000 Vektoren oder 5 MB Body pro Request.
 * Wir batchen automatisch.
 */
async function upsertVectors(vectors, { batchSize = 1000 } = {}) {
  if (!Array.isArray(vectors) || vectors.length === 0) {
    return { upserted: 0, mutationIds: [] };
  }
  const mutationIds = [];
  let upserted = 0;
  for (let i = 0; i < vectors.length; i += batchSize) {
    const batch = vectors.slice(i, i + batchSize);
    const ndjson = batch.map(v => JSON.stringify(v)).join('\n');
    const r = await fetch(indexUrl('/upsert'), {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/x-ndjson' }),
      body: ndjson
    });
    const body = await readJsonOrThrow(r, `upsertVectors batch ${i}-${i + batch.length}`);
    if (body?.result?.mutationId) mutationIds.push(body.result.mutationId);
    upserted += batch.length;
  }
  return { upserted, mutationIds };
}

/**
 * Insert (nicht überschreiben). vectors gleiche Form wie upsertVectors.
 */
async function insertVectors(vectors, { batchSize = 1000 } = {}) {
  if (!Array.isArray(vectors) || vectors.length === 0) {
    return { inserted: 0, mutationIds: [] };
  }
  const mutationIds = [];
  let inserted = 0;
  for (let i = 0; i < vectors.length; i += batchSize) {
    const batch = vectors.slice(i, i + batchSize);
    const ndjson = batch.map(v => JSON.stringify(v)).join('\n');
    const r = await fetch(indexUrl('/insert'), {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/x-ndjson' }),
      body: ndjson
    });
    const body = await readJsonOrThrow(r, `insertVectors batch ${i}-${i + batch.length}`);
    if (body?.result?.mutationId) mutationIds.push(body.result.mutationId);
    inserted += batch.length;
  }
  return { inserted, mutationIds };
}

/**
 * Nearest-Neighbor-Query.
 * @param {number[]} vector - Query-Embedding
 * @param {object} opts
 * @param {number} opts.topK - Anzahl Treffer (Default 30, max 100)
 * @param {object} opts.filter - z.B. { gaBand: "GA001" } oder { gaBand: { $in: ["GA001","GA002"] } }
 * @param {'none'|'indexed'|'all'} opts.returnMetadata - Default 'indexed'
 * @param {boolean} opts.returnValues - Default false
 */
async function queryNearest(vector, { topK = 30, filter = null, returnMetadata = 'indexed', returnValues = false } = {}) {
  const body = { vector, topK, returnMetadata, returnValues };
  if (filter && Object.keys(filter).length > 0) body.filter = filter;
  const r = await fetch(indexUrl('/query'), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body)
  });
  const result = await readJsonOrThrow(r, 'queryNearest');
  return result.result || { count: 0, matches: [] };
}

async function getByIds(ids) {
  const r = await fetch(indexUrl('/get_by_ids'), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ ids })
  });
  const result = await readJsonOrThrow(r, 'getByIds');
  return result.result || [];
}

async function deleteByIds(ids) {
  const r = await fetch(indexUrl('/delete_by_ids'), {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ ids })
  });
  return readJsonOrThrow(r, 'deleteByIds');
}

module.exports = {
  isConfigured,
  getIndexName,
  createIndex,
  describeIndex,
  getIndexInfo,
  createMetadataIndex,
  listMetadataIndexes,
  upsertVectors,
  insertVectors,
  queryNearest,
  getByIds,
  deleteByIds
};
