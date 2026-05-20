# 🍦 Sistema TPV - Heladería Profesional

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

Sistema profesional de Punto de Venta (TPV) diseñado específicamente para heladerías, con interfaz moderna, gestión completa de inventario, ventas y reportes avanzados.

## ✨ Características Principales

### 📊 Dashboard Interactivo
- Visualización en tiempo real de ventas y métricas
- Gráficos de tendencias de los últimos 7 días
- Alertas de productos con stock bajo
- Estadísticas consolidadas del día y del mes

### 🛒 Punto de Venta
- Interfaz intuitiva y rápida para procesamiento de ventas
- Búsqueda rápida de productos
- Carrito de compras visual
- Múltiples métodos de pago
- Generación automática de facturas

### 📦 Gestión de Inventario
- Control completo de productos
- Alertas automáticas de stock bajo
- Historial de movimientos de inventario
- Categorización de productos
- Gestión de precios y costos

### 👥 Sistema de Usuarios
- Autenticación segura con hash SHA-256
- Roles y permisos (Administrador, Supervisor, Cajero)
- Registro de sesiones
- Control de acceso por funcionalidad

### 📈 Reportes y Análisis
- Reportes de ventas por período
- Análisis de productos más vendidos
- Informes de inventario
- Exportación a PDF y Excel
- Gráficos estadísticos avanzados

### 💾 Backups Automáticos
- Respaldo automático de base de datos
- Programación personalizable
- Restauración de backups
- Gestión de versiones

## 🚀 Instalación

### Requisitos del Sistema

- Python 3.8 o superior
- Windows 7/8/10/11 (32 o 64 bits)
- 4 GB de RAM mínimo
- 100 MB de espacio en disco

### Instalación desde Código Fuente

1. **Clonar el repositorio**
```bash
git clone https://github.com/usuario/heladeria-tpv.git
cd heladeria-tpv
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Ejecutar la aplicación**
```bash
cd app
python main.py
```

### Instalación desde Ejecutable

1. Descargar el instalador desde [Releases](https://github.com/usuario/heladeria-tpv/releases)
2. Ejecutar el instalador
3. Seguir las instrucciones en pantalla
4. Iniciar la aplicación desde el acceso directo

## 📖 Uso

### Primer Inicio

Al iniciar la aplicación por primera vez, use las siguientes credenciales:

- **Usuario:** `admin`
- **Contraseña:** `admin123`

**⚠️ IMPORTANTE:** Cambie la contraseña inmediatamente después del primer inicio.

### Navegación

La aplicación cuenta con un menú lateral intuitivo con las siguientes secciones:

- **🏠 Inicio:** Dashboard con estadísticas principales
- **🛒 Nueva Venta:** Procesar ventas rápidamente
- **📊 Ventas:** Historial y gestión de ventas
- **📦 Productos:** Administrar inventario
- **📋 Pedidos:** Gestión de pedidos a proveedores
- **📈 Reportes:** Generar informes y análisis
- **⚙️ Configuración:** Personalizar la aplicación
- **❓ Ayuda:** Manual de usuario y soporte

### Procesamiento de Ventas

1. Ir a **Nueva Venta**
2. Buscar o seleccionar productos
3. Ajustar cantidades según necesidad
4. Verificar el total
5. Procesar la venta
6. Generar factura (opcional)

### Gestión de Productos

1. Ir a **Productos**
2. Click en **Nuevo Producto**
3. Completar información:
   - Nombre
   - Categoría
   - Precio y costo
   - Stock inicial
   - Stock mínimo
4. Guardar

### Generación de Reportes

1. Ir a **Reportes**
2. Seleccionar tipo de reporte
3. Definir período de tiempo
4. Generar reporte
5. Exportar (PDF/Excel)

## 🏗️ Arquitectura

El proyecto sigue una arquitectura modular y profesional:

```
app/
├── main.py              # Aplicación principal
├── database.py          # Gestor de base de datos
├── models.py            # Modelos de datos
├── services.py          # Lógica de negocio
├── utils.py             # Utilidades y helpers
├── config.json          # Configuración
└── logs/                # Archivos de log
```

### Tecnologías Utilizadas

- **Frontend:** Tkinter con estilos personalizados
- **Backend:** Python 3.8+
- **Base de Datos:** SQLite3 con optimizaciones
- **Gráficos:** Matplotlib
- **Reportes:** ReportLab (PDF)
- **Logging:** Logging con rotación de archivos

### Patrones de Diseño

- **Singleton:** Para gestión de base de datos
- **MVC:** Separación de lógica y presentación
- **Service Layer:** Capa de servicios para lógica de negocio
- **Repository:** Abstracción de acceso a datos

## 🔧 Configuración

La aplicación se configura mediante el archivo `config.json`:

```json
{
    "app": {
        "name": "Sistema TPV Heladería",
        "version": "2.0.0"
    },
    "colors": {
        "primary": "#2C3E50",
        "accent": "#3498DB",
        "success": "#27AE60"
    },
    "security": {
        "session_timeout_minutes": 60,
        "max_login_attempts": 3
    }
}
```

## 📊 Base de Datos

### Esquema

- **usuarios:** Usuarios del sistema
- **productos:** Catálogo de productos
- **ventas:** Registro de ventas
- **detalles_venta:** Items de cada venta
- **pedidos:** Pedidos a proveedores
- **movimientos_inventario:** Trazabilidad de inventario
- **sesiones:** Control de sesiones activas

### Backups

Los backups se generan automáticamente cada 24 horas y se almacenan en:
```
%APPDATA%\HeladeriaPOS\backups\
```

## 🔐 Seguridad

- Contraseñas hasheadas con SHA-256
- Bloqueo automático después de 3 intentos fallidos
- Timeout de sesión configurable
- Validación de inputs en todas las entradas
- Logs de auditoría completos
- Transacciones atómicas en base de datos

## 📝 Logs

Los logs se almacenan en `logs/` con rotación automática:

- Tamaño máximo: 10 MB por archivo
- Archivos de backup: 5
- Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL

## � Testing

El proyecto incluye una suite completa de tests unitarios e integración.

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar con cobertura
pytest tests/ --cov=. --cov-report=html

# Ejecutar tests específicos
pytest tests/test_auth.py -v
pytest tests/test_productos.py -v
pytest tests/test_ventas.py -v
```

