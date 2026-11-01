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
    st.caption("Quisqueya, SPM | Sistema con Calculadora Inteligente + Lector de Barras")

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

if 'inventario' not in st.session_state or "Icono" not in st.session_state.inventario.columns or "Imagen" in st.session_state.inventario.columns:
    st.session_state.inventario = inventario_nuevo()

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'fiados' not in st.session_state: st.session_state.fiados=[]
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy=0

with st.sidebar:
    show_logo(150)
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo","🧮 Calculadora Materiales","📓 Fiado","📊 Cierre"])
    st.divider()
    if st.button("🔄 Resetear sistema"):
        st.session_state.clear()
        st.rerun()
    st.success("Soporte: 829-264-7574")

# --- PUNTO DE VENTA CON BARRAS ---
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        
        # === NUEVO SISTEMA DE BARRAS 606 ===
        st.markdown("#### 📷 Sistema de Barras 606")
        col_bar1, col_bar2 = st.columns([3,1])
        with col_bar1:
            codigo_escaneado = st.text_input("Pistolea el código aquí", placeholder="Ej: CEM001 o usa scanner USB...", key="barcode_scan")
        with col_bar2:
            st.write("")
            scan_btn = st.button("🔎 Buscar Código", use_container_width=True)
        
        if codigo_escaneado and (scan_btn or len(codigo_escaneado) >= 3):
            inv = st.session_state.inventario
            match = inv[inv["Código"].str.upper().str.strip() == codigo_escaneado.upper().strip()]
            if not match.empty:
                row = match.iloc[0]
                cant = 1
                st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                st.success(f"✅ {row['Producto']} agregado por código {row['Código']}")
                st.toast(f"Agregado: {row['Producto']}")
                # Limpia para próximo escaneo
                if "barcode_scan" in st.session_state:
                    st.session_state.barcode_scan = ""
            else:
                st.error(f"❌ Código '{codigo_escaneado}' no existe. Verifica en Catálogo.")
        
        st.divider()
        st.markdown("#### 🔍 Búsqueda por Nombre")
        buscador=st.text_input("Busca: cemento, varilla, block...", key="busc_nombre")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            for idx, row in res.iterrows():
                with st.container(border=True):
                    col_ico, col_info, col_btn = st.columns([1,2,1])
                    with col_ico:
                        st.markdown(f"<div style='font-size:45px;text-align:center'>{row['Icono']}</div>", unsafe_allow_html=True)
                    with col_info:
                        st.markdown(f"**{row['Producto']}**")
                        st.caption(f"{row['Código']} | Stock: {row['Stock']} | RD$ {row['Precio RD$']}")
                    with col_btn:
                        cant=st.number_input("Cant",1,1000,1,key=f"cant_{row['Código']}")
                        if st.button("Agregar", key=f"add_{row['Código']}"):
                            st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Código":row['Código']})
                            st.toast(f"{row['Producto']} agregado")
    with c2:
        st.subheader("Factura")
        if st.session_state.carrito:
            for i, item in enumerate(st.session_state.carrito):
                st.write(f"{item['Icono']} {item['Producto']} ({item.get('Código','')}) - {item['Cant']} x RD$ {item['Total']}")
            total=sum([x['Total'] for x in st.session_state.carrito])*1.18
            st.metric("TOTAL + ITBIS", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                st.session_state.ventas_hoy+=total
                st.success("Venta registrada!")
                st.balloons()
                st.session_state.carrito=[]
                st.rerun()
            if st.button("🗑️ Vaciar carrito"):
                st.session_state.carrito=[]
                st.rerun()
        else:
            st.info("Carrito vacío. Escanea o busca producto.")

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo Visual La Fe - Con Códigos de Barra")
    st.caption("Estos son los códigos que vas a imprimir para pegar en estantes")
    cols=st.columns(3)
    for i, (idx,row) in enumerate(st.session_state.inventario.iterrows()):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size:60px;text-align:center'>{row['Icono']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{row['Producto']}**")
                st.code(f"{row['Código']}", language="text")
                st.metric("Precio", f"RD$ {row['Precio RD$']}")

# --- CALCULADORA DE MATERIALES COMPLETA ---
elif menu=="🧮 Calculadora Materiales":
    st.title("🧮 Calculadora Inteligente La Fe")
    st.caption("Calcula exacto para que el cliente no compre de más ni de menos")
    
    obra=st.selectbox("¿Qué va a construir?", ["Pared de Blocks", "Zapata (4 zapatas)", "Piso 10x10 (100 m2)", "Casita 3x3 Completa", "Techo de Zinc 3x3"])
    
    if obra=="Pared de Blocks":
        c1,c2,c3=st.columns(3)
        largo=c1.number_input("Largo pared (metros)", 1.0, 100.0, 10.0)
        alto=c2.number_input("Alto pared (metros)", 1.0, 10.0, 2.5)
        tipo=c3.selectbox("Tipo Block", ["Block 6'' - RD$42", "Block 4'' - RD$35", "Block 8'' - RD$48"])
        precio_block = 42 if "6''" in tipo else (35 if "4''" in tipo else 48)
        
        if st.button("Calcular Pared", type="primary"):
            m2=largo*alto
            blocks=int(m2*12.5) + 5
            cemento=int(m2*1.15) + 1
            arena=round(m2*0.08, 2)
            varilla=int(m2*1.2)
            total=blocks*precio_block + cemento*550 + arena*2500 + varilla*420
            
            st.success(f"Para {m2} m2 de pared:")
            col1,col2=st.columns(2)
            with col1:
                st.markdown(f"""
                **Materiales:**
                - 🧱 {blocks} Blocks ({tipo})
                - 🏗️ {cemento} Fundas Cemento
                - 🏖️ {arena} m3 Arena
                - 🔩 {varilla} Varillas 3/8
                """)
            with col2:
                st.markdown(f"### TOTAL La Fe: RD$ {total:,}")
                st.info("Incluye 5% desperdicio")
                if st.button("Agregar todo al carrito"):
                    st.session_state.carrito.append({"Producto":f"Pared {m2}m2 - {blocks} Blocks","Icono":"🧱","Cant":1,"Precio":total,"Total":total})
                    st.success("Cotización agregada al Punto de Venta")

    elif obra=="Zapata (4 zapatas)":
        prof=st.number_input("Profundidad (m)", 0.5, 2.0, 1.0)
        if st.button("Calcular Zapatas", type="primary"):
            cemento=10
            varilla=16
            grava=1.0
            arena=0.8
            total=cemento*550 + varilla*420 + grava*2800 + arena*2500
            st.success(f"Para 4 zapatas de {prof}m:")
            st.markdown(f"- 🏗️ {cemento} Cementos, 🔩 {varilla} Varillas 1/2, 🪨 {grava}m3 Grava, 🏖️ {arena}m3 Arena")
            st.markdown(f"### TOTAL: RD$ {total:,}")

    elif obra=="Piso 10x10 (100 m2)":
        espesor=st.selectbox("Espesor", ["10cm (estándar)", "15cm (pesado)"])
        if st.button("Calcular Piso", type="primary"):
            cemento=70 if "10cm" in espesor else 100
            arena=7
            grava=8
            total=cemento*550 + arena*2500 + grava*2800
            st.success(f"Piso 10x10 = 100 m2:")
            st.markdown(f"- 🏗️ {cemento} Cementos, 🏖️ {arena}m3 Arena, 🪨 {grava}m3 Grava")
            st.markdown(f"### TOTAL: RD$ {total:,}")

    elif obra=="Casita 3x3 Completa":
        if st.button("Calcular Casita Completa", type="primary", use_container_width=True):
            st.markdown("""
            ### 🏠 Casita 3x3 (9 m2) - Lista La Fe:
            - 🧱 112 Blocks 6'' = RD$ 4,704
            - 🏗️ 15 Cemento Panam = RD$ 8,250
            - 🔩 20 Varilla 3/8 = RD$ 8,400
            - 🏖️ 2 m3 Arena Lavada = RD$ 5,000
            - 🪨 1.5 m3 Grava = RD$ 4,200
            - 🏠 6 Zinc 10ft = RD$ 4,500
            - 🪢 5 lb Alambre + 3 lb Clavos = RD$ 785
            #### 💰 TOTAL MATERIALES: RD$ 35,839
            """)
            st.warning("Precio ferretero real Quisqueya - ¡Todo disponible en La Fe!")
            if st.button("Cotizar casita completa"):
                st.session_state.carrito.append({"Producto":"Casita 3x3 Completa","Icono":"🏠","Cant":1,"Precio":35839,"Total":35839})
                st.success("Agregado al carrito")

    elif obra=="Techo de Zinc 3x3":
        if st.button("Calcular Techo", type="primary"):
            zinc=6
            clavos=2
            madera=10
            total=zinc*750 + clavos*120 + madera*400
            st.success(f"Techo 3x3:")
            st.markdown(f"- 🏠 {zinc} Zinc 10ft, 🔨 {clavos}lb Clavos, 🪵 {madera} Cuartones")
            st.markdown(f"### TOTAL: RD$ {total:,}")

elif menu=="📓 Fiado":
    st.title("📓 Control de Fiado - Cuaderno Digital")
    st.caption("Aquí anotas a quién le fiaste, como el cuaderno de antes pero que no se pierde")
    
    col1, col2 = st.columns([1,2])
    
    with col1:
        st.subheader("➕ Nuevo Fiado")
        with st.form("nuevo_fiado", clear_on_submit=True):
            cliente = st.text_input("Nombre del cliente / maestro", placeholder="Ej: José el Maestro")
            telefono = st.text_input("Teléfono / WhatsApp", placeholder="829-...")
            monto = st.number_input("Monto RD$", min_value=100, max_value=500000, value=5000, step=100)
            fecha = st.date_input("Fecha fiado", value=date.today())
            vence = st.date_input("Promesa de pago", value=date.today())
            nota = st.text_input("Qué se llevó", placeholder="Ej: 10 Cemento, 20 Varillas")
            
            guardar = st.form_submit_button("💾 Guardar Fiado", type="primary", use_container_width=True)
            if guardar:
                if cliente == "":
                    st.error("Pon el nombre")
                else:
                    st.session_state.fiados.append({
                        "Cliente": cliente,
                        "Tel": telefono,
                        "Monto": monto,
                        "Fecha": str(fecha),
                        "Vence": str(vence),
                        "Que llevó": nota,
                        "Estado": "Pendiente"
                    })
                    st.success(f"✅ Fiado de {cliente} por RD$ {monto} guardado")
                    st.balloons()
    
    with col2:
        st.subheader("📋 Lista de Fiados")
        if st.session_state.fiados:
            df = pd.DataFrame(st.session_state.fiados)
            buscar = st.text_input("🔍 Buscar cliente", placeholder="Escribe nombre...")
            if buscar:
                df = df[df["Cliente"].str.contains(buscar, case=False, na=False)]
            total_pendiente = df[df["Estado"]=="Pendiente"]["Monto"].sum() if "Estado" in df.columns else df["Monto"].sum()
            st.metric("💰 Total por cobrar en la calle", f"RD$ {total_pendiente:,.0f}", f"{len(df)} clientes")
            for i, row in df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3,1,1])
                    with c1:
                        st.markdown(f"**{row['Cliente']}** - RD$ {row['Monto']:,}")
                        st.caption(f"📞 {row.get('Tel','')} | 📅 Vence: {row.get('Vence', row.get('Fecha'))} | {row.get('Que llevó','')}")
                    with c2:
                        if row.get("Estado") == "Pendiente":
                            if st.button("✅ Cobrado", key=f"cob_{i}"):
                                st.session_state.fiados[i]["Estado"] = "Pagado"
                                st.success("Marcado como pagado")
                                st.rerun()
                        else:
                            st.success("Pagado")
                    with c3:
                        if st.button("🗑️ Borrar", key=f"del_{i}"):
                            st.session_state.fiados.pop(i)
                            st.rerun()
            st.divider()
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📭 No hay fiados aún. Agrega el primero a la izquierda.")

