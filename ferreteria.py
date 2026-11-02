import streamlit as st
import pandas as pd
from datetime import date, datetime
import streamlit.components.v1 as components

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
    st.caption("Quisqueya, SPM | POS 606 + Factura Imprimible 80mm")

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
        lineas.append(f"{item['Cant']} x {item['Producto'][:24]}")
        lineas.append(f"         RD$ {item['Total']:,}")
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
    # HTML para impresora 80mm
    html_code = f"""
    <html>
    <head>
        <style>
            @page {{ size: 80mm auto; margin: 2mm; }}
            body {{ font-family: 'Courier New', monospace; width: 72mm; font-size: 12px; line-height: 1.2; margin: 0 auto; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 11px; }}
            .btn-print {{ background: #FF6B00; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 10px; font-weight: bold; }}
            .btn-print:hover {{ background: #e55a00; }}
            @media print {{ .btn-print {{ display: none; }} body {{ width: 80mm; }} }}
        </style>
    </head>
    <body>
        <pre>{texto_factura}</pre>
        <button class="btn-print" onclick="window.print()">🖨️ IMPRIMIR FACTURA {num_factura:06d} - 80mm</button>
        <script>
            // Auto imprimir si se quiere
            // window.print();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=650, scrolling=True)

with st.sidebar:
    show_logo(150)
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("🔄 Resetear sistema"):
        st.session_state.clear()
        st.rerun()

# --- PUNTO DE VENTA ---
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
                st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":1,"Precio":row['Precio RD$'],"Total":1*row['Precio RD$'],"Código":row['Código']})
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
                        st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                        st.rerun()
    with c2:
        st.subheader("Factura")
        cliente_factura = st.text_input("Cliente", value="Cliente Mostrador", key="cliente_fact_pos")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                st.write(f"{item.get('Icono','')} {item['Producto'][:22]} - RD$ {item['Total']:,}")
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
        # FACTURA CON BOTON IMPRIMIR
        if st.session_state.ultima_factura:
            st.divider()
            st.markdown(f"### 🧾 Factura No {st.session_state.ultima_factura['num']:06d}")
            col_imp1, col_imp2 = st.columns(2)
            with col_imp1:
                st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", use_container_width=True)
            with col_imp2:
                st.write("Abajo está para imprimir:")
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
            st.session_state.carrito.append(st.session_state.calc_temp)
            st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito")
        for item in st.session_state.carrito:
            st.write(f"{item.get('Icono','')} {item['Producto']} - RD$ {item['Total']:,}")
        subtotal = sum([x['Total'] for x in st.session_state.carrito]); itbis=subtotal*0.18; total=subtotal*1.18
        st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
        cliente_calc = st.text_input("Cliente", value="Cliente Obra", key="cliente_calc_final")
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

    if st.session_state.ultima_factura:
        st.divider()
        st.markdown(f"### 🧾 Factura No {st.session_state.ultima_factura['num']:06d}")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 Descargar TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", key="down_calc_det")
        with col_d2:
            st.caption("Usa el botón naranja abajo para imprimir en 80mm")
        imprimir_factura_html(st.session_state.ultima_factura["texto"], st.session_state.ultima_factura["num"])

elif menu=="📓 Fiado":
    st.title("📓 Fiado")
    col1, col2 = st.columns([1,2])
    with col1:
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre cliente")
            monto = st.number_input("Monto RD$", min_value=100, max_value=500000, value=5000, step=100)
            nota = st.text_input("Qué se llevó")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary")
            if guardar and cliente:
                st.session_state.fiados.append({"Cliente": cliente,"Monto": monto,"Que llevó": nota,"Estado": "Pendiente"})
                st.success("Guardado")
    with col2:
        if st.session_state.fiados:
            st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)

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
    c_izq, c_der = st.columns([1.2, 1])
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
            st.dataframe(pd.DataFrame(st.session_state.historial_ventas), use_container_width=True)
        if st.button("🔒 Cerrar Día", type="primary"):
            st.session_state.ventas_hoy=0
            st.session_state.historial_ventas=[]
            st.rerun()
    with c_der:
        st.subheader("⚠️ Stock Bajo")
        bajo = st.session_state.inventario[st.session_state.inventario["Stock"] < 50]
        if not bajo.empty:
            st.dataframe(bajo[["Código","Producto","Stock"]], use_container_width=True)
        st.subheader("📦 Inventario Completo")
        st.dataframe(st.session_state.inventario[["Código","Producto","Stock","Precio RD$"]], use_container_width=True)
        valor_inv = (st.session_state.inventario["Stock"] * st.session_state.inventario["Precio RD$"]).sum()
        st.metric("Valor Inventario", f"RD$ {valor_inv:,.0f}")
