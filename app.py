# Así es como Streamlit busca la sección [connections.supabase]
conn = st.connection("supabase", type=SupabaseConnection)
import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="App Gestión Eléctrica", layout="wide", page_icon="⚡")

# 2. CONEXIÓN A SUPABASE (Con diagnóstico de errores)
try:
    # Busca la sección [connections.supabase] en tus Secrets de Streamlit
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("🚨 Error de configuración en los Secrets:")
    st.code(str(e))
    st.info("Asegúrate de que en 'Settings > Secrets' de Streamlit Cloud has pegado el formato TOML correctamente.")
    st.stop()

# 3. SISTEMA DE LOGIN
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Sistema Eléctrico")
        password = st.text_input("Introduce la contraseña del equipo", type="password")
        if st.button("Entrar"):
            # Cambia 'Electricidad2026' por la contraseña que quieras
            if password == "Electricidad2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

# 4. APLICACIÓN PRINCIPAL
if check_password():
    st.sidebar.title("🛠️ Menú Principal")
    menu = ["📊 Dashboard", "🏗️ Gestión de Obras", "⏱️ Registro de Horas", "📂 Documentación", "⚙️ Administración"]
    choice = st.sidebar.radio("Ir a:", menu)

    # --- PANTALLA: DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("📊 Estado Global")
        try:
            res = conn.query("cantidad_horas, obras(nombre)", table="horas").execute()
            if res.data and len(res.data) > 0:
                df_resumen = pd.DataFrame(res.data)
                df_resumen['obra'] = df_resumen['obras'].apply(lambda x: x['nombre'] if x else "Sin nombre")
                st.subheader("Horas por Proyecto")
                st.bar_chart(df_resumen.groupby('obra')['cantidad_horas'].sum())
            
            st.subheader("Obras Activas")
            obras_data = conn.query("*", table="obras").execute()
            if obras_data.data:
                st.dataframe(pd.DataFrame(obras_data.data), use_container_width=True)
        except Exception as e:
            st.warning("No se pudieron cargar los datos. ¿Has creado las tablas en Supabase?")
            st.error(str(e))

    # --- PANTALLA: GESTIÓN DE OBRAS ---
    elif choice == "🏗️ Gestión de Obras":
        st.title("🏗️ Alta de Proyectos")
        with st.form("nueva_obra"):
            nombre = st.text_input("Nombre de la Obra")
            cliente = st.text_input("Cliente")
            if st.form_submit_button("Registrar"):
                if nombre:
                    conn.table("obras").insert({"nombre": nombre, "cliente": cliente}).execute()
                    st.success(f"Obra '{nombre}' creada.")
                else:
                    st.error("El nombre es obligatorio.")

    # --- PANTALLA: REGISTRO DE HORAS ---
    elif choice == "⏱️ Registro de Horas":
        st.title("⏱️ Parte Diario")
        obras_res = conn.query("id, nombre", table="obras").execute()
        if obras_res.data:
            obras_dict = {o['nombre']: o['id'] for o in obras_res.data}
            with st.form("parte_horas"):
                obra_sel = st.selectbox("Obra", list(obras_dict.keys()))
                operario = st.text_input("Operario")
                h_trabajadas = st.number_input("Horas", min_value=0.5, step=0.5)
                detalles = st.text_area("Tareas")
                if st.form_submit_button("Guardar"):
                    conn.table("horas").insert({
                        "obra_id": obras_dict[obra_sel],
                        "operario": operario,
                        "cantidad_horas": h_trabajadas,
                        "tarea": detalles
                    }).execute()
                    st.success("✅ Guardado")
        else:
            st.info("Crea una obra primero.")

    # --- PANTALLA: DOCUMENTACIÓN ---
    elif choice == "📂 Documentación":
        st.title("📂 Subir Archivos")
        obras_res = conn.query("id, nombre", table="obras").execute()
        if obras_res.data:
            obra_doc = st.selectbox("Asociar a:", [o['nombre'] for o in obras_res.data])
            archivo = st.file_uploader("Imagen o PDF", type=["pdf", "jpg", "png"])
            if st.button("Subir") and archivo:
                path = f"{obra_doc}/{datetime.now().strftime('%Y%m%d_%H%M')}_{archivo.name}"
                conn.storage.from_("archivos_obra").upload(path, archivo.getvalue())
                st.success("Archivo subido.")

    # --- PANTALLA: ADMINISTRACIÓN ---
    elif choice == "⚙️ Administración":
        st.title("⚙️ Administración")
        admin_pass = st.text_input("Clave Maestra", type="password")
        if admin_pass == "AdminElect_2026":
            st.subheader("Exportar Datos")
            res_h = conn.query("*", table="horas").execute()
            if res_h.data:
                df = pd.DataFrame(res_h.data)
                st.download_button("📥 Descargar Excel (CSV)", df.to_csv(index=False).encode('utf-8'), "datos.csv")
