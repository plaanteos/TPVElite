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

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';
const SESSION_SECRET = process.env.SESSION_SECRET || '';
const INSTALLER_PATH = process.env.INSTALLER_PATH || '';
const DOWNLOAD_TARGET_URL = process.env.DOWNLOAD_TARGET_URL || '';
const MP_ACCESS_TOKEN = process.env.MP_ACCESS_TOKEN || '';
const MP_WEBHOOK_SECRET = process.env.MP_WEBHOOK_SECRET || '';
const MP_CURRENCY_ID = process.env.MP_CURRENCY_ID || 'USD';
const APP_WEB_URL = process.env.APP_WEB_URL || 'https://tpv-elite.vercel.app';
const BACKEND_PUBLIC_URL = process.env.BACKEND_PUBLIC_URL || '';
const MP_NOTIFICATION_URL = process.env.MP_NOTIFICATION_URL || '';
const BILLING_DATA_PATH = process.env.BILLING_DATA_PATH || path.join(__dirname, 'data', 'billing_subscriptions.json');
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

const BILLING_PLANS = {
  basico: {
    code: 'basico',
    name: 'Plan Basico',
    price: 10,
    description: '1 sucursal, hasta 3 empleados y 3000 productos',
  },
  pro: {
    code: 'pro',
    name: 'Plan PRO',
    price: 20,
    description: 'Hasta 3 sucursales, 25 empleados y funciones avanzadas',
  },
  super: {
    code: 'super',
    name: 'Plan SUPER',
    price: 35,
    description: 'Sucursales, empleados y productos ilimitados',
  },
};

if (!GOOGLE_CLIENT_ID) {
  console.warn('GOOGLE_CLIENT_ID no está configurado.');
}
if (!SESSION_SECRET || SESSION_SECRET.length < 20) {
  console.warn('SESSION_SECRET debería tener al menos 20 caracteres.');
}
if (!ALLOWED_ORIGINS.length) {
  console.warn('ALLOWED_ORIGINS no está configurado. CORS bloqueará solicitudes de navegador por seguridad.');
}
if (!MP_ACCESS_TOKEN) {
  console.warn('MP_ACCESS_TOKEN no está configurado. El checkout de MercadoPago quedará deshabilitado.');
}

const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));

const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 10 * 60 * 1000);
const RATE_LIMIT_AUTH_MAX = Number(process.env.RATE_LIMIT_AUTH_MAX || 20);
const rateLimitStore = new Map();
let volatileBillingStore = [];

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

function requireSession(req, res, next) {
  try {
    const authHeader = String(req.headers.authorization || '');
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : '';
    if (!token) {
      return res.status(401).json({ ok: false, error: 'Token de sesión requerido' });
    }
    req.sessionUser = verifySession(token);
    return next();
  } catch {
    return res.status(401).json({ ok: false, error: 'Sesión inválida o vencida' });
  }
}

function readBillingStore() {
  try {
    if (!fs.existsSync(BILLING_DATA_PATH)) {
      return volatileBillingStore;
    }
    const raw = fs.readFileSync(BILLING_DATA_PATH, 'utf-8');
    const parsed = raw ? JSON.parse(raw) : [];
    const result = Array.isArray(parsed) ? parsed : [];
    volatileBillingStore = result;
    return result;
  } catch {
    return volatileBillingStore;
  }
}

function writeBillingStore(records) {
  volatileBillingStore = records;
  try {
    const dir = path.dirname(BILLING_DATA_PATH);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(BILLING_DATA_PATH, JSON.stringify(records, null, 2), 'utf-8');
  } catch {
    // En serverless (Vercel) el fs puede ser read-only. Se mantiene en memoria.
  }
}

function upsertBillingRecord(record) {
  const items = readBillingStore();
  const idx = items.findIndex((r) => r.externalReference === record.externalReference);
  if (idx >= 0) {
    items[idx] = { ...items[idx], ...record, updatedAt: new Date().toISOString() };
  } else {
    items.push({ ...record, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() });
  }
  writeBillingStore(items);
  return items;
}

function findLatestSubscriptionForUser(userSub) {
  const items = readBillingStore()
    .filter((r) => r.userSub === userSub)
    .sort((a, b) => String(b.updatedAt || '').localeCompare(String(a.updatedAt || '')));
  return items[0] || null;
}

