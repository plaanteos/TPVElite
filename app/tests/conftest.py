"""
Configuración de fixtures para los tests del sistema TPV
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime
import sqlite3

# Añadir el directorio padre al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import DatabaseManager
from services import AuthService, ProductoService, VentaService
from models import Usuario


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Crea una base de datos temporal para los tests"""
    db_dir = tmp_path_factory.mktemp("test_db")
    db_path = db_dir / "test_heladeria.db"
    return str(db_path)


@pytest.fixture(scope="function")
def db_manager(test_db_path):
    """
    Fixture que proporciona un DatabaseManager con BD temporal
    Se crea antes de cada test y se limpia después
    """
    # Crear base de datos temporal
    db = DatabaseManager(str(test_db_path))
    
    # Crear esquema de base de datos
    _create_test_schema(db)
    
    # Insertar datos de prueba
    _insert_test_data(db)
    
    yield db
    
    # Limpiar después del test
    db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def auth_service(db_manager):
    """Fixture que proporciona un AuthService configurado"""
    return AuthService(db_manager)


@pytest.fixture
def producto_service(db_manager):
    """Fixture que proporciona un ProductoService configurado"""
    return ProductoService(db_manager)


@pytest.fixture
def venta_service(db_manager):
    """Fixture que proporciona un VentaService configurado"""
    return VentaService(db_manager)


@pytest.fixture
def test_user(db_manager):
    """Fixture que proporciona un usuario de prueba"""
    return Usuario(
        id=1,
        username="admin",
        nombre="Administrador Test",
        email="admin@test.com",
        rol="admin",
        activo=True
    )


@pytest.fixture
def test_vendedor(db_manager):
    """Fixture que proporciona un usuario vendedor de prueba"""
    return Usuario(
        id=2,
        username="vendedor1",
        nombre="Vendedor Test",
        email="vendedor@test.com",
        rol="vendedor",
        activo=True
    )


def _create_test_schema(db: DatabaseManager):
    """Crea el esquema de prueba"""
    # Tabla usuarios
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT,
            email TEXT,
            rol TEXT NOT NULL DEFAULT 'vendedor',
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP,
            intentos_fallidos INTEGER DEFAULT 0
        )
    """)
    
    # Tabla productos
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            costo REAL,
            stock INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            codigo_barras TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla ventas
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_venta TEXT UNIQUE NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            impuestos REAL NOT NULL,
            total REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            estado TEXT DEFAULT 'completada',
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabla detalles_venta
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS detalles_venta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)
    
    # Tabla movimientos_inventario
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            usuario_id INTEGER,
            referencia TEXT,
            notas TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabla proveedores
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            notas TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla pedidos
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_pedido TEXT UNIQUE NOT NULL,
            proveedor_id INTEGER NOT NULL,
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_entrega_estimada DATE,
            subtotal REAL NOT NULL,
            impuestos REAL NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            notas TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    
    # Tabla detalles_pedido
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS detalles_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)


def _insert_test_data(db: DatabaseManager):
    """Inserta datos de prueba en la base de datos"""
    import bcrypt
    
    # Usuarios de prueba
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.execute_query("""
        INSERT INTO usuarios (username, password_hash, nombre, apellido, email, rol, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("admin", password_hash, "Administrador", "Test", "admin@test.com", "admin", 1))
    
    password_hash2 = bcrypt.hashpw("vendedor123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.execute_query("""
        INSERT INTO usuarios (username, password_hash, nombre, apellido, email, rol, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("vendedor1", password_hash2, "Vendedor", "Test", "vendedor@test.com", "vendedor", 1))
    
    # Productos de prueba
    db.execute_query("""
        INSERT INTO productos (nombre, categoria, precio, costo, stock, stock_minimo, codigo_barras)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Helado Chocolate', 'Helados', 5.50, 3.00, 100, 10, '1234567890123'))
    
    db.execute_query("""
        INSERT INTO productos (nombre, categoria, precio, costo, stock, stock_minimo, codigo_barras)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Helado Vainilla', 'Helados', 5.50, 3.00, 80, 10, '1234567890124'))
    
    db.execute_query("""
        INSERT INTO productos (nombre, categoria, precio, costo, stock, stock_minimo, codigo_barras)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Cono Waffle', 'Complementos', 1.50, 0.80, 200, 20, '1234567890125'))
    
    db.execute_query("""
        INSERT INTO productos (nombre, categoria, precio, costo, stock, stock_minimo, codigo_barras)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Refresco', 'Bebidas', 2.00, 1.00, 50, 10, '1234567890126'))
    
    db.execute_query("""
        INSERT INTO productos (nombre, categoria, precio, costo, stock, stock_minimo, codigo_barras)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Helado Fresa', 'Helados', 5.50, 3.00, 0, 10, '1234567890127'))
    
    # Proveedores de prueba
    db.execute_query("""
        INSERT INTO proveedores (nombre, contacto, telefono, email)
        VALUES (?, ?, ?, ?)
    """, ('Lácteos SA', 'Juan Pérez', '555-1234', 'contacto@lacteos.com'))
    
    db.execute_query("""
        INSERT INTO proveedores (nombre, contacto, telefono, email)
        VALUES (?, ?, ?, ?)
    """, ('Dulces Express', 'María García', '555-5678', 'ventas@dulces.com'))
