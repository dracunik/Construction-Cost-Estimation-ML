import streamlit as st
import pandas as pd
import requests
import math
import time

# URL de la API
API_URL = "https://tesis-backend-nxpy.onrender.com/user"

# Inicializar el estado de la sesión para la navegación y la edición
if "create_user" not in st.session_state:
    st.session_state["create_user"] = False

if "edit_user" not in st.session_state:
    st.session_state["edit_user"] = False

if "user_to_edit" not in st.session_state:
    st.session_state["user_to_edit"] = None

# Función para obtener usuarios de la API
def get_users():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Error al obtener usuarios de la API.")
        return pd.DataFrame()

#Función para resetear estado de la sesión
def reset_session_state():
    st.session_state["create_user"] = False
    st.session_state["edit_user"] = False
    st.session_state["user_to_edit"] = None
    st.rerun()

# Función para manejar la creación o edición de usuarios
def handle_user_form():
    # Determinar si estamos creando o editando
    is_edit = st.session_state["edit_user"]
    user_data = st.session_state["user_to_edit"]

    # Si es una edición, pre-poblar los campos con los datos del usuario a editar
    if is_edit and user_data is not None:
        st.title("Editar Usuario")
        user_id = user_data['id']
        user_role = user_data['role']
        user_name = st.text_input("Nombre Completo:", user_data['name'])
        user_email = st.text_input("Correo:", user_data['email'])
        user_phone = st.text_input("Celular:", user_data['phone'])
        user_state = st.selectbox("Estado:", ["Activo", "Inactivo"], index=0 if "Activo" in user_data['state'] else 1)
        user_password = st.text_input("Contraseña:", type='password', value=user_data['password'])
    else:
        st.title("Crear Usuario")
        user_name = st.text_input("Nombre Completo:")
        user_email = st.text_input("Correo:")
        user_phone = st.text_input("Celular:")
        user_state = st.selectbox("Estado:", ["Activo", "Inactivo"])
        user_password = st.text_input("Contraseña:", type='password')

    # Botones para guardar y cancelar
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Guardar Usuario"):
            user = {
                "name": user_name,
                "email": user_email,
                "phone": user_phone,
                "state": user_state,
                "password": user_password,
                "role": 'usuario'
            }

            # Si es una edición, actualizar el usuario en la API
            if is_edit:
                user["id"] = user_data['id']
                user["role"] = user_data['role']
                response = requests.put(f"{API_URL}/{user_data['id']}", json=user)
                if response.status_code == 200:
                    st.success("Usuario editado exitosamente.")
                    time.sleep(0.5) 
                    reset_session_state()
                else:
                    st.error("Error al editar el usuario.")
            else:
                # Crear el nuevo usuario en la API
                response = requests.post(f"{API_URL}/create", json=user)
                if response.status_code == 200:
                    st.success("Usuario creado exitosamente.")
                    time.sleep(0.5) 
                    reset_session_state()
                else:
                    st.error("Error al crear el usuario.")
            
    with col2:
        if st.button("Cancelar"):
            reset_session_state()

# Función para eliminar un usuario
def delete_user(id):
    response = requests.delete(f"{API_URL}/{id}")
    if response.status_code == 200:
        st.success(f"Usuario con correo {id} eliminado exitosamente.")
    else:
        st.error("Error al eliminar el usuario.")
    time.sleep(0.5) 
    st.rerun()

# Obtener usuarios de la API
df_users = get_users()
df_users = df_users.iloc[::-1].reset_index(drop=True)

# Si el usuario está en la página de creación o edición, mostrar el formulario
if st.session_state["create_user"] or st.session_state["edit_user"]:
    handle_user_form()
else:
    st.title("Lista de Usuarios")

    # Función para agregar el ícono de status
    def add_status_emojis(status):
        return "🟢 Activo" if status == "Activo" else "🔴 Inactivo"

    df_users['state'] = df_users['state'].apply(add_status_emojis)

    with st.container():
        search_col, create_col = st.columns([4, 1])

        with search_col:
            search_term = st.text_input("Buscar usuario (nombre o correo):", key="search", placeholder="Buscar usuario...", label_visibility="collapsed")

        with create_col:
            if st.button("Crear Nuevo Usuario"):
                st.session_state["create_user"] = True
                st.rerun()

    # Filtrar DataFrame según el término de búsqueda
    if search_term:
        filtered_df = df_users[df_users['name'].str.contains(search_term, case=False) | 
                               df_users['email'].str.contains(search_term, case=False)]
    else:
        filtered_df = df_users

    # Verificar si el DataFrame filtrado está vacío
    if filtered_df.empty:
        st.warning("No se encontraron usuarios que coincidan con la búsqueda.")
    else:
        # Paginador: Dividir DataFrame filtrado en "páginas"
        def split_frame(input_df, rows):
            return [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]

        batch_size = 10
        total_pages = math.ceil(len(filtered_df) / batch_size)

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = 1

        def update_page():
            st.session_state["current_page"] = st.session_state["page_selector"]

        if st.session_state["current_page"] > total_pages and total_pages > 0:
            st.session_state["current_page"] = total_pages

        current_page = st.session_state["current_page"]

        with st.container():
            header_cols = st.columns([4, 4, 4, 4, 1, 1])
            header_cols[0].write("Nombre Completo")
            header_cols[1].write("Correo")
            header_cols[2].write("Celular")
            header_cols[3].write("Estado")
            header_cols[4].write("Editar")
            header_cols[5].write("Eliminar")

            pages = split_frame(filtered_df, batch_size)

            if current_page > total_pages:
                current_page = total_pages
                st.session_state["current_page"] = current_page

            current_page_data = pages[current_page - 1] if current_page <= total_pages else pd.DataFrame()

            for index, row in current_page_data.iterrows():
                cols = st.columns([4, 4, 4, 4, 1, 1])

                cols[0].text(row['name'])
                cols[1].text(row['email'])
                cols[2].text(row['phone'])
                cols[3].text(row['state'])

                with cols[4]:
                    if st.button("✏️", key=f"edit_{row['email']}"):
                        st.session_state["edit_user"] = True
                        st.session_state["user_to_edit"] = row
                        st.rerun()

                with cols[5]:
                    if st.button("🗑️", key=f"delete_{row['id']}"):
                        delete_user(row['id'])

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
