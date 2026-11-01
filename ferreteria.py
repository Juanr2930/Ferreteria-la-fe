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
    st.caption("Quisqueya, SPM - Catálogo Visual Pro")

# --- INVENTARIO LIMPIO - SIN URLs EXTERNAS ---
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

# Fuerza reset si viene con columnas viejas
if 'inventario' not in st.session_state or "Icono" not in st.session_state.inventario.columns or "Imagen" in st.session_state.inventario.columns:
    st.session_state.inventario = inventario_nuevo()

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'fiados' not in st.session_state: st.session_state.fiados=[]
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy=0

with st.sidebar:
    show_logo(150)
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo con Fotos","📊 Cierre"])
    st.divider()
    if st.button("🔄 Resetear inventario (si ves iconos raros)"):
        st.session_state.inventario = inventario_nuevo()
        st.session_state.clear()
        st.rerun()

# PUNTO DE VENTA
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta con Fotos")
        buscador=st.text_input("🔍 Busca: cemento, varilla, block...")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            for idx, row in res.iterrows():
                with st.container(border=True):
                    col_ico, col_info, col_btn = st.columns([1,2,1])
                    with col_ico:
                        st.markdown(f"<div style='font-size:50px;text-align:center'>{row['Icono']}</div>", unsafe_allow_html=True)
                    with col_info:
                        st.markdown(f"**{row['Producto']}**")
                        st.caption(f"{row['Código']} | Stock: {row['Stock']} | RD$ {row['Precio RD$']}")
                    with col_btn:
                        cant=st.number_input("Cant",1,1000,1,key=f"cant_{row['Código']}")
                        if st.button("Agregar", key=f"add_{row['Código']}"):
                            st.session_state.carrito.append({"Producto":row['Producto'],"Icono":row['Icono'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$']})
                            st.toast(f"{row['Producto']} agregado")
        else:
            st.info("Escribe cemento, varilla o block arriba")
    with c2:
        st.subheader("Factura")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                st.write(f"{item['Icono']} {item['Producto']} - {item['Cant']} x RD$ {item['Precio']} = RD$ {item['Total']}")
            total=sum([x['Total'] for x in st.session_state.carrito])*1.18
            st.metric("TOTAL", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                st.session_state.ventas_hoy+=total
                st.success("Venta registrada!")
                st.balloons()
                st.session_state.carrito=[]
        else:
            st.info("Carrito vacío")

elif menu=="📦 Catálogo con Fotos":
    st.title("Catálogo Visual")
    cols=st.columns(3)
    for i, (idx,row) in enumerate(st.session_state.inventario.iterrows()):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size:70px;text-align:center'>{row['Icono']}</div>", unsafe_allow_html=True)
                st.markdown(f"**{row['Producto']}**")
                st.metric("Precio", f"RD$ {row['Precio RD$']}")
                st.caption(f"Stock {row['Stock']}")

elif menu=="📊 Cierre":
    st.title("Cierre de Caja")
    st.metric("Vendido Hoy", f"RD$ {st.session_state.ventas_hoy:,.2f}")
