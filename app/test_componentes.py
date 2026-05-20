"""
🧪 Script de Prueba - Nuevos Componentes UX
============================================

Este script te permite probar los nuevos componentes sin ejecutar toda la app.
Ejecuta: py -3 test_componentes.py
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar colores y componentes del main
from main import ELITE_COLORS, LIGHT_COLORS, ToastNotification, ModernSearchBar, ModernButton, AnimationHelper


class TestApp:
    """App de prueba para los nuevos componentes"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Test - Componentes UX Modernos")
        self.root.geometry("900x700")
        
        # Variables
        self.current_theme = 'dark'
        self.colors = ELITE_COLORS
        
        # Configurar ventana
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Crear interfaz
        self.create_ui()
    
    def create_ui(self):
        """Crea la interfaz de prueba"""
        # Frame principal con scroll
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title = tk.Label(main_frame,
                        text="🧪 Prueba de Componentes Modernos",
                        font=('Segoe UI', 24, 'bold'),
                        bg=self.colors['bg_primary'],
                        fg=self.colors['text_primary'])
        title.pack(pady=(0, 30))
        
        # Sección 1: Toast Notifications
        self.create_toast_section(main_frame)
        
        # Separador
        tk.Frame(main_frame, bg=self.colors['border'], height=2).pack(fill='x', pady=20)
        
        # Sección 2: Search Bar
        self.create_search_section(main_frame)
        
        # Separador
        tk.Frame(main_frame, bg=self.colors['border'], height=2).pack(fill='x', pady=20)
        
        # Sección 3: Theme Toggle
        self.create_theme_section(main_frame)
        
        # Separador
        tk.Frame(main_frame, bg=self.colors['border'], height=2).pack(fill='x', pady=20)
        
        # Sección 4: Modern Buttons
        self.create_buttons_section(main_frame)
    
    def create_toast_section(self, parent):
        """Sección de prueba de toasts"""
        section = tk.Frame(parent, bg=self.colors['bg_card'], 
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        section.pack(fill='x', pady=10)
        
        # Título de sección
        tk.Label(section,
                text="🔔 Toast Notifications",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_card'],
                fg=self.colors['accent_blue']).pack(pady=15, padx=20, anchor='w')
        
        # Botones de prueba
        buttons_frame = tk.Frame(section, bg=self.colors['bg_card'])
        buttons_frame.pack(padx=20, pady=(0, 20))
        
        ModernButton(buttons_frame,
                    text="✓ Success Toast",
                    style='success',
                    command=lambda: self.show_toast('success')).pack(side='left', padx=5)
        
        ModernButton(buttons_frame,
                    text="✕ Error Toast",
                    style='danger',
                    command=lambda: self.show_toast('error')).pack(side='left', padx=5)
        
        ModernButton(buttons_frame,
                    text="⚠ Warning Toast",
                    style='warning',
                    command=lambda: self.show_toast('warning')).pack(side='left', padx=5)
        
        ModernButton(buttons_frame,
                    text="ℹ Info Toast",
                    style='info',
                    command=lambda: self.show_toast('info')).pack(side='left', padx=5)
        
        ModernButton(buttons_frame,
                    text="🎉 Multiple Toasts",
                    style='primary',
                    command=self.show_multiple_toasts).pack(side='left', padx=5)
    
    def show_toast(self, toast_type):
        """Muestra un toast de prueba"""
        messages = {
            'success': "✓ ¡Operación completada con éxito!",
            'error': "✕ Ha ocurrido un error al procesar la solicitud",
            'warning': "⚠ Advertencia: El stock está bajo",
            'info': "ℹ Información: El sistema se actualizará en 5 minutos"
        }
        
        ToastNotification(
            self.root,
            messages[toast_type],
            toast_type,
            3000
        ).show()
    
    def show_multiple_toasts(self):
        """Muestra varios toasts en secuencia"""
        ToastNotification(self.root, "Paso 1: Iniciando proceso...", 'info', 2000).show()
        self.root.after(800, lambda: ToastNotification(
            self.root, "Paso 2: Procesando datos...", 'info', 2000).show())
        self.root.after(1600, lambda: ToastNotification(
            self.root, "Paso 3: Guardando cambios...", 'info', 2000).show())
        self.root.after(2400, lambda: ToastNotification(
            self.root, "✓ ¡Proceso completado con éxito!", 'success', 3000).show())
    
    def create_search_section(self, parent):
        """Sección de prueba de búsqueda"""
        section = tk.Frame(parent, bg=self.colors['bg_card'],
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        section.pack(fill='x', pady=10)
        
        # Título
        tk.Label(section,
                text="🔍 Search Bar con Filtrado en Tiempo Real",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_card'],
                fg=self.colors['accent_blue']).pack(pady=15, padx=20, anchor='w')
        
        # Barra de búsqueda
        def on_search(text):
            result_label.config(text=f"Buscando: '{text}'" if text else "Escribe para buscar...")
            self.filter_list(text)
        
        search_bar = ModernSearchBar(
            section,
            placeholder="🔍 Buscar productos, clientes o ventas...",
            on_search=on_search,
            bg=self.colors['bg_card']
        )
        search_bar.pack(fill='x', padx=20, pady=(0, 10))
        
        # Label de resultado
        result_label = tk.Label(section,
                               text="Escribe para buscar...",
                               font=('Segoe UI', 11),
                               bg=self.colors['bg_card'],
                               fg=self.colors['text_secondary'])
        result_label.pack(padx=20, pady=(0, 10))
        
        # Lista de ejemplo
        list_frame = tk.Frame(section, bg=self.colors['bg_secondary'])
        list_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.test_listbox = tk.Listbox(list_frame,
                                       font=('Segoe UI', 10),
                                       bg=self.colors['bg_secondary'],
                                       fg=self.colors['text_primary'],
                                       height=5,
                                       bd=0,
                                       highlightthickness=0)
        self.test_listbox.pack(fill='x', padx=10, pady=10)
        
        # Datos de ejemplo
        self.test_data = [
            "Helado de Chocolate",
            "Helado de Vainilla",
            "Helado de Fresa",
            "Helado de Menta",
            "Helado de Limón",
            "Cono de Waffle",
            "Cono Simple",
            "Toppings Variados"
        ]
        
        for item in self.test_data:
            self.test_listbox.insert('end', f"  • {item}")
    
    def filter_list(self, search_text):
        """Filtra la lista en tiempo real"""
        self.test_listbox.delete(0, 'end')
        
        search_lower = search_text.lower()
        for item in self.test_data:
            if search_lower in item.lower() or search_text == "":
                self.test_listbox.insert('end', f"  • {item}")
        
        if self.test_listbox.size() == 0:
            self.test_listbox.insert('end', "  ❌ No se encontraron resultados")
    
    def create_theme_section(self, parent):
        """Sección de prueba de tema"""
        section = tk.Frame(parent, bg=self.colors['bg_card'],
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        section.pack(fill='x', pady=10)
        
        # Título
        tk.Label(section,
                text="🎨 Theme Toggle (Claro/Oscuro)",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_card'],
                fg=self.colors['accent_blue']).pack(pady=15, padx=20, anchor='w')
        
        # Info
        info_frame = tk.Frame(section, bg=self.colors['bg_card'])
        info_frame.pack(padx=20, pady=(0, 10))
        
        current_theme_label = tk.Label(info_frame,
                                       text=f"Tema actual: {self.current_theme.upper()}",
                                       font=('Segoe UI', 11),
                                       bg=self.colors['bg_card'],
                                       fg=self.colors['text_secondary'])
        current_theme_label.pack(side='left', padx=10)
        
        # Botón toggle
        icon = "🌙" if self.current_theme == 'dark' else "☀️"
        text = "Modo Claro" if self.current_theme == 'dark' else "Modo Oscuro"
        
        toggle_btn = ModernButton(info_frame,
                                 text=f"{icon}  {text}",
                                 style='secondary',
                                 command=lambda: self.toggle_theme(current_theme_label, toggle_btn))
        toggle_btn.pack(side='left', padx=10)
        
        # Nota
        tk.Label(section,
                text="Nota: En la app real, el tema se guarda en config.json",
                font=('Segoe UI', 9, 'italic'),
                bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(padx=20, pady=(0, 15))
    
    def toggle_theme(self, label, button):
        """Cambia el tema"""
        # Cambiar tema
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.colors = LIGHT_COLORS if self.current_theme == 'light' else ELITE_COLORS
        
        # Actualizar widgets (en la app real se refresca toda la pantalla)
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Actualizar label
        label.config(text=f"Tema actual: {self.current_theme.upper()}")
        
        # Actualizar botón
        icon = "🌙" if self.current_theme == 'dark' else "☀️"
        text = "Modo Claro" if self.current_theme == 'dark' else "Modo Oscuro"
        button.config(text=f"{icon}  {text}")
        
        # Toast
        theme_name = "Claro ☀️" if self.current_theme == 'light' else "Oscuro 🌙"
        ToastNotification(self.root, f"Tema cambiado a {theme_name}", 'info', 2000).show()
    
    def create_buttons_section(self, parent):
        """Sección de botones modernos"""
        section = tk.Frame(parent, bg=self.colors['bg_card'],
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
        section.pack(fill='x', pady=10)
        
        # Título
        tk.Label(section,
                text="🎯 Modern Buttons con Hover Effects",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_card'],
                fg=self.colors['accent_blue']).pack(pady=15, padx=20, anchor='w')
        
        # Botones
        buttons_frame = tk.Frame(section, bg=self.colors['bg_card'])
        buttons_frame.pack(padx=20, pady=(0, 20))
        
        styles = [
            ('Primary', 'primary'),
            ('Success', 'success'),
            ('Danger', 'danger'),
            ('Warning', 'warning'),
            ('Info', 'info'),
            ('Secondary', 'secondary')
        ]
        
        for name, style in styles:
            ModernButton(buttons_frame,
                        text=f"{name} Button",
                        style=style,
                        command=lambda n=name: ToastNotification(
                            self.root, f"Clic en botón {n}", 'info', 2000).show()).pack(side='left', padx=5)


def main():
    """Función principal"""
    root = tk.Tk()
    app = TestApp(root)
    root.mainloop()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST - COMPONENTES UX MODERNOS")
    print("=" * 60)
    print("\n📋 Componentes disponibles:")
    print("  1. 🔔 Toast Notifications (4 tipos + múltiples)")
    print("  2. 🔍 Search Bar con filtrado en tiempo real")
    print("  3. 🎨 Theme Toggle (Claro/Oscuro)")
    print("  4. 🎯 Modern Buttons (6 estilos)")
    print("\n🎮 Instrucciones:")
    print("  - Prueba cada botón para ver los componentes")
    print("  - Escribe en la barra de búsqueda")
    print("  - Cambia el tema con el toggle")
    print("  - Observa las animaciones y efectos hover")
    print("\n✨ ¡Disfruta probando los componentes!")
    print("=" * 60)
    print()
    
    main()
