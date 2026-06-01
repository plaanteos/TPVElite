# Estrategia de Migraciones Versionadas

## 1. Objetivo
Estandarizar cambios de esquema con control de versiones y rollback operacional.

## 2. Convención de versiones
- Formato: `YYYYMMDD_HHMM_<descripcion>`
- Ejemplo: `20260601_1200_add_bloqueado_hasta_usuarios`

## 3. Estructura propuesta
- Carpeta: `app/migrations/`
- Archivos SQL o Python por migración.
- Tabla de control: `schema_migrations(version TEXT PRIMARY KEY, applied_at TIMESTAMP)`

## 4. Flujo de ejecución
1. Leer versiones aplicadas desde `schema_migrations`.
2. Ejecutar migraciones pendientes en orden.
3. Registrar versión aplicada.
4. Si falla, detener y dejar evidencia en logs.

## 5. Rollback
- Cada migración debe documentar estrategia reversible cuando sea viable.
- En cambios destructivos, exigir backup previo obligatorio.
- Rollback mínimo: restauración de backup consistente.

## 6. Validación obligatoria
- Smoke tests post-migración:
  - login
  - venta
  - ajuste de stock
- Verificar integridad de constraints y llaves foráneas.

## 7. Política
- No modificar esquema manualmente en producción.
- Todo cambio de DB debe pasar por migración versionada y PR.
