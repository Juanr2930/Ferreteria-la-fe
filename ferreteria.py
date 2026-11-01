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
    st.caption("Quisqueya, SPM | Sistema con Calculadora Inteligente")

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

# --- PUNTO DE VENTA ---
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        buscador=st.text_input("🔍 Busca: cemento, varilla, block...")
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
                            st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$']})
                            st.toast(f"{row['Producto']} agregado")
    with c2:
        st.subheader("Factura")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                st.write(f"{item['Icono']} {item['Producto']} - {item['Cant']} x RD$ {item['Total']}")
            total=sum([x['Total'] for x in st.session_state.carrito])*1.18
            st.metric("TOTAL", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                st.session_state.ventas_hoy+=total
                st.success("Venta registrada!")
                st.balloons()
                st.session_state.carrito=[]

elif menu=="📦 Catálogo":
    st.title("📦 Catálogo Visual La Fe")
    cols=st.columns(3)
    for i, (idx,row) in enumerate(st.session_state.inventario.iterrows()):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size:60px;text-align:center'>{row['Icono']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{row['Producto']}**")
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
        prof=c1.number_input("Profundidad (m)", 0.5, 2.0, 1.0) if 'c1' in locals() else st.number_input("Profundidad", 0.5, 2.0, 1.0)
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
    st.title("📓 Fiado")
    if st.session_state.fiados:
        st.dataframe(pd.DataFrame(st.session_state.fiados))

elif menu=="📊 Cierre":
    st.title("📊 Cierre")
    st.metric("Vendido Hoy", f"RD$ {st.session_state.ventas_hoy:,.2f}")
