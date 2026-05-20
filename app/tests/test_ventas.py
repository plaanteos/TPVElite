"""
Tests para VentaService - Procesamiento de Ventas
"""
import pytest
from datetime import datetime
from services import VentaService, ProductoService
from models import Venta


class TestVentaService:
    """Tests unitarios para el servicio de ventas"""
    
    def test_crear_venta_exitosa(self, venta_service, test_user):
        """Test: Crear una venta exitosa"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 2, 'precio': 5.50},  # Helado Chocolate
            {'producto_id': 3, 'cantidad': 2, 'precio': 1.50}   # Cono Waffle
        ]
        metodo_pago = 'efectivo'
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago=metodo_pago
        )
        
        # Assert
        assert success is True
        assert venta_id is not None
        assert "exitosa" in message.lower()
    
    def test_crear_venta_actualiza_stock(self, venta_service, producto_service, test_user):
        """Test: La venta actualiza el stock correctamente"""
        # Arrange
        producto_id = 1
        cantidad_venta = 5
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        
        items = [
            {'producto_id': producto_id, 'cantidad': cantidad_venta, 'precio': 5.50}
        ]
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is True
        
        # Verificar que el stock disminuyó
        stock_final = producto_service.obtener_producto(producto_id).stock
        assert stock_final == stock_inicial - cantidad_venta
    
    def test_crear_venta_sin_stock_suficiente(self, venta_service, test_user):
        """Test: No permite venta sin stock suficiente"""
        # Arrange
        items = [
            {'producto_id': 5, 'cantidad': 10, 'precio': 5.50}  # Producto sin stock
        ]
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is False
        assert "stock" in message.lower()
        assert venta_id is None
    
    def test_crear_venta_genera_numero_unico(self, venta_service, test_user):
        """Test: Cada venta genera un número único"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 1, 'precio': 5.50}
        ]
        
        # Act - Crear dos ventas
        success1, msg1, venta_id1 = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        success2, msg2, venta_id2 = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='tarjeta'
        )
        
        # Assert
        assert success1 is True
        assert success2 is True
        assert venta_id1 != venta_id2
        
        # Obtener números de venta
        venta1 = venta_service.obtener_venta(venta_id1)
        venta2 = venta_service.obtener_venta(venta_id2)
        assert venta1.numero_venta != venta2.numero_venta
    
    def test_crear_venta_calcula_totales_correctamente(self, venta_service, test_user):
        """Test: Los totales se calculan correctamente"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 2, 'precio': 5.50},  # 11.00
            {'producto_id': 3, 'cantidad': 3, 'precio': 1.50}   # 4.50
        ]
        # Subtotal esperado: 15.50
        # Impuestos (16%): 2.48
        # Total: 17.98
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is True
        
        venta = venta_service.obtener_venta(venta_id)
        assert abs(venta.subtotal - 15.50) < 0.01
        assert abs(venta.impuestos - 2.48) < 0.01
        assert abs(venta.total - 17.98) < 0.01
    
    def test_crear_venta_con_items_vacios(self, venta_service, test_user):
        """Test: No permite venta sin items"""
        # Arrange
        items = []
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is False
        assert "items" in message.lower() or "productos" in message.lower()
    
    def test_crear_venta_con_cantidad_cero(self, venta_service, test_user):
        """Test: No permite items con cantidad cero"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 0, 'precio': 5.50}
        ]
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is False
    
    def test_crear_venta_con_cantidad_negativa(self, venta_service, test_user):
        """Test: No permite cantidades negativas"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': -5, 'precio': 5.50}
        ]
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Assert
        assert success is False
    
    def test_obtener_venta_existente(self, venta_service, test_user):
        """Test: Obtener venta por ID"""
        # Arrange - Crear venta primero
        items = [{'producto_id': 1, 'cantidad': 1, 'precio': 5.50}]
        success, msg, venta_id = venta_service.crear_venta(
            usuario_id=test_user.id,
            items=items,
            metodo_pago='efectivo'
        )
        
        # Act
        venta = venta_service.obtener_venta(venta_id)
        
        # Assert
        assert venta is not None
        assert venta.id == venta_id
        assert venta.usuario_id == test_user.id
        assert venta.metodo_pago == 'efectivo'
    
    def test_obtener_venta_inexistente(self, venta_service):
        """Test: Obtener venta que no existe"""
        # Act
        venta = venta_service.obtener_venta(9999)
        
        # Assert
        assert venta is None
    
    def test_listar_ventas(self, venta_service, test_user):
        """Test: Listar todas las ventas"""
        # Arrange - Crear algunas ventas
        items = [{'producto_id': 1, 'cantidad': 1, 'precio': 5.50}]
        
        venta_service.crear_venta(test_user.id, items, 'efectivo')
        venta_service.crear_venta(test_user.id, items, 'tarjeta')
        
        # Act
        ventas = venta_service.listar_ventas()
        
        # Assert
        assert len(ventas) >= 2
        assert all(isinstance(v, Venta) for v in ventas)
    
    def test_listar_ventas_por_usuario(self, venta_service, test_user, test_vendedor):
        """Test: Filtrar ventas por usuario"""
        # Arrange
        items = [{'producto_id': 1, 'cantidad': 1, 'precio': 5.50}]
        
        # Crear venta con admin
        venta_service.crear_venta(test_user.id, items, 'efectivo')
        
        # Crear venta con vendedor
        venta_service.crear_venta(test_vendedor.id, items, 'tarjeta')
        
        # Act
        ventas_admin = venta_service.listar_ventas(usuario_id=test_user.id)
        
        # Assert
        assert all(v.usuario_id == test_user.id for v in ventas_admin)
    
    def test_listar_ventas_con_filtro_fecha(self, venta_service, test_user):
        """Test: Filtrar ventas por rango de fechas"""
        # Arrange
        items = [{'producto_id': 1, 'cantidad': 1, 'precio': 5.50}]
        venta_service.crear_venta(test_user.id, items, 'efectivo')
        
        fecha_desde = datetime.now().strftime('%Y-%m-%d')
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        
        # Act
        ventas = venta_service.listar_ventas(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        
        # Assert
        assert len(ventas) >= 1
    
    def test_obtener_detalles_venta(self, venta_service, test_user):
        """Test: Obtener detalles de una venta"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 2, 'precio': 5.50},
            {'producto_id': 3, 'cantidad': 1, 'precio': 1.50}
        ]
        success, msg, venta_id = venta_service.crear_venta(
            test_user.id, items, 'efectivo'
        )
        
        # Act
        detalles = venta_service.obtener_detalles_venta(venta_id)
        
        # Assert
        assert len(detalles) == 2
        assert detalles[0]['cantidad'] == 2
        assert detalles[1]['cantidad'] == 1
    
    def test_cancelar_venta(self, venta_service, producto_service, test_user):
        """Test: Cancelar venta y restaurar stock"""
        # Arrange
        producto_id = 2
        cantidad = 3
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        
        items = [{'producto_id': producto_id, 'cantidad': cantidad, 'precio': 5.50}]
        success, msg, venta_id = venta_service.crear_venta(
            test_user.id, items, 'efectivo'
        )
        
        stock_despues_venta = producto_service.obtener_producto(producto_id).stock
        assert stock_despues_venta == stock_inicial - cantidad
        
        # Act
        success_cancel, msg_cancel = venta_service.cancelar_venta(venta_id)
        
        # Assert
        assert success_cancel is True
        
        # Verificar que el stock se restauró
        stock_final = producto_service.obtener_producto(producto_id).stock
        assert stock_final == stock_inicial
        
        # Verificar que el estado cambió
        venta = venta_service.obtener_venta(venta_id)
        assert venta.estado == 'cancelada'
    
    def test_venta_con_multiples_items_mismo_producto(self, venta_service, test_user):
        """Test: Venta con el mismo producto varias veces (debería sumar cantidades)"""
        # Arrange
        items = [
            {'producto_id': 1, 'cantidad': 2, 'precio': 5.50},
            {'producto_id': 1, 'cantidad': 3, 'precio': 5.50}
        ]
        
        # Act
        success, message, venta_id = venta_service.crear_venta(
            test_user.id, items, 'efectivo'
        )
        
        # Assert
        assert success is True
        
        # Verificar detalles
        detalles = venta_service.obtener_detalles_venta(venta_id)
        # Puede tener 2 líneas separadas o 1 línea sumada
        total_cantidad = sum(d['cantidad'] for d in detalles if d['producto_id'] == 1)
        assert total_cantidad == 5
    
    def test_metodos_pago_validos(self, venta_service, test_user):
        """Test: Ventas con diferentes métodos de pago"""
        items = [{'producto_id': 1, 'cantidad': 1, 'precio': 5.50}]
        
        # Efectivo
        s1, m1, id1 = venta_service.crear_venta(test_user.id, items, 'efectivo')
        assert s1 is True
        assert venta_service.obtener_venta(id1).metodo_pago == 'efectivo'
        
        # Tarjeta
        s2, m2, id2 = venta_service.crear_venta(test_user.id, items, 'tarjeta')
        assert s2 is True
        assert venta_service.obtener_venta(id2).metodo_pago == 'tarjeta'
        
        # Transferencia
        s3, m3, id3 = venta_service.crear_venta(test_user.id, items, 'transferencia')
        assert s3 is True
        assert venta_service.obtener_venta(id3).metodo_pago == 'transferencia'


