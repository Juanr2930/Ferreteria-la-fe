import streamlit as st
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="Ferreteria La Fe - Sistema 606", layout="wide", page_icon="🧱")

# LOGO - FUNCIONA CON JPG O PNG
def show_logo(w=120):
    try:
        st.image("logo.png", width=w)
    except:
        try:
            st.image("logo.jpg", width=w)
        except:
            st.markdown("### 🧱")

col_logo, col_title = st.columns([1,4])
with col_logo:
    show_logo(110)
with col_title:
    st.markdown("## Ferreteria La Fe - Sistema 606")
    st.caption("Quisqueya, SPM | Soporte: 829-264-7574")

if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame([
        ["CEM001","Cemento Panam 94lbs",550,120,"Cemento"],
        ["CEM002","Cemento Cemex",565,80,"Cemento"],
        ["VAR001","Varilla 3/8 x 20",420,200,"Varilla"],
        ["VAR002","Varilla 1/2 x 20",680,150,"Varilla"],
        ["BLK04","Block 4''",35,1000,"Blocks"],
        ["BLK06","Block 6''",42,1500,"Blocks"],
        ["BLK08","Block 8''",48,800,"Blocks"],
        ["ZIN001","Zinc Acanalado 10ft",750,50,"Techo"],
        ["ALAM01","Alambre Dulce lb",85,100,"Alambres"],
        ["CLAV01","Clavo 2 1/2 lb",120,60,"Clavos"],
        ["PINT01","Pintura Tropical Galon",1850,30,"Pintura"],
        ["ARE001","Arena Lavada m3",2500,20,"Agregados"],
        ["GRAV01","Grava m3",2800,15,"Agregados"],
    ], columns=["Codigo","Producto","Precio RD$","Stock","Cat"])

if 'carrito' not in st.session_state: st.session_state.carrito=[]
if 'fiados' not in st.session_state: st.session_state.fiados=[]
if 'ventas_hoy' not in st.session_state: st.session_state.ventas_hoy=0

with st.sidebar:
    show_logo(160)
    st.title("Ferreteria La Fe")
    menu=st.radio("Ir a:",["Punto de Venta","Calculadora Inteligente","Control de Fiado","Cierre de Caja"])
    st.divider()
    st.success("Soporte: 829-264-7574")

if menu=="Punto de Venta":
    c1,c2=st.columns([2,1])
    with c1:
        st.title("Punto de Venta")
        buscador=st.text_input("🔍 Escanea o escribe: cemento, varilla, block...")
        if buscador:
            res=st.session_state.inventario[st.session_state.inventario["Producto"].str.contains(buscador,case=False,na=False)]
            st.dataframe(res,use_container_width=True)
            if not res.empty:
                prod_sel=st.selectbox("Selecciona producto",res["Producto"].tolist())
                cant=st.number_input("Cantidad",1,1000,1)
                if st.button("➕ Agregar al carrito"):
                    item=res[res["Producto"]==prod_sel].iloc[0]
                    st.session_state.carrito.append({"Producto":prod_sel,"Cant":cant,"Precio":item["Precio RD$"],"Total":cant*item["Precio RD$"]})
                    st.toast(f"{prod_sel} agregado")
    with c2:
        st.subheader("Factura")
        if st.session_state.carrito:
            df_car=pd.DataFrame(st.session_state.carrito)
            st.table(df_car)
            subtotal=df_car["Total"].sum()
            total=subtotal*1.18
            st.metric("TOTAL A COBRAR",f"RD$ {total:,.2f}")
            tipo_pago=st.selectbox("Pago",["Efectivo","Transferencia","Fiado"])
            if st.button("✅ COBRAR",type="primary",use_container_width=True):
                st.session_state.ventas_hoy+=total
                st.success(f"Venta! NCF: B01-{datetime.now().strftime('%Y%m%d%H%M')}")
                st.balloons()
                st.session_state.carrito=[]
        else:
            st.info("Carrito vacio")

elif menu=="Calculadora Inteligente":
    st.title("🧮 Calculadora Inteligente")
    obra=st.selectbox("Que va a construir?",["Pared de Blocks","Casita 3x3 completa"])
    if obra=="Pared de Blocks":
        largo=st.number_input("Largo (metros)",1.0,100.0,10.0)
        alto=st.number_input("Alto (metros)",1.0,10.0,2.5)
        if st.button("Calcular",type="primary"):
            m2=largo*alto
            blocks=int(m2*12.5)
            cemento=int(m2*1.2)
            st.success(f"{blocks} Blocks, {cemento} Cementos para {m2} m2")
    else:
        if st.button("Calcular Casita 3x3"):
            st.markdown("### TOTAL: RD$ 35,054 - Todo en La Fe")

elif menu=="Control de Fiado":
    st.title("📓 Control de Fiado")
    with st.form("fiado"):
        cliente=st.text_input("Nombre","Jose el Maestro")
        monto=st.number_input("Monto RD$",100,100000,5000)
        if st.form_submit_button("Guardar"):
            st.session_state.fiados.append({"Cliente":cliente,"Monto":monto,"Fecha":str(date.today())})
            st.success("Guardado")
    if st.session_state.fiados:
        st.dataframe(pd.DataFrame(st.session_state.fiados),use_container_width=True)

elif menu=="Cierre de Caja":
    st.title("📊 Cierre de Caja")
    st.metric("Vendido Hoy",f"RD$ {st.session_state.ventas_hoy:,.2f}")
