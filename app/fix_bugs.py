#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para arreglar los bugs del TPV"""

import re

# Leer el archivo
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Eliminar el botón confirm_btn del header (líneas 3052-3057)
# Buscar y eliminar la sección del botón CONFIRMAR VENTA
pattern1 = r'\s+# Botón CONFIRMAR VENTA\s+confirm_btn = ModernButton\(header_content,\s+text="[^"]+CONFIRMAR VENTA",\s+style=\'success\',\s+padx=25,\s+pady=8\)\s+confirm_btn\.pack\(side=\'right\', padx=5\)\s+'
content = re.sub(pattern1, '\n        \n        # Contenedor principal con 2 columnas\n        ', content)

# 2. Arreglar las llamadas a _process_sale (eliminar total_label)
# Cambiar de: self._process_sale(cart_tree, total_label)
# A: self._process_sale(cart_tree)
content = content.replace(
    'command=lambda: self._process_sale(cart_tree, total_label)',
    'command=lambda: self._process_sale(cart_tree)'
)

# Eliminar la línea que configura confirm_btn
pattern2 = r'\s+# Configurar botón confirmar venta en header\s+confirm_btn\.configure\(command=lambda: self\._process_sale\(cart_tree, total_label\)\)\s+'
content = re.sub(pattern2, '\n        ', content)

# 3. Arreglar ToastNotification
# Cambiar de: ToastNotification(self.root, f"Tema cambiado a {theme_name}", 'info', 2000).show()
# A: ToastNotification(self.root, f"Tema cambiado a {theme_name}", 'info', 2000)
content = content.replace(
    "ToastNotification(self.root, f\"Tema cambiado a {theme_name}\", 'info', 2000).show()",
    "toast = ToastNotification(self.root, f\"Tema cambiado a {theme_name}\", 'info', 2000)\n            toast.show()"
)

# Guardar el archivo
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Cambios aplicados correctamente:")
print("   - Eliminado botón CONFIRMAR VENTA del header")
print("   - Corregidos parámetros de _process_sale()")
print("   - Corregido ToastNotification()")
