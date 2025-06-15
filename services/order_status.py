"""
Константы для статусов заказов
"""

# Английские статусы (используются в базе данных)
PENDING = "Pending"
PROCESSING = "Processing"
CONFIRMED = "Confirmed"
SHIPPED = "Shipped"
DELIVERED = "Delivered"
CANCELLED = "Cancelled"
COMPLETED = "Completed"

# Маппинг английских статусов на русские (для отображения)
STATUS_MAPPING = {
    PENDING: "В обработке",
    PROCESSING: "В обработке",
    CONFIRMED: "Подтвержден",
    SHIPPED: "Отправлен",
    DELIVERED: "Доставлен",
    CANCELLED: "Отменен",
    COMPLETED: "Завершен"
}

# Обратный маппинг (русские -> английские)
REVERSE_STATUS_MAPPING = {v: k for k, v in STATUS_MAPPING.items()}

# Эмодзи для статусов
STATUS_EMOJI = {
    PENDING: "🟡",
    PROCESSING: "🟡",
    CONFIRMED: "🔵",
    SHIPPED: "🟢",
    DELIVERED: "✅",
    CANCELLED: "❌",
    COMPLETED: "✅"
}

# Список всех возможных статусов
ALL_STATUSES = list(STATUS_MAPPING.keys()) 