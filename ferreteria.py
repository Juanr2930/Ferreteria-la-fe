import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components
import urllib.parse

st.set_page_config(page_title="Ferretería La Fe - Sistema 606", layout="wide", page_icon="🧱")

def show_logo(w=120):
    try:
        st.image("logo.png", width=w)
    except:
        st.markdown("### 🧱 La Fe")

col_logo, col_title = st.columns([1,4])
with col_logo:
    show_logo(110)
with col_title:
    st.markdown("## Ferretería La Fe - Sistema 606")
    st.caption("Quisqueya, SPM | POS 606 + Factura 80mm + Fiado WhatsApp + Stock Editable")

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

if 'inventario' not in st.session_state or "Icono" not in st.session_state.inventario.columns:
    st.session_state.inventario = inventario_nuevo()
if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'fiados' not in st.session_state: st.session_state.fiados=[]
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy=0
if 'ultima_factura' not in st.session_state: st.session_state.ultima_factura=None
if 'contador_factura' not in st.session_state: st.session_state.contador_factura=1
if 'calc_temp' not in st.session_state: st.session_state.calc_temp=None
if 'calc_detalle' not in st.session_state: st.session_state.calc_detalle=None
if 'historial_ventas' not in st.session_state: st.session_state.historial_ventas=[]

def agregar_al_carrito(nuevo_item):
    for i, item in enumerate(st.session_state.carrito):
        if item['Producto'] == nuevo_item['Producto']:
            st.session_state.carrito[i]['Cant'] += nuevo_item['Cant']
            st.session_state.carrito[i]['Total'] += nuevo_item['Total']
            return
    st.session_state.carrito.append(nuevo_item)

def generar_texto_factura(cliente, carrito, subtotal, itbis, total, num_factura):
    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    lineas = []
    lineas.append("="*42)
    lineas.append("      FERRETERIA LA FE - QUISQUEYA")
    lineas.append("      San Pedro de Macoris, RD")
    lineas.append("      Tel: 829-264-7574 - RNC: 123456789")
    lineas.append("="*42)
    lineas.append(f"FACTURA No: {num_factura:06d}")
    lineas.append(f"FECHA: {fecha}")
    lineas.append(f"CLIENTE: {cliente}")
    lineas.append("-"*42)
    for item in carrito:
        lineas.append(f"{item['Cant']} x {item['Producto'][:28]}")
        lineas.append(f"   RD$ {item['Total']:,}")
    lineas.append("-"*42)
    lineas.append(f"SUBTOTAL: RD$ {subtotal:,.2f}")
    lineas.append(f"ITBIS 18%: RD$ {itbis:,.2f}")
    lineas.append(f"TOTAL: RD$ {total:,.2f}")
    lineas.append("="*42)
    lineas.append("  Gracias por su compra en La Fe!")
    lineas.append("  Todo para su construccion")
    lineas.append("="*42)
    return "\n".join(lineas)

def imprimir_factura_html(texto_factura, num_factura):
    html_code = f"""
    <html>
    <head>
        <style>
            @page {{ size: 80mm auto; margin: 2mm; }}
            body {{ font-family: 'Courier New', monospace; width: 72mm; font-size: 12px; line-height: 1.3; margin: 0 auto; background: white; color: black; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 12px; margin: 0; }}
            .btn-print {{ background: #FF6B00; color: white; border: none; padding: 15px 20px; font-size: 18px; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 15px; font-weight: bold; }}
            @media print {{ .btn-print {{ display: none; }} body {{ width: 80mm; }} }}
        </style>
    </head>
    <body>
        <pre>{texto_factura}</pre>
        <button class="btn-print" onclick="window.print()">IMPRIMIR FACTURA {num_factura:06d}</button>
        <p style="text-align:center; font-size:10px;">Ferreteria La Fe - Sistema 606</p>
    </body>
    </html>
    """
    components.html(html_code, height=700, scrolling=True)

def generar_link_whatsapp(numero, cliente, monto, que_llevo, fecha):
    num_limpio = "".join(filter(str.isdigit, str(numero)))
    if len(num_limpio) == 10:
        num_limpio = "1" + num_limpio
    mensaje = f"Hola {cliente},\n\nTe saluda FERRETERIA LA FE de Quisqueya.\n\nTe recordamos que tienes un balance pendiente:\n\nMonto: RD$ {monto:,}\nDetalle: {que_llevo}\nFecha: {fecha}\n\nPor favor pasa por la ferreteria cuando puedas.\n\nGracias por tu compra!\nFerreteria La Fe - 829-264-7574"
    mensaje_encoded = urllib.parse.quote(mensaje)
    link = f"https://wa.me/{num_limpio}?text={mensaje_encoded}"
    return link, num_limpio

