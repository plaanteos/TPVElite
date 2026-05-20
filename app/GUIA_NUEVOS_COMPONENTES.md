# 🎯 Guía de Uso - Nuevos Componentes UX

**Fecha:** 9 de octubre de 2025  
**Para:** Desarrolladores y mantenedores

---

## 📚 Tabla de Contenidos

1. [ToastNotification](#1-toastnotification)
2. [ModernSearchBar](#2-modernsearchbar)
3. [Toggle de Tema](#3-toggle-de-tema)
4. [Ejemplos Prácticos](#4-ejemplos-prácticos)

---

## 1. ToastNotification

### 🎯 ¿Qué es?
Notificaciones temporales que aparecen en la esquina superior derecha de la pantalla con animaciones suaves.

### 📝 Sintaxis Básica

```python
ToastNotification(parent, mensaje, tipo, duracion).show()
```

### 🔧 Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | Requerido | Widget padre (normalmente `self.root`) |
| `mensaje` | str | Requerido | Texto a mostrar |
| `tipo` | str | `'info'` | Tipo: `'success'`, `'error'`, `'warning'`, `'info'` |
| `duracion` | int | `3000` | Milisegundos antes de cerrar |

### 🎨 Tipos de Toast

#### ✅ Success (Verde)
```python
ToastNotification(self.root, "¡Producto guardado con éxito!", 'success', 3000).show()
```
**Cuándo usar:**
- Operación completada exitosamente
- Guardado/actualización/eliminación exitosa
- Acción confirmada

#### ❌ Error (Rojo)
```python
ToastNotification(self.root, "Error al conectar con la base de datos", 'error', 4000).show()
```
**Cuándo usar:**
- Operación fallida
- Error de validación
- Problema de conexión

#### ⚠️ Warning (Amarillo)
```python
ToastNotification(self.root, "Stock bajo: Solo quedan 3 unidades", 'warning', 4000).show()
```
**Cuándo usar:**
- Advertencias no críticas
- Stock bajo
- Configuración recomendada

#### ℹ️ Info (Azul)
```python
ToastNotification(self.root, "Tema cambiado a modo claro", 'info', 2500).show()
```
**Cuándo usar:**
- Información general
- Cambios de estado
- Recordatorios

### 📋 Ejemplos Completos

#### Ejemplo 1: Después de guardar un producto
```python
def _save_product(self):
    try:
        # ... código para guardar producto ...
        
        if success:
            ToastNotification(
                self.root,
                f"Producto '{nombre}' guardado correctamente",
                'success',
                3000
            ).show()
        else:
            ToastNotification(
                self.root,
                f"Error: {error_message}",
                'error',
                4000
            ).show()
    except Exception as e:
        ToastNotification(
            self.root,
            f"Error inesperado: {str(e)}",
            'error',
            5000
        ).show()
```

#### Ejemplo 2: Validación de stock
```python
def _check_stock_levels(self):
    productos_bajo_stock = self.producto_service.obtener_productos_bajo_stock()
    
    if productos_bajo_stock:
        cantidad = len(productos_bajo_stock)
        ToastNotification(
            self.root,
            f"⚠️ {cantidad} producto{'s' if cantidad > 1 else ''} con stock bajo",
            'warning',
            4000
        ).show()
```

#### Ejemplo 3: Múltiples toasts (se apilan automáticamente)
```python
# Se muestran uno debajo del otro
ToastNotification(self.root, "Iniciando sincronización...", 'info', 2000).show()
self.root.after(1000, lambda: ToastNotification(
    self.root, "Descargando datos...", 'info', 2000).show())
self.root.after(2000, lambda: ToastNotification(
    self.root, "✓ Sincronización completada", 'success', 3000).show())
```

---

## 2. ModernSearchBar

### 🎯 ¿Qué es?
Barra de búsqueda moderna con placeholder animado, botón de limpiar y callback en tiempo real.

### 📝 Sintaxis Básica

```python
search_bar = ModernSearchBar(parent, placeholder="🔍 Buscar...", on_search=callback)
search_bar.pack(fill='x', pady=10)
```

### 🔧 Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `parent` | Widget | Requerido | Widget padre |
| `placeholder` | str | `"🔍 Buscar..."` | Texto placeholder |
| `on_search` | function | `None` | Callback al escribir |

### 🎯 Métodos Públicos

```python
# Obtener texto actual (sin placeholder)
texto = search_bar.get_text()

# Limpiar la búsqueda
search_bar.clear()
```

### 📋 Ejemplo Completo: Búsqueda de Productos

```python
def show_products_manager(self):
    """Muestra el gestor de productos con búsqueda en tiempo real"""
    self.clear_content()
    
    # Frame principal
    main_frame = tk.Frame(self.content_frame, bg=self.colors['bg_primary'])
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Título
    title_label = tk.Label(main_frame,
                          text="📦 Gestión de Productos",
                          font=('Segoe UI', 20, 'bold'),
                          bg=self.colors['bg_primary'],
                          fg=self.colors['text_primary'])
    title_label.pack(pady=(0, 20))
    
    # ✨ BARRA DE BÚSQUEDA MODERNA
    def on_search_products(text):
        """Se ejecuta cada vez que el usuario escribe"""
        self._filter_products_tree(products_tree, text)
    
    search_bar = ModernSearchBar(
        main_frame,
        placeholder="🔍 Buscar por nombre, categoría o SKU...",
        on_search=on_search_products
    )
    search_bar.pack(fill='x', pady=(0, 15))
    
    # Botones de acción
    buttons_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
    buttons_frame.pack(fill='x', pady=(0, 15))
    
    ModernButton(buttons_frame,
                text="➕ Nuevo Producto",
                style='success',
                command=lambda: self._new_product_dialog(products_tree)).pack(side='left', padx=5)
    
    ModernButton(buttons_frame,
                text="🔄 Actualizar",
                style='info',
                command=lambda: self._load_products_tree(products_tree)).pack(side='left', padx=5)
    
    # Tabla de productos
    tree_frame = tk.Frame(main_frame, bg=self.colors['bg_card'])
    tree_frame.pack(fill='both', expand=True)
    
    columns = ('ID', 'Nombre', 'Categoría', 'Precio', 'Stock', 'Estado')
    products_tree = ttk.Treeview(tree_frame,
                                columns=columns,
                                show='headings',
                                style='Modern.Treeview')
    
    for col in columns:
        products_tree.heading(col, text=col)
        products_tree.column(col, width=120)
    
    products_tree.pack(side='left', fill='both', expand=True)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=products_tree.yview)
    scrollbar.pack(side='right', fill='y')
    products_tree.configure(yscrollcommand=scrollbar.set)
    
    # Cargar productos
    self._load_products_tree(products_tree)


def _filter_products_tree(self, tree, search_text):
    """Filtra los productos en la tabla en tiempo real"""
    # Guardar todos los productos si no existen
    if not hasattr(self, '_all_products_cache'):
        self._all_products_cache = []
        for item in tree.get_children():
            values = tree.item(item)['values']
            self._all_products_cache.append(values)
    
    # Limpiar árbol
    for item in tree.get_children():
        tree.delete(item)
    
    # Filtrar y mostrar
    search_lower = search_text.lower()
    
    for values in self._all_products_cache:
        # Buscar en nombre, categoría y cualquier campo
        nombre = str(values[1]).lower()
        categoria = str(values[2]).lower()
        
        if (search_lower in nombre or 
            search_lower in categoria or 
            search_text == ""):
            tree.insert('', 'end', values=values)
```

### 🎨 Personalización

```python
# Con colores personalizados
search_bar = ModernSearchBar(
    parent,
    placeholder="🔍 Buscar clientes...",
    on_search=buscar_clientes,
    bg=ELITE_COLORS['bg_card']  # Fondo personalizado
)
```

---

## 3. Toggle de Tema

### 🎯 ¿Qué es?
Botón en el sidebar que cambia entre tema claro (☀️) y oscuro (🌙).

### 📝 Uso

```python
# Ya está integrado en el sidebar
# El usuario solo hace clic en el botón
```

### 🔧 Personalización Programática

```python
# Cambiar tema por código
self.toggle_theme()

# Obtener tema actual
current = self.current_theme  # 'dark' o 'light'

# Cambiar tema sin notificación
self.current_theme = 'light'
self.colors = LIGHT_COLORS
self._configure_elite_styles()
```

### 📊 Agregar Soporte de Tema a Tus Widgets

```python
def create_custom_card(self, parent):
    """Ejemplo de card que soporta ambos temas"""
    card = tk.Frame(parent,
                    bg=self.colors['bg_card'],  # ✅ Usa self.colors
                    highlightbackground=self.colors['border'],
                    highlightthickness=1)
    
    title = tk.Label(card,
                    text="Mi Card",
                    font=('Segoe UI', 14, 'bold'),
                    bg=self.colors['bg_card'],  # ✅ Usa self.colors
                    fg=self.colors['text_primary'])  # ✅ Usa self.colors
    title.pack(pady=10)
    
    return card
```

**❌ Evitar colores hardcodeados:**
```python
# MAL ❌
card = tk.Frame(parent, bg='#1e2531')  # Color fijo

# BIEN ✅
card = tk.Frame(parent, bg=self.colors['bg_card'])  # Dinámico
```

---

## 4. Ejemplos Prácticos

### 🛒 Ejemplo 1: Confirmar Venta con Toast

```python
def _process_sale(self, cart_tree):
    """Procesa una venta y muestra notificación"""
    try:
        if not self.current_cart:
            ToastNotification(
                self.root,
                "El carrito está vacío",
                'warning',
                2500
            ).show()
            return
        
        # Procesar venta...
        success, message, venta_id = self.venta_service.crear_venta(venta, user_id)
        
        if success:
            # ✅ Toast de éxito
            ToastNotification(
                self.root,
                f"✓ Venta #{venta.numero_venta} procesada con éxito",
                'success',
                4000
            ).show()
            
            # Limpiar carrito
            self.current_cart.clear()
            self._update_cart_tree(cart_tree)
        else:
            # ❌ Toast de error
            ToastNotification(
                self.root,
                f"Error al procesar venta: {message}",
                'error',
                4000
            ).show()
            
    except Exception as e:
        logger.error(f"Error en _process_sale: {e}")
        ToastNotification(
            self.root,
            f"Error inesperado: {str(e)}",
            'error',
            5000
        ).show()
```

### 👥 Ejemplo 2: Búsqueda de Usuarios

```python
def show_users_manager(self):
    """Gestión de usuarios con búsqueda en tiempo real"""
    self.clear_content()
    
    main_frame = tk.Frame(self.content_frame, bg=self.colors['bg_primary'])
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Título
    tk.Label(main_frame,
            text="👥 Gestión de Usuarios",
            font=('Segoe UI', 20, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary']).pack(pady=(0, 20))
    
    # Búsqueda
    def buscar_usuarios(texto):
        # Filtrar TreeView en tiempo real
        self._filter_users(users_tree, texto)
    
    search = ModernSearchBar(
        main_frame,
        placeholder="🔍 Buscar por nombre o email...",
        on_search=buscar_usuarios
    )
    search.pack(fill='x', pady=(0, 15))
    
    # Botones
    btn_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
    btn_frame.pack(fill='x', pady=(0, 15))
    
    ModernButton(btn_frame, "➕ Nuevo Usuario", 'success',
                lambda: self._new_user_dialog(users_tree)).pack(side='left', padx=5)
    
    # TreeView
    users_tree = ttk.Treeview(main_frame,
                             columns=('ID', 'Nombre', 'Email', 'Rol', 'Estado'),
                             show='headings',
                             style='Modern.Treeview')
    users_tree.pack(fill='both', expand=True)
    
    # Cargar usuarios
    self._load_users(users_tree)

def _filter_users(self, tree, search_text):
    """Filtra usuarios en tiempo real"""
    if not search_text:
        self._load_users(tree)
        return
    
    # Limpiar
    for item in tree.get_children():
        tree.delete(item)
    
    # Obtener todos los usuarios
    usuarios = self.auth_service.listar_usuarios()
    
    # Filtrar
    search_lower = search_text.lower()
    for user in usuarios:
        if (search_lower in user.nombre.lower() or
            search_lower in user.email.lower()):
            tree.insert('', 'end', values=(
                user.id,
                user.nombre,
                user.email,
                user.rol,
                'Activo' if user.activo else 'Inactivo'
            ))
```

### 📊 Ejemplo 3: Dashboard con Notificaciones

```python
def show_dashboard(self):
    """Dashboard con notificaciones de alertas"""
    self.clear_content()
    self.current_screen = "dashboard"
    
    # ... código del dashboard ...
    
    # Verificar alertas automáticamente
    self._check_dashboard_alerts()

def _check_dashboard_alerts(self):
    """Verifica y muestra alertas importantes"""
    try:
        # Verificar productos con stock bajo
        productos_bajo_stock = self.producto_service.obtener_productos_bajo_stock()
        
        if productos_bajo_stock:
            count = len(productos_bajo_stock)
            ToastNotification(
                self.root,
                f"⚠️ {count} producto{'s' if count > 1 else ''} con stock bajo",
                'warning',
                5000
            ).show()
        
        # Verificar ventas pendientes de procesar
        ventas_pendientes = self.venta_service.obtener_ventas_pendientes()
        
        if ventas_pendientes and len(ventas_pendientes) > 10:
            ToastNotification(
                self.root,
                f"ℹ️ Hay {len(ventas_pendientes)} ventas pendientes",
                'info',
                4000
            ).show()
            
    except Exception as e:
        logger.error(f"Error verificando alertas: {e}")
```

---

## 💡 Mejores Prácticas

### ✅ DO (Hacer)

1. **Usar toasts para feedback inmediato:**
   ```python
   # Bien ✅
   ToastNotification(self.root, "Guardado", 'success').show()
   ```

2. **Duración apropiada según tipo:**
   ```python
   # Success/Info: 2-3 segundos
   ToastNotification(self.root, "Listo", 'success', 2500).show()
   
   # Error/Warning: 4-5 segundos (más tiempo para leer)
   ToastNotification(self.root, "Error largo...", 'error', 5000).show()
   ```

3. **Mensajes concisos y claros:**
   ```python
   # Bien ✅
   "✓ Producto guardado correctamente"
   
   # Mal ❌
   "El sistema ha procedido a guardar el registro del producto en la base de datos"
   ```

### ❌ DON'T (Evitar)

1. **No abuses de los toasts:**
   ```python
   # Mal ❌ - Demasiados toasts
   for producto in productos:
       ToastNotification(self.root, f"Procesando {producto}", 'info').show()
   
   # Bien ✅ - Un toast al final
   ToastNotification(self.root, f"{len(productos)} productos procesados", 'success').show()
   ```

2. **No uses toasts para errores críticos:**
   ```python
   # Mal ❌
   ToastNotification(self.root, "Base de datos corrupta", 'error').show()
   
   # Bien ✅
   messagebox.showerror("Error Crítico", "Base de datos corrupta. La aplicación se cerrará.")
   ```

3. **No hagas búsquedas pesadas en el callback:**
   ```python
   # Mal ❌
   def on_search(text):
       # Consulta lenta a BD en cada tecla
       productos = db.query_slow(text)
   
   # Bien ✅
   def on_search(text):
       # Filtrar cache local (rápido)
       filtrar_cache(text)
   ```

---

## 🐛 Troubleshooting

### Problema: Toast no se muestra

**Causa:** Widget padre no existe o está oculto  
**Solución:**
```python
# Verificar que self.root existe
if self.root and self.root.winfo_exists():
    ToastNotification(self.root, "Mensaje", 'info').show()
```

### Problema: SearchBar no filtra

**Causa:** Callback no está conectado  
**Solución:**
```python
# Asegúrate de pasar on_search
search = ModernSearchBar(parent, on_search=tu_funcion)
```

### Problema: Tema no cambia

**Causa:** Widgets usan colores hardcodeados  
**Solución:**
```python
# Cambiar de:
widget = tk.Frame(parent, bg='#1e2531')

# A:
widget = tk.Frame(parent, bg=self.colors['bg_card'])
```

---

## 📚 Referencias

- **AnimationHelper:** Ver `main.py` líneas 99-267
- **ToastNotification:** Ver `main.py` líneas 270-423
- **ModernSearchBar:** Ver `main.py` líneas 584-703
- **ELITE_COLORS:** Ver `main.py` líneas 44-91
- **LIGHT_COLORS:** Ver `main.py` líneas 93-138

---

**✨ ¡Disfruta creando interfaces modernas!**
