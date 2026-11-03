import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse
import sqlite3, hashlib, time
from io import BytesIO

st.set_page_config(page_title="Ferreteria La Fe 606 PRO DEFINITIVO", layout="wide", page_icon="🧱")
DB_FILE = "lafe_606.db"

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
    INSERT OR IGNORE INTO ventas_config VALUES ('ventas_hoy','0');
    INSERT OR IGNORE INTO ventas_config VALUES ('contador_factura','1');
    """)
    conn.commit()
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
    cur.execute("DELETE FROM inventario")
    cur.executemany("INSERT INTO inventario VALUES (?,?,?,?,?,?)", productos)
    conn.commit()
    conn.close()

init_db()

def generar_clave(n,t):
    b=f"606-{n.upper().strip()}-{t}-LAFE2026"
    h=hashlib.md5(b.encode()).hexdigest().upper()[:12]
    return f"LAFE-{h[:4]}-{h[4:8]}-{h[8:12]}"

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

def agregar(it):
    for i,x in enumerate(st.session_state.carrito):
        if x['Producto']==it['Producto']:
            st.session_state.carrito[i]['Cant']+=it['Cant']
            st.session_state.carrito[i]['Total']+=it['Total']
            return
    st.session_state.carrito.append(it)

def generar_texto_factura(cliente,carrito,sub,itbis,total,num):
    f=datetime.now().strftime("%d/%m/%Y %I:%M %p")
    l=[f"{'='*42}","      FERRETERIA LA FE - QUISQUEYA",f"{'='*42}",f"FACTURA No: {num:06d}",f"FECHA: {f}",f"CLIENTE: {cliente}",f"{'-'*42}"]
    for it in carrito:
        l.append(f"{it['Cant']} x {it['Producto'][:28]}")
        l.append(f"   RD$ {it['Total']:,}")
    l+=[f"{'-'*42}",f"SUBTOTAL: RD$ {sub:,.2f}",f"ITBIS 18%: RD$ {itbis:,.2f}",f"TOTAL: RD$ {total:,.2f}",f"{'='*42}","  Gracias!"]
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
    menu=st.radio("Ir a:", ["🛒 Punto de Venta","📦 Catalogo COMPLETO","🏷️ Codigos de Barra","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("💾 Guardar en SQL",type="primary",use_container_width=True):
        save_inv(st.session_state.inventario)
        save_fiados(st.session_state.fiados)
        save_ventas(st.session_state.ventas_hoy)
        save_contador(st.session_state.contador_factura)
        st.success("Guardado!")

if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        cod=st.text_input("Pistolea codigo",placeholder="CEM001, CEM002, VAR001, etc")
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
        st.subheader("Factura")
        cliente=st.text_input("Cliente",value="Cliente Mostrador")
        if st.session_state.carrito:
            for it in st.session_state.carrito:
                st.write(f"{it.get('Icono','')} {it['Producto'][:22]} - {it['Cant']} x RD$ {it['Total']:,}")
            sub=sum([x['Total'] for x in st.session_state.carrito])
            itbis=sub*0.18
            total=sub*1.18
            st.metric("TOTAL + ITBIS",f"RD$ {total:,.2f}")
            if st.button("COBRAR Y FACTURA",type="primary",use_container_width=True):
                num=st.session_state.contador_factura
                texto=generar_texto_factura(cliente,st.session_state.carrito,sub,itbis,total,num)
                st.session_state.ultima_factura={"texto":texto,"num":num}
                st.session_state.ventas_hoy+=total
                st.session_state.contador_factura+=1
                for it in st.session_state.carrito:
                    if it.get("Codigo"):
                        idx=st.session_state.inventario[st.session_state.inventario["Codigo"]==it["Codigo"]].index
                        if not idx.empty:
                            st.session_state.inventario.loc[idx,"Stock"]-=it["Cant"]
                save_inv(st.session_state.inventario)
                save_ventas(st.session_state.ventas_hoy)
                save_contador(st.session_state.contador_factura)
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
            if st.button("Vaciar carrito"):
                st.session_state.carrito=[]
                st.rerun()
        if st.session_state.ultima_factura:
            st.download_button("Descargar TXT",st.session_state.ultima_factura["texto"],file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt",use_container_width=True)
            imprimir_factura_html(st.session_state.ultima_factura["texto"],st.session_state.ultima_factura["num"])

elif menu=="📦 Catalogo COMPLETO":
    st.title("📦 Catalogo COMPLETO - 13 Productos")
    st.success("Incluye CEM002, VAR002, BLK04, BLK08, ALAM01, CLAV01, PINT01, ARE001, GRAV01")
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
    st.title("📊 Cierre de Caja + Reporte Excel")
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
    st.subheader("📥 Reportes en Excel - Para DGII y Control")

    def generar_excel_completo_safe(df_inv, fiados_list, ventas_hoy):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            fiados_total_safe = sum([float(f.get("Monto",0)) for f in fiados_list if str(f.get("Estado","")).lower()=="pendiente"]) if fiados_list else 0
            valor_inv = (df_inv["Stock"]*df_inv["Precio"]).sum() if not df_inv.empty else 0
            df_resumen = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Negocio": st.session_state.negocio_nombre,
                "Ventas Hoy Efectivo": ventas_hoy,
                "Fiado Por Cobrar": fiados_total_safe,
                "Total Dia": ventas_hoy + fiados_total_safe,
                "Valor Inventario": valor_inv,
                "Factura Actual": st.session_state.contador_factura
            }])
            df_resumen.to_excel(writer, sheet_name='Cierre_Dia', index=False)
            df_inv.to_excel(writer, sheet_name='Inventario', index=False)
            if fiados_list and len(fiados_list) > 0:
                pd.DataFrame(fiados_list).to_excel(writer, sheet_name='Fiados', index=False)
            else:
                pd.DataFrame([{"Nota":"No hay fiados registrados aun - Sistema 606"}]).to_excel(writer, sheet_name='Fiados', index=False)
            if st.session_state.carrito:
                pd.DataFrame(st.session_state.carrito).to_excel(writer, sheet_name='Ultima_Venta', index=False)
        return output.getvalue()

    excel_data = generar_excel_completo_safe(st.session_state.inventario, fiados_list, ventas)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            label="📊 EXCEL COMPLETO DEL DIA",
            data=excel_data,
            file_name=f"REPORTE_LaFe_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
        st.caption("4 hojas: Cierre, Inventario, Fiados, Ultima Venta")
    
    with col_b:
        output_f = BytesIO()
        with pd.ExcelWriter(output_f, engine='openpyxl') as writer:
            if fiados_list and len(fiados_list) > 0:
                pd.DataFrame(fiados_list).to_excel(writer, sheet_name='Fiados_Por_Cobrar', index=False)
            else:
                pd.DataFrame([{"Nota":"No hay fiados aun - Agrega uno en Fiado"}]).to_excel(writer, sheet_name='Fiados_Por_Cobrar', index=False)
        st.download_button(
            label="📓 Solo Fiados Excel",
            data=output_f.getvalue(),
            file_name=f"FIADOS_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_c:
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='openpyxl') as writer:
            st.session_state.inventario.to_excel(writer, sheet_name='Inventario', index=False)
        st.download_button(
            label="📦 Solo Inventario Excel",
            data=output_inv.getvalue(),
            file_name=f"INVENTARIO_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

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
        st.subheader("Inventario Editable")
        try:
            df_edit=st.data_editor(st.session_state.inventario[["Codigo","Producto","Stock","Precio"]],use_container_width=True,num_rows="fixed")
            if st.button("Guardar Stock en SQL",type="primary",use_container_width=True):
                for _,row in df_edit.iterrows():
                    codigo=row["Codigo"]
                    real_idx=st.session_state.inventario[st.session_state.inventario["Codigo"]==codigo].index
                    if not real_idx.empty:
                        st.session_state.inventario.loc[real_idx,"Stock"]=row["Stock"]
                        st.session_state.inventario.loc[real_idx,"Precio"]=row["Precio"]
                save_inv(st.session_state.inventario)
                st.success("Guardado!")
                st.rerun()
            valor_inv=(st.session_state.inventario["Stock"]*st.session_state.inventario["Precio"]).sum()
            st.metric("Valor Inventario",f"RD$ {valor_inv:,.0f}")
        except Exception as e:
            st.error(f"Error: {e}")
