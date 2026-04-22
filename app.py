import streamlit as st  # <--- ESTA ES LA LÍNEA QUE FALTA
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="App Gestión Eléctrica", layout="wide", page_icon="⚡")

# 2. CONEXIÓN A SUPABASE
try:
    # Esta línea busca la sección [connections.supabase] en tus Secrets
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("🚨 Error de conexión o configuración en los Secrets")
    st.stop()

# 3. SISTEMA DE LOGIN
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Sistema Eléctrico")
        password = st.text_input("Introduce la contraseña del equipo", type="password")
        if st.button("Entrar"):
            # Contraseña por defecto
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
            # Consultamos las obras
            obras_data = conn.query("*", table="obras").execute()
            if obras_data.data:
                st.subheader("Obras Activas")
                st.dataframe(pd.DataFrame(obras_data.data), use_container_width=True)
            else:
                st.info("No hay obras creadas todavía. Ve a 'Gestión de Obras'.")
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")

    # --- PANTALLA: GESTIÓN DE OBRAS ---
    elif choice == "🏗️ Gestión de Obras":
        st.title("🏗️ Alta de Proyectos")
        with st.form("nueva_obra"):
            nombre = st.text_input("Nombre de la Obra")
            cliente = st.text_input("Cliente")
            if st.form_submit_button("Registrar Obra"):
                if nombre:
                    conn.table("obras").insert({"nombre": nombre, "cliente": cliente}).execute()
                    st.success(f"Obra '{nombre}' creada correctamente.")
                    st.rerun()
                else:
                    st.error("El nombre de la obra es obligatorio.")

    # --- PANTALLA: REGISTRO DE HORAS ---
    elif choice == "⏱️ Registro de Horas":
        st.title("⏱️ Parte Diario de Trabajo")
        res_obras = conn.query("id, nombre", table="obras").execute()
        if res_obras.data:
            obras_dict = {o['nombre']: o['id'] for o in res_obras.data}
            with st.form("parte_horas"):
                obra_sel = st.selectbox("Selecciona la Obra", list(obras_dict.keys()))
                operario = st.text_input("Nombre del Operario")
                h_trabajadas = st.number_input("Horas totales", min_value=0.5, step=0.5)
                detalles = st.text_area("Descripción de la tarea")
                
                if st.form_submit_button("Guardar Parte"):
                    conn.table("horas").insert({
                        "obra_id": obras_dict[obra_sel],
                        "operario": operario,
                        "cantidad_horas": h_trabajadas,
                        "tarea": detalles
                    }).execute()
                    st.success("✅ Parte registrado correctamente.")
        else:
            st.warning("Debes crear al menos una obra primero.")

    # --- PANTALLA: DOCUMENTACIÓN ---
    elif choice == "📂 Documentación":
        st.title("📂 Subir Planos y Albaranes")
        res_obras = conn.query("id, nombre", table="obras").execute()
        if res_obras.data:
            obra_doc = st.selectbox("Asociar a la obra:", [o['nombre'] for o in res_obras.data])
            archivo = st.file_uploader("Subir imagen o PDF", type=["pdf", "jpg", "png", "jpeg"])
            
            if st.button("Subir Archivo") and archivo:
                # Generamos una ruta limpia para el archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                nombre_limpio = archivo.name.replace(" ", "_")
                ruta = f"{obra_doc}/{timestamp}_{nombre_limpio}"
                
                try:
                    conn.storage.from_("archivos_obra").upload(ruta, archivo.getvalue())
                    st.success(f"¡Archivo '{archivo.name}' subido con éxito!")
                except Exception as e:
                    st.error(f"Error al subir: {e}. Revisa si el bucket 'archivos_obra' es público.")

    # --- PANTALLA: ADMINISTRACIÓN ---
    elif choice == "⚙️ Administración":
        st.title("⚙️ Panel de Administración")
        admin_pass = st.text_input("Clave de Administrador", type="password")
        if admin_pass == "AdminElect_2026":
            st.subheader("Opciones Avanzadas")
            if st.button("📥 Descargar histórico de horas (CSV)"):
                res_h = conn.query("*", table="horas").execute()
                if res_h.data:
                    csv = pd.DataFrame(res_h.data).to_csv(index=False).encode('utf-8')
                    st.download_button("Click para descargar", csv, "registro_horas.csv", "text/csv")
