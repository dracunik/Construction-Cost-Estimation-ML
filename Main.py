import streamlit as st
import requests
from streamlit_cookies_controller import CookieController
import time

# Configuración de la página
st.set_page_config(layout="wide")

cookie_controller = CookieController()

# URL de la API de login y de usuarios
API_URL_LOGIN = "https://tesis-backend-nxpy.onrender.com/login"
API_URL_USER = "https://tesis-backend-nxpy.onrender.com/user"

# Función para verificar credenciales en la API
def check_credentials(email, password):
    try:
        response = requests.post(API_URL_LOGIN, json={"email": email, "password": password})
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                return True, data.get("message"), data.get("user_id")
            else:
                return False, data.get("message"), None
        else:
            return False, "Error al comunicarse con la API.", None
    except Exception as e:
        return False, f"Ocurrió un error: {e}", None

# Función para obtener el rol del usuario filtrando por user_id
def get_user_role(user_id):
    try:
        response = requests.get(API_URL_USER)
        
        if response.status_code == 200:
            data = response.json()
            user = next((user for user in data if user["id"] == user_id), None)
            if user:
                return user.get("role")
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

# Función de logout
def logout():
    # Limpiar las cookies
    cookie_controller.remove("user_id")
    cookie_controller.remove("role")

    # Limpiar el session state
    st.session_state.clear()  # Limpia todas las variables del session_state
    
    time.sleep(2)

# Página de inicio de sesión
def login_page():
    st.title("Iniciar Sesión")
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión"):
        success, message, user_id = check_credentials(email, password)
        if success:
            role = get_user_role(user_id)
            cookie_controller.set('user_id', user_id)
            cookie_controller.set('role', role)
            st.success(message)
            time.sleep(0.5)
            st.rerun()  # Redirigir a la página principal después del login
        else:
            st.error(message)

# Página de inicio de sesión si no está autenticado
if cookie_controller.get('user_id'):
    user_role = cookie_controller.get('role')  # Obtener el rol del usuario desde las cookies

    # Definición de las páginas
    cost_estimations_page = st.Page(
        page="views/cost_estimations.py",
        title="Estimaciones de Costo",
        icon=":material/request_quote:"
    )

    requests_page = st.Page(
        page="views/requests.py",
        title="Solicitudes de Cambio",
        icon=":material/price_change:"
    )

    pages = [cost_estimations_page, requests_page]  # Por defecto, estas siempre están disponibles
    
    if user_role == 'admin':
        users_page = st.Page(
            page="views/users.py",
            title="Usuarios",
            icon=":material/group:"
        )
        pages.append(users_page)  # Agregar la página de usuarios solo si es ADMIN

    # Configuración de la navegación
    menu = st.navigation(pages=pages)

    # Barra de navegación
    st.logo("data/logo.png")

    # Mostrar el botón de log out
    if st.sidebar.button("Log Out"):  # Botón para cerrar sesión
        logout() 
        st.rerun()

    # Ejecutar navegación
    menu.run()

else:
    login_page()
    
