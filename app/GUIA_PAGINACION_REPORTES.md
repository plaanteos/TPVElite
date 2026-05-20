# Guía Rápida - Paginación y Reportes Personalizados

## 🔍 Sistema de Paginación

### ¿Qué es la paginación?

La paginación divide grandes listas de datos en páginas más pequeñas, haciendo que la aplicación sea más rápida y fácil de usar.

### ¿Dónde encontrarla?

La paginación está disponible en:
- ✅ **Historial de Ventas** (Menú principal → Ventas)
- ✅ **Gestión de Productos** (Menú principal → Productos)
- ✅ **Gestión de Pedidos** (Menú principal → Pedidos → Tab Pedidos)

### Controles de Paginación

```
┌─────────────────────────────────────────────────────┐
│  [◀ Anterior]  Página 2 de 10 (478 registros)  [Siguiente ▶]  │
└─────────────────────────────────────────────────────┘
```

**Elementos:**

1. **Botón "◀ Anterior"**
   - Navega a la página anterior
   - Deshabilitado cuando estás en la página 1
   - Atajos: También puedes usar las flechas del teclado (si implementado)

2. **Indicador de Página**
   - Muestra: "Página [actual] de [total] ([registros totales] registros)"
   - Ejemplo: "Página 2 de 10 (478 registros)"
   - Te indica exactamente dónde estás en la lista

3. **Botón "Siguiente ▶"**
   - Navega a la siguiente página
   - Deshabilitado cuando estás en la última página

4. **Selector "Por página"**
   - Ubicado en la parte superior (cerca de los filtros)
   - Opciones disponibles:
     - Ventas: 10, 25, 50, 100, 200 registros
     - Productos: 25, 50, 100, 200 registros
     - Pedidos: 25, 50, 100, 200 registros
   - Cambia automáticamente cuando seleccionas otro valor

### Ejemplo de Uso - Ventas

**Paso 1:** Abre "Historial de Ventas"
- Click en "Ventas" en el menú lateral
- Se carga automáticamente la página 1 con 50 ventas (por defecto)

**Paso 2:** Ajusta el tamaño de página
- Busca el selector "Por página:" en la parte superior
- Selecciona "10" si quieres ver menos registros
- Selecciona "100" si quieres ver más registros
- La lista se actualiza automáticamente

**Paso 3:** Navega entre páginas
- Click en "Siguiente ▶" para ver más ventas
- Click en "◀ Anterior" para volver atrás
- El indicador siempre te muestra en qué página estás

**Paso 4:** Combina con filtros
- Selecciona rango de fechas
- Click en "🔍 Buscar"
- La paginación se reinicia a la página 1 con los resultados filtrados

### Ejemplo de Uso - Productos

**Paso 1:** Abre "Gestión de Productos"
- Click en "Productos" en el menú lateral
- Se cargan 50 productos en la primera página

**Paso 2:** Busca un producto específico
- Escribe en el campo "Buscar:" (ej: "Helado")
- Click en "🔍 Buscar"
- La paginación se aplica solo a los resultados de búsqueda

**Paso 3:** Ajusta la vista
- Cambia "Por página:" a 25 para ver menos productos por pantalla
- Usa "Anterior" y "Siguiente" para navegar
- Observa el contador: "Página 1 de 3 (65 registros)"

### Ventajas de la Paginación

✅ **Más Rápido:** Carga solo lo que necesitas ver  
✅ **Menos Scroll:** Listas más manejables  
✅ **Mejor Rendimiento:** La aplicación responde más rápido  
✅ **Fácil Navegación:** Encuentra lo que buscas más rápido  

---

## 📊 Reportes Personalizados

### ¿Qué son?

Los reportes personalizados te permiten generar análisis detallados de tus ventas con múltiples filtros y agrupaciones.

### ¿Cómo acceder?

1. Abre el **Dashboard** (pantalla principal)
2. Busca la sección "Informes Rápidos"
3. Click en **"📈 Reporte Personalizado"**
4. Se abre una ventana con opciones de configuración

### Opciones Disponibles

#### 1. Rango de Fechas

```
Desde: [2025-01-01]    Hasta: [2025-02-08]
```

- **Desde:** Fecha de inicio del período a analizar
- **Hasta:** Fecha de fin del período
- **Formato:** YYYY-MM-DD (Año-Mes-Día)
- **Por defecto:** Últimos 30 días

