import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse

st.set_page_config(page_title="Ferretería La Fe - Sistema 606 PRO", layout="wide", page_icon="🧱")

# ========== GOOGLE SHEETS PERSISTENCIA ==========
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEETS_ENABLED = True
except:
    GSHEETS_ENABLED = False

def get_client():
    if not GSHEETS_ENABLED: return None
    try:
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        return None

def cargar_sheets():
    client = get_client()
    if not client: return None, None, None
    try:
        sh = client.open("LaFe_606_DB")
        df_inv = pd.DataFrame(sh.worksheet("inventario").get_all_records())
        fiados = sh.worksheet("fiados").get_all_records()
        v = sh.worksheet("ventas_hoy").get_all_records()
        ventas = float(v[0]["ventas_hoy"]) if v else 0
        return df_inv, fiados, ventas
    except:
        return None, None, None

def save_inv(df):
    client = get_client()
    if not client: return
    try:
        sh = client.open("LaFe_606_DB")
        ws = sh.worksheet("inventario")
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())
    except: pass

def save_fiados(lista):
    client = get_client()
    if not client: return
    try:
        sh = client.open("LaFe_606_DB")
        ws = sh.worksheet("fiados")
        if not lista:
            ws.clear()
            ws.update([["Cliente","WhatsApp","WhatsApp_Display","Monto","Fecha","Vence","Que llevó","Estado"]])
            return
        df = pd.DataFrame(lista)
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())
    except: pass

def save_ventas(monto):
    client = get_client()
    if not client: return
    try:
        sh = client.open("LaFe_606_DB")
        ws = sh.worksheet("ventas_hoy")
        ws.clear()
        ws.update([["ventas_hoy"], [monto]])
    except: pass

