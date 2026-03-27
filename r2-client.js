const { S3Client, ListObjectsV2Command, GetObjectCommand, PutObjectCommand, DeleteObjectCommand } = require('@aws-sdk/client-s3');

const EDITOR_PREFIX = 'editor/';

let s3 = null;

function getClient() {
    if (s3) return s3;
    const accountId = process.env.R2_ACCOUNT_ID;
    const accessKeyId = process.env.R2_ACCESS_KEY_ID;
    const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
    if (!accountId || !accessKeyId || !secretAccessKey) {
        return null;
    }
    s3 = new S3Client({
        region: 'auto',
        endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
        credentials: { accessKeyId, secretAccessKey }
    });
    return s3;
}

function getBucket() {
    return process.env.R2_BUCKET_NAME || 'ga-pdf';
}

async function listFiles(prefix) {
    const client = getClient();
    if (!client) throw new Error('R2 nicht konfiguriert');
    const fullPrefix = EDITOR_PREFIX + (prefix || '');
    const result = await client.send(new ListObjectsV2Command({
        Bucket: getBucket(),
        Prefix: fullPrefix,
        Delimiter: '/'
    }));

    const folders = (result.CommonPrefixes || []).map(p => {
        const name = p.Prefix.replace(EDITOR_PREFIX, '').replace(/\/$/, '');
        return { name, type: 'folder', key: p.Prefix };
    });

    const files = (result.Contents || []).filter(obj => obj.Key !== fullPrefix).map(obj => ({
        name: obj.Key.split('/').pop(),
        type: obj.Key.endsWith('.pdf') ? 'pdf' : 'md',
        key: obj.Key,
        size: obj.Size,
        lastModified: obj.LastModified
    }));

    return { folders, files };
}

async function getFile(key) {
    const client = getClient();
    if (!client) throw new Error('R2 nicht konfiguriert');
    const result = await client.send(new GetObjectCommand({
        Bucket: getBucket(),
        Key: key
    }));
    const byteArray = await result.Body.transformToByteArray();
    return {
        body: Buffer.from(byteArray),
        contentType: result.ContentType,
        size: byteArray.length
    };
}

async function putFile(key, body, contentType) {
    const client = getClient();
    if (!client) throw new Error('R2 nicht konfiguriert');
    await client.send(new PutObjectCommand({
        Bucket: getBucket(),
        Key: key,
        Body: body,
        ContentType: contentType
    }));
    return { key };
}

async function deleteFile(key) {
    const client = getClient();
    if (!client) throw new Error('R2 nicht konfiguriert');
    await client.send(new DeleteObjectCommand({
        Bucket: getBucket(),
        Key: key
    }));
    return { key };
}

function isConfigured() {
    return !!(process.env.R2_ACCOUNT_ID && process.env.R2_ACCESS_KEY_ID && process.env.R2_SECRET_ACCESS_KEY);
}

async function listFilesRaw(rawPrefix) {
    const client = getClient();
    if (!client) throw new Error('R2 nicht konfiguriert');
    const result = await client.send(new ListObjectsV2Command({
        Bucket: getBucket(),
        Prefix: rawPrefix,
        Delimiter: '/'
    }));

    const folders = (result.CommonPrefixes || []).map(p => {
        const name = p.Prefix.slice(rawPrefix.length).replace(/\/$/, '');
        return { name, type: 'folder', key: p.Prefix };
    });

    const files = (result.Contents || []).filter(obj => obj.Key !== rawPrefix).map(obj => ({
        name: obj.Key.split('/').pop(),
        type: obj.Key.endsWith('.pdf') ? 'pdf' : 'md',
        key: obj.Key,
        size: obj.Size,
        lastModified: obj.LastModified
    }));

    return { folders, files };
}

module.exports = { listFiles, listFilesRaw, getFile, putFile, deleteFile, isConfigured, EDITOR_PREFIX };
