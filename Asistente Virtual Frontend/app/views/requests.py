import streamlit as st
import pandas as pd
import requests
import math
from streamlit_cookies_controller import CookieController
import time

cookie_controller = CookieController()

# URLs de la API
API_URL_REQUESTS = "https://tesis-backend-nxpy.onrender.com/request"
API_URL_USERS = "https://tesis-backend-nxpy.onrender.com/user"

user_role = cookie_controller.get('role')
user_id = cookie_controller.get('user_id')

# Función para obtener solicitudes de la API
def get_requests():
    response = requests.get(API_URL_REQUESTS)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Error al obtener solicitudes de la API.")
        return pd.DataFrame()

# Función para obtener usuarios de la API
def get_users():
    response = requests.get(API_URL_USERS)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Error al obtener usuarios de la API.")
        return pd.DataFrame()

# Función para actualizar el estado de la solicitud en la API
def update_request_status(row, new_status):
    # Convertir la fila a un diccionario
    row_dict = row.to_dict()

    # Cambiar el estado en el diccionario
    row_dict['status'] = new_status

    # Eliminar claves con valores no serializables (por ejemplo, NaN o valores complejos)
    # Convertimos en cadenas o eliminamos cualquier valor no serializable
    for key, value in row_dict.items():
        if isinstance(value, pd.Timestamp):  # Si es un Timestamp, convertirlo a string
            row_dict[key] = value.isoformat()
        elif pd.isna(value):  # Si es NaN, lo eliminamos
            row_dict[key] = None
    
    # Realizar la solicitud PUT para actualizar el estado
    response = requests.put(f"{API_URL_REQUESTS}/{row_dict['id']}", json=row_dict)

    if response.status_code == 200:
        st.success(f"Solicitud actualizada con éxito.")
    else:
        st.error(f"Error al actualizar el estado de la solicitud: {response.status_code}")

# Cargar datos
df_requests = get_requests()
# Filtrar solicitudes según el rol del usuario
if user_role != 'admin':
    # Si el rol es 'usuario', solo mostrar las solicitudes cuyo 'user_id' coincida con el 'user_id' en la cookie
    df_requests = df_requests[df_requests['user_id'] == user_id]

df_users = get_users()

# Invertir el DataFrame para que el último registro sea el primero
df_requests = df_requests.iloc[::-1].reset_index(drop=True)

# Mapear `user_id` a `name` en df_requests
user_dict = df_users.set_index("id")["name"].to_dict()
df_requests["solicitante"] = df_requests["user_id"].map(user_dict)

# Título de la página
st.title("Lista de Solicitudes")

# Search bar para buscar por tipo de solicitud, nombre de solicitante o estado
with st.container():
    search_col, _ = st.columns([4, 1])

    with search_col:
        search_term = st.text_input("Buscar por tipo de solicitud o solicitante...", key="search", placeholder="Buscar por tipo de solicitud, estado o solicitante...", label_visibility="collapsed")

# Filtrar DataFrame según el término de búsqueda
if search_term:
    filtered_df = df_requests[
        df_requests['request_type'].str.contains(search_term, case=False) | 
        df_requests['solicitante'].str.contains(search_term, case=False) |
        df_requests['status'].str.contains(search_term, case=False)
    ]
else:
    filtered_df = df_requests

# Verificar si el DataFrame filtrado está vacío
if filtered_df.empty:
    st.warning("No se encontraron solicitudes que coincidan con la búsqueda.")
else:
    # Paginador: Dividir DataFrame filtrado en "páginas"
    def split_frame(input_df, rows):
        return [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]

    batch_size = 5
    total_pages = math.ceil(len(filtered_df) / batch_size)

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = 1

    def update_page():
        st.session_state["current_page"] = st.session_state["page_selector"]

    if st.session_state["current_page"] > total_pages and total_pages > 0:
        st.session_state["current_page"] = total_pages

    current_page = st.session_state["current_page"]

    with st.container():
        header_cols = st.columns([3, 3, 3, 3, 1, 1, 1])
        header_cols[0].write("Tipo de Solicitud")
        header_cols[1].write("Solicitante")
        header_cols[2].write("Estado")
        header_cols[3].write("Fecha de Solicitud")
        header_cols[4].write("Aprobar")
        header_cols[5].write("Rechazar")
        header_cols[6].write("Ver")

        pages = split_frame(filtered_df, batch_size)

        if current_page > total_pages:
            current_page = total_pages
            st.session_state["current_page"] = current_page

        current_page_data = pages[current_page - 1] if current_page <= total_pages else pd.DataFrame()

        # Mostrar datos de la página actual
        for index, row in current_page_data.iterrows():
            cols = st.columns([3, 3, 3, 3, 1, 1, 1])

            cols[0].text(row['request_type'])
            cols[1].text(row['solicitante'])
            cols[2].text(row['status'])
            cols[3].text(row['date'])

            # Mostrar "Aprobar" y "Rechazar" solo si está "Pendiente"
            if row['status'] == "Pendiente" and row['request_type'] in ["Edición", "Eliminación"] and user_role=='admin':
                with cols[4]:
                    if st.button("✔️", key=f"approve_{row['id']}"):
                        update_request_status(row,'Aprobado')
                        time.sleep(0.5) 
                        st.rerun()
                with cols[5]:
                    if st.button("❌", key=f"reject_{row['id']}"):
                        update_request_status(row,'Rechazado')
                        time.sleep(0.5) 
                        st.rerun()
            else:
                cols[4].text("-")
                cols[5].text("-")

            # Mostrar "Ver" solo si es de tipo "Edición" (sin importar el estado)
            if row['request_type'] == "Edición":
                with cols[6]:
                    if st.button("👁️", key=f"view_{row['id']}"):
                        # Almacenar el `request_id` seleccionado para mostrar detalles
                        st.session_state["selected_request"] = row
                        st.rerun()
            else:
                cols[6].text("-")

    # Paginador de la página
    paginator = st.columns([2, 1])

    with paginator[0]:
        st.markdown(f"Página **{current_page}** de **{total_pages}**")

    with paginator[1]:
        st.number_input(
            "Seleccionar Página", 
            min_value=1, 
            max_value=total_pages if total_pages > 0 else 1,
            value=current_page,
            step=1,
            key="page_selector",
            on_change=update_page,
            label_visibility="collapsed"
        )

# Detalles de solicitud seleccionada
if "selected_request" in st.session_state and st.session_state["selected_request"] is not None:
    st.write("### Detalle de Solicitud")
    selected_request = st.session_state["selected_request"]

    col1, col2 = st.columns(2)
        
    # Mostrar ambas versiones para "Edición" y solo la original para "Eliminación"
    with col1:
        st.subheader("Predicción Original")
        st.json(selected_request["original_prediction_object"]["input_list"])

    if selected_request["request_type"] == "Edición":
        with col2:
            st.subheader("Predicción Nueva")
            st.json(selected_request["new_prediction_object"]["input_list"])
    else:
        st.warning("No se encontró la predicción original para la solicitud seleccionada.")

    st.session_state["selected_request"] = None
