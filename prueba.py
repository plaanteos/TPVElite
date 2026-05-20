import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import pandas as pd
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib.pyplot as plt

class IceCreamShopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Ventas - Heladería")
        self.root.geometry("1200x700")
        
        # Configuración de la base de datos
        self.create_database()
        
        # Variables
        self.product_vars = {
            'name': tk.StringVar(),
            'price': tk.DoubleVar(),
            'stock': tk.IntVar()
        }
        
        self.create_gui()
        
    def create_database(self):
        conn = sqlite3.connect('icecream_shop.db')
        c = conn.cursor()
        
        # Crear tablas
        c.execute('''CREATE TABLE IF NOT EXISTS products
                    (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS sales
                    (id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, 
                     total_price REAL, date TEXT)''')
        
        conn.commit()
        conn.close()
        
    def create_gui(self):
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Pestañas
        sales_frame = ttk.Frame(notebook)
        inventory_frame = ttk.Frame(notebook)
        reports_frame = ttk.Frame(notebook)
        
        notebook.add(sales_frame, text='Ventas')
        notebook.add(inventory_frame, text='Inventario')
        notebook.add(reports_frame, text='Reportes')
        
        # Configurar frames
        self.setup_sales_frame(sales_frame)
        self.setup_inventory_frame(inventory_frame)
        self.setup_reports_frame(reports_frame)
    
    def setup_sales_frame(self, frame):
        # Lista de productos
        product_frame = ttk.LabelFrame(frame, text="Productos Disponibles")
        product_frame.grid(row=0, column=0, padx=10, pady=5, sticky='nsew')
        
        self.product_tree = ttk.Treeview(product_frame, columns=('ID', 'Nombre', 'Precio', 'Stock'),
                                       show='headings')
        self.product_tree.heading('ID', text='ID')
        self.product_tree.heading('Nombre', text='Nombre')
        self.product_tree.heading('Precio', text='Precio')
        self.product_tree.heading('Stock', text='Stock')
        self.product_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame de venta
        sale_frame = ttk.LabelFrame(frame, text="Nueva Venta")
        sale_frame.grid(row=0, column=1, padx=10, pady=5, sticky='nsew')
        
        ttk.Label(sale_frame, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(sale_frame)
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(sale_frame, text="Realizar Venta", 
                  command=self.make_sale).grid(row=1, column=0, columnspan=2, pady=10)
        
    def setup_inventory_frame(self, frame):
        # Formulario de producto
        form_frame = ttk.LabelFrame(frame, text="Gestión de Productos")
        form_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.product_vars['name']).grid(row=0, column=1)
        
        ttk.Label(form_frame, text="Precio:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.product_vars['price']).grid(row=1, column=1)
        
        ttk.Label(form_frame, text="Stock:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.product_vars['stock']).grid(row=2, column=1)
        
        ttk.Button(form_frame, text="Agregar Producto", 
                  command=self.add_product).grid(row=3, column=0, columnspan=2, pady=10)
        
    def setup_reports_frame(self, frame):
        # Botones de reportes
        ttk.Button(frame, text="Generar Reporte de Ventas", 
                  command=self.generate_sales_report).pack(pady=10)
        ttk.Button(frame, text="Ver Gráfico de Ventas", 
                  command=self.show_sales_chart).pack(pady=10)
        
    def add_product(self):
        try:
            name = self.product_vars['name'].get()
            price = self.product_vars['price'].get()
            stock = self.product_vars['stock'].get()
            
            conn = sqlite3.connect('icecream_shop.db')
            c = conn.cursor()
            c.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                     (name, price, stock))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
            self.refresh_product_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")
    
    def make_sale(self):
        try:
            selected = self.product_tree.selection()[0]
            product_id = self.product_tree.item(selected)['values'][0]
            quantity = int(self.quantity_entry.get())
            
            conn = sqlite3.connect('icecream_shop.db')
            c = conn.cursor()
            
            # Verificar stock
            c.execute("SELECT price, stock FROM products WHERE id=?", (product_id,))
            price, stock = c.fetchone()
            
            if quantity > stock:
                messagebox.showerror("Error", "Stock insuficiente")
                return
            
            # Actualizar stock
            new_stock = stock - quantity
            c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
            
            # Registrar venta
            total_price = price * quantity
            c.execute("INSERT INTO sales (product_id, quantity, total_price, date) VALUES (?, ?, ?, ?)",
                     (product_id, quantity, total_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Venta realizada correctamente")
            self.refresh_product_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al realizar la venta: {str(e)}")
    
    def refresh_product_list(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
            
        conn = sqlite3.connect('icecream_shop.db')
        c = conn.cursor()
        c.execute("SELECT * FROM products")
        for row in c.fetchall():
            self.product_tree.insert('', 'end', values=row)
        conn.close()
    
    def generate_sales_report(self):
        conn = sqlite3.connect('icecream_shop.db')
        query = '''
        SELECT p.name, s.quantity, s.total_price, s.date
        FROM sales s
        JOIN products p ON s.product_id = p.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Exportar a Excel
        df.to_excel('reporte_ventas.xlsx', index=False)
        messagebox.showinfo("Éxito", "Reporte generado: reporte_ventas.xlsx")
    
    def show_sales_chart(self):
        conn = sqlite3.connect('icecream_shop.db')
        df = pd.read_sql_query('''
            SELECT date, SUM(total_price) as total
            FROM sales
            GROUP BY date
        ''', conn)
        conn.close()
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['date'], df['total'])
        ax.set_title('Ventas por Fecha')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Total Ventas')
        plt.xticks(rotation=45)
        
        # Mostrar en ventana nueva
        top = tk.Toplevel()
        top.title("Gráfico de Ventas")
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = IceCreamShopApp(root)
    root.mainloop()