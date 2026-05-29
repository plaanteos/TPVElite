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

## Notas de seguridad

- No usar secreto de cliente en frontend.
- Revocar el secreto actual y rotar credenciales antes de produccion.
- Para bloqueo real de descarga, usar `INSTALLER_PATH` en servidor y no exponer el instalador por URL publica.
