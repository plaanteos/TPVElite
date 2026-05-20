"""
Script simple para actualizar la contraseña del admin a bcrypt
"""

import sqlite3
import os
import sys

# Agregar el directorio actual al path para importar models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Usuario

def update_admin_password():
    """Actualiza la contraseña del admin a bcrypt"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'heladeria.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Actualización de Contraseña Admin a bcrypt ===\n")
    
    # Generar hash bcrypt para admin123
    new_hash = Usuario.hash_password('admin123')
    
    # Actualizar en base de datos
    cursor.execute(
        "UPDATE usuarios SET password_hash = ? WHERE username = 'admin'",
        (new_hash,)
    )
    conn.commit()
    
    # Verificar
    cursor.execute("SELECT username, password_hash FROM usuarios WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        print(f"✓ Usuario: {result[0]}")
        print(f"✓ Nuevo hash bcrypt: {result[1][:30]}...")
        print(f"✓ Contraseña sigue siendo: admin123")
        print(f"\n✓ Migración completada exitosamente")
    else:
        print("✗ Error: Usuario admin no encontrado")
    
    conn.close()

if __name__ == "__main__":
    update_admin_password()
