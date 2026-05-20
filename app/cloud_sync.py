"""
Sistema TPV Elite — Sincronización Cloud (Supabase)
Cada instalación tiene un tenant_id único que identifica al negocio.
Los datos se replican en Supabase de forma asíncrona sin bloquear la UI.
"""

import threading
import queue
import logging
import uuid
import os
import json
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Tablas que se sincronizan con la nube.
# 'sesiones' se excluye intencionalmente (son datos de sesión local).
TABLAS_SINCRONIZADAS = {
    'usuarios',
    'productos',
    'ventas',
    'detalles_venta',
    'pedidos',
    'detalles_pedido',
    'movimientos_inventario',
}

# Columna primaria de cada tabla (para upsert)
CLAVE_PRIMARIA = {
    'usuarios':               'id',
    'productos':              'id',
    'ventas':                 'id',
    'detalles_venta':         'id',
    'pedidos':                'id',
    'detalles_pedido':        'id',
    'movimientos_inventario': 'id',
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
    Servicio de replicación local → Supabase.

    Flujo de escritura (write-through con fallback):
      1. La app escribe en SQLite local (siempre).
      2. Se encola la operación de cloud.
      3. El worker en background intenta sincronizar.
      4. Si falla (sin internet, credenciales ausentes), el error se loguea
         pero la app continúa sin interrupciones.

    Flujo de pull (multi-dispositivo):
      - Al iniciar la app, se llama a pull_all() para descargar los datos
        del cloud que no existan aún en local.
    """

    def __init__(self, config: dict):
        self.habilitado: bool = config.get('habilitado', False)
        self.supabase_url: str = config.get('supabase_url', '').rstrip('/')
        self.supabase_key: str = config.get('supabase_anon_key', '')
        self.tenant_id: str = config.get('tenant_id', '')

        self._client = None
        self._cola: queue.Queue = queue.Queue()
        self._conectado = False

        if self.habilitado and self.supabase_url and self.supabase_key and self.tenant_id:
            self._iniciar_cliente()
            self._iniciar_worker()
        else:
            logger.info("Cloud sync deshabilitado o sin credenciales configuradas.")

    # ── Inicialización ──────────────────────────────────────────────────────

    def _iniciar_cliente(self):
        try:
            from supabase import create_client
            self._client = create_client(self.supabase_url, self.supabase_key)
            self._conectado = True
            logger.info("Supabase client inicializado correctamente.")
        except ImportError:
            logger.warning(
                "La librería 'supabase' no está instalada. "
                "Ejecutá: pip install supabase"
            )
        except Exception as exc:
            logger.error(f"Error al conectar con Supabase: {exc}")

    def _iniciar_worker(self):
        hilo = threading.Thread(target=self._worker_loop, name='cloud-sync', daemon=True)
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
                logger.error(f"Error inesperado en worker cloud: {exc}")

    def _procesar(self, op: dict):
        if not self._client:
            return
        tabla = op['tabla']
        accion = op['accion']
        datos = op['datos']

        try:
            if accion == 'upsert':
                datos['tenant_id'] = self.tenant_id
                self._client.table(tabla).upsert(datos, on_conflict='tenant_id,local_id').execute()
            elif accion == 'delete':
                (
                    self._client.table(tabla)
                    .delete()
                    .eq('tenant_id', self.tenant_id)
                    .eq('local_id', datos['local_id'])
                    .execute()
                )
        except Exception as exc:
            logger.error(f"Error sync cloud [{accion}] {tabla}: {exc}")

    # ── API pública ─────────────────────────────────────────────────────────

    def push(self, tabla: str, accion: str, datos: dict):
        """
        Encola una operación de sincronización.

        Args:
            tabla:  nombre de la tabla SQLite (ej. 'productos')
            accion: 'upsert' o 'delete'
            datos:  diccionario con los datos de la fila (debe incluir 'id' como local_id)
        """
        if not self._conectado or tabla not in TABLAS_SINCRONIZADAS:
            return

        payload = dict(datos)
        # Mapear la PK local a 'local_id' para Supabase
        pk = CLAVE_PRIMARIA.get(tabla, 'id')
        if pk in payload:
            payload['local_id'] = payload[pk]

        self._cola.put({'tabla': tabla, 'accion': accion, 'datos': payload})

    def pull_tabla(self, tabla: str) -> List[Dict]:
        """
        Descarga todos los registros de una tabla desde Supabase.
        Útil al iniciar la app en un segundo dispositivo.
        """
        if not self._conectado:
            return []
        try:
            resp = (
                self._client.table(tabla)
                .select('*')
                .eq('tenant_id', self.tenant_id)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.error(f"Error pull cloud {tabla}: {exc}")
            return []

    def pull_all(self, db_manager) -> int:
        """
        Sincroniza desde la nube hacia local al inicio de la app.
        Solo importa filas que NO existan aún en local (por local_id).

        Args:
            db_manager: instancia de DatabaseManager para escrituras locales

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
                    # Verificar si ya existe localmente
                    existente = db_manager.fetch_one(
                        f"SELECT id FROM {tabla} WHERE id = ?", (local_id,)
                    )
                    if not existente:
                        total += self._importar_fila(tabla, fila, db_manager)
            except Exception as exc:
                logger.error(f"Error al importar {tabla} desde cloud: {exc}")

        if total:
            logger.info(f"Cloud pull completado: {total} registros importados.")
        return total

    def _importar_fila(self, tabla: str, fila: dict, db_manager) -> int:
        """Intenta insertar una fila cloud en SQLite local. Devuelve 1 si exitoso."""
        try:
            # Quitar columnas propias de Supabase que no existen en SQLite
            excluir = {'tenant_id', 'local_id', 'synced_at'}
            datos_local = {k: v for k, v in fila.items() if k not in excluir}

            if not datos_local:
                return 0

            columnas = ', '.join(datos_local.keys())
            placeholders = ', '.join('?' for _ in datos_local)
            valores = tuple(datos_local.values())

            ok = db_manager.execute_query(
                f"INSERT OR IGNORE INTO {tabla} ({columnas}) VALUES ({placeholders})",
                valores
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
