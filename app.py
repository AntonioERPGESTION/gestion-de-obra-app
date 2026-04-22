import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestión Eléctrica PRO",
    layout="wide",
    page_icon="⚡"
)

# ==========================================
# 2. CONEXIÓN A SUPABASE (CON DIAGNÓSTICO)
# ==========================================
try:
    # Esta línea conecta con la sección [connections.supabase] de tus Secrets
    conn = st.connection("supabase", type=SupabaseConnection)
    
    # Prueba de fuego: Intentar una consulta simple para verificar conexión real
    # Si falla aquí, es que las tablas no están creadas o las keys son erróneas
    test_query = conn.query("*", table="obras", count="exact").execute()
    st.sidebar.success("✅ Conexión con Supabase OK")
except Exception as e:
    st.error("🚨 ERROR DE CONEXIÓN O CONFIGURACIÓN")
    st.info("Detalle técnico del error:")
    st.code(str(e))
    st.warning("REVISA: 1. Que los Secrets en Streamlit Cloud tengan el formato TOML correcto. 2. Que hayas ejecutado el SQL en Supabase.")
    st.stop()

# ==========================================
# 3. SISTEMA DE SEGURIDAD (LOGIN)
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Sistema Gestión Eléctrica")
        password = st.text_input("Contraseña del equipo", type="password")
        if st.button("Entrar"):
            if password == "Electricidad2026": # <--- Tu contraseña
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================
if check_password():
    # Menú Lateral
    st.sidebar.title("🛠️ PANEL DE CONTROL")
    menu = ["📊 Dashboard", "🏗️ Nueva Obra", "⏱️ Registro de Horas", "📂 Documentación", "⚙️ Administración"]
    choice = st.sidebar.radio("Navegación:", menu)

    # --- PESTAÑA: DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("📊 Resumen de Actividad")
        
        # Obtener datos de horas y obras
        try:
            res_h = conn.query("cantidad_horas, obras(nombre)", table="horas").execute()
            if res_h.data:
                df_h = pd.DataFrame(res_h.data)
                df_h['obra_nombre'] = df_h['obras'].apply(lambda x: x['nombre'] if x else "Desconocida")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Total Horas por Obra")
                    st.bar_chart(df_h.groupby('obra_nombre')['cantidad_horas'].sum())
                with col2:
                    st.subheader("Resumen Numérico")
                    st.write(df_h.groupby('obra_nombre')['cantidad_horas'].sum())
            else:
                st.info("No hay registros de horas todavía.")
        except:
            st.warning("No se pudieron cargar gráficos. Asegúrate de tener datos en la tabla 'horas'.")

    # --- PESTAÑA: NUEVA OBRA ---
    elif choice == "🏗️ Nueva Obra":
        st.title("🏗️ Registro de Nueva Obra")
        with st.form("form_obra"):
            nombre_obra = st.text_input("Nombre de la Obra")
            cliente_obra = st.text_input("Cliente")
            submit = st.form_submit_button("Crear Proyecto")
            
            if submit:
                if nombre_obra:
                    conn.table("obras").insert({"nombre": nombre_obra, "cliente": cliente_obra}).execute()
                    st.success(f"Obra '{nombre_obra}' creada con éxito.")
                else:
                    st.error("El nombre de la obra es obligatorio.")

    # --- PESTAÑA: REGISTRO DE HORAS ---
    elif choice == "⏱️ Registro de Horas":
        st.title("⏱️ Parte Diario de Personal")
        
        # Cargar obras para el desplegable
        obras_data = conn.query("id, nombre", table="obras").execute()
        if obras_data.data:
            obras_dict = {o['nombre']: o['id'] for o in obras_data.data}
            
            with st.form("form_horas"):
                obra_sel = st.selectbox("Seleccionar Obra", list(obras_dict.keys()))
                operario = st.text_input("Nombre del Operario")
                h_cantidad = st.number_input("Horas trabajadas", min_value=0.5, step=0.5)
                tarea_desc = st.text_area("Descripción del trabajo")
                
                if st.form_submit_button("Guardar Parte"):
                    conn.table("horas").insert({
                        "obra_id": obras_dict[obra_sel],
                        "operario": operario,
                        "cantidad_horas": h_cantidad,
                        "tarea": tarea_desc
                    }).execute()
                    st.success("✅ Parte guardado correctamente.")
        else:
            st.warning("No hay obras activas. Crea una primero en 'Nueva Obra'.")

    # --- PESTAÑA: DOCUMENTACIÓN ---
    elif choice == "📂 Documentación":
        st.title("📂 Gestión de Archivos (Planos/Albaranes)")
        obras_data = conn.query("id, nombre", table="obras").execute()
        
        if obras_data.data:
            obra_doc = st.selectbox("Vincular archivo a:", [o['nombre'] for o in obras_data.data])
            archivo = st.file_uploader("Selecciona archivo (Imagen o PDF)", type=["pdf", "jpg", "png", "jpeg"])
            
            if st.button("Subir al Servidor") and archivo:
                # Generar nombre único: Obra/Fecha_Nombre.ext
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                path_storage = f"{obra_doc}/{timestamp}_{archivo.name.replace(' ', '_')}"
                
                try:
                    conn.storage.from_("archivos_obra").upload(path_storage, archivo.getvalue())
                    st.success(f"¡Archivo '{archivo.name}' subido correctamente!")
                except Exception as e:
                    st.error(f"Error al subir: {e}")
                    st.info("Asegúrate de que existe un Bucket llamado 'archivos_obra' en tu Storage de Supabase.")
        else:
            st.info("Crea una obra primero para poder subir documentos.")

    # --- PESTAÑA: ADMINISTRACIÓN ---
    elif choice == "⚙️ Administración":
        st.title("⚙️ Panel de Administración")
        pass_admin = st.text_input("Clave Maestra de Gestión", type="password")
        
        if pass_admin == "AdminElect_2026":
            st.subheader("Exportación y Limpieza")
            
            if st.button("📥 Generar Informe CSV (Horas)"):
                data_h = conn.query("*", table="horas").execute()
                if data_h.data:
                    df_csv = pd.DataFrame(data_h.data)
                    st.download_button("Descargar Archivo CSV", df_csv.to_csv(index=False).encode('utf-8'), "historico_horas.csv", "text/csv")
            
            st.divider()
            st.subheader("Borrado de Obras")
            obras_list = conn.query("id, nombre", table="obras").execute()
            if obras_list.data:
                df_o = pd.DataFrame(obras_list.data)
                id_a_borrar = st.selectbox("Obra a eliminar permanentemente", df_o['id'].tolist())
                if st.button("🔥 ELIMINAR OBRA Y TODOS SUS DATOS"):
                    conn.table("obras").delete().eq("id", id_a_borrar).execute()
                    st.warning("Obra eliminada del sistema.")
                    st.rerun()
