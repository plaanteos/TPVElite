"""
Tests para AuthService - Sistema de Autenticación
"""
import pytest
import bcrypt
from services import AuthService
from models import Usuario


class TestAuthService:
    """Tests unitarios para el servicio de autenticación"""
    
    def test_login_exitoso(self, auth_service):
        """Test: Login con credenciales correctas"""
        # Arrange
        username = "admin"
        password = "admin123"
        
        # Act
        success, message, user = auth_service.login(username, password)
        
        # Assert
        assert success is True
        assert "exitoso" in message.lower()
        assert user is not None
        assert user.username == username
        assert user.rol == "admin"
        assert auth_service.current_user is not None
        assert auth_service.current_user.username == username
    
    def test_login_fallido_password_incorrecto(self, auth_service):
        """Test: Login con password incorrecto"""
        # Arrange
        username = "admin"
        password = "password_incorrecto"
        
        # Act
        success, message, user = auth_service.login(username, password)
        
        # Assert
        assert success is False
        assert "incorrecta" in message.lower() or "inválida" in message.lower()
        assert user is None
        assert auth_service.current_user is None
    
    def test_login_fallido_usuario_inexistente(self, auth_service):
        """Test: Login con usuario que no existe"""
        # Arrange
        username = "usuario_inexistente"
        password = "cualquier_password"
        
        # Act
        success, message, user = auth_service.login(username, password)
        
        # Assert
        assert success is False
        assert "encontrado" in message.lower() or "existe" in message.lower()
        assert user is None
        assert auth_service.current_user is None
    
    def test_login_fallido_usuario_inactivo(self, auth_service, db_manager):
        """Test: Login con usuario desactivado"""
        # Arrange - Desactivar usuario vendedor
        db_manager.execute_query(
            "UPDATE usuarios SET activo = 0 WHERE username = ?",
            ("vendedor1",)
        )
        
        # Act
        success, message, user = auth_service.login("vendedor1", "vendedor123")
        
        # Assert
        assert success is False
        assert "inactivo" in message.lower() or "desactivado" in message.lower()
        assert user is None
    
    def test_logout(self, auth_service):
        """Test: Cierre de sesión"""
        # Arrange - Primero hacer login
        auth_service.login("admin", "admin123")
        assert auth_service.current_user is not None
        
        # Act
        auth_service.logout()
        
        # Assert
        assert auth_service.current_user is None
    
    def test_cambiar_password_exitoso(self, auth_service):
        """Test: Cambio de contraseña exitoso"""
        # Arrange
        auth_service.login("admin", "admin123")
        usuario_id = auth_service.current_user.id
        old_password = "admin123"
        new_password = "nuevo_password_123"
        
        # Act
        success, message = auth_service.cambiar_password(
            usuario_id, old_password, new_password
        )
        
        # Assert
        assert success is True
        assert "exitoso" in message.lower() or "actualizada" in message.lower()
        
        # Verificar que la nueva contraseña funciona
        auth_service.logout()
        success2, _, user2 = auth_service.login("admin", new_password)
        assert success2 is True
        assert user2 is not None
    
    def test_cambiar_password_fallido_password_actual_incorrecto(self, auth_service):
        """Test: Cambio de contraseña con password actual incorrecto"""
        # Arrange
        auth_service.login("admin", "admin123")
        usuario_id = auth_service.current_user.id
        old_password = "password_incorrecto"
        new_password = "nuevo_password_123"
        
        # Act
        success, message = auth_service.cambiar_password(
            usuario_id, old_password, new_password
        )
        
        # Assert
        assert success is False
        assert "actual" in message.lower() or "incorrecta" in message.lower()
    
    def test_cambiar_password_usuario_inexistente(self, auth_service):
        """Test: Cambio de contraseña para usuario inexistente"""
        # Arrange
        usuario_id = 9999  # ID que no existe
        old_password = "cualquier_password"
        new_password = "nuevo_password"
        
        # Act
        success, message = auth_service.cambiar_password(
            usuario_id, old_password, new_password
        )
        
        # Assert
        assert success is False
        assert "encontrado" in message.lower() or "existe" in message.lower()
    
    def test_verificar_password_bcrypt(self, db_manager):
        """Test: Verificación de hash bcrypt"""
        # Arrange
        password = "test_password_123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Act
        resultado_correcto = bcrypt.checkpw(password.encode('utf-8'), password_hash)
        resultado_incorrecto = bcrypt.checkpw("password_incorrecto".encode('utf-8'), password_hash)
        
        # Assert
        assert resultado_correcto is True
        assert resultado_incorrecto is False
    
    def test_hash_password_genera_diferente_salt(self):
        """Test: Cada hash genera un salt diferente"""
        # Arrange
        password = "mismo_password"
        
        # Act
        hash1 = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hash2 = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Assert
        assert hash1 != hash2  # Los hashes deben ser diferentes por el salt
        assert bcrypt.checkpw(password.encode('utf-8'), hash1)
        assert bcrypt.checkpw(password.encode('utf-8'), hash2)
    
    def test_login_vendedor(self, auth_service):
        """Test: Login con usuario vendedor"""
        # Arrange
        username = "vendedor1"
        password = "vendedor123"
        
        # Act
        success, message, user = auth_service.login(username, password)
        
        # Assert
        assert success is True
        assert user is not None
        assert user.rol == "vendedor"
        assert auth_service.current_user.rol == "vendedor"
    
    def test_multiples_intentos_login(self, auth_service):
        """Test: Múltiples intentos de login"""
        # Act & Assert - Varios intentos fallidos
        for i in range(3):
            success, _, _ = auth_service.login("admin", "password_incorrecto")
            assert success is False
        
        # Verificar que después de intentos fallidos, el correcto funciona
        success, message, user = auth_service.login("admin", "admin123")
        assert success is True
        assert user is not None
    
    def test_login_campos_vacios(self, auth_service):
        """Test: Login con campos vacíos"""
        # Test con username vacío
        success1, msg1, user1 = auth_service.login("", "password")
        assert success1 is False
        assert user1 is None
        
        # Test con password vacío
        success2, msg2, user2 = auth_service.login("admin", "")
        assert success2 is False
        assert user2 is None
        
        # Test con ambos vacíos
        success3, msg3, user3 = auth_service.login("", "")
        assert success3 is False
        assert user3 is None
    
    def test_current_user_persistencia(self, auth_service):
        """Test: El usuario actual persiste durante la sesión"""
        # Arrange & Act
        auth_service.login("admin", "admin123")
        user1 = auth_service.current_user
        user2 = auth_service.current_user
        
        # Assert
        assert user1 is user2
        assert user1.username == "admin"
    
    def test_logout_sin_login_previo(self, auth_service):
        """Test: Logout sin haber hecho login"""
        # Arrange
        assert auth_service.current_user is None
        
        # Act
        auth_service.logout()
        
        # Assert
        assert auth_service.current_user is None  # No debe causar error


