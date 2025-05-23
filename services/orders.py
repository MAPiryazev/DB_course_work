from services.notifications import notify_order_status_change, notify_new_order

def update_order_status(order_id: int, new_status: str) -> None:
    """
    Обновляет статус заказа
    :param order_id: ID заказа
    :param new_status: Новый статус
    """
    try:
        # Получаем информацию о заказе
        order = get_order_details(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Обновляем статус в БД
        repositories.orders.update_order_status(order_id, new_status)
        
        # Отправляем уведомление пользователю
        notify_order_status_change(order['user_id'], order_id, new_status)
        
        print(f"Order {order_id} status updated to {new_status}")
    except Exception as e:
        print(f"Error updating order status: {e}")
        raise

def create_order(user_id: int, items: list) -> int:
    """
    Создает новый заказ
    :param user_id: ID пользователя
    :param items: Список товаров в заказе
    :return: ID нового заказа
    """
    try:
        # Создаем заказ в БД
        order_id = repositories.orders.create_order(user_id, items)
        
        # Отправляем уведомление о новом заказе
        notify_new_order(user_id, order_id)
        
        return order_id
    except Exception as e:
        print(f"Error creating order: {e}")
        raise 