import streamlit as st
import pandas as pd
import requests
import math
import time
from streamlit_cookies_controller import CookieController

cookie_controller = CookieController()

# Definir la URL base del backend
base_url = "https://tesis-backend-nxpy.onrender.com"

# Definir opciones de superestructura
superestructura_optiones = [
    "adjacent box beams",
    "adjacent slab beams",
    "arch",
    "bulb tee",
    "channel beam",
    "concrete segmental box girder",
    "culvert",
    "deck arches",
    "i-beams",
    "inverset",
    "multi girder curved",
    "multi girder straight",
    "next beam",
    "next beam type d",
    "next beam type f",
    "precast box culvert",
    "prestressed adjacent box beams",
    "prestressed adjacent slab beams",
    "prestressed bulb tees",
    "prestressed I-beams",
    "prestressed spread box beams",
    "segmental box girder",
    "spread box beams",
    "steel multi girder straight",
    "steel segmental box girder",
    "three sided frame",
    "through girder",
    "through truss",
    "truss"
    ]

# Definir opciones de estribo
estribo_optiones = [
    "abutmentless",
    "cantilever stems",
    "culvert",
    "existing",
    "footing only",
    "integral",
    "integral & gravity",
    "invert slab",
    "other",
    "semi-integral",
    "short stem",
    "solid cantilever",
    "stem",
    "stub cantilever",
    "stub on msess wall"
    ]

# Inicializar el estado de la sesión para la creación o edición de un proyecto
if "create_project" not in st.session_state:
    st.session_state["create_project"] = False

    st.session_state["view_project"] = False

if "edit_project" not in st.session_state:
    st.session_state["edit_project"] = False
    st.session_state["project_to_view"] = None

if "project_to_edit" not in st.session_state:
    st.session_state["project_to_edit"] = None

# Función para manejar el formulario de creación de estimación
def handle_create_project():
    st.title("Crear Presupuesto")
    
    # Formulario para los campos
    tipo_superestructura = st.selectbox("Tipo de Superestructura", options=superestructura_optiones)
    tipo_estribo = st.selectbox("Tipo de Estribo", options=estribo_optiones)
    ancho = st.number_input("Ancho Total (m)", min_value=2.0, step=0.01)
    longitud = st.number_input("Longitud Total (m)", min_value=2.0, step=0.01)
    tramos = st.number_input("Número de Tramos", min_value=1, step=1, format="%d", value=1)
    año = st.number_input("Año de Construcción", min_value=1900, max_value=2100, step=1, format="%d", value=2024)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar"):
            # Preparar datos para la creación del presupuesto
            data = {
                "structureType": tipo_superestructura,
                "abutmentType": tipo_estribo,
                "total_Width": ancho,
                "number_of_Spans": tramos,
                "total_Length": longitud,
                "year": año
            }
            response = requests.post(f"{base_url}/estimation/predict", json=data)

            if response.status_code == 200:
                result = response.json()
                st.success(f"Estimación guardada con éxito.")
            else:
                st.error("Error al guardar la estimación.")
            time.sleep(0.5) 
            st.session_state["create_project"] = False
            st.rerun()

    with col2:
        if st.button("Cancelar"):
            st.session_state["create_project"] = False
            st.rerun()