@pytest.mark.integration
class TestAuthServiceIntegration:
    """Tests de integración para el flujo completo de autenticación"""
    
    def test_flujo_completo_login_cambio_password_logout(self, auth_service):
        """Test: Flujo completo de autenticación"""
        # 1. Login inicial
        success1, msg1, user1 = auth_service.login("admin", "admin123")
        assert success1 is True
        assert auth_service.current_user is not None
        
        # 2. Cambiar password
        success2, msg2 = auth_service.cambiar_password(
            user1.id, "admin123", "nuevo_pass_456"
        )
        assert success2 is True
        
        # 3. Logout
        auth_service.logout()
        assert auth_service.current_user is None
        
        # 4. Login con password antigua (debe fallar)
        success3, msg3, user3 = auth_service.login("admin", "admin123")
        assert success3 is False
        
        # 5. Login con nueva password (debe funcionar)
        success4, msg4, user4 = auth_service.login("admin", "nuevo_pass_456")
        assert success4 is True
        assert auth_service.current_user is not None
    
    def test_sesion_multiple_usuarios(self, auth_service):
        """Test: Cambio de sesión entre usuarios"""
        # Login con admin
        auth_service.login("admin", "admin123")
        assert auth_service.current_user.username == "admin"
        
        # Logout
        auth_service.logout()
        assert auth_service.current_user is None
        
        # Login con vendedor
        auth_service.login("vendedor1", "vendedor123")
        assert auth_service.current_user.username == "vendedor1"
        assert auth_service.current_user.rol == "vendedor"
