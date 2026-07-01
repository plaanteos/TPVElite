# Backend minimo de autenticacion y descarga

Este servicio valida login con Google en servidor y habilita la descarga con token temporal.

## Requisitos

- Node.js 18+

## Configuracion

1. Copiar `.env.example` a `.env`.
2. Completar variables:

- `GOOGLE_CLIENT_ID`: Client ID web de Google.
- `SESSION_SECRET`: clave larga para firmar JWT de sesion.
- `ALLOWED_ORIGINS`: dominios permitidos por CORS.
- `INSTALLER_PATH`: ruta local al instalador en servidor (recomendado para produccion).
- `DOWNLOAD_TARGET_URL`: fallback de redireccion si no hay `INSTALLER_PATH`.
- `MP_ACCESS_TOKEN`: Access Token de MercadoPago (sandbox o produccion).
- `MP_WEBHOOK_SECRET`: secreto propio para proteger el endpoint webhook (header `x-webhook-secret`).
- `BACKEND_PUBLIC_URL`: URL publica del backend para construir webhook URL.
- `APP_WEB_URL`: URL publica de la landing (redirect post-checkout).
- `MP_NOTIFICATION_URL`: opcional para fijar URL de webhook exacta.
- `BILLING_DATA_PATH`: ruta de persistencia local del estado de suscripciones.

## Ejecutar

```bash
npm install
npm run dev
```

Servicio en `http://localhost:8787`.

## Endpoints

- `GET /health`
- `POST /api/auth/google` body: `{ accessToken, context }`
- `GET /api/download-link?context=...` con header `Authorization: Bearer <sessionToken>`
- `GET /api/download?token=...`

### Billing / MercadoPago

- `GET /api/billing/plans`
- `GET /api/billing/subscription` con header `Authorization: Bearer <sessionToken>`
- `POST /api/billing/checkout` con header `Authorization: Bearer <sessionToken>` y body `{ planCode }`
- `POST /api/billing/webhook` (MercadoPago)

`planCode` soportados: `basico`, `pro`, `super`.

## Flujo de cobro (estado actual)

1. Usuario inicia sesión con Google en landing.
2. Frontend llama `POST /api/billing/checkout` con plan elegido.
3. Backend crea preferencia de checkout en MercadoPago y devuelve `checkoutUrl`.
4. Usuario completa pago en MercadoPago.
5. MercadoPago notifica a `POST /api/billing/webhook`.
6. Backend actualiza estado de suscripción en persistencia local (`BILLING_DATA_PATH`).

## Estado de la implementación

- Implementado: creación de checkout, endpoint webhook, tracking de estado de suscripción.
- Pendiente para producción robusta: persistencia en DB real, firma oficial de webhook de MercadoPago, reconciliación recurrente y panel administrativo de billing.

## Notas de seguridad

- No usar secreto de cliente en frontend.
- Revocar el secreto actual y rotar credenciales antes de produccion.
- Para bloqueo real de descarga, usar `INSTALLER_PATH` en servidor y no exponer el instalador por URL publica.
