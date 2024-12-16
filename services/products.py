from pandas import DataFrame
import repositories.products
import pandas as pd


def fetch_product_names_and_ids() -> pd.DataFrame:
    try:
        print("Fetching product names and IDs...")
        products = repositories.products.get_products_names_id()

        if not products:
            print("No products found.")
            return pd.DataFrame(columns=["name", "product_id"])

        print(f"Received {len(products)} products.")
        return pd.DataFrame(products)
    except Exception as e:
        print(f"Error while fetching products: {e}")
        raise

def fetch_product_details_by_id(product_id: int) -> dict:
    """
    Получает всю информацию о продукте по его id
    :param product_id: id продукта для которого мы запрашиваем информацию.
    :return: словарь которых хранит детализированную информацию.
    """
    try:
        product_details = repositories.products.get_product_details_by_id(product_id)

        if not product_details:
            print(f"No product found for ID: {product_id}")
            return {}

        print(f"Received product details for ID: {product_id}")
        return product_details
    except Exception as e:
        print(f"Error while fetching product details: {e}")
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
        print("Product added to cart successfully.")
    except Exception as e:
        print(f"Error in add_product_to_user_cart: {e}")
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
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while checking stock for product ID {product_id}: {e}")
        raise

def reduce_product_stock(product_id: int, quantity: int) -> None:
    """
    Обертка для функции decrease_product_stock. Уменьшает количество товара на складе.

    :param product_id: ID продукта.
    :param quantity: Количество, на которое нужно уменьшить.
    """
    try:
        repositories.products.decrease_product_stock(product_id, quantity)
        print(f"Successfully decreased stock for product ID {product_id} by {quantity}.")
    except ValueError as e:
        print(f"Stock decrease error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while decreasing stock for product ID {product_id}: {e}")
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
        print(f"Product '{name}' added successfully with ID: {product_id}.")
        return product_id
    except Exception as e:
        print(f"Error while adding new product: {e}")
        raise