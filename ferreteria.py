import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3
import os
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
    CREATE TABLE IF NOT EXISTS inventario (Código TEXT PRIMARY KEY, Producto TEXT NOT NULL, "Precio RD$" REAL NOT NULL, Stock INTEGER NOT NULL, Cat TEXT, Icono TEXT);
    CREATE TABLE IF NOT EXISTS fiados (Cliente TEXT, WhatsApp TEXT, WhatsApp_Display TEXT, Monto REAL, Fecha TEXT, Vence TEXT, "Que llevó" TEXT, Estado TEXT);
    CREATE TABLE IF NOT EXISTS ventas_config (clave TEXT PRIMARY KEY, valor TEXT);
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

# ========== LICENCIA 606 PRO - FIX DEFINITIVO SESION ==========
def generar_clave(nombre_negocio, telefono):
    base = f"606-{nombre_negocio.upper().strip()}-{telefono}-LAFE2026"
    hash_corto = hashlib.md5(base.encode()).hexdigest().upper()[:12]
    return f"LAFE-{hash_corto[:4]}-{hash_corto[4:8]}-{hash_corto[8:12]}"

if 'lic_activa' not in st.session_state:
    st.session_state.lic_activa = False
if 'lic_key' not in st.session_state:
    st.session_state.lic_key = ""
if 'negocio_nombre' not in st.session_state:
    st.session_state.negocio_nombre = "Ferretería La Fe"

if not st.session_state.lic_activa:
    st.markdown("# 🔒 Sistema 606 PRO - RD$ 25,000")
    st.markdown("### Ferretería La Fe - Activación")
    st.divider()
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("🛠️ Generador Admin (Solo tú)")
        nombre_input = st.text_input("Nombre ferretería cliente", value="ferreteria juan", key="nom_admin")
        tel_input = st.text_input("Teléfono cliente", value="8292647574", key="tel_admin")
        if st.button("🔑 Generar Clave"):
            clave_gen = generar_clave(nombre_input, tel_input)
            st.session_state['ultima_clave_gen'] = clave_gen
            st.session_state['ultimo_nombre_gen'] = nombre_input
            st.success("Clave generada:")
            st.code(clave_gen)
    with c2:
        st.subheader("🔓 Activar Sistema")
        valor_default = st.session_state.get('ultima_clave_gen', 'LAFE-A737-22C4-8670')
        clave_cliente = st.text_input("Pega tu Clave", value=valor_default, key="clave_act")
        if st.button("✅ Activar Sistema RD$ 25k", type="primary", use_container_width=True):
            if clave_cliente.strip().upper().startswith("LAFE-"):
                st.session_state.lic_activa = True
                st.session_state.lic_key = clave_cliente.strip().upper()
                st.session_state.negocio_nombre = st.session_state.get('ultimo_nombre_gen', nombre_input)
                st.success(f"✅ Activado para {st.session_state.negocio_nombre}!")
                st.balloons()
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("Clave debe empezar con LAFE-")
    st.info("Truco: Genera a la izquierda y dale directo a Activar a la derecha.")
    st.caption("Compra: Ferretería La Fe - 829-264-7574 - RD$25k")
    st.stop()

# ========== FUNCIONES PRINCIPALES ==========
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
    conn=get_conn()
    try:
        conn.execute("DELETE FROM inventario")
        df.to_sql("inventario", conn, if_exists="append", index=False)
        conn.commit()
    except: pass
    conn.close()
def save_fiados(lista):
    conn=get_conn()
    try:
        conn.execute("DELETE FROM fiados")
        if lista: pd.DataFrame(lista).to_sql("fiados", conn, if_exists="append", index=False)
        conn.commit()
    except: pass
    conn.close()
def save_ventas(monto):
    conn=get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('ventas_hoy', ?)", (str(monto),))
        conn.commit()
    except: pass
    conn.close()