# Función para solicitar la edición de una estimación
def handle_edit_project():
    st.title("Editar Presupuesto")
    
    project_data = st.session_state["project_to_edit"]
    
    # Mostrar el formulario con los valores actuales
    tipo_superestructura = st.selectbox("Tipo de Superestructura", options=superestructura_optiones, index=superestructura_optiones.index(project_data['structureType']))
    tipo_estribo = st.selectbox("Tipo de Estribo", options=estribo_optiones, index=estribo_optiones.index(project_data['abutmentType']))
    ancho = st.number_input("Ancho Total (m)", min_value=2.0, step=0.01, value=project_data['total_Width'])
    longitud = st.number_input("Longitud Total (m)", min_value=2.0, step=0.01, value=project_data['total_Length'])
    tramos = st.number_input("Número de Tramos", min_value=1, step=1, format="%d", value=project_data['number_of_Spans'])
    año = st.number_input("Año de Construcción", min_value=1900, max_value=2100, step=1, format="%d", value=project_data['year'])
    cost = st.number_input("Costo Total", min_value=1000.0, step=0.01, value=project_data['total_Cost'])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar Cambios"):
            # Preparar datos para la creación del request
            data = {
                "prediction_id": project_data['id'],  # Asegúrate de que esto se envíe desde el objeto
                "request_type": "Edición",  # Cambia esto según el tipo de request
                "user_id": cookie_controller.get('user_id'),  # Reemplaza esto con el ID del usuario adecuado
                "date": pd.to_datetime("now").strftime("%Y-%m-%d"),  # Obtén la fecha actual
                "original_prediction_object": {
                    "input_list": {
                        "structureType": project_data['structureType'],
                        "abutmentType": project_data['abutmentType'],
                        "total_Width": project_data['total_Width'],
                        "number_of_Spans": project_data['number_of_Spans'],
                        "total_Length": project_data['total_Length'],
                        "year": project_data['year']
                    },
                    "total_Cost": project_data['total_Cost']  # O el nuevo costo estimado si se calcula
                },
                "new_prediction_object": {
                    "input_list": {
                        "structureType": tipo_superestructura,
                        "abutmentType": tipo_estribo,
                        "total_Width": ancho,
                        "number_of_Spans": tramos,
                        "total_Length": longitud,
                        "year": año
                    },
                    "total_Cost": cost  # O el nuevo costo estimado si se calcula
                },
                "status": "Pendiente"  # O establece esto según tu lógica
            }

            # Enviar el request a la API
            response = requests.post(f"{base_url}/request/create", json=data)

            if response.status_code == 200:
                st.success("Solicitud de actualización creada con éxito.")
            else:
                st.error("Error al crear la solicitud de actualización.")
            time.sleep(0.5) 
            st.session_state["edit_project"] = False
            st.session_state["project_to_edit"] = None
            st.rerun()

    with col2:
        if st.button("Cancelar"):
            st.session_state["edit_project"] = False
            st.session_state["project_to_edit"] = None
            st.rerun()

# Función para solicitar la eliminación de una estimación
def handle_delete_project(id):
    # Preparar datos para la creación del request
    data = {
        "prediction_id": id,  # ID del proyecto a eliminar
        "request_type": "Eliminación",  # Tipo de request
        "user_id": cookie_controller.get('user_id'),  # ID del usuario adecuado
        "date": pd.to_datetime("now").strftime("%Y-%m-%d"),  # Fecha actual
        "original_prediction_object": {
            "input_list": {
                        "structureType": '',
                        "abutmentType": '',
                        "total_Width": 0,
                        "number_of_Spans": 0,
                        "total_Length": 0,
                        "year": 0
                    },  # No hay datos de entrada en la eliminación
            "total_Cost": 0  # Costo en cero ya que se está eliminando
        },
        "new_prediction_object": {
            "input_list": {
                        "structureType": '',
                        "abutmentType": '',
                        "total_Width": 0,
                        "number_of_Spans": 0,
                        "total_Length": 0,
                        "year": 0
                    },  # No hay datos de entrada en la eliminación
            "total_Cost": 0  # Costo en cero ya que se está eliminando
        },
        "status": "Pendiente"  # Establecer esto según tu lógica
    }

    # Enviar el request a la API
    response = requests.post(f"{base_url}/request/create", json=data)

    if response.status_code == 200:
        st.success("Solicitud de eliminación creada con éxito.")
    else:
        st.error("Error al crear la solicitud de actualización.")
    time.sleep(0.5) 
    st.rerun()
        
# Si el usuario está en la página de creación de estimación, mostrar el formulario
if st.session_state["create_project"]:
    handle_create_project()

# Si el usuario está en la página de edición de estimación, mostrar el formulario de edición
elif st.session_state["edit_project"]:
    handle_edit_project()

