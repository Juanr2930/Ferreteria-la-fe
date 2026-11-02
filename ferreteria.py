# COPIA TODO DESDE AQUÍ
import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3, os, hashlib, time

st.set_page_config(page_title="Ferretería La Fe - 606 PRO", layout="wide", page_icon="🧱")
DB_FILE = "lafe_606.db"
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn=get_conn();cur=conn.cursor()
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
            ["CEM001","Cemento Panam 94lbs",550,120,"Cemento","🏗️"],["VAR001","Varilla 3/8 x 20",420,200,"Varilla","🔩"],
            ["BLK06","Block 6''",42,1500,"Blocks","🧱"],["ZIN001","Zinc 10ft",750,50,"Techo","🏠"],
        ])
        conn.commit()
    conn.close()
init_db()

def generar_clave(nom,tel):
    base=f"606-{nom.upper().strip()}-{tel}-LAFE2026"
    h=hashlib.md5(base.encode()).hexdigest().upper()[:12]
    return f"LAFE-{h[:4]}-{h[4:8]}-{h[8:12]}"

if 'lic_activa' not in st.session_state: st.session_state.lic_activa=False
if 'lic_key' not in st.session_state: st.session_state.lic_key=""
if 'negocio_nombre' not in st.session_state: st.session_state.negocio_nombre="Ferretería La Fe"

if not st.session_state.lic_activa:
    st.markdown("# 🔒 Sistema 606 PRO - RD$ 25,000")
    c1,c2=st.columns(2)
    with c1:
        nom=st.text_input("Nombre ferretería", value="ferreteria juan")
        tel=st.text_input("Teléfono", value="8292647574")
        if st.button("🔑 Generar Clave"):
            st.session_state.ultima_clave=generar_clave(nom,tel)
            st.session_state.ultimo_nombre=nom
            st.code(st.session_state.ultima_clave)
    with c2:
        clave=st.text_input("Pega tu Clave", value=st.session_state.get('ultima_clave','LAFE-A737-22C4-8670'))
        if st.button("✅ Activar Sistema RD$ 25k", type="primary", use_container_width=True):
            if clave.strip().upper().startswith("LAFE-"):
                st.session_state.lic_activa=True;st.session_state.lic_key=clave.strip().upper()
                st.session_state.negocio_nombre=st.session_state.get('ultimo_nombre',nom)
                st.balloons();time.sleep(0.5);st.rerun()
    st.stop()

# --- SISTEMA COMPLETO ABAJO YA ACTIVADO ---
def cargar_sql():
    conn=get_conn()
    try:
        df_inv=pd.read_sql("SELECT * FROM inventario", conn)
        df_f=pd.read_sql("SELECT * FROM fiados", conn)
        fiados=df_f.to_dict('records') if not df_f.empty else []
        v=float(conn.execute("SELECT valor FROM ventas_config WHERE clave='ventas_hoy'").fetchone()[0])
        c=int(float(conn.execute("SELECT valor FROM ventas_config WHERE clave='contador_factura'").fetchone()[0]))
        conn.close();return df_inv,fiados,v,c
    except: conn.close();return None,None,None,None

def save_inv(df):
    conn=get_conn();conn.execute("DELETE FROM inventario");df.to_sql("inventario",conn,if_exists="append",index=False);conn.commit();conn.close()
def save_fiados(lista):
    conn=get_conn();conn.execute("DELETE FROM fiados")
    if lista: pd.DataFrame(lista).to_sql("fiados",conn,if_exists="append",index=False)
    conn.commit();conn.close()
def save_ventas(m): 
    conn=get_conn();conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('ventas_hoy', ?)",(str(m),));conn.commit();conn.close()
def save_contador(n):
    conn=get_conn();conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('contador_factura', ?)",(str(n),));conn.commit();conn.close()

if 'inventario' not in st.session_state:
    df_s,f_s,v_s,c_s=cargar_sql()
    if df_s is not None and not df_s.empty:
        st.session_state.inventario=df_s;st.session_state.fiados=f_s;st.session_state.ventas_hoy=v_s;st.session_state.contador_factura=c_s
    else:
        st.session_state.inventario=pd.DataFrame([["CEM001","Cemento",550,120,"Cemento","🏗️"]],columns=["Código","Producto","Precio RD$","Stock","Cat","Icono"])
        st.session_state.fiados=[];st.session_state.ventas_hoy=0;st.session_state.contador_factura=1

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'ultima_factura' not in st.session_state: st.session_state.ultima_factura=None
if 'calc_temp' not in st.session_state: st.session_state.calc_temp=None
if 'calc_detalle' not in st.session_state: st.session_state.calc_detalle=None

def agregar(it):
    for i,x in enumerate(st.session_state.carrito):
        if x['Producto']==it['Producto']: st.session_state.carrito[i]['Cant']+=it['Cant'];st.session_state.carrito[i]['Total']+=it['Total'];return
    st.session_state.carrito.append(it)

