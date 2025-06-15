from pandas import DataFrame
import repositories.cart
import pandas as pd
from services.redis_service import RedisService

redis_service = RedisService()

def fetch_user_cart(user_id: int) -> pd.DataFrame:
    """
    Обертка для получения содержимого корзины пользователя.

    :param user_id: ID пользователя, чью корзину нужно получить.
    :return: DataFrame с данными о содержимом корзины.
    """
    try:
        print(f"Fetching cart for user ID: {user_id}")
        
        # Try to get from cache first
        cached_cart = redis_service.get_cached_cart(str(user_id))
        if cached_cart:
            print("Retrieved cart from cache")
            return pd.DataFrame(cached_cart)
        
        # If not in cache, get from database
        cart_items = repositories.cart.get_user_cart(user_id)
        
        if not cart_items:
            print("Cart is empty.")
            return pd.DataFrame(columns=["cart_id", "product_id", "quantity", "added_date",
                                         "product_name", "price", "description",
                                         "stock_quantity", "warranty_period"])
        
        # Cache the results
        redis_service.cache_cart(str(user_id), cart_items)
        
        print(f"Received {len(cart_items)} items in the cart.")
        return pd.DataFrame(cart_items)
    except Exception as e:
        print(f"Error while fetching user cart: {e}")
        raise


def clear_cart(user_id: int) -> None:
    """
    Обертка для очистки корзины пользователя.

    :param user_id: ID пользователя, чью корзину нужно очистить.
    """
    try:
        print(f"Clearing cart for user ID: {user_id}")
        repositories.cart.clear_user_cart(user_id)
        
        # Invalidate cart cache
        redis_service.redis_client.delete(f"cart:{user_id}")
        
        print("Cart cleared successfully.")
    except Exception as e:
        print(f"Error while clearing user cart: {e}")
        raise


def update_cart_item(user_id: int, product_id: int, new_quantity: int) -> None:
    """
    Обертка для обновления количества товара в корзине пользователя.

    :param user_id: ID пользователя.
    :param product_id: ID продукта, который нужно обновить.
    :param new_quantity: Новое количество товара. Если 0, товар будет удален.
    """
    try:
        print(f"Updating quantity for product {product_id} in user {user_id}'s cart to {new_quantity}")
        repositories.cart.update_cart_item_quantity(user_id, product_id, new_quantity)
        
        # Invalidate cart cache
        redis_service.redis_client.delete(f"cart:{user_id}")
        
        print("Cart item updated successfully.")
    except Exception as e:
        print(f"Error while updating cart item: {e}")
        raise


def calculate_cart_total(user_id: int) -> dict:
    """
    Обертка для расчета общей стоимости товаров в корзине пользователя.

    :param user_id: ID пользователя.
    :return: Словарь с общей стоимостью и количеством товаров.
    """
    try:
        print(f"Calculating cart total for user ID: {user_id}")
        cart_total = repositories.cart.get_cart_total(user_id)
        print(f"Cart total calculated: {cart_total}")
        return cart_total
    except Exception as e:
        print(f"Error while calculating cart total: {e}")
        raise


def process_checkout(user_id: int) -> int:
    """
    Обертка для оформления заказа. Переносит товары из корзины в таблицу заказов.

    :param user_id: ID пользователя, оформляющего заказ.
    :return: ID созданного заказа.
    """
    try:
        print(f"Processing checkout for user ID: {user_id}")
        order_id = repositories.cart.checkout_cart(user_id)
        
        # Invalidate cart cache
        redis_service.redis_client.delete(f"cart:{user_id}")
        
        # Update order status in Redis
        redis_service.update_order_status(str(order_id), "Pending", str(user_id))
        
        print(f"Checkout successful. Order ID: {order_id}")
        return order_id
    except ValueError as e:
        print(f"Checkout error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during checkout for user ID {user_id}: {e}")
        raise