@pytest.mark.integration
class TestVentaServiceIntegration:
    """Tests de integración para flujos completos de ventas"""
    
    def test_flujo_completo_multiples_ventas(self, venta_service, producto_service, test_user):
        """Test: Flujo completo de múltiples ventas"""
        # Stock inicial del producto 1
        producto_id = 1
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        
        # Crear 3 ventas
        for i in range(3):
            items = [{'producto_id': producto_id, 'cantidad': 5, 'precio': 5.50}]
            success, msg, venta_id = venta_service.crear_venta(
                test_user.id, items, 'efectivo'
            )
            assert success is True
        
        # Verificar stock final
        stock_final = producto_service.obtener_producto(producto_id).stock
        assert stock_final == stock_inicial - 15  # 3 ventas x 5 unidades
    
    def test_venta_y_cancelacion(self, venta_service, producto_service, test_user):
        """Test: Crear venta y luego cancelarla"""
        # Arrange
        producto_id = 3
        cantidad = 10
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        
        # Crear venta
        items = [{'producto_id': producto_id, 'cantidad': cantidad, 'precio': 1.50}]
        success, msg, venta_id = venta_service.crear_venta(
            test_user.id, items, 'tarjeta'
        )
        assert success is True
        
        # Verificar stock disminuyó
        stock_intermedio = producto_service.obtener_producto(producto_id).stock
        assert stock_intermedio == stock_inicial - cantidad
        
        # Cancelar venta
        success_cancel, msg_cancel = venta_service.cancelar_venta(venta_id)
        assert success_cancel is True
        
        # Verificar stock se restauró
        stock_final = producto_service.obtener_producto(producto_id).stock
        assert stock_final == stock_inicial
    
    def test_ventas_concurrentes_mismo_producto(self, venta_service, test_user, test_vendedor):
        """Test: Dos ventas simultáneas del mismo producto"""
        producto_id = 2
        
        items1 = [{'producto_id': producto_id, 'cantidad': 10, 'precio': 5.50}]
        items2 = [{'producto_id': producto_id, 'cantidad': 15, 'precio': 5.50}]
        
        # Ambas ventas deberían procesar correctamente
        s1, m1, id1 = venta_service.crear_venta(test_user.id, items1, 'efectivo')
        s2, m2, id2 = venta_service.crear_venta(test_vendedor.id, items2, 'tarjeta')
        
        assert s1 is True
        assert s2 is True
