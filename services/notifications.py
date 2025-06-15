from datetime import datetime
import json
from services.redis_service import RedisService

redis_service = RedisService()

def create_notification(user_id: int, message: str, notification_type: str = "info") -> None:
    """
    Создает новое уведомление для пользователя
    :param user_id: ID пользователя
    :param message: Текст уведомления
    :param notification_type: Тип уведомления (info, success, warning, error)
    """
    notification = {
        "id": f"notif_{datetime.now().timestamp()}",
        "user_id": user_id,
        "message": message,
        "type": notification_type,
        "created_at": datetime.now().isoformat(),
        "read": False
    }
    
    # Сохраняем уведомление в Redis
    redis_service.redis_client.lpush(f"notifications:{user_id}", json.dumps(notification))
    # Ограничиваем количество уведомлений (храним последние 50)
    redis_service.redis_client.ltrim(f"notifications:{user_id}", 0, 49)
    
    # Публикуем событие о новом уведомлении
    redis_service.publish_event("new_notification", {
        "user_id": user_id,
        "notification": notification
    })

def get_user_notifications(user_id: int, limit: int = 10) -> list:
    """
    Получает уведомления пользователя
    :param user_id: ID пользователя
    :param limit: Максимальное количество уведомлений
    :return: Список уведомлений
    """
    notifications = redis_service.redis_client.lrange(f"notifications:{user_id}", 0, limit - 1)
    return [json.loads(n) for n in notifications]

def mark_notification_as_read(user_id: int, notification_id: str) -> None:
    """
    Отмечает уведомление как прочитанное
    :param user_id: ID пользователя
    :param notification_id: ID уведомления
    """
    notifications = get_user_notifications(user_id, limit=50)
    for notification in notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
            # Обновляем уведомление в Redis
            redis_service.redis_client.lset(
                f"notifications:{user_id}",
                notifications.index(notification),
                json.dumps(notification)
            )
            break

def get_unread_notifications_count(user_id: int) -> int:
    """
    Получает количество непрочитанных уведомлений
    :param user_id: ID пользователя
    :return: Количество непрочитанных уведомлений
    """
    notifications = get_user_notifications(user_id, limit=50)
    return sum(1 for n in notifications if not n["read"])

# Предопределенные типы уведомлений
def notify_order_status_change(user_id: int, order_id: int, new_status: str) -> None:
    """Уведомление об изменении статуса заказа"""
    create_notification(
        user_id,
        f"Статус заказа #{order_id} изменен на: {new_status}",
        "info"
    )

def notify_new_order(user_id: int, order_id: int) -> None:
    """Уведомление о новом заказе"""
    create_notification(
        user_id,
        f"Создан новый заказ #{order_id}",
        "success"
    )

def notify_low_stock(user_id: int, product_name: str) -> None:
    """Уведомление о низком запасе товара"""
    create_notification(
        user_id,
        f"Низкий запас товара: {product_name}",
        "warning"
    )

def notify_price_change(user_id: int, product_name: str, new_price: float) -> None:
    """Уведомление об изменении цены товара"""
    create_notification(
        user_id,
        f"Изменена цена товара {product_name}: {new_price} руб.",
        "info"
    ) 