import streamlit as st
import psycopg2
import urllib.parse as urlparse
import socket
import pandas as pd
import math
from datetime import date

st.set_page_config(page_title="Sistema 606 PRO - CLOUD", layout="wide")

# ================= CONEXION ARREGLADA - IPv4 / IPv6 =================
def get_conn():
    raw = st.secrets["DATABASE_URL"].strip().strip('"').strip("'").replace("\n", "").replace(" ", "")
    parsed = urlparse.urlparse(raw)
    host = parsed.hostname

    # Resolvemos el host a IP a mano para que Streamlit no falle con DNS
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = None

    kwargs = dict(
        host=host,
        port=parsed.port or 6543,
        user=parsed.username,
        password=parsed.password,
        dbname=parsed.path.lstrip("/"),
        sslmode="require",
        connect_timeout=10
    )
    if ip:
        kwargs["hostaddr"] = ip

    return psycopg2.connect(**kwargs)

def run(sql, params=None, fetch=False):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    data = None
    if fetch:
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        data = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
    conn.commit()
    cur.close()
    conn.close()
    return data

def init_db():
    run("""CREATE TABLE IF NOT EXISTS inventario (
        id SERIAL PRIMARY KEY,
        producto TEXT NOT NULL,
        categoria TEXT DEFAULT 'General',
        precio NUMERIC DEFAULT 0,
        costo NUMERIC DEFAULT 0,
        stock INTEGER DEFAULT 0,
        codigo TEXT DEFAULT ''
    )""")
    run("""CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        telefono TEXT DEFAULT '',
        deuda NUMERIC DEFAULT 0
    )""")
    run("""CREATE TABLE IF NOT EXISTS fiados (
        id SERIAL PRIMARY KEY,
        cliente TEXT NOT NULL,
        producto TEXT NOT NULL,
        monto NUMERIC DEFAULT 0,
        fecha DATE DEFAULT CURRENT_DATE,
        estado TEXT DEFAULT 'Pendiente'
    )""")
    run("""CREATE TABLE IF NOT EXISTS facturas (
        id SERIAL PRIMARY KEY,
        cliente TEXT NOT NULL,
        total NUMERIC DEFAULT 0,
        fecha DATE DEFAULT CURRENT_DATE,
        detalle TEXT DEFAULT ''
    )""")

try:
    init_db()
except Exception as e:
    st.error(f"ERROR REAL DE SUPABASE: {e}")
    st.info("Copia este mensaje tal cual y mandamelo. Este es el error que Streamlit te estaba tapando.")
    st.stop()

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("## 🔐 Sistema 606 PRO - CLOUD")
    st.markdown("### Ferretería La Fe")
    clave = st.text_input("Clave de acceso", type="password")
    if st.button("Entrar", use_container_width=True):
        if clave.strip() == "LAFE-606" or clave.strip() == "LaFe6060":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# ================= APP =================
st.markdown("# 🛠️ Sistema 606 PRO - CLOUD")
st.markdown("**Ferretería La Fe | San Pedro de Macorís**")

menu = st.sidebar.selectbox("Menú", ["📦 Inventario", "👥 Clientes / Fiados", "🧾 Facturar", "🧮 Calculadora de Materiales", "📊 Reportes"])
st.sidebar.success("✅ Conectado a Supabase")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.auth = False
    st.rerun()

