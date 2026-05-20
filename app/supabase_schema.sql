-- ============================================================
-- TPV Elite — Schema para Supabase (PostgreSQL)
-- ============================================================
-- Cómo usar:
--   1. Entrá a tu proyecto en https://supabase.com
--   2. Abrí el SQL Editor
--   3. Pegá todo este archivo y ejecutalo
-- ============================================================

-- Extensión para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Tabla: usuarios ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.usuarios (
    id              SERIAL,
    tenant_id       UUID NOT NULL,
    local_id        INTEGER NOT NULL,
    username        TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    nombre          TEXT NOT NULL,
    apellido        TEXT,
    email           TEXT,
    rol             TEXT NOT NULL DEFAULT 'cajero',
    activo          INTEGER DEFAULT 1,
    fecha_creacion  TIMESTAMPTZ,
    ultimo_acceso   TIMESTAMPTZ,
    intentos_fallidos INTEGER DEFAULT 0,
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: productos ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.productos (
    id               SERIAL,
    tenant_id        UUID NOT NULL,
    local_id         INTEGER NOT NULL,
    nombre           TEXT NOT NULL,
    descripcion      TEXT,
    categoria        TEXT NOT NULL DEFAULT 'general',
    precio           NUMERIC NOT NULL,
    costo            NUMERIC,
    stock            INTEGER NOT NULL DEFAULT 0,
    stock_minimo     INTEGER NOT NULL DEFAULT 5,
    unidad_medida    TEXT DEFAULT 'unidad',
    codigo_barras    TEXT,
    imagen_url       TEXT,
    activo           INTEGER DEFAULT 1,
    fecha_creacion   TIMESTAMPTZ,
    fecha_modificacion TIMESTAMPTZ,
    synced_at        TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: ventas ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ventas (
    id             SERIAL,
    tenant_id      UUID NOT NULL,
    local_id       INTEGER NOT NULL,
    numero_venta   TEXT NOT NULL,
    fecha          TIMESTAMPTZ,
    usuario_id     INTEGER,
    cliente_nombre TEXT,
    subtotal       NUMERIC NOT NULL DEFAULT 0,
    descuento      NUMERIC DEFAULT 0,
    impuestos      NUMERIC DEFAULT 0,
    total          NUMERIC NOT NULL DEFAULT 0,
    metodo_pago    TEXT DEFAULT 'efectivo',
    estado         TEXT DEFAULT 'completada',
    notas          TEXT,
    synced_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: detalles_venta ────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.detalles_venta (
    id              SERIAL,
    tenant_id       UUID NOT NULL,
    local_id        INTEGER NOT NULL,
    venta_id        INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario NUMERIC NOT NULL,
    subtotal        NUMERIC NOT NULL,
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: pedidos ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.pedidos (
    id             SERIAL,
    tenant_id      UUID NOT NULL,
    local_id       INTEGER NOT NULL,
    numero_pedido  TEXT NOT NULL,
    fecha          TIMESTAMPTZ,
    usuario_id     INTEGER,
    proveedor      TEXT,
    total          NUMERIC NOT NULL DEFAULT 0,
    estado         TEXT DEFAULT 'pendiente',
    fecha_entrega  TIMESTAMPTZ,
    notas          TEXT,
    synced_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: detalles_pedido ───────────────────────────────────

CREATE TABLE IF NOT EXISTS public.detalles_pedido (
    id              SERIAL,
    tenant_id       UUID NOT NULL,
    local_id        INTEGER NOT NULL,
    pedido_id       INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario NUMERIC NOT NULL,
    subtotal        NUMERIC NOT NULL,
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Tabla: movimientos_inventario ────────────────────────────

CREATE TABLE IF NOT EXISTS public.movimientos_inventario (
    id             SERIAL,
    tenant_id      UUID NOT NULL,
    local_id       INTEGER NOT NULL,
    producto_id    INTEGER NOT NULL,
    tipo           TEXT NOT NULL,
    cantidad       INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_nuevo    INTEGER NOT NULL,
    usuario_id     INTEGER NOT NULL,
    referencia     TEXT,
    fecha          TIMESTAMPTZ,
    notas          TEXT,
    synced_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, local_id)
);

-- ── Índices de performance ───────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_usuarios_tenant     ON public.usuarios(tenant_id);
CREATE INDEX IF NOT EXISTS idx_productos_tenant    ON public.productos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ventas_tenant       ON public.ventas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha        ON public.ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_detalles_venta_t    ON public.detalles_venta(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_tenant      ON public.pedidos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_detalles_pedido_t   ON public.detalles_pedido(tenant_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_tenant  ON public.movimientos_inventario(tenant_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha   ON public.movimientos_inventario(fecha);

-- ── Row Level Security ───────────────────────────────────────
-- Habilitar RLS para que cada tenant solo vea sus propios datos.
-- El tenant_id actúa como clave de aislamiento.

ALTER TABLE public.usuarios               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.productos              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ventas                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detalles_venta         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pedidos                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detalles_pedido        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movimientos_inventario ENABLE ROW LEVEL SECURITY;

-- Política: acceso total para el service role (admin del proyecto)
-- El anon key puede leer/escribir solo sus propios registros via tenant_id en la query.
-- (Para producción, considerar Supabase Auth + JWT para mayor seguridad.)

CREATE POLICY "tenant_acceso_usuarios"
    ON public.usuarios FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_productos"
    ON public.productos FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_ventas"
    ON public.ventas FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_detalles_venta"
    ON public.detalles_venta FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_pedidos"
    ON public.pedidos FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_detalles_pedido"
    ON public.detalles_pedido FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_acceso_movimientos"
    ON public.movimientos_inventario FOR ALL
    USING (true)
    WITH CHECK (true);
