import streamlit
import pandas as pd
from streamlit import session_state

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
        if auth.auth(email, password):
            streamlit.session_state["authenticated"] = True
            streamlit.session_state["username"] = email
            streamlit.success(f"Добро пожаловать, {email}!")
            streamlit.session_state.user = services.user.get_user(email)
            streamlit.session_state["admin"] = repositories.admin.get_admins(streamlit.session_state.user["user_id"].item())
            print(streamlit.session_state["admin"])
            streamlit.rerun()
        else:
            streamlit.error("Неверная почта или пароль!")
            
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
                if users["email"].isin([email]).any():
                    streamlit.error("Данная почта уже зарегистрирована!")
                else:
                    streamlit.success("Успешная регистрация")
                    streamlit.session_state["authenticated"] = True
                    #user = pd.DataFrame({"nickname" : nickname, "email" : email, "password" : password})
                    user_id = registr.registr(pd.DataFrame({"email": [email], "password": [password]}))
                    #user["user_id"] = user_id
                    user = pd.DataFrame({"user_id": [user_id], "email": [email], "password": [password]})
                    streamlit.session_state.user = user
                    streamlit.rerun()

def main():
    if not streamlit.session_state["authenticated"]:
        pg = streamlit.radio("Войдите или зарегистрируйтесь", ["Вход", "Регистрация"])
        if pg == "Вход":
            login()
        elif pg == "Регистрация":
            register()

    else:
        if streamlit.session_state["admin"]:
            print("admin mode enabled")
            page = streamlit.sidebar.radio(
                "Перейти к странице",
                ["Профиль", "Магазин","Корзина", "Админ"],
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
                ["Профиль", "Магазин","Корзина"],
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