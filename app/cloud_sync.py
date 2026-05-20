"""
Sistema TPV Elite — Sincronización Cloud con Turso (LibSQL)
Turso usa LibSQL, un fork de SQLite compatible al 100% con el mismo SQL.
Cada negocio se identifica con un tenant_id (UUID) almacenado en config.json.
Los datos se replican de forma asíncrona sin bloquear la UI.
"""

import threading
import queue
import logging
import uuid
import json
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Tablas que se sincronizan con Turso.
# 'sesiones' excluida intencionalmente — son datos de sesión local efímeros.
TABLAS_SINCRONIZADAS = {
    'usuarios',
    'productos',
    'ventas',
    'detalles_venta',
    'pedidos',
    'detalles_pedido',
    'movimientos_inventario',
}

_instancia: Optional['CloudSync'] = None
_lock = threading.Lock()


def inicializar(config_cloud: dict) -> 'CloudSync':
    """Crea e inicia la instancia singleton de CloudSync."""
    global _instancia
    with _lock:
        if _instancia is None:
            _instancia = CloudSync(config_cloud)
    return _instancia


def obtener() -> Optional['CloudSync']:
    """Devuelve la instancia activa, o None si no fue inicializada."""
    return _instancia


class CloudSync:
    """
    Servicio de replicación local SQLite → Turso (LibSQL).

    Flujo de escritura (write-through con fallback offline):
      1. La app escribe en SQLite local (siempre, sin depender del cloud).
      2. La fila escrita se encola para sincronización asíncrona.
      3. El worker en background la envía a Turso via HTTP.
      4. Si falla (sin internet, credenciales ausentes), se loguea el error
         pero la app continúa sin interrupciones.

    Flujo de pull (multi-dispositivo):
      - Al iniciar, pull_all() descarga desde Turso los registros
        que no existan aún en local (para el mismo tenant_id).
    """

    def __init__(self, config: dict):
        self.habilitado: bool = config.get('habilitado', False)
        self.turso_url: str   = config.get('turso_url', '').rstrip('/')
        self.turso_token: str = config.get('turso_token', '')
        self.tenant_id: str   = config.get('tenant_id', '')

        self._client = None
        self._cola: queue.Queue = queue.Queue()
        self._conectado = False

        if self.habilitado and self.turso_url and self.turso_token and self.tenant_id:
            self._iniciar_cliente()
            if self._conectado:
                self._asegurar_tablas()
                self._iniciar_worker()
        else:
            logger.info("Cloud sync deshabilitado o sin credenciales configuradas.")

    # ── Inicialización ──────────────────────────────────────────────────────

    def _iniciar_cliente(self):
        try:
            from libsql_client import create_client_sync
            self._client = create_client_sync(
                url=self.turso_url,
                auth_token=self.turso_token,
            )
            # Verificar conexión
            self._client.execute("SELECT 1")
            self._conectado = True
            logger.info(f"Turso client conectado: {self.turso_url}")
        except ImportError:
            logger.warning(
                "Librería 'libsql-client' no instalada. "
                "Ejecutá: pip install libsql-client"
            )
        except Exception as exc:
            logger.error(f"Error al conectar con Turso: {exc}")

    def _asegurar_tablas(self):
        """Crea las tablas en Turso si no existen — misma estructura SQLite + tenant_id."""
        ddls = [
            """CREATE TABLE IF NOT EXISTS usuarios (
                tenant_id TEXT NOT NULL,
                local_id  INTEGER NOT NULL,
                username  TEXT,
                password_hash TEXT,
                nombre    TEXT,
                apellido  TEXT,
                email     TEXT,
                rol       TEXT DEFAULT 'cajero',
                activo    INTEGER DEFAULT 1,
                fecha_creacion TEXT,
                ultimo_acceso  TEXT,
                intentos_fallidos INTEGER DEFAULT 0,
                synced_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS productos (
                tenant_id  TEXT NOT NULL,
                local_id   INTEGER NOT NULL,
                nombre     TEXT,
                descripcion TEXT,
                categoria  TEXT DEFAULT 'general',
                precio     REAL,
                costo      REAL,
                stock      INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 5,
                unidad_medida TEXT DEFAULT 'unidad',
                codigo_barras TEXT,
                imagen_url TEXT,
                activo     INTEGER DEFAULT 1,
                fecha_creacion TEXT,
                fecha_modificacion TEXT,
                synced_at  TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS ventas (
                tenant_id    TEXT NOT NULL,
                local_id     INTEGER NOT NULL,
                numero_venta TEXT,
                fecha        TEXT,
                usuario_id   INTEGER,
                cliente_nombre TEXT,
                subtotal     REAL DEFAULT 0,
                descuento    REAL DEFAULT 0,
                impuestos    REAL DEFAULT 0,
                total        REAL DEFAULT 0,
                metodo_pago  TEXT DEFAULT 'efectivo',
                estado       TEXT DEFAULT 'completada',
                notas        TEXT,
                synced_at    TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS detalles_venta (
                tenant_id       TEXT NOT NULL,
                local_id        INTEGER NOT NULL,
                venta_id        INTEGER,
                producto_id     INTEGER,
                cantidad        INTEGER,
                precio_unitario REAL,
                subtotal        REAL,
                synced_at       TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pedidos (
                tenant_id     TEXT NOT NULL,
                local_id      INTEGER NOT NULL,
                numero_pedido TEXT,
                fecha         TEXT,
                usuario_id    INTEGER,
                proveedor     TEXT,
                total         REAL DEFAULT 0,
                estado        TEXT DEFAULT 'pendiente',
                fecha_entrega TEXT,
                notas         TEXT,
                synced_at     TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS detalles_pedido (
                tenant_id       TEXT NOT NULL,
                local_id        INTEGER NOT NULL,
                pedido_id       INTEGER,
                producto_id     INTEGER,
                cantidad        INTEGER,
                precio_unitario REAL,
                subtotal        REAL,
                synced_at       TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
            """CREATE TABLE IF NOT EXISTS movimientos_inventario (
                tenant_id      TEXT NOT NULL,
                local_id       INTEGER NOT NULL,
                producto_id    INTEGER,
                tipo           TEXT,
                cantidad       INTEGER,
                stock_anterior INTEGER,
                stock_nuevo    INTEGER,
                usuario_id     INTEGER,
                referencia     TEXT,
                fecha          TEXT,
                notas          TEXT,
                synced_at      TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (tenant_id, local_id)
            )""",
        ]
        for ddl in ddls:
            try:
                self._client.execute(ddl)
            except Exception as exc:
                logger.warning(f"DDL omitido (tabla ya existente o error): {exc}")

    def _iniciar_worker(self):
        hilo = threading.Thread(
            target=self._worker_loop,
            name='turso-sync',
            daemon=True,
        )
        hilo.start()

    # ── Worker de sincronización ────────────────────────────────────────────

    def _worker_loop(self):
        while True:
            try:
                operacion = self._cola.get(timeout=2)
                if operacion is None:
                    break
                self._procesar(operacion)
                self._cola.task_done()
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error(f"Error inesperado en worker Turso: {exc}")

    def _procesar(self, op: dict):
        if not self._client:
            return
        tabla  = op['tabla']
        accion = op['accion']
        datos  = op['datos']

        try:
            if accion == 'upsert':
                columnas     = list(datos.keys())
                valores      = [datos[c] for c in columnas]
                placeholders = ', '.join('?' for _ in columnas)
                cols_sql     = ', '.join(columnas)
                sql = (
                    f"INSERT OR REPLACE INTO {tabla} ({cols_sql}) "
                    f"VALUES ({placeholders})"
                )
                self._client.execute(sql, valores)

            elif accion == 'delete':
                self._client.execute(
                    f"DELETE FROM {tabla} WHERE tenant_id = ? AND local_id = ?",
                    [self.tenant_id, datos['local_id']],
                )
        except Exception as exc:
            logger.error(f"Error sync Turso [{accion}] {tabla}: {exc}")

    # ── API pública ─────────────────────────────────────────────────────────

    def push(self, tabla: str, accion: str, datos: dict):
        """
        Encola una fila para sincronización asíncrona.

        Args:
            tabla:  nombre de la tabla (ej. 'productos')
            accion: 'upsert' o 'delete'
            datos:  diccionario con los datos de la fila (debe incluir 'id')
        """
        if not self._conectado or tabla not in TABLAS_SINCRONIZADAS:
            return

        payload  = dict(datos)
        local_id = payload.get('id')
        if local_id is None:
            return
        payload['local_id']  = local_id
        payload['tenant_id'] = self.tenant_id

        self._cola.put({'tabla': tabla, 'accion': accion, 'datos': payload})

    def pull_tabla(self, tabla: str) -> List[Dict]:
        """Descarga todos los registros del tenant desde Turso."""
        if not self._conectado:
            return []
        try:
            rs = self._client.execute(
                f"SELECT * FROM {tabla} WHERE tenant_id = ?",
                [self.tenant_id],
            )
            return [dict(zip(rs.columns, row)) for row in rs.rows]
        except Exception as exc:
            logger.error(f"Error pull Turso {tabla}: {exc}")
            return []

    def pull_all(self, db_manager) -> int:
        """
        Sincroniza datos desde Turso hacia SQLite local al inicio.
        Solo importa filas que NO existan aún en local (por local_id).

        Returns:
            cantidad de filas importadas
        """
        if not self._conectado:
            return 0

        total = 0
        for tabla in TABLAS_SINCRONIZADAS:
            try:
                filas = self.pull_tabla(tabla)
                for fila in filas:
                    local_id = fila.get('local_id')
                    if not local_id:
                        continue
                    existente = db_manager.fetch_one(
                        f"SELECT id FROM {tabla} WHERE id = ?", (local_id,)
                    )
                    if not existente:
                        total += self._importar_fila(tabla, fila, db_manager)
            except Exception as exc:
                logger.error(f"Error al importar {tabla} desde Turso: {exc}")

        if total:
            logger.info(f"Pull Turso completado: {total} registros importados.")
        return total

    def _importar_fila(self, tabla: str, fila: dict, db_manager) -> int:
        """Inserta una fila de Turso en SQLite local. Devuelve 1 si exitoso."""
        try:
            excluir     = {'tenant_id', 'local_id', 'synced_at'}
            datos_local = {k: v for k, v in fila.items() if k not in excluir}
            if not datos_local:
                return 0

            columnas     = ', '.join(datos_local.keys())
            placeholders = ', '.join('?' for _ in datos_local)
            valores      = tuple(datos_local.values())

            ok = db_manager.execute_query(
                f"INSERT OR IGNORE INTO {tabla} ({columnas}) VALUES ({placeholders})",
                valores,
            )
            return 1 if ok else 0
        except Exception as exc:
            logger.warning(f"No se pudo importar fila de {tabla}: {exc}")
            return 0

    @property
    def activo(self) -> bool:
        return self._conectado


# ── Utilidades de configuración ─────────────────────────────────────────────

def generar_tenant_id() -> str:
    """Genera un UUID v4 para identificar al negocio de forma única."""
    return str(uuid.uuid4())


def config_desde_json(ruta_config: str) -> dict:
    """Lee la sección 'cloud' de config.json. Devuelve {} si no existe."""
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos.get('cloud', {})
    except Exception:
        return {}


def guardar_tenant_id(ruta_config: str, tenant_id: str):
    """Persiste el tenant_id en config.json."""
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        if 'cloud' not in datos:
            datos['cloud'] = {}
        datos['cloud']['tenant_id'] = tenant_id
        with open(ruta_config, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as exc:
        logger.error(f"No se pudo guardar tenant_id en config: {exc}")