def inventario_nuevo():
    return pd.DataFrame([
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

# CARGAR
if 'inventario' not in st.session_state:
    df_s, f_s, v_s = cargar_sheets()
    if df_s is not None and not df_s.empty:
        st.session_state.inventario = df_s
        st.session_state.fiados = f_s if f_s else []
        st.session_state.ventas_hoy = v_s if v_s else 0
    else:
        st.session_state.inventario = inventario_nuevo()
        st.session_state.fiados = []
        st.session_state.ventas_hoy = 0

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'ultima_factura' not in st.session_state: st.session_state.ultima_factura=None
if 'contador_factura' not in st.session_state: st.session_state.contador_factura=1
if 'historial_ventas' not in st.session_state: st.session_state.historial_ventas=[]
if 'calc_temp' not in st.session_state: st.session_state.calc_temp=None
if 'calc_detalle' not in st.session_state: st.session_state.calc_detalle=None

def agregar_al_carrito(nuevo_item):
    for i, item in enumerate(st.session_state.carrito):
        if item['Producto'] == nuevo_item['Producto']:
            st.session_state.carrito[i]['Cant'] += nuevo_item['Cant']
            st.session_state.carrito[i]['Total'] += nuevo_item['Total']
            return
    st.session_state.carrito.append(nuevo_item)

def generar_texto_factura(cliente, carrito, subtotal, itbis, total, num_factura):
    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    lineas = [f"{'='*42}", "      FERRETERIA LA FE - QUISQUEYA", "      San Pedro de Macoris, RD", "      Tel: 829-264-7574 - RNC: 123456789", f"{'='*42}", f"FACTURA No: {num_factura:06d}", f"FECHA: {fecha}", f"CLIENTE: {cliente}", f"{'-'*42}"]
    for item in carrito:
        lineas.append(f"{item['Cant']} x {item['Producto'][:28]}")
        lineas.append(f"   RD$ {item['Total']:,}")
    lineas += [f"{'-'*42}", f"SUBTOTAL: RD$ {subtotal:,.2f}", f"ITBIS 18%: RD$ {itbis:,.2f}", f"TOTAL: RD$ {total:,.2f}", f"{'='*42}", "  Gracias por su compra en La Fe!"]
    return "\n".join(lineas)

def imprimir_factura_html(texto_factura, num_factura):
    html_code = f"""<html><head><style>@page {{ size: 80mm auto; margin: 2mm; }} body {{ font-family: 'Courier New', monospace; width: 72mm; font-size: 12px; line-height: 1.3; margin: 0 auto; background: white; color: black; }} pre {{ white-space: pre-wrap; }} .btn-print {{ background: #FF6B00; color: white; border: none; padding: 15px 20px; font-size: 18px; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 15px; font-weight: bold; }} @media print {{ .btn-print {{ display: none; }} }}</style></head><body><pre>{texto_factura}</pre><button class="btn-print" onclick="window.print()">IMPRIMIR FACTURA {num_factura:06d}</button></body></html>"""
    components.html(html_code, height=700, scrolling=True)

def generar_link_whatsapp(numero, cliente, monto, que_llevo, fecha):
    num_limpio = "".join(filter(str.isdigit, str(numero)))
    if len(num_limpio) == 10: num_limpio = "1" + num_limpio
    mensaje = f"Hola {cliente},\n\nTe saluda FERRETERIA LA FE de Quisqueya.\n\nBalance pendiente:\nMonto: RD$ {monto:,}\nDetalle: {que_llevo}\nFecha: {fecha}\n\nPasa por la ferreteria cuando puedas.\nFerreteria La Fe - 829-264-7574"
    return f"https://wa.me/{num_limpio}?text={urllib.parse.quote(mensaje)}", num_limpio

def validar_numero_rd(numero):
    num_limpio = "".join(filter(str.isdigit, str(numero)))
    if len(num_limpio) == 11 and num_limpio.startswith("1"): num_limpio = num_limpio[1:]
    if len(num_limpio) != 10: return False, "Debe tener 10 dígitos", num_limpio
    if num_limpio[:3] not in ["809","829","849"]: return False, f"Prefijo debe ser 809,829,849", num_limpio
    return True, "Válido", num_limpio

# UI HEADER
col_logo, col_title = st.columns([1,4])
with col_logo:
    try: st.image("logo.png", width=110)
    except: st.markdown("### 🧱 La Fe")
with col_title:
    st.markdown("## Ferretería La Fe - Sistema 606 PRO RD$25k")
    if get_client(): st.caption("✅ PRO - Datos en la nube Google Sheets | Persistente")
    else: st.caption("⚠️ Modo Local - Configura Sheets para PRO")

with st.sidebar:
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("💾 Guardar todo en la nube", type="primary", use_container_width=True):
        save_inv(st.session_state.inventario)
        save_fiados(st.session_state.fiados)
        save_ventas(st.session_state.ventas_hoy)
        st.success("✅ Guardado!")
    if st.button("🔄 Resetear sistema"):
        st.session_state.clear()
        st.rerun()

# ========== PUNTO DE VENTA ==========
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        codigo_escaneado = st.text_input("Pistolea el código aquí", placeholder="Ej: CEM001")
        if st.button("🔎 Buscar Código"):
            inv = st.session_state.inventario
            match = inv[inv["Código"].str.upper().str.strip() == codigo_escaneado.upper().strip()]
            if not match.empty:
                row = match.iloc[0]
                agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio RD$'],"Total":1*row['Precio RD$'],"Código":row['Código']})
                st.rerun()
        st.divider()
        buscador=st.text_input("Busca: cemento, varilla, block...")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            for idx, row in res.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Producto']}** - RD$ {row['Precio RD$']} | Stock {row['Stock']}")
                    cant=st.number_input("Cant",1,1000,1,key=f"cant_{row['Código']}")
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
            itbis = subtotal * 0.18
            total = subtotal * 1.18
            st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR Y GENERAR FACTURA", type="primary", use_container_width=True):
                num = st.session_state.contador_factura
                texto_fact = generar_texto_factura(cliente_factura, st.session_state.carrito, subtotal, itbis, total, num)
                st.session_state.ultima_factura = {"texto": texto_fact, "cliente": cliente_factura, "total": total, "num": num}
                st.session_state.ventas_hoy+=total
                st.session_state.historial_ventas.append({"Factura": num, "Cliente": cliente_factura, "Total": total, "Fecha": datetime.now().strftime("%H:%M")})
                st.session_state.contador_factura+=1
                for item in st.session_state.carrito:
                    if item.get("Código"):
                        idx = st.session_state.inventario[st.session_state.inventario["Código"]==item["Código"]].index
                        if not idx.empty:
                            st.session_state.inventario.loc[idx, "Stock"] -= item["Cant"]
                # GUARDAR EN LA NUBE AUTOMATICO
                save_inv(st.session_state.inventario)
                save_ventas(st.session_state.ventas_hoy)
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
            if st.button("🗑️ Vaciar carrito"):
                st.session_state.carrito=[]
                st.rerun()
        if st.session_state.ultima_factura:
            st.divider()
            st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", use_container_width=True)
            imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo - Stock Actual")
    st.dataframe(st.session_state.inventario[["Código","Producto","Precio RD$","Stock","Cat"]], use_container_width=True)

elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora Inteligente")
    obra=st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Zapata (4 zapatas)", "Piso 10x10 (100 m2)", "Casita 3x3 Completa", "Techo de Zinc 3x3"])
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo (m)", 1.0, 100.0, 10.0)
        alto=c2.number_input("Alto (m)", 1.0, 10.0, 2.5)
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"])
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared", type="primary"):
            m2=largo*alto
            blocks=int(m2*12.5)+5; cemento=int(m2*1.15)+1; arena=round(m2*0.08,2); varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + arena*2500 + varilla*420
            detalle_df = pd.DataFrame([[f"🧱 {tipo}", blocks, f"RD$ {precio_block}", f"RD$ {blocks*precio_block:,}"],["🏗️ Cemento", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],["🏖️ Arena", arena, "RD$ 2,500", f"RD$ {int(arena*2500):,}"],["🔩 Varilla 3/8", varilla, "RD$ 420", f"RD$ {varilla*420:,}"]], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"Pared {m2} m2"}
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True):
            detalle_df = pd.DataFrame([["🧱 Block 6''", 112, "RD$ 42", "RD$ 4,704"],["🏗️ Cemento", 15, "RD$ 550", "RD$ 8,250"],["🔩 Varilla 3/8", 20, "RD$ 420", "RD$ 8,400"],["🏖️ Arena", 2, "RD$ 2,500", "RD$ 5,000"],["🪨 Grava", 1.5, "RD$ 2,800", "RD$ 4,200"],["🏠 Zinc 10ft", 6, "RD$ 750", "RD$ 4,500"]], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":"Casita 3x3 Completa","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": 35839, "titulo": "Casita 3x3 Completa"}
    if st.session_state.calc_detalle:
        st.divider()
        st.subheader(f"📋 Materiales: {st.session_state.calc_detalle['titulo']}")
        st.dataframe(st.session_state.calc_detalle["df"], use_container_width=True, hide_index=True)
        st.markdown(f"### 💰 TOTAL: RD$ {st.session_state.calc_detalle['total']:,}")
        if st.button("➕ AGREGAR AL CARRITO", type="primary", use_container_width=True):
            agregar_al_carrito(st.session_state.calc_temp)
            st.rerun()
    if st.session_state.carrito:
        st.divider()
        subtotal = sum([x['Total'] for x in st.session_state.carrito]); itbis=subtotal*0.18; total=subtotal*1.18
        st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
        cliente_calc = st.text_input("Cliente", value="Cliente Obra", key="cliente_calc")
        if st.button("✅ COBRAR Y FACTURAR - CALCULADORA", type="primary", use_container_width=True):
            num = st.session_state.contador_factura
            texto_fact = generar_texto_factura(cliente_calc, st.session_state.carrito, subtotal, itbis, total, num)
            st.session_state.ultima_factura = {"texto": texto_fact, "cliente": cliente_calc, "total": total, "num": num}
            st.session_state.ventas_hoy+=total
            st.session_state.contador_factura+=1
            save_ventas(st.session_state.ventas_hoy)
            st.session_state.carrito=[]
            st.balloons()
            st.rerun()
    if st.session_state.ultima_factura:
        st.divider()
        imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado - Validado PRO")
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre *", placeholder="Ej: Juan Perez")
            telefono = st.text_input("WhatsApp *", placeholder="Ej: 829-264-7574")
            monto = st.number_input("Monto RD$ *", min_value=100, max_value=500000, value=5000, step=100)
            fecha = st.date_input("Fecha fiado", value=date.today())
            vence = st.date_input("Vence", value=date.today())
            nota = st.text_input("Qué se llevó", placeholder="Ej: 10 Cemento")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar:
                if cliente.strip() == "":
                    st.error("❌ Pon nombre")
                else:
                    ok, msg, num_l = validar_numero_rd(telefono)
                    if not ok:
                        st.error(f"❌ {msg}")
                    else:
                        st.session_state.fiados.append({"Cliente": cliente.strip(),"WhatsApp": num_l,"WhatsApp_Display": f"{num_l[:3]}-{num_l[3:6]}-{num_l[6:]}","Monto": monto,"Fecha": str(fecha),"Vence": str(vence),"Que llevó": nota,"Estado": "Pendiente"})
                        save_fiados(st.session_state.fiados)
                        st.success(f"✅ Guardado y sincronizado en la nube")
                        st.balloons()
    with col2:
        st.subheader("📋 Fiados")
        if st.session_state.fiados:
            total_p = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"])
            st.metric("💰 Por cobrar", f"RD$ {total_p:,.0f}")
            for i, row in enumerate(st.session_state.fiados):
                with st.container(border=True):
                    c_info, c_ws, c_acc = st.columns([2.5, 1.5, 1])
                    with c_info:
                        estado = "🟡" if row.get("Estado")=="Pendiente" else "🟢"
                        st.markdown(f"{estado} **{row['Cliente']}** - RD$ {row['Monto']:,}")
                        st.caption(f"📱 {row.get('WhatsApp_Display', row.get('WhatsApp',''))} | Vence: {row.get('Vence','')}")
                    with c_ws:
                        link_ws, _ = generar_link_whatsapp(row.get('WhatsApp',''), row['Cliente'], row['Monto'], row.get('Que llevó',''), row.get('Fecha',''))
                        st.link_button(f"💬 WhatsApp", link_ws, use_container_width=True, type="primary")
                    with c_acc:
                        if row.get("Estado") == "Pendiente":
                            if st.button("✅ Cobrado", key=f"cob_{i}", use_container_width=True):
                                st.session_state.fiados[i]["Estado"] = "Pagado"
                                save_fiados(st.session_state.fiados)
                                st.rerun()
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            st.session_state.fiados.pop(i)
                            save_fiados(st.session_state.fiados)
                            st.rerun()

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja PRO")
    ventas = st.session_state.ventas_hoy
    fiados_total = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}")
    with c2: st.metric("📓 Fiado", f"RD$ {fiados_total:,.0f}")
    with c3: st.metric("📈 Total Día", f"RD$ {ventas+fiados_total:,.0f}")
    with c4: st.metric("🧱 Productos", f"{len(st.session_state.inventario)} tipos")
    st.divider()
    izq, der = st.columns([1.1, 1.4])
    with izq:
        st.subheader("💰 Cuadre")
        st.info(f"Sistema dice: RD$ {ventas:,.2f}")
        ef = st.number_input("Efectivo FÍSICO en caja", min_value=0.0, value=float(ventas), step=100.0)
        dif = ef - ventas
        if ventas>0:
            if dif==0: st.success(f"✅ CUADRE PERFECTO")
            elif dif>0: st.warning(f"⚠️ SOBRA RD$ {dif:,.2f}")
            else: st.error(f"❌ FALTA RD$ {abs(dif):,.2f}")
        if st.button("🔒 Cerrar Día", type="primary", use_container_width=True):
            st.session_state.ventas_hoy=0
            save_ventas(0)
            st.rerun()
    with der:
        st.subheader("📦 Inventario Editable - PRO")
        st.caption("EDITA el stock - Se guarda en la nube automáticamente")
        df_edit = st.data_editor(st.session_state.inventario[["Código","Producto","Stock","Precio RD$"]], use_container_width=True, num_rows="fixed", column_config={"Stock": st.column_config.NumberColumn("Stock EDITABLE", min_value=0, max_value=10000, step=1), "Precio RD$": st.column_config.NumberColumn("Precio RD$", min_value=0)}, key="editor_stock")
        if st.button("💾 Guardar cambios de Stock en la nube", type="primary", use_container_width=True):
            for idx, row in df_edit.iterrows():
                codigo = row["Código"]
                real_idx = st.session_state.inventario[st.session_state.inventario["Código"]==codigo].index
                if not real_idx.empty:
                    st.session_state.inventario.loc[real_idx, "Stock"] = row["Stock"]
                    st.session_state.inventario.loc[real_idx, "Precio RD$"] = row["Precio RD$"]
            save_inv(st.session_state.inventario)
            st.success("✅ Stock guardado en Google Sheets!")
            st.rerun()
        st.divider()
        c_fast1, c_fast2, c_fast3 = st.columns([2,1,1])
        with c_fast1:
            prod_entrada = st.selectbox("Producto que llegó", st.session_state.inventario["Producto"].tolist())
        with c_fast2:
            cant_entrada = st.number_input("Cantidad que llegó", min_value=1, max_value=1000, value=10)
        with c_fast3:
            st.write("")
            if st.button("➕ Sumar", use_container_width=True, type="primary"):
                idx = st.session_state.inventario[st.session_state.inventario["Producto"]==prod_entrada].index
                if not idx.empty:
                    st.session_state.inventario.loc[idx, "Stock"] += cant_entrada
                    save_inv(st.session_state.inventario)
                    st.success(f"✅ Sumaste {cant_entrada}")
                    st.rerun()
        valor_inv = (st.session_state.inventario["Stock"] * st.session_state.inventario["Precio RD$"]).sum()
        st.metric("💰 Valor Inventario", f"RD$ {valor_inv:,.0f}")
