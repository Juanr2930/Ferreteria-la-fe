import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3
import os
from io import BytesIO
import hashlib
import time

st.set_page_config(page_title="Ferretería La Fe - Sistema 606 PRO", layout="wide", page_icon="🧱")

DB_FILE = "lafe_606.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inventario (
        Código TEXT PRIMARY KEY,
        Producto TEXT NOT NULL,
        "Precio RD$" REAL NOT NULL,
        Stock INTEGER NOT NULL,
        Cat TEXT,
        Icono TEXT
    );
    CREATE TABLE IF NOT EXISTS fiados (
        Cliente TEXT,
        WhatsApp TEXT,
        WhatsApp_Display TEXT,
        Monto REAL,
        Fecha TEXT,
        Vence TEXT,
        "Que llevó" TEXT,
        Estado TEXT
    );
    CREATE TABLE IF NOT EXISTS ventas_config (
        clave TEXT PRIMARY KEY,
        valor TEXT
    );
    INSERT OR IGNORE INTO ventas_config (clave, valor) VALUES ('ventas_hoy', '0');
    INSERT OR IGNORE INTO ventas_config (clave, valor) VALUES ('contador_factura', '1');
    """)
    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]
    if count == 0:
        cur.executemany("INSERT INTO inventario VALUES (?,?,?,?,?,?)", [
            ["CEM001", "Cemento Panam 94lbs", 550, 120, "Cemento", "🏗️"],
            ["CEM002", "Cemento Cemex", 565, 80, "Cemento", "🏗️"],
            ["VAR001", "Varilla 3/8 x 20", 420, 200, "Varilla", "🔩"],
            ["VAR002", "Varilla 1/2 x 20", 680, 150, "Varilla", "🔩"],
            ["BLK04", "Block 4''", 35, 1000, "Blocks", "🧱"],
            ["BLK06", "Block 6''", 42, 1500, "Blocks", "🧱"],
            ["BLK08", "Block 8''", 48, 800, "Blocks", "🧱"],
            ["ZIN001", "Zinc Acanalado 10ft", 750, 50, "Techo", "🏠"],
            ["ALAM01", "Alambre Dulce lb", 85, 100, "Alambres", "🪢"],
            ["CLAV01", "Clavo 2 1/2 lb", 120, 60, "Clavos", "🔨"],
            ["PINT01", "Pintura Tropical Galón", 1850, 30, "Pintura", "🎨"],
            ["ARE001", "Arena Lavada m3", 2500, 20, "Agregados", "🏖️"],
            ["GRAV01", "Grava m3", 2800, 15, "Agregados", "🪨"],
        ])
        conn.commit()
    conn.close()

init_db()

# ========== LICENCIA 606 PRO - FIX DEFINITIVO ==========
def generar_clave(nombre_negocio, telefono):
    base = f"606-{nombre_negocio.upper().strip()}-{telefono}-LAFE2026"
    hash_corto = hashlib.md5(base.encode()).hexdigest().upper()[:12]
    return f"LAFE-{hash_corto[:4]}-{hash_corto[4:8]}-{hash_corto[8:12]}"

def verificar_licencia():
    conn = get_conn()
    try:
        row2 = conn.execute("SELECT valor FROM ventas_config WHERE clave='licencia_activa'").fetchone()
        row = conn.execute("SELECT valor FROM ventas_config WHERE clave='licencia_key'").fetchone()
        conn.close()
        if row2 and str(row2[0]) == "1":
            return True, row[0] if row else "ACTIVA"
        return False, None
    except:
        conn.close()
        return False, None

lic_activa, clave_actual = verificar_licencia()

if not lic_activa:
    st.markdown("# 🔒 Sistema 606 PRO - RD$ 25,000")
    st.markdown("### Ferretería La Fe - Activación")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛠️ Generador Admin")
        nombre_input = st.text_input("Nombre ferretería cliente", key="nom_admin", placeholder="ferreteria juan")
        tel_input = st.text_input("Teléfono cliente", key="tel_admin", placeholder="8292647574")
        if st.button("🔑 Generar Clave"):
            if nombre_input and tel_input:
                clave_gen = generar_clave(nombre_input, tel_input)
                st.session_state['ultima_clave_gen'] = clave_gen
                st.session_state['ultimo_nombre_gen'] = nombre_input
                st.success("Clave generada abajo:")
                st.code(clave_gen)
            else:
                st.error("Llena nombre y teléfono")

    with col2:
        st.subheader("🔓 Activar Sistema")
        valor_default = st.session_state.get('ultima_clave_gen', 'LAFE-A737-22C4-8670')
        clave_cliente = st.text_input("Pega tu Clave", value=valor_default, key="clave_act")
        if st.button("✅ Activar Sistema RD$ 25k", type="primary", use_container_width=True):
            clave_limpia = clave_cliente.strip().upper()
            if clave_limpia.startswith("LAFE-"):
                conn = get_conn()
                nombre_final = st.session_state.get('ultimo_nombre_gen', nombre_input if 'nombre_input' in locals() and nombre_input else 'Ferreteria Juan')
                conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('licencia_key', ?)", (clave_limpia,))
                conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('licencia_activa', '1')")
                conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('negocio_nombre', ?)", (nombre_final,))
                conn.commit()
                conn.close()
                st.success(f"✅ Activado para {nombre_final}!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("Clave debe empezar con LAFE-")
    
    st.info("Truco: Genera la clave a la izquierda y dale directo a Activar a la derecha, ya se copia sola.")
    st.caption("Compra: Ferretería La Fe - 829-264-7574 - RD$25k")
    st.stop()

# ========== CARGAR ESTADO ==========
def cargar_sql():
    conn = get_conn()
    try:
        df_inv = pd.read_sql("SELECT * FROM inventario", conn)
        df_fiados = pd.read_sql("SELECT * FROM fiados", conn)
        fiados_list = df_fiados.to_dict('records') if not df_fiados.empty else []
        ventas_row = conn.execute("SELECT valor FROM ventas_config WHERE clave='ventas_hoy'").fetchone()
        ventas = float(ventas_row[0]) if ventas_row else 0
        contador_row = conn.execute("SELECT valor FROM ventas_config WHERE clave='contador_factura'").fetchone()
        contador = int(float(contador_row[0])) if contador_row else 1
        conn.close()
        return df_inv, fiados_list, ventas, contador
    except:
        conn.close()
        return None, None, None, None

def save_inv(df):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM inventario")
        df.to_sql("inventario", conn, if_exists="append", index=False)
        conn.commit()
    except:
        pass
    conn.close()

def save_fiados(lista):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM fiados")
        if lista:
            pd.DataFrame(lista).to_sql("fiados", conn, if_exists="append", index=False)
        conn.commit()
    except:
        pass
    conn.close()

def save_ventas(monto):
    conn = get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('ventas_hoy', ?)", (str(monto),))
        conn.commit()
    except:
        pass
    conn.close()

def save_contador(num):
    conn = get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('contador_factura', ?)", (str(num),))
        conn.commit()
    except:
        pass
    conn.close()

if 'inventario' not in st.session_state:
    df_s, f_s, v_s, c_s = cargar_sql()
    if df_s is not None and not df_s.empty:
        st.session_state.inventario = df_s
        st.session_state.fiados = f_s if f_s else []
        st.session_state.ventas_hoy = v_s if v_s else 0
        st.session_state.contador_factura = c_s if c_s else 1
    else:
        st.session_state.inventario = pd.DataFrame([
            ["CEM001", "Cemento Panam 94lbs", 550, 120, "Cemento", "🏗️"],
            ["CEM002", "Cemento Cemex", 565, 80, "Cemento", "🏗️"],
            ["VAR001", "Varilla 3/8 x 20", 420, 200, "Varilla", "🔩"],
            ["VAR002", "Varilla 1/2 x 20", 680, 150, "Varilla", "🔩"],
            ["BLK04", "Block 4''", 35, 1000, "Blocks", "🧱"],
            ["BLK06", "Block 6''", 42, 1500, "Blocks", "🧱"],
            ["BLK08", "Block 8''", 48, 800, "Blocks", "🧱"],
            ["ZIN001", "Zinc Acanalado 10ft", 750, 50, "Techo", "🏠"],
            ["ALAM01", "Alambre Dulce lb", 85, 100, "Alambres", "🪢"],
            ["CLAV01", "Clavo 2 1/2 lb", 120, 60, "Clavos", "🔨"],
            ["PINT01", "Pintura Tropical Galón", 1850, 30, "Pintura", "🎨"],
            ["ARE001", "Arena Lavada m3", 2500, 20, "Agregados", "🏖️"],
            ["GRAV01", "Grava m3", 2800, 15, "Agregados", "🪨"],
        ], columns=["Código", "Producto", "Precio RD$", "Stock", "Cat", "Icono"])
        st.session_state.fiados = []
        st.session_state.ventas_hoy = 0
        st.session_state.contador_factura = 1

if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'ultima_factura' not in st.session_state:
    st.session_state.ultima_factura = None
if 'calc_temp' not in st.session_state:
    st.session_state.calc_temp = None
if 'calc_detalle' not in st.session_state:
    st.session_state.calc_detalle = None

def agregar_al_carrito(nuevo_item):
    for i, item in enumerate(st.session_state.carrito):
        if item['Producto'] == nuevo_item['Producto']:
            st.session_state.carrito[i]['Cant'] += nuevo_item['Cant']
            st.session_state.carrito[i]['Total'] += nuevo_item['Total']
            return
    st.session_state.carrito.append(nuevo_item)

def generar_texto_factura(cliente, carrito, subtotal, itbis, total, num_factura):
    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    lineas = [f"{'='*42}", "      FERRETERIA LA FE - QUISQUEYA", "      San Pedro de Macoris, RD", f"{'='*42}", f"FACTURA No: {num_factura:06d}", f"FECHA: {fecha}", f"CLIENTE: {cliente}", f"{'-'*42}"]
    for item in carrito:
        lineas.append(f"{item['Cant']} x {item['Producto'][:28]}")
        lineas.append(f"   RD$ {item['Total']:,}")
    lineas += [f"{'-'*42}", f"SUBTOTAL: RD$ {subtotal:,.2f}", f"ITBIS 18%: RD$ {itbis:,.2f}", f"TOTAL: RD$ {total:,.2f}", f"{'='*42}", "  Gracias por su compra!"]
    return "\n".join(lineas)

def imprimir_factura_html(texto_factura, num_factura):
    html_code = f"""<html><head><style>@page {{ size: 80mm auto; margin: 2mm; }} body {{ font-family: 'Courier New', monospace; width: 72mm; font-size: 12px; line-height: 1.3; margin: 0 auto; background: white; color: black; }} pre {{ white-space: pre-wrap; }} .btn-print {{ background: #FF6B00; color: white; border: none; padding: 15px 20px; font-size: 18px; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 15px; font-weight: bold; }} @media print {{ .btn-print {{ display: none; }} }}</style></head><body><pre>{texto_factura}</pre><button class="btn-print" onclick="window.print()">IMPRIMIR FACTURA {num_factura:06d}</button></body></html>"""
    components.html(html_code, height=700, scrolling=True)

def generar_link_whatsapp(numero, cliente, monto, que_llevo, fecha):
    num_limpio = "".join(filter(str.isdigit, str(numero)))
    if len(num_limpio) == 10:
        num_limpio = "1" + num_limpio
    mensaje = f"Hola {cliente}, balance pendiente RD$ {monto:,} - {que_llevo} - Ferreteria La Fe"
    return f"https://wa.me/{num_limpio}?text={urllib.parse.quote(mensaje)}", num_limpio

def validar_numero_rd(numero):
    num_limpio = "".join(filter(str.isdigit, str(numero)))
    if len(num_limpio) == 11 and num_limpio.startswith("1"):
        num_limpio = num_limpio[1:]
    if len(num_limpio) != 10:
        return False, "10 dígitos", num_limpio
    if num_limpio[:3] not in ["809","829","849"]:
        return False, "809/829/849", num_limpio
    return True, "Válido", num_limpio

# HEADER
conn = get_conn()
try:
    negocio_nombre_row = conn.execute("SELECT valor FROM ventas_config WHERE clave='negocio_nombre'").fetchone()
    nombre_mostrar = negocio_nombre_row[0] if negocio_nombre_row else "Ferretería La Fe"
    conn.close()
except:
    nombre_mostrar = "Ferretería La Fe"

col_logo, col_title = st.columns([1,4])
with col_logo:
    try:
        st.image("logo.png", width=110)
    except:
        st.markdown("### 🧱 La Fe")
with col_title:
    st.markdown(f"## {nombre_mostrar} - Sistema 606 PRO")
    st.caption(f"✅ Licencia: {clave_actual} | SQL Persistente")

with st.sidebar:
    st.title(nombre_mostrar)
    st.success(f"🔒 {clave_actual}")
    menu = st.radio("Ir a:", ["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("💾 Guardar en SQL", type="primary", use_container_width=True):
        save_inv(st.session_state.inventario)
        save_fiados(st.session_state.fiados)
        save_ventas(st.session_state.ventas_hoy)
        save_contador(st.session_state.contador_factura)
        st.success("Guardado!")
    st.divider()
    st.subheader("💾 Backups")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            st.download_button(label="📥 Backup DB", data=f, file_name=f"lafe_606_backup_{date.today()}.db", mime="application/octet-stream", use_container_width=True)
        try:
            conn = get_conn()
            df_inv_excel = pd.read_sql("SELECT * FROM inventario", conn)
            df_fiados_excel = pd.read_sql("SELECT * FROM fiados", conn)
            conn.close()
            csv_inv = df_inv_excel.to_csv(index=False).encode('utf-8')
            st.download_button(label="📊 Inventario Excel", data=csv_inv, file_name=f"Inventario_{date.today()}.csv", mime="text/csv", use_container_width=True)
            if not df_fiados_excel.empty:
                csv_fiados = df_fiados_excel.to_csv(index=False).encode('utf-8')
                st.download_button(label="📓 Fiados Excel", data=csv_fiados, file_name=f"Fiados_{date.today()}.csv", mime="text/csv", use_container_width=True, type="primary")
        except:
            pass
    st.divider()
    if st.button("🔄 Resetear"):
        st.session_state.clear()
        st.rerun()

# VENTAS
if menu == "🛒 Punto de Venta":
    c1, c2 = st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        codigo_escaneado = st.text_input("Pistolea código", placeholder="CEM001")
        if st.button("🔎 Buscar Código"):
            inv = st.session_state.inventario
            match = inv[inv["Código"].str.upper().str.strip() == codigo_escaneado.upper().strip()]
            if not match.empty:
                row = match.iloc[0]
                agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio RD$'],"Total":1*row['Precio RD$'],"Código":row['Código']})
                st.rerun()
        buscador = st.text_input("Busca producto")
        if buscador:
            res = st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            for idx, row in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Producto']}** - RD$ {row['Precio RD$']} | Stock {row['Stock']}")
                    cant = st.number_input("Cant",1,1000,1,key=f"cant_{row['Código']}")
                    if st.button("Agregar", key=f"add_{row['Código']}"):
                        agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                        st.rerun()
    with c2:
        st.subheader("Factura")
        cliente_factura = st.text_input("Cliente", value="Cliente Mostrador")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                st.write(f"{item.get('Icono','')} {item['Producto'][:22]} - {item['Cant']} x RD$ {item['Total']:,}")
            subtotal = sum([x['Total'] for x in st.session_state.carrito])
            total = subtotal * 1.18
            st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                num = st.session_state.contador_factura
                texto_fact = generar_texto_factura(cliente_factura, st.session_state.carrito, subtotal, subtotal*0.18, total, num)
                st.session_state.ultima_factura = {"texto": texto_fact, "num": num}
                st.session_state.ventas_hoy += total
                st.session_state.contador_factura += 1
                for item in st.session_state.carrito:
                    if item.get("Código"):
                        idx = st.session_state.inventario[st.session_state.inventario["Código"]==item["Código"]].index
                        if not idx.empty:
                            st.session_state.inventario.loc[idx, "Stock"] -= item["Cant"]
                save_inv(st.session_state.inventario)
                save_ventas(st.session_state.ventas_hoy)
                save_contador(st.session_state.contador_factura)
                st.session_state.carrito = []
                st.balloons()
                st.rerun()
            if st.button("🗑️ Vaciar"):
                st.session_state.carrito = []
                st.rerun()
        if st.session_state.ultima_factura:
            st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", use_container_width=True)
            imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu == "📦 Catálogo":
    st.dataframe(st.session_state.inventario[["Código","Producto","Precio RD$","Stock"]], use_container_width=True)

elif menu == "🧮 Calculadora Materiales":
    st.title("🧮 Calculadora")
    obra = st.selectbox("Obra", ["Pared de Blocks", "Casita 3x3"])
    if obra == "Pared de Blocks":
        c1, c2, c3 = st.columns(3)
        largo = c1.number_input("Largo (m)", 1.0, 100.0, 10.0)
        alto = c2.number_input("Alto (m)", 1.0, 10.0, 2.5)
        tipo = c3.selectbox("Tipo", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"])
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared", type="primary"):
            m2 = largo * alto
            blocks = int(m2 * 12.5) + 5
            total = blocks * precio_block + 5 * 550
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"total": total, "titulo": f"Pared {m2} m2 {blocks} blocks"}
    if st.session_state.calc_detalle:
        st.markdown(f"### TOTAL: RD$ {st.session_state.calc_detalle['total']:,}")
        if st.button("➕ AGREGAR AL CARRITO", type="primary", use_container_width=True):
            agregar_al_carrito(st.session_state.calc_temp)
            st.rerun()

elif menu == "📓 Fiado":
    st.title("📓 Fiado")
    cliente = st.text_input("Nombre")
    telefono = st.text_input("WhatsApp")
    monto = st.number_input("Monto", min_value=100, value=5000)
    if st.button("Guardar Fiado"):
        ok, msg, num_l = validar_numero_rd(telefono)
        if ok:
            st.session_state.fiados.append({"Cliente": cliente,"WhatsApp": num_l,"WhatsApp_Display": num_l,"Monto": monto,"Fecha": str(date.today()),"Vence": str(date.today()),"Que llevó": "","Estado": "Pendiente"})
            save_fiados(st.session_state.fiados)
            st.success("Guardado")
    for i, row in enumerate(st.session_state.fiados):
        with st.container(border=True):
            st.write(f"{row['Cliente']} - RD$ {row['Monto']:,}")
            if st.button("Cobrado", key=f"c_{i}"):
                st.session_state.fiados[i]["Estado"]="Pagado"
                save_fiados(st.session_state.fiados)
                st.rerun()

elif menu == "📊 Cierre":
    st.title("Cierre")
    st.metric("Ventas Hoy", f"RD$ {st.session_state.ventas_hoy:,.0f}")
    if st.button("Cerrar Día"):
        st.session_state.ventas_hoy = 0
        save_ventas(0)
        st.rerun()
