"""
Sistema TPV para Heladería - Módulo de Base de Datos
Autor: Jesus
Versión: 2.0.0
Descripción: Manejo profesional de la base de datos con optimizaciones y mejores prácticas
"""

import sqlite3
import os
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import threading

logger = logging.getLogger(__name__)

# Tablas que el cloud sync conoce
_TABLAS_CLOUD = {
    'usuarios', 'productos', 'ventas', 'detalles_venta',
    'pedidos', 'detalles_pedido', 'movimientos_inventario',
}

# Regex para extraer tabla y acción de un SQL de escritura
_RE_INSERT = re.compile(r'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)', re.IGNORECASE)
_RE_UPDATE = re.compile(r'UPDATE\s+(\w+)', re.IGNORECASE)
_RE_DELETE = re.compile(r'DELETE\s+FROM\s+(\w+)', re.IGNORECASE)


class DatabaseManager:
    """
    Gestor profesional de base de datos con pool de conexiones y transacciones seguras
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = 'heladeria.db'):
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = 'heladeria.db'):
        if not hasattr(self, 'initialized'):
            self.db_path = db_path
            self.initialized = True
            self._local = threading.local()
            self._create_tables()
            self._run_migrations()
            logger.info(f"Base de datos inicializada: {db_path}")
    
    def _run_migrations(self):
        """Aplica migraciones para compatibilidad con bases de datos existentes"""
        conn = self._get_connection()
        cursor = conn.cursor()
        migrations = [
            ("detalles_pedido", "recibido", "ALTER TABLE detalles_pedido ADD COLUMN recibido INTEGER DEFAULT 0"),
            ("pedidos", "subtotal", "ALTER TABLE pedidos ADD COLUMN subtotal REAL DEFAULT 0"),
            ("pedidos", "impuestos", "ALTER TABLE pedidos ADD COLUMN impuestos REAL DEFAULT 0"),
            ("productos", "proveedor_id", "ALTER TABLE productos ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id)"),
        ]
        for table, column, sql in migrations:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                try:
                    cursor.execute(sql)
                    conn.commit()
                    logger.info(f"Migración aplicada: {table}.{column}")
                except sqlite3.Error as e:
                    logger.warning(f"Migración omitida {table}.{column}: {e}")

        # Crear tabla proveedores si no existe (migración de tablas completas)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proveedores'")
        if not cursor.fetchone():
            try:
                cursor.execute('''
                    CREATE TABLE proveedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        contacto TEXT,
                        telefono TEXT,
                        email TEXT,
                        direccion TEXT,
                        notas TEXT,
                        activo INTEGER DEFAULT 1,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (activo IN (0, 1))
                    )
                ''')
                conn.commit()
                logger.info("Migración aplicada: tabla proveedores creada")
            except sqlite3.Error as e:
                logger.warning(f"Migración omitida tabla proveedores: {e}")


    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión thread-safe"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Habilitar foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection
    
    def _create_tables(self):
        """Crea las tablas de la base de datos con constraints y índices optimizados"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Tabla de usuarios con roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    apellido TEXT,
                    email TEXT UNIQUE,
                    rol TEXT NOT NULL DEFAULT 'cajero',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_acceso TIMESTAMP,
                    intentos_fallidos INTEGER DEFAULT 0,
                    CHECK (rol IN ('admin', 'supervisor', 'cajero')),
                    CHECK (activo IN (0, 1))
                )
            ''')
            
            # Tabla de productos mejorada
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    descripcion TEXT,
                    categoria TEXT NOT NULL DEFAULT 'general',
                    precio REAL NOT NULL CHECK(precio > 0),
                    costo REAL CHECK(costo >= 0),
                    stock INTEGER NOT NULL CHECK(stock >= 0),
                    stock_minimo INTEGER NOT NULL DEFAULT 5 CHECK(stock_minimo >= 0),
                    unidad_medida TEXT DEFAULT 'unidad',
                    codigo_barras TEXT UNIQUE,
                    imagen_url TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (activo IN (0, 1))
                )
            ''')
            
            # Tabla de ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_venta TEXT UNIQUE NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER NOT NULL,
                    cliente_nombre TEXT,
                    subtotal REAL NOT NULL CHECK(subtotal >= 0),
                    descuento REAL DEFAULT 0 CHECK(descuento >= 0),
                    impuestos REAL DEFAULT 0 CHECK(impuestos >= 0),
                    total REAL NOT NULL CHECK(total >= 0),
                    metodo_pago TEXT DEFAULT 'efectivo',
                    estado TEXT DEFAULT 'completada',
                    notas TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    CHECK (metodo_pago IN ('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'otro')),
                    CHECK (estado IN ('completada', 'cancelada', 'pendiente'))
                )
            ''')
            
            # Tabla de detalles de venta
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detalles_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unitario REAL NOT NULL CHECK(precio_unitario > 0),
                    subtotal REAL NOT NULL CHECK(subtotal > 0),
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''')
            
            # Tabla de pedidos a proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pedidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_pedido TEXT UNIQUE NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER NOT NULL,
                    proveedor TEXT,
                    total REAL NOT NULL CHECK(total >= 0),
                    estado TEXT DEFAULT 'pendiente',
                    fecha_entrega TIMESTAMP,
                    notas TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    CHECK (estado IN ('pendiente', 'recibido', 'cancelado'))
                )
            ''')
            
            # Tabla de detalles de pedido
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detalles_pedido (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unitario REAL NOT NULL CHECK(precio_unitario > 0),
                    subtotal REAL NOT NULL CHECK(subtotal > 0),
                    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''')
            
            # Tabla de movimientos de inventario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimientos_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    stock_anterior INTEGER NOT NULL,
                    stock_nuevo INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    referencia TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notas TEXT,
                    FOREIGN KEY (producto_id) REFERENCES productos(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    CHECK (tipo IN ('venta', 'compra', 'ajuste', 'devolucion', 'merma'))
                )
            ''')
            
            # Tabla de proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    contacto TEXT,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    notas TEXT,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (activo IN (0, 1))
                )
            ''')

            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sesiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    ip_address TEXT,
                    activa INTEGER DEFAULT 1,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    CHECK (activa IN (0, 1))
                )
            ''')
            
            # Crear índices para optimizar consultas
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
                "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)",
                "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)",
                "CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id)",
                "CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)",
                "CREATE INDEX IF NOT EXISTS idx_detalles_venta_venta ON detalles_venta(venta_id)",
                "CREATE INDEX IF NOT EXISTS idx_detalles_venta_producto ON detalles_venta(producto_id)",
                "CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha)",
                "CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado)",
                "CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_inventario(producto_id)",
                "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_inventario(fecha)",
                "CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones(usuario_id)",
                "CREATE INDEX IF NOT EXISTS idx_sesiones_activa ON sesiones(activa)"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            conn.commit()
            
            # Crear usuario admin por defecto si no existe
            self._create_default_admin()
            
            logger.info("Tablas e índices creados correctamente")
            
        except sqlite3.Error as e:
            logger.error(f"Error al crear tablas: {e}")
            conn.rollback()
            raise
    
    def _create_default_admin(self):
        """Crea un usuario administrador por defecto"""
        import hashlib
        
        username = "admin"
        password = "admin123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Verificar si ya existe el admin
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO usuarios (username, password_hash, nombre, apellido, rol, activo)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, password_hash, "Administrador", "Sistema", "admin", 1))
                conn.commit()
                logger.info("Usuario administrador creado correctamente")
        except sqlite3.Error as e:
            logger.error(f"Error al crear usuario admin: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """
        Ejecuta una consulta de modificación (INSERT, UPDATE, DELETE)

        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros de la consulta

        Returns:
            True si se ejecutó correctamente, False en caso contrario
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Query ejecutada: {query[:100]}...")
            self._sync_despues_de_write(query, last_id)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar query: {e}")
            conn.rollback()
            return False
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Ejecuta una consulta y retorna un solo resultado
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros de la consulta
            
        Returns:
            Una fila de resultado o None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            logger.debug(f"Query fetch_one ejecutada: {query[:100]}...")
            return result
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar fetch_one: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Ejecuta una consulta y retorna todos los resultados
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros de la consulta
            
        Returns:
            Lista de filas de resultado
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Query fetch_all ejecutada: {query[:100]}... ({len(results)} resultados)")
            return results
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar fetch_all: {e}")
            return []
    
    def execute_transaction(self, operations: List[Tuple[str, tuple]]) -> bool:
        """
        Ejecuta múltiples operaciones en una transacción

        Args:
            operations: Lista de tuplas (query, params)

        Returns:
            True si todas las operaciones se ejecutaron correctamente
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            last_ids = []
            for query, params in operations:
                cursor.execute(query, params)
                last_ids.append((query, cursor.lastrowid))
            conn.commit()
            logger.info(f"Transacción ejecutada correctamente ({len(operations)} operaciones)")
            for query, last_id in last_ids:
                self._sync_despues_de_write(query, last_id)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error en transacción: {e}")
            conn.rollback()
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Crea un backup de la base de datos
        
        Args:
            backup_path: Ruta donde guardar el backup
            
        Returns:
            True si el backup se creó correctamente
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup creado: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error al crear backup: {e}")
            return False
    
    def _sync_despues_de_write(self, query: str, last_id: Optional[int]):
        """
        Detecta la tabla afectada por la query y despacha la fila al cloud sync.
        Solo actúa si hay un cloud sync habilitado y la tabla está en la lista.
        """
        try:
            import cloud_sync
            sync = cloud_sync.obtener()
            if not sync or not sync.activo:
                return

            # Detectar tabla y acción
            for patron, accion in (
                (_RE_INSERT, 'upsert'),
                (_RE_UPDATE, 'upsert'),
                (_RE_DELETE, 'delete'),
            ):
                m = patron.search(query)
                if m:
                    tabla = m.group(1).lower()
                    if tabla not in _TABLAS_CLOUD:
                        return

                    if accion == 'delete':
                        # Para delete solo necesitamos el local_id
                        if last_id:
                            sync.push(tabla, 'delete', {'local_id': last_id})
                    elif last_id:
                        # Leer la fila recién escrita para enviarla completa
                        fila = self.fetch_one(
                            f"SELECT * FROM {tabla} WHERE id = ?", (last_id,)
                        )
                        if fila:
                            sync.push(tabla, 'upsert', dict(fila))
                    break
        except Exception as exc:
            logger.debug(f"Cloud sync dispatch omitido: {exc}")

    def close(self):
        """Cierra la conexión a la base de datos"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.info("Conexión a base de datos cerrada")
