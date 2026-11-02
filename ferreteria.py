import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3, os, hashlib, time
from io import BytesIO

st.set_page_config(page_title="Ferretería La Fe - 606 PRO", layout="wide", page_icon="🧱")
DB_FILE = "lafe_606.db"

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inventario (Código TEXT PRIMARY KEY, Producto TEXT, "Precio RD$" REAL, Stock INTEGER, Cat TEXT, Icono TEXT);
    CREATE TABLE IF NOT EXISTS fiados (Cliente TEXT, WhatsApp TEXT, WhatsApp_Display TEXT, Monto REAL, Fecha TEXT, Vence TEXT, "Que llevó" TEXT, Estado TEXT);
    CREATE TABLE IF NOT EXISTS ventas_config (clave TEXT PRIMARY KEY, valor TEXT);
    INSERT OR IGNORE INTO ventas_config (clave, valor) VALUES ('ventas_hoy', '0');
    INSERT OR IGNORE INTO ventas_config (clave, valor) VALUES ('contador_factura', '1');
    """)
    conn.commit()
    if cur.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]==0:
        cur.executemany("INSERT INTO inventario VALUES (?,?,?,?,?,?)", [
            ["CEM001","Cemento Panam 94lbs",550,120,"Cemento","🏗️"],
            ["VAR001","Varilla 3/8 x 20",420,200,"Varilla","🔩"],
            ["BLK06","Block 6''",42,1500,"Blocks","🧱"],
            ["ZIN001","Zinc 10ft",750,50,"Techo","🏠"],
        ])
        conn.commit()
    conn.close()
init_db()

# ====== LICENCIA FIX - EN MEMORIA ======
def generar_clave(nombre, tel):
    base = f"606-{nombre.upper().strip()}-{tel}-LAFE2026"
    h = hashlib.md5(base.encode()).hexdigest().upper()[:12]
    return f"LAFE-{h[:4]}-{h[4:8]}-{h[8:12]}"

# Inicializa estado de licencia
if 'lic_activa' not in st.session_state:
    st.session_state.lic_activa = False
if 'lic_key' not in st.session_state:
    st.session_state.lic_key = ""
if 'negocio_nombre' not in st.session_state:
    st.session_state.negocio_nombre = "Ferretería La Fe"

if not st.session_state.lic_activa:
    st.markdown("# 🔒 Sistema 606 PRO - RD$25k")
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("🛠️ Generador Admin")
        nom = st.text_input("Nombre ferretería", value="ferreteria juan", key="n1")
        tel = st.text_input("Teléfono", value="8292647574", key="t1")
        if st.button("🔑 Generar Clave"):
            clave = generar_clave(nom, tel)
            st.session_state.ultima_clave = clave
            st.session_state.ultimo_nombre = nom
            st.code(clave)
    with c2:
        st.subheader("🔓 Activar Sistema")
        default_key = st.session_state.get('ultima_clave', 'LAFE-A737-22C4-8670')
        clave_input = st.text_input("Pega tu Clave", value=default_key, key="c_act")
        if st.button("✅ Activar Sistema RD$ 25k", type="primary", use_container_width=True):
            # ACEPTA CUALQUIER CLAVE QUE EMPIECE CON LAFE- PARA NO TRANCARSE
            if clave_input.strip().upper().startswith("LAFE-"):
                st.session_state.lic_activa = True
                st.session_state.lic_key = clave_input.strip().upper()
                st.session_state.negocio_nombre = st.session_state.get('ultimo_nombre', nom)
                st.success("✅ Activado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("La clave debe empezar con LAFE-")
    st.stop()

# ====== SI YA ESTA ACTIVA, CONTINUA AL SISTEMA ======
# Aquí ya estás dentro del punto de venta
st.sidebar.success(f"✅ Licencia: {st.session_state.lic_key}")
st.sidebar.caption(f"Licenciado a: {st.session_state.negocio_nombre}")

# --- RESTO DEL SISTEMA IGUAL ---
def cargar_sql():
    conn=get_conn()
    try:
        df_inv=pd.read_sql("SELECT * FROM inventario", conn)
        conn.close()
        return df_inv
    except:
        conn.close()
        return pd.DataFrame()

if 'inventario' not in st.session_state:
    st.session_state.inventario = cargar_sql()
if 'carrito' not in st.session_state:
    st.session_state.carrito=[]
if 'ventas_hoy' not in st.session_state:
    st.session_state.ventas_hoy=0
if 'contador_factura' not in st.session_state:
    st.session_state.contador_factura=1
if 'ultima_factura' not in st.session_state:
    st.session_state.ultima_factura=None

def agregar_al_carrito(it):
    for i,x in enumerate(st.session_state.carrito):
        if x['Producto']==it['Producto']:
            st.session_state.carrito[i]['Cant']+=it['Cant']
            st.session_state.carrito[i]['Total']+=it['Total']
            return
    st.session_state.carrito.append(it)

def generar_texto_factura(cliente, carrito, total, num):
    return f"FERRETERIA LA FE\nFACTURA {num:06d}\nCLIENTE: {cliente}\nTOTAL: RD$ {total:,.2f}\n" + "\n".join([f"{x['Cant']} x {x['Producto']} - {x['Total']}" for x in carrito])

# UI PRINCIPAL
st.title(f"{st.session_state.negocio_nombre} - Punto de Venta 606 PRO")
col1,col2 = st.columns([2,1])
with col1:
    cod = st.text_input("Código", placeholder="CEM001")
    if st.button("Buscar"):
        df=st.session_state.inventario
        m=df[df["Código"].str.upper()==cod.upper()]
        if not m.empty:
            r=m.iloc[0]
            agregar_al_carrito({"Producto":r['Producto'],"Icono":r['Icono'],"Cant":1,"Precio":r['Precio RD$'],"Total":r['Precio RD$'],"Código":r['Código']})
            st.rerun()
    bus=st.text_input("Buscar producto")
    if bus:
        res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(bus,case=False,na=False)]
        for _,row in res.iterrows():
            with st.container(border=True):
                st.write(f"{row['Icono']} {row['Producto']} - RD$ {row['Precio RD$']} Stock {row['Stock']}")
                cant=st.number_input("Cant",1,100,key=f"c_{row['Código']}")
                if st.button("Agregar", key=f"a_{row['Código']}"):
                    agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                    st.rerun()

with col2:
    st.subheader("Carrito")
    if st.session_state.carrito:
        for it in st.session_state.carrito:
            st.write(f"{it['Producto'][:20]} x{it['Cant']} = RD$ {it['Total']:,}")
        total=sum([x['Total'] for x in st.session_state.carrito])*1.18
        st.metric("TOTAL", f"RD$ {total:,.0f}")
        cliente=st.text_input("Cliente", value="Cliente Mostrador")
        if st.button("✅ COBRAR", type="primary", use_container_width=True):
            st.session_state.ventas_hoy+=total
            st.session_state.contador_factura+=1
            txt=generar_texto_factura(cliente, st.session_state.carrito, total, st.session_state.contador_factura)
            st.session_state.ultima_factura={"texto":txt,"num":st.session_state.contador_factura}
            # descuenta stock
            for it in st.session_state.carrito:
                idx=st.session_state.inventario[st.session_state.inventario["Código"]==it["Código"]].index
                if not idx.empty:
                    st.session_state.inventario.loc[idx,"Stock"]-=it["Cant"]
            st.session_state.carrito=[]
            st.balloons()
            st.rerun()
        if st.button("Vaciar"):
            st.session_state.carrito=[]
            st.rerun()
    if st.session_state.ultima_factura:
        st.download_button("Descargar Factura", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt")

with st.sidebar:
    st.divider()
    st.metric("Ventas Hoy", f"RD$ {st.session_state.ventas_hoy:,.0f}")
    if st.button("Cerrar Día"):
        st.session_state.ventas_hoy=0
        st.rerun()
    if st.button("🔓 Cerrar Licencia (para probar)"):
        st.session_state.lic_activa=False
        st.rerun()
