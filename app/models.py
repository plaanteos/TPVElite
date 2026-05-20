"""
Sistema TPV para Heladería - Módulo de Modelos
Autor: Jesus
Versión: 2.0.0
Descripción: Modelos de datos y lógica de negocio
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
import bcrypt
import logging

logger = logging.getLogger(__name__)


@dataclass
class Usuario:
    """Modelo de usuario del sistema"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    nombre: str = ""
    apellido: str = ""
    email: Optional[str] = None
    rol: str = "cajero"
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None
    intentos_fallidos: int = 0
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Genera un hash bcrypt seguro de la contraseña
        Usa bcrypt con salt automático para proteger contra rainbow tables
        """
        # Generar hash con bcrypt (incluye salt automático)
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds es el estándar recomendado
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verificar_password(self, password: str) -> bool:
        """
        Verifica si la contraseña coincide con el hash bcrypt
        Maneja compatibilidad con hashes SHA-256 antiguos
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        
        # Verificar si es un hash bcrypt (comienza con $2b$)
        if self.password_hash.startswith('$2b$') or self.password_hash.startswith('$2a$'):
            try:
                return bcrypt.checkpw(password_bytes, hash_bytes)
            except Exception as e:
                logger.error(f"Error al verificar password bcrypt: {e}")
                return False
        else:
            # Compatibilidad con hashes SHA-256 antiguos
            import hashlib
            sha256_hash = hashlib.sha256(password_bytes).hexdigest()
            return self.password_hash == sha256_hash


@dataclass
class Producto:
    """Modelo de producto"""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    categoria: str = "general"
    precio: float = 0.0
    costo: float = 0.0
    stock: int = 0
    stock_minimo: int = 5
    unidad_medida: str = "unidad"
    codigo_barras: Optional[str] = None
    imagen_url: Optional[str] = None
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_modificacion: Optional[datetime] = None
    
    @property
    def margen_beneficio(self) -> float:
        """Calcula el margen de beneficio"""
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return 0.0
    
    @property
    def necesita_reabastecimiento(self) -> bool:
        """Verifica si el producto necesita reabastecimiento"""
        return self.stock <= self.stock_minimo
    
    @property
    def valor_inventario(self) -> float:
        """Calcula el valor total del inventario de este producto"""
        return self.stock * self.costo


@dataclass
class DetalleVenta:
    """Detalle de una venta"""
    id: Optional[int] = None
    venta_id: Optional[int] = None
    producto_id: int = 0
    producto_nombre: str = ""
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0
    
    def calcular_subtotal(self):
        """Calcula el subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario


@dataclass
class Venta:
    """Modelo de venta"""
    id: Optional[int] = None
    numero_venta: str = ""
    fecha: datetime = field(default_factory=datetime.now)
    usuario_id: int = 0
    usuario_nombre: str = ""
    cliente_nombre: Optional[str] = None
    subtotal: float = 0.0
    descuento: float = 0.0
    impuestos: float = 0.0
    total: float = 0.0
    metodo_pago: str = "efectivo"
    estado: str = "completada"
    notas: Optional[str] = None
    detalles: List[DetalleVenta] = field(default_factory=list)
    
    def calcular_totales(self):
        """Calcula los totales de la venta"""
        self.subtotal = sum(detalle.subtotal for detalle in self.detalles)
        self.total = self.subtotal - self.descuento + self.impuestos
    
    @property
    def cantidad_items(self) -> int:
        """Retorna la cantidad total de items"""
        return sum(detalle.cantidad for detalle in self.detalles)


@dataclass
class DetallePedido:
    """Detalle de un pedido"""
    id: Optional[int] = None
    pedido_id: Optional[int] = None
    producto_id: int = 0
    producto_nombre: str = ""
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0
    
    def calcular_subtotal(self):
        """Calcula el subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario


@dataclass
class Pedido:
    """Modelo de pedido a proveedor"""
    id: Optional[int] = None
    numero_pedido: str = ""
    fecha: datetime = field(default_factory=datetime.now)
    usuario_id: int = 0
    usuario_nombre: str = ""
    proveedor: str = ""
    total: float = 0.0
    estado: str = "pendiente"
    fecha_entrega: Optional[datetime] = None
    notas: Optional[str] = None
    detalles: List[DetallePedido] = field(default_factory=list)
    
    def calcular_total(self):
        """Calcula el total del pedido"""
        self.total = sum(detalle.subtotal for detalle in self.detalles)


@dataclass
class MovimientoInventario:
    """Modelo de movimiento de inventario"""
    id: Optional[int] = None
    producto_id: int = 0
    producto_nombre: str = ""
    tipo: str = "ajuste"
    cantidad: int = 0
    stock_anterior: int = 0
    stock_nuevo: int = 0
    usuario_id: int = 0
    usuario_nombre: str = ""
    referencia: Optional[str] = None
    fecha: datetime = field(default_factory=datetime.now)
    notas: Optional[str] = None


@dataclass
class Sesion:
    """Modelo de sesión de usuario"""
    id: Optional[int] = None
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_inicio: datetime = field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = None
    ip_address: Optional[str] = None
    activa: bool = True
