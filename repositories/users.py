import psycopg2
import psycopg2.extras
from settings import DB_CONFIG

def get_users() -> list[dict]:
    print("Receiving users")
    query = "SELECT user_id, email FROM users;"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()


def get_users_with_password() -> list[dict]:
    print("Receiving users")
    query = "SELECT password, email FROM users;"
    print(DB_CONFIG)
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()


def get_user_by_email(user_email) -> list[dict]:
    query = "SELECT user_id, email, balance FROM users WHERE email = %(email)s"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, {"email" : user_email})
            return cur.fetchall()

def get_user_balance_by_email(user_email) -> float:
    query = "SELECT balance FROM users WHERE email = %(email)s"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"email": user_email})
            result = cur.fetchone()
            if result is None:
                raise LookupError(f"Пользователь с email '{user_email}' не найден.")
            balance = result[0]
            if balance is None:
                raise ValueError(f"Баланс пользователя с email '{user_email}' равен NULL.")
            return balance


# user.py

def set_user_balance_by_email(user_email, new_balance: float) -> None:
    query = "UPDATE users SET balance = %(balance)s WHERE email = %(email)s"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {'balance': new_balance, 'email': user_email})
            if cur.rowcount == 0:
                raise LookupError(f"Пользователь с email '{user_email}' не найден.")