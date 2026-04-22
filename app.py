import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Gestión Eléctrica PRO", layout="wide", page_icon="⚡")

# 2. CONEXIÓN FORZADA (MANUAL)
try:
    # Leemos las claves directamente de los secrets
    url = st.secrets["URL_SUPABASE"]
    key = st.secrets["KEY_SUPABASE"]
    
    # Creamos la conexión pasando los parámetros explícitamente
    conn = st.connection(
        "supabase",
        type=SupabaseConnection,
        url=url,
        key=key
    )
    st.sidebar.success("✅ Conectado a Supabase")
except Exception as e:
    st.error("🚨 ERROR CRÍTICO DE CONFIGURACIÓN")
    st.write("No se encontraron las claves en Secrets. Asegúrate de que los nombres coinciden.")
    st.code(str(e))
    st.stop()

# 3. SISTEMA DE LOGIN
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Sistema Eléctrico")
        password = st.text_input("Contraseña del equipo", type="password")
        if st.button("Entrar"):
            if password == "Electricidad2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

# 4. APLICACIÓN
if check_password():
    st.sidebar.title("🛠️ MENÚ")
    menu = ["📊 Dashboard", "🏗️ Nueva Obra", "⏱️ Registro de Horas", "📂 Documentación", "⚙️ Administración"]
    choice = st.sidebar.radio("Ir a:", menu)

    # --- DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("📊 Estado de Obras")
        try:
            res = conn.query("*", table="obras").execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)
                
                # Gráfico de horas
                res_h = conn.query("cantidad_horas, obras(nombre)", table="horas").execute()
                if res_h.data:
                    df_h = pd.DataFrame(res_h.data)
                    df_h['obra'] = df_h['obras'].apply(lambda x: x['nombre'] if x else "N/A")
                    st.subheader("Horas Totales")
                    st.bar_chart(df_h.groupby('obra')['cantidad_horas'].sum())
            else:
                st.info("No hay datos todavía.")
        except Exception as e:
            st.error(f"Error al leer tablas: {e}")

    # --- NUEVA OBRA ---
    elif choice == "🏗️ Nueva Obra":
        st.title("🏗️ Registrar Proyecto")
        with st.form("form_obra"):
            nombre = st.text_input("Nombre de la Obra")
            cliente = st.text_input("Cliente")
            if st.form_submit_button("Crear"):
                if nombre:
                    conn.table("obras").insert({"nombre": nombre, "cliente": cliente}).execute()
                    st.success("Obra creada.")
                else:
                    st.error("Falta el nombre.")

    # --- REGISTRO DE HORAS ---
    elif choice == "⏱️ Registro de Horas":
        st.title("⏱️ Parte de Trabajo")
        obras = conn.query("id, nombre", table="obras").execute()
        if obras.data:
            nombres = {o['nombre']: o['id'] for o in obras.data}
            with st.form("f_horas"):
                obra_sel = st.selectbox("Obra", list(nombres.keys()))
                operario = st.text_input("Nombre")
                horas = st.number_input("Horas", step=0.5)
                tarea = st.text_area("Descripción")
                if st.form_submit_button("Guardar"):
                    conn.table("horas").insert({
                        "obra_id": nombres[obra_sel],
                        "operario": operario,
                        "cantidad_horas": horas,
                        "tarea": tarea
                    }).execute()
                    st.success("✅ Guardado")

    # --- DOCUMENTACIÓN ---
    elif choice == "📂 Documentación":
        st.title("📂 Subir Archivos")
        obras = conn.query("id, nombre", table="obras").execute()
        if obras.data:
            obra_sel = st.selectbox("Asociar a:", [o['nombre'] for o in obras.data])
            archivo = st.file_uploader("PDF o Imagen", type=["pdf", "jpg", "png"])
            if st.button("Subir") and archivo:
                path = f"{obra_sel}/{datetime.now().strftime('%Y%m%d_%H%M')}_{archivo.name}"
                conn.storage.from_("archivos_obra").upload(path, archivo.getvalue())
                st.success("Archivo subido.")

    # --- ADMINISTRACIÓN ---
    elif choice == "⚙️ Administración":
        st.title("⚙️ Administración")
        if st.text_input("Clave Admin", type="password") == "AdminElect_2026":
            if st.button("📥 Descargar CSV de Horas"):
                data = conn.query("*", table="horas").execute()
                if data.data:
                    st.download_button("Bajar CSV", pd.DataFrame(data.data).to_csv(index=False).encode('utf-8'), "horas.csv")
