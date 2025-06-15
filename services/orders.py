from services.notifications import notify_order_status_change, notify_new_order
import pandas as pd
import psycopg2
from settings import DB_CONFIG
import logging
from datetime import datetime
from services.order_status import PENDING, ALL_STATUSES

logger = logging.getLogger(__name__)

def get_all_orders():
    """Получить все заказы"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
        SELECT o.order_id, o.user_id, u.email, o.order_date, o.status
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_date DESC
        """
        orders_df = pd.read_sql_query(query, conn)
        conn.close()
        return orders_df
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise

def update_order_status(order_id: int, new_status: str):
    """Обновить статус заказа"""
    try:
        if new_status not in ALL_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {ALL_STATUSES}")
            
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        UPDATE orders
        SET status = %s
        WHERE order_id = %s
        """
        cursor.execute(query, (new_status, order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Order {order_id} status updated to {new_status}")
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise

def get_user_orders(user_id: int):
    """Получить заказы пользователя"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = """
        SELECT order_id, order_date, status
        FROM orders
        WHERE user_id = %s
        ORDER BY order_date DESC
        """
        orders_df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return orders_df
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        raise

def create_order(user_id: int, total_amount: float) -> int:
    """Создать новый заказ"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Создаем заказ с английским статусом
        query = """
        INSERT INTO orders (user_id, order_date, status)
        VALUES (%s, %s, %s)
        RETURNING order_id
        """
        cursor.execute(query, (user_id, datetime.now(), PENDING))
        order_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Created new order {order_id} for user {user_id}")
        return order_id
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise 