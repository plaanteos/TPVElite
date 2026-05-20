# 📘 Manual de Usuario
## Sistema TPV - Heladería Profesional v2.0.0

---

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Inicio de Sesión](#inicio-de-sesión)
3. [Dashboard](#dashboard)
4. [Punto de Venta](#punto-de-venta)
5. [Gestión de Productos](#gestión-de-productos)
6. [Gestión de Pedidos](#gestión-de-pedidos)
7. [Reportes](#reportes)
8. [Configuración](#configuración)
9. [Preguntas Frecuentes](#preguntas-frecuentes)
10. [Solución de Problemas](#solución-de-problemas)

---

## Introducción

Bienvenido al Sistema TPV - Heladería Profesional, una solución completa para la gestión de su negocio.

### Características Principales

- ✅ Gestión de ventas en tiempo real
- ✅ Control de inventario automatizado
- ✅ Múltiples usuarios con diferentes roles
- ✅ Reportes y estadísticas detalladas
- ✅ Backups automáticos
- ✅ Interfaz intuitiva y moderna

---

## Inicio de Sesión

### Primera Vez

Al iniciar la aplicación por primera vez, use estas credenciales:

- **Usuario:** admin
- **Contraseña:** admin123

⚠️ **IMPORTANTE:** Cambie la contraseña inmediatamente después del primer inicio.

### Recuperar Contraseña

Si olvidó su contraseña, contacte al administrador del sistema.

---

## Dashboard

El dashboard es la pantalla principal que muestra:

### Tarjetas de Estadísticas

1. **Ventas Hoy**
   - Total de ventas del día actual
   - Actualización en tiempo real

2. **Ventas del Mes**
   - Acumulado del mes en curso
   - Comparación con mes anterior

3. **Productos Bajo Stock**
   - Cantidad de productos que necesitan reabastecimiento
   - Click para ver detalles

### Gráfico de Tendencias

- Muestra las ventas de los últimos 7 días
- Permite identificar patrones y tendencias

---

## Punto de Venta

### Realizar una Venta

#### Paso 1: Agregar Productos

1. Busque el producto en la lista o use la barra de búsqueda
2. Doble click en el producto para agregarlo al carrito
3. O seleccione y presione el botón "➕ Agregar"

#### Paso 2: Ajustar Cantidades

- Los productos se agregan de uno en uno
- Para aumentar cantidad, vuelva a agregar el mismo producto
- Para quitar, seleccione en el carrito y presione "➖ Quitar"

#### Paso 3: Verificar Total

- El total se calcula automáticamente
- Revise que todos los productos sean correctos

#### Paso 4: Procesar Venta

1. Click en "💳 Procesar Venta"
2. Confirme la transacción
3. Se generará un número de venta único
4. El inventario se actualizará automáticamente

### Acciones Adicionales

- **Vaciar Carrito:** Elimina todos los productos del carrito
- **Buscar:** Filtra productos por nombre
- **Cancelar:** Vuelve al menú principal

---

## Gestión de Productos

### Agregar Nuevo Producto

1. Click en "Productos" en el menú lateral
2. Click en "Nuevo Producto"
3. Complete los campos:
   - **Nombre:** Nombre del producto (obligatorio)
   - **Descripción:** Descripción detallada
   - **Categoría:** Seleccione o cree una categoría
   - **Precio:** Precio de venta (obligatorio)
   - **Costo:** Costo del producto
   - **Stock Inicial:** Cantidad inicial en inventario
   - **Stock Mínimo:** Nivel para alerta de reabastecimiento
   - **Código de Barras:** Para escaneo rápido
4. Click en "Guardar"

### Editar Producto

1. Seleccione el producto en la lista
2. Click en "Editar"
3. Modifique los campos necesarios
4. Click en "Guardar Cambios"

### Eliminar Producto

1. Seleccione el producto
2. Click en "Eliminar"
3. Confirme la acción

⚠️ **Nota:** No se puede eliminar un producto con stock o que tenga ventas registradas.

### Ajustar Stock

1. Seleccione el producto
2. Click en "Ajustar Stock"
3. Ingrese la nueva cantidad
4. Seleccione el tipo de movimiento:
   - Compra
   - Ajuste
   - Merma
   - Devolución
5. Agregue notas (opcional)
6. Confirme

---

## Gestión de Pedidos

### Crear Pedido a Proveedor

1. Click en "Pedidos" en el menú lateral
2. Click en "Nuevo Pedido"
3. Seleccione el proveedor
4. Agregue productos al pedido:
   - Busque el producto
   - Ingrese la cantidad
   - Click en "Agregar"
5. Revise el total
6. Click en "Crear Pedido"

### Recibir Pedido

1. Vaya a la lista de pedidos
2. Seleccione el pedido pendiente
3. Click en "Recibir Pedido"
4. Verifique las cantidades
5. Confirme la recepción
6. El stock se actualizará automáticamente

### Cancelar Pedido

1. Seleccione el pedido
2. Click en "Cancelar Pedido"
3. Ingrese el motivo (opcional)
4. Confirme

---

## Reportes

### Tipos de Reportes

#### 1. Reporte de Ventas

- **Por Período:** Diario, semanal, mensual, personalizado
- **Por Producto:** Productos más vendidos
- **Por Método de Pago:** Efectivo, tarjeta, etc.
- **Por Usuario:** Ventas por empleado

#### 2. Reporte de Inventario

- **Stock Actual:** Lista completa de productos con stock
- **Productos Bajo Stock:** Productos que necesitan reabastecimiento
- **Valor de Inventario:** Valor total del inventario
- **Movimientos:** Historial de entradas y salidas

#### 3. Reporte Financiero

- **Ventas vs Costos:** Análisis de rentabilidad
- **Margen de Beneficio:** Por producto o general
- **Tendencias:** Proyecciones de ventas

### Generar Reporte

1. Seleccione el tipo de reporte
2. Configure los filtros:
   - Fecha de inicio
   - Fecha de fin
   - Categorías (opcional)
   - Otros filtros específicos
3. Click en "Generar Reporte"
4. Visualice el reporte en pantalla

### Exportar Reporte

- **PDF:** Para impresión o envío
- **Excel:** Para análisis adicional
- **CSV:** Para importar a otros sistemas

---

## Gestión de Usuarios

### Acceso a Usuarios

**Requisitos**: Rol de Administrador

1. Click en "👥 Usuarios" en el menú lateral
2. O presione **Ctrl+7**

### Pantalla Principal

La pantalla de gestión de usuarios muestra:

- **Lista de usuarios**: Todos los usuarios del sistema
- **Buscador**: Filtra por usuario, nombre o email
- **Paginación**: Controla cuántos usuarios ver por página (25/50/100/200)
- **Información mostrada**:
  - ID del usuario
  - Nombre de usuario (username)
  - Nombre completo
  - Email
  - Rol (admin/vendedor/supervisor)
  - Estado (Activo/Inactivo)
  - Fecha de creación

### Crear Nuevo Usuario

1. Click en **"➕ Nuevo Usuario"**
2. Complete los campos obligatorios (*):
   - **Usuario (username)**: Mínimo 3 caracteres
   - **Nombre Completo**: Nombre y apellido
   - **Email**: Formato válido (opcional pero recomendado)
   - **Contraseña**: Mínimo 6 caracteres
   - **Confirmar Contraseña**: Debe coincidir
   - **Rol**: admin/vendedor/supervisor

3. Click en **"💾 Guardar"**

**Validaciones**:
- Usuario único (no puede existir otro igual)
- Contraseñas deben coincidir
- Email con formato válido
- Contraseña hasheada con bcrypt

### Editar Usuario

1. Seleccione un usuario de la lista
2. Click en **"✏️ Editar"**
3. Modifique los campos deseados:
   - Nombre completo
   - Email
   - Rol
   - Estado (Activo/Inactivo)

4. Click en **"💾 Guardar Cambios"**

**Nota**: El nombre de usuario (username) no puede ser modificado después de creado.

### Resetear Contraseña

1. Seleccione un usuario de la lista
2. Click en **"🔑 Resetear Contraseña"**
3. Ingrese nueva contraseña (mínimo 6 caracteres)
4. Confirme la contraseña
5. Click en **"💾 Guardar"**

**Seguridad**: Las contraseñas se almacenan con hash bcrypt, nunca en texto plano.

### Desactivar Usuario

1. Seleccione un usuario de la lista
2. Click en **"🗑️ Eliminar"**
3. Confirme la acción

**Importante**:
- Los usuarios no se eliminan permanentemente, solo se desactivan
- No puede eliminar su propia cuenta
- Usuarios inactivos no pueden iniciar sesión
- Los datos históricos (ventas, movimientos) se conservan

### Roles y Permisos

#### Administrador (admin)
- Acceso completo al sistema
- Gestión de usuarios
- Configuración del sistema
- Todos los reportes
- Respaldos de base de datos

#### Supervisor
- Gestión de ventas
- Gestión de productos
- Reportes completos
- No puede gestionar usuarios

#### Vendedor
- Crear y consultar ventas
- Consultar productos
- Reportes básicos
- No puede modificar configuración

### Búsqueda y Filtros

**Buscador rápido**:
- Escribe en el campo de búsqueda
- Presiona **Enter** o click en 🔍
- Busca en: username, nombre completo y email

**Limpiar búsqueda**:
- Borra el texto del buscador
- Presiona Enter
- Se muestran todos los usuarios

### Paginación

**Controles disponibles**:
- **◀ Anterior**: Ir a página anterior
- **Siguiente ▶**: Ir a página siguiente
- **Mostrar X registros**: Cambia cantidad por página
  - 25 registros (predeterminado)
  - 50 registros
  - 100 registros
  - 200 registros

**Información de página**: "Página X de Y (Z registros)"

### Atajos de Teclado

- **Ctrl+7**: Abrir gestión de usuarios
- **F5**: Actualizar lista de usuarios
- **Ctrl+N**: Nuevo usuario (cuando esté enfocada la ventana)
- **Esc**: Cancelar diálogo actual

### Buenas Prácticas

1. **Contraseñas seguras**:
   - Mínimo 8 caracteres (recomendado)
   - Combinar letras, números y símbolos
   - Cambiar contraseñas periódicamente

2. **Roles adecuados**:
   - Asignar el rol mínimo necesario
   - Revisar permisos regularmente
   - No crear múltiples cuentas admin innecesarias

3. **Mantenimiento**:
   - Desactivar usuarios que ya no trabajan
   - Revisar últimos accesos periódicamente
   - Mantener emails actualizados

4. **Auditoría**:
   - Revisar logs de sistema regularmente
   - Verificar intentos de login fallidos
   - Controlar creaciones de usuarios

### Solución de Problemas

**No puedo crear usuario con cierto username**:
- El username ya existe (incluso si está inactivo)
- Use un nombre de usuario diferente

**Error al resetear contraseña**:
- Verifique que las contraseñas coincidan
- Contraseña debe tener mínimo 6 caracteres

**No veo el botón "Usuarios" en el menú**:
- Esta función requiere rol de Administrador
- Contacte a su administrador para obtener permisos

**Usuario bloqueado por intentos fallidos**:
- Un administrador debe reactivar la cuenta
- Editar el usuario y marcar como "Activo"
- Luego resetear la contraseña

---

## Configuración

### Perfil de Usuario

1. Click en su nombre en el header
2. Seleccione "Mi Perfil"
3. Puede cambiar:
   - Contraseña
   - Email
   - Nombre y apellido

### Configuración de la Aplicación

#### Tema Visual

```

- Seleccione entre diferentes esquemas de color
- Ajuste el tamaño de fuente
- Active/desactive animaciones

#### Impresoras

- Configure impresora para tickets
- Configure impresora para facturas
- Tamaño de papel
- Márgenes

#### Backups

- **Automáticos:** Configure la frecuencia
- **Manuales:** Realice backup en cualquier momento
- **Restaurar:** Desde un backup anterior

#### Moneda y Formato

- Símbolo de moneda
- Separador decimal
- Separador de miles
- Formato de fecha

---

## Preguntas Frecuentes

### ¿Cómo cambio mi contraseña?

1. Click en su nombre en el header
2. Seleccione "Cambiar Contraseña"
3. Ingrese contraseña actual
4. Ingrese nueva contraseña (2 veces)
5. Confirme

### ¿Puedo usar el sistema sin internet?

Sí, el sistema funciona completamente offline. Solo necesita internet si desea usar funciones de sincronización en la nube (próximamente).

### ¿Dónde se guardan los backups?

Los backups se guardan en:
```
C:\Users\[TuUsuario]\AppData\Roaming\HeladeriaPOS\backups\
```

### ¿Puedo usar múltiples computadoras?

Sí, puede instalar el sistema en varias computadoras. Para sincronizar datos, use la función de backup/restauración.

### ¿El sistema maneja múltiples sucursales?

La versión actual es para una sola sucursal. El modo multi-tienda estará disponible en la versión 2.2.

---

## Solución de Problemas

### La aplicación no inicia

1. Verifique que Python esté instalado
2. Verifique que todas las dependencias estén instaladas
3. Revise el archivo de log en `logs/`
4. Intente ejecutar desde la consola para ver errores

### Error de base de datos

1. Verifique permisos de escritura en la carpeta
2. Restaure desde un backup reciente
3. Contacte soporte técnico

### Impresora no responde

1. Verifique que la impresora esté encendida
2. Verifique los drivers
3. Reconfigure la impresora en Configuración

### Pantalla en blanco o congelada

1. Cierre y vuelva a abrir la aplicación
2. Verifique actualizaciones disponibles
3. Reinicie el equipo

### Stock inconsistente

1. Revise el historial de movimientos
2. Realice un ajuste de inventario
3. Contacte soporte si persiste

---

## Soporte Técnico

### Contacto

- 📧 Email: soporte@ejemplo.com
- 📱 WhatsApp: +123456789
- 🌐 Web: https://ejemplo.com/soporte
- 🕐 Horario: Lunes a Viernes, 9:00 - 18:00

### Información para Soporte

Al contactar soporte, proporcione:

1. Versión del sistema
2. Sistema operativo
3. Descripción del problema
4. Pasos para reproducir el error
5. Archivos de log (si es posible)

---

## Actualizaciones

Para verificar actualizaciones:

1. Vaya a Configuración
2. Click en "Buscar Actualizaciones"
3. Siga las instrucciones en pantalla

⚠️ **Importante:** Realice un backup antes de actualizar.

---

## Glosario

- **TPV:** Terminal Punto de Venta
- **SKU:** Stock Keeping Unit (Unidad de Mantenimiento de Stock)
- **Backup:** Copia de seguridad de datos
- **Stock:** Inventario disponible
- **Margen:** Diferencia entre precio y costo

---

**Versión del Manual:** 2.0.0  
**Fecha de Actualización:** Octubre 2025  
**Copyright © 2025 - Todos los derechos reservados**