else:
    # Mostrar título de sección
    st.title("Lista de Estimaciones")

    # Crear un contenedor para centrar los elementos
    with st.container():
        search_col, create_col = st.columns([4, 1])  # Ajustar proporciones

        # Colocar la barra de búsqueda
        with search_col:
            search_term = st.text_input("", key="search", placeholder="Buscar por tipo de superstructura o estribo ...", label_visibility="collapsed")

        # Botón para crear presupuesto
        with create_col:
            if st.button('Crear Estimación'):
                st.session_state["create_project"] = True
                st.rerun()

    # Llamar a la API para obtener las estimaciones
    response = requests.get(f"{base_url}/estimation")
    
    if response.status_code == 200:
        estimaciones = response.json()
        df_estimations = pd.DataFrame(estimaciones)  # Convertir a DataFrame

        # Aplanar las columnas de input_list
        df_estimations = df_estimations.join(pd.json_normalize(df_estimations['input_list'])).drop(columns=['input_list'])

        # Filtrar DataFrame según el término de búsqueda
        if search_term:
            filtered_df = df_estimations[df_estimations['structureType'].str.contains(search_term, case=False) | 
                                          df_estimations['abutmentType'].str.contains(search_term, case=False)]
        else:
            filtered_df = df_estimations  # Si no hay búsqueda, usar el DataFrame original

        # Verificar si el DataFrame filtrado está vacío
        if filtered_df.empty:
            st.warning("No se encontraron resultados para el término de búsqueda.")
            current_page_data = pd.DataFrame()  # Mostrar un DataFrame vacío para que no cause errores
        else:
            # Paginador: Dividir DataFrame filtrado en "páginas"
            def split_frame(input_df, rows):
                return [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]

            # Fijar el tamaño de página a 10 registros
            batch_size = 10
            total_pages = math.ceil(len(filtered_df) / batch_size)  # Calcular total de páginas según el DataFrame filtrado

            # Establecer la página actual en session_state (solo la primera vez)
            if "current_page" not in st.session_state:
                st.session_state["current_page"] = 1

            # Asegurarse de que la página actual no exceda el número total de páginas
            if st.session_state["current_page"] > total_pages:
                st.session_state["current_page"] = total_pages

            current_page = st.session_state["current_page"]

            # Ajustar el contenedor para mayor tamaño de tabla
            with st.container():
                header_cols = st.columns([2, 2, 2, 2, 2, 2, 2])  # Ajustar el ancho de las columnas
                header_cols[0].write("Tipo de Superestructura")
                header_cols[1].write("Tipo de Estribo")
                header_cols[2].write("Ancho Total")
                header_cols[3].write("Número de Tramos")
                header_cols[4].write("Longitud Total")
                header_cols[5].write("Costo Total")  
                header_cols[6].write("Acciones")   # Columna para los botones de acciones

                # Dividir el DataFrame filtrado en páginas
                pages = split_frame(filtered_df, batch_size)

                # Asegurarse de que la página actual no exceda el número total de páginas
                if current_page > total_pages:
                    current_page = total_pages
                    st.session_state["current_page"] = current_page

                current_page_data = pages[current_page - 1] if current_page <= total_pages else pd.DataFrame()

                # Mostrar los datos del current_page_data
                for index, row in current_page_data.iterrows():
                    cols = st.columns([2, 2, 2, 2, 2, 2, 1, 1])  # Ajustar las columnas

                    # Mostrar datos de la estimación
                    cols[0].text(row['structureType'])
                    cols[1].text(row['abutmentType'])
                    cols[2].text(row['total_Width'])
                    cols[3].text(row['number_of_Spans'])
                    cols[4].text(row['total_Length'])
                    cols[5].text(row['total_Cost'])

                     # Columna de acciones con botones separados
                    with cols[6]:
                        if st.button("✏️", key=f"edit_{row['id']}"):
                           st.session_state["edit_project"] = True
                           st.session_state["project_to_edit"] = row  # Guardar los datos de la fila completa
                           st.rerun()  # Recargar la app para mostrar el formulario de edición

                    with cols[7]:
                        if st.button("🗑️", key=f"delete_{row['id']}"):
                           handle_delete_project(row['id'])

                # Mostrar selector de página y número de página actual debajo de la tabla
                paginator = st.columns([2, 1])

                with paginator[0]:
                    st.markdown(f"Página **{current_page}** de **{total_pages}**")

                # Cambiar la página usando un selector de número
                with paginator[1]:
                    st.number_input(
                        "Seleccionar Página", 
                        min_value=1, 
                        max_value=total_pages if total_pages > 0 else 1,  # Asegurar que el máximo no sea 0
                        value=current_page,
                        step=1,
                        key="page_selector",
                        on_change=lambda: st.session_state.update({"current_page": st.session_state.page_selector}),
                        label_visibility="collapsed"
                    )
    else:
        st.error("Error al obtener las estimaciones desde el backend.")
