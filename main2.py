from os import access

import streamlit as st
import pandas as pd
from fastapi.openapi.models import OAuth2
from streamlit import session_state
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
from sympy.codegen.ast import continue_
from datetime import timedelta, datetime, timezone
import requests

from passw import hash_password, verify_password
import services.users
import services.user
import services.regist
import settings
from services.auth import Authotize
from services.redis_service import RedisService


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
registr = services.regist.Registration()
auth = Authotize()
redis_service = RedisService()
API_URL="http://127.0.0.1:8000"


@app.post("/register")
def register_user(email: str, password: str):
    users = services.users.get_users()
    if users["email"].isin([email]).any():
        raise HTTPException(status_code=400, detail="email already registered")
    
    user_id = registr.registr(pd.DataFrame({"email": [email], "password": [password]}))
    
    # Создаем токен для нового пользователя
    access_token_expires = timedelta(minutes=settings.JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])
    access_token = jwt.encode(
        {"sub": email, "exp": datetime.now(timezone.utc) + access_token_expires},
        settings.JWT_CONFIG["SECRET_KEY"],
        algorithm=settings.JWT_CONFIG["ALGORITHM"]
    )
    
    # Store token in Redis
    redis_service.store_token(
        str(user_id),
        access_token,
        settings.JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"] * 60
    )
    
    # Cache initial user profile
    user_data = services.user.get_user(email)
    redis_service.cache_data(f"profile:{user_id}", user_data.to_dict(orient="records")[0])
    
    return {
        "message": "Registration is successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/token") #это одновременно логин и выдача токена
def login_api (email: str, password: str):
    if auth.auth(email,password):
        access_token_expires = timedelta(minutes=settings.JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])
        access_token = jwt.encode(
            {"sub": email, "exp": datetime.now(timezone.utc) + access_token_expires}, settings.JWT_CONFIG["SECRET_KEY"], algorithm= settings.JWT_CONFIG["ALGORITHM"]
        )
        
        # Store token in Redis
        user = services.user.get_user(email)
        redis_service.store_token(
            str(user["user_id"].item()),
            access_token,
            settings.JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"] * 60
        )
        
        return {"message": "Successful authorization", "access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail = "Wrong email or password")

async def get_current_user(token: str= Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code= 401, detail="Invalid token")
    try:
        payload = jwt.decode(token, settings.JWT_CONFIG["SECRET_KEY"], algorithms=settings.JWT_CONFIG["ALGORITHM"])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        # Verify token in Redis
        user = services.user.get_user(email)
        stored_token = redis_service.get_token(str(user["user_id"].item()))
        if not stored_token or stored_token != token:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    user = services.user.get_user(email)
    if user is None:
        raise credentials_exception
    return user.to_dict(orient="records")[0]

@app.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    # Cache user profile data
    cached_profile = redis_service.get_cached_data(f"profile:{user['user_id']}")
    if cached_profile:
        return cached_profile
        
    profile_data = user
    redis_service.cache_data(f"profile:{user['user_id']}", profile_data)
    return profile_data



def login_page():
    st.title("Авторизация")
    st.write("Введите почту и пароль")
    email = st.text_input("Почта")
    password = st.text_input("Пароль", type = "password")

    if st.button("Войти"):
        response = requests.post(f"{API_URL}/token", params={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["authenticated"] = True
            
            # Store session in Redis
            redis_service.store_session(
                st.session_state["token"],
                {"email": email, "authenticated": True}
            )
            
            st.success("Вы успешно вошли!")
        else:
            st.error("Неверный email или пароль")



def profile():
    st.title("Профиль")

    if "token" not in st.session_state:
        st.error("Сначала войдите в систему")
        return

    # Check session in Redis
    session_data = redis_service.get_session(st.session_state["token"])
    if not session_data:
        st.error("Сессия истекла. Пожалуйста, войдите снова.")
        st.session_state["authenticated"] = False
        return

    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.get(f"{API_URL}/profile", headers=headers)

    if response.status_code == 200:
        user = response.json()
        st.write(f"Ваш email: {user['email']}")
    else:
        st.error("Ошибка при получении профиля")