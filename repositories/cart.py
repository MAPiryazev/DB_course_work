import psycopg2
import psycopg2.extras
from settings import DB_CONFIG
from pandas import DataFrame


def get_user_cart(user_id: int) -> list[dict]:
    """
    Получить содержимое корзины пользователя.
    Возвращает список продуктов в корзине пользователя с указанием количества и информации о продуктах.
    """
    print(f"Fetching cart for user_id: {user_id}")
    query = """
        SELECT 
            c.cart_id,
            c.product_id,
            c.quantity,
            c.added_date,
            p.name AS product_name,
            p.price,
            p.description,
            p.stock_quantity,
            p.warranty_period
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            return cur.fetchall()


def clear_user_cart(user_id: int) -> None:
    """
    Очистить корзину пользователя.
    """
    print(f"Clearing cart for user_id: {user_id}")
    query = "DELETE FROM carts WHERE user_id = %s;"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            conn.commit()


def update_cart_item_quantity(user_id: int, product_id: int, new_quantity: int) -> None:
    """
    Обновить количество товара в корзине пользователя.
    Если количество равно 0, товар удаляется из корзины.
    """
    print(f"Updating cart item quantity for user_id: {user_id}, product_id: {product_id}, new_quantity: {new_quantity}")
    if new_quantity == 0:
        # Удаляем товар из корзины
        query = "DELETE FROM carts WHERE user_id = %s AND product_id = %s;"
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, product_id))
                conn.commit()
    else:
        # Обновляем количество товара
        query = """
            UPDATE carts
            SET quantity = %s
            WHERE user_id = %s AND product_id = %s;
        """
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (new_quantity, user_id, product_id))
                conn.commit()


def get_cart_total(user_id: int) -> dict:
    """
    Рассчитать общую стоимость товаров в корзине пользователя.
    Возвращает общую стоимость и количество товаров.
    """
    print(f"Calculating cart total for user_id: {user_id}")
    query = """
        SELECT 
            SUM(p.price * c.quantity) AS total_price,
            SUM(c.quantity) AS total_quantity
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            return result if result else {'total_price': 0, 'total_quantity': 0}


def checkout_cart(user_id: int) -> int:
    """
    Переносит товары из корзины пользователя в таблицу orders и создает запись о новом заказе.
    Возвращает ID нового заказа.
    """
    print(f"Checking out cart for user_id: {user_id}")

    # SQL-запросы
    query_create_order = """
        INSERT INTO orders (user_id, order_date, status)
        VALUES (%s, NOW(), 'Pending')
        RETURNING order_id;
    """
    query_get_cart_items = """
        SELECT product_id, quantity
        FROM carts
        WHERE user_id = %s;
    """
    query_insert_order_items = """
        INSERT INTO order_items (order_id, product_id, quantity)
        VALUES (%s, %s, %s);
    """
    query_clear_cart = """
        DELETE FROM carts
        WHERE user_id = %s;
    """

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            try:
                # 1. Создаем новый заказ
                cur.execute(query_create_order, (user_id,))
                order_id = cur.fetchone()[0]

                # 2. Получаем товары из корзины
                cur.execute(query_get_cart_items, (user_id,))
                cart_items = cur.fetchall()

                if not cart_items:
                    raise ValueError("Cart is empty. Cannot create an order.")

                # 3. Переносим товары из корзины в order_items
                for item in cart_items:
                    product_id, quantity = item
                    cur.execute(query_insert_order_items, (order_id, product_id, quantity))

                # 4. Очищаем корзину
                cur.execute(query_clear_cart, (user_id,))

                # Фиксируем все изменения
                conn.commit()

                return order_id

            except Exception as e:
                # В случае ошибки откатываем транзакцию
                conn.rollback()
                print(f"Error during checkout: {e}")
                raise

