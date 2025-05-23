import streamlit
import pandas as pd
from streamlit import session_state
import requests

from services.auth import Authotize
import services.users
import services.regist
import services.user
import repositories.admin
from pages.profile import show_profile_page
from pages.store import show_store_page
from pages.cart_page import show_cart_page
from pages.admin import show_admin_page


auth = Authotize()
users = services.users.get_users()
registr = services.regist.Registration()


def login():
    streamlit.title("Авторизация")
    streamlit.write("Введите почту и пароль:")

    email = streamlit.text_input("Почта")
    password = streamlit.text_input("Пароль", type="password")
    if streamlit.button("Войти"):
        try:
            # Используем API endpoint для авторизации
            response = requests.post(
                "http://127.0.0.1:8000/token",
                params={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                streamlit.session_state["authenticated"] = True
                streamlit.session_state["username"] = email
                streamlit.session_state["token"] = data["access_token"]
                streamlit.session_state["user_id"] = data["user_id"]
                
                # Получаем сессионные данные
                session_response = requests.get(
                    "http://127.0.0.1:8000/session",
                    headers={"Authorization": f"Bearer {data['access_token']}"}
                )
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    streamlit.session_state["session_data"] = session_data
                
                streamlit.success(f"Добро пожаловать, {email}!")
                
                # Получаем данные пользователя
                user = services.user.get_user(email)
                streamlit.session_state.user = user
                streamlit.session_state["admin"] = repositories.admin.get_admins(streamlit.session_state.user["user_id"].item())
                streamlit.rerun()
            else:
                streamlit.error("Неверная почта или пароль!")
        except Exception as e:
            streamlit.error(f"Ошибка при авторизации: {str(e)}")

def logout():
    """Logout user and clear session"""
    if "token" in streamlit.session_state:
        try:
            response = requests.post(
                "http://127.0.0.1:8000/logout",
                headers={"Authorization": f"Bearer {streamlit.session_state['token']}"}
            )
            if response.status_code == 200:
                # Очищаем все данные сессии
                for key in list(streamlit.session_state.keys()):
                    del streamlit.session_state[key]
                streamlit.session_state["authenticated"] = False
                streamlit.rerun()
        except Exception as e:
            streamlit.error(f"Ошибка при выходе: {str(e)}")

def register():
    streamlit.title("Регистрация")
    streamlit.write("Введите почту")
    email = streamlit.text_input("Почта")
    streamlit.write("Введите пароль")
    password = streamlit.text_input("Пароль", type="password")
    streamlit.write("Подтвердите пароль")
    second_password = streamlit.text_input("Подтверждение пароля", type="password")

    if streamlit.button("Зарегистрироваться"):
        if (not(email) or not(password) or not(second_password)):
            streamlit.error("Введите требуемые значения!")
        else:
            if (password != second_password):
                streamlit.error("Пароли не совпадают!")
            else:
                try:
                    # Используем API endpoint для регистрации
                    response = requests.post(
                        "http://127.0.0.1:8000/register",
                        params={"email": email, "password": password}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        streamlit.success("Успешная регистрация")
                        streamlit.session_state["authenticated"] = True
                        streamlit.session_state["username"] = email
                        streamlit.session_state["token"] = data["access_token"]
                        
                        # Получаем данные пользователя
                        user = services.user.get_user(email)
                        streamlit.session_state.user = user
                        streamlit.rerun()
                    else:
                        error_data = response.json()
                        streamlit.error(error_data.get("detail", "Ошибка при регистрации"))
                except Exception as e:
                    streamlit.error(f"Ошибка при регистрации: {str(e)}")

def main():
    if not streamlit.session_state.get("authenticated", False):
        pg = streamlit.radio("Войдите или зарегистрируйтесь", ["Вход", "Регистрация"])
        if pg == "Вход":
            login()
        elif pg == "Регистрация":
            register()
    else:
        # Добавляем кнопку выхода в сайдбар
        if streamlit.sidebar.button("Выйти"):
            logout()
            return

        if streamlit.session_state.get("admin"):
            page = streamlit.sidebar.radio(
                "Перейти к странице",
                ["Профиль", "Магазин", "Корзина", "Админ"],
            )

            if page == "Профиль":
                show_profile_page()
            if page == "Магазин":
                show_store_page()
            if page == "Корзина":
                show_cart_page()
            if page == "Админ":
                show_admin_page()

        else:
            page = streamlit.sidebar.radio(
                "Перейти к странице",
                ["Профиль", "Магазин", "Корзина"],
            )

            if page == "Профиль":
                show_profile_page()
            if page == "Магазин":
                show_store_page()
            if page == "Корзина":
                show_cart_page()


if "authenticated" not in streamlit.session_state:
    streamlit.session_state["authenticated"] = False

if "admin" not in streamlit.session_state:
    streamlit.session_state["admin"] = False

if "user" not in streamlit.session_state:
    streamlit.session_state.user = pd.DataFrame(
        columns = ["user_id", "email", "balance"]
    )

if __name__ == "__main__":
    main()