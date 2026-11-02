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
    st.caption("Quisqueya, SPM | POS 606 + Factura + Cierre Completo")

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
if 'historial_ventas' not in st.session_state: st.session_state.historial_ventas=[]

def generar_texto_factura(cliente, carrito, subtotal, itbis, total, num_factura):
    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    lineas = []
    lineas.append("="*42)
    lineas.append("      FERRETERIA LA FE - QUISQUEYA")
    lineas.append("      San Pedro de Macoris, RD")
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
        if st.session_state.ultima_factura:
            st.code(st.session_state.ultima_factura["texto"])
            st.download_button("📥 Descargar Factura", st.session_state.ultima_factura["texto"], file_name=f"FACTURA_{st.session_state.ultima_factura['num']:06d}.txt")

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
            st.session_state.calc_temp = {"Producto":f"Pared {m2}m2 {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": f"{m2}m2"}
    elif obra=="Zapata (4 zapatas)":
        prof=st.number_input("Profundidad (m)", 0.5, 2.0, 1.0, key="prof_z")
        if st.button("Calcular Zapatas", type="primary", key="calc_zap"):
            total=10*550+16*420+1*2800+0.8*2500
            st.session_state.calc_temp = {"Producto":f"Zapatas 4x {prof}m","Icono":"🏗️","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": "Zapatas"}
    elif obra=="Piso 10x10 (100 m2)":
        espesor=st.selectbox("Espesor", ["10cm (estándar)", "15cm (pesado)"], key="esp_piso")
        if st.button("Calcular Piso", type="primary", key="calc_piso"):
            cemento=70 if "10cm" in espesor else 100
            total=cemento*550+7*2500+8*2800
            st.session_state.calc_temp = {"Producto":f"Piso 10x10 {espesor}","Icono":"🏖️","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": "Piso"}
    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True, key="calc_casita"):
            st.session_state.calc_temp = {"Producto":"Casita 3x3 Completa - Materiales Completos","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839,"Código":"", "detalle": "Casita 3x3"}
    elif obra=="Techo de Zinc 3x3":
        if st.button("Calcular Techo", type="primary", key="calc_techo"):
            total=6*750+2*120+10*400
            st.session_state.calc_temp = {"Producto":f"Techo Zinc 3x3","Icono":"🏠","Cant":1,"Precio":total,"Total":total,"Código":"", "detalle": "Techo"}

    if st.session_state.calc_temp:
        st.success(f"✅ Cotización: {st.session_state.calc_temp['Producto']} - RD$ {st.session_state.calc_temp['Total']:,}")
        if st.button("➕ AGREGAR AL CARRITO", type="primary", use_container_width=True, key="add_calc_final"):
            st.session_state.carrito.append(st.session_state.calc_temp)
            st.session_state.calc_temp=None
            st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito")
        for item in st.session_state.carrito:
            st.write(f"{item.get('Icono','')} {item['Producto']} - RD$ {item['Total']:,}")
        subtotal = sum([x['Total'] for x in st.session_state.carrito]); total=subtotal*1.18
        st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
        cliente_calc = st.text_input("Cliente", value="Cliente Obra", key="cliente_calc_final")
        if st.button("✅ COBRAR Y FACTURAR - CALCULADORA", type="primary", use_container_width=True, key="cobrar_calc_final"):
            num = st.session_state.contador_factura
            texto_fact = generar_texto_factura(cliente_calc, st.session_state.carrito, subtotal, subtotal*0.18, total, num)
            st.session_state.ultima_factura = {"texto": texto_fact, "cliente": cliente_calc, "total": total, "num": num}
            st.session_state.ventas_hoy+=total
            st.session_state.historial_ventas.append({"Factura": num, "Cliente": cliente_calc, "Total": total, "Fecha": datetime.now().strftime("%H:%M")})
            st.session_state.contador_factura+=1
            st.session_state.carrito=[]
            st.balloons()
            st.rerun()
    if st.session_state.ultima_factura:
        st.code(st.session_state.ultima_factura["texto"])

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado")
    col1, col2 = st.columns([1,2])
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre cliente")
            telefono = st.text_input("Teléfono")
            monto = st.number_input("Monto RD$", min_value=100, max_value=500000, value=5000, step=100)
            nota = st.text_input("Qué se llevó")
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar and cliente:
                st.session_state.fiados.append({"Cliente": cliente,"Tel": telefono,"Monto": monto,"Que llevó": nota,"Estado": "Pendiente"})
                st.success(f"✅ Fiado de {cliente} guardado")
    with col2:
        if st.session_state.fiados:
            st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)

