import psycopg2
import psycopg2.extras
from settings import DB_CONFIG


def get_admins(admin_id) -> bool:
    query = """SELECT user_id FROM users WHERE user_id = %(admin_id)s AND role = 'admin'"""

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"admin_id": admin_id})
            return (cur.fetchone() != None)

