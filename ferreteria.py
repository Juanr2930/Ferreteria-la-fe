import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3, hashlib, time, json
from io import BytesIO

st.set_page_config(page_title="Ferreteria La Fe 606 PRO DEFINITIVO", layout="wide", page_icon="🧱")
DB_FILE = "lafe_606.db"
CLAVE_JEFE = "6060"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inventario (Codigo TEXT PRIMARY KEY, Producto TEXT, Precio REAL, Stock INTEGER, Cat TEXT, Icono TEXT);
    CREATE TABLE IF NOT EXISTS fiados (Cliente TEXT, WhatsApp TEXT, WhatsApp_Display TEXT, Monto REAL, Fecha TEXT, Vence TEXT, QueLlevo TEXT, Estado TEXT);
    CREATE TABLE IF NOT EXISTS ventas_config (clave TEXT PRIMARY KEY, valor TEXT);
    CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT, RNC TEXT, Telefono TEXT, WhatsApp TEXT, Direccion TEXT, FechaRegistro TEXT);
    CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY AUTOINCREMENT, Numero INTEGER, NCF TEXT, Cliente TEXT, RNC TEXT, Telefono TEXT, Fecha TEXT, Items TEXT, Subtotal REAL, Itbis REAL, Total REAL, Estado TEXT, TipoComprobante TEXT);
    INSERT OR IGNORE INTO ventas_config VALUES ('ventas_hoy','0');
    INSERT OR IGNORE INTO ventas_config VALUES ('contador_factura','1');
    INSERT OR IGNORE INTO ventas_config VALUES ('contador_ncf','1');
    """)
    conn.commit()
    # Solo cargar productos iniciales si esta vacio, para que no se borre tu inventario cada vez que abres
    count = cur.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]
    if count == 0:
        productos = [
            ("CEM001","Cemento Panam 94lbs",550,120,"Cemento","🏗️"),
            ("CEM002","Cemento Cemex",565,80,"Cemento","🏗️"),
            ("VAR001","Varilla 3/8 x 20",420,200,"Varilla","🔩"),
            ("VAR002","Varilla 1/2 x 20",680,150,"Varilla","🔩"),
            ("BLK04","Block 4''",35,1000,"Blocks","🧱"),
            ("BLK06","Block 6''",42,1500,"Blocks","🧱"),
            ("BLK08","Block 8''",48,800,"Blocks","🧱"),
            ("ZIN001","Zinc Acanalado 10ft",750,50,"Techo","🏠"),
            ("ALAM01","Alambre Dulce lb",85,100,"Alambres","🪢"),
            ("CLAV01","Clavo 2 1/2 lb",120,60,"Clavos","🔨"),
            ("PINT01","Pintura Tropical Galon",1850,30,"Pintura","🎨"),
            ("ARE001","Arena Lavada m3",2500,20,"Agregados","🏖️"),
            ("GRAV01","Grava m3",2800,15,"Agregados","🪨"),
        ]
        cur.executemany("INSERT INTO inventario VALUES (?,?,?,?,?,?)", productos)
    conn.commit()
    conn.close()

init_db()

def generar_clave(n,t):
    b=f"606-{n.upper().strip()}-{t}-LAFE2026"
    h=hashlib.md5(b.encode()).hexdigest().upper()[:12]
    return f"LAFE-{h[:4]}-{h[4:8]}-{h[8:12]}"

def generar_ncf():
    conn = get_conn()
    n = int(float(conn.execute("SELECT valor FROM ventas_config WHERE clave='contador_ncf'").fetchone()[0]))
    conn.execute("INSERT OR REPLACE INTO ventas_config VALUES ('contador_ncf',?)", (str(n+1),))
    conn.commit()
    conn.close()
    return f"B02{str(n).zfill(8)}", n

if 'lic_activa' not in st.session_state:
    st.session_state.lic_activa=False
    st.session_state.lic_key=""
    st.session_state.negocio_nombre="Ferreteria La Fe"

if not st.session_state.lic_activa:
    st.markdown("# 🔒 Sistema 606 PRO - RD$ 25,000")
    c1,c2=st.columns(2)
    with c1:
        nom=st.text_input("Nombre ferreteria",value="ferreteria juan")
        tel=st.text_input("Telefono",value="8292647574")
        if st.button("Generar Clave"):
            st.session_state.ultima_clave=generar_clave(nom,tel)
            st.session_state.ultimo_nombre=nom
            st.code(st.session_state.ultima_clave)
    with c2:
        clave=st.text_input("Pega Clave",value=st.session_state.get('ultima_clave','LAFE-A737-22C4-8670'))
        if st.button("Activar Sistema",type="primary",use_container_width=True):
            if clave.upper().startswith("LAFE-"):
                st.session_state.lic_activa=True
                st.session_state.lic_key=clave.upper()
                st.session_state.negocio_nombre=st.session_state.get('ultimo_nombre',nom)
                st.balloons()
                time.sleep(0.5)
                st.rerun()
    st.stop()

def cargar_sql():
    conn=get_conn()
    try:
        df_inv=pd.read_sql("SELECT * FROM inventario",conn)
        df_f=pd.read_sql("SELECT * FROM fiados",conn)
        fiados=df_f.to_dict('records') if not df_f.empty else []
        v=float(conn.execute("SELECT valor FROM ventas_config WHERE clave='ventas_hoy'").fetchone()[0])
        c=int(float(conn.execute("SELECT valor FROM ventas_config WHERE clave='contador_factura'").fetchone()[0]))
        conn.close()
        return df_inv,fiados,v,c
    except:
        conn.close()
        return None,None,None,None

def save_inv(df):
    conn=get_conn()
    conn.execute("DELETE FROM inventario")
    df.to_sql("inventario",conn,if_exists="append",index=False)
    conn.commit()
    conn.close()

def save_fiados(lista):
    conn=get_conn()
    conn.execute("DELETE FROM fiados")
    if lista:
        df_temp = pd.DataFrame(lista)
        df_temp.to_sql("fiados",conn,if_exists="append",index=False)
    conn.commit()
    conn.close()

def save_ventas(m):
    conn=get_conn()
    conn.execute("INSERT OR REPLACE INTO ventas_config VALUES ('ventas_hoy',?)",(str(m),))
    conn.commit()
    conn.close()

def save_contador(n):
    conn=get_conn()
    conn.execute("INSERT OR REPLACE INTO ventas_config VALUES ('contador_factura',?)",(str(n),))
    conn.commit()
    conn.close()

def cargar_clientes():
    conn=get_conn()
    df=pd.read_sql("SELECT * FROM clientes",conn)
    conn.close()
    return df

def cargar_facturas():
    conn=get_conn()
    df=pd.read_sql("SELECT * FROM facturas ORDER BY id DESC",conn)
    conn.close()
    return df

if 'inventario' not in st.session_state:
    df_s,f_s,v_s,c_s=cargar_sql()
    st.session_state.inventario=df_s
    st.session_state.fiados=f_s
    st.session_state.ventas_hoy=v_s
    st.session_state.contador_factura=c_s
if 'carrito' not in st.session_state:
    st.session_state.carrito=[]
if 'ultima_factura' not in st.session_state:
    st.session_state.ultima_factura=None
if 'calc_temp' not in st.session_state:
    st.session_state.calc_temp=None
if 'calc_detalle' not in st.session_state:
    st.session_state.calc_detalle=None
if 'cliente_seleccionado' not in st.session_state:
    st.session_state.cliente_seleccionado="Cliente Mostrador"
if 'rnc_seleccionado' not in st.session_state:
    st.session_state.rnc_seleccionado=""

def agregar(it):
    for i,x in enumerate(st.session_state.carrito):
        if x['Producto']==it['Producto']:
            st.session_state.carrito[i]['Cant']+=it['Cant']
            st.session_state.carrito[i]['Total']+=it['Total']
            return
    st.session_state.carrito.append(it)

def generar_texto_factura(cliente, rnc, ncf, carrito, sub, itbis, total, num, tipo_comp="B02 - Consumo"):
    f=datetime.now().strftime("%d/%m/%Y %I:%M %p")
    l=[f"{'='*42}","      FERRETERIA LA FE - QUISQUEYA",f"{'='*42}",f"FACTURA No: {num:06d}",f"NCF: {ncf}",f"COMPROBANTE: {tipo_comp}",f"FECHA: {f}",f"CLIENTE: {cliente}",f"RNC: {rnc if rnc else 'N/A'}",f"{'-'*42}"]
    for it in carrito:
        l.append(f"{it['Cant']} x {it['Producto'][:28]}")
        l.append(f"   RD$ {it['Total']:,}")
    l+=[f"{'-'*42}",f"SUBTOTAL: RD$ {sub:,.2f}",f"ITBIS 18%: RD$ {itbis:,.2f}",f"TOTAL: RD$ {total:,.2f}",f"{'='*42}","  Gracias por su compra!"]
    return "\n".join(l)

def imprimir_factura_html(texto,num):
    html=f"<html><head><style>@page{{size:80mm auto;margin:2mm}}body{{font-family:Courier;width:72mm;font-size:12px;margin:0 auto}}pre{{white-space:pre-wrap}}.btn{{background:#FF6B00;color:white;border:none;padding:15px;width:100%;font-size:18px;border-radius:10px}}</style></head><body><pre>{texto}</pre><button class='btn' onclick='window.print()'>IMPRIMIR {num:06d}</button></body></html>"
    components.html(html,height=700,scrolling=True)

def generar_link_whatsapp(numero, cliente, monto, llevo, fecha, vence):
    num = "".join(filter(str.isdigit,str(numero)))
    if len(num)==10:
        num="1"+num
    msg = f"Hola {cliente}, te queda un balance de RD$ {monto:,} por {llevo} del {fecha}. VENCE el {vence}. Por favor pasa por Ferreteria La Fe - Quisqueya. Gracias!"
    return f"https://wa.me/{num}?text={urllib.parse.quote(msg)}",num

def validar_rd(numero):
    num="".join(filter(str.isdigit,str(numero)))
    if len(num)==11 and num.startswith("1"):
        num=num[1:]
    if len(num)!=10:
        return False,"10 digitos",num
    if num[:3] not in ["809","829","849"]:
        return False,"809/829/849",num
    return True,"OK",num

def html_codigos_barra(df):
    items=""
    for _,r in df.iterrows():
        items+=f'<div class="etiqueta"><div class="top"><span class="ico">{r["Icono"]}</span><div><div class="prod">{r["Producto"]}</div><div class="cod">{r["Codigo"]}</div></div></div><svg class="barcode" jsbarcode-format="CODE128" jsbarcode-value="{r["Codigo"]}" jsbarcode-textmargin="0" jsbarcode-height="40"></svg></div>'
    items+='<div class="etiqueta libre">- Espacio libre -</div><div class="etiqueta libre">- Espacio libre -</div>'
    return f'<html><head><script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script><style>@page{{size:A4;margin:10mm}}body{{font-family:Arial}}h2{{text-align:center}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.etiqueta{{border:1px dashed #bbb;border-radius:10px;padding:10px;text-align:center;height:110px}}.top{{display:flex;gap:6px;align-items:center;justify-content:center;font-size:11px;text-align:left}}.prod{{font-size:10px;font-weight:bold}}.cod{{font-weight:900;font-size:12px}}.ico{{font-size:18px}}.libre{{color:#999;display:flex;align-items:center;justify-content:center}}.btn{{background:black;color:white;padding:14px;width:100%;border:none;border-radius:10px;font-size:16px;margin:10px 0;cursor:pointer}}@media print{{.btn{{display:none}}}}</style></head><body><h2>Codigos de Barra - Sistema 606</h2><button class="btn" onclick="window.print()">IMPRIMIR A4 ADHESIVO</button><div class="grid">{items}</div><script>JsBarcode(".barcode").init();</script></body></html>'

with st.sidebar:
    st.title(st.session_state.negocio_nombre)
    st.success(f"🔒 {st.session_state.lic_key}")
    menu=st.radio("Ir a:", ["🛒 Punto de Venta","👥 Clientes","🧾 Facturas","📦 Catalogo","🏷️ Codigos de Barra","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre","🔐 Inventario Jefe","🔍 Ver Base de Datos SQL"])
    st.divider()
    if st.button("💾 Guardar en SQL",type="primary",use_container_width=True):
        save_inv(st.session_state.inventario)
        save_fiados(st.session_state.fiados)
        save_ventas(st.session_state.ventas_hoy)
        save_contador(st.session_state.contador_factura)
        st.success("Guardado!")

# ================= PUNTO DE VENTA CON CARRITO EDITABLE =================
if menu=="🛒 Punto de Venta":
    st.title("🛒 Punto de Venta")
    # Selector de cliente intuitivo
    df_cli = cargar_clientes()
    st.subheader("1️⃣ Elige Cliente para esta venta")
    c_cli1, c_cli2, c_cli3 = st.columns([2,1,1])
    with c_cli1:
        opciones = ["Cliente Mostrador"] + df_cli["Nombre"].tolist() if not df_cli.empty else ["Cliente Mostrador"]
        cliente_sel = st.selectbox("Cliente", opciones, index=0)
        st.session_state.cliente_seleccionado = cliente_sel
        if cliente_sel != "Cliente Mostrador" and not df_cli.empty:
            fila = df_cli[df_cli["Nombre"]==cliente_sel].iloc[0]
            st.session_state.rnc_seleccionado = fila["RNC"]
            st.caption(f"RNC: {fila['RNC']} | Tel: {fila['Telefono']} | {fila['Direccion']}")
        else:
            st.session_state.rnc_seleccionado = ""
    with c_cli2:
        rnc_manual = st.text_input("RNC / Cedula", value=st.session_state.rnc_seleccionado, placeholder="130-00000-1")
        st.session_state.rnc_seleccionado = rnc_manual
    with c_cli3:
        st.caption("Si no existe, ve a 👥 Clientes y crealo")
        if st.button("➕ Nuevo Cliente Rapido"):
            st.switch_page("app.py")

    st.divider()
    c1,c2=st.columns([2,1])
    with c1:
        st.subheader("2️⃣ Busca y Agrega Productos")
        cod=st.text_input("Pistolea codigo",placeholder="CEM001, CEM002, VAR001, etc - Sin lector, solo escribe el codigo")
        if st.button("Buscar Codigo"):
            inv=st.session_state.inventario
            match=inv[inv["Codigo"].str.upper().str.strip()==cod.upper().strip()]
            if not match.empty:
                row=match.iloc[0]
                agregar({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio'],"Total":row['Precio'],"Codigo":row['Codigo']})
                st.rerun()
        buscador=st.text_input("🔍 Busca producto",placeholder="cemex, clavo, varilla, block, alambre, pintura, arena, grava")
        df_inv = st.session_state.inventario.copy()
        if buscador and buscador.strip() != "":
            texto = buscador.strip().lower()
            mask = df_inv["Producto"].str.lower().str.contains(texto, na=False) | df_inv["Codigo"].str.lower().str.contains(texto, na=False)
            res = df_inv[mask]
        else:
            res = df_inv
        if res.empty:
            st.warning("No encontrado")
        else:
            for _,row in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"{row['Icono']} **{row['Producto']}** - RD$ {row['Precio']} | Stock {row['Stock']} | **{row['Codigo']}**")
                    cant=st.number_input("Cant",1,1000,1,key=f"cant_{row['Codigo']}")
                    if st.button("Agregar",key=f"add_{row['Codigo']}"):
                        agregar({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio'],"Total":cant*row['Precio'],"Codigo":row['Codigo']})
                        st.rerun()
    with c2:
        st.subheader("3️⃣ Carrito - Puedes Editar Aqui")
        st.caption("Cambia cantidad o quita algo antes de facturar. Nada se factura solo.")
        if st.session_state.carrito:
            # Carrito editable
            for idx, it in enumerate(list(st.session_state.carrito)):
                with st.container(border=True):
                    st.write(f"{it.get('Icono','')} **{it['Producto'][:28]}**")
                    cc1, cc2, cc3 = st.columns([2,1,1])
                    with cc1:
                        nueva_cant = st.number_input("Cant", min_value=1, max_value=1000, value=int(it['Cant']), key=f"edit_cant_{idx}")
                        if nueva_cant != it['Cant']:
                            st.session_state.carrito[idx]['Cant'] = nueva_cant
                            st.session_state.carrito[idx]['Total'] = nueva_cant * it['Precio']
                            st.rerun()
                    with cc2:
                        st.write(f"RD$ {it['Total']:,}")
                    with cc3:
                        if st.button("❌", key=f"del_cart_{idx}"):
                            st.session_state.carrito.pop(idx)
                            st.rerun()
            sub=sum([x['Total'] for x in st.session_state.carrito])
            itbis=sub*0.18
            total=sub*1.18
            st.metric("TOTAL + ITBIS",f"RD$ {total:,.2f}")
            st.info(f"Cliente: {st.session_state.cliente_seleccionado} | RNC: {st.session_state.rnc_seleccionado or 'N/A'}")
            tipo_comp = st.selectbox("Tipo Comprobante DGII", ["B02 - Consumo (sin RNC)", "B01 - Credito Fiscal (con RNC)", "B04 - Regimen Especial"])
            if st.button("📝 ENVIAR A FACTURACION (No cobra aun)",type="primary",use_container_width=True):
                num=st.session_state.contador_factura
                # Guardar como BORRADOR, no cobra, no descuenta stock todavia
                conn=get_conn()
                conn.execute("INSERT INTO facturas (Numero, NCF, Cliente, RNC, Telefono, Fecha, Items, Subtotal, Itbis, Total, Estado, TipoComprobante) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (num, "", st.session_state.cliente_seleccionado, st.session_state.rnc_seleccionado, "", datetime.now().strftime("%d/%m/%Y %I:%M %p"), json.dumps(st.session_state.carrito), sub, itbis, total, "Pendiente - Por Revisar", tipo_comp))
                conn.commit()
                conn.close()
                st.session_state.contador_factura+=1
                save_contador(st.session_state.contador_factura)
                st.session_state.carrito=[]
                st.success(f"✅ Factura #{num:06d} enviada a Facturacion. La persona que imprime la puede editar.")
                st.balloons()
                st.rerun()
            if st.button("Vaciar carrito"):
                st.session_state.carrito=[]
                st.rerun()
        else:
            st.info("Carrito vacio. Agrega productos a la izquierda.")
        if st.session_state.ultima_factura:
            st.download_button("Descargar TXT",st.session_state.ultima_factura["texto"],file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt",use_container_width=True)
            imprimir_factura_html(st.session_state.ultima_factura["texto"],st.session_state.ultima_factura["num"])

elif menu=="👥 Clientes":
    st.title("👥 Clientes - Base de Datos de Clientes")
    st.caption("Aqui guardas nombre, RNC, telefono, fecha. Luego en Punto de Venta lo eliges en 1 click.")
    col1,col2=st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Cliente")
        with st.form("nuevo_cliente",clear_on_submit=True):
            nom_c=st.text_input("Nombre Completo *", placeholder="Juan Perez")
            rnc_c=st.text_input("RNC / Cedula *", placeholder="001-1234567-8 o 130-00000-1")
            tel_c=st.text_input("Telefono", placeholder="829-264-7574")
            wa_c=st.text_input("WhatsApp", placeholder="8292647574")
            dir_c=st.text_input("Direccion", placeholder="Quisqueya, San Pedro")
            fecha_c=st.date_input("Fecha Registro", value=date.today())
            guardar_c=st.form_submit_button("Guardar Cliente",type="primary",use_container_width=True)
            if guardar_c:
                if nom_c.strip()=="":
                    st.error("Pon nombre")
                else:
                    conn=get_conn()
                    conn.execute("INSERT INTO clientes (Nombre,RNC,Telefono,WhatsApp,Direccion,FechaRegistro) VALUES (?,?,?,?,?,?)",(nom_c.strip(), rnc_c, tel_c, wa_c, dir_c, str(fecha_c)))
                    conn.commit()
                    conn.close()
                    st.success(f"Cliente {nom_c} guardado")
                    st.rerun()
    with col2:
        st.subheader("📋 Lista de Clientes")
        df_cli = cargar_clientes()
        buscar_cli = st.text_input("🔎 Buscar cliente por nombre o RNC", placeholder="Juan, 001-...")
        if buscar_cli and not df_cli.empty:
            df_cli = df_cli[df_cli["Nombre"].str.contains(buscar_cli, case=False, na=False) | df_cli["RNC"].str.contains(buscar_cli, case=False, na=False)]
        if df_cli.empty:
            st.info("No hay clientes aun. Crea el primero a la izquierda.")
        else:
            st.write(f"**{len(df_cli)} clientes registrados**")
            st.dataframe(df_cli, use_container_width=True, hide_index=True)
            # Borrar cliente
            for _, r in df_cli.iterrows():
                with st.container(border=True):
                    st.write(f"**{r['Nombre']}** - RNC: {r['RNC']} | 📱 {r['Telefono']} | 📅 {r['FechaRegistro']}")
                    if st.button(f"🗑️ Borrar {r['Nombre']}", key=f"del_cli_{r['id']}"):
                        conn=get_conn()
                        conn.execute("DELETE FROM clientes WHERE id=?", (int(r['id']),))
                        conn.commit()
                        conn.close()
                        st.rerun()

elif menu=="🧾 Facturas":
    st.title("🧾 Facturas - Revisar, Editar y Imprimir")
    st.caption("Aqui llega todo lo que se vende en Punto de Venta. La persona que imprime puede corregir antes de imprimir. Nada es automatico.")
    df_fact = cargar_facturas()
    if df_fact.empty:
        st.info("No hay facturas aun. Vende algo en Punto de Venta y aqui aparecera como Pendiente.")
    else:
        # Filtros
        filtro = st.selectbox("Ver:", ["Todas","Pendiente - Por Revisar","Impresa / Cobrada"])
        if filtro != "Todas":
            df_fact = df_fact[df_fact["Estado"]==filtro]
        for _, fac in df_fact.iterrows():
            items = json.loads(fac["Items"]) if fac["Items"] else []
            estado_color = "🟡" if "Pendiente" in fac["Estado"] else "🟢"
            with st.container(border=True):
                st.markdown(f"{estado_color} **Factura #{int(fac['Numero']):06d}** - {fac['Cliente']} | RNC: {fac['RNC']} | {fac['Fecha']} | **Total: RD$ {fac['Total']:,.2f}** | {fac['Estado']} | NCF: {fac['NCF'] or 'Sin asignar'}")
                st.caption(f"Comprobante: {fac['TipoComprobante']}")
                # Mostrar items actuales
                for it in items:
                    st.write(f"- {it['Cant']} x {it['Producto']} = RD$ {it['Total']:,}")
                # Si esta pendiente, permitir editar
                if "Pendiente" in fac["Estado"]:
                    st.divider()
                    st.subheader("✏️ Editar esta factura antes de imprimir")
                    # Editar items: permitir quitar o cambiar cantidad
                    items_editados = []
                    cambios = False
                    for idx2, it in enumerate(items):
                        c_e1, c_e2, c_e3 = st.columns([3,1,1])
                        with c_e1:
                            st.write(f"{it['Producto']}")
                        with c_e2:
                            nueva = st.number_input(f"Cant #{fac['id']}-{idx2}", min_value=0, value=int(it['Cant']), key=f"fac_edit_{fac['id']}_{idx2}")
                            if nueva != it['Cant']:
                                cambios = True
                            if nueva > 0:
                                it_copy = it.copy()
                                it_copy['Cant'] = nueva
                                it_copy['Total'] = nueva * it['Precio']
                                items_editados.append(it_copy)
                            # Si es 0, se elimina
                        with c_e3:
                            st.write(f"RD$ {it['Total']:,}")
                    # Agregar producto extra a la factura
                    st.write("**Agregar producto extra que el cliente pidio de mas:**")
                    df_inv2 = st.session_state.inventario
                    prod_extra = st.selectbox(f"Producto extra #{fac['id']}", ["Ninguno"] + df_inv2["Producto"].tolist(), key=f"extra_prod_{fac['id']}")
                    cant_extra = st.number_input(f"Cant extra #{fac['id']}", min_value=1, value=1, key=f"extra_cant_{fac['id']}")
                    col_g, col_i = st.columns(2)
                    with col_g:
                        if st.button(f"💾 Guardar Cambios en Factura #{int(fac['Numero']):06d}", key=f"save_fac_{fac['id']}", use_container_width=True):
                            if prod_extra != "Ninguno":
                                row_extra = df_inv2[df_inv2["Producto"]==prod_extra].iloc[0]
                                items_editados.append({"Producto":prod_extra,"Icono":row_extra["Icono"],"Cant":cant_extra,"Precio":row_extra["Precio"],"Total":cant_extra*row_extra["Precio"],"Codigo":row_extra["Codigo"]})
                            new_sub = sum([x['Total'] for x in items_editados])
                            new_itbis = new_sub*0.18
                            new_total = new_sub*1.18
                            conn=get_conn()
                            conn.execute("UPDATE facturas SET Items=?, Subtotal=?, Itbis=?, Total=? WHERE id=?", (json.dumps(items_editados), new_sub, new_itbis, new_total, int(fac['id'])))
                            conn.commit()
                            conn.close()
                            st.success("Cambios guardados")
                            st.rerun()
                    with col_i:
                        if st.button(f"✅ Aprobar, Generar NCF e Imprimir #{int(fac['Numero']):06d}", key=f"print_fac_{fac['id']}", type="primary", use_container_width=True):
                            # Si hubo cambios, guardarlos primero
                            if prod_extra != "Ninguno":
                                row_extra = df_inv2[df_inv2["Producto"]==prod_extra].iloc[0]
                                items_editados.append({"Producto":prod_extra,"Icono":row_extra["Icono"],"Cant":cant_extra,"Precio":row_extra["Precio"],"Total":cant_extra*row_extra["Precio"],"Codigo":row_extra["Codigo"]})
                            new_sub = sum([x['Total'] for x in items_editados])
                            new_itbis = new_sub*0.18
                            new_total = new_sub*1.18
                            ncf_nuevo, _ = generar_ncf()
                            texto = generar_texto_factura(fac['Cliente'], fac['RNC'], ncf_nuevo, items_editados, new_sub, new_itbis, new_total, int(fac['Numero']), fac['TipoComprobante'])
                            st.session_state.ultima_factura = {"texto": texto, "num": int(fac['Numero'])}
                            # Descontar stock y sumar ventas solo AHORA que se aprueba
                            for it in items_editados:
                                if it.get("Codigo"):
                                    idx = st.session_state.inventario[st.session_state.inventario["Codigo"]==it["Codigo"]].index
                                    if not idx.empty:
                                        st.session_state.inventario.loc[idx,"Stock"] -= it['Cant']
                            save_inv(st.session_state.inventario)
                            st.session_state.ventas_hoy += new_total
                            save_ventas(st.session_state.ventas_hoy)
                            conn=get_conn()
                            conn.execute("UPDATE facturas SET Items=?, Subtotal=?, Itbis=?, Total=?, Estado=?, NCF=? WHERE id=?", (json.dumps(items_editados), new_sub, new_itbis, new_total, "Impresa / Cobrada", ncf_nuevo, int(fac['id'])))
                            conn.commit()
                            conn.close()
                            st.success(f"Factura aprobada con NCF {ncf_nuevo}")
                            st.rerun()
                    if st.button(f"🗑️ Anular Factura #{int(fac['Numero']):06d}", key=f"anular_{fac['id']}"):
                        conn=get_conn()
                        conn.execute("DELETE FROM facturas WHERE id=?", (int(fac['id']),))
                        conn.commit()
                        conn.close()
                        st.rerun()
                else:
                    # Si ya esta impresa, mostrar boton de re-imprimir
                    texto_re = generar_texto_factura(fac['Cliente'], fac['RNC'], fac['NCF'], items, fac['Subtotal'], fac['Itbis'], fac['Total'], int(fac['Numero']), fac['TipoComprobante'])
                    st.download_button(f"⬇️ Descargar TXT Factura #{int(fac['Numero']):06d}", texto_re, file_name=f"FACTURA_{int(fac['Numero']):06d}.txt", key=f"dl_{fac['id']}")
                    imprimir_factura_html(texto_re, int(fac['Numero']))

elif menu=="📦 Catalogo":
    st.title("📦 Catalogo - Solo para ver")
    st.caption("Este catalogo es solo lectura. Para cambiar precios o stock, ve a Inventario Jefe con tu clave.")
    st.dataframe(st.session_state.inventario[["Codigo","Producto","Precio","Stock","Cat","Icono"]],use_container_width=True,hide_index=True)

elif menu=="🏷️ Codigos de Barra":
    st.title("🏷️ Codigos de Barra")
    html=html_codigos_barra(st.session_state.inventario)
    components.html(html,height=900,scrolling=True)

elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora - 8 Opciones")
    obra=st.selectbox("Que va a construir?", ["Pared de Blocks", "Casita 3x3 Completa", "Zapata Aislada", "Columna 3m", "Viga 4m", "Piso / Losa 10m2", "Techo Zinc 20m2", "Empanete 20m2"])
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo (m)",1.0,100.0,10.0)
        alto=c2.number_input("Alto (m)",1.0,10.0,2.5)
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42","Block 4'' - RD$35","Block 8'' - RD$48"])
        precio_block=42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared",type="primary"):
            m2=largo*alto
            blocks=int(m2*12.5)+5
            cemento=int(m2*1.15)+1
            arena=round(m2*0.08,2)
            varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + int(arena*2500) + varilla*420
            df=pd.DataFrame([[f"Block {tipo}",blocks,f"RD$ {precio_block}",f"RD$ {blocks*precio_block:,}"],["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"],["Varilla 3/8",varilla,"RD$ 420",f"RD$ {varilla*420:,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"Pared {m2} m2"}
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa",type="primary",use_container_width=True):
            df=pd.DataFrame([["Block 6''",112,"RD$ 42","RD$ 4,704"],["Cemento",15,"RD$ 550","RD$ 8,250"],["Varilla 3/8",20,"RD$ 420","RD$ 8,400"],["Arena",2,"RD$ 2,500","RD$ 5,000"],["Grava",1.5,"RD$ 2,800","RD$ 4,200"],["Zinc 10ft",6,"RD$ 750","RD$ 4,500"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":"Casita 3x3 Completa","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":35839,"titulo":"Casita 3x3 Completa"}
    elif obra=="Zapata Aislada":
        c1,c2,c3=st.columns(3)
        cant=c1.number_input("Cuantas zapatas",1,20,4)
        lado=c2.number_input("Lado zapata (m)",0.6,2.0,1.0)
        prof=c3.number_input("Profundidad (m)",0.6,2.0,1.0)
        if st.button("Calcular Zapata",type="primary"):
            conc=lado*lado*prof*cant
            cemento=int(conc*7)+1
            arena=round(conc*0.5,2)
            grava=round(conc*0.7,2)
            varilla=int(cant*6)
            total=cemento*550 + int(arena*2500) + int(grava*2800) + varilla*680
            df=pd.DataFrame([["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"],["Grava",grava,"RD$ 2,800",f"RD$ {int(grava*2800):,}"],["Varilla 1/2",varilla,"RD$ 680",f"RD$ {varilla*680:,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"{cant} Zapatas {lado}x{lado}m","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"{cant} Zapatas {lado}m"}
    elif obra=="Columna 3m":
        cant=st.number_input("Cuantas columnas",1,20,4)
        if st.button("Calcular Columna",type="primary"):
            cemento=int(cant*1.2)+1
            arena=round(cant*0.15,2)
            grava=round(cant*0.18,2)
            varilla=int(cant*4)
            alambre=int(cant*2)
            total=cemento*550 + int(arena*2500) + int(grava*2800) + varilla*680 + alambre*85
            df=pd.DataFrame([["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"],["Grava",grava,"RD$ 2,800",f"RD$ {int(grava*2800):,}"],["Varilla 1/2",varilla,"RD$ 680",f"RD$ {varilla*680:,}"],["Alambre lb",alambre,"RD$ 85",f"RD$ {alambre*85:,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"{cant} Columnas 3m","Icono":"🏛️","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"{cant} Columnas"}
    elif obra=="Viga 4m":
        cant=st.number_input("Cuantas vigas 4m",1,20,3)
        if st.button("Calcular Viga",type="primary"):
            cemento=int(cant*1.0)+1
            varilla=int(cant*5)
            total=cemento*550 + varilla*680 + cant*2*85
            df=pd.DataFrame([["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Varilla 1/2",varilla,"RD$ 680",f"RD$ {varilla*680:,}"],["Alambre",cant*2,"RD$ 85",f"RD$ {cant*2*85:,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"{cant} Vigas 4m","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"{cant} Vigas 4m"}
    elif obra=="Piso / Losa 10m2":
        m2=st.number_input("M2 de piso/losa",1.0,200.0,10.0)
        if st.button("Calcular Piso/Losa",type="primary"):
            cemento=int(m2*0.9)+1
            arena=round(m2*0.08,2)
            grava=round(m2*0.10,2)
            total=cemento*550 + int(arena*2500) + int(grava*2800)
            df=pd.DataFrame([["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"],["Grava",grava,"RD$ 2,800",f"RD$ {int(grava*2800):,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"Piso {m2}m2","Icono":"⬜","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"Piso {m2} m2"}
    elif obra=="Techo Zinc 20m2":
        m2=st.number_input("M2 de techo",1.0,200.0,20.0)
        if st.button("Calcular Techo Zinc",type="primary"):
            zinc=int(m2/2.5)+1
            clavo=int(zinc*0.5)+1
            varilla=int(m2/5)+1
            total=zinc*750 + clavo*120 + varilla*420
            df=pd.DataFrame([["Zinc 10ft",zinc,"RD$ 750",f"RD$ {zinc*750:,}"],["Clavo lb",clavo,"RD$ 120",f"RD$ {clavo*120:,}"],["Varilla 3/8",varilla,"RD$ 420",f"RD$ {varilla*420:,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"Techo Zinc {m2}m2","Icono":"🏠","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"Techo {m2} m2"}
    elif obra=="Empanete 20m2":
        m2=st.number_input("M2 de empanete",1.0,500.0,20.0)
        if st.button("Calcular Empanete",type="primary"):
            cemento=int(m2*0.25)+1
            arena=round(m2*0.04,2)
            total=cemento*550 + int(arena*2500)
            df=pd.DataFrame([["Cemento",cemento,"RD$ 550",f"RD$ {cemento*550:,}"],["Arena",arena,"RD$ 2,500",f"RD$ {int(arena*2500):,}"]],columns=["Material","Cant.","Precio","Subtotal"])
            st.session_state.calc_temp={"Producto":f"Empanete {m2}m2","Icono":"🎨","Cant":1,"Precio":total,"Total":total,"Codigo":""}
            st.session_state.calc_detalle={"df":df,"total":total,"titulo":f"Empanete {m2} m2"}
    if st.session_state.calc_detalle:
        st.divider()
        st.subheader(f"📋 Materiales: {st.session_state.calc_detalle['titulo']}")
        st.dataframe(st.session_state.calc_detalle["df"],use_container_width=True,hide_index=True)
        st.markdown(f"### 💰 TOTAL: RD$ {st.session_state.calc_detalle['total']:,}")
        if st.button("AGREGAR AL CARRITO",type="primary",use_container_width=True):
            agregar(st.session_state.calc_temp)
            st.rerun()

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado")
    col1,col2=st.columns([1,2])
    with col1:
        st.subheader("Nuevo Fiado")
        with st.form("nuevo_fiado",clear_on_submit=True):
            cliente=st.text_input("Nombre *",placeholder="Juan Perez")
            telefono=st.text_input("WhatsApp *",placeholder="829-264-7574")
            monto=st.number_input("Monto RD$ *",min_value=100,value=5000,step=100)
            fecha=st.date_input("Fecha fiado",value=date.today())
            vence=st.date_input("Vence",value=date.today())
            nota=st.text_input("Que se llevo",placeholder="10 Cemento")
            guardar=st.form_submit_button("Guardar Fiado",type="primary",use_container_width=True)
            if guardar:
                if cliente.strip()=="":
                    st.error("Pon nombre")
                else:
                    ok,msg,num_l=validar_rd(telefono)
                    if not ok:
                        st.error(f"❌ {msg}")
                    else:
                        st.session_state.fiados.append({"Cliente":cliente.strip(),"WhatsApp":num_l,"WhatsApp_Display":f"{num_l[:3]}-{num_l[3:6]}-{num_l[6:]}","Monto":monto,"Fecha":str(fecha),"Vence":str(vence),"QueLlevo":nota,"Estado":"Pendiente"})
                        save_fiados(st.session_state.fiados)
                        st.success("Guardado")
                        st.balloons()
    with col2:
        st.subheader("Fiados")
        fiados_list=st.session_state.get('fiados',[])
        if fiados_list:
            try:
                total_p=sum([float(f.get("Monto",0)) for f in fiados_list if str(f.get("Estado","")).lower()=="pendiente"])
            except:
                total_p=0
            st.metric("Por cobrar",f"RD$ {total_p:,.0f}")
            for i,row in enumerate(fiados_list):
                with st.container(border=True):
                    c_info,c_ws,c_acc=st.columns([2.5,1.5,1])
                    with c_info:
                        estado="🟡" if str(row.get("Estado","")).lower()=="pendiente" else "🟢"
                        st.markdown(f"{estado} **{row.get('Cliente','')}** - RD$ {float(row.get('Monto',0)):,}")
                        st.caption(f"📱 {row.get('WhatsApp_Display',row.get('WhatsApp',''))} | Vence: {row.get('Vence','')}")
                    with c_ws:
                        link_ws,_=generar_link_whatsapp(row.get('WhatsApp',''),row.get('Cliente',''),row.get('Monto',0),row.get('QueLlevo',''),row.get('Fecha',''),row.get('Vence',''))
                        st.link_button("WhatsApp",link_ws,use_container_width=True,type="primary")
                    with c_acc:
                        if str(row.get("Estado","")).lower()=="pendiente":
                            if st.button("Cobrado",key=f"cob_{i}",use_container_width=True):
                                st.session_state.fiados[i]["Estado"]="Pagado"
                                save_fiados(st.session_state.fiados)
                                st.rerun()
                        if st.button("🗑️",key=f"del_{i}",use_container_width=True):
                            st.session_state.fiados.pop(i)
                            save_fiados(st.session_state.fiados)
                            st.rerun()

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja + Reporte Excel PRO")
    ventas=st.session_state.get('ventas_hoy',0)
    fiados_list=st.session_state.get('fiados',[])
    try:
        fiados_total=sum([float(f.get("Monto",0)) for f in fiados_list if str(f.get("Estado","")).lower()=="pendiente"])
    except:
        fiados_total=0
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Efectivo Hoy",f"RD$ {ventas:,.0f}")
    c2.metric("Fiado",f"RD$ {fiados_total:,.0f}")
    c3.metric("Total Dia",f"RD$ {ventas+fiados_total:,.0f}")
    c4.metric("Productos",f"{len(st.session_state.inventario)} tipos")
    st.divider()
    st.subheader("📥 Reportes en Excel")
    def generar_excel_completo_safe(df_inv, fiados_list, ventas_hoy):
        from openpyxl.styles import Font, PatternFill, Alignment
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            fiados_total_safe = sum([float(f.get("Monto",0)) for f in fiados_list if str(f.get("Estado","")).lower()=="pendiente"]) if fiados_list else 0
            valor_inv = (df_inv["Stock"]*df_inv["Precio"]).sum() if not df_inv.empty else 0
            df_resumen = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),"Negocio": st.session_state.negocio_nombre,"Ventas Hoy Efectivo": float(ventas_hoy),"Fiado Por Cobrar": float(fiados_total_safe),"Total Dia": float(ventas_hoy + fiados_total_safe),"Valor Inventario": float(valor_inv),"Factura Actual": int(st.session_state.contador_factura)}])
            df_resumen.to_excel(writer, sheet_name='Cierre_Dia', index=False)
            df_inv.to_excel(writer, sheet_name='Inventario', index=False)
            if fiados_list and len(fiados_list) > 0:
                pd.DataFrame(fiados_list).to_excel(writer, sheet_name='Fiados', index=False)
            else:
                pd.DataFrame([{"Nota":"No hay fiados registrados aun - Sistema 606"}]).to_excel(writer, sheet_name='Fiados', index=False)
            df_fact_all = cargar_facturas()
            if not df_fact_all.empty:
                df_fact_all.to_excel(writer, sheet_name='Facturas', index=False)
            if st.session_state.carrito:
                pd.DataFrame(st.session_state.carrito).to_excel(writer, sheet_name='Ultima_Venta', index=False)
            for sheet_name in writer.sheets:
                ws = writer.sheets[sheet_name]
                fill = PatternFill(start_color="FF6B00", end_color="FF6B00", fill_type="solid")
                for col in range(1, ws.max_column + 1):
                    cell = ws.cell(row=1, column=col)
                    cell.font = Font(bold=True, color="FFFFFF", size=11)
                    cell.fill = fill
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 4, 40)
                    ws.column_dimensions[column_letter].width = adjusted_width
        return output.getvalue()
    excel_data = generar_excel_completo_safe(st.session_state.inventario, fiados_list, ventas)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(label="📊 EXCEL COMPLETO DEL DIA", data=excel_data, file_name=f"REPORTE_LaFe_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
    with col_b:
        output_f = BytesIO()
        with pd.ExcelWriter(output_f, engine='openpyxl') as writer:
            if fiados_list and len(fiados_list) > 0:
                pd.DataFrame(fiados_list).to_excel(writer, sheet_name='Fiados_Por_Cobrar', index=False)
            else:
                pd.DataFrame([{"Nota":"No hay fiados aun"}]).to_excel(writer, sheet_name='Fiados_Por_Cobrar', index=False)
        st.download_button(label="📓 Solo Fiados Excel", data=output_f.getvalue(), file_name=f"FIADOS_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with col_c:
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='openpyxl') as writer:
            st.session_state.inventario.to_excel(writer, sheet_name='Inventario', index=False)
        st.download_button(label="📦 Solo Inventario Excel", data=output_inv.getvalue(), file_name=f"INVENTARIO_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.divider()
    izq,der=st.columns([1.1,1.4])
    with izq:
        st.subheader("Cuadre")
        st.info(f"Sistema dice: RD$ {ventas:,.2f}")
        ef=st.number_input("Efectivo FISICO en caja",min_value=0.0,value=float(ventas),step=100.0)
        dif=ef-ventas
        if ventas>0:
            if dif==0:
                st.success("CUADRE PERFECTO")
            elif dif>0:
                st.warning(f"SOBRA RD$ {dif:,.2f}")
            else:
                st.error(f"FALTA RD$ {abs(dif):,.2f}")
        if st.button("Cerrar Dia",type="primary",use_container_width=True):
            st.session_state.ventas_hoy=0
            save_ventas(0)
            st.rerun()
    with der:
        st.subheader("Resumen Inventario (Solo lectura)")
        valor_inv=(st.session_state.inventario["Stock"]*st.session_state.inventario["Precio"]).sum()
        st.metric("Valor Inventario",f"RD$ {valor_inv:,.0f}")
        st.caption("Para editar ve a 🔐 Inventario Jefe")

elif menu=="🔐 Inventario Jefe":
    st.title("🔐 Inventario Jefe - Solo el Jefe")
    st.caption("Esta seccion es privada. El empleado no puede entrar. Aqui si puedes cambiar precio, stock y agregar productos.")
    if 'jefe_ok' not in st.session_state:
        st.session_state.jefe_ok = False
    if not st.session_state.jefe_ok:
        clave_jefe = st.text_input("Pon clave de Jefe", type="password", placeholder="Clave del jefe")
        if st.button("Entrar como Jefe", type="primary"):
            if clave_jefe == CLAVE_JEFE:
                st.session_state.jefe_ok = True
                st.rerun()
            else:
                st.error("Clave incorrecta. Pregunta al jefe.")
        st.info("Clave por defecto: 6060 - Cambiala en el codigo donde dice CLAVE_JEFE = '6060'")
        st.stop()
    st.success("✅ Acceso Jefe Autorizado")
    if st.button("🔒 Cerrar sesion Jefe"):
        st.session_state.jefe_ok = False
        st.rerun()
    st.subheader("📦 Inventario Editable - Solo Jefe")
    try:
        df_edit=st.data_editor(st.session_state.inventario[["Codigo","Producto","Stock","Precio","Cat","Icono"]],use_container_width=True,num_rows="dynamic")
        if st.button("💾 Guardar Cambios en SQL - Jefe",type="primary",use_container_width=True):
            # Guardar todo, incluyendo productos nuevos
            st.session_state.inventario = df_edit.copy()
            save_inv(st.session_state.inventario)
            st.success("Guardado por el Jefe!")
            st.rerun()
        valor_inv=(st.session_state.inventario["Stock"]*st.session_state.inventario["Precio"]).sum()
        st.metric("Valor Inventario",f"RD$ {valor_inv:,.0f}")
        st.divider()
        st.subheader("➕ Agregar Producto Nuevo")
        with st.form("nuevo_prod_jefe"):
            nc = st.text_input("Codigo", placeholder="EJ: TUB001")
            np = st.text_input("Producto", placeholder="Tubo PVC 3''")
            nprecio = st.number_input("Precio", min_value=1, value=100)
            nstock = st.number_input("Stock", min_value=0, value=50)
            ncat = st.text_input("Categoria", value="General")
            nicono = st.text_input("Icono", value="📦")
            if st.form_submit_button("Agregar Producto"):
                nuevo = pd.DataFrame([{"Codigo":nc,"Producto":np,"Precio":nprecio,"Stock":nstock,"Cat":ncat,"Icono":nicono}])
                st.session_state.inventario = pd.concat([st.session_state.inventario, nuevo], ignore_index=True)
                save_inv(st.session_state.inventario)
                st.success("Producto agregado")
                st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

elif menu=="🔍 Ver Base de Datos SQL":
    st.title("🔍 Base de Datos SQL - La Fe 606")
    st.caption("Vista minimalista | Archivo: lafe_606.db")
    conn = get_conn()
    try:
        total_prod = conn.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]
        total_fiados = conn.execute("SELECT COUNT(*) FROM fiados").fetchone()[0]
        total_stock = conn.execute("SELECT SUM(Stock) FROM inventario").fetchone()[0] or 0
        valor_inv = conn.execute("SELECT SUM(Stock*Precio) FROM inventario").fetchone()[0] or 0
        ventas_hoy_db = conn.execute("SELECT valor FROM ventas_config WHERE clave='ventas_hoy'").fetchone()[0]
        contador_db = conn.execute("SELECT valor FROM ventas_config WHERE clave='contador_factura'").fetchone()[0]
    except Exception as e:
        total_prod, total_fiados, total_stock, valor_inv = 0,0,0,0
        ventas_hoy_db, contador_db = "0","1"
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📦 Productos", total_prod)
    c2.metric("📓 Fiados", total_fiados)
    c3.metric("📊 Stock Total", f"{total_stock:,}")
    c4.metric("💰 Valor Inventario", f"RD$ {valor_inv:,.0f}")
    st.caption(f"Ventas Hoy: RD$ {float(ventas_hoy_db):,.0f} | Proxima Factura: {int(float(contador_db)):06d}")
    st.divider()
    tabla = st.selectbox("Elige tabla:", ["inventario", "fiados", "ventas_config", "clientes", "facturas"])
    buscar = st.text_input("🔎 Buscar en esta tabla...", placeholder="Ej: cemento, varilla, Juan, CEM001...")
    try:
        df_sql = pd.read_sql(f"SELECT * FROM {tabla}", conn)
        if buscar:
            mask = df_sql.astype(str).apply(lambda x: x.str.contains(buscar, case=False, na=False)).any(axis=1)
            df_sql = df_sql[mask]
        st.write(f"**{len(df_sql)} filas** en `{tabla}`")
        st.dataframe(df_sql, use_container_width=True, hide_index=True)
        col_d, col_e = st.columns(2)
        with col_d:
            csv = df_sql.to_csv(index=False).encode('utf-8')
            st.download_button(f"⬇️ Descargar {tabla} CSV", data=csv, file_name=f"{tabla}_lafe606.csv", mime="text/csv", use_container_width=True)
        with col_e:
            if st.button("🔄 Recargar desde SQL", use_container_width=True):
                st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
    conn.close()
