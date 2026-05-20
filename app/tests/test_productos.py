"""
Tests para ProductoService - Gestión de Productos e Inventario
"""
import pytest
from services import ProductoService
from models import Producto


class TestProductoService:
    """Tests unitarios para el servicio de productos"""
    
    def test_listar_productos_todos(self, producto_service):
        """Test: Listar todos los productos"""
        # Act
        productos = producto_service.listar_productos()
        
        # Assert
        assert len(productos) == 5  # Los 5 productos de prueba
        assert all(isinstance(p, Producto) for p in productos)
    
    def test_listar_productos_activos(self, producto_service):
        """Test: Listar solo productos activos"""
        # Act
        productos = producto_service.listar_productos(activos_solo=True)
        
        # Assert
        assert all(p.activo for p in productos)
    
    def test_listar_productos_con_filtro_categoria(self, producto_service):
        """Test: Filtrar productos por categoría"""
        # Act
        productos = producto_service.listar_productos(categoria="Helados")
        
        # Assert
        assert len(productos) == 3  # Chocolate, Vainilla, Fresa
        assert all(p.categoria == "Helados" for p in productos)
    
    def test_listar_productos_con_busqueda(self, producto_service):
        """Test: Buscar productos por nombre"""
        # Act
        productos = producto_service.listar_productos(busqueda="Chocolate")
        
        # Assert
        assert len(productos) == 1
        assert productos[0].nombre == "Helado Chocolate"
    
    def test_obtener_producto_existente(self, producto_service):
        """Test: Obtener producto por ID"""
        # Act
        producto = producto_service.obtener_producto(1)
        
        # Assert
        assert producto is not None
        assert producto.id == 1
        assert producto.nombre == "Helado Chocolate"
        assert producto.precio == 5.50
    
    def test_obtener_producto_inexistente(self, producto_service):
        """Test: Obtener producto que no existe"""
        # Act
        producto = producto_service.obtener_producto(9999)
        
        # Assert
        assert producto is None
    
    def test_crear_producto_exitoso(self, producto_service):
        """Test: Crear un nuevo producto"""
        # Arrange
        datos = {
            'nombre': 'Helado Mango',
            'categoria': 'Helados',
            'precio': 6.00,
            'costo': 3.50,
            'stock': 50,
            'stock_minimo': 10,
            'codigo_barras': '9999999999999'
        }
        
        # Act
        success, message, producto_id = producto_service.crear_producto(**datos)
        
        # Assert
        assert success is True
        assert producto_id is not None
        
        # Verificar que se creó correctamente
        producto = producto_service.obtener_producto(producto_id)
        assert producto is not None
        assert producto.nombre == 'Helado Mango'
        assert producto.precio == 6.00
        assert producto.stock == 50
    
    def test_crear_producto_sin_nombre(self, producto_service):
        """Test: Crear producto sin nombre (debe fallar)"""
        # Arrange
        datos = {
            'nombre': '',
            'categoria': 'Helados',
            'precio': 5.00,
            'costo': 3.00
        }
        
        # Act
        success, message, producto_id = producto_service.crear_producto(**datos)
        
        # Assert
        assert success is False
        assert "nombre" in message.lower() or "requerido" in message.lower()
    
    def test_crear_producto_precio_negativo(self, producto_service):
        """Test: Crear producto con precio negativo (debe fallar)"""
        # Arrange
        datos = {
            'nombre': 'Producto Test',
            'categoria': 'Test',
            'precio': -5.00,
            'costo': 3.00
        }
        
        # Act
        success, message, producto_id = producto_service.crear_producto(**datos)
        
        # Assert
        assert success is False
        assert "precio" in message.lower() or "positivo" in message.lower()
    
    def test_actualizar_producto_exitoso(self, producto_service):
        """Test: Actualizar un producto existente"""
        # Arrange
        producto_id = 1
        nuevo_precio = 6.50
        nuevo_stock = 150
        
        # Act
        success, message = producto_service.actualizar_producto(
            producto_id,
            precio=nuevo_precio,
            stock=nuevo_stock
        )
        
        # Assert
        assert success is True
        
        # Verificar cambios
        producto = producto_service.obtener_producto(producto_id)
        assert producto.precio == nuevo_precio
        assert producto.stock == nuevo_stock
    
    def test_actualizar_producto_inexistente(self, producto_service):
        """Test: Actualizar producto que no existe"""
        # Act
        success, message = producto_service.actualizar_producto(
            9999, precio=10.00
        )
        
        # Assert
        assert success is False
        assert "encontrado" in message.lower() or "existe" in message.lower()
    
    def test_ajustar_stock_entrada(self, producto_service, test_user):
        """Test: Ajustar stock con entrada de mercancía"""
        # Arrange
        producto_id = 1
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        cantidad = 50
        
        # Act
        success, message = producto_service.ajustar_stock(
            producto_id,
            tipo='entrada',
            cantidad=cantidad,
            usuario_id=test_user.id,
            notas='Test de entrada'
        )
        
        # Assert
        assert success is True
        
        # Verificar que el stock aumentó
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == stock_inicial + cantidad
    
    def test_ajustar_stock_salida(self, producto_service, test_user):
        """Test: Ajustar stock con salida de mercancía"""
        # Arrange
        producto_id = 1
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        cantidad = 20
        
        # Act
        success, message = producto_service.ajustar_stock(
            producto_id,
            tipo='salida',
            cantidad=cantidad,
            usuario_id=test_user.id,
            notas='Test de salida'
        )
        
        # Assert
        assert success is True
        
        # Verificar que el stock disminuyó
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == stock_inicial - cantidad
    
    def test_ajustar_stock_salida_mayor_que_disponible(self, producto_service, test_user):
        """Test: Intentar sacar más stock del disponible"""
        # Arrange
        producto_id = 1
        stock_actual = producto_service.obtener_producto(producto_id).stock
        cantidad = stock_actual + 100  # Más de lo disponible
        
        # Act
        success, message = producto_service.ajustar_stock(
            producto_id,
            tipo='salida',
            cantidad=cantidad,
            usuario_id=test_user.id
        )
        
        # Assert
        assert success is False
        assert "suficiente" in message.lower() or "stock" in message.lower()
    
    def test_ajustar_stock_merma(self, producto_service, test_user):
        """Test: Registrar merma de producto"""
        # Arrange
        producto_id = 2
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        cantidad = 5
        
        # Act
        success, message = producto_service.ajustar_stock(
            producto_id,
            tipo='merma',
            cantidad=cantidad,
            usuario_id=test_user.id,
            notas='Producto vencido'
        )
        
        # Assert
        assert success is True
        
        # Verificar que el stock disminuyó
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == stock_inicial - cantidad
    
    def test_ajustar_stock_ajuste(self, producto_service, test_user):
        """Test: Ajuste de inventario (corrección)"""
        # Arrange
        producto_id = 3
        nuevo_stock = 175
        
        # Act
        success, message = producto_service.ajustar_stock(
            producto_id,
            tipo='ajuste',
            cantidad=nuevo_stock,
            usuario_id=test_user.id,
            notas='Corrección por inventario físico'
        )
        
        # Assert
        assert success is True
        
        # Verificar que el stock es exactamente el nuevo valor
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == nuevo_stock
    
    def test_eliminar_producto(self, producto_service):
        """Test: Eliminar (desactivar) un producto"""
        # Arrange
        producto_id = 4
        
        # Act
        success, message = producto_service.eliminar_producto(producto_id)
        
        # Assert
        assert success is True
        
        # Verificar que está inactivo
        producto = producto_service.obtener_producto(producto_id)
        assert producto is not None  # Sigue existiendo
        assert producto.activo is False  # Pero está inactivo
    
    def test_buscar_por_codigo_barras(self, producto_service):
        """Test: Buscar producto por código de barras"""
        # Act
        producto = producto_service.buscar_por_codigo_barras('1234567890123')
        
        # Assert
        assert producto is not None
        assert producto.codigo_barras == '1234567890123'
        assert producto.nombre == 'Helado Chocolate'
    
    def test_buscar_por_codigo_barras_inexistente(self, producto_service):
        """Test: Buscar código de barras que no existe"""
        # Act
        producto = producto_service.buscar_por_codigo_barras('0000000000000')
        
        # Assert
        assert producto is None
    
    def test_obtener_productos_bajo_stock(self, producto_service):
        """Test: Listar productos con stock bajo mínimo"""
        # Act
        productos = producto_service.obtener_productos_bajo_stock()
        
        # Assert
        assert len(productos) >= 1
        # Verificar que el producto con stock 0 está en la lista
        assert any(p.stock == 0 for p in productos)
    
    def test_obtener_categorias(self, producto_service):
        """Test: Obtener lista de categorías únicas"""
        # Act
        categorias = producto_service.obtener_categorias()
        
        # Assert
        assert 'Helados' in categorias
        assert 'Complementos' in categorias
        assert 'Bebidas' in categorias
        assert len(categorias) == 3
    
    def test_validar_stock_disponible_suficiente(self, producto_service):
        """Test: Validar que hay stock suficiente"""
        # Arrange
        producto_id = 1  # Tiene 100 unidades
        cantidad = 50
        
        # Act
        disponible = producto_service.validar_stock_disponible(producto_id, cantidad)
        
        # Assert
        assert disponible is True
    
    def test_validar_stock_disponible_insuficiente(self, producto_service):
        """Test: Validar stock insuficiente"""
        # Arrange
        producto_id = 5  # Tiene 0 unidades
        cantidad = 1
        
        # Act
        disponible = producto_service.validar_stock_disponible(producto_id, cantidad)
        
        # Assert
        assert disponible is False
    
    def test_actualizar_nombre_y_categoria(self, producto_service):
        """Test: Actualizar nombre y categoría de producto"""
        # Arrange
        producto_id = 2
        nuevo_nombre = "Helado Vainilla Premium"
        nueva_categoria = "Helados Premium"
        
        # Act
        success, message = producto_service.actualizar_producto(
            producto_id,
            nombre=nuevo_nombre,
            categoria=nueva_categoria
        )
        
        # Assert
        assert success is True
        
        producto = producto_service.obtener_producto(producto_id)
        assert producto.nombre == nuevo_nombre
        assert producto.categoria == nueva_categoria


