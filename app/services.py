"""
Sistema TPV para Heladería - Módulo de Servicios
Autor: Jesus
Versión: 2.0.0
Descripción: Capa de servicios con lógica de negocio
"""

from typing import List, Optional, Tuple
from datetime import datetime
import logging

from database import DatabaseManager
from models import Usuario, Producto, Venta, DetalleVenta, Pedido, DetallePedido, MovimientoInventario
from utils import generate_invoice_number, generate_order_number

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio de autenticación y autorización"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.current_user: Optional[Usuario] = None
        self.current_session_id: Optional[int] = None
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Usuario]]:
        """
        Autentica un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            (éxito, mensaje, usuario)
        """
        try:
            # Buscar usuario
            row = self.db.fetch_one(
                "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
                (username,)
            )
            
            if not row:
                logger.warning(f"Intento de login fallido: usuario '{username}' no encontrado")
                return False, "Usuario o contraseña incorrectos", None
            
            # Crear objeto Usuario
            usuario = Usuario(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                nombre=row['nombre'],
                apellido=row['apellido'],
                email=row['email'],
                rol=row['rol'],
                activo=bool(row['activo']),
                intentos_fallidos=row['intentos_fallidos']
            )
            
            # Verificar contraseña
            if not usuario.verificar_password(password):
                # Incrementar intentos fallidos
                self.db.execute_query(
                    "UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 WHERE id = ?",
                    (usuario.id,)
                )
                
                # Bloquear usuario si supera 3 intentos
                if usuario.intentos_fallidos >= 2:  # 3er intento
                    self.db.execute_query(
                        "UPDATE usuarios SET activo = 0 WHERE id = ?",
                        (usuario.id,)
                    )
                    logger.warning(f"Usuario '{username}' bloqueado por múltiples intentos fallidos")
                    return False, "Usuario bloqueado por múltiples intentos fallidos", None
                
                logger.warning(f"Intento de login fallido: contraseña incorrecta para '{username}'")
                return False, "Usuario o contraseña incorrectos", None
            
            # Login exitoso
            self.db.execute_query(
                """UPDATE usuarios SET 
                   ultimo_acceso = ?, 
                   intentos_fallidos = 0 
                   WHERE id = ?""",
                (datetime.now(), usuario.id)
            )
            
            # Crear sesión
            self.db.execute_query(
                "INSERT INTO sesiones (usuario_id, fecha_inicio, activa) VALUES (?, ?, 1)",
                (usuario.id, datetime.now())
            )
            
            self.current_user = usuario
            logger.info(f"Usuario '{username}' inició sesión correctamente")
            return True, "Inicio de sesión exitoso", usuario
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return False, "Error al iniciar sesión", None
    
    def logout(self):
        """Cierra la sesión del usuario actual"""
        if self.current_user and self.current_session_id:
            self.db.execute_query(
                "UPDATE sesiones SET fecha_fin = ?, activa = 0 WHERE id = ?",
                (datetime.now(), self.current_session_id)
            )
            logger.info(f"Usuario '{self.current_user.username}' cerró sesión")
        
        self.current_user = None
        self.current_session_id = None
    
    def has_permission(self, required_role: str) -> bool:
        """
        Verifica si el usuario actual tiene el rol requerido
        
        Args:
            required_role: Rol requerido (admin, supervisor, cajero)
            
        Returns:
            True si tiene permiso, False en caso contrario
        """
        if not self.current_user:
            return False
        
        roles_hierarchy = {'admin': 3, 'supervisor': 2, 'cajero': 1}
        user_level = roles_hierarchy.get(self.current_user.rol, 0)
        required_level = roles_hierarchy.get(required_role, 0)
        
        return user_level >= required_level