def save_contador(num):
    conn=get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO ventas_config (clave, valor) VALUES ('contador_factura', ?)", (str(num),))
        conn.commit()
    except: pass
    conn.close()

if 'inventario' not in st.session_state:
    df_s, f_s, v_s, c_s = cargar_sql()
    if df_s is not None and not df_s.empty:
        st.session_state.inventario=df_s
        st.session_state.fiados=f_s if f_s else []
        st.session_state.ventas_hoy=v_s if v_s else 0
        st.session_state.contador_factura=c_s if c_s else 1
    else:
        st.session_state.inventario=pd.DataFrame([
            ["CEM001","Cemento Panam 94lbs",550,120,"Cemento","🏗️"],
            ["CEM002","Cemento Cemex",565,80,"Cemento","🏗️"],
            ["VAR001","Varilla 3/8 x 20",420,200,"Varilla","🔩"],
            ["VAR002","Varilla 1/2 x 20",680,150,"Varilla","🔩"],
            ["BLK04","Block 4''",35,1000,"Blocks","🧱"],
            ["BLK06","Block 6''",42,1500,"Blocks","🧱"],
            ["BLK08","Block 8''",48,800,"Blocks","🧱"],
            ["ZIN001","Zinc Acanalado 10ft",750,50,"Techo","🏠"],
            ["ALAM01","Alambre Dulce lb",85,100,"Alambres","🪢"],
            ["CLAV01","Clavo 2 1/2 lb",120,60,"Clavos","🔨"],
            ["PINT01","Pintura Tropical Galón",1850,30,"Pintura","🎨"],
            ["ARE001","Arena Lavada m3",2500,20,"Agregados","🏖️"],
            ["GRAV01","Grava m3",2800,15,"Agregados","🪨"],
        ], columns=["Código","Producto","Precio RD$","Stock","Cat","Icono"])
        st.session_state.fiados=[]
        st.session_state.ventas_hoy=0
        st.session_state.contador_factura=1

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'ultima_factura' not in st.session_state: st.session_state.ultima_factura=None
if 'calc_temp' not in st.session_state: st.session_state.calc_temp=None
if 'calc_detalle' not in st.session_state: st.session_state.calc_detalle=None

def agregar_al_carrito(nuevo_item):
    for i,item in enumerate(st.session_state.carrito):
        if item['Producto']==nuevo_item['Producto']:
            st.session_state.carrito[i]['Cant']+=nuevo_item['Cant']
            st.session_state.carrito[i]['Total']+=nuevo_item['Total']
            return
    st.session_state.carrito.append(nuevo_item)

def generar_texto_factura(cliente, carrito, subtotal, itbis, total, num):
    fecha=datetime.now().strftime("%d/%m/%Y %I:%M %p")
    lineas=[f"{'='*42}","      FERRETERIA LA FE - QUISQUEYA",f"{'='*42}",f"FACTURA No: {num:06d}",f"FECHA: {fecha}",f"CLIENTE: {cliente}",f"{'-'*42}"]
    for item in carrito:
        lineas.append(f"{item['Cant']} x {item['Producto'][:28]}")
        lineas.append(f"   RD$ {item['Total']:,}")
    lineas+=[f"{'-'*42}",f"SUBTOTAL: RD$ {subtotal:,.2f}",f"ITBIS 18%: RD$ {itbis:,.2f}",f"TOTAL: RD$ {total:,.2f}",f"{'='*42}","  Gracias por su compra!"]
    return "\n".join(lineas)

def imprimir_factura_html(texto, num):
    html=f"""<html><head><style>@page{{size:80mm auto;margin:2mm}}body{{font-family:'Courier New',monospace;width:72mm;font-size:12px;margin:0 auto}}pre{{white-space:pre-wrap}}.btn{{background:#FF6B00;color:white;border:none;padding:15px;width:100%;font-size:18px;border-radius:10px;cursor:pointer}}@media print{{.btn{{display:none}}}}</style></head><body><pre>{texto}</pre><button class="btn" onclick="window.print()">IMPRIMIR {num:06d}</button></body></html>"""
    components.html(html, height=700, scrolling=True)

