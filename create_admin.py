import psycopg2
import bcrypt
from settings import DB_CONFIG

def create_admin(email: str, password: str):
    # Хешируем пароль
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    # SQL запрос для создания админа
    query = """
        INSERT INTO users (email, password, balance, role)
        VALUES (%s, %s, 0, 'admin')
        RETURNING user_id
    """
    
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (email, hashed_password))
                user_id = cur.fetchone()[0]
                print(f"Admin user created successfully with ID: {user_id}")
                return user_id
    except psycopg2.IntegrityError:
        print(f"Error: Email {email} is already registered")
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    # Запрашиваем данные для создания админа
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
    create_admin(email, password) 