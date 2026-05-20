# 🧪 Guía de Testing - Sistema TPV Heladería

## Descripción General

Este proyecto incluye una suite completa de tests unitarios e integración utilizando **pytest** para asegurar la calidad y confiabilidad del código.

## Estructura de Tests

```
app/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures y configuración compartida
│   ├── pytest.ini           # Configuración de pytest
│   ├── test_auth.py         # Tests de autenticación
│   ├── test_productos.py    # Tests de gestión de productos
│   └── test_ventas.py       # Tests de ventas
```

## Instalación de Dependencias

```bash
pip install pytest pytest-cov bcrypt
```

O usando el archivo de requerimientos:

```bash
pip install -r requirements.txt
```

## Ejecutar Tests

### Ejecutar todos los tests

```bash
pytest tests/
```

### Ejecutar tests con salida verbose

```bash
pytest tests/ -v
```

### Ejecutar un archivo específico

```bash
pytest tests/test_auth.py -v
```

### Ejecutar un test específico

```bash
pytest tests/test_auth.py::TestAuthService::test_login_exitoso -v
```

### Ejecutar solo tests de una marca específica

```bash
pytest tests/ -m unit          # Solo tests unitarios
pytest tests/ -m integration   # Solo tests de integración
pytest tests/ -m slow          # Solo tests lentos
```

## Cobertura de Tests

### Generar reporte de cobertura en consola

```bash
pytest tests/ --cov=. --cov-report=term
```

### Generar reporte HTML

```bash
pytest tests/ --cov=. --cov-report=html
```

El reporte se generará en `htmlcov/index.html`, ábrelo en tu navegador.

### Excluir archivos de cobertura

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

## Descripción de Tests

### test_auth.py (17 tests)

Tests para el sistema de autenticación:

- ✅ **Login exitoso**: Verifica credenciales correctas
- ✅ **Login fallido**: Contraseña incorrecta, usuario inexistente, usuario inactivo
- ✅ **Logout**: Cierre de sesión
- ✅ **Verificación bcrypt**: Hash y verificación de contraseñas
- ✅ **Persistencia de sesión**: Manejo de usuarios activos
- ✅ **Múltiples intentos**: Bloqueo por intentos fallidos
- ✅ **Integración completa**: Flujos de login/logout/cambio de contraseña

**Comandos útiles:**
```bash
pytest tests/test_auth.py -v
pytest tests/test_auth.py -k "login" -v  # Solo tests de login
```

### test_productos.py (25+ tests)

Tests para gestión de productos:

- ✅ **CRUD**: Crear, leer, actualizar, eliminar productos
- ✅ **Stock**: Ajustes de entrada, salida, merma
- ✅ **Validación**: Precios, cantidades, campos requeridos
- ✅ **Búsqueda**: Por código de barras, nombre, categoría
- ✅ **Stock bajo**: Alertas de stock mínimo
- ✅ **Integración**: Flujos completos de gestión

**Comandos útiles:**
```bash
pytest tests/test_productos.py -v
pytest tests/test_productos.py -k "stock" -v  # Solo tests de stock
```

### test_ventas.py (20+ tests)

Tests para sistema de ventas:

- ✅ **Crear venta**: Procesamiento completo
- ✅ **Stock**: Actualización automática
- ✅ **Cálculos**: Subtotales, impuestos, totales
- ✅ **Validación**: Stock suficiente, datos válidos
- ✅ **Cancelación**: Restauración de stock
- ✅ **Métodos de pago**: Efectivo, tarjeta, transferencia
- ✅ **Números únicos**: Generación de números de venta

**Comandos útiles:**
```bash
pytest tests/test_ventas.py -v
pytest tests/test_ventas.py -k "venta" -v
```

## Configuración de pytest (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Tests unitarios rápidos
    integration: Tests de integración
    slow: Tests que tardan más tiempo
```

## Fixtures Disponibles (conftest.py)

### Fixtures principales:

- **`test_db_path`**: Crea una base de datos temporal para tests
- **`db_manager`**: DatabaseManager con esquema de prueba
- **`auth_service`**: Servicio de autenticación configurado
- **`producto_service`**: Servicio de productos configurado
- **`venta_service`**: Servicio de ventas configurado
- **`test_user`**: Usuario admin de prueba
- **`test_vendedor`**: Usuario vendedor de prueba

### Datos de prueba:

Cada test recibe una base de datos limpia con:
- 2 usuarios: `admin` (admin123) y `vendedor1` (vendedor123)
- 5 productos de ejemplo
- 2 proveedores de ejemplo

## Buenas Prácticas

### 1. Aislamiento de Tests

Cada test debe ser independiente y no depender del resultado de otros:

```python
@pytest.mark.unit
def test_crear_producto(producto_service):
    # Arrange
    datos = {...}
    
    # Act
    success, message, producto = producto_service.crear_producto(**datos)
    
    # Assert
    assert success is True
    assert producto.nombre == datos['nombre']
```

### 2. Uso de Fixtures

Reutiliza fixtures en lugar de crear datos manualmente:

```python
def test_login(auth_service, test_user):
    success, message, usuario = auth_service.login("admin", "admin123")
    assert usuario.username == test_user.username
```

### 3. Tests Descriptivos

Nombres claros que indican qué se está probando:

```python
def test_ajustar_stock_salida_mayor_que_disponible(producto_service):
    # Test que verifica que no se puede retirar más stock del disponible
    pass
```

### 4. Marcado de Tests

Usa marcadores para organizar tests:

```python
@pytest.mark.unit
def test_rapido():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_complejo():
    pass
```

## Debugging de Tests

### Ver output completo

```bash
pytest tests/ -v -s  # -s muestra prints
```

### Detener en el primer error

```bash
pytest tests/ -x
```

### Modo de debugging interactivo

```bash
pytest tests/ --pdb  # Inicia debugger en error
```

### Ver logs capturados

```bash
pytest tests/ -v --log-cli-level=DEBUG
```

## Integración Continua (CI)

Para ejecutar tests en CI/CD, agrega este comando:

```bash
pytest tests/ --cov=. --cov-report=xml --cov-report=term
```

## Troubleshooting

### Error: "No module named 'pytest'"

```bash
pip install pytest pytest-cov
```

### Error: "No module named 'bcrypt'"

```bash
pip install bcrypt
```

### Tests fallan por problemas de base de datos

Los tests usan bases de datos temporales en memoria. Si hay problemas:

1. Verifica que la estructura en `conftest.py` coincida con `database.py`
2. Asegúrate de que todos los campos obligatorios estén en los INSERT
3. Revisa los logs: `pytest tests/ -v -s`

### Tests muy lentos

```bash
pytest tests/ -m "not slow"  # Excluir tests lentos
```

## Métricas Actuales

- **Total de tests**: 62+
- **Tests pasando**: 10 (en progreso)
- **Cobertura objetivo**: >40%
- **Tiempo de ejecución**: ~95 segundos

## Próximos Pasos

1. ✅ Crear infraestructura de tests
2. ✅ Implementar tests unitarios básicos
3. ⚠️ Corregir tests fallidos (en progreso)
4. ⚠️ Alcanzar 40%+ cobertura
5. ⏳ Agregar tests de UI (futuro)
6. ⏳ Tests de performance (futuro)

## Recursos

- [Documentación oficial de pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [bcrypt documentation](https://github.com/pyca/bcrypt/)

---

**Última actualización**: Febrero 2025
**Mantenedor**: Equipo de Desarrollo
