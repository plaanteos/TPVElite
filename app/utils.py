"""
Sistema TPV para Heladería - Módulo de Utilidades
Autor: Jesus
Versión: 2.0.0
Descripción: Funciones de utilidad y helpers
"""

import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib
import re


def setup_logging(log_dir: str = 'logs', level: str = 'INFO'):
    """
    Configura el sistema de logging profesional
    
    Args:
        log_dir: Directorio donde guardar los logs
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Crear directorio de logs si no existe
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar el formato del log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Obtener el logger raíz
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Handler para archivo (con rotación)
    log_file = os.path.join(log_dir, f'tpv_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    logger.info("=" * 80)
    logger.info("Sistema de logging inicializado correctamente")
    logger.info("=" * 80)


def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """
    Carga la configuración desde un archivo JSON
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Diccionario con la configuración
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging.info(f"Configuración cargada desde: {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear el archivo de configuración: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str = 'config.json'):
    """
    Guarda la configuración en un archivo JSON
    
    Args:
        config: Diccionario con la configuración
        config_path: Ruta donde guardar el archivo
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.info(f"Configuración guardada en: {config_path}")
    except Exception as e:
        logging.error(f"Error al guardar la configuración: {e}")


def resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta a un recurso, funciona para dev y para PyInstaller
    
    Args:
        relative_path: Ruta relativa al recurso
        
    Returns:
        Ruta absoluta al recurso
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def format_currency(amount: float, currency: str = '$') -> str:
    """
    Formatea un número como moneda
    
    Args:
        amount: Cantidad a formatear
        currency: Símbolo de moneda
        
    Returns:
        String formateado como moneda
    """
    return f"{currency}{amount:,.2f}"


def format_datetime(dt: datetime, format: str = '%d/%m/%Y %H:%M:%S') -> str:
    """
    Formatea un datetime como string
    
    Args:
        dt: Datetime a formatear
        format: Formato deseado
        
    Returns:
        String formateado
    """
    return dt.strftime(format)


def validate_email(email: str) -> bool:
    """
    Valida el formato de un email
    
    Args:
        email: Email a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Valida el formato de un teléfono
    
    Args:
        phone: Teléfono a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    # Eliminar espacios y caracteres especiales
    phone = re.sub(r'[^\d]', '', phone)
    # Validar que tenga entre 10 y 15 dígitos
    return 10 <= len(phone) <= 15


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres no válidos
    
    Args:
        filename: Nombre de archivo a sanitizar
        
    Returns:
        Nombre de archivo sanitizado
    """
    # Remover caracteres no válidos
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Reemplazar espacios por guiones bajos
    filename = filename.replace(' ', '_')
    return filename


def generate_invoice_number(prefix: str = 'INV') -> str:
    """
    Genera un número de factura único
    
    Args:
        prefix: Prefijo para el número de factura
        
    Returns:
        Número de factura único
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"


def generate_order_number(prefix: str = 'ORD') -> str:
    """
    Genera un número de pedido único
    
    Args:
        prefix: Prefijo para el número de pedido
        
    Returns:
        Número de pedido único
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"


def calculate_percentage(part: float, total: float) -> float:
    """
    Calcula el porcentaje de una parte respecto al total
    
    Args:
        part: Parte
        total: Total
        
    Returns:
        Porcentaje
    """
    if total == 0:
        return 0.0
    return (part / total) * 100


def truncate_text(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """
    Trunca un texto a una longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def create_backup_filename(base_name: str = 'backup') -> str:
    """
    Crea un nombre de archivo para backup con timestamp
    
    Args:
        base_name: Nombre base del archivo
        
    Returns:
        Nombre de archivo con timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.db"


def ensure_directory(directory: str):
    """
    Asegura que un directorio exista, si no lo crea
    
    Args:
        directory: Ruta del directorio
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Directorio creado: {directory}")


def get_app_data_dir(app_name: str = 'HeladeriaPOS') -> str:
    """
    Obtiene el directorio de datos de la aplicación
    
    Args:
        app_name: Nombre de la aplicación
        
    Returns:
        Ruta al directorio de datos
    """
    if sys.platform == 'win32':
        # Windows
        app_data = os.getenv('APPDATA')
        if app_data:
            return os.path.join(app_data, app_name)
    elif sys.platform == 'darwin':
        # macOS
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:
        # Linux y otros
        return os.path.join(os.path.expanduser('~'), f'.{app_name.lower()}')
    
    # Fallback
    return os.path.join(os.path.expanduser('~'), app_name)


class Validator:
    """Clase para validaciones comunes"""
    
    @staticmethod
    def is_positive_number(value: Any) -> bool:
        """Verifica si un valor es un número positivo"""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_positive_integer(value: Any) -> bool:
        """Verifica si un valor es un entero positivo"""
        try:
            return int(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_non_negative_integer(value: Any) -> bool:
        """Verifica si un valor es un entero no negativo"""
        try:
            return int(value) >= 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_non_empty_string(value: Any) -> bool:
        """Verifica si un valor es una cadena no vacía"""
        return isinstance(value, str) and len(value.strip()) > 0
    
    @staticmethod
    def is_valid_price(value: Any) -> bool:
        """Verifica si un valor es un precio válido"""
        try:
            price = float(value)
            return price >= 0 and round(price, 2) == price
        except (ValueError, TypeError):
            return False


class ColorHelper:
    """Helper para trabajar con colores"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convierte un color hexadecimal a RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convierte un color RGB a hexadecimal"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    @staticmethod
    def darken_color(hex_color: str, factor: float = 0.8) -> str:
        """Oscurece un color"""
        r, g, b = ColorHelper.hex_to_rgb(hex_color)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return ColorHelper.rgb_to_hex(r, g, b)
    
    @staticmethod
    def lighten_color(hex_color: str, factor: float = 1.2) -> str:
        """Aclara un color"""
        r, g, b = ColorHelper.hex_to_rgb(hex_color)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return ColorHelper.rgb_to_hex(r, g, b)
