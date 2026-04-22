import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gestión Eléctrica PRO", layout="wide", page_icon="⚡")

# 2. CONEXIÓN
try:
    # Usamos la Key de los secrets (asegúrate de que sea la 'service_role')
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets["URL_SUPABASE"],
        key=st.secrets["KEY_SUPABASE"]
    )
except Exception as e:
    st.error("Error configurando la conexión.")
    st.stop()

# 3. LOGIN
if "password_correct" not in st.session_state:
    st.title("🔐 Acceso")
    if st.text_input("Contraseña", type="password") == "Electricidad2026":
        if st.button("Entrar"):
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# 4. APP
st.sidebar.title("🛠️ Menú")
menu = ["📊 Dashboard", "🏗️ Nueva Obra", "⏱️ Registro de Horas", "📂 Documentación"]
choice = st.sidebar.radio("Navegación", menu)

if choice == "📊 Dashboard":
    st.title("📊 Resumen")
    try:
        # Usamos execute() directamente sobre la tabla
        items = conn.table("obras").select("*").execute()
        if items.data:
            st.write("Obras activas:")
            st.table(pd.DataFrame(items.data))
    except Exception as e:
        st.error(f"Error al leer: {e}")

elif choice == "🏗️ Nueva Obra":
    st.title("🏗️ Registrar Obra")
    with st.form("f_obra"):
        nombre = st.text_input("Nombre de la Obra")
        cliente = st.text_input("Cliente")
        if st.form_submit_button("Guardar"):
            try:
                # El insert suele fallar si RLS está activo
                conn.table("obras").insert({"nombre": nombre, "cliente": cliente}).execute()
                st.success("✅ Obra guardada en la base de datos")
            except Exception as e:
                st.error("Error al guardar. ¿Ejecutaste el SQL de 'DISABLE RLS'?")
                st.code(str(e))

elif choice == "⏱️ Registro de Horas":
    st.title("⏱️ Parte Diario")
    try:
        obras = conn.table("obras").select("id, nombre").execute()
        if obras.data:
            dict_obras = {o['nombre']: o['id'] for o in obras.data}
            with st.form("f_horas"):
                o_sel = st.selectbox("Obra", list(dict_obras.keys()))
                operario = st.text_input("Operario")
                horas = st.number_input("Horas", min_value=1.0)
                if st.form_submit_button("Registrar"):
                    conn.table("horas").insert({
                        "obra_id": dict_obras[o_sel],
                        "operario": operario,
                        "cantidad_horas": horas
                    }).execute()
                    st.success("Parte enviado")
    except Exception as e:
        st.error(f"Error: {e}")
