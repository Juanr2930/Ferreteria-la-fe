import streamlit as st
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="Ferretería La Fe - Sistema 606", layout="wide", page_icon="🧱")

def show_logo(w=120):
    try:
        st.image("logo.png", width=w)
    except:
        st.markdown("### 🧱")

# --- HEADER CON LOGO ---
col_logo, col_title = st.columns([1,4])
with col_logo:
    show_logo(110)
with col_title:
    st.markdown("## Ferretería La Fe - Sistema 606")
    st.caption("Quisqueya, SPM | Soporte: 829-264-7574 | Productos con Foto")

# --- INVENTARIO CON FOTOS ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame([
        # Codigo, Producto, Precio, Stock, Cat, Imagen URL, Emoji
        ["CEM001", "Cemento Panam 94lbs", 550, 120, "Cemento", "https://cdn-icons-png.flaticon.com/512/1087/1087815.png", "🏗️"],
        ["CEM002", "Cemento Cemex", 565, 80, "Cemento", "https://cdn-icons-png.flaticon.com/512/1087/1087815.png", "🏗️"],
        ["VAR001", "Varilla 3/8 x 20", 420, 200, "Varilla", "https://cdn-icons-png.flaticon.com/512/2942/2942789.png", "🔩"],
        ["VAR002", "Varilla 1/2 x 20", 680, 150, "Varilla", "https://cdn-icons-png.flaticon.com/512/2942/2942789.png", "🔩"],
        ["BLK04", "Block 4''", 35, 1000, "Blocks", "https://cdn-icons-png.flaticon.com/512/1048/1048953.png", "🧱"],
        ["BLK06", "Block 6''", 42, 1500, "Blocks", "https://cdn-icons-png.flaticon.com/512/1048/1048953.png", "🧱"],
        ["BLK08", "Block 8''", 48, 800, "Blocks", "https://cdn-icons-png.flaticon.com/512/1048/1048953.png", "🧱"],
        ["ZIN001", "Zinc Acanalado 10ft", 750, 50, "Techo", "https://cdn-icons-png.flaticon.com/512/1995/1995515.png", "🏠"],
        ["ALAM01", "Alambre Dulce lb", 85, 100, "Alambres", "https://cdn-icons-png.flaticon.com/512/3069/3069041.png", "🪢"],
        ["CLAV01", "Clavo 2 1/2 lb", 120, 60, "Clavos", "https://cdn-icons-png.flaticon.com/512/820/820149.png", "🔨"],
        ["PINT01", "Pintura Tropical Galón", 1850, 30, "Pintura", "https://cdn-icons-png.flaticon.com/512/1598/1598196.png", "🎨"],
        ["ARE001", "Arena Lavada m3", 2500, 20, "Agregados", "https://cdn-icons-png.flaticon.com/512/2921/2921220.png", "🏖️"],
        ["GRAV01", "Grava m3", 2800, 15, "Agregados", "https://cdn-icons-png.flaticon.com/512/2921/2921220.png", "🪨"],
    ], columns=["Código", "Producto", "Precio RD$", "Stock", "Cat", "Imagen", "Icono"])

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'fiados' not in st.session_state: st.session_state.fiados=[]
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy=0

with st.sidebar:
    show_logo(160)
    st.title("Ferretería La Fe")
    menu=st.radio("Ir a:",["🛒 Punto de Venta","📦 Catálogo con Fotos","🧮 Calculadora","📓 Fiado","📊 Cierre"])
    st.divider()
    st.success("Soporte: 829-264-7574")

# --- PUNTO DE VENTA CON FOTOS ---
if menu=="🛒 Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        buscador=st.text_input("🔍 Busca: cemento, varilla, block...")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            if not res.empty:
                # MOSTRAR CON FOTO GRANDE
                for idx, row in res.iterrows():
                    with st.container(border=True):
                        col_foto, col_info, col_btn = st.columns([1,2,1])
                        with col_foto:
                            st.image(row["Imagen"], width=80)
                        with col_info:
                            st.markdown(f"**{row['Icono']} {row['Producto']}**")
                            st.caption(f"{row['Código']} | Stock: {row['Stock']} | RD$ {row['Precio RD$']}")
                        with col_btn:
                            cant = st.number_input(f"Cant {row['Código']}", 1, 1000, 1, key=f"cant_{row['Código']}")
                            if st.button(f"Agregar", key=f"btn_{row['Código']}"):
                                st.session_state.carrito.append({"Producto":row['Producto'],"Cant":cant,"Precio":row['Precio RD$'],"Total":cant*row['Precio RD$'],"Foto":row['Imagen']})
                                st.toast(f"{row['Producto']} agregado ✅")
            else:
                st.warning("No encontrado, prueba otra palabra")
        else:
            st.info("Escribe arriba para buscar con foto")
    
    with c2:
        st.subheader("🧾 Factura")
        if st.session_state.carrito:
            for item in st.session_state.carrito:
                with st.container(border=True):
                    c1,c2=st.columns([1,2])
                    with c1: st.image(item['Foto'], width=50)
                    with c2:
                        st.write(f"**{item['Producto']}**")
                        st.caption(f"{item['Cant']} x RD$ {item['Precio']} = RD$ {item['Total']}")
            df_car=pd.DataFrame(st.session_state.carrito)
            total=df_car["Total"].sum()*1.18
            st.metric("TOTAL", f"RD$ {total:,.2f}")
            if st.button("✅ COBRAR", type="primary", use_container_width=True):
                st.session_state.ventas_hoy+=total
                st.success(f"Venta! NCF: B01-{datetime.now().strftime('%Y%m%d%H%M')}")
                st.balloons()
                st.session_state.carrito=[]
        else:
            st.info("Carrito vacío")

elif menu=="📦 Catálogo con Fotos":
    st.title("📦 Catálogo Visual La Fe")
    st.caption("Toca la categoría para filtrar")
    cat=st.selectbox("Categoría", ["Todos"] + st.session_state.inventario["Cat"].unique().tolist())
    df = st.session_state.inventario if cat=="Todos" else st.session_state.inventario[st.session_state.inventario["Cat"]==cat]
    
    cols=st.columns(3)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row["Imagen"], width=100)
                st.markdown(f"**{row['Icono']} {row['Producto']}**")
                st.metric("Precio", f"RD$ {row['Precio RD$']}")
                st.caption(f"Stock: {row['Stock']} | {row['Código']}")

elif menu=="🧮 Calculadora":
    st.title("🧮 Calculadora Inteligente")
    obra=st.selectbox("Obra", ["Pared de Blocks","Casita 3x3"])
    if st.button("Calcular", type="primary"):
        st.success("Cotización: RD$ 35,054 - Ver detalle en versión anterior")

elif menu=="📓 Fiado":
    st.title("📓 Fiado")
    if st.session_state.fiados:
        st.dataframe(pd.DataFrame(st.session_state.fiados), use_container_width=True)

elif menu=="📊 Cierre":
    st.title("📊 Cierre")
    st.metric("Vendido Hoy", f"RD$ {st.session_state.ventas_hoy:,.2f}")
