"""
Script de migración para actualizar los métodos de pago en la base de datos
Ejecutar una sola vez después de actualizar el código
"""

import sqlite3
import os
from pathlib import Path

# Ruta a la base de datos
DB_PATH = Path(__file__).parent / 'heladeria.db'

def migrate_payment_methods():
    """Migra la tabla ventas para soportar nuevos métodos de pago"""
    
    if not DB_PATH.exists():
        print(f"⚠️  Base de datos no encontrada en: {DB_PATH}")
        return
    
    print("🔄 Iniciando migración de métodos de pago...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla ventas existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ventas'
        """)
        
        if not cursor.fetchone():
            print("⚠️  Tabla 'ventas' no existe. No se requiere migración.")
            return
        
        # Crear tabla temporal con la nueva estructura
        print("📝 Creando tabla temporal...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_new (
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
        """)
        
        # Copiar datos, convirtiendo 'tarjeta' a 'tarjeta_credito'
        print("📋 Copiando datos...")
        cursor.execute("""
            INSERT INTO ventas_new 
            SELECT id, numero_venta, fecha, usuario_id, cliente_nombre,
                   subtotal, descuento, impuestos, total,
                   CASE 
                       WHEN metodo_pago = 'tarjeta' THEN 'tarjeta_credito'
                       ELSE metodo_pago 
                   END as metodo_pago,
                   estado, notas
            FROM ventas
        """)
        
        # Eliminar tabla antigua
        print("🗑️  Eliminando tabla antigua...")
        cursor.execute("DROP TABLE ventas")
        
        # Renombrar tabla nueva
        print("✏️  Renombrando tabla nueva...")
        cursor.execute("ALTER TABLE ventas_new RENAME TO ventas")
        
        # Confirmar cambios
        conn.commit()
        print("✅ Migración completada exitosamente!")
        print(f"   - Registros migrados: {cursor.rowcount}")
        print(f"   - Métodos de pago actualizados: efectivo, tarjeta_credito, tarjeta_debito, transferencia")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Error durante la migración: {e}")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN DE MÉTODOS DE PAGO")
    print("=" * 60)
    migrate_payment_methods()
    print("\n✨ Proceso finalizado")
    input("Presione Enter para salir...")
