from os import access

import streamlit
import pandas as pd
from fastapi.openapi.models import OAuth2
from streamlit import session_state
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
from sympy.codegen.ast import continue_
from datetime import timedelta, datetime, timezone

from passw import hash_password, verify_password
import services.users
import services.user
import services.regist
import settings
from services.auth import Authotize


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
registr = services.regist.Registration()
auth = Authotize()


@app.post("/register")
def register_user(email: str, password: str):
    users = services.users.get_users()
    if users["email"].isin([email]).any():
        raise HTTPException(status_code=400, detail="email already registered")
    user_id = registr.registr(pd.DataFrame({"email": [email], "password": [password]}))
    return {"message": "Registration is successful"}


@app.post("/token") #это одновременно логин и выдача токена
def login (email: str, password: str):
    if auth.auth(email,password):
        access_token_expires = timedelta(minutes=settings.JWT_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])
        access_token = jwt.encode(
            {"sub": email, "exp": datetime.now(timezone.utc) + access_token_expires}, settings.JWT_CONFIG["SECRET_KEY"], algorithm= settings.JWT_CONFIG["ALGORITHM"]
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
    except JWTError:
        raise credentials_exception

    user = services.user.get_user(email)
    if user is None:
        raise credentials_exception
    return user

@app.get("/profile")
def get_profile(user: dict = Depends(get_current_user)): #TODO тут надо еще в дикт преобразовать нормально датафрейм
    return user