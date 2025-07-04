from pandas import DataFrame
import repositories.products
import pandas as pd
from services.redis_service import RedisService
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_service = RedisService()

def fetch_product_names_and_ids() -> pd.DataFrame:
    try:
        logger.info("Fetching product names and IDs...")
        
        # Try to get from cache first
        cached_products = redis_service.get_cached_products()
        if cached_products:
            logger.info("Retrieved products from cache")
            return pd.DataFrame(cached_products)
        
        # If not in cache, get from database
        products = repositories.products.get_products_names_id()
        
        if not products:
            logger.warning("No products found.")
            return pd.DataFrame(columns=["name", "product_id"])
        
        # Cache the results
        redis_service.cache_products(products)
        
        logger.info(f"Received {len(products)} products.")
        return pd.DataFrame(products)
    except Exception as e:
        logger.error(f"Error while fetching products: {e}")
        raise

def fetch_product_details_by_id(product_id: int) -> dict:
    """
    Получает всю информацию о продукте по его id
    :param product_id: id продукта для которого мы запрашиваем информацию.
    :return: словарь которых хранит детализированную информацию.
    """
    try:
        # Try to get from cache first
        cached_product = redis_service.redis_client.hgetall(f"product:{product_id}")
        
        # Check if we have all required fields
        required_fields = ['product_id', 'name', 'price', 'description', 
                         'warranty_period', 'stock_quantity', 'manufacturer_id']
        
        if cached_product:
            logger.info(f"Retrieved product {product_id} from cache")
            # Check if all required fields are present
            missing_fields = [field for field in required_fields if field not in cached_product]
            if missing_fields:
                logger.warning(f"Missing fields in cache: {missing_fields}")
                # Get fresh data from DB
                product_details = repositories.products.get_product_details_by_id(product_id)
                if product_details:
                    # Convert reviews to string before caching
                    if 'reviews' in product_details:
                        product_details['reviews'] = json.dumps(product_details['reviews'])
                    # Update cache with fresh data
                    redis_service.redis_client.hset(f"product:{product_id}", mapping=product_details)
                    redis_service.redis_client.expire(f"product:{product_id}", 3600)
                    # Convert reviews back to list before returning
                    if 'reviews' in product_details:
                        product_details['reviews'] = json.loads(product_details['reviews'])
                    return product_details
                return {}
            
            # Convert numeric strings back to numbers
            numeric_fields = {
                'price': float,
                'stock_quantity': int,
                'warranty_period': int,
                'product_id': int,
                'manufacturer_id': int
            }
            
            for field, converter in numeric_fields.items():
                if field in cached_product:
                    try:
                        cached_product[field] = converter(cached_product[field])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not convert {field} to {converter.__name__}: {e}")
                        # If conversion fails, get fresh data from DB
                        product_details = repositories.products.get_product_details_by_id(product_id)
                        if product_details:
                            # Convert reviews to string before caching
                            if 'reviews' in product_details:
                                product_details['reviews'] = json.dumps(product_details['reviews'])
                            # Update cache with fresh data
                            redis_service.redis_client.hset(f"product:{product_id}", mapping=product_details)
                            redis_service.redis_client.expire(f"product:{product_id}", 3600)
                            # Convert reviews back to list before returning
                            if 'reviews' in product_details:
                                product_details['reviews'] = json.loads(product_details['reviews'])
                            return product_details
                        continue
            
            # Convert reviews from string back to list if present
            if 'reviews' in cached_product:
                try:
                    cached_product['reviews'] = json.loads(cached_product['reviews'])
                except json.JSONDecodeError:
                    logger.warning("Could not parse reviews JSON")
                    cached_product['reviews'] = []
            
            return cached_product
        
        # If not in cache, get from database
        logger.info(f"Getting product {product_id} details from database")
        product_details = repositories.products.get_product_details_by_id(product_id)
        
        if not product_details:
            logger.warning(f"No product found for ID: {product_id}")
            return {}
        
        # Convert reviews to string before caching
        if 'reviews' in product_details:
            product_details['reviews'] = json.dumps(product_details['reviews'])
            
        # Cache the result
        redis_service.redis_client.hset(f"product:{product_id}", mapping=product_details)
        redis_service.redis_client.expire(f"product:{product_id}", 3600)  # Cache for 1 hour
        
        # Convert reviews back to list before returning
        if 'reviews' in product_details:
            product_details['reviews'] = json.loads(product_details['reviews'])
        
        logger.info(f"Received product details for ID: {product_id}")
        return product_details
    except Exception as e:
        logger.error(f"Error while fetching product details: {e}")
        raise