elif menu=="📊 Cierre":
    st.title("📊 Cierre de Caja - Ferretería La Fe")
    st.caption(f"Fecha: {date.today()} | Quisqueya, SPM")
    col1, col2, col3, col4 = st.columns(4)
    ventas = st.session_state.ventas_hoy
    fiados_total = sum([f["Monto"] for f in st.session_state.fiados if f.get("Estado")=="Pendiente"]) if st.session_state.fiados else 0
    total_dia = ventas + fiados_total
    with col1:
        st.metric("💵 Efectivo/Transf", f"RD$ {ventas:,.0f}")
    with col2:
        st.metric("📓 Fiado del Día", f"RD$ {fiados_total:,.0f}")
    with col3:
        st.metric("📈 Total Movido", f"RD$ {total_dia:,.0f}")
    with col4:
        st.metric("🧱 Productos", f"{len(st.session_state.inventario)} tipos")
    st.divider()
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("💰 Cuadre de Caja")
        efectivo_fisico = st.number_input("¿Cuánto efectivo hay FÍSICO en la gaveta?", min_value=0.0, value=float(ventas), step=100.0)
        diferencia = efectivo_fisico - ventas
        if ventas == 0 and efectivo_fisico == 0:
            st.info("Aún no hay ventas hoy")
        elif diferencia == 0:
            st.success(f"✅ CUADRE PERFECTO - Caja: RD$ {efectivo_fisico:,.0f}")
            st.balloons()
        elif diferencia < 0:
            st.error(f"🚨 FALTAN RD$ {abs(diferencia):,.2f}")
        else:
            st.warning(f"⚠️ SOBRAN RD$ {diferencia:,.2f}")
        st.divider()
        if st.button("🔒 Cerrar Día y Reiniciar (para mañana)", type="primary"):
            st.session_state.ventas_hoy = 0
            st.success("Día cerrado.")
            st.rerun()
    with c2:
        st.subheader("⚠️ Inventario Bajo")
        bajo = st.session_state.inventario[st.session_state.inventario["Stock"] < 50]
        if not bajo.empty:
            st.dataframe(bajo[["Producto","Stock","Precio RD$"]], use_container_width=True)
            st.error(f"{len(bajo)} productos con stock bajo!")
        else:
            st.success("Todo el stock está bien")
