import streamlit as st
import json
import threading
import time
from services.redis_service import RedisService
import logging

logger = logging.getLogger(__name__)

class NotificationHandler:
    def __init__(self):
        self.redis_service = RedisService()
        self.last_check_time = time.time()
        self.status_mapping = {
            "Pending": "В обработке",
            "Processing": "В обработке",
            "Confirmed": "Подтвержден",
            "Shipped": "Отправлен",
            "Delivered": "Доставлен",
            "Cancelled": "Отменен"
        }

    def check_notifications(self):
        """Check for new notifications"""
        try:
            current_time = time.time()
            # Проверяем сообщения только каждые 2 секунды
            if current_time - self.last_check_time < 2:
                return

            self.last_check_time = current_time
            message = self.redis_service.get_message()
            
            if message:
                logger.info(f"Processing notification: {message}")
                self._handle_notification(message)
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")

    def _handle_notification(self, message):
        """Handle different types of notifications"""
        try:
            if 'type' not in message:
                return

            if message['type'] == 'order_status_changed':
                self._handle_order_status_change(message)
            # Добавьте другие типы уведомлений здесь
        except Exception as e:
            logger.error(f"Error handling notification: {e}")

    def _handle_order_status_change(self, message):
        """Handle order status change notification"""
        try:
            order_id = message.get('order_id')
            status = message.get('status')
            user_id = message.get('user_id')

            if not all([order_id, status]):
                logger.error("Missing required fields in order status notification")
                return

            # Проверяем, относится ли уведомление к текущему пользователю
            current_user_id = st.session_state.get('user', {}).get('user_id')
            if current_user_id and str(current_user_id) == str(user_id):
                # Преобразуем статус в русский
                status_ru = self.status_mapping.get(status, status)
                st.toast(f"Статус заказа #{order_id} изменен на: {status_ru}")
                logger.info(f"Displayed notification for order {order_id} status change to {status_ru}")
        except Exception as e:
            logger.error(f"Error handling order status change: {e}")

def init_notifications():
    """Initialize notifications in session state"""
    if "notifications" not in st.session_state:
        st.session_state.notifications = []

def add_notification(message: str, type: str = "info"):
    """Add a notification to the session state"""
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    
    # Add new notification
    st.session_state.notifications.append({
        "message": message,
        "type": type,
        "timestamp": time.time()
    })
    
    # Keep only last 5 notifications
    if len(st.session_state.notifications) > 5:
        st.session_state.notifications = st.session_state.notifications[-5:]

def notification_listener():
    """Listen for notifications from Redis PubSub"""
    try:
        while True:
            message = redis_service.get_message()
            if message and message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    if data.get('type') == 'order_status_changed':
                        # Преобразуем статус в русский
                        status_mapping = {
                            "Pending": "В обработке",
                            "Processing": "В обработке",
                            "Confirmed": "Подтвержден",
                            "Shipped": "Отправлен",
                            "Delivered": "Доставлен",
                            "Cancelled": "Отменен"
                        }
                        status_ru = status_mapping.get(data['status'], data['status'])
                        add_notification(
                            f"Статус заказа {data['order_id']} изменен на {status_ru}",
                            "success"
                        )
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error in notification listener: {e}")
        # Try to reconnect
        try:
            redis_service.close_pubsub()
            redis_service.pubsub = redis_service.redis_client.pubsub()
            redis_service.pubsub.subscribe("order_status_changed")
        except Exception as reconnect_error:
            print(f"Failed to reconnect: {reconnect_error}")

def start_notification_listener():
    """Start notification listener in a separate thread"""
    if "notification_thread" not in st.session_state:
        st.session_state.notification_thread = threading.Thread(
            target=notification_listener,
            daemon=True
        )
        st.session_state.notification_thread.start()

def show_notifications():
    """Show notifications in the UI"""
    if 'notification_handler' not in st.session_state:
        st.session_state.notification_handler = NotificationHandler()

    # Проверяем новые уведомления
    st.session_state.notification_handler.check_notifications() 