def generar_link_whatsapp(numero, cliente, monto, que_llevo, fecha):
    num_limpio="".join(filter(str.isdigit,str(numero)))
    if len(num_limpio)==10: num_limpio="1"+num_limpio
    mensaje=f"Hola {cliente},\nTe saluda FERRETERIA LA FE Quisqueya.\n\nBalance pendiente:\nMonto: RD$ {monto:,}\nDetalle: {que_llevo}\nFecha: {fecha}\n\nPasa por la ferreteria.\nFerreteria La Fe - 829-264-7574"
    return f"https://wa.me/{num_limpio}?text={urllib.parse.quote(mensaje)}", num_limpio

def validar_numero_rd(numero):
    num="".join(filter(str.isdigit,str(numero)))
    if len(num)==11 and num.startswith("1"): num=num[1:]
    if len(num)!=10: return False,"Debe tener 10 dígitos",num
    if num[:3] not in ["809","829","849"]: return False,"Debe ser 809/829/849",num
    return True,"Válido",num

# SIDEBAR
with st.sidebar:
    st.title(st.session_state.negocio_nombre)
    st.success(f"🔒 {st.session_state.lic_key}")
    menu=st.radio("Ir a:", ["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
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
            st.download_button("📥 Backup DB", f, file_name=f"lafe_606_{date.today()}.db", use_container_width=True)
        try:
            conn=get_conn()
            df_inv=pd.read_sql("SELECT * FROM inventario", conn)
            df_f=pd.read_sql("SELECT * FROM fiados", conn)
            conn.close()
            st.download_button("📊 Inventario CSV", df_inv.to_csv(index=False).encode('utf-8'), file_name=f"Inventario_{date.today()}.csv", mime="text/csv", use_container_width=True)
            if not df_f.empty:
                st.download_button("📓 Fiados CSV", df_f.to_csv(index=False).encode('utf-8'), file_name=f"Fiados_{date.today()}.csv", mime="text/csv", type="primary", use_container_width=True)
        except: pass
    st.divider()
    if st.button("🔓 Cerrar Licencia (test)"):
        st.session_state.lic_activa=False
        st.rerun()

# ========== PUNTO DE VENTA ==========
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        cod=st.text_input("Pistolea código", placeholder="CEM001")
        if st.button("🔎 Buscar Código"):
            inv=st.session_state.inventario
            match=inv[inv["Código"].str.upper().str.strip()==cod.upper().strip()]
            if not match.empty:
                row=match.iloc[0]
                agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio RD$'],"Total":1*row['Precio RD$'],"Código":row['Código']})
                st.rerun()
        buscador=st.text_input("Busca producto")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            for _,row in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Producto']}** - RD$ {row['Precio RD$']} | Stock {row['Stock']}")
                    cant=st.number_input("Cant",1,1000,1,key=f"cant_{row['Código']}")
                    if st.button("Agregar", key=f"add_{row['Código']}"):
                        agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                        st.rerun()
    with c2:
        st.subheader("Factura")
        cliente_fact=st.text_input("Cliente", value="Cliente Mostrador")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                st.write(f"{item.get('Icono','')} {item['Producto'][:22]} - {item['Cant']} x RD$ {item['Total']:,}")
            subtotal=sum([x['Total'] for x in st.session_state.carrito])
            itbis=subtotal*0.18
            total=subtotal*1.18
            st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR Y FACTURA", type="primary", use_container_width=True):
                num=st.session_state.contador_factura
                texto=generar_texto_factura(cliente_fact, st.session_state.carrito, subtotal, itbis, total, num)
                st.session_state.ultima_factura={"texto":texto,"num":num}
                st.session_state.ventas_hoy+=total
                st.session_state.contador_factura+=1
                for item in st.session_state.carrito:
                    if item.get("Código"):
                        idx=st.session_state.inventario[st.session_state.inventario["Código"]==item["Código"]].index
                        if not idx.empty:
                            st.session_state.inventario.loc[idx,"Stock"]-=item["Cant"]
                save_inv(st.session_state.inventario)
                save_ventas(st.session_state.ventas_hoy)
                save_contador(st.session_state.contador_factura)
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
            if st.button("🗑️ Vaciar carrito"):
                st.session_state.carrito=[]
                st.rerun()
        if st.session_state.ultima_factura:
            st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", use_container_width=True)
            imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo")
    st.dataframe(st.session_state.inventario[["Código","Producto","Precio RD$","Stock","Cat"]], use_container_width=True)

elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora Inteligente")
    obra=st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Casita 3x3 Completa"])
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo (m)",1.0,100.0,10.0)
        alto=c2.number_input("Alto (m)",1.0,10.0,2.5)
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42","Block 4'' - RD$35","Block 8'' - RD$48"])
        precio_block=42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared", type="primary"):
            m2=largo*alto
            blocks=int(m2*12.5)+5
            cemento=int(m2*1.15)+1
            arena=round(m2*0.08,2)
            varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + int(arena*2500) + varilla*420
            df=pd.DataFrame([[f"🧱 {tipo}",blocks,f"RD$ {precio_block}",f"RD$ {blocks*precio_block:,}"],["🏗️ Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["🏖️ Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"],["🔩 Varilla 3/8",varilla,"RD$ 420",f"RD$ {varilla*420:,}"]], columns=["Material","Cant. Necesaria","Precio Unit.","Subtotal"])
            st.session_state.calc_temp={"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"Pared {m2} m2"}
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True):
            df=pd.DataFrame([["🧱 Block 6''",112,"RD$ 42","RD$ 4,704"],["🏗️ Cemento",15,"RD$ 550","RD$ 8,250"],["🔩 Varilla 3/8",20,"RD$ 420","RD$ 8,400"],["🏖️ Arena",2,"RD$ 2,500","RD$ 5,000"],["🪨 Grava",1.5,"RD$ 2,800","RD$ 4,200"],["🏠 Zinc 10ft",6,"RD$ 750","RD$ 4,500"]], columns=["Material","Cant. Necesaria","Precio Unit.","Subtotal"])
            st.session_state.calc_temp={"Producto":"Casita 3x3 Completa","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":""}
            st.session_state.calc_detalle={"df":df,"total":35839,"titulo":"Casita 3x3 Completa"}
    if st.session_state.calc_detalle:
        st.divider()
        st.subheader(f"📋 Materiales: {st.session_state.calc_detalle['titulo']}")
        st.dataframe(st.session_state.calc_detalle["df"], use_container_width=True, hide_index=True)
        st.markdown(f"### 💰 TOTAL: RD$ {st.session_state.calc_detalle['total']:,}")
        if st.button("➕ AGREGAR AL CARRITO", type="primary", use_container_width=True):
            agregar_al_carrito(st.session_state.calc_temp)
            st.rerun()

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado")
    col1,col2=st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente=st.text_input("Nombre *", placeholder="Juan Perez")
            telefono=st.text_input("WhatsApp *", placeholder="829-264-7574")
            monto=st.number_input("Monto RD$ *", min_value=100, value=5000, step=100)
            fecha=st.date_input("Fecha fiado", value=date.today())
            vence=st.date_input("Vence", value=date.today())
            nota=st.text_input("Qué se llevó", placeholder="10 Cemento")
            guardar=st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar:
                if cliente.strip()=="": st.error("Pon nombre")
                else:
                    ok,msg,num_l=validar_numero_rd(telefono)
                    if not ok: st.error(f"❌ {msg}")
                    else:
                        st.session_state.fiados.append({"Cliente":cliente.strip(),"WhatsApp":num_l,"WhatsApp_Display":f"{num_l[:3]}-{num_l[3:6]}-{num_l[6:]}","Monto":monto,"Fecha":str(fecha),"Vence":str(vence),"Que llevó":nota,"Estado":"Pendiente"})
                        save_fiados(st.session_state.fiados)
                        st.success("✅ Guardado")
                        st.balloons()
    with col2:
        st.subheader("📋 Fiados")
        if st.session_state.fiados:
            total_p=sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"])
            st.metric("💰 Por cobrar", f"RD$ {total_p:,.0f}")
            for i,row in enumerate(st.session_state.fiados):
                with st.container(border=True):
                    c_info,c_ws,c_acc=st.columns([2.5,1.5,1])
                    with c_info:
                        estado="🟡" if row.get("Estado")=="Pendiente" else "🟢"
                        st.markdown(f"{estado} **{row['Cliente']}** - RD$ {row['Monto']:,}")
                        st.caption(f"📱 {row.get('WhatsApp_Display',row.get('WhatsApp',''))} | Vence: {row.get('Vence','')}")
                    with c_ws:
                        link_ws,_=generar_link_whatsapp(row.get('WhatsApp',''), row['Cliente'], row['Monto'], row.get('Que llevó',''), row.get('Fecha',''))
                        st.link_button("💬 WhatsApp", link_ws, use_container_width=True, type="primary")
                    with c_acc:
                        if row.get("Estado")=="Pendiente":
                            if st.button("✅ Cobrado", key=f"cob_{i}", use_container_width=True):
                                st.session_state.fiados[i]["Estado"]="Pagado"
                                save_fiados(st.session_state.fiados)
                                st.rerun()
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            st.session_state.fiados.pop(i)
                            save_fiados(st.session_state.fiados)
                            st.rerun()

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja")
    ventas=st.session_state.ventas_hoy
    fiados_total=sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    c1,c2,c3,c4=st.columns(4)
    c1.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}")
    c2.metric("📓 Fiado", f"RD$ {fiados_total:,.0f}")
    c3.metric("📈 Total Día", f"RD$ {ventas+fiados_total:,.0f}")
    c4.metric("🧱 Productos", f"{len(st.session_state.inventario)} tipos")
    st.divider()
    izq,der=st.columns([1.1,1.4])
    with izq:
        st.subheader("💰 Cuadre")
        st.info(f"Sistema dice: RD$ {ventas:,.2f}")
        ef=st.number_input("Efectivo FÍSICO en caja", min_value=0.0, value=float(ventas), step=100.0)
        dif=ef-ventas
        if ventas>0:
            if dif==0: st.success("✅ CUADRE PERFECTO")
            elif dif>0: st.warning(f"⚠️ SOBRA RD$ {dif:,.2f}")
            else: st.error(f"❌ FALTA RD$ {abs(dif):,.2f}")
        if st.button("🔒 Cerrar Día", type="primary", use_container_width=True):
            st.session_state.ventas_hoy=0
            save_ventas(0)
            st.rerun()
    with der:
        st.subheader("📦 Inventario Editable")
        df_edit=st.data_editor(st.session_state.inventario[["Código","Producto","Stock","Precio RD$"]], use_container_width=True, num_rows="fixed")
        if st.button("💾 Guardar Stock en SQL", type="primary", use_container_width=True):
            for _,row in df_edit.iterrows():
                codigo=row["Código"]
                real_idx=st.session_state.inventario[st.session_state.inventario["Código"]==codigo].index
                if not real_idx.empty:
                    st.session_state.inventario.loc[real_idx,"Stock"]=row["Stock"]
                    st.session_state.inventario.loc[real_idx,"Precio RD$"]=row["Precio RD$"]
            save_inv(st.session_state.inventario)
            st.success("✅ Guardado!")
            st.rerun()
        valor_inv=(st.session_state.inventario["Stock"]*st.session_state.inventario["Precio RD$"]).sum()
        st.metric("💰 Valor Inventario", f"RD$ {valor_inv:,.0f}")
