import psycopg2
import psycopg2.extras
from settings import DB_CONFIG
from pandas import DataFrame


def get_products_names_id() -> list[dict]:
    print("Receiving products")
    query = "SELECT name, product_id FROM products;"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()


def get_product_details_by_id(product_id: int) -> dict:
    print(f"Receiving details for product_id: {product_id}")
    query = """
        SELECT 
            p.product_id,
            p.name AS product_name,
            p.price,
            p.description,
            p.warranty_period,
            p.stock_quantity,
            m.manufacturer_id,
            m.name AS manufacturer_name,
            m.country AS manufacturer_country,
            COALESCE(
                json_agg(
                    json_build_object(
                        'review_id', r.review_id,
                        'rating', r.rating,
                        'review_text', r.review_text,
                        'review_date', r.review_date,
                        'user_id', r.user_id
                    )
                ) FILTER (WHERE r.review_id IS NOT NULL), 
                '[]'
            ) AS reviews
        FROM products p
        LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id
        LEFT JOIN reviews r ON p.product_id = r.product_id
        WHERE p.product_id = %s
        GROUP BY p.product_id, m.manufacturer_id;
    """

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (product_id,))
            result = cur.fetchone()
            return result if result else {}



def add_product_to_cart(user_id: int, product_id: int, quantity: int) -> None:
    print(f"Adding product {product_id} to cart for user {user_id} with quantity {quantity}")
    query = """
        INSERT INTO carts (user_id, product_id, quantity, added_date)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (user_id, product_id) 
        DO UPDATE SET quantity = carts.quantity + EXCLUDED.quantity;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, product_id, quantity))
            conn.commit()


def decrease_product_stock(product_id: int, quantity: int) -> None:
    print(f"Decreasing stock for product {product_id} by {quantity}")
    query = """
        UPDATE products
        SET stock_quantity = stock_quantity - %s
        WHERE product_id = %s AND stock_quantity >= %s;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (quantity, product_id, quantity))
            if cur.rowcount == 0:
                raise ValueError("Not enough stock to fulfill the request")
            conn.commit()

def peek_products_stock(product_id: int) -> int:
    print(f"Checking stock for product {product_id}")
    query = "SELECT stock_quantity FROM products WHERE product_id = %s;"
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))
            result = cur.fetchone()
            if result is None:
                raise ValueError(f"Product with id {product_id} not found")
            return result[0]


def add_new_product(name: str, price: float, description: str, warranty_period: int, manufacturer_id: int, stock_quantity: int) -> int:
    """
    Добавить новый продукт в таблицу products.
    Возвращает ID нового продукта.
    """
    print(f"Adding new product: {name}")
    query = """
        INSERT INTO products (name, price, description, warranty_period, manufacturer_id, stock_quantity)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING product_id;
    """
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (name, price, description, warranty_period, manufacturer_id, stock_quantity))
            product_id = cur.fetchone()[0]
            conn.commit()
            return product_id