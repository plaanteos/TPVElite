"""
Tests E2E de flujos críticos del TPV.
"""

import pytest
from datetime import datetime, timedelta
from models import Venta, DetalleVenta


@pytest.mark.integration
class TestE2EFlujosCriticos:
    """Cobertura de punta a punta sobre flujos sensibles de negocio."""

    def test_e2e_login_venta_stock_logout(self, auth_service, venta_service, producto_service, test_user):
        # 1) Login
        ok_login, _, usuario = auth_service.login("admin", "admin123")
        assert ok_login is True
        assert usuario is not None

        # 2) Venta
        producto_id = 1
        stock_inicial = producto_service.obtener_producto(producto_id).stock
        detalle = DetalleVenta(
            producto_id=producto_id,
            producto_nombre='Helado Chocolate',
            cantidad=2,
            precio_unitario=5.50,
        )
        detalle.calcular_subtotal()

        venta = Venta(
            usuario_id=test_user.id,
            metodo_pago='efectivo',
            detalles=[detalle],
            impuestos=0,
        )

        ok_venta, _, venta_id = venta_service.crear_venta(venta, test_user.id)
        assert ok_venta is True
        assert venta_id is not None

        # 3) Validación de stock
        stock_final = producto_service.obtener_producto(producto_id).stock
        assert stock_final == stock_inicial - 2

        # 4) Logout
        auth_service.logout()
        assert auth_service.current_user is None

    def test_e2e_bloqueo_temporal_por_intentos(self, auth_service):
        # 3 intentos fallidos
        for _ in range(3):
            ok, _, _ = auth_service.login("admin", "password_incorrecto")
            assert ok is False

        # El cuarto, aun con password correcta, debe estar temporalmente bloqueado
        ok, msg, usuario = auth_service.login("admin", "admin123")
        assert ok is False
        assert "bloqueado temporalmente" in msg.lower()
        assert usuario is None

    def test_e2e_actualizacion_producto_y_reporte_ventas(
        self,
        auth_service,
        producto_service,
        venta_service,
        test_user,
    ):
        # 1) Login
        ok_login, _, usuario = auth_service.login("admin", "admin123")
        assert ok_login is True
        assert usuario is not None

        # 2) Actualización de producto
        producto = producto_service.obtener_producto(1)
        assert producto is not None

        nuevo_precio = producto.precio + 1
        producto.precio = nuevo_precio

        ok_update, _ = producto_service.actualizar_producto(producto.id, producto)
        assert ok_update is True

        producto_actualizado = producto_service.obtener_producto(1)
        assert producto_actualizado is not None
        assert producto_actualizado.precio == nuevo_precio

        # 3) Venta para alimentar reporte
        detalle = DetalleVenta(
            producto_id=1,
            producto_nombre=producto_actualizado.nombre,
            cantidad=1,
            precio_unitario=producto_actualizado.precio,
        )
        detalle.calcular_subtotal()

        venta = Venta(
            usuario_id=test_user.id,
            metodo_pago='efectivo',
            detalles=[detalle],
            impuestos=0,
        )

        ok_venta, _, venta_id = venta_service.crear_venta(venta, test_user.id)
        assert ok_venta is True
        assert venta_id is not None

        # 4) Reporte de ventas por rango de fechas
        fecha_desde = datetime.now() - timedelta(days=1)
        fecha_hasta = datetime.now() + timedelta(days=1)
        ventas = venta_service.listar_ventas(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        ids = [v.id for v in ventas]
        assert venta_id in ids

        # 5) Logout
        auth_service.logout()
        assert auth_service.current_user is None