async function mercadoPagoRequest(endpoint, options = {}) {
  if (!MP_ACCESS_TOKEN) {
    const err = new Error('MercadoPago no configurado');
    err.status = 503;
    throw err;
  }

  const response = await fetch(`https://api.mercadopago.com${endpoint}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${MP_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data?.message || `MercadoPago HTTP ${response.status}`);
    error.status = response.status;
    error.details = data;
    throw error;
  }
  return data;
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

app.get('/api/health', (_req, res) => {
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

app.get('/api/billing/plans', (_req, res) => {
  return res.json({ ok: true, plans: Object.values(BILLING_PLANS) });
});

app.get('/api/billing/subscription', requireSession, (req, res) => {
  const current = findLatestSubscriptionForUser(req.sessionUser.sub);
  return res.json({ ok: true, subscription: current });
});

app.post('/api/billing/checkout', requireSession, async (req, res) => {
  try {
    const planCode = String(req.body?.planCode || '').trim().toLowerCase();
    const plan = BILLING_PLANS[planCode];
    if (!plan) {
      return res.status(400).json({ ok: false, error: 'Plan inválido' });
    }

    if (!MP_ACCESS_TOKEN) {
      return res.status(503).json({ ok: false, error: 'MercadoPago no configurado en backend' });
    }

    const externalReference = `${req.sessionUser.sub}:${plan.code}:${Date.now()}`;
    const notificationUrl = MP_NOTIFICATION_URL || (BACKEND_PUBLIC_URL
      ? `${BACKEND_PUBLIC_URL.replace(/\/$/, '')}/api/billing/webhook`
      : undefined);

    const preferencePayload = {
      items: [
        {
          id: plan.code,
          title: `TPV Elite - ${plan.name}`,
          description: plan.description,
          quantity: 1,
          unit_price: Number(plan.price),
          currency_id: MP_CURRENCY_ID,
        },
      ],
      payer: {
        email: req.sessionUser.email,
        name: req.sessionUser.name || undefined,
      },
      external_reference: externalReference,
      back_urls: {
        success: `${APP_WEB_URL.replace(/\/$/, '')}/?billing=success&plan=${encodeURIComponent(plan.code)}`,
        pending: `${APP_WEB_URL.replace(/\/$/, '')}/?billing=pending&plan=${encodeURIComponent(plan.code)}`,
        failure: `${APP_WEB_URL.replace(/\/$/, '')}/?billing=failure&plan=${encodeURIComponent(plan.code)}`,
      },
      auto_return: 'approved',
      metadata: {
        tpv_user_sub: req.sessionUser.sub,
        tpv_user_email: req.sessionUser.email,
        tpv_plan_code: plan.code,
      },
      statement_descriptor: 'TPVELITE',
      notification_url: notificationUrl,
    };

    const preference = await mercadoPagoRequest('/checkout/preferences', {
      method: 'POST',
      body: JSON.stringify(preferencePayload),
    });

    upsertBillingRecord({
      externalReference,
      userSub: req.sessionUser.sub,
      userEmail: req.sessionUser.email,
      planCode: plan.code,
      planName: plan.name,
      amount: plan.price,
      currency: MP_CURRENCY_ID,
      status: 'pending_checkout',
      preferenceId: preference.id || null,
      checkoutUrl: preference.init_point || preference.sandbox_init_point || null,
      lastEvent: 'checkout_created',
    });

    return res.json({
      ok: true,
      plan,
      preferenceId: preference.id,
      checkoutUrl: preference.init_point || null,
      sandboxCheckoutUrl: preference.sandbox_init_point || null,
      externalReference,
    });
  } catch (error) {
    return res.status(error.status || 500).json({
      ok: false,
      error: error.message || 'No se pudo iniciar checkout de MercadoPago',
      details: error.details || null,
    });
  }
});

app.post('/api/billing/webhook', async (req, res) => {
  try {
    const topic = String(req.query.topic || req.query.type || req.body?.type || '').trim();
    const dataId = String(req.query['data.id'] || req.body?.data?.id || '').trim();

    if (MP_WEBHOOK_SECRET) {
      const incomingSecret = String(req.headers['x-webhook-secret'] || '').trim();
      if (!incomingSecret || incomingSecret !== MP_WEBHOOK_SECRET) {
        return res.status(401).json({ ok: false, error: 'Webhook secret inválido' });
      }
    }

    if (!topic || !dataId) {
      return res.status(400).json({ ok: false, error: 'Webhook inválido: topic/data.id requeridos' });
    }

    if (!MP_ACCESS_TOKEN) {
      return res.status(503).json({ ok: false, error: 'MercadoPago no configurado en backend' });
    }

    if (topic !== 'payment') {
      return res.json({ ok: true, ignored: true, topic });
    }

    const payment = await mercadoPagoRequest(`/v1/payments/${encodeURIComponent(dataId)}`);
    const externalReference = String(payment.external_reference || '').trim();
    if (!externalReference) {
      return res.status(422).json({ ok: false, error: 'Pago sin external_reference' });
    }

    const approved = String(payment.status || '').toLowerCase() === 'approved';
    const normalizedStatus = approved ? 'active' : `payment_${String(payment.status || 'unknown').toLowerCase()}`;

    upsertBillingRecord({
      externalReference,
      userSub: String(payment.metadata?.tpv_user_sub || '').trim() || undefined,
      userEmail: String(payment.metadata?.tpv_user_email || '').trim() || undefined,
      planCode: String(payment.metadata?.tpv_plan_code || '').trim() || undefined,
      status: normalizedStatus,
      paymentId: payment.id,
      paymentStatus: payment.status,
      paymentStatusDetail: payment.status_detail,
      paidAmount: payment.transaction_amount,
      currency: payment.currency_id || MP_CURRENCY_ID,
      lastEvent: 'payment_webhook',
    });

    return res.json({ ok: true, status: normalizedStatus });
  } catch (error) {
    return res.status(error.status || 500).json({
      ok: false,
      error: error.message || 'Error procesando webhook de MercadoPago',
      details: error.details || null,
    });
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

export default app;
