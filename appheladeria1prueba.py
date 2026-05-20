import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import os
import uuid
import hashlib
import csv
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageTk
import json
import logging
import re
import threading
import queue
import socket
import barcode



# Configuración del sistema de logging
logging.basicConfig(
    filename='tpv_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TPV_System')

# Clase para manejar la base de datos
class DatabaseManager:
    def __init__(self, db_name="tpv_database.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            logger.info("Conexión a la base de datos establecida")
        except sqlite3.Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            messagebox.showerror("Error de Base de Datos", f"No se pudo conectar a la base de datos: {e}")
    
    def create_tables(self):
        try:
            # Tabla de usuarios
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de productos
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    price REAL NOT NULL,
                    cost REAL,
                    stock INTEGER DEFAULT 0,
                    min_stock INTEGER DEFAULT 5,
                    supplier_id INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    image_path TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                )
            ''')
            
            # Tabla de categorías
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            ''')
            
            # Tabla de proveedores
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    tax_id TEXT,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de ventas
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_number TEXT UNIQUE,
                    date TIMESTAMP,
                    customer_id INTEGER,
                    user_id INTEGER,
                    subtotal REAL,
                    tax REAL,
                    discount REAL,
                    total REAL,
                    payment_method TEXT,
                    payment_status TEXT,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de detalles de venta
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    price REAL,
                    discount REAL,
                    total REAL,
                    notes TEXT,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabla de clientes
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    tax_id TEXT,
                    created_at TIMESTAMP,
                    loyalty_points INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de movimientos de inventario
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    date TIMESTAMP,
                    type TEXT,
                    quantity INTEGER,
                    reason TEXT,
                    user_id INTEGER,
                    reference_id INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de configuración
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    description TEXT
                )
            ''')
            
            # Tabla de caja
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_register (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opening_time TIMESTAMP,
                    closing_time TIMESTAMP,
                    initial_amount REAL,
                    final_amount REAL,
                    user_id INTEGER,
                    notes TEXT,
                    status TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de movimientos de caja
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    register_id INTEGER,
                    amount REAL,
                    type TEXT,
                    description TEXT,
                    time TIMESTAMP,
                    user_id INTEGER,
                    FOREIGN KEY (register_id) REFERENCES cash_register (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Tablas creadas correctamente")
            
            # Insertar usuario admin por defecto si no existe
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if self.cursor.fetchone()[0] == 0:
                salt = os.urandom(32).hex()
                password_hash = hashlib.sha256(('admin' + salt).encode()).hexdigest()
                self.cursor.execute('''
                    INSERT INTO users (username, password_hash, salt, role, last_login, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('admin', password_hash, salt, 'admin', datetime.datetime.now(), 1))
                self.conn.commit()
                logger.info("Usuario admin creado por defecto")
                
        except sqlite3.Error as e:
            logger.error(f"Error al crear las tablas: {e}")
            messagebox.showerror("Error de Base de Datos", f"No se pudieron crear las tablas: {e}")
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Conexión a la base de datos cerrada")
    
    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error al ejecutar la consulta: {e}")
            return False
    
    def fetch_one(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error al obtener datos: {e}")
            return None
    
    def fetch_all(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error al obtener datos: {e}")
            return []

# Clase para autenticación y gestión de usuarios
class AuthManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_user = None
    
    def login(self, username, password):
        user_data = self.db_manager.fetch_one(
            "SELECT id, username, password_hash, salt, role FROM users WHERE username = ? AND is_active = 1",
            (username,)
        )
        
        if user_data:
            user_id, username, stored_hash, salt, role = user_data
            calculated_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            
            if calculated_hash == stored_hash:
                self.current_user = {
                    'id': user_id,
                    'username': username,
                    'role': role
                }
                # Actualizar último login
                self.db_manager.execute_query(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.datetime.now(), user_id)
                )
                logger.info(f"Usuario {username} ha iniciado sesión")
                return True
                
        logger.warning(f"Intento de inicio de sesión fallido para el usuario: {username}")
        return False
    
    def logout(self):
        if self.current_user:
            username = self.current_user['username']
            self.current_user = None
            logger.info(f"Usuario {username} ha cerrado sesión")
            return True
        return False
    
    def is_authenticated(self):
        return self.current_user is not None
    
    def get_current_user(self):
        return self.current_user
    
    def has_permission(self, required_role):
        if not self.current_user:
            return False
        
        if required_role == 'any':
            return True
            
        if self.current_user['role'] == 'admin':
            return True
            
        return self.current_user['role'] == required_role
    
    def change_password(self, user_id, new_password):
        salt = os.urandom(32).hex()
        password_hash = hashlib.sha256((new_password + salt).encode()).hexdigest()
        
        success = self.db_manager.execute_query(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (password_hash, salt, user_id)
        )
        
        if success:
            logger.info(f"Contraseña cambiada para el usuario ID: {user_id}")
        else:
            logger.warning(f"Error al cambiar la contraseña para el usuario ID: {user_id}")
            
        return success
    
    def add_user(self, username, password, role):
        # Verificar si el usuario ya existe
        existing_user = self.db_manager.fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        
        if existing_user:
            logger.warning(f"Intento de crear usuario duplicado: {username}")
            return False, "El nombre de usuario ya existe"
        
        salt = os.urandom(32).hex()
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        success = self.db_manager.execute_query(
            '''INSERT INTO users (username, password_hash, salt, role, last_login, is_active)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (username, password_hash, salt, role, datetime.datetime.now(), 1)
        )
        
        if success:
            logger.info(f"Nuevo usuario creado: {username} con rol: {role}")
            return True, "Usuario creado exitosamente"
        else:
            logger.error(f"Error al crear nuevo usuario: {username}")
            return False, "Error al crear el usuario"

# Clase para gestionar el inventario
class InventoryManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def add_product(self, product_data):
        try:
            query = '''
                INSERT INTO products (
                    barcode, name, description, category, price, cost,
                    stock, min_stock, supplier_id, created_at, updated_at,
                    image_path, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            now = datetime.datetime.now()
            
            params = (
                product_data.get('barcode'),
                product_data.get('name'),
                product_data.get('description'),
                product_data.get('category'),
                product_data.get('price', 0),
                product_data.get('cost', 0),
                product_data.get('stock', 0),
                product_data.get('min_stock', 5),
                product_data.get('supplier_id'),
                now,
                now,
                product_data.get('image_path'),
                1
            )
            
            success = self.db_manager.execute_query(query, params)
            
            if success:
                logger.info(f"Producto agregado: {product_data.get('name')}")
                
                # Obtener el ID del producto recién insertado
                product_id = self.db_manager.fetch_one("SELECT last_insert_rowid()")[0]
                
                # Registrar movimiento de inventario inicial si hay stock
                initial_stock = product_data.get('stock', 0)
                if initial_stock > 0:
                    self.register_movement(
                        product_id=product_id,
                        movement_type="initial",
                        quantity=initial_stock,
                        reason="Stock inicial",
                        user_id=product_data.get('user_id'),
                        reference_id=None
                    )
                
                return True, product_id
            else:
                logger.error(f"Error al agregar producto: {product_data.get('name')}")
                return False, None
                
        except Exception as e:
            logger.error(f"Excepción al agregar producto: {e}")
            return False, None
    
    def update_product(self, product_id, product_data):
        try:
            query = '''
                UPDATE products SET 
                    barcode = ?,
                    name = ?,
                    description = ?,
                    category = ?,
                    price = ?,
                    cost = ?,
                    min_stock = ?,
                    supplier_id = ?,
                    updated_at = ?,
                    image_path = ?
                WHERE id = ?
            '''
            
            params = (
                product_data.get('barcode'),
                product_data.get('name'),
                product_data.get('description'),
                product_data.get('category'),
                product_data.get('price', 0),
                product_data.get('cost', 0),
                product_data.get('min_stock', 5),
                product_data.get('supplier_id'),
                datetime.datetime.now(),
                product_data.get('image_path'),
                product_id
            )
            
            success = self.db_manager.execute_query(query, params)
            
            if success:
                logger.info(f"Producto actualizado: ID {product_id}")
                return True
            else:
                logger.error(f"Error al actualizar producto: ID {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción al actualizar producto: {e}")
            return False
    
    def get_product(self, product_id):
        query = "SELECT * FROM products WHERE id = ?"
        product = self.db_manager.fetch_one(query, (product_id,))
        
        if product:
            # Convertir a diccionario para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            product_dict = dict(zip(columns, product))
            return product_dict
        else:
            return None
    
    def get_product_by_barcode(self, barcode):
        query = "SELECT * FROM products WHERE barcode = ?"
        product = self.db_manager.fetch_one(query, (barcode,))
        
        if product:
            # Convertir a diccionario para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            product_dict = dict(zip(columns, product))
            return product_dict
        else:
            return None
    
    def get_all_products(self, active_only=True):
        if active_only:
            query = "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
        else:
            query = "SELECT * FROM products ORDER BY name"
            
        products = self.db_manager.fetch_all(query)
        
        if products:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            products_list = []
            for product in products:
                products_list.append(dict(zip(columns, product)))
            return products_list
        else:
            return []
    
    def update_stock(self, product_id, new_quantity, movement_type, reason, user_id, reference_id=None):
        # Obtener stock actual
        current_stock = self.get_product(product_id).get('stock', 0)
        
        # Calcular la diferencia
        if movement_type in ['sale', 'adjustment_out', 'damage', 'expiry', 'transfer_out']:
            quantity_change = -abs(new_quantity)  # Negativo para salidas
        else:
            quantity_change = abs(new_quantity)   # Positivo para entradas
        
        # Actualizar el stock
        new_stock = current_stock + quantity_change
        
        query = "UPDATE products SET stock = ?, updated_at = ? WHERE id = ?"
        success = self.db_manager.execute_query(query, (new_stock, datetime.datetime.now(), product_id))
        
        if success:
            # Registrar el movimiento
            self.register_movement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=new_quantity,  # La cantidad original (no el cambio)
                reason=reason,
                user_id=user_id,
                reference_id=reference_id
            )
            
            logger.info(f"Stock actualizado para producto ID {product_id}. Nuevo stock: {new_stock}")
            return True, new_stock
        else:
            logger.error(f"Error al actualizar stock para producto ID {product_id}")
            return False, current_stock
    
    def register_movement(self, product_id, movement_type, quantity, reason, user_id, reference_id=None):
        query = '''
            INSERT INTO inventory_movements (
                product_id, date, type, quantity, reason, user_id, reference_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            product_id,
            datetime.datetime.now(),
            movement_type,
            quantity,
            reason,
            user_id,
            reference_id
        )
        
        success = self.db_manager.execute_query(query, params)
        
        if success:
            logger.info(f"Movimiento de inventario registrado: {movement_type} para producto ID {product_id}")
            return True
        else:
            logger.error(f"Error al registrar movimiento de inventario para producto ID {product_id}")
            return False
    
    def get_low_stock_products(self):
        query = '''
            SELECT * FROM products 
            WHERE stock <= min_stock AND is_active = 1
            ORDER BY (stock - min_stock), name
        '''
        
        products = self.db_manager.fetch_all(query)
        
        if products:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            products_list = []
            for product in products:
                products_list.append(dict(zip(columns, product)))
            return products_list
        else:
            return []
    
    def get_inventory_movements(self, product_id=None, start_date=None, end_date=None, movement_type=None):
        query_parts = ["SELECT im.*, p.name as product_name, u.username FROM inventory_movements im"]
        query_parts.append("LEFT JOIN products p ON im.product_id = p.id")
        query_parts.append("LEFT JOIN users u ON im.user_id = u.id")
        
        conditions = []
        params = []
        
        if product_id:
            conditions.append("im.product_id = ?")
            params.append(product_id)
        
        if start_date:
            conditions.append("im.date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("im.date <= ?")
            params.append(end_date)
        
        if movement_type:
            conditions.append("im.type = ?")
            params.append(movement_type)
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY im.date DESC")
        
        query = " ".join(query_parts)
        
        movements = self.db_manager.fetch_all(query, params if params else None)
        
        if movements:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            movements_list = []
            for movement in movements:
                movements_list.append(dict(zip(columns, movement)))
            return movements_list
        else:
            return []

# Clase para gestionar las ventas
class SalesManager:
    def __init__(self, db_manager, inventory_manager):
        self.db_manager = db_manager
        self.inventory_manager = inventory_manager
        self.current_sale = None
    
    def create_new_sale(self, user_id, customer_id=None):
        self.current_sale = {
            'items': [],
            'user_id': user_id,
            'customer_id': customer_id,
            'date': datetime.datetime.now(),
            'subtotal': 0,
            'tax': 0,
            'discount': 0,
            'total': 0,
            'payment_method': None,
            'payment_status': 'pending',
            'notes': None
        }
        
        return True
    
    def add_item_to_sale(self, product_id, quantity, price=None, discount=0):
        if not self.current_sale:
            logger.error("No hay una venta activa para agregar items")
            return False, "No hay una venta activa"
        
        # Verificar si el producto existe y tiene suficiente stock
        product = self.inventory_manager.get_product(product_id)
        if not product:
            logger.warning(f"Intento de agregar producto inexistente ID: {product_id} a la venta")
            return False, "Producto no encontrado"
        
        if product['stock'] < quantity:
            logger.warning(f"Stock insuficiente para producto ID: {product_id}. Solicitado: {quantity}, Disponible: {product['stock']}")
            return False, f"Stock insuficiente. Disponible: {product['stock']}"
        
        # Si no se especifica el precio, usar el del producto
        if price is None:
            price = product['price']
        
        # Calcular el total del item
        item_total = price * quantity - discount
        
        # Agregar el item a la venta
        self.current_sale['items'].append({
            'product_id': product_id,
            'product_name': product['name'],
            'quantity': quantity,
            'price': price,
            'discount': discount,
            'total': item_total
        })
        
        # Actualizar los totales de la venta
        self._update_sale_totals()
        
        logger.info(f"Item agregado a la venta: {product['name']} x {quantity}")
        return True, "Item agregado a la venta"
    
    def remove_item_from_sale(self, item_index):
        if not self.current_sale or item_index >= len(self.current_sale['items']):
            logger.error(f"Intento de eliminar item inexistente: índice {item_index}")
            return False, "Item no encontrado"
        
        removed_item = self.current_sale['items'].pop(item_index)
        self._update_sale_totals()
        
        logger.info(f"Item eliminado de la venta: {removed_item['product_name']}")
        return True, "Item eliminado de la venta"
    
    def update_item_quantity(self, item_index, new_quantity):
        if not self.current_sale or item_index >= len(self.current_sale['items']):
            logger.error(f"Intento de actualizar item inexistente: índice {item_index}")
            return False, "Item no encontrado"
        
        item = self.current_sale['items'][item_index]
        product = self.inventory_manager.get_product(item['product_id'])
        
        if product['stock'] < new_quantity:
            logger.warning(f"Stock insuficiente para actualizar producto ID: {item['product_id']}. Solicitado: {new_quantity}, Disponible: {product['stock']}")
            return False, f"Stock insuficiente. Disponible: {product['stock']}"
        
        # Actualizar cantidad y total
        item['quantity'] = new_quantity
        item['total'] = item['price'] * new_quantity - item['discount']
        
        self._update_sale_totals()
        
        logger.info(f"Cantidad actualizada para item: {item['product_name']}. Nueva cantidad: {new_quantity}")
        return True, "Cantidad actualizada"
    
    def apply_discount(self, discount_amount):
        if not self.current_sale:
            logger.error("No hay una venta activa para aplicar descuento")
            return False, "No hay una venta activa"
        
        self.current_sale['discount'] = discount_amount
        self._update_sale_totals()
        
        logger.info(f"Descuento aplicado a la venta: {discount_amount}")
        return True, "Descuento aplicado"
    
    def set_payment_method(self, method):
        if not self.current_sale:
            logger.error("No hay una venta activa para establecer método de pago")
            return False, "No hay una venta activa"
        
        valid_methods = ['cash', 'card', 'transfer', 'check', 'credit', 'other']
        if method not in valid_methods:
            logger.warning(f"Método de pago inválido: {method}")
            return False, "Método de pago inválido"
        
        self.current_sale['payment_method'] = method
        logger.info(f"Método de pago establecido: {method}")
        return True, "Método de pago establecido"
    
    def set_payment_status(self, status):
        if not self.current_sale:
            logger.error("No hay una venta activa para establecer estado de pago")
            return False, "No hay una venta activa"
        
        valid_statuses = ['pending', 'paid', 'partial', 'canceled', 'refunded']
        if status not in valid_statuses:
            logger.warning(f"Estado de pago inválido: {status}")
            return False, "Estado de pago inválido"
        
        self.current_sale['payment_status'] = status
        logger.info(f"Estado de pago establecido: {status}")
        return True, "Estado de pago establecido"
    
    def set_notes(self, notes):
        if not self.current_sale:
            logger.error("No hay una venta activa para agregar notas")
            return False, "No hay una venta activa"
        
        self.current_sale['notes'] = notes
        logger.info("Notas agregadas a la venta")
        return True, "Notas agregadas"
    
    def _update_sale_totals(self):
        if not self.current_sale:
            return
        
        # Calcular subtotal
        subtotal = sum(item['total'] for item in self.current_sale['items'])
        
        # Obtener tasa de impuesto de la configuración (por defecto 0.16 o 16%)
        tax_rate = self._get_tax_rate()
        
        # Calcular impuesto sobre el subtotal menos descuento
        taxable_amount = subtotal - self.current_sale['discount']
        tax = taxable_amount * tax_rate if taxable_amount > 0 else 0
        
        # Calcular total
        total = taxable_amount + tax
        
        # Actualizar la venta
        self.current_sale['subtotal'] = subtotal
        self.current_sale['tax'] = tax
        self.current_sale['total'] = total
    
    def _get_tax_rate(self):
        # Obtener tasa de impuesto de la configuración
        tax_rate_config = self.db_manager.fetch_one("SELECT value FROM config WHERE key = 'tax_rate'")
        if tax_rate_config:
            try:
                return float(tax_rate_config[0]) / 100.0  # Convertir de porcentaje a decimal
            except (ValueError, TypeError):
                pass
        return 0.16  # 16% por defecto
    
    def get_current_sale(self):
        return self.current_sale
    
    def cancel_sale(self):
        if not self.current_sale:
            logger.warning("Intento de cancelar una venta inexistente")
            return False, "No hay una venta activa para cancelar"
        
        logger.info("Venta cancelada")
        self.current_sale = None
        return True, "Venta cancelada exitosamente"
    
    def finalize_sale(self):
        if not self.current_sale or not self.current_sale['items']:
            logger.warning("Intento de finalizar una venta vacía o inexistente")
            return False, "No hay una venta activa o no tiene productos"
        
        if not self.current_sale['payment_method']:
            logger.warning("Intento de finalizar venta sin método de pago")
            return False, "Debe especificar un método de pago"
        
        try:
            # Generar número de venta único
            sale_number = f"V{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Insertar la venta en la base de datos
            query = '''
                INSERT INTO sales (
                    sale_number, date, customer_id, user_id,
                    subtotal, tax, discount, total,
                    payment_method, payment_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                sale_number,
                self.current_sale['date'],
                self.current_sale['customer_id'],
                self.current_sale['user_id'],
                self.current_sale['subtotal'],
                self.current_sale['tax'],
                self.current_sale['discount'],
                self.current_sale['total'],
                self.current_sale['payment_method'],
                self.current_sale['payment_status'],
                self.current_sale['notes']
            )
            
            success = self.db_manager.execute_query(query, params)
            
            if not success:
                logger.error("Error al guardar la venta en la base de datos")
                return False, "Error al guardar la venta"
            
            # Obtener el ID de la venta
            sale_id = self.db_manager.fetch_one("SELECT last_insert_rowid()")[0]
            
            # Insertar los items de la venta
            for item in self.current_sale['items']:
                query = '''
                    INSERT INTO sale_items (
                        sale_id, product_id, quantity, price,
                        discount, total, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                
                params = (
                    sale_id,
                    item['product_id'],
                    item['quantity'],
                    item['price'],
                    item['discount'],
                    item['total'],
                    None  # Notas del item
                )
                
                success = self.db_manager.execute_query(query, params)
                
                if not success:
                    logger.error(f"Error al guardar el item {item['product_name']} de la venta")
                    # Consideramos continuar a pesar del error
                
                # Actualizar el inventario
                self.inventory_manager.update_stock(
                    product_id=item['product_id'],
                    new_quantity=item['quantity'],
                    movement_type='sale',
                    reason=f"Venta #{sale_number}",
                    user_id=self.current_sale['user_id'],
                    reference_id=sale_id
                )
            
            # Si hay un cliente, actualizar sus puntos de lealtad
            if self.current_sale['customer_id']:
                self._update_customer_loyalty_points(sale_id)
            
            # Guardar la venta actual antes de limpiarla
            completed_sale = self.current_sale.copy()
            completed_sale['id'] = sale_id
            completed_sale['sale_number'] = sale_number
            
            # Limpiar la venta actual
            self.current_sale = None
            
            logger.info(f"Venta finalizada exitosamente. Número: {sale_number}, ID: {sale_id}")
            return True, completed_sale
            
        except Exception as e:
            logger.error(f"Excepción al finalizar la venta: {e}")
            return False, f"Error al finalizar la venta: {str(e)}"
    
    def _update_customer_loyalty_points(self, sale_id):
        if not self.current_sale or not self.current_sale['customer_id']:
            return
        
        try:
            # Obtener la configuración de puntos
            points_config = self.db_manager.fetch_one("SELECT value FROM config WHERE key = 'loyalty_points_rate'")
            points_rate = float(points_config[0]) if points_config else 0.01  # Por defecto 1 punto por cada 100 unidades
            
            # Calcular puntos a añadir (redondeado a entero)
            points_to_add = int(self.current_sale['total'] * points_rate)
            
            if points_to_add > 0:
                # Actualizar puntos del cliente
                query = '''
                    UPDATE customers 
                    SET loyalty_points = loyalty_points + ? 
                    WHERE id = ?
                '''
                
                self.db_manager.execute_query(query, (points_to_add, self.current_sale['customer_id']))
                
                logger.info(f"Puntos de lealtad actualizados para cliente ID {self.current_sale['customer_id']}. Añadidos: {points_to_add}")
        
        except Exception as e:
            logger.error(f"Error al actualizar puntos de lealtad: {e}")
    
    def get_sale(self, sale_id):
        # Obtener los datos principales de la venta
        query = "SELECT * FROM sales WHERE id = ?"
        sale_data = self.db_manager.fetch_one(query, (sale_id,))
        
        if not sale_data:
            return None
        
        # Convertir a diccionario
        columns = [col[0] for col in self.db_manager.cursor.description]
        sale_dict = dict(zip(columns, sale_data))
        
        # Obtener los items de la venta
        query = '''
            SELECT si.*, p.name as product_name 
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        '''
        
        items_data = self.db_manager.fetch_all(query, (sale_id,))
        
        # Convertir items a lista de diccionarios
        items = []
        if items_data:
            columns = [col[0] for col in self.db_manager.cursor.description]
            for item in items_data:
                items.append(dict(zip(columns, item)))
        
        sale_dict['items'] = items
        
        # Si hay cliente, obtener sus datos
        if sale_dict['customer_id']:
            query = "SELECT name, email, phone FROM customers WHERE id = ?"
            customer_data = self.db_manager.fetch_one(query, (sale_dict['customer_id'],))
            
            if customer_data:
                sale_dict['customer_name'] = customer_data[0]
                sale_dict['customer_email'] = customer_data[1]
                sale_dict['customer_phone'] = customer_data[2]
        
        # Obtener nombre del usuario
        query = "SELECT username FROM users WHERE id = ?"
        user_data = self.db_manager.fetch_one(query, (sale_dict['user_id'],))
        
        if user_data:
            sale_dict['username'] = user_data[0]
        
        return sale_dict
    
    def get_sales(self, start_date=None, end_date=None, user_id=None, customer_id=None, status=None):
        query_parts = ["SELECT s.*, u.username, c.name as customer_name FROM sales s"]
        query_parts.append("LEFT JOIN users u ON s.user_id = u.id")
        query_parts.append("LEFT JOIN customers c ON s.customer_id = c.id")
        
        conditions = []
        params = []
        
        if start_date:
            conditions.append("s.date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("s.date <= ?")
            params.append(end_date)
        
        if user_id:
            conditions.append("s.user_id = ?")
            params.append(user_id)
        
        if customer_id:
            conditions.append("s.customer_id = ?")
            params.append(customer_id)
        
        if status:
            conditions.append("s.payment_status = ?")
            params.append(status)
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY s.date DESC")
        
        query = " ".join(query_parts)
        
        sales_data = self.db_manager.fetch_all(query, params if params else None)
        
        if not sales_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = [col[0] for col in self.db_manager.cursor.description]
        sales_list = []
        for sale in sales_data:
            sales_list.append(dict(zip(columns, sale)))
        
        return sales_list
    
    def cancel_saved_sale(self, sale_id):
        # Verificar si la venta existe
        sale = self.get_sale(sale_id)
        if not sale:
            logger.warning(f"Intento de cancelar venta inexistente ID: {sale_id}")
            return False, "Venta no encontrada"
        
        # Verificar si ya está cancelada
        if sale['payment_status'] == 'canceled':
            logger.warning(f"Intento de cancelar venta ya cancelada ID: {sale_id}")
            return False, "La venta ya está cancelada"
        
        # Actualizar estado de la venta
        query = "UPDATE sales SET payment_status = 'canceled' WHERE id = ?"
        success = self.db_manager.execute_query(query, (sale_id,))
        
        if not success:
            logger.error(f"Error al cancelar venta ID: {sale_id}")
            return False, "Error al cancelar la venta"
        
        # Devolver inventario
        for item in sale['items']:
            self.inventory_manager.update_stock(
                product_id=item['product_id'],
                new_quantity=item['quantity'],
                movement_type='sale_return',
                reason=f"Cancelación venta #{sale['sale_number']}",
                user_id=sale['user_id'],
                reference_id=sale_id
            )
        
        logger.info(f"Venta ID: {sale_id} cancelada exitosamente")
        return True, "Venta cancelada exitosamente"

# Clase para gestionar la caja
class CashRegisterManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_active_register(self):
        query = "SELECT * FROM cash_register WHERE status = 'open' ORDER BY opening_time DESC LIMIT 1"
        register_data = self.db_manager.fetch_one(query)
        
        if register_data:
            # Convertir a diccionario
            columns = [col[0] for col in self.db_manager.cursor.description]
            register_dict = dict(zip(columns, register_data))
            return register_dict
        else:
            return None
    
    def open_register(self, user_id, initial_amount, notes=None):
        # Verificar si ya hay una caja abierta
        active_register = self.get_active_register()
        if active_register:
            logger.warning(f"Intento de abrir caja cuando ya hay una activa. Usuario ID: {user_id}")
            return False, "Ya hay una caja abierta. Debe cerrarla primero."
        
        # Abrir nueva caja
        query = '''
            INSERT INTO cash_register (
                opening_time, initial_amount, user_id, notes, status
            ) VALUES (?, ?, ?, ?, ?)
        '''
        
        params = (
            datetime.datetime.now(),
            initial_amount,
            user_id,
            notes,
            'open'
        )
        
        success = self.db_manager.execute_query(query, params)
        
        if success:
            register_id = self.db_manager.fetch_one("SELECT last_insert_rowid()")[0]
            
            # Registrar el movimiento inicial
            self.add_movement(
                register_id=register_id,
                amount=initial_amount,
                movement_type='initial',
                description="Monto inicial de caja",
                user_id=user_id
            )
            
            logger.info(f"Caja abierta por usuario ID: {user_id}. Monto inicial: {initial_amount}")
            return True, register_id
        else:
            logger.error(f"Error al abrir caja. Usuario ID: {user_id}")
            return False, "Error al abrir la caja"
    
    def close_register(self, user_id, final_amount, notes=None):
        # Obtener la caja activa
        active_register = self.get_active_register()
        if not active_register:
            logger.warning(f"Intento de cerrar caja inexistente. Usuario ID: {user_id}")
            return False, "No hay una caja abierta para cerrar"
        
        # Verificar que sea el mismo usuario o un administrador
        if active_register['user_id'] != user_id:
            is_admin = self.db_manager.fetch_one(
                "SELECT role FROM users WHERE id = ? AND role = 'admin'",
                (user_id,)
            )
            if not is_admin:
                logger.warning(f"Usuario ID: {user_id} intentó cerrar caja abierta por otro usuario")
                return False, "No tiene permisos para cerrar esta caja"
        
        # Cerrar la caja
        query = '''
            UPDATE cash_register 
            SET closing_time = ?, final_amount = ?, notes = ?, status = ?
            WHERE id = ?
        '''
        
        params = (
            datetime.datetime.now(),
            final_amount,
            notes,
            'closed',
            active_register['id']
        )
        
        success = self.db_manager.execute_query(query, params)
        
        if success:
            # Registrar el movimiento final
            self.add_movement(
                register_id=active_register['id'],
                amount=final_amount,
                movement_type='final',
                description="Monto final de caja",
                user_id=user_id
            )
            
            logger.info(f"Caja ID: {active_register['id']} cerrada por usuario ID: {user_id}. Monto final: {final_amount}")
            return True, self.calculate_register_balance(active_register['id'])
        else:
            logger.error(f"Error al cerrar caja ID: {active_register['id']}. Usuario ID: {user_id}")
            return False, "Error al cerrar la caja"
    
    def add_movement(self, register_id, amount, movement_type, description, user_id):
        query = '''
            INSERT INTO cash_movements (
                register_id, amount, type, description, time, user_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            register_id,
            amount,
            movement_type,
            description,
            datetime.datetime.now(),
            user_id
        )
        
        success = self.db_manager.execute_query(query, params)
        
        if success:
            logger.info(f"Movimiento de caja registrado. Tipo: {movement_type}, Monto: {amount}")
            return True, "Movimiento registrado correctamente"
        else:
            logger.error(f"Error al registrar movimiento de caja. Tipo: {movement_type}, Monto: {amount}")
            return False, "Error al registrar el movimiento"
    
    def get_movements(self, register_id):
        query = '''
            SELECT cm.*, u.username 
            FROM cash_movements cm
            LEFT JOIN users u ON cm.user_id = u.id
            WHERE cm.register_id = ?
            ORDER BY cm.time
        '''
        
        movements_data = self.db_manager.fetch_all(query, (register_id,))
        
        if not movements_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = [col[0] for col in self.db_manager.cursor.description]
        movements_list = []
        for movement in movements_data:
            movements_list.append(dict(zip(columns, movement)))
        
        return movements_list
    
    def calculate_register_balance(self, register_id):
        # Obtener datos de la caja
        query = "SELECT initial_amount, final_amount FROM cash_register WHERE id = ?"
        register_data = self.db_manager.fetch_one(query, (register_id,))
        
        if not register_data:
            return None
        
        initial_amount, final_amount = register_data
        
        # Obtener movimientos de entrada y salida
        query = '''
            SELECT 
                SUM(CASE WHEN type IN ('sale', 'deposit', 'initial') THEN amount ELSE 0 END) as inflows,
                SUM(CASE WHEN type IN ('withdrawal', 'expense', 'final') THEN amount ELSE 0 END) as outflows
            FROM cash_movements
            WHERE register_id = ?
        '''
        
        movement_data = self.db_manager.fetch_one(query, (register_id,))
        
        if not movement_data:
            inflows, outflows = 0, 0
        else:
            inflows, outflows = movement_data
            inflows = inflows or 0  # Convertir None a 0
            outflows = outflows or 0  # Convertir None a 0
        
        # Calcular el balance esperado
        expected_balance = initial_amount + inflows - outflows
        
        # Calcular la diferencia con el monto final (si existe)
        difference = 0
        if final_amount is not None:
            difference = final_amount - expected_balance
        
        return {
            'register_id': register_id,
            'initial_amount': initial_amount,
            'inflows': inflows,
            'outflows': outflows,
            'expected_balance': expected_balance,
            'final_amount': final_amount,
            'difference': difference
        }

# Clase para gestionar reportes
class ReportManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def sales_by_period(self, period_type, start_date, end_date):
        if period_type == 'daily':
            date_format = '%Y-%m-%d'
            date_extract = "strftime('%Y-%m-%d', date)"
        elif period_type == 'weekly':
            date_format = '%Y-%W'
            date_extract = "strftime('%Y-%W', date)"
        elif period_type == 'monthly':
            date_format = '%Y-%m'
            date_extract = "strftime('%Y-%m', date)"
        else:
            logger.error(f"Tipo de periodo inválido: {period_type}")
            return None
        
        query = f'''
            SELECT 
                {date_extract} as period,
                COUNT(*) as num_sales,
                SUM(total) as total_amount,
                AVG(total) as avg_sale,
                SUM(tax) as total_tax
            FROM sales
            WHERE date >= ? AND date <= ? AND payment_status != 'canceled'
            GROUP BY period
            ORDER BY period
        '''
        
        sales_data = self.db_manager.fetch_all(query, (start_date, end_date))
        
        if not sales_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = ['period', 'num_sales', 'total_amount', 'avg_sale', 'total_tax']
        sales_list = []
        for sale in sales_data:
            sale_dict = dict(zip(columns, sale))
            
            # Formatear el periodo según su tipo
            if period_type == 'daily':
                sale_dict['period_formatted'] = datetime.datetime.strptime(sale_dict['period'], '%Y-%m-%d').strftime('%d/%m/%Y')
            elif period_type == 'weekly':
                year, week = sale_dict['period'].split('-')
                sale_dict['period_formatted'] = f"Semana {week} de {year}"
            elif period_type == 'monthly':
                year, month = sale_dict['period'].split('-')
                month_name = datetime.datetime(int(year), int(month), 1).strftime('%B')
                sale_dict['period_formatted'] = f"{month_name} {year}"
            
            sales_list.append(sale_dict)
        
        return sales_list
    
    def sales_by_product(self, start_date, end_date, limit=10):
        query = '''
            SELECT 
                p.id, p.name, p.category,
                SUM(si.quantity) as total_quantity,
                SUM(si.total) as total_amount,
                COUNT(DISTINCT s.id) as num_sales
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.date >= ? AND s.date <= ? AND s.payment_status != 'canceled'
            GROUP BY p.id
            ORDER BY total_amount DESC
            LIMIT ?
        '''
        
        sales_data = self.db_manager.fetch_all(query, (start_date, end_date, limit))
        
        if not sales_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = ['id', 'name', 'category', 'total_quantity', 'total_amount', 'num_sales']
        sales_list = []
        for sale in sales_data:
            sales_list.append(dict(zip(columns, sale)))
        
        return sales_list
    
    def sales_by_category(self, start_date, end_date):
        query = '''
            SELECT 
                COALESCE(p.category, 'Sin categoría') as category,
                COUNT(DISTINCT s.id) as num_sales,
                SUM(si.total) as total_amount,
                SUM(si.quantity) as total_quantity
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.date >= ? AND s.date <= ? AND s.payment_status != 'canceled'
            GROUP BY category
            ORDER BY total_amount DESC
        '''
        
        sales_data = self.db_manager.fetch_all(query, (start_date, end_date))
        
        if not sales_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = ['category', 'num_sales', 'total_amount', 'total_quantity']
        sales_list = []
        for sale in sales_data:
            sales_list.append(dict(zip(columns, sale)))
        
        return sales_list
    
    def inventory_valuation(self):
        query = '''
            SELECT 
                id, name, barcode, category, 
                stock, cost,
                (stock * cost) as inventory_value,
                price,
                (price - cost) as margin,
                ((price - cost) / price * 100) as margin_percent
            FROM products
            WHERE is_active = 1
            ORDER BY inventory_value DESC
        '''
        
        inventory_data = self.db_manager.fetch_all(query)
        
        if not inventory_data:
            return []
        
        # Convertir a lista de diccionarios
        columns = ['id', 'name', 'barcode', 'category', 'stock', 'cost', 
                   'inventory_value', 'price', 'margin', 'margin_percent']
        inventory_list = []
        for item in inventory_data:
            inventory_list.append(dict(zip(columns, item)))
        
        # Calcular totales
        total_items = sum(item['stock'] for item in inventory_list)
        total_value = sum(item['inventory_value'] for item in inventory_list)
        
        return {
            'items': inventory_list,
            'total_items': total_items,
            'total_value': total_value
        }
    
    def export_report_to_csv(self, data, filename):
        try:
            if not data:
                logger.warning("Intento de exportar datos vacíos a CSV")
                return False, "No hay datos para exportar"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if isinstance(data, dict) and 'items' in data:
                    # Para reportes que tienen estructura {items: [...], totales...}
                    fieldnames = data['items'][0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for row in data['items']:
                        writer.writerow(row)
                    
                    # Agregar línea de totales
                    writer.writerow({})  # Línea en blanco
                    totals = {k: v for k, v in data.items() if k != 'items'}
                    for key, value in totals.items():
                        writer.writerow({'id': f'Total {key}', 'name': str(value)})
                else:
                    # Para reportes que son solo lista de diccionarios
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for row in data:
                        writer.writerow(row)
            
            logger.info(f"Reporte exportado a CSV: {filename}")
            return True, f"Reporte exportado exitosamente a {filename}"
            
        except Exception as e:
            logger.error(f"Error al exportar a CSV: {e}")
            return False, f"Error al exportar: {str(e)}"
    
    def generate_sales_chart(self, data, chart_type, filename):
        try:
            plt.figure(figsize=(12, 6))
            
            if chart_type == 'bar':
                periods = [item['period_formatted'] for item in data]
                values = [item['total_amount'] for item in data]
                
                plt.bar(periods, values)
                plt.xlabel('Periodo')
                plt.ylabel('Ventas Totales')
                plt.title('Ventas por Periodo')
                plt.xticks(rotation=45)
                
            elif chart_type == 'pie':
                labels = [item['category'] for item in data]
                sizes = [item['total_amount'] for item in data]
                
                plt.pie(sizes, labels=labels, autopct='%1.1f%%')
                plt.axis('equal')
                plt.title('Ventas por Categoría')
                
            elif chart_type == 'line':
                periods = [item['period_formatted'] for item in data]
                values = [item['total_amount'] for item in data]
                
                plt.plot(periods, values, marker='o')
                plt.xlabel('Periodo')
                plt.ylabel('Ventas Totales')
                plt.title('Tendencia de Ventas')
                plt.xticks(rotation=45)
                
            plt.tight_layout()
            plt.savefig(filename)
            plt.close()
            
            logger.info(f"Gráfico generado: {filename}")
            return True, f"Gráfico generado exitosamente: {filename}"
            
        except Exception as e:
            logger.error(f"Error al generar gráfico: {e}")
            return False, f"Error al generar gráfico: {str(e)}"
    
def generate_pdf_report(self, title, data, filename):
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, title)
        
        # Fecha del reporte
        c.setFont("Helvetica", 10)
        c.drawString(72, height - 90, f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y_position = height - 120
        
        # Si son datos con estructura especial (con 'items' y totales)
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
            
            # Encabezados
            c.setFont("Helvetica-Bold", 10)
            x_positions = [72, 200, 300, 400, 500]
            headers = list(items[0].keys())[:5]  # Limitamos a 5 columnas
            
            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y_position, header.capitalize())
            
            y_position -= 20
            c.setFont("Helvetica", 10)
            
            # Filas de datos
            for item in items[:20]:  # Limitamos a 20 filas
                for i, key in enumerate(headers):
                    value = str(item[key])
                    if len(value) > 25:  # Truncar valores muy largos
                        value = value[:22] + "..."
                    c.drawString(x_positions[i], y_position, value)
                y_position -= 15
                
                if y_position < 72:
                    c.showPage()
                    y_position = height - 72
            
            # Totales
            y_position -= 20
            c.setFont("Helvetica-Bold", 10)
            totals = {k: v for k, v in data.items() if k != 'items'}
            for key, value in totals.items():
                c.drawString(72, y_position, f"Total {key}: {value}")
                y_position -= 15
                
        else:
            # Para listas simples de diccionarios
            # Encabezados
            c.setFont("Helvetica-Bold", 10)
            x_positions = [72, 200, 300, 400, 500]
            headers = list(data[0].keys())[:5]  # Limitamos a 5 columnas
            
            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y_position, header.capitalize())
            
            y_position -= 20
            c.setFont("Helvetica", 10)
            
            # Filas de datos
            for item in data[:20]:  # Limitamos a 20 filas
                for i, key in enumerate(headers):
                    value = str(item[key])
                    if len(value) > 25:  # Truncar valores muy largos
                        value = value[:22] + "..."
                    c.drawString(x_positions[i], y_position, value)
                y_position -= 15
                
                # Comprobar si necesitamos una nueva página
                if y_position < 72:
                    c.showPage()
                    y_position = height - 72
                    c.setFont("Helvetica", 10)
            
            # Verificar si hay más de 20 filas de datos
            if len(data) > 20:
                y_position -= 10
                c.drawString(72, y_position, f"... y {len(data) - 20} filas más")
        
        # Pie de página
        y_position = 40
        c.setFont("Helvetica", 8)
        c.line(72, y_position + 10, width - 72, y_position + 10)
        c.drawString(72, y_position, "TV Pointer - Sistema de Gestión")
        c.drawString(width - 120, y_position, f"Página 1")
        
        # Guardar el PDF
        c.save()
        return True, f"Reporte generado exitosamente: {filename}"
        
    except Exception as e:
        return False, f"Error al generar el reporte: {str(e)}"
    # Clase para gestionar clientes
class CustomerManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_customer(self, name, email=None, phone=None, address=None, tax_id=None):
        query = '''
            INSERT INTO customers (name, email, phone, address, tax_id, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (name, email, phone, address, tax_id, datetime.datetime.now(), 1)
        success = self.db_manager.execute_query(query, params)
        
        if success:
            logger.info(f"Cliente agregado: {name}")
            return True, "Cliente agregado exitosamente"
        else:
            logger.error(f"Error al agregar cliente: {name}")
            return False, "Error al agregar el cliente"

    def update_customer(self, customer_id, name=None, email=None, phone=None, address=None, tax_id=None):
        query = '''
            UPDATE customers SET 
                name = ?, email = ?, phone = ?, address = ?, tax_id = ?, updated_at = ?
            WHERE id = ?
        '''
        params = (name, email, phone, address, tax_id, datetime.datetime.now(), customer_id)
        success = self.db_manager.execute_query(query, params)
        
        if success:
            logger.info(f"Cliente actualizado: ID {customer_id}")
            return True, "Cliente actualizado exitosamente"
        else:
            logger.error(f"Error al actualizar cliente: ID {customer_id}")
            return False, "Error al actualizar el cliente"

    def get_customer(self, customer_id):
        query = "SELECT * FROM customers WHERE id = ?"
        customer = self.db_manager.fetch_one(query, (customer_id,))
        
        if customer:
            columns = [col[0] for col in self.db_manager.cursor.description]
            customer_dict = dict(zip(columns, customer))
            return customer_dict
        else:
            return None

    def search_customers(self, search_term):
        query = '''
            SELECT * FROM customers 
            WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR tax_id LIKE ?
        '''
        search_term = f"%{search_term}%"
        customers = self.db_manager.fetch_all(query, (search_term, search_term, search_term, search_term))
        
        if customers:
            columns = [col[0] for col in self.db_manager.cursor.description]
            customers_list = [dict(zip(columns, customer)) for customer in customers]
            return customers_list
        else:
            return []

    def deactivate_customer(self, customer_id):
        query = "UPDATE customers SET is_active = 0 WHERE id = ?"
        success = self.db_manager.execute_query(query, (customer_id,))
        
        if success:
            logger.info(f"Cliente desactivado: ID {customer_id}")
            return True, "Cliente desactivado exitosamente"
        else:
            logger.error(f"Error al desactivar cliente: ID {customer_id}")
            return False, "Error al desactivar el cliente"

# Clase para gestionar facturas
class InvoiceManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_invoice(self, sale_id):
        sale = self.db_manager.fetch_one("SELECT * FROM sales WHERE id = ?", (sale_id,))
        if not sale:
            logger.error(f"Venta no encontrada para generar factura: ID {sale_id}")
            return False, "Venta no encontrada"

        # Obtener detalles de la venta
        items = self.db_manager.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,))
        customer = self.db_manager.fetch_one("SELECT * FROM customers WHERE id = ?", (sale[3],)) if sale[3] else None

        # Crear el PDF de la factura
        filename = f"factura_{sale_id}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Encabezado de la factura
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, "Factura de Venta")
        c.setFont("Helvetica", 10)
        c.drawString(72, height - 90, f"Fecha: {sale[2]}")
        c.drawString(72, height - 105, f"Venta No: {sale[1]}")
        if customer:
            c.drawString(72, height - 120, f"Cliente: {customer[1]}")
            c.drawString(72, height - 135, f"Email: {customer[2]}")
            c.drawString(72, height - 150, f"Teléfono: {customer[3]}")

        # Detalles de los productos
        c.setFont("Helvetica-Bold", 10)
        c.drawString(72, height - 180, "Producto")
        c.drawString(300, height - 180, "Cantidad")
        c.drawString(400, height - 180, "Precio")
        c.drawString(500, height - 180, "Total")
        c.setFont("Helvetica", 10)
        y_position = height - 195

        for item in items:
            c.drawString(72, y_position, item[2])
            c.drawString(300, y_position, str(item[3]))
            c.drawString(400, y_position, f"${item[4]:.2f}")
            c.drawString(500, y_position, f"${item[6]:.2f}")
            y_position -= 15

        # Totales
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, y_position - 20, "Subtotal:")
        c.drawString(500, y_position - 20, f"${sale[5]:.2f}")
        c.drawString(400, y_position - 35, "Impuesto:")
        c.drawString(500, y_position - 35, f"${sale[6]:.2f}")
        c.drawString(400, y_position - 50, "Total:")
        c.drawString(500, y_position - 50, f"${sale[8]:.2f}")

        # Pie de página
        y_position = 40
        c.setFont("Helvetica", 8)
        c.line(72, y_position + 10, width - 72, y_position + 10)
        c.drawString(72, y_position, "TV Pointer - Sistema de Gestión")
        c.drawString(width - 120, y_position, f"Página 1")

        # Guardar el PDF
        c.save()
        logger.info(f"Factura generada: {filename}")
        return True, filename

# Clase para gestionar el inventario
class InventoryManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def add_product(self, product_data):
        try:
            query = '''
                INSERT INTO products (
                    barcode, name, description, category, price, cost,
                    stock, min_stock, supplier_id, created_at, updated_at,
                    image_path, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            now = datetime.datetime.now()
            
            params = (
                product_data.get('barcode'),
                product_data.get('name'),
                product_data.get('description'),
                product_data.get('category'),
                product_data.get('price', 0),
                product_data.get('cost', 0),
                product_data.get('stock', 0),
                product_data.get('min_stock', 5),
                product_data.get('supplier_id'),
                now,
                now,
                product_data.get('image_path'),
                1
            )
            
            success = self.db_manager.execute_query(query, params)
            
            if success:
                logger.info(f"Producto agregado: {product_data.get('name')}")
                
                # Obtener el ID del producto recién insertado
                product_id = self.db_manager.fetch_one("SELECT last_insert_rowid()")[0]
                
                # Registrar movimiento de inventario inicial si hay stock
                initial_stock = product_data.get('stock', 0)
                if initial_stock > 0:
                    self.register_movement(
                        product_id=product_id,
                        movement_type="initial",
                        quantity=initial_stock,
                        reason="Stock inicial",
                        user_id=product_data.get('user_id'),
                        reference_id=None
                    )
                
                return True, product_id
            else:
                logger.error(f"Error al agregar producto: {product_data.get('name')}")
                return False, None
                
        except Exception as e:
            logger.error(f"Excepción al agregar producto: {e}")
            return False, None
    
    def update_product(self, product_id, product_data):
        try:
            query = '''
                UPDATE products SET 
                    barcode = ?,
                    name = ?,
                    description = ?,
                    category = ?,
                    price = ?,
                    cost = ?,
                    min_stock = ?,
                    supplier_id = ?,
                    updated_at = ?,
                    image_path = ?
                WHERE id = ?
            '''
            
            params = (
                product_data.get('barcode'),
                product_data.get('name'),
                product_data.get('description'),
                product_data.get('category'),
                product_data.get('price', 0),
                product_data.get('cost', 0),
                product_data.get('min_stock', 5),
                product_data.get('supplier_id'),
                datetime.datetime.now(),
                product_data.get('image_path'),
                product_id
            )
            
            success = self.db_manager.execute_query(query, params)
            
            if success:
                logger.info(f"Producto actualizado: ID {product_id}")
                return True
            else:
                logger.error(f"Error al actualizar producto: ID {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción al actualizar producto: {e}")
            return False
    
    def get_product(self, product_id):
        query = "SELECT * FROM products WHERE id = ?"
        product = self.db_manager.fetch_one(query, (product_id,))
        
        if product:
            # Convertir a diccionario para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            product_dict = dict(zip(columns, product))
            return product_dict
        else:
            return None
    
    def get_product_by_barcode(self, barcode):
        query = "SELECT * FROM products WHERE barcode = ?"
        product = self.db_manager.fetch_one(query, (barcode,))
        
        if product:
            # Convertir a diccionario para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            product_dict = dict(zip(columns, product))
            return product_dict
        else:
            return None
    
    def get_all_products(self, active_only=True):
        if active_only:
            query = "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
        else:
            query = "SELECT * FROM products ORDER BY name"
            
        products = self.db_manager.fetch_all(query)
        
        if products:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            products_list = []
            for product in products:
                products_list.append(dict(zip(columns, product)))
            return products_list
        else:
            return []
    
    def update_stock(self, product_id, new_quantity, movement_type, reason, user_id, reference_id=None):
        # Obtener stock actual
        current_stock = self.get_product(product_id).get('stock', 0)
        
        # Calcular la diferencia
        if movement_type in ['sale', 'adjustment_out', 'damage', 'expiry', 'transfer_out']:
            quantity_change = -abs(new_quantity)  # Negativo para salidas
        else:
            quantity_change = abs(new_quantity)   # Positivo para entradas
        
        # Actualizar el stock
        new_stock = current_stock + quantity_change
        
        query = "UPDATE products SET stock = ?, updated_at = ? WHERE id = ?"
        success = self.db_manager.execute_query(query, (new_stock, datetime.datetime.now(), product_id))
        
        if success:
            # Registrar el movimiento
            self.register_movement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=new_quantity,  # La cantidad original (no el cambio)
                reason=reason,
                user_id=user_id,
                reference_id=reference_id
            )
            
            logger.info(f"Stock actualizado para producto ID {product_id}. Nuevo stock: {new_stock}")
            return True, new_stock
        else:
            logger.error(f"Error al actualizar stock para producto ID {product_id}")
            return False, current_stock
    
    def register_movement(self, product_id, movement_type, quantity, reason, user_id, reference_id=None):
        query = '''
            INSERT INTO inventory_movements (
                product_id, date, type, quantity, reason, user_id, reference_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            product_id,
            datetime.datetime.now(),
            movement_type,
            quantity,
            reason,
            user_id,
            reference_id
        )
        
        success = self.db_manager.execute_query(query, params)
        
        if success:
            logger.info(f"Movimiento de inventario registrado: {movement_type} para producto ID {product_id}")
            return True
        else:
            logger.error(f"Error al registrar movimiento de inventario para producto ID {product_id}")
            return False
    
    def get_low_stock_products(self):
        query = '''
            SELECT * FROM products 
            WHERE stock <= min_stock AND is_active = 1
            ORDER BY (stock - min_stock), name
        '''
        
        products = self.db_manager.fetch_all(query)
        
        if products:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            products_list = []
            for product in products:
                products_list.append(dict(zip(columns, product)))
            return products_list
        else:
            return []
    
    def get_inventory_movements(self, product_id=None, start_date=None, end_date=None, movement_type=None):
        query_parts = ["SELECT im.*, p.name as product_name, u.username FROM inventory_movements im"]
        query_parts.append("LEFT JOIN products p ON im.product_id = p.id")
        query_parts.append("LEFT JOIN users u ON im.user_id = u.id")
        
        conditions = []
        params = []
        
        if product_id:
            conditions.append("im.product_id = ?")
            params.append(product_id)
        
        if start_date:
            conditions.append("im.date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("im.date <= ?")
            params.append(end_date)
        
        if movement_type:
            conditions.append("im.type = ?")
            params.append(movement_type)
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY im.date DESC")
        
        query = " ".join(query_parts)
        
        movements = self.db_manager.fetch_all(query, params if params else None)
        
        if movements:
            # Convertir a lista de diccionarios para facilitar su uso
            columns = [col[0] for col in self.db_manager.cursor.description]
            movements_list = []
            for movement in movements:
                movements_list.append(dict(zip(columns, movement)))
            return movements_list
        else:
            return []
        
class TPVApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema TPV - Heladería")
        self.root.geometry("1200x800")
        
        # Inicializar managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthManager(self.db_manager)
        self.inventory_manager = InventoryManager(self.db_manager)
        self.customer_manager = CustomerManager(self.db_manager)
        self.invoice_manager = InvoiceManager(self.db_manager)
        
        # Configurar el estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Crear el menú principal
        self.create_menu()
        
        # Crear el marco principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Mostrar la pantalla de login
        self.show_login_screen()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cerrar Sesión", command=self.logout)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Ventas
        sales_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventas", menu=sales_menu)
        sales_menu.add_command(label="Nueva Venta", command=self.show_pos_screen)
        sales_menu.add_command(label="Historial de Ventas", command=self.show_sales_history)
        
        # Menú Inventario
        inventory_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inventario", menu=inventory_menu)
        inventory_menu.add_command(label="Gestionar Productos", command=self.show_inventory_manager)
        inventory_menu.add_command(label="Stock Bajo", command=self.show_low_stock)
        
        # Menú Clientes
        customers_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Clientes", menu=customers_menu)
        customers_menu.add_command(label="Gestionar Clientes", command=self.show_customer_manager)

    def show_login_screen(self):
        # Limpiar el marco principal
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Crear el marco de login
        login_frame = ttk.LabelFrame(self.main_frame, text="Iniciar Sesión")
        login_frame.pack(expand=True, padx=20, pady=20)
        
        ttk.Label(login_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5)
        username_entry = ttk.Entry(login_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(login_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(login_frame, text="Iniciar Sesión", 
                  command=lambda: self.login(username_entry.get(), password_entry.get())
                  ).grid(row=2, column=0, columnspan=2, pady=10)

    def login(self, username, password):
        success, user = self.auth_manager.login(username, password)
        if success:
            self.current_user = user
            self.show_pos_screen()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def logout(self):
        self.auth_manager.logout()
        self.show_login_screen()

    def show_pos_screen(self):
        # Implementar la pantalla de punto de venta
        pass

    def show_sales_history(self):
        # Implementar la pantalla de historial de ventas
        pass

    def show_inventory_manager(self):
        # Implementar la pantalla de gestión de inventario
        pass

    def show_low_stock(self):
        # Implementar la pantalla de productos con stock bajo
        pass

    def show_customer_manager(self):
        # Implementar la pantalla de gestión de clientes
        pass

    def run(self):
        self.root.mainloop()
# Ejecución de la aplicación
if __name__ == "__main__":
    app = TPVApp()
    app.run()