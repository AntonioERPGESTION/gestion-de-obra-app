# Reemplaza tu bloque de conexión por este para diagnosticar:
try:
    # Esto busca automáticamente la sección [connections.supabase] en tus Secrets
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("🚨 Error técnico detallado:")
    st.code(str(e)) # Esto nos dirá si es un problema de URL, de Key o de red
    st.stop()
import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN Y CONEXIÓN
st.set_page_config(page_title="App Gestión Eléctrica", layout="wide", page_icon="⚡")

try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("Error de conexión. Revisa los Secrets en Streamlit Cloud.")
    st.stop()

# 2. SISTEMA DE LOGIN SENCILLO
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Sistema Eléctrico")
        password = st.text_input("Introduce la contraseña del equipo", type="password")
        if st.button("Entrar"):
            if password == "Electricidad2024": # <--- CAMBIA ESTO
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

if check_password():
    # 3. MENÚ LATERAL
    st.sidebar.title("🛠️ Menú Principal")
    menu = ["📊 Dashboard", "🏗️ Gestión de Obras", "⏱️ Registro de Horas", "📂 Documentación", "⚙️ Administración"]
    choice = st.sidebar.radio("Ir a:", menu)

    # --- PANTALLA: DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("📊 Estado Global de las Obras")
        
        # Resumen visual
        res = conn.query("cantidad_horas, obras(nombre)", table="horas").execute()
        if res.data:
            df_resumen = pd.DataFrame(res.data)
            df_resumen['obra'] = df_resumen['obras'].apply(lambda x: x['nombre'] if x else "Sin nombre")
            st.subheader("Consumo de Horas por Proyecto")
            st.bar_chart(df_resumen.groupby('obra')['cantidad_horas'].sum())
        
        st.subheader("Lista de Obras Activas")
        obras_data = conn.query("*", table="obras").execute()
        if obras_data.data:
            st.dataframe(pd.DataFrame(obras_data.data), use_container_width=True)

    # --- PANTALLA: GESTIÓN DE OBRAS ---
    elif choice == "🏗️ Gestión de Obras":
        st.title("🏗️ Alta de Nuevos Proyectos")
        with st.form("nueva_obra"):
            nombre = st.text_input("Nombre de la Obra (ej: Polígono Ind. X)")
            cliente = st.text_input("Cliente / Empresa")
            if st.form_submit_button("Registrar Obra"):
                if nombre:
                    conn.table("obras").insert({"nombre": nombre, "cliente": cliente}).execute()
                    st.success(f"Obra '{nombre}' creada con éxito.")
                else:
                    st.error("El nombre es obligatorio.")

    # --- PANTALLA: REGISTRO DE HORAS ---
    elif choice == "⏱️ Registro de Horas":
        st.title("⏱️ Parte de Trabajo Diario")
        obras_res = conn.query("id, nombre", table="obras").execute()
        if obras_res.data:
            obras_dict = {o['nombre']: o['id'] for o in obras_res.data}
            with st.form("parte_horas"):
                obra_sel = st.selectbox("Selecciona Obra", list(obras_dict.keys()))
                operario = st.text_input("Tu Nombre")
                h_trabajadas = st.number_input("Horas", min_value=0.5, step=0.5)
                detalles = st.text_area("Tareas realizadas")
                
                if st.form_submit_button("Enviar Parte"):
                    payload = {
                        "obra_id": obras_dict[obra_sel],
                        "operario": operario,
                        "cantidad_horas": h_trabajadas,
                        "tarea": detalles
                    }
                    conn.table("horas").insert(payload).execute()
                    st.success("Parte enviado correctamente.")
        else:
            st.warning("Primero debes crear una obra en 'Gestión de Obras'.")

    # --- PANTALLA: DOCUMENTACIÓN ---
    elif choice == "📂 Documentación":
        st.title("📂 Archivos y Albaranes")
        obras_res = conn.query("id, nombre", table="obras").execute()
        if obras_res.data:
            obra_doc = st.selectbox("Asociar archivo a:", [o['nombre'] for o in obras_res.data])
            archivo = st.file_uploader("Subir PDF o Imagen", type=["pdf", "jpg", "png", "jpeg"])
            
            if st.button("Subir al Sistema") and archivo:
                # Ruta: NombreObra/NombreArchivo
                nombre_archivo = f"{obra_doc}/{datetime.now().strftime('%Y%m%d')}_{archivo.name}"
                try:
                    conn.storage.from_("archivos_obra").upload(nombre_archivo, archivo.getvalue())
                    st.success(f"Archivo subido correctamente a la carpeta de {obra_doc}")
                except Exception as e:
                    st.error(f"Error al subir: {e}. ¿Has creado el bucket 'archivos_obra' en Supabase?")

    # --- PANTALLA: ADMINISTRACIÓN ---
    elif choice == "⚙️ Administración":
        st.title("⚙️ Panel Administrativo")
        admin_pass = st.text_input("Clave Maestra", type="password")
        
        if admin_pass == "AdminElect_2026":
            tab1, tab2 = st.tabs(["📊 Exportar Datos", "🗑️ Borrar Registros"])
            
            with tab1:
                st.subheader("Descargar histórico")
                res_h = conn.query("*", table="horas").execute()
                if res_h.data:
                    df_final = pd.DataFrame(res_h.data)
                    csv = df_final.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar Horas en CSV", csv, "horas_obra.csv", "text/csv")
            
            with tab2:
                st.subheader("Zona de Peligro")
                obras_lista = conn.query("*", table="obras").execute()
                if obras_lista.data:
                    df_o = pd.DataFrame(obras_lista.data)
                    id_borrar = st.selectbox("ID Obra a eliminar", df_o['id'].tolist())
                    if st.button("⚠️ ELIMINAR OBRA PERMANENTEMENTE"):
                        conn.table("obras").delete().eq("id", id_borrar).execute()
                        st.warning("Obra eliminada. Recuerda configurar DELETE CASCADE en Supabase.")
                        st.rerun()
