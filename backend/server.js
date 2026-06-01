import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import jwt from 'jsonwebtoken';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT || 8787);
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';
const SESSION_SECRET = process.env.SESSION_SECRET || '';
const INSTALLER_PATH = process.env.INSTALLER_PATH || '';
const DOWNLOAD_TARGET_URL = process.env.DOWNLOAD_TARGET_URL || '';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

if (!GOOGLE_CLIENT_ID) {
  console.warn('GOOGLE_CLIENT_ID no está configurado.');
}
if (!SESSION_SECRET || SESSION_SECRET.length < 20) {
  console.warn('SESSION_SECRET debería tener al menos 20 caracteres.');
}
if (!ALLOWED_ORIGINS.length) {
  console.warn('ALLOWED_ORIGINS no está configurado. CORS bloqueará solicitudes de navegador por seguridad.');
}

const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));

const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 10 * 60 * 1000);
const RATE_LIMIT_AUTH_MAX = Number(process.env.RATE_LIMIT_AUTH_MAX || 20);
const rateLimitStore = new Map();

function getClientIp(req) {
  const forwarded = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim();
  return forwarded || req.ip || req.socket?.remoteAddress || 'unknown';
}

function createIpRateLimiter(maxRequests, windowMs) {
  return (req, res, next) => {
    const ip = getClientIp(req);
    const now = Date.now();
    const key = `${req.path}:${ip}`;
    const current = rateLimitStore.get(key);

    if (!current || now > current.resetAt) {
      rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
      return next();
    }

    if (current.count >= maxRequests) {
      return res.status(429).json({ ok: false, error: 'Rate limit excedido, intente más tarde' });
    }

    current.count += 1;
    rateLimitStore.set(key, current);
    return next();
  };
}

app.use((req, res, next) => {
  const requestId = crypto.randomUUID();
  req.requestId = requestId;
  res.setHeader('X-Request-Id', requestId);
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  next();
});

app.use((req, res, next) => {
  const startedAt = Date.now();
  res.on('finish', () => {
    const payload = {
      level: 'info',
      requestId: req.requestId,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      durationMs: Date.now() - startedAt,
      ip: getClientIp(req),
      timestamp: new Date().toISOString(),
    };
    console.log(JSON.stringify(payload));
  });
  next();
});

app.use(cors({
  origin(origin, callback) {
    if (!origin) return callback(null, true);
    if (ALLOWED_ORIGINS.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('Origen no permitido por CORS'));
  },
  credentials: true,
}));

function signSession(user) {
  return jwt.sign(
    {
      sub: user.sub,
      email: user.email,
      name: user.name || '',
      picture: user.picture || '',
      type: 'session',
    },
    SESSION_SECRET,
    { expiresIn: '8h' }
  );
}

function verifySession(token) {
  const payload = jwt.verify(token, SESSION_SECRET);
  if (payload.type !== 'session') {
    throw new Error('Tipo de token inválido');
  }
  return payload;
}

function signDownloadToken(user, context) {
  return jwt.sign(
    {
      sub: user.sub,
      email: user.email,
      ctx: context || 'landing',
      type: 'download',
    },
    SESSION_SECRET,
    { expiresIn: '3m' }
  );
}

function verifyDownloadToken(token) {
  const payload = jwt.verify(token, SESSION_SECRET);
  if (payload.type !== 'download') {
    throw new Error('Token de descarga inválido');
  }
  return payload;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const error = new Error(`Error HTTP ${response.status}`);
    error.status = response.status;
    error.details = data;
    throw error;
  }

  return data;
}

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'tpvelite-auth-backend' });
});

app.post('/api/auth/google', createIpRateLimiter(RATE_LIMIT_AUTH_MAX, RATE_LIMIT_WINDOW_MS), async (req, res) => {
  try {
    const accessToken = String(req.body?.accessToken || '').trim();
    const context = String(req.body?.context || 'landing').trim();

    if (!accessToken) {
      return res.status(400).json({ ok: false, error: 'accessToken requerido' });
    }

    const tokenInfo = await fetchJson(
      `https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=${encodeURIComponent(accessToken)}`
    );

    if (!tokenInfo.aud || tokenInfo.aud !== GOOGLE_CLIENT_ID) {
      return res.status(401).json({ ok: false, error: 'Token de Google no válido para esta app' });
    }

    const profile = await fetchJson('https://www.googleapis.com/oauth2/v3/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!profile.email || profile.email_verified === false) {
      return res.status(401).json({ ok: false, error: 'Email de Google no verificado' });
    }

    const user = {
      sub: profile.sub || tokenInfo.sub || profile.email,
      email: profile.email,
      name: profile.name || '',
      picture: profile.picture || '',
    };

    const sessionToken = signSession(user);
    const downloadToken = signDownloadToken(user, context);

    return res.json({
      ok: true,
      user,
      sessionToken,
      downloadUrl: `/api/download?token=${encodeURIComponent(downloadToken)}`,
    });
  } catch (error) {
    return res.status(500).json({
      ok: false,
      error: 'No se pudo validar la sesión de Google',
      details: error?.details || error?.message || 'error-desconocido',
    });
  }
});

app.get('/api/download-link', createIpRateLimiter(RATE_LIMIT_AUTH_MAX, RATE_LIMIT_WINDOW_MS), (req, res) => {
  try {
    const authHeader = String(req.headers.authorization || '');
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
    const context = String(req.query.context || 'landing');

    if (!token) {
      return res.status(401).json({ ok: false, error: 'Token de sesión requerido' });
    }

    const session = verifySession(token);
    const downloadToken = signDownloadToken(session, context);

    return res.json({
      ok: true,
      downloadUrl: `/api/download?token=${encodeURIComponent(downloadToken)}`,
    });
  } catch {
    return res.status(401).json({ ok: false, error: 'Sesión inválida o vencida' });
  }
});

app.get('/api/download', (req, res) => {
  try {
    const token = String(req.query.token || '');
    if (!token) {
      return res.status(401).send('Token requerido');
    }

    verifyDownloadToken(token);

    if (INSTALLER_PATH) {
      const absolutePath = path.isAbsolute(INSTALLER_PATH)
        ? INSTALLER_PATH
        : path.resolve(__dirname, INSTALLER_PATH);

      if (!fs.existsSync(absolutePath)) {
        return res.status(404).send('Instalador no encontrado en el servidor');
      }

      return res.download(absolutePath, 'TPVElite_Setup.exe');
    }

    if (DOWNLOAD_TARGET_URL) {
      return res.redirect(302, DOWNLOAD_TARGET_URL);
    }

    return res.status(500).send('No hay fuente de descarga configurada');
  } catch {
    return res.status(401).send('Token inválido o vencido');
  }
});

app.use((error, _req, res, _next) => {
  if (String(error?.message || '').includes('CORS')) {
    return res.status(403).json({ ok: false, error: 'Origen no permitido' });
  }
  return res.status(500).json({ ok: false, error: 'Error interno' });
});

app.listen(PORT, () => {
  console.log(`Backend auth TPV Elite escuchando en http://localhost:${PORT}`);
});