class ProductoService:
    """Servicio para gestión de productos"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def crear_producto(self, producto: Producto, usuario_id: int) -> Tuple[bool, str, Optional[int]]:
        """Crea un nuevo producto"""
        try:
            # Validaciones
            if not producto.nombre:
                return False, "El nombre del producto es obligatorio", None
            
            if producto.precio <= 0:
                return False, "El precio debe ser mayor a 0", None
            
            if producto.stock < 0:
                return False, "El stock no puede ser negativo", None
            
            # Verificar si ya existe
            existing = self.db.fetch_one(
                "SELECT id FROM productos WHERE nombre = ?",
                (producto.nombre,)
            )
            if existing:
                return False, f"Ya existe un producto con el nombre '{producto.nombre}'", None
            
            # Insertar producto
            success = self.db.execute_query(
                """INSERT INTO productos 
                   (nombre, descripcion, categoria, precio, costo, stock, stock_minimo, 
                    unidad_medida, codigo_barras, proveedor_id, activo, fecha_creacion, fecha_modificacion)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                (producto.nombre, producto.descripcion, producto.categoria, producto.precio,
                 producto.costo, producto.stock, producto.stock_minimo, producto.unidad_medida,
                 producto.codigo_barras, getattr(producto, 'proveedor_id', None), datetime.now(), datetime.now())
            )
            
            if not success:
                return False, "Error al crear el producto", None
            
            # Obtener ID del producto creado
            row = self.db.fetch_one("SELECT last_insert_rowid() as id")
            producto_id = row['id']
            
            # Registrar movimiento de inventario inicial
            if producto.stock > 0:
                self.db.execute_query(
                    """INSERT INTO movimientos_inventario
                       (producto_id, tipo, cantidad, stock_anterior, stock_nuevo, usuario_id, 
                        referencia, fecha, notas)
                       VALUES (?, 'ajuste', ?, 0, ?, ?, 'Stock inicial', ?, 'Stock inicial del producto')""",
                    (producto_id, producto.stock, producto.stock, usuario_id, datetime.now())
                )
            
            logger.info(f"Producto creado: {producto.nombre} (ID: {producto_id})")
            return True, "Producto creado correctamente", producto_id
            
        except Exception as e:
            logger.error(f"Error al crear producto: {e}")
            return False, f"Error al crear el producto: {str(e)}", None
    
    def actualizar_producto(self, producto_id: int, producto: Producto) -> Tuple[bool, str]:
        """Actualiza un producto existente"""
        try:
            # Verificar que existe
            existing = self.db.fetch_one("SELECT id FROM productos WHERE id = ?", (producto_id,))
            if not existing:
                return False, "Producto no encontrado"
            
            # Actualizar
            success = self.db.execute_query(
                """UPDATE productos SET
                   nombre = ?, descripcion = ?, categoria = ?, precio = ?, costo = ?,
                   stock_minimo = ?, unidad_medida = ?, codigo_barras = ?, proveedor_id = ?,
                   fecha_modificacion = ?
                   WHERE id = ?""",
                (producto.nombre, producto.descripcion, producto.categoria, producto.precio,
                 producto.costo, producto.stock_minimo, producto.unidad_medida,
                 producto.codigo_barras, getattr(producto, 'proveedor_id', None),
                 datetime.now(), producto_id)
            )
            
            if success:
                logger.info(f"Producto actualizado: ID {producto_id}")
                return True, "Producto actualizado correctamente"
            else:
                return False, "Error al actualizar el producto"
                
        except Exception as e:
            logger.error(f"Error al actualizar producto: {e}")
            return False, f"Error al actualizar el producto: {str(e)}"
    
    def obtener_producto(self, producto_id: int) -> Optional[Producto]:
        """Obtiene un producto por su ID"""
        try:
            row = self.db.fetch_one("SELECT * FROM productos WHERE id = ?", (producto_id,))
            if row:
                return Producto(
                    id=row['id'],
                    nombre=row['nombre'],
                    descripcion=row['descripcion'],
                    categoria=row['categoria'],
                    precio=row['precio'],
                    costo=row['costo'],
                    stock=row['stock'],
                    stock_minimo=row['stock_minimo'],
                    unidad_medida=row['unidad_medida'],
                    codigo_barras=row['codigo_barras'],
                    proveedor_id=row['proveedor_id'] if 'proveedor_id' in row.keys() else None,
                    activo=bool(row['activo'])
                )
            return None
        except Exception as e:
            logger.error(f"Error al obtener producto: {e}")
            return None
    
    def listar_productos(self, solo_activos: bool = True) -> List[Producto]:
        """Lista todos los productos"""
        try:
            query = "SELECT * FROM productos"
            if solo_activos:
                query += " WHERE activo = 1"
            query += " ORDER BY nombre"
            
            rows = self.db.fetch_all(query)
            productos = []
            
            for row in rows:
                productos.append(Producto(
                    id=row['id'],
                    nombre=row['nombre'],
                    descripcion=row['descripcion'],
                    categoria=row['categoria'],
                    precio=row['precio'],
                    costo=row['costo'],
                    stock=row['stock'],
                    stock_minimo=row['stock_minimo'],
                    unidad_medida=row['unidad_medida'],
                    codigo_barras=row['codigo_barras'],
                    activo=bool(row['activo'])
                ))
            
            return productos
        except Exception as e:
            logger.error(f"Error al listar productos: {e}")
            return []
    
    def productos_bajo_stock(self) -> List[Producto]:
        """Lista productos con stock bajo"""
        try:
            rows = self.db.fetch_all(
                "SELECT * FROM productos WHERE stock <= stock_minimo AND activo = 1 ORDER BY stock"
            )
            
            productos = []
            for row in rows:
                productos.append(Producto(
                    id=row['id'],
                    nombre=row['nombre'],
                    descripcion=row['descripcion'],
                    categoria=row['categoria'],
                    precio=row['precio'],
                    costo=row['costo'],
                    stock=row['stock'],
                    stock_minimo=row['stock_minimo'],
                    unidad_medida=row['unidad_medida'],
                    codigo_barras=row['codigo_barras'],
                    activo=bool(row['activo'])
                ))
            
            return productos
        except Exception as e:
            logger.error(f"Error al obtener productos con stock bajo: {e}")
            return []
    
    def ajustar_stock(self, producto_id: int, cantidad: int, tipo: str, 
                     usuario_id: int, referencia: str = None, notas: str = None) -> Tuple[bool, str]:
        """Ajusta el stock de un producto"""
        try:
            # Obtener stock actual
            row = self.db.fetch_one("SELECT stock FROM productos WHERE id = ?", (producto_id,))
            if not row:
                return False, "Producto no encontrado"
            
            stock_actual = row['stock']
            nuevo_stock = stock_actual + cantidad
            
            if nuevo_stock < 0:
                return False, "Stock insuficiente"
            
            # Actualizar stock
            operations = [
                ("UPDATE productos SET stock = ?, fecha_modificacion = ? WHERE id = ?",
                 (nuevo_stock, datetime.now(), producto_id)),
                ("""INSERT INTO movimientos_inventario
                    (producto_id, tipo, cantidad, stock_anterior, stock_nuevo, usuario_id, 
                     referencia, fecha, motivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (producto_id, tipo, abs(cantidad), stock_actual, nuevo_stock, usuario_id,
                  referencia, datetime.now(), notas))
            ]
            
            success = self.db.execute_transaction(operations)
            
            if success:
                logger.info(f"Stock ajustado para producto ID {producto_id}: {stock_actual} -> {nuevo_stock}")
                return True, "Stock actualizado correctamente"
            else:
                return False, "Error al actualizar el stock"
                
        except Exception as e:
            logger.error(f"Error al ajustar stock: {e}")
            return False, f"Error al ajustar el stock: {str(e)}"


class VentaService:
    """Servicio para gestión de ventas"""
    
    def __init__(self, db: DatabaseManager, producto_service: ProductoService):
        self.db = db
        self.producto_service = producto_service
    
    def crear_venta(self, venta: Venta, usuario_id: int) -> Tuple[bool, str, Optional[int]]:
        """Crea una nueva venta"""
        try:
            # Validaciones
            if not venta.detalles:
                return False, "La venta debe tener al menos un producto", None
            
            # Generar número de venta
            venta.numero_venta = generate_invoice_number()
            venta.usuario_id = usuario_id
            
            # Calcular totales
            venta.calcular_totales()
            
            # Verificar stock disponible
            for detalle in venta.detalles:
                producto = self.producto_service.obtener_producto(detalle.producto_id)
                if not producto:
                    return False, f"Producto {detalle.producto_nombre} no encontrado", None
                
                if producto.stock < detalle.cantidad:
                    return False, f"Stock insuficiente para {producto.nombre}", None
            
            # ✅ Iniciar transacción manual con BEGIN
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                # 1. Insertar venta
                cursor.execute(
                    """INSERT INTO ventas
                       (numero_venta, fecha, usuario_id, cliente_nombre, subtotal, descuento,
                        impuestos, total, metodo_pago, estado, notas)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (venta.numero_venta, venta.fecha, usuario_id, venta.cliente_nombre,
                     venta.subtotal, venta.descuento, venta.impuestos, venta.total,
                     venta.metodo_pago, venta.estado, venta.notas)
                )
                
                # Obtener el ID de la venta recién insertada
                venta_id = cursor.lastrowid
                
                # 2. Procesar cada detalle
                for detalle in venta.detalles:
                    # Insertar detalle
                    cursor.execute(
                        """INSERT INTO detalles_venta
                           (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                           VALUES (?, ?, ?, ?, ?)""",
                        (venta_id, detalle.producto_id, detalle.cantidad,
                         detalle.precio_unitario, detalle.subtotal)
                    )
                    
                    # Obtener producto para stock actual
                    producto = self.producto_service.obtener_producto(detalle.producto_id)
                    nuevo_stock = producto.stock - detalle.cantidad
                    
                    # Actualizar stock
                    cursor.execute(
                        "UPDATE productos SET stock = ?, fecha_modificacion = ? WHERE id = ?",
                        (nuevo_stock, datetime.now(), detalle.producto_id)
                    )
                    
                    # Registrar movimiento de inventario
                    cursor.execute(
                        """INSERT INTO movimientos_inventario
                           (producto_id, tipo, cantidad, stock_anterior, stock_nuevo, usuario_id,
                            referencia, fecha, notas)
                           VALUES (?, 'venta', ?, ?, ?, ?, ?, ?, ?)""",
                        (detalle.producto_id, detalle.cantidad, producto.stock, nuevo_stock,
                         usuario_id, venta.numero_venta, datetime.now(),
                         f"Venta #{venta.numero_venta}")
                    )
                
                # ✅ Confirmar transacción
                conn.commit()
                
            except Exception as e:
                # ❌ Revertir cambios si hay error
                conn.rollback()
                logger.error(f"Error en transacción de venta: {e}")
                return False, f"Error al procesar la venta: {str(e)}", None
            
            logger.info(f"Venta creada: {venta.numero_venta} (ID: {venta_id})")
            return True, "Venta realizada correctamente", venta_id
            
        except Exception as e:
            logger.error(f"Error al crear venta: {e}")
            return False, f"Error al crear la venta: {str(e)}", None
    
    def obtener_venta(self, venta_id: int) -> Optional[Venta]:
        """Obtiene una venta por su ID"""
        try:
            # Obtener venta
            row = self.db.fetch_one("SELECT * FROM ventas WHERE id = ?", (venta_id,))
            if not row:
                return None
            
            # Crear objeto Venta
            venta = Venta(
                id=row['id'],
                numero_venta=row['numero_venta'],
                fecha=datetime.fromisoformat(row['fecha']),
                usuario_id=row['usuario_id'],
                cliente_nombre=row['cliente_nombre'],
                subtotal=row['subtotal'],
                descuento=row['descuento'],
                impuestos=row['impuestos'],
                total=row['total'],
                metodo_pago=row['metodo_pago'],
                estado=row['estado'],
                notas=row['notas']
            )
            
            # Obtener detalles
            detalles_rows = self.db.fetch_all(
                """SELECT dv.*, p.nombre as producto_nombre
                   FROM detalles_venta dv
                   JOIN productos p ON dv.producto_id = p.id
                   WHERE dv.venta_id = ?""",
                (venta_id,)
            )
            
            for detalle_row in detalles_rows:
                venta.detalles.append(DetalleVenta(
                    id=detalle_row['id'],
                    venta_id=detalle_row['venta_id'],
                    producto_id=detalle_row['producto_id'],
                    producto_nombre=detalle_row['producto_nombre'],
                    cantidad=detalle_row['cantidad'],
                    precio_unitario=detalle_row['precio_unitario'],
                    subtotal=detalle_row['subtotal']
                ))
            
            return venta
            
        except Exception as e:
            logger.error(f"Error al obtener venta: {e}")
            return None
    
    def listar_ventas(self, fecha_desde: datetime = None, fecha_hasta: datetime = None) -> List[Venta]:
        """Lista ventas con filtros opcionales"""
        try:
            query = "SELECT * FROM ventas WHERE 1=1"
            params = []
            
            if fecha_desde:
                query += " AND fecha >= ?"
                params.append(fecha_desde)
            
            if fecha_hasta:
                query += " AND fecha <= ?"
                params.append(fecha_hasta)
            
            query += " ORDER BY fecha DESC"
            
            rows = self.db.fetch_all(query, tuple(params))
            ventas = []
            
            for row in rows:
                ventas.append(Venta(
                    id=row['id'],
                    numero_venta=row['numero_venta'],
                    fecha=datetime.fromisoformat(row['fecha']),
                    usuario_id=row['usuario_id'],
                    cliente_nombre=row['cliente_nombre'],
                    subtotal=row['subtotal'],
                    descuento=row['descuento'],
                    impuestos=row['impuestos'],
                    total=row['total'],
                    metodo_pago=row['metodo_pago'],
                    estado=row['estado'],
                    notas=row['notas']
                ))
            
            return ventas
            
        except Exception as e:
            logger.error(f"Error al listar ventas: {e}")
            return []
