import streamlit as st
import pandas as pd
from datetime import date, datetime

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
    st.caption("Quisqueya, SPM | POS 606 + Calculadora Detallada + Factura + Cierre")

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
    lineas.append("      Tel: 829-264-7574")
    lineas.append("="*42)
    lineas.append(f"FACTURA No: {num_factura:06d}")
    lineas.append(f"FECHA: {fecha}")
    lineas.append(f"CLIENTE: {cliente}")
    lineas.append("-"*42)
    for item in carrito:
        lineas.append(f"{item['Cant']} x {item['Producto'][:24]} RD${item['Total']}")
    lineas.append("-"*42)
    lineas.append(f"SUBTOTAL: RD$ {subtotal:,.2f}")
    lineas.append(f"ITBIS 18%: RD$ {itbis:,.2f}")
    lineas.append(f"TOTAL: RD$ {total:,.2f}")
    lineas.append("="*42)
    return "\n".join(lineas)

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
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
        if st.session_state.ultima_factura:
            st.code(st.session_state.ultima_factura["texto"])
            st.download_button("📥 Descargar Factura", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt")

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo - Stock Actual")
    st.dataframe(st.session_state.inventario[["Código","Producto","Precio RD$","Stock","Cat"]], use_container_width=True)

# --- CALCULADORA DETALLADA CON DESGLOSE POR MATERIAL ---
elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora Inteligente La Fe")
    st.caption("Calcula exacto con desglose de cada material")
    obra=st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Zapata (4 zapatas)", "Piso 10x10 (100 m2)", "Casita 3x3 Completa", "Techo de Zinc 3x3"])
    
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo pared (metros)", 1.0, 100.0, 10.0, key="largo_p")
        alto=c2.number_input("Alto pared (metros)", 1.0, 10.0, 2.5, key="alto_p")
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"], key="tipo_p")
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        codigo_block = "BLK06" if "6''" in tipo else ("BLK04" if "4''" in tipo else "BLK08")
        if st.button("Calcular Pared", type="primary", key="calc_pared"):
            m2=largo*alto
            blocks=int(m2*12.5)+5
            cemento=int(m2*1.15)+1
            arena=round(m2*0.08,2)
            varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + arena*2500 + varilla*420
            # Detalle con tabla
            detalle_df = pd.DataFrame([
                [f"🧱 {tipo}", blocks, f"RD$ {precio_block}", f"RD$ {blocks*precio_block:,}"],
                ["🏗️ Cemento Panam 94lbs", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],
                ["🏖️ Arena Lavada m3", arena, "RD$ 2,500", f"RD$ {int(arena*2500):,}"],
                ["🔩 Varilla 3/8 x 20", varilla, "RD$ 420", f"RD$ {varilla*420:,}"],
            ], columns=["Material", "Cantidad Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 - {blocks} Blocks {tipo}","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "m2": m2, "titulo": f"Pared {m2} m2 ({largo}m x {alto}m)"}

    elif obra=="Zapata (4 zapatas)":
        prof=st.number_input("Profundidad (m)", 0.5, 2.0, 1.0, key="prof_z")
        if st.button("Calcular Zapatas", type="primary", key="calc_zap"):
            cemento=10; varilla=16; grava=1.0; arena=0.8
            total=cemento*550 + varilla*680 + int(grava*2800) + int(arena*2500)
            detalle_df = pd.DataFrame([
                ["🏗️ Cemento Panam 94lbs", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],
                ["🔩 Varilla 1/2 x 20", varilla, "RD$ 680", f"RD$ {varilla*680:,}"],
                ["🪨 Grava m3", grava, "RD$ 2,800", f"RD$ {int(grava*2800):,}"],
                ["🏖️ Arena Lavada m3", arena, "RD$ 2,500", f"RD$ {int(arena*2500):,}"],
            ], columns=["Material", "Cantidad Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Zapatas 4x {prof}m","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"4 Zapatas {prof}m profundidad"}

    elif obra=="Piso 10x10 (100 m2)":
        espesor=st.selectbox("Espesor", ["10cm (estándar)", "15cm (pesado)"], key="esp_piso")
        if st.button("Calcular Piso", type="primary", key="calc_piso"):
            cemento=70 if "10cm" in espesor else 100; arena=7; grava=8
            total=cemento*550 + arena*2500 + grava*2800
            detalle_df = pd.DataFrame([
                ["🏗️ Cemento Panam 94lbs", cemento, "RD$ 550", f"RD$ {cemento*550:,}"],
                ["🏖️ Arena Lavada m3", arena, "RD$ 2,500", f"RD$ {arena*2500:,}"],
                ["🪨 Grava m3", grava, "RD$ 2,800", f"RD$ {grava*2800:,}"],
            ], columns=["Material", "Cantidad Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Piso 10x10 {espesor}","Icono":"🏖️","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": f"Piso 10x10 = 100 m2 - {espesor}"}

    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True, key="calc_casita"):
            detalle_df = pd.DataFrame([
                ["🧱 Block 6''", 112, "RD$ 42", "RD$ 4,704"],
                ["🏗️ Cemento Panam 94lbs", 15, "RD$ 550", "RD$ 8,250"],
                ["🔩 Varilla 3/8 x 20", 20, "RD$ 420", "RD$ 8,400"],
                ["🏖️ Arena Lavada m3", 2, "RD$ 2,500", "RD$ 5,000"],
                ["🪨 Grava m3", 1.5, "RD$ 2,800", "RD$ 4,200"],
                ["🏠 Zinc Acanalado 10ft", 6, "RD$ 750", "RD$ 4,500"],
                ["🪢 Alambre Dulce lb", 5, "RD$ 85", "RD$ 425"],
                ["🔨 Clavo 2 1/2 lb", 3, "RD$ 120", "RD$ 360"],
            ], columns=["Material", "Cantidad Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":"Casita 3x3 Completa - Materiales Completos","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": 35839, "titulo": "Casita 3x3 (9 m2) Completa"}

    elif obra=="Techo de Zinc 3x3":
        if st.button("Calcular Techo", type="primary", key="calc_techo"):
            zinc=6; clavos=2; madera=10
            total=zinc*750 + clavos*120 + madera*400
            detalle_df = pd.DataFrame([
                ["🏠 Zinc Acanalado 10ft", zinc, "RD$ 750", f"RD$ {zinc*750:,}"],
                ["🔨 Clavo 2 1/2 lb", clavos, "RD$ 120", f"RD$ {clavos*120:,}"],
                ["🪵 Cuartones Madera", madera, "RD$ 400", f"RD$ {madera*400:,}"],
            ], columns=["Material", "Cantidad Necesaria", "Precio Unit.", "Subtotal"])
            st.session_state.calc_temp = {"Producto":f"Techo Zinc 3x3 {zinc} laminas","Icono":"🏠","Cant":1,"Precio":total,"Total":total,"Código":""}
            st.session_state.calc_detalle = {"df": detalle_df, "total": total, "titulo": "Techo de Zinc 3x3"}

    # MOSTRAR DESGLOSE DETALLADO
    if st.session_state.calc_detalle:
        st.divider()
        st.subheader(f"📋 Materiales necesarios para: {st.session_state.calc_detalle['titulo']}")
        st.dataframe(st.session_state.calc_detalle["df"], use_container_width=True, hide_index=True)
        st.markdown(f"### 💰 TOTAL MATERIALES: RD$ {st.session_state.calc_detalle['total']:,}")
        st.caption("Precios reales Ferretería La Fe - Quisqueya")
        
        col_add1, col_add2 = st.columns([2,1])
        with col_add1:
            if st.button("➕ AGREGAR ESTA COTIZACIÓN COMPLETA AL CARRITO", type="primary", use_container_width=True, key="add_calc_final_det"):
                st.session_state.carrito.append(st.session_state.calc_temp)
                st.success("✅ ¡Cotización agregada! Baja para cobrar y facturar")
                st.rerun()
        with col_add2:
            if st.button("🗑️ Limpiar Cálculo", key="clear_calc"):
                st.session_state.calc_temp=None
                st.session_state.calc_detalle=None
                st.rerun()

    # CARRITO Y FACTURA EN CALCULADORA
    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito Actual - Listo para cobrar")
        for item in st.session_state.carrito:
            st.write(f"{item.get('Icono','')} {item['Producto']} - RD$ {item['Total']:,}")
        subtotal = sum([x['Total'] for x in st.session_state.carrito])
        itbis = subtotal * 0.18
        total = subtotal * 1.18
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write(f"Subtotal: RD$ {subtotal:,.2f}")
            st.write(f"ITBIS 18%: RD$ {itbis:,.2f}")
            st.metric("TOTAL A COBRAR", f"RD$ {total:,.2f}")
        with col_t2:
            cliente_calc = st.text_input("Cliente para factura", value="Cliente Obra", key="cliente_calc_final")
            if st.button("✅ COBRAR Y GENERAR FACTURA - CALCULADORA", type="primary", use_container_width=True, key="cobrar_calc_final_det"):
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
        st.markdown("### 🧾 Ultima Factura Generada")
        st.code(st.session_state.ultima_factura["texto"])
        st.download_button("📥 Descargar Factura", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", key="down_calc_final_det")

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado")
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre cliente")
            monto = st.number_input("Monto RD$", min_value=100, max_value=500000, value=5000, step=100)
            nota = st.text_input("Qué se llevó")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar and cliente:
                st.session_state.fiados.append({"Cliente": cliente,"Monto": monto,"Que llevó": nota,"Estado": "Pendiente"})
                st.success(f"✅ Fiado de {cliente} guardado")
    with col2:
        if st.session_state.fiados:
            st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja - Ferretería La Fe")
    ventas = st.session_state.ventas_hoy
    fiados_total = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    total_dia = ventas + fiados_total

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}")
    with col2: st.metric("📓 Fiado", f"RD$ {fiados_total:,.0f}")
    with col3: st.metric("📈 Total Día", f"RD$ {total_dia:,.0f}")
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
        critico = st.session_state.inventario[st.session_state.inventario["Stock"] < 20]
        if not critico.empty:
            st.error(f"🚨 CRÍTICO <20: {len(critico)} productos")
            st.dataframe(critico[["Código","Producto","Stock"]], use_container_width=True)
        elif not bajo.empty:
            st.warning(f"⚠️ Bajo <50: {len(bajo)} productos")
            st.dataframe(bajo[["Código","Producto","Stock"]], use_container_width=True)
        else:
            st.success("✅ Stock bien")
        st.divider()
        st.subheader("📦 Inventario Completo")
        st.dataframe(st.session_state.inventario[["Código","Producto","Stock","Precio RD$"]], use_container_width=True)
        valor_inv = (st.session_state.inventario["Stock"] * st.session_state.inventario["Precio RD$"]).sum()
        st.metric("Valor Inventario", f"RD$ {valor_inv:,.0f}")