with st.sidebar:
    show_logo(150)
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("🔄 Resetear sistema"):
        st.session_state.clear()
        st.rerun()

if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        codigo_escaneado = st.text_input("Pistolea el código aquí", placeholder="Ej: CEM001", key="barcode_scan")
        if st.button("🔎 Buscar Código"):
            inv = st.session_state.inventario
            match = inv[inv["Código"].str.upper().str.strip() == codigo_escaneado.upper().strip()]
            if not match.empty:
                row = match.iloc[0]
                agregar_al_carrito({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio RD$'],"Total":1*row['Precio RD$'],"Código":row['Código']})
                st.rerun()
        st.divider()
        buscador=st.text_input("Busca: cemento, varilla, block...", key="busc_nombre")
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
        cliente_factura = st.text_input("Cliente", value="Cliente Mostrador", key="cliente_fact_pos")
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
        largo=c1.number_input("Largo (m)", 1.0, 100.0, 10.0, key="largo_p")
        alto=c2.number_input("Alto (m)", 1.0, 10.0, 2.5, key="alto_p")
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"], key="tipo_p")
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared", type="primary", key="calc_pared"):
            m2=largo*alto
            blocks=int(m2*12.5)+5; cemento=int(m2*1.15)+1; arena=round(m2*0.08,2); varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + arena*2500 + varilla*420
            detalle_df = pd.DataFrame([
                [f"🧱 {tipo}", blocks, f"RD$ {precio_block}", f"RD$ {blocks*precio_block:,}"],
                ["🏗️ Cemento Panam", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],
                ["🏖️ Arena Lavada", arena, "RD$ 2,500", f"RD$ {int(arena*2500):,}"],
                ["🔩 Varilla 3/8", varilla, "RD$ 420", f"RD$ {varilla*420:,}"],
            ], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"Pared {m2} m2"}
    elif obra=="Zapata (4 zapatas)":
        prof=st.number_input("Profundidad (m)", 0.5, 2.0, 1.0, key="prof_z")
        if st.button("Calcular Zapatas", type="primary", key="calc_zap"):
            total=10*550+16*680+2800+2000
            detalle_df = pd.DataFrame([
                ["🏗️ Cemento", 10, "RD$ 550", "RD$ 5,500"],
                ["🔩 Varilla 1/2", 16, "RD$ 680", "RD$ 10,880"],
                ["🪨 Grava", 1, "RD$ 2,800", "RD$ 2,800"],
                ["🏖️ Arena", 0.8, "RD$ 2,500", "RD$ 2,000"],
            ], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Zapatas 4x {prof}m","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"4 Zapatas {prof}m"}
    elif obra=="Piso 10x10 (100 m2)":
        espesor=st.selectbox("Espesor", ["10cm (estándar)", "15cm (pesado)"], key="esp_piso")
        if st.button("Calcular Piso", type="primary", key="calc_piso"):
            cemento=70 if "10cm" in espesor else 100
            total=cemento*550+7*2500+8*2800
            detalle_df = pd.DataFrame([
                ["🏗️ Cemento", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],
                ["🏖️ Arena", 7, "RD$ 2,500", "RD$ 17,500"],
                ["🪨 Grava", 8, "RD$ 2,800", "RD$ 22,400"],
            ], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Piso 10x10 {espesor}","Icono":"🏖️","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"Piso 100 m2 {espesor}"}
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True, key="calc_casita"):
            detalle_df = pd.DataFrame([
                ["🧱 Block 6''", 112, "RD$ 42", "RD$ 4,704"],
                ["🏗️ Cemento", 15, "RD$ 550", "RD$ 8,250"],
                ["🔩 Varilla 3/8", 20, "RD$ 420", "RD$ 8,400"],
                ["🏖️ Arena", 2, "RD$ 2,500", "RD$ 5,000"],
                ["🪨 Grava", 1.5, "RD$ 2,800", "RD$ 4,200"],
                ["🏠 Zinc 10ft", 6, "RD$ 750", "RD$ 4,500"],
                ["🪢 Alambre", 5, "RD$ 85", "RD$ 425"],
                ["🔨 Clavos", 3, "RD$ 120", "RD$ 360"],
            ], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":"Casita 3x3 Completa","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": 35839, "titulo": "Casita 3x3 Completa"}
    elif obra=="Techo de Zinc 3x3":
        if st.button("Calcular Techo", type="primary", key="calc_techo"):
            total=6*750+2*120+10*400
            detalle_df = pd.DataFrame([
                ["🏠 Zinc 10ft", 6, "RD$ 750", "RD$ 4,500"],
                ["🔨 Clavos", 2, "RD$ 120", "RD$ 240"],
                ["🪵 Cuartones", 10, "RD$ 400", "RD$ 4,000"],
            ], columns=["Material", "Cant. Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":"Techo Zinc 3x3","Icono":"🏠","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": "Techo Zinc 3x3"}

    if st.session_state.calc_detalle:
        st.divider()
        st.subheader(f"📋 Materiales para: {st.session_state.calc_detalle['titulo']}")
        st.dataframe(st.session_state.calc_detalle["df"], use_container_width=True, hide_index=True)
        st.markdown(f"### 💰 TOTAL: RD$ {st.session_state.calc_detalle['total']:,}")
        if st.button("➕ AGREGAR AL CARRITO", type="primary", use_container_width=True, key="add_calc_final_det"):
            agregar_al_carrito(st.session_state.calc_temp)
            st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito")
        for item in st.session_state.carrito:
            st.write(f"{item.get('Icono','')} {item['Producto']} - {item['Cant']} x RD$ {item['Total']:,}")
        subtotal = sum([x['Total'] for x in st.session_state.carrito]); itbis=subtotal*0.18; total=subtotal*1.18
        st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
        cliente_calc = st.text_input("Cliente", value="Cliente Obra", key="cliente_calc_final")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ COBRAR Y FACTURAR - CALCULADORA", type="primary", use_container_width=True, key="cobrar_calc_final_det"):
                num = st.session_state.contador_factura
                texto_fact = generar_texto_factura(cliente_calc, st.session_state.carrito, subtotal, itbis, total, num)
                st.session_state.ultima_factura = {"texto": texto_fact, "cliente": cliente_calc, "total": total, "num": num}
                st.session_state.ventas_hoy+=total
                st.session_state.historial_ventas.append({"Factura": num, "Cliente": cliente_calc, "Total": total, "Fecha": datetime.now().strftime("%H:%M")})
                st.session_state.contador_factura+=1
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
        with col_c2:
            if st.button("🗑️ Vaciar carrito calculadora", use_container_width=True):
                st.session_state.carrito=[]
                st.rerun()

    if st.session_state.ultima_factura:
        st.divider()
        st.markdown(f"### 🧾 Factura No {st.session_state.ultima_factura['num']:06d}")
        st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", key="down_calc_det", use_container_width=True)
        imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado - Con WhatsApp")
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre del cliente *", placeholder="Ej: Juan Perez")
            telefono = st.text_input("WhatsApp *", placeholder="Ej: 829-264-7574")
            monto = st.number_input("Monto RD$ *", min_value=100, max_value=500000, value=5000, step=100)
            fecha = st.date_input("Fecha fiado", value=date.today())
            vence = st.date_input("Fecha promesa de pago", value=date.today())
            nota = st.text_input("Qué se llevó", placeholder="Ej: 10 Cemento, 20 Varilla")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar:
                if cliente == "" or telefono == "":
                    st.error("❌ Pon nombre y WhatsApp")
                else:
                    st.session_state.fiados.append({
                        "Cliente": cliente,
                        "WhatsApp": telefono,
                        "Monto": monto,
                        "Fecha": str(fecha),
                        "Vence": str(vence),
                        "Que llevó": nota,
                        "Estado": "Pendiente"
                    })
                    st.success(f"✅ Fiado de {cliente} guardado")
                    st.balloons()
    with col2:
        st.subheader("📋 Lista de Fiados")
        if st.session_state.fiados:
            total_pendiente = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"])
            st.metric("💰 Total por cobrar", f"RD$ {total_pendiente:,.0f}")
            for i, row in enumerate(st.session_state.fiados):
                with st.container(border=True):
                    c_info, c_ws, c_acc = st.columns([2.5, 1.5, 1])
                    with c_info:
                        estado_color = "🟡" if row.get("Estado")=="Pendiente" else "🟢"
                        st.markdown(f"{estado_color} **{row['Cliente']}** - RD$ {row['Monto']:,}")
                        st.caption(f"📱 {row.get('WhatsApp','Sin número')} | 📦 {row.get('Que llevó','')} | Vence: {row.get('Vence','')}")
                    with c_ws:
                        try:
                            link_ws, num_formateado = generar_link_whatsapp(row.get('WhatsApp',''), row['Cliente'], row['Monto'], row.get('Que llevó','materiales'), row.get('Fecha',''))
                            st.link_button(f"💬 WhatsApp", link_ws, use_container_width=True, type="primary")
                        except:
                            st.write("Sin WhatsApp")
                    with c_acc:
                        if row.get("Estado") == "Pendiente":
                            if st.button("✅ Cobrado", key=f"cob_{i}", use_container_width=True):
                                st.session_state.fiados[i]["Estado"] = "Pagado"
                                st.success("Cobrado!")
                                st.rerun()
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            st.session_state.fiados.pop(i)
                            st.rerun()
            st.divider()
            st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)
        else:
            st.info("📭 No hay fiados aún.")

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja - Ferretería La Fe")
    ventas = st.session_state.ventas_hoy
    fiados_total = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}")
    with col2: st.metric("📓 Fiado", f"RD$ {fiados_total:,.0f}")
    with col3: st.metric("📈 Total Día", f"RD$ {ventas+fiados_total:,.0f}")
    with col4: st.metric("🧱 Productos", f"{len(st.session_state.inventario)} tipos")
    st.divider()
    c_izq, c_der = st.columns([1.1, 1.4])
    with c_izq:
        st.subheader("💰 Cuadre de Caja")
        st.info(f"Sistema dice: RD$ {ventas:,.2f}")
        efectivo_fisico = st.number_input("Efectivo FÍSICO en caja", min_value=0.0, value=float(ventas), step=100.0, key="efectivo_fisico")
        diferencia = efectivo_fisico - ventas
        if ventas>0:
            if diferencia==0:
                st.success(f"✅ CUADRE PERFECTO RD$ {efectivo_fisico:,.2f}")
                st.balloons()
            elif diferencia>0:
                st.warning(f"⚠️ SOBRA RD$ {diferencia:,.2f}")
            else:
                st.error(f"❌ FALTA RD$ {abs(diferencia):,.2f}")
        if st.session_state.historial_ventas:
            st.subheader("📋 Ventas de Hoy")
            st.dataframe(pd.DataFrame(st.session_state.historial_ventas), use_container_width=True)
        if st.button("🔒 Cerrar Día", type="primary", use_container_width=True):
            st.session_state.ventas_hoy=0
            st.session_state.historial_ventas=[]
            st.rerun()
        st.divider()
        st.subheader("⚠️ Stock Bajo")
        bajo = st.session_state.inventario[st.session_state.inventario["Stock"] < 50]
        critico = st.session_state.inventario[st.session_state.inventario["Stock"] < 20]
        if not critico.empty:
            st.error(f"🚨 CRÍTICO <20: {len(critico)} productos")
            st.dataframe(critico[["Código","Producto","Stock"]], use_container_width=True)
        elif not bajo.empty:
            st.warning(f"⚠️ Bajo <50: {len(bajo)} productos")
            st.dataframe(bajo[["Código","Producto","Stock"]], use_container_width=True)
        else:
            st.success("✅ Stock bien")
    with c_der:
        st.subheader("📦 Inventario Editable")
        st.caption("EDITA el stock cuando te llega mercancía. Doble click en el número.")
        df_editable = st.data_editor(
            st.session_state.inventario[["Código","Producto","Stock","Precio RD$"]],
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Stock": st.column_config.NumberColumn("Stock EDITABLE", min_value=0, max_value=10000, step=1, format="%d"),
                "Precio RD$": st.column_config.NumberColumn("Precio RD$", min_value=0, format="RD$ %d"),
            },
            key="editor_stock"
        )
        if st.button("💾 Guardar cambios de Stock", type="primary", use_container_width=True):
            for idx, row in df_editable.iterrows():
                codigo = row["Código"]
                real_idx = st.session_state.inventario[st.session_state.inventario["Código"]==codigo].index
                if not real_idx.empty:
                    st.session_state.inventario.loc[real_idx, "Stock"] = row["Stock"]
                    st.session_state.inventario.loc[real_idx, "Precio RD$"] = row["Precio RD$"]
            st.success("✅ Stock actualizado!")
            st.rerun()
        st.divider()
        st.subheader("➕ Entrada Rápida - Llegó camión")
        c_fast1, c_fast2, c_fast3 = st.columns([2,1,1])
        with c_fast1:
            prod_entrada = st.selectbox("Producto que llegó", st.session_state.inventario["Producto"].tolist(), key="prod_entrada")
        with c_fast2:
            cant_entrada = st.number_input("Cantidad que llegó", min_value=1, max_value=1000, value=10, key="cant_entrada")
        with c_fast3:
            st.write("")
            if st.button("➕ Sumar", use_container_width=True, type="primary"):
                idx = st.session_state.inventario[st.session_state.inventario["Producto"]==prod_entrada].index
                if not idx.empty:
                    st.session_state.inventario.loc[idx, "Stock"] += cant_entrada
                    st.success(f"✅ Sumaste {cant_entrada} a {prod_entrada}")
                    st.rerun()
        st.divider()
        valor_inv = (st.session_state.inventario["Stock"] * st.session_state.inventario["Precio RD$"]).sum()
        st.metric("💰 Valor Total Inventario", f"RD$ {valor_inv:,.0f}")
