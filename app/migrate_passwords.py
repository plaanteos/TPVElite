"""
Script para migrar contraseñas SHA-256 a bcrypt
Ejecutar una sola vez para actualizar las contraseñas existentes
"""

import sqlite3
import os
from models import Usuario

def migrate_passwords():
    """Migra todas las contraseñas SHA-256 a bcrypt"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'heladeria.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Migración de Contraseñas a bcrypt ===\n")
    
    # Obtener todos los usuarios
    cursor.execute("SELECT id, username, password_hash FROM usuarios")
    usuarios = cursor.fetchall()
    
    migrados = 0
    ya_migrados = 0
    
    for user_id, username, password_hash in usuarios:
        # Verificar si ya es bcrypt
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
            print(f"✓ Usuario '{username}' ya tiene bcrypt")
            ya_migrados += 1
            continue
        
        # Preguntar si migrar (necesitamos la contraseña en texto plano)
        print(f"\n⚠️  Usuario '{username}' tiene hash SHA-256 antiguo")
        print(f"   Hash actual: {password_hash[:20]}...")
        print("\n   IMPORTANTE: No se puede convertir automáticamente de SHA-256 a bcrypt")
        print("   Opciones:")
        print("   1. El usuario debe cambiar su contraseña en el sistema")
        print("   2. Si conoces la contraseña, ingrésala ahora para migrarla")
        print("   3. Saltar este usuario (podrá seguir usando SHA-256 temporalmente)")
        
        opcion = input(f"\n   ¿Conoces la contraseña de '{username}'? (s/n/saltar): ").lower()
        
        if opcion == 's':
            password = input(f"   Ingresa la contraseña de '{username}': ")
            
            # Verificar que la contraseña sea correcta
            import hashlib
            if hashlib.sha256(password.encode()).hexdigest() == password_hash:
                # Generar nuevo hash bcrypt
                new_hash = Usuario.hash_password(password)
                
                # Actualizar en base de datos
                cursor.execute(
                    "UPDATE usuarios SET password_hash = ? WHERE id = ?",
                    (new_hash, user_id)
                )
                conn.commit()
                
                print(f"   ✓ Contraseña de '{username}' migrada a bcrypt exitosamente")
                migrados += 1
            else:
                print(f"   ✗ Contraseña incorrecta para '{username}'")
        elif opcion == 'n':
            print(f"   → '{username}' deberá cambiar su contraseña desde la aplicación")
        else:
            print(f"   → Saltando '{username}'")
    
    conn.close()
    
    print(f"\n=== Resumen de Migración ===")
    print(f"Usuarios migrados a bcrypt: {migrados}")
    print(f"Usuarios que ya tenían bcrypt: {ya_migrados}")
    print(f"Total de usuarios: {len(usuarios)}")
    print(f"\n✓ Migración completada")

if __name__ == "__main__":
    migrate_passwords()
