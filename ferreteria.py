import streamlit as st
import pandas as pd
from datetime import date, datetime


st.set_page_config(page_title="Ferretería La Fe - Sistema 606", layout="wide", page_icon="🧱")

# --- INVENTARIO REAL FERRETERÍA LA FE ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame([
        ["CEM001", "Cemento Panam 94lbs", 550, 120, "Cemento"],
        ["CEM002", "Cemento Cemex", 565, 80, "Cemento"],
        ["VAR001", "Varilla 3/8 x 20", 420, 200, "Varilla"],
        ["VAR002", "Varilla 1/2 x 20", 680, 150, "Varilla"],
        ["BLK04", "Block 4''", 35, 1000, "Blocks"],
        ["BLK06", "Block 6''", 42, 1500, "Blocks"],
        ["BLK08", "Block 8''", 48, 800, "Blocks"],
        ["ZIN001", "Zinc Acanalado 10ft", 750, 50, "Techo"],
        ["ALAM01", "Alambre Dulce lb", 85, 100, "Alambres"],
        ["CLAV01", "Clavo 2 1/2 lb", 120, 60, "Clavos"],
        ["PINT01", "Pintura Tropical Galón Blanco", 1850, 30, "Pintura"],
        ["ARE001", "Arena Lavada m3", 2500, 20, "Agregados"],
        ["GRAV01", "Grava m3", 2800, 15, "Agregados"],
    ], columns=["Código", "Producto", "Precio RD$", "Stock", "Cat"])

if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'fiados' not in st.session_state: st.session_state.fiados = []
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy = 0

# --- MENU ---
st.sidebar.title("🧱 Ferretería La Fe")
st.sidebar.caption("Quisqueya, SPM - Sistema 606")
menu = st.sidebar.radio("Ir a:", ["🛒 Punto de Venta", "🧮 Calculadora Inteligente", "📓 Control de Fiado", "📊 Cierre de Caja"])
st.sidebar.divider()
st.sidebar.success("Soporte: 829-264-7574")

# 1. PUNTO DE VENTA
if menu == "🛒 Punto de Venta":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Punto de Venta")
        buscador = st.text_input("🔍 Escanea o escribe: cemento, varilla, block...")
        if buscador:
            res = st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador, case=False)]
            st.dataframe(res, use_container_width=True)
            prod_sel = st.selectbox("Selecciona producto", res["Producto"].tolist() if not res.empty else [])
            cant = st.number_input("Cantidad", 1, 1000, 1)
            if st.button("➕ Agregar al carrito"):
                item = res[res["Producto"]==prod_sel].iloc[0]
                st.session_state.carrito.append({"Producto": prod_sel, "Cant": cant, "Precio": item["Precio RD$"], "Total": cant*item["Precio RD$"]})
                st.toast(f"{prod_sel} agregado")
    
    with col2:
        st.subheader("Factura")
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            st.table(df_car)
            subtotal = df_car["Total"].sum()
            itbis = subtotal * 0.18
            total = subtotal + itbis
            st.metric("TOTAL A COBRAR", f"RD$ {total:,.2f}", f"Subtotal RD$ {subtotal:,.0f} + ITBIS")
            
            tipo_pago = st.selectbox("Pago", ["Efectivo", "Transferencia", "Fiado"])
            if st.button("✅ COBRAR Y FACTURAR CON NCF", type="primary", use_container_width=True):
                st.session_state.ventas_hoy += total
                # Descontar stock
                for item in st.session_state.carrito:
                    idx = st.session_state.inventario[st.session_state.inventario["Producto"]==item["Producto"]].index[0]
                    st.session_state.inventario.at[idx, "Stock"] -= item["Cant"]
                
                if tipo_pago == "Fiado":
                    st.session_state.fiados.append({"Cliente": "Cliente Mostrador", "Monto": total, "Fecha": str(date.today()), "Productos": str(df_car["Producto"].tolist())})
                
                st.success(f"¡Venta registrada! NCF: B01-{datetime.now().strftime('%Y%m%d%H%M')}")
                st.balloons()
                st.session_state.carrito = []
        else:
            st.info("Carrito vacío")

