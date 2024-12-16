import bcrypt
import psycopg2

# Подключение к базе данных
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="123456"
)

# Хэширование пароля
hashed_password = bcrypt.hashpw("123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Запрос на обновление
query1 = """
        UPDATE users
        SET password = %(hashed_password)s
        WHERE role = 'admin'
    """
try:
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(query1, {"hashed_password": hashed_password})
finally:
    conn.close()