def generar_link_whatsapp(numero, cliente, monto, que_llevo, fecha):
    num="".join(filter(str.isdigit,str(numero))); 
    if len(num)==10: num="1"+num
    msg=f"Hola {cliente}, balance RD$ {monto:,} - {que_llevo} - Ferreteria La Fe"
    return f"https://wa.me/{num}?text={urllib.parse.quote(msg)}", num

def validar_rd(numero):
    num="".join(filter(str.isdigit,str(numero)))
    if len(num)==11 and num.startswith("1"): num=num[1:]
    if len(num)!=10: return False,"10 dígitos",num
    if num[:3] not in ["809","829","849"]: return False,"809/829/849",num
    return True,"OK",num

with st.sidebar:
    st.title(st.session_state.negocio_nombre);st.success(f"🔒 {st.session_state.lic_key}")
    menu=st.radio("Ir a:", ["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    if st.button("💾 Guardar SQL", type="primary", use_container_width=True):
        save_inv(st.session_state.inventario);save_fiados(st.session_state.fiados);save_ventas(st.session_state.ventas_hoy);save_contador(st.session_state.contador_factura);st.success("Guardado!")

if menu=="🛒 Punto de Venta":
    st.title("Punto de Venta"); bus=st.text_input("Busca")
    if bus:
        res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(bus,case=False,na=False)]
        for _,r in res.iterrows():
            with st.container(border=True):
                st.write(f"{r['Producto']} RD$ {r['Precio RD$']} Stock {r['Stock']}")
                cant=st.number_input("Cant",1,100,key=f"c_{r['Código']}")
                if st.button("Agregar", key=f"a_{r['Código']}"): agregar({"Producto":r['Producto'],"Cant":cant,"Total":cant*r['Precio RD$'],"Código":r['Código']});st.rerun()
    st.subheader("Carrito")
    if st.session_state.carrito:
        for it in st.session_state.carrito: st.write(f"{it['Producto']} x{it['Cant']} = {it['Total']}")
        tot=sum([x['Total'] for x in st.session_state.carrito])*1.18
        st.metric("TOTAL", f"RD$ {tot:,.0f}")
        if st.button("✅ COBRAR", type="primary", use_container_width=True):
            st.session_state.ventas_hoy+=tot;st.session_state.contador_factura+=1;st.session_state.carrito=[];save_ventas(st.session_state.ventas_hoy);st.balloons();st.rerun()

elif menu=="📓 Fiado":
    st.title("Fiado con WhatsApp"); cliente=st.text_input("Cliente"); tel=st.text_input("WhatsApp"); monto=st.number_input("Monto", value=5000)
    if st.button("Guardar Fiado"):
        ok,msg,num=validar_rd(tel)
        if ok: st.session_state.fiados.append({"Cliente":cliente,"WhatsApp":num,"Monto":monto,"Fecha":str(date.today()),"Vence":str(date.today()),"Que llevó":"","Estado":"Pendiente"});save_fiados(st.session_state.fiados);st.success("Guardado")
    for i,row in enumerate(st.session_state.get('fiados',[])):
        with st.container(border=True):
            st.write(f"{row.get('Cliente')} - RD$ {float(row.get('Monto',0)):,} - {row.get('Estado')}")
            link,_=generar_link_whatsapp(row.get('WhatsApp',''), row.get('Cliente',''), row.get('Monto',0), row.get('Que llevó',''), row.get('Fecha',''))
            st.link_button("💬 WhatsApp", link)
            if st.button("Cobrado", key=f"cob_{i}"): st.session_state.fiados[i]["Estado"]="Pagado";save_fiados(st.session_state.fiados);st.rerun()

elif menu=="📊 Cierre":
    ventas=st.session_state.get('ventas_hoy',0)
    fiados_list=st.session_state.get('fiados',[])
    try: fiados_total=sum([float(f.get("Monto",0)) for f in fiados_list if str(f.get("Estado","")).lower()=="pendiente"])
    except: fiados_total=0
    st.metric("Ventas Hoy", f"RD$ {ventas:,.0f}"); st.metric("Fiado por cobrar", f"RD$ {fiados_total:,.0f}")
    if st.button("Cerrar Día"): st.session_state.ventas_hoy=0;save_ventas(0);st.rerun()

elif menu=="🧮 Calculadora Materiales":
    st.title("Calculadora"); largo=st.number_input("Largo",10.0); alto=st.number_input("Alto",2.5)
    if st.button("Calcular Pared"):
        m2=largo*alto; blocks=int(m2*12.5); total=blocks*42
        st.session_state.calc_temp={"Producto":f"Pared {m2}m2","Cant":1,"Total":total,"Código":""}
        st.metric("TOTAL", f"RD$ {total:,}")
        if st.button("Agregar al carrito"): agregar(st.session_state.calc_temp);st.rerun()
else:
    st.dataframe(st.session_state.inventario)
