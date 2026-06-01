# Runbook Operativo - TPV Elite

## 1. Objetivo
Guía de operación para incidentes, recuperación, rollback y rotación de secretos.

## 2. Incidentes

### 2.1 Clasificación
- Sev1: sistema caído o ventas bloqueadas.
- Sev2: degradación fuerte (errores intermitentes, sincronización fallando).
- Sev3: errores menores sin impacto crítico.

### 2.2 Flujo de respuesta
1. Confirmar impacto y alcance.
2. Activar contención inmediata.
3. Identificar causa raíz.
4. Aplicar corrección temporal o definitiva.
5. Verificar recuperación y no-regresión.
6. Registrar postmortem.

## 3. Recuperación

### 3.1 Base de datos local
1. Detener aplicación.
2. Respaldar archivo actual (`heladeria.db`).
3. Restaurar último backup válido.
4. Iniciar aplicación y ejecutar checks de login/ventas/stock.

### 3.2 Backend auth/download
1. Verificar variables de entorno críticas:
   - `GOOGLE_CLIENT_ID`
   - `SESSION_SECRET`
   - `ALLOWED_ORIGINS`
2. Revisar `/health`.
3. Revisar logs estructurados por `requestId`.

## 4. Rollback
1. Identificar último commit estable en `main`.
2. Ejecutar rollback por deploy (sin reescritura destructiva de historial).
3. Revalidar smoke checks:
   - login
   - nueva venta
   - ajuste de stock
   - descarga instalador

## 5. Rotación de secretos

### 5.1 Turso
1. Revocar token comprometido en consola Turso.
2. Generar nuevo token.
3. Configurar `TPV_TURSO_TOKEN` en entorno.
4. Verificar que `app/config.json` no incluya token en claro.

### 5.2 Backend
1. Rotar `SESSION_SECRET`.
2. Validar expiración de sesiones antiguas.
3. Verificar CORS y endpoints críticos.

## 6. Checklist post-incidente
- [ ] Servicio restablecido.
- [ ] Datos consistentes.
- [ ] Alertas apagadas.
- [ ] Causa raíz documentada.
- [ ] Acción preventiva registrada.