# --- CIERRE COMPLETO PROFESIONAL - CON CUADRE, STOCK, INVENTARIO ---
elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja - Ferretería La Fe")
    st.caption(f"Fecha: {datetime.now().strftime('%d/%m/%Y %I:%M %p')} | Quisqueya, SPM")

    ventas = st.session_state.ventas_hoy
    fiados_total = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    total_dia = ventas + fiados_total
    num_facturas = len(st.session_state.historial_ventas)

    # METRICAS ARRIBA
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💵 Efectivo Hoy", f"RD$ {ventas:,.0f}", f"{num_facturas} facturas")
    with col2: st.metric("📓 Fiado por Cobrar", f"RD$ {fiados_total:,.0f}")
    with col3: st.metric("📈 Total Día", f"RD$ {total_dia:,.0f}")
    with col4: st.metric("🧱 Tipos Productos", f"{len(st.session_state.inventario)}")

    st.divider()

    c_izq, c_der = st.columns([1.2, 1])

    with c_izq:
        st.subheader("💰 Cuadre de Caja - ¿Cuadra o no cuadra?")
        st.info(f"Sistema dice que vendiste: **RD$ {ventas:,.2f}** en efectivo")
        
        efectivo_fisico = st.number_input("¿Cuánto efectivo hay FÍSICO en la caja? (cuenta los billetes)", min_value=0.0, value=float(ventas), step=100.0, key="efectivo_fisico")
        
        diferencia = efectivo_fisico - ventas
        
        if ventas == 0:
            st.warning("Aún no hay ventas hoy. Haz una venta en Punto de Venta.")
        else:
            if diferencia == 0:
                st.success(f"✅ ¡CUADRE PERFECTO! RD$ {efectivo_fisico:,.2f} - Todo cuadra nítido")
                st.balloons()
            elif diferencia > 0:
                st.warning(f"⚠️ SOBRA DINERO: RD$ {diferencia:,.2f} - Hay RD$ {diferencia:,.0f} de más en caja (¿propina o error?)")
            else:
                st.error(f"❌ FALTA DINERO: RD$ {abs(diferencia):,.2f} - Faltan RD$ {abs(diferencia):,.0f} en caja")

        st.divider()
        st.subheader("📋 Historial de Ventas de Hoy")
        if st.session_state.historial_ventas:
            df_hist = pd.DataFrame(st.session_state.historial_ventas)
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("No hay ventas aún hoy")

        if st.button("🔒 Cerrar Día - Poner en 0", type="primary", use_container_width=True):
            st.session_state.ventas_hoy = 0
            st.session_state.historial_ventas = []
            st.success("Día cerrado. Caja en 0 para mañana")
            st.rerun()

    with c_der:
        st.subheader("⚠️ Alerta Stock Bajo - ¡Pedir!")
        # Stock bajo < 50
        bajo = st.session_state.inventario[st.session_state.inventario["Stock"] < 50].copy()
        # Stock critico < 20
        critico = st.session_state.inventario[st.session_state.inventario["Stock"] < 20].copy()
        
        if not critico.empty:
            st.error(f"🚨 CRÍTICO: {len(critico)} productos con menos de 20 unidades")
            st.dataframe(critico[["Código","Producto","Stock"]], use_container_width=True)
        elif not bajo.empty:
            st.warning(f"⚠️ {len(bajo)} productos con stock bajo (<50)")
            st.dataframe(bajo[["Código","Producto","Stock","Precio RD$"]], use_container_width=True)
        else:
            st.success("✅ Todo el stock está bien - No hay productos bajos")

        st.divider()
        st.subheader("📦 Inventario Completo Actual")
        st.dataframe(st.session_state.inventario[["Código","Producto","Stock","Precio RD$","Cat"]], use_container_width=True, height=400)
        
        # Valor inventario
        st.session_state.inventario["Valor Total"] = st.session_state.inventario["Stock"] * st.session_state.inventario["Precio RD$"]
        valor_inv = st.session_state.inventario["Valor Total"].sum()
        st.metric("💰 Valor Total Inventario", f"RD$ {valor_inv:,.0f}")
        
        if st.button("📥 Descargar Inventario Excel"):
            st.download_button("Descargar CSV", st.session_state.inventario.to_csv(index=False), file_name=f"inventario_la_fe_{date.today()}.csv", mime="text/csv")