**Ejemplos:**
- Ventas de enero: Desde `2025-01-01` Hasta `2025-01-31`
- Ventas de hoy: Desde `2025-02-08` Hasta `2025-02-08`
- Último mes: Desde `2025-01-08` Hasta `2025-02-08`

#### 2. Categoría de Producto

```
Categoría: [Todas ▼]
```

**Opciones:**
- **Todas:** Incluye todos los productos sin filtro
- **Helados:** Solo ventas de helados
- **Postres:** Solo ventas de postres
- **Bebidas:** Solo ventas de bebidas
- *(Las categorías se cargan dinámicamente según tu inventario)*

**Cuándo usarlo:**
- Analizar qué categoría vende más
- Comparar rendimiento entre categorías
- Identificar productos estrella de una categoría

#### 3. Usuario Vendedor

```
Usuario: [Todos ▼]
```

**Opciones:**
- **Todos:** Ventas de todos los usuarios
- **Admin:** Solo ventas del usuario Admin
- **Juan:** Solo ventas del usuario Juan
- *(Se muestran todos los usuarios activos)*

**Cuándo usarlo:**
- Evaluar desempeño individual
- Calcular comisiones por vendedor
- Identificar mejores vendedores

#### 4. Método de Pago

```
Método Pago: [Todos ▼]
```

**Opciones:**
- **Todos:** Incluye todos los métodos
- **Efectivo:** Solo pagos en efectivo
- **Tarjeta:** Solo pagos con tarjeta
- **Transferencia:** Solo pagos por transferencia

**Cuándo usarlo:**
- Análisis de flujo de caja (efectivo vs. tarjeta)
- Reportes para conciliación bancaria
- Identificar preferencias de pago de clientes

#### 5. Estado de Venta

```
Estado: [Todos ▼]
```

**Opciones:**
- **Todos:** Incluye completadas y canceladas
- **Completada:** Solo ventas exitosas
- **Cancelada:** Solo ventas canceladas

**Cuándo usarlo:**
- Excluir ventas canceladas de reportes de ingresos
- Analizar motivos de cancelación
- Calcular tasa de éxito de ventas

#### 6. Agrupación y Análisis

```
⚪ Por día
⚪ Por semana
⚪ Por mes
⚪ Sin agrupación (detallado)
```

**Por Día:**
- Muestra totales diarios
- Útil para análisis de corto plazo
- Ejemplo: Comparar ventas de lunes vs. viernes

**Por Semana:**
- Agrupa ventas por semana (ISO)
- Útil para tendencias semanales
- Ejemplo: Identificar mejores semanas del mes

**Por Mes:**
- Totales mensuales
- Útil para análisis de largo plazo
- Ejemplo: Comparar enero vs. febrero

**Sin Agrupación (Detallado):**
- Lista todas las ventas individuales
- Incluye productos vendidos en cada venta
- Útil para auditorías y verificación

### Ejemplo Práctico 1: Ventas del Mes

**Objetivo:** Ver cuánto vendí en febrero

**Configuración:**
```
Desde: 2025-02-01
Hasta: 2025-02-28
Categoría: Todas
Usuario: Todos
Método Pago: Todos
Estado: Completada
Agrupación: Por día
```

**Resultado esperado:**
```
Período          Ventas     Productos    Total
================================================================
2025-02-01       15         245          $3,450.50
2025-02-02       18         302          $4,123.75
2025-02-03       12         198          $2,876.25
...
================================================================
TOTALES          478        7,856        $89,234.75

Promedio por venta: $186.67
```

### Ejemplo Práctico 2: Mejor Vendedor

**Objetivo:** ¿Quién vendió más en enero?

**Pasos:**
1. Genera un reporte para cada vendedor por separado:
   - Usuario: Admin → Anota el total
   - Usuario: Juan → Anota el total
   - Usuario: María → Anota el total

2. Configuración base:
```
Desde: 2025-01-01
Hasta: 2025-01-31
Categoría: Todas
Usuario: [Seleccionar cada uno]
Método Pago: Todos
Estado: Completada
Agrupación: Por mes
```

3. Compara los totales de cada reporte

### Ejemplo Práctico 3: Análisis de Categoría

**Objetivo:** ¿Los helados o los postres venden más?

