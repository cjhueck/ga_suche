const express = require('express');
const multer = require('multer');
const r2 = require('./r2-client');

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 200 * 1024 * 1024 } });

const ADMIN_EMAILS = ['christoph.hueck@gmx.net', 'admin@ga-suche.de'];

function createEditorRouter({ supabaseClient, editorEmails }) {
    const router = express.Router();

    function isLocalRequest(req) {
        const host = req.hostname || req.headers.host || '';
        return host === 'localhost' || host === '127.0.0.1' || host.startsWith('localhost:');
    }

    function isAdmin(user) {
        return user && ADMIN_EMAILS.includes(user.email);
    }

    function getUserPrefix(req) {
        if (isLocalRequest(req)) return '';
        if (!req.editorUser) return '';
        if (isAdmin(req.editorUser)) return '';
        return req.editorUser.id + '/';
    }

    function canAccessKey(req, key) {
        if (isLocalRequest(req)) return true;
        if (!req.editorUser) return false;
        if (isAdmin(req.editorUser)) return true;
        const sharedDir = r2.EDITOR_PREFIX + 'shared/';
        if (key.startsWith(sharedDir)) return true;
        const userDir = r2.EDITOR_PREFIX + req.editorUser.id + '/';
        return key.startsWith(userDir);
    }

    async function requireAuth(req, res, next) {
        if (isLocalRequest(req)) return next();
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'Authentifizierung erforderlich' });
        }
        try {
            const token = authHeader.split(' ')[1];
            const { data: { user }, error } = await supabaseClient.auth.getUser(token);
            if (error || !user) {
                return res.status(401).json({ error: 'Ungültiger Token' });
            }
            if (!editorEmails.includes(user.email) && user.user_metadata?.role !== 'editor') {
                return res.status(403).json({ error: 'Keine Editor-Berechtigung' });
            }
            req.editorUser = user;
            next();
        } catch (err) {
            res.status(401).json({ error: 'Auth-Fehler: ' + err.message });
        }
    }

    router.get('/status', (req, res) => {
        res.json({ r2Configured: r2.isConfigured() });
    });

    router.get('/whoami', requireAuth, (req, res) => {
        const user = req.editorUser;
        res.json({
            userId: user ? user.id : 'local',
            email: user ? user.email : 'local',
            isAdmin: isLocalRequest(req) || (user && isAdmin(user)),
            prefix: getUserPrefix(req)
        });
    });

    router.get('/files', requireAuth, async (req, res) => {
        try {
            const scope = req.query.scope || 'user';
            const subpath = req.query.prefix || '';

            if (scope === 'ga_pdf') {
                const rawPrefix = 'ga_pdf/' + subpath;
                const result = await r2.listFilesRaw(rawPrefix);
                return res.json(result);
            }

            let prefix;
            if (scope === 'shared') {
                prefix = 'shared/' + subpath;
            } else if (scope === 'all' && (isLocalRequest(req) || isAdmin(req.editorUser))) {
                prefix = subpath;
            } else {
                prefix = getUserPrefix(req) + subpath;
            }
            const result = await r2.listFiles(prefix);
            res.json(result);
        } catch (err) {
            console.error('[Editor] listFiles error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    router.get('/file/*', requireAuth, async (req, res) => {
        try {
            const key = req.params[0];
            if (!key || !(key.startsWith('editor/') || key.startsWith('ga_pdf/'))) {
                return res.status(400).json({ error: 'Ungültiger Dateipfad' });
            }
            if (!key.startsWith('ga_pdf/') && !canAccessKey(req, key)) {
                return res.status(403).json({ error: 'Kein Zugriff auf diese Datei' });
            }
            
            req.setTimeout(600000);
            res.setTimeout(600000);
            if (req.socket) req.socket.setTimeout(600000);
            
            const result = await r2.getFileStream(key);
            const sizeMB = result.contentLength ? (result.contentLength / 1024 / 1024).toFixed(1) : '?';
            console.log(`[Editor] Streaming ${key} (${sizeMB} MB)`);
            
            const contentType = result.contentType || (key.endsWith('.pdf') ? 'application/pdf' : 'text/markdown; charset=utf-8');
            res.setHeader('Content-Type', contentType);
            if (result.contentLength) res.setHeader('Content-Length', result.contentLength);
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.flushHeaders();
            
            result.stream.on('error', (err) => {
                console.error(`[Editor] Stream-Fehler für ${key}: ${err.message}`);
                if (!res.headersSent) res.status(500).json({ error: err.message });
                else res.destroy();
            });
            result.stream.pipe(res);
        } catch (err) {
            console.error('[Editor] getFile error:', err.message);
            if (err.name === 'NoSuchKey' || err.$metadata?.httpStatusCode === 404) {
                return res.status(404).json({ error: 'Datei nicht gefunden' });
            }
            if (!res.headersSent) res.status(500).json({ error: err.message });
        }
    });

    router.put('/file/*', requireAuth, express.raw({ type: '*/*', limit: '50mb' }), async (req, res) => {
        try {
            const key = req.params[0];
            if (!key || !key.startsWith('editor/')) {
                return res.status(400).json({ error: 'Ungültiger Dateipfad' });
            }
            if (!canAccessKey(req, key)) {
                return res.status(403).json({ error: 'Kein Zugriff auf diese Datei' });
            }
            const contentType = req.headers['content-type'] || 'text/markdown; charset=utf-8';
            await r2.putFile(key, req.body || Buffer.alloc(0), contentType);
            res.json({ success: true, key });
        } catch (err) {
            console.error('[Editor] putFile error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    router.post('/upload', requireAuth, upload.single('file'), async (req, res) => {
        try {
            if (!req.file) {
                return res.status(400).json({ error: 'Keine Datei hochgeladen' });
            }
            const scope = req.body.scope || 'user';
            let basePath;
            if (scope === 'shared') {
                basePath = 'shared/';
            } else {
                basePath = getUserPrefix(req);
            }
            const folder = req.body.folder || '';
            const filename = req.file.originalname;
            const key = r2.EDITOR_PREFIX + basePath + (folder ? folder.replace(/\/$/, '') + '/' : '') + filename;
            const contentType = req.file.mimetype || (filename.endsWith('.pdf') ? 'application/pdf' : 'text/markdown');
            await r2.putFile(key, req.file.buffer, contentType);
            res.json({ success: true, key, filename });
        } catch (err) {
            console.error('[Editor] upload error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    router.post('/copy', requireAuth, express.json(), async (req, res) => {
        try {
            const { sourceKey, targetKey } = req.body;
            if (!sourceKey || !targetKey) {
                return res.status(400).json({ error: 'sourceKey und targetKey erforderlich' });
            }
            if (!sourceKey.startsWith('ga_pdf/') && !sourceKey.startsWith('editor/')) {
                return res.status(400).json({ error: 'Ungültige Quelldatei' });
            }
            if (!targetKey.startsWith('editor/')) {
                return res.status(400).json({ error: 'Ziel muss im editor/-Bereich liegen' });
            }
            if (!canAccessKey(req, targetKey)) {
                return res.status(403).json({ error: 'Kein Schreibzugriff auf den Zielordner' });
            }
            const source = await r2.getFile(sourceKey);
            const contentType = source.contentType || (sourceKey.endsWith('.pdf') ? 'application/pdf' : 'text/markdown; charset=utf-8');
            await r2.putFile(targetKey, source.body, contentType);
            res.json({ success: true, targetKey });
        } catch (err) {
            console.error('[Editor] copy error:', err.message);
            if (err.name === 'NoSuchKey' || err.$metadata?.httpStatusCode === 404) {
                return res.status(404).json({ error: 'Quelldatei nicht gefunden' });
            }
            res.status(500).json({ error: err.message });
        }
    });

    router.delete('/file/*', requireAuth, async (req, res) => {
        try {
            const key = req.params[0];
            if (!key || !key.startsWith('editor/')) {
                return res.status(400).json({ error: 'Ungültiger Dateipfad' });
            }
            if (!canAccessKey(req, key)) {
                return res.status(403).json({ error: 'Kein Zugriff auf diese Datei' });
            }
            await r2.deleteFile(key);
            res.json({ success: true, key });
        } catch (err) {
            console.error('[Editor] deleteFile error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    return router;
}

module.exports = createEditorRouter;