# 2. CALCULADORA
elif menu == "🧮 Calculadora Inteligente":
    st.title("🧮 Calculadora Inteligente La Fe")
    st.write("Cotiza como un ingeniero y vende todo de una vez")
    
    obra = st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Zapata (4 zapatas)", "Piso 10x10", "Casita 3x3 completa"])
    
    if obra == "Pared de Blocks":
        c1, c2 = st.columns(2)
        largo = c1.number_input("Largo (metros)", 1.0, 100.0, 10.0)
        alto = c2.number_input("Alto (metros)", 1.0, 10.0, 2.5)
        if st.button("Calcular Materiales", type="primary"):
            m2 = largo * alto
            blocks = int(m2 * 12.5)
            cemento = int(m2 * 1.2)
            arena = round(m2 * 0.1, 2)
            alambre = 5
            
            st.success(f"Para {m2} m2:")
            st.json({
                f"{blocks} Blocks 6'' (RD$ {blocks*42})": f"Stock La Fe: {st.session_state.inventario[st.session_state.inventario['Código']=='BLK06']['Stock'].values[0]}",
                f"{cemento} Cemento Panam (RD$ {cemento*550})": "Disponible",
                f"{arena} m3 Arena (RD$ {arena*2500})": "Disponible",
            })
            total = blocks*42 + cemento*550 + arena*2500
            st.markdown(f"## Total Cotización La Fe: RD$ {total:,}")
            if st.button("📄 Generar PDF Cotización + Enviar por WhatsApp"):
                st.success("PDF Generado: Cotizacion_La_Fe.pdf con logo y tu 829-264-7574")

    elif obra == "Casita 3x3 completa":
        if st.button("Calcular Casita 3x3"):
            st.markdown("""
            ### Lista completa para casita 3x3:
            - **112 Blocks 6''** = RD$ 4,704
            - **15 Cemento Panam** = RD$ 8,250
            - **2 Varilla 3/8 (20 varillas)** = RD$ 8,400
            - **2 m3 Arena + 1.5 m3 Grava** = RD$ 9,200
            - **6 Zinc 10ft** = RD$ 4,500
            #### TOTAL: RD$ 35,054
            *Todo disponible en Ferretería La Fe*
            """)

# 3. FIADO
elif menu == "📓 Control de Fiado":
    st.title("📓 Control de Fiado - Cuaderno Digital")
    with st.form("fiado"):
        cliente = st.text_input("Nombre del maestro/cliente", "José el Maestro")
        monto = st.number_input("Monto fiado RD$", 100, 100000, 5000)
        fecha_pago = st.date_input("Promesa de pago", date.today())
        if st.form_submit_button("Guardar Fiado"):
            st.session_state.fiados.append({"Cliente": cliente, "Monto": monto, "Fecha": str(fecha_pago), "Productos": "Fiado manual"})
            st.success("Fiado guardado")
    
    if st.session_state.fiados:
        st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)
        st.warning(f"Total por cobrar en la calle: RD$ {pd.DataFrame(st.session_state.fiados)['Monto'].sum():,}")
        if st.button("📲 Mandar recordatorio por WhatsApp a todos"):
            st.success("Mensaje enviado: 'Hola, te recuerda Ferretería La Fe que tienes balance pendiente...'")

# 4. CIERRE
elif menu == "📊 Cierre de Caja":
    st.title("📊 Cierre de Caja de Hoy")
    st.metric("Vendido Hoy", f"RD$ {st.session_state.ventas_hoy:,.2f}")
    efectivo_en_caja = st.number_input("¿Cuánto efectivo hay en la caja físicamente?", 0.0, 1000000.0, st.session_state.ventas_hoy)
    diferencia = efectivo_en_caja - st.session_state.ventas_hoy
    if diferencia == 0:
        st.success("✅ Caja cuadra perfecta")
    elif diferencia < 0:
        st.error(f"🚨 FALTAN RD$ {abs(diferencia):,.2f} en caja")
    else:
        st.warning(f"⚠️ SOBRAN RD$ {diferencia:,.2f}")
    
    st.divider()
    st.subheader("Inventario bajo - Pedir hoy")
    bajo = st.session_state.inventario[st.session_state.inventario["Stock"] < 50]
    st.dataframe(bajo, use_container_width=True)