### Cobertura de Tests

- **test_auth.py**: 17 tests de autenticación
  - Login/logout
  - Gestión de contraseñas con bcrypt
  - Sesiones y permisos
  
- **test_productos.py**: 25+ tests de productos
  - CRUD completo
  - Gestión de stock
  - Validaciones
  
- **test_ventas.py**: 20+ tests de ventas
  - Procesamiento de ventas
  - Cálculos y totales
  - Métodos de pago

**Total**: 62+ tests unitarios e integración

### Ver Reporte de Cobertura

```bash
pytest tests/ --cov=. --cov-report=html
# Abrir: htmlcov/index.html
```

Consulta [TESTING.md](TESTING.md) para documentación completa de testing.

## �🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Jesus**

- GitHub: [@usuario](https://github.com/usuario)
- Email: contacto@ejemplo.com

## 🙏 Agradecimientos

- A todos los que han contribuido al proyecto
- A la comunidad de Python
- A los usuarios que han proporcionado feedback

## 📞 Soporte

Para soporte técnico:

- 📧 Email: soporte@ejemplo.com
- 📱 WhatsApp: +123456789
- 🌐 Web: https://ejemplo.com/soporte

## 🗺️ Roadmap

### Versión 2.1 (Próximamente)
- [ ] Integración con impresoras térmicas
- [ ] App móvil complementaria
- [ ] Sincronización en la nube
- [ ] Lector de código de barras
- [ ] Integración con pasarelas de pago

### Versión 2.2
- [ ] Modo multi-tienda
- [ ] CRM integrado
- [ ] Programa de fidelización
- [ ] API REST para integraciones
- [ ] Dashboard web

## 📸 Capturas de Pantalla

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Punto de Venta
![POS](screenshots/pos.png)

### Gestión de Productos
![Productos](screenshots/productos.png)

---

⭐️ Si este proyecto te ha sido útil, por favor considera darle una estrella en GitHub!
