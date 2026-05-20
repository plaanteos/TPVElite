import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import time
import threading
import shutil
import os
import sys
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # Directorio temporal del ejecutable
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

db_path = resource_path('heladeria.db')
conn = sqlite3.connect(db_path)
class HeladeriaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Heladería")
        self.root.geometry("1000x550")
        self.root.state('zoomed')
        
        # Intentar establecer un ícono para la ventana
        try:
            self.root.iconbitmap(resource_path('icono.ico'))
        except:
            pass  # Si no encuentra el ícono, continúa sin él
            
        # Obtener el directorio de datos de la aplicación
        if getattr(sys, 'frozen', False):
            # Si es un ejecutable
            self.app_data_dir = os.path.join(os.getenv('APPDATA'), 'HeladeriaPOS')
        else:
            # Si se ejecuta desde Python
            self.app_data_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Crear el directorio si no existe
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
            
        # Configurar el directorio de datos de la aplicación
        self.app_data_dir = os.path.join(os.path.expanduser('~'), 'HeladeriaPOS')
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        if not os.path.exists(os.path.join(self.app_data_dir, 'backups')):
            os.makedirs(os.path.join(self.app_data_dir, 'backups'))
            
        # Crear el directorio para pedidos
        self.pedidos_dir = os.path.join(self.app_data_dir, 'pedidos')
        if not os.path.exists(self.pedidos_dir):
            os.makedirs(self.pedidos_dir)
            
        self.pedidos_actuales = []
            
        self.colors = {
            'primary': '#FF0000',
            'secondary': '#0000FF',
            'accent': '#FFD700',
            'bg_light': '#F0F8FF',
            'text_dark': '#000080',
            'success': '#228B22',  # Verde para estado normal
            'warning': '#FFA500',  # Amarillo para estado medio
            'error': '#DC143C'     # Rojo para estado bajo
        }
        # Aumentar tamaño de fuente general
        self.fonts = {
            'normal': ('Arial', 12),
            'bold': ('Arial', 12, 'bold'),
            'large': ('Arial', 14),
            'large_bold': ('Arial', 14, 'bold'),
            'extra_large': ('Arial', 16, 'bold')
        }
        self.configure_styles()
        self.crear_base_datos()
        self.producto_seleccionado = tk.StringVar()
        self.cantidad = tk.StringVar()
        self.precio = tk.StringVar()
        self.pedidos_actuales = []
        self.root.configure(bg=self.colors['bg_light'])
        self.crear_menu()
        self.main_frame = ttk.Frame(self.root, padding="10", style='Main.TFrame')
        self.main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.mostrar_stock()
        self.mostrar_gestion_backups() 
        self.realizar_backup()
        
        # Agregar opción de tema oscuro/claro
        self.tema = tk.StringVar(value='claro')
        self.tema.trace('w', self.cambiar_tema)
        self.crear_menu_tema()
        
        # Agregar notificaciones dinámicas
        self.notificaciones = tk.StringVar()
        self.notificaciones_label = ttk.Label(self.root, textvariable=self.notificaciones, style='Info.TLabel')
        self.notificaciones_label.grid(row=2, column=0, sticky="ew")
        
        # Configurar el diseño responsivo
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def cambiar_tema(self, *args):
        if self.tema.get() == 'oscuro':
            self.colors = {
                'primary': '#1E1E1E',
                'secondary': '#2E2E2E',
                'accent': '#FFD700',
                'bg_light': '#2E2E2E',
                'text_dark': '#FFFFFF',
                'success': '#228B22',
                'warning': '#FFA500',
                'error': '#DC143C'
            }
        else:
            self.colors = {
                'primary': '#FF0000',
                'secondary': '#0000FF',
                'accent': '#FFD700',
                'bg_light': '#F0F8FF',
                'text_dark': '#000080',
                'success': '#228B22',
                'warning': '#FFA500',
                'error': '#DC143C'
            }
        self.configure_styles()
        self.root.configure(bg=self.colors['bg_light'])
        self.mostrar_stock()

    def crear_menu_tema(self):
        menu_tema = tk.Menu(self.root)
        self.root.config(menu=menu_tema)
        tema_menu = tk.Menu(menu_tema, tearoff=0)
        menu_tema.add_cascade(label="Tema", menu=tema_menu)
        tema_menu.add_radiobutton(label="Claro", variable=self.tema, value='claro')
        tema_menu.add_radiobutton(label="Oscuro", variable=self.tema, value='oscuro')

    def agregar_busqueda(self, tree, frame):
        try:
            # Frame principal de búsqueda
            search_frame = ttk.Frame(frame)
            search_frame.grid(row=1, column=0, pady=5, sticky="ew")
            
            # Configurar el grid
            frame.grid_columnconfigure(0, weight=1)
            search_frame.grid_columnconfigure(1, weight=1)
            
            # Label y entrada de búsqueda
            ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, padx=5)
            
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var)
            search_entry.grid(row=0, column=1, padx=5, sticky="ew")
            
            # Filtro por columna
            ttk.Label(search_frame, text="Filtrar por:").grid(row=0, column=2, padx=5)
            
            # Obtener columnas
            columns = tree["columns"]
            column_names = [tree.heading(col)["text"] for col in columns]
            
            # Combobox para columnas
            filter_cb = ttk.Combobox(search_frame, values=column_names, state='readonly',
                                    width=15)
            if column_names:
                filter_cb.set(column_names[0])
            filter_cb.grid(row=0, column=3, padx=5)
            
            # Coincidencia exacta
            exact_match_var = tk.BooleanVar()
            ttk.Checkbutton(search_frame, text="Coincidencia exacta",
                            variable=exact_match_var).grid(row=0, column=4, padx=5)
            
            # Etiqueta resultados
            results_label = ttk.Label(search_frame, text="Mostrando todos los elementos")
            results_label.grid(row=1, column=1, columnspan=3, padx=5, sticky="w")
            
            def filtrar(*args):
                search_term = search_entry.get().lower()
                selected_column = filter_cb.current()  # Obtiene el índice de la columna seleccionada
                exact_match = exact_match_var.get()
                
                # Limpiar árbol
                for item in tree.get_children():
                    tree.delete(item)
                
                # Obtener datos
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                c.execute('SELECT id, nombre, precio, stock, stock_minimo FROM productos')
                productos = c.fetchall()
                conn.close()
                
                # Contador de resultados
                matches = 0
                
                # Filtrar y mostrar productos
                for producto in productos:
                    # Convertir el valor de la columna seleccionada a string y lowercase
                    valor_columna = str(producto[selected_column]).lower()
                    
                    # Verificar coincidencia según el tipo de búsqueda
                    if exact_match:
                        coincide = valor_columna == search_term
                    else:
                        coincide = search_term in valor_columna
                    
                    if coincide or not search_term:  # Mostrar todo si no hay término de búsqueda
                        stock_actual = producto[3]
                        stock_minimo = producto[4]
                        
                        if stock_actual > stock_minimo:
                            estado = "✅ SUPERIOR"
                            tag = 'normal'
                        elif stock_actual == stock_minimo:
                            estado = "⚠️ MEDIO"
                            tag = 'medio'
                        else:
                            estado = "❌ BAJO"
                            tag = 'bajo'
                        
                        tree.insert('', 'end',
                                values=(producto[0],
                                        producto[1],
                                        f"${producto[2]:.2f}",
                                        producto[3],
                                        producto[4],
                                        estado),
                                tags=(tag,))
                        matches += 1
                search_entry.bind('<KeyRelease>', filtrar)
                # Actualizar etiqueta de resultados
                if search_term:
                    results_label.config(text=f"Se encontraron {matches} resultado(s)")
                else:
                    results_label.config(text="Mostrando todos los elementos")
            
            def clear_search():
                search_var.set('')
                filter_cb.set(column_names[0])
                exact_match_var.set(False)
                filtrar()
                search_entry.focus()
            
            # Guardar todos los items originales con sus tags
            self._all_items = [(item, tree.item(item)['values'], tree.item(item)['tags']) 
                            for item in tree.get_children('')]
            
            # Botones
            ttk.Button(search_frame, text="Buscar", 
                    command=filtrar).grid(row=0, column=5, padx=5)
            
            ttk.Button(search_frame, text="Limpiar", 
                    command=clear_search).grid(row=1, column=5, padx=5)
            
            # Eventos
            search_entry.bind('<Return>', lambda e: filtrar())
            filter_cb.bind('<<ComboboxSelected>>', lambda e: filtrar())
            search_entry.bind('<Escape>', lambda e: clear_search())
            
            # Foco inicial
            search_entry.focus()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar búsqueda: {str(e)}")
            print(f"Error en agregar_busqueda: {e}")
        
    def configure_styles(self):
        style = ttk.Style()
        style.configure('Main.TFrame', background=self.colors['bg_light'])
        style.configure('Menu.TButton',
                       background=self.colors['primary'],
                       foreground='Black',
                       padding=(20, 10),
                       font=self.fonts['large_bold'])
        style.configure('Title.TLabelframe',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dark'])
        style.configure('Title.TLabelframe.Label',
                       font=self.fonts['large_bold'],
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dark'])
        style.configure('Action.TButton',
                       background=self.colors['secondary'],
                       foreground='Black',
                       padding=(15, 8),
                       font=self.fonts['normal'])
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='Black',
                       padding=(15, 8),
                       font=self.fonts['normal'])
        style.configure('Danger.TButton',
                       background=self.colors['error'],
                       foreground='Black',
                       padding=(15, 8),
                       font=self.fonts['normal'])
        style.configure('Info.TLabel',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dark'],
                       font=self.fonts['normal'])
        style.configure('Title.TLabelframe', background='#f0f0f0')
        style.configure('Title.TLabelframe.Label', font=('Helvetica', 10, 'bold'))
        style.configure('Action.TButton', background='#4CAF50', padding=5)
        style.configure('Success.TButton', background='#2196F3', padding=5)
        style.configure('Danger.TButton', background='#f44336', padding=5)
        style.configure('Custom.Treeview', rowheight=25)
        style.configure('Custom.Treeview.Heading', font=('Helvetica', 9, 'bold'))

    def crear_base_datos(self):
        db_path = os.path.join(self.app_data_dir, 'heladeria.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS productos
                    (id INTEGER PRIMARY KEY,
                     nombre TEXT NOT NULL UNIQUE,
                     precio REAL NOT NULL CHECK(precio > 0),
                     stock INTEGER NOT NULL CHECK(stock >= 0),
                     stock_minimo INTEGER NOT NULL CHECK(stock_minimo >= 0))''')
        # Nueva tabla para informes
        c.execute('''CREATE TABLE IF NOT EXISTS informes
                    (id INTEGER PRIMARY KEY,
                     fecha TIMESTAMP,
                     tipo TEXT,
                     contenido TEXT)''')
        conn.commit()
        conn.close()
        
    def cualquier_metodo_que_use_db(self):
        db_path = os.path.join(self.app_data_dir, 'heladeria.db')
        conn = sqlite3.connect(db_path)

    def crear_menu(self):
        # Frame del menú con fondo personalizado
        self.menu_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.menu_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.menu_frame.grid_columnconfigure(5, weight=1)
        
        # Botones del menú con iconos
        menu_buttons = [
            ("📊 Ver Stock", self.mostrar_stock),
            ("🔄 Actualizar Stock", self.mostrar_actualizar_stock),
            ("🛍️ Realizar Pedidos", self.mostrar_pedidos),
            ("📈 Informes", self.generar_informes),
            ("💾 Backups", self.mostrar_gestion_backups),
            ("❓ Ayuda", self.mostrar_ayuda)
        ]
        
        for i, (text, command) in enumerate(menu_buttons):
            btn = ttk.Button(self.menu_frame, text=text, 
                           command=command,
                           style='Menu.TButton')
            btn.grid(row=0, column=i, padx=5, pady=5)
    
    def mostrar_stock(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        list_frame = ttk.LabelFrame(self.main_frame, text="Stock Actual",
                                  padding="10", style='Title.TLabelframe')
        list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dark'],
                       fieldbackground=self.colors['bg_light'],
                       font=self.fonts['normal'])  # Fuente más grande para el Treeview
        style.configure("Custom.Treeview.Heading",
                       font=self.fonts['bold'])    # Fuente más grande para los encabezados
        self.tree = ttk.Treeview(list_frame,
                                columns=('ID', 'Nombre', 'Precio', 'Stock', 'Stock Mín', 'Estado'),
                                show='headings',
                                style="Custom.Treeview")
        self.tree.heading('ID', text='ID')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Precio', text='Precio')
        self.tree.heading('Stock', text='Stock Actual')
        self.tree.heading('Stock Mín', text='Stock Mínimo')
        self.tree.heading('Estado', text='Estado')
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.actualizar_lista_stock()
        self.agregar_busqueda(self.tree, list_frame)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Botón para eliminar producto
        ttk.Button(list_frame, text="Eliminar Producto", command=self.eliminar_producto, 
                   style='Danger.TButton').grid(row=2, column=0, pady=5)

    def actualizar_lista_stock(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = sqlite3.connect('heladeria.db')
        c = conn.cursor()
        c.execute('SELECT id, nombre, precio, stock, stock_minimo FROM productos')
        productos = c.fetchall()
        conn.close()
        for producto in productos:
            # Determinar el estado y el color basado en el nivel de stock
            stock_actual = producto[3]
            stock_minimo = producto[4]
            if stock_actual > stock_minimo :  # Más del stock mínimo
                estado = "✅ SUPERIOR"
                tag = 'normal'
            elif stock_actual == stock_minimo:      # igual al stock mínimo
                estado = "⚠️ MEDIO"
                tag = 'medio'
            else:                                  # Menos al stock mínimo
                estado = "❌ BAJO"
                tag = 'bajo'
                
            self.tree.insert('', 'end',
                           values=(producto[0], producto[1], f"${producto[2]:.2f}", 
                                  producto[3], producto[4], estado),
                           tags=(tag,))
            
        # Configurar los colores y fuentes para cada estado
        self.tree.tag_configure('normal',
                              foreground=self.colors['success'],
                              font=self.fonts['extra_large'])
        self.tree.tag_configure('medio',
                              foreground=self.colors['warning'],
                              font=self.fonts['extra_large'])
        self.tree.tag_configure('bajo',
                              foreground=self.colors['error'],
                              font=self.fonts['extra_large'])

    def eliminar_producto(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")
            return
            
        # Obtener los datos del producto seleccionado
        item_values = self.tree.item(selected_item, 'values')
        producto_nombre = item_values[1]  # El nombre está en la segunda columna
        
        # Mostrar mensaje de confirmación
        if messagebox.askyesno("Confirmar eliminación", 
                            f"¿Está seguro que desea eliminar el producto '{producto_nombre}'?"):
            item_id = item_values[0]  # El ID está en la primera columna
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()
            try:
                c.execute('DELETE FROM productos WHERE id = ?', (item_id,))
                conn.commit()
                self.mostrar_notificacion(f"Producto '{producto_nombre}' eliminado correctamente.")
                self.actualizar_lista_stock()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar el producto: {str(e)}")
            finally:
                conn.close()

    def mostrar_actualizar_stock(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        update_frame = ttk.LabelFrame(self.main_frame, text="Actualizar Stock",
                                    padding="10", style='Title.TLabelframe')
        update_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Sección para agregar nuevo producto
        ttk.Label(update_frame, text="Agregar Nuevo Producto",
                style='Info.TLabel').grid(row=0, column=0, columnspan=2, pady=10)
        labels = ['Nombre:', 'Precio:', 'Stock Inicial:', 'Stock Mínimo:']
        entries = []
        for i, label in enumerate(labels):
            ttk.Label(update_frame, text=label,
                    style='Info.TLabel').grid(row=i+1, column=0, padx=5, pady=5)
            entry = ttk.Entry(update_frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5)
            entries.append(entry)

        def agregar_producto():
            try:
                nombre = entries[0].get().strip()
                precio = float(entries[1].get())
                stock_inicial = int(entries[2].get())
                stock_minimo = int(entries[3].get())
                if not nombre:
                    raise ValueError("El nombre del producto no puede estar vacío")
                if precio <= 0:
                    raise ValueError("El precio debe ser un número positivo")
                if stock_inicial < 0 or stock_minimo < 0:
                    raise ValueError("El stock y el stock mínimo no pueden ser negativos")
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                c.execute('SELECT * FROM productos WHERE nombre = ?', (nombre,))
                producto_existente = c.fetchone()
                if producto_existente:
                    mensaje = f"""El producto ya existe con los siguientes detalles:
    ID: {producto_existente[0]}
    Nombre: {producto_existente[1]}
    Precio: ${producto_existente[2]:.2f}
    Stock actual: {producto_existente[3]}
    Stock mínimo: {producto_existente[4]}"""
                    messagebox.showerror("Error - Producto Duplicado", mensaje)
                    conn.close()
                    return
                c.execute('''INSERT INTO productos (nombre, precio, stock, stock_minimo)
                            VALUES (?, ?, ?, ?)''',
                        (nombre, precio, stock_inicial, stock_minimo))
                conn.commit()
                conn.close()
                self.mostrar_notificacion("Producto agregado correctamente")
                for entry in entries:
                    entry.delete(0, tk.END)
                actualizar_combo_productos()
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")

        ttk.Button(update_frame, text="Agregar Producto",
                command=agregar_producto,
                style='Success.TButton').grid(row=5, column=0, columnspan=2, pady=10)
        
        # Separador entre secciones
        ttk.Separator(update_frame, orient='horizontal').grid(row=6, column=0,
                                                            columnspan=2, sticky='ew', pady=10)
        
        # Sección para actualizar producto existente
        ttk.Label(update_frame, text="Actualizar Stock Existente",
                style='Info.TLabel').grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Label(update_frame, text="Producto:",
                style='Info.TLabel').grid(row=8, column=0, padx=5, pady=5)
        producto_cb = ttk.Combobox(update_frame)
        producto_cb.grid(row=8, column=1, padx=5, pady=5)
        
        # Label para mostrar el precio actual
        precio_actual_label = ttk.Label(update_frame, text="Precio actual: $0.00",
                                    style='Info.TLabel')
        precio_actual_label.grid(row=9, column=0, columnspan=2, pady=5)

        def actualizar_combo_productos():
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()
            c.execute('SELECT nombre FROM productos')
            productos = [row[0] for row in c.fetchall()]
            conn.close()
            producto_cb['values'] = productos

        def on_producto_selected(event):
            producto = producto_cb.get()
            if producto:
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                c.execute('SELECT precio FROM productos WHERE nombre = ?', (producto,))
                precio = c.fetchone()
                conn.close()
                if precio:
                    precio_actual_label.config(text=f"Precio actual: ${precio[0]:.2f}")
                    producto_cb.precio_actual = precio[0]

        producto_cb.bind('<<ComboboxSelected>>', on_producto_selected)
        actualizar_combo_productos()

        ttk.Label(update_frame, text="Nuevo Stock:",
                style='Info.TLabel').grid(row=10, column=0, padx=5, pady=5)
        nuevo_stock_entry = ttk.Entry(update_frame)
        nuevo_stock_entry.grid(row=10, column=1, padx=5, pady=5)
        
        ttk.Label(update_frame, text="Nuevo Precio:",
                style='Info.TLabel').grid(row=11, column=0, padx=5, pady=5)
        nuevo_precio_entry = ttk.Entry(update_frame)
        nuevo_precio_entry.grid(row=11, column=1, padx=5, pady=5)

        # Label para mostrar el porcentaje de cambio
        porcentaje_label = ttk.Label(update_frame, text="", style='Info.TLabel')
        porcentaje_label.grid(row=12, column=0, columnspan=2, pady=5)

        def calcular_porcentaje_cambio(event=None):
            try:
                nuevo_precio_str = nuevo_precio_entry.get()
                if nuevo_precio_str and hasattr(producto_cb, 'precio_actual'):
                    nuevo_precio = float(nuevo_precio_str)
                    precio_actual = producto_cb.precio_actual
                    porcentaje = ((nuevo_precio - precio_actual) / precio_actual) * 100
                    if porcentaje > 0:
                        porcentaje_label.config(
                            text=f"Incremento del precio: {porcentaje:.1f}%",
                            foreground=self.colors['error'])
                    elif porcentaje < 0:
                        porcentaje_label.config(
                            text=f"Reducción del precio: {abs(porcentaje):.1f}%",
                            foreground=self.colors['success'])
                    else:
                        porcentaje_label.config(text="No hay cambio en el precio")
            except ValueError:
                porcentaje_label.config(text="")
            except Exception:
                porcentaje_label.config(text="")

        nuevo_precio_entry.bind('<KeyRelease>', calcular_porcentaje_cambio)

        def actualizar_producto():
            try:
                producto = producto_cb.get()
                if not producto:
                    raise ValueError("Debe seleccionar un producto")
                nuevo_stock = nuevo_stock_entry.get()
                nuevo_precio = nuevo_precio_entry.get()
                if not nuevo_stock and not nuevo_precio:
                    raise ValueError("Debe ingresar al menos un valor para actualizar")
                
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                
                # Obtener stock actual antes de actualizar
                c.execute('SELECT stock, precio FROM productos WHERE nombre = ?', (producto,))
                stock_actual, precio_actual = c.fetchone()
                
                if nuevo_stock: 
                    stock = int(nuevo_stock)
                    if stock < 0:
                        raise ValueError("El stock no puede ser negativo")
                    
                    # Si el nuevo stock es menor al actual, preguntar motivo
                    if stock < stock_actual:
                        # Crear ventana de selección
                        motivo_window = tk.Toplevel()
                        motivo_window.title("Motivo de reducción de stock")
                        motivo_window.geometry("300x150")
                        motivo_window.transient(self.root)  # Hacer ventana modal
                        motivo_window.grab_set()  # Forzar foco en esta ventana
                        
                        ttk.Label(motivo_window, 
                                text="¿Por qué motivo se reduce el stock?",
                                style='Info.TLabel').pack(pady=10)
                        
                        motivo = tk.StringVar()
                        def confirmar_motivo(tipo):
                            motivo.set(tipo)
                            motivo_window.destroy()
                        
                        ttk.Button(motivo_window, 
                                text="Venta realizada",
                                command=lambda: confirmar_motivo("venta"),
                                style='Success.TButton').pack(pady=5)
                                
                        ttk.Button(motivo_window, 
                                text="Falta de entrega del pedido",
                                command=lambda: confirmar_motivo("falta_entrega"),
                                style='Action.TButton').pack(pady=5)
                        # Esperar a que se cierre la ventana
                        self.root.wait_window(motivo_window)
                        
                        # Si no se seleccionó motivo, cancelar operación
                        if not motivo.get():
                            return
                        
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        diferencia = stock_actual - stock
                        
                        if motivo.get() == "venta":
                            contenido = f"\n=== REGISTRO DE VENTA - {fecha_actual} ===\n"
                            contenido += f"Producto: {producto}\n"
                            contenido += f"Unidades vendidas: {diferencia}\n"
                            contenido += f"Precio unitario: ${precio_actual:.2f}\n"
                            contenido += f"Total venta: ${(diferencia * precio_actual):.2f}\n"
                        else:  # falta_entrega
                            contenido = f"\n=== REGISTRO DE FALTA DE ENTREGA - {fecha_actual} ===\n"
                            contenido += f"Producto: {producto}\n"
                            contenido += f"Unidades faltantes: {diferencia}\n"
                            contenido += f"Precio unitario: ${precio_actual:.2f}\n"
                            contenido += f"Valor faltante: ${(diferencia * precio_actual):.2f}\n"
                        
                        contenido += f"Stock anterior: {stock_actual}\n"
                        contenido += f"Stock actual: {stock}\n"
                        contenido += "=" * 40 + "\n"
                        
                        c.execute('''INSERT INTO informes (fecha, tipo, contenido)
                                    VALUES (?, ?, ?)''', (fecha_actual, motivo.get(), contenido))
                    
                    elif stock > stock_actual:
                        # Para incrementos de stock, registrar como recepción normal
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        diferencia = stock - stock_actual
                        
                        contenido = f"\n=== REGISTRO DE RECEPCIÓN - {fecha_actual} ===\n"
                        contenido += f"Producto: {producto}\n"
                        contenido += f"Unidades recibidas: {diferencia}\n"
                        contenido += f"Precio unitario: ${precio_actual:.2f}\n"
                        contenido += f"Total recepción: ${(diferencia * precio_actual):.2f}\n"
                        contenido += f"Stock anterior: {stock_actual}\n"
                        contenido += f"Stock actual: {stock}\n"
                        contenido += "=" * 40 + "\n"
                        
                        c.execute('''INSERT INTO informes (fecha, tipo, contenido)
                                    VALUES (?, ?, ?)''', (fecha_actual, 'recepcion', contenido))
                    
                    c.execute('UPDATE productos SET stock = ? WHERE nombre = ?',
                            (stock, producto))
                if nuevo_precio:
                    precio = float(nuevo_precio)
                    if precio <= 0:
                        raise ValueError("El precio debe ser mayor que 0")
                    c.execute('UPDATE productos SET precio = ? WHERE nombre = ?',
                            (precio, producto))
                
                conn.commit()
                conn.close()
                self.mostrar_notificacion("Producto actualizado correctamente")
                nuevo_stock_entry.delete(0, tk.END)
                nuevo_precio_entry.delete(0, tk.END)
                producto_cb.set('')
                porcentaje_label.config(text="")
                precio_actual_label.config(text="Precio actual: $0.00")
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar producto: {str(e)}")
            #-----------------------------------------------------------
        # Agregar el botón de actualizar
        ttk.Button(update_frame, text="Actualizar Producto",
                command=actualizar_producto,
                style='Success.TButton').grid(row=13, column=0, columnspan=2, pady=10)

    def mostrar_pedidos(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Crear marco principal para pedidos
        pedido_frame = ttk.LabelFrame(self.main_frame, text="Nuevo Pedido", padding="10")
        pedido_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        stock_frame = ttk.LabelFrame(self.main_frame, text="Stock Actual", padding="10")
        stock_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        stock_tree = ttk.Treeview(stock_frame, columns=('Producto', 'Stock', 'Precio'), show='headings')
        stock_tree.heading('Producto', text='Producto')
        stock_tree.heading('Stock', text='Stock')
        stock_tree.heading('Precio', text='Precio')
        stock_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(stock_frame, orient="vertical", command=stock_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        stock_tree.configure(yscrollcommand=scrollbar.set)

        # Ajustar las columnas para que ocupen todo el espacio
        stock_tree.column('Producto', width=200, anchor='center')
        stock_tree.column('Stock', width=100, anchor='center')
        stock_tree.column('Precio', width=100, anchor='center')

        # Agregar datos de prueba (puedes reemplazar esto con una consulta SQL)
        for producto in [('Helado de Vainilla', 20, '$100'), ('Helado de Chocolate', 15, '$120')]:
            stock_tree.insert('', 'end', values=producto)

        # Agregar formulario de pedido
        ttk.Label(pedido_frame, text="Producto:").grid(row=0, column=0, padx=5, pady=5)
        producto_cb = ttk.Combobox(pedido_frame, values=['Helado de Vainilla', 'Helado de Chocolate'])
        producto_cb.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(pedido_frame, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5)
        cantidad_entry = ttk.Entry(pedido_frame)
        cantidad_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(pedido_frame, text="Agregar al pedido", command=lambda: self.agregar_pedido(producto_cb, cantidad_entry))
        # Función para actualizar vista de stock
        def actualizar_vista_stock():
            for item in stock_tree.get_children():
                stock_tree.delete(item)
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()
            c.execute('SELECT nombre, stock, precio FROM productos')
            for producto in c.fetchall():
                stock_tree.insert('', 'end', values=(
                    producto[0],
                    producto[1],
                    f"${producto[2]:.2f}"
                ))
            conn.close()
        
        actualizar_vista_stock()
        
        ttk.Label(pedido_frame, text="Producto:",
                 style='Info.TLabel').grid(row=0, column=0, padx=5, pady=5)
        conn = sqlite3.connect('heladeria.db')
        c = conn.cursor()
        c.execute('SELECT nombre FROM productos')
        productos = [row[0] for row in c.fetchall()]
        conn.close()
        producto_cb = ttk.Combobox(pedido_frame, values=productos)
        producto_cb.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(pedido_frame, text="Cantidad:",
                 style='Info.TLabel').grid(row=1, column=0, padx=5, pady=5)
        cantidad_entry = ttk.Entry(pedido_frame)
        cantidad_entry.grid(row=1, column=1, padx=5, pady=5)
        self.pedidos_actuales = []
        

       

        def agregar_item_pedido():
            producto = producto_cb.get()
            try:
                cantidad = int(cantidad_entry.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                c.execute('SELECT id, precio FROM productos WHERE nombre = ?', (producto,))
                prod_data = c.fetchone()
                if prod_data:
                    self.pedidos_actuales.append({
                        'id': prod_data[0],
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio': prod_data[1]
                    })
                    actualizar_lista_pedidos()
                    producto_cb.set('')
                    cantidad_entry.delete(0, tk.END)
                    actualizar_vista_stock()
                    conn.close()
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar item: {str(e)}")

        ttk.Button(pedido_frame, text="Agregar al pedido",
                  command=agregar_item_pedido,
                  style='Action.TButton').grid(row=2, column=0, columnspan=2, pady=10)
        items_frame = ttk.LabelFrame(self.main_frame, text="Items del pedido",
                                   padding="10", style='Title.TLabelframe')
        items_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        style = ttk.Style()
        style.configure("pedidos.Treeview",
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dark'],
                       fieldbackground=self.colors['bg_light'])
        self.pedido_tree = ttk.Treeview(items_frame,
                                       columns=('Producto', 'Cantidad', 'Precio Unit.', 'Subtotal'),
                                       show='headings',
                                       style="pedidos.Treeview")
        self.pedido_tree.heading('Producto', text='Producto')
        self.pedido_tree.heading('Cantidad', text='Cantidad')
        self.pedido_tree.heading('Precio Unit.', text='Precio Unit.')
        self.pedido_tree.heading('Subtotal', text='Subtotal')
        self.pedido_tree.grid(row=0, column=0, sticky="nsew")
        
        def actualizar_lista_pedidos():
            for item in self.pedido_tree.get_children():
                self.pedido_tree.delete(item)
            total = 0
            for item in self.pedidos_actuales:
                subtotal = item['cantidad'] * item['precio']
                total += subtotal
                self.pedido_tree.insert('', 'end', values=(
                    item['producto'],
                    item['cantidad'],
                    f"${item['precio']:.2f}",
                    f"${subtotal:.2f}"
                ))
            total_label.config(text=f"Total: ${total:.2f}")

        def modificar_producto_pedido():
            selected_item = self.pedido_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Seleccione un producto para modificar")
                return
            
            # Obtener el índice del item seleccionado
            item_index = self.pedido_tree.index(selected_item)
            
            # Crear ventana de modificación
            mod_window = tk.Toplevel(self.root)
            mod_window.title("Modificar Producto")
            mod_window.geometry("300x200")
            
            # Configurar la ventana
            ttk.Label(mod_window, text="Nueva cantidad:",
                     style='Info.TLabel').pack(pady=10)
            nueva_cantidad = ttk.Entry(mod_window)
            nueva_cantidad.pack(pady=5)
            nueva_cantidad.insert(0, str(self.pedidos_actuales[item_index]['cantidad']))
            
            def guardar_modificacion():
                try:
                    cantidad = int(nueva_cantidad.get())
                    if cantidad <= 0:
                        raise ValueError("La cantidad debe ser mayor a 0")
                    
                    # Actualizar la cantidad en el pedido
                    self.pedidos_actuales[item_index]['cantidad'] = cantidad
                    actualizar_lista_pedidos()
                    mod_window.destroy()
                    
                except ValueError as ve:
                    messagebox.showerror("Error", str(ve))
                except Exception as e:
                    messagebox.showerror("Error", f"Error al modificar producto: {str(e)}")
            
            ttk.Button(mod_window, text="Guardar",
                      command=guardar_modificacion,
                      style='Success.TButton').pack(pady=10)
            ttk.Button(mod_window, text="Cancelar",
                      command=mod_window.destroy,
                      style='Danger.TButton').pack(pady=5)

        def eliminar_producto_pedido():
            selected_item = self.pedido_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Seleccione un producto para eliminar")
                return
            
            if messagebox.askyesno("Confirmar eliminación", 
                                 "¿Está seguro de eliminar este producto del pedido?"):
                # Obtener el índice del item seleccionado
                item_index = self.pedido_tree.index(selected_item)
                # Eliminar el producto de la lista
                self.pedidos_actuales.pop(item_index)
                actualizar_lista_pedidos()

        total_label = ttk.Label(items_frame, text="Total: $0.00",
                              style='Info.TLabel', font=('Arial', 12, 'bold'))
        total_label.grid(row=1, column=0, pady=10)

        def confirmar_pedido():
            if not self.pedidos_actuales:
                messagebox.showerror("Error", "No hay items en el pedido")
                return
            try:
                conn = sqlite3.connect('heladeria.db')
                c = conn.cursor()
                for item in self.pedidos_actuales:
                    c.execute('''UPDATE productos 
                                SET stock = stock + ? 
                                WHERE id = ?''',
                             (item['cantidad'], item['id']))
                conn.commit()
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total = sum(item['cantidad'] * item['precio'] for item in self.pedidos_actuales)
                contenido = f"\n=== NUEVO PEDIDO - {fecha_actual} ===\n"
                for item in self.pedidos_actuales:
                    contenido += f"Producto: {item['producto']}\n"
                    contenido += f"Cantidad: {item['cantidad']}\n"
                    contenido += f"Precio unitario: ${item['precio']:.2f}\n"
                    contenido += f"Subtotal: ${item['cantidad'] * item['precio']:.2f}\n"
                    contenido += "-" * 30 + "\n"
                contenido += f"TOTAL: ${total:.2f}\n"
                contenido += "=" * 40 + "\n"
                
                # Guardar en la base de datos
                c.execute('''INSERT INTO informes (fecha, tipo, contenido)
                            VALUES (?, ?, ?)''', (fecha_actual, 'pedido', contenido))
                conn.commit()
                conn.close()

                # Crear directorio si no existe
                if not os.path.exists('pedidos'):
                    os.makedirs('pedidos')

                # Guardar en archivo txt
                fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"pedido_{fecha_archivo}.txt"
                ruta_archivo = os.path.join('pedidos', nombre_archivo)
                
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido)

                self.mostrar_notificacion("Pedido procesado correctamente")
                messagebox.showinfo("Éxito", f"Pedido procesado correctamente\nArchivo guardado como: {nombre_archivo}")
                self.pedidos_actuales = []
                actualizar_lista_pedidos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar el pedido: {str(e)}")

        def cancelar_pedido():
            if messagebox.askyesno("Cancelar pedido", "¿Está seguro de cancelar el pedido actual?"):
                self.pedidos_actuales = []
                actualizar_lista_pedidos()
                
        botones_frame = ttk.Frame(items_frame, style='Main.TFrame')
        botones_frame.grid(row=2, column=0, pady=10)

        # Todos los botones en una sola fila
        ttk.Button(botones_frame, text="Modificar Producto",
                  command=modificar_producto_pedido,
                  style='Action.TButton').grid(row=0, column=0, padx=2)
        
        ttk.Button(botones_frame, text="Eliminar Producto",
                  command=eliminar_producto_pedido,
                  style='Danger.TButton').grid(row=0, column=1, padx=2)
        
        ttk.Button(botones_frame, text="Confirmar Pedido",
                  command=confirmar_pedido,
                  style='Success.TButton').grid(row=0, column=2, padx=2)
        
        ttk.Button(botones_frame, text="Cancelar Pedido",
                  command=cancelar_pedido,
                  style='Danger.TButton').grid(row=0, column=3, padx=2)

        scrollbar = ttk.Scrollbar(items_frame, orient="vertical",
                                command=self.pedido_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pedido_tree.configure(yscrollcommand=scrollbar.set)
        
        guardar_pedido()
        def guardar_pedido(self, contenido):
            # Modificar para usar la ruta correcta de pedidos
            fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"pedido_{fecha_archivo}.txt"
            ruta_archivo = os.path.join(self.pedidos_dir, nombre_archivo)
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)

    def generar_informes(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        informe_frame = ttk.LabelFrame(self.main_frame, text="Generar Informes",
                                     padding="10", style='Title.TLabelframe')
        informe_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ttk.Label(informe_frame, text="Informes del Sistema",
                 style='Info.TLabel').grid(row=0, column=0, columnspan=3, pady=10)# Botones de informes
        #informe de ventas
        ttk.Label(informe_frame, text="💰 Informe de Ventas",
                 style='Info.TLabel').grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(informe_frame, text="ver nuevo",
                  command=lambda: self.informe_ventas('nuevo'),
                  style='Success.TButton').grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(informe_frame, text="ver acumulativo",
                  command=lambda: self.informe_ventas('acumulativo'),
                  style='Success.TButton').grid(row=3, column=2, padx=5, pady=5)
        # Informe de Pedidos
        ttk.Label(informe_frame, text="📈 Informe de Pedidos",
                 style='Info.TLabel').grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(informe_frame, text="Ver nuevo",
                  command=lambda: self.informe_pedidos('nuevo'),
                  style='Success.TButton').grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(informe_frame, text="ver acumulativo",
                  command=lambda: self.informe_pedidos('acumulativo'),
                  style='Success.TButton').grid(row=1, column=2, padx=5, pady=5)
        # Informe de Inventario
        ttk.Label(informe_frame, text="📊 Informe de Stock",
                  
                 style='Info.TLabel').grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(informe_frame, text="Ver nuevo",
                  command=lambda: self.informe_inventario('nuevo'),
                  style='Success.TButton').grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(informe_frame, text="ver acumulativo",
                  command=lambda: self.informe_inventario('acumulativo'),
                  style='Success.TButton').grid(row=2, column=2, padx=5, pady=5)

    def informe_ventas(self, tipo):
        try:
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()

            if tipo == 'nuevo':
                c.execute('SELECT contenido FROM informes WHERE tipo = "venta" ORDER BY fecha DESC')
                ventas = c.fetchall()
                if not ventas:
                    messagebox.showinfo("Informe de Ventas", "No hay registros de ventas.")
                    return

                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.join('informes', f'informe_ventas_{fecha_actual.replace(":", "_").replace(" ", "_")}.txt')
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                total_ventas = 0
                productos_vendidos = {}

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== INFORME DE VENTAS ===\n")
                    f.write(f"Fecha: {fecha_actual}\n\n")
                    
                    for venta in ventas:
                        f.write(venta[0])
                        lineas = venta[0].split('\n')
                        for i, linea in enumerate(lineas):
                            if 'Total venta: $' in linea:
                                total_ventas += float(linea.split('$')[1])
                            elif 'Producto: ' in linea:
                                producto = linea.split('Producto: ')[1]
                                unidades = int(lineas[i+1].split('Unidades vendidas: ')[1])
                                productos_vendidos[producto] = productos_vendidos.get(producto, 0) + unidades

                    f.write("\n=== RESUMEN DE VENTAS ===\n")
                    f.write(f"Total ventas: ${total_ventas:.2f}\n")
                    f.write("\nProductos más vendidos:\n")
                    for producto, unidades in sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- {producto}: {unidades} unidades\n")

                c.execute('''INSERT INTO informes (fecha, tipo, contenido) VALUES (?, ?, ?)''', (fecha_actual, 'informe_ventas', f"Informe guardado en: {filename}"))
                conn.commit()

            # Mostrar el informe más reciente
            c.execute('''SELECT contenido FROM informes WHERE tipo IN ("venta", "informe_ventas") ORDER BY fecha DESC''')
            contenido = c.fetchone()

            if contenido:
                messagebox.showinfo("Informe de Ventas", contenido[0])
            else:
                messagebox.showinfo("Informe de Ventas", "No hay registros de ventas.")

            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar informe: {str(e)}")

    def informe_pedidos(self, tipo):
        try:
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()

            if tipo == 'nuevo':
                c.execute('SELECT contenido FROM informes WHERE tipo = "pedido" ORDER BY fecha DESC')
                pedidos = c.fetchall()
                if not pedidos:
                    messagebox.showinfo("Informe de Pedidos", "No hay registros de pedidos.")
                    return

                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.join('informes', f'informe_pedidos_{fecha_actual.replace(":", "_").replace(" ", "_")}.txt')
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== INFORME DE PEDIDOS ===\n")
                    f.write(f"Fecha: {fecha_actual}\n\n")
                    for pedido in pedidos:
                        f.write(pedido[0])

                c.execute('''INSERT INTO informes (fecha, tipo, contenido) VALUES (?, ?, ?)''', (fecha_actual, 'informe_pedidos', f"Informe guardado en: {filename}"))
                conn.commit()

            # Mostrar el informe más reciente
            c.execute('''SELECT contenido FROM informes WHERE tipo IN ("pedido", "informe_pedidos") ORDER BY fecha DESC''')
            contenido = c.fetchone()

            if contenido:
                messagebox.showinfo("Informe de Pedidos", contenido[0])
            else:
                messagebox.showinfo("Informe de Pedidos", "No hay registros de pedidos.")

            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar informe: {str(e)}")

    def informe_inventario(self, tipo):
        try:
            conn = sqlite3.connect('heladeria.db')
            c = conn.cursor()
            c.execute('SELECT nombre, precio, stock, stock_minimo FROM productos')
            productos = c.fetchall()

            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = os.path.join('informes', f'informe_inventario_{fecha_actual.replace(":", "_").replace(" ", "_")}.txt')
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== INFORME DE INVENTARIO ===\n")
                f.write(f"Fecha: {fecha_actual}\n\n")
                for producto in productos:
                    estado = "Normal" if producto[2] > producto[3] else "Bajo"
                    f.write(f"Producto: {producto[0]}\n")
                    f.write(f"Precio: ${producto[1]:.2f}\n")
                    f.write(f"Stock Actual: {producto[2]}\n")
                    f.write(f"Stock Mínimo: {producto[3]}\n")
                    f.write(f"Estado: {estado}\n")
                    f.write("-" * 30 + "\n")

            if tipo == 'nuevo':
                c.execute('''INSERT INTO informes (fecha, tipo, contenido) VALUES (?, ?, ?)''', (fecha_actual, 'informe_inventario', f"Informe guardado en: {filename}"))
                conn.commit()

            messagebox.showinfo("Informe de Inventario", f"Informe generado correctamente:\n{filename}")
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar informe: {str(e)}")
            
    def realizar_backup(self):
        try:
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_path = os.path.join(self.app_data_dir, 'heladeria.db')
            backup_path = os.path.join(self.app_data_dir, 'backups', f'backup_{timestamp}.db')
            
            # Copiar archivo de base de datos
            shutil.copy2(db_path, backup_path)
            self.mostrar_notificacion("Backup creado correctamente")
            
            # Actualizar lista de backups si la ventana está abierta
            for widget in self.main_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget('text') == "Gestión de Backups":
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.LabelFrame) and child.cget('text') == "Backups Existentes":
                            for tree in child.winfo_children():
                                if isinstance(tree, ttk.Treeview):
                                    self.actualizar_lista_backups(tree)
                                    break
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup: {str(e)}")

    def actualizar_lista_backups(self, backup_tree):
        """Actualizar la lista de backups en el Treeview."""
        for item in backup_tree.get_children():
            backup_tree.delete(item)
            
        backup_dir = os.path.join(self.app_data_dir, 'backups')
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.endswith('.db'):
                    file_path = os.path.join(backup_dir, file)
                    size = os.path.getsize(file_path) / 1024  # Tamaño en KB
                    date = datetime.fromtimestamp(os.path.getctime(file_path))
                    backup_tree.insert('', 'end', values=(
                        date.strftime('%Y-%m-%d %H:%M:%S'),
                        f'{size:.2f} KB',
                        file_path))

    def mostrar_gestion_backups(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        backup_frame = ttk.LabelFrame(self.main_frame, text="Gestión de Backups",
                                    padding="10", style='Title.TLabelframe')
        backup_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Frame para realizar backup
        create_frame = ttk.LabelFrame(backup_frame, text="Crear Backup",
                                    padding="10", style='Title.TLabelframe')
        create_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ttk.Button(create_frame, text="Realizar Backup Manual",
                command=self.realizar_backup,
                style='Action.TButton').grid(row=0, column=0, padx=5, pady=5)
                
        # Frame para listar backups
        list_frame = ttk.LabelFrame(backup_frame, text="Backups Existentes",
                                padding="10", style='Title.TLabelframe')
        list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Crear Treeview para mostrar backups
        backup_tree = ttk.Treeview(list_frame,
                                columns=('Fecha', 'Tamaño', 'Ruta'),
                                show='headings',
                                style="Custom.Treeview")
        backup_tree.heading('Fecha', text='Fecha')
        backup_tree.heading('Tamaño', text='Tamaño')
        backup_tree.heading('Ruta', text='Ruta')
        backup_tree.grid(row=0, column=0, sticky="nsew")
        backup_tree.column("Ruta", width=500, anchor="w")
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=backup_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        backup_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configurar expansión del frame
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        def restaurar_backup():
            selected = backup_tree.selection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione un backup para restaurar")
                return
                
            if messagebox.askyesno("Confirmar restauración",
                                "¿Está seguro de restaurar este backup? Se perderán los datos actuales."):
                try:
                    # Obtener la ruta del backup seleccionado
                    backup_path = backup_tree.item(selected[0])['values'][2]
                    db_path = os.path.join(self.app_data_dir, 'heladeria.db')
                    
                    # Verificar el archivo de destino antes de copiar
                    if os.path.exists(backup_path):
                        # Cerrar conexión activa a la base de datos (si existe)
                        if hasattr(self, 'db_connection') and self.db_connection:
                            self.db_connection.close()
                            self.db_connection = None
                            print("Conexión cerrada correctamente")
                        
                        # Copiar el archivo de backup al archivo principal de la base de datos
                        shutil.copy2(backup_path, db_path)
                        print("Backup restaurado desde:", backup_path)
                        
                        # Reabrir la conexión a la base de datos con el archivo restaurado
                        self.crear_base_datos()  # Reconectar base de datos
                        
                        messagebox.showinfo("Éxito", "Backup restaurado correctamente")
                        
                        # Actualizar la vista principal
                        self.mostrar_stock()
                    else:
                        messagebox.showerror("Error", f"No se encontró el archivo de backup: {backup_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al restaurar backup: {str(e)}")

        def eliminar_backup():
            selected = backup_tree.selection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione un backup para eliminar")
                return
                
            if messagebox.askyesno("Confirmar eliminación",
                                "¿Está seguro de eliminar este backup?"):
                try:
                    backup_path = backup_tree.item(selected[0])['values'][2]
                    os.remove(backup_path)
                    self.actualizar_lista_backups(backup_tree)  # Llamada actualizada
                    messagebox.showinfo("Éxito", "Backup eliminado correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar backup: {str(e)}")
        
        # Botones de acción para backups
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Actualizar Lista",
                command=lambda: self.actualizar_lista_backups(backup_tree),  # Llamada actualizada
                style='Action.TButton').grid(row=0, column=0, padx=5)
                
        ttk.Button(button_frame, text="Restaurar Backup",
                command=restaurar_backup,
                style='Success.TButton').grid(row=0, column=1, padx=5)
                
        ttk.Button(button_frame, text="Eliminar Backup",
                command=eliminar_backup,
                style='Danger.TButton').grid(row=0, column=2, padx=5)
                
        # Inicializar la lista de backups
        self.actualizar_lista_backups(backup_tree)
        
    def mostrar_ayuda(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        help_frame = ttk.LabelFrame(self.main_frame, text="Guía de Usuario",
                                  padding="20", style='Title.TLabelframe')
        help_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        help_text = tk.Text(help_frame, wrap=tk.WORD, width=100, height=25,
                           font=('Arial', 14), bg=self.colors['bg_light'],
                           fg=self.colors['text_dark'])
        help_text.grid(row=0, column=0, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(help_frame, orient="vertical",
                                command=help_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        help_text.configure(yscrollcommand=scrollbar.set)
        
        guia = """
GUÍA DE USUARIO - SISTEMA DE GESTIÓN DE HELADERÍA

1. VISIÓN GENERAL
================
Este sistema permite gestionar el inventario, pedidos y ventas de una heladería de manera eficiente y organizada.

2. FUNCIONES PRINCIPALES
=====================

2.1 Ver Stock
------------
- Muestra una lista completa de todos los productos en inventario
- Indica el stock actual y mínimo de cada producto
- Muestra el estado del stock (Normal o Bajo)
- Los productos con stock bajo se marcan automáticamente en rojo
- Permite eliminar productos del inventario
- Actualización en tiempo real del estado del stock
- Búsqueda y filtrado de productos

2.2 Actualizar Stock
------------------
a) Agregar Nuevo Producto:
   - Ingrese el nombre del producto (debe ser único)
   - Establezca el precio inicial
   - Defina el stock inicial
   - Establezca el stock mínimo de advertencia
   - El sistema validará que no exista un producto con el mismo nombre
   - Haga clic en "Agregar Producto"

b) Modificar Producto Existente:
   - Seleccione el producto del menú desplegable
   - Visualice el precio actual del producto
   - Ingrese la nueva cantidad de stock (opcional)
   - Ingrese el nuevo precio (opcional)
   - El sistema calculará automáticamente el porcentaje de cambio en el precio
   - Si reduce el stock, se registrará automáticamente como una venta
   - Haga clic en "Actualizar Producto"

2.3 Realizar Pedidos
------------------
a) Crear Nuevo Pedido:
   - Seleccione el producto a pedir
   - Ingrese la cantidad deseada
   - Haga clic en "Agregar a la pedido"
   - Repita para agregar más productos
   - Visualice el subtotal por producto y total general
   - Modifique cantidades de productos ya agregados
   - Elimine productos individuales del pedido
   - Use "Confirmar pedido" para finalizar
   - Use "Cancelar pedido" para eliminar todos los items

b) Gestión de Pedidos:
   - Los pedidos se guardan automáticamente
   - Se genera un archivo de texto con los detalles
   - Se actualiza el inventario automáticamente
   - Se registra en el historial de pedidos

2.4 Informes
----------
a) Informe de Pedidos:
   - Ver Acumulativo: Muestra el historial completo de pedidos
   - Crear Nuevo: Genera un informe actualizado con los últimos pedidos
   - Incluye detalles de productos, cantidades y costos
   - Muestra fecha y hora de cada pedido

b) Informe de Inventario:
   - Ver Acumulativo: Muestra el estado actual del inventario
   - Crear Nuevo: Genera un informe actualizado del stock
   - Incluye precios, cantidades y estados de todos los productos
   - Identifica productos con stock bajo

c) Informe de Ventas:
   - Ver Acumulativo: Muestra el historial de todas las ventas
   - Crear Nuevo: Genera un informe detallado de ventas
   - Incluye productos vendidos, cantidades y montos
   - Muestra estadísticas de productos más vendidos
   - Calcula el total de ventas realizadas
   - Registra cambios en el stock y precios

2.5 Gestión de Backups
--------------------
a) Crear Backup:
   - Backup manual con un clic
   - Se guarda con fecha y hora
   - Incluye toda la base de datos
   - Verificación automática de integridad

b) Restaurar Backup:
   - Seleccione el backup a restaurar
   - Confirmación de seguridad
   - Restauración completa de datos
   - Actualización automática de vistas

c) Administrar Backups:
   - Lista de backups disponibles
   - Información de fecha y tamaño
   - Opción de eliminar backups antiguos
   - Actualización de lista en tiempo real

3. CONSEJOS ÚTILES
================
- Revise regularmente el estado del stock para evitar faltantes
- Mantenga actualizado el stock mínimo según la demanda estacional
- Guarde los pedidos al final del día para mejor control
- Verifique los productos antes de confirmar un pedido
- Monitoree los cambios de precios y su impacto en las ventas
- Utilice los informes para tomar decisiones de inventario
- Realice respaldos periódicos de la base de datos
- Verifique las ventas diarias para control de caja

4. SOLUCIÓN DE PROBLEMAS
=====================
Si encuentra algún error:
1. Verifique que todos los campos requeridos estén completos
2. Asegúrese de ingresar números válidos (positivos)
3. Confirme que el producto existe antes de actualizarlo
4. Verifique la conexión con la base de datos
5. Revise que los precios sean mayores a cero
6. Confirme que el stock no sea negativo
7. Asegúrese de tener permisos de escritura en la base de datos
8. Verifique el espacio disponible en disco

Problemas comunes:
a) Error al crear backup:
   - Verifique permisos de escritura
   - Asegure espacio suficiente
   - Cierre otros programas usando la base de datos

b) Error al restaurar backup:
   - Verifique que el archivo existe
   - Confirme que no está dañado
   - Cierre todas las conexiones activas

c) Error en informes:
   - Verifique la conexión a la base de datos
   - Asegure que hay datos para mostrar
   - Confirme los permisos de lectura

5. ATAJOS DE TECLADO
==================
- Tab: Navegar entre campos de entrada
- Enter: Confirmar entrada de datos
- Esc: Cancelar operación actual
- Ctrl + N: Nuevo pedido
- Ctrl + S: Guardar cambios
- F5: Actualizar vista actual
- F1: Mostrar ayuda

6. GESTIÓN DE VENTAS
==================
El sistema registra automáticamente las ventas cuando:
- Se reduce el stock de un producto
- Se actualiza el inventario
- Se confirma un pedido

Cada registro de venta incluye:
- Fecha y hora de la transacción
- Producto vendido
- Cantidad vendida
- Precio unitario
- Total de la venta
- Stock anterior y actual
- Usuario que realizó la operación

7. SEGURIDAD Y RESPALDOS
=====================
- El sistema utiliza SQLite para almacenar datos
- Se recomienda realizar respaldos diarios
- Cada operación queda registrada con fecha y hora
- Los informes se pueden exportar para respaldo
- Se validan todas las entradas de datos
- Se requiere confirmación para operaciones críticas

Recomendaciones de seguridad:
- Realice backups antes de actualizaciones
- Mantenga copias en ubicaciones diferentes
- Verifique la integridad de los backups
- No elimine backups sin confirmar
- Documente los cambios importantes

8. SOPORTE TÉCNICO
=====================
8.1 Contacto:
- Desarrollador: Jesús J. Copes
- Teléfono: +54 3408670623
- Correo Electrónico: jesusjcopes@gmail.com

8.2 Tipos de Soporte:
- Consultas operativas
- Problemas técnicos
- Recuperación de datos
- Capacitación adicional
- Actualizaciones del sistema

Última actualización: Enero 2025
Versión del documento: 5.4

Muchas gracias por la confianza y por dejarme ser quien haga su programa de gestión.
"""
        help_text.insert('1.0', guia)
        help_text.config(state='disabled')

    def mostrar_notificacion(self, mensaje):
        self.notificaciones.set(mensaje)
        self.root.after(5000, lambda: self.notificaciones.set(''))

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        producto_id = self.tree.item(item, "values")[0]
        self.mostrar_detalle_producto(producto_id)

    def mostrar_detalle_producto(self, producto_id):
        detalle_window = tk.Toplevel(self.root)
        detalle_window.title("Detalle del Producto")
        detalle_window.geometry("400x300")
        conn = sqlite3.connect('heladeria.db')
        c = conn.cursor()
        c.execute('SELECT * FROM productos WHERE id = ?', (producto_id,))
        producto = c.fetchone()
        conn.close()
        ttk.Label(detalle_window, text=f"ID: {producto[0]}").pack(pady=5)
        ttk.Label(detalle_window, text=f"Nombre: {producto[1]}").pack(pady=5)
        ttk.Label(detalle_window, text=f"Precio: ${producto[2]:.2f}").pack(pady=5)
        ttk.Label(detalle_window, text=f"Stock: {producto[3]}").pack(pady=5)
        ttk.Label(detalle_window, text=f"Stock Mínimo: {producto[4]}").pack(pady=5)

def main():
    try:
        root = tk.Tk()
        app = HeladeriaPOS(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Error crítico: {str(e)}\n\nPor favor, contacte al soporte técnico.")
        
if __name__ == "__main__":
    main()