"""
Script para actualizar la base de datos a la versión 2.0
"""
import sqlite3
import os

def update_database():
    db_path = os.path.join(os.path.dirname(__file__), 'heladeria.db')
    
    print(f"Actualizando base de datos: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # === ACTUALIZAR TABLA PRODUCTOS ===
        print("=== Actualizando tabla PRODUCTOS ===")
        cursor.execute("PRAGMA table_info(productos)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales: {columns}")
        
        # Agregar columnas faltantes a productos
        columns_to_add = {
            'descripcion': 'TEXT',
            'categoria': 'TEXT',
            'costo': 'REAL DEFAULT 0',
            'unidad_medida': 'TEXT DEFAULT "unidad"',
            'codigo_barras': 'TEXT',
            'activo': 'INTEGER DEFAULT 1',
            'fecha_creacion': 'TIMESTAMP',
            'fecha_modificacion': 'TIMESTAMP'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE productos ADD COLUMN {column_name} {column_type}"
                    print(f"Agregando columna: {column_name}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✓ Columna {column_name} agregada")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error al agregar {column_name}: {e}")
        
        # Verificar columnas finales
        cursor.execute("PRAGMA table_info(productos)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas finales: {final_columns}\n")
        
        # === ACTUALIZAR TABLA VENTAS ===
        print("=== Actualizando tabla VENTAS ===")
        cursor.execute("PRAGMA table_info(ventas)")
        ventas_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales: {ventas_columns}")
        
        # Agregar columnas faltantes a ventas
        ventas_columns_to_add = {
            'numero_venta': 'TEXT',
            'usuario_id': 'INTEGER DEFAULT 1',
            'estado': 'TEXT DEFAULT "completada"',
            'metodo_pago': 'TEXT DEFAULT "efectivo"',
            'cliente_nombre': 'TEXT',
            'notas': 'TEXT',
            'subtotal': 'REAL DEFAULT 0',
            'impuestos': 'REAL DEFAULT 0',
            'descuento': 'REAL DEFAULT 0'
        }
        
        for column_name, column_type in ventas_columns_to_add.items():
            if column_name not in ventas_columns:
                try:
                    sql = f"ALTER TABLE ventas ADD COLUMN {column_name} {column_type}"
                    print(f"Agregando columna: {column_name}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✓ Columna {column_name} agregada")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error al agregar {column_name}: {e}")
        
        # Verificar columnas finales
        cursor.execute("PRAGMA table_info(ventas)")
        ventas_final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas finales: {ventas_final_columns}\n")
        
        # === ACTUALIZAR TABLA DETALLES_VENTA ===
        print("=== Actualizando tabla DETALLES_VENTA ===")
        cursor.execute("PRAGMA table_info(detalles_venta)")
        detalles_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales: {detalles_columns}")
        
        # Agregar columnas faltantes a detalles_venta
        detalles_columns_to_add = {
            'subtotal': 'REAL DEFAULT 0',
            'descuento': 'REAL DEFAULT 0'
        }
        
        for column_name, column_type in detalles_columns_to_add.items():
            if column_name not in detalles_columns:
                try:
                    sql = f"ALTER TABLE detalles_venta ADD COLUMN {column_name} {column_type}"
                    print(f"Agregando columna: {column_name}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✓ Columna {column_name} agregada")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error al agregar {column_name}: {e}")
        
        # Verificar columnas finales
        cursor.execute("PRAGMA table_info(detalles_venta)")
        detalles_final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas finales: {detalles_final_columns}\n")
        
        # === ACTUALIZAR TABLA MOVIMIENTOS_INVENTARIO ===
        print("=== Actualizando tabla MOVIMIENTOS_INVENTARIO ===")
        cursor.execute("PRAGMA table_info(movimientos_inventario)")
        movimientos_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales: {movimientos_columns}")
        
        # Agregar columnas faltantes a movimientos_inventario
        movimientos_columns_to_add = {
            'stock_anterior': 'INTEGER DEFAULT 0',
            'stock_nuevo': 'INTEGER DEFAULT 0',
            'usuario_id': 'INTEGER DEFAULT 1',
            'referencia': 'TEXT'
        }
        
        for column_name, column_type in movimientos_columns_to_add.items():
            if column_name not in movimientos_columns:
                try:
                    sql = f"ALTER TABLE movimientos_inventario ADD COLUMN {column_name} {column_type}"
                    print(f"Agregando columna: {column_name}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✓ Columna {column_name} agregada")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error al agregar {column_name}: {e}")
        
        # Verificar columnas finales
        cursor.execute("PRAGMA table_info(movimientos_inventario)")
        movimientos_final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas finales: {movimientos_final_columns}\n")
        
        # === CREAR TABLA PROVEEDORES SI NO EXISTE ===
        print("=== Verificando tabla PROVEEDORES ===")
        cursor.execute("""
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
        conn.commit()
        print("✓ Tabla proveedores verificada\n")
        
        # === CREAR TABLA PEDIDOS SI NO EXISTE ===
        print("=== Verificando tabla PEDIDOS ===")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_pedido TEXT UNIQUE NOT NULL,
                proveedor_id INTEGER NOT NULL,
                fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_entrega_estimada DATE,
                fecha_entrega_real DATE,
                estado TEXT DEFAULT 'pendiente',
                subtotal REAL DEFAULT 0,
                impuestos REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notas TEXT,
                usuario_id INTEGER DEFAULT 1,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        conn.commit()
        print("✓ Tabla pedidos verificada\n")
        
        # === CREAR TABLA DETALLES_PEDIDO SI NO EXISTE ===
        print("=== Verificando tabla DETALLES_PEDIDO ===")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalles_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL DEFAULT 0,
                recibido INTEGER DEFAULT 0,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        conn.commit()
        print("✓ Tabla detalles_pedido verificada\n")
        
        print("✓ Base de datos actualizada correctamente")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()