def add_product_to_user_cart(user_id: int, product_id: int, quantity: int) -> None:
    """
    функция - обертка для того чтобы добавлять товары в корзину пользователя

    :param user_id: ID of the user.
    :param product_id: ID of the product to add.
    :param quantity: Quantity of the product to add.
    """
    try:
        repositories.products.add_product_to_cart(user_id, product_id, quantity)
        logger.info("Product added to cart successfully.")
    except Exception as e:
        logger.error(f"Error in add_product_to_user_cart: {e}")
        raise

def check_product_stock(product_id: int) -> int:
    """
    Обертка для функции peek_products_stock. Проверяет, сколько товара доступно на складе.

    :param product_id: ID продукта.
    :return: количество доступного товара.
    """
    try:
        stock_quantity = repositories.products.peek_products_stock(product_id)
        return stock_quantity
    except ValueError as e:
        logger.error(f"Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while checking stock for product ID {product_id}: {e}")
        raise

def reduce_product_stock(product_id: int, quantity: int) -> None:
    """
    Обертка для функции decrease_product_stock. Уменьшает количество товара на складе.

    :param product_id: ID продукта.
    :param quantity: Количество, на которое нужно уменьшить.
    """
    try:
        repositories.products.decrease_product_stock(product_id, quantity)
        logger.info(f"Successfully decreased stock for product ID {product_id} by {quantity}.")
    except ValueError as e:
        logger.error(f"Stock decrease error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while decreasing stock for product ID {product_id}: {e}")
        raise

def add_new_product(name: str, price: float, description: str, warranty_period: int, manufacturer_id: int, stock_quantity: int) -> int:
    """
    Обертка для функции добавления нового продукта в базу данных.

    :param name: Название продукта.
    :param price: Цена продукта.
    :param description: Описание продукта.
    :param warranty_period: Гарантийный срок.
    :param manufacturer_id: ID производителя.
    :param stock_quantity: Количество на складе.
    :return: ID нового продукта.
    """
    try:
        product_id = repositories.products.add_new_product(name, price, description, warranty_period, manufacturer_id, stock_quantity)
        logger.info(f"Product '{name}' added successfully with ID: {product_id}.")
        return product_id
    except Exception as e:
        logger.error(f"Error while adding new product: {e}")
        raise

def filter_products(category: str = None, min_price: float = None, max_price: float = None) -> pd.DataFrame:
    """
    Фильтрация товаров по параметрам
    :param category: Категория товара
    :param min_price: Минимальная цена
    :param max_price: Максимальная цена
    :return: DataFrame с отфильтрованными товарами
    """
    try:
        # Создаем ключ для кеширования на основе параметров фильтрации
        filter_key = f"filter:{category}:{min_price}:{max_price}"
        
        # Проверяем кеш
        cached_result = redis_service.get_temporary_data(filter_key)
        if cached_result:
            logger.info("Получены отфильтрованные товары из кеша")
            return pd.DataFrame(cached_result)
        
        # Получаем все товары
        products = repositories.products.get_products_names_id()
        
        # Применяем фильтры
        filtered_products = []
        for product in products:
            if category and product.get('category') != category:
                continue
            if min_price and product.get('price', 0) < min_price:
                continue
            if max_price and product.get('price', 0) > max_price:
                continue
            filtered_products.append(product)
        
        # Кешируем результат
        redis_service.cache_temporary_data(filter_key, filtered_products)
        
        logger.info(f"Отфильтровано {len(filtered_products)} товаров")
        return pd.DataFrame(filtered_products)
    except Exception as e:
        logger.error(f"Ошибка при фильтрации товаров: {e}")
        raise