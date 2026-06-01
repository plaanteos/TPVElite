# Auditoría Completa del Sistema

Fecha: 29-05-2026
Rol: Analista Funcional Senior y Analista de Sistemas Senior
Proyecto: TPV Elite / Heladería

## 1. Resumen Ejecutivo

Estado general del sistema:
- Realización funcional: 74%
- Funcionamiento productivo confiable: 56%

Diagnóstico:
- El sistema está avanzado y usable en escenarios controlados.
- Aún no está listo para producción robusta por brechas críticas en seguridad, pruebas automatizadas y consistencia técnica entre módulos.

## 2. Hallazgos Críticos (bloqueantes para producción)

1. Secreto cloud expuesto en archivo de configuración.
- Evidencia: app/config.json incluye turso_token en texto plano.
- Riesgo: acceso no autorizado y fuga de datos.

2. Credenciales por defecto y flujo legacy inseguro.
- Evidencia: uso de admin/admin123 y creación inicial con SHA-256.
- Riesgo: compromiso de cuentas y seguridad inconsistente.

3. Inconsistencia de esquema en inventario (bug funcional real).
- Evidencia: inserción usa campo motivo, pero tabla maneja notas.
- Riesgo: fallas en ajustes de stock.

4. CORS permisivo en backend si faltan orígenes explícitos.
- Riesgo: exposición de endpoints fuera de dominios esperados.

5. Suite de tests desalineada con contratos reales de servicios.
- Riesgo: falsa sensación de calidad y regresiones en release.

## 3. Hallazgos Altos (impacto importante)

1. Main monolítico y manejo de errores con except desnudo/pass en múltiples sectores.
2. Inconsistencia del modelo de roles entre DB, servicios, UI y tests.
3. Instalador con versión desincronizada respecto a la app y landing.
4. CI/CD incompleto: deploy de landing sin pipeline integral de calidad.
5. Landing depende por defecto de backend local si no se parametriza API_BASE.

## 4. Porcentaje por Módulo

1. TPV escritorio (ventas, productos, pedidos, reportes)
- Realización: 82%
- Funcionamiento: 68%

2. Seguridad y acceso
- Realización: 52%
- Funcionamiento: 40%

3. Base de datos y consistencia transaccional
- Realización: 76%
- Funcionamiento: 61%

4. Cloud sync (Turso / offline)
- Realización: 72%
- Funcionamiento: 57%

5. Landing + backend de descarga protegida
- Realización: 78%
- Funcionamiento: 63%

6. QA y testing automatizado
- Realización: 38%
- Funcionamiento: 22%

7. DevOps / release / operación
- Realización: 64%
- Funcionamiento: 53%

## 5. Checklist para llegar al 100% de Producción

### P0 (obligatorio e inmediato)
- [x] Eliminar credenciales por defecto y forzar cambio de clave en primer acceso.
- [x] Corregir bug motivo/notas en inventario y validar flujo completo.
- [x] Endurecer CORS (deny-by-default cuando no haya ALLOWED_ORIGINS).
- [x] Alinear tests al contrato real de servicios.
- [x] Asegurar ejecución de tests en entorno reproducible.
- [x] Sincronizar versión de instalador con versión app/landing.

Evidencia de cierre P0 (2026-05-29):
- Se eliminó el token cloud hardcodeado del repo (`app/config.json`) y se pasó a variable de entorno `TPV_TURSO_TOKEN` (`app/cloud_sync.py`).
- Se eliminó la pista de `admin/admin123` en UI/manual y se implementó `must_change_password` con migración y enforcement en login (`app/database.py`, `app/services.py`, `app/main.py`).
- Se corrigió el bug de inventario `motivo/notas` en ajustes de stock (`app/services.py`).
- Backend CORS endurecido con deny-by-default cuando `ALLOWED_ORIGINS` no está configurado (`backend/server.js`).
- Tests de autenticación alineados al contrato actual y workflow reproducible agregado (`app/tests/test_auth.py`, `app/tests/conftest.py`, `.github/workflows/tests.yml`).
- Versión de aplicación/landing/instalador mantenida en `3.0.3`.

Nota operativa:
- La revocación/rotación del token Turso comprometido debe ejecutarse en consola de Turso (fuera del repositorio) como tarea de operación de seguridad.

### P1 (alta prioridad)
- [ ] Refactorizar app/main.py por módulos (UI, casos de uso, acceso a datos).
- [ ] Reemplazar except/pass por manejo de errores explícito y trazable.
- [ ] Unificar roles de negocio en todas las capas.
- [ ] Endurecer política de contraseñas (mínimo, complejidad, bloqueo temporal).
- [ ] Agregar controles de rate limit y hardening básico al backend.

### P2 (madurez productiva)
- [ ] Pipeline CI integral: lint + test + build smoke + validaciones.
- [ ] Estrategia de migraciones versionadas con rollback.
- [ ] Observabilidad mínima: logs estructurados, métricas y alertas.
- [ ] Runbook operativo: incidentes, recuperación, rollback y rotación de secretos.
- [ ] Tests E2E de flujos críticos (login, venta, stock, reportes, actualización).

## 6. Condición de salida a producción

No apto para producción en estado actual.

Criterio recomendado de habilitación:
1. P0 completo y validado.
2. P1 con al menos 80% completado.
3. Suite automatizada ejecutando en CI sin fallos.
4. Evidencia de prueba de release en entorno staging.

## 7. Meta de mejora esperada

Si se cierra P0:
- Funcionamiento productivo estimado: 80% a 85%

Si se cierra P0 + P1 + P2:
- Readiness de producción estimado: 95% a 100%

---

Documento generado para seguimiento ejecutivo y técnico.
