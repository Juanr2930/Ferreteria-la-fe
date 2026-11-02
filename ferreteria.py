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
    st.caption("Quisqueya, SPM | Calculadora + Lector 606 + Factura")

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
                st.success(f"✅ {row['Producto']} agregado")
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
                st.session_state.contador_factura+=1
                st.session_state.carrito=[]
                st.balloons()
                st.rerun()
        if st.session_state.ultima_factura:
            st.code(st.session_state.ultima_factura["texto"])
            st.download_button("📥 Descargar Factura", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt")

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo")
    cols=st.columns(3)
    for i, (idx,row) in enumerate(st.session_state.inventario.iterrows()):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f"**{row['Producto']}**")
                st.code(f"{row['Código']}")
                st.metric("Precio", f"RD$ {row['Precio RD$']}")

# --- CALCULADORA ARREGLADA 100% - AHORA SI VA AL CARRITO ---
elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora Inteligente La Fe - ARREGLADA")
    obra=st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Zapata (4 zapatas)", "Piso 10x10 (100 m2)", "Casita 3x3 Completa", "Techo de Zinc 3x3"])
    
    # --- PARED ---
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo pared (metros)", 1.0, 100.0, 10.0, key="largo_p")
        alto=c2.number_input("Alto pared (metros)", 1.0, 10.0, 2.5, key="alto_p")
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"], key="tipo_p")
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        if st.button("Calcular Pared", type="primary", key="calc_pared"):
            m2=largo*alto
            blocks=int(m2*12.5) + 5
            cemento=int(m2*1.15) + 1
            arena=round(m2*0.08, 2)
            varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + arena*2500 + varilla*420
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 - {blocks} Blocks {tipo} - {cemento} Cem - {arena}m3 Arena - {varilla} Var","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": f"{m2}m2: {blocks} Blocks, {cemento} Cemento, {arena} Arena, {varilla} Varilla"}
    
    # --- ZAPATA ---
    elif obra=="Zapata (4 zapatas)":
        prof=st.number_input("Profundidad (m)", 0.5, 2.0, 1.0, key="prof_z")
        if st.button("Calcular Zapatas", type="primary", key="calc_zap"):
            cemento=10; varilla=16; grava=1.0; arena=0.8
            total=cemento*550 + varilla*420 + grava*2800 + arena*2500
            st.session_state.calc_temp = {"Producto":f"Zapatas 4x {prof}m - {cemento} Cem {varilla} Var","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": f"4 zapatas {prof}m"}

    # --- PISO ---
    elif obra=="Piso 10x10 (100 m2)":
        espesor=st.selectbox("Espesor", ["10cm (estándar)", "15cm (pesado)"], key="esp_piso")
        if st.button("Calcular Piso", type="primary", key="calc_piso"):
            cemento=70 if "10cm" in espesor else 100; arena=7; grava=8
            total=cemento*550 + arena*2500 + grava*2800
            st.session_state.calc_temp = {"Producto":f"Piso 10x10 {espesor} - {cemento} Cem","Icono":"🏖️","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": f"Piso 100m2 {espesor}"}

    # --- CASITA ---
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True, key="calc_casita"):
            st.session_state.calc_temp = {"Producto":"Casita 3x3 Completa - Materiales Completos","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":"", "detalle": "Casita 3x3: 112 Blocks, 15 Cemento, 20 Varilla, Arena, Grava, Zinc"}

    # --- TECHO ---
    elif obra=="Techo de Zinc 3x3":
        if st.button("Calcular Techo", type="primary", key="calc_techo"):
            zinc=6; clavos=2; madera=10
            total=zinc*750 + clavos*120 + madera*400
            st.session_state.calc_temp = {"Producto":f"Techo Zinc 3x3 - {zinc} Zinc 10ft","Icono":"🏠","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": f"Techo 3x3 {zinc} laminas"}

    # --- MOSTRAR RESULTADO Y BOTON DE AGREGAR (FUERA DEL IF DE CALCULAR - ASI SI FUNCIONA) ---
    if st.session_state.calc_temp:
        st.divider()
        st.success(f"✅ Cotización lista: {st.session_state.calc_temp['detalle']}")
        st.markdown(f"### TOTAL: RD$ {st.session_state.calc_temp['Total']:,}")
        if st.button("➕ AGREGAR ESTA COTIZACIÓN AL CARRITO", type="primary", use_container_width=True, key="add_calc_final"):
            st.session_state.carrito.append(st.session_state.calc_temp)
            st.session_state.calc_temp = None
            st.success("✅ ¡Agregado al carrito! Baja para cobrar")
            st.rerun()

    # --- CARRITO Y FACTURA EN LA CALCULADORA ---
    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito Actual")
        for item in st.session_state.carrito:
            st.write(f"{item.get('Icono','')} {item['Producto']} - RD$ {item['Total']:,}")
        subtotal = sum([x['Total'] for x in st.session_state.carrito])
        itbis = subtotal * 0.18
        total = subtotal * 1.18
        st.metric("TOTAL + ITBIS 18%", f"RD$ {total:,.2f}")
        cliente_calc = st.text_input("Cliente para factura", value="Cliente Obra", key="cliente_calc_obra_final")
        if st.button("✅ COBRAR Y GENERAR FACTURA - CALCULADORA", type="primary", use_container_width=True, key="cobrar_calc_final"):
            num = st.session_state.contador_factura
            texto_fact = generar_texto_factura(cliente_calc, st.session_state.carrito, subtotal, itbis, total, num)
            st.session_state.ultima_factura = {"texto": texto_fact, "cliente": cliente_calc, "total": total, "num": num}
            st.session_state.ventas_hoy+=total
            st.session_state.contador_factura+=1
            st.session_state.carrito=[]
            st.balloons()
            st.success(f"Factura No {num:06d} generada RD$ {total:,.2f}")
            st.rerun()

    if st.session_state.ultima_factura:
        st.divider()
        st.markdown("### 🧾 Ultima Factura")
        st.code(st.session_state.ultima_factura["texto"])
        st.download_button("📥 Descargar Factura TXT", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt", key="down_calc_final")

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado")
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre del cliente")
            telefono = st.text_input("Teléfono")
            monto = st.number_input("Monto RD$", min_value=100, max_value=500000, value=5000, step=100)
            fecha = st.date_input("Fecha fiado", value=date.today())
            vence = st.date_input("Promesa de pago", value=date.today())
            nota = st.text_input("Qué se llevó")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar and cliente:
                st.session_state.fiados.append({"Cliente": cliente,"Tel": telefono,"Monto": monto,"Fecha": str(fecha),"Vence": str(vence),"Que llevó": nota,"Estado": "Pendiente"})
                st.success(f"✅ Fiado de {cliente} guardado")
    with col2:
        if st.session_state.fiados:
            df = pd.DataFrame(st.session_state.fiados)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📭 No hay fiados aún.")

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja")
    ventas = st.session_state.ventas_hoy
    st.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}")
    if st.button("🔒 Cerrar Día", type="primary"):
        st.session_state.ventas_hoy = 0
        st.rerun()