**Configuración 1 (Helados):**
```
Desde: 2025-01-01
Hasta: 2025-02-08
Categoría: Helados
Usuario: Todos
Método Pago: Todos
Estado: Completada
Agrupación: Por mes
```

**Configuración 2 (Postres):**
```
Desde: 2025-01-01
Hasta: 2025-02-08
Categoría: Postres
Usuario: Todos
Método Pago: Todos
Estado: Completada
Agrupación: Por mes
```

**Resultado:** Compara el total de cada reporte

### Ejemplo Práctico 4: Auditoría Detallada

**Objetivo:** Revisar todas las ventas de un día específico

**Configuración:**
```
Desde: 2025-02-08
Hasta: 2025-02-08
Categoría: Todas
Usuario: Todos
Método Pago: Todos
Estado: Todos
Agrupación: Sin agrupación (detallado)
```

**Resultado esperado:**
```
Venta #V-2025-0001 - 2025-02-08 09:15:00
Usuario: Admin | Método: Efectivo
----------------------------------------------------------------
  Helado de Vainilla (500ml)           x2   @ $5.50      = $11.00
  Cono Chocolate                       x1   @ $2.00      = $2.00
----------------------------------------------------------------
TOTAL: $13.00

Venta #V-2025-0002 - 2025-02-08 10:30:00
Usuario: Juan | Método: Tarjeta
----------------------------------------------------------------
  Helado de Fresa (1L)                 x1   @ $9.00      = $9.00
  ...
```

### Exportar el Reporte

Una vez generado el reporte:

1. **Vista previa:** El reporte se muestra en una ventana
2. **Botón "💾 Guardar":** Click para exportar
3. **Selecciona formato:**
   - **TXT:** Archivo de texto plano
   - **PDF:** Documento PDF profesional
   - **XLSX:** Hoja de cálculo Excel
4. **Elige ubicación:** Selecciona dónde guardar el archivo
5. **Confirmar:** El archivo se guarda exitosamente

### Consejos y Trucos

💡 **Para reportes rápidos diarios:**
- Usa la misma fecha en "Desde" y "Hasta"
- Agrupación: "Sin agrupación"
- Así ves todas las ventas del día

💡 **Para análisis mensual:**
- Usa el primer y último día del mes
- Agrupación: "Por día"
- Así ves la tendencia día a día

💡 **Para comparar períodos:**
- Genera dos reportes (ej: enero y febrero)
- Mismos filtros, solo cambia las fechas
- Exporta ambos a Excel para comparar

💡 **Para conciliación bancaria:**
- Filtra por método: "Tarjeta"
- Agrupación: "Sin agrupación"
- Exporta a Excel y suma los totales

💡 **Para excluir ventas de prueba:**
- Estado: "Completada" (excluye canceladas)
- Así solo cuentas ventas reales

### Preguntas Frecuentes

**Q: ¿Puedo guardar mis configuraciones favoritas?**
A: Actualmente no, pero es una mejora planificada. Por ahora, anota tus configuraciones favoritas.

**Q: ¿Hay límite de registros en el reporte?**
A: No hay límite. Puedes generar reportes con miles de ventas, pero considera usar agrupación para reportes muy grandes.

**Q: ¿Puedo imprimir el reporte?**
A: Sí, exporta a PDF y luego imprime el PDF desde tu visor de PDF.

**Q: ¿Los reportes incluyen impuestos?**
A: Sí, los totales mostrados son los totales finales de cada venta, incluyendo impuestos.

**Q: ¿Puedo filtrar por rango de precios?**
A: Actualmente no, pero puedes exportar a Excel y filtrar allí.

---

## 📌 Resumen Rápido

### Para Paginación:
1. Abre cualquier lista (Ventas, Productos, Pedidos)
2. Ajusta "Por página:" según prefieras
3. Usa "◀ Anterior" y "Siguiente ▶" para navegar
4. El indicador te muestra siempre dónde estás

### Para Reportes Personalizados:
1. Dashboard → "📈 Reporte Personalizado"
2. Configura fechas y filtros según tu necesidad
3. Selecciona tipo de agrupación
4. Click "📊 Generar Reporte"
5. Revisa y exporta en el formato que prefieras

---

**¿Necesitas ayuda adicional?**
Consulta el manual completo en `MANUAL.md` o contacta al soporte técnico.
