import streamlit as st
from st_supabase_connection import SupabaseConnection

# Intentar conectar
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.sidebar.success("✅ Conectado a la Base de Datos")
except Exception as e:
    st.sidebar.error("❌ Error de conexión")
    st.sidebar.write(e)
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de la página
st.set_page_config(page_title="Gestión de Obra Eléctrica", layout="wide")

# --- TÍTULO Y NAVEGACIÓN ---
st.title("⚡ Sistema de Gestión de Instalaciones")
menu = ["Dashboard", "Nueva Obra", "Registro de Horas", "Albaranes y Archivos"]
choice = st.sidebar.selectbox("Menú Principal", menu)

# --- FUNCIONES DE PERSISTENCIA (Base de datos local en CSV) ---
def guardar_datos(df, filename):
    df.to_csv(filename, index=False)

def cargar_datos(filename, columnas):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columnas)

# --- SECCIONES ---

if choice == "Dashboard":
    st.subheader("📊 Estado de las Obras")
    df_obras = cargar_datos("obras.csv", ["ID", "Nombre", "Cliente", "Estado"])
    if not df_obras.empty:
        st.dataframe(df_obras, use_container_width=True)
    else:
        st.info("No hay obras registradas.")

elif choice == "Nueva Obra":
    st.subheader("🏗️ Registrar Nueva Obra")
    with st.form("form_obra"):
        id_obra = st.text_input("ID Obra (ej: 2024-01)")
        nombre = st.text_input("Nombre de la Obra")
        cliente = st.text_input("Cliente")
        submit = st.form_submit_button("Crear Obra")
        
        if submit:
            df = cargar_datos("obras.csv", ["ID", "Nombre", "Cliente", "Estado"])
            nueva_fila = pd.DataFrame([[id_obra, nombre, cliente, "Activa"]], columns=df.columns)
            df = pd.concat([df, nueva_fila], ignore_index=True)
            guardar_datos(df, "obras.csv")
            st.success(f"Obra '{nombre}' creada correctamente.")

elif choice == "Registro de Horas":
    st.subheader("⏱️ Reporte de Personal")
    df_obras = cargar_datos("obras.csv", ["ID", "Nombre"])
    
    with st.form("form_horas"):
        obra_sel = st.selectbox("Seleccionar Obra", df_obras["Nombre"].tolist() if not df_obras.empty else ["N/A"])
        operario = st.text_input("Nombre del Operario")
        horas = st.number_input("Horas trabajadas", min_value=0.5, step=0.5)
        comentario = st.text_area("Tareas realizadas")
        submit_h = st.form_submit_button("Registrar Horas")
        
        if submit_h:
            df_h = cargar_datos("horas.csv", ["Fecha", "Obra", "Operario", "Horas", "Tarea"])
            nueva_h = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), obra_sel, operario, horas, comentario]], columns=df_h.columns)
            df_h = pd.concat([df_h, nueva_h], ignore_index=True)
            guardar_datos(df_h, "horas.csv")
            st.success("Horas guardadas.")

elif choice == "Albaranes y Archivos":
    st.subheader("📂 Gestión de Documentación")
    subida = st.file_uploader("Subir albarán o plano (PDF/JPG)", type=["pdf", "jpg", "png"])
    if subida:
        # Aquí podrías conectar con AWS S3 o Google Drive API
        # Por ahora lo guardamos en una carpeta local 'uploads'
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        with open(os.path.join("uploads", subida.name), "wb") as f:
            f.write(subida.getbuffer())
        st.success(f"Archivo {subida.name} guardado en el servidor.")