# ---------- INVENTARIO ----------
if menu == "📦 Inventario":
    st.subheader("📦 Inventario")
    with st.expander("➕ Agregar producto", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            prod = st.text_input("Producto")
        with c2:
            cat = st.selectbox("Categoría", ["General", "Ferretería", "Plomería", "Electricidad", "Pintura", "Herramientas", "Construcción"])
        with c3:
            precio = st.number_input("Precio venta", min_value=0.0, value=0.0)
        with c4:
            stock = st.number_input("Stock", min_value=0, value=0)
        costo = st.number_input("Costo", min_value=0.0, value=0.0)
        codigo = st.text_input("Código / SKU")
        if st.button("Guardar producto", use_container_width=True):
            if prod.strip():
                run("INSERT INTO inventario (producto, categoria, precio, costo, stock, codigo) VALUES (%s,%s,%s,%s,%s,%s)",
                    (prod.strip(), cat, precio, costo, stock, codigo.strip()))
                st.success(f"✅ {prod} guardado")
                st.rerun()
            else:
                st.error("Escribe el nombre del producto")

    buscar = st.text_input("🔍 Buscar producto")
    if buscar:
        df = run("SELECT id, producto, categoria, precio, costo, stock, codigo FROM inventario WHERE producto ILIKE %s OR codigo ILIKE %s ORDER BY id DESC", (f"%{buscar}%", f"%{buscar}%"), fetch=True)
    else:
        df = run("SELECT id, producto, categoria, precio, costo, stock, codigo FROM inventario ORDER BY id DESC", fetch=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if df is not None and not df.empty:
        st.markdown("---")
        st.markdown("**Editar / Eliminar**")
        id_sel = st.selectbox("Selecciona ID", df["id"].tolist())
        fila = df[df["id"] == id_sel].iloc[0]
        e1, e2 = st.columns(2)
        with e1:
            nuevo_precio = st.number_input("Nuevo precio", value=float(fila["precio"]))
        with e2:
            nuevo_stock = st.number_input("Nuevo stock", value=int(fila["stock"]))
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("💾 Actualizar", use_container_width=True):
                run("UPDATE inventario SET precio=%s, stock=%s WHERE id=%s", (nuevo_precio, nuevo_stock, int(id_sel)))
                st.success("Actualizado")
                st.rerun()
        with col_b:
            if st.button("🗑️ Eliminar", use_container_width=True):
                run("DELETE FROM inventario WHERE id=%s", (int(id_sel),))
                st.success("Eliminado")
                st.rerun()

# ---------- CLIENTES / FIADOS ----------
elif menu == "👥 Clientes / Fiados":
    st.subheader("👥 Clientes y Fiados")
    tab1, tab2 = st.tabs(["Clientes", "Fiados"])
    with tab1:
        with st.form("nuevo_cliente"):
            nombre = st.text_input("Nombre del cliente")
            tel = st.text_input("Teléfono")
            if st.form_submit_button("Guardar cliente"):
                if nombre.strip():
                    run("INSERT INTO clientes (nombre, telefono) VALUES (%s,%s)", (nombre.strip(), tel.strip()))
                    st.success("Cliente guardado")
                    st.rerun()
        df_c = run("SELECT id, nombre, telefono, deuda FROM clientes ORDER BY id DESC", fetch=True)
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    with tab2:
        with st.form("nuevo_fiado"):
            cliente_f = st.text_input("Cliente que fía")
            prod_f = st.text_input("Producto fiado")
            monto_f = st.number_input("Monto", min_value=0.0, value=0.0)
            if st.form_submit_button("Registrar fiado"):
                if cliente_f.strip() and prod_f.strip():
                    run("INSERT INTO fiados (cliente, producto, monto, fecha) VALUES (%s,%s,%s,%s)", (cliente_f.strip(), prod_f.strip(), monto_f, date.today()))
                    run("UPDATE clientes SET deuda = deuda + %s WHERE nombre ILIKE %s", (monto_f, cliente_f.strip()))
                    st.success("Fiado registrado")
                    st.rerun()
        df_f = run("SELECT id, cliente, producto, monto, fecha, estado FROM fiados ORDER BY id DESC", fetch=True)
        st.dataframe(df_f, use_container_width=True, hide_index=True)
        if df_f is not None and not df_f.empty:
            id_pagar = st.selectbox("Marcar como pagado - ID", df_f["id"].tolist())
            if st.button("✅ Marcar Pagado"):
                fila_f = df_f[df_f["id"] == id_pagar].iloc[0]
                run("UPDATE fiados SET estado='Pagado' WHERE id=%s", (int(id_pagar),))
                run("UPDATE clientes SET deuda = deuda - %s WHERE nombre ILIKE %s", (float(fila_f["monto"]), str(fila_f["cliente"])))
                st.success("Pagado")
                st.rerun()

# ---------- FACTURAR ----------
elif menu == "🧾 Facturar":
    st.subheader("🧾 Facturar")
    df_inv = run("SELECT id, producto, precio, stock FROM inventario ORDER BY producto", fetch=True)
    if df_inv is not None and not df_inv.empty:
        cliente_fact = st.text_input("Cliente")
        prod_sel = st.selectbox("Producto", df_inv["producto"].tolist())
        fila_p = df_inv[df_inv["producto"] == prod_sel].iloc[0]
        st.info(f"Precio: RD$ {float(fila_p['precio']):,.2f} | Stock: {int(fila_p['stock'])}")
        cant = st.number_input("Cantidad", min_value=1, value=1)
        total = float(fila_p["precio"]) * cant
        st.markdown(f"### Total: RD$ {total:,.2f}")
        if st.button("🧾 Generar Factura", use_container_width=True):
            run("INSERT INTO facturas (cliente, total, fecha, detalle) VALUES (%s,%s,%s,%s)",
                (cliente_fact or "Cliente General", total, date.today(), f"{cant} x {prod_sel}"))
            run("UPDATE inventario SET stock = stock - %s WHERE id=%s", (int(cant), int(fila_p["id"])))
            st.success(f"✅ Factura generada - Total RD$ {total:,.2f}")
            st.balloons()
        st.markdown("---")
        st.markdown("**Últimas Facturas**")
        df_fact_list = run("SELECT id, cliente, total, fecha, detalle FROM facturas ORDER BY id DESC LIMIT 20", fetch=True)
        st.dataframe(df_fact_list, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay productos en inventario. Agrega primero en Inventario.")

# ---------- CALCULADORA DE MATERIALES ----------
elif menu == "🧮 Calculadora de Materiales":
    st.subheader("🧮 Calculadora de Materiales - Ferretería La Fe")
    st.markdown("Calcula cemento, arena, grava, blocks y varilla para que el cliente sepa cuánto comprar.")

    tipo = st.selectbox("¿Qué va a construir?", ["🧱 Pared de Blocks", "🏗️ Losa / Techo de Concreto", "🦶 Zapata / Columna", "🧱 Piso / Contrapiso", "🧱 Repello / Pañete"])

    # Precios editables para que puedas cotizar de una vez
    st.markdown("**Precios de hoy (puedes cambiarlos)**")
    p1, p2, p3, p4, p5 = st.columns(5)
    with p1:
        pr_cemento = st.number_input("Cemento (funda)", value=650.0)
    with p2:
        pr_arena = st.number_input("Arena (m³)", value=1800.0)
    with p3:
        pr_grava = st.number_input("Grava (m³)", value=2000.0)
    with p4:
        pr_block = st.number_input("Block (unidad)", value=65.0)
    with p5:
        pr_varilla = st.number_input("Varilla (unidad)", value=450.0)

    total_estimado = 0
    detalle_calc = ""

    if tipo == "🧱 Pared de Blocks":
        c1, c2 = st.columns(2)
        with c1:
            largo = st.number_input("Largo de la pared (metros)", min_value=0.0, value=5.0)
        with c2:
            alto = st.number_input("Alto de la pared (metros)", min_value=0.0, value=2.5)
        area = largo * alto
        # Block 8": 12.5 blocks por m2
        blocks = math.ceil(area * 12.5)
        # Mortero: 1 funda cemento por cada 1.5 m2 aprox, arena 0.03 m3 por m2
        cemento = math.ceil(area / 1.5)
        arena = round(area * 0.03, 2)
        total_estimado = blocks * pr_block + cemento * pr_cemento + arena * pr_arena
        detalle_calc = f"Pared {largo}m x {alto}m = {area:.1f} m²"
        st.markdown(f"### 📐 Área: {area:.1f} m²")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("🧱 Blocks 8\"", blocks)
        with col_r2:
            st.metric("Cemento", f"{cemento} fundas")
        with col_r3:
            st.metric("Arena", f"{arena} m³")
        st.info("💡 Incluye 5% de desperdicio. Para block de 6\" usa la misma cantidad.")

    elif tipo == "🏗️ Losa / Techo de Concreto":
        c1, c2, c3 = st.columns(3)
        with c1:
            largo = st.number_input("Largo (metros)", min_value=0.0, value=6.0)
        with c2:
            ancho = st.number_input("Ancho (metros)", min_value=0.0, value=5.0)
        with c3:
            espesor = st.selectbox("Espesor", ["0.10 m (4 pulg)", "0.12 m (5 pulg)", "0.15 m (6 pulg)"])
        esp = float(espesor.split(" ")[0])
        volumen = largo * ancho * esp
        # Concreto 1:2:3 -> 7 fundas cemento por m3, 0.5 m3 arena, 0.7 m3 grava
        cemento = math.ceil(volumen * 7)
        arena = round(volumen * 0.5, 2)
        grava = round(volumen * 0.7, 2)
        # Varilla: 1 varilla 3/8 por cada 1.2 m2 aprox
        varilla = math.ceil((largo * ancho) / 1.2)
        total_estimado = cemento * pr_cemento + arena * pr_arena + grava * pr_grava + varilla * pr_varilla
        detalle_calc = f"Losa {largo}m x {ancho}m x {esp}m = {volumen:.2f} m³"
        st.markdown(f"### 📐 Volumen de concreto: {volumen:.2f} m³")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("Cemento", f"{cemento} fundas")
        with col_r2:
            st.metric("Arena", f"{arena} m³")
        with col_r3:
            st.metric("Grava", f"{grava} m³")
        with col_r4:
            st.metric("Varilla 3/8", f"{varilla} uds")

    elif tipo == "🦶 Zapata / Columna":
        c1, c2, c3 = st.columns(3)
        with c1:
            cantidad = st.number_input("Cantidad de zapatas / columnas", min_value=1, value=4)
        with c2:
            lado = st.number_input("Lado zapata (metros)", min_value=0.0, value=0.80)
        with c3:
            alto_c = st.number_input("Alto / Profundidad (metros)", min_value=0.0, value=0.80)
        volumen = cantidad * lado * lado * alto_c
        cemento = math.ceil(volumen * 8)
        arena = round(volumen * 0.5, 2)
        grava = round(volumen * 0.7, 2)
        varilla = cantidad * 4
        total_estimado = cemento * pr_cemento + arena * pr_arena + grava * pr_grava + varilla * pr_varilla
        detalle_calc = f"{cantidad} zapatas de {lado}m x {lado}m x {alto_c}m = {volumen:.2f} m³"
        st.markdown(f"### 📐 Volumen total: {volumen:.2f} m³")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("Cemento", f"{cemento} fundas")
        with col_r2:
            st.metric("Arena", f"{arena} m³")
        with col_r3:
            st.metric("Grava", f"{grava} m³")
        with col_r4:
            st.metric("Varilla 1/2", f"{varilla} uds")

    elif tipo == "🧱 Piso / Contrapiso":
        c1, c2, c3 = st.columns(3)
        with c1:
            largo = st.number_input("Largo (metros)", min_value=0.0, value=5.0)
        with c2:
            ancho = st.number_input("Ancho (metros)", min_value=0.0, value=4.0)
        with c3:
            espesor = st.selectbox("Espesor", ["0.05 m", "0.07 m", "0.10 m"])
        esp = float(espesor.split(" ")[0])
        volumen = largo * ancho * esp
        cemento = math.ceil(volumen * 6)
        arena = round(volumen * 0.6, 2)
        grava = round(volumen * 0.7, 2)
        total_estimado = cemento * pr_cemento + arena * pr_arena + grava * pr_grava
        detalle_calc = f"Piso {largo}m x {ancho}m x {esp}m = {volumen:.2f} m³"
        st.markdown(f"### 📐 Volumen: {volumen:.2f} m³")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Cemento", f"{cemento} fundas")
        with col_r2:
            st.metric("Arena", f"{arena} m³")
        with col_r3:
            st.metric("Grava", f"{grava} m³")

    elif tipo == "🧱 Repello / Pañete":
        c1, c2 = st.columns(2)
        with c1:
            largo = st.number_input("Largo pared (metros)", min_value=0.0, value=5.0)
        with c2:
            alto = st.number_input("Alto pared (metros)", min_value=0.0, value=2.5)
        area = largo * alto
        # Repello: 1 funda por 4 m2, arena 0.02 m3 por m2
        cemento = math.ceil(area / 4)
        arena = round(area * 0.02, 2)
        total_estimado = cemento * pr_cemento + arena * pr_arena
        detalle_calc = f"Repello {largo}m x {alto}m = {area:.1f} m²"
        st.markdown(f"### 📐 Área: {area:.1f} m²")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Cemento", f"{cemento} fundas")
        with col_r2:
            st.metric("Arena fina", f"{arena} m³")

    st.markdown("---")
    st.markdown(f"### 💰 Total Estimado: RD$ {total_estimado:,.2f}")
    st.caption(detalle_calc)
    st.caption("Precios estimados. Puedes cambiar los precios arriba para cotizar exacto.")

    if st.button("🧾 Guardar esta cotización como Factura", use_container_width=True):
        cliente_calc = st.text_input("Nombre del cliente para la cotización", key="cliente_calc")
        if cliente_calc.strip():
            run("INSERT INTO facturas (cliente, total, fecha, detalle) VALUES (%s,%s,%s,%s)",
                (cliente_calc.strip(), total_estimado, date.today(), f"CALCULADORA: {tipo} - {detalle_calc}"))
            st.success(f"✅ Cotización guardada como factura para {cliente_calc} - RD$ {total_estimado:,.2f}")
        else:
            st.warning("Escribe el nombre del cliente arriba para guardar la cotización")

# ---------- REPORTES ----------
elif menu == "📊 Reportes":
    st.subheader("📊 Reportes")
    df_inv2 = run("SELECT * FROM inventario", fetch=True)
    df_fiados2 = run("SELECT * FROM fiados WHERE estado='Pendiente'", fetch=True)
    df_fact = run("SELECT * FROM facturas ORDER BY id DESC", fetch=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Productos", len(df_inv2) if df_inv2 is not None else 0)
    with c2:
        total_fiado = df_fiados2["monto"].sum() if df_fiados2 is not None and not df_fiados2.empty else 0
        st.metric("Total Fiado Pendiente", f"RD$ {total_fiado:,.2f}")
    with c3:
        total_ventas = df_fact["total"].sum() if df_fact is not None and not df_fact.empty else 0
        st.metric("Total Ventas", f"RD$ {total_ventas:,.2f}")
    st.markdown("**Últimas Facturas / Cotizaciones**")
    st.dataframe(df_fact, use_container_width=True, hide_index=True)
    st.markdown("**Fiados Pendientes**")
    st.dataframe(df_fiados2, use_container_width=True, hide_index=True)
