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
import urllib.error
import urllib.request
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

COLUMNAS_CLOUD = {
    'usuarios': {
        'username', 'password_hash', 'nombre', 'apellido', 'email', 'rol',
        'activo', 'fecha_creacion', 'ultimo_acceso', 'intentos_fallidos',
    },
    'productos': {
        'nombre', 'descripcion', 'categoria', 'precio', 'costo', 'stock',
        'stock_minimo', 'unidad_medida', 'codigo_barras', 'imagen_url',
        'proveedor_id', 'activo', 'fecha_creacion', 'fecha_modificacion',
    },
    'ventas': {
        'numero_venta', 'fecha', 'usuario_id', 'cliente_nombre', 'subtotal',
        'descuento', 'impuestos', 'total', 'metodo_pago', 'estado', 'notas',
    },
    'detalles_venta': {
        'venta_id', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal',
    },
    'pedidos': {
        'numero_pedido', 'fecha', 'usuario_id', 'proveedor', 'subtotal',
        'impuestos', 'total', 'estado', 'fecha_entrega', 'notas',
    },
    'detalles_pedido': {
        'pedido_id', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal',
    },
    'movimientos_inventario': {
        'producto_id', 'tipo', 'cantidad', 'stock_anterior', 'stock_nuevo',
        'usuario_id', 'referencia', 'fecha', 'notas',
    },
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
            # Verificar conexión con el endpoint HTTP nativo de Turso.
            self._http_execute("SELECT 1")
            self._conectado = True
            logger.info(f"Turso HTTP conectado: {self._http_url()}")
        except Exception as exc:
            logger.error(f"Error al conectar con Turso: {exc}")

    def _http_url(self) -> str:
        url = self.turso_url
        if url.startswith('libsql://'):
            url = 'https://' + url[len('libsql://'):]
        return url.rstrip('/')

    def _sql_literal(self, value: Any) -> str:
        if value is None:
            return 'NULL'
        if isinstance(value, bool):
            return '1' if value else '0'
        if isinstance(value, (int, float)):
            return str(value)
        texto = str(value).replace("'", "''")
        return f"'{texto}'"

    def _render_sql(self, sql: str, args: Optional[List[Any]] = None) -> str:
        if not args:
            return sql

        partes = sql.split('?')
        if len(partes) - 1 != len(args):
            raise ValueError('Cantidad de argumentos no coincide con placeholders')

        sql_rendered = partes[0]
        for parte, arg in zip(partes[1:], args):
            sql_rendered += self._sql_literal(arg) + parte
        return sql_rendered

    def _http_execute(self, sql: str, args: Optional[List[Any]] = None) -> Dict[str, Any]:
        sql_rendered = self._render_sql(sql, args)
        payload: Dict[str, Any] = {
            'requests': [
                {
                    'type': 'execute',
                    'stmt': {
                        'sql': sql_rendered,
                    },
                }
            ]
        }

        request = urllib.request.Request(
            f"{self._http_url()}/v2/pipeline",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self.turso_token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        resultados = data.get('results') or []
        if not resultados:
            raise RuntimeError(f"Respuesta vacía de Turso para SQL: {sql[:80]}")

        primer_resultado = resultados[0]
        if primer_resultado.get('type') != 'ok':
            raise RuntimeError(f"Respuesta no OK de Turso: {primer_resultado}")

        response_body = primer_resultado.get('response', {})
        if not isinstance(response_body, dict):
            return {}
        return response_body.get('result', response_body)

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
                proveedor_id INTEGER,
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
                subtotal      REAL DEFAULT 0,
                impuestos     REAL DEFAULT 0,
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
                self._http_execute(ddl)
            except Exception as exc:
                logger.warning(f"DDL omitido (tabla ya existente o error): {exc}")

        migraciones = [
            "ALTER TABLE productos ADD COLUMN proveedor_id INTEGER",
            "ALTER TABLE pedidos ADD COLUMN subtotal REAL DEFAULT 0",
            "ALTER TABLE pedidos ADD COLUMN impuestos REAL DEFAULT 0",
        ]
        for sql in migraciones:
            try:
                self._http_execute(sql)
            except Exception as exc:
                logger.debug(f"Migración cloud omitida: {exc}")

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
        if not self._conectado:
            return
        tabla  = op['tabla']
        accion = op['accion']
        datos  = op['datos']

        try:
            if accion == 'upsert':
                columnas_permitidas = COLUMNAS_CLOUD.get(tabla, set())
                columnas     = ['tenant_id', 'local_id'] + [c for c in datos.keys() if c in columnas_permitidas]
                valores      = [datos['tenant_id'], datos['local_id']] + [datos[c] for c in datos.keys() if c in columnas_permitidas]
                placeholders = ', '.join('?' for _ in columnas)
                cols_sql     = ', '.join(columnas)
                sql = (
                    f"INSERT OR REPLACE INTO {tabla} ({cols_sql}) "
                    f"VALUES ({placeholders})"
                )
                self._http_execute(sql, valores)

            elif accion == 'delete':
                self._http_execute(
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
            rs = self._http_execute(
                f"SELECT * FROM {tabla} WHERE tenant_id = ?",
                [self.tenant_id],
            )
            columnas = rs.get('cols', [])
            filas = rs.get('rows', [])
            return [dict(zip([c.get('name') for c in columnas], row)) for row in filas]
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