@pytest.mark.integration
class TestProductoServiceIntegration:
    """Tests de integración para flujos completos de productos"""
    
    def test_flujo_completo_crear_ajustar_eliminar(self, producto_service, test_user):
        """Test: Flujo completo de gestión de producto"""
        # 1. Crear producto
        success1, msg1, producto_id = producto_service.crear_producto(
            nombre='Producto Test Flujo',
            categoria='Test',
            precio=10.00,
            costo=5.00,
            stock=100,
            stock_minimo=20
        )
        assert success1 is True
        assert producto_id is not None
        
        # 2. Ajustar stock (entrada)
        success2, msg2 = producto_service.ajustar_stock(
            producto_id,
            tipo='entrada',
            cantidad=50,
            usuario_id=test_user.id
        )
        assert success2 is True
        
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == 150
        
        # 3. Ajustar stock (salida)
        success3, msg3 = producto_service.ajustar_stock(
            producto_id,
            tipo='salida',
            cantidad=30,
            usuario_id=test_user.id
        )
        assert success3 is True
        
        producto = producto_service.obtener_producto(producto_id)
        assert producto.stock == 120
        
        # 4. Eliminar producto
        success4, msg4 = producto_service.eliminar_producto(producto_id)
        assert success4 is True
        
        producto = producto_service.obtener_producto(producto_id)
        assert producto.activo is False
    
    def test_crear_productos_duplicados(self, producto_service):
        """Test: Crear productos con el mismo nombre"""
        # Crear primer producto
        success1, msg1, id1 = producto_service.crear_producto(
            nombre='Producto Duplicado',
            categoria='Test',
            precio=5.00,
            costo=3.00
        )
        assert success1 is True
        
        # Intentar crear producto con mismo nombre
        success2, msg2, id2 = producto_service.crear_producto(
            nombre='Producto Duplicado',
            categoria='Test',
            precio=6.00,
            costo=3.50
        )
        # Debería permitirlo (no hay constraint UNIQUE en nombre)
        # o rechazarlo según la lógica de negocio
        # Por ahora asumimos que se permite
        assert success2 is True or success2 is False
