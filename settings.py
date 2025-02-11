import os
from dotenv import load_dotenv

load_dotenv("env.env")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

JWT_CONFIG = {
    "SECRET_KEY" : os.getenv("SECRET_KEY"),
    "ALGORITHM" : os.getenv("ALGORITHM"),
    "ACCESS_TOKEN_EXPIRE_MINUTES" : int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
}

POOL_MIN_CONN = int(os.getenv("POOL_MIN_CONN", 1))
POOL_MAX_CONN = int(os.getenv("POOL_MAX_CONN", 10))

